import pandas as pd


def covariance_matrix(
    returns: pd.DataFrame,
    periods_per_year: int = 252,
) -> pd.DataFrame:
    return returns.cov() * periods_per_year