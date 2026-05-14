import pandas as pd

from src.db.connection import get_connection

# For now: fake portfolio with 100% in the test iShares ETF
PORTFOLIO = {
    "DE0002635307": 1.00,
}


def main():
    con = get_connection()

    portfolio_df = pd.DataFrame(
        [
            {"etf_isin": isin, "portfolio_weight": weight}
            for isin, weight in PORTFOLIO.items()
        ]
    )

    con.register("portfolio_df", portfolio_df)

    lookthrough = con.execute("""
        SELECT
            h.etf_isin,
            p.portfolio_weight,
            h.holding_name,
            h.holding_ticker,
            h.sector,
            h.country,
            h.currency,
            h.holding_weight / 100 AS etf_holding_weight,
            p.portfolio_weight * h.holding_weight / 100 AS effective_weight
        FROM etf_holdings h
        JOIN portfolio_df p
            ON h.etf_isin = p.etf_isin
        ORDER BY effective_weight DESC
    """).fetchdf()

    sector = con.execute("""
        SELECT
            h.sector,
            SUM(p.portfolio_weight * h.holding_weight / 100) AS effective_weight
        FROM etf_holdings h
        JOIN portfolio_df p
            ON h.etf_isin = p.etf_isin
        GROUP BY h.sector
        ORDER BY effective_weight DESC
    """).fetchdf()

    con.close()

    print("\nTop look-through holdings")
    print(lookthrough.head(20))

    print("\nSector exposure")
    print(sector)


if __name__ == "__main__":
    main()