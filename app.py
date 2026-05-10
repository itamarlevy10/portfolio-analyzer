import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from main import build_portfolio, calculate_returns, get_sector_exposure
from risk_metrics import get_portfolio_summary, calculate_portfolio_metrics
from optimizer import get_efficient_frontier, get_efficient_frontier_line
from backtester import run_backtest
import anthropic

st.set_page_config(page_title="Portfolio Analyzer", page_icon="📈", layout="wide")

st.title("📈 Portfolio Analyzer")
st.subheader("Understand your investments. Make smarter decisions.")
st.divider()

# ── Asset List ────────────────────────────────────────────────
POPULAR_ASSETS = [
    ("Apple Inc.", "AAPL"),
    ("Microsoft", "MSFT"),
    ("NVIDIA", "NVDA"),
    ("Amazon", "AMZN"),
    ("Alphabet (Google)", "GOOGL"),
    ("Meta Platforms", "META"),
    ("Tesla", "TSLA"),
    ("Berkshire Hathaway", "BRK-B"),
    ("Eli Lilly", "LLY"),
    ("JPMorgan Chase", "JPM"),
    ("Visa", "V"),
    ("Mastercard", "MA"),
    ("Exxon Mobil", "XOM"),
    ("UnitedHealth", "UNH"),
    ("Johnson & Johnson", "JNJ"),
    ("Walmart", "WMT"),
    ("Procter & Gamble", "PG"),
    ("Home Depot", "HD"),
    ("Chevron", "CVX"),
    ("Merck", "MRK"),
    ("AbbVie", "ABBV"),
    ("Costco", "COST"),
    ("Bank of America", "BAC"),
    ("Netflix", "NFLX"),
    ("Salesforce", "CRM"),
    ("AMD", "AMD"),
    ("Intel", "INTC"),
    ("Qualcomm", "QCOM"),
    ("Texas Instruments", "TXN"),
    ("Adobe", "ADBE"),
    ("Broadcom", "AVGO"),
    ("Oracle", "ORCL"),
    ("Cisco", "CSCO"),
    ("IBM", "IBM"),
    ("Palantir", "PLTR"),
    ("Snowflake", "SNOW"),
    ("CrowdStrike", "CRWD"),
    ("Datadog", "DDOG"),
    ("ServiceNow", "NOW"),
    ("Workday", "WDAY"),
    ("Palo Alto Networks", "PANW"),
    ("Fortinet", "FTNT"),
    ("Cloudflare", "NET"),
    ("Spotify", "SPOT"),
    ("Uber", "UBER"),
    ("Airbnb", "ABNB"),
    ("Block (Square)", "SQ"),
    ("PayPal", "PYPL"),
    ("Shopify", "SHOP"),
    ("Coinbase", "COIN"),
    ("Robinhood", "HOOD"),
    ("Goldman Sachs", "GS"),
    ("Morgan Stanley", "MS"),
    ("Wells Fargo", "WFC"),
    ("Citigroup", "C"),
    ("American Express", "AXP"),
    ("BlackRock", "BLK"),
    ("Charles Schwab", "SCHW"),
    ("Boeing", "BA"),
    ("Lockheed Martin", "LMT"),
    ("Raytheon", "RTX"),
    ("General Electric", "GE"),
    ("Caterpillar", "CAT"),
    ("Deere & Company", "DE"),
    ("3M", "MMM"),
    ("UPS", "UPS"),
    ("FedEx", "FDX"),
    ("Nike", "NKE"),
    ("Starbucks", "SBUX"),
    ("McDonald's", "MCD"),
    ("Coca-Cola", "KO"),
    ("PepsiCo", "PEP"),
    ("Philip Morris", "PM"),
    ("Altria", "MO"),
    ("Disney", "DIS"),
    ("Comcast", "CMCSA"),
    ("AT&T", "T"),
    ("Verizon", "VZ"),
    ("T-Mobile", "TMUS"),
    ("Pfizer", "PFE"),
    ("Moderna", "MRNA"),
    ("BioNTech", "BNTX"),
    ("Gilead Sciences", "GILD"),
    ("Amgen", "AMGN"),
    ("CVS Health", "CVS"),
    ("Anthem", "ELV"),
    ("Intuitive Surgical", "ISRG"),
    ("Thermo Fisher", "TMO"),
    ("Danaher", "DHR"),
    ("ASML", "ASML"),
    ("Taiwan Semiconductor", "TSM"),
    ("Toyota", "TM"),
    ("Shell", "SHEL"),
    ("BP", "BP"),
    ("S&P 500 ETF", "SPY"),
    ("Nasdaq 100 ETF", "QQQ"),
    ("Total Market ETF", "VTI"),
    ("International ETF", "VXUS"),
    ("Emerging Markets ETF", "EEM"),
    ("Small Cap ETF", "IWM"),
    ("Dividend ETF", "VYM"),
    ("Growth ETF", "VUG"),
    ("Value ETF", "VTV"),
    ("Technology ETF", "XLK"),
    ("Healthcare ETF", "XLV"),
    ("Financials ETF", "XLF"),
    ("Energy ETF", "XLE"),
    ("Consumer ETF", "XLY"),
    ("Industrials ETF", "XLI"),
    ("Real Estate ETF", "VNQ"),
    ("Utilities ETF", "XLU"),
    ("Clean Energy ETF", "ICLN"),
    ("Semiconductor ETF", "SOXX"),
    ("Biotech ETF", "IBB"),
    ("ARK Innovation ETF", "ARKK"),
    ("Vanguard S&P 500", "VOO"),
    ("iShares Core S&P", "IVV"),
    ("Long-Term Treasury", "TLT"),
    ("Short-Term Treasury", "SHY"),
    ("Mid-Term Treasury", "IEF"),
    ("Corporate Bonds", "LQD"),
    ("High Yield Bonds", "HYG"),
    ("TIPS Inflation", "TIP"),
    ("Total Bond Market", "BND"),
    ("International Bonds", "BNDX"),
    ("Emerging Market Bonds", "EMB"),
    ("Gold ETF", "GLD"),
    ("Silver ETF", "SLV"),
    ("Oil ETF", "USO"),
    ("Natural Gas ETF", "UNG"),
    ("Agriculture ETF", "DBA"),
    ("Copper ETF", "CPER"),
    ("Bitcoin ETF", "IBIT"),
    ("Ethereum ETF", "ETHA"),
    ("MicroStrategy", "MSTR"),
    ("Check Point Software", "CHKP"),
    ("Nice Systems", "NICE"),
    ("Amdocs", "DOX"),
    ("CyberArk", "CYBR"),
    ("Tower Semiconductor", "TSEM"),
    ("Elbit Systems", "ESLT"),
    ("Bank Hapoalim", "POLI.TA"),
    ("Bank Leumi", "LUMI.TA"),
    ("Mizrahi Tefahot", "MZTF.TA"),
    ("Bank Discount", "DSCT.TA"),
    ("First International Bank", "FIBI.TA"),
    ("Harel Insurance", "HARL.TA"),
    ("Phoenix Holdings", "PHOE.TA"),
    ("Clal Insurance", "CLIS.TA"),
    ("Azrieli Group", "AZRG.TA"),
    ("Gazit Globe", "GZT.TA"),
    ("Delek Group", "DLEKG.TA"),
    ("NewMed Energy", "NWMD.TA"),
    ("Teva Pharmaceutical", "TEVA"),
    ("Cellebrite", "CLBT"),
    ("monday.com", "MNDY"),
    ("Global-e Online", "GLBE"),
    ("eToro", "ETOR"),
    ("TA-125 Index", "^TA125.TA"),
    ("TA-35 Index", "^TA35.TA"),
    ("TA-90 Index", "^TA90.TA"),
    ("TA Tech-Elite", "^TATECH.TA"),
    ("TA Real Estate Index", "^TARE.TA"),
    ("TA Banks Index", "^TABANK.TA"),
    ("MSCI World ETF", "URTH"),
    ("Europe ETF", "VGK"),
    ("Japan ETF", "EWJ"),
    ("China ETF", "MCHI"),
    ("India ETF", "INDA"),
    ("Brazil ETF", "EWZ"),
    ("UK ETF", "EWU"),
    ("Germany ETF", "EWG"),
]

