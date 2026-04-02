"""X/Twitter scraper via RSS bridge services (Nitter, RSSHub)."""

from datetime import datetime, timedelta, timezone

import feedparser
import requests

from src.config import NITTER_INSTANCES, TWITTER_ACCOUNTS, Article


def _try_nitter_feed(handle: str, instance: str, timeout: int = 10) -> feedparser.FeedParserDict | None:
    """Try fetching a Twitter user's RSS feed from a Nitter instance."""
    url = f"{instance}/{handle}/rss"
    try:
        resp = requests.get(url, timeout=timeout, headers={
            "User-Agent": "SpaceXNewsDigest/1.0"
        })
        if resp.status_code == 200:
            feed = feedparser.parse(resp.content)
            if feed.entries:
                return feed
    except Exception:
        pass
    return None


def _try_rsshub_feed(handle: str, timeout: int = 10) -> feedparser.FeedParserDict | None:
    """Try fetching via RSSHub."""
    url = f"https://rsshub.app/twitter/user/{handle}"
    try:
        resp = requests.get(url, timeout=timeout, headers={
            "User-Agent": "SpaceXNewsDigest/1.0"
        })
        if resp.status_code == 200:
            feed = feedparser.parse(resp.content)
            if feed.entries:
                return feed
    except Exception:
        pass
    return None


def fetch_twitter_account(account: dict, hours: int = 24) -> list[Article]:
    """Fetch recent tweets from an account using available RSS bridges."""
    handle = account["handle"]
    name = account["name"]
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    # Try Nitter instances first
    feed = None
    for instance in NITTER_INSTANCES:
        feed = _try_nitter_feed(handle, instance)
        if feed:
            break

    # Fallback to RSSHub
    if not feed:
        feed = _try_rsshub_feed(handle)

    if not feed:
        print(f"  [@{handle}] All RSS bridges failed, skipping")
        return []

    articles = []
    for entry in feed.entries[:10]:  # Cap at 10 tweets per account
        title = entry.get("title", "")[:200]
        link = entry.get("link", f"https://x.com/{handle}")
        date = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            from time import mktime
            date = datetime.fromtimestamp(mktime(entry.published_parsed), tz=timezone.utc)

        if date and date < cutoff:
            continue

        articles.append(Article(
            title=f"@{handle}: {title}",
            url=link,
            source=f"X/@{handle}",
            summary=title,
            date=date,
            author=name,
            is_tweet=True,
        ))

    print(f"  [@{handle}] Found {len(articles)} recent tweets")
    return articles


def fetch_all_twitter(hours: int = 24) -> list[Article]:
    """Fetch tweets from all configured Twitter accounts."""
    print("Fetching X/Twitter feeds...")
    all_articles = []
    for account in TWITTER_ACCOUNTS:
        all_articles.extend(fetch_twitter_account(account, hours=hours))
    return all_articles
