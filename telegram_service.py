import re
import requests

from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_ADMIN_CHAT_ID,
    TELEGRAM_LINK_BOT_ENABLED,
)
from utils.db import update_user_telegram_link


def _base_url():
    if not TELEGRAM_BOT_TOKEN:
        return ""
    return f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def send_telegram_message(chat_id: str, message: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not chat_id:
        return False

    try:
        url = f"{_base_url()}/sendMessage"
        response = requests.post(
            url,
            json={
                "chat_id": str(chat_id),
                "text": message,
            },
            timeout=15,
        )
        return response.status_code == 200 and response.json().get("ok") is True
    except Exception:
        return False


def send_telegram_alert(message: str) -> bool:
    return send_telegram_message(TELEGRAM_ADMIN_CHAT_ID, message)


def extract_phone_from_text(text: str) -> str:
    raw = re.sub(r"[^0-9]", "", str(text or ""))
    if len(raw) == 11 and raw.startswith("01"):
        return raw
    return ""


def sync_telegram_phone_links() -> int:
    if not TELEGRAM_LINK_BOT_ENABLED:
        return 0
    if not TELEGRAM_BOT_TOKEN:
        return 0

    updated = 0
    try:
        url = f"{_base_url()}/getUpdates"
        response = requests.get(url, timeout=20)
        if response.status_code != 200:
            return 0

        data = response.json()
        if not data.get("ok"):
            return 0

        for item in data.get("result", []):
            msg = item.get("message", {}) or {}
            chat = msg.get("chat", {}) or {}
            from_user = msg.get("from", {}) or {}
            text = msg.get("text", "") or ""

            phone = extract_phone_from_text(text)
            if not phone:
                contact = msg.get("contact", {}) or {}
                phone = extract_phone_from_text(contact.get("phone_number", ""))

            if not phone:
                continue

            chat_id = str(chat.get("id", "")).strip()
            username = str(from_user.get("username", "")).strip()

            if chat_id:
                update_user_telegram_link(phone, chat_id, username)
                updated += 1

        return updated
    except Exception:
        return 0
