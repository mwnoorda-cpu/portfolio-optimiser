from __future__ import annotations

import argparse
from pathlib import Path

from portfolio_optimiser.data.ishares_holdings import get_ishares_holdings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download iShares ETF holdings from an iShares product page."
    )

    parser.add_argument(
        "--isin",
        required=True,
        help="Fund ISIN, e.g. DE0002635307",
    )

    parser.add_argument(
        "--product-url",
        required=True,
        help="Full iShares product page URL",
    )

    parser.add_argument(
        "--output-dir",
        default="data/raw/ishares",
        help="Output folder for holdings CSV files",
    )

    parser.add_argument(
        "--as-of-date",
        default=None,
        help="Optional holdings date, format YYYY-MM-DD. Not all iShares endpoints support this.",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print candidate holdings URLs and failed attempts.",
    )

    args = parser.parse_args()

    result = get_ishares_holdings(
        isin=args.isin,
        product_page_url=args.product_url,
        as_of_date=args.as_of_date,
        debug=args.debug,
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    date_suffix = f"_{args.as_of_date}" if args.as_of_date else ""
    output_file = output_dir / f"{args.isin}_holdings{date_suffix}.csv"

    result.data.to_csv(output_file, index=False)

    print("SUCCESS")
    print(f"ISIN: {result.isin}")
    print(f"Rows: {result.rows}")
    print(f"Product page: {result.product_page_url}")
    print(f"Holdings URL: {result.holdings_url}")
    print(f"Output file: {output_file}")


if __name__ == "__main__":
    main()