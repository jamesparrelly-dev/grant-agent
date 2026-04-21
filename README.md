# Sun Metalon — Federal Grant Monitor

Autonomous agent that scans SBIR.gov and Grants.gov daily, scores opportunities against Sun Metalon's profile using Claude, and surfaces matches via Slack and a GitHub Pages dashboard.

## How it works

```
SBIR.gov + Grants.gov
        ↓
   scraper.py     — fetch + dedup new grants
        ↓
   scorer.py      — score 0-100 via Claude API
        ↓
   notify.py      — post top matches to Slack
        ↓
build_dashboard.py — regenerate static dashboard
        ↓
  GitHub Pages    — live dashboard at your-repo URL
```

Runs daily at **7am CT** via GitHub Actions. No server required.

---

## Setup (15 minutes)

### 1. Create the GitHub repository

```bash
git init grant-agent
cd grant-agent
# copy all files here
git add .
git commit -m "initial commit"
gh repo create grant-agent --public --source=. --push
# or push to an existing repo
```

### 2. Enable GitHub Pages

- Go to your repo → **Settings** → **Pages**
- Source: **Deploy from a branch**
- Branch: `main` / folder: `/dashboard`
- Click Save

Your dashboard will be live at:
`https://YOUR-USERNAME.github.io/grant-agent/`

### 3. Add secrets

Go to your repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Secret name | Value |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key from console.anthropic.com |
| `SLACK_WEBHOOK_URL` | Your Slack incoming webhook URL |

**Get a Slack webhook:**
1. Go to https://api.slack.com/apps → Create New App
2. Features → Incoming Webhooks → Activate → Add to channel
3. Copy the webhook URL

### 4. Run manually to test

- Go to your repo → **Actions** → **Grant Monitor — Daily Scan**
- Click **Run workflow**
- Watch the logs — it should fetch, score, and commit results

### 5. Verify the dashboard

After the workflow completes, visit your GitHub Pages URL. You should see scored grants.

---

## Files

| File | Purpose |
|---|---|
| `main.py` | Pipeline orchestrator |
| `scraper.py` | Fetches from SBIR.gov + Grants.gov |
| `scorer.py` | Scores grants via Claude API |
| `notify.py` | Posts to Slack |
| `build_dashboard.py` | Generates static dashboard HTML |
| `requirements.txt` | Python dependencies |
| `.github/workflows/scan.yml` | GitHub Actions schedule |
| `dashboard/index.html` | The live dashboard (auto-generated) |
| `dashboard/grants_data.json` | All scored grants (auto-generated) |
| `seen_ids.json` | Dedup tracker (auto-generated) |

---

## Tuning

**Adjust scoring thresholds** in `scorer.py` — `SCORE_PROMPT_TEMPLATE` controls what Claude evaluates.

**Add more keywords** in `scraper.py` — `SUN_METALON_KEYWORDS` list.

**Change schedule** in `.github/workflows/scan.yml` — edit the cron expression.

**Slack threshold** in `notify.py` — currently notifies for scores ≥ 60. Change the `60` in:
```python
notifiable = [g for g in scored if g.get("score", 0) >= 60]
```
