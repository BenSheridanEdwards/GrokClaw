#!/bin/sh
# Reset alpha paper-trading state to a clean baseline.
# Backs up prior ledgers/memory first, then starts bankroll at $1000.
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR="$WORKSPACE_ROOT/data/polymarket-reset-backups/$STAMP"

move_if_exists() {
  src="$1"
  rel="$2"
  if [ -f "$src" ]; then
    dst_dir="$BACKUP_DIR/$(dirname "$rel")"
    mkdir -p "$dst_dir"
    mv "$src" "$dst_dir/$(basename "$rel")"
  fi
}

# Trading ledgers/state.
move_if_exists "$WORKSPACE_ROOT/data/polymarket-decisions.json" "data/polymarket-decisions.json"
move_if_exists "$WORKSPACE_ROOT/data/polymarket-results.json" "data/polymarket-results.json"
move_if_exists "$WORKSPACE_ROOT/data/polymarket-trades.json" "data/polymarket-trades.json"
move_if_exists "$WORKSPACE_ROOT/data/polymarket-skips.json" "data/polymarket-skips.json"
move_if_exists "$WORKSPACE_ROOT/data/polymarket-bankroll.json" "data/polymarket-bankroll.json"
move_if_exists "$WORKSPACE_ROOT/data/polymarket-pending-trade.json" "data/polymarket-pending-trade.json"
move_if_exists "$WORKSPACE_ROOT/data/polymarket-promotion-alert.json" "data/polymarket-promotion-alert.json"

# Reset alpha memory stores so new strategy starts clean.
move_if_exists "$WORKSPACE_ROOT/data/alpha/memory/alpha-polymarket.mv2" "data/alpha/memory/alpha-polymarket.mv2"
move_if_exists "$WORKSPACE_ROOT/data/alpha/memory/mempalace-alpha.jsonl" "data/alpha/memory/mempalace-alpha.jsonl"

mkdir -p "$WORKSPACE_ROOT/data"
TODAY_UTC="$(date -u +%F)"
cat >"$WORKSPACE_ROOT/data/polymarket-bankroll.json" <<EOF
{"date":"$TODAY_UTC","market_id":"reset","question":"Dexter strategy baseline reset","side":"hold","odds":1.0,"stake_amount":0.0,"pnl_amount":0.0,"bankroll_before":1000.0,"bankroll_after":1000.0}
EOF

printf '{"armed":false,"last_alert_date":"","last_run_id":"","baseline":"%s"}\n' "$STAMP" >"$WORKSPACE_ROOT/data/polymarket-promotion-alert.json"

echo "Reset complete."
echo "Backup directory: $BACKUP_DIR"
echo "Baseline bankroll: $WORKSPACE_ROOT/data/polymarket-bankroll.json"
