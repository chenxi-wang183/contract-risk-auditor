import streamlit as st
import os
import re
import tempfile
from datetime import datetime
from docx import Document
import pdfplumber
from sop_analyzer import analyze_all   # ← 保留你的逻辑引擎

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="Intelligent Contract Review",
    page_icon="⚖️",
    layout="wide",
)

# -------------------- CUSTOM CSS (Fonts + Layout) --------------------
st.markdown("""
<style>
body, input, textarea, button {
    font-family: 'Times New Roman', serif !important;
}

/* Heading Font */
h1 {
    font-family: 'Times New Roman', serif !important;
}

/* Upload Box */
.upload-box {
    border: 2px dashed #1A4AFF;
    border-radius: 10px;
    padding: 28px;
    background-color:#F9FAFF;
    text-align:center;
    font-weight:600;
    color:#1A4AFF;
    margin-bottom: 18px;
}

/* Centered Download Button (White/Black + Shadow) */
button[kind="secondary"] {
    border-radius: 8px !important;
    border: 1.5px solid #111 !important;
    background-color: #fff !important;
    color:#111 !important;
    padding: 11px 26px !important;
    box-shadow: 0 3px 8px rgba(0,0,0,0.15) !important;
    font-weight:600 !important;
}
button[kind="secondary"]:hover {
    background-color:#F4F4F4 !important;
}
</style>
""", unsafe_allow_html=True)

# -------------------- SIDEBAR --------------------
with st.sidebar:
    st.markdown("### Settings")

    api_key = st.text_input("Enter your OpenAI API Key", type="password")
    if not api_key:
        st.warning("Please enter your API key to use the analyzer.")
    else:
        st.success("API key loaded.")

    st.markdown("---")
    st.markdown("#### Upload History")
    if "history" not in st.session_state:
        st.session_state["history"] = []
    for file in st.session_state["history"]:
        st.markdown(f"- {file}")

# -------------------- HEADER --------------------
st.markdown("""
<div style="text-align:center; margin-top:-10px;">
    <svg width="62" height="62" viewBox="0 0 24 24" fill="none" stroke="#1A4AFF" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
        <line x1="12" y1="1" x2="12" y2="22"></line>
        <path d="M5 6h14"></path>
        <path d="M3 6l4 8 4-8"></path>
        <path d="M13 6l4 8 4-8"></path>
    </svg>
    <h1 style="font-size:44px; font-weight:800; margin-top:6px;">
        Intelligent Contract Review
    </h1>
    <p style="color:#444; font-size:17px;">
        Contract Risk Identification & Clause-Level Legal Assessment for NDAs
    </p>
</div>
""", unsafe_allow_html=True)

# -------------------- UPLOAD AREA --------------------
st.markdown('<div class="upload-box">Drag & Drop Your Contract Here<br>(or Browse Files below)</div>', unsafe_allow_html=True)
uploaded = st.file_uploader("Browse Files", type=["pdf", "docx", "txt"])

# -------------------- TEXT EXTRACTION --------------------
def extract_text(file):
    name = file.name.lower()
    if name.endswith(".txt"):
        return file.read().decode("utf-8", errors="ignore")
    elif name.endswith(".docx"):
        from docx import Document
        doc = Document(file)
        return "\n".join(p.text for p in doc.paragraphs)
    elif name.endswith(".pdf"):
        text = ""
        with pdfplumber.open(file) as pdf:
            for p in pdf.pages:
                t = p.extract_text()
                if t:
                    text += t + "\n"
        return text
    return ""

# -------------------- CLAUSE SPLITTING --------------------
def split_into_clauses(text):
    lines = text.splitlines()
    clauses = []
    current = {"title": None, "content": []}
    pattern = re.compile(r"^\s*(\d+(\.\d+)*)(\.|\))?\s")
    for line in lines:
        if pattern.match(line):
            if current["title"] and current["content"]:
                clauses.append({"title": current["title"], "text": "\n".join(current["content"]).strip()})
            current = {"title": line.strip(), "content": []}
        else:
            current["content"].append(line)
    if current["title"] and current["content"]:
        clauses.append({"title": current["title"], "text": "\n".join(current["content"]).strip()})
    return clauses

