from pathlib import Path
import pandas as pd


def extract_ishares_as_of_date(file_path: str | Path) -> str | None:
    meta = pd.read_csv(
        file_path,
        nrows=1,
        header=None,
        encoding="utf-8-sig",
    )

    # Expected first row: Fund Holdings as of,13-May-2026
    if meta.shape[1] < 2:
        return None

    raw_date = meta.iloc[0, 1]

    parsed = pd.to_datetime(raw_date, errors="coerce")

    if pd.isna(parsed):
        return None

    return parsed.date().isoformat()


def parse_ishares_holdings(file_path: str | Path) -> tuple[pd.DataFrame, str | None]:
    as_of_date = extract_ishares_as_of_date(file_path)

    df = pd.read_csv(
        file_path,
        skiprows=2,
        encoding="utf-8-sig",
    )

    df.columns = [
        str(col).strip().lower().replace(" ", "_")
        for col in df.columns
    ]

    column_mapping = {
        "ticker": "holding_ticker",
        "name": "holding_name",
        "weight_(%)": "holding_weight",
        "sector": "sector",
        "location": "country",
        "market_currency": "currency",
    }

    out = pd.DataFrame()

    for source_col, target_col in column_mapping.items():
        out[target_col] = df[source_col] if source_col in df.columns else None

    out["holding_weight"] = pd.to_numeric(
        out["holding_weight"],
        errors="coerce",
    )

    out = out[out["holding_name"].notna()].copy()

    return out, as_of_date