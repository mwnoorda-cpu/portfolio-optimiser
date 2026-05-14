import logging
import yfinance as yf

logging.getLogger("yfinance").setLevel(logging.CRITICAL)


YAHOO_SUFFIXES = [
    ".AS",  # Amsterdam
    ".DE",  # Xetra / Germany
    ".F",   # Frankfurt
    ".PA",  # Paris
    ".MI",  # Milan
    ".L",   # London
    ".SW",  # Switzerland
]


def candidate_yahoo_tickers(symbol: str) -> list[str]:
    symbol = str(symbol).strip()

    candidates = [symbol]
    candidates += [f"{symbol}{suffix}" for suffix in YAHOO_SUFFIXES]

    return list(dict.fromkeys(candidates))


def is_valid_yahoo_ticker(yahoo_ticker: str) -> bool:
    try:
        data = yf.download(
            yahoo_ticker,
            period="1mo",
            progress=False,
            threads=False,
            auto_adjust=False,
        )
        return not data.empty
    except Exception:
        return False


def resolve_yahoo_ticker(symbol: str) -> str | None:
    for candidate in candidate_yahoo_tickers(symbol):
        if is_valid_yahoo_ticker(candidate):
            return candidate

    return None