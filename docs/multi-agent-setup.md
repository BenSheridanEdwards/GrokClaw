# Multi-Agent Setup (Kimi + Alpha)

GrokClaw runs multiple OpenClaw agents on one gateway. Grok uses xAI; Kimi uses Ollama cloud (free); Alpha uses OpenRouter (free tier).

## Prerequisites

### Kimi (Ollama cloud)

1. Install [Ollama](https://ollama.ai) and ensure it is running.
2. Sign in for cloud models: `ollama signin` (complete in browser).
3. Pull Kimi K2.5 cloud:

   ```bash
   ollama pull kimi-k2.5:cloud
   ```

4. Verify: `ollama list` should show `kimi-k2.5:cloud`.

### Alpha (OpenRouter free)

1. Create an account at [OpenRouter](https://openrouter.ai).
2. Add your API key to `.env`:

   ```
   OPENROUTER_API_KEY=sk-or-...
   ```

3. Alpha uses `arcee-ai/trinity-large-preview:free` — trained for agent harnesses like OpenClaw, $0/M tokens.
4. Restart the gateway so it picks up the env: `./tools/gateway-ctl.sh restart`.

## Agent routing

See `docs/agent-tasks.md` for the full task breakdown by agent.

| Agent | Model | Cron jobs |
|-------|-------|-----------|
| Grok | xai/grok-4-1-fast-non-reasoning | daily-grokclaw-suggestion, grok-daily-brief, grok-cron-scrutiny, pr-watch, paperclip-sync |
| Kimi | ollama/kimi-k2.5:cloud | polymarket-daily-trade, polymarket-daily-resolve, polymarket-weekly-digest, reliability-report |
| Alpha | openrouter/arcee-ai/trinity-large-preview:free | alpha-daily-research |

## Manual runs

```bash
# Grok (default)
./tools/run-openclaw-agent.sh

# Kimi
./tools/run-openclaw-agent-kimi.sh
# or
OPENCLAW_AGENT_ID=kimi ./tools/run-openclaw-agent.sh
```

## Cron job sync

OpenClaw persists cron jobs at `~/.openclaw/cron/jobs.json`. The workspace `cron/jobs.json` is the source of truth for version control.

### Telegram delivery (required)

OpenClaw maps legacy **`payload.deliver: false`** together with **`payload.channel` / `payload.to`** to **`delivery.mode: "none"`**, which disables completion announcements to Telegram. Isolated `agentTurn` jobs then produce **no** forum notification unless you fix delivery metadata.

Use **job-level** `delivery` (not inside `payload`):  
`"delivery": { "mode": "announce", "channel": "telegram", "to": "-1003831656556", "bestEffort": true }`

Use **`"payload": { "kind": "agentTurn", ... }`** for isolated scheduled agent turns. Older snake_case examples (`agent_turn`) are stale and can silently break runtime behavior or repo tooling.

### Cron scrutiny (structured log + Grok audit)

- Each scheduled job should end by appending one line:  
  `./tools/cron-run-record.sh <job_name> <grok|kimi|alpha> ok|error|skipped 'one-line factual outcome'`  
  Records go to `data/cron-runs/YYYY-MM-DD.jsonl` (gitignored).
- **`grok-cron-scrutiny`** (hourly) runs Grok on `./tools/cron-scrutiny-context.sh` output, judges value vs hollow spin vs missing data, and posts the verdict to **health-alerts**. This is separate from **pr-watch** (PR/deploy is its own flow; scrutiny only evaluates patterns in the log).

After editing `cron/jobs.json`:

1. Validate: `python3 tools/cron-jobs-tool.py validate`
2. Sync (merges scheduler `state` from the existing `~/.openclaw` file by job id): `./tools/sync-cron-jobs.sh --restart`

Or copy manually: `cp cron/jobs.json ~/.openclaw/cron/jobs.json` then `./tools/gateway-ctl.sh restart`.

`tools/self-deploy.sh` validates, pulls, syncs cron to runtime, then restarts the gateway. A bad config blocks deploy.

Or use `openclaw cron add` / `openclaw cron edit` to manage jobs via CLI.

**Important:** Never commit scheduler state (`state`, `createdAtMs`, `updatedAtMs`) to the repo. Strip before committing: `python3 tools/cron-jobs-tool.py strip`. Tests enforce this.

## Consistency checklist

Run after any infrastructure change:

- **After deploy:** `./tools/self-deploy.sh` handles cron sync + restart automatically.
- **After cron edit:** `python3 tools/cron-jobs-tool.py validate && ./tools/sync-cron-jobs.sh --restart`
- **After dependency change (Ollama, OpenRouter):** Document in prerequisites above, verify with `./tools/grokclaw-doctor.sh --check`
- **Full system check:** `./tools/grokclaw-doctor.sh --check` (read-only) or `--heal` (auto-fix); `./tools/grokclaw-doctor.sh --status` prints one machine-readable line (read-only)
- **Before committing cron:** `python3 tools/cron-jobs-tool.py strip` to remove scheduler state

## Self-healing

`tools/grokclaw-doctor.sh` runs every 30min via launchd (`com.grokclaw.doctor`) with `--heal --quiet`. It:

1. Checks gateway, Paperclip, Ollama health
2. Verifies Telegram connectivity
3. Confirms launchd agents and system crontab
4. Validates cron config and detects repo-vs-runtime drift
5. Tests gateway CLI auth

When `--heal` is set, it auto-restarts downed services and re-syncs cron drift. Failures that can't be auto-healed are posted to Telegram health-alerts.

Additionally, `tools/health-check.sh` (system crontab, every 5min) calls the doctor on gateway death.

## Verification

```bash
# Full system health check
./tools/grokclaw-doctor.sh --check

# One-line status (for scripts / dashboards)
./tools/grokclaw-doctor.sh --status

# List agents (use GrokClaw config)
openclaw agents list

# List loaded cron jobs
openclaw cron list

# List models (should include ollama/kimi-k2.5:cloud)
openclaw models list

# Test Kimi manually
openclaw agent --agent kimi --message "Hello" --session-id test-kimi-1
```
