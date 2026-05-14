import pandas as pd


def normalize_from_common_start(
    prices: pd.DataFrame,
    base_value: float = 100.0,
) -> pd.DataFrame:
    """
    Normalize all series from the first date
    where every selected ETF has valid data.
    """

    common_prices = prices.dropna()

    if common_prices.empty:
        return common_prices

    first_row = common_prices.iloc[0]

    return common_prices.divide(first_row) * base_value


def normalize_from_first_valid(
    prices: pd.DataFrame,
    base_value: float = 100.0,
) -> pd.DataFrame:
    """
    Normalize each series independently
    from its own first valid observation.
    """

    first_valid_prices = prices.apply(
        lambda col: col.dropna().iloc[0]
    )

    return prices.divide(first_valid_prices) * base_value