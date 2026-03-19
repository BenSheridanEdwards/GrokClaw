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
| Grok | xai/grok-4-1-fast-non-reasoning | daily-grokclaw-suggestion, grok-daily-brief, pr-watch, paperclip-sync |
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

OpenClaw persists cron jobs at `~/.openclaw/cron/jobs.json`. The workspace `cron/jobs.json` is the source of truth for version control. After editing `cron/jobs.json` in the repo:

1. Copy: `cp cron/jobs.json ~/.openclaw/cron/jobs.json`
2. Restart gateway: `./tools/gateway-ctl.sh restart`

Or use `openclaw cron add` / `openclaw cron edit` to manage jobs via CLI.

## Verification

```bash
# List agents (use GrokClaw config)
OPENCLAW_CONFIG_PATH=~/.openclaw/openclaw.json openclaw agents list

# List models (should include ollama/kimi-k2.5:cloud)
openclaw models list

# Test Kimi manually
OPENCLAW_CONFIG_PATH=~/.openclaw/openclaw.json openclaw agent --agent kimi --message "Hello" --session-id test-kimi-1
```
