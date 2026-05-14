import numpy as np
import pandas as pd
from scipy.optimize import minimize


def portfolio_return(weights: np.ndarray, expected_returns: pd.Series) -> float:
    return float(weights @ expected_returns.values)


def portfolio_volatility(weights: np.ndarray, covariance_matrix: pd.DataFrame) -> float:
    return float(np.sqrt(weights @ covariance_matrix.values @ weights))


def negative_sharpe_ratio(
    weights: np.ndarray,
    expected_returns: pd.Series,
    covariance_matrix: pd.DataFrame,
    risk_free_rate: float = 0.0,
) -> float:
    port_return = portfolio_return(weights, expected_returns)
    port_vol = portfolio_volatility(weights, covariance_matrix)

    if port_vol == 0:
        return 999

    return -((port_return - risk_free_rate) / port_vol)


def max_sharpe_portfolio(
    expected_returns: pd.Series,
    covariance_matrix: pd.DataFrame,
    risk_free_rate: float = 0.0,
    max_weight: float = 0.40,
) -> pd.Series:
    n_assets = len(expected_returns)

    initial_weights = np.repeat(1 / n_assets, n_assets)

    bounds = tuple((0, max_weight) for _ in range(n_assets))

    constraints = {
        "type": "eq",
        "fun": lambda weights: np.sum(weights) - 1,
    }

    result = minimize(
        negative_sharpe_ratio,
        initial_weights,
        args=(expected_returns, covariance_matrix, risk_free_rate),
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
    )

    if not result.success:
        raise RuntimeError(f"Optimization failed: {result.message}")

    return pd.Series(
        result.x,
        index=expected_returns.index,
        name="Max Sharpe Weight",
    )

def min_volatility_portfolio(
    covariance_matrix: pd.DataFrame,
    max_weight: float = 0.40,
) -> pd.Series:
    n_assets = len(covariance_matrix)

    initial_weights = np.repeat(1 / n_assets, n_assets)

    bounds = tuple((0, max_weight) for _ in range(n_assets))

    constraints = {
        "type": "eq",
        "fun": lambda weights: np.sum(weights) - 1,
    }

    result = minimize(
        portfolio_volatility,
        initial_weights,
        args=(covariance_matrix,),
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
    )

    if not result.success:
        raise RuntimeError(f"Optimization failed: {result.message}")

    return pd.Series(
        result.x,
        index=covariance_matrix.index,
        name="Min Vol Weight",
    )