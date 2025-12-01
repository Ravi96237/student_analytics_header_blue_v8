"""
SCET – Student Performance & Retention Analytics
Powered by IBM watsonx.ai (Granite)

Version v4 (Attendance Rules Edition):
- Student Name and Roll No mandatory
- Attractive SCET-branded UI
- Dropout, Placement, Exam Forecast
- Attendance-credit-based exam prediction
- JNTUH-style attendance rules (75% eligibility, 65–75% condonation, <65% detention)
- PDF report includes attendance eligibility info
"""

import os
import json
from typing import Tuple, Optional, Dict, Any
from io import BytesIO

import streamlit as st
from dotenv import load_dotenv

# IBM watsonx.ai Granite imports
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.foundation_models.schema import (
    TextGenParameters,
    TextGenDecodingMethod,
)

# PDF generation
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors

# Load .env if present
load_dotenv()

st.set_page_config(
    page_title="SCET – Student Analytics (Granite on watsonx.ai)",
    layout="wide",
    page_icon="🎓",
)


st.markdown(
    '''
    <div style="
        width:100%;
        padding:28px 10px;
        background:linear-gradient(135deg,#0052D4,#4364F7,#6FB1FC);
        border-radius:18px;
        text-align:center;
        color:white;
        font-size:26px;
        font-weight:800;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        box-shadow:0 12px 34px rgba(0,50,150,0.45);
        border:1px solid rgba(255,255,255,0.18);
    ">
        📊 Student Performance & Retention Analytics
    </div>
    ''',
    unsafe_allow_html=True
)



if "reports" not in st.session_state:
    st.session_state["reports"] = {}
if "last_pdf" not in st.session_state:
    st.session_state["last_pdf"] = None

