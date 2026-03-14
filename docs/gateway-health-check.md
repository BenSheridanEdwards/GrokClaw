# GrokClaw Gateway Health Check

`tools/health-check.sh` monitors the PicoClaw gateway process and posts a Slack alert if it dies.

## How it works

- Checks for a running `picoclaw gateway` process
- Falls back to HTTP probe on `http://127.0.0.1:18800/health`
- Uses `.gateway-health-state` to track status — only alerts once on transition alive → dead, not on every check
- Exit 0 if healthy, exit 1 if not
- No LLM involved — pure shell

## Trigger: system crontab only

This runs via **system crontab**, not PicoClaw's agent cron or heartbeat. PicoClaw cron requires the gateway to be alive — it cannot detect its own death.

Current crontab entry (already installed):
```
*/5 * * * * /Users/jarvis/.picoclaw/workspace/tools/health-check.sh >> /tmp/picoclaw-health.log 2>&1
```

Verify:
```sh
crontab -l | grep health-check
```

Logs: `/tmp/picoclaw-health.log`

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PICOCLAW_WORKSPACE` | Derived from script path | Workspace root |
| `PICOCLAW_GATEWAY_PORT` | `18800` | Gateway HTTP port |
| `SLACK_CHANNEL_ID` | `C0ALE1S0LSF` | Slack channel for alerts |
