"""Claude AI summarizer — synthesizes collected articles into a daily briefing."""

import os

import anthropic

from src.config import CLAUDE_MODEL, MAX_ARTICLES_FOR_SUMMARY, SUMMARY_MAX_TOKENS, Article

SYSTEM_PROMPT = """You are a space industry journalist writing a daily SpaceX briefing for an enthusiast audience.

Write in a professional but engaging tone. Be concise and informative. Structure the briefing with clear sections and cite sources inline with markdown links."""

USER_PROMPT_TEMPLATE = """Here are today's SpaceX-related articles and tweets. Write a daily digest.

Structure:
1. **TL;DR** — One sentence summary of the day
2. **Top Story** — The biggest SpaceX news
3. **Launch Updates** — Upcoming or recent launches
4. **Starship & Development** — Engineering and testing news
5. **Business & Industry** — Contracts, partnerships, financials
6. **From X/Twitter** — Notable posts from SpaceX figures

Rules:
- Omit any section that has no relevant content
- Cite sources with markdown links: [Source Name](url)
- Keep total length under 1000 words
- Use bullet points within sections for readability
- If there's very little news, write a shorter briefing — don't pad

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

    # Split into news and tweets
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
    lines = ["# SpaceX Daily Digest\n", "*AI summary unavailable — raw headlines below.*\n"]
    for a in articles[:20]:
        lines.append(f"- **[{a.source}]** [{a.title}]({a.url})")
    return "\n".join(lines)
