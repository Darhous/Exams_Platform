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
    init_db, save_user, save_result, save_book,
    get_books_by_subject, fetch_questions, get_all_questions,
    delete_question, add_question, fetch_df, save_flag, stats_counts, execute,
)
from utils.helpers import is_admin, normalize_name, normalize_phone

from services.notification_service import send_welcome_notification, send_exam_notifications

try:    from services.ai_feedback_service import generate_exam_feedback
except: generate_exam_feedback = None
try:    from services.telegram_service import send_telegram_alert
except: send_telegram_alert = None
try:    from services.ai_service import generate_ai_explanation
except: generate_ai_explanation = None
try:    from services.certificate_service import generate_certificate
except: generate_certificate = None
try:    from services.export_service import export_results_excel
except: export_results_excel = None


# ── Setup ───────────────────────────────────────────────────────────────────
init_db()
Path("books").mkdir(exist_ok=True)
Path("exports").mkdir(exist_ok=True)
Path("certificates").mkdir(exist_ok=True)

st.set_page_config(
    page_title="🛡️ منصة امتحانات التحول الرقمي - جامعة جنوب الوادي (المجموعة 205)",
    page_icon="🛡️", layout="wide", initial_sidebar_state="collapsed",
)

SUBJECT_MAP = {
    "تكنولوجيا المعلومات":"IT","معالج النصوص":"Word","الجداول الإلكترونية":"Excel",
    "العروض التقديمية":"PowerPoint","قواعد البيانات":"Access","تطبيقات الموبايل":"Mobile",
    "تطبيقات الويب":"WebApps","الأمن السيبراني":"CyberSecurity","البحث عبر الإنترنت":"InternetSearch",
}
DISPLAY_SUBJECTS    = list(SUBJECT_MAP.keys())
REVERSE_SUBJECT_MAP = {v:k for k,v in SUBJECT_MAP.items()}


# ── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&display=swap');
*{box-sizing:border-box;}

:root{
  --primary:#0f2f63;--primary-2:#1a56b0;--secondary:#0f7a7d;
  --success:#169b62;--warning:#d99108;--danger:#d13f52;
  --text:#11233b;--muted:#68788f;--border:#e2ebf7;
  --shadow:0 16px 44px rgba(15,47,99,.08);
  --shadow-soft:0 10px 30px rgba(17,35,59,.05);
}

