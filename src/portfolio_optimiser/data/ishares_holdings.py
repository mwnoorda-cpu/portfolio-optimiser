from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from datetime import date, datetime
from io import StringIO
from typing import Any
from urllib.parse import urljoin

import pandas as pd
import requests


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/139.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
              "application/json,text/csv,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,nl;q=0.8",
    "Referer": "https://www.ishares.com/",
}


@dataclass(frozen=True)
class ISharesHoldingResult:
    isin: str | None
    product_page_url: str
    holdings_url: str
    rows: int
    data: pd.DataFrame


def _normalise_product_page_url(url: str) -> str:
    """
    Clean product page URL so endpoint discovery/appending works consistently.
    """
    url = url.strip()
    url = url.split("#", 1)[0]
    url = url.split("?", 1)[0]
    return url.rstrip("/")


def _format_as_of_date(as_of_date: str | date | datetime | None) -> str | None:
    """
    Converts YYYY-MM-DD/date/datetime to YYYYMMDD.
    """
    if as_of_date is None:
        return None

    if isinstance(as_of_date, datetime):
        return as_of_date.strftime("%Y%m%d")

    if isinstance(as_of_date, date):
        return as_of_date.strftime("%Y%m%d")

    s = str(as_of_date).strip()

    if re.fullmatch(r"\d{8}", s):
        return s

    return datetime.strptime(s, "%Y-%m-%d").strftime("%Y%m%d")


def _get_with_retries(
    session: requests.Session,
    url: str,
    *,
    max_retries: int = 3,
    timeout: int = 30,
    sleep_seconds: float = 1.5,
) -> requests.Response:
    """
    GET with simple retry logic for transient iShares failures.
    """
    last_exc: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            response = session.get(url, timeout=timeout, headers=DEFAULT_HEADERS)

            if response.status_code in {429, 500, 502, 503, 504}:
                time.sleep(sleep_seconds * attempt)
                continue

            return response

        except requests.RequestException as exc:
            last_exc = exc
            time.sleep(sleep_seconds * attempt)

    if last_exc:
        raise RuntimeError(f"iShares request failed after retries: {last_exc}") from last_exc

    raise RuntimeError(f"iShares request failed after retries: {url}")


def _raw_value(x: Any) -> Any:
    """
    iShares JSON often wraps values like {'raw': 123, 'fmt': '123'}.
    """
    if isinstance(x, dict) and "raw" in x:
        return x["raw"]
    return x


def _map_ishares_json_row(row: list[Any]) -> dict[str, Any]:
    """
    Mapping for old-style iShares aaData JSON endpoint.

    This is defensive because iShares columns can differ by fund/region.
    """
    def get(i: int) -> Any:
        return _raw_value(row[i]) if i < len(row) else None

    return {
        "ticker": get(0),
        "name": get(1),
        "sector": get(2),
        "asset_class": get(3),
        "market_value": get(4),
        "weight": get(5),
        "notional_value": get(6),
        "shares": get(7),
        "cusip": get(8),
        "isin": get(9),
        "sedol": get(10),
        "price": get(11),
        "location": get(12),
        "exchange": get(13),
        "currency": get(14),
        "fx_rate": get(15),
        "maturity": get(16),
    }


def discover_ishares_holdings_urls(product_page_url: str, html: str) -> list[str]:
    """
    Discover candidate holdings download URLs from the actual product page HTML.

    Important:
    - We do not hardcode ticker/fileName.
    - We collect .ajax URLs and hrefs that look related to holdings/downloads.
    - We later test/parse each candidate and keep the first valid one.
    """
    clean_url = _normalise_product_page_url(product_page_url)
    candidates: list[str] = []

    # Direct .ajax links embedded in HTML or JavaScript.
    ajax_urls = re.findall(
        r"""(?P<url>[^"'<> ]+\.ajax\?[^"'<> ]+)""",
        html,
        flags=re.IGNORECASE,
    )

    for raw_url in ajax_urls:
        url = raw_url.replace("&amp;", "&")
        full_url = urljoin(clean_url + "/", url)

        lowered = full_url.lower()
        if (
            "holding" in lowered
            or "holdings" in lowered
            or "filename" in lowered
            or "filetype=csv" in lowered
            or "filetype=json" in lowered
            or "tab=all" in lowered
        ):
            candidates.append(full_url)

    # href links that look like downloads or ajax endpoints.
    hrefs = re.findall(
        r"""href=["'](?P<href>[^"']+)["']""",
        html,
        flags=re.IGNORECASE,
    )

    for href in hrefs:
        href = href.replace("&amp;", "&")
        full_url = urljoin(clean_url + "/", href)
        lowered = full_url.lower()

        if (
            "download" in lowered
            or "holding" in lowered
            or "holdings" in lowered
            or ".ajax" in lowered
        ):
            candidates.append(full_url)

    # Extra fallback:
    # Some iShares pages contain the holdings fileName in JS but not as a clean href.
    file_names = re.findall(
        r"""fileName[=:]["']?([A-Za-z0-9_\-]+_holdings)["']?""",
        html,
        flags=re.IGNORECASE,
    )

    ajax_codes = re.findall(
        r"""([0-9]{10,}\.ajax)""",
        html,
        flags=re.IGNORECASE,
    )

    for ajax_code in ajax_codes:
        for file_name in file_names:
            candidates.append(
                f"{clean_url}/{ajax_code}?dataType=fund&fileName={file_name}&fileType=csv"
            )

    # Old talsan/ishares-style fallback. This is not preferred, but useful for some regions.
    candidates.append(f"{clean_url}/1467271812596.ajax?fileType=json&tab=all")

    # Deduplicate while preserving order.
    seen: set[str] = set()
    out: list[str] = []

    for url in candidates:
        if url not in seen:
            seen.add(url)
            out.append(url)

    return out


