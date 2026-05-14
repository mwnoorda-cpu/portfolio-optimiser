from src.data.holdings_providers.ishares_discovery import (
    discover_ishares_holdings_url,
)

# Test iShares ETF ISIN
isin = "DE0002635307"

result = discover_ishares_holdings_url(isin)

print(result)