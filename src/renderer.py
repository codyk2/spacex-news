"""HTML renderer — generates a single scrollable feed page."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup

from src.config import Article, FEED_HISTORY_DAYS

PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"
OUTPUT_DIR = PROJECT_ROOT / "output"
DATA_FILE = OUTPUT_DIR / "articles.json"


def _markdown_to_html(md: str) -> str:
    """Simple markdown to HTML conversion."""
    html = md
    html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
    html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
    html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)
    html = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', html)
    html = re.sub(r"^---+$", "<hr>", html, flags=re.MULTILINE)
    html = re.sub(r"^> (.+)$", r"<blockquote>\1</blockquote>", html, flags=re.MULTILINE)

    def replace_ul(match: re.Match) -> str:
        items = re.findall(r"^[-*] (.+)$", match.group(0), re.MULTILINE)
        li = "".join(f"<li>{item}</li>" for item in items)
        return f"<ul>{li}</ul>"
    html = re.sub(r"(^[-*] .+\n?)+", replace_ul, html, flags=re.MULTILINE)

    blocks = html.split("\n\n")
    processed = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if block.startswith(("<h", "<ul", "<ol", "<hr", "<blockquote")):
            processed.append(block)
        else:
            processed.append(f"<p>{block}</p>")
    return "\n".join(processed)


def _article_to_dict(a: Article) -> dict:
    return {
        "title": a.title,
        "url": a.url,
        "source": a.source,
        "summary": a.summary,
        "date": a.date.isoformat() if a.date else None,
        "author": a.author,
        "is_tweet": a.is_tweet,
    }


def _dict_to_article(d: dict) -> Article:
    return Article(
        title=d["title"],
        url=d["url"],
        source=d["source"],
        summary=d["summary"],
        date=datetime.fromisoformat(d["date"]) if d.get("date") else None,
        author=d.get("author", ""),
        is_tweet=d.get("is_tweet", False),
    )


def _load_history() -> dict:
    """Load stored article history. Structure: { "YYYY-MM-DD": { "articles": [...], "briefing": "..." } }"""
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return {}


def _save_history(history: dict):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")


def _prune_history(history: dict) -> dict:
    """Keep only the last N days."""
    sorted_dates = sorted(history.keys(), reverse=True)
    pruned = {}
    for date_key in sorted_dates[:FEED_HISTORY_DAYS]:
        pruned[date_key] = history[date_key]
    return pruned


def save_daily(briefing_md: str, articles: list[Article], date: datetime | None = None) -> Path:
    """Add today's articles to history and render the full feed page."""
    if date is None:
        date = datetime.now(timezone.utc)

    date_str = date.strftime("%Y-%m-%d")

    # Load existing history and add today
    history = _load_history()
    history[date_str] = {
        "articles": [_article_to_dict(a) for a in articles],
        "briefing": briefing_md,
    }
    history = _prune_history(history)
    _save_history(history)

    # Build template data: list of days, newest first
    days = []
    for day_key in sorted(history.keys(), reverse=True):
        day_data = history[day_key]
        day_date = datetime.strptime(day_key, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        day_articles = [_dict_to_article(d) for d in day_data["articles"]]
        briefing_raw = day_data.get("briefing", "")
        # Convert plain paragraphs to <p> tags
        if briefing_raw and not briefing_raw.startswith("#"):
            briefing_html = "\n".join(f"<p>{p.strip()}</p>" for p in briefing_raw.split("\n\n") if p.strip())
        else:
            briefing_html = _markdown_to_html(briefing_raw) if briefing_raw else ""
        days.append({
            "date_key": day_key,
            "date_display": day_date.strftime("%A, %B %d"),
            "is_today": day_key == date_str,
            "briefing_html": Markup(briefing_html),
            "articles": day_articles,
            "count": len(day_articles),
        })

    # Copy static assets
    static_src = PROJECT_ROOT / "static"
    static_dst = OUTPUT_DIR / "static"
    static_dst.mkdir(parents=True, exist_ok=True)
    for f in static_src.iterdir():
        if f.is_file():
            (static_dst / f.name).write_bytes(f.read_bytes())

    # Collect unique source names across all days
    all_sources: set[str] = set()
    for day in days:
        for a in day["articles"]:
            all_sources.add(a.source)
    sources = sorted(all_sources)

    # Render single feed page
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)
    template = env.get_template("feed.html")
    html = template.render(days=days, sources=sources)

    output_file = OUTPUT_DIR / "index.html"
    output_file.write_text(html, encoding="utf-8")
    print(f"  Saved feed: {output_file} ({sum(d['count'] for d in days)} total articles across {len(days)} days)")

    return output_file
