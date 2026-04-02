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


SPACEX_KEYWORDS = [
    "spacex", "falcon", "starship", "starlink", "dragon", "raptor",
    "elon musk", "crew dragon", "falcon 9", "falcon heavy", "boca chica",
    "starbase", "cape canaveral", "vandenberg", "merlin engine", "superheavy",
    "super heavy", "orbital launch", "booster catch", "mechazilla",
]

# RSS feeds
RSS_FEEDS: list[dict] = [
    # Core SpaceX sources
    {
        "name": "SpaceNews",
        "url": "https://spacenews.com/feed/",
        "filter_keywords": SPACEX_KEYWORDS,
    },
    {
        "name": "NASASpaceflight",
        "url": "https://www.nasaspaceflight.com/feed/",
        "filter_keywords": SPACEX_KEYWORDS,
    },
    {
        "name": "Teslarati",
        "url": "https://www.teslarati.com/category/spacex/feed/",
        "filter_keywords": [],  # Already SpaceX-filtered
    },
    {
        "name": "Ars Technica",
        "url": "https://arstechnica.com/space/feed/",
        "filter_keywords": SPACEX_KEYWORDS,
    },
    {
        "name": "Space.com",
        "url": "https://www.space.com/feeds/all",
        "filter_keywords": SPACEX_KEYWORDS,
    },
    {
        "name": "The Verge",
        "url": "https://www.theverge.com/rss/space/index.xml",
        "filter_keywords": SPACEX_KEYWORDS,
    },
    # Additional sources
    {
        "name": "Google News",
        "url": "https://news.google.com/rss/search?q=spacex+when:2d&hl=en-US&gl=US&ceid=US:en",
        "filter_keywords": [],  # Already SpaceX-filtered by query
    },
    {
        "name": "CNBC Space",
        "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=106983516",
        "filter_keywords": SPACEX_KEYWORDS,
    },
    {
        "name": "Spaceflight Now",
        "url": "https://spaceflightnow.com/feed/",
        "filter_keywords": SPACEX_KEYWORDS,
    },
    {
        "name": "Everyday Astronaut",
        "url": "https://everydayastronaut.com/feed/",
        "filter_keywords": SPACEX_KEYWORDS,
    },
    {
        "name": "Electrek",
        "url": "https://electrek.co/guides/spacex/feed/",
        "filter_keywords": [],  # Already SpaceX-filtered
    },
    {
        "name": "TechCrunch",
        "url": "https://techcrunch.com/feed/",
        "filter_keywords": SPACEX_KEYWORDS,
    },
    {
        "name": "BBC Science",
        "url": "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
        "filter_keywords": SPACEX_KEYWORDS,
    },
]

# X/Twitter accounts via RSS bridges
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

# How many days of history to keep on the feed page
FEED_HISTORY_DAYS = 14
