import yfinance as yf
import pandas as pd
import numpy as np

# vectorbt is installed and available for advanced portfolio analytics
# the core simulation below uses pandas for clarity and line-by-line transparency


def run_backtest(holdings, period="5y"):
    # extract ticker symbols from the holdings list
    tickers = [h["ticker"] for h in holdings]

    # build a dict so we can look up any ticker's weight in O(1)
    weights_dict = {h["ticker"]: h["weight"] for h in holdings}

    # always include SPY so we can benchmark regardless of whether the user holds it
    all_tickers = list(set(tickers + ["SPY"]))

    # --- Download Price Data ----------------------------------------

    # download closing prices one ticker at a time — consistent with the rest of the codebase
    prices_raw = {}
    for ticker in all_tickers:
        try:
            stock = yf.Ticker(ticker)                        # create a yfinance object for the ticker
            hist = stock.history(period=period)              # fetch full OHLCV history for the period
            prices_raw[ticker] = hist["Close"]               # keep only end-of-day closing prices
        except Exception:
            pass                                             # skip tickers that fail (e.g., delisted)

    # combine all individual price Series into one aligned DataFrame
    prices_df = pd.DataFrame(prices_raw)

    # filter out tickers whose entire price column is NaN (delisted / bad symbols)
    valid_tickers = [t for t in tickers if t in prices_df.columns and not prices_df[t].isna().all()]
    skipped = [t for t in tickers if t not in valid_tickers]
    for t in skipped:
        print(f"WARNING: No price data for {t} in backtester — skipping (possibly delisted)")

    # bail out early if no valid tickers remain
    if not valid_tickers:
        raise ValueError("No price data returned for any of the selected tickers and period.")

    # keep only rows where every valid portfolio ticker has data
    port_prices = prices_df[valid_tickers].dropna()

    # renormalize weights so they still sum to 1 after skipping bad tickers
    total_weight = sum(weights_dict[t] for t in valid_tickers)
    weights_dict = {t: weights_dict[t] / total_weight for t in valid_tickers}

    # SPY price series, also aligned to the same rows later
    spy_raw = prices_df["SPY"] if "SPY" in prices_df.columns else None

    # bail out early if there is no data (bad period, de-listed tickers, etc.)
    if port_prices.empty:
        raise ValueError("No price data returned for the selected tickers and period.")

    # --- Monthly Rebalancing Simulation ----------------------------------------

    INITIAL_VALUE = 10_000.0                                 # starting portfolio value in USD

    # find the first calendar day of every month covered by the data
    month_starts = port_prices.resample("MS").first().index  # "MS" = month start frequency

    # map each calendar month-start to the nearest actual trading day
    actual_rebalance_dates = set()
    for d in month_starts:
        future_dates = port_prices.index[port_prices.index >= d]  # trading days on or after d
        if len(future_dates) > 0:
            actual_rebalance_dates.add(future_dates[0])      # first real trading day in that month

    # track how many fractional shares we hold for each ticker
    current_shares = {}

    # accumulate daily portfolio values into a plain list (faster than Series appends)
    daily_values = []

    for date in port_prices.index:                           # iterate over every trading day
        prices_today = port_prices.loc[date]                 # today's closing price for every ticker

        if date in actual_rebalance_dates or len(current_shares) == 0:
            # rebalance: recalculate total value, then reset share counts to hit target weights

            if len(current_shares) == 0:
                current_val = INITIAL_VALUE                  # very first day — use starting cash
            else:
                # today's value before rebalancing (mark-to-market at today's open equivalent)
                current_val = sum(
                    current_shares[t] * prices_today[t] for t in valid_tickers
                )

            # buy exactly the right number of fractional shares per ticker
            current_shares = {}
            for t in valid_tickers:
                dollars_for_ticker = current_val * weights_dict[t]   # dollar allocation
                current_shares[t] = dollars_for_ticker / prices_today[t]  # shares = dollars / price

        # mark the portfolio to market at today's closing prices
        val = sum(current_shares[t] * prices_today[t] for t in valid_tickers)
        daily_values.append(val)

    # wrap the list into a time-indexed Series
    portfolio_series = pd.Series(daily_values, index=port_prices.index)

    # --- Compute Portfolio Metrics ----------------------------------------

    # day-over-day percentage changes (first row becomes NaN, so we drop it)
    daily_returns = portfolio_series.pct_change().dropna()

    # total return: end value / start value − 1
    total_return = (portfolio_series.iloc[-1] / portfolio_series.iloc[0]) - 1

    # annualised return (CAGR) — scales total return to a per-year basis
    n_years = len(daily_returns) / 252             # 252 = average trading days per year
    annual_return = (1 + total_return) ** (1 / n_years) - 1

    # maximum drawdown — the deepest peak-to-trough fall across the whole period
    cum_normalized = portfolio_series / portfolio_series.iloc[0]   # normalize to 1.0 at start
    running_peak = cum_normalized.cummax()                          # highest value seen so far
    drawdown_series = (cum_normalized - running_peak) / running_peak  # negative when below peak
    max_drawdown = drawdown_series.min()                            # worst (most negative) value

    # Sharpe ratio — annualised return above the risk-free rate per unit of volatility
    RISK_FREE = 0.04                               # approximate risk-free rate (4% US T-bill)
    daily_rf = RISK_FREE / 252                     # convert annual risk-free rate to daily
    excess_returns = daily_returns - daily_rf      # daily return above the risk-free floor
    sharpe = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)  # annualise

    # single-day extremes
    best_day = daily_returns.max()                 # highest single-day gain
    worst_day = daily_returns.min()                # lowest single-day loss (negative)

    # monthly returns — resample to last trading day of each month, then take pct change
    monthly_vals = portfolio_series.resample("ME").last()   # month-end portfolio value
    monthly_returns = monthly_vals.pct_change().dropna()    # month-over-month % change

    # fraction of months that ended higher than they started
    months_positive = (monthly_returns > 0).mean()          # 0.0 – 1.0

    # --- SPY Benchmark ----------------------------------------

    spy_result = None
    if spy_raw is not None:
        # align SPY to the exact same dates as the portfolio (forward-fill any gaps)
        spy_aligned = spy_raw.reindex(port_prices.index).ffill().dropna()

        # normalise SPY to also start at $10,000 for an apples-to-apples comparison
        spy_series = (spy_aligned / spy_aligned.iloc[0]) * INITIAL_VALUE

        # compute the same set of metrics for SPY
        spy_daily = spy_series.pct_change().dropna()
        spy_total = (spy_series.iloc[-1] / spy_series.iloc[0]) - 1
        spy_n_years = len(spy_daily) / 252
        spy_annual = (1 + spy_total) ** (1 / spy_n_years) - 1

        spy_cum = spy_series / spy_series.iloc[0]
        spy_peak = spy_cum.cummax()
        spy_mdd = ((spy_cum - spy_peak) / spy_peak).min()

        spy_excess = spy_daily - daily_rf
        spy_sharpe = (spy_excess.mean() / spy_excess.std()) * np.sqrt(252)

        spy_result = {
            "portfolio_value": spy_series,         # daily SPY value normalised to $10,000
            "total_return": spy_total,             # total % return
            "annual_return": spy_annual,           # annualised % return
            "max_drawdown": spy_mdd,               # worst drawdown
            "sharpe": spy_sharpe,                  # Sharpe ratio
        }

    # return everything the UI needs
    return {
        "portfolio_value": portfolio_series,       # daily portfolio value starting at $10,000
        "total_return": total_return,              # total % return over the full period
        "annual_return": annual_return,            # annualised (CAGR) return
        "max_drawdown": max_drawdown,              # worst peak-to-trough loss (negative decimal)
        "sharpe": sharpe,                          # Sharpe ratio
        "best_day": best_day,                      # best single-day return
        "worst_day": worst_day,                    # worst single-day return
        "months_positive": months_positive,        # fraction of months with a gain
        "monthly_returns": monthly_returns,        # Series of monthly returns for bar chart
        "spy": spy_result,                         # benchmark dict (same keys) or None
    }
