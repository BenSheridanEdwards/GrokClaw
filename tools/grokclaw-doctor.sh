#!/bin/sh
# GrokClaw self-healing doctor.
# Diagnoses system health and auto-heals what it can.
# What it can't fix, it reports to Telegram health.
#
# Modes:
#   --check    Read-only diagnostics (default)
#   --heal     Diagnose + attempt auto-recovery
#   --quiet    Suppress stdout; only alert Telegram on failures
#
# Exit codes: 0 = healthy, 1 = issues found (healed or reported)
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

HEAL=0
QUIET=0
for arg in "$@"; do
  case "$arg" in
    --heal)  HEAL=1 ;;
    --quiet) QUIET=1 ;;
    --check) HEAL=0 ;;
  esac
done

if [ -f "$WORKSPACE_ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$WORKSPACE_ROOT/.env"
  set +a
fi

ISSUES=""
HEALED=""
FAILED=""
WORKFLOW_FAILURE_ESCALATED=0

log() {
  [ "$QUIET" -eq 0 ] && echo "$1" || true
}

add_issue() {
  ISSUES="${ISSUES}${ISSUES:+\n}$1"
}

add_healed() {
  HEALED="${HEALED}${HEALED:+\n}$1"
}

add_failed() {
  FAILED="${FAILED}${FAILED:+\n}$1"
}

# --- 1. Gateway health ---
log "Checking gateway..."
if curl -sf --connect-timeout 3 http://127.0.0.1:18800/health >/dev/null 2>&1; then
  log "  Gateway: UP"
else
  add_issue "Gateway DOWN"
  if [ "$HEAL" -eq 1 ]; then
    log "  Healing: restarting gateway..."
    if "$WORKSPACE_ROOT/tools/gateway-ctl.sh" restart >/dev/null 2>&1; then
      sleep 8
      if curl -sf --connect-timeout 3 http://127.0.0.1:18800/health >/dev/null 2>&1; then
        add_healed "Gateway restarted successfully"
      else
        add_failed "Gateway restart failed — still DOWN"
      fi
    else
      add_failed "Gateway restart command failed"
    fi
  fi
fi

# --- 2. Paperclip health ---
log "Checking Paperclip..."
if curl -sf --connect-timeout 3 http://127.0.0.1:3100/api/health >/dev/null 2>&1; then
  log "  Paperclip: UP"
else
  add_issue "Paperclip DOWN"
  if [ "$HEAL" -eq 1 ]; then
    log "  Healing: restarting Paperclip..."
    if "$WORKSPACE_ROOT/tools/paperclip-ctl.sh" restart >/dev/null 2>&1; then
      sleep 8
      if curl -sf --connect-timeout 3 http://127.0.0.1:3100/api/health >/dev/null 2>&1; then
        add_healed "Paperclip restarted successfully"
      else
        add_failed "Paperclip restart failed — still DOWN"
      fi
    else
      add_failed "Paperclip restart command failed"
    fi
  fi
fi

# --- 3. Ollama health ---
log "Checking Ollama..."
if curl -sf --connect-timeout 3 http://127.0.0.1:11434/ >/dev/null 2>&1; then
  log "  Ollama: UP"
else
  add_issue "Ollama DOWN (Kimi jobs will fail)"
  if [ "$HEAL" -eq 1 ]; then
    log "  Healing: starting Ollama via brew services..."
    if brew services start ollama >/dev/null 2>&1 || ollama serve >/dev/null 2>&1 &
    then
      sleep 5
      if curl -sf --connect-timeout 3 http://127.0.0.1:11434/ >/dev/null 2>&1; then
        add_healed "Ollama started successfully"
      else
        add_failed "Ollama start failed — still DOWN"
      fi
    else
      add_failed "Could not start Ollama"
    fi
  fi
fi

# --- 3b. Model fallback detection (once-per-day notification) ---
log "Checking for model fallbacks..."
FALLBACK_STATE="$HOME/.openclaw/state/model-fallback-notified.txt"
FALLBACK_TODAY="$(date -u +%Y-%m-%d)"
FALLBACK_LAST="$(cat "$FALLBACK_STATE" 2>/dev/null || echo "")"
GATEWAY_STDERR="$HOME/.openclaw/logs/gateway-stderr.log"

if [ "$FALLBACK_TODAY" != "$FALLBACK_LAST" ] && [ -f "$GATEWAY_STDERR" ]; then
  fallback_summary="$(python3 -c "
import re, sys
from collections import OrderedDict
hits = OrderedDict()
for line in open('$GATEWAY_STDERR', encoding='utf-8', errors='replace'):
    if '$FALLBACK_TODAY' not in line:
        continue
    m = re.search(r'decision=(?:fallback_model|surface_error).*reason=(\w+).*provider=(\S+)', line)
    if m:
        reason, provider = m.group(1), m.group(2)
        provider_short = provider.split('/')[-1].split(':')[0] if '/' in provider else provider
        key = (reason, provider_short)
        hits[key] = hits.get(key, 0) + 1
if not hits:
    sys.exit(0)
parts = []
for (reason, prov), count in hits.items():
    label = 'rate limit' if reason == 'rate_limit' else 'timeout' if reason == 'timeout' else reason
    parts.append(f'{prov}: {label} ({count}x)')
print('; '.join(parts))
" 2>/dev/null || echo "")"

  if [ -n "$fallback_summary" ]; then
    log "  Model fallbacks today: $fallback_summary"
    mkdir -p "$(dirname "$FALLBACK_STATE")"
    printf '%s' "$FALLBACK_TODAY" > "$FALLBACK_STATE"
    if [ -n "${TELEGRAM_BOT_TOKEN:-}" ]; then
      printf '%s\n' "Model fallbacks today: $fallback_summary. Agents fell back to next provider in chain." \
        | "$WORKSPACE_ROOT/tools/telegram-post.sh" health 2>/dev/null || true
    fi
  else
    log "  No model fallbacks today"
  fi
else
  log "  Already notified today"
fi

# --- 4. Telegram connectivity ---
log "Checking Telegram..."
TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
  add_issue "TELEGRAM_BOT_TOKEN not set"
else
  if curl -sf --connect-timeout 5 "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe" >/dev/null 2>&1; then
    log "  Telegram API: reachable"
  else
    add_failed "Telegram API unreachable (network or token issue) — cannot self-report"
  fi
fi

# --- 5. launchd agents ---
log "Checking launchd..."
for label in com.grokclaw.gateway com.grokclaw.paperclip; do
  if launchctl list 2>/dev/null | grep -q "$label"; then
    log "  $label: loaded"
  else
    add_issue "$label not loaded in launchd"
    if [ "$HEAL" -eq 1 ]; then
      plist="$HOME/Library/LaunchAgents/${label}.plist"
      if [ -f "$plist" ]; then
        log "  Healing: bootstrapping $label..."
        if launchctl bootstrap "gui/$(id -u)" "$plist" 2>/dev/null; then
          add_healed "$label loaded"
        else
          add_failed "Failed to load $label"
        fi
      else
        add_failed "$label plist not found at $plist"
      fi
    fi
  fi
done

# --- 6. System crontab ---
log "Checking system crontab..."
if crontab -l 2>/dev/null | grep -q "health-check.sh"; then
  log "  health-check.sh: scheduled"
else
  add_issue "health-check.sh not in system crontab"
  if [ "$HEAL" -eq 1 ]; then
    log "  Healing: adding health-check to crontab..."
    (crontab -l 2>/dev/null; echo "*/2 * * * * $WORKSPACE_ROOT/tools/health-check.sh >> /tmp/openclaw-health.log 2>&1") | crontab -
    add_healed "health-check.sh added to crontab"
  fi
fi

# --- 7. Cron jobs validation ---
log "Checking cron config..."
if python3 "$WORKSPACE_ROOT/tools/cron-jobs-tool.py" validate >/dev/null 2>&1; then
  log "  cron/jobs.json: valid"
else
  add_issue "cron/jobs.json validation failed"
fi

# --- 8. Repo vs runtime cron sync ---
log "Checking cron sync..."
RUNTIME_CRON="$HOME/.openclaw/cron/jobs.json"
if [ -f "$RUNTIME_CRON" ]; then
  drift=$(python3 -c "
import json, hashlib
def normalize_schedule(s):
    if not isinstance(s, dict): return s
    return {'kind': s.get('kind'), 'expr': s.get('expr')}
def job_hash(j):
    return hashlib.md5(json.dumps({
        'name': j.get('name'), 'schedule': normalize_schedule(j.get('schedule')),
        'agentId': j.get('agentId'), 'enabled': j.get('enabled'),
        'payload': j.get('payload'), 'delivery': j.get('delivery'),
    }, sort_keys=True).encode()).hexdigest()
repo = json.load(open('$WORKSPACE_ROOT/cron/jobs.json'))
rt = json.load(open('$RUNTIME_CRON'))
repo_h = {j['id']: job_hash(j) for j in repo.get('jobs', [])}
rt_h = {j['id']: job_hash(j) for j in rt.get('jobs', [])}
diffs = []
for jid in set(repo_h) | set(rt_h):
    if jid not in rt_h:
        diffs.append(f'missing from runtime: {jid}')
    elif jid not in repo_h:
        pass
    elif repo_h[jid] != rt_h[jid]:
        rn = next((j['name'] for j in repo['jobs'] if j['id'] == jid), jid)
        diffs.append(f'config drift: {rn}')
print('|'.join(diffs) if diffs else '')
" 2>/dev/null || echo "error")
  if [ -z "$drift" ]; then
    log "  Cron sync: OK"
  elif [ "$drift" = "error" ]; then
    add_issue "Could not compare cron configs"
  else
    add_issue "Cron drift: $drift"
    if [ "$HEAL" -eq 1 ]; then
      log "  Healing: syncing cron jobs..."
      if "$WORKSPACE_ROOT/tools/sync-cron-jobs.sh" >/dev/null 2>&1; then
        "$WORKSPACE_ROOT/tools/gateway-ctl.sh" restart >/dev/null 2>&1
        sleep 5
        add_healed "Cron jobs synced and gateway restarted"
      else
        add_failed "Cron sync failed"
      fi
    fi
  fi
else
  add_issue "Runtime cron file missing ($RUNTIME_CRON)"
  if [ "$HEAL" -eq 1 ]; then
    log "  Healing: syncing cron jobs..."
    if "$WORKSPACE_ROOT/tools/sync-cron-jobs.sh" --restart >/dev/null 2>&1; then
      add_healed "Cron jobs synced from repo"
    else
      add_failed "Cron sync failed"
    fi
  fi
fi

# --- 9. Core workflow health (quick detect + full contract verification) ---
log "Checking core workflow run evidence (cron-runs)..."
WH_QUICK="$(mktemp)"
if python3 "$WORKSPACE_ROOT/tools/_workflow_health.py" audit-quick >"$WH_QUICK" 2>&1; then
  quick_healthy="$(python3 -c 'import json,sys; print("1" if json.load(open(sys.argv[1], encoding="utf-8")).get("healthy") else "0")' "$WH_QUICK" 2>/dev/null || echo "0")"
else
  quick_healthy="0"
fi

WH_FULL="$(mktemp)"
if python3 "$WORKSPACE_ROOT/tools/_workflow_health.py" audit >"$WH_FULL" 2>/dev/null; then
  full_healthy="$(python3 -c 'import json,sys; print("1" if json.load(open(sys.argv[1], encoding="utf-8")).get("healthy") else "0")' "$WH_FULL" 2>/dev/null || echo "0")"
  if [ "$quick_healthy" = "1" ] && [ "$full_healthy" = "1" ]; then
    log "  Core workflows: recent runs recorded"
  else
    python3 "$WORKSPACE_ROOT/tools/_workflow_health_handle.py" <"$WH_FULL" >/dev/null 2>&1 || true
    WORKFLOW_FAILURE_ESCALATED=1
    log "  Core workflows: failure escalated through workflow health handler"
  fi
else
  add_issue "Workflow health: full audit failed"
fi
rm -f "$WH_QUICK"
rm -f "$WH_FULL"

# --- 10. Gateway CLI auth ---
log "Checking gateway auth..."
if OPENCLAW_CONFIG_PATH="$HOME/.openclaw/openclaw.json" openclaw cron list >/dev/null 2>&1; then
  log "  Gateway auth: OK"
else
  add_issue "Gateway CLI auth failed (token mismatch or gateway unreachable)"
fi

# --- Summary and alerting ---
if [ -z "$ISSUES" ] && [ -z "$FAILED" ] && [ "$WORKFLOW_FAILURE_ESCALATED" -eq 0 ]; then
  log ""
  log "All checks passed."
  exit 0
fi

summary=""
if [ -n "$HEALED" ]; then
  summary="${summary}Auto-healed:\n${HEALED}\n"
fi
if [ -n "$FAILED" ]; then
  summary="${summary}NEEDS ATTENTION:\n${FAILED}\n"
fi
if [ -n "$ISSUES" ] && [ "$HEAL" -eq 0 ]; then
  summary="${summary}Issues found (run with --heal to fix):\n${ISSUES}\n"
fi
if [ "$WORKFLOW_FAILURE_ESCALATED" -eq 1 ]; then
  summary="${summary}Workflow failures were escalated through the approval-gated health handler.\n"
fi

log ""
log "=== Doctor summary ==="
printf '%b\n' "$summary"

if [ -n "$FAILED" ] || { [ -n "$ISSUES" ] && [ "$HEAL" -eq 0 ]; }; then
  alert_body="GrokClaw Doctor:"
  if [ -n "$HEALED" ]; then
    alert_body="$alert_body\nHealed: $(printf '%b' "$HEALED" | tr '\n' '; ')"
  fi
  if [ -n "$FAILED" ]; then
    alert_body="$alert_body\nFailed: $(printf '%b' "$FAILED" | tr '\n' '; ')"
  fi
  if [ -n "$ISSUES" ] && [ "$HEAL" -eq 0 ]; then
    alert_body="$alert_body\nIssues: $(printf '%b' "$ISSUES" | tr '\n' '; ')"
  fi

  if [ -n "$TELEGRAM_BOT_TOKEN" ] && curl -sf --connect-timeout 3 "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe" >/dev/null 2>&1; then
    "$WORKSPACE_ROOT/tools/telegram-post.sh" health "$(printf '%b' "$alert_body")" 2>/dev/null || true
  fi
  exit 1
fi

if [ "$WORKFLOW_FAILURE_ESCALATED" -eq 1 ]; then
  exit 1
fi

exit 0
