
import hashlib
import html
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import streamlit as st


try:
    from src.beta_access import (
        render_beta_gate,
        render_usage_status,
        render_feedback_form,
        can_use_ai,
        consume_ai_use,
    )
except ImportError:
    from beta_access import (
        render_beta_gate,
        render_usage_status,
        render_feedback_form,
        can_use_ai,
        consume_ai_use,
    )


from src.ai_agent import (
    analyze_issue,
    analyze_issue_deep,
    generate_contribution_comment,
    summarize_repository,
)
from src.github_client import (
    fetch_open_issues,
    get_gssoc_filter_options,
    get_repository_metadata,
    get_repository_readme,
    get_issue_context,
    search_github_repositories,
    search_gssoc_projects,
)
from src.issue_ranker import rank_issues


MAX_AI_ISSUES = 1
DEFAULT_SORT = "Most Good First Issues"


# ─────────────────────────────────────────────────────────────
# PAGE CONFIG + THEME
# ─────────────────────────────────────────────────────────────

def configure_page() -> None:
    st.set_page_config(
        page_title="GitScout AI",
        page_icon="🧭",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

def inject_css() -> None:
    """
    Premium GitScout AI UI theme.
    Focus: readable white cards, stronger hierarchy, clean dropdowns, less Streamlit-default feel.
    """
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg: #F4F6FA;
    --surface: #FFFFFF;
    --surface-soft: #F8FAFC;
    --surface-hover: #FDFEFF;
    --ink: #101828;
    --ink-2: #344054;
    --muted: #4B5563;
    --muted-2: #667085;
    --line: #E4E7EC;
    --line-2: #D0D5DD;
    --primary: #315CF6;
    --primary-hover: #2448D8;
    --primary-soft: #EEF3FF;
    --ai: #7C3AED;
    --ai-soft: #F4F0FF;
    --success: #079455;
    --success-soft: #ECFDF3;
    --warning: #DC6803;
    --warning-soft: #FFFAEB;
    --danger: #D92D20;
    --danger-soft: #FEF3F2;
    --shadow-sm: 0 1px 2px rgba(16, 24, 40, 0.06);
    --shadow-md: 0 10px 30px rgba(16, 24, 40, 0.08);
    --shadow-lg: 0 24px 70px rgba(16, 24, 40, 0.13);
    --radius: 18px;
}

* { box-sizing: border-box !important; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background: var(--bg) !important;
    color: var(--ink) !important;
    font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
    -webkit-font-smoothing: antialiased !important;
}

[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stSidebar"],
#MainMenu, footer, .stDeployButton { display: none !important; visibility: hidden !important; }

.main .block-container {
    max-width: 1440px !important;
    padding: 1.5rem 2.3rem 3rem !important;
}

h1, h2, h3, h4, h5, h6, p, span, label, div, button, li, a {
    font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
}

h1 { font-size: 2.25rem !important; line-height: 1.12 !important; letter-spacing: -0.045em !important; font-weight: 800 !important; color: var(--ink) !important; }
h2 { font-size: 1.45rem !important; line-height: 1.25 !important; letter-spacing: -0.03em !important; font-weight: 750 !important; color: var(--ink) !important; }
h3 { font-size: 1.1rem !important; line-height: 1.3 !important; letter-spacing: -0.02em !important; font-weight: 700 !important; color: var(--ink) !important; }

[data-testid="stMarkdownContainer"] p {
    color: var(--ink-2) !important;
    font-size: 14.5px !important;
    line-height: 1.65 !important;
}

[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * {
    color: var(--muted) !important;
    font-size: 12.5px !important;
    line-height: 1.45 !important;
    font-weight: 500 !important;
}

/* Streamlit bordered containers become clean cards */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--surface) !important;
    border: 1px solid var(--line) !important;
    border-radius: var(--radius) !important;
    box-shadow: var(--shadow-sm) !important;
    overflow: hidden !important;
}

[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: var(--line-2) !important;
    box-shadow: var(--shadow-md) !important;
}

[data-testid="stVerticalBlockBorderWrapper"] > div,
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"],
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"],
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="column"],
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] {
    background: transparent !important;
    color: var(--ink) !important;
}

[data-testid="stVerticalBlockBorderWrapper"] h1,
[data-testid="stVerticalBlockBorderWrapper"] h2,
[data-testid="stVerticalBlockBorderWrapper"] h3,
[data-testid="stVerticalBlockBorderWrapper"] h4,
[data-testid="stVerticalBlockBorderWrapper"] strong { color: var(--ink) !important; }

[data-testid="stVerticalBlockBorderWrapper"] p,
[data-testid="stVerticalBlockBorderWrapper"] span,
[data-testid="stVerticalBlockBorderWrapper"] div { color: var(--ink-2) !important; }

/* Buttons */
.stButton > button, [data-testid="stLinkButton"] a {
    min-height: 2.65rem !important;
    border-radius: 12px !important;
    border: 1px solid var(--line-2) !important;
    background: var(--surface) !important;
    color: var(--ink-2) !important;
    font-weight: 650 !important;
    font-size: 14px !important;
    box-shadow: var(--shadow-sm) !important;
    transition: 0.16s ease !important;
    text-decoration: none !important;
}

.stButton > button:hover, [data-testid="stLinkButton"] a:hover {
    transform: translateY(-1px) !important;
    border-color: #B8C3D9 !important;
    background: var(--surface-soft) !important;
    color: var(--ink) !important;
    box-shadow: var(--shadow-md) !important;
}

.stButton > button[kind="primary"], .stButton > button[data-testid="baseButton-primary"] {
    background: var(--primary) !important;
    border-color: var(--primary) !important;
    color: white !important;
    box-shadow: 0 12px 24px rgba(49, 92, 246, 0.22) !important;
}

.stButton > button[kind="primary"]:hover, .stButton > button[data-testid="baseButton-primary"]:hover {
    background: var(--primary-hover) !important;
    border-color: var(--primary-hover) !important;
    color: white !important;
}

/* Inputs */
.stTextInput input,
.stNumberInput input,
.stTextArea textarea,
.stSelectbox div[data-baseweb="select"] > div,
.stMultiSelect div[data-baseweb="select"] > div {
    background: #FFFFFF !important;
    color: var(--ink) !important;
    border: 1px solid var(--line-2) !important;
    border-radius: 12px !important;
    min-height: 2.7rem !important;
    font-size: 14px !important;
    box-shadow: var(--shadow-sm) !important;
}

.stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(49, 92, 246, 0.14) !important;
    outline: none !important;
}

