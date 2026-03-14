# PicoClaw Gateway Health Check

The `tools/gateway-health-check.sh` script detects when the PicoClaw gateway process has died and posts an alert to the `grok-orchestrator` Slack channel.

## How it works

- **Detection**: Checks for a running `picoclaw` process; if none found, optionally probes `http://127.0.0.1:18800/` (gateway port from `config.json`).
- **Alerting**: Posts to Slack only when status *changes* from alive → dead (avoids repeated alerts).
- **State**: Uses `.gateway-health-state` in the workspace root to track previous status.

## Setup (system cron)

The health check must run via **system cron**, not PicoClaw's agent cron, because the agent depends on the gateway being up.

**This is already installed.** The following entry was added to the system crontab as part of this PR:

```
*/5 * * * * /Users/jarvis/.picoclaw/workspace/tools/gateway-health-check.sh >> /tmp/picoclaw-health.log 2>&1
```

Verify it is active:
```sh
crontab -l | grep gateway-health-check
```

Logs are written to `/tmp/picoclaw-health.log`.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PICOCLAW_WORKSPACE` | Derived from script path | Workspace root |
| `SLACK_CHANNEL_ID` | `C0ALE1S0LSF` | Slack channel for alerts |
