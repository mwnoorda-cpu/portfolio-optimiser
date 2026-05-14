import re
from urllib.parse import quote_plus, urljoin, urlparse, parse_qs, unquote

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.ishares.com"


def get_headers() -> dict:
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        )
    }


def clean_duckduckgo_url(url: str) -> str:
    parsed = urlparse(url)

    if "duckduckgo.com" not in parsed.netloc:
        return url

    qs = parse_qs(parsed.query)

    if "uddg" in qs:
        return unquote(qs["uddg"][0])

    return url


def find_ishares_product_page_by_isin(isin: str) -> str | None:
    query = quote_plus(f"site:ishares.com {isin} iShares")
    search_url = f"https://duckduckgo.com/html/?q={query}"

    response = requests.get(search_url, headers=get_headers(), timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    links = []

    for a in soup.find_all("a", href=True):
        href = clean_duckduckgo_url(a["href"])

        if "ishares.com" in href and "/products/" in href:
            links.append(href)

    product_links = [
        link
        for link in links
        if re.search(r"/products/\d+/", link)
    ]

    if not product_links:
        return None

    return product_links[0]


def extract_holdings_url_from_product_page(product_page_url: str) -> str | None:
    response = requests.get(product_page_url, headers=get_headers(), timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for a in soup.find_all("a", href=True):
        href = a.get("href", "")

        if (
            "fileType=csv" in href
            and "dataType=fund" in href
            and "holdings" in href.lower()
        ):
            return urljoin(BASE_URL, href.replace("&amp;", "&"))

    return None


def extract_product_id(product_page_url: str) -> str | None:
    match = re.search(r"/products/(\d+)/", product_page_url)
    if match:
        return match.group(1)
    return None


def discover_ishares_holdings_url(isin: str) -> dict:
    product_page_url = find_ishares_product_page_by_isin(isin)

    if product_page_url is None:
        return {
            "isin": isin,
            "product_page_url": None,
            "product_id": None,
            "holdings_url": None,
            "status": "product_page_not_found",
        }

    holdings_url = extract_holdings_url_from_product_page(product_page_url)

    return {
        "isin": isin,
        "product_page_url": product_page_url,
        "product_id": extract_product_id(product_page_url),
        "holdings_url": holdings_url,
        "status": "found" if holdings_url else "holdings_url_not_found",
    }