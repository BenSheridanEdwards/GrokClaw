# Multi-Agent Setup

`NorthStar.md` is the policy document. This file is the runtime setup companion for the current 4-workflow system.

## Current agent routing

| Agent | Model | Active work |
|-------|-------|-------------|
| Grok | `xai/grok-4-1-fast-non-reasoning` | Daily system brief, OpenClaw research, PR review, Telegram/Linear coordination |
| Kimi | `ollama/kimi-k2.5:cloud` | Hourly Polymarket research and trading |
| Alpha | `openrouter/arcee-ai/trinity-large-preview:free` | Hourly Polymarket research and trading |

## Prerequisites

### Kimi

1. Install [Ollama](https://ollama.ai) and ensure it is running.
2. Sign in for cloud models with `ollama signin`.
3. Pull Kimi with `ollama pull kimi-k2.5:cloud`.
4. Verify with `ollama list`.

### Alpha

1. Add `OPENROUTER_API_KEY` to `.env`.
2. Restart the gateway with `./tools/gateway-ctl.sh restart`.

## Active scheduled workflows

The only OpenClaw cron jobs that should exist are:

- `grok-daily-brief`
- `grok-openclaw-research`
- `alpha-polymarket`
- `kimi-polymarket`

Validate with:

```bash
python3 tools/cron-jobs-tool.py validate
openclaw cron list
```

## Supporting reliability workflows

These are outside the four core cron jobs but are still part of the live runtime:

- `tools/health-check.sh` from system cron every 2 minutes for fast gateway death detection and watchdog handoff
- `tools/gateway-watchdog.sh` via launchd `com.grokclaw.gateway-watchdog` at `01,06,11,16,21,26,31,36,41,46,51,56` for bounded automatic gateway repair
- `tools/grokclaw-doctor.sh --check --quiet` via launchd `com.grokclaw.doctor` at `02,17,32,47` for workflow-health auditing
- `tools/pr-review-watch.sh` via launchd `com.grokclaw.pr-review-watch` to wake Grok when the PR review queue changes

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

# Kimi
OPENCLAW_AGENT_ID=kimi ./tools/run-openclaw-agent.sh

# Alpha
OPENCLAW_AGENT_ID=alpha ./tools/run-openclaw-agent.sh

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

The repo-managed `.githooks/pre-commit` hook runs `./tools/run-health-e2e-tests.sh` automatically before each commit.