def parse_ishares_holdings_response(content: bytes, content_type: str = "") -> pd.DataFrame:
    """
    Parse either:
    - old JSON aaData holdings
    - newer CSV holdings downloads
    """
    text = content.decode("utf-8-sig", errors="replace").strip()

    if not text:
        raise ValueError("Empty iShares response.")

    # If iShares returns HTML, this is not the holdings file.
    if text.lower().startswith("<!doctype html") or text.lower().startswith("<html"):
        raise ValueError("Response is HTML, not a holdings file.")

    # JSON path.
    if "json" in content_type.lower() or text.startswith("{"):
        payload = json.loads(text)

        if isinstance(payload, dict) and "aaData" in payload:
            rows = payload.get("aaData") or []
            df = pd.DataFrame([_map_ishares_json_row(row) for row in rows])
            if df.empty:
                raise ValueError("JSON holdings response contained zero rows.")
            return df

        raise ValueError(f"Unexpected JSON holdings format. First 300 chars: {text[:300]}")

    # CSV path.
    lines = text.splitlines()

    header_idx = None

    for i, line in enumerate(lines):
        lowered = line.lower()

        # Common iShares holdings columns.
        if (
            "isin" in lowered
            and "weight" in lowered
            and (
                "ticker" in lowered
                or "issuer ticker" in lowered
                or "name" in lowered
            )
        ):
            header_idx = i
            break

    if header_idx is None:
        raise ValueError(f"Could not find CSV holdings header. First 500 chars: {text[:500]}")

    csv_text = "\n".join(lines[header_idx:])

    # Try normal comma CSV first.
    try:
        df = pd.read_csv(StringIO(csv_text))
    except Exception:
        # Some regions may use semicolon separator.
        df = pd.read_csv(StringIO(csv_text), sep=";")

    # Drop empty footer rows.
    df = df.dropna(how="all")

    if df.empty:
        raise ValueError("CSV holdings response contained zero rows.")

    return df


def _apply_as_of_date_to_candidate_url(candidate_url: str, as_of_date: str | date | datetime | None) -> str:
    """
    Adds asOfDate=YYYYMMDD to candidate URL if requested and not already present.
    Not every iShares endpoint supports this, but it is safe to try.
    """
    yyyymmdd = _format_as_of_date(as_of_date)

    if not yyyymmdd:
        return candidate_url

    if "asOfDate=" in candidate_url:
        return re.sub(r"asOfDate=\d{8}", f"asOfDate={yyyymmdd}", candidate_url)

    joiner = "&" if "?" in candidate_url else "?"
    return f"{candidate_url}{joiner}asOfDate={yyyymmdd}"


def get_ishares_holdings(
    *,
    product_page_url: str,
    isin: str | None = None,
    as_of_date: str | date | datetime | None = None,
    session: requests.Session | None = None,
    debug: bool = True,
) -> ISharesHoldingResult:
    """
    Fetch iShares ETF holdings from a known product page URL.

    Flow:
    1. Open product page.
    2. Discover holdings/download URLs from the actual HTML.
    3. Try each candidate URL.
    4. Parse first valid CSV/JSON holdings file.
    """
    own_session = session is None
    session = session or requests.Session()

    try:
        clean_product_url = _normalise_product_page_url(product_page_url)

        product_response = _get_with_retries(session, clean_product_url)

        if product_response.status_code == 403:
            raise PermissionError(
                "iShares returned 403 Forbidden on the product page. "
                "Try an individual product URL instead of a professional URL."
            )

        if product_response.status_code == 404:
            raise FileNotFoundError(f"iShares product page not found: {clean_product_url}")

        product_response.raise_for_status()

        candidate_urls = discover_ishares_holdings_urls(
            clean_product_url,
            product_response.text,
        )

        if not candidate_urls:
            raise RuntimeError(
                "Could not discover any holdings download URL from the iShares product page. "
                f"Product page: {clean_product_url}"
            )

        if debug:
            print("Candidate holdings URLs:")
            for candidate in candidate_urls:
                print(f" - {candidate}")

        last_error: str | None = None

        for candidate_url in candidate_urls:
            candidate_url_with_date = _apply_as_of_date_to_candidate_url(
                candidate_url,
                as_of_date,
            )

            try:
                response = _get_with_retries(session, candidate_url_with_date)

                if response.status_code != 200:
                    last_error = (
                        f"{candidate_url_with_date} returned HTTP {response.status_code}"
                    )
                    continue

                df = parse_ishares_holdings_response(
                    response.content,
                    response.headers.get("content-type", ""),
                )

                if df.empty:
                    last_error = f"{candidate_url_with_date} parsed but returned zero rows"
                    continue

                df.insert(0, "source_url", candidate_url_with_date)

                if isin is not None:
                    df.insert(0, "fund_isin", isin)

                requested_date = None
                if as_of_date is not None:
                    requested_date = datetime.strptime(
                        _format_as_of_date(as_of_date),
                        "%Y%m%d",
                    ).strftime("%Y-%m-%d")
                    df.insert(0, "requested_as_of_date", requested_date)

                return ISharesHoldingResult(
                    isin=isin,
                    product_page_url=clean_product_url,
                    holdings_url=candidate_url_with_date,
                    rows=len(df),
                    data=df,
                )

            except Exception as exc:
                last_error = f"{candidate_url_with_date}: {exc}"
                if debug:
                    print(f"Failed candidate: {last_error}")
                continue

        raise RuntimeError(
            "Found candidate holdings URLs, but none could be downloaded and parsed. "
            f"Last error: {last_error}"
        )

    finally:
        if own_session:
            session.close()