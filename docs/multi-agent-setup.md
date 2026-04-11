# Multi-Agent Setup

`NorthStar.md` is the policy document. This file is the runtime setup companion for the current 2-workflow system.

## Current agent routing

| Agent | Model | Active work |
|-------|-------|-------------|
| Grok | `xai/grok-4-1-fast-non-reasoning` | Daily system brief, PR review, Telegram/Linear coordination |
| Alpha | `xai/grok-4-1-fast-non-reasoning` (fallback: `openrouter/nvidia/nemotron-3-super-120b-a12b:free`) | Hourly Polymarket research and trading |
| Kimi | placeholder shell | Reserved for future reassignment; no active jobs, memory, or runtime state |

## Gateway LaunchAgent and cron timezone

OpenClaw evaluates `cron/jobs.json` expressions in the **gateway process timezone**. `agents.defaults.userTimezone` affects agent-facing time, not the cron scheduler. GrokClaw’s workflow health and docs assume **UTC** schedules (`08:00` daily brief, top-of-hour Polymarket).

Set **`TZ=UTC`** in the gateway LaunchAgent `EnvironmentVariables` (see `launchd/com.grokclaw.gateway.plist` in this repo) so `0 8 * * *` fires at 08:00 UTC. Without it, the Mac system zone shifts every job and `_workflow_health.py` will report stale or missing runs.

After changing the plist: `cp launchd/com.grokclaw.gateway.plist ~/Library/LaunchAgents/` (adjust paths if your home or repo root differs), then `./tools/gateway-ctl.sh restart`.

## Prerequisites

### Alpha

1. Keep `OPENROUTER_API_KEY` in `.env` so Alpha can fall back to Nemotron if xAI is unavailable.
2. Restart the gateway with `./tools/gateway-ctl.sh restart`.
3. Verify agent model routing with `openclaw agents list` and a quick `openclaw agent --agent alpha --message "reply OK" --json`.
4. **Paperclip:** Add a second company agent (e.g. title **Research Worker**) with adapter `openclaw_gateway` and `agentId: "alpha"`. Copy that agent’s UUID into `.env` as **`PAPERCLIP_ALPHA_AGENT_ID`** so hourly Polymarket run issues assign to them instead of Grok (see `AGENTS.md` → Paperclip second agent).

## Active scheduled workflows

The only OpenClaw cron jobs that should exist are:

- `grok-daily-brief`
- `alpha-polymarket`

Each of these uses a **thin** `agentTurn` message: run **`./tools/cron-core-workflow-run.sh <job> <agent>`** from the GrokClaw repo root. That script starts Paperclip, records `started`, runs one `openclaw agent` turn from `docs/prompts/cron-work-<job>.md`, and **always** records a terminal line + finishes Paperclip on exit (including failures). Tune agent wall time with `OPENCLAW_AGENT_TIMEOUT_SECONDS` (especially for Alpha).

**Telegram completion announce:** Grok jobs use `delivery.mode: "announce"` so OpenClaw posts a short job-complete notice to the forum. **`alpha-polymarket` uses `delivery.mode: "none"`** because the agent often emits a very long transcript; posting that as the completion message exceeds Telegram’s **4096-character** limit and surfaces as a client-side “something went wrong.” The hourly Polymarket topic is still updated by the workflow itself via **`tools/telegram-post.sh polymarket`** (see `docs/prompts/cron-work-alpha-polymarket.md`). That prompt uses **TRADE** / **HOLD** wording so a normal “no bet this hour” reads as routine risk discipline, not an error. `tools/_telegram_post.py` also truncates any single message over 4096 chars as a safety net.

Validate with:

```bash
python3 tools/cron-jobs-tool.py validate
openclaw cron list
```

## Supporting reliability workflows

These are outside the two core cron jobs but are still part of the live runtime:

- `tools/health-check.sh` from system cron every 2 minutes for fast gateway death detection and watchdog handoff
- `tools/gateway-watchdog.sh` via launchd `com.grokclaw.gateway-watchdog` at `01,06,11,16,21,26,31,36,41,46,51,56` for bounded automatic gateway repair
- `tools/grokclaw-doctor.sh --check --quiet` via launchd `com.grokclaw.doctor` at `02,17,32,47` as the workflow missed-run/drift catch-all
- `tools/pr-review-watch.sh` via launchd `com.grokclaw.pr-review-watch` to wake Grok when the PR review queue changes

## Workflow health flow

Workflow validation is split intentionally:

- `tools/cron-run-record.sh` writes a `started` record as soon as the run issue is created, then writes the final result, closes Paperclip, and runs `tools/_workflow_health.py audit-one <job> --include-paperclip`, piping the JSON to `tools/_workflow_health_handle.py`
- `tools/grokclaw-doctor.sh` runs `tools/_workflow_health.py audit-quick` after the workflow grace windows
- The doctor now runs `tools/_workflow_health.py audit` before declaring green, so “fresh cron evidence” and “full run contract healthy” stay aligned
- `tools/_workflow_health_handle.py` posts Telegram health alerts, requests approval-gated Linear drafts, and dedupes repeated failures in `~/.openclaw/state/workflow-health-failures.json`

## Cron sync

`cron/jobs.json` in the repo is the source of truth.

After editing it:

```bash
python3 tools/cron-jobs-tool.py validate
./tools/sync-cron-jobs.sh --restart
```

Do not commit scheduler state fields. Strip them first:

```bash
python3 tools/cron-jobs-tool.py strip
```

## Manual runs

```bash
# Grok
./tools/run-openclaw-agent.sh

# Alpha
OPENCLAW_AGENT_ID=alpha ./tools/run-openclaw-agent.sh

# Bound long runs or add one retry for transient provider failures
OPENCLAW_AGENT_TIMEOUT_SECONDS=900 OPENCLAW_AGENT_RETRIES=1 ./tools/run-openclaw-agent.sh

# PR queue wake check
./tools/pr-review-watch.sh
```

## Maintenance (cron evidence + workflow-health noise)

After fixing scheduler drift or false-positive workflow health, clean JSONL orphans and automation tickets:

```bash
# Dry-run: lists duplicate/orphan `started` lines in data/cron-runs/*.jsonl
./tools/grokclaw-maintenance.sh cron-runs
./tools/grokclaw-maintenance.sh cron-runs --apply

# Dry-run: open Linear issues with the exact workflow-health template title, stale drafts, state file
./tools/grokclaw-maintenance.sh linear-workflow-health
./tools/grokclaw-maintenance.sh linear-workflow-health --apply
```

`linear-workflow-health --apply` cancels only issues whose title **exactly** matches the workflow-health draft title (see `tools/_workflow_health.py` `build_draft`). It also deletes `data/pending-linear-draft-workflow-health-*.json` and resets `~/.openclaw/state/workflow-health-failures.json`.

### Stuck cron (`already-running` / `in_progress_run`)

If `openclaw cron run` returns `"reason": "already-running"` or workflow health reports a run stuck past grace, OpenClaw’s `jobs.json` may still have `state.runningAtMs` after a dropped client. Clear it and re-enqueue:

```bash
./tools/cron-unstick-and-run.sh 9c1b0a7d4e2f1003 9c1b0a7d4e2f1001
```

(IDs are from `~/.openclaw/cron/jobs.json` / `openclaw cron list`.) The script **disables both core jobs** before restart so the scheduler does not immediately start due runs and race `openclaw cron run`. Dry strip only: `python3 tools/_cron_unstick_running.py --dry-run`.

## Verification

```bash
./tools/run-health-e2e-tests.sh
./tools/grokclaw-doctor.sh --check
openclaw agents list
openclaw cron list
openclaw models list
./tools/pr-review-watch.sh
```

Husky runs `tools/test-all.sh` as a pre-commit hook (shell syntax, Python syntax, full unit suite, e2e smoke).
