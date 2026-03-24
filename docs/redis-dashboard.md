# Redis Dashboard

`tools/redis-dashboard.sh` collects Redis metrics (memory, keys, clients, uptime) and posts them to the Telegram health topic.

## How it works

- Uses `redis-cli` to query Redis INFO (server, memory, clients) and DBSIZE
- Builds a formatted report and posts via `tools/telegram-post.sh` to the health topic
- Skips gracefully if `redis-cli` is not installed or Redis is unreachable
- No LLM involved — pure shell

## Trigger

- **OpenClaw cron**: job `redis-dashboard` at 07:15 daily (`cron/jobs.json`)
- **Manual**: `./tools/redis-dashboard.sh` or `./tools/redis-dashboard.sh --dry-run`

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379` | Redis connection URL |
| `WORKSPACE_ROOT` | Derived from script path | Workspace root |
| `TELEGRAM_*` | From `.env` | Telegram credentials for posting |

## Prerequisites

- `redis-cli` installed and on PATH
- Redis server running (when using OpenClaw Redis skill, gateway auth, or cache)

## Usage

```sh
# Dry run — print report without posting
./tools/redis-dashboard.sh --dry-run

# Full run — post to Telegram health topic
./tools/redis-dashboard.sh
```

## Optional: system crontab

For Redis monitoring that runs even when the gateway is down, add to system crontab:

```sh
(crontab -l 2>/dev/null; echo "15 7 * * * REDIS_URL=redis://localhost:6379 /path/to/GrokClaw/tools/redis-dashboard.sh >> /tmp/redis-dashboard.log 2>&1") | crontab -
```

Replace `/path/to/GrokClaw` with the actual workspace path.
