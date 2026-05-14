from src.db.connection import get_connection


def main():
    provider = "iShares"

    con = get_connection()

    df = con.execute(
        """
        SELECT isin, product, symbol, yahoo_ticker
        FROM etf_universe
        WHERE provider = ?
        LIMIT 20
        """,
        [provider],
    ).fetchdf()

    con.close()

    print(df)


if __name__ == "__main__":
    main()