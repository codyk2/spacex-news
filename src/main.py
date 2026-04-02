"""Main entry point — run the full daily digest pipeline."""

import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env for local development
load_dotenv()

from src.scraper import collect_all
from src.summarizer import summarize
from src.renderer import save_daily


def main():
    print("=" * 50)
    print("  SpaceX Daily News Digest")
    print("=" * 50)

    # 1. Collect articles from all sources
    articles = collect_all(hours=24)

    if not articles:
        print("\n[!] No articles found. Generating empty digest.")

    # 2. Summarize with Claude
    briefing = summarize(articles)

    # 3. Render and save HTML
    output_path = save_daily(briefing, articles)

    print(f"\n{'=' * 50}")
    print(f"  Done! Digest saved to: {output_path}")
    print(f"{'=' * 50}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
