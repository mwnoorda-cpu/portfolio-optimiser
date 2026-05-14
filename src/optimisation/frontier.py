import numpy as np
import pandas as pd

from src.analytics.portfolio_stats import (
    portfolio_return,
    portfolio_volatility,
    portfolio_sharpe,
)


def random_portfolios(
    expected_returns: pd.Series,
    covariance_matrix: pd.DataFrame,
    risk_free_rate: float = 0.0,
    n_portfolios: int = 5_000,
    max_weight: float = 0.40,
    random_seed: int = 42,
) -> pd.DataFrame:
    rng = np.random.default_rng(random_seed)
    tickers = expected_returns.index.tolist()
    results = []

    for _ in range(n_portfolios):
        weights = rng.random(len(tickers))
        weights = weights / weights.sum()

        if weights.max() > max_weight:
            continue

        weights_series = pd.Series(weights, index=tickers)

        results.append({
            "Expected Return": portfolio_return(weights_series, expected_returns),
            "Expected Volatility": portfolio_volatility(weights_series, covariance_matrix),
            "Sharpe Ratio": portfolio_sharpe(
                weights_series,
                expected_returns,
                covariance_matrix,
                risk_free_rate,
            ),
        })

    return pd.DataFrame(results)