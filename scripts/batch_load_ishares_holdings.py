from pathlib import Path
import time
import pandas as pd

from src.db.connection import get_connection
from src.data.holdings_providers.ishares import download_ishares_holdings_from_url
from src.data.holdings_providers.ishares_discovery import discover_ishares_holdings_url
from src.data.holdings_providers.ishares_parser import parse_ishares_holdings

FAILURE_LOG = Path("data/processed/ishares_holdings_failures.csv")
SUCCESS_LOG = Path("data/processed/ishares_holdings_successes.csv")


def load_holdings_to_db(etf_isin: str, provider: str, source_file: str):
    holdings, as_of_date = parse_ishares_holdings(source_file)

    if as_of_date is None:
        raise ValueError("Could not extract as_of_date.")

    holdings["etf_isin"] = etf_isin
    holdings["as_of_date"] = as_of_date
    holdings["holding_isin"] = None
    holdings["provider"] = provider
    holdings["exposure_type"] = "reported_holdings"
    holdings["source_file"] = source_file

    holdings = holdings[
        [
            "etf_isin",
            "as_of_date",
            "holding_isin",
            "holding_name",
            "holding_ticker",
            "holding_weight",
            "sector",
            "country",
            "currency",
            "provider",
            "exposure_type",
            "source_file",
        ]
    ]

    con = get_connection()

    con.execute(
        """
        DELETE FROM etf_holdings
        WHERE etf_isin = ?
          AND as_of_date = ?
          AND provider = ?
        """,
        [etf_isin, as_of_date, provider],
    )

    con.register("holdings_df", holdings)

    con.execute(
        """
        INSERT INTO etf_holdings (
            etf_isin,
            as_of_date,
            holding_isin,
            holding_name,
            holding_ticker,
            holding_weight,
            sector,
            country,
            currency,
            provider,
            exposure_type,
            source_file
        )
        SELECT
            etf_isin,
            as_of_date,
            holding_isin,
            holding_name,
            holding_ticker,
            holding_weight,
            sector,
            country,
            currency,
            provider,
            exposure_type,
            source_file
        FROM holdings_df
        """
    )

    con.close()

    return as_of_date, len(holdings), holdings["holding_weight"].sum()


def main():
    con = get_connection()

    universe = con.execute(
        """
        SELECT isin, product, symbol, yahoo_ticker
        FROM etf_universe
        WHERE provider = 'iShares'
          AND isin IS NOT NULL
          AND symbol IS NOT NULL
        ORDER BY product
        """
    ).fetchdf()

    con.close()

    failures = []
    successes = []

    total = len(universe)

    for i, row in universe.iterrows():
        etf_isin = row["isin"]
        product = row["product"]
        symbol = row["symbol"]

        print(f"[{i + 1}/{total}] {symbol} | {etf_isin} | {product}")

        try:
            discovery = discover_ishares_holdings_url(etf_isin)

            if discovery["status"] != "found":
                raise ValueError(discovery["status"])

            raw_file = download_ishares_holdings_from_url(
                url=discovery["holdings_url"],
                output_name=f"{etf_isin}_{symbol}_holdings.csv",
            )

            as_of_date, rows_loaded, total_weight = load_holdings_to_db(
                etf_isin=etf_isin,
                provider="iShares",
                source_file=str(raw_file),
            )

            successes.append(
                {
                    "isin": etf_isin,
                    "symbol": symbol,
                    "product": product,
                    "product_page_url": discovery["product_page_url"],
                    "product_id": discovery["product_id"],
                    "holdings_url": discovery["holdings_url"],
                    "as_of_date": as_of_date,
                    "rows_loaded": rows_loaded,
                    "total_weight": total_weight,
                }
            )

            print(
                f"  Loaded {rows_loaded} rows | "
                f"as_of_date={as_of_date} | "
                f"weight={total_weight:.2f}"
            )

            time.sleep(0.5)

        except Exception as e:
            failures.append(
                {
                    "isin": etf_isin,
                    "symbol": symbol,
                    "product": product,
                    "reason": str(e),
                }
            )
            print(f"  FAILED: {e}")
            time.sleep(0.5)

    FAILURE_LOG.parent.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(successes).to_csv(
        SUCCESS_LOG,
        index=False,
        encoding="utf-8-sig",
    )

    pd.DataFrame(failures).to_csv(
        FAILURE_LOG,
        index=False,
        encoding="utf-8-sig",
    )

    print("\nDone.")
    print(f"Successes: {len(successes)}")
    print(f"Failures: {len(failures)}")
    print(f"Success log: {SUCCESS_LOG}")
    print(f"Failure log: {FAILURE_LOG}")


if __name__ == "__main__":
    main()