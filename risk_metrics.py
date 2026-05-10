import pandas as pd
import numpy as np
import yfinance as yf

# ── Risk Metrics ────────────────────────────────────────────

def get_risk_free_rate():
    # ^IRX is the 13-week US Treasury Bill — the industry standard
    # for risk-free rate. yfinance returns it as an annualized percentage.
    irx = yf.Ticker("^IRX")
    hist = irx.history(period="5d")  # get last 5 days in case today is missing

    # the value is given as a percentage (e.g. 4.5 means 4.5%)
    # we divide by 100 to convert to decimal (0.045)
    rate = hist["Close"].dropna().iloc[-1] / 100

    return rate

def calculate_volatility(returns):
    # std() computes the standard deviation of daily returns per asset
    daily_vol = returns.std()

    # we multiply by sqrt(252) to convert from daily to annual volatility
    # 252 = number of trading days in a year — this is industry standard
    annual_vol = daily_vol * np.sqrt(252)

    return annual_vol

def calculate_sharpe(returns, risk_free_rate=None):
    # if no rate is provided, fetch the current rate live from yfinance
    if risk_free_rate is None:
        risk_free_rate = get_risk_free_rate()

    daily_mean = returns.mean()
    daily_rf = risk_free_rate / 252
    excess_return = daily_mean - daily_rf
    daily_vol = returns.std()
    sharpe = (excess_return * 252) / (daily_vol * np.sqrt(252))

    return sharpe

def calculate_beta(returns, market_ticker="SPY"):
    # download market returns separately using our existing function
    from main import get_stock_data, calculate_returns

    # get market price data and convert to returns
    market_prices = get_stock_data(market_ticker, period="1y")
    market_returns = market_prices["Close"].pct_change().dropna()

    betas = {}  # empty dict to store each asset's beta

    for ticker in returns.columns:  # loop over each asset in the portfolio
        # align dates — both series must have the same trading days
        aligned = returns[ticker].align(market_returns, join="inner")
        asset_ret = aligned[0]
        market_ret = aligned[1]

        # covariance measures how asset and market move together
        covariance = asset_ret.cov(market_ret)

        # variance measures how much the market moves on its own
        variance = market_ret.var()

        # beta = covariance / variance
        betas[ticker] = covariance / variance

    # convert dict to a pandas Series for clean output
    return pd.Series(betas)

def calculate_max_drawdown(returns):
    # convert daily returns to cumulative growth
    # e.g. [0.01, -0.02, 0.03] becomes [1.01, 0.99, 1.02...]
    cumulative = (1 + returns).cumprod()

    # at each day, find the highest point reached SO FAR
    # this is the "peak" we're measuring the drop from
    running_max = cumulative.cummax()

    # calculate how far we've dropped from the peak at each day
    # e.g. if peak was 1.5 and now we're at 1.2 → drawdown = (1.2-1.5)/1.5 = -20%
    drawdown = (cumulative - running_max) / running_max

    # return the worst (most negative) drawdown for each asset
    max_drawdown = drawdown.min()

    return max_drawdown

def calculate_var(returns, confidence=0.95):
    # sort daily returns from worst to best for each asset
    # the 5th percentile (for 95% confidence) is the cutoff loss level
    var = returns.quantile(1 - confidence)

    # var is negative (it's a loss) — we return it as-is so callers see the sign
    return var

def calculate_portfolio_var(returns, holdings, confidence=0.95):
    # build a dictionary mapping each ticker to its portfolio weight
    weights = {h["ticker"]: h["weight"] for h in holdings}

    # compute the daily return of the combined weighted portfolio
    portfolio_returns = sum(
        returns[ticker] * weights[ticker]
        for ticker in returns.columns
        if ticker in weights
    )

    # the VaR is the return at the (1 - confidence) percentile
    # e.g. at 95% confidence, we look at the worst 5% of days
    var = portfolio_returns.quantile(1 - confidence)

    return var

def calculate_correlation(returns):
    # .corr() computes the correlation between every pair of columns
    # result is a matrix: each cell = correlation between row asset and column asset
    # diagonal is always 1.0 (every asset perfectly correlates with itself)
    correlation_matrix = returns.corr()

    return correlation_matrix

