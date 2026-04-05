# Multi-Agent Setup

`NorthStar.md` is the policy document. This file is the runtime setup companion for the current 3-workflow system.

## Current agent routing

| Agent | Model | Active work |
|-------|-------|-------------|
| Grok | `xai/grok-4-1-fast-non-reasoning` | Daily system brief, OpenClaw research, PR review, Telegram/Linear coordination |
| Alpha | `openrouter/nvidia/nemotron-3-super-120b-a12b:free` | Hourly Polymarket research and trading |
| Kimi | placeholder shell | Reserved for future reassignment; no active jobs, memory, or runtime state |

## Prerequisites

### Alpha

1. Add `OPENROUTER_API_KEY` to `.env`.
2. Restart the gateway with `./tools/gateway-ctl.sh restart`.
3. Verify agent model routing with `openclaw agents list` and a quick `openclaw agent --agent alpha --message "reply OK" --json`.

## Active scheduled workflows

The only OpenClaw cron jobs that should exist are:

- `grok-daily-brief`
- `grok-openclaw-research`
- `alpha-polymarket`

Validate with:

```bash
python3 tools/cron-jobs-tool.py validate
openclaw cron list
```

## Supporting reliability workflows

These are outside the three core cron jobs but are still part of the live runtime:

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
