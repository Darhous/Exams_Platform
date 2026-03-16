import os
import re
import requests
from typing import Tuple, List, Optional
from dotenv import load_dotenv

load_dotenv()

WHATSAPP_TOKEN = (
    os.getenv("WHATSAPP_TOKEN")
    or os.getenv("WHATSAPP_ACCESS_TOKEN")
    or ""
).strip()

WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v22.0").strip()
WHATSAPP_TEMPLATE_LANG = os.getenv("WHATSAPP_TEMPLATE_LANG", "ar_EG").strip()


def normalize_egypt_phone(phone: str) -> str:
    if not phone:
        return ""

    phone = str(phone).strip()
    phone = re.sub(r"[^\d+]", "", phone)

    if phone.startswith("+"):
        phone = phone[1:]

    if phone.startswith("0020"):
        return phone[2:]

    if phone.startswith("01") and len(phone) == 11:
        return "2" + phone

    if phone.startswith("1") and len(phone) == 10:
        return "20" + phone

    if phone.startswith("20") and len(phone) == 12:
        return phone

    return re.sub(r"\D", "", phone)


def _get_url() -> str:
    return f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages"


def _get_headers() -> dict:
    return {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }


def _post(payload: dict) -> Tuple[bool, str]:
    if not WHATSAPP_TOKEN:
        return False, "WHATSAPP token غير مضبوط."

    if not WHATSAPP_PHONE_NUMBER_ID:
        return False, "WHATSAPP_PHONE_NUMBER_ID غير مضبوط."

    try:
        response = requests.post(
            _get_url(),
            headers=_get_headers(),
            json=payload,
            timeout=30,
        )
        return response.status_code in (200, 201), response.text
    except Exception as e:
        return False, str(e)


def send_whatsapp_text_message(phone: str, message: str) -> Tuple[bool, str]:
    normalized_phone = normalize_egypt_phone(phone)

    if not normalized_phone:
        return False, "رقم الهاتف غير صالح."

    payload = {
        "messaging_product": "whatsapp",
        "to": normalized_phone,
        "type": "text",
        "text": {"body": message},
    }

    return _post(payload)


def send_whatsapp_template_message(
    phone: str,
    template_name: str,
    language_code: Optional[str] = None,
    body_params: Optional[List[str]] = None,
) -> Tuple[bool, str]:
    normalized_phone = normalize_egypt_phone(phone)

    if not normalized_phone:
        return False, "رقم الهاتف غير صالح."

    language_code = (language_code or WHATSAPP_TEMPLATE_LANG or "ar_EG").strip()

    components = []
    if body_params:
        components.append(
            {
                "type": "body",
                "parameters": [{"type": "text", "text": str(v)} for v in body_params],
            }
        )

    payload = {
        "messaging_product": "whatsapp",
        "to": normalized_phone,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language_code},
        },
    }

    if components:
        payload["template"]["components"] = components

    return _post(payload)


def send_whatsapp_message(phone: str, message: str) -> Tuple[bool, str]:
    return send_whatsapp_text_message(phone, message)


def send_welcome_template(phone: str) -> Tuple[bool, str]:
    return send_whatsapp_template_message(
        phone=phone,
        template_name="exam_welcome_ar",
        language_code=WHATSAPP_TEMPLATE_LANG,
        body_params=None,
    )


def send_exam_summary_template(
    phone: str,
    student_name: str,
    exam_name: str,
    score: str,
    total: str,
    percent: str,
    time_taken: str,
    correct_answers: str,
    wrong_answers: str,
) -> Tuple[bool, str]:
    return send_whatsapp_template_message(
        phone=phone,
        template_name="exam_summary_ar",
        language_code=WHATSAPP_TEMPLATE_LANG,
        body_params=[
            student_name,
            exam_name,
            score,
            total,
            percent,
            time_taken,
            correct_answers,
            wrong_answers,
        ],
    )


def send_hello_world_template(phone: str) -> Tuple[bool, str]:
    return send_whatsapp_template_message(
        phone=phone,
        template_name="hello_world",
        language_code="en_US",
        body_params=None,
    )