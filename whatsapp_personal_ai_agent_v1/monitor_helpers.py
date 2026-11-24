"""Pure helper functions for matching enabled contacts and identifying messages."""
import hashlib
import json
import re
from pathlib import Path

def normalize_label(value):
    value = (value or '').casefold().strip()
    value = re.sub(r'\s+', ' ', value)
    return re.sub(r'^[^\w]+|[^\w]+$', '', value)

def load_allowed_contacts(contacts_file: Path):
    if not contacts_file.exists():
        return {}
    raw = json.loads(contacts_file.read_text(encoding='utf-8'))
    allowed = {}
    for phone, settings in raw.items():
        name = normalize_label(str(settings.get('name', '')))
        normalized_phone = ''.join(ch for ch in str(phone) if ch.isdigit())
        if settings.get('enabled') and name and normalized_phone:
            allowed[name] = normalized_phone
    return allowed

def message_fingerprint(phone, message_text, source_key=''):
    normalized = f'{phone}\n{source_key.strip()}\n{message_text.strip()}'
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
