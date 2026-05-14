from pathlib import Path
import time
import pandas as pd

from src.data.degiro_universe import get_degiro_core_selection
from src.data.yahoo_mapper import resolve_yahoo_ticker

OUTPUT_PATH = Path("data/processed/mapped_degiro_universe.csv")


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    df = get_degiro_core_selection()
    results = []

    total = len(df)

    for i, row in df.iterrows():
        symbol = row.get("symbol")
        product = row.get("product")

        print(f"[{i + 1}/{total}] Mapping {symbol} - {product}")

        yahoo_ticker = resolve_yahoo_ticker(symbol)

        item = row.to_dict()
        item["yahoo_ticker"] = yahoo_ticker
        item["mapping_status"] = "mapped" if yahoo_ticker else "unmapped"

        results.append(item)

        # Small delay to reduce Yahoo rate-limit risk
        time.sleep(0.2)

    mapped = pd.DataFrame(results)
    mapped.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print(f"Saved mapped universe to {OUTPUT_PATH}")
    print(mapped["mapping_status"].value_counts(dropna=False))


if __name__ == "__main__":
    main()