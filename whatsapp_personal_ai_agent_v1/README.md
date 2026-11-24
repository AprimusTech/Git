# WhatsApp Personal AI Agent — Day 3

Day 1 foundation + Day 2 draft AI + Day 3 Tkinter GUI and improved Hinglish prompt.

## Safety and scope
- This build only generates drafts. It does not connect to WhatsApp or send messages.
- Contact whitelist: only configured contacts with `enabled: true` are allowed for AI drafting.
- Auto-send is intentionally unavailable.

## Windows setup
Use your existing virtual environment if present:
```bat
.venv\Scripts\activate
python main.py
```
Launch the GUI dashboard:
```bat
python gui.py
```

If Ollama is configured locally, ensure it is running and the configured model is pulled.

## GUI tabs
- Contacts & Rules: add/edit phone, display name, whitelist toggle, style, instructions.
- Generate Draft: choose enabled contact, paste incoming message, generate draft, copy it.
- Draft History: shows drafts generated in the current GUI session.

Database drafts are logged to SQLite. The GUI does not send WhatsApp messages.
