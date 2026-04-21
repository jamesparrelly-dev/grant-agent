"""
build_dashboard.py — Generates static dashboard/index.html from grants_data.json
This HTML file is committed to the repo and served via GitHub Pages
"""

import json
from pathlib import Path
from datetime import datetime

GRANTS_DATA_FILE = Path("dashboard/grants_data.json")
DASHBOARD_OUTPUT = Path("dashboard/index.html")

DASHBOARD_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sun Metalon — Grant Monitor</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #0a0a0f;
    --surface: #111118;
    --surface2: #18181f;
    --border: #2a2a35;
    --border2: #353545;
    --text: #e8e8f0;
    --text2: #9898b0;
    --text3: #5a5a70;
    --gold: #c9a84c;
    --gold-dim: #7a6230;
    --blue: #4a9eff;
    --blue-dim: #1a3a66;
    --green: #3ecf8e;
    --green-dim: #0f4030;
    --amber: #f0a030;
    --amber-dim: #5a3a10;
    --red: #ef4444;
    --red-dim: #4a1414;
    --purple: #a78bfa;
    --purple-dim: #2d1f5a;
    --mono: 'IBM Plex Mono', monospace;
    --sans: 'IBM Plex Sans', sans-serif;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--sans);
    font-size: 14px;
    line-height: 1.6;
    min-height: 100vh;
  }

  /* TOP BAR */
  .topbar {
    border-bottom: 1px solid var(--border);
    padding: 0 32px;
    height: 56px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    background: var(--bg);
    z-index: 100;
  }
  .logo {
    display: flex;
    align-items: center;
    gap: 10px;
    font-family: var(--mono);
    font-size: 13px;
    font-weight: 500;
    letter-spacing: 0.05em;
    color: var(--text);
  }
  .logo-mark {
    width: 28px; height: 28px;
    background: var(--gold);
    border-radius: 4px;
    display: flex; align-items: center; justify-content: center;
    font-size: 14px; font-weight: 600; color: #0a0a0f;
  }
  .last-updated {
    font-family: var(--mono);
    font-size: 11px;
    color: var(--text3);
  }

  /* STATS BAR */
  .stats-bar {
    display: flex;
    gap: 1px;
    background: var(--border);
    border-bottom: 1px solid var(--border);
  }
  .stat {
    flex: 1;
    padding: 16px 24px;
    background: var(--surface);
  }
  .stat-label {
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text3);
    margin-bottom: 4px;
  }
  .stat-value {
    font-family: var(--mono);
    font-size: 22px;
    font-weight: 500;
    color: var(--text);
  }
  .stat-value.gold { color: var(--gold); }
  .stat-value.green { color: var(--green); }
  .stat-value.blue { color: var(--blue); }

  /* CONTROLS */
  .controls {
    padding: 16px 32px;
    display: flex;
    gap: 12px;
    align-items: center;
    border-bottom: 1px solid var(--border);
    flex-wrap: wrap;
  }
  .search-wrap {
    position: relative;
    flex: 1;
    min-width: 200px;
  }
  .search-wrap svg {
    position: absolute;
    left: 12px;
    top: 50%;
    transform: translateY(-50%);
    opacity: 0.4;
  }
  input[type="search"] {
    width: 100%;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text);
    font-family: var(--sans);
    font-size: 13px;
    padding: 8px 12px 8px 36px;
    outline: none;
    transition: border-color 0.15s;
  }
  input[type="search"]:focus { border-color: var(--border2); }
  input[type="search"]::placeholder { color: var(--text3); }

  .filter-group {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
  }
  .filter-btn {
    padding: 6px 14px;
    border-radius: 20px;
    border: 1px solid var(--border);
    background: transparent;
    color: var(--text2);
    font-family: var(--mono);
    font-size: 11px;
    cursor: pointer;
    transition: all 0.15s;
    letter-spacing: 0.03em;
  }
  .filter-btn:hover { border-color: var(--border2); color: var(--text); }
  .filter-btn.active { border-color: var(--gold); color: var(--gold); background: rgba(201,168,76,0.08); }

  .sort-select {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text2);
    font-family: var(--mono);
    font-size: 11px;
    padding: 7px 12px;
    outline: none;
    cursor: pointer;
  }

  /* GRANT TABLE */
  .grant-list {
    padding: 0 32px 40px;
  }

  .grant-card {
    border: 1px solid var(--border);
    border-radius: 8px;
    margin-top: 12px;
    background: var(--surface);
    transition: border-color 0.15s, background 0.15s;
    overflow: hidden;
  }
  .grant-card:hover { border-color: var(--border2); background: var(--surface2); }
  .grant-card.urgent { border-left: 3px solid var(--amber); }

  .grant-header {
    padding: 16px 20px;
    display: grid;
    grid-template-columns: 52px 1fr auto;
    gap: 16px;
    align-items: start;
    cursor: pointer;
  }

  .score-badge {
    width: 48px; height: 48px;
    border-radius: 6px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    font-family: var(--mono);
    flex-shrink: 0;
  }
  .score-badge .num {
    font-size: 18px;
    font-weight: 500;
    line-height: 1;
  }
  .score-badge .lbl {
    font-size: 9px;
    letter-spacing: 0.05em;
    opacity: 0.7;
    margin-top: 2px;
  }
  .score-excellent { background: var(--green-dim); color: var(--green); }
  .score-good { background: var(--blue-dim); color: var(--blue); }
  .score-moderate { background: var(--amber-dim); color: var(--amber); }
  .score-weak { background: rgba(30,30,40,1); color: var(--text3); }
  .score-not-relevant { background: rgba(20,20,30,1); color: var(--text3); }

  .grant-title-block {}
  .grant-title {
    font-size: 14px;
    font-weight: 500;
    color: var(--text);
    margin-bottom: 6px;
    line-height: 1.4;
  }
  .grant-meta {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    align-items: center;
  }
  .meta-chip {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 0.04em;
    padding: 2px 8px;
    border-radius: 4px;
    background: var(--surface2);
    color: var(--text2);
    border: 1px solid var(--border);
  }
  .meta-chip.source { color: var(--purple); border-color: var(--purple-dim); background: var(--purple-dim); }
  .meta-chip.urgent-chip { color: var(--amber); border-color: var(--amber-dim); background: var(--amber-dim); }
  .meta-chip.amount { color: var(--gold); border-color: var(--gold-dim); background: rgba(201,168,76,0.06); }

  .grant-actions {
    display: flex;
    flex-direction: column;
    gap: 6px;
    align-items: flex-end;
    flex-shrink: 0;
  }
  .btn-link {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 7px 14px;
    border-radius: 6px;
    border: 1px solid var(--border);
    background: transparent;
    color: var(--text2);
    font-family: var(--mono);
    font-size: 11px;
    text-decoration: none;
    transition: all 0.15s;
    white-space: nowrap;
    cursor: pointer;
  }
  .btn-link:hover { border-color: var(--gold); color: var(--gold); }
  .btn-link.primary { border-color: var(--blue-dim); color: var(--blue); background: rgba(74,158,255,0.06); }
  .btn-link.primary:hover { border-color: var(--blue); }

  .grant-detail {
    display: none;
    padding: 0 20px 16px 20px;
    border-top: 1px solid var(--border);
    margin-top: 4px;
  }
  .grant-detail.open { display: block; }
  .detail-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    padding-top: 16px;
  }
  .detail-section {}
  .detail-label {
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--text3);
    margin-bottom: 6px;
  }
  .detail-value {
    font-size: 13px;
    color: var(--text2);
    line-height: 1.6;
  }
  .rationale-box {
    margin-top: 16px;
    padding: 12px 16px;
    background: var(--surface2);
    border-radius: 6px;
    border-left: 3px solid var(--gold-dim);
  }
  .rationale-box .detail-label { margin-bottom: 6px; }
  .rationale-box .detail-value { color: var(--text); font-size: 13px; }
  .key-match-pill {
    display: inline-block;
    margin-top: 8px;
    padding: 3px 10px;
    background: rgba(201,168,76,0.08);
    border: 1px solid var(--gold-dim);
    border-radius: 4px;
    font-family: var(--mono);
    font-size: 11px;
    color: var(--gold);
  }

  /* EMPTY STATE */
  .empty {
    text-align: center;
    padding: 60px 20px;
    color: var(--text3);
    font-family: var(--mono);
    font-size: 13px;
  }

  /* COUNT BAR */
  .count-bar {
    padding: 10px 32px;
    font-family: var(--mono);
    font-size: 11px;
    color: var(--text3);
    border-bottom: 1px solid var(--border);
  }
  .count-bar span { color: var(--text2); }

  /* SCROLLBAR */
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
</style>
</head>
<body>

