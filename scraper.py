"""
scraper.py — Fetches grant opportunities from SBIR.gov and Grants.gov
Deduplicates against previously seen grant IDs stored in seen_ids.json
"""

import json
import os
import requests
from datetime import datetime, timedelta
from pathlib import Path

SEEN_IDS_FILE = Path("seen_ids.json")
GRANTS_OUTPUT_FILE = Path("raw_grants.json")

SUN_METALON_KEYWORDS = [
    "metal scrap", "scrap metal", "dross", "slag", "metal recycling",
    "foundry", "metal recovery", "aluminum recycling", "steel recycling",
    "metal manufacturing", "circular manufacturing", "waste metal",
    "metal purification", "metal refining", "secondary metal",
    "manufacturing waste", "industrial recycling", "metal processing"
]

SUN_METALON_NAICS = ["331510", "562920", "333249"]

TARGET_AGENCIES = ["DOE", "DOD", "NSF", "EPA", "ARPA", "ARPA-E", "NIST", "DOC"]


def load_seen_ids():
    if SEEN_IDS_FILE.exists():
        with open(SEEN_IDS_FILE) as f:
            return set(json.load(f))
    return set()


def save_seen_ids(seen_ids):
    with open(SEEN_IDS_FILE, "w") as f:
        json.dump(list(seen_ids), f)


def fetch_sbir_grants():
    """Fetch open SBIR/STTR solicitations from SBIR.gov API"""
    grants = []
    print("Fetching from SBIR.gov...")

    # SBIR.gov public API - open solicitations
    url = "https://api.sbir.gov/public/solicitations"
    params = {
        "rows": 100,
        "open": "true",
        "keyword": " OR ".join(SUN_METALON_KEYWORDS[:6])  # API keyword filter
    }

    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        for item in data.get("results", []):
            grant = {
                "id": f"sbir_{item.get('solicitation_number', item.get('solicitation_id', ''))}",
                "source": "SBIR.gov",
                "title": item.get("program_title") or item.get("solicitation_title", ""),
                "agency": item.get("agency", ""),
                "program": item.get("program", "SBIR"),
                "description": item.get("program_description") or item.get("abstract", ""),
                "open_date": item.get("open_date", ""),
                "close_date": item.get("close_date", ""),
                "award_amount": item.get("award_amount_max") or item.get("award_amount", ""),
                "url": item.get("solicitation_url") or f"https://www.sbir.gov/sbirsearch/detail/{item.get('solicitation_id', '')}",
                "phase": item.get("phase", ""),
                "topics": item.get("topics", []),
                "raw": item
            }
            grants.append(grant)

    except requests.RequestException as e:
        print(f"SBIR.gov API error: {e}")
        # Fallback: try keyword-based topic search
        grants.extend(fetch_sbir_by_keyword())

    print(f"  → {len(grants)} SBIR grants fetched")
    return grants


def fetch_sbir_by_keyword():
    """Fallback: search SBIR.gov by individual keywords"""
    grants = []
    seen = set()

    for keyword in ["metal recycling", "foundry", "metal scrap", "dross"]:
        url = "https://api.sbir.gov/public/solicitations"
        params = {"rows": 25, "open": "true", "keyword": keyword}
        try:
            resp = requests.get(url, params=params, timeout=20)
            if resp.status_code == 200:
                for item in resp.json().get("results", []):
                    sid = str(item.get("solicitation_id", ""))
                    if sid and sid not in seen:
                        seen.add(sid)
                        grants.append({
                            "id": f"sbir_{sid}",
                            "source": "SBIR.gov",
                            "title": item.get("program_title") or item.get("solicitation_title", ""),
                            "agency": item.get("agency", ""),
                            "program": item.get("program", "SBIR"),
                            "description": item.get("program_description", ""),
                            "open_date": item.get("open_date", ""),
                            "close_date": item.get("close_date", ""),
                            "award_amount": item.get("award_amount_max", ""),
                            "url": f"https://www.sbir.gov/sbirsearch/detail/{sid}",
                            "phase": item.get("phase", ""),
                            "topics": [],
                            "raw": item
                        })
        except Exception:
            pass
    return grants


GRANTS_GOV_SEARCHES = [
    # Targeted pass — specific to Sun Metalon's tech
    "metal recycling scrap foundry dross slag metal recovery",
    # Broad pass — catches adjacent manufacturing and clean-energy grants
    "manufacturing recycling industrial materials recovery clean energy advanced manufacturing",
]


