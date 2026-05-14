import pandas as pd


def calculate_returns(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.pct_change().dropna()


def annualized_return(returns: pd.DataFrame, periods_per_year: int = 252) -> pd.Series:
    return (1 + returns).prod() ** (periods_per_year / len(returns)) - 1


def annualized_volatility(returns: pd.DataFrame, periods_per_year: int = 252) -> pd.Series:
    return returns.std() * periods_per_year**0.5


def downside_deviation(
    returns: pd.DataFrame,
    target_return: float = 0.0,
    periods_per_year: int = 252,
) -> pd.Series:
    downside = returns.where(returns < target_return, 0)
    return downside.std() * periods_per_year**0.5


def sharpe_ratio(returns: pd.DataFrame, risk_free_rate: float = 0.0) -> pd.Series:
    ann_ret = annualized_return(returns)
    ann_vol = annualized_volatility(returns)
    return (ann_ret - risk_free_rate) / ann_vol


def sortino_ratio(
    returns: pd.DataFrame,
    risk_free_rate: float = 0.0,
    target_return: float = 0.0,
) -> pd.Series:
    ann_ret = annualized_return(returns)
    downside_vol = downside_deviation(returns, target_return)
    return (ann_ret - risk_free_rate) / downside_vol


def max_drawdown(returns: pd.DataFrame) -> pd.Series:
    wealth = (1 + returns).cumprod()
    running_max = wealth.cummax()
    drawdown = wealth / running_max - 1
    return drawdown.min()


def calmar_ratio(returns: pd.DataFrame) -> pd.Series:
    ann_ret = annualized_return(returns)
    mdd = max_drawdown(returns).abs()
    return ann_ret / mdd

def summary_table(
    returns: pd.DataFrame,
    risk_free_rate: float = 0.0,
) -> pd.DataFrame:
    table = pd.DataFrame({
        "Annualized Return": annualized_return(returns),
        "Annualized Volatility": annualized_volatility(returns),
        "Downside Deviation": downside_deviation(returns),
        "Sharpe Ratio": sharpe_ratio(returns, risk_free_rate),
        "Sortino Ratio": sortino_ratio(returns, risk_free_rate),
        "Max Drawdown": max_drawdown(returns),
        "Calmar Ratio": calmar_ratio(returns),
    })

    return table.sort_values("Sharpe Ratio", ascending=False)


def correlation_matrix(returns: pd.DataFrame) -> pd.DataFrame:
    return returns.corr()