ASSET_OPTIONS = [f"{name} ({ticker})" for name, ticker in POPULAR_ASSETS]

def extract_ticker(label):
    # extract ticker symbol from "Apple Inc. (AAPL)" → "AAPL"
    return label.split("(")[-1].replace(")", "").strip()

def explain_sharpe(sharpe):
    if sharpe > 2:
        return "🟢 Excellent — outstanding return for the risk taken"
    elif sharpe > 1:
        return "🟢 Good — you're being rewarded well for the risk you're taking"
    elif sharpe > 0:
        return "🟡 Mediocre — positive return but not great relative to risk"
    else:
        return "🔴 Poor — you'd have done better in a risk-free savings account"

def explain_volatility(vol):
    if vol < 0.08:
        return "🟢 Low — this portfolio is very stable, similar to bonds"
    elif vol < 0.15:
        return "🟢 Moderate — typical for a diversified stock portfolio"
    elif vol < 0.25:
        return "🟡 High — expect significant swings day to day"
    else:
        return "🔴 Very high — this portfolio can move dramatically in short periods"

def explain_max_drawdown(mdd):
    if mdd > -0.05:
        return "🟢 Minimal — very small worst-case loss historically"
    elif mdd > -0.15:
        return "🟢 Manageable — a bad month but recoverable"
    elif mdd > -0.30:
        return "🟡 Significant — this would test most investors' patience"
    else:
        return "🔴 Severe — most investors would panic-sell at this level"

def explain_beta(beta):
    if beta < 0:
        return "🟢 Negative — moves opposite to the market, a true hedge"
    elif beta < 0.5:
        return "🟢 Low — much less sensitive to market swings than average"
    elif beta < 1.0:
        return "🟢 Below market — moves less than the market"
    elif beta < 1.3:
        return "🟡 Near market — moves roughly with the market"
    else:
        return "🔴 High — amplifies market moves, up and down"

def explain_var(var):
    # var is a negative decimal, e.g. -0.032 means a 3.2% potential daily loss
    if var > -0.02:
        return "🟢 Low risk — on a bad day, losses are expected to stay under 2%"
    elif var > -0.04:
        return "🟢 Moderate — typical for a diversified stock portfolio"
    elif var > -0.07:
        return "🟡 Elevated — expect occasional days with 4–7% losses"
    else:
        return "🔴 High — severe single-day losses are plausible with this portfolio"

# ── Sidebar ───────────────────────────────────────────────────
st.sidebar.header("Your Portfolio")

benchmark = st.sidebar.selectbox(
    "Benchmark Market",
    options=["SPY (US Market)", "^TA125.TA (Israel Market)"],
    help="We compare your portfolio against this index to calculate Beta"
)
benchmark_ticker = benchmark.split(" ")[0]

period = st.sidebar.selectbox(
    "Time Period",
    options=["6mo", "1y", "2y", "5y"],
    index=1,
    help="How far back to analyze"
)

st.sidebar.divider()

input_mode = st.sidebar.radio(
    "Input mode",
    options=["💰 Amount invested", "📊 Portfolio weight %"],
)

if input_mode == "💰 Amount invested":
    currency = st.sidebar.selectbox("Currency", options=["₪ ILS", "$ USD", "€ EUR"])
    currency_symbol = currency.split(" ")[0]
else:
    currency_symbol = "%"

st.sidebar.subheader("Your holdings")

if "holdings_rows" not in st.session_state:
    st.session_state.holdings_rows = [{"ticker": "", "value": 0.0}]