<div class="topbar">
  <div class="logo">
    <div class="logo-mark">S</div>
    SUN METALON / GRANT MONITOR
  </div>
  <div class="last-updated" id="last-updated"></div>
</div>

<div class="stats-bar">
  <div class="stat">
    <div class="stat-label">Total Tracked</div>
    <div class="stat-value blue" id="stat-total">—</div>
  </div>
  <div class="stat">
    <div class="stat-label">Excellent / Good</div>
    <div class="stat-value green" id="stat-high">—</div>
  </div>
  <div class="stat">
    <div class="stat-label">Closing Soon</div>
    <div class="stat-value gold" id="stat-urgent">—</div>
  </div>
  <div class="stat">
    <div class="stat-label">Top Score</div>
    <div class="stat-value" id="stat-top">—</div>
  </div>
</div>

<div class="controls">
  <div class="search-wrap">
    <svg width="14" height="14" viewBox="0 0 16 16" fill="white"><circle cx="6.5" cy="6.5" r="4.5" fill="none" stroke="currentColor" stroke-width="1.5"/><line x1="10.5" y1="10.5" x2="14" y2="14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
    <input type="search" id="search-input" placeholder="Search grants, agencies, keywords...">
  </div>
  <div class="filter-group" id="tier-filters">
    <button class="filter-btn active" data-tier="all">All</button>
    <button class="filter-btn" data-tier="Excellent">Excellent</button>
    <button class="filter-btn" data-tier="Good">Good</button>
    <button class="filter-btn" data-tier="Moderate">Moderate</button>
    <button class="filter-btn" data-tier="urgent">⚡ Urgent</button>
  </div>
  <select class="sort-select" id="sort-select">
    <option value="score">Sort: Score</option>
    <option value="deadline">Sort: Deadline</option>
    <option value="amount">Sort: Amount</option>
    <option value="recent">Sort: Recent</option>
  </select>
