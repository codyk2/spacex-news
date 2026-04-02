# SpaceX Daily News Digest

AI-powered daily briefing on all things SpaceX. Scrapes leading space news sources and notable X/Twitter accounts, then uses Claude to synthesize everything into a clean, readable daily digest.

## How It Works

1. **Scrape** — Collects articles from SpaceNews, NASASpaceflight, Teslarati, Ars Technica, Space.com, The Verge, and X/Twitter accounts (@SpaceX, @elonmusk, @SciGuySpace, etc.)
2. **Summarize** — Sends collected articles to Claude AI for synthesis into a structured daily briefing
3. **Publish** — Renders a static HTML page and deploys to GitHub Pages

Runs daily via GitHub Actions at 10:00 AM UTC.

## Live Site

**[codyk2.github.io/spacex-news](https://codyk2.github.io/spacex-news)**

## Run Locally

```bash
# Clone
git clone https://github.com/codyk2/spacex-news.git
cd spacex-news

# Install
pip install -r requirements.txt

# Set API key
export ANTHROPIC_API_KEY=sk-ant-...

# Run
python -m src.main
```

Output is saved to `output/YYYY-MM-DD/index.html`.

## Setup (GitHub Actions)

1. Go to repo **Settings > Secrets > Actions**
2. Add `ANTHROPIC_API_KEY` secret
3. Go to **Settings > Pages** and set source to `gh-pages` branch
4. The workflow runs daily, or trigger manually from **Actions > Daily SpaceX Digest > Run workflow**

## Project Structure

```
src/
  config.py         # Source URLs, settings
  main.py           # Pipeline entry point
  scraper.py        # Orchestrator (parallel fetch + dedup)
  summarizer.py     # Claude API summarization
  renderer.py       # Jinja2 → HTML generation
  sources/
    rss.py          # RSS feed parser
    twitter.py      # X/Twitter via Nitter RSS bridges
    web.py          # HTML scraper fallback
templates/          # Jinja2 HTML templates
static/             # CSS
output/             # Generated pages (deployed to gh-pages)
```

## Tech Stack

- Python 3.12
- Claude AI (Anthropic SDK)
- BeautifulSoup4 + feedparser
- Jinja2 templates
- GitHub Actions + GitHub Pages
