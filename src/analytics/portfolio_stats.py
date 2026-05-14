import numpy as np
import pandas as pd


def portfolio_return(
    weights: pd.Series,
    expected_returns: pd.Series,
) -> float:
    aligned_returns = expected_returns.loc[weights.index]
    return float(weights @ aligned_returns)


def portfolio_volatility(
    weights: pd.Series,
    covariance_matrix: pd.DataFrame,
) -> float:
    cov = covariance_matrix.loc[weights.index, weights.index]
    return float(np.sqrt(weights.values @ cov.values @ weights.values))


def portfolio_sharpe(
    weights: pd.Series,
    expected_returns: pd.Series,
    covariance_matrix: pd.DataFrame,
    risk_free_rate: float = 0.0,
) -> float:
    ret = portfolio_return(weights, expected_returns)
    vol = portfolio_volatility(weights, covariance_matrix)

    if vol == 0:
        return np.nan

    return (ret - risk_free_rate) / vol


def portfolio_summary(
    weights: pd.Series,
    expected_returns: pd.Series,
    covariance_matrix: pd.DataFrame,
    risk_free_rate: float = 0.0,
) -> pd.Series:
    ret = portfolio_return(weights, expected_returns)
    vol = portfolio_volatility(weights, covariance_matrix)
    sharpe = portfolio_sharpe(
        weights,
        expected_returns,
        covariance_matrix,
        risk_free_rate,
    )

    return pd.Series({
        "Expected Return": ret,
        "Expected Volatility": vol,
        "Sharpe Ratio": sharpe,
    })