def get_portfolio_summary(returns, benchmark="SPY"):
    rf_rate = get_risk_free_rate()

    summary = {
        "volatility": calculate_volatility(returns),
        "sharpe": calculate_sharpe(returns, risk_free_rate=rf_rate),
        "beta": calculate_beta(returns, market_ticker=benchmark),
        "max_drawdown": calculate_max_drawdown(returns),
        "var_95": calculate_var(returns, confidence=0.95),  # per-asset daily VaR at 95%
        "correlation": calculate_correlation(returns),
        "risk_free_rate": rf_rate,
    }

    return summary

def calculate_portfolio_metrics(returns, holdings, risk_free_rate=None):
    """
    Calculates Sharpe and Volatility for the entire portfolio as one unit,
    weighted by each asset's allocation.
    """
    # NaN-safe sentinel used when we can't compute metrics
    _nan_result = {
        "volatility": float("nan"),
        "sharpe": float("nan"),
        "annual_return": float("nan"),
        "max_drawdown": float("nan"),
        "var_95": float("nan"),
    }

    if risk_free_rate is None:
        risk_free_rate = get_risk_free_rate()

    # build weights dictionary from the input holdings list
    weights = {h["ticker"]: h["weight"] for h in holdings}

    # only use tickers that are present in BOTH the returns DataFrame and the weights dict
    # (a ticker gets dropped from returns when build_portfolio skips it due to bad data)
    valid_tickers = [t for t in returns.columns if t in weights]

    # bail out immediately if there's nothing to work with
    if not valid_tickers or returns.empty:
        print("WARNING: No valid tickers to compute portfolio metrics")
        return _nan_result

    # renormalize weights so they still sum to 1 after any tickers were skipped
    total_weight = sum(weights[t] for t in valid_tickers)

    try:
        # calculate daily weighted portfolio return using only the valid tickers
        portfolio_returns = sum(
            returns[t] * (weights[t] / total_weight)   # scaled weight so they add up to 1
            for t in valid_tickers
        )

        # debug prints — confirm we have real data before continuing
        print("DEBUG portfolio_returns head:\n", portfolio_returns.head())
        print("DEBUG std:", portfolio_returns.std(), "  mean:", portfolio_returns.mean())

        # if all returns are NaN even after filtering, give up gracefully
        if portfolio_returns.empty or portfolio_returns.isna().all():
            print("WARNING: portfolio_returns is empty or all NaN — cannot compute metrics")
            return _nan_result

        # annualized portfolio volatility
        portfolio_vol = portfolio_returns.std() * (252 ** 0.5)

        # annualized portfolio return
        portfolio_annual_return = portfolio_returns.mean() * 252

        # portfolio sharpe ratio
        portfolio_sharpe = (portfolio_annual_return - risk_free_rate) / portfolio_vol

        # portfolio max drawdown
        cumulative = (1 + portfolio_returns).cumprod()
        rolling_max = cumulative.cummax()
        drawdown = (cumulative - rolling_max) / rolling_max
        portfolio_mdd = drawdown.min()

        # portfolio VaR at 95% — worst daily loss we'd expect 95% of the time
        portfolio_var = portfolio_returns.quantile(0.05)

        return {
            "volatility": portfolio_vol,
            "sharpe": portfolio_sharpe,
            "annual_return": portfolio_annual_return,
            "max_drawdown": portfolio_mdd,
            "var_95": portfolio_var,
        }

    except Exception as e:
        # catch any unexpected error so the whole app doesn't crash
        print(f"ERROR in calculate_portfolio_metrics: {e}")
        return _nan_result


# ── Test ────────────────────────────────────────────────────

if __name__ == "__main__":
    from main import build_portfolio, calculate_returns

    my_portfolio = [
        {"ticker": "AAPL", "weight": 0.4},
        {"ticker": "SPY",  "weight": 0.4},
        {"ticker": "TLT",  "weight": 0.2},
    ]

    prices = build_portfolio(my_portfolio)
    returns = calculate_returns(prices)

    # one function call to get everything
    summary = get_portfolio_summary(returns)

    print("=== Portfolio Risk Summary ===")
    print("\nRisk-Free Rate:", round(summary["risk_free_rate"] * 100, 3), "%")
    print("\nVolatility:\n", summary["volatility"].round(4))
    print("\nSharpe Ratio:\n", summary["sharpe"].round(4))
    print("\nBeta:\n", summary["beta"].round(4))
    print("\nMax Drawdown:\n", summary["max_drawdown"].round(4))
    print("\nCorrelation Matrix:\n", summary["correlation"].round(4))