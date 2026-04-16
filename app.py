"""
EventForge AI — Streamlit Web UI  (no-sidebar, top-bar layout)
Run with: streamlit run app.py
"""

import streamlit as st
import json
import os
import time
from dotenv import load_dotenv
load_dotenv()

# Auto-build ChromaDB on first launch (Streamlit Cloud has no persistent disk)
CHROMA_DIR = "./chroma_db"
if not os.path.exists(CHROMA_DIR) or len(os.listdir(CHROMA_DIR)) == 0:
    import streamlit as st
    with st.spinner("⚙️ First launch — building knowledge base (~30 sec)..."):
        import sys
        sys.path.insert(0, "./rag")       # adjust if ingest.py is in a subfolder
        from ingest import main as ingest_main
        ingest_main(data_dir="./data")
    st.success("✅ Knowledge base ready!")
    st.rerun()

from validator import validate_and_normalise, ValidationError, print_supported_options
from config import SUPPORTED_SPORTS, SUPPORTED_GEOGRAPHIES
from orchestrator import run_pipeline

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="EventForge AI",
    page_icon="🏟️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Instrument+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Reset & Base ─────────────────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] { font-family: 'Instrument Sans', sans-serif; }

:root {
    --bg:         #09090B;
    --surface:    #111113;
    --surface2:   #18181C;
    --surface3:   #1F1F25;
    --border:     #1E1E26;
    --border2:    #2A2A36;
    --text:       #EAEAF2;
    --text2:      #C8C8D8;
    --muted:      #52526A;
    --muted2:     #7A7A96;
    --amber:      #F5A623;
    --amber-dim:  #2D1E04;
    --amber-mid:  #6B480D;
    --amber-glow: rgba(245,166,35,0.08);
    --blue:       #4A9EFF;
    --blue-dim:   #0A1829;
    --green:      #34D399;
    --green-dim:  #062318;
    --red:        #F87171;
    --purple:     #A78BFA;
    --radius:     10px;
    --radius-sm:  6px;
}

/* ── App Shell ────────────────────────────────────────────────────────────── */
.stApp { background: var(--bg); color: var(--text); }

/* Hide sidebar toggle & streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="collapsedControl"] { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }

/* Full-width main block */
.block-container {
    max-width: 1320px !important;
    padding: 0 2rem 3rem !important;
    margin: 0 auto !important;
}

/* ── Top Nav ──────────────────────────────────────────────────────────────── */
.topnav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 0 1rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 2.4rem;
}
.topnav-logo {
    display: flex;
    align-items: baseline;
    gap: 0.4rem;
}
.topnav-logo-text {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 3.1rem;
    letter-spacing: 0.08em;
    color: var(--text);
    line-height: 1;
}
.topnav-logo-text span { color: var(--amber); }
.topnav-tag {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--amber);
    background: var(--amber-dim);
    border: 1px solid var(--amber-mid);
    padding: 3px 10px;
    border-radius: 3px;
    margin-left: 8px;
}
.topnav-right {
    display: flex;
    align-items: center;
    gap: 1.4rem;
}
.topnav-stat {
    text-align: right;
}
.topnav-stat-val {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.5rem;
    letter-spacing: 0.04em;
    color: var(--text);
    line-height: 1;
}
.topnav-stat-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.55rem;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    color: var(--text2);
    margin-top: 2px;
}
.topnav-divider {
    width: 1px;
    height: 36px;
    background: var(--border2);
}

/* ── Hero ─────────────────────────────────────────────────────────────────── */
.hero-strip {
    display: grid;
    grid-template-columns: 1fr auto;
    align-items: start;
    gap: 2rem;
    margin-bottom: 2.8rem;
}
.hero-eyebrow {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1rem;
    font-weight: 500;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: var(--amber);
    margin-bottom: 0.6rem;
    display: flex;
    align-items: center;
    gap: 10px;
}
.hero-eyebrow::before {
    content: '';
    display: inline-block;
    width: 28px;
    height: 1.5px;
    background: var(--amber);
}
.hero-strip h1.hero-title {
    font-size: 7rem !important;
    font-family: 'Bebas Neue', sans-serif;
    font-weight: 400;
    letter-spacing: 0.03em;
    color: var(--text);
    margin: 0;
    line-height: 0.88;
}
.hero-title span { color: var(--amber); }
.hero-sub {
    font-size: 1rem;
    color: var(--text2);
    margin-top: 1rem;
    line-height: 1.65;
    max-width: 520px;
}
.hero-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 1.2rem;
}
.hero-pill {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--muted2);
    background: var(--surface2);
    border: 1px solid var(--border2);
    padding: 4px 12px;
    border-radius: 3px;
}

/* ── Config Panel ─────────────────────────────────────────────────────────── */
.config-panel {
    background: var(--surface);
    border: 1px solid var(--border2);
    border-radius: var(--radius);
    padding: 1rem 1.2rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.config-panel::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--amber), transparent 60%);
}
.config-panel-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.2rem;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    color: var(--muted2);
    margin-bottom: 1.6rem;
    display: flex;
    align-items: center;
    gap: 10px;
}
.config-panel-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
}

