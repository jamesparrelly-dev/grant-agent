"""
main.py — Orchestrates the full grant monitoring pipeline:
  1. scraper.py       — fetch new grants from SBIR.gov + Grants.gov
  2. state_scraper.py — fetch grants from 8 US state programs
  3. scorer.py        — score with Claude against Sun Metalon profile
  4. notify.py        — post top matches to Slack
  5. build_dashboard.py — regenerate static dashboard HTML
"""

import sys
import traceback
from datetime import datetime


def run_step(name, fn):
    print(f"\n{'─'*50}")
    print(f"STEP: {name}")
    print(f"{'─'*50}")
    try:
        result = fn()
        print(f"✓ {name} complete")
        return result
    except Exception as e:
        print(f"✗ {name} FAILED: {e}")
        traceback.print_exc()
        return None


def main():
    print(f"\n{'='*50}")
    print(f"SUN METALON GRANT MONITOR")
    print(f"Run started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{'='*50}")

    import scraper
    import state_scraper
    import scorer
    import notify
    import build_dashboard

    run_step("Scrape federal grant sources", scraper.run)
    run_step("Scrape state grant sources", state_scraper.run)
    run_step("Score with Claude", scorer.run)
    run_step("Send Slack notification", notify.run)
    run_step("Build dashboard", build_dashboard.run)

    print(f"\n{'='*50}")
    print(f"Pipeline complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