# -------------------- MAIN LOGIC --------------------
if uploaded and api_key:
    text = extract_text(uploaded)
    st.session_state["history"].append(uploaded.name)

    clauses = split_into_clauses(text)
    results, counters = analyze_all(clauses)

    # --- RISK SUMMARY BAR ---
    st.markdown(
        f"""
        <div style="display:flex; justify-content:center; gap:38px; margin: 16px 0 30px 0; font-size:18px;">
            <div style="color:#D64545; font-weight:600;">■ Red: {counters.get('RED',0)}</div>
            <div style="color:#E6A700; font-weight:600;">■ Yellow: {counters.get('YELLOW',0)}</div>
            <div style="color:#198754; font-weight:600;">■ Green: {counters.get('GREEN',0)}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # --- CLAUSE OUTPUT CARDS + legal tone enhancement ---
    from explain_llm import enhance_explanation
    for r in results:
        r["risk"] = enhance_explanation(api_key, r["original_excerpt"], r["risk"], r["suggestion"])

    for r in results:
        color = {"RED": "#D64545","YELLOW": "#E6A700","GREEN": "#198754"}[r["level"]]
        st.markdown(
            f"""
            <div style="border-left:6px solid {color}; padding:14px; margin:12px 0; background:#F7F9FF;">
              <b>{r["title"]}</b> — {r["level"]}
              <br><br><b>(1) Original (excerpt):</b><br>{r["original_excerpt"]}
              <br><br><b>(2) Risk Analysis:</b><br>{r["risk"]}
              <br><br><b>(3) Suggested Revision:</b><br>{r["suggestion"]}
            </div>
            """,
            unsafe_allow_html=True
        )

# -------------------- REPORT GENERATION --------------------
def save_report(results):
    from docx.shared import RGBColor
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement

    doc = Document()
    doc.add_heading("NDA Risk Assessment Report", level=1)

    date = datetime.now().strftime("%Y-%m-%d")
    doc.add_paragraph(f"Generated on: {date}\n")

    for r in results:
        heading = doc.add_heading(level=2)
        run = heading.add_run(f"{r['title']} — {r['level']}")
        if r["level"] == "RED":
            run.font.color.rgb = RGBColor(214, 69, 69)
        elif r["level"] == "YELLOW":
            run.font.color.rgb = RGBColor(230, 167, 0)
        else:
            run.font.color.rgb = RGBColor(25, 135, 84)

        p = doc.add_paragraph()
        run = p.add_run("")
        p_format = p._p.get_or_add_pPr()
        border = OxmlElement('w:pBdr')
        left = OxmlElement('w:left')
        left.set(qn('w:val'), 'single')
        left.set(qn('w:sz'), '18')
        left.set(qn('w:space'), '4')
        left.set(qn('w:color'),
                 'D64545' if r["level"] == "RED"
                 else 'E6A700' if r["level"] == "YELLOW"
                 else '198754')
        border.append(left)
        p_format.append(border)

        doc.add_paragraph("(1) Original (excerpt):")
        doc.add_paragraph(r["original_excerpt"])
        doc.add_paragraph("(2) Risk Analysis:")
        doc.add_paragraph(r["risk"])
        doc.add_paragraph("(3) Suggested Revision:")
        doc.add_paragraph(r["suggestion"])
        doc.add_paragraph("")

    path = os.path.join(tempfile.gettempdir(), "NDA_Risk_Report.docx")
    doc.save(path)
    return path

# -------------------- DOWNLOAD --------------------
if uploaded and api_key:
    report_path = save_report(results)
    with open(report_path, "rb") as f:
        report_bytes = f.read()

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True)

    # left-aligned download placement
    col_left, col_right = st.columns([1, 3])  # 左列放内容，右列空出来

    with col_left:
        st.markdown(
            """
            <div style="text-align:left; margin-bottom:8px;">
                <span style="font-size:18px; font-weight:600;">Download Full Report</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.download_button(
            label="Download Full Report (.docx)",
            data=report_bytes,
            file_name="NDA_Risk_Report.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key="download_report_left",
            help="Download the NDA Legal Risk Report",
            use_container_width=False
        )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)