html,body,[data-testid="stAppViewContainer"]{
  direction:rtl;text-align:right;
  font-family:'Cairo',sans-serif !important;
  color:#11233b;
}
.stApp{
  background:
    radial-gradient(circle at top right,rgba(26,86,176,.12),transparent 28%),
    radial-gradient(circle at bottom left,rgba(15,122,125,.11),transparent 30%),
    linear-gradient(135deg,#f8fbff 0%,#eef5ff 52%,#fbfdff 100%);
}
.block-container{max-width:1460px;padding-top:1rem;padding-bottom:2rem;}
#MainMenu,footer,header{visibility:hidden;}

/* ═══ option buttons — الحل الجذري ═══
   كل زر اختيار يأخذ شكل الـ div المخصص تماماً
   بدون أي label ظاهر — اللون والنص في الـ HTML */
div[class*="option-btn-wrap"] > div[data-testid="stButton"] > button,
.opt-btn-area > div[data-testid="stButton"] > button {
  all: unset !important;
  display: block !important;
  width: 100% !important;
  height: 100% !important;
  position: absolute !important;
  inset: 0 !important;
  cursor: pointer !important;
  opacity: 0 !important;
  z-index: 9 !important;
}

/* الـ wrapper الخاص بكل اختيار */
.opt-wrap {
  position: relative;
  margin-bottom: 8px;
  border-radius: 14px;
  overflow: hidden;
}

/* الـ div الظاهر — النص والألوان هنا */
.opt-face {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 13px 16px;
  border-radius: 14px;
  border: 2px solid #dbe6f5;
  background: #ffffff;
  font-size: 15px;
  font-weight: 700;
  font-family: 'Cairo', sans-serif;
  direction: rtl;
  text-align: right;
  word-break: break-word;
  line-height: 1.6;
  color: #11233b;
  pointer-events: none;  /* الـ click يمر للـ button تحته */
  transition: background .12s, border-color .12s;
  min-height: 52px;
}
.opt-face.selected {
  background: #1a56b0;
  border-color: #1a56b0;
  color: #ffffff;
}
.opt-face.res-correct {
  background: #dcfce7;
  border-color: #22c55e;
  color: #14532d;
}
.opt-face.res-wrong {
  background: #fee2e2;
  border-color: #ef4444;
  color: #7f1d1d;
}
.opt-face.res-neutral {
  background: #f8faff;
  border-color: #e5e7eb;
  color: #9ca3af;
}
.opt-icon {
  font-size: 18px;
  flex-shrink: 0;
  line-height: 1;
}
.opt-text { flex: 1; }

/* ═══ نخفي الـ label الزر الافتراضي من Streamlit ═══ */
.opt-wrap div[data-testid="stButton"] {
  position: absolute !important;
  inset: 0 !important;
  width: 100% !important;
  height: 100% !important;
  z-index: 9 !important;
}
.opt-wrap div[data-testid="stButton"] > button {
  position: absolute !important;
  inset: 0 !important;
  width: 100% !important;
  height: 100% !important;
  opacity: 0 !important;
  cursor: pointer !important;
  padding: 0 !important;
  margin: 0 !important;
  border: none !important;
  background: transparent !important;
  box-shadow: none !important;
  font-size: 0 !important;
  color: transparent !important;
}

/* ═══ باقي الـ UI ═══ */
.main-hero{
  background:linear-gradient(135deg,rgba(15,47,99,.98) 0%,rgba(26,86,176,.96) 56%,rgba(15,122,125,.90) 100%);
  color:white;border-radius:32px;padding:38px 32px 30px;
  box-shadow:0 24px 64px rgba(15,47,99,.22);margin-bottom:20px;
  overflow:hidden;position:relative;
}
.main-hero:before,.main-hero:after{
  content:"";position:absolute;background:rgba(255,255,255,.08);border-radius:50%;
}
.main-hero:before{left:-90px;top:-90px;width:240px;height:240px;}
.main-hero:after{right:-70px;bottom:-70px;width:190px;height:190px;}
.hero-title{font-size:35px;font-weight:900;margin-bottom:8px;position:relative;z-index:2;}
.hero-subtitle{font-size:15px;font-weight:600;opacity:.98;position:relative;z-index:2;line-height:1.9;}
.hero-badge-row{display:flex;gap:10px;flex-wrap:wrap;margin-top:16px;position:relative;z-index:2;}
.hero-badge{background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.18);
            color:#fff;border-radius:999px;padding:8px 14px;font-size:13px;font-weight:800;}
.glass-entry{background:rgba(255,255,255,.84);backdrop-filter:blur(20px);
             border:1px solid rgba(255,255,255,.6);border-radius:32px;
             padding:40px;box-shadow:0 20px 72px rgba(15,47,99,.10);}
.section-card{background:rgba(255,255,255,.97);border:1px solid var(--border);
              border-radius:26px;padding:24px;box-shadow:var(--shadow);margin-bottom:18px;}
.section-card-soft{background:linear-gradient(135deg,rgba(255,255,255,.98) 0%,rgba(244,248,255,.98) 100%);
                   border:1px solid var(--border);border-radius:28px;padding:24px;
                   box-shadow:var(--shadow);margin-bottom:18px;}
.section-title{color:#11233b;font-size:24px;font-weight:900;margin-bottom:6px;}
.section-subtitle{color:var(--muted);font-size:14px;font-weight:700;margin-bottom:12px;line-height:1.9;}
.metric-box{background:linear-gradient(135deg,#fff 0%,#f7fbff 100%);border:1px solid var(--border);
            border-radius:24px;padding:20px 18px;box-shadow:var(--shadow-soft);margin-bottom:10px;}
.metric-title{color:var(--muted);font-size:13px;font-weight:800;margin-bottom:8px;}
.metric-value{color:#11233b;font-size:28px;font-weight:900;line-height:1.2;}
.metric-note{color:var(--primary-2);font-size:12px;font-weight:800;margin-top:6px;}
.info-strip{background:linear-gradient(135deg,#fff 0%,#f3f8ff 100%);border:1px solid var(--border);
            border-radius:20px;padding:16px 18px;margin-bottom:18px;
            box-shadow:0 8px 24px rgba(16,24,40,.04);}
.info-chip-row{display:flex;gap:10px;flex-wrap:wrap;}
.info-chip{background:#ecf4ff;color:var(--primary);padding:8px 14px;border-radius:999px;
           font-size:13px;font-weight:900;border:1px solid #dbe8ff;}
.exam-head{background:linear-gradient(135deg,rgba(15,47,99,.98) 0%,rgba(26,86,176,.95) 100%);
           color:white;border-radius:24px;padding:24px;
           box-shadow:0 16px 48px rgba(15,47,99,.18);margin-bottom:16px;}
.exam-title{font-size:28px;font-weight:900;margin-bottom:8px;}
.exam-chip-row{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px;}
.exam-chip{background:rgba(255,255,255,.15);color:white;border:1px solid rgba(255,255,255,.18);
           border-radius:999px;padding:8px 12px;font-size:13px;font-weight:900;}
.question-card{background:#fff;border-radius:22px;border:1px solid var(--border);
               padding:22px;box-shadow:var(--shadow-soft);margin-bottom:16px;}
.question-index{display:inline-block;background:#edf4ff;color:var(--primary);
                border:1px solid #dbe8ff;padding:7px 12px;border-radius:999px;
                font-size:13px;font-weight:900;margin-bottom:10px;}
.question-title{color:#11233b;font-size:20px;font-weight:900;margin-bottom:8px;line-height:1.9;}
.question-meta{color:var(--muted);font-size:13px;font-weight:700;margin-bottom:12px;}
.library-book{background:linear-gradient(135deg,#fff 0%,#f7fbff 100%);border:1px solid var(--border);
              border-radius:18px;padding:18px;box-shadow:0 8px 22px rgba(16,24,40,.04);margin-bottom:12px;}
.admin-danger{background:#fff6f6;border:1px solid #ffd8d8;border-radius:24px;padding:22px;}
.admin-note{color:var(--muted);font-size:13px;font-weight:700;}
.small-muted{color:var(--muted);font-size:13px;font-weight:700;}
.input-note{color:#6a7a92;font-size:12px;font-weight:700;margin-top:-8px;margin-bottom:8px;line-height:1.8;}
.phone-valid{color:var(--success);font-size:12px;font-weight:800;margin-top:-6px;margin-bottom:8px;}
.phone-invalid{color:var(--danger);font-size:12px;font-weight:800;margin-top:-6px;margin-bottom:8px;}
.login-help-text{margin-top:-4px;margin-bottom:14px;color:#6a7a92;font-size:13px;font-weight:800;line-height:1.9;}
.dev-credit{margin-top:16px;text-align:center;color:var(--muted);font-size:13px;font-weight:700;line-height:1.9;}
.dev-credit a{color:var(--primary-2) !important;text-decoration:none !important;font-weight:900;}
.result-shell{margin-top:18px;margin-bottom:14px;}
.result-hero{background:linear-gradient(135deg,#0f172a 0%,#163264 45%,#1a56b0 100%);
             border:1px solid rgba(255,255,255,.08);border-radius:28px;padding:30px 24px;
             color:#fff;box-shadow:0 18px 45px rgba(15,23,42,.22);margin-bottom:18px;}
.result-hero-title{font-size:31px;font-weight:900;margin-bottom:10px;text-align:center;}
.result-hero-subtitle{font-size:15px;opacity:.96;text-align:center;line-height:2;}
.status-badge{display:inline-block;margin-top:14px;padding:8px 16px;border-radius:999px;font-size:13px;font-weight:900;}
.status-pass{background:rgba(22,163,74,.16);color:#dcfce7;border:1px solid rgba(220,252,231,.20);}
.status-fail{background:rgba(220,38,38,.18);color:#fee2e2;border:1px solid rgba(254,226,226,.20);}
.result-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin:18px 0 14px;}
.result-stat-card{background:rgba(255,255,255,.98);border:1px solid var(--border);
                  border-radius:22px;padding:18px 16px;box-shadow:var(--shadow-soft);text-align:center;}
.result-stat-label{font-size:13px;color:var(--muted);font-weight:800;margin-bottom:8px;}
.result-stat-value{font-size:28px;color:#11233b;font-weight:900;line-height:1.3;}
.result-stat-note{margin-top:6px;font-size:12px;color:#8a9ab0;font-weight:700;}
.summary-panel{background:#fff;border:1px solid var(--border);border-radius:24px;
               padding:22px 20px;box-shadow:var(--shadow-soft);margin-top:12px;margin-bottom:16px;}
.summary-title{font-size:22px;font-weight:900;color:#11233b;margin-bottom:10px;}
.summary-text{font-size:15px;line-height:2;color:#334155;font-weight:700;}
.mistakes-box{background:#fff;border:1px solid #ffe1e1;border-radius:24px;padding:20px;
              margin-top:16px;box-shadow:var(--shadow-soft);}
.mistakes-title{font-size:21px;font-weight:900;color:#b91c1c;margin-bottom:14px;}
.mistake-item{border:1px solid var(--border);border-right:5px solid var(--danger);
              border-radius:18px;padding:16px;margin-bottom:12px;background:#fcfcfd;}
.mistake-q{font-weight:900;color:#11233b;margin-bottom:8px;line-height:1.9;}
.mistake-a{color:#475569;line-height:1.95;margin-bottom:4px;font-size:14px;font-weight:700;}
.ai-feedback-box{background:linear-gradient(135deg,#fff 0%,#f6faff 100%);
                 border:1px solid var(--border);border-radius:24px;padding:22px;
                 box-shadow:var(--shadow-soft);margin-top:18px;}
.ai-feedback-title{font-size:21px;font-weight:900;color:#11233b;margin-bottom:10px;}
.ai-feedback-summary{color:#334155;font-size:15px;line-height:2;font-weight:700;margin-bottom:14px;}
.ai-feedback-item{border:1px solid #dde8f7;border-radius:18px;padding:16px;margin-bottom:12px;background:#fff;}
hr.pretty{border:none;height:1px;background:linear-gradient(to left,transparent,#d9e4f7,transparent);margin:18px 0 14px;}

/* أزرار Streamlit العادية */
div.stButton > button,div.stDownloadButton > button,div.stFormSubmitButton > button{
  width:100%;border:none;border-radius:14px;padding:12px 18px;
  font-weight:900;font-size:15px;font-family:'Cairo',sans-serif;
  background:linear-gradient(135deg,#0f2f63 0%,#1a56b0 100%);
  color:white;box-shadow:0 10px 24px rgba(26,86,176,.24);transition:all .22s ease;
}
div.stButton > button:hover{transform:translateY(-2px);}

.stTabs [data-baseweb="tab-list"]{gap:10px;background:rgba(255,255,255,.74);padding:10px;
  border-radius:20px;border:1px solid var(--border);
  box-shadow:0 10px 28px rgba(16,24,40,.04);margin-bottom:18px;}
.stTabs [data-baseweb="tab"]{background:white;border-radius:14px;padding:10px 16px;
  font-weight:900;color:#11233b;border:1px solid var(--border);font-family:'Cairo',sans-serif;}
.stTabs [aria-selected="true"]{
  background:linear-gradient(135deg,#0f2f63 0%,#1a56b0 100%) !important;
  color:white !important;border:none !important;}
.stProgress > div > div > div > div{background:linear-gradient(135deg,#1a56b0,#0f7a7d);}
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea{
  border-radius:14px !important;border:1px solid #dbe6f5 !important;
  background:#fbfdff !important;color:#11233b !important;font-family:'Cairo',sans-serif !important;}
[data-testid="stNumberInput"] input{border-radius:14px !important;color:#11233b !important;}
[data-baseweb="select"] > div{background:#fff !important;color:#11233b !important;}
[data-baseweb="select"] *{color:#11233b !important;}
[data-testid="stSelectbox"] label,[data-testid="stNumberInput"] label,
[data-testid="stTextInput"] label,[data-testid="stTextArea"] label,
[data-testid="stFileUploader"] label{color:#11233b !important;font-weight:900 !important;}
h1,h2,h3,h4,h5{color:#11233b;font-weight:900 !important;font-family:'Cairo',sans-serif !important;}
.library-book,.library-book *{direction:rtl !important;text-align:right !important;}
.question-card,.question-card *{direction:rtl !important;text-align:right !important;}

@media(max-width:900px){
  .block-container{padding-top:.6rem;padding-left:.7rem;padding-right:.7rem;}
  .main-hero,.glass-entry,.section-card,.section-card-soft,
  .question-card,.summary-panel,.mistakes-box,.ai-feedback-box{
    padding:16px 14px !important;border-radius:18px !important;}
  .result-hero{padding:20px 16px !important;border-radius:20px !important;}
  .result-hero,.result-hero *{color:#fff !important;-webkit-text-fill-color:#fff !important;}
  .hero-title{font-size:20px !important;line-height:1.6 !important;}
  .question-title{font-size:16px !important;overflow-wrap:anywhere !important;}
  .result-grid{grid-template-columns:1fr !important;}
  .info-chip,.hero-badge,.exam-chip{font-size:11px !important;padding:5px 9px !important;}
  .opt-face{font-size:14px !important;padding:12px 14px !important;}
}
</style>
""", unsafe_allow_html=True)


# ── Session defaults ─────────────────────────────────────────────────────────
DEFAULTS = {
    "entered":False,"user_name":"","user_phone":"","is_admin":False,
    "test_active":False,"test_data":None,"test_subject":"","test_subject_code":"",
    "start_time":None,"warnings_count":0,"submitted":False,
    "last_score":None,"last_total":None,"last_percent":None,"last_time":None,
    "last_mistakes":[],"last_all_answers":[],"ai_feedback":None,
    "mistake_explanations":{},"welcome_sent":False,
    "exam_answers":{},
}
for k,v in DEFAULTS.items():
    if k not in st.session_state: st.session_state[k]=v


# ── Helpers ──────────────────────────────────────────────────────────────────
def T(v): return html.escape(str(v)) if v is not None else ""

def render_metric_box(title,value,note=""):
    st.markdown(f"""<div class="metric-box">
      <div class="metric-title">{T(title)}</div>
      <div class="metric-value">{T(value)}</div>
      <div class="metric-note">{T(note)}</div>
    </div>""",unsafe_allow_html=True)

def fmt_elapsed(t0):
    e=max(0,int(time.time()-t0));m,s=divmod(e,60)
    return e,f"{m} دقيقة و {s} ثانية"

def norm_label(v):
    v=str(v).strip() if v else ""
    return REVERSE_SUBJECT_MAP.get(v,v) if v in REVERSE_SUBJECT_MAP else v

def localize_df(df,col="subject"):
    if df is None or df.empty or col not in df.columns: return df
    d=df.copy();d[col]=d[col].apply(norm_label);return d

def book_field(row,f,default=""):
    try:
        if hasattr(row,'index') and f in row.index:
            v=row[f];return default if pd.isna(v) else v
    except: pass
    return default

def all_books():
    for q in ["SELECT * FROM books ORDER BY created_at DESC,id DESC",
               "SELECT * FROM books ORDER BY id DESC"]:
        try:
            df=fetch_df(q)
            if df is not None and not df.empty: return localize_df(df,"subject")
            break
        except: continue
    return pd.DataFrame()

def clear_answers():
    st.session_state["exam_answers"]={}
    for k in [k for k in st.session_state if k.startswith("flag_note_")]:
        del st.session_state[k]

def reset_test():
    clear_answers()
    for k,v in [("test_active",False),("test_data",None),("test_subject",""),
                ("test_subject_code",""),("start_time",None),("warnings_count",0),("submitted",False)]:
        st.session_state[k]=v

def reset_result():
    for k,v in [("submitted",False),("last_score",None),("last_total",None),
                ("last_percent",None),("last_time",None),("last_mistakes",[]),
                ("last_all_answers",[]),("ai_feedback",None),("mistake_explanations",{})]:
        st.session_state[k]=v

def get_user_results():
    return localize_df(fetch_df(
        "SELECT * FROM results WHERE user_name=? AND user_phone=? ORDER BY test_date DESC",
        (st.session_state["user_name"],st.session_state["user_phone"])),"subject")

def dashboard_summary():
    df=get_user_results();n=len(df)
    avg=round(float(df["percent"].mean()),2) if not df.empty else 0
    last=float(df.iloc[0]["percent"]) if not df.empty else 0
    return n,avg,last,df

def norm_phone(p): return re.sub(r"[^0-9]","",str(p or ""))[:11]

def validate_phone(p):
    c=norm_phone(normalize_phone(p))
    if not c:                  return False,"يرجى كتابة رقم التليفون."
    if not c.isdigit():        return False,"رقم التليفون يجب أن يحتوي على أرقام فقط."
    if len(c)!=11:             return False,"رقم التليفون يجب أن يكون 11 رقمًا بالضبط."
    if not c.startswith("01"): return False,"رقم التليفون يجب أن يبدأ بـ 01."
    return True,c

def ai_feedback_safe(subject,user_name,mistakes):
    if generate_exam_feedback is None:
        return {"summary_ar":"الملخص الذكي غير متاح حالياً.","mistakes":[]}
    try: return generate_exam_feedback(subject=subject,user_name=user_name,mistakes=mistakes)
    except Exception as e:
        print("feedback err:",e)
        return {"summary_ar":"حدث خطأ أثناء إنشاء الملخص.","mistakes":[]}

def explain(subject,question,user_ans,correct,key):
    cache=st.session_state["mistake_explanations"]
    if key in cache: return cache[key]
    if generate_ai_explanation is None: exp="الشرح الذكي غير متاح حالياً."
    else:
        try: exp=generate_ai_explanation(subject,question,user_ans,correct)
        except: exp="تعذر إنشاء شرح ذكي لهذه الإجابة حالياً."
    cache[key]=exp;st.session_state["mistake_explanations"]=cache
    return exp

def send_welcome():
    if st.session_state.get("welcome_sent"): return
    try:
        send_welcome_notification(st.session_state["user_name"],st.session_state["user_phone"])
        st.session_state["welcome_sent"]=True
    except: pass

def start_exam(df,label,code):
    clear_answers();reset_result()
    st.session_state.update({"test_data":df.copy(),"test_subject":label,"test_subject_code":code,
                              "start_time":time.time(),"test_active":True,
                              "warnings_count":0,"submitted":False})

def tg_alert(msg):
    if send_telegram_alert:
        try: send_telegram_alert(msg)
        except: pass

def notify_student(score,total,percent,time_str,mistakes,warnings=False):
    try:
        send_exam_notifications(
            user_name=st.session_state["user_name"],user_phone=st.session_state["user_phone"],
            subject=st.session_state["test_subject"],score=score,total=total,percent=percent,
            time_str=time_str,warnings_count=st.session_state.get("warnings_count",0),
            mistakes=mistakes,failure_due_to_warnings=warnings)
    except: pass


# ── Option renderer ──────────────────────────────────────────────────────────
def render_options(qid: int, opts: list, result_mode: bool = False):
    """
    يعرض الاختيارات كـ HTML div مع زر Streamlit شفاف فوقه.
    result_mode=True: يلوّن الصح أخضر والغلط أحمر بدون أي زر.
    """
    answers = st.session_state["exam_answers"]
    current = answers.get(str(qid), "")
    correct = answers.get(f"{qid}__correct", "")

    for j, opt in enumerate(opts):
        if result_mode:
            if opt == correct:
                css_class = "res-correct"; icon = "✅"
            elif opt == current and opt != correct:
                css_class = "res-wrong";   icon = "❌"
            else:
                css_class = "res-neutral"; icon = "◯"
        else:
            css_class = "selected" if opt == current else ""
            icon = "●" if opt == current else "○"

        # الـ div الظاهر
        st.markdown(f"""
        <div class="opt-wrap">
          <div class="opt-face {css_class}">
            <span class="opt-icon">{icon}</span>
            <span class="opt-text">{T(opt)}</span>
          </div>
        """, unsafe_allow_html=True)

        # الزر الشفاف — فقط أثناء الامتحان
        if not result_mode:
            if st.button("‌", key=f"ob_{qid}_{j}", use_container_width=True):
                st.session_state["exam_answers"][str(qid)] = opt
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)


def submit_exam(dfq):
    if st.session_state.get("submitted"): return
    if not st.session_state.get("start_time"):
        st.error("تعذر تسليم الاختبار لأن وقت البدء غير متوفر."); return

    _,time_str=fmt_elapsed(st.session_state["start_time"])
    answers=st.session_state["exam_answers"]
    score=0;mistakes=[];all_ans=[]

    for _,row in dfq.iterrows():
        qid=int(row["id"])
        correct=str(row["correct_answer"]).strip()
        user=answers.get(str(qid),"")
        ok=(user==correct)
        if ok: score+=1
        else:
            mistakes.append({"id":qid,"subject":norm_label(row["subject"]),
                             "question":row["question"],"user":user or "لم يجب","correct":correct})
        all_ans.append({"id":qid,"subject":norm_label(row["subject"]),
                        "question":row["question"],"user":user or "لم يجب",
                        "correct":correct,"is_correct":ok})
        st.session_state["exam_answers"][f"{qid}__correct"]=correct

    total=len(dfq);percent=round((score/total)*100,2) if total else 0.0
    save_result(st.session_state["user_name"],st.session_state["user_phone"],
                st.session_state["test_subject"],score,total,percent,time_str,
                st.session_state.get("warnings_count",0))
    tg_alert(f"تنبيه\nالطالب:{st.session_state['user_name']}\nالهاتف:{st.session_state['user_phone']}\n"
             f"المادة:{st.session_state['test_subject']}\nالنتيجة:{score}/{total}({percent}%)\nالوقت:{time_str}")
    notify_student(score,total,percent,time_str,mistakes)
    st.session_state.update({"last_score":score,"last_total":total,"last_percent":percent,
        "last_time":time_str,"last_mistakes":mistakes,"last_all_answers":all_ans,
        "submitted":True,"test_active":False})
    st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# Entry Screen
# ════════════════════════════════════════════════════════════════════════════
if not st.session_state["entered"]:
    _,c2,_=st.columns([1,1.45,1])
    with c2:
        st.markdown("""<div class="main-hero">
          <div class="hero-title">🛡️ منصة امتحانات التحول الرقمي - جامعة جنوب الوادي (المجموعة 205)</div>
          <div class="hero-subtitle">منصة حديثة للاختبارات الإلكترونية، المتابعة الدقيقة، وإظهار النتائج بشكل فوري واحترافي.</div>
          <div class="hero-badge-row">
            <div class="hero-badge">واجهة راقية</div><div class="hero-badge">نتائج فورية</div>
            <div class="hero-badge">اختبارات متنوعة</div><div class="hero-badge">مكتبة رقمية</div>
          </div>
        </div>""",unsafe_allow_html=True)
        st.markdown('<div class="glass-entry">',unsafe_allow_html=True)
        st.markdown('<div class="section-title">الدخول إلى المنصة</div>',unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">اكتب الاسم ورقم التليفون بشكل صحيح للدخول إلى المنصة.</div>',unsafe_allow_html=True)
        st.markdown('<div class="login-help-text">اكتب رقم التليفون من 11 رقمًا بالأرقام فقط مثل: 01012345678</div>',unsafe_allow_html=True)
        with st.form("entry_form",clear_on_submit=False):
            name =st.text_input("👤 الاسم",placeholder="اكتب الاسم هنا")
            phone=st.text_input("📱 رقم التليفون",placeholder="اكتب رقم التليفون هنا",max_chars=11)
            lp=norm_phone(phone)
            if phone and lp!=phone:
                st.markdown('<div class="phone-invalid">يُسمح بكتابة الأرقام فقط.</div>',unsafe_allow_html=True)
            elif phone and len(lp)<11:
                st.markdown('<div class="phone-invalid">رقم التليفون يجب أن يكون 11 رقمًا.</div>',unsafe_allow_html=True)
            elif len(lp)==11:
                st.markdown('<div class="phone-valid">✅ رقم التليفون مكتمل وجاهز للدخول.</div>',unsafe_allow_html=True)
            else:
                st.markdown('<div class="input-note">يجب أن يبدأ الرقم بـ 01 وأن يكون 11 رقمًا.</div>',unsafe_allow_html=True)
            if st.form_submit_button("دخول المنصة"):
                cn=normalize_name(name);ok,pr=validate_phone(phone)
                if not cn: st.error("يرجى كتابة الاسم.")
                elif not ok: st.error(pr)
                else:
                    adm=is_admin(cn,pr);reset_test();reset_result()
                    st.session_state.update({"entered":True,"user_name":cn,"user_phone":pr,
                                              "is_admin":adm,"welcome_sent":False})
                    save_user(cn,pr,adm);send_welcome();st.rerun()
        st.markdown("""<div class="dev-credit">تم تطوير المنصة بمعرفة
          <a href="mailto:ahmeddarhous@gmail.com">أحمد درهوس 01030002331</a></div>""",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)
    st.stop()


# ════════════════════════════════════════════════════════════════════════════
# Header + Info Strip
# ════════════════════════════════════════════════════════════════════════════
role_text="مدير النظام" if st.session_state["is_admin"] else "طالب"
cl,cr=st.columns([6,1.3])
with cl:
    st.markdown(f"""<div class="main-hero">
      <div class="hero-title">🛡️ منصة امتحانات التحول الرقمي - جامعة جنوب الوادي (المجموعة 205)</div>
      <div class="hero-subtitle">مرحباً <b>{T(st.session_state["user_name"])}</b>
        — الحالة: <b>{role_text}</b> — رقم التليفون: <b>{T(st.session_state["user_phone"])}</b></div>
      <div class="hero-badge-row">
        <div class="hero-badge">واجهة احترافية</div><div class="hero-badge">نتائج محفوظة</div>
        <div class="hero-badge">تقييم لحظي</div><div class="hero-badge">مراجعة الأخطاء</div>
      </div>
    </div>""",unsafe_allow_html=True)
with cr:
    st.markdown("<div style='height:12px'></div>",unsafe_allow_html=True)
    if st.button("تسجيل خروج"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

attempts_count,avg_percent,last_percent,user_results_df=dashboard_summary()
st.markdown(f"""<div class="info-strip"><div class="info-chip-row">
  <div class="info-chip">👤 {T(st.session_state["user_name"])}</div>
  <div class="info-chip">📱 {T(st.session_state["user_phone"])}</div>
  <div class="info-chip">📊 محاولاتك: {attempts_count}</div>
  <div class="info-chip">📈 متوسطك: {avg_percent}%</div>
  <div class="info-chip">⭐ آخر نتيجة: {last_percent}%</div>
</div></div>""",unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# Tabs
# ════════════════════════════════════════════════════════════════════════════
if st.session_state["is_admin"]:
    tab_dash,tab_sys,tab_sub,tab_mix,tab_lib=st.tabs(
        ["📊 لوحة الإدارة","⚙️ إدارة النظام","📚 اختبار المواد","🏆 الامتحان المجمع","📥 المكتبة"])
else:
    tab_sub,tab_mix,tab_lib=st.tabs(["📚 اختبار المواد","🏆 الامتحان المجمع","📥 المكتبة"])


# ════════════════════════════════════════════════════════════════════════════
# Admin
# ════════════════════════════════════════════════════════════════════════════
if st.session_state["is_admin"]:
    with tab_dash:
        st.markdown('<div class="section-card-soft">',unsafe_allow_html=True)
        st.markdown('<div class="section-title">لوحة التحكم الرسومية</div>',unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">مؤشرات الأداء، الرسوم البيانية، نتائج الطلاب، وبلاغات مراجعة الأسئلة.</div>',unsafe_allow_html=True)
        uc,tc,bc,fc=stats_counts()
        m1,m2,m3,m4=st.columns(4)
        with m1: render_metric_box("إجمالي الطلاب",str(uc),"عدد المستخدمين العاديين")
        with m2: render_metric_box("إجمالي الاختبارات",str(tc),"كل المحاولات المسجلة")
        with m3: render_metric_box("الكتب المرفوعة",str(bc),"ملفات PDF داخل المكتبة")
        with m4: render_metric_box("بلاغات الأسئلة",str(fc),"بحاجة إلى مراجعة")
        rdf=localize_df(fetch_df("SELECT * FROM results ORDER BY test_date DESC"),"subject")
        fdf=localize_df(fetch_df("SELECT * FROM flagged_questions ORDER BY created_at DESC"),"subject")
        st.markdown('<hr class="pretty">',unsafe_allow_html=True)
        st.markdown("### 📈 الرسوم البيانية")
        if not rdf.empty:
            c1,c2=st.columns(2)
            with c1:
                st.markdown("#### متوسط الدرجات حسب المادة")
                st.bar_chart(rdf.groupby("subject",as_index=False)["percent"].mean().rename(columns={"percent":"متوسط النسبة"}).set_index("subject"))
            with c2:
                st.markdown("#### عدد المحاولات حسب المادة")
                st.bar_chart(rdf.groupby("subject",as_index=False)["id"].count().rename(columns={"id":"عدد المحاولات"}).set_index("subject"))
            st.markdown("#### أوقات الذروة")
            try:
                pdf=pd.to_datetime(rdf["test_date"],errors="coerce").dropna().dt.hour.value_counts().sort_index().reset_index()
                if not pdf.empty:
                    pdf.columns=["الساعة","عدد الدخول"];pdf["الساعة"]=pdf["الساعة"].astype(str)
                    st.line_chart(pdf.set_index("الساعة"))
            except: st.info("تعذر تحليل أوقات الذروة.")
        else: st.info("لا توجد نتائج كافية.")
        st.markdown('<hr class="pretty">',unsafe_allow_html=True)
        cr1,cr2=st.columns([1.3,1])
        with cr1:
            st.markdown("### 📋 سجل النتائج")
            if not rdf.empty:
                sf=st.selectbox("فلترة حسب المادة",["الكل"]+DISPLAY_SUBJECTS,key="adm_sf")
                fr=rdf if sf=="الكل" else rdf[rdf["subject"]==sf]
                st.dataframe(fr.rename(columns={"user_name":"اسم الطالب","user_phone":"رقم الهاتف",
                    "subject":"المادة","score":"النتيجة","total":"الدرجة النهائية","percent":"النسبة",
                    "time_taken":"الوقت","warnings_count":"التحذيرات","test_date":"التاريخ"
                }).drop(columns=["id"],errors="ignore"),width="stretch",height=430)
            else: st.info("لا توجد نتائج.")
        with cr2:
            st.markdown("### 🚩 البلاغات")
            if not fdf.empty: st.dataframe(fdf,width="stretch",height=430)
            else: st.info("لا توجد بلاغات.")
        st.markdown("</div>",unsafe_allow_html=True)

    with tab_sys:
        st.markdown('<div class="section-card-soft">',unsafe_allow_html=True)
        st.markdown('<div class="section-title">إدارة النظام</div>',unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">إضافة الأسئلة، حذفها، رفع الكتب، تصدير التقارير.</div>',unsafe_allow_html=True)
        at=st.tabs(["➕ إضافة سؤال","🗑️ إدارة الأسئلة","📥 رفع الكتب","📤 تصدير النتائج","⚠️ منطقة الخطر"])
        with at[0]:
            st.markdown('<div class="section-card">',unsafe_allow_html=True)
            st.markdown("### ➕ إضافة سؤال جديد")
            with st.form("add_q"):
                c1,c2=st.columns(2)
                with c1: qsl=st.selectbox("المادة",DISPLAY_SUBJECTS)
                with c2: qt=st.selectbox("نوع السؤال",["اختياري","صح وخطأ"])
                qtxt=st.text_area("نص السؤال",height=140)
                c1,c2=st.columns(2)
                with c1: o1=st.text_input("الخيار الأول");o2=st.text_input("الخيار الثاني")
                with c2: o3=st.text_input("الخيار الثالث");o4=st.text_input("الخيار الرابع")
                cor=st.text_input("الإجابة الصحيحة")
                if st.form_submit_button("حفظ السؤال"):
                    if not qtxt.strip() or not cor.strip(): st.error("يرجى كتابة نص السؤال والإجابة الصحيحة.")
                    else:
                        add_question(SUBJECT_MAP[qsl],qt,qtxt.strip(),o1.strip(),o2.strip(),o3.strip(),o4.strip(),cor.strip())
                        st.success("تمت إضافة السؤال بنجاح.");st.rerun()
            st.markdown("</div>",unsafe_allow_html=True)
        with at[1]:
            st.markdown('<div class="section-card">',unsafe_allow_html=True)
            st.markdown("### 🗑️ إدارة بنك الأسئلة")
            qdf=localize_df(get_all_questions(),"subject")
            if not qdf.empty:
                fs2=st.selectbox("فلترة حسب المادة",["الكل"]+DISPLAY_SUBJECTS,key="q_fs")
                fq=qdf if fs2=="الكل" else qdf[qdf["subject"]==fs2]
                fq=fq.copy();fq["label"]=fq["id"].astype(str)+" - "+fq["question"]
                sel=st.selectbox("اختر السؤال المراد حذفه",fq["label"].tolist())
                if st.button("حذف السؤال نهائياً"):
                    delete_question(int(sel.split(" - ")[0]));st.success("تم الحذف.");st.rerun()
                st.dataframe(fq.drop(columns=["label"]),width="stretch",height=360)
            else: st.info("لا توجد أسئلة.")
            st.markdown("</div>",unsafe_allow_html=True)
        with at[2]:
            st.markdown('<div class="section-card">',unsafe_allow_html=True)
            st.markdown("### 📥 رفع الكتب وملفات PDF")
            ufiles=st.file_uploader("ارفع ملف PDF أو أكثر",type=["pdf"],accept_multiple_files=True,key="books_up")
            if ufiles:
                payload=[]
                for i,f in enumerate(ufiles):
                    st.markdown('<div class="library-book">',unsafe_allow_html=True)
                    c1,c2=st.columns([1.8,1.2])
                    with c1: bn=st.text_input(f"اسم الكتاب #{i+1}",value=Path(f.name).stem,key=f"bn_{i}")
                    with c2: bs=st.selectbox(f"المادة #{i+1}",DISPLAY_SUBJECTS,key=f"bs_{i}")
                    st.markdown(f"<div class='small-muted'>الملف: {T(f.name)}</div>",unsafe_allow_html=True)
                    st.markdown("</div>",unsafe_allow_html=True)
                    payload.append((f,bn.strip(),SUBJECT_MAP[bs]))
                if st.button("حفظ كل الكتب المرفوعة",key="save_books"):
                    if any(not n for _,n,_ in payload): st.error("يرجى كتابة اسم لكل كتاب.")
                    else:
                        for f,cn,sc in payload:
                            sn=f"{uuid.uuid4().hex}.pdf"
                            with open(Path("books")/sn,"wb") as fp: fp.write(f.getbuffer())
                            save_book(sc,cn,sn)
                        st.success(f"تم حفظ {len(payload)} كتاب/ملف بنجاح.");st.rerun()
            else: st.info("اختر ملف PDF واحد أو أكثر لبدء الرفع.")
            st.markdown("</div>",unsafe_allow_html=True)
        with at[3]:
            st.markdown('<div class="section-card">',unsafe_allow_html=True)
            st.markdown("### 📤 تصدير النتائج")
            esl=st.selectbox("اختر المادة",["الكل"]+DISPLAY_SUBJECTS,key="exp_s")
            if st.button("إنشاء ملف Excel للنتائج"):
                if export_results_excel is None: st.error("خدمة التصدير غير متاحة.")
                else:
                    ep=export_results_excel("الكل" if esl=="الكل" else SUBJECT_MAP[esl])
                    st.success(f"تم إنشاء الملف: {ep}")
                    with open(ep,"rb") as f:
                        st.download_button("⬇️ تحميل ملف النتائج",data=f,file_name=Path(ep).name,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            st.markdown("</div>",unsafe_allow_html=True)
        with at[4]:
            st.markdown('<div class="admin-danger">',unsafe_allow_html=True)
            st.markdown("### ⚠️ منطقة الخطر")
            st.markdown('<div class="admin-note">هذه الأوامر نهائية ولا يمكن التراجع عنها.</div>',unsafe_allow_html=True)
            c1,c2,c3=st.columns(3)
            with c1:
                if st.button("حذف كل النتائج"):   execute("DELETE FROM results");          st.success("تم.");st.rerun()
            with c2:
                if st.button("حذف كل البلاغات"): execute("DELETE FROM flagged_questions"); st.success("تم.");st.rerun()
            with c3:
                if st.button("حذف المستخدمين"):  execute("DELETE FROM users WHERE is_admin=0"); st.success("تم.");st.rerun()
            st.markdown("</div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# Subject Exam
# ════════════════════════════════════════════════════════════════════════════
with tab_sub:
    st.markdown('<div class="section-card-soft">',unsafe_allow_html=True)
    st.markdown('<div class="section-title">اختبار المواد</div>',unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">اختر المادة، نوع الأسئلة، وعدد الأسئلة لبدء اختبار مخصص.</div>',unsafe_allow_html=True)
    c1,c2,c3=st.columns(3)
    with c1: ssl=st.selectbox("اختر المادة",DISPLAY_SUBJECTS)
    with c2: stp=st.selectbox("نوع الأسئلة",["اختياري","صح وخطأ","ميكس"],key="sub_type")
    with c3: snq=st.number_input("عدد الأسئلة",min_value=1,max_value=100,value=10)
    if st.button("🚀 بدء الاختبار",key="start_single"):
        tdf=fetch_questions(SUBJECT_MAP[ssl],stp,snq)
        if tdf.empty: st.error("لا توجد أسئلة كافية لهذه المادة أو النوع.")
        else: start_exam(tdf,ssl,SUBJECT_MAP[ssl]);st.rerun()
    if not user_results_df.empty:
        st.markdown('<hr class="pretty">',unsafe_allow_html=True)
        st.markdown("### 📌 ملخص سريع لأدائك")
        c1,c2,c3=st.columns(3)
        with c1: render_metric_box("عدد محاولاتك",str(attempts_count),"كل الاختبارات المسجلة")
        with c2: render_metric_box("متوسط النسبة",f"{avg_percent}%","متوسط النتائج")
        with c3: render_metric_box("آخر نتيجة",f"{last_percent}%","أحدث اختبار مسجل")
    st.markdown("</div>",unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# Mixed Exam
# ════════════════════════════════════════════════════════════════════════════
with tab_mix:
    st.markdown('<div class="section-card-soft">',unsafe_allow_html=True)
    st.markdown('<div class="section-title">الامتحان المجمع</div>',unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">اختبار شامل من مختلف المواد. عند تحقيق 80%+ سيتم توليد شهادة اجتياز PDF تلقائياً.</div>',unsafe_allow_html=True)
    mn=st.number_input("عدد أسئلة الامتحان المجمع",min_value=10,max_value=500,value=30)
    c1,c2,c3=st.columns(3)
    with c1: render_metric_box("نوع الاختبار","شامل","يغطي كل المواد")
    with c2: render_metric_box("النجاح للشهادة","80%","لإصدار شهادة PDF")
    with c3: render_metric_box("عدد الأسئلة",str(mn),"يمكنك تغييره قبل البدء")
    if st.button("🔥 بدء الامتحان المجمع",key="start_mix"):
        tdf=fetch_questions(subject=None,q_type="ميكس",limit=mn)
        if tdf.empty: st.error("لا توجد أسئلة كافية حاليًا.")
        else: start_exam(tdf,"امتحان شامل","MIXED");st.rerun()
    st.markdown("</div>",unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# Library
# ════════════════════════════════════════════════════════════════════════════
with tab_lib:
    st.markdown('<div class="section-card-soft">',unsafe_allow_html=True)
    st.markdown('<div class="section-title">المكتبة الرقمية والتحميل</div>',unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">تصفح الكتب والمذكرات حسب المادة أو استعرض جميع الكتب المتاحة.</div>',unsafe_allow_html=True)
    lib_t=st.tabs(["📚 حسب المادة","🗂️ جميع الكتب"])
    def _book_card(row,idx,prefix,subj_label=None):
        st.markdown('<div class="library-book">',unsafe_allow_html=True)
        b1,b2=st.columns([4.5,1.5])
        cn=book_field(row,"custom_name","كتاب بدون اسم")
        cat=book_field(row,"created_at","غير متاح")
        fn=book_field(row,"file_name","")
        rid=book_field(row,"id",idx)
        sl=subj_label or norm_label(book_field(row,"subject","غير محددة"))
        with b1:
            st.markdown(f"#### {T(cn)}")
            st.markdown(f"<div class='small-muted'>المادة: {T(sl)} — تمت إضافته: {T(cat)}</div>",unsafe_allow_html=True)
        with b2:
            fp=Path("books")/str(fn)
            if fn and fp.exists():
                with open(fp,"rb") as pf:
                    st.download_button("⬇️ تحميل",data=pf,file_name=f"{cn}.pdf",mime="application/pdf",key=f"{prefix}_{idx}_{rid}")
            else: st.caption("الملف غير متوفر")
        st.markdown("</div>",unsafe_allow_html=True)
    with lib_t[0]:
        lsl=st.selectbox("اختر المادة",DISPLAY_SUBJECTS,key="lib_sub")
        bdf=localize_df(get_books_by_subject(SUBJECT_MAP[lsl]),"subject")
        if not bdf.empty:
            st.markdown(f"### 📚 الكتب المتاحة لمادة: {T(lsl)}")
            for i,row in bdf.iterrows(): _book_card(row,i,"dl_s",lsl)
        else: st.info("لا توجد كتب مرفوعة لهذه المادة حاليًا.")
    with lib_t[1]:
        abdf=all_books()
        if not abdf.empty:
            st.markdown("### 🗂️ جميع الكتب المتاحة")
            for i,row in abdf.iterrows(): _book_card(row,i,"dl_a")
        else: st.info("لا توجد كتب مرفوعة داخل المكتبة حالياً.")
    st.markdown('<div class="small-muted" style="margin-top:14px;text-align:center;font-size:14px;">جميع الحقوق محفوظة لمؤلفي الكتب.</div>',unsafe_allow_html=True)
    st.markdown("</div>",unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# Active Exam
# ════════════════════════════════════════════════════════════════════════════
if st.session_state.get("test_active") and st.session_state.get("test_data") is not None:
    st.markdown("---")
    dfq=st.session_state["test_data"]
    if dfq.empty:
        st.error("لا توجد أسئلة للاختبار الحالي.");reset_test()
    else:
        _,el=fmt_elapsed(st.session_state["start_time"])
        tq=len(dfq)
        aq=sum(1 for _,r in dfq.iterrows() if st.session_state["exam_answers"].get(str(int(r["id"]))))
        st.markdown(f"""<div class="exam-head">
          <div class="exam-title">📘 {T(st.session_state["test_subject"])}</div>
          <div>أجب عن الأسئلة التالية، ثم قم بتسليم الاختبار في النهاية.</div>
          <div class="exam-chip-row">
            <div class="exam-chip">⏱️ الوقت: {T(el)}</div>
            <div class="exam-chip">📊 تم الإجابة: {aq} / {tq}</div>
            <div class="exam-chip">⚠️ التحذيرات: {st.session_state.get("warnings_count",0)} / 3</div>
          </div>
        </div>""",unsafe_allow_html=True)
        st.progress(aq/tq if tq else 0,text=f"نسبة التقدم: {aq} من {tq}")
        st.warning("عند الوصول إلى 3 تحذيرات يتم إنهاء الاختبار وتسجيل نتيجة صفرية.")
        w1,w2,_=st.columns([1.4,1.4,5])
        with w1:
            if st.button("تسجيل تحذير",key="warn_btn"):
                st.session_state["warnings_count"]+=1
                if st.session_state["warnings_count"]>=3:
                    save_result(st.session_state["user_name"],st.session_state["user_phone"],
                                st.session_state["test_subject"],0,len(dfq),0.0,
                                "تم إنهاء الاختبار بسبب التحذيرات",st.session_state["warnings_count"])
                    st.session_state.update({"submitted":True,"test_active":False,"last_score":0,
                        "last_total":len(dfq),"last_percent":0.0,
                        "last_time":"تم إنهاء الاختبار بسبب التحذيرات",
                        "last_mistakes":[],"last_all_answers":[],"ai_feedback":None})
                    tg_alert(f"إنهاء بسبب تحذيرات\nالطالب:{st.session_state['user_name']}")
                    notify_student(0,len(dfq),0.0,"تم إنهاء الاختبار بسبب التحذيرات",[],warnings=True)
                    st.error("تم إنهاء الاختبار بسبب الوصول إلى 3 تحذيرات.");st.rerun()
                st.rerun()
        with w2:
            if st.button("إلغاء الاختبار",key="cancel_btn"):
                reset_test();st.rerun()

        # ── Questions ──────────────────────────────────────────────────────
        for i,(_,row) in enumerate(dfq.iterrows()):
            qid=int(row["id"])
            subj=norm_label(row["subject"])
            opts=(["صح","خطأ"] if row["q_type"]!="اختياري"
                  else [str(o).strip() for o in [row["opt1"],row["opt2"],row["opt3"],row["opt4"]] if str(o).strip()])

            st.markdown('<div class="question-card">',unsafe_allow_html=True)
            st.markdown(f'<div class="question-index">سؤال رقم {i+1}</div>',unsafe_allow_html=True)
            st.markdown(f'<div class="question-title">{T(row["question"])}</div>',unsafe_allow_html=True)
            st.markdown(f'<div class="question-meta">المادة: {T(subj)} | النوع: {T(row["q_type"])}</div>',unsafe_allow_html=True)

            render_options(qid, opts, result_mode=False)

            with st.expander("🚩 الإبلاغ عن خطأ في السؤال"):
                note=st.text_area("اكتب ملاحظتك",key=f"flag_note_{qid}")
                if st.button("إرسال البلاغ",key=f"flag_btn_{qid}"):
                    save_flag(qid,row["question"],subj,st.session_state["user_name"],
                              st.session_state["user_phone"],note.strip())
                    st.success("تم إرسال البلاغ بنجاح.")
            st.markdown("</div>",unsafe_allow_html=True)

        if st.button("✅ تسليم وإنهاء الاختبار",key="submit_btn"):
            submit_exam(dfq)


# ════════════════════════════════════════════════════════════════════════════
# Result View
# ════════════════════════════════════════════════════════════════════════════
if st.session_state.get("submitted") and st.session_state.get("last_score") is not None:
    score=st.session_state["last_score"]
    total=st.session_state["last_total"]
    percent=st.session_state["last_percent"]
    time_str=st.session_state["last_time"]
    mistakes=st.session_state.get("last_mistakes",[])
    all_answers=st.session_state.get("last_all_answers",[])
    passed=float(percent)>=50 if isinstance(percent,(int,float)) else False
    warn_c=st.session_state.get("warnings_count",0)
    stopped=(time_str=="تم إنهاء الاختبار بسبب التحذيرات")

    if stopped:   summary=f"تم إيقاف اختبار {st.session_state.get('test_subject','الامتحان')} بسبب الوصول إلى الحد الأقصى من التحذيرات."
    elif passed:  summary=f"أداء ممتاز يا {st.session_state.get('user_name','الطالب')}. حققت {score} من {total} بنسبة {percent}% خلال {time_str}."
    else:         summary=f"تم الانتهاء من {st.session_state.get('test_subject','الامتحان')}. حصلت على {score} من {total} بنسبة {percent}% خلال {time_str}."

    status_html=('<div class="status-badge status-pass">✅ تم اجتياز الامتحان بنجاح</div>'
                 if passed and not stopped
                 else '<div class="status-badge status-fail">❌ لم يتم اجتياز الامتحان</div>')

    st.markdown('<div class="result-shell">',unsafe_allow_html=True)
    st.markdown(f"""<div class="result-hero">
      <div class="result-hero-title">النتيجة النهائية</div>
      <div class="result-hero-subtitle">
        تهانينا <strong>{T(st.session_state.get("user_name","الطالب"))}</strong><br>
        تم الانتهاء من امتحان <strong>{T(st.session_state.get("test_subject","الامتحان"))}</strong><br>
        {status_html}
      </div>
    </div>""",unsafe_allow_html=True)

    st.markdown(f"""<div class="result-grid">
      <div class="result-stat-card"><div class="result-stat-label">الدرجة</div><div class="result-stat-value">{score}/{total}</div><div class="result-stat-note">إجمالي الأسئلة</div></div>
      <div class="result-stat-card"><div class="result-stat-label">النسبة المئوية</div><div class="result-stat-value">{percent}%</div><div class="result-stat-note">مستوى الأداء</div></div>
      <div class="result-stat-card"><div class="result-stat-label">إجابات صحيحة</div><div class="result-stat-value">{score}</div><div class="result-stat-note">عدد الإجابات الصحيحة</div></div>
      <div class="result-stat-card"><div class="result-stat-label">إجابات خاطئة</div><div class="result-stat-value">{max(0,total-score)}</div><div class="result-stat-note">عدد الإجابات الخاطئة</div></div>
      <div class="result-stat-card"><div class="result-stat-label">الوقت المستغرق</div><div class="result-stat-value">{T(time_str)}</div><div class="result-stat-note">مدة أداء الاختبار</div></div>
      <div class="result-stat-card"><div class="result-stat-label">التحذيرات</div><div class="result-stat-value">{warn_c}</div><div class="result-stat-note">عدد التحذيرات المسجلة</div></div>
    </div>""",unsafe_allow_html=True)

    st.markdown(f"""<div class="summary-panel">
      <div class="summary-title">الملخص النهائي</div>
      <div class="summary-text">{T(summary)}</div>
    </div>""",unsafe_allow_html=True)

    if st.session_state.get("test_subject")=="امتحان شامل" and percent>=80 and not stopped:
        if generate_certificate:
            cp=generate_certificate(st.session_state["user_name"],percent,score,total)
            st.success("🏅 مبروك! يمكنك تحميل شهادة الاجتياز.")
            with open(cp,"rb") as f:
                st.download_button("⬇️ تحميل الشهادة PDF",data=f,file_name=Path(cp).name,
                    mime="application/pdf",key=f"cert_{int(time.time())}")
        else: st.info("خدمة إنشاء الشهادة غير متاحة حالياً.")

    # ── مراجعة الأسئلة بألوان النتيجة ──
    if all_answers:
        st.markdown('<div class="mistakes-box">',unsafe_allow_html=True)
        st.markdown('<div class="mistakes-title">مراجعة الأسئلة والشرح</div>',unsafe_allow_html=True)
        for m in all_answers:
            ckey=f"{m['id']}::{m['user']}::{m['correct']}"
            ai_exp=explain(m["subject"],m["question"],m["user"],m["correct"],ckey)
            bc="#22c55e" if m["is_correct"] else "#ef4444"
            ic="✅" if m["is_correct"] else "❌"
            try:
                qrow=st.session_state["test_data"].loc[st.session_state["test_data"]["id"]==m["id"]].iloc[0]
                ropts=(["صح","خطأ"] if qrow["q_type"]!="اختياري"
                       else [str(o).strip() for o in [qrow["opt1"],qrow["opt2"],qrow["opt3"],qrow["opt4"]] if str(o).strip()])
            except: ropts=[]

            st.markdown(f"""<div class="mistake-item" style="border-right-color:{bc};">
              <div class="mistake-q">{ic} {T(m['question'])}</div>""",unsafe_allow_html=True)

            # الاختيارات ملوّنة — result_mode
            render_options(m["id"], ropts, result_mode=True)

            st.markdown(f"""
              <div class="mistake-a" style="margin-top:10px;"><strong>إجابتك:</strong> {T(m['user'])}</div>
              <div class="mistake-a"><strong>الإجابة الصحيحة:</strong> {T(m['correct'])}</div>
              <div class="mistake-a"><strong>شرح مبسط:</strong> {T(ai_exp)}</div>
            </div>""",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)
        if not mistakes: st.balloons();st.success("ممتاز جدًا! إجاباتك كلها صحيحة بدون أي أخطاء.")

    # AI Feedback
    if st.session_state.get("ai_feedback") is None:
        try: st.session_state["ai_feedback"]=ai_feedback_safe(
                st.session_state.get("test_subject","التحول الرقمي"),
                st.session_state.get("user_name","طالب"),mistakes)
        except Exception as e:
            print("ai err:",e)
            st.session_state["ai_feedback"]={"summary_ar":"تعذر إنشاء التغذية الراجعة.","mistakes":[]}

    if st.session_state.get("ai_feedback"):
        af=st.session_state["ai_feedback"]
        st.markdown('<div class="ai-feedback-box">',unsafe_allow_html=True)
        st.markdown('<div class="ai-feedback-title">🤖 تحليل ذكي للأداء</div>',unsafe_allow_html=True)
        st.markdown(f'<div class="ai-feedback-summary">{T(af.get("summary_ar",""))}</div>',unsafe_allow_html=True)
        for idx,item in enumerate(af.get("mistakes",[]),1):
            st.markdown(f"""<div class="ai-feedback-item">
              <div class="mistake-q">{idx}) {T(item.get('question',''))}</div>
              <div class="mistake-a"><strong>إجابتك:</strong> {T(item.get('user_answer',''))}</div>
              <div class="mistake-a"><strong>الإجابة الصحيحة:</strong> {T(item.get('correct_answer',''))}</div>
              <div class="mistake-a"><strong>الشرح:</strong> {T(item.get('brief_explanation_ar',''))}</div>
            </div>""",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

    c1,_=st.columns([1.2,4])
    with c1:
        if st.button("مسح النتيجة من الشاشة",key="clear_res"):
            reset_result();clear_answers();st.rerun()
    st.markdown("</div>",unsafe_allow_html=True)
