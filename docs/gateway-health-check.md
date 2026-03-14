# PicoClaw Gateway Health Check

The `tools/health-check.sh` script detects when the PicoClaw gateway process has died and posts an alert to the `grok-orchestrator` Slack channel.

## How it works

- **Detection**: Checks for `picoclaw gateway` process and probes `http://127.0.0.1:18800/health` (configurable via `PICOCLAW_GATEWAY_PORT`).
- **Alerting**: Posts to Slack only when status *changes* from alive → dead (avoids repeated alerts).
- **State**: Uses `.gateway-health-state` in the workspace root to track previous status.
- **Exit**: 0 if healthy, 1 if unhealthy.

## Scheduling

**PicoClaw cron** (`cron/jobs.json`): Runs every 5 minutes when the gateway is up. The agent executes the script.

**HEARTBEAT** (`HEARTBEAT.md`): Includes the health check in periodic agent tasks (~every 30 min).

**System cron** (recommended for detecting gateway death): When the gateway is down, PicoClaw cron and HEARTBEAT cannot run. Add to crontab (`crontab -e`):

```
# PicoClaw gateway health check — every 5 minutes
*/5 * * * * /Users/jarvis/.picoclaw/workspace/tools/health-check.sh
```

Adjust the path if your workspace is elsewhere. Ensure `SLACK_BOT_TOKEN` is set in `.env` so alerts can be posted.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PICOCLAW_WORKSPACE` | Derived from script path | Workspace root |
| `PICOCLAW_GATEWAY_PORT` | `18800` | Gateway HTTP port |
| `SLACK_CHANNEL_ID` | `C0ALE1S0LSF` | Slack channel for alerts |
