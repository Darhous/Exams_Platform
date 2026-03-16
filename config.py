import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "").strip()
TELEGRAM_LINK_BOT_ENABLED = os.getenv("TELEGRAM_LINK_BOT_ENABLED", "true").strip().lower() == "true"

WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v22.0").strip()
WHATSAPP_ENABLED = os.getenv("WHATSAPP_ENABLED", "false").strip().lower() == "true"

NOTIFICATIONS_SEND_TELEGRAM = os.getenv("NOTIFICATIONS_SEND_TELEGRAM", "true").strip().lower() == "true"
NOTIFICATIONS_SEND_WHATSAPP = os.getenv("NOTIFICATIONS_SEND_WHATSAPP", "true").strip().lower() == "true"

APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8501").strip()
