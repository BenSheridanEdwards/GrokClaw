# Agent Tasks

All scheduled tasks and which agent runs them.

## Reporting chain

Kimi and Alpha report to Grok; Grok reports to you (Ben).

- **Kimi** and **Alpha** write to `data/agent-reports/YYYY-MM-DD.json` via `agent-report.sh`
- **Grok** runs `grok-daily-brief` at 08:00, reads reports, synthesizes, posts to suggestions
- **All** scheduled jobs append a one-line record via `tools/cron-run-record.sh` → `data/cron-runs/*.jsonl` for **`grok-cron-scrutiny`** (hourly Telegram verdict on value vs hollow vs missing data)

Exception: Polymarket posts to Telegram in real time (trades are time-sensitive) and also reports to Grok.

## Workspaces

All agents share the same workspace (`/Users/jarvis/Engineering/Projects/GrokClaw`) so they can run shared tools. Agent-specific outputs go to `data/agent-reports/` (tagged by agent).

## Grok (default) — reports to you

| Job | Schedule | Task |
|-----|----------|------|
| daily-grokclaw-suggestion | 06:00 daily | Research one improvement from Known gaps, post to suggestions with Approve button |
| grok-daily-brief | 08:00 daily | Read agent reports, synthesize Kimi + Alpha into brief, post to suggestions |
| grok-cron-scrutiny | :20 every hour | Read cron run JSONL context; judge substance vs spin; post health-alerts scrutiny |
| pr-watch | Every 10 min | List ready PRs, review grok/* PRs, post review + merge/reject buttons, reconcile merged → Done, trigger self-deploy |
| paperclip-sync | Every 6h | Board sync, execute highest-priority todo issue, post summary to health-alerts |
| changelog-weekly-check | Monday 07:00 | Check for OpenClaw updates via GitHub/npm, post to health-alerts if update available |

## Kimi — reports to Grok

| Job | Schedule | Task |
|-----|----------|------|
| polymarket-daily-trade | Every 4h | Fetch candidate, web_search validate, decide YES/NO/SKIP, loop until bet or exhaust, post to polymarket + agent-report |
| polymarket-daily-resolve | 23:45 daily | Resolve paper trades, alert Telegram if promotion gate transitions, agent-report |
| polymarket-weekly-digest | 01:00 Monday | Weekly digest to Telegram, append to memory, agent-report |
| reliability-report | 07:00 daily | Gateway status, log errors, merged PRs → agent-report + health headline |

## Alpha — reports to Grok

| Job | Schedule | Task |
|-----|----------|------|
| alpha-daily-research | 07:30 daily | Research one topic (priority order), agent-report + health headline |

## Topic routing

| Telegram topic | Agent(s) |
|----------------|----------|
| suggestions (2) | Grok (daily brief, suggestions) |
| polymarket (3) | Kimi (real-time trades) |
| health (4) | Grok (`paperclip-sync`, `grok-cron-scrutiny`, deploy results), Kimi (`reliability-report`), Alpha (`alpha-daily-research`), changelog notices |
| pr-reviews (5) | Grok |

## Manual runs

```bash
# Grok (default)
./tools/run-openclaw-agent.sh

# Kimi
OPENCLAW_AGENT_ID=kimi ./tools/run-openclaw-agent.sh
# or
./tools/run-openclaw-agent-kimi.sh

# Alpha
OPENCLAW_AGENT_ID=alpha ./tools/run-openclaw-agent.sh
```
