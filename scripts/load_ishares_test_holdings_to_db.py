from src.db.connection import get_connection
from src.data.holdings_providers.ishares_parser import parse_ishares_holdings

ETF_ISIN = "DE0002635307"
PROVIDER = "iShares"
SOURCE_FILE = "data/raw/holdings/ishares/ishares_test_holdings.csv"


def main():
    holdings, as_of_date = parse_ishares_holdings(SOURCE_FILE)

    if as_of_date is None:
        raise ValueError("Could not extract as_of_date from iShares file.")

    holdings["etf_isin"] = ETF_ISIN
    holdings["as_of_date"] = as_of_date
    holdings["holding_isin"] = None
    holdings["provider"] = PROVIDER
    holdings["exposure_type"] = "reported_holdings"
    holdings["source_file"] = SOURCE_FILE

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
        [ETF_ISIN, as_of_date, PROVIDER],
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

    check = con.execute(
        """
        SELECT
            etf_isin,
            as_of_date,
            COUNT(*) AS rows_loaded,
            SUM(holding_weight) AS total_weight
        FROM etf_holdings
        WHERE etf_isin = ?
          AND as_of_date = ?
        GROUP BY etf_isin, as_of_date
        """,
        [ETF_ISIN, as_of_date],
    ).fetchdf()

    con.close()

    print(check)


if __name__ == "__main__":
    main()