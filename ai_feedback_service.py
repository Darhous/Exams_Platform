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
                    "question": {"type": "string"},
                    "user_answer": {"type": "string"},
                    "correct_answer": {"type": "string"},
                    "brief_explanation_ar": {"type": "string"}
                },
                "required": [
                    "question",
                    "user_answer",
                    "correct_answer",
                    "brief_explanation_ar"
                ]
            }
        }
    },
    "required": ["summary_ar", "mistakes"]
}

SYSTEM_INSTRUCTION = """
أنت مساعد تعليمي عربي داخل منصة امتحانات.
المطلوب:
- تلخيص أداء الطالب باختصار شديد.
- شرح عربي بسيط جدًا لكل إجابة خاطئة.
- لا تكتب إلا JSON مطابق للـ schema.
- لا تخترع معلومات غير موجودة.
"""

def _fallback(mistakes: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "summary_ar": "تم إنهاء الامتحان، لكن الشرح الذكي غير متاح حاليًا.",
        "mistakes": [
            {
                "question": str(item.get("question", "")),
                "user_answer": str(item.get("user_answer", "")),
                "correct_answer": str(item.get("correct_answer", "")),
                "brief_explanation_ar": "الشرح الذكي غير متاح حاليًا."
            }
            for item in mistakes
        ]
    }

def generate_exam_feedback(subject: str, user_name: str, mistakes: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not mistakes:
        return {
            "summary_ar": "ممتاز، لا توجد إجابات خاطئة.",
            "mistakes": []
        }

    if not is_gemini_ready():
        return _fallback(mistakes)

    prompt_lines = [
        f"اسم الطالب: {user_name or 'طالب'}",
        f"المادة: {subject or 'التحول الرقمي'}",
        "",
        "اشرح الأخطاء التالية شرحًا عربيًا بسيطًا جدًا:",
        ""
    ]

    for i, item in enumerate(mistakes, start=1):
        prompt_lines.append(f"{i}) السؤال: {item.get('question', '')}")
        prompt_lines.append(f"إجابة الطالب: {item.get('user_answer', '')}")
        prompt_lines.append(f"الإجابة الصحيحة: {item.get('correct_answer', '')}")
        prompt_lines.append("")

    result = generate_json(
        prompt="\\n".join(prompt_lines),
        schema=FEEDBACK_SCHEMA,
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=0.2,
        max_output_tokens=4096,
    )

    if not isinstance(result, dict):
        return _fallback(mistakes)

    result.setdefault("summary_ar", "تم تحليل الإجابات الخاطئة.")
    result.setdefault("mistakes", [])

    normalized = []
    for item in result.get("mistakes", []):
        normalized.append({
            "question": str(item.get("question", "")),
            "user_answer": str(item.get("user_answer", "")),
            "correct_answer": str(item.get("correct_answer", "")),
            "brief_explanation_ar": str(item.get("brief_explanation_ar", "")).strip() or "لا يوجد شرح متاح."
        })

    result["mistakes"] = normalized
    return result
