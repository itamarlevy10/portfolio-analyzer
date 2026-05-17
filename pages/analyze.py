import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import random
from datetime import datetime, timezone, timedelta
import pytz
from main import build_portfolio, calculate_returns, get_sector_exposure
from risk_metrics import get_portfolio_summary, calculate_portfolio_metrics
from optimizer import get_efficient_frontier, get_efficient_frontier_line
from backtester import run_backtest
import anthropic

_ANALYSIS_MSGS = [
    "Crunching the numbers...", "Asking the market...", "Calculating your risk...",
    "Downloading market data...", "Running the models...",
]
_SECTOR_MSGS = ["Mapping your sectors...", "Identifying your industries...", "Checking what you own..."]
_FRONTIER_MSGS = ["Scanning 500 portfolios...", "Finding the efficient frontier...", "Computing optimal allocations..."]
_BACKTEST_MSGS = ["Rewinding the market...", "Simulating historical trades...", "Time-travelling through your returns..."]

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    -webkit-font-smoothing: antialiased;
}

/* ── Kill native Streamlit chrome ──────────────────────────────────── */
[data-testid="stHeader"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

/* ── App background ────────────────────────────────────────────────── */
.stApp { background: #0D1421 !important; }

/* ── Sidebar ───────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: #0F1629 !important;
    border-right: 1px solid rgba(255,255,255,0.07) !important;
    top: 52px !important;
    width: 300px !important;
    min-width: 300px !important;
}
section[data-testid="stSidebar"] > div { padding-top: 0 !important; }
[data-testid="stSidebarContent"] { padding: 0 14px 24px !important; }

/* Sidebar page navigation */
[data-testid="stSidebarNav"] { padding-bottom: 6px !important; }
[data-testid="stSidebarNavLink"] {
    color: #7A8AA0 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    border-radius: 8px !important;
}
[data-testid="stSidebarNavLink"]:hover { color: #FFFFFF !important; background: rgba(255,255,255,0.05) !important; }
[data-testid="stSidebarNavLink"][aria-current="page"] { color: #93C5FD !important; background: rgba(37,99,235,0.12) !important; }

/* ── Main content ──────────────────────────────────────────────────── */
.main .block-container {
    padding-top: 72px !important;
    padding-left: 2.2rem !important;
    padding-right: 2.2rem !important;
    max-width: 1400px !important;
    margin-left: auto !important;
    margin-right: auto !important;
}

/* ── Sidebar inputs ────────────────────────────────────────────────── */
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: rgba(255,255,255,0.04) !important;
    border-color: rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    font-size: 13px !important;
    color: #FFFFFF !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] > div:focus-within { border-color: #2563EB !important; }
[data-testid="stSidebar"] input {
    background: rgba(255,255,255,0.04) !important;
    border-color: rgba(255,255,255,0.1) !important;
    color: #FFFFFF !important;
    border-radius: 10px !important;
    font-size: 13px !important;
}
[data-testid="stSidebar"] input:focus { border-color: #2563EB !important; box-shadow: none !important; }
[data-testid="stSidebar"] input::placeholder { color: #4F6079 !important; }
[data-testid="stSidebar"] [data-testid="stNumberInput"] input {
    font-family: 'JetBrains Mono', monospace !important;
}
[data-testid="stNumberInput"] button {
    background: rgba(255,255,255,0.05) !important;
    border-color: rgba(255,255,255,0.08) !important;
    color: #B7C2D2 !important;
}

/* ── Segmented control (button groups) ─────────────────────────────── */
[data-testid="stSegmentedControl"] {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    padding: 3px !important;
}
[data-testid="stSegmentedControl"] button {
    background: transparent !important;
    color: #7A8AA0 !important;
    border: none !important;
    border-radius: 7px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 5px 10px !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stSegmentedControl"] button[aria-checked="true"],
[data-testid="stSegmentedControl"] button[data-active="true"],
[data-testid="stSegmentedControl"] button[data-selected="true"] {
    background: #142941 !important;
    color: #FFFFFF !important;
}
[data-testid="stSegmentedControl"] > label { display: none !important; }

/* ── Sidebar labels ────────────────────────────────────────────────── */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span { color: #B7C2D2; }
[data-testid="stSidebar"] .stMarkdown p { color: #B7C2D2 !important; }
[data-testid="stSidebar"] small { color: #7A8AA0 !important; }

/* ── Primary button ────────────────────────────────────────────────── */
.stButton > button[kind="primary"] {
    background: #2563EB !important;
    color: white !important;
    font-weight: 600 !important;
    font-size: 13.5px !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 10px 18px !important;
    width: 100% !important;
    box-shadow: 0 4px 14px -4px rgba(37,99,235,0.45) !important;
    transition: background 0.15s !important;
    font-family: 'Inter', sans-serif !important;
    letter-spacing: -0.01em !important;
}
.stButton > button[kind="primary"]:hover { background: #1D4ED8 !important; }
.stButton > button[kind="primary"]:active { transform: translateY(1px) !important; }

/* ── Secondary button ──────────────────────────────────────────────── */
.stButton > button:not([kind="primary"]) {
    background: transparent !important;
    color: #B7C2D2 !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    transition: all 0.15s !important;
    font-family: 'Inter', sans-serif !important;
}
.stButton > button:not([kind="primary"]):hover {
    background: rgba(255,255,255,0.05) !important;
    color: #FFFFFF !important;
    border-color: rgba(255,255,255,0.2) !important;
}

/* ── Tabs ──────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: #0F1E33 !important;
    border-radius: 12px !important;
    padding: 4px !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    gap: 2px !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #7A8AA0 !important;
    border-radius: 9px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 8px 16px !important;
    border: none !important;
}
.stTabs [aria-selected="true"] {
    background: #142941 !important;
    color: #FFFFFF !important;
    box-shadow: inset 0 0 0 1px rgba(255,255,255,0.1) !important;
}

/* ── Expanders ─────────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    background: #131E30 !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}
[data-testid="stExpander"] summary {
    font-weight: 600 !important;
    font-size: 13.5px !important;
    color: #FFFFFF !important;
    padding: 14px 16px !important;
}
[data-testid="stExpander"] summary:hover { background: rgba(255,255,255,0.02) !important; }

/* ── Alerts ────────────────────────────────────────────────────────── */
[data-testid="stSuccess"] {
    background: rgba(22,163,74,0.1) !important;
    border: 1px solid rgba(22,163,74,0.25) !important;
    border-radius: 12px !important;
}
[data-testid="stInfo"] {
    background: rgba(37,99,235,0.08) !important;
    border: 1px solid rgba(37,99,235,0.2) !important;
    border-radius: 12px !important;
}
[data-testid="stWarning"] {
    background: rgba(217,119,6,0.08) !important;
    border: 1px solid rgba(217,119,6,0.2) !important;
    border-radius: 12px !important;
}
[data-testid="stError"] {
    background: rgba(220,38,38,0.08) !important;
    border: 1px solid rgba(220,38,38,0.2) !important;
    border-radius: 12px !important;
}

/* ── Equal-height risk metric columns ──────────────────────────────── */
[data-testid="stHorizontalBlock"] {
    align-items: stretch !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"] > div:first-child {
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
}
.rm-card { flex: 1 !important; }
.rm-badge { white-space: nowrap !important; }

/* ── Per-asset metric cards (inside expanders) ─────────────────────── */
.asset-metric-card {
    background: #FFFFFF;
    border-radius: 12px;
    padding: 14px 16px 12px;
    border: 1px solid #E8ECF2;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    height: 100%;
}
.asset-metric-label {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #6B7A8D;
    font-weight: 600;
    margin-bottom: 4px;
}
.asset-metric-value {
    font-size: 26px;
    font-weight: 700;
    color: #0A1628;
    letter-spacing: -0.025em;
    line-height: 1.1;
    margin-bottom: 6px;
}
.asset-metric-explain {
    font-size: 11px;
    color: #6B7A8D;
    line-height: 1.4;
}

/* ── Dataframes ────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* ── Dividers ──────────────────────────────────────────────────────── */
hr { border-color: rgba(255,255,255,0.07) !important; margin: 10px 0 !important; }

/* ── Text inputs (AI advisor) ──────────────────────────────────────── */
[data-testid="stTextInput"] input {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 10px !important;
    color: #FFFFFF !important;
    font-size: 13.5px !important;
    padding: 10px 14px !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: #2563EB !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.15) !important;
}
[data-testid="stTextInput"] input::placeholder { color: #4F6079 !important; }

/* ── Select dropdowns ──────────────────────────────────────────────── */
[data-baseweb="select"] > div {
    background: rgba(255,255,255,0.04) !important;
    border-color: rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
}

/* ── Plotly chart wrapper ──────────────────────────────────────────── */
[data-testid="stPlotlyChart"] {
    background: #131E30 !important;
    border-radius: 14px !important;
    padding: 8px !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
}

/* ── Spinner ───────────────────────────────────────────────────────── */
[data-testid="stSpinner"] { color: #2563EB !important; }

/* ── Captions ──────────────────────────────────────────────────────── */
[data-testid="stCaptionContainer"] p { color: #7A8AA0 !important; font-size: 12px !important; }

/* ── Sidebar section labels (injected HTML) ─────────────────────────── */
.sb-section-label {
    font-size: 10.5px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.09em;
    color: #4F6079;
    margin-top: 18px;
    margin-bottom: 6px;
    display: block;
}
.sb-portfolio-title {
    font-size: 17px;
    font-weight: 700;
    color: #FFFFFF;
    letter-spacing: -0.01em;
    margin-bottom: 2px;
}
.sb-holdings-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 18px;
    margin-bottom: 8px;
}
.sb-holdings-header .label { font-size: 10.5px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.09em; color: #4F6079; }
.sb-holdings-header .drag { font-size: 10.5px; color: #4F6079; }

/* ── Holding card ──────────────────────────────────────────────────── */
.holding-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 11px;
    padding: 11px 12px 10px;
    margin-bottom: 7px;
}
.holding-top {
    display: flex;
    align-items: center;
    gap: 9px;
    margin-bottom: 6px;
}
.holding-badge {
    width: 36px;
    height: 36px;
    border-radius: 7px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 10px;
    font-weight: 700;
    color: white;
    flex-shrink: 0;
    letter-spacing: 0.01em;
    font-family: 'JetBrains Mono', monospace;
}
.holding-ticker { font-size: 13px; font-weight: 600; color: #FFFFFF; line-height: 1.2; }
.holding-company { font-size: 11px; color: #7A8AA0; line-height: 1.2; }
.holding-pct-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
}
.holding-pct { font-size: 11px; color: #7A8AA0; }
.holding-bar-track {
    height: 3px;
    background: rgba(255,255,255,0.07);
    border-radius: 2px;
    overflow: hidden;
    margin-top: 4px;
}
.holding-bar-fill {
    height: 100%;
    border-radius: 2px;
    transition: width 0.4s ease;
}

/* ── Dashboard header ──────────────────────────────────────────────── */
.dash-breadcrumb {
    font-size: 12px;
    color: #4F6079;
    margin-bottom: 6px;
    font-family: 'Inter', sans-serif;
}
.dash-breadcrumb span { color: #B7C2D2; }
.dash-header-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 22px;
}
.dash-title {
    font-size: 30px;
    font-weight: 700;
    color: #FFFFFF;
    letter-spacing: -0.02em;
    line-height: 1;
}
.dash-actions { display: flex; gap: 8px; }
.dash-btn {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 7px 13px;
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 8px;
    background: transparent;
    color: #B7C2D2;
    font-size: 12.5px;
    font-weight: 500;
    cursor: pointer;
    font-family: 'Inter', sans-serif;
    letter-spacing: -0.01em;
}

/* ── Portfolio value card ──────────────────────────────────────────── */
.pv-card {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 22px 24px;
    margin-bottom: 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}
.pv-label {
    font-size: 10.5px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.09em;
    color: #6B7A8D;
    margin-bottom: 6px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.pv-time-btns { display: flex; gap: 2px; }
.pv-time-btn {
    padding: 3px 9px;
    border-radius: 6px;
    border: none;
    background: transparent;
    color: #6B7A8D;
    font-size: 11.5px;
    font-weight: 500;
    cursor: pointer;
    font-family: 'Inter', sans-serif;
}
.pv-time-btn.active { background: #0A1628; color: #FFFFFF; }
.pv-amount {
    font-size: 52px;
    font-weight: 700;
    color: #0A1628;
    letter-spacing: -0.035em;
    line-height: 1;
    margin-bottom: 10px;
}
.pv-amount .cents { color: #9AABB8; font-size: 38px; }
.pv-change-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 14px; }
.pv-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: rgba(22,163,74,0.1);
    border: 1px solid rgba(22,163,74,0.22);
    border-radius: 8px;
    padding: 4px 9px;
    font-size: 12.5px;
    font-weight: 600;
    color: #16A34A;
}
.pv-badge.neg {
    background: rgba(220,38,38,0.08);
    border-color: rgba(220,38,38,0.2);
    color: #DC2626;
}
.pv-compare { font-size: 13px; color: #6B7A8D; }
.pv-stats-row {
    display: flex;
    gap: 28px;
    padding-top: 14px;
    border-top: 1px solid #F0F4F8;
    flex-wrap: wrap;
}
.pv-stat-label {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: #6B7A8D;
    font-weight: 600;
    margin-bottom: 3px;
}
.pv-stat-val { font-size: 19px; font-weight: 700; letter-spacing: -0.015em; }
.pv-stat-val.pos { color: #16A34A; }
.pv-stat-val.neg { color: #DC2626; }
.pv-stat-val.neutral { color: #0A1628; }

/* ── Risk metrics section ──────────────────────────────────────────── */
.rm-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
    margin-top: 4px;
}
.rm-header-left {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.09em;
    color: #7A8AA0;
}
.rm-header-right { font-size: 12px; color: #4F6079; }

/* ── Risk metric card ──────────────────────────────────────────────── */
.rm-card {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 18px 20px 16px;
    border: 1px solid #E8ECF2;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    height: 100%;
}
.rm-card-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 6px;
}
.rm-card-label {
    font-size: 10.5px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: #6B7A8D;
}
.rm-info {
    width: 16px;
    height: 16px;
    border: 1.5px solid #C8D4DE;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 9px;
    color: #9AA8B4;
    font-weight: 600;
    cursor: help;
    flex-shrink: 0;
}
.rm-value {
    font-size: 36px;
    font-weight: 700;
    color: #0A1628;
    letter-spacing: -0.03em;
    line-height: 1.1;
    margin-bottom: 9px;
}
.rm-value .unit { font-size: 26px; color: #6B7A8D; font-weight: 600; }
.rm-mid {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}
.rm-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
}
.rm-badge.green  { background: #DCFCE7; color: #16A34A; }
.rm-badge.orange { background: #FEF3C7; color: #D97706; }
.rm-badge.red    { background: #FEE2E2; color: #DC2626; }
.rm-badge.blue   { background: #DBEAFE; color: #1D4ED8; }
.rm-dot { width: 6px; height: 6px; border-radius: 50%; }
.rm-badge.green  .rm-dot { background: #16A34A; }
.rm-badge.orange .rm-dot { background: #D97706; }
.rm-badge.red    .rm-dot { background: #DC2626; }
.rm-badge.blue   .rm-dot { background: #1D4ED8; }
.rm-secondary { font-size: 11px; color: #9AABB8; }
.rm-progress {
    display: flex;
    gap: 3px;
}
.rm-seg {
    flex: 1;
    height: 3px;
    border-radius: 2px;
    background: #EAF0F6;
}
.rm-seg.green  { background: #16A34A; }
.rm-seg.orange { background: #D97706; }
.rm-seg.red    { background: #DC2626; }
.rm-seg.blue   { background: #2563EB; }

/* ── Section headers in main area ──────────────────────────────────── */
.section-head {
    font-size: 14px;
    font-weight: 600;
    color: #FFFFFF;
    letter-spacing: -0.01em;
    margin: 24px 0 12px;
}
.section-head .sub {
    font-size: 12px;
    font-weight: 400;
    color: #7A8AA0;
    margin-left: 6px;
}
</style>
""", unsafe_allow_html=True)

# ── Chart theme ───────────────────────────────────────────────────────────────
def _chart_layout(**extra):
    base = dict(
        paper_bgcolor="#131E30",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#B7C2D2", size=12),
        xaxis=dict(
            gridcolor="rgba(255,255,255,0.05)",
            linecolor="rgba(255,255,255,0.07)",
            tickfont=dict(color="#7A8AA0", size=11),
        ),
        yaxis=dict(
            gridcolor="rgba(255,255,255,0.05)",
            linecolor="rgba(255,255,255,0.07)",
            tickfont=dict(color="#7A8AA0", size=11),
        ),
        margin=dict(l=8, r=8, t=8, b=8),
    )
    base.update(extra)
    return base

# ── Live market tickers ───────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def _fetch_tickers():
    symbols = {"SPY": "SPY", "VIX": "^VIX", "USD/ILS": "ILS=X", "TA-125": "^TA125.TA"}
    out = {}
    for name, sym in symbols.items():
        try:
            fi = yf.Ticker(sym).fast_info
            cur = fi.last_price
            prev = fi.previous_close
            if cur and prev and prev != 0:
                out[name] = (float(cur), float((cur - prev) / prev * 100))
            elif cur:
                out[name] = (float(cur), 0.0)
            else:
                out[name] = (None, None)
        except Exception:
            out[name] = (None, None)
    return out

def _market_open():
    eastern = pytz.timezone("America/New_York")
    now_et = datetime.now(pytz.utc).astimezone(eastern)
    if now_et.weekday() >= 5:
        return False
    open_t = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
    close_t = now_et.replace(hour=16, minute=0, second=0, microsecond=0)
    return open_t <= now_et <= close_t

@st.cache_data(ttl=30)
def _search_assets(query):
    try:
        results = yf.Search(query, max_results=8).quotes
        filtered = [r for r in results if r.get("quoteType") in ("EQUITY", "ETF", "INDEX", "MUTUALFUND")]
        out = []
        for r in filtered[:8]:
            name = r.get("longname") or r.get("shortname") or r["symbol"]
            out.append({"symbol": r["symbol"], "name": name})
        return out
    except Exception:
        return []

tickers_data = _fetch_tickers()
market_open = _market_open()

def _ticker_html(name, val, chg):
    if val is None:
        return f'<span class="nav-tick"><span class="nt-name">{name}</span></span>'
    color = "#4ADE80" if chg >= 0 else "#F87171"
    sign = "+" if chg >= 0 else ""
    return (f'<span class="nav-tick">'
            f'<span class="nt-name">{name}</span>'
            f'<span class="nt-val">{val:,.2f}</span>'
            f'<span class="nt-chg" style="color:{color}">{sign}{chg:.2f}%</span>'
            f'</span>')

tickers_html = "&nbsp;&nbsp;&nbsp;".join(
    _ticker_html(n, v, c) for n, (v, c) in tickers_data.items()
)
market_label = "● Markets Open" if market_open else "○ Markets Closed"
market_class = "open" if market_open else "closed"

st.markdown(f"""
<style>
.navbar {{
    position: fixed; top: 0; left: 0; right: 0; height: 52px;
    background: #0A1421; border-bottom: 1px solid rgba(255,255,255,0.08);
    z-index: 999999; display: flex; align-items: center;
    padding: 0 20px; gap: 20px;
    font-family: 'Inter', sans-serif;
}}
.nav-brand {{ display: flex; align-items: center; gap: 9px; min-width: 210px; }}
.nav-logo {{
    width: 30px; height: 30px; background: #2563EB; border-radius: 7px;
    display: flex; align-items: center; justify-content: center;
}}
.nav-logo svg {{ display: block; }}
.nav-name {{ font-size: 14.5px; font-weight: 600; color: #FFFFFF; letter-spacing: -0.01em; }}
.nav-tickers {{ display: flex; align-items: center; flex: 1; overflow: hidden; }}
.nav-tick {{ display: inline-flex; align-items: center; gap: 5px; white-space: nowrap; }}
.nt-name {{ font-size: 12.5px; color: #7A8AA0; font-weight: 500; }}
.nt-val {{ font-size: 12.5px; color: #E2E8F0; font-weight: 600; font-family: 'JetBrains Mono', monospace; }}
.nt-chg {{ font-size: 11.5px; font-family: 'JetBrains Mono', monospace; }}
.nav-right {{ display: flex; align-items: center; gap: 10px; flex-shrink: 0; }}
.market-badge {{
    font-size: 11.5px; font-weight: 500; padding: 4px 10px; border-radius: 20px; border: 1px solid; white-space: nowrap;
}}
.market-badge.open {{ color: #4ADE80; border-color: rgba(74,222,128,0.3); background: rgba(74,222,128,0.08); }}
.market-badge.closed {{ color: #F87171; border-color: rgba(248,113,113,0.3); background: rgba(248,113,113,0.08); }}
.nav-avatar {{
    width: 30px; height: 30px; border-radius: 50%; background: #2563EB;
    color: white; display: flex; align-items: center; justify-content: center;
    font-size: 11px; font-weight: 700; cursor: pointer;
}}
</style>
<div class="navbar">
    <div class="nav-brand">
        <div class="nav-logo">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <polyline points="1,12 5,6 8,9 11,4 15,7" stroke="white" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
            </svg>
        </div>
        <span class="nav-name">Portfolio Analyzer</span>
    </div>
    <div class="nav-tickers">{tickers_html}</div>
    <div class="nav-right">
        <span class="market-badge {market_class}">{market_label}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Metric badge helper ───────────────────────────────────────────────────────
def _badge(metric, value):
    """Return (label, color_class) for a risk metric."""
    if metric == "sharpe":
        if value > 2:   return "Excellent", "green"
        if value > 1:   return "Good", "green"
        if value > 0:   return "Mediocre", "orange"
        return "Poor", "red"
    if metric == "volatility":
        if value < 0.08:  return "Low", "green"
        if value < 0.15:  return "Moderate", "green"
        if value < 0.25:  return "High", "orange"
        return "Very High", "red"
    if metric == "beta":
        if value < 0:    return "Hedge", "green"
        if value < 0.5:  return "Low", "green"
        if value < 1.0:  return "Below market", "green"
        if value < 1.3:  return "Near market", "orange"
        return "High", "red"
    if metric == "max_drawdown":
        if value > -0.05:  return "Minimal", "green"
        if value > -0.15:  return "Manageable", "orange"
        if value > -0.30:  return "Significant", "orange"
        return "Severe", "red"
    if metric == "var":
        if value > -0.02:  return "Low risk", "green"
        if value > -0.04:  return "Moderate", "green"
        if value > -0.07:  return "Elevated", "orange"
        return "High", "red"
    return "", "orange"

def _segs(color, filled, total=4):
    """Return HTML for a segmented progress bar."""
    parts = []
    for i in range(total):
        cls = color if i < filled else ""
        parts.append(f'<div class="rm-seg {cls}"></div>')
    return "".join(parts)

def _filled_count(metric, value):
    """Return how many segments to fill (1-4)."""
    if metric == "sharpe":
        if value > 2:   return 4
        if value > 1:   return 3
        if value > 0.5: return 2
        return 1
    if metric == "volatility":
        if value < 0.08:  return 4
        if value < 0.15:  return 3
        if value < 0.25:  return 2
        return 1
    if metric == "beta":
        if abs(value - 1) < 0.1:  return 4
        if abs(value - 1) < 0.3:  return 3
        if abs(value - 1) < 0.6:  return 2
        return 1
    if metric == "max_drawdown":
        if value > -0.05:  return 1
        if value > -0.15:  return 2
        if value > -0.30:  return 3
        return 4
    if metric == "var":
        if value > -0.02:  return 1
        if value > -0.04:  return 2
        if value > -0.07:  return 3
        return 4
    return 2

def _rm_card(label, value_str, badge_label, badge_color, secondary, segs_html, help_title=""):
    return f"""
<div class="rm-card">
  <div class="rm-card-top">
    <span class="rm-card-label">{label}</span>
    <span class="rm-info" title="{help_title}">i</span>
  </div>
  <div class="rm-value">{value_str}</div>
  <div class="rm-mid">
    <span class="rm-badge {badge_color}">
      <span class="rm-dot"></span>{badge_label}
    </span>
    <span class="rm-secondary">{secondary}</span>
  </div>
  <div class="rm-progress">{segs_html}</div>
</div>"""

# ── Plain-language explains (no emojis) ───────────────────────────────────────
def explain_sharpe(v):
    if v > 2:   return "Excellent — outstanding return for the risk taken"
    if v > 1:   return "Good — well rewarded for the risk you are taking"
    if v > 0:   return "Mediocre — positive but not great relative to risk"
    return "Poor — a risk-free savings account would have done better"

def explain_volatility(v):
    if v < 0.08:  return "Low — very stable, similar to a bond-like portfolio"
    if v < 0.15:  return "Moderate — typical for a diversified stock portfolio"
    if v < 0.25:  return "High — expect significant swings day to day"
    return "Very High — can move dramatically in short periods"

def explain_max_drawdown(v):
    if v > -0.05:  return "Minimal — very small worst-case loss historically"
    if v > -0.15:  return "Manageable — a rough patch but recoverable"
    if v > -0.30:  return "Significant — this would test most investors' patience"
    return "Severe — most investors would panic-sell at this level"

def explain_beta(v):
    if v < 0:    return "Negative — moves opposite to the market, a true hedge"
    if v < 0.5:  return "Low — much less sensitive to market swings than average"
    if v < 1.0:  return "Below market — moves less than the market"
    if v < 1.3:  return "Near market — moves roughly with the market"
    return "High — amplifies market moves, both up and down"

def explain_var(v):
    if v > -0.02:  return "Low risk — on a bad day, losses expected to stay under 2%"
    if v > -0.04:  return "Moderate — typical for a diversified stock portfolio"
    if v > -0.07:  return "Elevated — expect occasional 4-7% single-day losses"
    return "High — severe single-day losses are plausible"

# ── Asset constants ───────────────────────────────────────────────────────────
POPULAR_ASSETS = [
    ("Apple Inc.", "AAPL"), ("Microsoft", "MSFT"), ("NVIDIA", "NVDA"),
    ("Amazon", "AMZN"), ("Alphabet (Google)", "GOOGL"), ("Meta Platforms", "META"),
    ("Tesla", "TSLA"), ("Berkshire Hathaway", "BRK-B"), ("Eli Lilly", "LLY"),
    ("JPMorgan Chase", "JPM"), ("Visa", "V"), ("Mastercard", "MA"),
    ("Exxon Mobil", "XOM"), ("UnitedHealth", "UNH"), ("Johnson & Johnson", "JNJ"),
    ("Walmart", "WMT"), ("Procter & Gamble", "PG"), ("Home Depot", "HD"),
    ("Chevron", "CVX"), ("Merck", "MRK"), ("AbbVie", "ABBV"), ("Costco", "COST"),
    ("Bank of America", "BAC"), ("Netflix", "NFLX"), ("Salesforce", "CRM"),
    ("AMD", "AMD"), ("Intel", "INTC"), ("Qualcomm", "QCOM"),
    ("Texas Instruments", "TXN"), ("Adobe", "ADBE"), ("Broadcom", "AVGO"),
    ("Oracle", "ORCL"), ("Cisco", "CSCO"), ("IBM", "IBM"), ("Palantir", "PLTR"),
    ("Snowflake", "SNOW"), ("CrowdStrike", "CRWD"), ("Datadog", "DDOG"),
    ("ServiceNow", "NOW"), ("Workday", "WDAY"), ("Palo Alto Networks", "PANW"),
    ("Fortinet", "FTNT"), ("Cloudflare", "NET"), ("Spotify", "SPOT"),
    ("Uber", "UBER"), ("Airbnb", "ABNB"), ("Block (Square)", "SQ"),
    ("PayPal", "PYPL"), ("Shopify", "SHOP"), ("Coinbase", "COIN"),
    ("Robinhood", "HOOD"), ("Goldman Sachs", "GS"), ("Morgan Stanley", "MS"),
    ("Wells Fargo", "WFC"), ("Citigroup", "C"), ("American Express", "AXP"),
    ("BlackRock", "BLK"), ("Charles Schwab", "SCHW"), ("Boeing", "BA"),
    ("Lockheed Martin", "LMT"), ("Raytheon", "RTX"), ("General Electric", "GE"),
    ("Caterpillar", "CAT"), ("Deere & Company", "DE"), ("3M", "MMM"),
    ("UPS", "UPS"), ("FedEx", "FDX"), ("Nike", "NKE"), ("Starbucks", "SBUX"),
    ("McDonald's", "MCD"), ("Coca-Cola", "KO"), ("PepsiCo", "PEP"),
    ("Philip Morris", "PM"), ("Altria", "MO"), ("Disney", "DIS"),
    ("Comcast", "CMCSA"), ("AT&T", "T"), ("Verizon", "VZ"), ("T-Mobile", "TMUS"),
    ("Pfizer", "PFE"), ("Moderna", "MRNA"), ("BioNTech", "BNTX"),
    ("Gilead Sciences", "GILD"), ("Amgen", "AMGN"), ("CVS Health", "CVS"),
    ("Anthem", "ELV"), ("Intuitive Surgical", "ISRG"), ("Thermo Fisher", "TMO"),
    ("Danaher", "DHR"), ("ASML", "ASML"), ("Taiwan Semiconductor", "TSM"),
    ("Toyota", "TM"), ("Shell", "SHEL"), ("BP", "BP"),
    ("S&P 500 ETF", "SPY"), ("Nasdaq 100 ETF", "QQQ"), ("Total Market ETF", "VTI"),
    ("International ETF", "VXUS"), ("Emerging Markets ETF", "EEM"),
    ("Small Cap ETF", "IWM"), ("Dividend ETF", "VYM"), ("Growth ETF", "VUG"),
    ("Value ETF", "VTV"), ("Technology ETF", "XLK"), ("Healthcare ETF", "XLV"),
    ("Financials ETF", "XLF"), ("Energy ETF", "XLE"), ("Consumer ETF", "XLY"),
    ("Industrials ETF", "XLI"), ("Real Estate ETF", "VNQ"),
    ("Utilities ETF", "XLU"), ("Clean Energy ETF", "ICLN"),
    ("Semiconductor ETF", "SOXX"), ("Biotech ETF", "IBB"),
    ("ARK Innovation ETF", "ARKK"), ("Vanguard S&P 500", "VOO"),
    ("iShares Core S&P", "IVV"), ("Long-Term Treasury", "TLT"),
    ("Short-Term Treasury", "SHY"), ("Mid-Term Treasury", "IEF"),
    ("Corporate Bonds", "LQD"), ("High Yield Bonds", "HYG"),
    ("TIPS Inflation", "TIP"), ("Total Bond Market", "BND"),
    ("International Bonds", "BNDX"), ("Emerging Market Bonds", "EMB"),
    ("Gold ETF", "GLD"), ("Silver ETF", "SLV"), ("Oil ETF", "USO"),
    ("Natural Gas ETF", "UNG"), ("Agriculture ETF", "DBA"),
    ("Copper ETF", "CPER"), ("Bitcoin ETF", "IBIT"), ("Ethereum ETF", "ETHA"),
    ("MicroStrategy", "MSTR"), ("Check Point Software", "CHKP"),
    ("Nice Systems", "NICE"), ("Amdocs", "DOX"), ("CyberArk", "CYBR"),
    ("Tower Semiconductor", "TSEM"), ("Elbit Systems", "ESLT"),
    ("Bank Hapoalim", "POLI.TA"), ("Bank Leumi", "LUMI.TA"),
    ("Mizrahi Tefahot", "MZTF.TA"), ("Bank Discount", "DSCT.TA"),
    ("First International Bank", "FIBI.TA"), ("Harel Insurance", "HARL.TA"),
    ("Phoenix Holdings", "PHOE.TA"), ("Clal Insurance", "CLIS.TA"),
    ("Azrieli Group", "AZRG.TA"), ("Gazit Globe", "GZT.TA"),
    ("Delek Group", "DLEKG.TA"), ("NewMed Energy", "NWMD.TA"),
    ("Teva Pharmaceutical", "TEVA"), ("Cellebrite", "CLBT"),
    ("monday.com", "MNDY"), ("Global-e Online", "GLBE"), ("eToro", "ETOR"),
    ("TA-125 Index", "^TA125.TA"), ("TA-35 Index", "^TA35.TA"),
    ("TA-90 Index", "^TA90.TA"), ("TA Tech-Elite", "^TATECH.TA"),
    ("TA Real Estate Index", "^TARE.TA"), ("TA Banks Index", "^TABANK.TA"),
    ("MSCI World ETF", "URTH"), ("Europe ETF", "VGK"), ("Japan ETF", "EWJ"),
    ("China ETF", "MCHI"), ("India ETF", "INDA"), ("Brazil ETF", "EWZ"),
    ("UK ETF", "EWU"), ("Germany ETF", "EWG"),
]

ASSET_OPTIONS = [f"{name} ({ticker})" for name, ticker in POPULAR_ASSETS]
TICKER_TO_NAME = {ticker: name for name, ticker in POPULAR_ASSETS}

_BADGE_COLORS = ["#3B82F6", "#8B5CF6", "#06B6D4", "#F97316", "#EF4444", "#10B981",
                 "#F59E0B", "#EC4899", "#14B8A6", "#6366F1"]

def _ticker_color(ticker):
    return _BADGE_COLORS[sum(ord(c) for c in ticker) % len(_BADGE_COLORS)]

def extract_ticker(label):
    return label.split("(")[-1].replace(")", "").strip()

# ── App state ─────────────────────────────────────────────────────────────────
if "app_state" not in st.session_state:
    st.session_state["app_state"] = "landing"
_state = st.session_state["app_state"]

if _state in ("landing", "analyze_form"):
    st.markdown("""<style>
section[data-testid="stSidebar"],
[data-testid="stSidebarNav"],
[data-testid="collapsedControl"] { display: none !important; }
.main .block-container { padding-top: 80px !important; }
</style>""", unsafe_allow_html=True)

if _state == "landing":
    _ll, _lm, _lr = st.columns([1, 4, 1])
    with _lm:
        st.markdown("""
<div style="text-align:center;padding:50px 0 52px">
  <div style="width:56px;height:56px;background:#2563EB;border-radius:14px;
              display:inline-flex;align-items:center;justify-content:center;margin-bottom:20px">
    <svg width="26" height="26" viewBox="0 0 16 16" fill="none">
      <polyline points="1,12 5,6 8,9 11,4 15,7" stroke="white" stroke-width="1.8"
                stroke-linecap="round" stroke-linejoin="round" fill="none"/>
    </svg>
  </div>
  <div style="font-size:42px;font-weight:700;color:#FFFFFF;letter-spacing:-0.025em;
              margin-bottom:10px;line-height:1.1">Portfolio Analyzer</div>
  <div style="font-size:16px;color:#7A8AA0">Your intelligent investment companion</div>
</div>""", unsafe_allow_html=True)

        _lb, _lgap, _la = st.columns([5, 1, 5])
        with _lb:
            st.markdown("""
<div style="background:#0F1E33;border:1px solid rgba(255,255,255,0.09);border-radius:18px;
            padding:36px 28px 20px;text-align:center;min-height:220px">
  <div style="font-size:38px;margin-bottom:14px">🤖</div>
  <div style="font-size:19px;font-weight:700;color:#FFFFFF;margin-bottom:10px">Build My Portfolio</div>
  <div style="font-size:13px;color:#7A8AA0;line-height:1.6;margin-bottom:20px">
    Answer 5 questions and get an AI-designed portfolio tailored to your goals, risk, and budget.
  </div>
</div>""", unsafe_allow_html=True)
            if st.button("Build with AI →", key="go_build", type="primary", use_container_width=True):
                st.switch_page("pages/1_Build_My_Portfolio.py")

        with _la:
            st.markdown("""
<div style="background:#0F1E33;border:1.5px solid rgba(37,99,235,0.45);border-radius:18px;
            padding:36px 28px 20px;text-align:center;min-height:220px;
            box-shadow:0 0 40px rgba(37,99,235,0.07)">
  <div style="font-size:38px;margin-bottom:14px">📊</div>
  <div style="font-size:19px;font-weight:700;color:#FFFFFF;margin-bottom:10px">Analyse Existing Portfolio</div>
  <div style="font-size:13px;color:#7A8AA0;line-height:1.6;margin-bottom:20px">
    Enter your holdings and get deep risk insights, performance charts, and AI analysis.
  </div>
</div>""", unsafe_allow_html=True)
            if st.button("Start Analysis →", key="go_analyze", type="primary", use_container_width=True):
                st.session_state["app_state"] = "analyze_form"
                st.rerun()
    st.stop()

elif _state == "analyze_form":
    if "holdings_rows" not in st.session_state:
        st.session_state.holdings_rows = [{"ticker": "", "value": 0.0, "name": ""}]

    _fl, _fm, _fr = st.columns([1, 3, 1])
    with _fm:
        if st.button("← Home", key="form_back"):
            st.session_state["app_state"] = "landing"
            st.rerun()

        st.markdown("""
<div style="margin:20px 0 28px">
  <div style="font-size:28px;font-weight:700;color:#FFFFFF;letter-spacing:-0.02em;margin-bottom:6px">
    Analyse your portfolio</div>
  <div style="font-size:14px;color:#7A8AA0">
    Add your holdings and we'll calculate risk metrics, returns, and AI insights.</div>
</div>""", unsafe_allow_html=True)

        st.markdown('<p style="font-size:11px;font-weight:600;color:#4F6079;letter-spacing:0.09em;'
                    'margin-bottom:4px">HOLDINGS</p>', unsafe_allow_html=True)

        for _fi, _frow in enumerate(st.session_state.holdings_rows):
            _fticker = _frow.get("ticker", "")
            _fca, _fcb, _fcc = st.columns([4, 3, 1])
            with _fca:
                if not _fticker:
                    _fq = st.text_input("Asset", placeholder="Search: AAPL, SPY, TEVA...",
                                        key=f"fs_{_fi}", label_visibility="collapsed")
                    if _fq and len(_fq) >= 2:
                        for _fres in _search_assets(_fq)[:5]:
                            if st.button(f"{_fres['name']} ({_fres['symbol']})",
                                         key=f"fp_{_fi}_{_fres['symbol']}", use_container_width=True):
                                st.session_state.holdings_rows[_fi]["ticker"] = _fres["symbol"]
                                st.session_state.holdings_rows[_fi]["name"] = _fres["name"]
                                if f"fs_{_fi}" in st.session_state:
                                    del st.session_state[f"fs_{_fi}"]
                                st.rerun()
                else:
                    _fn = _frow.get("name") or TICKER_TO_NAME.get(_fticker, "")
                    st.markdown(
                        f'<div style="padding:10px 0 4px;font-size:14px;font-weight:600;color:#FFFFFF">'
                        f'{_fticker} <span style="color:#7A8AA0;font-weight:400;font-size:12px">{_fn}</span></div>',
                        unsafe_allow_html=True)
            with _fcb:
                _fi_init = None if _frow["value"] == 0.0 else _frow["value"]
                _fi_raw = st.number_input("Amount", min_value=0.0, value=_fi_init,
                                          placeholder="$ Amount...", key=f"fv_{_fi}",
                                          label_visibility="collapsed")
                st.session_state.holdings_rows[_fi]["value"] = float(_fi_raw) if _fi_raw else 0.0
            with _fcc:
                if _fticker:
                    if st.button("×", key=f"fch_{_fi}"):
                        st.session_state.holdings_rows[_fi]["ticker"] = ""
                        st.session_state.holdings_rows[_fi]["name"] = ""
                        st.rerun()
                else:
                    if len(st.session_state.holdings_rows) > 1 and st.button("×", key=f"frm_{_fi}"):
                        st.session_state.holdings_rows.pop(_fi)
                        st.rerun()

        if st.button("+ Add asset", key="form_add_asset"):
            st.session_state.holdings_rows.append({"ticker": "", "value": 0.0, "name": ""})
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        _fsa, _fsb, _fsc = st.columns(3)
        with _fsa:
            _f_period_lbl = st.selectbox("Period", ["1M", "6M", "1Y", "2Y", "5Y"],
                                         index=2, key="form_period_sel")
        with _fsb:
            _f_currency = st.selectbox("Currency", ["$ USD", "₪ ILS", "€ EUR"],
                                       index=0, key="form_currency_sel")
        with _fsc:
            _f_benchmark = st.selectbox("Benchmark",
                                        ["SPY · US Market", "^TA125.TA · Israel Market"],
                                        index=0, key="form_bench_sel")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Analyse Portfolio →", type="primary", use_container_width=True, key="form_run"):
            _f_filled = [r for r in st.session_state.holdings_rows
                         if r["ticker"].strip() and r["value"] > 0]
            if not _f_filled:
                st.error("Please add at least one asset with an amount.")
            else:
                _f_pmap = {"1M": "1mo", "6M": "6mo", "1Y": "1y", "2Y": "2y", "5Y": "5y"}
                _f_prd = _f_pmap[_f_period_lbl]
                _f_csym = _f_currency.split(" ")[0]
                _f_bm = _f_benchmark.split(" ")[0]
                _f_total = sum(r["value"] for r in _f_filled)
                _f_hlds = [{"ticker": r["ticker"], "weight": r["value"] / _f_total}
                           for r in _f_filled]
                with st.spinner("Analysing your portfolio..."):
                    _f_prices  = build_portfolio(_f_hlds, period=_f_prd)
                    _f_returns = calculate_returns(_f_prices)
                    _f_summary = get_portfolio_summary(_f_returns, benchmark=_f_bm)
                    _f_pm      = calculate_portfolio_metrics(
                        _f_returns, _f_hlds, risk_free_rate=_f_summary["risk_free_rate"])
                st.session_state["analysis"] = {
                    "returns": _f_returns, "holdings": _f_hlds,
                    "summary": _f_summary, "portfolio_metrics": _f_pm,
                    "period": _f_prd, "total_invested": _f_total,
                    "currency_symbol": _f_csym, "benchmark_ticker": _f_bm,
                }
                st.session_state["app_state"] = "dashboard"
                st.session_state["bench_sel"]    = _f_benchmark
                st.session_state["period_seg"]   = _f_period_lbl
                st.session_state["currency_seg"] = _f_currency
                st.session_state.pop("opt_result", None)
                st.session_state.pop("opt_frontier", None)
                st.session_state.pop("cum_ret_lines", None)
                st.rerun()
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.markdown('<span class="sb-section-label">PORTFOLIO</span><div class="sb-portfolio-title">My Holdings</div>', unsafe_allow_html=True)

st.sidebar.markdown('<span class="sb-section-label">BENCHMARK</span>', unsafe_allow_html=True)
_bench_opts = ["SPY · US Market", "^TA125.TA · Israel Market"]
_bench_sel = st.sidebar.selectbox("Benchmark", options=_bench_opts, label_visibility="collapsed", key="bench_sel")
benchmark_ticker = _bench_sel.split(" ")[0]

st.sidebar.markdown('<span class="sb-section-label">TIME PERIOD</span>', unsafe_allow_html=True)
_period_label = st.sidebar.segmented_control(
    "Time Period", options=["6M", "1Y", "2Y", "5Y"], default="1Y",
    key="period_seg", label_visibility="collapsed",
)
_period_map = {"6M": "6mo", "1Y": "1y", "2Y": "2y", "5Y": "5y"}
period = _period_map.get(_period_label or "1Y", "1y")

st.sidebar.markdown('<span class="sb-section-label">INPUT MODE</span>', unsafe_allow_html=True)
_input_mode = st.sidebar.segmented_control(
    "Input Mode", options=["Amount", "Weight %"], default="Amount",
    key="input_mode_seg", label_visibility="collapsed",
)
input_mode = _input_mode or "Amount"

if input_mode == "Amount":
    _currency = st.sidebar.segmented_control(
        "Currency", options=["₪ ILS", "$ USD", "€ EUR"], default="$ USD",
        key="currency_seg", label_visibility="collapsed",
    )
    currency_symbol = (_currency or "$ USD").split(" ")[0]
else:
    currency_symbol = "%"

if "holdings_rows" not in st.session_state:
    st.session_state.holdings_rows = [{"ticker": "", "value": 0.0, "name": ""}]

# Holdings section header
_n_filled = len([r for r in st.session_state.holdings_rows if r["ticker"]])
st.sidebar.markdown(
    f'<div class="sb-holdings-header">'
    f'<span class="label">HOLDINGS · {_n_filled}</span>'
    f'</div>',
    unsafe_allow_html=True,
)

# Render individual holding cards
for i, row in enumerate(st.session_state.holdings_rows):
    ticker = row.get("ticker", "")

    if not ticker:
        # Single search box — results appear as suggestion buttons below
        query = st.sidebar.text_input(
            f"Search {i+1}",
            placeholder="Search: Apple, AAPL, SPY...",
            key=f"search_{i}",
            label_visibility="collapsed",
        )
        if query and len(query) >= 2:
            results = _search_assets(query)
            if results:
                for r in results:
                    btn_label = f"{r['name']}  ({r['symbol']})"
                    if st.sidebar.button(btn_label, key=f"pick_{i}_{r['symbol']}", use_container_width=True):
                        st.session_state.holdings_rows[i]["ticker"] = r["symbol"]
                        st.session_state.holdings_rows[i]["name"] = r["name"]
                        if f"search_{i}" in st.session_state:
                            del st.session_state[f"search_{i}"]
                        st.rerun()
            else:
                st.sidebar.caption("No results — try a different name or ticker")
    else:
        # Holding card visual
        total_val = sum(r["value"] for r in st.session_state.holdings_rows if r["value"] > 0)
        pct = (row["value"] / total_val * 100) if total_val > 0 else 0
        color = _ticker_color(ticker)
        abbr = ticker.replace("^", "").replace(".", "")[:4].upper()
        company = row.get("name") or TICKER_TO_NAME.get(ticker, "")

        st.sidebar.markdown(
            f'<div class="holding-card">'
            f'  <div class="holding-top">'
            f'    <div class="holding-badge" style="background:{color}">{abbr}</div>'
            f'    <div>'
            f'      <div class="holding-ticker">{ticker}</div>'
            f'      <div class="holding-company">{company}</div>'
            f'    </div>'
            f'  </div>'
            f'  <div class="holding-pct-row"><span class="holding-pct">{pct:.1f}% of portfolio</span></div>'
            f'  <div class="holding-bar-track">'
            f'    <div class="holding-bar-fill" style="width:{min(pct,100):.1f}%;background:{color}"></div>'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Amount / weight input — value=None shows empty field instead of 0.00
    if input_mode == "Amount":
        _init = None if row["value"] == 0.0 else row["value"]
        _raw = st.sidebar.number_input(
            f"Amount {currency_symbol}",
            min_value=0.0,
            value=_init,
            placeholder="Enter amount...",
            key=f"value_{i}",
            label_visibility="collapsed",
        )
        st.session_state.holdings_rows[i]["value"] = float(_raw) if _raw is not None else 0.0
    else:
        _init_w = None if row["value"] == 0.0 else row["value"]
        _raw_w = st.sidebar.number_input(
            "Weight %",
            min_value=0.0,
            max_value=100.0,
            value=_init_w,
            placeholder="Enter weight %...",
            key=f"value_{i}",
            label_visibility="collapsed",
        )
        st.session_state.holdings_rows[i]["value"] = float(_raw_w) if _raw_w is not None else 0.0

    col_rm, col_ch = st.sidebar.columns([1, 1])
    if col_rm.button("Remove", key=f"rm_{i}"):
        st.session_state.holdings_rows.pop(i)
        st.rerun()
    if ticker and col_ch.button("Change", key=f"change_{i}"):
        st.session_state.holdings_rows[i]["ticker"] = ""
        st.session_state.holdings_rows[i]["name"] = ""
        if f"search_{i}" in st.session_state:
            del st.session_state[f"search_{i}"]
        st.rerun()

    st.sidebar.markdown('<hr style="margin:6px 0;border-color:rgba(255,255,255,0.06)">', unsafe_allow_html=True)

if st.sidebar.button("+ Add asset"):
    st.session_state.holdings_rows.append({"ticker": "", "value": 0.0, "name": ""})
    st.rerun()

_total = sum(r["value"] for r in st.session_state.holdings_rows)
if input_mode == "Amount":
    st.sidebar.caption(f"Total: {currency_symbol}{_total:,.2f}")
else:
    _col = "red" if abs(_total - 100) > 0.5 and _total > 0 else "#7A8AA0"
    st.sidebar.markdown(f'<small style="color:{_col}">Total weight: {_total:.1f}%</small>', unsafe_allow_html=True)

st.sidebar.markdown("<br>", unsafe_allow_html=True)
analyze = st.sidebar.button("Analyze Portfolio", type="primary")

# ── Computation ───────────────────────────────────────────────────────────────
if analyze:
    filled_rows = [
        r for r in st.session_state.holdings_rows
        if r["ticker"].strip() != "" and r["value"] > 0
    ]

    if not filled_rows:
        st.error("Please add at least one asset with a value.")
    else:
        if input_mode == "Amount":
            total_invested = sum(r["value"] for r in filled_rows)
            holdings = [
                {"ticker": r["ticker"], "weight": r["value"] / total_invested}
                for r in filled_rows
            ]
        else:
            total_w = sum(r["value"] for r in filled_rows)
            if abs(total_w - 100.0) > 0.1:
                st.error(f"Weights must sum to 100%. Currently: {total_w:.1f}%")
                st.stop()
            holdings = [
                {"ticker": r["ticker"], "weight": r["value"] / 100}
                for r in filled_rows
            ]

        with st.spinner(random.choice(_ANALYSIS_MSGS)):
            prices = build_portfolio(holdings, period=period)
            returns = calculate_returns(prices)
            summary = get_portfolio_summary(returns, benchmark=benchmark_ticker)
            portfolio_metrics = calculate_portfolio_metrics(
                returns, holdings, risk_free_rate=summary["risk_free_rate"]
            )

        st.session_state["analysis"] = {
            "returns": returns,
            "holdings": holdings,
            "summary": summary,
            "portfolio_metrics": portfolio_metrics,
            "period": period,
            "total_invested": _total if input_mode == "Amount" else None,
            "currency_symbol": currency_symbol if input_mode == "Amount" else None,
            "benchmark_ticker": benchmark_ticker,
        }
        st.session_state["app_state"] = "dashboard"
        st.session_state.pop("opt_result", None)
        st.session_state.pop("opt_frontier", None)
        st.session_state.pop("cum_ret_lines", None)

# ── Display ───────────────────────────────────────────────────────────────────
if "analysis" not in st.session_state:
    st.session_state["app_state"] = "landing"
    st.rerun()

else:
    _d = st.session_state["analysis"]
    returns = _d["returns"]
    holdings = _d["holdings"]
    summary = _d["summary"]
    portfolio_metrics = _d["portfolio_metrics"]
    period_used = _d.get("period", "1y")
    total_invested = _d.get("total_invested")
    csym = _d.get("currency_symbol", "$")
    benchmark_ticker = _d.get("benchmark_ticker", benchmark_ticker)

    # ── Dashboard header ──────────────────────────────────────────
    _dh_back, _dh_title, _dh_actions = st.columns([1, 6, 1])
    with _dh_back:
        if st.button("← Home", key="dash_home"):
            st.session_state["app_state"] = "landing"
            st.session_state.pop("analysis", None)
            st.rerun()
    st.markdown(f"""
<div class="dash-breadcrumb">Workspace / Personal / <span>Long-term Growth</span></div>
<div class="dash-header-row">
  <div class="dash-title">Dashboard</div>
</div>
""", unsafe_allow_html=True)

    # ── Portfolio value card ──────────────────────────────────────
    pm = portfolio_metrics
    annual_ret = pm.get("annual_return", 0.0)
    import math
    has_metrics = not math.isnan(annual_ret)

    _DASH_PERIODS   = ["1M", "6M", "YTD", "1Y", "2Y", "ALL"]
    _DASH_PERIOD_YF = {"1M": "1mo", "6M": "6mo", "YTD": "ytd", "1Y": "1y", "2Y": "2y", "ALL": "max"}
    _YF_TO_DASH     = {"1mo": "1M", "6mo": "6M", "ytd": "YTD", "1y": "1Y", "2y": "2Y", "5y": "2Y", "max": "ALL"}
    _active_dash    = _YF_TO_DASH.get(period_used, "1Y")

    # Period selector — compact segmented control, right-aligned
    _sp, _pr = st.columns([2, 3])
    with _pr:
        _new_dash = st.segmented_control(
            "Period", options=_DASH_PERIODS, default=_active_dash,
            key="dash_seg", label_visibility="collapsed",
        )
        if _new_dash and _DASH_PERIOD_YF.get(_new_dash) != period_used:
            _np = _DASH_PERIOD_YF[_new_dash]
            with st.spinner("Updating..."):
                _np_prices  = build_portfolio(holdings, period=_np)
                _np_returns = calculate_returns(_np_prices)
                _np_summary = get_portfolio_summary(_np_returns, benchmark=benchmark_ticker)
                _np_pm      = calculate_portfolio_metrics(_np_returns, holdings, risk_free_rate=_np_summary["risk_free_rate"])
            st.session_state["analysis"].update({
                "returns": _np_returns, "summary": _np_summary,
                "portfolio_metrics": _np_pm, "period": _np,
            })
            st.session_state.pop("cum_ret_lines", None)
            st.rerun()

    _period_label_map = {"5d": "last week", "1mo": "last month", "6mo": "6 months ago",
                         "ytd": "at the start of the year", "1y": "a year ago",
                         "2y": "2 years ago", "max": "at the start"}

    if total_invested and total_invested > 0 and has_metrics:
        cur_val = total_invested
        prev_val = cur_val / (1 + annual_ret) if (1 + annual_ret) != 0 else cur_val
        change_amt = cur_val - prev_val
        change_pct = annual_ret * 100
        pos = change_amt >= 0
        badge_cls = "pv-badge" if pos else "pv-badge neg"
        sign = "+" if pos else ""

        ils_rate = None
        if "USD/ILS" in tickers_data and tickers_data["USD/ILS"][0]:
            ils_rate = tickers_data["USD/ILS"][0]

        compare_text = f"vs. {csym}{prev_val:,.0f} {_period_label_map.get(period_used, 'a year ago')}"
        if ils_rate and csym == "$":
            ils_val = cur_val * ils_rate
            compare_text += f" &nbsp;·&nbsp; ≈ ₪{ils_val:,.0f}"

        int_part = f"{int(cur_val):,}"
        dec_part = f"{cur_val % 1:.2f}"[1:]

        _next_val = cur_val * (1 + annual_ret)
        if pos:
            _motivation = (f"If markets behave the same way next year <em style='color:#9AABB8;font-weight:400'>(they won't!)</em>, "
                           f"your portfolio could reach <strong>{csym}{_next_val:,.0f}</strong> — "
                           f"that's another +{change_pct:.1f}%.")
            _mot_color = "#16A34A"
        else:
            _motivation = (f"Markets have rough patches. If things recover next year at the same rate, "
                           f"you'd be back at <strong>{csym}{_next_val:,.0f}</strong>.")
            _mot_color = "#D97706"

        st.markdown(f"""
<div class="pv-card">
  <div class="pv-label">
    PORTFOLIO VALUE &nbsp;·&nbsp; {csym.replace("$","USD").replace("₪","ILS").replace("€","EUR")} VALUE
  </div>
  <div class="pv-amount">{csym}{int_part}<span class="cents">{dec_part}</span></div>
  <div class="pv-change-row">
    <span class="{badge_cls}">{sign}{csym}{abs(change_amt):,.0f} &nbsp;·&nbsp; {sign}{change_pct:.1f}%</span>
    <span class="pv-compare">{compare_text}</span>
  </div>
  <div style="padding-top:14px;border-top:1px solid #F0F4F8;font-size:14px;color:{_mot_color};font-weight:500;line-height:1.5">
    {_motivation}
  </div>
</div>
""", unsafe_allow_html=True)

    elif has_metrics:
        annual_ret = pm.get("annual_return", 0.0)
        pos = annual_ret >= 0
        sign = "+" if pos else ""
        _period_desc = _period_label_map.get(period_used, "a year ago")
        if pos:
            _motivation = (f"If markets behave the same way next year <em style='color:#9AABB8;font-weight:400'>(they won't!)</em>, "
                           f"this portfolio could return another +{annual_ret*100:.1f}%.")
            _mot_color = "#16A34A"
        else:
            _motivation = (f"Markets have rough patches. A recovery could bring "
                           f"this portfolio back up by {abs(annual_ret*100):.1f}%.")
            _mot_color = "#D97706"
        st.markdown(f"""
<div class="pv-card">
  <div class="pv-label">PORTFOLIO PERFORMANCE &nbsp;·&nbsp; {_active_dash}</div>
  <div class="pv-amount" style="font-size:40px">{sign}{annual_ret*100:.1f}<span class="cents">%</span></div>
  <div class="pv-change-row">
    <span class="{'pv-badge' if pos else 'pv-badge neg'}">Annual Return</span>
    <span class="pv-compare">Based on {len(holdings)} assets</span>
  </div>
  <div style="padding-top:14px;border-top:1px solid #F0F4F8;font-size:14px;color:{_mot_color};font-weight:500">
    {_motivation}
  </div>
</div>
""", unsafe_allow_html=True)

    st.divider()

    # ── Cumulative Returns (second after dashboard) ───────────────
    st.markdown('<div class="section-head">Cumulative Returns <span class="sub">How $10,000 grows over time</span></div>', unsafe_allow_html=True)

    _cum_all = (1 + returns).cumprod() * 10000
    _w_map   = {h["ticker"]: h["weight"] for h in holdings}
    _port_daily_r = sum(returns[tk] * _w_map[tk] for tk in returns.columns if tk in _w_map)
    _port_cum = (1 + _port_daily_r).cumprod() * 10000
    _all_lines = list(_cum_all.columns) + ["My Portfolio"]

    if "cum_ret_lines" not in st.session_state:
        st.session_state["cum_ret_lines"] = _all_lines

    _chart_slot = st.empty()

    _sel_lines = st.multiselect(
        "Visible lines", options=_all_lines, key="cum_ret_lines",
        label_visibility="collapsed",
    )

    _fig_r = go.Figure()
    for _tk in _cum_all.columns:
        if _tk in _sel_lines:
            _fig_r.add_trace(go.Scatter(
                x=_cum_all.index, y=_cum_all[_tk].round(2), name=_tk, mode="lines",
                hovertemplate=f"<b>{_tk}</b><br>%{{x|%b %d, %Y}}: $%{{y:,.0f}}<extra></extra>",
            ))
    if "My Portfolio" in _sel_lines:
        _fig_r.add_trace(go.Scatter(
            x=_port_cum.index, y=_port_cum.round(2), name="My Portfolio",
            mode="lines", line=dict(color="#2563EB", width=3),
            hovertemplate="<b>My Portfolio</b><br>%{x|%b %d, %Y}: $%{y:,.0f}<extra></extra>",
        ))
    _fig_r.add_hline(y=10000, line_dash="dash", line_color="rgba(255,255,255,0.15)",
                     annotation_text="Starting value", annotation_font_color="#7A8AA0")
    _fig_r.update_layout(**_chart_layout(
        xaxis_title="Date", yaxis_title="Value ($)", hovermode="closest",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(color="#B7C2D2")),
        height=440,
    ))
    _chart_slot.plotly_chart(_fig_r, use_container_width=True)

    st.divider()

    # ── Risk Metrics ──────────────────────────────────────────────
    st.markdown("""
<div class="rm-header">
  <span class="rm-header-left">RISK METRICS &nbsp;·&nbsp; COMBINED PORTFOLIO</span>
  <span class="rm-header-right">Computed over last period of daily returns</span>
</div>
""", unsafe_allow_html=True)

    if has_metrics:
        sharpe_v  = pm["sharpe"]
        vol_v     = pm["volatility"]
        mdd_v     = pm["max_drawdown"]
        var_v     = pm["var_95"]

        # compute average beta across assets
        beta_v = float(summary["beta"].mean()) if not summary["beta"].empty else 1.0

        row1 = st.columns(3, gap="medium")
        row2 = st.columns(2, gap="medium")

        # Sharpe
        bl, bc = _badge("sharpe", sharpe_v)
        fc = _filled_count("sharpe", sharpe_v)
        with row1[0]:
            st.markdown(_rm_card(
                "SHARPE RATIO",
                f"{sharpe_v:.2f}",
                bl, bc,
                "return per unit of risk",
                _segs(bc, fc),
                explain_sharpe(sharpe_v),
            ), unsafe_allow_html=True)

        # Volatility
        bl, bc = _badge("volatility", vol_v)
        fc = _filled_count("volatility", vol_v)
        with row1[1]:
            st.markdown(_rm_card(
                "VOLATILITY",
                f'{vol_v*100:.1f}<span class="unit">%</span>',
                bl, bc,
                "annualized",
                _segs(bc, fc),
                explain_volatility(vol_v),
            ), unsafe_allow_html=True)

        # Beta
        bl, bc = _badge("beta", beta_v)
        fc = _filled_count("beta", beta_v)
        with row1[2]:
            bench_name = benchmark_ticker.replace("^TA125.TA", "TA-125").replace("SPY", "SPY")
            st.markdown(_rm_card(
                f"BETA VS {bench_name}",
                f"{beta_v:.2f}",
                bl, bc,
                f"vs. {bench_name}",
                _segs("blue", fc),
                explain_beta(beta_v),
            ), unsafe_allow_html=True)

        # Max Drawdown
        bl, bc = _badge("max_drawdown", mdd_v)
        fc = _filled_count("max_drawdown", mdd_v)
        with row2[0]:
            st.markdown(_rm_card(
                "MAX DRAWDOWN",
                f'{mdd_v*100:.1f}<span class="unit">%</span>',
                bl, bc,
                "worst peak-to-trough",
                _segs(bc, fc),
                explain_max_drawdown(mdd_v),
            ), unsafe_allow_html=True)

        # VaR
        bl, bc = _badge("var", var_v)
        fc = _filled_count("var", var_v)
        with row2[1]:
            if total_invested and total_invested > 0:
                daily_loss = f"≈ {csym}{abs(var_v * total_invested):,.0f} / day"
            else:
                daily_loss = f"{var_v*100:.2f}% daily"
            st.markdown(_rm_card(
                "DAILY VAR · 95%",
                f'{var_v*100:.1f}<span class="unit">%</span>',
                bl, bc,
                daily_loss,
                _segs(bc, fc),
                "On 95% of days, losses won't exceed this amount.",
            ), unsafe_allow_html=True)
    else:
        st.warning("Could not calculate metrics — one or more assets may have insufficient data.")

    st.divider()

    # ── Per-asset breakdown ───────────────────────────────────────
    st.markdown('<div class="section-head">Per Asset Breakdown</div>', unsafe_allow_html=True)

    for ticker in returns.columns:
        with st.expander(f"{ticker}"):
            _ac1, _ac2, _ac3, _ac4, _ac5 = st.columns(5, gap="small")
            _asset_metrics = [
                ("VOLATILITY",    f"{summary['volatility'][ticker]*100:.1f}%",  explain_volatility(summary['volatility'][ticker])),
                ("SHARPE",        f"{summary['sharpe'][ticker]:.2f}",            explain_sharpe(summary['sharpe'][ticker])),
                ("BETA",          f"{summary['beta'][ticker]:.2f}",              explain_beta(summary['beta'][ticker])),
                ("MAX DRAWDOWN",  f"{summary['max_drawdown'][ticker]*100:.1f}%", explain_max_drawdown(summary['max_drawdown'][ticker])),
                ("DAILY VAR 95%", f"{summary['var_95'][ticker]*100:.2f}%",       explain_var(summary['var_95'][ticker])),
            ]
            for _col, (_lbl, _val, _exp) in zip([_ac1, _ac2, _ac3, _ac4, _ac5], _asset_metrics):
                with _col:
                    st.markdown(f"""
<div class="asset-metric-card">
  <div class="asset-metric-label">{_lbl}</div>
  <div class="asset-metric-value">{_val}</div>
  <div class="asset-metric-explain">{_exp}</div>
</div>""", unsafe_allow_html=True)

    st.divider()

    # ── Correlation heatmap ───────────────────────────────────────
    st.markdown('<div class="section-head">Correlation Heatmap <span class="sub">Lower = better diversification</span></div>', unsafe_allow_html=True)
    _hm_scale = [[0.0, "#3B1A1A"], [0.25, "#7C2D2D"], [0.5, "#1E293B"],
                 [0.75, "#1D4ED8"], [1.0, "#93C5FD"]]
    fig_hm = px.imshow(
        summary['correlation'].round(2), text_auto=".2f",
        color_continuous_scale=_hm_scale, zmin=-1, zmax=1, aspect="auto",
    )
    fig_hm.update_traces(
        textfont=dict(color="#FFFFFF", size=13, family="JetBrains Mono"),
    )
    fig_hm.update_layout(**_chart_layout(
        height=max(300, len(returns.columns) * 70),
        coloraxis_colorbar=dict(
            tickfont=dict(color="#7A8AA0", size=11),
            title=dict(text="r", font=dict(color="#7A8AA0")),
            thickness=14,
        ),
        margin=dict(l=8, r=8, t=20, b=8),
    ))
    st.plotly_chart(fig_hm, use_container_width=True)

    st.divider()

    # ── Sector exposure ───────────────────────────────────────────
    st.markdown('<div class="section-head">Sector Exposure <span class="sub">What industries you are invested in</span></div>', unsafe_allow_html=True)
    with st.spinner(random.choice(_SECTOR_MSGS)):
        sector_data = get_sector_exposure(holdings)
        st.session_state["sector_data"] = sector_data

    if sector_data:
        labels = list(sector_data.keys())
        values = [round(v * 100, 1) for v in sector_data.values()]
        colors = []
        set3 = px.colors.qualitative.Set3
        ci = 0
        for lbl in labels:
            if lbl == "Unknown":
                colors.append("#D3D3D3")
            else:
                colors.append(set3[ci % len(set3)]); ci += 1

        fig_sec = px.pie(names=labels, values=values, hole=0.4, color_discrete_sequence=colors)
        fig_sec.update_traces(
            textposition="inside", textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>%{value:.1f}%<extra></extra>",
        )
        fig_sec.update_layout(**_chart_layout(height=440, showlegend=True,
                                              legend=dict(font=dict(color="#B7C2D2"))))
        st.plotly_chart(fig_sec, use_container_width=True)

        unk = sector_data.get("Unknown", 0)
        if unk > 0:
            st.info(
                f"About the Unknown slice ({unk*100:.1f}%): ETFs, bond funds, and indices "
                f"hold hundreds of assets across many industries and can't be broken into a single sector."
            )

    st.divider()

    # ── Efficient Frontier ────────────────────────────────────────
    st.markdown('<div class="section-head">Efficient Frontier Explorer</div>', unsafe_allow_html=True)

    if len(holdings) < 2:
        st.info("Add at least 2 assets to explore the efficient frontier.")
    else:
        if "opt_frontier" not in st.session_state:
            with st.spinner(random.choice(_FRONTIER_MSGS)):
                try:
                    st.session_state["opt_frontier"] = get_efficient_frontier(returns, n_points=500)
                    st.session_state["opt_frontier_line"] = get_efficient_frontier_line(returns, n_points=40)
                except Exception as e:
                    st.error(f"Could not compute efficient frontier: {e}")

        if "opt_frontier" in st.session_state:
            frontier_df  = st.session_state["opt_frontier"]
            frontier_line_df = st.session_state.get("opt_frontier_line", pd.DataFrame())

            st.markdown(
                "**Each dot is a possible allocation. Hover to explore. Click to select.**  \n"
                "Move right → more risk.  Move up → more return.  Yellow = best Sharpe."
            )

            hover_random = []
            for _, row_ in frontier_df.iterrows():
                wl = "<br>".join(f"  {t}: {row_[t]*100:.0f}%" for t in returns.columns)
                hover_random.append(
                    f"<b>Return:</b> {row_['return']*100:.1f}%<br>"
                    f"<b>Volatility:</b> {row_['volatility']*100:.1f}%<br>"
                    f"<b>Sharpe:</b> {row_['sharpe']:.2f}<br>{wl}"
                )

            fig_ef = go.Figure()
            fig_ef.add_trace(go.Scatter(
                x=frontier_df["volatility"] * 100, y=frontier_df["return"] * 100,
                mode="markers",
                marker=dict(color=frontier_df["sharpe"], colorscale="Plasma", size=6,
                            opacity=0.65, colorbar=dict(title="Sharpe", thickness=12), showscale=True),
                name="Possible Portfolios", hovertext=hover_random, hoverinfo="text",
            ))

            if not frontier_line_df.empty:
                fl = frontier_line_df.sort_values("volatility").reset_index(drop=True)
                hover_line = []
                for _, row_ in fl.iterrows():
                    wl = "<br>".join(f"  {t}: {row_.get(t,0)*100:.0f}%" for t in returns.columns)
                    hover_line.append(
                        f"<b>Efficient Frontier</b><br>"
                        f"<b>Return:</b> {row_['return']*100:.1f}%<br>"
                        f"<b>Volatility:</b> {row_['volatility']*100:.1f}%<br>"
                        f"<b>Sharpe:</b> {row_['sharpe']:.2f}<br>{wl}"
                    )
                fig_ef.add_trace(go.Scatter(
                    x=fl["volatility"] * 100, y=fl["return"] * 100,
                    mode="lines+markers", line=dict(color="white", width=2.5),
                    marker=dict(size=5, color="white"), name="Efficient Frontier",
                    hovertext=hover_line, hoverinfo="text",
                ))

            fig_ef.add_trace(go.Scatter(
                x=[pm["volatility"] * 100], y=[pm["annual_return"] * 100],
                mode="markers+text",
                marker=dict(symbol="star", size=22, color="#2563EB", line=dict(color="white", width=1.5)),
                text=["You"], textposition="top center", name="Your Portfolio",
                hovertext=(
                    f"<b>Your Portfolio</b><br>"
                    f"Return: {pm['annual_return']*100:.1f}%<br>"
                    f"Volatility: {pm['volatility']*100:.1f}%<br>"
                    f"Sharpe: {pm['sharpe']:.2f}"
                ),
                hoverinfo="text",
            ))

            fig_ef.update_layout(**_chart_layout(
                xaxis_title="Volatility (%) — Risk →",
                yaxis_title="Expected Return (%) ↑",
                height=520,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                            font=dict(color="#B7C2D2")),
            ))

            event = st.plotly_chart(
                fig_ef, use_container_width=True,
                on_select="rerun", selection_mode="points", key="frontier_chart",
            )

            if event.selection and event.selection.points:
                pt = event.selection.points[0]
                curve_num = pt.get("curve_number", 0)
                pt_idx = pt.get("point_index", 0)

                if curve_num == 0 and pt_idx < len(frontier_df):
                    _row = frontier_df.iloc[pt_idx]; src = "Random Portfolio"
                elif curve_num == 1 and not frontier_line_df.empty:
                    fl_s = frontier_line_df.sort_values("volatility").reset_index(drop=True)
                    _row = fl_s.iloc[pt_idx] if pt_idx < len(fl_s) else None; src = "Efficient Frontier"
                else:
                    _row = None; src = ""

                if _row is not None:
                    st.session_state["frontier_selected"] = {t: float(_row.get(t, 0)) for t in returns.columns}
                    st.session_state["frontier_selected_stats"] = {
                        "return": float(_row["return"]),
                        "volatility": float(_row["volatility"]),
                        "sharpe": float(_row["sharpe"]),
                        "source": src,
                    }

            if "frontier_selected" in st.session_state:
                sel_w = st.session_state["frontier_selected"]
                sel_s = st.session_state["frontier_selected_stats"]
                st.markdown("---")
                st.markdown(f"#### Selected Portfolio — *{sel_s['source']}*")

                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("Expected Return", f"{sel_s['return']*100:.1f}%",
                              delta=f"{(sel_s['return']-pm['annual_return'])*100:+.1f}% vs current")
                with c2:
                    st.metric("Volatility", f"{sel_s['volatility']*100:.1f}%",
                              delta=f"{(sel_s['volatility']-pm['volatility'])*100:+.1f}% vs current",
                              delta_color="inverse")
                with c3:
                    st.metric("Sharpe Ratio", round(sel_s["sharpe"], 2),
                              delta=f"{sel_s['sharpe']-pm['sharpe']:+.2f} vs current")

                st.markdown("**Weights:**")
                wcols = st.columns(len(sel_w))
                for col, (tk, wt) in zip(wcols, sel_w.items()):
                    col.metric(tk, f"{wt*100:.1f}%")

                cur_sh = round(pm["sharpe"], 2); sel_sh = round(sel_s["sharpe"], 2)
                if sel_sh > cur_sh:
                    st.info(f"This allocation has a better Sharpe ratio ({sel_sh} vs your {cur_sh}). Weights are bounded 5-40% per asset.")
                elif sel_sh < cur_sh:
                    st.info(f"This allocation has a lower Sharpe ratio ({sel_sh} vs your {cur_sh}). May suit a specific risk target.")
                else:
                    st.info(f"Nearly the same Sharpe ratio ({cur_sh}). Weights bounded 5-40%.")

                if st.button("Analyze this allocation", type="primary"):
                    sel_holdings = [{"ticker": t, "weight": w} for t, w in sel_w.items() if w > 0.001]
                    new_pm = calculate_portfolio_metrics(returns, sel_holdings, risk_free_rate=summary["risk_free_rate"])
                    st.session_state["analysis"]["holdings"] = sel_holdings
                    st.session_state["analysis"]["portfolio_metrics"] = new_pm
                    st.session_state.pop("frontier_selected", None)
                    st.session_state.pop("frontier_selected_stats", None)
                    st.rerun()

    st.divider()

    # ── Backtest ──────────────────────────────────────────────────
    st.markdown('<div class="section-head">Backtest <span class="sub">Historical simulation with monthly rebalancing</span></div>', unsafe_allow_html=True)

    bt_period_label = st.selectbox(
        "Backtest period", options=["1 year", "3 years", "5 years"], index=2, key="bt_period_select"
    )
    _pmap = {"1 year": "1y", "3 years": "3y", "5 years": "5y"}
    bt_yf_period = _pmap[bt_period_label]

    if st.button("Run Backtest", type="primary", key="run_bt_btn"):
        with st.spinner(random.choice(_BACKTEST_MSGS)):
            try:
                bt_result = run_backtest(holdings, period=bt_yf_period)
                st.session_state["backtest"] = bt_result
                st.session_state["backtest_label"] = bt_period_label
            except Exception as e:
                st.error(f"Backtest failed: {e}")

    if "backtest" in st.session_state:
        bt = st.session_state["backtest"]
        saved_label = st.session_state.get("backtest_label", "5 years")

        fig_bt = go.Figure()
        fig_bt.add_trace(go.Scatter(
            x=bt["portfolio_value"].index, y=bt["portfolio_value"].round(2),
            name="My Portfolio", mode="lines", line=dict(color="#2563EB", width=2.5),
            hovertemplate="<b>My Portfolio</b><br>%{x|%b %d, %Y}: $%{y:,.0f}<extra></extra>",
        ))
        if bt["spy"] is not None:
            fig_bt.add_trace(go.Scatter(
                x=bt["spy"]["portfolio_value"].index, y=bt["spy"]["portfolio_value"].round(2),
                name="SPY", mode="lines", line=dict(color="#F97316", width=2, dash="dash"),
                hovertemplate="<b>SPY</b><br>%{x|%b %d, %Y}: $%{y:,.0f}<extra></extra>",
            ))
        fig_bt.add_hline(y=10000, line_dash="dot", line_color="rgba(255,255,255,0.2)",
                         annotation_text="$10,000 start", annotation_font_color="#7A8AA0")
        fig_bt.update_layout(**_chart_layout(
            xaxis_title="Date", yaxis_title="Portfolio Value ($)", hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                        font=dict(color="#B7C2D2")),
            height=440,
        ))
        st.plotly_chart(fig_bt, use_container_width=True)

        spy = bt["spy"]
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            tr_d = f"{(bt['total_return']-spy['total_return'])*100:+.1f}% vs SPY" if spy else None
            st.metric("Total Return", f"{bt['total_return']*100:.1f}%", delta=tr_d)
        with c2:
            ar_d = f"{(bt['annual_return']-spy['annual_return'])*100:+.1f}% vs SPY" if spy else None
            st.metric("Annual Return (CAGR)", f"{bt['annual_return']*100:.1f}%", delta=ar_d)
        with c3:
            st.metric("Max Drawdown", f"{bt['max_drawdown']*100:.1f}%")
        with c4:
            st.metric("Sharpe Ratio", round(bt["sharpe"], 2))

        monthly = bt["monthly_returns"]
        bar_colors = ["#22C55E" if r > 0 else "#EF4444" for r in monthly]
        fig_m = go.Figure()
        fig_m.add_trace(go.Bar(
            x=monthly.index, y=(monthly * 100).round(2),
            marker_color=bar_colors, name="Monthly Return",
            hovertemplate="%{x|%b %Y}: %{y:.2f}%<extra></extra>",
        ))
        fig_m.add_hline(y=0, line_color="rgba(255,255,255,0.12)", line_width=1)
        fig_m.update_layout(**_chart_layout(
            xaxis_title="Month", yaxis_title="Return (%)", height=320, showlegend=False,
        ))
        st.plotly_chart(fig_m, use_container_width=True)

        spy_total_str = f"{spy['total_return']*100:.1f}%" if spy else "N/A"
        vs_word = "outperformed" if spy and bt["total_return"] > spy["total_return"] else "underperformed"
        st.info(
            f"Over **{saved_label}**, your portfolio returned **{bt['total_return']*100:.1f}%** "
            f"vs SPY's **{spy_total_str}** — you **{vs_word}** the benchmark.  \n"
            f"Best day: +{bt['best_day']*100:.2f}%  |  "
            f"Worst day: {bt['worst_day']*100:.2f}%  |  "
            f"{bt['months_positive']*100:.0f}% of months were positive."
        )

    st.divider()

    # ── AI Portfolio Advisor ──────────────────────────────────────
    st.markdown('<div class="section-head">AI Portfolio Advisor <span class="sub">Personalised analysis powered by Claude</span></div>', unsafe_allow_html=True)

    _api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    _key_missing = not _api_key or _api_key.startswith("sk-ant-YOUR") or _api_key == "placeholder"

    if _key_missing:
        st.info("AI Advisor is disabled — add your Anthropic API key to `.streamlit/secrets.toml` to enable it.")
    else:
        followup_text = st.text_input(
            "Follow-up question (optional)",
            placeholder="e.g. Should I add bonds? How do I reduce tech exposure?",
            key="ai_followup_input",
        )
        _ca, _cb = st.columns([1, 1])
        with _ca:
            run_ai_analysis = st.button("Get AI Analysis", type="primary", key="ai_run_btn")
        with _cb:
            run_ai_followup = st.button("Ask Follow-up", key="ai_followup_btn")

        def _build_ctx():
            lines = ["=== PORTFOLIO HOLDINGS ==="]
            for h in holdings:
                lines.append(f"  {h['ticker']}: {h['weight']*100:.1f}%")
            lines += [
                "\n=== PORTFOLIO METRICS ===",
                f"  Annual Return:  {pm['annual_return']*100:.1f}%",
                f"  Volatility:     {pm['volatility']*100:.1f}%",
                f"  Sharpe Ratio:   {pm['sharpe']:.2f}",
                f"  Max Drawdown:   {pm['max_drawdown']*100:.1f}%",
                f"  Daily VaR 95%:  {pm['var_95']*100:.2f}%",
                f"  Risk-Free Rate: {summary['risk_free_rate']*100:.2f}%",
                "\n=== PER-ASSET METRICS ===",
            ]
            for tk in returns.columns:
                lines.append(
                    f"  {tk}: Sharpe {summary['sharpe'][tk]:.2f}, "
                    f"Vol {summary['volatility'][tk]*100:.1f}%, "
                    f"Beta {summary['beta'][tk]:.2f}, "
                    f"MaxDD {summary['max_drawdown'][tk]*100:.1f}%"
                )
            if "sector_data" in st.session_state:
                lines.append("\n=== SECTOR EXPOSURE ===")
                for sec, w in st.session_state["sector_data"].items():
                    lines.append(f"  {sec}: {w*100:.1f}%")
            if "backtest" in st.session_state:
                _bt = st.session_state["backtest"]
                _lbl = st.session_state.get("backtest_label", "")
                lines += [
                    f"\n=== BACKTEST RESULTS ({_lbl}) ===",
                    f"  Total Return: {_bt['total_return']*100:.1f}%",
                    f"  Annual Return: {_bt['annual_return']*100:.1f}%",
                    f"  Max Drawdown: {_bt['max_drawdown']*100:.1f}%",
                    f"  Sharpe: {_bt['sharpe']:.2f}",
                    f"  Best Day: +{_bt['best_day']*100:.2f}%",
                    f"  Worst Day: {_bt['worst_day']*100:.2f}%",
                    f"  Months Positive: {_bt['months_positive']*100:.0f}%",
                ]
                if _bt["spy"]:
                    lines.append(f"  SPY Total Return: {_bt['spy']['total_return']*100:.1f}%")
            return "\n".join(lines)

        _AI_SYSTEM = """You are a friendly, educational investment advisor for young investors aged 18-30.
Tone: honest, encouraging, clear. Explain simply — no jargon.
Never recommend specific stock picks or give direct buy/sell orders.
Focus on portfolio construction, diversification, and risk management principles."""

        _PROMPT_TMPL = """{context}

Please analyse this portfolio and provide:
**1. Summary** (2-3 sentences) — main strengths and weaknesses.
**2. Top Risks** (2-3 bullets) — biggest risks to understand.
**3. Actionable Recommendations** (2-3 bullets) — specific, practical steps.
**4. Young Investor Rating: X/10** — rate for an 18-30 year old with 1-2 sentence explanation."""

        if run_ai_analysis or run_ai_followup:
            try:
                _client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
                _ctx = _build_ctx()
                if run_ai_followup and followup_text.strip():
                    _prev = st.session_state.get("ai_response", "")
                    _prompt = (
                        f"{_ctx}\n\nPrevious analysis:\n{_prev}\n\nFollow-up: {followup_text.strip()}"
                        if _prev else f"{_ctx}\n\nQuestion: {followup_text.strip()}"
                    )
                else:
                    _prompt = _PROMPT_TMPL.format(context=_ctx)

                with st.spinner("Claude is analysing your portfolio..."):
                    _resp = _client.messages.create(
                        model="claude-sonnet-4-6",
                        max_tokens=1024,
                        system=[{"type": "text", "text": _AI_SYSTEM,
                                 "cache_control": {"type": "ephemeral"}}],
                        messages=[{"role": "user", "content": _prompt}],
                    )
                    st.session_state["ai_response"] = _resp.content[0].text
            except anthropic.AuthenticationError:
                st.error("Invalid API key — check `.streamlit/secrets.toml`.")
            except Exception as _e:
                st.error(f"AI analysis failed: {_e}")

        if "ai_response" in st.session_state:
            st.markdown(st.session_state["ai_response"])
