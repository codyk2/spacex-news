"""Main scraper orchestrator — collects from all sources."""

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from src.config import Article
from src.sources.rss import fetch_all_rss
from src.sources.twitter import fetch_all_twitter
from src.sources.web import fetch_all_web

# Higher = preferred when deduplicating (keep the better source)
SOURCE_PRIORITY = {
    "Ars Technica": 10,
    "SpaceNews": 9,
    "NASASpaceflight": 9,
    "Teslarati": 8,
    "Spaceflight Now": 8,
    "The Verge": 7,
    "TechCrunch": 7,
    "Space.com": 6,
    "CNBC": 6,
    "Everyday Astronaut": 6,
    "Electrek": 5,
}
DEFAULT_PRIORITY = 3  # Google News aggregated sources


def _normalize_title(title: str) -> set[str]:
    """Normalize a title into a set of lowercase keywords for comparison."""
    title = title.lower()
    # Strip trailing source attribution like "- Bloomberg" or "| Reuters"
    title = re.sub(r"\s*[-|–—]\s*[a-z][a-z0-9\s.&']+$", "", title)
    title = re.sub(r"[^a-z0-9\s]", "", title)
    words = set(title.split())
    stop = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "is", "it", "its", "with", "by", "from", "as", "be", "was",
            "are", "has", "have", "had", "this", "that", "will", "can", "may",
            "says", "said", "report", "reports", "new", "how", "what", "why",
            "could", "would", "about", "more", "than", "after", "into", "up"}
    return words - stop


def _title_similarity(a: set[str], b: set[str]) -> float:
    """Jaccard similarity between two title word sets."""
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _source_priority(source: str) -> int:
    return SOURCE_PRIORITY.get(source, DEFAULT_PRIORITY)


def _deduplicate(articles: list[Article]) -> list[Article]:
    """Remove duplicates by URL and by title similarity."""
    # First pass: exact URL dedup
    seen_urls: set[str] = set()
    url_unique = []
    for article in articles:
        normalized = article.url.rstrip("/").lower()
        # Strip Google News redirect wrapper
        if "news.google.com" in normalized:
            normalized = article.url  # Keep as-is since redirects vary
        if normalized not in seen_urls:
            seen_urls.add(normalized)
            url_unique.append(article)

    # Second pass: fuzzy title dedup
    kept: list[Article] = []
    kept_titles: list[set[str]] = []

    for article in url_unique:
        title_words = _normalize_title(article.title)
        if len(title_words) < 3:
            kept.append(article)
            kept_titles.append(title_words)
            continue

        is_dup = False
        for i, existing_words in enumerate(kept_titles):
            if _title_similarity(title_words, existing_words) > 0.35:
                # Keep the one from the higher-priority source
                if _source_priority(article.source) > _source_priority(kept[i].source):
                    kept[i] = article
                    kept_titles[i] = title_words
                is_dup = True
                break

        if not is_dup:
            kept.append(article)
            kept_titles.append(title_words)

    return kept


def _sort_articles(articles: list[Article]) -> list[Article]:
    """Sort by date (newest first), undated articles last."""
    def sort_key(a: Article) -> datetime:
        return a.date if a.date else datetime.min.replace(tzinfo=timezone.utc)
    return sorted(articles, key=sort_key, reverse=True)


def collect_all(hours: int = 24) -> list[Article]:
    """
    Collect articles from all sources in parallel.
    Returns deduplicated, sorted list of articles from the last `hours` hours.
    """
    print(f"=== SpaceX News Scraper ===")
    print(f"Collecting articles from the last {hours} hours...\n")

    all_articles: list[Article] = []

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(fetch_all_rss, hours): "RSS",
            executor.submit(fetch_all_twitter, hours): "Twitter",
            executor.submit(fetch_all_web): "Web",
        }

        for future in as_completed(futures):
            source_type = futures[future]
            try:
                articles = future.result()
                all_articles.extend(articles)
            except Exception as e:
                print(f"\n[!] {source_type} scraper failed: {e}")

    raw_count = len(all_articles)
    all_articles = _deduplicate(all_articles)
    all_articles = _sort_articles(all_articles)

    news = [a for a in all_articles if not a.is_tweet]
    tweets = [a for a in all_articles if a.is_tweet]

    print(f"\n=== Collection Complete ===")
    print(f"  Raw articles: {raw_count}")
    print(f"  After dedup: {len(all_articles)} ({raw_count - len(all_articles)} duplicates removed)")
    print(f"  News: {len(news)}, Tweets: {len(tweets)}")

    return all_articles


if __name__ == "__main__":
    articles = collect_all()
    for a in articles[:20]:
        prefix = "[TWEET]" if a.is_tweet else "[NEWS]"
        print(f"\n{prefix} {a.source}")
        print(f"  {a.title}")
        print(f"  {a.url}")
