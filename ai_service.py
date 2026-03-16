import requests
from config import GEMINI_API_KEY


def generate_ai_explanation(subject: str, question: str, user_answer: str, correct_answer: str) -> str:
    if not GEMINI_API_KEY:
        return (
            f"شرح مختصر: في مادة {subject}، الإجابة الصحيحة هي ({correct_answer}) "
            f"بينما كانت إجابتك ({user_answer})."
        )

    prompt = f"""
    اشرح للطالب باللغة العربية بشكل مختصر جدًا ولمدة 2 أو 3 جمل فقط:
    المادة: {subject}
    السؤال: {question}
    إجابة الطالب: {user_answer}
    الإجابة الصحيحة: {correct_answer}

    المطلوب:
    - توضيح لماذا الإجابة الصحيحة صحيحة
    - توضيح الخطأ في إجابة الطالب إن وجد
    - بدون تطويل
    """.strip()

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    )
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    try:
        response = requests.post(url, json=payload, timeout=25)
        if response.status_code != 200:
            return (
                f"شرح مختصر: الإجابة الصحيحة هي ({correct_answer}) "
                f"وإجابتك كانت ({user_answer})."
            )

        data = response.json()
        candidates = data.get("candidates", [])
        if not candidates:
            return (
                f"شرح مختصر: الإجابة الصحيحة هي ({correct_answer}) "
                f"وإجابتك كانت ({user_answer})."
            )

        parts = candidates[0].get("content", {}).get("parts", [])
        text = "\n".join(part.get("text", "") for part in parts if part.get("text"))
        text = text.strip()

        if not text:
            return (
                f"شرح مختصر: الإجابة الصحيحة هي ({correct_answer}) "
                f"وإجابتك كانت ({user_answer})."
            )

        return text
    except Exception:
        return (
            f"شرح مختصر: الإجابة الصحيحة هي ({correct_answer}) "
            f"وإجابتك كانت ({user_answer})."
        )
