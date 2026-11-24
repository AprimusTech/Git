"""Interactive local test: generate a draft for an enabled test contact."""
from main import initialize_database, sync_contacts, normalize_phone
from database import log_message
from ai_engine import generate_reply


def run():
    initialize_database()
    sync_contacts()
    phone = normalize_phone(input("Enter whitelisted contact phone (country code + number): "))
    incoming = input("Paste a sample incoming message: ").strip()
    if not incoming:
        print("No message supplied; exiting.")
        return
    # This is a local test input. It is logged to the local DB as an incoming message.
    log_message(phone, "incoming", incoming, status="test_input")
    try:
        draft = generate_reply(phone, incoming)
    except Exception as exc:
        print(f"Draft generation failed: {exc}")
        return
    print("\n=== AI DRAFT (NOT SENT) ===")
    print(draft)
    print("===========================")

if __name__ == "__main__":
    run()
