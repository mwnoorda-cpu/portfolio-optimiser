from pathlib import Path
from io import StringIO
import requests
import pandas as pd

DEGIRO_CORE_SELECTION_URL = (
    "https://www.degiro.nl/assets/js/data/core-selection-list-nl.csv"
)

CACHE_PATH = Path("data/raw/degiro_core_selection.csv")


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [
        col.replace("\ufeff", "")
        .replace("ï»¿", "")
        .strip()
        .lower()
        .replace(" ", "_")
        for col in df.columns
    ]
    return df


def get_degiro_core_selection(force_refresh: bool = False) -> pd.DataFrame:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

    if CACHE_PATH.exists() and not force_refresh:
        df = pd.read_csv(CACHE_PATH, encoding="utf-8-sig")
    else:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0 Safari/537.36"
            )
        }

        response = requests.get(DEGIRO_CORE_SELECTION_URL, headers=headers, timeout=30)
        response.raise_for_status()

        df = pd.read_csv(StringIO(response.text), encoding="utf-8-sig")
        df.to_csv(CACHE_PATH, index=False, encoding="utf-8-sig")

    df = clean_columns(df)

    # Remove repeated header row inside the data
    if "product" in df.columns:
        df = df[df["product"].str.lower().ne("etf naam")]

    return df.reset_index(drop=True)