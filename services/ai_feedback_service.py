from typing import Any, Dict, List
from services.gemini_service import is_gemini_ready, generate_json

FEEDBACK_SCHEMA = {
    "type": "object",
    "properties": {
        "summary_ar": {"type": "string"},
        "mistakes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question":             {"type": "string"},
                    "user_answer":          {"type": "string"},
                    "correct_answer":       {"type": "string"},
                    "brief_explanation_ar": {"type": "string"},
                },
                "required": [
                    "question",
                    "user_answer",
                    "correct_answer",
                    "brief_explanation_ar",
                ],
            },
        },
    },
    "required": ["summary_ar", "mistakes"],
}

SYSTEM_INSTRUCTION = (
    "أنت مساعد تعليمي عربي داخل منصة امتحانات.\n"
    "المطلوب:\n"
    "- تلخيص أداء الطالب باختصار شديد.\n"
    "- شرح عربي بسيط جدًا لكل إجابة خاطئة.\n"
    "- لا تكتب إلا JSON مطابق للـ schema.\n"
    "- لا تخترع معلومات غير موجودة.\n"
)

_MAX_STR = 300


def _sanitize(value: Any) -> str:
    """منع Prompt Injection وتقليص القيم الطويلة."""
    return str(value or "").replace("\n", " ").replace("\r", " ").strip()[:_MAX_STR]


def _normalize_item(item: Dict[str, Any]) -> Dict[str, str]:
    """توحيد مفاتيح الـ dict سواء جاي من app.py أو من Gemini."""
    # app.py بيبعت "user"، Gemini بيرجع "user_answer"
    user_answer = item.get("user_answer") or item.get("user") or ""
    return {
        "question":             _sanitize(item.get("question", "")),
        "user_answer":          _sanitize(user_answer),
        "correct_answer":       _sanitize(item.get("correct_answer") or item.get("correct", "")),
        "brief_explanation_ar": str(item.get("brief_explanation_ar", "")).strip() or "لا يوجد شرح متاح.",
    }


def _fallback(mistakes: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "summary_ar": "تم إنهاء الامتحان، لكن الشرح الذكي غير متاح حاليًا.",
        "mistakes": [
            {**_normalize_item(item), "brief_explanation_ar": "الشرح الذكي غير متاح حاليًا."}
            for item in mistakes
        ],
    }


def generate_exam_feedback(
    subject: str,
    user_name: str,
    mistakes: List[Dict[str, Any]],
) -> Dict[str, Any]:
    if not mistakes:
        return {
            "summary_ar": "ممتاز، لا توجد إجابات خاطئة.",
            "mistakes": [],
        }

    if not is_gemini_ready():
        return _fallback(mistakes)

    # بناء الـ prompt مع sanitize لكل قيمة
    lines = [
        f"اسم الطالب: {_sanitize(user_name) or 'طالب'}",
        f"المادة: {_sanitize(subject) or 'التحول الرقمي'}",
        "",
        "اشرح الأخطاء التالية شرحًا عربيًا بسيطًا جدًا:",
        "",
    ]
    for i, item in enumerate(mistakes, start=1):
        norm = _normalize_item(item)
        lines.append(f"{i}) السؤال: {norm['question']}")
        lines.append(f"   إجابة الطالب: {norm['user_answer']}")
        lines.append(f"   الإجابة الصحيحة: {norm['correct_answer']}")
        lines.append("")

    # FIX: "\n" حقيقي مش "\\n"
    prompt = "\n".join(lines)

    result = generate_json(
        prompt=prompt,
        schema=FEEDBACK_SCHEMA,
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=0.2,
        max_output_tokens=4096,
    )

    if not isinstance(result, dict):
        return _fallback(mistakes)

    result.setdefault("summary_ar", "تم تحليل الإجابات الخاطئة.")
    result.setdefault("mistakes", [])

    result["mistakes"] = [_normalize_item(item) for item in result["mistakes"]]

    return result