</div>

<div class="count-bar"><span id="showing-count">0</span> grants shown</div>

<div class="grant-list" id="grant-list">
  <div class="empty">Loading grants...</div>
</div>

<script>
const DATA_URL = 'grants_data.json';
let allGrants = [];
let activeFilter = 'all';
let activeSort = 'score';
let searchQuery = '';

function scoreClass(tier) {
  const map = {
    'Excellent': 'score-excellent',
    'Good': 'score-good',
    'Moderate': 'score-moderate',
    'Weak': 'score-weak',
    'Not Relevant': 'score-not-relevant'
  };
  return map[tier] || 'score-weak';
}

function formatAmount(a) {
  if (!a) return null;
  const n = parseInt(String(a).replace(/[^0-9]/g,''));
  if (isNaN(n)) return String(a);
  if (n >= 1e6) return '$' + (n/1e6).toFixed(1) + 'M';
  if (n >= 1e3) return '$' + Math.round(n/1e3) + 'K';
  return '$' + n;
}

function daysUntil(dateStr) {
  if (!dateStr) return null;
  try {
    const d = new Date(dateStr);
    const diff = Math.round((d - Date.now()) / 86400000);
    return diff;
  } catch(e) { return null; }
}

function deadlineLabel(dateStr) {
  const d = daysUntil(dateStr);
  if (d === null) return dateStr || 'N/A';
  if (d < 0) return 'Closed';
  if (d === 0) return 'Closes today';
  if (d === 1) return '1 day left';
  return d + ' days left';
}

