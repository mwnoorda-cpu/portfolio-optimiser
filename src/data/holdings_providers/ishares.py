from pathlib import Path
import requests

RAW_DIR = Path("data/raw/holdings/ishares")


def download_ishares_holdings_from_url(url: str, output_name: str) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        )
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    output_path = RAW_DIR / output_name
    output_path.write_bytes(response.content)

    return output_path


def build_ishares_holdings_url(product_id: str, slug: str, file_name: str) -> str:
    return (
        f"https://www.ishares.com/ch/professionals/en/products/{product_id}/"
        f"{slug}/1495092304805.ajax?"
        f"fileType=csv&fileName={file_name}_holdings&dataType=fund"
    )