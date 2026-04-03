"""Claude AI summarizer — synthesizes collected articles into a daily briefing."""

import os

import anthropic

from src.config import CLAUDE_MODEL, MAX_ARTICLES_FOR_SUMMARY, SUMMARY_MAX_TOKENS, Article

SYSTEM_PROMPT = """You are a senior space industry journalist writing a concise daily SpaceX briefing. Your reader is a SpaceX enthusiast who wants to know what happened today in 60 seconds of reading. Write in clean, authoritative prose — no fluff, no filler."""

USER_PROMPT_TEMPLATE = """Here are today's SpaceX-related articles and tweets. Write a 3-paragraph daily digest.

Format:
- Paragraph 1: The lead story — what is the single biggest SpaceX development today? Give context and why it matters.
- Paragraph 2: Other notable news — cover 2-3 secondary stories in a flowing paragraph. Connect them if possible.
- Paragraph 3: Quick hits — anything else worth noting, upcoming launches, smaller developments.

Rules:
- Exactly 3 paragraphs, no headers, no bullet points, no markdown formatting
- Plain prose only — write it like a newspaper column
- 200-350 words total
- Cite sources naturally inline: "according to [Source Name]" or "Source Name reported that..."
- Do NOT use markdown links — just name the publication
- If there's very little news, write shorter — never pad
- No sign-off or closing line

---

ARTICLES:
{articles}

TWEETS:
{tweets}"""


def _format_articles(articles: list[Article]) -> str:
    lines = []
    for a in articles:
        date_str = a.date.strftime("%Y-%m-%d %H:%M UTC") if a.date else "Unknown date"
        lines.append(f"- [{a.source}] {a.title}\n  URL: {a.url}\n  Date: {date_str}\n  Summary: {a.summary}\n")
    return "\n".join(lines) if lines else "No articles found today."


def summarize(articles: list[Article]) -> str:
    """Send collected articles to Claude and get a synthesized daily briefing."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[!] ANTHROPIC_API_KEY not set, returning raw article list")
        return _fallback_summary(articles)

    news = [a for a in articles if not a.is_tweet][:MAX_ARTICLES_FOR_SUMMARY]
    tweets = [a for a in articles if a.is_tweet][:15]

    prompt = USER_PROMPT_TEMPLATE.format(
        articles=_format_articles(news),
        tweets=_format_articles(tweets),
    )

    print(f"\nSummarizing {len(news)} articles + {len(tweets)} tweets with Claude...")

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=SUMMARY_MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        summary = message.content[0].text
        print(f"  Summary generated ({len(summary)} chars)")
        return summary
    except Exception as e:
        print(f"[!] Claude API error: {e}")
        return _fallback_summary(articles)


def _fallback_summary(articles: list[Article]) -> str:
    """Plain-text fallback when Claude API is unavailable."""
    if not articles:
        return ""
    # Build a simple 3-paragraph summary from headlines
    top = articles[0]
    para1 = f"Today's top story: {top.title} (via {top.source})."
    others = [a.title for a in articles[1:5]]
    para2 = "Also making news: " + "; ".join(others) + "." if others else ""
    more = [a.title for a in articles[5:8]]
    para3 = "Quick hits: " + "; ".join(more) + "." if more else ""
    return "\n\n".join(p for p in [para1, para2, para3] if p)
