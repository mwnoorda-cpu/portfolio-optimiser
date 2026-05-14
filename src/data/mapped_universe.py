from pathlib import Path
import pandas as pd

MAPPED_UNIVERSE_PATH = Path(
    "data/processed/mapped_degiro_universe.csv"
)


def get_mapped_universe() -> pd.DataFrame:
    df = pd.read_csv(MAPPED_UNIVERSE_PATH)

    df = df[df["mapping_status"] == "mapped"].copy()

    df = df[df["yahoo_ticker"].notna()].copy()

    return df.reset_index(drop=True)