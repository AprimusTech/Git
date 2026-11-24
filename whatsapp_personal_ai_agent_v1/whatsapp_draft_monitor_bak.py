"""Read-only WhatsApp Web monitor. Generates local drafts; never sends messages.

This version reads WhatsApp's message metadata (data-pre-plain-text / data-id)
 instead of relying on the obsolete .message-in CSS class.
"""
import argparse
import asyncio
import logging
import re
from pathlib import Path

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

from config import DATA_DIR
from database import (initialize_database, log_message, queue_draft,
                      register_processed_message, set_app_state)
from ai_engine import generate_reply
from monitor_helpers import load_allowed_contacts, normalize_label, message_fingerprint

BASE = Path(__file__).resolve().parent
PROFILE = DATA_DIR / 'whatsapp_browser_profile'
CONTACTS_FILE = BASE / 'contacts.json'
POLL_SECONDS = 4

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s', datefmt='%H:%M:%S')
log = logging.getLogger('wa-monitor')


def _extract_sender(pre_plain_text):
    """Extract sender label from WhatsApp metadata: '[time, date] Sender: '."""
    if not pre_plain_text:
        return ''
    match = re.search(r'\]\s*(.*?):\s*$', pre_plain_text)
    return normalize_label(match.group(1)) if match else ''


async def find_enabled_chat_rows(page, allowed):
    result = []
    rows = page.locator('[role="listitem"], [role="row"]')
    count = await rows.count()
    log.info('Chat-list rows found: %s', count)
    for index in range(count):
        row = rows.nth(index)
        try:
            aria = (await row.get_attribute('aria-label')) or ''
            candidates = [part.strip() for part in aria.split(',') if part.strip()]
            titles = row.locator('[title]')
            for j in range(min(await titles.count(), 8)):
                title = await titles.nth(j).get_attribute('title')
                if title:
                    candidates.append(title.strip())
            matched = next((normalize_label(c) for c in candidates if normalize_label(c) in allowed), None)
            if matched:
                result.append((row, matched))
        except Exception as exc:
            log.debug('Skipped unreadable chat row: %s', exc)
    log.info('Enabled chat rows matched: %s', len(result))
    return result


async def read_incoming_messages(page, contact_name):
    """Read visible text messages and positively identify incoming direction.

    The old `.message-in` class is no longer assumed. We use message metadata
    and only accept messages whose sender matches the currently opened 1:1 chat.
    Ambiguous direction is skipped rather than risking a draft from our own text.
    """
    rows = await page.locator('div.copyable-text[data-pre-plain-text], [data-pre-plain-text]').evaluate_all("""els => els.map(el => {
      const metaNode = el.matches('[data-pre-plain-text]') ? el : el.closest('[data-pre-plain-text]');
      const dataIdNode = el.closest('[data-id]') || el;
      const textNodes = el.querySelectorAll('.selectable-text');
      const texts = Array.from(textNodes).map(n => (n.innerText || n.textContent || '').trim()).filter(Boolean);
      const text = texts.join('\\n').trim();
      const pre = metaNode ? (metaNode.getAttribute('data-pre-plain-text') || '') : '';
      const dataId = dataIdNode ? (dataIdNode.getAttribute('data-id') || '') : '';
      const cls = (el.className && typeof el.className === 'string') ? el.className : '';
      return {text, pre, dataId, cls};
    })""")
    wanted = normalize_label(contact_name)
    found = []
    for item in rows:
        body = (item.get('text') or '').strip()
        if not body:
            continue
        pre = item.get('pre') or ''
        data_id = item.get('dataId') or ''
        sender = _extract_sender(pre)
        # WhatsApp data-id prefixes can explicitly identify incoming/outgoing.
        if data_id.startswith('true_'):
            is_incoming = True
        elif data_id.startswith('false_'):
            is_incoming = False
        elif 'message-in' in (item.get('cls') or ''):
            is_incoming = True
        elif 'message-out' in (item.get('cls') or ''):
            is_incoming = False
        elif sender:
            is_incoming = sender == wanted
        else:
            is_incoming = False
        if is_incoming:
            source_key = data_id or pre
            found.append((body, source_key))
    log.info('Message DOM candidates=%s; positively identified incoming=%s', len(rows), len(found))
    if rows and not found:
        # Metadata is deliberately not logged verbatim because it can contain contact details.
        meta_count = sum(1 for r in rows if r.get('pre'))
        id_count = sum(1 for r in rows if r.get('dataId'))
        log.warning('No incoming direction could be verified (metadata=%s, data-id=%s, chat=%s).', meta_count, id_count, contact_name)
    return found[-30:]


