# PicoClaw Gateway Health Check

The `tools/gateway-health-check.sh` script detects when the PicoClaw gateway process has died and posts an alert to the `grok-orchestrator` Slack channel.

## How it works

- **Detection**: Checks for a running `picoclaw` process; if none found, optionally probes `http://127.0.0.1:18790/` (default gateway port).
- **Alerting**: Posts to Slack only when status *changes* from alive → dead (avoids repeated alerts).
- **State**: Uses `.gateway-health-state` in the workspace root to track previous status.

## Setup (system cron)

The health check must run via **system cron**, not PicoClaw's agent cron, because the agent depends on the gateway being up.

Add to crontab (`crontab -e`):

```
# PicoClaw gateway health check — every 5 minutes
*/5 * * * * /Users/jarvis/.picoclaw/workspace/tools/gateway-health-check.sh
```

Adjust the path if your workspace is elsewhere. Ensure `SLACK_BOT_TOKEN` is set in `.env` so alerts can be posted.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PICOCLAW_WORKSPACE` | Derived from script path | Workspace root |
| `SLACK_CHANNEL_ID` | `C0ALE1S0LSF` | Slack channel for alerts |
