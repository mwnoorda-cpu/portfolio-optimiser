from pathlib import Path
import pandas as pd

from src.db.connection import get_connection

SOURCE_PATH = Path("data/processed/mapped_degiro_universe.csv")


def infer_provider(product: str) -> str | None:
    if not isinstance(product, str):
        return None

    text = product.lower()

    provider_patterns = {
        "iShares": ["ishares"],
        "Vanguard": ["vanguard"],
        "SPDR": ["spdr"],
        "Xtrackers": ["xtrackers", "db x-trackers"],
        "Amundi": ["amundi"],
        "Invesco": ["invesco"],
        "WisdomTree": ["wisdomtree", "wisdom tree"],
        "UBS": ["ubs"],
        "JPM": ["jpm", "j.p. morgan", "jp morgan", "jpmorgan"],
        "HSBC": ["hsbc"],
        "Lyxor": ["lyxor"],
        "VanEck": ["vaneck", "van eck"],
        "BNP Paribas": ["bnp"],
        "DWS": ["dws"],
        "Franklin": ["franklin"],
        "Fidelity": ["fidelity"],
        "Legal & General": ["l&g", "legal & general", "lgim"],
        "Global X": ["global x"],
        "HANetf": ["hanetf"],
        "Rize": ["rize"],
        "Tabula": ["tabula"],
        "21Shares": ["21shares"],
        "CoinShares": ["coinshares"],
    }

    for provider, patterns in provider_patterns.items():
        if any(pattern in text for pattern in patterns):
            return provider

    return None


def main():
    if not SOURCE_PATH.exists():
        raise FileNotFoundError(f"Missing file: {SOURCE_PATH}")

    df = pd.read_csv(SOURCE_PATH, encoding="utf-8-sig")

    column_map = {
        "isin": "isin",
        "product": "product",
        "symbol": "symbol",
        "yahoo_ticker": "yahoo_ticker",
        "benchmark": "benchmark",
        "region": "region",
        "currency": "currency",
        "total_expense_ratio": "total_expense_ratio",
        "mapping_status": "mapping_status",
    }

    out = pd.DataFrame()

    for source_col, target_col in column_map.items():
        out[target_col] = df[source_col] if source_col in df.columns else None

    out["provider"] = out["product"].apply(infer_provider)

    out["replication_method"] = None
    out["lookthrough_quality"] = None
    out["economic_exposure_basis"] = None

    con = get_connection()

    con.execute("DELETE FROM etf_universe")
    con.register("universe_df", out)

    con.execute("""
        INSERT INTO etf_universe (
            isin,
            product,
            symbol,
            yahoo_ticker,
            benchmark,
            region,
            currency,
            total_expense_ratio,
            mapping_status,
            provider,
            replication_method,
            lookthrough_quality,
            economic_exposure_basis
        )
        SELECT
            isin,
            product,
            symbol,
            yahoo_ticker,
            benchmark,
            region,
            currency,
            total_expense_ratio,
            mapping_status,
            provider,
            replication_method,
            lookthrough_quality,
            economic_exposure_basis
        FROM universe_df
    """)

    count = con.execute("SELECT COUNT(*) FROM etf_universe").fetchone()[0]

    mapped = con.execute("""
        SELECT COUNT(*) FROM etf_universe
        WHERE mapping_status = 'mapped'
    """).fetchone()[0]

    provider_breakdown = con.execute("""
        SELECT provider, COUNT(*) AS etf_count
        FROM etf_universe
        GROUP BY provider
        ORDER BY etf_count DESC
    """).fetchdf()

    con.close()

    print(f"Loaded {count} ETFs into etf_universe")
    print(f"Mapped ETFs: {mapped}")
    print(provider_breakdown)


if __name__ == "__main__":
    main()