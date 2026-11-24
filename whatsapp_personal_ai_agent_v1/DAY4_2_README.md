# Day 4.2 — Integrated WhatsApp Draft Dashboard

## What changed

- The dashboard can start/stop the read-only WhatsApp monitor.
- The monitor is the only process that opens the persistent WhatsApp browser profile.
- The GUI polls SQLite and displays monitor-generated drafts in **Live Draft Inbox**.
- Draft history is read from SQLite, so it survives closing/reopening the GUI.
- Contact matching remains exact by configured WhatsApp display name to reduce wrong-person matches.
- Monitor errors and unmatched contacts are logged visibly in its terminal.
- New database tables are created with additive migrations; existing contacts/messages/drafts are preserved.
- No send-message code is included. `auto_reply` is ignored; all drafts require manual review.
- AI prompt history excludes unsent drafts and avoids repeating the current incoming message.

## Install into the existing Windows project

1. Close the old GUI and stop any running `whatsapp_connect.py` or `whatsapp_draft_monitor.py` windows with `Ctrl+C`.
2. Make a backup of the project folder. Do not delete `data`, `contacts.json`, `.venv`, or the browser profile.
3. Extract the patch ZIP into the existing project folder and choose **Replace** for the Python files. The patch does not contain `contacts.json`, `data/agent.db`, `.venv`, or browser session files.
4. Open PowerShell in the project folder and run:

```powershell
.venv\Scripts\Activate.ps1
python -m py_compile *.py
python -m unittest discover -s tests -v
python -m unittest test_ai_engine -v
python gui.py
```

5. In the GUI, verify that the enabled contact names match the WhatsApp chat names exactly (case is ignored). Click **Start WhatsApp Monitor**.
6. Keep the GUI open. The monitor opens the existing WhatsApp browser profile in a separate terminal. Scan QR if requested.
7. The first scan is a baseline: messages already present are intentionally skipped. Send a new test message from another account to one enabled contact. The new incoming message and draft should appear in **Live Draft Inbox** after the scan.
8. Select a draft to preview it, then use **Copy selected draft** if you want to paste it manually in WhatsApp.

## Important behavior and limitations

- Do not run `whatsapp_connect.py` alongside the monitor. The GUI's Start button launches the monitor, which owns the browser profile.
- Exact display-name matching is deliberately conservative. If a chat name differs from `contacts.json`, correct the contact name in the GUI and save it.
- WhatsApp Web is an unofficial, changing web interface. DOM selectors may need maintenance; check the monitor terminal for errors. The code does not guarantee detection of every message or media type.
- Current monitor processes the latest incoming text bubble in each matched chat. It does not process images, audio, documents, groups, or full message backlogs.
- Keep the browser visible and logged in. Do not share the browser profile or database; they may contain private data.
- Nothing is sent automatically. Do not enable automatic sending; no send implementation exists in this build.