/* ── Form field labels ────────────────────────────────────────────────────── */
label, .stTextInput label, .stSelectbox label,
.stNumberInput label, .stSlider label, .stTextArea label {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.62rem !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.14em !important;
    color: var(--muted2) !important;
    margin-bottom: 4px !important;
}

/* ── Inputs ───────────────────────────────────────────────────────────────── */
input, textarea, select,
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea,
[data-baseweb="select"] div {
    background: var(--surface2) !important;
    border: 1px solid var(--border2) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text) !important;
    font-family: 'Instrument Sans', sans-serif !important;
    font-size: 0.9rem !important;
}
input:focus, textarea:focus,
[data-baseweb="input"] input:focus {
    border-color: var(--amber) !important;
    box-shadow: 0 0 0 3px rgba(245,166,35,0.1) !important;
    outline: none !important;
}

/* Slider track */
.stSlider [data-baseweb="slider"] [role="progressbar"] { background: var(--amber) !important; }
.stSlider [data-baseweb="slider"] [role="slider"]      { background: var(--amber) !important; border-color: var(--amber) !important; }

/* Selectbox arrow */
[data-baseweb="select"] svg { color: var(--muted2) !important; }

/* ── Primary Button ───────────────────────────────────────────────────────── */
.stButton > button {
    background: var(--amber) !important;
    color: #09090B !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 1.5rem !important;
    font-weight : 700 !important;
    letter-spacing: 0.14em !important;
    padding: 0.75rem 2.4rem !important;
    width: 100% !important;
    cursor: pointer !important;
    transition: opacity 0.18s, transform 0.14s !important;
}
.stButton > button:hover  { opacity: 0.87 !important; transform: translateY(-1px) !important; }
.stButton > button:active { transform: translateY(0) !important; }

/* ── Download Buttons ─────────────────────────────────────────────────────── */
[data-testid="stDownloadButton"] button {
    background: var(--surface2) !important;
    border: 1px solid var(--border2) !important;
    color: var(--text2) !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'Instrument Sans', sans-serif !important;
    font-size: 1rem !important;
    font-weight: 500 !important;
    transition: border-color 0.18s, color 0.18s !important;
}
[data-testid="stDownloadButton"] button:hover {
    border-color: var(--amber) !important;
    color: var(--amber) !important;
}

/* ── Tabs ─────────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid var(--border) !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    color: var(--muted) !important;
    font-family: 'Instrument Sans', sans-serif !important;
    font-size: 0.83rem !important;
    font-weight: 500 !important;
    padding: 0.65rem 1.2rem !important;
    margin-bottom: -1px !important;
    transition: color 0.18s, border-color 0.18s !important;
    letter-spacing: 0.01em !important;
}
.stTabs [aria-selected="true"]   { color: var(--text) !important; border-bottom-color: var(--amber) !important; }
.stTabs [data-baseweb="tab"]:hover { color: var(--muted2) !important; }
.stTabs [data-baseweb="tab-panel"] { padding-top: 1.6rem !important; }

/* ── Metrics row ──────────────────────────────────────────────────────────── */
.metric-row {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 1px;
    background: var(--border);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    overflow: hidden;
    margin-bottom: 2rem;
}
.metric-box {
    background: var(--surface);
    padding: 1.3rem 1.5rem;
    position: relative;
    transition: background 0.18s;
}
.metric-box:hover { background: var(--surface2); }
.metric-box::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 2px;
    background: transparent;
    transition: background 0.2s;
}
.metric-box:hover::after { background: var(--amber); }
.metric-val {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.3rem;
    letter-spacing: 0.02em;
    color: var(--text);
    line-height: 1;
}
.metric-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    color: var(--text2);
    text-transform: uppercase;
    letter-spacing: 0.14em;
    margin-top: 5px;
}
.metric-delta { font-size: 0.7rem; color: var(--green); margin-top: 3px; font-weight: 500; }

/* ── Section label ────────────────────────────────────────────────────────── */
.sec-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.18em;
    color: var(--text2);
    margin: 1.6rem 0 0.9rem;
    display: flex;
    align-items: center;
    gap: 12px;
}
.sec-label::after { content: ''; flex: 1; height: 1px; background: var(--border); }

/* ── Info cards (landing) ─────────────────────────────────────────────────── */
.info-cards-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1px;
    background: var(--border);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    overflow: hidden;
    margin-top: 0.5rem;
}
.info-card { background: var(--surface); padding: 1.6rem 1.8rem; }
.info-card-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1rem;
    text-transform: uppercase;
    letter-spacing: 0.18em;
    color: var(--amber);
    margin-bottom: 0.8rem;
}
.info-card-body { font-size: 0.9rem; color: var(--text2); line-height: 1.75; }

