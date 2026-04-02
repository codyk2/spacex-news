"""Main scraper orchestrator — collects from all sources."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from src.config import Article
from src.sources.rss import fetch_all_rss
from src.sources.twitter import fetch_all_twitter
from src.sources.web import fetch_all_web


def _deduplicate(articles: list[Article]) -> list[Article]:
    """Remove duplicate articles by URL."""
    seen_urls: set[str] = set()
    unique = []
    for article in articles:
        normalized = article.url.rstrip("/").lower()
        if normalized not in seen_urls:
            seen_urls.add(normalized)
            unique.append(article)
    return unique


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

    # Run all source fetchers in parallel
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

    # Deduplicate and sort
    all_articles = _deduplicate(all_articles)
    all_articles = _sort_articles(all_articles)

    # Separate tweets from articles for summary
    news = [a for a in all_articles if not a.is_tweet]
    tweets = [a for a in all_articles if a.is_tweet]

    print(f"\n=== Collection Complete ===")
    print(f"  News articles: {len(news)}")
    print(f"  Tweets: {len(tweets)}")
    print(f"  Total unique: {len(all_articles)}")

    return all_articles


if __name__ == "__main__":
    articles = collect_all()
    for a in articles[:20]:
        prefix = "[TWEET]" if a.is_tweet else "[NEWS]"
        print(f"\n{prefix} {a.source}")
        print(f"  {a.title}")
        print(f"  {a.url}")
