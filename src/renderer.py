"""HTML renderer — generates static pages from templates."""

import os
import re
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup

from src.config import Article

PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"
OUTPUT_DIR = PROJECT_ROOT / "output"


def _markdown_to_html(md: str) -> str:
    """Simple markdown to HTML conversion (no external dependency)."""
    html = md

    # Headers
    html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
    html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
    html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)

    # Bold and italic
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)

    # Links
    html = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', html)

    # Horizontal rules
    html = re.sub(r"^---+$", "<hr>", html, flags=re.MULTILINE)

    # Blockquotes
    html = re.sub(r"^> (.+)$", r"<blockquote>\1</blockquote>", html, flags=re.MULTILINE)

    # Unordered lists — group consecutive lines
    def replace_ul(match: re.Match) -> str:
        items = re.findall(r"^[-*] (.+)$", match.group(0), re.MULTILINE)
        li = "".join(f"<li>{item}</li>" for item in items)
        return f"<ul>{li}</ul>"
    html = re.sub(r"(^[-*] .+\n?)+", replace_ul, html, flags=re.MULTILINE)

    # Paragraphs — wrap remaining text blocks
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


def render_daily(briefing_md: str, articles: list[Article], date: datetime | None = None) -> str:
    """Render the daily digest HTML page."""
    if date is None:
        date = datetime.now(timezone.utc)

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)
    template = env.get_template("daily.html")

    briefing_html = _markdown_to_html(briefing_md)

    return template.render(
        date_display=date.strftime("%B %d, %Y"),
        date_iso=date.strftime("%Y-%m-%d"),
        briefing_html=Markup(briefing_html),
        articles=articles,
    )


def render_index(digests: list[dict]) -> str:
    """Render the index page listing all daily digests."""
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)
    template = env.get_template("index.html")
    return template.render(digests=digests)


def save_daily(briefing_md: str, articles: list[Article], date: datetime | None = None) -> Path:
    """Render and save a daily digest, then update the index."""
    if date is None:
        date = datetime.now(timezone.utc)

    date_str = date.strftime("%Y-%m-%d")

    # Ensure output directories exist
    daily_dir = OUTPUT_DIR / date_str
    daily_dir.mkdir(parents=True, exist_ok=True)

    # Copy static assets to output
    static_src = PROJECT_ROOT / "static"
    static_dst = OUTPUT_DIR / "static"
    static_dst.mkdir(parents=True, exist_ok=True)
    for f in static_src.iterdir():
        if f.is_file():
            (static_dst / f.name).write_bytes(f.read_bytes())

    # Render and save daily page
    html = render_daily(briefing_md, articles, date)
    daily_file = daily_dir / "index.html"
    daily_file.write_text(html, encoding="utf-8")
    print(f"  Saved daily digest: {daily_file}")

    # Build index of all digests
    digests = []
    for d in sorted(OUTPUT_DIR.iterdir(), reverse=True):
        if d.is_dir() and d.name != "static" and (d / "index.html").exists():
            digests.append({
                "date": d.name,
                "path": f"{d.name}/index.html",
                "article_count": "—",  # Could parse from file if needed
            })

    index_html = render_index(digests)
    (OUTPUT_DIR / "index.html").write_text(index_html, encoding="utf-8")
    print(f"  Updated index: {OUTPUT_DIR / 'index.html'}")

    return daily_file
