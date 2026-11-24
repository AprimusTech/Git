import json
from config import CONTACTS_PATH
from database import initialize_database, upsert_contact

def normalize_phone(phone):
    # Store digits only, including country code. Example India: 91XXXXXXXXXX
    return ''.join(ch for ch in str(phone) if ch.isdigit())

def load_contacts():
    if not CONTACTS_PATH.exists():
        CONTACTS_PATH.write_text("{}", encoding="utf-8")
        return {}
    return json.loads(CONTACTS_PATH.read_text(encoding="utf-8"))

def sync_contacts():
    contacts = load_contacts()
    for phone, settings in contacts.items():
        normalized = normalize_phone(phone)
        if not normalized:
            continue
        contact = {"phone": normalized, **settings}
        upsert_contact(contact)
    return len(contacts)

def main():
    initialize_database()
    count = sync_contacts()
    print("WhatsApp Personal AI Agent - Day 1 foundation")
    print(f"Database ready. Contact settings loaded: {count}")
    print("Mode: approval-only foundation (no WhatsApp login or sending yet)")
    print("Edit contacts.json, then rerun to sync changes.")

if __name__ == "__main__":
    main()