async def wait_for_whatsapp_ready(page):
    await page.goto('https://web.whatsapp.com', wait_until='domcontentloaded')
    log.info('Waiting for WhatsApp Web login/readiness (up to 2 minutes)...')
    try:
        await page.wait_for_function("""() => !!document.querySelector('[role="grid"], [role="list"]') || !!document.querySelector('canvas[aria-label*="Scan"], [data-testid*="qrcode"]')""", timeout=120000)
    except PlaywrightTimeoutError:
        raise RuntimeError('WhatsApp Web did not become ready. Check QR login and browser window.')
    if await page.locator('canvas[aria-label*="Scan"], [data-testid*="qrcode"]').count():
        log.info('QR code visible. Scan it with your phone; waiting for login...')
        await page.wait_for_selector('[role="grid"], [role="list"]', timeout=120000)


async def monitor():
    initialize_database()
    allowed = load_allowed_contacts(CONTACTS_FILE)
    if not allowed:
        log.error('No enabled contacts with names found in contacts.json.')
        return
    PROFILE.mkdir(parents=True, exist_ok=True)
    log.info('Starting read-only WhatsApp draft monitor.')
    log.info('This process owns the browser profile. Do NOT run whatsapp_connect.py simultaneously.')
    log.info('Enabled contacts: %s', ', '.join(allowed.keys()))
    log.info('Draft-only mode: no WhatsApp messages will be sent. Ctrl+C stops monitoring.')
    set_app_state('monitor_status', 'starting')

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            str(PROFILE), headless=False, viewport={'width': 1440, 'height': 950},
            args=['--disable-notifications'])
        page = context.pages[0] if context.pages else await context.new_page()
        try:
            await wait_for_whatsapp_ready(page)
            log.info('WhatsApp Web ready. Scanning enabled contacts...')
            set_app_state('monitor_status', 'running')
            baseline = True
            while True:
                try:
                    matches = await find_enabled_chat_rows(page, allowed)
                    for row, contact_name in matches:
                        phone = allowed[contact_name]
                        try:
                            await row.click(timeout=3500)
                            await page.wait_for_timeout(500)
                            messages = await read_incoming_messages(page, contact_name)
                            for body, source_key in messages:
                                fingerprint = message_fingerprint(phone, body, source_key)
                                first_seen = register_processed_message(phone, fingerprint)
                                if not first_seen:
                                    continue
                                if baseline:
                                    continue
                                incoming_id = log_message(phone, 'incoming', body,
                                                          status='monitor_detected', source_key=source_key)
                                log.info('INCOMING DETECTED | %s (%s): %s', contact_name, phone, body[:180])
                                try:
                                    draft = generate_reply(phone, body)
                                    log_message(phone, 'draft', draft, status='generated_from_monitor')
                                    queue_id = queue_draft(phone, incoming_id, draft)
                                    log.info('AI DRAFT #%s READY — NOT SENT: %s', queue_id, draft)
                                    set_app_state('last_draft_at', 'just now')
                                except Exception as exc:
                                    log.exception('Draft generation failed for %s: %s', contact_name, exc)
                                    set_app_state('last_monitor_error', str(exc)[:500])
                        except Exception as exc:
                            log.warning('Could not scan chat %s: %s', contact_name, exc)
                    if baseline:
                        baseline = False
                        log.info('Baseline complete. New incoming messages will now generate drafts.')
                    set_app_state('last_scan_at', 'running')
                except Exception as exc:
                    log.exception('Monitor scan cycle failed: %s', exc)
                    set_app_state('last_monitor_error', str(exc)[:500])
                await asyncio.sleep(POLL_SECONDS)
        finally:
            set_app_state('monitor_status', 'stopped')
            # Avoid a second close if the browser was already closed by the user.
            try:
                await context.close()
            except Exception as exc:
                log.info('Browser context already closed during shutdown: %s', exc)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Read-only WhatsApp AI draft monitor')
    parser.parse_args()
    try:
        asyncio.run(monitor())
    except KeyboardInterrupt:
        log.info('Monitor stopped by user.')
        set_app_state('monitor_status', 'stopped')
    except Exception as exc:
        log.exception('Monitor stopped because of an error: %s', exc)
        try:
            set_app_state('monitor_status', 'error: ' + str(exc)[:300])
        except Exception:
            pass
