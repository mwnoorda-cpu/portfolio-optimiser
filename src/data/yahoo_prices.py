import yfinance as yf


def get_prices(tickers, start="2024-01-01"):
    data = yf.download(
        tickers,
        start=start,
        progress=False,
        threads=False,
        auto_adjust=False,
    )

    if data.empty:
        raise RuntimeError("No price data returned from Yahoo Finance.")

    return data["Close"]