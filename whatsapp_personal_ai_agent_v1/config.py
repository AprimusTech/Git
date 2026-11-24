from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "agent.db"
CONTACTS_PATH = ROOT_DIR / "contacts.json"

DEFAULT_MODE = "approval_only"
AUTO_SEND_ENABLED = True

# Select 'ollama' (local) or 'openai' (cloud API).
AI_PROVIDER = "ollama"
OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2:3b"
#OLLAMA_MODEL = "qwen3.5:9b"
OPENAI_MODEL = "gpt-4o-mini"
