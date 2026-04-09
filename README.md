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

Approvals and merge decisions are action-button driven (single-poller mode), not free-text commands. Daily suggestions now use a two-step approval: first approve the suggestion, then approve the drafted Linear ticket before creation. See `docs/approval-workflow.md`.

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
- Telegram audit reporting: `tools/telegram-audit-report.sh`
- Self-deploy on merged main: `tools/self-deploy.sh`

## Polymarket Strategy

Hourly Alpha runs are bonding-first:
- market data from Polymarket APIs
- `copy_strategy` from known bonding wallets near resolution
- evaluation window targets near-certain entries in `95c-100c` (`97c-99c` still preferred when available)
- near-resolution candidate window is broadened to about `36h` for faster strategy evaluation
- at least one matching bonding wallet is sufficient (additional matching wallets increase confidence)
- bonding evaluation gates are loosened for sample collection (`min edge 0.5%`, `min confidence 0.45`, `min bonding volume 2000`, `max open exposure 8%`)
- if no valid bonding setup exists, the run records HOLD (no whale fallback)

Decision path:
- fetch/stage: `tools/polymarket-trade.sh`
- decide/skip: `tools/polymarket-decide.sh`
- resolve/results: `tools/polymarket-resolve-turn.sh`
- digest/reporting: `tools/polymarket-digest.sh`, `tools/polymarket-report.sh`

## Multi-Agent Setup

Grok (xAI) handles suggestions, daily brief, PR review, and Paperclip. Alpha uses the same Grok fast model for the hourly Polymarket workflow, with OpenRouter Nemotron 3 Super (free) as fallback if xAI is down. Kimi remains available as a placeholder shell for future reassignment, but has no active scheduled work. Alpha reports to Grok; Grok reports to you. See `docs/multi-agent-setup.md` and `docs/agent-tasks.md`.

## Key Agent Docs

- `AGENTS.md` - Grok operating instructions and multi-agent layout
- `CURSOR.md` - Cursor implementation contract
- `IDENTITY.md` - mission and operating stance
- `SOUL.md` - values
- `USER.md` - user profile and communication preferences