for i, row in enumerate(st.session_state.holdings_rows):
    st.sidebar.markdown(f"**Asset {i+1}**")

    if f"manual_{i}" not in st.session_state:
        st.session_state[f"manual_{i}"] = False

    if not st.session_state[f"manual_{i}"]:
        selected = st.sidebar.selectbox(
            "Search asset",
            options=[""] + ASSET_OPTIONS,
            index=0,
            key=f"asset_{i}",
            placeholder="Type to search: Apple, SPY, Gold..."
        )
        if selected:
            st.session_state.holdings_rows[i]["ticker"] = extract_ticker(selected)

        if st.sidebar.button("🔍 Not in the list? Search live", key=f"manual_btn_{i}"):
            st.session_state[f"manual_{i}"] = True
            st.rerun()

    else:
        query = st.sidebar.text_input(
            "Search any asset",
            placeholder="Type company name or ticker...",
            key=f"query_{i}"
        )
        if query and len(query) >= 2:
            with st.spinner("Searching..."):
                try:
                    results = yf.Search(query).quotes
                    filtered = [
                        r for r in results
                        if r.get("quoteType") in ["EQUITY", "ETF"]
                    ][:6]
                    if filtered:
                        options = [
                            f"{r.get('longname', r.get('shortname', ''))} ({r['symbol']})"
                            for r in filtered
                        ]
                        chosen = st.sidebar.selectbox(
                            "Select asset",
                            options=[""] + options,
                            key=f"live_select_{i}"
                        )
                        if chosen:
                            st.session_state.holdings_rows[i]["ticker"] = extract_ticker(chosen)
                            st.sidebar.caption(f"✅ {st.session_state.holdings_rows[i]['ticker']}")
                    else:
                        st.sidebar.caption("No results found")
                except Exception:
                    st.sidebar.caption("Search error — try again")

        if st.sidebar.button("← Back to list", key=f"back_{i}"):
            st.session_state[f"manual_{i}"] = False
            st.rerun()

    if row.get("ticker"):
        st.sidebar.caption(f"✅ Selected: {row['ticker']}")

    if input_mode == "💰 Amount invested":
        st.session_state.holdings_rows[i]["value"] = st.sidebar.number_input(
            f"Amount ({currency_symbol})",
            min_value=0.0,
            value=row["value"],
            key=f"value_{i}"
        )
    else:
        st.session_state.holdings_rows[i]["value"] = st.sidebar.number_input(
            "Weight %",
            min_value=0.0,
            max_value=100.0,
            value=row["value"],
            key=f"value_{i}"
        )

    st.sidebar.divider()

if st.sidebar.button("➕ Add asset"):
    st.session_state.holdings_rows.append({"ticker": "", "value": 0.0})
    st.rerun()

total = sum(r["value"] for r in st.session_state.holdings_rows)
if input_mode == "💰 Amount invested":
    st.sidebar.caption(f"Total invested: {currency_symbol}{round(total, 2):,}")
else:
    st.sidebar.caption(f"Total weight: {round(total, 1)}%")

analyze = st.sidebar.button("Analyze Portfolio", type="primary")

# ── Compute (runs only when the Analyze button is clicked) ────
# We store all results in session_state so other buttons (like
# "Optimize") don't wipe the page on their rerun.
if analyze:
    filled_rows = [
        r for r in st.session_state.holdings_rows
        if r["ticker"].strip() != "" and r["value"] > 0
    ]

    if len(filled_rows) == 0:
        st.error("Please add at least one asset with a value.")

    else:
        if input_mode == "💰 Amount invested":
            total_invested = sum(r["value"] for r in filled_rows)
            holdings = [
                {"ticker": r["ticker"], "weight": r["value"] / total_invested}
                for r in filled_rows
            ]
        else:
            total_weight = sum(r["value"] for r in filled_rows)
            if abs(total_weight - 100.0) > 0.1:
                st.error(f"Weights must sum to 100%. Currently: {round(total_weight, 1)}%")
                st.stop()
            holdings = [
                {"ticker": r["ticker"], "weight": r["value"] / 100}
                for r in filled_rows
            ]

        with st.spinner("Fetching data and calculating risk metrics..."):
            prices = build_portfolio(holdings, period=period)
            returns = calculate_returns(prices)
            summary = get_portfolio_summary(returns, benchmark=benchmark_ticker)
            portfolio_metrics = calculate_portfolio_metrics(
                returns, holdings, risk_free_rate=summary["risk_free_rate"]
            )

        # persist results so they survive subsequent button clicks
        st.session_state["analysis"] = {
            "returns": returns,
            "holdings": holdings,
            "summary": summary,
            "portfolio_metrics": portfolio_metrics,
            "period": period,
        }
        # clear stale optimizer results when the portfolio is re-analysed
        st.session_state.pop("opt_result", None)
        st.session_state.pop("opt_frontier", None)

# ── Display (runs whenever session_state has analysis data) ───
if "analysis" not in st.session_state:
    st.info("👈 Search for assets in the sidebar and click **Analyze Portfolio**")

