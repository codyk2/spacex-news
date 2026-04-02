"""RSS feed parser for SpaceX news sources."""

import re
from datetime import datetime, timedelta, timezone
from time import mktime

import feedparser
import requests
from bs4 import BeautifulSoup

from src.config import RSS_FEEDS, Article


def _clean_html(raw_html: str) -> str:
    """Strip HTML tags and clean up whitespace."""
    text = BeautifulSoup(raw_html, "html.parser").get_text(separator=" ")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:500]  # Cap summary length


def _parse_date(entry: dict) -> datetime | None:
    """Extract datetime from a feed entry."""
    for field in ("published_parsed", "updated_parsed"):
        parsed = entry.get(field)
        if parsed:
            return datetime.fromtimestamp(mktime(parsed), tz=timezone.utc)
    return None


def _matches_keywords(text: str, keywords: list[str]) -> bool:
    """Check if text contains any of the keywords (case-insensitive)."""
    if not keywords:
        return True  # No filter = include everything
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)


def _extract_google_news_source(title: str) -> tuple[str, str]:
    """Extract the real publication name from Google News titles.

    Google News titles look like: "SpaceX files for IPO - Bloomberg.com"
    Returns (clean_title, source_name).
    """
    # Match " - SourceName" or " - SourceName.com" at end of title
    match = re.search(r"\s+[-\u2013\u2014]\s+([A-Za-z][A-Za-z0-9\s.&']+)$", title)
    if match:
        source = match.group(1).strip()
        # Remove common suffixes
        source = re.sub(r"\.(com|org|net|co\.uk|io)$", "", source, flags=re.IGNORECASE).strip()
        clean_title = title[:match.start()].strip()
        return clean_title, source
    return title, ""


def fetch_rss_feed(feed_config: dict, hours: int = 24) -> list[Article]:
    """Fetch and parse a single RSS feed, filtering for SpaceX content."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    articles = []
    is_google_news = "news.google.com" in feed_config["url"]

    try:
        resp = requests.get(feed_config["url"], timeout=15, headers={
            "User-Agent": "SpaceXNewsDigest/1.0 (+https://github.com/codyk2/spacex-news)"
        })
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
    except Exception as e:
        print(f"  [!] Failed to fetch {feed_config['name']}: {e}")
        return []

    for entry in feed.entries:
        title = entry.get("title", "")
        summary_raw = entry.get("summary", entry.get("description", ""))
        summary = _clean_html(summary_raw)
        link = entry.get("link", "")
        author = entry.get("author", "")
        date = _parse_date(entry)
        source = feed_config["name"]

        # Extract real source from Google News titles
        if is_google_news:
            title, extracted_source = _extract_google_news_source(title)
            if extracted_source:
                source = extracted_source

        # Filter by date
        if date and date < cutoff:
            continue

        # Filter by keywords
        searchable = f"{title} {summary}"
        if not _matches_keywords(searchable, feed_config.get("filter_keywords", [])):
            continue

        articles.append(Article(
            title=title,
            url=link,
            source=source,
            summary=summary,
            date=date,
            author=author,
        ))

    print(f"  [{feed_config['name']}] Found {len(articles)} SpaceX articles")
    return articles


def fetch_all_rss(hours: int = 24) -> list[Article]:
    """Fetch all configured RSS feeds."""
    print("Fetching RSS feeds...")
    all_articles = []
    for feed_config in RSS_FEEDS:
        all_articles.extend(fetch_rss_feed(feed_config, hours=hours))
    return all_articles
