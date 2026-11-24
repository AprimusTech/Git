"""Compatibility launcher: use the integrated monitor from the dashboard instead.
Do not launch a second browser against the same persistent WhatsApp profile.
"""
import sys
from pathlib import Path
import subprocess

BASE = Path(__file__).resolve().parent
print('Use gui.py -> Start WhatsApp Monitor. This prevents two processes opening the same browser profile.')
print('If you need terminal-only mode, run: python whatsapp_draft_monitor.py')
if len(sys.argv) > 1 and sys.argv[1] == '--monitor':
    subprocess.run([sys.executable, str(BASE / 'whatsapp_draft_monitor.py')], cwd=str(BASE))