function renderGrant(g, idx) {
  const days = daysUntil(g.close_date);
  const urgent = g.flag_urgent || (days !== null && days >= 0 && days <= 30);
  const amount = formatAmount(g.award_amount);
  const sc = scoreClass(g.tier);
  const id = 'g' + idx;

  return `
  <div class="grant-card${urgent ? ' urgent' : ''}" id="card-${id}">
    <div class="grant-header" onclick="toggleDetail('${id}')">
      <div class="score-badge ${sc}">
        <div class="num">${g.score || '—'}</div>
        <div class="lbl">SCORE</div>
      </div>
      <div class="grant-title-block">
        <div class="grant-title">${escHtml(g.title || 'Untitled')}</div>
        <div class="grant-meta">
          <span class="meta-chip source">${escHtml(g.source || '')}</span>
          <span class="meta-chip">${escHtml(g.agency || 'Unknown')}</span>
          ${g.program ? `<span class="meta-chip">${escHtml(g.program)}</span>` : ''}
          ${g.phase ? `<span class="meta-chip">${escHtml(g.phase)}</span>` : ''}
          ${amount ? `<span class="meta-chip amount">${amount}</span>` : ''}
          ${urgent && days !== null && days >= 0 ? `<span class="meta-chip urgent-chip">⚡ ${deadlineLabel(g.close_date)}</span>` : ''}
        </div>
      </div>
      <div class="grant-actions">
        <a class="btn-link primary" href="${escHtml(g.url || '#')}" target="_blank" onclick="event.stopPropagation()">
          View Grant ↗
        </a>
        <button class="btn-link" onclick="event.stopPropagation(); toggleDetail('${id}')">
          Details
        </button>
      </div>
    </div>
    <div class="grant-detail" id="detail-${id}">
      <div class="detail-grid">
        <div class="detail-section">
          <div class="detail-label">Agency</div>
          <div class="detail-value">${escHtml(g.agency || 'N/A')}</div>
        </div>
        <div class="detail-section">
          <div class="detail-label">Deadline</div>
          <div class="detail-value">${escHtml(g.close_date || 'N/A')} ${days !== null && days >= 0 ? '· ' + deadlineLabel(g.close_date) : ''}</div>
        </div>
        <div class="detail-section">
          <div class="detail-label">Award Amount</div>
          <div class="detail-value">${amount || 'N/A'}</div>
        </div>
        <div class="detail-section">
          <div class="detail-label">Program / Phase</div>
          <div class="detail-value">${escHtml((g.program || '') + (g.phase ? ' · ' + g.phase : '') || 'N/A')}</div>
        </div>
      </div>
      <div class="rationale-box">
        <div class="detail-label">Claude's Analysis</div>
        <div class="detail-value">${escHtml(g.rationale || 'No analysis available.')}</div>
        ${g.key_match ? `<div class="key-match-pill">Key match: ${escHtml(g.key_match)}</div>` : ''}
      </div>
      ${g.description ? `
      <div style="margin-top:14px">
        <div class="detail-label">Description</div>
        <div class="detail-value" style="max-height:120px;overflow:auto">${escHtml(g.description.slice(0,600))}${g.description.length > 600 ? '...' : ''}</div>
      </div>` : ''}
    </div>
  </div>`;
}