else:
    # unpack all results from session state
    _d = st.session_state["analysis"]
    returns = _d["returns"]
    holdings = _d["holdings"]
    summary = _d["summary"]
    portfolio_metrics = _d["portfolio_metrics"]
    period_used = _d.get("period", "1y")

    # ── Results ───────────────────────────────────────────
    st.success(f"✅ Analysis complete — {len(holdings)} assets over {period_used}")

    st.subheader("Portfolio Composition")
    for h in holdings:
        st.write(f"**{h['ticker']}** — {round(h['weight']*100, 1)}%")

    st.divider()

    # ── Risk Metrics ──────────────────────────────────────
    st.subheader("Risk Metrics")

    # show a warning if metrics couldn't be computed (e.g. a ticker had no data and was skipped)
    import math
    if math.isnan(portfolio_metrics.get("annual_return", float("nan"))):
        st.warning("Could not calculate portfolio metrics — one or more assets may have insufficient data (possibly delisted or invalid tickers were removed from the calculation)")

    st.markdown("#### 📦 Your Portfolio (combined)")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric(
            label="Portfolio Return",
            value=f"{round(portfolio_metrics['annual_return']*100, 1)}%",
            help="Annualized return of your combined portfolio"
        )
    with col2:
        st.metric(
            label="Portfolio Volatility",
            value=f"{round(portfolio_metrics['volatility']*100, 1)}%",
            help="How much your combined portfolio fluctuates annually"
        )
    with col3:
        st.metric(
            label="Portfolio Sharpe",
            value=round(portfolio_metrics['sharpe'], 2),
            help="Return per unit of risk. Above 1 is good, above 2 is excellent"
        )
    with col4:
        st.metric(
            label="Portfolio Max Drawdown",
            value=f"{round(portfolio_metrics['max_drawdown']*100, 1)}%",
            help="Worst peak-to-trough loss your combined portfolio experienced"
        )
    with col5:
        st.metric(
            label="Daily VaR (95%)",
            value=f"{round(portfolio_metrics['var_95']*100, 2)}%",
            help="On 95% of days, your portfolio won't lose more than this amount"
        )

    # plain language explanations for portfolio
    st.caption(explain_volatility(portfolio_metrics['volatility']))
    st.caption(explain_sharpe(portfolio_metrics['sharpe']))
    st.caption(explain_max_drawdown(portfolio_metrics['max_drawdown']))
    st.caption(explain_var(portfolio_metrics['var_95']))

    st.divider()

    st.markdown("#### Per Asset averages")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label="Risk-Free Rate",
            value=f"{round(summary['risk_free_rate']*100, 2)}%",
            help="Current 13-week US Treasury Bill rate"
        )
    with col2:
        st.metric(
            label="Avg Volatility",
            value=f"{round(summary['volatility'].mean()*100, 1)}%",
            help="Average annualized volatility across all assets"
        )
    with col3:
        st.metric(
            label="Avg Sharpe Ratio",
            value=round(summary['sharpe'].mean(), 2),
            help="Above 1 is good, above 2 is excellent"
        )
    with col4:
        st.metric(
            label="Avg Max Drawdown",
            value=f"{round(summary['max_drawdown'].mean()*100, 1)}%",
            help="Average worst peak-to-trough loss over the period"
        )

    st.divider()

    # ── Per Asset Breakdown ───────────────────────────────
    st.subheader("Per Asset Breakdown")
    for ticker in returns.columns:
        with st.expander(f"📊 {ticker}"):
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Volatility", f"{round(summary['volatility'][ticker]*100, 1)}%")
            c2.metric("Sharpe", round(summary['sharpe'][ticker], 2))
            c3.metric("Beta", round(summary['beta'][ticker], 2))
            c4.metric("Max Drawdown", f"{round(summary['max_drawdown'][ticker]*100, 1)}%")
            c5.metric("Daily VaR (95%)", f"{round(summary['var_95'][ticker]*100, 2)}%")

            # plain language explanations per asset
            st.caption(explain_volatility(summary['volatility'][ticker]))
            st.caption(explain_sharpe(summary['sharpe'][ticker]))
            st.caption(explain_beta(summary['beta'][ticker]))
            st.caption(explain_max_drawdown(summary['max_drawdown'][ticker]))
            st.caption(explain_var(summary['var_95'][ticker]))

    st.divider()

    # ── Correlation Matrix ────────────────────────────────
    st.subheader("Correlation Matrix")
    st.dataframe(summary['correlation'].round(2), use_container_width=True)

    st.divider()

    # ── Cumulative Returns Chart ──────────────────────────
    st.subheader("📈 Cumulative Returns")
    st.caption("How $10,000 invested on day one would have grown over time")

    cumulative = (1 + returns).cumprod() * 10000

    fig_returns = go.Figure()
    for ticker in cumulative.columns:
        fig_returns.add_trace(go.Scatter(
            x=cumulative.index,
            y=cumulative[ticker].round(2),
            name=ticker,
            mode="lines",
            hovertemplate=f"<b>{ticker}</b><br>Date: %{{x|%b %d, %Y}}<br>Value: $%{{y:,.0f}}<extra></extra>"
        ))

    weights = {h["ticker"]: h["weight"] for h in holdings}
    portfolio_daily = sum(
        returns[ticker] * weights[ticker]
        for ticker in returns.columns
        if ticker in weights
    )
    portfolio_cumulative = (1 + portfolio_daily).cumprod() * 10000

    fig_returns.add_trace(go.Scatter(
        x=portfolio_cumulative.index,
        y=portfolio_cumulative.round(2),
        name="📦 My Portfolio",
        mode="lines",
        line=dict(color="black", width=3),
        hovertemplate="<b>My Portfolio</b><br>Date: %{x|%b %d, %Y}<br>Value: $%{y:,.0f}<extra></extra>"
    ))

    fig_returns.update_layout(
        xaxis_title="Date",
        yaxis_title="Portfolio Value ($)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=450,
    )
    fig_returns.add_hline(
        y=10000, line_dash="dash",
        line_color="gray", opacity=0.5,
        annotation_text="Starting value"
    )
    st.plotly_chart(fig_returns, use_container_width=True)

    st.divider()

    # ── Correlation Heatmap ───────────────────────────────
    st.subheader("🔥 Correlation Heatmap")
    st.caption("How much your assets move together. Lower correlation = better diversification.")

    fig_heatmap = px.imshow(
        summary['correlation'].round(2),
        text_auto=True,
        color_continuous_scale="RdYlGn",
        zmin=-1, zmax=1,
        aspect="auto"
    )
    fig_heatmap.update_layout(height=400)
    st.plotly_chart(fig_heatmap, use_container_width=True)

    st.divider()

    # ── Sector Exposure ───────────────────────────────────
    st.subheader("🏭 Sector Exposure")
    st.caption("What industries is your portfolio actually invested in?")

    with st.spinner("Fetching sector data..."):
        sector_data = get_sector_exposure(holdings)
        st.session_state["sector_data"] = sector_data   # persist so AI advisor can use it

    if sector_data:
        labels = list(sector_data.keys())
        values = [round(v * 100, 1) for v in sector_data.values()]
        colors = []
        set3 = px.colors.qualitative.Set3
        color_index = 0
        for label in labels:
            if label == "Unknown":
                colors.append("#D3D3D3")
            else:
                colors.append(set3[color_index % len(set3)])
                color_index += 1

        fig_sector = px.pie(
            names=labels,
            values=values,
            hole=0.4,
            color_discrete_sequence=colors
        )
        fig_sector.update_traces(
            textposition="inside",
            textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>%{value:.1f}%<extra></extra>"
        )
        fig_sector.update_layout(height=450, showlegend=True)
        st.plotly_chart(fig_sector, use_container_width=True)

        unknown_weight = sector_data.get("Unknown", 0)
        if unknown_weight > 0:
            st.info(
                f"**ℹ️ About the Unknown slice ({round(unknown_weight*100, 1)}%):** "
                f"ETFs, bond funds, and indices don't have a single sector — they hold "
                f"hundreds of assets across many industries. This portion of your portfolio "
                f"is diversified across multiple sectors that can't be broken down here."
            )

    st.divider()

    # ── Efficient Frontier Explorer ───────────────────────
    # Each dot is a random portfolio drawn from the user's assets.
    # The white curve is the actual efficient frontier — the set of portfolios
    # that minimise risk for every achievable return level.
    # Clicking any point loads its weights into an interactive detail card below.
    st.subheader("🎯 Efficient Frontier Explorer")

    if len(holdings) < 2:
        st.info("Add at least 2 assets to your portfolio to explore the efficient frontier.")
    else:
        # generate frontier data automatically on first load (or after re-analysis)
        # opt_frontier is cleared from session_state whenever "Analyze Portfolio" runs
        if "opt_frontier" not in st.session_state:
            with st.spinner("Computing efficient frontier — this takes a few seconds..."):
                try:
                    frontier_df = get_efficient_frontier(returns, n_points=500)
                    frontier_line_df = get_efficient_frontier_line(returns, n_points=40)
                    st.session_state["opt_frontier"] = frontier_df
                    st.session_state["opt_frontier_line"] = frontier_line_df
                except Exception as e:
                    st.error(f"Could not compute efficient frontier: {e}")

        if "opt_frontier" in st.session_state:
            frontier_df = st.session_state["opt_frontier"]
            frontier_line_df = st.session_state.get("opt_frontier_line", pd.DataFrame())

            # instructional text — shown above the chart
            st.markdown(
                "**Each dot is a possible way to allocate your assets. "
                "Hover to explore. Click a dot to see its weights and load it.**  \n"
                "Move right → more risk.   Move up → more return.   "
                "Yellow dots → best risk/reward ratio (Sharpe)."
            )

            # build a hover label string for every random portfolio point
            hover_random = []
            for _, row in frontier_df.iterrows():
                w_lines = "<br>".join(
                    f"  {t}: {row[t]*100:.0f}%" for t in returns.columns
                )
                hover_random.append(
                    f"<b>Return:</b> {row['return']*100:.1f}%<br>"
                    f"<b>Volatility:</b> {row['volatility']*100:.1f}%<br>"
                    f"<b>Sharpe:</b> {row['sharpe']:.2f}<br>"
                    f"── Weights ──<br>{w_lines}"
                )

            fig_frontier = go.Figure()

            # trace 0 — random portfolio cloud coloured by Sharpe (yellow=high, purple=low)
            fig_frontier.add_trace(go.Scatter(
                x=frontier_df["volatility"] * 100,
                y=frontier_df["return"] * 100,
                mode="markers",
                marker=dict(
                    color=frontier_df["sharpe"],
                    colorscale="Plasma",
                    size=6,
                    opacity=0.65,
                    colorbar=dict(title="Sharpe", thickness=12),
                    showscale=True,
                ),
                name="Possible Portfolios",
                hovertext=hover_random,
                hoverinfo="text",
            ))

            # trace 1 — actual efficient frontier line (sorted by vol so it draws smoothly)
            if not frontier_line_df.empty:
                fl = frontier_line_df.sort_values("volatility").reset_index(drop=True)
                hover_line = []
                for _, row in fl.iterrows():
                    w_lines = "<br>".join(
                        f"  {t}: {row.get(t, 0)*100:.0f}%" for t in returns.columns
                    )
                    hover_line.append(
                        f"<b>Efficient Frontier</b><br>"
                        f"<b>Return:</b> {row['return']*100:.1f}%<br>"
                        f"<b>Volatility:</b> {row['volatility']*100:.1f}%<br>"
                        f"<b>Sharpe:</b> {row['sharpe']:.2f}<br>"
                        f"── Weights (5–40% bounds) ──<br>{w_lines}"
                    )
                fig_frontier.add_trace(go.Scatter(
                    x=fl["volatility"] * 100,
                    y=fl["return"] * 100,
                    mode="lines+markers",
                    line=dict(color="white", width=2.5),
                    marker=dict(size=5, color="white"),
                    name="Efficient Frontier",
                    hovertext=hover_line,
                    hoverinfo="text",
                ))

            # trace 2 — current portfolio (blue star)
            fig_frontier.add_trace(go.Scatter(
                x=[portfolio_metrics["volatility"] * 100],
                y=[portfolio_metrics["annual_return"] * 100],
                mode="markers+text",
                marker=dict(
                    symbol="star", size=22, color="royalblue",
                    line=dict(color="white", width=1.5),
                ),
                text=["⭐ You"],
                textposition="top center",
                name="Your Portfolio",
                hovertext=(
                    f"<b>Your Portfolio</b><br>"
                    f"Return: {portfolio_metrics['annual_return']*100:.1f}%<br>"
                    f"Volatility: {portfolio_metrics['volatility']*100:.1f}%<br>"
                    f"Sharpe: {portfolio_metrics['sharpe']:.2f}"
                ),
                hoverinfo="text",
            ))

            fig_frontier.update_layout(
                xaxis_title="Volatility (%) — Risk →",
                yaxis_title="Expected Return (%) ↑",
                height=520,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )

            # on_select="rerun" triggers a page rerun whenever the user clicks a point
            event = st.plotly_chart(
                fig_frontier,
                use_container_width=True,
                on_select="rerun",
                selection_mode="points",
                key="frontier_chart",
            )

            # ── Click Interaction ─────────────────────────────
            # extract which point was clicked and store it in session state
            # so the detail card persists through subsequent button-click reruns
            if event.selection and event.selection.points:
                pt = event.selection.points[0]
                curve_num = pt.get("curve_number", 0)
                pt_idx = pt.get("point_index", 0)

                # only handle clicks on the random cloud (trace 0) or frontier line (trace 1)
                if curve_num == 0 and pt_idx < len(frontier_df):
                    row = frontier_df.iloc[pt_idx]
                    source_label = "Random Portfolio"
                elif curve_num == 1 and not frontier_line_df.empty:
                    fl_sorted = frontier_line_df.sort_values("volatility").reset_index(drop=True)
                    if pt_idx < len(fl_sorted):
                        row = fl_sorted.iloc[pt_idx]
                        source_label = "Efficient Frontier"
                    else:
                        row = None
                        source_label = ""
                else:
                    row = None
                    source_label = ""

                if row is not None:
                    st.session_state["frontier_selected"] = {
                        t: float(row.get(t, 0)) for t in returns.columns
                    }
                    st.session_state["frontier_selected_stats"] = {
                        "return": float(row["return"]),
                        "volatility": float(row["volatility"]),
                        "sharpe": float(row["sharpe"]),
                        "source": source_label,
                    }

            # ── Detail Card ───────────────────────────────────
            # shown whenever a point is selected (survives button-click reruns via session state)
            if "frontier_selected" in st.session_state:
                sel_w = st.session_state["frontier_selected"]
                sel_s = st.session_state["frontier_selected_stats"]

                st.markdown("---")
                st.markdown(f"#### 📋 Selected Portfolio — *{sel_s['source']}*")

                # performance metrics vs current portfolio
                c1, c2, c3 = st.columns(3)
                with c1:
                    ret_d = round((sel_s["return"] - portfolio_metrics["annual_return"]) * 100, 1)
                    st.metric("Expected Return", f"{sel_s['return']*100:.1f}%",
                              delta=f"{ret_d:+.1f}% vs current")
                with c2:
                    vol_d = round((sel_s["volatility"] - portfolio_metrics["volatility"]) * 100, 1)
                    st.metric("Volatility", f"{sel_s['volatility']*100:.1f}%",
                              delta=f"{vol_d:+.1f}% vs current", delta_color="inverse")
                with c3:
                    sha_d = round(sel_s["sharpe"] - portfolio_metrics["sharpe"], 2)
                    st.metric("Sharpe Ratio", round(sel_s["sharpe"], 2),
                              delta=f"{sha_d:+.2f} vs current")

                # weights breakdown — one metric per asset
                st.markdown("**Weights in this portfolio:**")
                weight_cols = st.columns(len(sel_w))
                for col, (ticker, wt) in zip(weight_cols, sel_w.items()):
                    col.metric(ticker, f"{wt*100:.1f}%")

                # plain language comparison
                cur_sh = round(portfolio_metrics["sharpe"], 2)
                sel_sh = round(sel_s["sharpe"], 2)
                if sel_sh > cur_sh:
                    st.info(
                        f"💡 This allocation has a better Sharpe ratio ({sel_sh} vs your {cur_sh}). "
                        f"You'd earn more return for every unit of risk you take.  "
                        f"Weights are constrained between 5% and 40% per asset for practical diversification."
                    )
                elif sel_sh < cur_sh:
                    st.info(
                        f"💡 This allocation has a lower Sharpe ratio ({sel_sh} vs your {cur_sh}). "
                        f"It might suit you if you're targeting a specific return or volatility level.  "
                        f"Weights are constrained between 5% and 40% per asset for practical diversification."
                    )
                else:
                    st.info(
                        f"💡 This allocation has nearly the same Sharpe ratio as your current portfolio ({cur_sh}).  "
                        f"Weights are constrained between 5% and 40% per asset for practical diversification."
                    )

                # AI explanation placeholder — will connect Claude API in a future version
                st.caption("🤖 Coming soon: AI explanation of this allocation")

                # load selected weights into the main analyzer and rerun the full page
                if st.button("📊 Analyze this allocation", type="primary"):
                    selected_holdings = [
                        {"ticker": t, "weight": w}
                        for t, w in sel_w.items()
                        if w > 0.001   # drop near-zero weights
                    ]
                    new_pm = calculate_portfolio_metrics(
                        returns,
                        selected_holdings,
                        risk_free_rate=summary["risk_free_rate"],
                    )
                    # update the analysis in session state — all charts will reflect the new weights
                    st.session_state["analysis"]["holdings"] = selected_holdings
                    st.session_state["analysis"]["portfolio_metrics"] = new_pm
                    # clear the selection card
                    st.session_state.pop("frontier_selected", None)
                    st.session_state.pop("frontier_selected_stats", None)
                    st.rerun()

    st.divider()

    # ── Backtest ──────────────────────────────────────────────────
    # simulates holding the portfolio with monthly rebalancing and compares to SPY
    st.subheader("📅 Backtest")
    st.caption("See how your portfolio would have performed historically with monthly rebalancing back to target weights.")

    # period picker — maps friendly labels to yfinance period strings
    bt_period_label = st.selectbox(
        "Backtest period",
        options=["1 year", "3 years", "5 years"],
        index=2,
        key="bt_period_select",
    )

    # map display text to yfinance period string
    _period_map = {"1 year": "1y", "3 years": "3y", "5 years": "5y"}
    bt_yf_period = _period_map[bt_period_label]

    if st.button("▶ Run Backtest", type="primary", key="run_bt_btn"):
        with st.spinner("Downloading historical data and simulating portfolio..."):
            try:
                bt_result = run_backtest(holdings, period=bt_yf_period)   # run the backtest
                st.session_state["backtest"] = bt_result                  # persist across reruns
                st.session_state["backtest_label"] = bt_period_label      # also save label
            except Exception as e:
                st.error(f"Backtest failed: {e}")

    # display results if a backtest has been run (survives button-click reruns)
    if "backtest" in st.session_state:
        bt = st.session_state["backtest"]                                  # unpack results
        saved_label = st.session_state.get("backtest_label", "5 years")   # restore period label

        # ── Portfolio vs SPY Line Chart ────────────────────────────
        fig_bt = go.Figure()

        # portfolio value trace — blue solid line
        fig_bt.add_trace(go.Scatter(
            x=bt["portfolio_value"].index,
            y=bt["portfolio_value"].round(2),
            name="My Portfolio",
            mode="lines",
            line=dict(color="royalblue", width=2.5),
            hovertemplate="<b>My Portfolio</b><br>%{x|%b %d, %Y}: $%{y:,.0f}<extra></extra>",
        ))

        # SPY benchmark trace — orange dashed line
        if bt["spy"] is not None:
            fig_bt.add_trace(go.Scatter(
                x=bt["spy"]["portfolio_value"].index,
                y=bt["spy"]["portfolio_value"].round(2),
                name="SPY Benchmark",
                mode="lines",
                line=dict(color="orange", width=2, dash="dash"),
                hovertemplate="<b>SPY</b><br>%{x|%b %d, %Y}: $%{y:,.0f}<extra></extra>",
            ))

        # horizontal reference line at the $10,000 starting value
        fig_bt.add_hline(y=10000, line_dash="dot", line_color="gray", opacity=0.5,
                         annotation_text="Starting $10,000")

        fig_bt.update_layout(
            title=f"Portfolio Value — {saved_label} (Monthly Rebalancing, Starting $10,000)",
            xaxis_title="Date",
            yaxis_title="Portfolio Value ($)",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=450,
        )
        st.plotly_chart(fig_bt, use_container_width=True)

        # ── 4 Key Metric Cards ─────────────────────────────────────
        spy = bt["spy"]                                                    # shorthand

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            # show delta vs SPY if benchmark data exists
            tr_delta = (
                f"{(bt['total_return'] - spy['total_return']) * 100:+.1f}% vs SPY"
                if spy else None
            )
            st.metric("Total Return", f"{bt['total_return']*100:.1f}%", delta=tr_delta)

        with c2:
            ar_delta = (
                f"{(bt['annual_return'] - spy['annual_return']) * 100:+.1f}% vs SPY"
                if spy else None
            )
            st.metric("Annual Return (CAGR)", f"{bt['annual_return']*100:.1f}%", delta=ar_delta)

        with c3:
            # drawdown is always negative — no delta needed
            st.metric(
                "Max Drawdown",
                f"{bt['max_drawdown']*100:.1f}%",
                help="Worst peak-to-trough loss during the backtest period",
            )

        with c4:
            st.metric(
                "Sharpe Ratio",
                round(bt["sharpe"], 2),
                help="Return per unit of risk. Above 1 is good, above 2 is excellent.",
            )

        # ── Monthly Returns Bar Chart ──────────────────────────────
        monthly = bt["monthly_returns"]                                    # Series of monthly % changes

        # colour each bar: green for gains, red for losses
        bar_colors = ["#2ecc71" if r > 0 else "#e74c3c" for r in monthly]

        fig_monthly = go.Figure()
        fig_monthly.add_trace(go.Bar(
            x=monthly.index,
            y=(monthly * 100).round(2),                                    # display as %
            marker_color=bar_colors,
            name="Monthly Return",
            hovertemplate="%{x|%b %Y}: %{y:.2f}%<extra></extra>",
        ))
        fig_monthly.add_hline(y=0, line_color="gray", line_width=1)        # zero reference line
        fig_monthly.update_layout(
            title="Monthly Returns",
            xaxis_title="Month",
            yaxis_title="Return (%)",
            height=350,
            showlegend=False,
        )
        st.plotly_chart(fig_monthly, use_container_width=True)

        # ── Plain Language Summary ─────────────────────────────────
        spy_total_str = f"{spy['total_return']*100:.1f}%" if spy else "N/A"
        outperformed = spy and bt["total_return"] > spy["total_return"]
        vs_word = "outperformed" if outperformed else "underperformed"

        st.info(
            f"**Over {saved_label}**, your portfolio returned "
            f"**{bt['total_return']*100:.1f}%** vs SPY's **{spy_total_str}** "
            f"— you **{vs_word}** the benchmark.  \n"
            f"**Best day:** +{bt['best_day']*100:.2f}%  |  "
            f"**Worst day:** {bt['worst_day']*100:.2f}%  |  "
            f"**{bt['months_positive']*100:.0f}%** of months were positive."
        )

    st.divider()

    # ── AI Portfolio Advisor ──────────────────────────────────────────
    # sends portfolio metrics + backtest results to Claude for personalised analysis
    st.subheader("🤖 AI Portfolio Advisor")
    st.caption("Get a personalised AI analysis of your portfolio — strengths, risks, and actionable tips.")

    # check if an API key has been configured and is not the placeholder value
    _api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    _key_missing = not _api_key or _api_key.startswith("sk-ant-YOUR") or _api_key == "placeholder"

    if _key_missing:
        st.info("🔑 AI Advisor is disabled — add your Anthropic API key to `.streamlit/secrets.toml` to enable it.")
    else:
        # follow-up question input appears above the buttons so users see it first
        followup_text = st.text_input(
            "Ask a follow-up question (optional)",
            placeholder="e.g. Should I add bonds? How do I reduce my tech exposure?",
            key="ai_followup_input",
        )

        # two side-by-side buttons — main analysis and follow-up
        _col_a, _col_b = st.columns([1, 1])
        with _col_a:
            run_ai_analysis = st.button("🧠 Get AI Analysis", type="primary", key="ai_run_btn")
        with _col_b:
            run_ai_followup = st.button("💬 Ask Follow-up", key="ai_followup_btn")

        def _build_portfolio_context():
            # assembles all available portfolio data into a plain-text block for the prompt
            lines = []

            lines.append("=== PORTFOLIO HOLDINGS ===")
            for h in holdings:
                lines.append(f"  {h['ticker']}: {h['weight']*100:.1f}%")

            pm = portfolio_metrics                            # shorthand
            lines.append("\n=== PORTFOLIO METRICS ===")
            lines.append(f"  Annual Return:  {pm['annual_return']*100:.1f}%")
            lines.append(f"  Volatility:     {pm['volatility']*100:.1f}%")
            lines.append(f"  Sharpe Ratio:   {round(pm['sharpe'], 2)}")
            lines.append(f"  Max Drawdown:   {pm['max_drawdown']*100:.1f}%")
            lines.append(f"  Daily VaR 95%:  {pm['var_95']*100:.2f}%")
            lines.append(f"  Risk-Free Rate: {summary['risk_free_rate']*100:.2f}%")

            lines.append("\n=== PER-ASSET METRICS ===")
            for ticker in returns.columns:
                lines.append(
                    f"  {ticker}: Sharpe {round(summary['sharpe'][ticker], 2)}, "
                    f"Vol {summary['volatility'][ticker]*100:.1f}%, "
                    f"Beta {round(summary['beta'][ticker], 2)}, "
                    f"MaxDD {summary['max_drawdown'][ticker]*100:.1f}%"
                )

            # include sector breakdown if it was fetched earlier
            if "sector_data" in st.session_state:
                lines.append("\n=== SECTOR EXPOSURE ===")
                for sector, w in st.session_state["sector_data"].items():
                    lines.append(f"  {sector}: {w*100:.1f}%")

            # include backtest results if available
            if "backtest" in st.session_state:
                _bt = st.session_state["backtest"]
                _lbl = st.session_state.get("backtest_label", "")
                lines.append(f"\n=== BACKTEST RESULTS ({_lbl}) ===")
                lines.append(f"  Total Return:    {_bt['total_return']*100:.1f}%")
                lines.append(f"  Annual Return:   {_bt['annual_return']*100:.1f}%")
                lines.append(f"  Max Drawdown:    {_bt['max_drawdown']*100:.1f}%")
                lines.append(f"  Sharpe Ratio:    {round(_bt['sharpe'], 2)}")
                lines.append(f"  Best Day:        +{_bt['best_day']*100:.2f}%")
                lines.append(f"  Worst Day:       {_bt['worst_day']*100:.2f}%")
                lines.append(f"  Months Positive: {_bt['months_positive']*100:.0f}%")
                if _bt["spy"]:
                    lines.append(f"  SPY Total Return:{_bt['spy']['total_return']*100:.1f}%")

            return "\n".join(lines)

        # system prompt — cached at the API level so repeated clicks reuse the same context
        _AI_SYSTEM = """You are a friendly, educational investment advisor for young investors aged 18-30.

Your tone: honest, encouraging, clear. Explain ideas simply — no jargon.
Your goal: help the investor understand and improve their portfolio.

Never recommend specific stock picks or give direct buy/sell orders.
Focus on portfolio construction, diversification, and risk management principles."""

        # main analysis prompt — asks Claude for a structured four-part response
        _ANALYSIS_PROMPT_TEMPLATE = """{context}

Please analyse this portfolio and provide:

**1. Summary** (2-3 sentences)
What are the main strengths and weaknesses of this portfolio?

**2. Top Risks** (2-3 bullet points)
What are the biggest risks this investor should understand?

**3. Actionable Recommendations** (2-3 bullet points)
What specific, practical steps could improve this portfolio?

**4. Young Investor Rating: X/10**
Rate this portfolio for an 18-30 year old and explain in 1-2 sentences."""

        if run_ai_analysis or run_ai_followup:
            try:
                # initialise the Anthropic client using the secret key from secrets.toml
                _ai_client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
                _context = _build_portfolio_context()            # build the data block

                if run_ai_followup and followup_text.strip():
                    # send the follow-up question with full context and previous answer
                    _prev = st.session_state.get("ai_response", "")
                    if _prev:
                        _prompt = (
                            f"{_context}\n\nPrevious analysis:\n{_prev}"
                            f"\n\nFollow-up question: {followup_text.strip()}"
                        )
                    else:
                        _prompt = f"{_context}\n\nQuestion: {followup_text.strip()}"
                else:
                    # main analysis request
                    _prompt = _ANALYSIS_PROMPT_TEMPLATE.format(context=_context)

                with st.spinner("Claude is analysing your portfolio..."):
                    _ai_response = _ai_client.messages.create(
                        model="claude-sonnet-4-20250514",        # Claude Sonnet 4 as requested
                        max_tokens=1024,                         # enough for a structured 4-part answer
                        system=[{
                            "type": "text",
                            "text": _AI_SYSTEM,
                            "cache_control": {"type": "ephemeral"},  # cache system prompt for reuse
                        }],
                        messages=[{"role": "user", "content": _prompt}],
                    )
                    _ai_text = _ai_response.content[0].text     # extract the text block
                    st.session_state["ai_response"] = _ai_text  # persist so it survives reruns

            except anthropic.AuthenticationError:
                st.error("Invalid API key — please add your key to `.streamlit/secrets.toml`: `ANTHROPIC_API_KEY = \"sk-ant-...\"`")
            except Exception as _e:
                st.error(f"AI analysis failed: {_e}")

        # display the last AI response (persists through subsequent button clicks)
        if "ai_response" in st.session_state:
            st.markdown(st.session_state["ai_response"])
