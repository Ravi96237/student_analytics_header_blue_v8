# 🎓 Student Performance & Retention Analytics  
**Powered by IBM watsonx.ai — Granite Models**

This project is a smart academic analytics dashboard that empowers institutions to proactively identify student risks, improve placement readiness, and forecast exam outcomes — enabling timely interventions to boost success and retention.

---

## 🚀 Key Features

| Feature | Description |
|--------|-------------|
| **Dropout Risk Prediction** | Flags students at risk using CGPA, backlogs, attendance & warnings |
| **Placement Readiness Analyzer** | Suggests company tier fit (Tier-1/2/3) using projects, internships, skills |
| **Exam Score Forecaster** | Predicts chances of passing including **attendance-credit marks** |
| **Attendance Eligibility Rules** | Automatically checks JNTUH-style criteria: 75% Eligible / 65–75% Condonation / <65% Detention |
| **PDF Report Export** | Combines all analytics into a professional printable format |
| **IBM watsonx.ai Granite Integration** | For real-time AI scoring (optional Demo Mode available) |
| **Modern UI with Blue Analytics Header** | Built using Streamlit with clean UX |

---

## 🧠 Powered by IBM watsonx.ai (Granite)

This app can directly use Granite foundation models hosted on IBM watsonx.ai 🌐  
Just provide your API settings in the sidebar:

- `WATSONX_APIKEY`
- `WATSONX_URL`
- `WATSONX_PROJECT_ID`
- `GRANITE_MODEL_ID`

Or use **Demo Mode** with no internet/API required.

---

## 🏗️ Tech Stack

- **Python**
- **Streamlit**
- **IBM watsonx.ai SDK**
- **Granite Models**
- **ReportLab** (PDF generation)
- **NumPy / Pandas**
- **FAISS** (future student similarity features)

---

## 🔧 Installation

```bash
pip install -r requirements.txt
