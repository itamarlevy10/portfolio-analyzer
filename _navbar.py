import streamlit as st
import yfinance as yf
import pytz
from datetime import datetime


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


def _ticker_html(name, val, chg):
    if val is None:
        return f'<span class="nav-tick"><span class="nt-name">{name}</span></span>'
    color = "#4ADE80" if chg >= 0 else "#F87171"
    sign = "+" if chg >= 0 else ""
    return (
        f'<span class="nav-tick">'
        f'<span class="nt-name">{name}</span>'
        f'<span class="nt-val">{val:,.2f}</span>'
        f'<span class="nt-chg" style="color:{color}">{sign}{chg:.2f}%</span>'
        f'</span>'
    )


def render_navbar():
    tickers_data = _fetch_tickers()
    market_open = _market_open()

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
.nav-brand {{
    display: flex; align-items: center; gap: 9px; min-width: 210px;
    text-decoration: none;
}}
.nav-brand:hover .nav-logo {{ background: #1d4ed8; }}
.nav-logo {{
    width: 30px; height: 30px; background: #2563EB; border-radius: 7px;
    display: flex; align-items: center; justify-content: center;
    transition: background 0.15s;
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
    font-size: 11.5px; font-weight: 500; padding: 4px 10px; border-radius: 20px;
    border: 1px solid; white-space: nowrap;
}}
.market-badge.open {{ color: #4ADE80; border-color: rgba(74,222,128,0.3); background: rgba(74,222,128,0.08); }}
.market-badge.closed {{ color: #F87171; border-color: rgba(248,113,113,0.3); background: rgba(248,113,113,0.08); }}
</style>
<div class="navbar">
    <a class="nav-brand" href="/" target="_self">
        <div class="nav-logo">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <polyline points="1,12 5,6 8,9 11,4 15,7"
                    stroke="white" stroke-width="1.8"
                    stroke-linecap="round" stroke-linejoin="round" fill="none"/>
            </svg>
        </div>
        <span class="nav-name">Portfolio Analyzer</span>
    </a>
    <div class="nav-tickers">{tickers_html}</div>
    <div class="nav-right">
        <span class="market-badge {market_class}">{market_label}</span>
    </div>
</div>
""", unsafe_allow_html=True)
