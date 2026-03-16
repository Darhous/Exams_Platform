import requests
from config import GEMINI_API_KEY

_GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent"
)
_MAX_CHARS = 600


def _fallback(correct_answer: str, user_answer: str) -> str:
    return (
        f"شرح مختصر: الإجابة الصحيحة هي ({correct_answer}) "
        f"وإجابتك كانت ({user_answer})."
    )


def _sanitize(value: str) -> str:
    """منع Prompt Injection بإزالة أي محاولة لتغيير التعليمات."""
    return str(value).replace("\n", " ").replace("\r", " ").strip()[:300]


def generate_ai_explanation(
    subject: str,
    question: str,
    user_answer: str,
    correct_answer: str,
) -> str:
    if not GEMINI_API_KEY:
        return _fallback(correct_answer, user_answer)

    # تنظيف المدخلات قبل إدراجها في الـ prompt
    s_subject   = _sanitize(subject)
    s_question  = _sanitize(question)
    s_user      = _sanitize(user_answer)
    s_correct   = _sanitize(correct_answer)

    prompt = (
        f"اشرح للطالب باللغة العربية في جملتين أو ثلاث فقط:\n"
        f"المادة: {s_subject}\n"
        f"السؤال: {s_question}\n"
        f"إجابة الطالب: {s_user}\n"
        f"الإجابة الصحيحة: {s_correct}\n"
        f"وضّح لماذا الإجابة الصحيحة صحيحة، وأين كان الخطأ إن وُجد، بدون تطويل."
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 200},  # حد أقصى للرد
    }

    try:
        response = requests.post(
            _GEMINI_URL,
            params={"key": GEMINI_API_KEY},
            json=payload,
            timeout=25,
        )
        response.raise_for_status()
        data = response.json()

        parts = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [])
        )
        text = "\n".join(p.get("text", "") for p in parts if p.get("text")).strip()

        if not text:
            return _fallback(correct_answer, user_answer)

        # قص الرد لو طويل أكتر من اللازم
        return text[:_MAX_CHARS] if len(text) > _MAX_CHARS else text

    except Exception:
        return _fallback(correct_answer, user_answer)
