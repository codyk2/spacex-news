from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Article:
    title: str
    url: str
    source: str
    summary: str
    date: datetime | None = None
    author: str = ""
    is_tweet: bool = False


# RSS feeds — all have SpaceX-relevant content
RSS_FEEDS: list[dict] = [
    {
        "name": "SpaceNews",
        "url": "https://spacenews.com/feed/",
        "filter_keywords": ["spacex", "falcon", "starship", "starlink", "dragon", "raptor", "elon musk"],
    },
    {
        "name": "NASASpaceflight",
        "url": "https://www.nasaspaceflight.com/feed/",
        "filter_keywords": ["spacex", "falcon", "starship", "starlink", "dragon", "raptor"],
    },
    {
        "name": "Teslarati",
        "url": "https://www.teslarati.com/category/spacex/feed/",
        "filter_keywords": [],  # Already SpaceX-filtered
    },
    {
        "name": "Ars Technica - Space",
        "url": "https://arstechnica.com/space/feed/",
        "filter_keywords": ["spacex", "falcon", "starship", "starlink", "dragon", "elon musk"],
    },
    {
        "name": "Space.com",
        "url": "https://www.space.com/feeds/all",
        "filter_keywords": ["spacex", "falcon", "starship", "starlink", "dragon", "elon musk"],
    },
    {
        "name": "The Verge - Space",
        "url": "https://www.theverge.com/rss/space/index.xml",
        "filter_keywords": ["spacex", "falcon", "starship", "starlink", "dragon", "elon musk"],
    },
]

# X/Twitter accounts via RSS bridges
# Multiple Nitter instances for redundancy
NITTER_INSTANCES = [
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.woodland.cafe",
]

TWITTER_ACCOUNTS = [
    {"handle": "SpaceX", "name": "SpaceX"},
    {"handle": "elonmusk", "name": "Elon Musk"},
    {"handle": "SciGuySpace", "name": "Eric Berger"},
    {"handle": "nextspaceflight", "name": "Next Spaceflight"},
    {"handle": "SpaceflightNow", "name": "Spaceflight Now"},
]

# Summarization settings
CLAUDE_MODEL = "claude-sonnet-4-6-20250514"
MAX_ARTICLES_FOR_SUMMARY = 30
SUMMARY_MAX_TOKENS = 4096
