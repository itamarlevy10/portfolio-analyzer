# Portfolio Analyzer — AI-Powered Investment Analysis

> A full-stack financial analytics platform built for the next generation of Israeli investors — no finance degree required.

Portfolio Analyzer lets you build a custom stock portfolio, analyze its risk in plain language, optimize weights using modern portfolio theory, backtest against real historical data, and get AI-generated recommendations — all from a clean Streamlit web interface.

---

## Features

- 📊 **Portfolio Builder** — enter holdings by dollar amount or weight %, supporting ILS / USD / EUR
- 🔍 **200+ Preloaded Assets** — Israeli and US stocks, ETFs, and indices; live yfinance search for anything else
- 📉 **Risk Metrics Per Asset** — Volatility, Sharpe Ratio, Beta, Max Drawdown, Value at Risk (95%), Correlation Matrix
- 🎨 **Plain-Language Explanations** — color-coded 🟢🟡🔴 summaries so any investor understands their exposure
- 📈 **Interactive Charts** — cumulative returns (Plotly), correlation heatmap, sector allocation donut
- 🏦 **Dual Benchmark Support** — compare against SPY (S&P 500) or ^TA125.TA (Tel Aviv 125)
- ⏱️ **Flexible Time Periods** — 6 months, 1 year, 2 years, 5 years
- 🧮 **Portfolio Optimizer** — Markowitz efficient frontier via PyPortfolioOpt; suggests optimal weight allocation
- 🔁 **Backtester** — simulate historical performance with custom strategies using vectorbt
- 🤖 **AI Advisor** — Claude API integration delivers personalized, plain-language portfolio recommendations
- 💾 **Portfolio Persistence** — save and auto-load portfolios across sessions

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend / UI | [Streamlit](https://streamlit.io/) |
| Data | [yfinance](https://github.com/ranaroussi/yfinance) |
| Visualization | [Plotly](https://plotly.com/python/) |
| Risk & Math | [pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/), [SciPy](https://scipy.org/) |
| Portfolio Optimization | [PyPortfolioOpt](https://pyportfolioopt.readthedocs.io/) |
| Backtesting | [vectorbt](https://vectorbt.dev/) |
| AI Recommendations | [Claude API](https://www.anthropic.com/) (Anthropic) |
| Language | Python 3.11 |

---

## How to Run Locally

**Prerequisites:** Python 3.11+

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/portfolio-analyzer.git
cd portfolio-analyzer

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Add your Claude API key for the AI Advisor feature
mkdir -p .streamlit
echo '[anthropic]\napi_key = "YOUR_API_KEY"' > .streamlit/secrets.toml

# 5. Launch the app
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## Screenshots

> _Coming soon — UI screenshots and demo GIF._

---

## Project Structure

```
portfolio_analyzer/
├── app.py              # Streamlit UI — sidebar, charts, results display
├── main.py             # Data layer — fetch prices, build portfolio, sector data
├── risk_metrics.py     # Calculations — Sharpe, Beta, VaR, Drawdown, Correlation
├── optimizer.py        # Portfolio optimizer — efficient frontier, weight suggestions
├── backtester.py       # Backtesting engine — historical simulation via vectorbt
├── requirements.txt    # Python dependencies
└── .streamlit/
    └── secrets.toml    # API keys (not committed)
```

---

## Built With AI Tools

This project was developed using:

- **[Claude Code](https://www.anthropic.com/claude-code)** — Anthropic's AI coding assistant, used throughout development for architecture decisions, debugging, and feature implementation
- **[Claude API](https://www.anthropic.com/)** — Powers the in-app AI Advisor feature, delivering personalized portfolio analysis in plain language

---

## License

MIT License — free to use, modify, and distribute.

---

_Built by [Itamar Levy](mailto:itamarlevy10@gmail.com) · Designed for Israeli investors aged 18–30_