/* ── Sponsor Card ─────────────────────────────────────────────────────────── */
.sponsor-card {
    display: grid;
    grid-template-columns: 1fr auto;
    align-items: center;
    gap: 1rem;
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--border2);
    border-radius: var(--radius-sm);
    padding: 1rem 1.3rem;
    margin-bottom: 0.55rem;
    transition: border-left-color 0.2s, background 0.18s;
}
.sponsor-card:hover { border-left-color: var(--amber); background: var(--surface2); }
.sponsor-name   { font-size: 1.2rem; font-weight: 700; color: var(--text); }
.sponsor-meta   { font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: var(--muted); margin-top: 3px; letter-spacing: 0.05em; }
.sponsor-reason { font-size: 1rem; color: var(--text2); margin-top: 6px; line-height: 1.55; }
.priority-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    font-weight: 500;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 4px 11px;
    border-radius: 3px;
    white-space: nowrap;
}
.priority-high   { background: rgba(52,211,153,0.1);  color: var(--green);  border: 1px solid rgba(52,211,153,0.22); }
.priority-medium { background: rgba(245,166,35,0.1);  color: var(--amber);  border: 1px solid rgba(245,166,35,0.22); }
.priority-low    { background: rgba(248,113,113,0.1); color: var(--red);    border: 1px solid rgba(248,113,113,0.22); }

/* ── Speaker Grid ─────────────────────────────────────────────────────────── */
.speaker-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(175px, 1fr)); gap: 10px; }
.speaker-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 1.3rem 1rem;
    text-align: center;
    transition: border-color 0.2s, transform 0.15s, background 0.15s;
}
.speaker-card:hover { border-color: var(--amber-mid); background: var(--surface2); transform: translateY(-2px); }
.speaker-avatar {
    width: 54px;
    height: 54px;
    border-radius: 50%;
    margin: 0 auto 12px;

    display: flex;
    align-items: center;
    justify-content: center;

    font-size: 1.2rem;
    font-weight: 700;
    letter-spacing: 0.05em;

    color: #09090B;

    background: linear-gradient(135deg, #F5A623, #FFD166);
    border: 2px solid rgba(245,166,35,0.4);

    box-shadow: 0 0 12px rgba(245,166,35,0.25);
}
.speaker-name  { font-size: 1rem; font-weight: 600; color: var(--text); }
.speaker-sport { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: var(--text2); margin-top: 4px; letter-spacing: 0.05em; }
.speaker-tag   {
    display: inline-block;
    font-size: 0.62rem;
    color: var(--amber);
    background: var(--amber-dim);
    border: 1px solid var(--amber-mid);
    padding: 3px 9px;
    border-radius: 3px;
    margin-top: 9px;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.05em;
}

/* ── Venue Cards ──────────────────────────────────────────────────────────── */
.venue-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 1.2rem 1.5rem;
    margin-bottom: 0.7rem;
    display: grid;
    grid-template-columns: 1fr auto;
    align-items: center;
    gap: 1rem;
    transition: background 0.18s;
}
.venue-card:hover { border-left-color: var(--amber); background: var(--surface2); }

.venue-name { font-family: 'Bebas Neue', sans-serif; font-size: 1.55rem; letter-spacing: 0.04em; color: var(--text); }

.venue-meta   { font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: var(--text2); margin-top: 4px; letter-spacing: 0.05em; line-height: 1.85; }
.venue-reason { font-size: 0.9rem; color: var(--muted); margin-top: 8px; line-height: 1.55; }
.venue-rank   { font-family: 'Bebas Neue', sans-serif; font-size: 3.2rem; letter-spacing: 0.02em; line-height: 1; color: var(--border2); }
.venue-card.top .venue-rank { color: var(--amber-mid); }

/* ── Pricing Grid ─────────────────────────────────────────────────────────── */
.pricing-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(155px, 1fr)); gap: 10px; margin-bottom: 1.6rem; }
.pricing-tier {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 1.3rem 1rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: background 0.18s;
}
.pricing-tier:hover { background: var(--surface2); }
.pricing-tier::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; background: var(--border2); }
.pricing-tier:first-child::before { background: var(--amber); }
.tier-name  { font-family: 'JetBrains Mono', monospace; font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.14em; color: var(--muted); margin-bottom: 9px; }
.tier-price { font-family: 'Bebas Neue', sans-serif; font-size: 2.1rem; letter-spacing: 0.02em; color: var(--text); line-height: 1; }
.tier-sales { font-size: 0.9rem; color: var(--muted); margin-top: 5px; }
.tier-rev   { font-size: 0.8rem; color: var(--green); margin-top: 5px; font-weight: 500; }

/* ── Exhibitor Cards ──────────────────────────────────────────────────────── */
.exhibitor-card {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 0.9rem 1.3rem;
    margin-bottom: 0.55rem;
    transition: background 0.18s, border-color 0.2s;
}
.exhibitor-card:hover { background: var(--surface2); border-color: var(--border2); }
.exhibitor-name { font-weight: 600; color: var(--text); font-size: 0.92rem; }
.exhibitor-meta { font-family: 'JetBrains Mono', monospace; font-size: 0.63rem; color: var(--muted); margin-top: 3px; letter-spacing: 0.05em; }
.exhibitor-fit  { font-size: 0.81rem; color: var(--muted2); margin-top: 5px; line-height: 1.45; }
.booth-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    padding: 4px 10px;
    border-radius: 3px;
    background: var(--blue-dim);
    color: var(--blue);
    border: 1px solid rgba(74,158,255,0.18);
    white-space: nowrap;
    letter-spacing: 0.06em;
}

