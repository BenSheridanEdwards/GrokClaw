# GrokClaw HEARTBEAT

Periodic tasks run by the agent. Default interval: every 30 minutes.

## Tasks

- Run `./tools/health-check.sh`. If it exits non-zero, the script will have already alerted to Slack.
