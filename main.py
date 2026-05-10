import yfinance as yf
import pandas as pd

# ── Data Layer ──────────────────────────────────────────────

def get_stock_data(ticker, period="1y"):
    # yf.Ticker creates an object representing a single financial asset
    stock = yf.Ticker(ticker)
    # .history downloads historical price data for the requested time period
    df = stock.history(period=period)
    return df

def build_portfolio(holdings, period="1y"):
    # empty dictionary that will collect each asset's closing prices
    prices = {}

    for holding in holdings:        # loop over every asset in the list
        ticker = holding["ticker"]  # extract the ticker symbol
        df = get_stock_data(ticker, period=period)
        close = df["Close"]         # keep only the Close column — the end-of-day price

        # skip tickers that have no data — yfinance returns all-NaN for delisted symbols
        if close.empty or close.isna().all():
            print(f"WARNING: No price data for {ticker} — skipping (possibly delisted or invalid ticker)")
            continue

        prices[ticker] = close

    # convert the dictionary into a structured table — one column per asset
    portfolio_df = pd.DataFrame(prices)
    return portfolio_df

def calculate_returns(portfolio_df):
    # .pct_change() computes daily % change: (today - yesterday) / yesterday
    # fill_method=None avoids a FutureWarning about deprecated forward-fill behaviour
    returns = portfolio_df.pct_change(fill_method=None)
    # drop the first row — it's NaN because there's no "yesterday" for day 1
    returns = returns.dropna()
    return returns

def get_sector_exposure(holdings):
    """
    For each holding, fetch its sector from yfinance.
    Multiply by weight to get weighted sector exposure.
    Returns a dictionary: {sector: total_weight}
    """
    sector_weights = {}  # will accumulate weight per sector

    for holding in holdings:
        ticker = holding["ticker"]
        weight = holding["weight"]

        try:
            # yf.Ticker().info returns a dict with lots of metadata
            info = yf.Ticker(ticker).info
            # "sector" key gives us e.g. "Technology", "Healthcare"
            sector = info.get("sector", "Unknown")
        except Exception:
            sector = "Unknown"

        # add this holding's weight to its sector
        if sector in sector_weights:
            sector_weights[sector] += weight
        else:
            sector_weights[sector] = weight

    return sector_weights

# ── Run ─────────────────────────────────────────────────────

if __name__ == "__main__":
    my_portfolio = [
        {"ticker": "AAPL", "weight": 0.4},  # Apple stock
        {"ticker": "SPY",  "weight": 0.4},  # S&P 500 index fund
        {"ticker": "TLT",  "weight": 0.2},  # long-term government bonds
    ]

    prices = build_portfolio(my_portfolio)
    returns = calculate_returns(prices)

    print("=== Prices (last 5 days) ===")
    print(prices.tail())
    print("\n=== Daily Returns (last 5 days) ===")
    print(returns.tail())
    print("\nTable shape:", returns.shape)