function escHtml(s) {
  return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function toggleDetail(id) {
  const el = document.getElementById('detail-' + id);
  if (el) el.classList.toggle('open');
}

function filtered() {
  let gs = [...allGrants];

  if (activeFilter === 'urgent') {
    gs = gs.filter(g => {
      const d = daysUntil(g.close_date);
      return g.flag_urgent || (d !== null && d >= 0 && d <= 30);
    });
  } else if (activeFilter !== 'all') {
    gs = gs.filter(g => g.tier === activeFilter);
  }

  if (searchQuery) {
    const q = searchQuery.toLowerCase();
    gs = gs.filter(g =>
      (g.title||'').toLowerCase().includes(q) ||
      (g.agency||'').toLowerCase().includes(q) ||
      (g.description||'').toLowerCase().includes(q) ||
      (g.rationale||'').toLowerCase().includes(q) ||
      (g.key_match||'').toLowerCase().includes(q)
    );
  }

  if (activeSort === 'deadline') {
    gs.sort((a,b) => {
      const da = daysUntil(a.close_date) ?? 9999;
      const db = daysUntil(b.close_date) ?? 9999;
      return da - db;
    });
  } else if (activeSort === 'amount') {
    gs.sort((a,b) => {
      const pa = parseInt(String(a.award_amount||'0').replace(/[^0-9]/g,'')) || 0;
      const pb = parseInt(String(b.award_amount||'0').replace(/[^0-9]/g,'')) || 0;
      return pb - pa;
    });
  } else if (activeSort === 'recent') {
    gs.sort((a,b) => (b.scored_at||'').localeCompare(a.scored_at||''));
  } else {
    gs.sort((a,b) => (b.score||0) - (a.score||0));
  }

  return gs;
}

function render() {
  const gs = filtered();
  const list = document.getElementById('grant-list');
  document.getElementById('showing-count').textContent = gs.length;

  if (!gs.length) {
    list.innerHTML = '<div class="empty">No grants match your filters.</div>';
    return;
  }
  list.innerHTML = gs.map((g,i) => renderGrant(g,i)).join('');
}

function updateStats() {
  document.getElementById('stat-total').textContent = allGrants.length;
  const high = allGrants.filter(g => g.score >= 60).length;
  document.getElementById('stat-high').textContent = high;
  const urgent = allGrants.filter(g => {
    const d = daysUntil(g.close_date);
    return g.flag_urgent || (d !== null && d >= 0 && d <= 30);
  }).length;
  document.getElementById('stat-urgent').textContent = urgent;
  const top = allGrants.length ? Math.max(...allGrants.map(g=>g.score||0)) : 0;
  document.getElementById('stat-top').textContent = top + '/100';
}

// Events
document.getElementById('search-input').addEventListener('input', e => {
  searchQuery = e.target.value;
  render();
});

document.getElementById('tier-filters').addEventListener('click', e => {
  const btn = e.target.closest('.filter-btn');
  if (!btn) return;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  activeFilter = btn.dataset.tier;
  render();
});

document.getElementById('sort-select').addEventListener('change', e => {
  activeSort = e.target.value;
  render();
});

// Load data
fetch(DATA_URL)
  .then(r => r.json())
  .then(data => {
    allGrants = data.grants || [];
    const lu = data.last_updated ? new Date(data.last_updated).toLocaleString() : 'Unknown';
    document.getElementById('last-updated').textContent = 'Last updated: ' + lu;
    updateStats();
    render();
  })
  .catch(() => {
    document.getElementById('grant-list').innerHTML =
      '<div class="empty">Could not load grants data. Run the agent first.</div>';
  });
</script>
</body>
</html>'''


def run():
    print(f"\n{'='*50}")
    print("Dashboard Builder")
    print(f"{'='*50}\n")

    Path("dashboard").mkdir(exist_ok=True)

    # Write the dashboard HTML
    with open(DASHBOARD_OUTPUT, "w") as f:
        f.write(DASHBOARD_HTML)

    print(f"✓ Dashboard written to {DASHBOARD_OUTPUT}")

    # Create a minimal grants_data.json if it doesn't exist
    if not GRANTS_DATA_FILE.exists():
        empty_data = {
            "last_updated": datetime.now().isoformat(),
            "total_grants": 0,
            "new_this_run": 0,
            "grants": []
        }
        with open(GRANTS_DATA_FILE, "w") as f:
            json.dump(empty_data, f, indent=2)
        print(f"✓ Created empty grants_data.json")
    else:
        with open(GRANTS_DATA_FILE) as f:
            data = json.load(f)
        print(f"✓ Dashboard will display {len(data.get('grants', []))} grants")


if __name__ == "__main__":
    run()
