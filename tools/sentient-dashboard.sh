#!/bin/sh
# Generate Sentient dashboard (HTML) with model rankings, trade log, P&L.
# Usage: sentient-dashboard.sh [output_path]
# Default: data/sentient-dashboard.html
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
OUTPUT="${1:-$WORKSPACE_ROOT/data/sentient-dashboard.html}"

exec python3 - "$WORKSPACE_ROOT" "$OUTPUT" <<'PY'
import json
import os
import sys
from datetime import datetime

workspace = sys.argv[1]
out_path = sys.argv[2]
data_dir = os.path.join(workspace, "data")

def load_jsonl(path):
    if not os.path.exists(path):
        return []
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return rows

trades = load_jsonl(os.path.join(data_dir, "sentient-trades.json"))
results = load_jsonl(os.path.join(data_dir, "sentient-results.json"))
decisions = load_jsonl(os.path.join(data_dir, "sentient-decisions.json"))
bankroll_rows = load_jsonl(os.path.join(data_dir, "sentient-bankroll.json"))

current = 1000.0
if bankroll_rows:
    current = float(bankroll_rows[-1].get("bankroll_after", 1000))
total_pnl = sum(float(r.get("pnl_amount", 0)) for r in results)
wins = sum(1 for r in results if r.get("won"))
acc = (wins / len(results) * 100) if results else 0

html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Sentient Model Arena Dashboard</title>
<style>
body{font-family:system-ui;max-width:800px;margin:2em auto;padding:1em;background:#111;color:#eee;}
h1{color:#0af;}
table{border-collapse:collapse;width:100%;}
th,td{border:1px solid #333;padding:0.5em;text-align:left;}
th{background:#222;}
tr:nth-child(even){background:#1a1a1a;}
.win{color:#4f4;}
.loss{color:#f44;}
</style>
</head>
<body>
<h1>Sentient Model Arena Dashboard</h1>
<p><strong>Bankroll:</strong> $%.2f | <strong>P&L:</strong> $%+.2f | <strong>Accuracy:</strong> %.1f%% | <strong>Resolved:</strong> %d</p>
<h2>Trade log</h2>
<table>
<tr><th>Date</th><th>Question</th><th>Side</th><th>Odds</th><th>Result</th><th>P&L</th></tr>
""" % (current, total_pnl, acc, len(results))

for r in results[-20:][::-1]:
    res = "WIN" if r.get("won") else "LOSS"
    cls = "win" if r.get("won") else "loss"
    html += "<tr><td>%s</td><td>%s</td><td>%s</td><td>%.2f</td><td class=\"%s\">%s</td><td class=\"%s\">$%+.2f</td></tr>\n" % (
        r.get("resolved_at", ""),
        (r.get("question", "")[:60] + "…" if len(r.get("question", "")) > 60 else r.get("question", "")),
        r.get("side", ""),
        float(r.get("odds", 0)),
        cls, res, cls, float(r.get("pnl_amount", 0)))

html += "</table>\n<h2>Open trades</h2>\n<table>\n<tr><th>Date</th><th>Question</th><th>Side</th><th>Odds</th></tr>\n"
for t in trades:
    if not t.get("resolved"):
        html += "<tr><td>%s</td><td>%s</td><td>%s</td><td>%.2f</td></tr>\n" % (
            t.get("date", ""),
            (t.get("question", "")[:60] + "…" if len(t.get("question", "")) > 60 else t.get("question", "")),
            t.get("side", ""),
            float(t.get("odds", 0)))
html += """</table>
<p><small>Generated %s — Paper trading only</small></p>
</body>
</html>
""" % datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w") as f:
    f.write(html)
print("Dashboard written to", out_path)
PY