/* ── GTM ──────────────────────────────────────────────────────────────────── */
.phase-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 1.2rem 1.4rem 1.2rem 2.6rem;
    margin-bottom: 0.75rem;
    position: relative;
    transition: background 0.18s;
}
.phase-card:hover { background: var(--surface2); }
.phase-card::before {
    content: attr(data-phase);
    position: absolute;
    left: 1rem;
    top: 1.2rem;
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1rem;
    letter-spacing: 0.08em;
    color: var(--amber);
}
.phase-title { font-family: 'JetBrains Mono', monospace; font-size: 1.2rem; text-transform: uppercase; letter-spacing: 0.14em; color: var(--text); margin-bottom: 6px; }
.phase-body  { font-size: 0.89rem; color: var(--muted2); line-height: 1.65; }
.channel-pill {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.2rem;
    padding: 4px 10px;
    border-radius: 3px;
    background: var(--surface2);
    border: 1px solid var(--border2);
    color: var(--muted2);
    margin: 3px 3px 3px 0;
    letter-spacing: 0.06em;
}
.community-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 0.95rem 1.3rem; margin-bottom: 0.55rem; transition: background 0.18s; }
.community-card:hover { background: var(--surface2); }
.community-head { display: flex; justify-content: space-between; align-items: baseline; }
.community-name  { font-weight: 600; color: var(--text); font-size: 1rem; }
.community-niche { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: var(--amber); letter-spacing: 0.06em; }
.community-meta  { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: var(--muted); margin-top: 2px; }
.community-msg   { font-size: 0.81rem; color: var(--muted2); margin-top: 7px; font-style: italic; line-height: 1.55; }

/* ── Schedule ─────────────────────────────────────────────────────────────── */
.schedule-wrap { position: relative; padding-left: 1.5rem; }
.schedule-wrap::before { content: ''; position: absolute; left: 7px; top: 8px; bottom: 8px; width: 1px; background: var(--border); }
.sched-item {
    position: relative;
    display: grid;
    grid-template-columns: 130px 1fr auto;
    gap: 20px;
    padding: 10px 0 10px 1rem;
    align-items: start;
    border-radius: 4px;
    transition: background 0.15s;
}
.sched-item:hover { background: var(--surface2); }
.sched-item::before {
    content: '';
    position: absolute;
    left: -1.5rem;
    top: 16px;
    width: 9px; height: 9px;
    border-radius: 50%;
    background: var(--border2);
    border: 2px solid var(--bg);
    transition: background 0.18s;
}
.sched-item:hover::before { background: var(--amber); }
.sched-time  { font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: var(--muted); padding-top: 2px; white-space: nowrap; }
.sched-title { font-size: 0.93rem; color: var(--text); font-weight: 500; }
.sched-who   { font-family: 'JetBrains Mono', monospace; font-size: 0.73rem; color: var(--muted); margin-top: 3px; letter-spacing: 0.04em; }
.sched-type  { font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; padding: 3px 8px; border-radius: 3px; background: var(--surface2); color: var(--muted2); border: 1px solid var(--border2); letter-spacing: 0.06em; white-space: nowrap; }

/* ── Metric container overrides ───────────────────────────────────────────── */
[data-testid="metric-container"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    padding: 1rem 1.3rem !important;
}
[data-testid="metric-container"] label {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.7rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.12em !important;
    color: var(--muted) !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 1.85rem !important;
    letter-spacing: 0.02em !important;
    color: var(--text) !important;
}

/* ── Progress / Status ────────────────────────────────────────────────────── */
.stProgress > div > div > div { background: var(--amber) !important; }
[data-testid="stStatusWidget"] { border: 1px solid var(--border) !important; border-radius: var(--radius-sm) !important; background: var(--surface) !important; }

/* ── Misc ─────────────────────────────────────────────────────────────────── */
.stCaption { color: var(--muted) !important; font-size: 0.78rem !important; }
hr { border-color: var(--border) !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--muted); }
</style>
""", unsafe_allow_html=True)

# ── Top Nav ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="topnav">
  <div class="topnav-logo">
    <div class="topnav-logo-text">Event<span>Forge</span> AI</div>
    <div class="topnav-tag">v2.0</div>
  </div>
  <div class="topnav-right">
    <div class="topnav-stat">
      <div class="topnav-stat-val">1,300+</div>
      <div class="topnav-stat-label">Events Indexed</div>
    </div>
    <div class="topnav-divider"></div>
    <div class="topnav-stat">
      <div class="topnav-stat-val">736</div>
      <div class="topnav-stat-label">Speakers</div>
    </div>
    <div class="topnav-divider"></div>
    <div class="topnav-stat">
      <div class="topnav-stat-val">8</div>
      <div class="topnav-stat-label">Agents Active</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Hero ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-strip">
  <div>
    <div class="hero-eyebrow">Multi-agent event intelligence</div>
    <h1 class="hero-title">Plan your<br><span>next event.</span></h1>
    <div class="hero-sub">
      Configure your event below and let eight AI agents run in parallel —
      sponsors, speakers, venues, pricing, exhibitors, GTM strategy, ops, and synthesis.
      Every recommendation is grounded in real data, not generated from thin air.
    </div>
    <div class="hero-pills">
      <span class="hero-pill">RAG-grounded</span>
      <span class="hero-pill">LangGraph orchestration</span>
      <span class="hero-pill">692 real venues</span>
      <span class="hero-pill">102 known sponsors</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Config Panel ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="config-panel">
  <div class="config-panel-title">Event Configuration</div>
</div>
""", unsafe_allow_html=True)

