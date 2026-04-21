"""
scorer.py — Scores grants against Sun Metalon's profile using Claude API
Outputs scored_grants.json with relevance scores and rationale
"""

import json
import os
import time
from pathlib import Path
import anthropic

RAW_GRANTS_FILE = Path("raw_grants.json")
SCORED_GRANTS_FILE = Path("scored_grants.json")
EXISTING_SCORED_FILE = Path("docs/grants_data.json")

SUN_METALON_PROFILE = """
COMPANY: Sun Metalon
INDUSTRY: Deep tech hardware — metal manufacturing and recycling

TECHNOLOGY: Proprietary system that cleans metal scrap (dross, slag, contaminated scrap) 
generated during metal production and returns it as purified metal back into the production 
stream. Eliminates waste, reduces raw material cost, improves yield.

CUSTOMERS: Foundries, Tier 1/2 metal suppliers, multinational metal producers (e.g. Nippon Steel)

STAGE: Scaling — ~15 US employees (Wood Dale, IL), ~30 in Japan (Yokohama)

NAICS CODES: 331510 (Iron and Steel Foundries), 562920 (Materials Recovery Facilities), 
333249 (Other Industrial and Commercial Machinery Manufacturing)

TARGET GRANT AGENCIES: DOE (ARPA-E, Advanced Manufacturing Office), DOD, NSF, EPA, NIST

KEY KEYWORDS: metal scrap, dross, slag, metal recycling, foundry, metal recovery, 
aluminum recycling, steel recycling, circular manufacturing, metal purification, 
industrial waste reduction, secondary metals, clean manufacturing

PHASE ELIGIBILITY: SBIR Phase I and Phase II. STTR possible if university partner found.

GRANT SWEET SPOTS:
- Manufacturing efficiency / industrial decarbonization
- Metal recycling and circular economy
- Clean energy manufacturing processes
- Waste reduction in industrial processes
- Advanced materials recovery
- Foundry modernization
"""

SCORE_PROMPT_TEMPLATE = """You are evaluating federal grant opportunities for Sun Metalon.

SUN METALON PROFILE:
{profile}

GRANT TO EVALUATE:
Title: {title}
Agency: {agency}
Program: {program}
Phase: {phase}
Description: {description}
Award Amount: {award_amount}
Close Date: {close_date}
URL: {url}

Score this grant's relevance to Sun Metalon on a scale of 0-100:
- 80-100: Excellent fit — directly addresses Sun Metalon's technology or market
- 60-79: Good fit — related to manufacturing, recycling, or clean industrial processes  
- 40-59: Moderate fit — tangentially related, worth reviewing
- 20-39: Weak fit — general manufacturing but unlikely match
- 0-19: Not relevant

Respond ONLY with a JSON object in this exact format (no markdown, no explanation outside JSON):
{{
  "score": <number 0-100>,
  "tier": "<Excellent|Good|Moderate|Weak|Not Relevant>",
  "rationale": "<2 sentences max explaining why this grant fits or doesn't fit Sun Metalon>",
  "key_match": "<the single most relevant aspect: technology/market/agency/keyword>",
  "flag_urgent": <true if close_date is within 30 days, else false>
}}"""


def score_grant(client, grant):
    """Send a single grant to Claude for scoring"""
    description = grant.get("description", "")
    if len(description) > 1500:
        description = description[:1500] + "..."

    prompt = SCORE_PROMPT_TEMPLATE.format(
        profile=SUN_METALON_PROFILE,
        title=grant.get("title", "N/A"),
        agency=grant.get("agency", "N/A"),
        program=grant.get("program", "N/A"),
        phase=grant.get("phase", "N/A"),
        description=description,
        award_amount=grant.get("award_amount", "N/A"),
        close_date=grant.get("close_date", "N/A"),
        url=grant.get("url", "N/A")
    )

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)


def load_existing_grants():
    """Load already-scored grants to merge with new ones"""
    if EXISTING_SCORED_FILE.exists():
        with open(EXISTING_SCORED_FILE) as f:
            data = json.load(f)
            return {g["id"]: g for g in data.get("grants", [])}
    return {}


def run():
    print(f"\n{'='*50}")
    print("Grant Scorer — Claude API")
    print(f"{'='*50}\n")

    if not RAW_GRANTS_FILE.exists():
        print("No raw_grants.json found. Run scraper.py first.")
        return []

    with open(RAW_GRANTS_FILE) as f:
        grants = json.load(f)

    if not grants:
        print("No new grants to score.")
        return []

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    client = anthropic.Anthropic(api_key=api_key)

    print(f"Scoring {len(grants)} grants...\n")

    scored = []
    errors = []

    for i, grant in enumerate(grants):
        title = grant.get("title", "Unknown")[:60]
        print(f"[{i+1}/{len(grants)}] {title}...", end=" ", flush=True)

        try:
            result = score_grant(client, grant)
            score = result.get("score", 0)
            tier = result.get("tier", "Unknown")
            print(f"→ {score}/100 ({tier})")

            scored_grant = {
                **grant,
                "score": score,
                "tier": tier,
                "rationale": result.get("rationale", ""),
                "key_match": result.get("key_match", ""),
                "flag_urgent": result.get("flag_urgent", False),
                "scored_at": __import__("datetime").datetime.now().isoformat()
            }
            # Remove raw data to keep file size manageable
            scored_grant.pop("raw", None)
            scored.append(scored_grant)

        except Exception as e:
            print(f"→ ERROR: {e}")
            errors.append({"grant": grant.get("id"), "error": str(e)})

        # Rate limit — be gentle with the API
        if i < len(grants) - 1:
            time.sleep(0.5)

    # Sort by score descending
    scored.sort(key=lambda x: x.get("score", 0), reverse=True)

    # Merge with existing scored grants (keep history)
    existing = load_existing_grants()
    for g in scored:
        existing[g["id"]] = g

    all_grants = sorted(existing.values(), key=lambda x: x.get("score", 0), reverse=True)

    # Save scored output
    with open(SCORED_GRANTS_FILE, "w") as f:
        json.dump(scored, f, indent=2)

    # Save merged dashboard data
    Path("docs").mkdir(exist_ok=True)
    dashboard_data = {
        "last_updated": __import__("datetime").datetime.now().isoformat(),
        "total_grants": len(all_grants),
        "new_this_run": len(scored),
        "grants": all_grants
    }
    with open(EXISTING_SCORED_FILE, "w") as f:
        json.dump(dashboard_data, f, indent=2)

    print(f"\n{'='*50}")
    print(f"Scored: {len(scored)} grants")
    print(f"Errors: {len(errors)}")
    print(f"Top match: {scored[0]['title'][:50] if scored else 'None'} ({scored[0].get('score', 0)}/100 if scored else '')")
    print(f"Saved to docs/grants_data.json")

    return scored


if __name__ == "__main__":
    run()
