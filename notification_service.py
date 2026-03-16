from services.whatsapp_service import (
    send_welcome_template,
    send_exam_summary_template,
)


def send_welcome_notification(student_name: str, phone: str):
    return send_welcome_template(phone)


def send_exam_notifications(
    user_name: str,
    user_phone: str,
    subject: str,
    score: int,
    total: int,
    percent: float,
    time_str: str,
    warnings_count: int = 0,
    mistakes=None,
    failure_due_to_warnings: bool = False,
):
    mistakes = mistakes or []
    correct_answers = score
    wrong_answers = max(0, total - score)
    exam_name = "الامتحان" if not subject else subject

    return send_exam_summary_template(
        phone=user_phone,
        student_name=user_name,
        exam_name=exam_name,
        score=str(score),
        total=str(total),
        percent=str(percent),
        time_taken=str(time_str),
        correct_answers=str(correct_answers),
        wrong_answers=str(wrong_answers),
    )