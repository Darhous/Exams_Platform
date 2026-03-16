from dotenv import load_dotenv
load_dotenv()

import html
import re
import time
import uuid
from pathlib import Path

import pandas as pd
import streamlit as st

from utils.db import (
    init_db,
    save_user,
    save_result,
    save_book,
    get_books_by_subject,
    fetch_questions,
    get_all_questions,
    delete_question,
    add_question,
    fetch_df,
    save_flag,
    stats_counts,
    execute,
)
from utils.helpers import is_admin, normalize_name, normalize_phone

# =========================
# Stable Service Imports
# =========================
from services.notification_service import (
    send_welcome_notification,
    send_exam_notifications,
)

try:
    from services.ai_feedback_service import generate_exam_feedback
except Exception:
    generate_exam_feedback = None

try:
    from services.telegram_service import send_telegram_alert
except Exception:
    send_telegram_alert = None

try:
    from services.ai_service import generate_ai_explanation
except Exception:
    generate_ai_explanation = None

try:
    from services.certificate_service import generate_certificate
except Exception:
    generate_certificate = None

try:
    from services.export_service import export_results_excel
except Exception:
    export_results_excel = None


# =========================
# Initial Setup
# =========================
init_db()
Path("books").mkdir(exist_ok=True)
Path("exports").mkdir(exist_ok=True)
Path("certificates").mkdir(exist_ok=True)

st.set_page_config(
    page_title="🛡️ منصة امتحانات التحول الرقمي - جامعة جنوب الوادي (المجموعة 205)",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =========================
# Subject Mapping
# =========================
SUBJECT_MAP = {
    "تكنولوجيا المعلومات": "IT",
    "معالج النصوص": "Word",
    "الجداول الإلكترونية": "Excel",
    "العروض التقديمية": "PowerPoint",
    "قواعد البيانات": "Access",
    "تطبيقات الموبايل": "Mobile",
    "تطبيقات الويب": "WebApps",
    "الأمن السيبراني": "CyberSecurity",
    "البحث عبر الإنترنت": "InternetSearch",
}
DISPLAY_SUBJECTS = list(SUBJECT_MAP.keys())
REVERSE_SUBJECT_MAP = {v: k for k, v in SUBJECT_MAP.items()}


# =========================
# Premium UI Theme
# =========================
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&display=swap');

:root{
    --primary:#0f2f63;
    --primary-2:#1a56b0;
    --secondary:#0f7a7d;
    --accent:#5b8cff;
    --success:#169b62;
    --warning:#d99108;
    --danger:#d13f52;
    --text:#11233b;
    --muted:#68788f;
    --card:#ffffff;
    --border:#e2ebf7;
    --soft:#f3f7ff;
    --soft-2:#edf4ff;
    --soft-3:#f9fbff;
    --shadow:0 16px 44px rgba(15,47,99,.08);
    --shadow-soft:0 10px 30px rgba(17,35,59,.05);
}

html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
    direction: rtl;
    text-align: right;
    font-family: 'Cairo', sans-serif !important;
    color: var(--text);
}

.stApp {
    background:
        radial-gradient(circle at top right, rgba(26,86,176,0.12), transparent 28%),
        radial-gradient(circle at bottom left, rgba(15,122,125,0.11), transparent 30%),
        linear-gradient(135deg, #f8fbff 0%, #eef5ff 52%, #fbfdff 100%);
}

.block-container {
    max-width: 1460px;
    padding-top: 1rem;
    padding-bottom: 2rem;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.main-hero {
    background:
        linear-gradient(135deg, rgba(15,47,99,0.98) 0%, rgba(26,86,176,0.96) 56%, rgba(15,122,125,0.90) 100%);
    color: white;
    border-radius: 32px;
    padding: 38px 32px 30px 32px;
    box-shadow: 0 24px 64px rgba(15,47,99,0.22);
    margin-bottom: 20px;
    overflow: hidden;
    position: relative;
}

.main-hero:before {
    content: "";
    position: absolute;
    left: -90px;
    top: -90px;
    width: 240px;
    height: 240px;
    background: rgba(255,255,255,0.08);
    border-radius: 50%;
}

.main-hero:after {
    content: "";
    position: absolute;
    right: -70px;
    bottom: -70px;
    width: 190px;
    height: 190px;
    background: rgba(255,255,255,0.08);
    border-radius: 50%;
}

.hero-title{
    font-size: 35px;
    font-weight: 900;
    margin-bottom: 8px;
    position: relative;
    z-index: 2;
}

.hero-subtitle{
    font-size: 15px;
    font-weight: 600;
    opacity: .98;
    position: relative;
    z-index: 2;
    line-height: 1.9;
}

.hero-badge-row{
    display:flex;
    gap:10px;
    flex-wrap:wrap;
    margin-top:16px;
    position: relative;
    z-index: 2;
}

.hero-badge{
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.18);
    color:#fff;
    border-radius:999px;
    padding:8px 14px;
    font-size:13px;
    font-weight:800;
}

.glass-entry {
    background: rgba(255,255,255,.84);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,.6);
    border-radius: 32px;
    padding: 40px;
    box-shadow: 0 20px 72px rgba(15,47,99,.10);
}

.section-card {
    background: rgba(255,255,255,.97);
    border: 1px solid var(--border);
    border-radius: 26px;
    padding: 24px;
    box-shadow: var(--shadow);
    margin-bottom: 18px;
}

.section-card-soft {
    background: linear-gradient(135deg, rgba(255,255,255,.98) 0%, rgba(244,248,255,.98) 100%);
    border: 1px solid var(--border);
    border-radius: 28px;
    padding: 24px;
    box-shadow: var(--shadow);
    margin-bottom: 18px;
}

.section-title {
    color: var(--text);
    font-size: 24px;
    font-weight: 900;
    margin-bottom: 6px;
}

.section-subtitle {
    color: var(--muted);
    font-size: 14px;
    font-weight: 700;
    margin-bottom: 12px;
    line-height: 1.9;
}