# ------------------
# Global Styling
# ------------------
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.0rem;
            padding-bottom: 2rem;
            padding-left: 2.0rem;
            padding-right: 2.0rem;
        }

        body {
            background: radial-gradient(circle at top left, #e0f2fe 0, #ffffff 55%, #f5f3ff 100%);
        }

        .main-header {
            background: linear-gradient(135deg, #0f172a, #1d4ed8, #4c1d95);
            border-radius: 1.6rem;
            padding: 1.2rem 1.5rem;
            color: white;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1.2rem;
            box-shadow: 0 18px 45px rgba(15, 23, 42, 0.45);
        }

        .main-header-left {
            display: flex;
            gap: 1.0rem;
            align-items: center;
        }

        .main-header-icon {
            width: 78px;
            height: 78px;
            border-radius: 999px;
            background: radial-gradient(circle at 30% 30%, rgba(248, 250, 252, 0.9), rgba(15, 23, 42, 0.15));
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 32px;
            box-shadow: 0 12px 30px rgba(15, 23, 42, 0.5);
            overflow: hidden;
        }

        .college-name {
            font-size: 16px;
            font-weight: 800;
            letter-spacing: 0.13em;
            text-transform: uppercase;
        }

        .college-tagline {
            font-size: 11px;
            opacity: 0.95;
            letter-spacing: 0.06em;
        }

        .main-header-text-title {
            font-size: 21px;
            font-weight: 700;
            margin-top: 0.25rem;
        }

        .pill-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.15rem 0.7rem;
            border-radius: 999px;
            background: rgba(148, 163, 184, 0.35);
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.09em;
        }

        .pill-badge span {
            opacity: 0.95;
        }

        .sub-title-text {
            font-size: 13px;
            opacity: 0.95;
            margin-top: 0.25rem;
        }

        .main-header-right {
            text-align: right;
            font-size: 11px;
        }

        .tag-chip {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.18rem 0.7rem;
            border-radius: 999px;
            background: rgba(22, 163, 74, 0.18);
            font-size: 11px;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .metric-card {
            padding: 0.9rem 1rem;
            border-radius: 1.1rem;
            border: 1px solid rgba(148, 163, 184, 0.38);
            background: rgba(255, 255, 255, 0.96);
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.12);
            backdrop-filter: blur(10px);
        }

        .metric-label {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.11em;
            color: #6b7280;
        }

        .metric-value {
            font-size: 17px;
            font-weight: 600;
            margin-top: 0.15rem;
        }

        .metric-sub {
            font-size: 12px;
            color: #9ca3af;
            margin-top: 0.1rem;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.3rem;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 999px;
            padding-top: 0.35rem;
            padding-bottom: 0.35rem;
            padding-left: 0.85rem;
            padding-right: 0.85rem;
            background-color: rgba(148, 163, 184, 0.16);
            color: #374151;
            font-size: 13px;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #2563eb, #4c1d95) !important;
            color: #f9fafb !important;
        }

        .section-card {
            border-radius: 1.3rem;
            padding: 1.2rem 1.25rem 1.1rem;
            background: rgba(255, 255, 255, 0.98);
            border: 1px solid rgba(209, 213, 219, 0.8);
            box-shadow: 0 10px 32px rgba(15, 23, 42, 0.12);
            backdrop-filter: blur(12px);
        }

        .section-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 0.25rem;
        }

        .section-sub {
            font-size: 13px;
            color: #6b7280;
            margin-bottom: 0.6rem;
        }

        .risk-box {
            padding: 0.78rem 1rem;
            border-radius: 0.95rem;
            font-size: 14px;
            margin-top: 0.55rem;
        }

        .risk-high {
            background: linear-gradient(120deg, rgba(248, 113, 113, 0.08), rgba(239, 68, 68, 0.14));
            border: 1px solid rgba(239, 68, 68, 0.48);
            color: #7f1d1d;
        }

        .risk-medium {
            background: linear-gradient(120deg, rgba(251, 191, 36, 0.09), rgba(245, 158, 11, 0.15));
            border: 1px solid rgba(245, 158, 11, 0.48);
            color: #78350f;
        }

        .risk-low {
            background: linear-gradient(120deg, rgba(34, 197, 94, 0.09), rgba(22, 163, 74, 0.15));
            border: 1px solid rgba(22, 163, 74, 0.5);
            color: #14532d;
        }

        .reco-list li {
            margin-bottom: 0.25rem;
        }

        .small-label {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.11em;
            color: #6b7280;
        }

        footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------
# Helper: Attendance rules (JNTUH style)
# --------------
def attendance_status(att_percent: Optional[float]) -> Optional[Tuple[str, str, str]]:
    """
    Returns (label, message, severity) for attendance rules.
    severity: 'success' | 'warning' | 'error'
    """
    if att_percent is None:
        return None
    try:
        a = float(att_percent)
    except Exception:
        return None

    if a >= 75:
        label = "Eligible for SEE (No condonation required)"
        msg = (
            "Attendance is **≥ 75%** in aggregate. Student is eligible to appear for the "
            "Semester End Examinations (SEE) without condonation, as per attendance rules."
        )
        return label, msg, "success"
    elif 65 <= a < 75:
        label = "Shortage 65–75%: Condonation Possible"
        msg = (
            "Attendance is between **65% and 75%**. Student is **not automatically eligible** for SEE. "
            "Shortage of attendance can be condoned by the College Academic Committee on genuine grounds "
            "with supporting evidence, on payment of the prescribed condonation fee (e.g., Rs. 300/-)."
        )
        return label, msg, "warning"
    else:
        label = "Below 65%: Detention (Not Eligible for SEE)"
        msg = (
            "Attendance is **below 65%** in aggregate. Shortage **cannot be condoned**. "
            "Student is not eligible to take the end examinations for this semester and is liable for detention "
            "with re-registration required in a later semester."
        )
        return label, msg, "error"


def show_attendance_rule_block(title: str, att_percent: Optional[float]):
    status = attendance_status(att_percent)
    if not status:
        return
    label, msg, severity = status
    st.markdown(f"#### 🎯 {title}")
    if severity == "success":
        st.success(f"**{label}**\n\n{msg}")
    elif severity == "warning":
        st.warning(f"**{label}**\n\n{msg}")
    else:
        st.error(f"**{label}**\n\n{msg}")


