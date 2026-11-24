"""Experimental WhatsApp Desktop UIA monitor. Draft-only; no sending implemented.
Run the diagnostic first to confirm the app exposes message text through UI Automation.
"""
import asyncio
import json
import re
import time
from pathlib import Path

from pywinauto import Desktop
from config import DATA_DIR
from database import initialize_database, log_message, queue_draft
from ai_engine import generate_reply
from monitor_helpers import load_allowed_contacts, message_fingerprint

BASE = Path(__file__).resolve().parent
CONTACTS_FILE = BASE / "contacts.json"
POLL_SECONDS = 4
MAX_TEXT_LEN = 4000


def find_whatsapp_window():
    for window in Desktop(backend="uia").windows():
        title = (window.window_text() or "").strip()
        if "whatsapp" in title.casefold():
            return window
    return None



def visible_text_snapshot(window):
    """Collect UIA text names; avoid coordinate-based clicking and keyboard input."""
    values = []
    for el in window.descendants():
        try:
            name = (el.element_info.name or "").strip()
            if name and len(name) <= MAX_TEXT_LEN:
                values.append(name)
        except Exception:
            continue
    # Keep stable order, de-duplicate identical labels.
    return list(dict.fromkeys(values))


def best_contact_match(snapshot, enabled):
    """Exact normalized contact-name match only; never substring match."""
    norm = {name.casefold().strip(): phone for name, phone in enabled.items()}
    hits = []
    for value in snapshot:
        candidate = value.casefold().strip()
        if candidate in norm:
            hits.append((value, norm[candidate]))
    # Do not process if UIA text gives ambiguous duplicate contact labels.
    unique = {}
    for name, phone in hits:
        unique.setdefault(phone, name)
    return list(unique.items())


async def monitor():
    initialize_database()
    enabled = load_allowed_contacts(CONTACTS_FILE)
    if not enabled:
        print("No enabled contacts found in contacts.json. Enable/name contacts first.")
        return
    print("WhatsApp Desktop UIA monitor started (DRAFT-ONLY).")
    print("No chat clicks, keyboard typing, or sends are performed.")
    print("Open WhatsApp Desktop and keep it visible. Stop with Ctrl+C.")
    fingerprints = set()
    baseline = True
    try:
        while True:
            win = find_whatsapp_window()
            if win is None:
                print("WhatsApp Desktop window not found; retrying...")
                await asyncio.sleep(POLL_SECONDS)
                continue
            snap = visible_text_snapshot(win)
            contacts = best_contact_match(snap, enabled)
            if not baseline:
                for phone, display_name in contacts:
                    # UIA exposes contact labels but not a reliable message boundary/direction
                    # in all WhatsApp Desktop builds. Only report the contact detection here.
                    print(f"UIA contact label seen: {display_name} ({phone[-4:]})")
            if baseline:
                baseline = False
                print(f"Baseline UIA snapshot captured: {len(snap)} visible text items.")
                print("UIA can see contact labels; this build intentionally does not infer incoming messages.")
            await asyncio.sleep(POLL_SECONDS)
    except KeyboardInterrupt:
        print("Desktop monitor stopped.")


if __name__ == "__main__":
    asyncio.run(monitor())
