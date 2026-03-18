# PicoClaw / OpenClaw Changelog Monitoring

`tools/changelog-check.sh` monitors GitHub releases for PicoClaw (sipeed/picoclaw) and OpenClaw (openclaw/openclaw). When new releases are detected, it posts a summary to Slack.

## How it works

- Fetches latest release from each repo via GitHub API
- Compares with last-seen versions in `.changelog-check-state`
- Posts to Slack only when a new release is detected (no spam on repeated runs)
- First run: records current versions, no alert
- Uses Python for robust JSON parsing (handles control chars in release bodies)

## Trigger: PicoClaw cron

Scheduled in `cron/jobs.json` as `picoclaw-changelog-check`:

- **Schedule**: Sunday 07:00 (`0 7 * * 0`)
- **Payload**: Agent runs the script; script handles fetch, compare, and Slack post

## Alternative: system crontab

For a fully non-LLM path (no agent invocation), add to system crontab:

```
0 7 * * 0 /path/to/workspace/tools/changelog-check.sh >> /tmp/changelog-check.log 2>&1
```

Replace `/path/to/workspace` with `$PICOCLAW_WORKSPACE` or the actual workspace path.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PICOCLAW_WORKSPACE` | Derived from script path | Workspace root |
| `SLACK_CHANNEL_ID` | `C0ALE1S0LSF` | Slack channel for alerts |

## State file

`.changelog-check-state` stores last-seen versions:

```
picoclaw_tag=v0.2.3
openclaw_tag=v2026.3.13-1
```

Delete this file to reset (next run will treat as first run, no alert).
