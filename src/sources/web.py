"""HTML web scraper fallback for sources without reliable RSS."""

import re
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from src.config import Article


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def scrape_spacex_com() -> list[Article]:
    """Scrape spacex.com/launches for recent launch info."""
    articles = []
    try:
        resp = requests.get("https://www.spacex.com/launches/", timeout=15, headers={
            "User-Agent": "SpaceXNewsDigest/1.0"
        })
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # SpaceX.com uses dynamic rendering, so we get what's in the initial HTML
        for item in soup.select("a[href*='/launches/']")[:5]:
            title = _clean_text(item.get_text())
            if not title or len(title) < 5:
                continue
            href = item.get("href", "")
            url = f"https://www.spacex.com{href}" if href.startswith("/") else href
            articles.append(Article(
                title=title,
                url=url,
                source="SpaceX.com",
                summary=f"Launch page: {title}",
                date=datetime.now(timezone.utc),
                author="SpaceX",
            ))
    except Exception as e:
        print(f"  [!] Failed to scrape spacex.com: {e}")

    print(f"  [SpaceX.com] Found {len(articles)} launch entries")
    return articles


def fetch_all_web() -> list[Article]:
    """Run all web scrapers."""
    print("Fetching web sources...")
    return scrape_spacex_com()