# Two-column form layout
col_a, col_b, col_c = st.columns([2, 2, 1])

with col_a:
    event_name = st.text_input(
        "Event Name",
        placeholder="e.g. IPL Fan Fest 2026",
        value="IPL Fan Fest 2026"
    )
    sport = st.selectbox(
        "Sport / Category",
        options=sorted(SUPPORTED_SPORTS),
        index=sorted(SUPPORTED_SPORTS).index("cricket"),
        help="Select a sport your data covers well"
    )
    geography = st.selectbox(
        "Geography",
        options=SUPPORTED_GEOGRAPHIES,
        index=SUPPORTED_GEOGRAPHIES.index("India"),
    )

with col_b:
    audience = st.slider(
        "Target Audience Size",
        min_value=500,
        max_value=100_000,
        value=50_000,
        step=500,
        format="%d"
    )
    budget = st.number_input(
        "Budget (USD)",
        min_value=0,
        max_value=10_000_000,
        value=500_000,
        step=50_000,
        format="%d"
    )
    notes = st.text_area(
        "Additional Notes",
        placeholder="Focus on youth engagement, outdoor venue preferred...",
        height=82
    )

with col_c:
    st.markdown("<div style='height: 1.6rem'></div>", unsafe_allow_html=True)
    run_btn = st.button("Generate Plan", use_container_width=True)

st.markdown("<div style='margin-bottom: 2rem'></div>", unsafe_allow_html=True)