def _parse_grants_gov_item(item):
    return {
        "id": f"gg_{item.get('id', '')}",
        "source": "Grants.gov",
        "title": item.get("title", ""),
        "agency": item.get("agencyName", ""),
        "program": "Federal Grant",
        "description": item.get("synopsis", "") or item.get("description", ""),
        "open_date": item.get("openDate", ""),
        "close_date": item.get("closeDate", ""),
        "award_amount": item.get("awardCeiling", ""),
        "url": f"https://www.grants.gov/search-results-detail/{item.get('id', '')}",
        "phase": "",
        "topics": [],
        "raw": item,
    }


def fetch_grants_gov():
    """Fetch from Grants.gov search API using two keyword passes."""
    print("Fetching from Grants.gov...")
    seen = set()
    grants = []

    url = "https://apply07.grants.gov/grantsws/rest/opportunities/search/"

    for keyword_set in GRANTS_GOV_SEARCHES:
        payload = {
            "keyword": keyword_set,
            "oppStatuses": "forecasted|posted",
            "rows": 100,
            "startRecordNum": 0,
            "sortBy": "openDate|desc",
            "fundingCategories": "ST|MR|EN|AG",  # Science & Tech, Manufacturing, Energy, Agriculture
            "fundingInstruments": "G|CA|O",       # Grants, Cooperative Agreements, Other
        }
        try:
            resp = requests.post(url, json=payload, timeout=30)
            resp.raise_for_status()
            for item in resp.json().get("oppHits", []):
                gid = str(item.get("id", ""))
                if gid and gid not in seen:
                    seen.add(gid)
                    grants.append(_parse_grants_gov_item(item))
        except requests.RequestException as e:
            print(f"  Grants.gov search error ({keyword_set[:30]}…): {e}")

    print(f"  → {len(grants)} Grants.gov opportunities fetched")
    return grants


BROAD_KEYWORDS = [
    "manufacturing", "recycling", "industrial", "materials recovery",
    "clean energy", "advanced manufacturing", "circular economy",
    "waste reduction", "sustainability", "decarbonization",
]


def is_relevant(grant):
    """Pre-filter before sending to Claude for scoring.

    Grants.gov results are already API-filtered by keyword search, so pass
    them all through. For SBIR, require at least one keyword or agency match.
    """
    if grant.get("source") == "Grants.gov":
        return True

    text = (
        (grant.get("title") or "") + " " +
        (grant.get("description") or "") + " " +
        " ".join(grant.get("topics", []))
    ).lower()

    all_keywords = [kw.lower() for kw in SUN_METALON_KEYWORDS + BROAD_KEYWORDS]
    keyword_hit = any(kw in text for kw in all_keywords)

    agency = (grant.get("agency") or "").upper()
    agency_hit = any(a in agency for a in TARGET_AGENCIES)

    return keyword_hit or agency_hit


def deduplicate(grants, seen_ids):
    """Remove grants we've already processed"""
    new_grants = []
    for grant in grants:
        gid = grant["id"]
        if gid and gid not in seen_ids:
            new_grants.append(grant)
    return new_grants


def run():
    print(f"\n{'='*50}")
    print(f"Grant Scanner — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}\n")

    seen_ids = load_seen_ids()
    print(f"Previously seen grants: {len(seen_ids)}\n")

    # Fetch from all sources
    all_grants = []
    all_grants.extend(fetch_sbir_grants())
    all_grants.extend(fetch_grants_gov())

    print(f"\nTotal fetched: {len(all_grants)}")

    # Dedup
    new_grants = deduplicate(all_grants, seen_ids)
    print(f"New (not seen before): {len(new_grants)}")

    # Pre-filter by keyword relevance
    relevant_grants = [g for g in new_grants if is_relevant(g)]
    print(f"Keyword-relevant: {len(relevant_grants)}")

    # Update seen IDs (mark all new as seen, not just relevant ones)
    for g in new_grants:
        seen_ids.add(g["id"])
    save_seen_ids(seen_ids)

    # Save relevant grants for scorer
    with open(GRANTS_OUTPUT_FILE, "w") as f:
        json.dump(relevant_grants, f, indent=2)

    print(f"\nSaved {len(relevant_grants)} grants to {GRANTS_OUTPUT_FILE}")
    return relevant_grants


if __name__ == "__main__":
    run()
