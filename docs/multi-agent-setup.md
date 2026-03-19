# Multi-Agent Setup (Kimi + Hunter Alpha)

GrokClaw runs multiple OpenClaw agents on one gateway. Grok uses xAI; Kimi uses Ollama (local, free); Alpha uses OpenRouter (API, free tier).

## Prerequisites

### Kimi (Ollama)

1. Install [Ollama](https://ollama.ai) and ensure it is running.
2. Pull Kimi K2.5:

   ```bash
   ollama pull kimi-k2.5
   ```

3. Verify: `ollama list` should show `kimi-k2.5`.

### Hunter Alpha (OpenRouter)

1. Create an account at [OpenRouter](https://openrouter.ai).
2. Add your API key to `.env`:

   ```
   OPENROUTER_API_KEY=sk-or-...
   ```

3. Restart the gateway so it picks up the env: `./tools/gateway-ctl.sh restart`.

## Agent routing

| Agent | Model | Cron jobs |
|-------|-------|-----------|
| Grok | xai/grok-4-1-fast-non-reasoning | daily-grokclaw-suggestion, pr-watch, paperclip-sync |
| Kimi | ollama/kimi-k2.5 | polymarket-daily-trade, polymarket-daily-resolve, polymarket-weekly-digest, reliability-report |

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

OpenClaw persists cron jobs at `~/.openclaw/cron/jobs.json`. The workspace `cron/jobs.json` is the source of truth for version control. After editing `cron/jobs.json` in the repo:

1. Stop the gateway: `./tools/gateway-ctl.sh unload` (or ensure it is not running).
2. Copy or merge: `cp cron/jobs.json ~/.openclaw/cron/jobs.json`
3. Reload: `./tools/gateway-ctl.sh load`

Or use `openclaw cron add` / `openclaw cron edit` to manage jobs via CLI.

## Verification

```bash
# List agents
openclaw agents list --bindings

# List models (should include ollama/kimi-k2.5)
openclaw models list

# Test Kimi manually
openclaw agent --agent kimi --message "Hello, who are you?" --session-id test-kimi-1
```
