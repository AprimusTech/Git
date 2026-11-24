"""SQLite persistence for the WhatsApp draft-only assistant.

Safe, additive migrations preserve existing contacts, messages and draft history.
"""
import sqlite3
from config import DB_PATH, DATA_DIR

SCHEMA = '''
CREATE TABLE IF NOT EXISTS contacts (
    phone TEXT PRIMARY KEY,
    display_name TEXT NOT NULL DEFAULT '',
    enabled INTEGER NOT NULL DEFAULT 0,
    auto_reply INTEGER NOT NULL DEFAULT 0,
    style TEXT NOT NULL DEFAULT '',
    instructions TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone TEXT NOT NULL,
    direction TEXT NOT NULL CHECK(direction IN ('incoming', 'outgoing', 'draft')),
    body TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'logged',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(phone) REFERENCES contacts(phone)
);
CREATE TABLE IF NOT EXISTS reply_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone TEXT NOT NULL,
    incoming_message_id INTEGER,
    draft_text TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected', 'sent')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TEXT,
    FOREIGN KEY(phone) REFERENCES contacts(phone),
    FOREIGN KEY(incoming_message_id) REFERENCES messages(id)
);
CREATE TABLE IF NOT EXISTS contact_memory (
    phone TEXT PRIMARY KEY,
    memory_text TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS processed_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(phone, fingerprint)
);
CREATE TABLE IF NOT EXISTS app_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
'''


def _connect():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.execute('PRAGMA busy_timeout=15000')
    conn.execute('PRAGMA foreign_keys=ON')
    return conn


def initialize_database():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.executescript(SCHEMA)
        # Additive compatibility migrations for databases created by earlier builds.
        cols = {r[1] for r in conn.execute('PRAGMA table_info(messages)')}
        if 'source_key' not in cols:
            conn.execute('ALTER TABLE messages ADD COLUMN source_key TEXT')


def upsert_contact(contact):
    with _connect() as conn:
        conn.execute('''INSERT INTO contacts(phone, display_name, enabled, auto_reply, style, instructions)
            VALUES(?,?,?,?,?,?) ON CONFLICT(phone) DO UPDATE SET
              display_name=excluded.display_name, enabled=excluded.enabled,
              auto_reply=excluded.auto_reply, style=excluded.style,
              instructions=excluded.instructions, updated_at=CURRENT_TIMESTAMP''',
            (contact['phone'], contact.get('name', ''), int(contact.get('enabled', False)),
             int(contact.get('auto_reply', False)), contact.get('style', ''),
             contact.get('instructions', '')))


def log_message(phone, direction, body, status='logged', source_key=None):
    with _connect() as conn:
        cur = conn.execute(
            'INSERT INTO messages(phone,direction,body,status,source_key) VALUES(?,?,?,?,?)',
            (phone, direction, body, status, source_key))
        return cur.lastrowid


def queue_draft(phone, incoming_message_id, draft_text):
    with _connect() as conn:
        cur = conn.execute(
            'INSERT INTO reply_queue(phone,incoming_message_id,draft_text) VALUES(?,?,?)',
            (phone, incoming_message_id, draft_text))
        return cur.lastrowid


def get_whitelisted_contact(phone):
    with _connect() as conn:
        row = conn.execute('''SELECT phone,display_name,enabled,auto_reply,style,instructions
            FROM contacts WHERE phone=? AND enabled=1''', (phone,)).fetchone()
    if not row:
        return None
    return {'phone': row[0], 'name': row[1], 'enabled': bool(row[2]),
            'auto_reply': bool(row[3]), 'style': row[4], 'instructions': row[5]}


def get_recent_messages(phone, limit=12):
    with _connect() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute('''SELECT direction,body,created_at FROM messages
            WHERE phone=? ORDER BY id DESC LIMIT ?''', (phone, int(limit))).fetchall()
    return list(reversed([dict(row) for row in rows]))


def get_contact_memory(phone):
    with _connect() as conn:
        row = conn.execute('SELECT memory_text FROM contact_memory WHERE phone=?', (phone,)).fetchone()
    return row[0] if row else ''


def register_processed_message(phone, fingerprint):
    """Return True only for the first time this message fingerprint is seen."""
    with _connect() as conn:
        cur = conn.execute('INSERT OR IGNORE INTO processed_messages(phone,fingerprint) VALUES(?,?)',
                           (phone, fingerprint))
        return cur.rowcount == 1


def get_recent_drafts(limit=250):
    with _connect() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute('''SELECT q.id AS queue_id, q.phone, c.display_name,
            im.body AS incoming, q.draft_text AS draft, q.status, q.created_at
            FROM reply_queue q LEFT JOIN contacts c ON c.phone=q.phone
            LEFT JOIN messages im ON im.id=q.incoming_message_id
            ORDER BY q.id DESC LIMIT ?''', (int(limit),)).fetchall()
    return [dict(r) for r in rows]


def set_app_state(key, value):
    with _connect() as conn:
        conn.execute('''INSERT INTO app_state(key,value) VALUES(?,?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=CURRENT_TIMESTAMP''',
            (key, str(value)))


def get_app_state(key, default=''):
    with _connect() as conn:
        row = conn.execute('SELECT value FROM app_state WHERE key=?', (key,)).fetchone()
    return row[0] if row else default
