from datetime import datetime

ADMIN_NAME = "darhous"
ADMIN_PHONE = "01030002331"

SUBJECTS = [
    "تكنولوجيا المعلومات",
    "معالج النصوص",
    "الجداول الإلكترونية",
    "العروض التقديمية",
    "قواعد البيانات",
    "تطبيقات الموبايل",
    "تطبيقات الويب",
    "الأمن السيبراني",
    "البحث عبر الإنترنت",
]

def normalize_name(name: str) -> str:
    return (name or "").strip()

def normalize_phone(phone: str) -> str:
    return (phone or "").strip().replace(" ", "")

def is_admin(name: str, phone: str) -> bool:
    return normalize_name(name).lower() == ADMIN_NAME and normalize_phone(phone) == ADMIN_PHONE

def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
