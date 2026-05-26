"""
Digital Maturity - Full Streamlit Application
Run with: streamlit run site.py

Required packages (install if missing):
    pip install streamlit requests beautifulsoup4 fpdf2 google-generativeai
"""

import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from fpdf import FPDF
import google.generativeai as genai
import io
import base64
import re
import os

# ============================================================
# CONFIGURATION
# ============================================================

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash-lite"

genai.configure(api_key=GOOGLE_API_KEY)

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="DigiMetrica",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# SESSION STATE INIT
# ============================================================

def init_session():
    defaults = {
        "page": "Home",
        "test_answers": {},
        "test_done": False,
        "dmi_score": 0,
        "ai_recommendation": "",
        "ai_loading": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

# ============================================================
# GLOBAL CSS
# ============================================================

def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');

    /* ---- Reset & Base ---- */
    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
        background-color: #07080d;
        color: #e8eaf0;
    }
    .stApp {
        background: #07080d;
    }

    /* ---- Hide Streamlit chrome ---- */
    #MainMenu, footer, header { visibility: hidden; }
    .block-container {
        padding-top: 0 !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        padding-bottom: 0 !important;

        max-width: 1400px !important;
        margin: 0 auto !important;
    }

    /* ---- Scrollbar ---- */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: #0e0f17; }
    ::-webkit-scrollbar-thumb { background: #2563eb; border-radius: 4px; }

    /* ---- Navbar ---- */
    .navbar {
        position: sticky;
        top: 0;
        z-index: 999;
        background: rgba(7,8,13,0.92);
        backdrop-filter: blur(16px);
        border-bottom: 1px solid rgba(255,255,255,0.07);
        padding: 0 80px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        height: 64px;
    }
    .navbar-logo {
        font-family: 'Syne', sans-serif;
        font-weight: 800;
        font-size: 22px;
        color: #fff;
        letter-spacing: -0.5px;
        white-space: nowrap;
    }
    .navbar-logo span { color: #2563eb; }
    .navbar-links {
        display: flex;
        gap: 4px;
        align-items: center;
    }
    .nav-btn {
        background: transparent;
        border: none;
        color: rgba(255,255,255,0.6);
        font-family: 'DM Sans', sans-serif;
        font-size: 14px;
        font-weight: 500;
        padding: 8px 16px;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
        white-space: nowrap;
        text-decoration: none;
    }
    .nav-btn:hover { color: #fff; background: rgba(255,255,255,0.07); }
    .nav-btn.active {
        color: #fff;
        background: rgba(37,99,235,0.18);
        border: 1px solid rgba(37,99,235,0.35);
    }

    /* ---- Page wrapper ---- */
    .page-wrap {
        max-width: 1000px;
        margin: 0 auto;
        padding: 0px 24px 0px;
    }

    /* ---- Hero ---- */
    .hero {
        position: relative;
        padding: 100px 0 80px;
        text-align: center;
        overflow: hidden;
    }
    .hero-bg {
        position: absolute; inset: 0;
        background: radial-gradient(ellipse 80% 60% at 50% 0%, rgba(37,99,235,0.22) 0%, transparent 70%);
        pointer-events: none;
    }
    .hero-tag {
        display: inline-block;
        background: rgba(37,99,235,0.15);
        border: 1px solid rgba(37,99,235,0.4);
        color: #60a5fa;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 2px;
        text-transform: uppercase;
        padding: 6px 16px;
        border-radius: 100px;
        margin-bottom: 28px;
    }
    .hero h1 {
        font-family: 'Syne', sans-serif;
        font-size: clamp(48px, 7vw, 88px);
        font-weight: 800;
        line-height: 1.0;
        color: #fff;
        letter-spacing: -2px;
        margin: 0 0 24px;
    }
    .hero h1 span { color: #2563eb; }
    .hero-sub {
        font-size: 18px;
        color: rgba(255,255,255,0.55);
        max-width: 580px;
        margin: 0 auto 48px !important;
        line-height: 1.7;
        font-weight: 300;
        text-align: center !important;
    }

    /* ---- Buttons ---- */
    .btn-primary {
        display: inline-block;
        background: #2563eb;
        color: #fff !important;
        font-family: 'DM Sans', sans-serif;
        font-size: 16px;
        font-weight: 600;
        padding: 16px 40px;
        border-radius: 12px;
        border: none;
        cursor: pointer;
        text-decoration: none;
        transition: all 0.25s ease;
        box-shadow: 0 0 40px rgba(37,99,235,0.35);
    }
    .btn-primary:hover {
        background: #1d4ed8;
        box-shadow: 0 0 60px rgba(37,99,235,0.5);
        transform: translateY(-2px);
    }
    .btn-secondary {
        display: inline-block;
        background: rgba(255,255,255,0.06);
        color: #fff !important;
        font-family: 'DM Sans', sans-serif;
        font-size: 15px;
        font-weight: 500;
        padding: 12px 28px;
        border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.12);
        cursor: pointer;
        text-decoration: none;
        transition: all 0.2s ease;
    }
    .btn-secondary:hover {
        background: rgba(255,255,255,0.10);
        border-color: rgba(255,255,255,0.2);
    }

    /* ---- Section titles ---- */
    .section-label {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 3px;
        text-transform: uppercase;
        color: #2563eb;
        margin-bottom: 12px;
    }
    .section-title {
        font-family: 'Syne', sans-serif;
        font-size: clamp(28px, 4vw, 44px);
        font-weight: 800;
        color: #fff;
        letter-spacing: -1px;
        margin: 0 0 16px;
        line-height: 1.15;
    }
    .section-sub {
        font-size: 16px;
        color: rgba(255,255,255,0.5);
        max-width: 520px;
        line-height: 1.7;
    }

    /* ---- Cards ---- */
    .card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 20px;
        padding: 32px;
        transition: all 0.3s ease;
    }
    .card:hover {
        background: rgba(255,255,255,0.07);
        border-color: rgba(37,99,235,0.35);
        transform: translateY(-4px);
        box-shadow: 0 20px 60px rgba(0,0,0,0.4);
    }
    .card-icon {
        font-size: 32px;
        margin-bottom: 16px;
    }
    .card h3 {
        font-family: 'Syne', sans-serif;
        font-size: 20px;
        font-weight: 700;
        color: #fff;
        margin: 0 0 10px;
    }
    .card p {
        font-size: 14px;
        color: rgba(255,255,255,0.5);
        line-height: 1.7;
        margin: 0;
    }

    /* ---- Pricing cards ---- */
    .pricing-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 32px;
        margin-top: 48px;
        padding: 28px;
    }
    .pricing-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 24px;
        padding: 36px 28px;
        position: relative;
        transition: all 0.3s ease;
    }
    .pricing-card:hover { transform: translateY(-4px); }
    .pricing-card.featured {
        background: linear-gradient(160deg, rgba(37,99,235,0.25) 0%, rgba(37,99,235,0.08) 100%);
        border-color: rgba(37,99,235,0.5);
        box-shadow: 0 0 80px rgba(37,99,235,0.2);
    }
    .pricing-badge {
        position: absolute;
        top: -14px;
        left: 50%;
        transform: translateX(-50%);
        background: #2563eb;
        color: #fff;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        padding: 5px 16px;
        border-radius: 100px;
        white-space: nowrap;
    }
    .pricing-name {
        font-family: 'Syne', sans-serif;
        font-size: 22px;
        font-weight: 700;
        color: #fff;
        margin-bottom: 8px;
    }
    .pricing-price {
        font-family: 'Syne', sans-serif;
        font-size: 48px;
        font-weight: 800;
        color: #fff;
        line-height: 1;
        margin: 20px 0 4px;
    }
    .pricing-price span {
        font-size: 18px;
        font-weight: 400;
        color: rgba(255,255,255,0.4);
    }
    .pricing-desc {
        font-size: 13px;
        color: rgba(255,255,255,0.45);
        margin: 16px 0 24px;
        line-height: 1.6;
    }
    .pricing-feature {
        font-size: 13px;
        color: rgba(255,255,255,0.65);
        padding: 8px 0;
        border-bottom: 1px solid rgba(255,255,255,0.06);
        display: flex;
        gap: 10px;
        align-items: flex-start;
    }
    .pricing-feature:last-child { border-bottom: none; }
    .pricing-check { color: #2563eb; font-size: 15px; flex-shrink: 0; }

    /* ---- CTA Section ---- */
    .cta-section {
        text-align: center;
        padding: 80px 0 20px;
        margin-bottom: 120px;
    }

    /* ---- Divider ---- */
    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent);
        margin: 90px 0;
    }

    /* ---- Test page ---- */
    .test-header {
        text-align: center;
        padding: 48px 0 32px;
    }
    .question-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 28px 32px;
        margin-bottom: 16px;
        transition: border-color 0.2s;
    }
    .question-card.answered { border-color: rgba(37,99,235,0.3); }
    .question-card.unanswered { border-color: rgba(239,68,68,0.4); }
    .q-number {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #2563eb;
        margin-bottom: 8px;
    }
    .q-text {
        font-size: 16px;
        font-weight: 500;
        color: #fff;
        margin-bottom: 16px;
        line-height: 1.5;
    }

    /* ---- Radio buttons override ---- */
    .stRadio > label { display: none !important; }
    .stRadio [data-testid="stMarkdownContainer"] p {
        font-size: 14px !important;
        color: rgba(255,255,255,0.75) !important;
    }
    .stRadio div[role="radiogroup"] {
        gap: 6px !important;
    }
    .stRadio div[role="radiogroup"] label {
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 10px !important;
        padding: 10px 16px !important;
        cursor: pointer !important;
        transition: all 0.15s !important;
    }
    .stRadio div[role="radiogroup"] label:hover {
        background: rgba(37,99,235,0.12) !important;
        border-color: rgba(37,99,235,0.3) !important;
    }

    /* ---- Result ---- */
    .result-hero {
        text-align: center;
        padding: 48px 0 32px;
    }
    .result-score {
        font-family: 'Syne', sans-serif;
        font-size: 96px;
        font-weight: 800;
        color: #fff;
        line-height: 1;
    }
    .result-score span { color: #2563eb; }
    .result-label {
        font-size: 20px;
        color: rgba(255,255,255,0.5);
        margin-top: 8px;
    }
    .metric-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
    }
    .metric-val {
        font-family: 'Syne', sans-serif;
        font-size: 36px;
        font-weight: 700;
        color: #fff;
    }
    .metric-lbl {
        font-size: 12px;
        color: rgba(255,255,255,0.4);
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-top: 4px;
    }
    .ai-box {
        background: rgba(37,99,235,0.08);
        border: 1px solid rgba(37,99,235,0.25);
        border-radius: 20px;
        padding: 36px;
        margin-top: 32px;
    }
    .ai-box h3 {
        font-family: 'Syne', sans-serif;
        font-size: 22px;
        font-weight: 700;
        color: #fff;
        margin-bottom: 16px;
    }
    .ai-box p {
        font-size: 15px;
        color: rgba(255,255,255,0.7);
        line-height: 1.8;
        max-width: 700px;
    }
    .action-row {
        display: flex;
        gap: 16px;
        justify-content: center;
        flex-wrap: wrap;
        margin-top: 40px;
        padding-bottom: 60px;
    }

    /* ---- News ---- */
    .news-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 20px;
        overflow: hidden;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    .news-card:hover {
        border-color: rgba(37,99,235,0.4);
        transform: translateY(-4px);
        box-shadow: 0 20px 60px rgba(0,0,0,0.4);
    }
    .news-img {
        width: 100%;
        height: 200px;
        object-fit: cover;
    }
    .news-body { padding: 20px 22px; }
    .news-source {
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #2563eb;
        margin-bottom: 8px;
    }
    .news-title {
        font-family: 'Syne', sans-serif;
        font-size: 16px;
        font-weight: 700;
        color: #fff;
        line-height: 1.4;
        margin-bottom: 12px;
    }
    .news-link {
        font-size: 13px;
        color: #60a5fa;
        text-decoration: none;
    }
    .news-link:hover { text-decoration: underline; }

    /* ---- General Info / Timeline ---- */
    .timeline-item {
        display: flex;
        gap: 24px;
        margin-bottom: 40px;
        position: relative;
    }
    .timeline-dot {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: rgba(37,99,235,0.2);
        border: 2px solid #2563eb;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        flex-shrink: 0;
        margin-top: 4px;
    }
    .timeline-content h4 {
        font-family: 'Syne', sans-serif;
        font-size: 18px;
        font-weight: 700;
        color: #fff;
        margin: 0 0 8px;
    }
    .timeline-content p {
        font-size: 14px;
        color: rgba(255,255,255,0.55);
        line-height: 1.7;
        margin: 0;
    }

    /* ---- Cabinet ---- */
    .cabinet-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 24px 28px;
        margin-bottom: 14px;
        cursor: pointer;
        transition: all 0.2s;
    }
    .cabinet-card:hover {
        border-color: rgba(37,99,235,0.35);
        background: rgba(255,255,255,0.06);
    }
    .cabinet-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 10px;
    }
    .cabinet-title {
        font-family: 'Syne', sans-serif;
        font-size: 18px;
        font-weight: 700;
        color: #fff;
    }
    .cabinet-score {
        font-family: 'Syne', sans-serif;
        font-size: 28px;
        font-weight: 800;
        color: #2563eb;
    }
    .tag {
        display: inline-block;
        background: rgba(37,99,235,0.15);
        border: 1px solid rgba(37,99,235,0.3);
        color: #60a5fa;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
        padding: 3px 10px;
        border-radius: 100px;
    }
    .tag.trial { background: rgba(16,185,129,0.12); border-color: rgba(16,185,129,0.3); color: #34d399; }
    .expand-content {
        margin-top: 20px;
        padding-top: 20px;
        border-top: 1px solid rgba(255,255,255,0.07);
    }
    .answer-row {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        font-size: 13px;
        gap: 12px;
    }
    .answer-q { color: rgba(255,255,255,0.55); flex: 1; }
    .answer-a { color: rgba(255,255,255,0.85); font-weight: 500; text-align: right; max-width: 55%; }

    /* ---- Account ---- */
    .account-grid {
        display: grid;
        grid-template-columns: 1fr auto;
        gap: 40px;
        align-items: start;
    }
    .account-name {
        font-family: 'Syne', sans-serif;
        font-size: 36px;
        font-weight: 800;
        color: #fff;
        margin-bottom: 4px;
    }
    .account-email {
        font-size: 15px;
        color: rgba(255,255,255,0.45);
        margin-bottom: 32px;
    }
    .info-row {
        display: flex;
        gap: 16px;
        margin-bottom: 16px;
        align-items: center;
    }
    .info-label {
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: rgba(255,255,255,0.3);
        width: 120px;
        flex-shrink: 0;
    }
    .info-val {
        font-size: 15px;
        color: rgba(255,255,255,0.85);
    }
    .avatar {
        width: 96px;
        height: 96px;
        border-radius: 50%;
        background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'Syne', sans-serif;
        font-size: 36px;
        font-weight: 800;
        color: #fff;
        border: 3px solid rgba(37,99,235,0.5);
        box-shadow: 0 0 40px rgba(37,99,235,0.3);
    }
    .stats-row {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 16px;
        margin-top: 32px;
    }
    .stat-box {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 20px;
        text-align: center;
    }
    .stat-num {
        font-family: 'Syne', sans-serif;
        font-size: 32px;
        font-weight: 800;
        color: #2563eb;
    }
    .stat-txt {
        font-size: 12px;
        color: rgba(255,255,255,0.4);
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 4px;
    }

    /* ---- Stagger animation ---- */
    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(24px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .fade-up { animation: fadeUp 0.55s ease forwards; }
    .delay-1 { animation-delay: 0.1s; opacity: 0; }
    .delay-2 { animation-delay: 0.2s; opacity: 0; }
    .delay-3 { animation-delay: 0.3s; opacity: 0; }
    .delay-4 { animation-delay: 0.4s; opacity: 0; }

    /* ---- Streamlit widget overrides ---- */
    .stButton > button {
        background: #2563eb !important;
        color: #fff !important;
        border: none !important;
        border-radius: 10px !important;
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        padding: 12px 28px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 24px rgba(37,99,235,0.3) !important;
        width: auto !important; 
        min-width: 220px !important;
    }
    .stButton > button:hover {
        background: #1d4ed8 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 8px 32px rgba(37,99,235,0.45) !important;
    }
    div[data-testid="stProgress"] > div > div {
        background-color: #2563eb !important;
        border-radius: 10px !important;
    }
    div[data-testid="stProgress"] > div {
        background-color: rgba(255,255,255,0.08) !important;
        border-radius: 10px !important;
        height: 10px !important;
    }
    .stAlert { border-radius: 12px !important; }

    /* ---- Misc ---- */
    a { color: #60a5fa; }
    strong { color: #fff; }
    </style>
    """, unsafe_allow_html=True)

inject_css()

# ============================================================
# QUESTIONS & ANSWERS
# ============================================================
# Each question has a list of options (A, B, C, D, E).
# The score for each option is its index + 1 (A=1, B=2, C=3, D=4, E=5).
# EDIT THE OPTIONS BELOW TO ADD YOUR ACTUAL ANSWER CHOICES.

QUESTIONS = [
    {
        "id": 1,
        "text": "Do you have a clear plan or strategy for the company's development in the digital direction for at least 1-2 years?",
        "options": [
            # --- INSERT YOUR ANSWER OPTIONS FOR QUESTION 1 BELOW ---
            "Not at all",
            "Only common ideas",
            "There is an approximate plan",
            "There is a prescribed plan, but we rarely update it",
            "There is a clear document with goals and deadlines that we regularly use",
        ]
    },
    {
        "id": 2,
        "text": "How often do you or the director personally deal with business digitalization issues?",
        "options": [
            # --- INSERT YOUR ANSWER OPTIONS FOR QUESTION 2 BELOW ---
            "Almost never",
            "Only on serious problems",
            "Sometimes",
            "Regularly",
            "Constantly",
        ]
    },
    {
        "id": 3,
        "text": "Do you use sales, customer and competitor data when making important decisions?",
        "options": [
            # --- INSERT YOUR ANSWER OPTIONS FOR QUESTION 3 BELOW ---
            "No",
            "Sometimes we watch simple reports",
            "We regularly look at basic statistics",
            "We use detailed analytics",
            "Yes, this is the basis of almost all important decisions",
        ]
    },
    {
        "id": 4,
        "text": "How comfortable are your employees working with a computer, programs and digital tools?",
        "options": [
            # --- INSERT YOUR ANSWER OPTIONS FOR QUESTION 4 BELOW ---
            "Many people feel insecure",
            "Only basic skills (Excel, Word, Messengers)",
            "They work normally with the main programs",
            "They have a good command of the necessary tools",
            "Employees confidently work with modern digital tools",
        ]
    },
    {
        "id": 5,
        "text": "Do you train employees in new programs and applications?",
        "options": [
            # --- INSERT YOUR ANSWER OPTIONS FOR QUESTION 5 BELOW ---
            "No",
            "Only when it’s necessary",
            "Sometimes",
            "Regularly",
            "Ongoing practice of training",
        ]
    },
    {
        "id": 6,
        "text": "Can your employees offer and implement new digital tools themselves?",
        "options": [
            # --- INSERT YOUR ANSWER OPTIONS FOR QUESTION 6 BELOW ---
            "No",
            "They can offer, but it doesn’t go any further",
            "Sometimes ideas are accepted",
            "Employee ideas are often reviewed and implemented",
            "Employees are actively involved in digitalization",
        ]
    },
    {
        "id": 7,
        "text": "How related are your main programs (accounting, sales, warehouse, payments)?",
        "options": [
            # --- INSERT YOUR ANSWER OPTIONS FOR QUESTION 7 BELOW ---
            "Everything works separately",
            "Partially connected",
            "Most of the programs are integrated",
            "Almost everything works in a single system",
            "Full integration of all key systems",
        ]
    },
    {
        "id": 8,
        "text": "What solutions do you mainly use for the company's work?",
        "options": [
            # --- INSERT YOUR ANSWER OPTIONS FOR QUESTION 8 BELOW ---
            "Only local programs on computers",
            "A mixture of local and cloud",
            "Mostly cloud services",
            "Modern cloud platforms and integrations",
            "Advanced cloud solutions with automation",
        ]
    },
    {
        "id": 9,
        "text": "How are things going with the automation of repetitive tasks (accounts, reminders, reports, etc.)?",
        "options": [
            # --- INSERT YOUR ANSWER OPTIONS FOR QUESTION 9 BELOW ---
            "It’s not automated ",
            "Automated quite a bit",
            "Automated the main routine tasks",
            "Most of the recurring tasks are automated",
            "Maximum process automation",
        ]
    },
    {
        "id": 10,
        "text": "How much do you understand the behavior of your customers (where do they come from, what do they need, why do they leave)?",
        "options": [
            # --- INSERT YOUR ANSWER OPTIONS FOR QUESTION 10 BELOW ---
            "Superficially",
            "There is a general understanding",
            "There is basic analytics",
            "We understand customer behavior well",
            "There is a deep analysis of the client through data",
        ]
    },
    {
        "id": 11,
        "text": "Do you use personalization for different customers?",
        "options": [
            # --- INSERT YOUR ANSWER OPTIONS FOR QUESTION 11 BELOW ---
            "No",
            "Sometimes",
            "Moderate",
            "Well personalized",
            "Strong personalization",
        ]
    },
    {
        "id": 12,
        "text": "How convenient is it for the client to buy from you or contact the company?",
        "options": [
            # --- INSERT YOUR ANSWER OPTIONS FOR QUESTION 12 BELOW ---
            "Only by phone or in person",
            "There are basic online channels (WhatsApp, Instagram)",
            "There is a website and messengers",
            "Convenient website and several communication channels",
            "Very convenient online purchase process and support",
        ]
    },
    {
        "id": 13,
        "text": "How automated are the company's internal processes (accounting, procurement, order fulfillment)?",
        "options": [
            # --- INSERT YOUR ANSWER OPTIONS FOR QUESTION 13 BELOW ---
            "Not at all",
            "Partially",
            "Many processes are automated",
            "Most of the processes are automated",
            "High level of automation",
        ]
    },
    {
        "id": 14,
        "text": "How often do you use data and reports in business management?",
        "options": [
            # --- INSERT YOUR ANSWER OPTIONS FOR QUESTION 14 BELOW ---
            "Almost never",
            "Sometimes",
            "Regularly",
            "Often",
            "We make decisions mainly based on data",
        ]
    },
    {
        "id": 15,
        "text": "How are things going with customer data protection and backup?",
        "options": [
            # --- INSERT YOUR ANSWER OPTIONS FOR QUESTION 15 BELOW ---
            "There is almost no protection",
            "There is a basic protection",
            "We make a backup",
            "Good protection and regular copying",
            "High level of data security",
        ]
    },
]

# ============================================================
# NAVIGATION
# ============================================================

PAGES = ["Home", "News", "General Info", "Cabinet", "Account"]

def render_navbar():
    current = st.session_state.page
    nav_html = f"""
    <div class="navbar">
        <div class="navbar-logo">Digi <span>Metrica</span></div>
        <div class="navbar-links" id="nav-links">
    """
    for p in PAGES:
        active_class = "active" if current == p else ""
        nav_html += f'<button class="nav-btn {active_class}" onclick="void(0)">{p}</button>'
    nav_html += "</div></div>"
    st.markdown(nav_html, unsafe_allow_html=True)

    # Real navigation with Streamlit columns
    cols = st.columns(len(PAGES) + 2)
    for i, p in enumerate(PAGES):
        with cols[i + 1]:
            # Invisible but clickable
            if st.button(p, key=f"nav_{p}", help=None, use_container_width=True):
                st.session_state.page = p
                st.rerun()

    st.markdown("""
    <style>
    /* Hide the actual streamlit nav buttons but keep them clickable */
    div[data-testid="column"] .stButton > button {
        opacity: 0 !important;
        position: absolute !important;
        top: -64px !important;
        height: 64px !important;
        border-radius: 0 !important;
        background: transparent !important;
        box-shadow: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================================
# HOME PAGE
# ============================================================

def page_home():
    st.markdown('<div class="page-wrap">', unsafe_allow_html=True)

    # --- Hero ---
    st.markdown("""
    <div class="hero fade-up">
        <div class="hero-bg"></div>
        <div class="hero-tag">AI-Powered Assessment Platform</div>
        <h1>DigiMetrica<br><span></span></h1>
        <p class="hero-sub">
            Discover where your company stands on the digital transformation spectrum.
            Get an AI-driven analysis and a personalised roadmap to the next level.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Start trial CTA in hero
    col_l, col_c, col_r = st.columns([2, 1, 2])
    with col_c:
        if st.button("Start Trial Test", key="hero_start"):
            st.session_state.page = "Test"
            st.rerun()

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # --- What we do ---
    st.markdown("""
    <div class="fade-up delay-1">
        <div class="section-label">What We Do</div>
        <div class="section-title">Measure. Understand.<br>Transform.</div>
        <p class="section-sub">
            The DigiMetrica is a structured 15-question assessment that evaluates
            your company across strategy, people, data, process, and technology dimensions.
            Upon completion, our AI engine provides a tailored action plan to accelerate
            your digital transformation journey.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # --- Advantages ---
    st.markdown("""
    <div class="section-label">Why Choose Us</div>
    <div class="section-title">Our Advantages</div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    advantages = [
        ("⚡", "AI Recommendations",
         "Powered by Gemini AI, each report comes with highly specific, prioritised action steps tailored to your unique digital profile."),
        ("📊", "Fast Analytics",
         "Complete the assessment in under 10 minutes and receive an instant Digital Maturity score with detailed dimensional breakdown."),
        ("🎯", "Personalised Insights",
         "No generic advice. Every recommendation is generated from your actual responses, giving you insights that are truly relevant to your business."),
    ]
    for col, (icon, title, desc) in zip([c1, c2, c3], advantages):
        with col:
            st.markdown(f"""
            <div class="card fade-up delay-2">
                <div class="card-icon">{icon}</div>
                <h3>{title}</h3>
                <p>{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # --- Pricing ---
    st.markdown("""
    <div class="section-label">Pricing</div>
    <div class="section-title">Subscription Plans</div>
    <p class="section-sub">Choose the plan that fits your organisation's needs and scale as you grow.</p>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="pricing-grid">
        <div class="pricing-card">
            <div class="pricing-name">Starter</div>
            <div class="pricing-price">9,900₸<span>/month</span></div>
            <div class="pricing-desc">Perfect for small businesses taking their first step into digital self-assessment.</div>
            <div class="pricing-feature"><span class="pricing-check">✓</span> Digital Maturity assessment</div>
            <div class="pricing-feature"><span class="pricing-check">✓</span> Overall DMI score</div>
            <div class="pricing-feature"><span class="pricing-check">✓</span> Basic analytics summary</div>
            <div class="pricing-feature"><span class="pricing-check">✓</span> 1 assessment per month</div>
        </div>
        <div class="pricing-card featured">
            <div class="pricing-badge">Best Offer</div>
            <div class="pricing-name">Pro</div>
            <div class="pricing-price">15,000₸<span>/month</span></div>
            <div class="pricing-desc">Ideal for growing companies that need deeper analysis and AI-driven strategic guidance.</div>
            <div class="pricing-feature"><span class="pricing-check">✓</span> Everything in Basic</div>
            <div class="pricing-feature"><span class="pricing-check">✓</span> Full AI-generated recommendations</div>
            <div class="pricing-feature"><span class="pricing-check">✓</span> Dimensional score breakdown</div>
            <div class="pricing-feature"><span class="pricing-check">✓</span> PDF export with full report</div>
            <div class="pricing-feature"><span class="pricing-check">✓</span> Unlimited assessments</div>
        </div>
        <div class="pricing-card">
            <div class="pricing-name">Enterprise</div>
            <div class="pricing-price">25,000₸<span>/month</span></div>
            <div class="pricing-desc">For enterprises that demand comprehensive reporting and long-term strategic planning support.</div>
            <div class="pricing-feature"><span class="pricing-check">✓</span> Everything in Premium</div>
            <div class="pricing-feature"><span class="pricing-check">✓</span> Strategic transformation roadmap</div>
            <div class="pricing-feature"><span class="pricing-check">✓</span> Multi-team assessments</div>
            <div class="pricing-feature"><span class="pricing-check">✓</span> Comparative industry benchmarking</div>
            <div class="pricing-feature"><span class="pricing-check">✓</span> Priority AI model access</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # --- CTA ---
    st.markdown("""
    <div class="cta-section fade-up delay-3">
        <div class="section-label">Get Started</div>
        <div class="section-title">Ready to discover your<br>Digital Maturity level?</div>
        <p class="section-sub" style="margin: 0 auto 40px;">
            Take the free 15-question assessment and receive an instant AI-powered report
            with actionable recommendations for your business.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_l2, col_c2, col_r2 = st.columns([2, 1, 2])
    with col_c2:
        if st.button("Start Trial Test  →", key="cta_start"):
            st.session_state.page = "Test"
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# TEST PAGE
# ============================================================

def calculate_score(answers: dict) -> int:
    """Calculate Digital Maturity Index as a percentage (0-100)."""
    total = sum(answers.values())
    max_score = len(QUESTIONS) * 5  # 15 * 5 = 75
    return round((total / max_score) * 100)


def get_level(score: int) -> tuple:
    """Return (level_name, color, description) based on score."""
    if score < 25:
        return "Beginner", "#ef4444", "Your organisation is at the very start of its digital journey."
    elif score < 45:
        return "Developing", "#f97316", "Some digital foundations are in place but significant gaps remain."
    elif score < 65:
        return "Intermediate", "#eab308", "Good digital progress with clear opportunities for acceleration."
    elif score < 80:
        return "Advanced", "#22c55e", "Strong digital capabilities across most dimensions."
    else:
        return "Leader", "#2563eb", "You are operating at the forefront of digital maturity."


def get_ai_recommendation(answers: dict, score: int) -> str:
    """Call Gemini AI and return recommendation string."""
    qa_lines = []
    for q in QUESTIONS:
        qid = q["id"]
        if qid in answers:
            chosen_idx = answers[qid] - 1
            chosen_text = q["options"][chosen_idx] if chosen_idx < len(q["options"]) else "Unknown"
            qa_lines.append(f"Q{qid}: {q['text']}\nAnswer: {chosen_text} (score {answers[qid]}/5)")

    qa_text = "\n\n".join(qa_lines)

    prompt = f"""
You are a senior digital transformation consultant analysing a company's Digital Maturity Assessment results.

The company's overall DigiMetrica Index is {score}%.

Below are their responses to each assessment question:

{qa_text}

Based on these results, please write a professional, executive-level Digital Maturity Report in the following structure:

1. EXECUTIVE SUMMARY (2-3 sentences)
2. KEY STRENGTHS (identify 2-3 areas where the company is performing well)
3. CRITICAL GAPS (identify the 3 weakest areas based on low scores)
4. STRATEGIC RECOMMENDATIONS (provide 4-5 concrete, prioritised action steps the company should take in the next 6-12 months)
5. LONG-TERM ROADMAP (brief 2-3 year outlook)

Use clear business language. Be specific and actionable. Avoid generic advice.
Do not use bullet symbols - use numbered lists or plain text formatting.
"""

    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        raise RuntimeError(f"Gemini API error: {e}")


def page_test():
    if st.session_state.test_done:
        render_results()
        return

    st.markdown('<div class="page-wrap">', unsafe_allow_html=True)
    st.markdown("""
    <div class="test-header fade-up">
        <div class="section-label">Assessment</div>
        <div class="section-title">DigiMetrica Index</div>
        <p class="section-sub" style="margin: 0 auto;">
            Answer all 15 questions honestly to receive an accurate assessment of
            your company's digital maturity level.
        </p>
    </div>
    """, unsafe_allow_html=True)

    answered = len(st.session_state.test_answers)
    progress = answered / len(QUESTIONS)
    st.progress(progress)
    st.markdown(f'<p style="text-align:right; font-size:13px; color:rgba(255,255,255,0.4); margin-top:6px;">{answered} / {len(QUESTIONS)} answered</p>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    show_validation = st.session_state.get("show_validation", False)

    for q in QUESTIONS:
        qid = q["id"]
        is_answered = qid in st.session_state.test_answers
        card_class = "question-card"
        if show_validation and not is_answered:
            card_class += " unanswered"
        elif is_answered:
            card_class += " answered"

        st.markdown(f"""
        <div class="{card_class}">
            <div class="q-number">Question {qid} of {len(QUESTIONS)}</div>
            <div class="q-text">{q['text']}</div>
        </div>
        """, unsafe_allow_html=True)

        current_val = st.session_state.test_answers.get(qid, None)
        # Build options display (no A/B/C labels shown)
        options_display = q["options"]

        # Find index if already answered
        idx = None
        if current_val is not None:
            idx = current_val - 1

        selected = st.radio(
            label=f"q_{qid}",
            options=options_display,
            index=idx,
            key=f"radio_{qid}",
            label_visibility="collapsed",
        )

        if selected is not None:
            score_val = options_display.index(selected) + 1
            st.session_state.test_answers[qid] = score_val

        st.markdown("<br>", unsafe_allow_html=True)

    # Validation error
    if show_validation:
        missing = [q["id"] for q in QUESTIONS if q["id"] not in st.session_state.test_answers]
        if missing:
            st.error(f"⚠️ Please answer all questions before submitting. Missing: {len(missing)} question(s).")

    col_l, col_c, col_r = st.columns([2, 1, 2])
    with col_c:
        if st.button("Finish Test", key="finish_test"):
            missing = [q["id"] for q in QUESTIONS if q["id"] not in st.session_state.test_answers]
            if missing:
                st.session_state.show_validation = True
                st.rerun()
            else:
                st.session_state.show_validation = False
                score = calculate_score(st.session_state.test_answers)
                st.session_state.dmi_score = score
                st.session_state.test_done = True

                # Get AI recommendation
                with st.spinner("Generating your AI-powered report..."):
                    try:
                        rec = get_ai_recommendation(st.session_state.test_answers, score)
                        st.session_state.ai_recommendation = rec
                    except RuntimeError as e:
                        st.session_state.ai_recommendation = f"Error: {e}"
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


def render_results():
    score = st.session_state.dmi_score
    level, level_color, level_desc = get_level(score)
    ai_rec = st.session_state.ai_recommendation

    st.markdown('<div class="page-wrap">', unsafe_allow_html=True)

    # Score hero
    st.markdown(f"""
    <div class="result-hero fade-up">
        <div class="section-label">Assessment Complete</div>
        <div class="result-score"><span>{score}</span>%</div>
        <div class="result-label">Your Index</div>
        <div style="margin-top:16px; display:inline-block; background:rgba({_hex_to_rgb(level_color)},0.15); border:1px solid {level_color}; color:{level_color}; padding:6px 18px; border-radius:100px; font-weight:700; font-size:14px; letter-spacing:1px;">
            {level.upper()}
        </div>
        <p style="font-size:15px; color:rgba(255,255,255,0.5); margin-top:10px;">{level_desc}</p>
    </div>
    """, unsafe_allow_html=True)

    # Progress bar
    st.progress(score / 100)

    st.markdown("<br>", unsafe_allow_html=True)

    # Metric cards
    total_points = sum(st.session_state.test_answers.values())
    max_points = len(QUESTIONS) * 5
    avg = total_points / len(QUESTIONS)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-val">{score}%</div>
            <div class="metric-lbl">DMI Score</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-val">{total_points}/{max_points}</div>
            <div class="metric-lbl">Total Points</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-val">{avg:.1f}/5</div>
            <div class="metric-lbl">Avg per Question</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Answers summary
    st.markdown('<div class="section-title" style="font-size:24px;">Your Responses</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    for q in QUESTIONS:
        qid = q["id"]
        ans_idx = st.session_state.test_answers.get(qid, 1) - 1
        ans_text = q["options"][ans_idx] if ans_idx < len(q["options"]) else "-"
        pts = st.session_state.test_answers.get(qid, 0)
        st.markdown(f"""
        <div class="answer-row">
            <div class="answer-q"><strong style="color:rgba(255,255,255,0.35)">Q{qid}.</strong> {q['text']}</div>
            <div class="answer-a">{ans_text} <span style="color:#2563eb;">({pts}/5)</span></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # AI Recommendation
    st.markdown("""
    <div class="ai-box fade-up">
        <h3>🤖 AI-Powered Recommendation</h3>
    """, unsafe_allow_html=True)

    if ai_rec.startswith("Error:"):
        st.error(ai_rec)
    else:
        # Render AI text with line breaks
        formatted = ai_rec.replace("\n", "<br>")
        st.markdown(f'<p style="font-size:15px; color:rgba(255,255,255,0.75); line-height:1.9;">{formatted}</p>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Action buttons
    st.markdown('<div class="action-row">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Retake Test", key="retake"):
            st.session_state.test_answers = {}
            st.session_state.test_done = False
            st.session_state.dmi_score = 0
            st.session_state.ai_recommendation = ""
            st.session_state.show_validation = False
            st.rerun()

    with col2:
        if st.button("🏠 Return Home", key="return_home"):
            st.session_state.page = "Home"
            st.rerun()

    with col3:
        pdf_bytes = generate_pdf(
            score=score,
            level=level,
            answers=st.session_state.test_answers,
            ai_rec=ai_rec,
        )
        st.download_button(
            label="📄 Save as PDF",
            data=pdf_bytes,
            file_name=f"digital_maturity_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf",
            key="download_pdf",
        )

    st.markdown('</div></div>', unsafe_allow_html=True)


def _hex_to_rgb(hex_color: str) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"{r},{g},{b}"

# ============================================================
# PDF EXPORT
# ============================================================

class DMIPdf(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(37, 99, 235)
        self.cell(0, 10, "DigiMetrica Index - Assessment Report", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(37, 99, 235)
        self.set_line_width(0.5)
        self.line(10, 18, 200, 18)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()} | Digital Maturity Platform", align="C")


def _clean_text(text: str) -> str:
    """Remove characters that fpdf latin-1 cannot encode."""
    replacements = {
        "\u2014": "-", "\u2013": "-", "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"', "\u2022": "-", "\u2026": "...",
        "\u00a0": " ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Remove any remaining non-latin-1 characters
    text = text.encode("latin-1", errors="replace").decode("latin-1")
    return text


def generate_pdf(score: int, level: str, answers: dict, ai_rec: str) -> bytes:
    pdf = DMIPdf()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Date
    pdf.set_font("Helvetica", size=9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 8, f"Date: {datetime.now().strftime('%B %d, %Y - %H:%M')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Score block
    pdf.set_fill_color(37, 99, 235)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 28)
    pdf.cell(0, 18, f"DigiMetrica Index: {score}%", align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=12)
    pdf.set_fill_color(20, 30, 70)
    pdf.cell(0, 10, f"Level: {level}", align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)

    # Answers
    pdf.set_text_color(30, 30, 30)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(37, 99, 235)
    pdf.cell(0, 10, "Your Responses", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(200, 200, 200)
    pdf.set_line_width(0.3)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

    for q in QUESTIONS:
        qid = q["id"]
        ans_idx = answers.get(qid, 1) - 1
        ans_text = q["options"][ans_idx] if ans_idx < len(q["options"]) else "-"
        pts = answers.get(qid, 0)

        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(60, 60, 60)
        q_text = _clean_text(f"Q{qid}. {q['text']}")
        pdf.multi_cell(0, 6, q_text, new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", size=9)
        pdf.set_text_color(37, 99, 235)
        ans_display = _clean_text(f"   Answer: {ans_text}  [{pts}/5]")
        pdf.multi_cell(0, 6, ans_display, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    pdf.ln(6)

    # AI Recommendation
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(37, 99, 235)
    pdf.cell(0, 10, "AI-Powered Recommendation", new_x="LMARGIN", new_y="NEXT")
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    pdf.set_font("Helvetica", size=10)
    pdf.set_text_color(30, 30, 30)

    if ai_rec.startswith("Error:"):
        pdf.multi_cell(0, 7, _clean_text(ai_rec), new_x="LMARGIN", new_y="NEXT")
    else:
        for paragraph in ai_rec.split("\n"):
            paragraph = _clean_text(paragraph.strip())
            if not paragraph:
                pdf.ln(3)
                continue
            # Bold section headers (all-caps lines like "1. EXECUTIVE SUMMARY")
            if re.match(r"^\d+\.", paragraph) and paragraph == paragraph.upper():
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(37, 99, 235)
                pdf.multi_cell(0, 7, paragraph, new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", size=10)
                pdf.set_text_color(30, 30, 30)
            else:
                pdf.multi_cell(0, 7, paragraph, new_x="LMARGIN", new_y="NEXT")

    output = io.BytesIO()
    pdf.output(output)
    return output.getvalue()

# ============================================================
# NEWS PAGE
# ============================================================

def fetch_techcrunch_news(limit=6):
    """Parse TechCrunch front page for news cards."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    try:
        resp = requests.get("https://techcrunch.com/", headers=headers, timeout=12)
        resp.raise_for_status()
    except requests.RequestException as e:
        return None, f"Could not reach TechCrunch: {e}"

    soup = BeautifulSoup(resp.text, "html.parser")

    articles = []

    # Primary selector from spec
    query_block = soup.find("div", class_=lambda c: c and "wp-block-query" in c and "is-layout-flow" in c)
    if query_block:
        ul = query_block.find("ul", class_=lambda c: c and "wp-block-post-template" in c)
        if ul:
            li_items = ul.find_all("li", recursive=False)[:limit]
            for li in li_items:
                title_tag = li.find("h2") or li.find("h3") or li.find("a")
                link_tag = li.find("a", href=True)
                img_tag = li.find("img")

                title = title_tag.get_text(strip=True) if title_tag else "No title"
                link = link_tag["href"] if link_tag else "#"
                img = img_tag.get("src") or img_tag.get("data-src") or "" if img_tag else ""

                if not link.startswith("http"):
                    link = "https://techcrunch.com" + link

                articles.append({"title": title, "link": link, "image": img})

    # Fallback: find all article tags
    if not articles:
        for article in soup.find_all("article")[:limit]:
            title_tag = article.find(["h2", "h3"])
            link_tag = article.find("a", href=True)
            img_tag = article.find("img")

            title = title_tag.get_text(strip=True) if title_tag else "No title"
            link = link_tag["href"] if link_tag else "#"
            img = img_tag.get("src") or img_tag.get("data-src") or "" if img_tag else ""

            if not link.startswith("http"):
                link = "https://techcrunch.com" + link

            articles.append({"title": title, "link": link, "image": img})

    if not articles:
        return None, "Could not parse articles. TechCrunch may have changed its structure."

    return articles[:limit], None


def page_news():
    st.markdown('<div class="page-wrap">', unsafe_allow_html=True)
    st.markdown("""
    <div class="fade-up">
        <div class="section-label">Latest</div>
        <div class="section-title">Tech News</div>
        <p class="section-sub">Live stories from TechCrunch - the pulse of the technology industry.</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    with st.spinner("Fetching latest news from TechCrunch..."):
        articles, error = fetch_techcrunch_news()

    if error:
        st.error(f"⚠️ {error}")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # Render 2 rows of 3
    for row_start in range(0, len(articles), 3):
        cols = st.columns(3)
        for col, article in zip(cols, articles[row_start:row_start + 3]):
            with col:
                img_html = (
                    f'<img class="news-img" src="{article["image"]}" alt="news image" onerror="this.style.display=\'none\'">'
                    if article["image"]
                    else '<div style="height:140px; background:rgba(37,99,235,0.1); border-radius:0;"></div>'
                )
                title = article["title"][:90] + ("..." if len(article["title"]) > 90 else "")
                st.markdown(f"""
                <div class="news-card">
                    {img_html}
                    <div class="news-body">
                        <div class="news-source">TechCrunch</div>
                        <div class="news-title">{title}</div>
                        <a class="news-link" href="{article['link']}" target="_blank" rel="noopener">Read article →</a>
                    </div>
                </div>
                <br>
                """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# GENERAL INFO PAGE
# ============================================================

def page_general_info():
    st.markdown('<div class="page-wrap">', unsafe_allow_html=True)

    st.markdown("""
    <div class="fade-up">
        <div class="section-label">About the Project</div>
        <div class="section-title">General Information</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # About section
    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown("""
        <div class="fade-up delay-1">
            <div class="section-label">Mission</div>
            <h2 style="font-family:'Syne',sans-serif; font-size:28px; font-weight:800; color:#fff; margin:0 0 16px;">
                Empowering companies to understand<br>and advance their digital readiness
            </h2>
            <p style="font-size:15px; color:rgba(255,255,255,0.55); line-height:1.8; margin-bottom:16px;">
                Digital Maturity is an AI-powered assessment platform designed to help organisations of all
                sizes gain a clear, data-driven picture of where they stand on the digital transformation
                spectrum - and what concrete steps to take next.
            </p>
            <p style="font-size:15px; color:rgba(255,255,255,0.55); line-height:1.8;">
                The platform evaluates five key dimensions: <strong>Strategy, People, Data, Process,</strong>
                and <strong>Technology</strong>. Each dimension is mapped to specific assessment questions,
                and together they produce a composite DigiMetrica Index (DMI) score.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="card fade-up delay-2" style="height:100%;">
            <div style="font-size:40px; margin-bottom:16px;">🎓</div>
            <h3>Academic Context</h3>
            <p>
                This project was developed as a <strong>graduation thesis</strong> exploring the intersection
                of digital transformation research and applied AI technology. The assessment framework is
                grounded in established academic models of digital maturity including the Gartner Digital
                Dexterity model and the MIT CISR Digital Maturity Framework.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Timeline
    st.markdown("""
    <div class="section-label">Journey</div>
    <div class="section-title" style="margin-bottom:40px;">Project Timeline</div>
    """, unsafe_allow_html=True)

    timeline_items = [
        ("💡", "The Idea",
         "The concept for Digital Maturity emerged from a deep interest in digital transformation and how it affects businesses of all sizes. The founder, Madina Turgumbay, observed that many organisations lacked a simple, structured way to assess their own digital readiness - prompting the development of this platform."),
        ("📚", "Research Phase",
         "Extensive research was conducted into existing digital maturity frameworks, industry reports from Gartner, McKinsey, and Deloitte, and academic literature on organisational digital capability. This phase shaped the assessment taxonomy and the weighting logic behind the DMI score."),
        ("🛠️", "Development",
         "The platform was built using Python and Streamlit, integrating Google's Gemini AI model for real-time analysis. The development prioritised accessibility - ensuring that any company could take the assessment without requiring technical expertise or expensive consultants."),
        ("🤖", "AI Integration",
         "Integration with the Gemini 2.5 Flash Lite model enables the generation of personalised, business-grade recommendations for every assessment. The AI prompt was carefully engineered to produce structured, executive-level reports rather than generic outputs."),
        ("🎓", "Thesis Submission",
         "This project was submitted as a graduation thesis, demonstrating the practical application of AI and modern web technologies in the field of digital business consulting. The platform represents both a functional product and a contribution to applied research in digital transformation."),
    ]

    for icon, title, desc in timeline_items:
        st.markdown(f"""
        <div class="timeline-item fade-up">
            <div class="timeline-dot">{icon}</div>
            <div class="timeline-content">
                <h4>{title}</h4>
                <p>{desc}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Founder
    st.markdown("""
    <div class="section-label">Team</div>
    <div class="section-title" style="margin-bottom:32px;">Founder</div>
    """, unsafe_allow_html=True)

    fc1, fc2 = st.columns([1, 3])
    with fc1:
        st.markdown("""
        <div style="width:100px; height:100px; border-radius:50%; background:linear-gradient(135deg,#2563eb,#7c3aed);
             display:flex; align-items:center; justify-content:center;
             font-family:'Syne',sans-serif; font-size:36px; font-weight:800; color:#fff;
             border:3px solid rgba(37,99,235,0.5); box-shadow:0 0 40px rgba(37,99,235,0.3);">
            MT
        </div>
        """, unsafe_allow_html=True)
    with fc2:
        st.markdown("""
        <div class="fade-up delay-2">
            <div style="font-family:'Syne',sans-serif; font-size:26px; font-weight:800; color:#fff; margin-bottom:4px;">
                Madina Turgumbay
            </div>
            <div style="font-size:13px; color:#60a5fa; margin-bottom:12px; letter-spacing:1px; text-transform:uppercase; font-weight:600;">
                Founder & Developer
            </div>
            <p style="font-size:14px; color:rgba(255,255,255,0.55); line-height:1.8; max-width:560px;">
                Madina is the creator of the Digital Maturity platform and the author of the underlying
                assessment methodology. Her academic work focuses on the practical challenges companies
                face during digital transformation and how structured self-assessment tools can accelerate
                organisational change. The goal of this project is to make professional-grade digital
                consulting accessible to every business, regardless of size or budget.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# CABINET PAGE (pre-loaded historical tests)
# ============================================================

CABINET_TESTS = [
    {
        "id": 1,
        "date": "May 12, 2025",
        "score": 58,
        "type": "Basic",
        "answers": {
            1: ("We have a basic plan but rarely follow it", 3),
            2: ("Occasionally - a few times per year", 3),
            3: ("We sometimes refer to basic reports", 3),
            4: ("Average level - most can use standard programs", 3),
            5: ("We train employees occasionally but inconsistently", 3),
            6: ("Some employees suggest ideas but implementation is slow", 3),
            7: ("Partial integration exists between some key systems", 3),
            8: ("Mix of spreadsheets, some cloud tools and messaging apps", 3),
            9: ("Several repetitive tasks are automated", 3),
            10: ("We track some basic metrics like website visits or sales", 3),
            11: ("We segment customers and tailor some communications", 3),
            12: ("Moderate convenience with some digital contact channels", 3),
            13: ("Partly automated but major steps still require manual effort", 2),
            14: ("Occasionally - when a specific problem appears", 2),
            15: ("Some policies exist but compliance is inconsistent", 2),
        },
        "recommendation": """EXECUTIVE SUMMARY
This assessment reflects a company at an intermediate stage of digital maturity with a score of 58%. While foundational digital processes are present across most dimensions, several critical gaps in automation, data utilization, and internal process integration are limiting the company's ability to scale and compete effectively in an increasingly digital marketplace.

KEY STRENGTHS
1. Digital Awareness - The organisation demonstrates a baseline commitment to digital tools, including the use of cloud-based applications and some cross-functional data sharing. This suggests leadership-level recognition of digital transformation as a business priority.
2. Customer-Facing Channels - The company has established moderate digital contact channels, which provide customers with acceptable interaction options. This represents a solid foundation for omnichannel expansion.
3. Process Awareness - There is an emerging awareness of automation opportunities, with several repetitive tasks already automated. This indicates a workforce that is open to process improvement.

CRITICAL GAPS
1. Strategy Execution Gap - While a digital strategy exists on paper, the lack of consistent follow-through suggests it is not embedded in day-to-day management decisions. Strategy must transition from a document to a living operational framework.
2. Data Underutilization - Despite collecting some metrics, data is not systematically used to drive decisions. The organisation is leaving significant value on the table by not operationalizing its data assets.
3. Internal Process Automation - With major operational steps still requiring manual effort, the company faces scalability limitations and elevated error rates. Accounting, procurement, and fulfillment workflows should be prioritized for automation investment.

STRATEGIC RECOMMENDATIONS
1. Establish a Digital Transformation Office or assign a dedicated Digital Lead responsible for tracking KPIs against the digital roadmap on a monthly basis.
2. Implement a Business Intelligence tool such as Power BI or Tableau to centralise reporting and enable data-driven weekly operational reviews.
3. Conduct a process audit to identify the top 5 highest-volume manual workflows and automate them within the next 6 months using tools such as Zapier, Make, or a dedicated ERP module.
4. Develop a structured digital skills training programme with quarterly learning goals, covering both existing tools and emerging technologies relevant to the industry.
5. Integrate your core business systems - accounting, CRM, and order management - to reduce manual data entry and improve cross-departmental visibility.

LONG-TERM ROADMAP
Over a 2-3 year horizon, the company should aim to reach the Advanced maturity tier by establishing predictive analytics capabilities, achieving full process automation in core departments, and building a customer data platform that enables personalisation at scale. The ultimate goal is to make data the primary driver of every significant business decision."""
    },
    {
        "id": 2,
        "date": "April 3, 2025",
        "score": 34,
        "type": "Trial",
        "answers": {
            1: ("We have some informal thoughts, nothing documented", 2),
            2: ("Rarely - only when a problem arises", 2),
            3: ("We collect data but rarely use it", 2),
            4: ("Employees manage basic tasks but avoid new tools", 2),
            5: ("Training happens only when there is a critical issue", 2),
            6: ("Very rarely - initiative is not encouraged", 2),
            7: ("Some data is manually transferred between systems", 2),
            8: ("Basic tools like Excel and email only", 2),
            9: ("A few small automations exist but nothing systematic", 2),
            10: ("We know a little from direct conversations only", 2),
            11: ("Minimal personalization based on broad categories", 2),
            12: ("Basic contact options but the process is cumbersome", 2),
            13: ("Mostly manual with a few spreadsheet helpers", 2),
            14: ("Rarely - only during annual reviews", 2),
            15: ("Minimal measures - basic password protection only", 2),
        },
        "recommendation": """EXECUTIVE SUMMARY
The assessment reveals a DigiMetrica of 34%, placing this organisation firmly in the Developing stage. While there is evident awareness of digital tools and some early adoption of basic technologies, the company is operating significantly below its potential. Immediate and structured action is required to prevent a widening competitive gap with more digitally mature peers.

KEY STRENGTHS
1. Technology Awareness - The organisation is using basic digital tools such as email and spreadsheets, indicating that staff are not completely unfamiliar with digital processes. This provides a manageable starting point for broader digital adoption.
2. Openness to Assessment - The willingness to undertake this assessment suggests that leadership is beginning to recognise the importance of digital maturity. This mindset is the essential precondition for all transformation work.

CRITICAL GAPS
1. Absence of Digital Strategy - There is no documented digital direction, which means digital investments are ad hoc and disconnected. Without a strategy, even well-intentioned digital initiatives will fail to deliver cumulative value.
2. Reactive Management Culture - The pattern of addressing digital issues only when problems arise creates a firefighting dynamic that prevents proactive innovation. Management must shift from reactive to strategic in its approach to technology.
3. Data Blindness - Decisions are made almost entirely by intuition, with collected data going largely unused. This exposes the company to significant risk in market assessment, customer understanding, and operational planning.
4. Low Digital Skill Base - The workforce's reluctance to adopt new tools will be the primary bottleneck to any digital programme. People capability development must be a parallel track to any technology investment.

STRATEGIC RECOMMENDATIONS
1. Develop and formally adopt a 12-month Digital Roadmap that identifies 3 to 5 priority initiatives, assigns ownership, and sets measurable milestones. Review this roadmap in monthly leadership meetings.
2. Replace spreadsheet-based management with a cloud-based tool such as Notion, Monday.com, or a lightweight CRM like HubSpot Free to establish basic operational visibility.
3. Invest in a structured digital literacy programme for all staff, beginning with the most critical tool areas: communication, data entry, and customer management.
4. Implement a simple data review ritual: a weekly 30-minute team meeting that reviews 3 to 5 key business metrics to start building a data-informed decision culture.
5. Conduct an immediate cybersecurity audit and implement multi-factor authentication, regular password policies, and a daily cloud backup routine to protect business-critical data.

LONG-TERM ROADMAP
Within 2 years, the company should target the Intermediate maturity tier by completing foundational system integrations, establishing consistent data reporting practices, and implementing automation in at least 3 core operational workflows. The focus in years 2 to 3 should shift toward customer intelligence - understanding behaviour patterns and beginning personalised engagement strategies."""
    },
    {
        "id": 3,
        "date": "February 18, 2025",
        "score": 72,
        "type": "Basic",
        "answers": {
            1: ("We have a clear documented strategy we mostly follow", 4),
            2: ("Regularly - at least monthly", 4),
            3: ("We regularly use data and analytics", 4),
            4: ("Most are comfortable with new tools and learn quickly", 4),
            5: ("We have a structured onboarding for new tools", 4),
            6: ("Employees regularly suggest and trial new tools", 4),
            7: ("Most systems share data with minimal manual work", 4),
            8: ("Dedicated business software with cloud storage and collaboration", 4),
            9: ("Most routine tasks are automated with clear workflows", 4),
            10: ("We have good analytics on customer journey and churn reasons", 4),
            11: ("We use behavioral data to personalize offers and messages", 4),
            12: ("Convenient with multiple channels and reasonably fast response", 4),
            13: ("Largely automated with digital workflows for most processes", 3),
            14: ("Regularly - monthly or weekly reviews", 3),
            15: ("Solid data protection with regular backups and access control", 3),
        },
        "recommendation": """EXECUTIVE SUMMARY
With a DigiMetrica Index of 72%, this organisation has achieved a strong Advanced level of digital maturity. The company demonstrates well-developed capabilities across strategy, people, customer engagement, and process automation. The primary opportunity now lies in converting good digital practices into exceptional ones - moving from reactive optimisation to proactive digital leadership.

KEY STRENGTHS
1. Strategic Alignment - The organisation maintains a documented digital strategy that is actively followed, with leadership engaging in digitalization issues on a regular basis. This top-down commitment creates the cultural foundation for sustained digital progress.
2. People and Culture - Employees are comfortable with digital tools, proactively suggest improvements, and receive structured onboarding for new technologies. This level of digital fluency is a significant competitive asset and accelerates the adoption of future innovations.
3. Customer Intelligence - The company has meaningful analytics on customer journeys, churn drivers, and behavioural patterns, and is leveraging this data for personalisation. This customer-centric digital capability directly drives commercial performance.

CRITICAL GAPS
1. Full Process Automation - While most routine tasks are automated, some major steps in accounting and procurement still require manual intervention. Moving to end-to-end automation with real-time exception alerts would eliminate the remaining inefficiency and reduce human error.
2. Data Security Maturity - Existing data protection measures are solid but have not yet reached enterprise-grade compliance standards. As the organisation grows, the absence of a formal cybersecurity framework and compliance certifications becomes an increasing liability.
3. Real-Time Decision Intelligence - While data reviews happen regularly, the organisation has not yet moved to live dashboards embedded in daily operations. This transition would significantly sharpen the speed and accuracy of operational decision-making.

STRATEGIC RECOMMENDATIONS
1. Implement a real-time operational dashboard - using tools such as Looker, Power BI, or Metabase - that surfaces live KPIs for sales, operations, and customer service, enabling truly data-driven daily management.
2. Complete the automation of internal processes by deploying an integrated ERP or workflow management system that connects accounting, procurement, and fulfillment with automated approval chains and exception notifications.
3. Commission an independent cybersecurity audit and develop a formal Information Security Policy with defined access tiers, incident response procedures, and a path toward ISO 27001 or equivalent certification.
4. Invest in advanced AI tools for predictive analytics and customer behaviour modelling to move beyond descriptive analytics toward prescriptive insights that guide proactive strategy.
5. Formalise an internal Innovation Programme that channels employee-driven digital ideas through a structured evaluation and implementation process, ensuring the organisation's strong digital culture continues to generate measurable value.

LONG-TERM ROADMAP
Over the next 2 to 3 years, the organisation is well-positioned to reach the Digital Leader tier. This will require full integration of AI-driven analytics into strategic planning, completion of enterprise-grade automation across all departments, and the development of proprietary data assets that create sustainable competitive differentiation. The organisation should also consider becoming a case study or benchmark for digital maturity within its industry vertical."""
    },
]


def page_cabinet():
    st.markdown('<div class="page-wrap">', unsafe_allow_html=True)
    st.markdown("""
    <div class="fade-up">
        <div class="section-label">History</div>
        <div class="section-title">My Cabinet</div>
        <p class="section-sub">All your past Digital Maturity assessments in one place.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Summary stats
    c1, c2, c3 = st.columns(3)
    scores = [t["score"] for t in CABINET_TESTS]
    with c1:
        st.markdown(f"""<div class="metric-card"><div class="metric-val">{len(CABINET_TESTS)}</div>
        <div class="metric-lbl">Total Tests</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-card"><div class="metric-val">{sum(scores)//len(scores)}%</div>
        <div class="metric-lbl">Avg DMI Score</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="metric-card"><div class="metric-val">{max(scores)}%</div>
        <div class="metric-lbl">Best Score</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Test cards with expand
    for test in CABINET_TESTS:
        level, lc, _ = get_level(test["score"])
        tag_class = "trial" if test["type"] == "Trial" else ""

        with st.expander(f"", expanded=False):
            pass

        # Custom expander using session state
        expand_key = f"expand_{test['id']}"
        if expand_key not in st.session_state:
            st.session_state[expand_key] = False

        is_expanded = st.session_state[expand_key]

        st.markdown(f"""
        <div class="cabinet-card">
            <div class="cabinet-meta">
                <div>
                    <div class="cabinet-title">Assessment #{test['id']}</div>
                    <div style="font-size:13px; color:rgba(255,255,255,0.35); margin-top:4px;">{test['date']}</div>
                </div>
                <div style="display:flex; align-items:center; gap:16px;">
                    <span class="tag {tag_class}">{test['type']}</span>
                    <div class="cabinet-score">{test['score']}%</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_btn, col_spacer = st.columns([1, 4])
        with col_btn:
            btn_label = "▲ Collapse" if is_expanded else "▼ View Details"
            if st.button(btn_label, key=f"toggle_{test['id']}"):
                st.session_state[expand_key] = not is_expanded
                st.rerun()

        if is_expanded:
            st.markdown('<div class="expand-content">', unsafe_allow_html=True)

            # Level badge
            st.markdown(f"""
            <div style="margin-bottom:20px;">
                <span style="font-size:13px; color:rgba(255,255,255,0.4);">Level: </span>
                <span style="color:{lc}; font-weight:700;">{level}</span>
                &nbsp;&nbsp;
                <span style="font-size:13px; color:rgba(255,255,255,0.4);">Score: </span>
                <span style="color:#fff; font-weight:700;">{test['score']}%</span>
            </div>
            """, unsafe_allow_html=True)

            # Answers
            st.markdown('<div style="font-size:12px; font-weight:700; letter-spacing:2px; text-transform:uppercase; color:#2563eb; margin-bottom:12px;">Responses</div>', unsafe_allow_html=True)
            for q in QUESTIONS:
                qid = q["id"]
                if qid in test["answers"]:
                    ans_text, pts = test["answers"][qid]
                    st.markdown(f"""
                    <div class="answer-row">
                        <div class="answer-q"><strong style="color:rgba(255,255,255,0.3)">Q{qid}.</strong> {q['text']}</div>
                        <div class="answer-a">{ans_text} <span style="color:#2563eb">({pts}/5)</span></div>
                    </div>
                    """, unsafe_allow_html=True)

            # Recommendation
            st.markdown("""
            <div class="ai-box" style="margin-top:24px;">
                <h3>🤖 AI Recommendation</h3>
            """, unsafe_allow_html=True)
            rec_formatted = test["recommendation"].replace("\n", "<br>")
            st.markdown(f'<p style="font-size:14px; color:rgba(255,255,255,0.7); line-height:1.9;">{rec_formatted}</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# ACCOUNT PAGE
# ============================================================

def page_account():
    st.markdown('<div class="page-wrap">', unsafe_allow_html=True)

    st.markdown("""
    <div class="fade-up">
        <div class="section-label">Profile</div>
        <div class="section-title">My Account</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    ac1, ac2 = st.columns([4, 1])
    with ac1:
        st.markdown("""
        <div class="account-name">Madina Turgumbay</div>
        <div class="account-email">madinka@gmail.com</div>
        """, unsafe_allow_html=True)

        info_items = [
            ("Full Name", "Madina Turgumbay"),
            ("Date of Birth", "May 10, 2001"),
            ("Email", "madinka@gmail.com"),
            ("Member Since", "January 2025"),
            ("Current Plan", "Basic"),
            ("Assessments Taken", "3"),
        ]
        for label, val in info_items:
            st.markdown(f"""
            <div class="info-row">
                <div class="info-label">{label}</div>
                <div class="info-val">{val}</div>
            </div>
            """, unsafe_allow_html=True)

    with ac2:
        st.markdown("""
        <div style="display:flex; justify-content:flex-end;">
            <div class="avatar">MT</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Stats
    st.markdown('<div class="section-title" style="font-size:22px; margin-bottom:24px;">Activity Overview</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="stats-row">
        <div class="stat-box">
            <div class="stat-num">3</div>
            <div class="stat-txt">Tests Taken</div>
        </div>
        <div class="stat-box">
            <div class="stat-num">55%</div>
            <div class="stat-txt">Avg DMI Score</div>
        </div>
        <div class="stat-box">
            <div class="stat-num">72%</div>
            <div class="stat-txt">Best Score</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Plan card
    st.markdown("""
    <div class="section-title" style="font-size:22px; margin-bottom:24px;">Subscription</div>
    <div class="card" style="max-width:400px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <div style="font-family:'Syne',sans-serif; font-size:22px; font-weight:700; color:#fff;">Basic Plan</div>
                <div style="font-size:13px; color:rgba(255,255,255,0.4); margin-top:4px;">Free tier - renews monthly</div>
            </div>
            <div style="font-size:28px;">🆓</div>
        </div>
        <div style="margin-top:20px; padding-top:16px; border-top:1px solid rgba(255,255,255,0.07);">
            <div style="font-size:13px; color:rgba(255,255,255,0.5); line-height:1.7;">
                Upgrade to <strong>Premium</strong> to unlock AI recommendations,
                unlimited assessments, and full PDF reports.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# ROUTER
# ============================================================

render_navbar()

page = st.session_state.page

if page == "Home":
    page_home()
elif page == "Test":
    page_test()
elif page == "News":
    page_news()
elif page == "General Info":
    page_general_info()
elif page == "Cabinet":
    page_cabinet()
elif page == "Account":
    page_account()
else:
    page_home()