# ── Landing state ──────────────────────────────────────────────────────────────
if "state" not in st.session_state and not run_btn:
    st.markdown("""
    <div class="info-cards-row">
      <div class="info-card">
        <div class="info-card-label">01 · How it works</div>
        <div class="info-card-body">
          Configure your event above, then click <strong style="color:#EAEAF2">Generate Plan</strong>.
          Eight AI agents run in parallel — sponsors, speakers, venues, pricing, exhibitors, GTM, ops, and synthesiser.
        </div>
      </div>
      <div class="info-card">
        <div class="info-card-label">02 · Data-grounded</div>
        <div class="info-card-body">
          Every recommendation is retrieved from a real dataset of 1,300+ events, 736 speakers,
          692 venues, and 102 known sponsors — not hallucinated from training data.
        </div>
      </div>
      <div class="info-card">
        <div class="info-card-label">03 · Agent roster</div>
        <div class="info-card-body">
          Sponsor · Speaker · Exhibitor · Venue · Pricing · Community · Ops · Synthesiser —
          all coordinated by a LangGraph orchestrator with shared state.
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ── Run pipeline ───────────────────────────────────────────────────────────────
if run_btn:
    try:
        clean = validate_and_normalise(sport, geography, audience, float(budget) if budget else None)
    except ValidationError as e:
        st.error(str(e))
        st.stop()

    progress_bar = st.progress(0)
    status       = st.status("Running agents...", expanded=True)

    agent_steps = [
        (15,  "🎯  Sponsor Agent — finding relevant sponsors..."),
        (30,  "🎤  Speaker Agent — discovering athletes & experts..."),
        (45,  "🏢  Exhibitor Agent — identifying exhibitors..."),
        (60,  "🏟️   Venue Agent — matching venues..."),
        (72,  "🎟️   Pricing Agent — modelling ticket tiers..."),
        (84,  "📣  Community Agent — building GTM strategy..."),
        (93,  "📋  Ops Agent — building event agenda..."),
        (100, "✨  Synthesiser — compiling final plan..."),
    ]

    with status:
        for pct, msg in agent_steps[:-1]:
            st.write(msg)
            progress_bar.progress(pct)
            time.sleep(0.4)

        st.write(agent_steps[-1][1])
        progress_bar.progress(99)

        final_name = event_name or f"{sport.title()} Event {geography} 2026"
        state = run_pipeline(
            event_category       = clean["event_category"],
            geography            = clean["geography"],
            target_audience_size = clean["target_audience_size"],
            budget_usd           = clean.get("budget_usd"),
            event_name           = final_name,
            additional_notes     = notes or None,
        )
        progress_bar.progress(100)

    st.session_state["state"]      = state
    st.session_state["event_name"] = final_name
    status.update(label="✅ Plan generated!", state="complete")


# ── Helper ─────────────────────────────────────────────────────────────────────
def extract_report_section(final_plan: str, keywords: list[str]) -> str:
    if not final_plan:
        return ""
    lines = final_plan.splitlines()
    start_idx = None
    heading_level = 0
    for i, line in enumerate(lines):
        stripped = line.lstrip("#").strip().lower()
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            if any(kw.lower() in stripped for kw in keywords):
                start_idx = i
                heading_level = level
                break
    if start_idx is None:
        return ""
    section_lines = [lines[start_idx]]
    for line in lines[start_idx + 1:]:
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            if level <= heading_level:
                break
        section_lines.append(line)
    return "\n".join(section_lines).strip()


# ── Render results ─────────────────────────────────────────────────────────────
if "state" in st.session_state:
    state      = st.session_state["state"]
    event_name = st.session_state.get("event_name", "Your Event")

    sponsors    = state.get("sponsors")    or []
    speakers    = state.get("speakers")    or []
    venues      = state.get("venues")      or []
    pricing     = state.get("pricing")     or {}
    exhibitors  = state.get("exhibitors")  or []
    communities = state.get("communities") or {}
    ops_plan    = state.get("ops_plan")    or {}
    final_plan  = state.get("final_plan")  or ""

    # ── Event title row ───────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="display:flex;align-items:baseline;gap:1rem;margin-bottom:1.6rem">
      <div style="font-family:'Bebas Neue',sans-serif;font-size:2rem;letter-spacing:0.04em;color:var(--text)">{event_name}</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:0.62rem;text-transform:uppercase;letter-spacing:0.14em;color:var(--muted)">Generated plan</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Metrics ───────────────────────────────────────────────────────────────
    # ── Normalize pricing_tiers defensively on the frontend too ──────────────
    # The LLM may return a dict instead of list, or use different key names.
    _TIER_ALIASES = {
        "tier_name":       ["tier_name", "name", "tier", "ticket_type", "category",
                            "level", "type", "label", "ticket_tier", "section"],
        "price_usd":       ["price_usd", "price", "cost", "amount", "ticket_price",
                            "price_per_ticket", "rate", "value", "usd", "fee"],
        "expected_sales":  ["expected_sales", "sales", "quantity", "tickets",
                            "expected_tickets", "units", "capacity", "count"],
        "revenue_est_usd": ["revenue_est_usd", "revenue", "revenue_est",
                            "estimated_revenue", "rev", "income"],
    }
    def _norm_tier(t):
        low = {k.lower(): v for k, v in t.items()}
        r = {}
        for canon, aliases in _TIER_ALIASES.items():
            for a in aliases:
                if a in low:
                    r[canon] = low[a]
                    break
        if "tier_name" not in r:
            r["tier_name"] = next(iter(t.values()), "—")
        return r

    _raw_tiers = pricing.get("pricing_tiers", [])
    if isinstance(_raw_tiers, dict):
        _tiers_list = []
        for _k, _v in _raw_tiers.items():
            if isinstance(_v, dict):
                _v.setdefault("tier_name", _k)
                _tiers_list.append(_norm_tier(_v))
            else:
                _tiers_list.append({"tier_name": _k, "price_usd": _v})
        tiers = _tiers_list
    elif isinstance(_raw_tiers, list):
        tiers = [_norm_tier(t) if isinstance(t, dict) else t for t in _raw_tiers]
    else:
        tiers = []
    total_rev = pricing.get("total_revenue_projection_usd", 0)

    st.markdown(f"""
    <div class="metric-row">
      <div class="metric-box">
        <div class="metric-val">{len(sponsors)}</div>
        <div class="metric-label">Sponsors</div>
      </div>
      <div class="metric-box">
        <div class="metric-val">{len(speakers)}</div>
        <div class="metric-label">Speakers</div>
      </div>
      <div class="metric-box">
        <div class="metric-val">{len(venues)}</div>
        <div class="metric-label">Venues</div>
      </div>
      <div class="metric-box">
        <div class="metric-val">{len(exhibitors)}</div>
        <div class="metric-label">Exhibitors</div>
      </div>
      <div class="metric-box">
        <div class="metric-val">${total_rev:,.0f}</div>
        <div class="metric-label">Rev Projection</div>
        <div class="metric-delta">↑ Projected</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tabs = st.tabs(["Sponsors", "Speakers", "Venues", "Pricing",
                    "Exhibitors", "GTM", "Schedule", "Full Report"])

    # ── SPONSORS ──────────────────────────────────────────────────────────────
    with tabs[0]:
        if sponsors:
            for s in sponsors:
                priority = s.get("priority", "Medium")
                badge_cls = {"High": "priority-high", "Medium": "priority-medium", "Low": "priority-low"}.get(priority, "priority-medium")
                st.markdown(f"""
                <div class="sponsor-card">
                  <div>
                    <div class="sponsor-name">{s.get('sponsor_name','—')}</div>
                    <div class="sponsor-meta">{s.get('sponsor_type','—')} &nbsp;·&nbsp; {s.get('estimated_deal_range','Negotiable')}</div>
                    <div class="sponsor-reason">{s.get('relevance_reason','')}</div>
                  </div>
                  <span class="priority-badge {badge_cls}">{priority}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            section = extract_report_section(final_plan, ["sponsor"])
            if section:
                st.info("No structured sponsor data returned — showing report excerpt.")
                st.markdown(section)
            else:
                st.info("No sponsor data returned.")

    # ── SPEAKERS ──────────────────────────────────────────────────────────────
    with tabs[1]:
        if speakers:
            emojis = ["🎾","🏏","⚽","🏎️","🥊","🏀","🏒","⚾","🥋","⛳"]
            cards_html = '<div class="speaker-grid">'
            for i, s in enumerate(speakers):
                name = s.get('name', 'TBD')
                initials = "".join([word[0] for word in name.split()[:2]]).upper()

                cards_html += f"""
                <div class="speaker-card">
                  <div class="speaker-avatar">{initials}</div>
                  <div class="speaker-name">{s.get('name','TBD')}</div>
                  <div class="speaker-sport">{s.get('sport_or_domain','')}</div>
                  <div><span class="speaker-tag">{s.get('suggested_session_type','')}</span></div>
                </div>"""
            cards_html += '</div>'
            st.markdown(cards_html, unsafe_allow_html=True)
        else:
            section = extract_report_section(final_plan, ["speaker"])
            if section:
                st.info("No structured speaker data returned — showing report excerpt.")
                st.markdown(section)
            else:
                st.info("No speaker data returned.")

    # ── VENUES ────────────────────────────────────────────────────────────────
    with tabs[2]:
        if venues:
            for i, v in enumerate(venues):
                card_cls = "venue-card top" if i == 0 else "venue-card"
                st.markdown(f"""
                <div class="{card_cls}">
                  <div>
                    <div class="venue-name">{v.get('venue_name','—')}</div>
                    <div class="venue-meta">
                      📍 {v.get('city','—')}, {v.get('country','—')}<br>
                      👥 Capacity: {v.get('capacity','—')}<br>
                      💰 {v.get('estimated_rental_range_usd','Contact venue')}
                    </div>
                    <div class="venue-reason">{v.get('recommendation_reason','')}</div>
                  </div>
                  <div class="venue-rank">#{i+1}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            section = extract_report_section(final_plan, ["venue"])
            if section:
                st.info("No structured venue data returned — showing report excerpt.")
                st.markdown(section)
            else:
                st.info("No venue data returned.")

    # ── PRICING ───────────────────────────────────────────────────────────────
    # ── PRICING ───────────────────────────────────────────────────────────────
    with tabs[3]:
        if tiers:
            tiers_html = '<div class="pricing-grid">'

            for t in tiers:
            # ── CASE 1: Proper dict ─────────────────────
                if isinstance(t, dict):
                    name  = t.get('tier_name', '—')
                    price = t.get('price_usd')
                    sales = t.get('expected_sales')
                    rev   = t.get('revenue_est_usd')

                    price_display = f"${price:,}" if isinstance(price, (int, float)) else "—"
                    sales_display = f"{sales:,} tickets" if isinstance(sales, (int, float)) else ""
                    rev_display   = f"+${rev:,.0f}" if isinstance(rev, (int, float)) else ""

            # ── CASE 2: String like "VIP - $100" ───────
                elif isinstance(t, str):
                    name = t

                    import re
                    match = re.search(r"\$?(\d+)", t)
                    if match:
                        price_display = f"${int(match.group(1)):,}"
                    else:
                        price_display = "—"

                    sales_display = ""
                    rev_display   = ""

            # ── CASE 3: Unknown format ────────────────
                else:
                    name = "—"
                    price_display = "—"
                    sales_display = ""
                    rev_display   = ""

                tiers_html += f"""
                <div class="pricing-tier">
                  <div class="tier-name">{name}</div>
                  <div class="tier-price">{price_display}</div>
                  <div class="tier-sales">{sales_display}</div>
                  <div class="tier-rev">{rev_display}</div>
                </div>"""

            tiers_html += '</div>'
            st.markdown(tiers_html, unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Attendance", f"{pricing.get('total_expected_attendance',0):,}")
            col2.metric("Revenue Projection", f"${pricing.get('total_revenue_projection_usd',0):,.0f}")
            col3.metric("Break-even Attendance", f"{pricing.get('break_even_attendance',0):,}")

            conf = pricing.get("confidence", "—")
            st.markdown(f"<div class='sec-label'>Model Confidence — {conf}</div>", unsafe_allow_html=True)
            st.caption(pricing.get("reasoning",""))

        else:
            section = extract_report_section(final_plan, ["pricing", "ticket", "price"])
            if section:
                st.info("No structured pricing data returned — showing report excerpt.")
                st.markdown(section)
            else:
                st.info("No pricing data returned.")

        # Debug expander — remove after confirmed working
        with st.expander("🔍 Raw pricing data (debug)", expanded=False):
            st.json(pricing)

    # ── EXHIBITORS ────────────────────────────────────────────────────────────
    with tabs[4]:
        if exhibitors:
            for e in exhibitors:
                st.markdown(f"""
                <div class="exhibitor-card">
                  <div>
                    <div class="exhibitor-name">{e.get('company_name','—')}</div>
                    <div class="exhibitor-meta">{e.get('category','—')} &nbsp;·&nbsp; {e.get('sub_category','—')} &nbsp;·&nbsp; {e.get('geography','—')}</div>
                    <div class="exhibitor-fit">{e.get('why_good_fit','')}</div>
                  </div>
                  <span class="booth-badge">{e.get('booth_tier','Standard')}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            section = extract_report_section(final_plan, ["exhibitor"])
            if section:
                st.info("No structured exhibitor data returned — showing report excerpt.")
                st.markdown(section)
            else:
                st.info("No exhibitor data returned.")

    # ── GTM ───────────────────────────────────────────────────────────────────
    with tabs[5]:
        gtm          = communities.get("gtm_strategy", {})
        target_comms = communities.get("target_communities", [])

        if gtm:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div class="phase-card" data-phase="01">
                  <div class="phase-title">Pre-Event — 8+ weeks out</div>
                  <div class="phase-body">{gtm.get('phase_1_pre_event','—')}</div>
                </div>
                <div class="phase-card" data-phase="02">
                  <div class="phase-title">Launch — 4–8 weeks out</div>
                  <div class="phase-body">{gtm.get('phase_2_launch','—')}</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class="phase-card" data-phase="03">
                  <div class="phase-title">Final Push — 0–4 weeks out</div>
                  <div class="phase-body">{gtm.get('phase_3_final_push','—')}</div>
                </div>
                """, unsafe_allow_html=True)
                channels = gtm.get("key_channels", [])
                if channels:
                    st.markdown("<div class='sec-label'>Key Channels</div>", unsafe_allow_html=True)
                    pills = "".join(f'<span class="channel-pill">{c}</span>' for c in channels)
                    st.markdown(f'<div>{pills}</div>', unsafe_allow_html=True)
                reach = gtm.get("estimated_reach", 0)
                if reach:
                    st.markdown(f"<p style='font-size:0.82rem;color:var(--green);margin-top:10px'>Est. Reach: {reach:,}</p>", unsafe_allow_html=True)

        if target_comms:
            st.markdown("<div class='sec-label'>Target Communities</div>", unsafe_allow_html=True)
            for c in target_comms:
                st.markdown(f"""
                <div class="community-card">
                  <div class="community-head">
                    <span class="community-name">{c.get('community_name','—')}</span>
                    <span class="community-niche">{c.get('niche','—')}</span>
                  </div>
                  <div class="community-meta">{c.get('platform','—')} &nbsp;·&nbsp; {c.get('members','—')} members</div>
                  <div class="community-msg">"{c.get('outreach_message','')}"</div>
                </div>
                """, unsafe_allow_html=True)

        if not gtm and not target_comms:
            section = extract_report_section(final_plan, ["gtm", "go-to-market", "community", "marketing"])
            if section:
                st.info("No structured GTM data returned — showing report excerpt.")
                st.markdown(section)
            else:
                st.info("No GTM data returned.")

    # ── SCHEDULE ──────────────────────────────────────────────────────────────
    with tabs[6]:
        agenda = ops_plan.get("agenda", [])
        if agenda:
            rows_html = '<div class="schedule-wrap">'
            for item in agenda:
                rows_html += f"""
                <div class="sched-item">
                  <div class="sched-time">{item.get('time_slot','—')}</div>
                  <div>
                    <div class="sched-title">{item.get('session_title','—')}</div>
                    <div class="sched-who">{item.get('speaker_or_performer','—')} &nbsp;·&nbsp; {item.get('room_or_stage','—')}</div>
                  </div>
                  <span class="sched-type">{item.get('session_type','—')}</span>
                </div>"""
            rows_html += '</div>'
            st.markdown(rows_html, unsafe_allow_html=True)

            res = ops_plan.get("resource_plan", {})
            if res:
                st.markdown("<div class='sec-label'>Resources</div>", unsafe_allow_html=True)
                col1, col2, col3 = st.columns(3)
                col1.metric("Rooms Needed",   res.get("total_rooms_needed","—"))
                col2.metric("Staff Estimate", res.get("total_staff_est","—"))
                with col3:
                    for item in res.get("equipment_checklist", []):
                        st.markdown(f"<div style='font-size:0.8rem;color:var(--muted2);padding:2px 0'>· {item}</div>", unsafe_allow_html=True)
        else:
            section = extract_report_section(final_plan, ["schedule", "agenda", "program", "ops"])
            if section:
                st.info("No structured schedule data returned — showing report excerpt.")
                st.markdown(section)
            else:
                st.info("No schedule data returned.")

    # ── FULL REPORT ───────────────────────────────────────────────────────────
    with tabs[7]:
        if final_plan:
            st.markdown(final_plan)
            st.markdown("<div class='sec-label'>Downloads</div>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="⬇ Download Full Report (.md)",
                    data=final_plan.encode("utf-8"),
                    file_name=f"{event_name.replace(' ','_')}_plan.md",
                    mime="text/markdown",
                )
            with col2:
                debug = {k: v for k, v in state.items() if k not in ("messages","final_plan")}
                st.download_button(
                    label="⬇ Download Raw Agent Data (.json)",
                    data=json.dumps(debug, indent=2, default=str, ensure_ascii=False).encode("utf-8"),
                    file_name=f"{event_name.replace(' ','_')}_debug.json",
                    mime="application/json",
                )
        else:
            st.info("No report generated.")

    if state.get("errors"):
        with st.expander("⚠️ Agent Warnings"):
            for e in state["errors"]:
                st.warning(e)
