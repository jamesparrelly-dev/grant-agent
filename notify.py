"""
notify.py — Posts top-scored grants to Slack via incoming webhook
"""

import json
import os
import requests
from pathlib import Path
from datetime import datetime

SCORED_GRANTS_FILE = Path("scored_grants.json")
DASHBOARD_URL = os.environ.get("DASHBOARD_URL", "https://your-username.github.io/grant-agent/")


def format_amount(amount):
    if not amount:
        return "N/A"
    try:
        n = int(str(amount).replace(",", "").replace("$", ""))
        if n >= 1_000_000:
            return f"${n/1_000_000:.1f}M"
        if n >= 1_000:
            return f"${n/1_000:.0f}K"
        return f"${n}"
    except Exception:
        return str(amount)


def tier_emoji(tier):
    return {
        "Excellent": "🟢",
        "Good": "🔵",
        "Moderate": "🟡",
        "Weak": "🟠",
        "Not Relevant": "🔴"
    }.get(tier, "⚪")


def days_until(date_str):
    if not date_str:
        return None
    for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%S"]:
        try:
            d = datetime.strptime(date_str[:10], fmt[:8] if "T" in fmt else fmt)
            delta = (d - datetime.now()).days
            return delta
        except Exception:
            pass
    return None


def build_slack_message(top_grants, total_scored, new_count):
    today = datetime.now().strftime("%B %d, %Y")

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"☀️ Sun Metalon Grant Monitor — {today}"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Scanned federal grant databases. Found *{new_count} new opportunities*, scored against Sun Metalon's profile. Top matches below."
            }
        },
        {"type": "divider"}
    ]

    for i, grant in enumerate(top_grants[:5], 1):
        score = grant.get("score", 0)
        tier = grant.get("tier", "")
        emoji = tier_emoji(tier)
        title = grant.get("title", "Untitled")[:80]
        agency = grant.get("agency", "Unknown Agency")
        rationale = grant.get("rationale", "")
        amount = format_amount(grant.get("award_amount"))
        url = grant.get("url", "#")
        close_date = grant.get("close_date", "")
        days = days_until(close_date)
        urgent = grant.get("flag_urgent", False)

        deadline_str = ""
        if days is not None:
            if days < 0:
                deadline_str = " · ⚠️ Closed"
            elif days == 0:
                deadline_str = " · ⚠️ *Closes TODAY*"
            elif days <= 14:
                deadline_str = f" · ⚠️ *{days}d left*"
            else:
                deadline_str = f" · {days}d left"

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*{i}. <{url}|{title}>*\n"
                    f"{emoji} *{score}/100* · {agency} · {amount}{deadline_str}\n"
                    f"_{rationale}_"
                )
            }
        })

        if i < len(top_grants[:5]):
            blocks.append({"type": "divider"})

    blocks.extend([
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{total_scored} total grants* tracked in database. <{DASHBOARD_URL}|View full dashboard →>"
            }
        }
    ])

    return {
        "text": f"Sun Metalon Grant Monitor — {new_count} new opportunities found",
        "blocks": blocks
    }


def run():
    print(f"\n{'='*50}")
    print("Slack Notifier")
    print(f"{'='*50}\n")

    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("No SLACK_WEBHOOK_URL set — skipping Slack notification")
        return

    if not SCORED_GRANTS_FILE.exists():
        print("No scored_grants.json found. Run scorer.py first.")
        return

    with open(SCORED_GRANTS_FILE) as f:
        scored = json.load(f)

    if not scored:
        print("No new scored grants — skipping notification")
        return

    # Only notify for Excellent or Good tier
    notifiable = [g for g in scored if g.get("score", 0) >= 60]
    all_new = len(scored)

    if not notifiable:
        print(f"No high-scoring grants (≥60) in this run — skipping Slack")
        print(f"(Scored {all_new} grants, highest score: {scored[0].get('score', 0) if scored else 0})")
        return

    # Count total in dashboard
    dashboard_file = Path("docs/grants_data.json")
    total = len(notifiable)
    if dashboard_file.exists():
        with open(dashboard_file) as f:
            total = json.load(f).get("total_grants", total)

    payload = build_slack_message(notifiable, total, all_new)

    print(f"Posting {len(notifiable[:5])} top grants to Slack...")
    resp = requests.post(webhook_url, json=payload, timeout=15)

    if resp.status_code == 200:
        print("✓ Slack notification sent successfully")
    else:
        print(f"✗ Slack error {resp.status_code}: {resp.text}")
        raise Exception(f"Slack webhook failed: {resp.status_code}")


if __name__ == "__main__":
    run()
