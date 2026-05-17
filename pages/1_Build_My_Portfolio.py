import streamlit as st
import anthropic
import json
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from _navbar import render_navbar

# hide sidebar entirely on this page
st.markdown("""
<style>
section[data-testid="stSidebar"] { display: none !important; }
button[data-testid="stSidebarCollapsedControl"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

render_navbar()

st.title("Build My Portfolio")
st.subheader("Answer a few questions and get a personalized AI-designed portfolio in seconds.")
st.divider()

# ── API Key Check ──────────────────────────────────────────────────────────────
_api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
_key_missing = not _api_key or _api_key.startswith("sk-ant-YOUR") or _api_key == "placeholder"

if _key_missing:
    st.error("🔑 API key missing — add your Anthropic API key to `.streamlit/secrets.toml` to use this feature.")
    st.stop()

# ── Questionnaire ──────────────────────────────────────────────────────────────
st.subheader("Tell us about yourself")

with st.form("build_form"):
    col_left, col_right = st.columns(2)

    with col_left:
        amount = st.number_input(
            "💰 How much do you want to invest?",
            min_value=100,
            max_value=10_000_000,
            value=10_000,
            step=500,
            help="The total amount you plan to put into this portfolio",
        )
        currency = st.selectbox(
            "Currency",
            options=["$ USD", "₪ ILS"],
        )

    with col_right:
        horizon = st.radio(
            "⏳ Time horizon",
            options=["Short (1–2 years)", "Medium (3–5 years)", "Long (5+ years)"],
            index=1,
            help="How long you plan to keep this money invested",
        )
        market = st.radio(
            "🌍 Asset preference",
            options=["US Assets", "Israeli Assets", "Mix of both"],
            index=0,
            help="Which market you prefer to invest in",
        )

    risk_val = st.slider(
        "⚖️ Risk tolerance",
        min_value=0,
        max_value=100,
        value=50,
        help="0 = most conservative (bonds & ETFs). 100 = most aggressive (high-growth stocks).",
    )

    avoid = st.multiselect(
        "🚫 Sectors to avoid (optional)",
        options=["Weapons & Defense", "Tobacco", "Gambling", "Alcohol", "Fossil Fuels"],
        help="We'll exclude these industries from your portfolio recommendations",
    )

    submitted = st.form_submit_button(
        "🤖 Build My Portfolio",
        type="primary",
        use_container_width=True,
    )

# ── Claude API Call ────────────────────────────────────────────────────────────
if submitted:
    currency_symbol = currency.split(" ")[0]
    avoid_str = ", ".join(avoid) if avoid else "none"
    risk_desc = (
        "Very conservative (heavy bonds/ETFs, minimal stock exposure)" if risk_val <= 20 else
        "Conservative (mostly ETFs, small stock allocation)" if risk_val <= 40 else
        "Balanced (mix of ETFs and quality stocks)" if risk_val <= 60 else
        "Moderately aggressive (growth stocks + some ETFs)" if risk_val <= 80 else
        "Very aggressive (concentrated high-growth stocks, minimal hedging)"
    )

    # build the structured prompt — very explicit about JSON format so Claude follows it
    _prompt = f"""You are a portfolio advisor for young investors (18-30 years old).

The investor answered these questions:
- Investment amount: {currency_symbol}{amount:,}
- Time horizon: {horizon}
- Risk tolerance: {risk_val}/100 — {risk_desc}
- Sectors to avoid: {avoid_str}
- Asset preference: {market}

Create exactly 3 portfolio recommendations named Conservative, Balanced, and Aggressive.
Each portfolio must have 4 to 7 assets. All weights must sum to exactly 1.0.

Asset selection rules:
- Use only real tickers available on NYSE, NASDAQ, or TASE (Tel Aviv Stock Exchange)
- For "US Assets": use US stocks and ETFs only (SPY, QQQ, AAPL, MSFT, TLT, BND, etc.)
- For "Israeli Assets": prioritize Israeli names — TEVA, CHKP, NICE, MNDY, CYBR, CLBT, GLBE, ESLT, and Israeli bank/ETF tickers like POLI.TA, LUMI.TA, MZTF.TA, ^TA125.TA
- For "Mix of both": include 2-3 Israeli assets alongside US ETFs and stocks
- Exclude any company in sectors the investor wants to avoid
- Conservative profile: mostly broad ETFs and bonds (SPY, BND, TLT, QQQ). Low individual stock concentration.
- Balanced profile: mix of quality growth stocks and broad ETFs. Some international exposure.
- Aggressive profile: individual high-growth stocks with limited ETF hedging. More concentrated positions.
- Each asset weight must be between 0.05 and 0.50

Respond with ONLY valid JSON — no text before or after. Exact schema:
{{
  "portfolios": [
    {{
      "name": "Conservative",
      "tagline": "One short phrase that captures the spirit of this portfolio",
      "description": "2-3 sentences explaining the strategy and who it suits best",
      "expected_return_range": "X-Y% annually",
      "risk_level": "Low",
      "holdings": [
        {{
          "ticker": "SPY",
          "name": "S&P 500 ETF",
          "weight": 0.40,
          "reason": "One sentence explaining why this asset belongs in this portfolio"
        }}
      ]
    }},
    {{
      "name": "Balanced",
      "tagline": "...",
      "description": "...",
      "expected_return_range": "...",
      "risk_level": "Medium",
      "holdings": [...]
    }},
    {{
      "name": "Aggressive",
      "tagline": "...",
      "description": "...",
      "expected_return_range": "...",
      "risk_level": "High",
      "holdings": [...]
    }}
  ]
}}"""

    with st.spinner("Claude is designing your 3 portfolios — hang tight..."):
        try:
            _client = anthropic.Anthropic(api_key=_api_key)
            _response = _client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2500,
                system=[{
                    "type": "text",
                    "text": "You are a portfolio advisor. Respond with valid JSON only. No prose, no markdown fences, just raw JSON.",
                    "cache_control": {"type": "ephemeral"},
                }],
                messages=[{"role": "user", "content": _prompt}],
            )
            _raw = _response.content[0].text.strip()

            # strip markdown code fences if Claude added them despite instructions
            if _raw.startswith("```"):
                _raw = _raw.split("```")[1]
                if _raw.startswith("json"):
                    _raw = _raw[4:]
                _raw = _raw.rsplit("```", 1)[0]

            _data = json.loads(_raw.strip())
            st.session_state["build_portfolios"] = _data["portfolios"]
            st.session_state["build_meta"] = {
                "amount": amount,
                "currency": currency_symbol,
                "horizon": horizon,
                "risk": f"{risk_val}/100",
                "avoid": avoid,
                "market": market,
            }

        except json.JSONDecodeError as _e:
            st.error(f"Claude returned an unexpected format — please try again. ({_e})")
            st.stop()
        except anthropic.AuthenticationError:
            st.error("Invalid API key. Check your `.streamlit/secrets.toml`.")
            st.stop()
        except Exception as _e:
            st.error(f"Something went wrong: {_e}")
            st.stop()

# ── Display Portfolio Cards ────────────────────────────────────────────────────
if "build_portfolios" in st.session_state:
    portfolios = st.session_state["build_portfolios"]
    meta = st.session_state.get("build_meta", {})

    st.divider()
    st.subheader("Your 3 Portfolio Options")

    if meta:
        st.caption(
            f"Designed for **{meta.get('currency', '$')}{meta.get('amount', 0):,}** · "
            f"{meta.get('horizon', '')} · "
            f"{meta.get('risk', '')} risk · "
            f"{meta.get('market', '')}"
        )

    _risk_icon = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}

    cols = st.columns(3)

    for i, (col, portfolio) in enumerate(zip(cols, portfolios)):
        with col:
            risk_icon = _risk_icon.get(portfolio.get("risk_level", ""), "⚪")

            st.markdown(f"### {portfolio.get('name', '')}")
            st.caption(f"*{portfolio.get('tagline', '')}*")

            st.markdown(
                f"{risk_icon} **Risk:** {portfolio.get('risk_level', 'N/A')}  \n"
                f"📈 **Expected return:** {portfolio.get('expected_return_range', 'N/A')}"
            )

            st.markdown(portfolio.get("description", ""))

            # asset allocation table
            st.markdown("**Asset allocation:**")
            holdings = portfolio.get("holdings", [])
            for h in holdings:
                weight_pct = round(h.get("weight", 0) * 100, 1)
                st.markdown(f"**{h.get('ticker', '')}** — {weight_pct}%")
                st.caption(f"{h.get('name', '')} · {h.get('reason', '')}")

            st.markdown("")

    # ── Follow-up Chat ─────────────────────────────────────────────────────────
    st.divider()
    st.subheader("Ask a follow-up question")
    st.caption("Ask Claude anything about these portfolios — risks, alternatives, how to get started, tax implications, anything.")

    if "followup_history" not in st.session_state:
        st.session_state["followup_history"] = []

    # render past messages
    for msg in st.session_state["followup_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # build portfolio context string once
    _port_ctx = "\n\n".join(
        f"**{p['name']}** ({p.get('risk_level','?')} risk, {p.get('expected_return_range','?')} expected):\n"
        + "\n".join(f"  - {h['ticker']} ({h['name']}): {round(h['weight']*100,1)}% — {h['reason']}"
                    for h in p.get("holdings", []))
        for p in portfolios
    )
    _followup_system = (
        "You are a portfolio advisor helping a young investor understand their personalised portfolio options. "
        "Answer concisely and in plain language. Avoid jargon unless you explain it. "
        "The three portfolios you designed for this user are:\n\n" + _port_ctx
    )

    if question := st.chat_input("e.g. What are the main risks of the Aggressive option?"):
        st.session_state["followup_history"].append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Claude is thinking..."):
                try:
                    _client = anthropic.Anthropic(api_key=_api_key)
                    _messages = [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state["followup_history"]
                    ]
                    _resp = _client.messages.create(
                        model="claude-sonnet-4-6",
                        max_tokens=1024,
                        system=[{"type": "text", "text": _followup_system,
                                 "cache_control": {"type": "ephemeral"}}],
                        messages=_messages,
                    )
                    _answer = _resp.content[0].text
                    st.markdown(_answer)
                    st.session_state["followup_history"].append({"role": "assistant", "content": _answer})
                except Exception as _e:
                    st.error(f"Could not get a response: {_e}")
