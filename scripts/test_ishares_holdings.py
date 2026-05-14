from pathlib import Path

from portfolio_optimiser.data.ishares_holdings import get_ishares_holdings


fund_isin = "DE0002635307"

result = get_ishares_holdings(
    isin=fund_isin,
    product_page_url=(
        "https://www.ishares.com/ch/individual/en/products/251931/"
        "ishares-stoxx-europe-600-ucits-etf-de-fund"
    ),
    debug=False,
)

output_dir = Path("data/raw/ishares")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / f"{fund_isin}_holdings.csv"
result.data.to_csv(output_file, index=False)

print("SUCCESS")
print(
    {
        "isin": result.isin,
        "product_page_url": result.product_page_url,
        "holdings_url": result.holdings_url,
        "rows": result.rows,
        "output_file": str(output_file),
    }
)