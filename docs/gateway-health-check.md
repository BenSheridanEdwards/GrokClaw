# GrokClaw Gateway Health Check

`tools/health-check.sh` monitors the OpenClaw gateway process and posts a Telegram alert if it dies.

## How it works

- Checks HTTP probe on `http://127.0.0.1:18800/health`
- Uses `.gateway-health-state` to track status — only alerts once on transition alive → dead, not on every check
- Runs `tools/telegram-poller-guard.sh` to detect and auto-fix Telegram poller conflicts
- Exit 0 if healthy, exit 1 if not
- No LLM involved — pure shell

## Trigger: system crontab only

This runs via **system crontab**, not agent cron or heartbeat. Agent cron requires the gateway to be alive — it cannot detect its own death.

Current crontab entry (already installed):
```
*/5 * * * * /Users/jarvis/Engineering/Projects/GrokClaw/tools/health-check.sh >> /tmp/openclaw-health.log 2>&1
```

Verify:
```sh
crontab -l | grep health-check
```

Logs: `/tmp/openclaw-health.log`

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WORKSPACE_ROOT` | Derived from script path | Workspace root |
| `OPENCLAW_GATEWAY_PORT` | `18800` | Gateway HTTP port |
| `TELEGRAM_GROUP_ID` | From `.env` | Telegram group ID for alerts |
