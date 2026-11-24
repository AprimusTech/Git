# Day 4 — WhatsApp Web connection (experimental, read-only)

**Account-risk notice:** WhatsApp Web UI automation is unofficial, can break as the UI changes, and may risk account restrictions. Use at your own risk. This script has no send-message capability.

## Install
Run in your project directory with the venv active:
```powershell
python -m pip install -r requirements-day4.txt
python -m playwright install chromium
```

## Run
Ensure `contacts.json` has at least one enabled contact with a name. Then:
```powershell
python whatsapp_connect.py
```
A browser opens WhatsApp Web. Scan its QR code using WhatsApp on your phone if prompted. Keep the browser visible; Ctrl+C stops.

## Experimental limitations
- Chat/message selectors are heuristic and may fail when WhatsApp Web changes its DOM.
- It matches chat display names to enabled contacts, not verified phone numbers. Duplicate display names can cause ambiguity. Do not use it for sensitive messages or trust its identity match.
- This step only tests connection and console detection. It does not store incoming messages, generate AI drafts from detected messages, or send messages.
- Never paste passwords, OTPs, or session credentials into code or config files.
