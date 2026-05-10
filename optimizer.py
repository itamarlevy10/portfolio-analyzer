import pandas as pd
import numpy as np
from pypfopt import EfficientFrontier, expected_returns, risk_models

# ── Portfolio Optimizer ──────────────────────────────────────
# Uses PyPortfolioOpt (Modern Portfolio Theory) to find the
# mathematically optimal asset weights for a given goal.

# Target weight bounds — applied to every function below
_MIN_W = 0.05   # every asset gets at least 5% (ensures meaningful presence)
_MAX_W = 0.40   # no single asset can exceed 40% (prevents over-concentration)


def _feasible_bounds(n):
    # with n assets summing to 1, (min, max) must satisfy: n*max >= 1 and n*min <= 1
    # for n=2 the 40% cap would be infeasible (0.40+0.40=0.80 < 1), so we relax
    lo = min(_MIN_W, 1.0 / n)              # floor can't be above equal-weight
    hi = max(_MAX_W, 1.0 / n)              # ceiling can't be below equal-weight
    return (lo, hi)


def _max_feasible_return(mu):
    # greedily assign the maximum allowed weight to the highest-return assets first
    # all assets start at their minimum; we distribute remaining weight downward
    n = len(mu)
    lo, hi = _feasible_bounds(n)
    w = pd.Series(lo, index=mu.index)     # everyone starts at the floor
    remaining = 1.0 - n * lo              # slack after assigning minimums
    for idx in mu.sort_values(ascending=False).index:
        extra = min(hi - lo, remaining)   # at most (hi - lo) extra per asset
        w[idx] += extra
        remaining -= extra
        if remaining <= 1e-9:
            break
    return float(w @ mu)


def optimize_portfolio(returns, strategy="max_sharpe", risk_free_rate=0.05):
    # drop rows with any NaN so every asset has data on every date
    returns = returns.dropna()

    # rebuild a price series from returns so PyPortfolioOpt can use it
    # we start at 100 and apply cumulative compounding: price_t = 100 * ∏(1 + r_i)
    prices = (1 + returns).cumprod() * 100

    # annualized expected return per asset — geometric mean, scaled by 252 trading days
    mu = expected_returns.mean_historical_return(prices, frequency=252)

    # covariance matrix using Ledoit-Wolf shrinkage instead of raw sample covariance
    # shrinkage regularises the matrix, making it more stable with limited history
    S = risk_models.CovarianceShrinkage(prices, frequency=252).ledoit_wolf()

    # per-asset weight bounds, relaxed automatically when n is small (e.g. only 2 assets)
    bounds = _feasible_bounds(len(mu))

    # create the EfficientFrontier solver (long-only, weights sum to 1)
    ef = EfficientFrontier(mu, S, weight_bounds=bounds)

    if strategy == "max_sharpe":
        # find the portfolio with the highest Sharpe ratio (return per unit of risk)
        ef.max_sharpe(risk_free_rate=risk_free_rate)

    elif strategy == "min_volatility":
        # find the portfolio with the lowest possible volatility regardless of return
        ef.min_volatility()

    elif strategy == "max_return":
        # compute the highest return achievable under the weight bounds, then target
        # 95% of it — slightly inside the boundary keeps the solver numerically stable
        ef.efficient_return(target_return=_max_feasible_return(mu) * 0.95)

    else:
        raise ValueError(
            f"Unknown strategy '{strategy}'. "
            "Choose 'max_sharpe', 'min_volatility', or 'max_return'."
        )

    # round very small weights to zero and normalise so they sum exactly to 1
    raw_weights = ef.clean_weights()

    # compute the three performance numbers for this portfolio
    expected_ret, volatility, sharpe = ef.portfolio_performance(
        risk_free_rate=risk_free_rate,
        verbose=False,
    )

    return {
        "weights": dict(raw_weights),    # {ticker: weight}, sums to 1
        "expected_return": expected_ret, # annualised expected return (decimal)
        "volatility": volatility,        # annualised standard deviation (decimal)
        "sharpe": sharpe,                # Sharpe ratio of the optimised portfolio
    }


def get_efficient_frontier(returns, n_points=100):
    # generate n_points random portfolios via Monte Carlo simulation
    # each portfolio has random weights that sum to 1 (long-only, unconstrained)
    # the cloud visualises the full opportunity set; the frontier line shows the optimal edge

    returns = returns.dropna()
    n_assets = len(returns.columns)
    tickers = list(returns.columns)

    mu = returns.mean() * 252           # annualised expected return per asset
    cov = returns.cov() * 252           # annualised covariance matrix

    results = []

    for _ in range(n_points):
        # sample random weights that sum to 1
        raw = np.random.random(n_assets)
        weights = raw / raw.sum()

        port_return = float(np.dot(weights, mu))
        port_vol = float(np.sqrt(weights @ cov.values @ weights))
        port_sharpe = port_return / port_vol if port_vol > 0 else 0.0

        row = {"volatility": port_vol, "return": port_return, "sharpe": port_sharpe}
        # store each asset's weight so hover and click-to-select can show them
        for t, w in zip(tickers, weights):
            row[t] = w

        results.append(row)

    return pd.DataFrame(results)


def get_efficient_frontier_line(returns, n_points=40, risk_free_rate=0.05):
    # trace the actual efficient frontier — the left-most edge of the opportunity set
    # for each target return level, solve for the minimum-variance portfolio
    # connecting these optimal portfolios draws the "efficient frontier" curve

    returns = returns.dropna()
    tickers = list(returns.columns)
    prices = (1 + returns).cumprod() * 100

    mu = expected_returns.mean_historical_return(prices, frequency=252)
    S = risk_models.CovarianceShrinkage(prices, frequency=252).ledoit_wolf()
    bounds = _feasible_bounds(len(mu))

    # lower bound: return of the minimum-volatility portfolio
    ef_min = EfficientFrontier(mu, S, weight_bounds=bounds)
    ef_min.min_volatility()
    min_ret, _, _ = ef_min.portfolio_performance(verbose=False)

    # upper bound: highest return achievable under the weight constraints
    max_ret = _max_feasible_return(mu) * 0.95

    if max_ret <= min_ret:
        return pd.DataFrame()   # degenerate case — frontier is a single point

    # evenly spaced return targets from the min-vol point to the max-return point
    targets = np.linspace(min_ret, max_ret, n_points)

    line_points = []
    for target in targets:
        try:
            ef = EfficientFrontier(mu, S, weight_bounds=bounds)
            ef.efficient_return(target_return=target)
            w = ef.clean_weights()
            ret, vol, sharpe = ef.portfolio_performance(
                risk_free_rate=risk_free_rate, verbose=False
            )
            row = {"volatility": vol, "return": ret, "sharpe": sharpe}
            # store weights so clicking a frontier-line point also shows the allocation
            for t in tickers:
                row[t] = w.get(t, 0.0)
            line_points.append(row)
        except Exception:
            continue   # skip any infeasible target (can happen at the boundaries)

    return pd.DataFrame(line_points)