# --------------
# Header with College Logo & Name
# --------------
hcol1, hcol2 = st.columns([3.0, 1.6])

with hcol1:
    st.markdown(
        """
        
                    <div class="main-header-text-title">
                        Student Analytics Dashboard
                    </div>
                    <div class="sub-title-text">
                        Identify at-risk students, improve placement readiness, and forecast exam results –
                        powered by Granite on IBM watsonx.ai.
                    </div>
                </div>
            </div>
        """,
        unsafe_allow_html=True,
    )

with hcol2:
    st.markdown(
        """
        
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# -----------------
# Student Name & Roll (MANDATORY)
# -----------------
st.write("")
sn_col1, sn_col2, sn_col3 = st.columns([2.2, 2.2, 1.6])
with sn_col1:
    student_name = st.text_input("Student Name *", placeholder="Enter student full name")
with sn_col2:
    student_id = st.text_input("Roll No / ID *", placeholder="e.g., 21CSE1234")
with sn_col3:
    
    mode_label = "Demo Simulation" if os.getenv("DEMO_MODE") == "True" else "Live Granite / API"
    st.markdown(f'<div class="metric-value">{mode_label}</div>', unsafe_allow_html=True)
    st.markdown('<div class="metric-sub">Set in sidebar</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def ensure_student_info() -> bool:
    if not student_name or not student_id:
        st.error("Please enter both **Student Name** and **Roll No / ID** at the top before running analysis or generating report.")
        return False
    return True


# --------------------------
# Sidebar: watsonx + Granite
# --------------------------
st.sidebar.header("⚙️ IBM watsonx.ai Settings")

default_api_key = os.getenv("WATSONX_APIKEY", "")
default_url = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
default_project_id = os.getenv("WATSONX_PROJECT_ID", "")
default_model_id = os.getenv("GRANITE_MODEL_ID", "ibm/granite-3-8b-instruct")

watsonx_api_key = st.sidebar.text_input(
    "WATSONX_APIKEY",
    type="password",
    value=default_api_key,
    help="IBM Cloud API key with watsonx.ai access.",
)

watsonx_url = st.sidebar.text_input(
    "WATSONX_URL",
    value=default_url,
    help="Service URL for watsonx.ai (e.g. https://us-south.ml.cloud.ibm.com).",
)

watsonx_project_id = st.sidebar.text_input(
    "WATSONX_PROJECT_ID",
    value=default_project_id,
    help="Project ID from your watsonx.ai project (Project → Manage → Details).",
)

granite_model_id = st.sidebar.text_input(
    "GRANITE_MODEL_ID",
    value=default_model_id,
    help="Granite model ID (e.g. ibm/granite-3-8b-instruct).",
)

st.sidebar.markdown("---")
demo_mode = st.sidebar.checkbox(
    "Use Demo Mode (no Watsonx call)",
    value=False,
    help="Turn this ON for offline demo (no API calls).",
)
os.environ["DEMO_MODE"] = "True" if demo_mode else "False"

st.sidebar.markdown("---")
st.sidebar.caption(
    "Tip: Add `WATSONX_APIKEY`, `WATSONX_URL`, `WATSONX_PROJECT_ID`, and `GRANITE_MODEL_ID` "
    "in a `.env` file so they load automatically."
)


@st.cache_resource(show_spinner=False)
def get_granite_model(
    api_key: str,
    url: str,
    project_id: str,
    model_id: str,
) -> Tuple[Optional[ModelInference], Optional[str]]:
    if not api_key or not url or not project_id:
        return None, "Missing WATSONX_APIKEY, WATSONX_URL, or WATSONX_PROJECT_ID."
    try:
        creds = Credentials(api_key=api_key, url=url)
        params = TextGenParameters(
            decoding_method=TextGenDecodingMethod.SAMPLE,
            temperature=0.25,
            top_p=0.9,
            max_new_tokens=512,
        )
        model = ModelInference(
            model_id=model_id,
            params=params,
            credentials=creds,
            project_id=project_id,
        )
        return model, None
    except Exception as e:
        return None, f"Error creating Granite model client: {e}"


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    import json as _json
    segments = []
    stack = 0
    start = None
    for i, ch in enumerate(text):
        if ch == "{":
            if stack == 0:
                start = i
            stack += 1
        elif ch == "}":
            if stack > 0:
                stack -= 1
                if stack == 0 and start is not None:
                    segments.append(text[start : i + 1])
                    start = None
    for seg in reversed(segments):
        try:
            return _json.loads(seg)
        except Exception:
            continue
    try:
        return _json.loads(text)
    except Exception:
        return None


def call_granite_for_task(
    task_name: str,
    profile: Dict[str, Any],
    extra_instructions: str = "",
) -> Tuple[Optional[Dict[str, Any]], str]:
    if demo_mode:
        return None, "Demo mode active (local simulated logic used)."

    model, err = get_granite_model(
        watsonx_api_key,
        watsonx_url,
        watsonx_project_id,
        granite_model_id,
    )
    if err:
        return None, err

    prompt = f"""
You are an academic analytics assistant helping college faculty make data-driven decisions.

TASK: {task_name}

STUDENT PROFILE (JSON):
{json.dumps(profile, indent=2)}

{extra_instructions}

Return your answer as a strict JSON object using this schema:
{{
  "risk_level": string,
  "predicted_score": number|null,
  "summary": string,
  "recommendations": [
    "string", "string", "string"
  ]
}}

Important: Return ONLY the JSON. No markdown.
"""
    try:
        generated = model.generate_text(prompt=prompt)
    except Exception as e:
        return None, f"Error calling Granite model: {e}"

    if not isinstance(generated, str):
        generated = str(generated)

    parsed = extract_json_from_text(generated)
    if parsed is None:
        return None, f"Could not parse JSON from model response. Raw output:\n\n{generated}"
    return parsed, ""


def interpretation_box(level: str, message: str):
    lvl = (level or "").lower()
    css_class = "risk-box "
    if any(tag in lvl for tag in ["high", "tier-1", "tier1"]):
        css_class += "risk-high"
    elif any(tag in lvl for tag in ["medium", "moderate", "tier-2", "tier2"]):
        css_class += "risk-medium"
    else:
        css_class += "risk-low"
    st.markdown(
        f'<div class="{css_class}"><b>{level or "Info"}:</b> {message}</div>',
        unsafe_allow_html=True,
    )


def store_report(section_key: str, profile: Dict[str, Any], result: Dict[str, Any]):
    st.session_state["reports"][section_key] = {
        "profile": profile,
        "result": result,
    }


def split_text(text: str, max_chars: int):
    words = text.split()
    line = []
    for w in words:
        if sum(len(x) for x in line) + len(line) + len(w) > max_chars:
            yield " ".join(line)
            line = [w]
        else:
            line.append(w)
    if line:
        yield " ".join(line)


def attendance_status_lines(att_percent: Optional[float]):
    status = attendance_status(att_percent)
    if not status:
        return []
    label, msg, _ = status
    lines = [f"Attendance Eligibility: {label}"]
    for line in split_text(msg, 100):
        lines.append(line)
    return lines


def generate_pdf(student_name: str, student_id: str) -> Optional[bytes]:
    reports = st.session_state.get("reports", {})
    if not reports:
        return None

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 60

    # Header band
    c.setFillColor(colors.HexColor("#0f172a"))
    c.rect(0, y - 40, width, 50, fill=1, stroke=0)
    c.setFillColor(colors.white)

    try:
        logo = ImageReader("scet_logo.jpg")
        c.drawImage(logo, 40, y - 38, width=90, height=40, preserveAspectRatio=True, mask='auto')
    except Exception:
        pass

    c.setFont("Helvetica-Bold", 15)
    c.drawString(150, y - 15, "")
    c.setFont("Helvetica", 10)
    c.drawString(150, y - 30, "Student Performance & Retention Analytics Report")
    y -= 80

    # Student info box
    c.setFillColor(colors.HexColor("#f3f4ff"))
    c.roundRect(30, y - 40, width - 60, 55, 10, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#111827"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y - 15, f"Student Name: {student_name}")
    if student_id:
        c.drawString(300, y - 15, f"Roll No / ID: {student_id}")
    y -= 70

    sections = [
        ("Dropout Risk Analysis", "dropout"),
        ("Placement Readiness", "placement"),
        ("Exam Performance Forecast", "exam"),
    ]

    for section_label, key in sections:
        data = reports.get(key)
        if not data:
            continue
        profile = data.get("profile", {})
        result = data.get("result", {})

        if y < 140:
            c.showPage()
            y = height - 60

        c.setFillColor(colors.HexColor("#1d4ed8"))
        c.roundRect(30, y - 24, width - 60, 22, 8, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(40, y - 10, section_label)
        y -= 32

        c.setFont("Helvetica", 10)
        c.setFillColor(colors.HexColor("#111827"))
        risk_level = str(result.get("risk_level", "N/A"))
        pred_score = result.get("predicted_score", None)
        c.drawString(40, y, f"Level / Tier: {risk_level}")
        y -= 14
        if pred_score is not None:
            c.drawString(40, y, f"Score / Prediction: {pred_score}")
            y -= 16

        summary = str(result.get("summary", ""))
        if summary:
            c.setFont("Helvetica-Oblique", 9)
            c.setFillColor(colors.HexColor("#374151"))
            for line in split_text(summary, 95):
                c.drawString(50, y, line)
                y -= 12

        # Attendance eligibility line (for sections that have attendance)
        att_val = None
        if key == "dropout":
            att_val = profile.get("attendance_percent")
        elif key == "exam":
            att_val = profile.get("attendance_percent")
        if att_val is not None:
            lines = attendance_status_lines(att_val)
            if lines:
                y -= 4
                c.setFont("Helvetica", 9)
                c.setFillColor(colors.HexColor("#111827"))
                for line in lines:
                    c.drawString(50, y, line)
                    y -= 11

        recs = result.get("recommendations", []) or []
        if recs:
            y -= 6
            c.setFont("Helvetica-Bold", 10)
            c.setFillColor(colors.HexColor("#111827"))
            c.drawString(40, y, "Recommendations:")
            y -= 12
            c.setFont("Helvetica", 9)
            for rec in recs:
                for line in split_text(rec, 90):
                    c.drawString(50, y, f"- {line}")
                    y -= 11
                    if y < 80:
                        c.showPage()
                        y = height - 60
                        c.setFont("Helvetica", 9)

        y -= 18

    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(colors.HexColor("#6b7280"))
    c.drawString(40, 40, "Generated using SCET Student Analytics Dashboard (IBM watsonx.ai – Granite).")
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()


# ---------------
# MAIN TABS
# ---------------
tab1, tab2, tab3 = st.tabs(["🧍 Dropout Risk", "💼 Placement Readiness", "✍️ Exam Forecast"])

with tab1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🧍 Student Dropout Predictor</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Identify at-risk students 1–2 semesters in advance and schedule interventions.</div>',
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        cgpa = st.number_input("Current CGPA", 0.0, 10.0, 7.0, 0.1, key="drop_cgpa")
        attendance = st.slider("Attendance (%)", 0, 100, 80, key="drop_att")
    with c2:
        assignments = st.slider("Avg Assignment Score (%)", 0, 100, 75, key="drop_assign")
        warnings = st.number_input("Number of Academic Warnings", 0, 10, 0, key="drop_warn")
    with c3:
        sem = st.selectbox("Current Semester", list(range(1, 9)), key="drop_sem")
        backlog = st.number_input("Active Backlogs", 0, 15, 0, key="drop_backlog")

    if st.button("🔍 Analyze Dropout Risk", key="btn_dropout"):
        if ensure_student_info():
            profile = {
                "cgpa": cgpa,
                "attendance_percent": attendance,
                "avg_assignment_score_percent": assignments,
                "no_of_academic_warnings": warnings,
                "current_semester": sem,
                "active_backlogs": backlog,
            }
            if demo_mode:
                risk_score = 0
                if cgpa < 6: risk_score += 1
                if attendance < 75: risk_score += 1
                if assignments < 60: risk_score += 1
                if warnings >= 2: risk_score += 1
                if backlog >= 2: risk_score += 1
                if risk_score >= 4:
                    level = "High"
                    msg = "Student appears at very high risk of dropout based on academics & engagement indicators."
                elif risk_score >= 2:
                    level = "Medium"
                    msg = "Student is at moderate risk. Timely mentoring and follow-up can prevent escalation."
                else:
                    level = "Low"
                    msg = "Student currently appears low risk, but should still be monitored periodically."
                result = {
                    "risk_level": level,
                    "predicted_score": risk_score,
                    "summary": msg,
                    "recommendations": [
                        "Schedule a 1:1 mentoring or counselling session.",
                        "Share a personalized study roadmap and upcoming assessments.",
                        "Monitor attendance and assignment submissions for the next few weeks.",
                    ],
                }
                interpretation_box(level, msg)
                show_attendance_rule_block("Attendance Eligibility (Dropout Risk)", attendance)
                store_report("dropout", profile, result)
            else:
                with st.spinner("Calling Granite on watsonx.ai for dropout risk analysis..."):
                    result, err = call_granite_for_task(
                        task_name="Student Dropout Risk Prediction",
                        profile=profile,
                        extra_instructions=(
                            "Assess how likely this student is to drop out in the next 1–2 semesters. "
                            "Use 'High', 'Medium', or 'Low' in risk_level."
                        ),
                    )
                if err:
                    st.error(err)
                else:
                    level = result.get("risk_level", "Info")
                    summary = result.get("summary", "")
                    interpretation_box(level, summary)
                    show_attendance_rule_block("Attendance Eligibility (Dropout Risk)", attendance)
                    store_report("dropout", profile, result)
                    recs = result.get("recommendations", []) or []
                    if recs:
                        st.markdown("#### ✅ Granite Recommendations")
                        st.markdown('<ul class="reco-list">', unsafe_allow_html=True)
                        for r in recs:
                            st.markdown(f"<li>{r}</li>", unsafe_allow_html=True)
                        st.markdown("</ul>", unsafe_allow_html=True)
                    with st.expander("🔎 Raw Granite JSON (technical view)", expanded=False):
                        st.code(json.dumps(result, indent=2), language="json")
    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">💼 Placement Success Analyzer</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Estimate which company tier the student is currently ready for (Tier-1 / Tier-2 / Tier-3).</div>',
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        cgpa_p = st.number_input("CGPA", 0.0, 10.0, 7.5, 0.1, key="place_cgpa")
        num_intern = st.number_input("Number of Internships", 0, 10, 1, key="place_intern")
    with c2:
        projects = st.number_input("Number of Major Projects", 0, 10, 2, key="place_projects")
        hackathons = st.number_input("Hackathons / Competitions", 0, 20, 1, key="place_hacks")
    with c3:
        comm_skill = st.slider("Communication Skill (1-10)", 1, 10, 7, key="place_comm")
        tech_skill = st.slider("Technical Skill (1-10)", 1, 10, 8, key="place_tech")

    if st.button("📌 Analyze Placement Readiness", key="btn_placement"):
        if ensure_student_info():
            profile = {
                "cgpa": cgpa_p,
                "internships": num_intern,
                "major_projects": projects,
                "hackathons": hackathons,
                "communication_skill_1_10": comm_skill,
                "technical_skill_1_10": tech_skill,
            }
            if demo_mode:
                score = (cgpa_p / 10) * 0.4 + (tech_skill / 10) * 0.3 + (comm_skill / 10) * 0.2
                score += min(num_intern, 3) * 0.03 + min(projects, 3) * 0.02
                if score >= 0.8:
                    level = "Tier-1"
                    msg = "Strong profile suitable for Tier-1 / Product companies."
                elif score >= 0.6:
                    level = "Tier-2"
                    msg = "Good profile for Tier-2 companies; can push towards Tier-1 with focused prep."
                elif score >= 0.4:
                    level = "Tier-3"
                    msg = "Currently aligned with Tier-3 / service companies; needs improvement for higher tiers."
                else:
                    level = "Not ready"
                    msg = "Placement readiness appears low; intensive training and real-world projects recommended."
                result = {
                    "risk_level": level,
                    "predicted_score": round(score, 2),
                    "summary": msg,
                    "recommendations": [
                        "Encourage participation in contests, hackathons, and technical clubs.",
                        "Recommend building standout portfolio projects (GitHub + live demos).",
                        "Organize mock interviews focusing on problem solving and communication.",
                    ],
                }
                interpretation_box(level, msg)
                store_report("placement", profile, result)
            else:
                with st.spinner("Calling Granite on watsonx.ai for placement analysis..."):
                    result, err = call_granite_for_task(
                        task_name="Placement Success & Company Tier Analysis",
                        profile=profile,
                        extra_instructions=(
                            "Based on this profile, estimate the most likely placement outcome. "
                            "Use 'Tier-1', 'Tier-2', 'Tier-3', or 'Not ready' in risk_level."
                        ),
                    )
                if err:
                    st.error(err)
                else:
                    level = result.get("risk_level", "Unknown")
                    summary = result.get("summary", "")
                    interpretation_box(level, summary)
                    store_report("placement", profile, result)
                    recs = result.get("recommendations", []) or []
                    if recs:
                        st.markdown("#### ✅ Granite Recommendations")
                        st.markdown('<ul class="reco-list">', unsafe_allow_html=True)
                        for r in recs:
                            st.markdown(f"<li>{r}</li>", unsafe_allow_html=True)
                        st.markmarkdown("</ul>", unsafe_allow_html=True)
                    with st.expander("🔎 Raw Granite JSON (technical view)", expanded=False):
                        st.code(json.dumps(result, indent=2), language="json")
    st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">✍️ Exam Performance Forecaster</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Forecast final exam score and identify students who are likely to fail, including attendance-based credits.</div>',
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        ia1 = st.slider("Internal Test 1 (%)", 0, 100, 65, key="exam_ia1")
        ia2 = st.slider("Internal Test 2 (%)", 0, 100, 70, key="exam_ia2")
    with c2:
        quiz = st.slider("Quiz / Online Test Avg (%)", 0, 100, 75, key="exam_quiz")
        attendance_e = st.slider("Attendance (%)", 0, 100, 85, key="exam_att")
    with c3:
        lab_perf = st.slider("Lab Performance (%)", 0, 100, 80, key="exam_lab")
        attendance_credit = st.number_input(
            "Attendance Credits (marks)", 0.0, 10.0, 2.0, 0.5, key="exam_att_credit"
        )
        engagement = st.slider("Class Engagement (1-10)", 1, 10, 7, key="exam_eng")

    if st.button("📈 Forecast Final Exam Score", key="btn_exam"):
        if ensure_student_info():
            profile = {
                "internal_test_1_percent": ia1,
                "internal_test_2_percent": ia2,
                "quiz_average_percent": quiz,
                "attendance_percent": attendance_e,
                "lab_performance_percent": lab_perf,
                "attendance_credits": attendance_credit,
                "class_engagement_1_10": engagement,
            }
            if demo_mode:
                core = (ia1 + ia2 + quiz + lab_perf) / 4
                pred = 0.65 * core + 0.15 * attendance_e + 1.2 * (engagement * 1.5)
                pred += attendance_credit * 1.5  # attendance credit-based boost
                pred = max(0, min(100, pred))
                if pred < 40:
                    level = "High"
                    msg = "Student at high risk of failing. Strong remedial support is needed."
                elif pred < 60:
                    level = "Medium"
                    msg = "Borderline performance. Extra coaching and continuous assessment will help."
                else:
                    level = "Low"
                    msg = "Likely to pass comfortably. Encourage attempting higher-order questions."
                result = {
                    "risk_level": level,
                    "predicted_score": round(pred, 2),
                    "summary": msg + " Attendance credits have been factored into this prediction.",
                    "recommendations": [
                        "Provide topic-wise revision schedules and quizzes.",
                        "Conduct weekly mini-tests to track concept mastery.",
                        "Ensure attendance credits are transparently communicated to the student.",
                    ],
                }
                if isinstance(pred, (int, float)):
                    st.success(f"Predicted Final Exam Score (with attendance credits): {float(pred):.2f} / 100")
                interpretation_box(level, msg)
                show_attendance_rule_block("Attendance Eligibility (Exam)", attendance_e)
                store_report("exam", profile, result)
            else:
                with st.spinner("Calling Granite on watsonx.ai for exam performance forecast..."):
                    result, err = call_granite_for_task(
                        task_name="Final Exam Score Forecasting (with Attendance Credits)",
                        profile=profile,
                        extra_instructions=(
                            "Predict an approximate final exam score out of 100 for this student. "
                            "Consider internal tests, quizzes, lab performance, overall attendance_percent, "
                            "and attendance_credits (marks awarded for high attendance). "
                            "Put the numeric value (0–100) in predicted_score. "
                            "In risk_level, use 'High', 'Medium', or 'Low' to indicate RISK OF FAILING."
                        ),
                    )
                if err:
                    st.error(err)
                else:
                    predicted_score = result.get("predicted_score", None)
                    level = result.get("risk_level", "Unknown")
                    summary = result.get("summary", "")
                    if isinstance(predicted_score, (int, float)):
                        st.success(f"Predicted Final Exam Score (with attendance credits): {float(predicted_score):.2f} / 100")
                    interpretation_box(level, summary)
                    show_attendance_rule_block("Attendance Eligibility (Exam)", attendance_e)
                    store_report("exam", profile, result)
                    recs = result.get("recommendations", []) or []
                    if recs:
                        st.markdown("#### ✅ Granite Recommendations")
                        st.markdown('<ul class="reco-list">', unsafe_allow_html=True)
                        for r in recs:
                            st.markdown(f"<li>{r}</li>", unsafe_allow_html=True)
                        st.markdown("</ul>", unsafe_allow_html=True)
                    with st.expander("🔎 Raw Granite JSON (technical view)", expanded=False):
                        st.code(json.dumps(result, indent=2), language="json")
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------
# PDF SECTION
# ---------------
st.markdown("----")
pc1, pc2 = st.columns([2, 3])
with pc1:
    st.markdown("### 📝 Generate Student PDF Report")
    st.write("Run one or more analyses above, then create a single attractive PDF report for this student.")
    if st.button("📄 Generate PDF Report"):
        if not ensure_student_info():
            st.session_state["last_pdf"] = None
        else:
            pdf_bytes = generate_pdf(student_name, student_id)
            if pdf_bytes is None:
                st.error("No analysis data found. Please run at least one prediction first.")
            else:
                st.session_state["last_pdf"] = pdf_bytes
                st.success("Report generated successfully. Use the download button on the right.")

with pc2:
    if st.session_state.get("last_pdf"):
        st.download_button(
            label="⬇️ Download Latest Report",
            data=st.session_state["last_pdf"],
            file_name=f"{student_name or 'student'}_analytics_report.pdf",
            mime="application/pdf",
        )
    else:
        st.info("Once a report is generated, a download button will appear here.")