.metric-box {
    background: linear-gradient(135deg, #ffffff 0%, #f7fbff 100%);
    border: 1px solid var(--border);
    border-radius: 24px;
    padding: 20px 18px;
    box-shadow: var(--shadow-soft);
    margin-bottom: 10px;
}

.metric-title{
    color: var(--muted);
    font-size: 13px;
    font-weight: 800;
    margin-bottom: 8px;
}

.metric-value{
    color: var(--text);
    font-size: 28px;
    font-weight: 900;
    line-height: 1.2;
}

.metric-note{
    color: var(--primary-2);
    font-size: 12px;
    font-weight: 800;
    margin-top: 6px;
}

.info-strip {
    background: linear-gradient(135deg, #ffffff 0%, #f3f8ff 100%);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 16px 18px;
    margin-bottom: 18px;
    box-shadow: 0 8px 24px rgba(16,24,40,.04);
}

.info-chip-row{
    display:flex;
    gap:10px;
    flex-wrap:wrap;
}

.info-chip{
    background:#ecf4ff;
    color:var(--primary);
    padding:8px 14px;
    border-radius:999px;
    font-size:13px;
    font-weight:900;
    border:1px solid #dbe8ff;
}

.exam-head {
    background: linear-gradient(135deg, rgba(15,47,99,0.98) 0%, rgba(26,86,176,0.95) 100%);
    color: white;
    border-radius: 24px;
    padding: 24px;
    box-shadow: 0 16px 48px rgba(15,47,99,.18);
    margin-bottom: 16px;
}

.exam-title{
    font-size: 28px;
    font-weight: 900;
    margin-bottom: 8px;
}

.exam-chip-row{
    display:flex;
    gap:10px;
    flex-wrap:wrap;
    margin-top:12px;
}

.exam-chip{
    background: rgba(255,255,255,.15);
    color:white;
    border:1px solid rgba(255,255,255,.18);
    border-radius:999px;
    padding:8px 12px;
    font-size:13px;
    font-weight:900;
}

.question-card {
    background: rgba(255,255,255,.99);
    border-radius: 22px;
    border: 1px solid var(--border);
    padding: 22px;
    box-shadow: var(--shadow-soft);
    margin-bottom: 16px;
}

.question-index {
    display:inline-block;
    background: #edf4ff;
    color: var(--primary);
    border:1px solid #dbe8ff;
    padding: 7px 12px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 900;
    margin-bottom: 10px;
}

.question-title {
    color: var(--text);
    font-size: 20px;
    font-weight: 900;
    margin-bottom: 8px;
    line-height: 1.9;
}

.question-meta {
    color: var(--muted);
    font-size: 13px;
    font-weight: 700;
    margin-bottom: 12px;
}

.library-book{
    background: linear-gradient(135deg, #ffffff 0%, #f7fbff 100%);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0 8px 22px rgba(16,24,40,.04);
    margin-bottom: 12px;
}

.admin-danger{
    background: #fff6f6;
    border:1px solid #ffd8d8;
    border-radius:24px;
    padding:22px;
}

.admin-note{
    color:var(--muted);
    font-size:13px;
    font-weight:700;
}

.small-muted{
    color: var(--muted);
    font-size: 13px;
    font-weight: 700;
}

.input-note{
    color:#6a7a92;
    font-size:12px;
    font-weight:700;
    margin-top:-8px;
    margin-bottom:8px;
    line-height: 1.8;
}

.phone-valid{
    color: var(--success);
    font-size: 12px;
    font-weight: 800;
    margin-top: -6px;
    margin-bottom: 8px;
}

.phone-invalid{
    color: var(--danger);
    font-size: 12px;
    font-weight: 800;
    margin-top: -6px;
    margin-bottom: 8px;
}

.login-help-text{
    margin-top: -4px;
    margin-bottom: 14px;
    color: #6a7a92;
    font-size: 13px;
    font-weight: 800;
    line-height: 1.9;
}

.dev-credit{
    margin-top: 16px;
    text-align: center;
    color: var(--muted);
    font-size: 13px;
    font-weight: 700;
    line-height: 1.9;
}

.dev-credit a{
    color: var(--primary-2) !important;
    text-decoration: none !important;
    font-weight: 900;
}

.dev-credit a:hover{
    text-decoration: underline !important;
}

.result-shell{
    margin-top: 18px;
    margin-bottom: 14px;
}

.result-hero{
    background: linear-gradient(135deg, #0f172a 0%, #163264 45%, #1a56b0 100%);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 28px;
    padding: 30px 24px;
    color: #ffffff;
    box-shadow: 0 18px 45px rgba(15, 23, 42, 0.22);
    margin-bottom: 18px;
}

.result-hero-title{
    font-size: 31px;
    font-weight: 900;
    margin-bottom: 10px;
    text-align: center;
}

.result-hero-subtitle{
    font-size: 15px;
    opacity: 0.96;
    text-align: center;
    line-height: 2;
}

.status-badge{
    display:inline-block;
    margin-top:14px;
    padding:8px 16px;
    border-radius:999px;
    font-size:13px;
    font-weight:900;
}

.status-pass{
    background: rgba(22, 163, 74, 0.16);
    color: #dcfce7;
    border: 1px solid rgba(220,252,231,0.20);
}

.status-fail{
    background: rgba(220, 38, 38, 0.18);
    color: #fee2e2;
    border: 1px solid rgba(254,226,226,0.20);
}

.result-grid{
    display:grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap:14px;
    margin: 18px 0 14px 0;
}

.result-stat-card{
    background: rgba(255,255,255,.98);
    border: 1px solid var(--border);
    border-radius: 22px;
    padding: 18px 16px;
    box-shadow: var(--shadow-soft);
    text-align: center;
}

.result-stat-label{
    font-size: 13px;
    color: var(--muted);
    font-weight: 800;
    margin-bottom: 8px;
}

.result-stat-value{
    font-size: 28px;
    color: var(--text);
    font-weight: 900;
    line-height: 1.3;
}

.result-stat-note{
    margin-top: 6px;
    font-size: 12px;
    color: #8a9ab0;
    font-weight: 700;
}

.summary-panel{
    background: #ffffff;
    border: 1px solid var(--border);
    border-radius: 24px;
    padding: 22px 20px;
    box-shadow: var(--shadow-soft);
    margin-top: 12px;
    margin-bottom: 16px;
}

.summary-title{
    font-size: 22px;
    font-weight: 900;
    color: var(--text);
    margin-bottom: 10px;
}

.summary-text{
    font-size: 15px;
    line-height: 2;
    color: #334155;
    font-weight: 700;
}

.mistakes-box{
    background: #ffffff;
    border: 1px solid #ffe1e1;
    border-radius: 24px;
    padding: 20px;
    margin-top: 16px;
    box-shadow: var(--shadow-soft);
}

.mistakes-title{
    font-size: 21px;
    font-weight: 900;
    color: #b91c1c;
    margin-bottom: 14px;
}

.mistake-item{
    border: 1px solid var(--border);
    border-right: 5px solid var(--danger);
    border-radius: 18px;
    padding: 16px;
    margin-bottom: 12px;
    background: #fcfcfd;
}

.mistake-q{
    font-weight: 900;
    color: var(--text);
    margin-bottom: 8px;
    line-height: 1.9;
}

.mistake-a{
    color: #475569;
    line-height: 1.95;
    margin-bottom: 4px;
    font-size: 14px;
    font-weight: 700;
}

.ai-feedback-box{
    background: linear-gradient(135deg, #ffffff 0%, #f6faff 100%);
    border: 1px solid var(--border);
    border-radius: 24px;
    padding: 22px;
    box-shadow: var(--shadow-soft);
    margin-top: 18px;
}

.ai-feedback-title{
    font-size: 21px;
    font-weight: 900;
    color: var(--text);
    margin-bottom: 10px;
}

.ai-feedback-summary{
    color: #334155;
    font-size: 15px;
    line-height: 2;
    font-weight: 700;
    margin-bottom: 14px;
}

.ai-feedback-item{
    border: 1px solid #dde8f7;
    border-radius: 18px;
    padding: 16px;
    margin-bottom: 12px;
    background: #ffffff;
}

hr.pretty {
    border: none;
    height: 1px;
    background: linear-gradient(to left, transparent, #d9e4f7, transparent);
    margin: 18px 0 14px 0;
}

div.stButton > button,
div.stDownloadButton > button,
div.stFormSubmitButton > button {
    width: 100%;
    border: none;
    border-radius: 14px;
    padding: 12px 18px;
    font-weight: 900;
    font-size: 15px;
    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-2) 100%);
    color: white;
    box-shadow: 0 10px 24px rgba(26,86,176,.24);
    transition: all .22s ease;
}

div.stButton > button:hover,
div.stDownloadButton > button:hover,
div.stFormSubmitButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 14px 30px rgba(26,86,176,.28);
}

.stTabs [data-baseweb="tab-list"] {
    gap: 10px;
    background: rgba(255,255,255,.74);
    padding: 10px;
    border-radius: 20px;
    border: 1px solid var(--border);
    box-shadow: 0 10px 28px rgba(16,24,40,.04);
    margin-bottom: 18px;
}

.stTabs [data-baseweb="tab"] {
    background: white;
    border-radius: 14px;
    padding: 10px 16px;
    font-weight: 900;
    color: var(--text);
    border: 1px solid var(--border);
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-2) 100%) !important;
    color: white !important;
    border: none !important;
}

.stProgress > div > div > div > div {
    background: linear-gradient(135deg, var(--primary-2), var(--secondary));
}

[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    border-radius: 14px !important;
    border: 1px solid #dbe6f5 !important;
    background: #fbfdff !important;
}

[data-testid="stNumberInput"] input {
    border-radius: 14px !important;
}

h1,h2,h3,h4,h5 {
    color: var(--text);
    font-weight: 900 !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# =========================
# Session State Defaults
# =========================
defaults = {
    "entered": False,
    "user_name": "",
    "user_phone": "",
    "is_admin": False,
    "test_active": False,
    "test_data": None,
    "test_subject": "",
    "test_subject_code": "",
    "start_time": None,
    "warnings_count": 0,
    "submitted": False,
    "last_score": None,
    "last_total": None,
    "last_percent": None,
    "last_time": None,
    "last_mistakes": [],
    "ai_feedback": None,
    "mistake_explanations": {},
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# =========================
# Helpers
# =========================
def safe_text(value):
    return html.escape(str(value)) if value is not None else ""


def render_metric_box(title: str, value: str, note: str = ""):
    st.markdown(
        f"""
        <div class="metric-box">
            <div class="metric-title">{safe_text(title)}</div>
            <div class="metric-value">{safe_text(value)}</div>
            <div class="metric-note">{safe_text(note)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_elapsed(start_time):
    elapsed = max(0, int(time.time() - start_time))
    mins, secs = divmod(elapsed, 60)
    return elapsed, f"{mins} دقيقة و {secs} ثانية"


def normalize_subject_label(value):
    value = str(value).strip() if value is not None else ""
    if value in REVERSE_SUBJECT_MAP:
        return REVERSE_SUBJECT_MAP[value]
    if value in SUBJECT_MAP:
        return value
    return value


def normalize_subject_code(value):
    value = str(value).strip() if value is not None else ""
    if value in SUBJECT_MAP:
        return SUBJECT_MAP[value]
    return value


def localize_subject_column(df, col_name="subject"):
    if df is None or df.empty or col_name not in df.columns:
        return df
    new_df = df.copy()
    new_df[col_name] = new_df[col_name].apply(normalize_subject_label)
    return new_df


def clear_exam_answers():
    answer_keys = [k for k in st.session_state.keys() if str(k).startswith("answer_")]
    flag_keys = [k for k in st.session_state.keys() if str(k).startswith("flag_note_")]
    for k in answer_keys + flag_keys:
        del st.session_state[k]


def reset_test_state():
    clear_exam_answers()
    st.session_state["test_active"] = False
    st.session_state["test_data"] = None
    st.session_state["test_subject"] = ""
    st.session_state["test_subject_code"] = ""
    st.session_state["start_time"] = None
    st.session_state["warnings_count"] = 0
    st.session_state["submitted"] = False


def reset_last_result():
    st.session_state["submitted"] = False
    st.session_state["last_score"] = None
    st.session_state["last_total"] = None
    st.session_state["last_percent"] = None
    st.session_state["last_time"] = None
    st.session_state["last_mistakes"] = []
    st.session_state["ai_feedback"] = None
    st.session_state["mistake_explanations"] = {}


def get_user_results(name, phone):
    df = fetch_df(
        "SELECT * FROM results WHERE user_name=? AND user_phone=? ORDER BY test_date DESC",
        (name, phone),
    )
    return localize_subject_column(df, "subject")


def get_dashboard_summary():
    user_results = get_user_results(
        st.session_state["user_name"],
        st.session_state["user_phone"],
    )
    total_attempts = len(user_results)
    avg_percent = round(float(user_results["percent"].mean()), 2) if not user_results.empty else 0
    last_percent = float(user_results.iloc[0]["percent"]) if not user_results.empty else 0
    return total_attempts, avg_percent, last_percent, user_results


def get_all_books():
    books_df = fetch_df("SELECT * FROM books ORDER BY created_at DESC")
    return localize_subject_column(books_df, "subject")


def render_result_section():
    if not (st.session_state.get("submitted") and st.session_state.get("last_score") is not None):
        return

    score = st.session_state["last_score"]
    total = st.session_state["last_total"]
    percent = st.session_state["last_percent"]
    time_str = st.session_state["last_time"]
    mistakes = st.session_state.get("last_mistakes", [])
    passed = float(percent) >= 50 if isinstance(percent, (int, float)) else False
    correct_count = score
    wrong_count = max(0, total - score)
    warning_count = st.session_state.get("warnings_count", 0)

    if time_str == "تم إنهاء الاختبار بسبب التحذيرات":
        summary_text = (
            f"تم إيقاف اختبار {st.session_state.get('test_subject', 'الامتحان')} بسبب الوصول إلى الحد الأقصى من التحذيرات. "
            "يرجى الالتزام بالتعليمات في المحاولة القادمة."
        )
    elif passed:
        summary_text = (
            f"أداء ممتاز يا {st.session_state.get('user_name', 'الطالب')}. "
            f"لقد حققت {score} من {total} بنسبة {percent}% "
            f"وأجبت بشكل صحيح على {correct_count} سؤال خلال {time_str}."
        )
    else:
        summary_text = (
            f"تم الانتهاء من {st.session_state.get('test_subject', 'الامتحان')}. "
            f"حصلت على {score} من {total} بنسبة {percent}% خلال {time_str}. "
            "يمكنك مراجعة الأخطاء والشرح المبسط بالأسفل لتحسين مستواك في المحاولة القادمة."
        )

    status_html = (
        '<div class="status-badge status-pass">✅ تم اجتياز الامتحان بنجاح</div>'
        if passed and time_str != "تم إنهاء الاختبار بسبب التحذيرات"
        else '<div class="status-badge status-fail">❌ لم يتم اجتياز الامتحان</div>'
    )

    st.markdown('<div class="result-shell">', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="result-hero">
            <div class="result-hero-title">النتيجة النهائية</div>
            <div class="result-hero-subtitle">
                تهانينا <strong>{safe_text(st.session_state.get("user_name", "الطالب"))}</strong><br>
                تم الانتهاء من امتحان <strong>{safe_text(st.session_state.get("test_subject", "الامتحان"))}</strong>
                ويمكنك الآن مراجعة الملخص النهائي بالتفصيل.
                <br>{status_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="result-grid">
            <div class="result-stat-card">
                <div class="result-stat-label">الدرجة</div>
                <div class="result-stat-value">{safe_text(f"{score}/{total}")}</div>
                <div class="result-stat-note">إجمالي الأسئلة</div>
            </div>
            <div class="result-stat-card">
                <div class="result-stat-label">النسبة المئوية</div>
                <div class="result-stat-value">{safe_text(f"{percent}%")}</div>
                <div class="result-stat-note">مستوى الأداء</div>
            </div>
            <div class="result-stat-card">
                <div class="result-stat-label">إجابات صحيحة</div>
                <div class="result-stat-value">{safe_text(correct_count)}</div>
                <div class="result-stat-note">عدد الإجابات الصحيحة</div>
            </div>
            <div class="result-stat-card">
                <div class="result-stat-label">إجابات خاطئة</div>
                <div class="result-stat-value">{safe_text(wrong_count)}</div>
                <div class="result-stat-note">عدد الإجابات الخاطئة</div>
            </div>
            <div class="result-stat-card">
                <div class="result-stat-label">الوقت المستغرق</div>
                <div class="result-stat-value">{safe_text(time_str)}</div>
                <div class="result-stat-note">مدة أداء الاختبار</div>
            </div>
            <div class="result-stat-card">
                <div class="result-stat-label">التحذيرات</div>
                <div class="result-stat-value">{safe_text(warning_count)}</div>
                <div class="result-stat-note">عدد التحذيرات المسجلة</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="summary-panel">
            <div class="summary-title">الملخص النهائي</div>
            <div class="summary-text">{safe_text(summary_text)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if (
        st.session_state["test_subject"] == "امتحان شامل"
        and percent >= 80
        and time_str != "تم إنهاء الاختبار بسبب التحذيرات"
    ):
        if generate_certificate is not None:
            cert_path = generate_certificate(st.session_state["user_name"], percent, score, total)
            st.success("🏅 مبروك! لقد اجتزت الامتحان المجمع ويمكنك تحميل شهادة الاجتياز.")
            with open(cert_path, "rb") as f:
                st.download_button(
                    "⬇️ تحميل الشهادة PDF",
                    data=f,
                    file_name=Path(cert_path).name,
                    mime="application/pdf",
                    key=f"cert_{int(time.time())}",
                )
        else:
            st.info("خدمة إنشاء الشهادة غير متاحة حالياً.")

    if mistakes:
        st.markdown('<div class="mistakes-box">', unsafe_allow_html=True)
        st.markdown('<div class="mistakes-title">مراجعة الإجابات غير الصحيحة</div>', unsafe_allow_html=True)

        for m in mistakes:
            cache_key = f"{m['id']}::{m['user']}::{m['correct']}"
            ai_exp = get_mistake_explanation(
                m["subject"],
                m["question"],
                m["user"],
                m["correct"],
                cache_key,
            )

            st.markdown(
                f"""
                <div class="mistake-item">
                    <div class="mistake-q">{safe_text(m['question'])}</div>
                    <div class="mistake-a"><strong>إجابتك:</strong> {safe_text(m['user'])}</div>
                    <div class="mistake-a"><strong>الإجابة الصحيحة:</strong> {safe_text(m['correct'])}</div>
                    <div class="mistake-a"><strong>شرح مبسط:</strong> {safe_text(ai_exp)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.balloons()
        st.success("ممتاز جدًا! إجاباتك كلها صحيحة بدون أي أخطاء.")

    if st.session_state.get("ai_feedback") is None:
        try:
            ai_feedback = build_ai_exam_feedback(
                subject=st.session_state.get("test_subject", "التحول الرقمي"),
                user_name=st.session_state.get("user_name", "طالب"),
                mistakes=mistakes,
            )
            st.session_state["ai_feedback"] = ai_feedback
        except Exception as e:
            print("AI feedback hook failed:", e)
            st.session_state["ai_feedback"] = {
                "summary_ar": "تعذر إنشاء التغذية الراجعة الذكية.",
                "mistakes": []
            }

    c1, _ = st.columns([1.2, 4])
    with c1:
        if st.button("مسح النتيجة من الشاشة", key="clear_last_result"):
            reset_last_result()
            clear_exam_answers()
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.get("ai_feedback"):
        ai_feedback = st.session_state["ai_feedback"]
        st.markdown('<div class="ai-feedback-box">', unsafe_allow_html=True)
        st.markdown('<div class="ai-feedback-title">🤖 شرح مبسط وتحليل ذكي للأداء</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="ai-feedback-summary">{safe_text(ai_feedback.get("summary_ar", ""))}</div>',
            unsafe_allow_html=True,
        )

        for idx, item in enumerate(ai_feedback.get("mistakes", []), start=1):
            st.markdown(
                f"""
                <div class="ai-feedback-item">
                    <div class="mistake-q">{idx}) {safe_text(item.get('question', ''))}</div>
                    <div class="mistake-a"><strong>إجابتك:</strong> {safe_text(item.get('user_answer', ''))}</div>
                    <div class="mistake-a"><strong>الإجابة الصحيحة:</strong> {safe_text(item.get('correct_answer', ''))}</div>
                    <div class="mistake-a"><strong>الشرح:</strong> {safe_text(item.get('brief_explanation_ar', ''))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)


def count_answered_questions(df_questions):
    answered = 0
    for _, row in df_questions.iterrows():
        qid = int(row["id"])
        if st.session_state.get(f"answer_{qid}") not in [None, ""]:
            answered += 1
    return answered


def normalize_phone_live(phone: str) -> str:
    return re.sub(r"[^0-9]", "", str(phone or ""))[:11]


def validate_phone_input(phone: str):
    cleaned = normalize_phone_live(normalize_phone(phone))
    if not cleaned:
        return False, "يرجى كتابة رقم التليفون."
    if not cleaned.isdigit():
        return False, "رقم التليفون يجب أن يحتوي على أرقام فقط."
    if len(cleaned) != 11:
        return False, "رقم التليفون يجب أن يكون 11 رقمًا بالضبط."
    if not cleaned.startswith("01"):
        return False, "رقم التليفون يجب أن يبدأ بـ 01."
    return True, cleaned


def build_ai_exam_feedback(subject: str, user_name: str, mistakes: list):
    if generate_exam_feedback is None:
        return {
            "summary_ar": "الملخص الذكي غير متاح حالياً.",
            "mistakes": []
        }

    try:
        return generate_exam_feedback(
            subject=subject,
            user_name=user_name,
            mistakes=mistakes,
        )
    except Exception as e:
        print("Gemini feedback generation failed:", e)
        return {
            "summary_ar": "حدث خطأ أثناء إنشاء الملخص الذكي.",
            "mistakes": []
        }


def get_mistake_explanation(subject, question, user_answer, correct_answer, cache_key):
    cached = st.session_state.get("mistake_explanations", {})
    if cache_key in cached:
        return cached[cache_key]

    if generate_ai_explanation is None:
        explanation = "الشرح الذكي غير متاح حالياً."
    else:
        try:
            explanation = generate_ai_explanation(subject, question, user_answer, correct_answer)
        except Exception:
            explanation = "تعذر إنشاء شرح ذكي لهذه الإجابة حالياً."

    cached[cache_key] = explanation
    st.session_state["mistake_explanations"] = cached
    return explanation


def send_login_whatsapp_message():
    user_name = st.session_state.get("user_name", "")
    user_phone = st.session_state.get("user_phone", "")

    try:
        result = send_welcome_notification(user_name, user_phone)
        print("send_welcome_notification result:", result)
        return result
    except Exception as e:
        print("send_welcome_notification failed:", e)
        return False, str(e)


def start_exam(test_df, subject_label, subject_code):
    clear_exam_answers()
    reset_last_result()
    st.session_state["test_data"] = test_df.copy()
    st.session_state["test_subject"] = subject_label
    st.session_state["test_subject_code"] = subject_code
    st.session_state["start_time"] = time.time()
    st.session_state["test_active"] = True
    st.session_state["warnings_count"] = 0
    st.session_state["submitted"] = False


def send_exam_summary_to_admin(score, total, percent, time_str):
    if send_telegram_alert is None:
        return

    alert_text = (
        f"تنبيه جديد من منصة الامتحانات\n"
        f"الطالب: {st.session_state['user_name']}\n"
        f"الهاتف: {st.session_state['user_phone']}\n"
        f"المادة: {st.session_state['test_subject']}\n"
        f"النتيجة: {score}/{total} ({percent}%)\n"
        f"الوقت: {time_str}\n"
        f"التحذيرات: {st.session_state.get('warnings_count', 0)}"
    )
    try:
        send_telegram_alert(alert_text)
    except Exception:
        pass


def send_student_exam_notifications(score, total, percent, time_str, mistakes, failure_due_to_warnings=False):
    try:
        result = send_exam_notifications(
            user_name=st.session_state["user_name"],
            user_phone=st.session_state["user_phone"],
            subject=st.session_state["test_subject"],
            score=score,
            total=total,
            percent=percent,
            time_str=time_str,
            warnings_count=st.session_state.get("warnings_count", 0),
            mistakes=mistakes,
            failure_due_to_warnings=failure_due_to_warnings,
        )
        print("send_exam_notifications result:", result)
        return result
    except Exception as e:
        print("send_exam_notifications failed:", e)
        return False, str(e)


def submit_exam(df_questions):
    if st.session_state.get("submitted"):
        return

    if st.session_state.get("start_time") is None:
        st.error("تعذر تسليم الاختبار لأن وقت البدء غير متوفر.")
        return

    _, time_str = format_elapsed(st.session_state["start_time"])
    score = 0
    mistakes = []

    for _, row in df_questions.iterrows():
        qid = int(row["id"])
        correct = str(row["correct_answer"]).strip()
        user_ans = st.session_state.get(f"answer_{qid}")

        if user_ans == correct:
            score += 1
        else:
            mistakes.append(
                {
                    "id": qid,
                    "subject": normalize_subject_label(row["subject"]),
                    "question": row["question"],
                    "user": user_ans if user_ans else "لم يجب",
                    "correct": correct,
                }
            )

    total = len(df_questions)
    percent = round((score / total) * 100, 2) if total else 0.0

    save_result(
        st.session_state["user_name"],
        st.session_state["user_phone"],
        st.session_state["test_subject"],
        score,
        total,
        percent,
        time_str,
        st.session_state.get("warnings_count", 0),
    )

    send_exam_summary_to_admin(score, total, percent, time_str)
    send_student_exam_notifications(score, total, percent, time_str, mistakes, failure_due_to_warnings=False)

    st.session_state["last_score"] = score
    st.session_state["last_total"] = total
    st.session_state["last_percent"] = percent
    st.session_state["last_time"] = time_str
    st.session_state["last_mistakes"] = mistakes
    st.session_state["submitted"] = True
    st.session_state["test_active"] = False


# =========================
# Entry Screen
# =========================
if not st.session_state["entered"]:
    c1, c2, c3 = st.columns([1, 1.45, 1])

    with c2:
        st.markdown(
            """
            <div class="main-hero">
                <div class="hero-title">🛡️ منصة امتحانات التحول الرقمي - جامعة جنوب الوادي (المجموعة 205)</div>
                <div class="hero-subtitle">
                    منصة حديثة للاختبارات الإلكترونية، المتابعة الدقيقة، وإظهار النتائج بشكل فوري واحترافي.
                </div>
                <div class="hero-badge-row">
                    <div class="hero-badge">واجهة راقية</div>
                    <div class="hero-badge">نتائج فورية</div>
                    <div class="hero-badge">اختبارات متنوعة</div>
                    <div class="hero-badge">مكتبة رقمية</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="glass-entry">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">الدخول إلى المنصة</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-subtitle">اكتب الاسم ورقم التليفون بشكل صحيح للدخول إلى المنصة ومتابعة الاختبارات والنتائج.</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="login-help-text">اكتب رقم التليفون من 11 رقمًا بالأرقام فقط مثل: 01012345678</div>',
            unsafe_allow_html=True,
        )

        with st.form("entry_form", clear_on_submit=False):
            name = st.text_input("👤 الاسم", placeholder="اكتب الاسم هنا")
            phone = st.text_input(
                "📱 رقم التليفون",
                placeholder="اكتب رقم التليفون هنا",
                max_chars=11,
            )

            live_phone = normalize_phone_live(phone)
            if phone and live_phone != phone:
                st.markdown(
                    '<div class="phone-invalid">يُسمح بكتابة الأرقام فقط، وتم حذف أي رموز أو حروف غير صالحة تلقائيًا.</div>',
                    unsafe_allow_html=True,
                )
            elif phone and len(live_phone) < 11:
                st.markdown(
                    '<div class="phone-invalid">رقم التليفون يجب أن يكون 11 رقمًا.</div>',
                    unsafe_allow_html=True,
                )
            elif len(live_phone) == 11:
                st.markdown(
                    '<div class="phone-valid">✅ رقم التليفون مكتمل وجاهز للدخول.</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<div class="input-note">سيتم قبول الأرقام فقط، ويجب أن يبدأ الرقم بـ 01 وأن يكون مكونًا من 11 رقمًا.</div>',
                    unsafe_allow_html=True,
                )

            submitted = st.form_submit_button("دخول المنصة")

            if submitted:
                clean_name = normalize_name(name)
                ok_phone, phone_result = validate_phone_input(phone)

                if not clean_name:
                    st.error("يرجى كتابة الاسم.")
                elif not ok_phone:
                    st.error(phone_result)
                else:
                    clean_phone = phone_result
                    admin_state = is_admin(clean_name, clean_phone)

                    reset_test_state()
                    reset_last_result()

                    st.session_state["entered"] = True
                    st.session_state["user_name"] = clean_name
                    st.session_state["user_phone"] = clean_phone
                    st.session_state["is_admin"] = admin_state

                    save_user(clean_name, clean_phone, admin_state)
                    send_login_whatsapp_message()
                    st.rerun()

        st.markdown(
            """
            <div class="dev-credit">
                تم تطوير المنصة بمعرفة
                <a href="mailto:ahmeddarhous@gmail.com?subject=استفسار%20بخصوص%20منصة%20الامتحانات">
                    أحمد درهوس 01030002331
                </a>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.stop()


# =========================
# Top Header
# =========================
role_text = "مدير النظام" if st.session_state["is_admin"] else "طالب"
role_emoji = "🛡️" if st.session_state["is_admin"] else "🎓"

top_left, top_right = st.columns([6, 1.3])

with top_left:
    st.markdown(
        f"""
        <div class="main-hero">
            <div class="hero-title">🛡️ منصة امتحانات التحول الرقمي - جامعة جنوب الوادي (المجموعة 205)</div>
            <div class="hero-subtitle">
                مرحباً <b>{safe_text(st.session_state["user_name"])}</b>
                — الحالة: <b>{role_text}</b>
                — رقم التليفون: <b>{safe_text(st.session_state["user_phone"])}</b>
            </div>
            <div class="hero-badge-row">
                <div class="hero-badge">جامعة جنوب الوادي</div>
                <div class="hero-badge">نتائج محفوظة</div>
                <div class="hero-badge">تقييم لحظي</div>
                <div class="hero-badge">مراجعة الأخطاء</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with top_right:
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    if st.button("تسجيل خروج"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


# =========================
# Info Strip
# =========================
attempts_count, avg_percent, last_percent, user_results_df = get_dashboard_summary()
st.markdown(
    f"""
    <div class="info-strip">
        <div class="info-chip-row">
            <div class="info-chip">👤 المستخدم: {safe_text(st.session_state["user_name"])}</div>
            <div class="info-chip">📱 الهاتف: {safe_text(st.session_state["user_phone"])}</div>
            <div class="info-chip">📊 محاولاتك: {attempts_count}</div>
            <div class="info-chip">📈 متوسطك: {avg_percent}%</div>
            <div class="info-chip">⭐ آخر نتيجة: {last_percent}%</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================
# Tabs
# =========================
if st.session_state["is_admin"]:
    tabs = st.tabs(
        [
            "📊 لوحة الإدارة",
            "⚙️ إدارة النظام",
            "📚 اختبار المواد",
            "🏆 الامتحان المجمع",
            "📥 المكتبة والتحميل",
        ]
    )
else:
    tabs = st.tabs(
        [
            "📚 اختبار المواد",
            "🏆 الامتحان المجمع",
            "📥 المكتبة والتحميل",
        ]
    )


# =========================
# Admin Dashboard
# =========================
if st.session_state["is_admin"]:
    with tabs[0]:
        st.markdown('<div class="section-card-soft">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">لوحة التحكم الرسومية</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-subtitle">مؤشرات الأداء، الرسوم البيانية، نتائج الطلاب، وبلاغات مراجعة الأسئلة.</div>',
            unsafe_allow_html=True,
        )

        users_count, tests_count, books_count, flags_count = stats_counts()
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            render_metric_box("إجمالي الطلاب", str(users_count), "عدد المستخدمين العاديين")
        with m2:
            render_metric_box("إجمالي الاختبارات", str(tests_count), "كل المحاولات المسجلة")
        with m3:
            render_metric_box("الكتب المرفوعة", str(books_count), "ملفات PDF داخل المكتبة")
        with m4:
            render_metric_box("بلاغات الأسئلة", str(flags_count), "بحاجة إلى مراجعة")

        results_df = fetch_df("SELECT * FROM results ORDER BY test_date DESC")
        results_df = localize_subject_column(results_df, "subject")
        flags_df = fetch_df("SELECT * FROM flagged_questions ORDER BY created_at DESC")
        flags_df = localize_subject_column(flags_df, "subject")

        st.markdown('<hr class="pretty">', unsafe_allow_html=True)
        st.markdown("### 📈 الرسوم البيانية والتحليلات")

        if not results_df.empty:
            c1, c2 = st.columns(2)

            with c1:
                st.markdown("#### متوسط درجات الطلاب حسب المادة")
                by_subject = results_df.groupby("subject", as_index=False)["percent"].mean()
                by_subject = by_subject.rename(columns={"percent": "متوسط النسبة"})
                st.bar_chart(by_subject.set_index("subject"))

            with c2:
                st.markdown("#### عدد المحاولات حسب المادة")
                attempts = results_df.groupby("subject", as_index=False)["id"].count()
                attempts = attempts.rename(columns={"id": "عدد المحاولات"})
                st.bar_chart(attempts.set_index("subject"))

            st.markdown("#### أوقات الذروة لدخول الطلاب")
            try:
                dt_series = pd.to_datetime(results_df["test_date"], errors="coerce")
                peak_df = dt_series.dropna().dt.hour.value_counts().sort_index().reset_index()
                if not peak_df.empty:
                    peak_df.columns = ["الساعة", "عدد الدخول"]
                    peak_df["الساعة"] = peak_df["الساعة"].astype(str)
                    st.line_chart(peak_df.set_index("الساعة"))
            except Exception:
                st.info("تعذر تحليل أوقات الذروة حالياً.")
        else:
            st.info("لا توجد نتائج كافية لعرض الرسوم البيانية.")

        st.markdown('<hr class="pretty">', unsafe_allow_html=True)

        c_res1, c_res2 = st.columns([1.3, 1])
        with c_res1:
            st.markdown("### 📋 سجل النتائج التفصيلي")
            if not results_df.empty:
                subject_filter = st.selectbox(
                    "فلترة النتائج حسب المادة",
                    ["الكل"] + DISPLAY_SUBJECTS,
                    key="admin_results_filter",
                )
                filtered_results = results_df.copy()
                if subject_filter != "الكل":
                    filtered_results = filtered_results[filtered_results["subject"] == subject_filter]

                display_df = filtered_results.rename(
                    columns={
                        "user_name": "اسم الطالب",
                        "user_phone": "رقم الهاتف",
                        "subject": "المادة",
                        "score": "النتيجة",
                        "total": "الدرجة النهائية",
                        "percent": "النسبة",
                        "time_taken": "الوقت",
                        "warnings_count": "التحذيرات",
                        "test_date": "تاريخ الاختبار",
                    }
                ).drop(columns=["id"], errors="ignore")
                st.dataframe(display_df, width="stretch", height=430)
            else:
                st.info("لا توجد نتائج مسجلة حتى الآن.")

        with c_res2:
            st.markdown("### 🚩 بلاغات مراجعة الأسئلة")
            if not flags_df.empty:
                st.dataframe(flags_df, width="stretch", height=430)
            else:
                st.info("لا توجد بلاغات حالياً.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[1]:
        st.markdown('<div class="section-card-soft">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">إدارة النظام</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-subtitle">إضافة الأسئلة، حذفها، رفع الكتب، تصدير التقارير، وتنفيذ أوامر الصيانة.</div>',
            unsafe_allow_html=True,
        )

        admin_tabs = st.tabs(
            [
                "➕ إضافة سؤال",
                "🗑️ إدارة الأسئلة",
                "📥 رفع الكتب",
                "📤 تصدير النتائج",
                "⚠️ منطقة الخطر",
            ]
        )

        with admin_tabs[0]:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("### ➕ إضافة سؤال جديد")
            st.markdown(
                '<div class="small-muted">أضف أسئلة جديدة مباشرة إلى بنك الأسئلة.</div>',
                unsafe_allow_html=True,
            )

            with st.form("add_question_form"):
                col1, col2 = st.columns(2)
                with col1:
                    q_subject_label = st.selectbox("المادة", DISPLAY_SUBJECTS)
                with col2:
                    q_type = st.selectbox("نوع السؤال", ["اختياري", "صح وخطأ"])

                q_text = st.text_area("نص السؤال", height=140)

                c1, c2 = st.columns(2)
                with c1:
                    opt1 = st.text_input("الخيار الأول")
                    opt2 = st.text_input("الخيار الثاني")
                with c2:
                    opt3 = st.text_input("الخيار الثالث")
                    opt4 = st.text_input("الخيار الرابع")

                correct = st.text_input("الإجابة الصحيحة")
                add_submit = st.form_submit_button("حفظ السؤال")

                if add_submit:
                    if not q_text.strip() or not correct.strip():
                        st.error("يرجى كتابة نص السؤال والإجابة الصحيحة.")
                    else:
                        q_subject_code = SUBJECT_MAP[q_subject_label]
                        add_question(
                            q_subject_code,
                            q_type,
                            q_text.strip(),
                            opt1.strip(),
                            opt2.strip(),
                            opt3.strip(),
                            opt4.strip(),
                            correct.strip(),
                        )
                        st.success("تمت إضافة السؤال بنجاح.")
                        st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

        with admin_tabs[1]:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("### 🗑️ إدارة بنك الأسئلة")
            st.markdown(
                '<div class="small-muted">معاينة الأسئلة الحالية وحذف أي سؤال من القاعدة.</div>',
                unsafe_allow_html=True,
            )

            q_df = get_all_questions()
            q_df = localize_subject_column(q_df, "subject")

            if not q_df.empty:
                filter_subject = st.selectbox(
                    "فلترة الأسئلة حسب المادة",
                    ["الكل"] + DISPLAY_SUBJECTS,
                    key="questions_filter_subject",
                )
                filtered_q = q_df.copy()
                if filter_subject != "الكل":
                    filtered_q = filtered_q[filtered_q["subject"] == filter_subject]

                filtered_q["label"] = filtered_q["id"].astype(str) + " - " + filtered_q["question"]
                selected = st.selectbox("اختر السؤال المراد حذفه", filtered_q["label"].tolist())
                if st.button("حذف السؤال نهائياً"):
                    qid = int(selected.split(" - ")[0])
                    delete_question(qid)
                    st.success("تم حذف السؤال بنجاح.")
                    st.rerun()

                st.dataframe(filtered_q.drop(columns=["label"]), width="stretch", height=360)
            else:
                st.info("لا توجد أسئلة داخل القاعدة حالياً.")
            st.markdown("</div>", unsafe_allow_html=True)

        with admin_tabs[2]:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("### 📥 رفع كتب ومذكرات PDF")
            st.markdown(
                '<div class="small-muted">يمكنك رفع عدة ملفات PDF مرة واحدة، ثم تحديد اسم كل كتاب والمادة التابعة له قبل الحفظ النهائي.</div>',
                unsafe_allow_html=True,
            )

            uploaded_books = st.file_uploader(
                "ارفع ملف PDF واحد أو عدة ملفات",
                type=["pdf"],
                accept_multiple_files=True,
                key="multi_books_uploader",
            )

            if uploaded_books:
                st.markdown("#### الملفات الجاهزة للحفظ")
                for idx, up_file in enumerate(uploaded_books):
                    st.markdown('<div class="library-book">', unsafe_allow_html=True)
                    col1, col2 = st.columns([1.2, 1])
                    default_name = Path(up_file.name).stem
                    with col1:
                        st.text_input(
                            f"اسم الكتاب الظاهر للطالب #{idx + 1}",
                            value=default_name,
                            key=f"book_name_{idx}",
                        )
                    with col2:
                        st.selectbox(
                            f"المادة #{idx + 1}",
                            DISPLAY_SUBJECTS,
                            key=f"book_subject_{idx}",
                        )
                    st.markdown(
                        f"<div class='small-muted'>الملف المرفوع: {safe_text(up_file.name)}</div>",
                        unsafe_allow_html=True,
                    )
                    st.markdown("</div>", unsafe_allow_html=True)

                if st.button("حفظ كل الكتب المرفوعة", key="save_multi_books"):
                    saved_count = 0
                    skipped_files = []

                    for idx, up_file in enumerate(uploaded_books):
                        custom_name = str(st.session_state.get(f"book_name_{idx}", "")).strip()
                        subject_label = st.session_state.get(f"book_subject_{idx}")

                        if not custom_name or not subject_label:
                            skipped_files.append(up_file.name)
                            continue

                        subject_code = SUBJECT_MAP[subject_label]
                        safe_name = f"{uuid.uuid4().hex}.pdf"
                        file_path = Path("books") / safe_name
                        with open(file_path, "wb") as f:
                            f.write(up_file.getbuffer())
                        save_book(subject_code, custom_name, safe_name)
                        saved_count += 1

                    if saved_count:
                        st.success(f"تم حفظ {saved_count} كتاب/مذكرة بنجاح.")
                    if skipped_files:
                        st.warning("لم يتم حفظ بعض الملفات لوجود اسم أو مادة غير مكتملة: " + "، ".join(skipped_files))
                    if saved_count:
                        st.rerun()
            else:
                st.info("ارفع ملفات PDF ليظهر لك نموذج ربط كل ملف بالمادة المناسبة.")

            st.markdown("</div>", unsafe_allow_html=True)

        with admin_tabs[3]:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("### 📤 تصدير النتائج")
            st.markdown(
                '<div class="small-muted">أنشئ ملف Excel احترافي بنتائج كل الطلاب أو مادة محددة.</div>',
                unsafe_allow_html=True,
            )

            export_subject_label = st.selectbox(
                "اختر المادة",
                ["الكل"] + DISPLAY_SUBJECTS,
                key="export_subject"
            )

            if st.button("إنشاء ملف Excel للنتائج"):
                if export_results_excel is None:
                    st.error("خدمة تصدير Excel غير متاحة حالياً.")
                else:
                    export_subject_value = "الكل" if export_subject_label == "الكل" else SUBJECT_MAP[export_subject_label]
                    export_path = export_results_excel(export_subject_value)
                    st.success(f"تم إنشاء الملف بنجاح: {export_path}")
                    with open(export_path, "rb") as f:
                        st.download_button(
                            "⬇️ تحميل ملف النتائج",
                            data=f,
                            file_name=Path(export_path).name,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        )
            st.markdown("</div>", unsafe_allow_html=True)

        with admin_tabs[4]:
            st.markdown('<div class="admin-danger">', unsafe_allow_html=True)
            st.markdown("### ⚠️ منطقة الخطر")
            st.markdown(
                '<div class="admin-note">هذه الأوامر نهائية ولا يمكن التراجع عنها.</div>',
                unsafe_allow_html=True,
            )

            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("حذف كل النتائج"):
                    execute("DELETE FROM results")
                    st.success("تم حذف جميع النتائج.")
                    st.rerun()
            with c2:
                if st.button("حذف كل البلاغات"):
                    execute("DELETE FROM flagged_questions")
                    st.success("تم حذف جميع البلاغات.")
                    st.rerun()
            with c3:
                if st.button("حذف كل المستخدمين عدا الأدمن"):
                    execute("DELETE FROM users WHERE is_admin=0")
                    st.success("تم حذف جميع المستخدمين العاديين.")
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)


student_offset = 2 if st.session_state["is_admin"] else 0


# =========================
# Subject Exam
# =========================
with tabs[student_offset]:
    st.markdown('<div class="section-card-soft">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">اختبار المواد</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">اختر المادة، نوع الأسئلة، وعدد الأسئلة لبدء اختبار مخصص.</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        selected_subject_label = st.selectbox("اختر المادة", DISPLAY_SUBJECTS)
    with c2:
        selected_type = st.radio("نوع الأسئلة", ["اختياري", "صح وخطأ", "ميكس"], horizontal=True)
    with c3:
        num_questions = st.number_input("عدد الأسئلة", min_value=1, max_value=100, value=10)

    if st.button("🚀 بدء الاختبار", key="start_single"):
        selected_subject_code = SUBJECT_MAP[selected_subject_label]
        test_df = fetch_questions(selected_subject_code, selected_type, num_questions)

        if test_df.empty:
            st.error("لا توجد أسئلة كافية لهذه المادة أو النوع.")
        else:
            start_exam(test_df, selected_subject_label, selected_subject_code)
            st.rerun()

    if not user_results_df.empty:
        st.markdown('<hr class="pretty">', unsafe_allow_html=True)
        st.markdown("### 📌 ملخص سريع لأدائك")
        c1, c2, c3 = st.columns(3)
        with c1:
            render_metric_box("عدد محاولاتك", str(attempts_count), "كل الاختبارات المسجلة")
        with c2:
            render_metric_box("متوسط النسبة", f"{avg_percent}%", "متوسط النتائج")
        with c3:
            render_metric_box("آخر نتيجة", f"{last_percent}%", "أحدث اختبار مسجل")
    st.markdown("</div>", unsafe_allow_html=True)


# =========================
# Comprehensive Exam
# =========================
with tabs[student_offset + 1]:
    st.markdown('<div class="section-card-soft">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">الامتحان المجمع</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">اختبار شامل من مختلف المواد لتقييم المستوى العام. عند تحقيق 80% أو أكثر سيتم توليد شهادة اجتياز PDF تلقائياً.</div>',
        unsafe_allow_html=True,
    )

    mix_num = st.number_input("عدد أسئلة الامتحان المجمع", min_value=10, max_value=500, value=30)

    c1, c2, c3 = st.columns(3)
    with c1:
        render_metric_box("نوع الاختبار", "شامل", "يغطي كل المواد")
    with c2:
        render_metric_box("النجاح للشهادة", "80%", "لإصدار شهادة PDF")
    with c3:
        render_metric_box("عدد الأسئلة", str(mix_num), "يمكنك تغييره قبل البدء")

    if st.button("🔥 بدء الامتحان المجمع", key="start_mix"):
        test_df = fetch_questions(subject=None, q_type="ميكس", limit=mix_num)
        if test_df.empty:
            st.error("لا توجد أسئلة كافية حاليًا.")
        else:
            start_exam(test_df, "امتحان شامل", "MIXED")
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# =========================
# Library
# =========================
with tabs[student_offset + 2]:
    st.markdown('<div class="section-card-soft">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">المكتبة الرقمية والتحميل</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">تصفح الكتب والمذكرات حسب المادة أو من خلال قسم جميع الكتب، ثم حمّلها مباشرة بصيغة PDF.</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="small-muted">جميع الحقوق محفوظة لمؤلفي الكتب.</div>',
        unsafe_allow_html=True,
    )

    library_tabs = st.tabs(["📚 حسب المادة", "🗂️ جميع الكتب"])

    with library_tabs[0]:
        lib_subject_label = st.selectbox("اختر المادة", DISPLAY_SUBJECTS, key="library_subject")
        lib_subject_code = SUBJECT_MAP[lib_subject_label]
        books_df = localize_subject_column(get_books_by_subject(lib_subject_code), "subject")

        if not books_df.empty:
            st.markdown(f"### 📚 الكتب المتاحة لمادة: {safe_text(lib_subject_label)}")
            for idx, row in books_df.iterrows():
                st.markdown('<div class="library-book">', unsafe_allow_html=True)
                b1, b2 = st.columns([4.5, 1.5])
                with b1:
                    st.markdown(f"#### {safe_text(row['custom_name'])}")
                    st.markdown(
                        f"<div class='small-muted'>المادة: {safe_text(normalize_subject_label(row['subject']))} — تمت إضافته بتاريخ: {safe_text(row['created_at'])}</div>",
                        unsafe_allow_html=True,
                    )
                with b2:
                    file_path = Path("books") / row["file_name"]
                    if file_path.exists():
                        with open(file_path, "rb") as pdf_file:
                            st.download_button(
                                label="⬇️ تحميل الملف",
                                data=pdf_file,
                                file_name=f"{row['custom_name']}.pdf",
                                mime="application/pdf",
                                key=f"dl_subject_{idx}_{row['id']}",
                            )
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("لا توجد كتب أو مذكرات مرفوعة لهذه المادة حاليًا.")

    with library_tabs[1]:
        all_books_df = get_all_books()
        if not all_books_df.empty:
            st.markdown("### 🗂️ جميع الكتب المتاحة داخل المكتبة")
            for idx, row in all_books_df.iterrows():
                st.markdown('<div class="library-book">', unsafe_allow_html=True)
                b1, b2 = st.columns([4.5, 1.5])
                with b1:
                    st.markdown(f"#### {safe_text(row['custom_name'])}")
                    st.markdown(
                        f"<div class='small-muted'>المادة: {safe_text(normalize_subject_label(row['subject']))} — تمت إضافته بتاريخ: {safe_text(row['created_at'])}</div>",
                        unsafe_allow_html=True,
                    )
                with b2:
                    file_path = Path("books") / row["file_name"]
                    if file_path.exists():
                        with open(file_path, "rb") as pdf_file:
                            st.download_button(
                                label="⬇️ تحميل الملف",
                                data=pdf_file,
                                file_name=f"{row['custom_name']}.pdf",
                                mime="application/pdf",
                                key=f"dl_all_{idx}_{row['id']}",
                            )
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("لا توجد كتب مرفوعة داخل المكتبة حتى الآن.")
    st.markdown("</div>", unsafe_allow_html=True)


# =========================
# Active Exam Area
# =========================
if st.session_state.get("test_active") and st.session_state.get("test_data") is not None:
    st.markdown("---")

    df_questions = st.session_state["test_data"]

    if df_questions.empty:
        st.error("لا توجد أسئلة للاختبار الحالي.")
        reset_test_state()
    else:
        _, elapsed_label = format_elapsed(st.session_state["start_time"])
        total_questions = len(df_questions)
        answered_questions = count_answered_questions(df_questions)
        progress_value = answered_questions / total_questions if total_questions else 0

        st.markdown(
            f"""
            <div class="exam-head">
                <div class="exam-title">📘 {safe_text(st.session_state["test_subject"])}</div>
                <div>أجب عن الأسئلة التالية، ثم قم بتسليم الاختبار في النهاية.</div>
                <div class="exam-chip-row">
                    <div class="exam-chip">⏱️ الوقت الحالي: {safe_text(elapsed_label)}</div>
                    <div class="exam-chip">📊 تم الإجابة: {answered_questions} / {total_questions}</div>
                    <div class="exam-chip">⚠️ التحذيرات: {st.session_state.get("warnings_count", 0)} / 3</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.progress(progress_value, text=f"نسبة التقدم: {answered_questions} من {total_questions}")

        st.warning(
            "ملاحظة: النسخة الحالية تحتوي على نظام تحذيرات يدوي كمقدمة لنظام منع الغش. عند الوصول إلى 3 تحذيرات يتم إنهاء الاختبار وتسجيل نتيجة صفرية."
        )

        warn1, warn2, _ = st.columns([1.4, 1.4, 5])
        with warn1:
            if st.button("تسجيل تحذير", key="manual_warning_btn"):
                st.session_state["warnings_count"] += 1
                if st.session_state["warnings_count"] >= 3:
                    save_result(
                        st.session_state["user_name"],
                        st.session_state["user_phone"],
                        st.session_state["test_subject"],
                        0,
                        len(df_questions),
                        0.0,
                        "تم إنهاء الاختبار بسبب التحذيرات",
                        st.session_state["warnings_count"],
                    )

                    st.session_state["submitted"] = True
                    st.session_state["test_active"] = False
                    st.session_state["last_score"] = 0
                    st.session_state["last_total"] = len(df_questions)
                    st.session_state["last_percent"] = 0.0
                    st.session_state["last_time"] = "تم إنهاء الاختبار بسبب التحذيرات"
                    st.session_state["last_mistakes"] = []
                    st.session_state["ai_feedback"] = None
                    st.session_state["mistake_explanations"] = {}

                    if send_telegram_alert is not None:
                        try:
                            send_telegram_alert(
                                f"تم إنهاء اختبار بسبب التحذيرات\n"
                                f"الطالب: {st.session_state['user_name']}\n"
                                f"الهاتف: {st.session_state['user_phone']}\n"
                                f"المادة: {st.session_state['test_subject']}\n"
                                f"التحذيرات: {st.session_state['warnings_count']}"
                            )
                        except Exception:
                            pass

                    send_student_exam_notifications(
                        score=0,
                        total=len(df_questions),
                        percent=0.0,
                        time_str="تم إنهاء الاختبار بسبب التحذيرات",
                        mistakes=[],
                        failure_due_to_warnings=True,
                    )

                    st.error("تم إنهاء الاختبار بسبب الوصول إلى 3 تحذيرات.")
                    st.rerun()
                st.rerun()

        with warn2:
            if st.button("إلغاء الاختبار", key="cancel_exam_btn"):
                reset_test_state()
                st.rerun()

        for idx, row in df_questions.iterrows():
            qid = int(row["id"])
            row_subject_label = normalize_subject_label(row["subject"])

            st.markdown('<div class="question-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="question-index">سؤال رقم {idx + 1}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="question-title">{safe_text(row["question"])}</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="question-meta">المادة: {safe_text(row_subject_label)} | النوع: {safe_text(row["q_type"])}</div>',
                unsafe_allow_html=True,
            )

            if row["q_type"] == "اختياري":
                options = [
                    str(opt).strip()
                    for opt in [row["opt1"], row["opt2"], row["opt3"], row["opt4"]]
                    if str(opt).strip()
                ]
                st.radio("اختر إجابة", options, key=f"answer_{qid}", index=None)
            else:
                st.radio("اختر إجابة", ["صح", "خطأ"], key=f"answer_{qid}", index=None)

            with st.expander("🚩 الإبلاغ عن خطأ في السؤال"):
                note = st.text_area("اكتب ملاحظتك", key=f"flag_note_{qid}")
                if st.button("إرسال البلاغ", key=f"flag_btn_{qid}"):
                    save_flag(
                        qid,
                        row["question"],
                        row_subject_label,
                        st.session_state["user_name"],
                        st.session_state["user_phone"],
                        note.strip(),
                    )
                    st.success("تم إرسال البلاغ بنجاح.")

            st.markdown("</div>", unsafe_allow_html=True)

        if st.button("✅ تسليم وإنهاء الاختبار", key="submit_exam_btn"):
            submit_exam(df_questions)

        if st.session_state.get("submitted") and st.session_state.get("last_score") is not None:
            st.markdown("---")
            render_result_section()


# =========================
# Last Result View
# =========================
if (
    st.session_state.get("submitted")
    and st.session_state.get("last_score") is not None
    and not st.session_state.get("test_active")
):
    render_result_section()
