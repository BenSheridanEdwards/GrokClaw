# GrokClaw

GrokClaw is an OpenClaw-powered autonomous engineering operator.

Grok runs as PM + coordinator:
- researches and proposes one daily improvement
- creates PM-quality Linear tickets on approval
- delegates implementation to Cursor
- reviews PRs and coordinates merge decisions in Telegram
- maintains system reliability (health checks, watchdog, deploy loop)

## Core Integrations

- Telegram forum group (topic-based workflows)
- Linear (`GrokClaw` team)
- GitHub (`BenSheridanEdwards/GrokClaw`)
- OpenClaw gateway + cron

## Workflow Topics (Telegram)

- `suggestions` (topic 2): daily ideas and approvals
- `polymarket` (topic 3): trading loop and reports
- `health` (topic 4): incidents, watchdog, deploy alerts
- `pr-reviews` (topic 5): review summaries and merge actions

Approvals and merge decisions are action-button driven (single-poller mode), not free-text commands.

## Persistent Memory (Required)

Memory persistence is not optional.

- Canonical memory file: `memory/MEMORY.md`
- Runtime state files: `~/.openclaw/state/*`
- Agent must read `memory/MEMORY.md` before suggestions/research.
- After every verified action, append a dated bullet under `Completed work`.
- Never re-suggest anything listed under `Completed work`.
- Keep `Suggestion history`, `Known gaps`, and `System configuration` current.

If memory is stale, GrokClaw regresses and repeats work.

## Reliability Model

- Gateway process control: `tools/gateway-ctl.sh`
- Health probe and alerts: `tools/health-check.sh`
- Watchdog restart: `tools/gateway-watchdog.sh`
- Retry wrapper: `tools/retry.sh`
- Single-poller guard: `tools/telegram-poller-guard.sh`
- Safe action dispatch (idempotent): `tools/dispatch-telegram-action.sh`
- Self-deploy on merged main: `tools/self-deploy.sh`

## Polymarket Strategy

Daily loop stages one candidate with:
- market data from Polymarket API
- `copy_strategy` prior derived from top trader positions
- external validation via web research before final decision

Decision path:
- fetch/stage: `tools/polymarket-trade.sh`
- decide/skip: `tools/polymarket-decide.sh`
- resolve/results: `tools/polymarket-resolve-turn.sh`
- digest/reporting: `tools/polymarket-digest.sh`, `tools/polymarket-report.sh`

## Key Agent Docs

- `AGENTS.md` - Grok operating instructions
- `CURSOR.md` - Cursor implementation contract
- `IDENTITY.md` - mission and operating stance
- `SOUL.md` - values
- `USER.md` - user profile and communication preferences