.stTextInput input::placeholder, .stTextArea textarea::placeholder { color: #98A2B3 !important; }

.stTextInput label, .stNumberInput label, .stTextArea label, .stSelectbox label, .stMultiSelect label {
    color: var(--ink-2) !important;
    font-size: 12px !important;
    font-weight: 700 !important;
    letter-spacing: 0.035em !important;
    text-transform: uppercase !important;
}

/* Fix black dropdowns */
div[data-baseweb="popover"], div[data-baseweb="popover"] > div,
div[data-baseweb="menu"], ul[role="listbox"], [role="listbox"] {
    background: #FFFFFF !important;
    color: var(--ink) !important;
    border: 1px solid var(--line) !important;
    border-radius: 14px !important;
    box-shadow: var(--shadow-lg) !important;
}

div[data-baseweb="menu"] li, [role="option"] {
    background: #FFFFFF !important;
    color: var(--ink-2) !important;
    font-size: 14px !important;
    padding: 10px 14px !important;
}

div[data-baseweb="menu"] li:hover, [role="option"]:hover,
div[data-baseweb="menu"] li[aria-selected="true"], [role="option"][aria-selected="true"] {
    background: var(--primary-soft) !important;
    color: var(--primary-hover) !important;
}

.stMultiSelect span[data-baseweb="tag"] {
    background: var(--primary-soft) !important;
    color: var(--primary-hover) !important;
    border: 1px solid #C7D7FE !important;
    border-radius: 999px !important;
    font-weight: 650 !important;
}

/* Slider red override */
.stSlider [data-baseweb="slider"] div[role="slider"] {
    background: var(--primary) !important;
    border-color: var(--primary) !important;
}
.stSlider [data-baseweb="slider"] > div > div {
    background-color: var(--primary) !important;
}

/* Metrics */
[data-testid="stMetricLabel"] { color: var(--muted) !important; font-size: 11px !important; letter-spacing: .05em !important; text-transform: uppercase !important; font-weight: 700 !important; }
[data-testid="stMetricValue"] { color: var(--ink) !important; font-size: 1.15rem !important; font-weight: 800 !important; }

hr { border: 0 !important; border-top: 1px solid var(--line) !important; margin: 1.1rem 0 !important; opacity: 1 !important; }
[data-testid="column"] { min-width: 0 !important; }

/* Custom product components */
.gs-repo-card, .gs-issue-card, .gs-coach-card, .gs-comment-card {
    background: #FFFFFF;
    border: 1px solid var(--line);
    border-radius: 18px;
    box-shadow: var(--shadow-sm);
    padding: 18px;
    margin-bottom: 16px;
}
.gs-repo-card:hover, .gs-issue-card:hover, .gs-coach-card:hover { border-color: #B8C3D9; box-shadow: var(--shadow-md); }
.gs-card-top { display:flex; align-items:flex-start; justify-content:space-between; gap:14px; margin-bottom:8px; }
.gs-title { color: var(--ink); font-size: 16px; line-height:1.35; font-weight: 800; letter-spacing:-0.015em; margin:0; }
.gs-desc { color: var(--ink-2); font-size: 14px; line-height:1.6; margin: 10px 0 12px; }
.gs-meta { color: var(--muted); font-size: 12.5px; line-height:1.5; font-weight: 550; }
.gs-match { background: var(--surface-soft); border: 1px solid var(--line); border-radius: 12px; padding: 10px 12px; color: var(--ink-2); font-size: 13px; line-height: 1.45; margin-top: 12px; }
.gs-label { color: var(--muted); font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: .065em; margin-right: 7px; }
.gs-chip { display:inline-flex; align-items:center; border-radius:999px; padding:4px 9px; font-size:12px; font-weight:700; border:1px solid var(--line); background:var(--surface-soft); color:var(--ink-2); white-space:nowrap; }
.gs-chip-good { background: var(--success-soft); color: var(--success); border-color:#ABEFC6; }
.gs-chip-ai { background: var(--ai-soft); color: var(--ai); border-color:#DDD6FE; }
.gs-chip-score { background: var(--primary-soft); color: var(--primary-hover); border-color:#C7D7FE; }
.gs-stats { display:flex; gap:16px; flex-wrap:wrap; color:var(--muted); font-size:12.5px; margin-top:12px; }
.gs-section-grid { display:grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap:14px; margin-top:14px; }
.gs-coach-card h4 { margin:0 0 8px; color:var(--ink); font-size:14.5px; font-weight:800; }
.gs-coach-card ul { padding-left: 1.15rem; margin: 0; }
.gs-coach-card li { margin: 6px 0; color: var(--ink-2); font-size: 14px; line-height:1.55; }
.gs-comment-card { background: #FCFCFD; }
.gs-comment-text { white-space: pre-wrap; color: var(--ink); font-size: 14px; line-height: 1.7; margin:0; }
.gs-comment-text::selection, .gs-comment-card *::selection { background:#DDE7FF !important; color: var(--ink) !important; }
.gs-empty-note { background: var(--primary-soft); border:1px solid #C7D7FE; color:var(--primary-hover); border-radius:14px; padding:13px 15px; font-weight:600; }

@media (max-width: 900px) {
    .main .block-container { padding: 1rem !important; }
    .gs-section-grid { grid-template-columns: 1fr; }
}


/* ─────────────────────────────────────────────────────────────
   FINAL UI POLISH OVERRIDES — May 29
   Fixes: dark dropdowns, unreadable comments, crowded cards, nav weight.
───────────────────────────────────────────────────────────── */
:root {
    --app-bg: #F6F7FB;
    --card-bg: #FFFFFF;
    --ink: #0F172A;
    --ink-2: #27364A;
    --muted: #475569;
    --muted-2: #64748B;
    --border: #DDE3EE;
    --border-2: #C9D4E5;
    --primary: #3457F5;
    --primary-hover: #243FD0;
    --primary-soft: #EEF2FF;
    --success: #087F5B;
    --warning: #B45309;
    --danger: #B42318;
}

html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background: var(--app-bg) !important;
    color: var(--ink) !important;
}

.main .block-container {
    max-width: 1420px !important;
    padding: 1.2rem 2rem 3rem !important;
}

/* Cards should be easy to separate */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--card-bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: 18px !important;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06) !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: var(--border-2) !important;
    box-shadow: 0 14px 36px rgba(15, 23, 42, 0.09) !important;
}

/* readable text */
[data-testid="stMarkdownContainer"] p,
[data-testid="stVerticalBlockBorderWrapper"] p,
[data-testid="stVerticalBlockBorderWrapper"] div,
[data-testid="stVerticalBlockBorderWrapper"] span {
    color: var(--ink-2) !important;
}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * {
    color: var(--muted) !important;
    font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
    font-size: 13px !important;
}

/* top nav */
.gs-brand-title {
    font-size: 1.55rem;
    font-weight: 850;
    letter-spacing: -0.045em;
    color: var(--ink);
    line-height: 1.1;
}
.gs-brand-subtitle {
    margin-top: 4px;
    color: var(--muted);
    font-size: 0.9rem;
    font-weight: 600;
}
.gs-brand-icon {
    display: inline-grid;
    place-items: center;
    width: 32px;
    height: 32px;
    margin-right: 10px;
    border-radius: 10px;
    background: linear-gradient(135deg, #EEF2FF, #F5F3FF);
    color: var(--primary);
    font-weight: 900;
    border: 1px solid #DDE3FF;
}

/* button text should not look washed out */
.stButton > button {
    color: var(--ink) !important;
    font-weight: 700 !important;
}
.stButton > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"] {
    color: #FFFFFF !important;
    background: var(--primary) !important;
    border-color: var(--primary) !important;
}
.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="baseButton-primary"]:hover {
    background: var(--primary-hover) !important;
    border-color: var(--primary-hover) !important;
}

/* force dropdown menus light; this fixes the black menu bug */
div[data-baseweb="popover"],
div[data-baseweb="menu"],
ul[role="listbox"],
[role="listbox"] {
    background: #FFFFFF !important;
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
    box-shadow: 0 18px 45px rgba(15, 23, 42, 0.16) !important;
    color: var(--ink) !important;
}
div[data-baseweb="menu"] *,
ul[role="listbox"] *,
[role="option"],
[role="option"] * {
    background: transparent !important;
    color: var(--ink) !important;
    opacity: 1 !important;
}
[role="option"]:hover,
div[data-baseweb="menu"] li:hover {
    background: var(--primary-soft) !important;
    color: var(--primary-hover) !important;
}

/* multiselect chips calmer */
.stMultiSelect span[data-baseweb="tag"] {
    background: #EEF2FF !important;
    color: #243FD0 !important;
    border: 1px solid #C7D2FE !important;
    border-radius: 999px !important;
    font-weight: 700 !important;
}

/* final repo cards */
.gs-repo-card-v2 {
    background: #FFFFFF;
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 18px 18px 16px;
    min-height: 360px;
    box-shadow: 0 8px 22px rgba(15, 23, 42, 0.055);
    display: flex;
    flex-direction: column;
    gap: 12px;
}
.gs-repo-card-v2:hover {
    border-color: #B7C5DC;
    box-shadow: 0 16px 42px rgba(15, 23, 42, 0.10);
    transform: translateY(-1px);
}
.gs-repo-title-row {
    display:flex;
    justify-content:space-between;
    gap:12px;
    align-items:flex-start;
}
.gs-repo-title {
    margin:0;
    color:var(--ink);
    font-size:1rem;
    line-height:1.3;
    font-weight:850;
    letter-spacing:-0.02em;
    word-break:break-word;
}
.gs-repo-desc {
    margin:0;
    color:var(--ink-2);
    font-size:0.93rem;
    line-height:1.55;
    min-height:66px;
}
.gs-overview-box {
    background:#F8FAFC;
    border:1px solid #E2E8F0;
    border-radius:14px;
    padding:12px 13px;
    display:grid;
    gap:9px;
}
.gs-overview-row {
    display:grid;
    grid-template-columns: 92px 1fr;
    gap:10px;
    align-items:start;
}
.gs-overview-label {
    color:#64748B;
    font-size:0.72rem;
    font-weight:850;
    text-transform:uppercase;
    letter-spacing:0.06em;
}
.gs-overview-value {
    color:#1E293B;
    font-size:0.86rem;
    font-weight:650;
    line-height:1.35;
}
.gs-tag-row { display:flex; gap:6px; flex-wrap:wrap; }
.gs-mini-tag {
    border:1px solid #D7DEE9;
    background:#FFFFFF;
    color:#334155;
    border-radius:999px;
    padding:4px 8px;
    font-size:0.75rem;
    font-weight:700;
}
.gs-stats-row {
    margin-top:auto;
    padding-top:12px;
    border-top:1px solid #E7ECF3;
    display:flex;
    gap:14px;
    flex-wrap:wrap;
    color:#64748B;
    font-size:0.82rem;
    font-weight:700;
}
.gs-soft-pill {
    display:inline-flex;
    align-items:center;
    border-radius:999px;
    padding:4px 9px;
    border:1px solid #D6E4FF;
    background:#EEF4FF;
    color:#2448D8;
    font-size:0.75rem;
    font-weight:800;
    white-space:nowrap;
}

/* issue list card */
.gs-issue-row-card {
    background:#FFFFFF;
    border:1px solid var(--border);
    border-radius:16px;
    padding:15px 16px;
    margin-bottom:10px;
    box-shadow:0 6px 18px rgba(15,23,42,.045);
}
.gs-issue-row-card.selected {
    border-color:#AAB8FF;
    background:#F8FAFF;
}
.gs-issue-title {
    margin:0;
    color:var(--ink);
    font-weight:850;
    font-size:0.98rem;
    line-height:1.35;
}
.gs-issue-meta {
    margin-top:8px;
    color:#64748B;
    font-size:0.82rem;
    font-weight:650;
}
.gs-fit-pill {
    display:inline-flex;
    border-radius:999px;
    background:#F1F5F9;
    border:1px solid #DDE5F0;
    color:#334155;
    padding:3px 8px;
    font-size:0.75rem;
    font-weight:850;
}

/* black comment box with native copy button */
[data-testid="stCode"] pre {
    background:#0B1220 !important;
    color:#F8FAFC !important;
    border:1px solid #1E293B !important;
    border-radius:16px !important;
    padding:18px !important;
    line-height:1.65 !important;
    font-size:13.5px !important;
    box-shadow:inset 0 1px 0 rgba(255,255,255,.05), 0 14px 35px rgba(15,23,42,.16) !important;
}
[data-testid="stCode"] code {
    color:#F8FAFC !important;
    background:transparent !important;
    border:none !important;
    padding:0 !important;
    text-shadow:none !important;
}
[data-testid="stCode"] button {
    background:#111827 !important;
    border:1px solid #334155 !important;
    color:#FFFFFF !important;
}
::selection { background:#BFDBFE; color:#0F172A; }



/* ─────────────────────────────────────────────────────────────
   FINAL FEEDBACK + DROPDOWN + COACH POLISH
───────────────────────────────────────────────────────────── */
[role="listbox"],
ul[role="listbox"],
div[data-baseweb="menu"],
div[data-baseweb="popover"],
div[data-baseweb="popover"] > div {
    background: #FFFFFF !important;
    color: #0F172A !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 14px !important;
    box-shadow: 0 24px 64px rgba(15, 23, 42, 0.22) !important;
}
[role="option"],
[role="option"] *,
div[data-baseweb="menu"] li,
div[data-baseweb="menu"] li * {
    background: #FFFFFF !important;
    color: #0F172A !important;
    opacity: 1 !important;
}
[role="option"]:hover,
div[data-baseweb="menu"] li:hover,
[role="option"][aria-selected="true"] {
    background: #EEF2FF !important;
    color: #1D4ED8 !important;
}

/* st.dialog feedback popup: light, readable, product-like */
div[data-testid="stDialog"] div[role="dialog"],
div[role="dialog"] {
    background: #FFFFFF !important;
    color: #0F172A !important;
    border-radius: 24px !important;
    border: 1px solid #D9E2EF !important;
    box-shadow: 0 32px 90px rgba(15, 23, 42, 0.34) !important;
}
div[data-testid="stDialog"] *,
div[role="dialog"] * {
    color: #0F172A !important;
}
div[data-testid="stDialog"] label,
div[role="dialog"] label {
    color: #1E293B !important;
}
div[data-testid="stDialog"] textarea,
div[role="dialog"] textarea {
    background: #FFFFFF !important;
    color: #0F172A !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 14px !important;
}
.gs-feedback-kicker {
    display:inline-flex;
    align-items:center;
    width:fit-content;
    padding:5px 10px;
    border-radius:999px;
    background:#EEF2FF;
    color:#1D4ED8 !important;
    font-size:12px;
    font-weight:800;
    letter-spacing:.04em;
    text-transform:uppercase;
}
.gs-feedback-title {
    margin-top:12px;
    color:#0F172A !important;
    font-size:1.45rem;
    line-height:1.15;
    font-weight:850;
    letter-spacing:-.035em;
}
.gs-feedback-copy {
    margin:8px 0 0;
    color:#475569 !important;
    font-size:14.5px;
    line-height:1.55;
}
.gs-star-help {
    color:#334155 !important;
    font-weight:800;
    margin:14px 0 8px;
}
/* star buttons */
div[role="dialog"] .stButton > button,
div[data-testid="stDialog"] .stButton > button {
    color:#0F172A !important;
}

.gs-score-pill {
    display:inline-flex;
    width:fit-content;
    align-items:center;
    gap:6px;
    padding:5px 9px;
    border-radius:999px;
    background:#EEF2FF;
    color:#1D4ED8 !important;
    border:1px solid #C7D2FE;
    font-size:12px;
    font-weight:850;
    cursor:help;
}

</style>
""",
        unsafe_allow_html=True,
    )



# ─────────────────────────────────────────────────────────────
# CACHE WRAPPERS
# ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def cached_filter_options() -> Dict[str, List[str]]:
    try:
        data = get_gssoc_filter_options()
        if not isinstance(data, dict):
            return {"tech_stacks": [], "languages": [], "difficulties": []}

        return {
            "tech_stacks": unique_clean(data.get("tech_stacks") or data.get("tech_stack") or data.get("stacks") or []),
            "languages": unique_clean(data.get("languages") or data.get("language") or []),
            "difficulties": unique_clean(data.get("difficulties") or data.get("difficulty") or []),
        }
    except Exception:
        return {"tech_stacks": [], "languages": [], "difficulties": []}


@st.cache_data(ttl=900, show_spinner=False)
def cached_search_projects(
    keywords: str,
    tech_stack: str,
    language: str,
    difficulty: str,
    sort_by: str,
) -> List[Dict[str, Any]]:
    results = search_gssoc_projects(
        keywords=keywords or "",
        tech_stack=tech_stack or "",
        language=language or "",
        difficulty=difficulty or "",
        sort_by=sort_by or DEFAULT_SORT,
    )
    return results if isinstance(results, list) else []



@st.cache_data(ttl=900, show_spinner=False)
def cached_github_repo_search(
    keywords: str,
    domain: str,
    tech_stack: tuple,
    languages: tuple,
    sort_by: str,
) -> List[Dict[str, Any]]:
    results = search_github_repositories(
        keywords=keywords or "",
        domain=domain or "",
        tech_stack=list(tech_stack or ()),
        languages=list(languages or ()),
        sort_by=sort_by or "Best match",
        per_page=18,
    )
    return results if isinstance(results, list) else []


@st.cache_data(ttl=1800, show_spinner=False)
def cached_repo_metadata(full_name: str) -> Dict[str, Any]:
    return get_repository_metadata(full_name)


@st.cache_data(ttl=1800, show_spinner=False)
def cached_repo_readme(full_name: str) -> str:
    return get_repository_readme(full_name)


@st.cache_data(ttl=1800, show_spinner=False)
def cached_open_issues(full_name: str) -> List[Dict[str, Any]]:
    issues = fetch_open_issues(full_name)
    return issues if isinstance(issues, list) else []


@st.cache_data(ttl=3600, show_spinner=False)
def cached_repo_summary(repo_data: Dict[str, Any]) -> Dict[str, Any]:
    return summarize_repository(repo_data)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_issue_analysis(issue_data: Dict[str, Any], skill_level: str) -> Dict[str, Any]:
    return analyze_issue(issue_data, skill_level)


@st.cache_data(ttl=1200, show_spinner=False)
def cached_issue_context(full_name: str, issue_number: int) -> Dict[str, Any]:
    return get_issue_context(full_name, issue_number, max_comments=5)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_deep_issue_analysis(issue_context: Dict[str, Any], user_profile: Dict[str, Any]) -> Dict[str, Any]:
    return analyze_issue_deep(issue_context, user_profile)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_contribution_comment(issue_breakdown: Dict[str, Any], style: str) -> Dict[str, Any]:
    return generate_contribution_comment(issue_breakdown, style)


# ─────────────────────────────────────────────────────────────
# SESSION
# ─────────────────────────────────────────────────────────────

def init_session_state() -> None:
    defaults = {
        "page": "discover",

        "repo_results": [],
        "selected_repos": [],
        "active_repo": None,
        "active_repo_detail": None,

        "ranked_issues": [],
        "selected_issue_idx": 0,
        "issue_ai_breakdowns": {},
        "generated_comments": {},
        "saved_issues": [],

        "keywords": "",
        "hero_keywords": "",
        "repo_filter_keywords": "",

        "domain_filter": "AI/ML",
        "tech_stack": [],
        "language": [],
        "difficulty": "Beginner Friendly",
        "sort_by": DEFAULT_SORT,
        "skill_level": "Beginner",

        "repo_filters_open": False,
        "issue_filters_open": False,
        "advanced_repo_filters_open": False,
        "repo_search_text": "",
        "issue_url_input": "",
        "issue_url_comment_style": "Short and polite",
        "issue_url_generated_comment": "",
        "issue_url_context_loaded": False,

        "user_skills": ["Python basics"],
        "ml_interests": ["AI/ML"],
        "contribution_types": ["Docs", "Bug"],

        "issue_labels": [],
        "custom_labels": "",
        "assignee_filter": "Any",
        "max_comments": 5,
        "issue_keywords": "",
        "issue_type": "Any",
        "ml_area": "Any",
        "required_knowledge": "Any",
        "issue_sort": "Best match",
        "comment_style": "Short and polite",
        "roadmap_built": False,
        "default_repos_loaded": False,
        "starter_query_index": 0,
        "advanced_issue_filters_open": False,
        "show_original_issue_body": False,
        "time_available": "1-2 hours",
        "roadmap_stage": "Python → NumPy/Pandas",
        "feedback_star_rating": 4,
        "feedback_modal_closed": False,
        "feedback_submitted": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def go(page: str) -> None:
    st.session_state.page = page
    st.rerun()


# ─────────────────────────────────────────────────────────────
# GENERAL HELPERS
# ─────────────────────────────────────────────────────────────

def unique_clean(value: Any) -> List[str]:
    if value is None:
        return []

    if isinstance(value, str):
        items = [part.strip() for part in value.split(",")]
    elif isinstance(value, (list, tuple, set)):
        items = [str(item).strip() for item in value]
    else:
        items = [str(value).strip()]

    cleaned: List[str] = []
    seen = set()

    for item in items:
        if not item:
            continue
        key = item.lower()
        if key not in seen:
            cleaned.append(item)
            seen.add(key)

    return cleaned


def safe_key(value: Any) -> str:
    return hashlib.md5(str(value).encode("utf-8", errors="ignore")).hexdigest()[:10]


def strip_markdown(text: Any) -> str:
    raw = str(text or "")
    raw = re.sub(r"```.*?```", " ", raw, flags=re.DOTALL)
    raw = re.sub(r"`([^`]*)`", r"\1", raw)
    raw = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", raw)
    raw = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", raw)
    raw = re.sub(r"^\s{0,3}#{1,6}\s*", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"[*_>#\-]+", " ", raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    return raw


def truncate(text: Optional[Any], length: int = 155) -> str:
    clean = strip_markdown(text)
    if not clean:
        return "No description available."
    return clean if len(clean) <= length else clean[: length - 3] + "..."


def extract_repo_full_name(url: str) -> str:
    if not url:
        return ""

    try:
        parsed = urlparse(url)
        parts = [part for part in parsed.path.strip("/").split("/") if part]

        if len(parts) >= 2:
            return f"{parts[0]}/{parts[1]}"
    except Exception:
        return ""

    return ""


def repo_url(repo: Dict[str, Any]) -> str:
    return (
        repo.get("repo_url")
        or repo.get("github_url")
        or repo.get("html_url")
        or repo.get("url")
        or "#"
    )


def repo_full_name(repo: Dict[str, Any]) -> str:
    explicit = repo.get("repo_full_name") or repo.get("full_name")

    if explicit:
        return str(explicit)

    url_full_name = extract_repo_full_name(repo_url(repo))
    if url_full_name:
        return url_full_name

    name = repo.get("name")
    if isinstance(name, str) and "/" in name:
        return name

    return str(name or "")


def get_repo_display_name(repo: Dict[str, Any]) -> str:
    return repo_full_name(repo) or str(repo.get("name") or "Unknown repository")


def get_repo_tags(repo: Dict[str, Any]) -> List[str]:
    return unique_clean(repo.get("tech_stack") or repo.get("topics") or repo.get("tags"))[:7]


def searchable_repo_text(repo: Dict[str, Any]) -> str:
    parts = [
        repo.get("name", ""),
        repo_full_name(repo),
        repo.get("description", ""),
        repo.get("summary", ""),
        " ".join(get_repo_tags(repo)),
        repo.get("language", ""),
    ]
    return " ".join(str(part) for part in parts).lower()


def infer_best_for(repo: Dict[str, Any]) -> str:
    text = searchable_repo_text(repo).lower()

    # AI/ML Specifics
    if any(word in text for word in ["nlp", "language model", "transformer", "huggingface", "tokenizer", "llm"]):
        return "NLP / LLMs"
    if any(word in text for word in ["vision", "image", "opencv", "ocr", "segmentation", "detection"]):
        return "Computer Vision"
    if any(word in text for word in ["pandas", "numpy", "preprocess", "data clean", "dataset"]):
        return "Data Science"
    if any(word in text for word in ["sklearn", "scikit", "classification", "regression", "clustering"]):
        return "Classical ML"
    if any(word in text for word in ["pytorch", "tensorflow", "keras", "deep learning", "neural"]):
        return "Deep Learning"

    # Web & Mobile
    if any(word in text for word in ["react", "vue", "nextjs", "angular", "tailwind", "frontend", "svelte", "html", "css"]):
        return "Frontend Web Dev"
    if any(word in text for word in ["django", "flask", "fastapi", "express", "nodejs", "spring", "rails", "graphql", "rest api", "backend"]):
        return "Backend Dev"
    if any(word in text for word in ["flutter", "react native", "swift", "kotlin", "android", "ios", "mobile"]):
        return "Mobile App Dev"

    # DevOps, Systems, Databases
    if any(word in text for word in ["docker", "kubernetes", "ansible", "terraform", "aws", "gcp", "azure", "ci/cd", "devops", "cloud"]):
        return "Cloud / DevOps"
    if any(word in text for word in ["rust", "golang", "c++", "kernel", "systems", "embedded", "assembler"]):
        return "Systems / Tools"
    if any(word in text for word in ["sql", "postgresql", "mongodb", "mysql", "redis", "database", "query"]):
        return "Databases"

    # Docs / General
    if any(word in text for word in ["doc", "readme", "tutorial", "example"]):
        return "Docs / Examples"

    lang = str(repo.get("language") or "").strip()
    if lang:
        return f"{lang} Projects"

    return "General Development"


def infer_required_skills(repo: Dict[str, Any]) -> List[str]:
    text = searchable_repo_text(repo).lower()
    skills = []

    lang = str(repo.get("language") or "").strip()
    if lang:
        skills.append(lang)

    # General languages if not explicitly set
    if "python" in text and "Python" not in skills:
        skills.append("Python")
    if ("javascript" in text or " js" in text or "node" in text) and "JavaScript" not in skills:
        skills.append("JavaScript")
    if ("typescript" in text or " ts" in text) and "TypeScript" not in skills:
        skills.append("TypeScript")
    if "rust" in text and "Rust" not in skills:
        skills.append("Rust")
    if "golang" in text and "Go" not in skills:
        skills.append("Go")

    # Frameworks / Tools
    if "react" in text:
        skills.append("React")
    if "vue" in text:
        skills.append("Vue")
    if "node" in text:
        skills.append("Node.js")
    if "docker" in text:
        skills.append("Docker")
    if "numpy" in text:
        skills.append("NumPy")
    if "pandas" in text:
        skills.append("Pandas")
    if "sklearn" in text or "scikit" in text:
        skills.append("Scikit-learn")
    if "pytorch" in text:
        skills.append("PyTorch")
    if any(word in text for word in ["doc", "readme", "tutorial"]):
        skills.append("Docs")

    # Remove duplicates preserving order
    unique_skills = []
    for s in skills:
        if s not in unique_skills:
            unique_skills.append(s)

    return unique_skills[:4] or [lang or "Git", "GitHub"]


def infer_contribution_fit(repo: Dict[str, Any]) -> str:
    text = searchable_repo_text(repo).lower()
    difficulty = str(repo.get("difficulty", "")).lower()
    good_first = int(repo.get("good_first_issues", 0) or 0)

    if good_first > 0 or "beginner" in difficulty or "good first issue" in text:
        return "Beginner friendly"

    if any(word in text for word in ["pytorch", "tensorflow", "deep learning", "cuda", "neural"]):
        return "Needs ML basics"

    if any(word in text for word in ["react", "nextjs", "angular", "vue", "frontend"]):
        return "Needs Web basics"

    if any(word in text for word in ["rust", "c++", "kernel", "systems", "assembly"]):
        return "Needs Systems basics"

    return "Beginner possible"


def infer_available_work(repo: Dict[str, Any]) -> List[str]:
    text = searchable_repo_text(repo)
    work = []

    if any(word in text for word in ["doc", "readme", "tutorial", "example"]):
        work.append("Docs")
    if any(word in text for word in ["bug", "fix", "issue"]):
        work.append("Bugs")
    if any(word in text for word in ["test", "pytest", "unittest"]):
        work.append("Tests")
    if any(word in text for word in ["example", "notebook", "demo"]):
        work.append("Examples")
    if any(word in text for word in ["api", "backend", "fastapi"]):
        work.append("API")
    if any(word in text for word in ["preprocess", "dataset", "data"]):
        work.append("Data")

    return work[:4] or ["Docs", "Bugs", "Examples"]


def github_stat(value: Any) -> str:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return "—"

    return str(number) if number > 0 else "—"


def dynamic_repo_reasons(repo: Dict[str, Any]) -> List[str]:
    tags = get_repo_tags(repo)
    language = str(repo.get("language") or "").strip()
    skills = infer_required_skills(repo)
    fit = infer_contribution_fit(repo)
    open_issues = repo.get("open_issues") or repo.get("open_issues_count") or 0

    reasons = []

    if language:
        reasons.append(f"Uses {language}, which matches your language filters.")
    elif "Python" in skills:
        reasons.append("Uses Python, matching standard developer workflows.")

    if fit == "Beginner friendly":
        reasons.append("Looks beginner-friendly based on labels, tags, or difficulty.")
    elif fit == "Needs Web basics":
        reasons.append("Great project to practice web development basics.")
    elif fit == "Needs ML basics":
        reasons.append("Perfect candidate for building practical machine learning experience.")

    if open_issues and int(open_issues) > 0:
        reasons.append(f"Has {open_issues} open issues to explore.")

    if tags:
        reasons.append(f"Project area: {infer_best_for(repo)}.")

    if not reasons:
        reasons.append("Good candidate for checking beginner-friendly contribution opportunities.")

    reasons.append("GitScout ranks issues quickly first, then uses AI only for the selected issue.")

    return reasons[:4]



CURATED_AI_ML_REPOS = [
    {
        "name": "scikit-learn",
        "repo_full_name": "scikit-learn/scikit-learn",
        "repo_url": "https://github.com/scikit-learn/scikit-learn",
        "description": "Classical machine learning library with docs, tests, examples, and beginner-friendly documentation work.",
        "language": "Python",
        "tech_stack": ["Python", "Scikit-learn", "Classical ML", "Docs", "Testing"],
        "difficulty": "Intermediate",
        "good_first_issues": 0,
        "open_issues": 0,
    },
    {
        "name": "transformers",
        "repo_full_name": "huggingface/transformers",
        "repo_url": "https://github.com/huggingface/transformers",
        "description": "Popular NLP and LLM library with model examples, docs, tests, and active issue discussions.",
        "language": "Python",
        "tech_stack": ["Python", "NLP", "LLM", "PyTorch", "Docs"],
        "difficulty": "Intermediate",
        "good_first_issues": 0,
        "open_issues": 0,
    },
    {
        "name": "d2l-en",
        "repo_full_name": "d2l-ai/d2l-en",
        "repo_url": "https://github.com/d2l-ai/d2l-en",
        "description": "Dive into Deep Learning book repo with educational notebooks, examples, and documentation improvements.",
        "language": "Python",
        "tech_stack": ["Python", "Deep Learning", "Docs", "Notebooks"],
        "difficulty": "Beginner Friendly",
        "good_first_issues": 0,
        "open_issues": 0,
    },
    {
        "name": "fastai",
        "repo_full_name": "fastai/fastai",
        "repo_url": "https://github.com/fastai/fastai",
        "description": "Deep learning library focused on practical workflows, tutorials, documentation, and learner-friendly examples.",
        "language": "Python",
        "tech_stack": ["Python", "Deep Learning", "PyTorch", "Docs"],
        "difficulty": "Intermediate",
        "good_first_issues": 0,
        "open_issues": 0,
    },
    {
        "name": "pandas",
        "repo_full_name": "pandas-dev/pandas",
        "repo_url": "https://github.com/pandas-dev/pandas",
        "description": "Core Python data analysis library with documentation, tests, bug fixes, and data-cleaning related issues.",
        "language": "Python",
        "tech_stack": ["Python", "Pandas", "Data cleaning", "Testing", "Docs"],
        "difficulty": "Intermediate",
        "good_first_issues": 0,
        "open_issues": 0,
    },
    {
        "name": "mlflow",
        "repo_full_name": "mlflow/mlflow",
        "repo_url": "https://github.com/mlflow/mlflow",
        "description": "MLOps platform for experiment tracking, model registry, deployments, docs, and backend issues.",
        "language": "Python",
        "tech_stack": ["Python", "MLOps", "Backend", "Docs", "Testing"],
        "difficulty": "Intermediate",
        "good_first_issues": 0,
        "open_issues": 0,
    },
    {
        "name": "keras",
        "repo_full_name": "keras-team/keras",
        "repo_url": "https://github.com/keras-team/keras",
        "description": "Deep learning framework with examples, docs, tests, and beginner-friendly educational improvements.",
        "language": "Python",
        "tech_stack": ["Python", "Deep Learning", "TensorFlow", "Keras", "Docs"],
        "difficulty": "Intermediate",
        "good_first_issues": 0,
        "open_issues": 0,
    },
    {
        "name": "pytorch tutorials",
        "repo_full_name": "pytorch/tutorials",
        "repo_url": "https://github.com/pytorch/tutorials",
        "description": "Tutorial repository for PyTorch with examples, docs, notebooks, and learner-facing improvements.",
        "language": "Python",
        "tech_stack": ["Python", "PyTorch", "Deep Learning", "Docs", "Notebooks"],
        "difficulty": "Beginner Friendly",
        "good_first_issues": 0,
        "open_issues": 0,
    },
]



DOMAIN_OPTIONS = [
    "AI/ML", "Web Development", "Backend", "Cybersecurity", "DevOps", "Mobile",
    "Data Science", "Blockchain", "Docs", "Testing", "UI/UX", "Databases",
    "Cloud", "Automation", "CLI Tools", "Developer Tools"
]

DOMAIN_TECH_STACKS = {
    "AI/ML": ["Machine Learning", "Deep Learning", "NLP", "Computer Vision", "PyTorch", "TensorFlow", "Scikit-learn", "Pandas", "NumPy", "Jupyter", "MLOps", "Keras", "Transformers", "Reinforcement Learning"],
    "Web Development": ["React", "Next.js", "Vue", "Angular", "TypeScript", "JavaScript", "Tailwind CSS", "CSS", "HTML", "Svelte", "Nuxt", "Web3.js", "Webpack", "Frontend"],
    "Backend": ["Python", "FastAPI", "Django", "Flask", "Node.js", "Express", "Java", "Spring Boot", "Go", "Rust", "PostgreSQL", "MongoDB", "API", "REST"],
    "Cybersecurity": ["Security", "Encryption", "Authentication", "JWT", "OAuth", "OWASP", "Penetration Testing", "Network Security", "Zero Trust", "Cryptography", "Python", "Go"],
    "DevOps": ["Docker", "Kubernetes", "CI/CD", "GitHub Actions", "Terraform", "Prometheus", "Grafana", "Jenkins", "CloudFormation", "Monitoring", "Infrastructure as Code"],
    "Mobile": ["React Native", "Flutter", "Swift", "Kotlin", "iOS", "Android", "Cross-platform", "Native", "Mobile UI"],
    "Data Science": ["Pandas", "NumPy", "Matplotlib", "Jupyter", "Data Visualization", "ETL", "Data Engineering", "Statistics", "Scikit-learn", "SQL"],
    "Blockchain": ["Solidity", "Web3", "Smart Contracts", "Ethereum", "Rust", "Go", "The Graph", "Hardhat", "Truffle", "DeFi"],
    "Docs": ["Documentation", "Markdown", "MDX", "Docusaurus", "Sphinx", "API Docs", "Examples", "Tutorials", "Technical Writing"],
    "Testing": ["Testing", "Jest", "PyTest", "Unit Testing", "Integration Testing", "E2E", "Cypress", "Selenium", "Test Framework"],
    "UI/UX": ["React", "TypeScript", "CSS", "Design System", "Accessibility", "HTML", "Storybook", "Figma", "Component Library", "CSS Framework"],
    "Databases": ["PostgreSQL", "MongoDB", "Redis", "MySQL", "Elasticsearch", "DynamoDB", "Database Design", "SQL", "Migrations"],
    "Cloud": ["AWS", "Google Cloud", "Azure", "Kubernetes", "Docker", "Deployment", "Cloud Native", "Serverless", "Lambda"],
    "Automation": ["Python", "JavaScript", "Bash", "Scripting", "Automation", "Workflow", "CI/CD", "Task Automation", "RPA"],
    "CLI Tools": ["CLI", "Command Line", "Go", "Rust", "Python", "Shell", "TypeScript", "Command Line Interface", "Terminal"],
    "Developer Tools": ["Developer Tools", "IDE", "Build Tools", "Compiler", "Debugger", "Code Generation", "Linter", "Formatter", "Testing Tools"],
}

LEVEL_OPTIONS = ["Beginner Friendly", "Intermediate", "Advanced"]

LANGUAGE_OPTIONS = [
    "Python", "JavaScript", "TypeScript", "Java", "C", "C++", "Go", "Rust",
    "Kotlin", "Swift", "PHP", "Ruby", "C#", "HTML/CSS", "SQL", "Solidity",
    "Shell", "Dart", "Scala"
]

SORT_OPTIONS = ["Best match", "Most Good First Issues", "Most Open Issues", "Recently Updated", "Beginner Friendly First", "Name A-Z"]

STARTER_AI_ML_QUERIES = [
    "python machine learning docs beginner",
    "pandas numpy data preprocessing docs",
    "scikit learn examples documentation",
    "nlp python transformers docs",
    "computer vision python opencv",
    "pytorch examples beginner",
    "data science python good first issue",
    "mlops python docs testing",
]


def get_next_starter_query() -> str:
    idx = int(st.session_state.get("starter_query_index", 0))
    query = STARTER_AI_ML_QUERIES[idx % len(STARTER_AI_ML_QUERIES)]
    st.session_state.starter_query_index = idx + 1
    return query


def is_selected_repo(repo: Dict[str, Any]) -> bool:
    """Return True if this repository is already in the current shortlist."""
    full_name = repo_full_name(repo)
    if not full_name:
        return False

    return any(repo_full_name(item) == full_name for item in st.session_state.selected_repos)


def add_repo_to_shortlist(repo: Dict[str, Any]) -> None:
    """Add a repository to the session shortlist without duplicates."""
    if not is_selected_repo(repo):
        st.session_state.selected_repos.append(dict(repo))




def issue_text(issue: Dict[str, Any]) -> str:
    return " ".join(
        [
            str(issue.get("title", "")),
            str(issue.get("body", "")),
            " ".join(unique_clean(issue.get("labels", []))),
        ]
    ).lower()


def infer_issue_type(issue: Dict[str, Any]) -> str:
    text = issue_text(issue)

    if any(word in text for word in ["doc", "readme", "documentation", "typo"]):
        return "Docs"
    if any(word in text for word in ["notebook", "example", "tutorial", "demo"]):
        return "Example notebook"
    if any(word in text for word in ["preprocess", "dataset", "data cleaning", "data pipeline"]):
        return "Data preprocessing"
    if any(word in text for word in ["train", "training", "model", "loss", "epoch"]):
        return "Model training"
    if any(word in text for word in ["metric", "accuracy", "evaluation", "benchmark"]):
        return "Evaluation"
    if any(word in text for word in ["api", "endpoint", "backend", "server"]):
        return "API/backend"
    if any(word in text for word in ["test", "pytest", "unit test"]):
        return "Testing"
    if any(word in text for word in ["bug", "fix", "error", "crash"]):
        return "Bug"
    return "General"


def infer_ml_area(issue: Dict[str, Any]) -> str:
    text = issue_text(issue)

    if any(word in text for word in ["nlp", "tokenizer", "transformer", "llm", "language model"]):
        return "NLP"
    if any(word in text for word in ["vision", "image", "opencv", "ocr", "segmentation", "detection"]):
        return "Computer Vision"
    if any(word in text for word in ["sklearn", "classification", "regression", "clustering"]):
        return "Classical ML"
    if any(word in text for word in ["pytorch", "tensorflow", "keras", "neural", "deep learning"]):
        return "Deep Learning"
    if any(word in text for word in ["data", "dataset", "preprocess", "cleaning"]):
        return "Data cleaning"
    if any(word in text for word in ["docker", "deploy", "pipeline", "mlops", "workflow"]):
        return "MLOps"
    return "General"


def infer_required_knowledge(issue: Dict[str, Any]) -> str:
    text = issue_text(issue)

    if "pytorch" in text:
        return "PyTorch"
    if "tensorflow" in text or "keras" in text:
        return "TensorFlow"
    if "sklearn" in text or "scikit" in text:
        return "Scikit-learn"
    if "numpy" in text or "pandas" in text:
        return "NumPy/Pandas"
    return "Python only"


def issue_matches_filters(issue: Dict[str, Any]) -> bool:
    labels = [label.lower() for label in unique_clean(issue.get("labels", []))]
    selected_labels = [label.lower() for label in st.session_state.issue_labels]
    custom_labels = [
        label.strip().lower()
        for label in st.session_state.custom_labels.split(",")
        if label.strip()
    ]

    common_labels = {
        "good first issue", "help wanted", "bug", "documentation", "enhancement",
        "frontend", "backend", "ui", "api", "python", "javascript"
    }

    # If the user selected almost every label, treat it as "Any label".
    # Otherwise the filter feels broken because it is visually "everything".
    label_filter_is_all = selected_labels and set(selected_labels).issuperset(common_labels)

    required_labels = ([] if label_filter_is_all else selected_labels) + custom_labels
    if required_labels and not any(label in labels for label in required_labels):
        return False

    if st.session_state.assignee_filter == "Only unassigned" and issue.get("assignee"):
        return False

    if st.session_state.assignee_filter == "Assigned only" and not issue.get("assignee"):
        return False

    if int(issue.get("comments", 0) or 0) > int(st.session_state.max_comments):
        return False

    if st.session_state.issue_type != "Any" and infer_issue_type(issue) != st.session_state.issue_type:
        return False

    if st.session_state.ml_area != "Any" and infer_ml_area(issue) != st.session_state.ml_area:
        return False

    if st.session_state.required_knowledge != "Any" and infer_required_knowledge(issue) != st.session_state.required_knowledge:
        return False

    keyword = st.session_state.issue_keywords.strip().lower()
    if keyword and keyword not in issue_text(issue):
        return False

    return True


def local_issue_score(issue: Dict[str, Any]) -> float:
    score = 0.0
    labels = [label.lower() for label in unique_clean(issue.get("labels", []))]
    comments = int(issue.get("comments", 0) or 0)
    issue_type = infer_issue_type(issue)
    ml_area = infer_ml_area(issue)
    required = infer_required_knowledge(issue)

    if not issue.get("assignee"):
        score += 18
    if "good first issue" in labels:
        score += 22
    if "help wanted" in labels:
        score += 14

    if comments == 0:
        score += 16
    elif comments <= 2:
        score += 12
    elif comments <= 5:
        score += 8

    if issue_type in st.session_state.contribution_types:
        score += 10

    if ml_area in st.session_state.ml_interests or st.session_state.ml_area == ml_area:
        score += 10

    if required in st.session_state.user_skills or required == "Python only":
        score += 10

    created_at = issue.get("created_at")
    if created_at:
        try:
            created = datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
            age_days = (datetime.now(timezone.utc) - created).days
            if age_days <= 30:
                score += 4
        except ValueError:
            pass

    return min(score, 100)


def score_badge(score: int) -> str:
    """Clean numeric score. No red/orange emoji dots."""
    try:
        value = int(score)
    except (TypeError, ValueError):
        value = 0
    return f"{value}/100"


def score_label(score: int) -> str:
    try:
        value = int(score)
    except (TypeError, ValueError):
        value = 0
    if value >= 75:
        return "Strong fit"
    if value >= 55:
        return "Good fit"
    return "Candidate"


def _h(value: Any) -> str:
    """Small HTML escape helper for custom cards."""
    return html.escape(str(value or ""), quote=True)


def issue_key(issue: Dict[str, Any]) -> str:
    return str(issue.get("url") or issue.get("html_url") or issue.get("title") or safe_key(issue))


def is_issue_saved(issue: Dict[str, Any]) -> bool:
    key = issue_key(issue)
    return any(saved.get("_saved_key") == key for saved in st.session_state.saved_issues)


def toggle_save_issue(issue: Dict[str, Any]) -> None:
    key = issue_key(issue)

    if is_issue_saved(issue):
        st.session_state.saved_issues = [
            saved for saved in st.session_state.saved_issues
            if saved.get("_saved_key") != key
        ]
    else:
        saved = dict(issue)
        saved["_saved_key"] = key
        saved["_saved_at"] = datetime.now(timezone.utc).isoformat()
        repo = st.session_state.active_repo_detail or st.session_state.active_repo or {}
        saved["_repo_name"] = get_repo_display_name(repo)
        st.session_state.saved_issues.append(saved)


# ─────────────────────────────────────────────────────────────
# DATA ACTIONS
# ─────────────────────────────────────────────────────────────



def selected_is_any(selected: Any, all_options: Optional[List[str]] = None, broad_threshold: int = 6) -> bool:
    items = selected if isinstance(selected, list) else unique_clean(selected)
    if not items:
        return True
    if all_options and set(items).issuperset(set(all_options)):
        return True
    return len(items) >= broad_threshold


def contains_any_choice(text: str, selected_items: Any, aliases: Optional[Dict[str, List[str]]] = None) -> bool:
    """OR logic for multi-select filters.

    Empty selection means "Any".
    Multiple selections mean "match at least one".
    """
    items = selected_items if isinstance(selected_items, list) else unique_clean(selected_items)
    if not items:
        return True

    text = (text or "").lower()
    aliases = aliases or {}

    for item in items:
        key = str(item).lower().strip()
        if not key:
            continue

        choices = [key] + [alias.lower() for alias in aliases.get(str(item), [])]
        if any(choice in text for choice in choices):
            return True

    return False


def match_summary(repo: Dict[str, Any], domain: str, languages: List[str], stacks: List[str]) -> str:
    text = searchable_repo_text(repo)
    repo_lang = str(repo.get("language", "") or "").strip()

    matched_parts = []

    if domain:
        matched_parts.append(domain)

    if languages:
        lang_hits = []
        for lang in languages:
            if repo_lang.lower() == str(lang).lower() or str(lang).lower() in text:
                lang_hits.append(str(lang))
        if lang_hits:
            matched_parts.append("Lang: " + ", ".join(lang_hits[:2]))

    if stacks:
        stack_hits = []
        for stack in stacks:
            if str(stack).lower() in text:
                stack_hits.append(str(stack))
        if stack_hits:
            matched_parts.append("Stack: " + ", ".join(stack_hits[:3]))

    if repo.get("_matched_query"):
        matched_parts.append("GitHub match")

    return " · ".join(matched_parts[:4]) if matched_parts else "General match"


def project_matches_filters(
    repo: Dict[str, Any],
    keywords: str = "",
    tech_stack: Any = "",
    language: Any = "",
    difficulty: str = "",
    domain: str = "AI/ML",
) -> bool:
    text = searchable_repo_text(repo)
    tags_text = " ".join(get_repo_tags(repo)).lower()
    combined_text = f"{text} {tags_text}"

    domain_terms = {
        "AI/ML": ["ai", "ml", "machine", "learning", "python", "data", "model", "nlp", "vision", "pytorch", "tensorflow"],
        "Web Development": ["react", "next", "frontend", "web", "javascript", "typescript", "html", "css", "vue", "angular"],
        "Backend": ["backend", "api", "server", "fastapi", "django", "flask", "node", "database", "express", "spring"],
        "Cybersecurity": ["security", "auth", "owasp", "cyber", "jwt", "oauth", "encryption", "vulnerability", "penetration"],
        "DevOps": ["devops", "docker", "kubernetes", "ci", "deploy", "terraform", "monitoring", "infrastructure"],
        "Mobile": ["mobile", "android", "flutter", "react native", "ios", "kotlin", "swift"],
        "Data Science": ["data", "pandas", "numpy", "jupyter", "visualization", "analytics", "etl", "engineering"],
        "Blockchain": ["blockchain", "solidity", "web3", "smart contract", "graph", "ethereum", "defi"],
        "Docs": ["documentation", "docs", "tutorial", "guide", "markdown", "docusaurus"],
        "Testing": ["testing", "test", "jest", "pytest", "e2e", "cypress", "selenium"],
        "UI/UX": ["ui", "ux", "design", "component", "storybook", "accessibility", "figma"],
        "Databases": ["database", "postgresql", "mongodb", "redis", "mysql", "elasticsearch"],
        "Cloud": ["cloud", "aws", "gcp", "azure", "kubernetes", "serverless"],
        "Automation": ["automation", "script", "workflow", "rpa", "task"],
        "CLI Tools": ["cli", "command", "terminal", "tool", "go", "rust"],
        "Developer Tools": ["tool", "ide", "build", "compiler", "debugger", "linter"],
    }

    # Domain is the main intent. It should match at least one domain signal,
    # but GitHub search results are allowed if they came from the domain query.
    if domain:
        terms = domain_terms.get(domain, [])
        domain_ok = any(term in combined_text for term in terms) or bool(repo.get("is_github_search"))
        if terms and not domain_ok:
            return False

    # Keyword behaves as OR words, not all words.
    if keywords:
        words = [w.strip().lower() for w in str(keywords).replace(",", " ").split() if w.strip()]
        ignore = {"find", "repo", "repos", "project", "projects", "issue", "issues", "good", "first", "beginner"}
        words = [w for w in words if w not in ignore and len(w) > 1]
        if words and not any(word in combined_text for word in words):
            return False

    # OR logic inside tech stack. Empty = any stack.
    techs = tech_stack if isinstance(tech_stack, list) else unique_clean(tech_stack)
    if not selected_is_any(techs, DOMAIN_TECH_STACKS.get(domain, []), broad_threshold=7):
        if not contains_any_choice(combined_text, techs):
            return False

    # OR logic inside languages. Empty = any language.
    langs = language if isinstance(language, list) else unique_clean(language)
    if not selected_is_any(langs, LANGUAGE_OPTIONS, broad_threshold=6):
        repo_lang = str(repo.get("language", "")).lower()
        lang_text = f"{combined_text} {repo_lang}"
        if not contains_any_choice(lang_text, langs, {"HTML/CSS": ["html", "css"]}):
            return False

    # Difficulty should not hide good GitHub results too aggressively because
    # public GitHub repos rarely expose our custom difficulty labels.
    if difficulty and not repo.get("is_github_search"):
        difficulty_text = str(repo.get("difficulty", "")).lower()
        if difficulty_text and difficulty.lower() not in difficulty_text:
            return False

    return True


def curated_projects(keywords: str = "", tech_stack: Any = "", language: Any = "", difficulty: str = "", domain: str = "AI/ML") -> List[Dict[str, Any]]:
    if domain != "AI/ML":
        return []
    return [dict(repo) for repo in CURATED_AI_ML_REPOS if project_matches_filters(repo, keywords, tech_stack, language, difficulty, domain)]


def score_repo_match(repo: Dict[str, Any], keywords: str = "", domain: str = "", languages: Optional[List[str]] = None, tech_stacks: Optional[List[str]] = None) -> float:
    """Score how well a repo matches the search criteria for ranking."""
    score = 0.0
    languages = languages or []
    tech_stacks = tech_stacks or []
    
    # Curated repos get highest priority
    if repo.get("is_curated"):
        score += 100
    
    # Source priority: GitHub from domain search > GitHub general > GSSoC
    if repo.get("is_github_search"):
        score += 50
    if repo.get("is_gssoc"):
        score += 30
    
    # Stars (normalized, max +30)
    stars = int(repo.get("stars", 0) or 0)
    score += min(30, stars / 500)
    
    # Open issues (indicator of activity, max +20)
    open_issues = int(repo.get("open_issues", 0) or 0) + int(repo.get("good_first_issues", 0) or 0)
    score += min(20, open_issues / 50)
    
    # Keyword matches in repo text
    if keywords:
        text = searchable_repo_text(repo).lower()
        words = [w.strip().lower() for w in str(keywords).replace(",", " ").split() if w.strip()]
        for word in words:
            if len(word) > 1 and word in text:
                score += 5
    
    # Language match (exact match or topic match)
    if languages:
        repo_lang = str(repo.get("language", "")).lower()
        for lang in languages:
            if repo_lang == lang.lower() or lang.lower() in searchable_repo_text(repo).lower():
                score += 10
                break
    
    # Tech stack match
    if tech_stacks:
        combined_text = searchable_repo_text(repo).lower()
        for stack in tech_stacks:
            if str(stack).lower() in combined_text:
                score += 8
    
    # Recency bonus (updated recently is good)
    try:
        updated_at = repo.get("updated_at", "")
        if updated_at:
            from datetime import datetime, timezone
            updated = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            days_old = (datetime.now(timezone.utc) - updated).days
            if days_old < 30:
                score += 15
            elif days_old < 90:
                score += 10
            elif days_old < 365:
                score += 5
    except Exception:
        pass
    
    return score


def unique_projects(projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    unique = []
    for project in projects:
        key = repo_full_name(project).lower()
        if not key:
            key = str(project.get("name", "")).lower()
        if key and key not in seen:
            unique.append(project)
            seen.add(key)
    return unique


def rank_search_results(projects: List[Dict[str, Any]], domain: str = "", keywords: str = "", languages: Optional[List[str]] = None, tech_stacks: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Rank projects by relevance to search criteria."""
    languages = languages or []
    tech_stacks = tech_stacks or []
    
    # Score each project
    scored = []
    for project in projects:
        score = score_repo_match(project, keywords=keywords, domain=domain, languages=languages, tech_stacks=tech_stacks)
        scored.append((score, project))
    
    # Sort by score descending (highest scores first), then by stars
    scored.sort(key=lambda x: (x[0], x[1].get("stars", 0)), reverse=True)
    
    return [project for _, project in scored]


def search_projects() -> None:
    try:
        keywords = st.session_state.repo_search_text or st.session_state.keywords or ""
        domain = st.session_state.domain_filter or "AI/ML"
        tech_stack = st.session_state.tech_stack or []
        languages = st.session_state.language or []
        difficulty = st.session_state.difficulty or ""

        with st.spinner(f"Searching {domain} repositories..."):
            # Gather results from all sources
            curated = curated_projects(
                keywords=keywords,
                tech_stack=tech_stack,
                language=languages,
                difficulty=difficulty,
                domain=domain,
            )
            # Mark curated repos so they rank higher
            for repo in curated:
                repo["is_curated"] = True

            # GSSoC search (optional source, not primary)
            backend_language = languages[0] if languages else ""
            gssoc = cached_search_projects(
                keywords=" ".join([keywords, domain] + tech_stack),
                tech_stack="",
                language=backend_language,
                difficulty=difficulty,
                sort_by=st.session_state.sort_by,
            )
            gssoc = [
                repo for repo in gssoc
                if project_matches_filters(repo, keywords, tech_stack, languages, difficulty, domain)
            ]

            # GitHub search is primary for all domains
            github = cached_github_repo_search(
                keywords=keywords,
                domain=domain,
                tech_stack=tuple(tech_stack),
                languages=tuple(languages),
                sort_by=st.session_state.sort_by,
            )
            github = [
                repo for repo in github
                if project_matches_filters(repo, keywords, tech_stack, languages, difficulty, domain)
            ]

            # Combine results: curated > github > gssoc (order matters for initial rank)
            combined = unique_projects(curated + github + gssoc)
            
            # Rank by relevance
            combined = rank_search_results(
                combined,
                domain=domain,
                keywords=keywords,
                languages=languages,
                tech_stacks=tech_stack
            )

            if not combined:
                # Fallback: broad search by domain only
                fallback = cached_github_repo_search(
                    keywords=domain,
                    domain=domain,
                    tech_stack=tuple(),
                    languages=tuple(),
                    sort_by="Best match",
                )
                combined = unique_projects(fallback)
                combined = rank_search_results(combined, domain=domain)

            st.session_state.repo_results = combined[:18]

        st.session_state.keywords = keywords
        st.session_state.hero_keywords = keywords
        st.session_state.page = "discover"
    except Exception as exc:
        st.error(f"Search failed: {exc}")


def load_default_repos_once(force_refresh: bool = False) -> None:
    if not force_refresh and (st.session_state.default_repos_loaded or st.session_state.repo_results):
        return

    query = get_next_starter_query()
    try:
        with st.spinner(f"Loading starter repositories for: {query}"):
            curated = curated_projects(keywords="", tech_stack=[], language=["Python"], difficulty="", domain="AI/ML")
            for repo in curated:
                repo["is_curated"] = True
                
            github = cached_github_repo_search(
                keywords=query,
                domain="AI/ML",
                tech_stack=tuple(),
                languages=("Python",),
                sort_by=DEFAULT_SORT,
            )
            gssoc = cached_search_projects(keywords=query, tech_stack="", language="Python", difficulty="", sort_by=DEFAULT_SORT)
            gssoc = [repo for repo in gssoc if project_matches_filters(repo, query, [], ["Python"], "", "AI/ML")]
            
            combined = unique_projects(curated + github + gssoc)
            combined = rank_search_results(combined, domain="AI/ML", keywords=query, languages=["Python"])
            st.session_state.repo_results = combined[:18]

        st.session_state.keywords = ""
        st.session_state.hero_keywords = ""
        st.session_state.repo_search_text = ""
        st.session_state.default_repos_loaded = True
    except Exception:
        curated = curated_projects(domain="AI/ML", language=["Python"])
        for repo in curated:
            repo["is_curated"] = True
        st.session_state.repo_results = curated[:12]
        st.session_state.default_repos_loaded = True


def enrich_active_repo(repo: Dict[str, Any]) -> Dict[str, Any]:
    full_name = repo_full_name(repo)
    detail = dict(repo)

    if not full_name:
        detail["summary"] = repo.get("description", "No description available.")
        return detail

    try:
        metadata = cached_repo_metadata(full_name)
        detail["repo_valid"] = True
        detail.update(
            {
                "stars": metadata.get("stars", repo.get("stars", 0)),
                "forks": metadata.get("forks", repo.get("forks", 0)),
                "open_issues": metadata.get("open_issues_count", repo.get("open_issues", 0)),
                "language": metadata.get("language", repo.get("language", "")),
                "topics": metadata.get("topics", repo.get("topics", [])),
                "updated_at": metadata.get("updated_at", repo.get("updated_at", "")),
            }
        )
    except Exception:
        detail["repo_valid"] = False

    try:
        readme = cached_repo_readme(full_name)
        detail["readme"] = readme
        summary_data = cached_repo_summary(detail)

        if isinstance(summary_data, dict):
            detail["summary"] = summary_data.get("summary", detail.get("description", ""))
        else:
            detail["summary"] = detail.get("description", "No summary available.")
    except Exception:
        detail["summary"] = detail.get("description", "No summary available.")

    return detail


def select_repo_for_project(repo: Dict[str, Any]) -> None:
    add_repo_to_shortlist(repo)
    st.session_state.active_repo = repo
    st.session_state.active_repo_detail = None
    st.session_state.ranked_issues = []
    st.session_state.selected_issue_idx = 0
    st.session_state.issue_ai_breakdowns = {}
    go("queue")


def find_and_rank_issues_fast() -> None:
    repo = st.session_state.active_repo_detail or st.session_state.active_repo

    if not repo:
        st.warning("Select a repository first.")
        return

    full_name = repo_full_name(repo)

    if not full_name or "/" not in full_name:
        st.error("This project does not have a valid GitHub repository URL, so GitScout cannot fetch issues for it.")
        return

    try:
        with st.spinner("Fetching and ranking issues without AI..."):
            raw_issues = cached_open_issues(full_name)

        filtered = [issue for issue in raw_issues if issue_matches_filters(issue)]

        if not filtered:
            st.session_state.ranked_issues = []
            st.warning("No issues matched your filters. Try increasing max comments or selecting fewer labels.")
            return

        ranked = []
        for issue in filtered:
            issue_copy = dict(issue)
            issue_copy["fast_score"] = round(local_issue_score(issue_copy))
            issue_copy["issue_type"] = infer_issue_type(issue_copy)
            issue_copy["ml_area"] = infer_ml_area(issue_copy)
            issue_copy["required_knowledge"] = infer_required_knowledge(issue_copy)
            issue_copy["summary"] = truncate(issue_copy.get("body") or issue_copy.get("title"), 160)
            issue_copy.setdefault("difficulty", "Beginner" if issue_copy["fast_score"] >= 70 else "Intermediate")
            issue_copy.setdefault("competition", "Low" if int(issue_copy.get("comments", 0) or 0) <= 2 else "Medium")
            issue_copy.setdefault("skill_match", min(10, max(1, round(issue_copy["fast_score"] / 10))))
            ranked.append(issue_copy)

        sort_by = st.session_state.issue_sort
        if sort_by == "Lowest competition":
            ranked.sort(key=lambda item: int(item.get("comments", 0) or 0))
        elif sort_by == "Newest":
            ranked.sort(key=lambda item: item.get("created_at") or "", reverse=True)
        elif sort_by == "Beginner easiest":
            ranked.sort(key=lambda item: (item.get("difficulty") != "Beginner", -item.get("fast_score", 0)))
        else:
            ranked.sort(key=lambda item: item.get("fast_score", 0), reverse=True)

        st.session_state.ranked_issues = ranked
        st.session_state.selected_issue_idx = 0

    except Exception as exc:
        message = str(exc)
        if "404" in message or "Not Found" in message:
            st.session_state.ranked_issues = []
            st.error(
                f"GitHub could not find `{full_name}` or its issues endpoint. "
                "This can happen when the project URL is outdated, private, renamed, or not a real GitHub repo."
            )
            st.info("Open the GitHub link from the project page to verify the repository, or choose another recommended repo.")
        else:
            st.error(f"Issue search failed: {exc}")



def extract_issue_section(body: str, headings: List[str], stop_headings: Optional[List[str]] = None) -> str:
    """Very small section extractor for GitHub issue templates.

    It is intentionally local and rule-based so the app can still explain issues
    when Gemini quota/rate-limit fails.
    """
    text = strip_markdown(body or "")
    if not text:
        return ""

    stop_headings = stop_headings or [
        "Proposed Solution", "Proposed Changes", "Expected behavior", "Expected Behavior",
        "Benefits", "Tasks", "Reproduction", "Additional context", "Screenshots",
        "Problem", "Description", "Motivation", "Acceptance Criteria"
    ]

    for heading in headings:
        pattern = re.compile(rf"({re.escape(heading)}\s*:?\s*)(.*)", re.IGNORECASE | re.DOTALL)
        match = pattern.search(text)
        if not match:
            continue

        section = match.group(2).strip()
        stop_positions = []
        for stop in stop_headings:
            if stop.lower() == heading.lower():
                continue
            stop_match = re.search(rf"\b{re.escape(stop)}\b\s*:?", section, re.IGNORECASE)
            if stop_match:
                stop_positions.append(stop_match.start())

        if stop_positions:
            section = section[:min(stop_positions)].strip()

        return section[:900].strip()

    return ""


def _issue_full_body(issue: Dict[str, Any]) -> str:
    """Return the longest available issue text so the coach does not only read the preview."""
    candidates = [
        issue.get("body"),
        issue.get("full_body"),
        issue.get("description"),
        issue.get("raw_body"),
        issue.get("summary"),
    ]
    clean = [strip_markdown(x) for x in candidates if str(x or "").strip()]
    return max(clean, key=len) if clean else ""


def _sentences_from_text(text: str, limit: int = 18) -> List[str]:
    text = strip_markdown(text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    pieces = re.split(r"(?<=[.!?])\s+", text)
    cleaned = []
    for piece in pieces:
        piece = piece.strip(" -•\t\n")
        if 35 <= len(piece) <= 280:
            cleaned.append(piece)
    return cleaned[:limit]


def _pick_sentences(text: str, keywords: List[str], fallback_count: int = 2) -> List[str]:
    sentences = _sentences_from_text(text, limit=28)
    hits = []
    for sentence in sentences:
        low = sentence.lower()
        if any(k in low for k in keywords):
            hits.append(sentence)
    if hits:
        return hits[:3]
    return sentences[:fallback_count]


def _is_weak_ai_value(value: Any) -> bool:
    text = " ".join(value) if isinstance(value, list) else strip_markdown(value)
    low = text.lower().strip()
    if not low:
        return True
    weak_phrases = [
        "check the issue body",
        "read the issue body",
        "identify the requested change",
        "make a small focused pr",
        "generate ai breakdown",
        "not confidently detected",
        "open the issue on github",
    ]
    return len(low) < 45 or any(p in low for p in weak_phrases)


def strengthen_issue_breakdown(issue: Dict[str, Any]) -> Dict[str, Any]:
    """Use the full issue body to replace generic AI/fallback lines with useful insight."""
    body = _issue_full_body(issue)
    title = strip_markdown(issue.get("title", "this issue"))
    full = f"{title}. {body}".strip()
    if not body:
        return issue

    local = local_issue_breakdown({**issue, "body": body})
    problem_lines = _pick_sentences(
        full,
        ["problem", "currently", "fails", "error", "bug", "cannot", "can't", "does not", "missing", "lacks", "unable", "issue", "bottleneck"],
    )
    change_lines = _pick_sentences(
        full,
        ["proposed", "expected", "add", "implement", "create", "update", "fix", "support", "allow", "ensure", "should", "need", "needs", "acceptance"],
    )
    approach_lines = _pick_sentences(
        full,
        ["file", "module", "component", "api", "backend", "frontend", "test", "readme", "config", "route", "service", "function"],
        fallback_count=3,
    )

    strengthened = dict(issue)
    replacements = {
        "core_problem": problem_lines or local.get("core_problem"),
        "expected_change": change_lines or local.get("expected_change"),
        "what_to_do": local.get("what_to_do") or approach_lines,
        "files_likely_needed": local.get("files_likely_needed"),
        "first_step": local.get("first_step"),
        "step_by_step_plan": local.get("step_by_step_plan"),
        "risks_or_unknowns": local.get("risks_or_unknowns"),
    }
    for key, replacement in replacements.items():
        if _is_weak_ai_value(strengthened.get(key)) and replacement:
            strengthened[key] = replacement
    return strengthened


def local_issue_breakdown(issue: Dict[str, Any], error: Optional[Exception] = None) -> Dict[str, Any]:
    """Create a useful issue explanation without AI.

    This is the safety net when Gemini is unavailable/quota-limited. It should
    still feel like a coach, not like copied issue text.
    """
    title = strip_markdown(issue.get("title", "this issue"))
    body = _issue_full_body(issue)
    lower = f"{title} {body}".lower()

    issue_type = infer_issue_type(issue)
    ml_area = infer_ml_area(issue)

    # Specialized deterministic explanations for common issue patterns.
    if "rabbitmq" in lower and ("redis" in lower or "pub/sub" in lower or "pub sub" in lower):
        core_problem = [
            "The backend currently appears to depend on Redis Pub/Sub for message publishing and subscription.",
            "The issue asks for RabbitMQ to be added as a pluggable alternative, so the app can use a more durable broker when needed.",
        ]
        expected_change = [
            "Add a RabbitMQ messaging implementation without removing the existing Redis Pub/Sub flow.",
            "Expose configuration so the project can choose Redis or RabbitMQ through environment/config settings.",
            "Keep the rest of the backend using a consistent messaging interface instead of hard-coding one broker everywhere.",
        ]
        what_to_do = [
            "Inspect the current Redis Pub/Sub implementation and understand its publish/subscribe methods.",
            "Find the interface or service layer used by the backend to send and consume messages.",
            "Create a RabbitMQ adapter/module with connection, exchange/queue setup, publish, and consume logic.",
            "Wire the selected broker through config or environment variables and add tests for the new path.",
        ]
        likely_files = [
            "backend messaging/pubsub module",
            "Redis Pub/Sub implementation folder",
            "configuration file / environment settings",
            "tests for messaging or backend services",
            "documentation or README setup notes",
        ]
        required = ["Backend architecture", "Async/message queues", "RabbitMQ basics", "Redis Pub/Sub basics", "Testing"]
        difficulty = "Intermediate"
        warning = "This is not just a small docs task. It needs backend design and careful testing so Redis support does not break."
        first_step = "Find the existing Redis Pub/Sub code and write down the methods the RabbitMQ adapter must match."

    elif "timeout" in lower and ("rag" in lower or "streaming" in lower or "cancellation" in lower):
        core_problem = [
            "Long-running RAG, retrieval, LLM inference, or streaming requests may keep running even after the client disconnects or the request takes too long.",
            "That can waste server resources, leave orphan async tasks, and create poor user experience for stalled requests.",
        ]
        expected_change = [
            "Add centralized timeout handling for long-running requests.",
            "Support cancelling abandoned async/streaming workflows cleanly.",
            "Return clear HTTP/SSE errors and log timeout/cancellation events for observability.",
        ]
        what_to_do = [
            "Find where RAG queries, retrieval, and streaming responses are executed.",
            "Add configurable timeout values through settings/environment config.",
            "Wrap long-running async operations so they can be cancelled safely.",
            "Add cleanup/logging and tests for timeout and client-disconnect cases.",
        ]
        likely_files = [
            "backend API route handling RAG queries",
            "streaming/SSE response handler",
            "RAG pipeline or retrieval service",
            "configuration/settings module",
            "tests for timeout and cancellation behavior",
        ]
        required = ["Async Python", "FastAPI/backend requests", "RAG pipeline basics", "Timeout/cancellation handling"]
        difficulty = "Advanced"
        warning = "This is a backend reliability task. It is better after understanding the project’s async flow."
        first_step = "Trace the request path from the API route to the RAG pipeline and identify where long-running tasks are created."

    elif ("new model" in lower or "add model" in lower or "transformers" in lower or "weight conversion" in lower) and ("model" in lower):
        core_problem = [
            "The library does not currently support the model mentioned in this issue.",
            "The requested work is likely to add a new model implementation, not just a small documentation update.",
        ]
        expected_change = [
            "Add model/config implementation files following the repository’s existing model patterns.",
            "Add weight conversion or loading support if official checkpoints already exist.",
            "Add tests and documentation/examples so users can load and use the model.",
        ]
        what_to_do = [
            "Study a similar model already implemented in the repo.",
            "Identify the expected config/model/test/docs structure.",
            "Implement the model carefully and verify output compatibility.",
            "Add tests, conversion notes, and documentation.",
        ]
        likely_files = [
            "model implementation folder",
            "configuration/modeling files",
            "conversion script",
            "tests",
            "documentation/model docs",
        ]
        required = ["PyTorch/model internals", "Transformers-style architecture", "Testing", "Model documentation"]
        difficulty = "Advanced"
        warning = "This is probably not a good first issue unless you already know model internals and the repo structure."
        first_step = "Find a similar existing model implementation in the repo and compare what files would be needed."

    elif "troubleshooting" in lower or ("readme" in lower and ("docker" in lower or "env" in lower or "setup" in lower)):
        core_problem = [
            "The project setup instructions exist, but beginners may get stuck when common setup errors happen.",
            "The issue asks for a troubleshooting section so contributors can fix common local setup problems faster.",
        ]
        expected_change = [
            "Add a clear Troubleshooting section to the README or docs.",
            "Cover common errors like Docker issues, missing environment variables, port conflicts, migrations, or service connection errors.",
        ]
        what_to_do = [
            "Run or inspect the setup flow and list likely beginner errors.",
            "Add short problem → cause → fix entries to the README/docs.",
            "Keep the instructions copy-paste friendly and platform-aware where needed.",
            "Preview the README and make sure formatting is clean.",
        ]
        likely_files = ["README.md", ".env.example", "docs/ setup pages"]
        required = ["Documentation writing", "Basic project setup", "Markdown"]
        difficulty = "Beginner"
        warning = ""
        first_step = "Open the README and find the best place to add a Troubleshooting section."

    else:
        problem = (
            extract_issue_section(body, ["Problem", "Description", "Motivation", "Current behavior", "Current Performance Bottleneck"])
            or " ".join(_pick_sentences(body, ["problem", "currently", "fails", "error", "cannot", "does not", "missing", "lacks", "unable"], fallback_count=2))
            or body[:650]
            or title
        )
        expected = (
            extract_issue_section(body, ["Proposed Solution", "Proposed Changes", "Expected behavior", "Expected Behavior", "Acceptance Criteria", "Tasks"])
            or " ".join(_pick_sentences(body, ["add", "implement", "create", "update", "fix", "support", "allow", "ensure", "should", "need", "expected", "proposed"], fallback_count=2))
            or f"Make a focused change that resolves the request in: {title}"
        )

        core_problem = [
            problem[:520],
            "GitScout extracted this from the full issue body, not only the title or first preview line.",
        ]
        expected_change = [
            expected[:520],
            "Keep the PR focused on this requested behavior and avoid unrelated refactors.",
        ]
        what_to_do = [
            "Read the complete issue body and mark the exact requested outcome.",
            "Search the repository for the feature, module, route, component, or docs area mentioned in the issue.",
            "Inspect the current behavior before editing so your PR fixes the real gap.",
            "Make a small focused change and include validation notes, screenshots, or tests when relevant.",
        ]
        likely_files = []
        if "readme" in lower or issue_type == "Docs":
            likely_files.extend(["README.md", "docs/ or documentation pages"])
        if "api" in lower or "backend" in lower or "request" in lower:
            likely_files.extend(["backend/API request handling code", "service or route handling the affected workflow"])
        if "frontend" in lower or "ui" in lower:
            likely_files.extend(["frontend component related to the issue", "UI state/error handling code"])
        if "test" in lower:
            likely_files.append("tests/ for the affected feature")
        if not likely_files:
            likely_files = ["Files/folders mentioned in the issue body", "Code area related to the issue title"]

        required = ["Git and GitHub PR workflow", "Ability to run the project locally", issue.get("required_knowledge") or "Project stack related to this issue"]
        advanced_keywords = ["architecture", "distributed", "rag", "streaming", "async cancellation", "timeout", "inference"]
        difficulty = "Advanced" if any(k in lower for k in advanced_keywords) else ("Beginner" if issue_type == "Docs" else "Intermediate")
        warning = "This may not be a good first PR. It likely needs repo-specific knowledge and careful testing." if difficulty == "Advanced" else ""
        first_step = "Open the issue on GitHub, read the full body, and identify the exact expected behavior."
        expected_change = expected_change

    steps = [
        first_step,
        "Find the existing implementation or documentation area related to the issue.",
        "Make a small focused change that solves only this issue.",
        "Add a test, docs update, or validation note depending on the task type.",
        "Open a PR with a short explanation of what changed and how you checked it.",
    ]

    return {
        "summary": f"This issue asks for a {difficulty.lower()} {issue_type.lower()} contribution related to: {title}.",
        "core_problem": core_problem,
        "expected_change": expected_change if 'expected_change' in locals() else expected_change,
        "why_it_matters": [
            "Solving this makes the project easier to use, extend, or maintain.",
            "A focused PR also helps maintainers review your contribution faster.",
        ],
        "what_to_do": what_to_do,
        "required_knowledge": required,
        "files_likely_needed": likely_files[:6],
        "step_by_step_plan": steps,
        "first_step": first_step,
        "risks_or_unknowns": [warning] if warning else [],
        "difficulty": difficulty,
        "beginner_warning": warning,
        "competition": issue.get("competition", issue.get("competition_level", "Low")),
        "skill_match": issue.get("skill_match", 6),
        "estimated_time": "1-3 hours for docs/small fixes; longer if implementation is complex.",
        "comment_short": _default_comment({
            **issue,
            "core_problem": " ".join(core_problem)[:260],
            "expected_change": " ".join(expected_change if isinstance(expected_change, list) else [str(expected_change)])[:220],
            "first_step": first_step,
        }),
        "comment_detailed": _default_comment({
            **issue,
            "core_problem": " ".join(core_problem)[:260],
            "expected_change": " ".join(expected_change if isinstance(expected_change, list) else [str(expected_change)])[:220],
            "first_step": first_step,
        }),
        "local_fallback": bool(error),
    }


def generate_ai_breakdown_for_selected() -> None:
    if not st.session_state.ranked_issues:
        return

    idx = min(st.session_state.selected_issue_idx, len(st.session_state.ranked_issues) - 1)
    issue = st.session_state.ranked_issues[idx]
    key = issue_key(issue)

    if key in st.session_state.issue_ai_breakdowns:
        return

    repo = st.session_state.active_repo_detail or st.session_state.active_repo or {}
    full_name = repo_full_name(repo)
    issue_number = issue.get("number")

    issue_context: Dict[str, Any] = dict(issue)

    try:
        with st.spinner("Fetching full issue context and generating AI breakdown..."):
            if full_name and issue_number:
                issue_context = cached_issue_context(full_name, int(issue_number))
            else:
                issue_context = dict(issue)

            issue_context.update({
                "fast_score": issue.get("fast_score"),
                "issue_type": issue.get("issue_type"),
                "ml_area": issue.get("ml_area"),
                "required_knowledge": issue.get("required_knowledge"),
            })

            user_profile = {
                "skill_level": st.session_state.skill_level,
                "user_skills": st.session_state.user_skills,
                "ml_interests": st.session_state.ml_interests,
                "contribution_types": st.session_state.contribution_types,
            }

            ai_result = cached_deep_issue_analysis(issue_context, user_profile)

        enriched_issue = dict(issue)
        enriched_issue.update(issue_context)
        if isinstance(ai_result, dict):
            enriched_issue.update(ai_result)

        enriched_issue.setdefault("title", issue.get("title", "Untitled issue"))
        enriched_issue.setdefault("url", issue.get("url", "#"))
        enriched_issue.setdefault("labels", issue.get("labels", []))
        enriched_issue.setdefault("comments", issue.get("comments", 0))

        st.session_state.issue_ai_breakdowns[key] = enriched_issue

    except Exception as exc:
        # Keep the UI useful even when Gemini/API quota fails. Do not show scary
        # raw API errors to the user; show a local coach-style fallback instead.
        fallback_issue = dict(issue)
        if isinstance(issue_context, dict):
            fallback_issue.update(issue_context)
        fallback_issue.update(local_issue_breakdown(fallback_issue, error=exc))
        st.session_state.issue_ai_breakdowns[key] = fallback_issue
        st.warning("AI quota/rate limit hit, so GitScout showed a local fallback explanation. Try AI again later for deeper analysis.")

# ─────────────────────────────────────────────────────────────
# NAVIGATION
# ─────────────────────────────────────────────────────────────
def render_nav() -> None:
    with st.container(border=True):
        brand_col, nav_col = st.columns([2.4, 3.1])
        with brand_col:
            st.markdown(
                """
                <div style="display:flex; align-items:center; padding:4px 0 2px;">
                    <div class="gs-brand-icon">G</div>
                    <div>
                        <div class="gs-brand-title">GitScout AI</div>
                        <div class="gs-brand-subtitle">open-source contribution coach</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with nav_col:
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1:
                if st.button("Discover", key="nav_discover", type="primary" if st.session_state.page == "discover" else "secondary", use_container_width=True):
                    go("discover")
            with c2:
                if st.button("Project", key="nav_queue", type="primary" if st.session_state.page == "queue" else "secondary", use_container_width=True):
                    go("queue")
            with c3:
                if st.button("Issue Coach", key="nav_issues", type="primary" if st.session_state.page == "issues" else "secondary", use_container_width=True):
                    go("issues")
            with c4:
                if st.button("Comment", key="nav_comment", type="primary" if st.session_state.page == "comment" else "secondary", use_container_width=True):
                    go("comment")
            with c5:
                if st.button(f"Saved ({len(st.session_state.saved_issues)})", key="nav_saved", type="primary" if st.session_state.page == "saved" else "secondary", use_container_width=True):
                    go("saved")
    st.divider()


def render_skill_matcher() -> None:
    with st.container(border=True):
        st.subheader("Find repositories")
        st.caption("Multiple languages and tech stacks work as OR choices. Empty means Any.")
        c1, c2, c3 = st.columns([1, 1, 1.2])
        with c1:
            st.selectbox("Domain", DOMAIN_OPTIONS, key="domain_filter")
            st.selectbox("Level", LEVEL_OPTIONS, key="difficulty")
        with c2:
            st.multiselect("Languages", LANGUAGE_OPTIONS, key="language", placeholder="Any language")
            st.caption("Selected languages = Python OR JavaScript OR Go")
            st.selectbox("Sort by", SORT_OPTIONS, key="sort_by")
        with c3:
            stack_options = DOMAIN_TECH_STACKS.get(st.session_state.domain_filter, DOMAIN_TECH_STACKS["AI/ML"])
            current_stack = [x for x in st.session_state.tech_stack if x in stack_options]
            if current_stack != st.session_state.tech_stack:
                st.session_state.tech_stack = current_stack
            st.multiselect("Tech stack", stack_options, key="tech_stack", placeholder="Any stack")
            st.caption("Selected stack = Auth OR JWT OR OWASP")
            st.text_input("Search keyword", key="repo_search_text", placeholder="docs, auth, backend, JWT...")
        b1, b2, b3 = st.columns([1, 1, 3])
        with b1:
            if st.button("Apply filters", key="apply_main_repo_filters", type="primary", use_container_width=True):
                search_projects()
                st.rerun()
        with b2:
            if st.button("Reset", key="reset_main_repo_filters", use_container_width=True):
                st.session_state.domain_filter = "AI/ML"
                st.session_state.tech_stack = []
                st.session_state.language = []
                st.session_state.difficulty = "Beginner Friendly"
                st.session_state.sort_by = DEFAULT_SORT
                st.session_state.repo_search_text = ""
                st.session_state.repo_results = []
                st.session_state.default_repos_loaded = False
                load_default_repos_once(force_refresh=True)
                st.rerun()
        with b3:
            st.caption("Tip: start with Python + Docs / Pandas / Scikit-learn for easier first PRs.")


def render_repo_refine_panel() -> None:
    st.info("Repository filters are now on the main Discover page.")

def render_repo_card(repo: Dict[str, Any], idx: int) -> None:
    """Readable repository card using Streamlit components only.

    This avoids raw HTML showing in the UI and keeps keys unique even when
    GitHub returns duplicate repos.
    """
    url = repo_url(repo)
    display_name = get_repo_display_name(repo)
    summary = truncate(repo.get("summary") or repo.get("description"), 190)
    tags = get_repo_tags(repo)

    best_for = infer_best_for(repo)
    required = infer_required_skills(repo)
    fit = infer_contribution_fit(repo)
    work = infer_available_work(repo)
    matched_str = match_summary(
        repo,
        st.session_state.domain_filter,
        st.session_state.language or [],
        st.session_state.tech_stack or [],
    )

    stars = github_stat(repo.get("stars"))
    forks = github_stat(repo.get("forks"))
    open_issues = github_stat(repo.get("open_issues") or repo.get("open_issues_count"))
    lang = str(repo.get("language") or "").strip() or "Unknown"
    unique = safe_key(f"{idx}-{display_name}-{url}")

    with st.container(border=True):
        top_l, top_r = st.columns([4, 1])
        with top_l:
            st.markdown(f"**{display_name}**")
        with top_r:
            if repo.get("is_curated"):
                st.caption("Curated")
            elif repo.get("is_github_search"):
                st.caption("GitHub")
            else:
                st.caption(lang)

        st.write(summary)

        with st.container(border=True):
            st.caption("Overview")
            r1, r2 = st.columns([1, 2.3])
            with r1:
                st.caption("BEST FOR")
            with r2:
                st.write(best_for)
            r3, r4 = st.columns([1, 2.3])
            with r3:
                st.caption("REQUIRED")
            with r4:
                st.write(" · ".join(required[:4]))
            r5, r6 = st.columns([1, 2.3])
            with r5:
                st.caption("WORK")
            with r6:
                st.write(" · ".join(work[:4]))
            r7, r8 = st.columns([1, 2.3])
            with r7:
                st.caption("MATCHED")
            with r8:
                st.write(matched_str)

        if tags:
            st.caption(" · ".join([lang] + tags[:3]))

        stat_parts = []
        if stars != "—":
            stat_parts.append(f"★ {stars}")
        if forks != "—":
            stat_parts.append(f"⑂ {forks}")
        if open_issues != "—":
            stat_parts.append(f"◎ {open_issues} issues")
        st.caption(" · ".join(stat_parts) if stat_parts else "GitHub stats load on the project page.")

        b1, b2 = st.columns(2)
        with b1:
            if st.button("View Project →", key=f"view_repo_{idx}_{unique}", type="primary", use_container_width=True):
                select_repo_for_project(repo)
        with b2:
            st.link_button("GitHub ↗", url, use_container_width=True)


def discover_page() -> None:
    load_default_repos_once()
    with st.container(border=True):
        left, right = st.columns([1.18, 0.82])
        with left:
            st.caption(f"✦ {len(st.session_state.repo_results)} repos · {len(st.session_state.ranked_issues)} ranked issues · {len(st.session_state.saved_issues)} saved")
            st.title("Discover open-source repos you can actually contribute to.")
            st.write("Choose your domain, language, level, and stack. GitScout finds matching repos first, then the Issue Coach helps you understand one issue deeply.")
        with right:
            with st.container(border=True):
                st.markdown("**Product loop**")
                st.write("Discover → Understand → Comment → Get assigned")
                st.caption("Search is only the entry. Understanding the issue is the real value.")
                if st.button("Generate comment from issue URL", key="dashboard_comment_button", type="primary", use_container_width=True):
                    go("comment")
    render_skill_matcher()
    h1, h2 = st.columns([5, 1])
    with h1:
        st.subheader("Matching repositories")
        st.caption("Live GitHub + project search. Filters use OR within languages/stacks and AND across filter groups.")
    with h2:
        if st.button("Refresh", key="refresh_default_repos", use_container_width=True):
            st.session_state.default_repos_loaded = False
            st.session_state.repo_results = []
            load_default_repos_once(force_refresh=True)
            st.rerun()
    if not st.session_state.repo_results:
        st.info("No repos matched. Try AI/ML + Python, or reset filters.")
        return
    for row_start in range(0, len(st.session_state.repo_results[:12]), 3):
        row = st.session_state.repo_results[row_start: row_start + 3]
        cols = st.columns(3)
        for offset, repo in enumerate(row):
            with cols[offset]:
                render_repo_card(repo, row_start + offset)


# ─────────────────────────────────────────────────────────────
# PROJECT PAGE
# ─────────────────────────────────────────────────────────────

def queue_page() -> None:
    repo = st.session_state.active_repo

    if not repo:
        st.warning("Select a repository first.")
        return

    if st.button("← Back to repositories", key="back_to_repos"):
        go("discover")

    if st.session_state.active_repo_detail is None:
        with st.spinner("Loading repository details and AI summary for this repo only..."):
            st.session_state.active_repo_detail = enrich_active_repo(repo)

    detail = st.session_state.active_repo_detail

    url = repo_url(detail)
    display_name = get_repo_display_name(detail)
    tags = get_repo_tags(detail)
    summary = detail.get("summary") or detail.get("description") or "No summary available."
    summary = truncate(summary, 650)

    stars = github_stat(detail.get("stars"))
    forks = github_stat(detail.get("forks"))
    open_issues = github_stat(detail.get("open_issues") or detail.get("open_issues_count"))

    best_for = infer_best_for(detail)
    required = infer_required_skills(detail)
    fit = infer_contribution_fit(detail)
    work = infer_available_work(detail)

    left, right = st.columns([0.9, 1.1])

    with left:
        with st.container(border=True):
            st.caption(f"`{display_name}`")
            st.header(detail.get("name", display_name))
            st.write(summary)

            if tags:
                st.caption("Tags: " + " · ".join(tags))

            s1, s2, s3 = st.columns(3)
            s1.metric("Stars", stars)
            s2.metric("Forks", forks)
            s3.metric("Open issues", open_issues)

            st.divider()
            st.markdown(f"**Best for:** {best_for}")
            st.markdown(f"**Required skills:** {' · '.join(required)}")
            st.markdown(f"**Contribution fit:** {fit}")
            st.markdown(f"**Available work:** {' · '.join(work)}")

        st.link_button("Open repository on GitHub ↗", url, use_container_width=True)

    with right:
        with st.container(border=True):
            st.subheader("Why this repo matches you")

            for reason in dynamic_repo_reasons(detail):
                st.write(f"✓ {reason}")

        with st.container(border=True):
            st.subheader("Suggested contribution path")
            st.write("1. Start with docs/examples or low-comment beginner issues.")
            st.write("2. Move to small bugs or tests in the same repo.")
            st.write("3. After one merged PR, try a data/model-related issue.")

        if detail.get("repo_valid") is False:
            st.error("GitHub could not verify this repository. The project listing may be outdated or the repo may be private/renamed.")
            st.caption("Open the GitHub link to verify it, or choose another recommended repo.")
        else:
            if st.button("Find issues in this repo →", key="goto_issues", type="primary", use_container_width=True):
                go("issues")


# ─────────────────────────────────────────────────────────────
# ISSUES PAGE
# ─────────────────────────────────────────────────────────────

def render_issue_refine_panel() -> None:
    with st.container(border=True):
        st.subheader("Find low-competition issues")
        st.caption("Start simple. Advanced filters are hidden so the page feels like a coach, not a form.")

        c1, c2, c3 = st.columns([1, 1, 1.2])

        with c1:
            st.selectbox("Assignee", ["Only unassigned", "Any", "Assigned only"], key="assignee_filter")

        with c2:
            st.number_input("Max comments", min_value=0, max_value=50, step=1, key="max_comments")

        with c3:
            st.selectbox(
                "Sort",
                ["Best match", "Lowest competition", "Newest", "Beginner easiest"],
                key="issue_sort",
            )

        toggle_label = "Hide advanced issue filters" if st.session_state.advanced_issue_filters_open else "Show advanced issue filters"
        if st.button(toggle_label, key="advanced_issue_filters_toggle", use_container_width=False):
            st.session_state.advanced_issue_filters_open = not st.session_state.advanced_issue_filters_open
            st.rerun()

        if st.session_state.advanced_issue_filters_open:
            st.divider()
            common_labels = [
                "good first issue",
                "help wanted",
                "bug",
                "documentation",
                "enhancement",
                "frontend",
                "backend",
                "ui",
                "api",
                "python",
                "javascript",
            ]

            a1, a2, a3 = st.columns(3)

            with a1:
                st.multiselect("Labels", common_labels, key="issue_labels")
                st.text_input("Custom labels", key="custom_labels", placeholder="auth, api, ui...")

            with a2:
                st.selectbox(
                    "Issue type",
                    [
                        "Any",
                        "Docs",
                        "Bug",
                        "Example notebook",
                        "Data preprocessing",
                        "Model training",
                        "Evaluation",
                        "API/backend",
                        "Testing",
                    ],
                    key="issue_type",
                )
                st.selectbox(
                    "ML area",
                    [
                        "Any",
                        "NLP",
                        "Computer Vision",
                        "Classical ML",
                        "Deep Learning",
                        "Data cleaning",
                        "MLOps",
                        "General",
                    ],
                    key="ml_area",
                )

            with a3:
                st.selectbox(
                    "Required knowledge",
                    ["Any", "Python only", "NumPy/Pandas", "Scikit-learn", "PyTorch", "TensorFlow"],
                    key="required_knowledge",
                )
                st.text_input("Keyword", key="issue_keywords", placeholder="loading, docs, tokenizer...")

        b1, b2 = st.columns([1, 3])
        with b1:
            if st.button("Find beginner issues", key="find_best_issues", type="primary", use_container_width=True):
                find_and_rank_issues_fast()
        with b2:
            st.caption("This ranking is instant and rule-based. AI runs only after you select an issue.")


def render_issue_list_item(issue: Dict[str, Any], idx: int) -> None:
    """Compact left-side issue card; stays aligned and readable."""
    selected = idx == st.session_state.selected_issue_idx
    score = int(issue.get("fast_score", 0) or 0)
    summary = truncate(issue.get("summary") or issue.get("body") or issue.get("title"), 130)
    competition = issue.get("competition_level") or issue.get("competition", "N/A")
    saved = is_issue_saved(issue)
    title = strip_markdown(issue.get("title", "Untitled issue"))
    issue_type = issue.get("issue_type", "General")
    comments = issue.get("comments", 0)
    required = issue.get("required_knowledge", "Python only")
    selected_class = " selected" if selected else ""
    selected_badge = '<span class="gs-fit-pill">Selected</span>' if selected else ''

    st.markdown(
        f"""
        <div class="gs-issue-row-card{selected_class}">
            <div style="display:flex; justify-content:space-between; gap:12px; align-items:flex-start;">
                <h3 class="gs-issue-title">{_h(title)}</h3>
                <div style="display:flex; gap:6px; flex-wrap:wrap; justify-content:flex-end;">{selected_badge}<span class="gs-fit-pill">Fit {_h(score)}/100</span></div>
            </div>
            <p class="gs-repo-desc" style="min-height:auto; margin-top:10px;">{_h(summary)}</p>
            <div class="gs-issue-meta">{_h(issue_type)} · {_h(required)} · {_h(comments)} comments · {_h(competition)} competition</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    b1, b2 = st.columns(2)
    with b1:
        label = "Selected" if selected else "Select issue"
        if st.button(label, key=f"select_issue_{idx}_{safe_key(issue.get('title', 'issue'))}", use_container_width=True):
            st.session_state.selected_issue_idx = idx
            st.rerun()
    with b2:
        save_label = "Unsave" if saved else "Save"
        if st.button(save_label, key=f"save_issue_{idx}_{safe_key(issue_key(issue))}", use_container_width=True):
            toggle_save_issue(issue)
            st.rerun()


def clean_ai_field(value: Any) -> str:
    text = strip_markdown(value)
    text = re.sub(r"^(summary|core problem|expected change|what you.?ll do|what to do|first step|why it matters)\s*[:\-]\s*", "", text, flags=re.IGNORECASE).strip()
    return text


def as_bullet_points(value: Any, max_items: int = 5) -> List[str]:
    if isinstance(value, list):
        items = [clean_ai_field(item) for item in value]
    else:
        text = clean_ai_field(value)
        if not text:
            return []
        if text.strip().startswith("{") or '"summary"' in text[:160]:
            return ["AI returned an invalid structure. Regenerate the breakdown or use the original issue body below."]
        rough = re.split(r"(?:\n+|\d+\.\s+|;\s+)", text)
        if len(rough) <= 1:
            rough = re.split(r"(?<=[.!?])\s+", text)
        items = [clean_ai_field(item) for item in rough]

    cleaned = []
    for item in items:
        if not item:
            continue
        if item.strip().startswith("{") or '"summary"' in item[:160]:
            continue
        cleaned.append(item)
    return cleaned[:max_items]


def render_bullets(items: List[str]) -> None:
    if not items:
        st.write("Not confidently detected yet.")
        return
    for item in items:
        st.write(f"• {item}")


def contribution_comment(issue: Dict[str, Any]) -> str:
    title = issue.get("title", "this issue")
    first_step = issue.get("first_step") or "I’ll start by reviewing the related files and understanding the expected change."

    return (
        f"Hi! I’d like to work on this issue.\n\n"
        f"I reviewed the issue: \"{strip_markdown(title)}\".\n\n"
        f"My first step will be: {strip_markdown(first_step)}\n\n"
        f"Please assign this to me if it is still available. Thank you!"
    )


def get_ai_breakdown(issue: Dict[str, Any]) -> Dict[str, Any]:
    key = issue_key(issue)
    stored = st.session_state.issue_ai_breakdowns.get(key)
    return stored or issue


def _stringify_list(value: Any) -> str:
    if not value:
        return "Not clear from issue."
    if isinstance(value, list):
        return "\n".join(f"- {strip_markdown(item)}" for item in value if str(item).strip())
    return strip_markdown(value)


def _default_comment(issue: Dict[str, Any]) -> str:
    title = strip_markdown(issue.get("title", "this issue"))
    core_value = issue.get("core_problem") or issue.get("summary") or title
    expected_value = issue.get("expected_change") or "make the requested change in a focused PR"

    core = " ".join(core_value) if isinstance(core_value, list) else strip_markdown(core_value)
    expected = " ".join(expected_value) if isinstance(expected_value, list) else strip_markdown(expected_value)
    first_step = strip_markdown(issue.get("first_step") or "review the issue carefully and inspect the relevant files before making changes")

    return (
        f"Hi! I’d like to work on this issue.\n\n"
        f"I understand that this issue is about {core[:260]}. "
        f"My first step would be to {first_step}. "
        f"After that, I’ll make a focused change for {expected[:220]}, avoid unrelated modifications, "
        f"and include a short validation note or test details in the PR so it is easier to review.\n\n"
        f"Please assign this to me if it is still available. Thank you!"
    )


def render_issue_detail(issue: Dict[str, Any]) -> None:
    """Readable issue coach panel with real card hierarchy."""
    key = issue_key(issue)
    enriched = strengthen_issue_breakdown(get_ai_breakdown(issue))

    score = int(issue.get("scout_score") or issue.get("fast_score", 0) or 0)
    labels = unique_clean(enriched.get("labels", []))
    summary = truncate(clean_ai_field(enriched.get("summary") or enriched.get("body") or enriched.get("title")), 300)
    competition = enriched.get("competition_level") or enriched.get("competition", "N/A")
    saved = is_issue_saved(issue)
    has_ai = key in st.session_state.issue_ai_breakdowns

    core_problem = enriched.get("core_problem") or "Generate AI breakdown to extract the actual core problem from the full issue body."
    expected_change = enriched.get("expected_change") or "Generate AI breakdown to understand what the maintainer expects to be changed."
    why_it_matters = enriched.get("why_it_matters") or ""
    what_to_do = enriched.get("what_to_do") or enriched.get("explanation") or "Generate AI breakdown to get a clear step-by-step explanation."
    likely_files = enriched.get("files_likely_needed") or ["Not confidently detected yet."]
    first_step = clean_ai_field(enriched.get("first_step") or "Open the issue on GitHub and read the latest maintainer comments.")
    plan = enriched.get("step_by_step_plan") or []
    risks = enriched.get("risks_or_unknowns") or []

    title = strip_markdown(enriched.get("title", "Untitled issue"))
    label_html = "".join(f'<span class="gs-chip">{_h(x)}</span>' for x in labels[:4])

    st.markdown(
        f"""
        <div class="gs-repo-card" style="padding:22px;">
            <div class="gs-card-top">
                <div>
                    <div style="display:flex; gap:6px; flex-wrap:wrap; margin-bottom:10px;">{label_html}</div>
                    <h2 style="margin:0; color:var(--ink); font-size:1.55rem; line-height:1.2; letter-spacing:-0.035em;">{_h(title)}</h2>
                </div>
                <div style="display:flex; flex-direction:column; align-items:flex-end; gap:6px;">
                    <span class="gs-chip gs-chip-score">Scout score {_h(score)}/100</span>
                    <span class="gs-chip">{_h(score_label(score))}</span>
                </div>
            </div>
            <p class="gs-desc" style="font-size:15px;">{_h(summary)}</p>
            <div class="gs-stats">
                <span><b>Type</b> · {_h(enriched.get('issue_type', 'General'))}</span>
                <span><b>Area</b> · {_h(enriched.get('ml_area', 'General'))}</span>
                <span><b>Comments</b> · {_h(enriched.get('comments', enriched.get('comments_count', 0)))}</span>
                <span><b>Competition</b> · {_h(competition)}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    action_1, action_2 = st.columns(2)
    with action_1:
        if not has_ai:
            if st.button("Understand this issue with AI", key=f"generate_ai_{safe_key(key)}", type="primary", use_container_width=True):
                email = st.session_state.get("beta_email", "")
                if not can_use_ai(email):
                    st.warning("You used your 2 beta AI generations. Please give feedback to unlock more later.")
                else:
                    used = consume_ai_use(
                        email=email,
                        action="ai_breakdown",
                        issue_url=enriched.get("html_url") or enriched.get("url", ""),
                        repo_name=get_repo_display_name(st.session_state.active_repo_detail or st.session_state.active_repo or {}),
                    )
                    if used:
                        generate_ai_breakdown_for_selected()
                        st.rerun()
        else:
            if enriched.get("local_fallback"):
                st.info("Showing a local fallback explanation. AI quota may be exhausted; try again later for deeper analysis.")
            else:
                st.success("AI breakdown generated.")

    with action_2:
        save_label = "Unsave issue" if saved else "Save issue"
        if st.button(save_label, key=f"save_selected_{safe_key(key)}", use_container_width=True):
            toggle_save_issue(issue)
            st.rerun()

    def section_card(title_text: str, items: Any, max_items: int = 4) -> None:
        bullets = as_bullet_points(items, max_items)
        if not bullets:
            return
        li = "".join(f"<li>{_h(item)}</li>" for item in bullets)
        st.markdown(
            f"""
            <div class="gs-coach-card">
                <h4>{_h(title_text)}</h4>
                <ul>{li}</ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div class="gs-section-grid">', unsafe_allow_html=True)
    section_card("Core problem", core_problem, 4)
    section_card("Expected change", expected_change, 4)
    if why_it_matters:
        section_card("Why it matters", why_it_matters, 3)
    section_card("Suggested approach", what_to_do, 5)
    section_card("Files likely involved", likely_files, 6)
    if plan:
        numbered = [f"{i}. {step}" for i, step in enumerate(as_bullet_points(plan, 6), start=1)]
        section_card("Step-by-step starting plan", numbered, 6)
    section_card("First step", first_step, 2)
    clean_risks = [
        item for item in as_bullet_points(risks, 5)
        if "not valid json" not in item.lower()
        and "api error" not in item.lower()
        and "quota" not in item.lower()
        and "rate limit" not in item.lower()
        and "429" not in item.lower()
    ]
    if clean_risks:
        section_card("Risks or unclear parts", clean_risks, 5)
    st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    if st.button(
        "Hide original GitHub issue body" if st.session_state.show_original_issue_body else "Show original GitHub issue body",
        key=f"toggle_body_{safe_key(key)}",
        use_container_width=True,
    ):
        st.session_state.show_original_issue_body = not st.session_state.show_original_issue_body
        st.rerun()

    if st.session_state.show_original_issue_body:
        st.text_area(
            "Original GitHub issue body",
            value=strip_markdown(enriched.get("body", "No issue body available.")),
            height=220,
            disabled=True,
            key=f"body_area_{safe_key(key)}",
        )

    st.markdown("### Ready-to-copy comment")
    style_key = f"comment_style_{safe_key(key)}"
    style = st.selectbox(
        "Comment style",
        ["Short and polite", "Beginner-friendly", "Confident technical", "Detailed plan"],
        key=style_key,
    )

    comment_lookup_key = f"{key}:{style}"
    existing_comment = st.session_state.generated_comments.get(comment_lookup_key)
    comment_text = existing_comment if existing_comment else _default_comment(enriched)

    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("Generate assignment comment", key=f"improve_comment_{safe_key(comment_lookup_key)}", type="primary", use_container_width=True):
            email = st.session_state.get("beta_email", "")
            if not can_use_ai(email):
                st.warning("You used your 2 beta AI generations. Please give feedback to unlock more later.")
            else:
                used = consume_ai_use(
                    email=email,
                    action="assignment_comment_from_issue_coach",
                    issue_url=enriched.get("html_url") or enriched.get("url", ""),
                    repo_name=get_repo_display_name(st.session_state.active_repo_detail or st.session_state.active_repo or {}),
                )
                if used:
                    try:
                        with st.spinner("Writing a better GitHub comment..."):
                            generated = cached_contribution_comment(enriched, style)
                        st.session_state.generated_comments[comment_lookup_key] = generated.get("comment", comment_text)
                        st.rerun()
                    except Exception as exc:
                        fallback = _default_comment(enriched)
                        st.session_state.generated_comments[comment_lookup_key] = fallback
                        st.warning(f"Comment AI fallback used: {exc}")
                        st.rerun()

    with c2:
        if st.button("Reset comment", key=f"reset_comment_{safe_key(comment_lookup_key)}", use_container_width=True):
            st.session_state.generated_comments.pop(comment_lookup_key, None)
            st.rerun()

    st.code(comment_text, language=None)

    st.link_button("Open issue on GitHub ↗", enriched.get("url", "#"), use_container_width=True)

def parse_github_issue_url(url: str) -> Optional[Dict[str, Any]]:
    match = re.search(r"github\.com/([^/]+/[^/]+)/issues/(\d+)", str(url or ""))
    if not match:
        return None
    return {"full_name": match.group(1), "issue_number": int(match.group(2))}


def generate_comment_from_issue_url() -> None:
    parsed = parse_github_issue_url(st.session_state.issue_url_input)
    if not parsed:
        st.error("Paste a valid GitHub issue URL like https://github.com/owner/repo/issues/123")
        return
    try:
        with st.spinner("Reading issue and generating comment..."):
            issue_context = cached_issue_context(parsed["full_name"], parsed["issue_number"])
            issue_context.update({
                "fast_score": 0,
                "issue_type": infer_issue_type(issue_context),
                "ml_area": infer_ml_area(issue_context),
                "required_knowledge": infer_required_knowledge(issue_context),
            })
            user_profile = {
                "skill_level": st.session_state.skill_level,
                "user_skills": st.session_state.user_skills,
                "ml_interests": st.session_state.ml_interests,
                "contribution_types": st.session_state.contribution_types,
            }
            breakdown = cached_deep_issue_analysis(issue_context, user_profile)
            breakdown.update(issue_context)
            breakdown["comment_intent"] = (
                "The user will paste this as a GitHub issue comment to ask to work on the issue and get assigned. "
                "Make it polite, specific to the issue, and not fake-confident."
            )
            generated = cached_contribution_comment(breakdown, st.session_state.issue_url_comment_style)
            st.session_state.issue_url_generated_comment = generated.get("comment", _default_comment(breakdown))
    except Exception as exc:
        st.error(f"Could not generate comment from URL: {exc}")


def render_issue_url_comment_box() -> None:
    with st.container(border=True):
        st.subheader("Comment Generator")
        st.write("Paste a GitHub issue URL and generate a clear assignment comment you can review before posting.")
        c1, c2 = st.columns([3, 1])
        with c1:
            st.text_input("GitHub issue URL", key="issue_url_input", placeholder="https://github.com/owner/repo/issues/123")
        with c2:
            st.selectbox("Comment style", ["Short and polite", "Beginner-friendly", "Confident technical", "Detailed plan"], key="issue_url_comment_style")
        if st.button("Generate assignment comment", key="generate_url_comment", type="primary", use_container_width=True):
            email = st.session_state.get("beta_email", "")

            if not can_use_ai(email):
                st.warning("You used your 2 beta AI generations. Please give feedback to unlock more later.")
            else:
                used = consume_ai_use(
                    email=email,
                    action="assignment_comment_from_url",
                    issue_url=st.session_state.get("issue_url_input", ""),
                )

                if used:
                    generate_comment_from_issue_url()
                    st.rerun()
        if st.session_state.issue_url_generated_comment:
            st.markdown("### Ready-to-copy comment")
            st.code(st.session_state.issue_url_generated_comment, language=None)


def comment_page() -> None:
    with st.container(border=True):
        st.subheader("Comment Generator")
        st.write(
            "Use this when you already found a GitHub issue and only want a strong comment to paste in the issue section."
        )
        st.caption("Goal: sound serious, specific, and polite — not like a generic AI comment.")

    render_issue_url_comment_box()


def issues_page() -> None:
    repo = st.session_state.active_repo_detail or st.session_state.active_repo

    if not repo:
        st.warning("Select a repository first.")
        return

    display_name = get_repo_display_name(repo)

    with st.container(border=True):
        left, right = st.columns([3, 2])

        with left:
            if st.button("← Back to project", key="back_to_project"):
                go("queue")

            st.subheader("Issue Coach")
            st.caption(f"{display_name} · {st.session_state.skill_level} mode · max {st.session_state.max_comments} comments")

        with right:
            st.markdown("**Flow:** Found → Understand → Confirm → Comment")
            st.progress(0.5 if st.session_state.ranked_issues else 0.25)

    render_issue_refine_panel()

    if not st.session_state.ranked_issues:
        st.info("Click **Find beginner issues** to rank open issues. Then select one and use **Understand this issue with AI**.")
        return

    left_col, right_col = st.columns([1.02, 1.18])

    with left_col:
        st.subheader("Ranked issues")
        for idx, issue in enumerate(st.session_state.ranked_issues):
            render_issue_list_item(issue, idx)

    with right_col:
        st.subheader("Understand this issue")
        selected_idx = min(st.session_state.selected_issue_idx, len(st.session_state.ranked_issues) - 1)
        render_issue_detail(st.session_state.ranked_issues[selected_idx])


# ─────────────────────────────────────────────────────────────
# SAVED PAGE
# ─────────────────────────────────────────────────────────────

def saved_page() -> None:
    st.subheader("🧭 My Path")
    st.caption("Your saved contribution path. Session-based for now; database can come later.")

    with st.container(border=True):
        st.markdown("**Roadmap progress**")
        st.write("1. Choose skills → 2. Pick repo → 3. Understand issue → 4. Comment → 5. PR")
        progress_value = 0.2
        if st.session_state.selected_repos:
            progress_value = 0.4
        if st.session_state.ranked_issues:
            progress_value = 0.6
        if st.session_state.saved_issues:
            progress_value = 0.8
        st.progress(progress_value)

    if not st.session_state.saved_issues:
        with st.container(border=True):
            st.write("No saved issues yet.")
            st.write("Save issues from the Issue Coach to build your contribution roadmap.")
        return

    for idx, issue in enumerate(st.session_state.saved_issues):
        with st.container(border=True):
            st.markdown(f"**{strip_markdown(issue.get('title', 'Untitled issue'))}**")
            st.caption(issue.get("_repo_name", "Saved repo"))
            st.write(truncate(issue.get("summary") or issue.get("body") or issue.get("title"), 180))

            c1, c2, c3 = st.columns(3)

            with c1:
                st.link_button("Open issue ↗", issue.get("url", "#"), use_container_width=True)

            with c2:
                if st.button("Mark in progress", key=f"progress_saved_{idx}_{safe_key(issue_key(issue))}", use_container_width=True):
                    st.toast("Marked as in progress for this session.")

            with c3:
                if st.button("Remove", key=f"remove_saved_{idx}_{safe_key(issue_key(issue))}", use_container_width=True):
                    st.session_state.saved_issues.pop(idx)
                    st.rerun()


# ─────────────────────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────────────────────
def _save_feedback_from_ui(rating: int, confused: str, improve: str, would_use_again: str) -> bool:
    email = st.session_state.get("beta_email", "")
    name = st.session_state.get("beta_name", "")
    payload = {
        "email": email,
        "name": name,
        "rating": int(rating),
        "confused": confused,
        "improve": improve,
        "would_use_again": would_use_again,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        try:
            from src.beta_access import get_supabase
        except Exception:
            from beta_access import get_supabase
        supabase = get_supabase()
        supabase.table("beta_feedback").insert(payload).execute()
        return True
    except Exception as exc:
        st.session_state["feedback_save_error"] = str(exc)
        return False


def _feedback_modal_inner() -> None:
    top_l, top_r = st.columns([7, 1])
    with top_l:
        st.markdown('<span class="gs-feedback-kicker">Beta feedback</span>', unsafe_allow_html=True)
        st.markdown('<div class="gs-feedback-title">Help improve GitScout</div>', unsafe_allow_html=True)
        st.markdown('<p class="gs-feedback-copy">You used your free AI generations. Tell me what felt useful, confusing, or missing.</p>', unsafe_allow_html=True)
    with top_r:
        if st.button("×", key="feedback_modal_close_x", use_container_width=True):
            st.session_state.feedback_modal_closed = True
            st.rerun()

    st.markdown('<div class="gs-star-help">How useful was GitScout?</div>', unsafe_allow_html=True)
    rating_cols = st.columns(5)
    current = int(st.session_state.get("feedback_star_rating", 4) or 4)
    for i, col in enumerate(rating_cols, start=1):
        with col:
            star = "★" if i <= current else "☆"
            if st.button(star, key=f"feedback_star_{i}", use_container_width=True):
                st.session_state.feedback_star_rating = i
                st.rerun()

    confused = st.text_area(
        "What confused you?",
        key="feedback_confused_text_modal",
        placeholder="Example: issue explanation, repo matching, filters...",
        height=95,
    )
    improve = st.text_area(
        "What should I improve first?",
        key="feedback_improve_text_modal",
        placeholder="Tell me the one thing that would make this more useful.",
        height=95,
    )
    would_use = st.radio(
        "Would you use this again?",
        ["Yes", "Maybe", "Not sure yet", "No"],
        key="feedback_would_use_choice_modal",
        horizontal=True,
    )

    c1, c2 = st.columns([2, 1])
    with c1:
        if st.button("Submit feedback", key="feedback_submit_modal", type="primary", use_container_width=True):
            saved = _save_feedback_from_ui(
                st.session_state.get("feedback_star_rating", 4),
                confused,
                improve,
                would_use,
            )
            st.session_state.feedback_submitted = True
            st.session_state.feedback_modal_closed = True
            st.toast("Feedback submitted. Thank you!" if saved else "Feedback saved for this session.")
            st.rerun()
    with c2:
        if st.button("Maybe later", key="feedback_maybe_later_modal", use_container_width=True):
            st.session_state.feedback_modal_closed = True
            st.rerun()


def render_feedback_modal() -> None:
    email = st.session_state.get("beta_email", "")
    if not email:
        return
    if st.session_state.get("feedback_submitted") or st.session_state.get("feedback_modal_closed"):
        return
    try:
        exhausted = not can_use_ai(email)
    except Exception:
        exhausted = False
    if not exhausted:
        return

    if hasattr(st, "dialog"):
        @st.dialog("Quick feedback")
        def _dialog():
            _feedback_modal_inner()
        _dialog()
    else:
        with st.container(border=True):
            _feedback_modal_inner()


def create_app() -> None:
    configure_page()
    init_session_state()
    inject_css()

    if not render_beta_gate():
        return

    # Do not call the old inline feedback/status form here. The new feedback
    # flow is a modal that appears only after the beta AI limit is exhausted.
    render_nav()

    page = st.session_state.page

    if page == "discover":
        discover_page()
    elif page == "queue":
        queue_page()
    elif page == "issues":
        issues_page()
    elif page == "comment":
        comment_page()
    elif page == "saved":
        saved_page()
    else:
        discover_page()

    render_feedback_modal()