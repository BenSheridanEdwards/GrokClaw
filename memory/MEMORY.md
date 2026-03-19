# Long-term Memory

Grok must read this file in full before proposing any suggestion, and update it after every verified action.

## Memory operating contract

- This file is the canonical long-term memory for GrokClaw.
- Update it after every verified workflow action (suggestion, approval, PR review, deploy, reliability fix).
- Keep `Completed work`, `Suggestion history`, and `Known gaps` synchronized with reality.
- Never re-suggest anything already listed in `Completed work`.
- Runtime state files (idempotency, guards) live in `~/.openclaw/state`; this file stores durable human-readable context.

---

## Completed work

- **2026-03-19** — Hardened Telegram single-poller reliability: removed callback poller path, added `tools/telegram-poller-guard.sh`, integrated guard into `tools/health-check.sh`, and made `tools/dispatch-telegram-action.sh` idempotent via persisted token dedupe state.
- **2026-03-19** — Upgraded Polymarket selection to include top-trader copy strategy: `tools/_polymarket_trade.py` now builds `copy_strategy` from leaderboard + live positions and prefers trader-backed candidate selection with volume fallback.
- **2026-03-19** — Updated agent documentation set for OpenClaw + Telegram + persistent memory contract: `README.md`, `AGENTS.md`, `CURSOR.md`, `IDENTITY.md`, `USER.md`.
- **2026-03-14** — Created private GitHub repo `BenSheridanEdwards/GrokClaw` and pushed the full workspace as the initial commit.
- **2026-03-14** — Connected GitHub to the GrokClaw Linear workspace (`github` + `githubPersonal` integrations active). Commits referencing `GRO-XXX` auto-link to Linear tickets.
- **2026-03-14** — Verified Cursor agent exists in the GrokClaw Linear workspace (ID: `ca233eb8-8630-49c9-8f7c-3708c1bd1c4b`) and can be delegated tickets via `delegateId` on `IssueCreateInput`.
- **2026-03-14** — Upgraded `tools/linear-ticket.sh` to always set `delegateId` to Cursor on every new issue. Verified working.
- **2026-03-14** — Created `tools/create-pr.sh`: creates a `grok/<issue-id>` branch off main, pushes it, and opens a draft GitHub PR linked to the Linear issue. Verified working (produced PR #2).
- **2026-03-14** — Full approval flow confirmed working end-to-end: `approve` → Linear ticket (with Cursor delegated) → GitHub PR → Slack reply with both links.
- **2026-03-14** — Rewrote `AGENTS.md` and `IDENTITY.md` to fully document the system, integrations, and complete suggestion → approval → implementation → Slack report flow.
- **2026-03-14** — Created `tools/slack-post.sh` + `tools/_slack_post.py`: posts to Slack via API directly, works from any context. Fixed quoting bug that caused approval Slack posts to fail.
- **2026-03-14** — Suggestion #4 (health check alerting) approved: Linear GRO-14 created, PR #5 opened, Slack thread reply posted successfully.
- **2026-03-14** — Created `CURSOR.md` with full Cursor agent operating instructions (what to do when assigned, repo layout, coding standards, definition of done).
- **2026-03-14** — Rewrote `tools/linear-ticket.sh` + `tools/_linear_ticket.py`: now accepts a description arg so Grok can pass PM-quality ticket body.
- **2026-03-14** — Updated `tools/create-pr.sh`: PR body now contains implementation spec and explicit Cursor instructions.
- **2026-03-14** — Created `tools/review-pr.sh`: fetches PR details, changed files, and diff for Grok to review.
- **2026-03-14** — Rewrote `AGENTS.md`: added PM ticket writing standards, PR review workflow, and explicit instruction to never use the message tool.
- **2026-03-14** — Updated `cron/jobs.json` payload to include memory-read step and full three-step approval flow.
- **2026-03-14** — Implemented GRO-14: `tools/health-check.sh` detects gateway death and alerts. Scheduled via cron/jobs.json, HEARTBEAT.md, and system cron; see `docs/gateway-health-check.md`.
- **2026-03-14** — Implemented the Polymarket paper-trading loop: staged candidate fetch, Grok decision engine with hard gates, skip/trade/result/bankroll ledgers, weekly digest/reporting, deterministic smoke test, stable cron jobs (`polymarket-daily-trade`, `polymarket-daily-resolve`, `polymarket-weekly-digest`), and manual fallback wrappers for direct runs. Verified with unit tests, `tools/polymarket-smoke.sh`, `tools/polymarket-daily-turn.sh`, and live cron list output.
- **2026-03-14** — Populated `USER.md` with real profile data sourced from bensheridanedwards.co.uk: timezone (WIB UTC+7), role (Fractional CTO/AI Engineering Lead at CodeWalnut), stack (React/TypeScript/AI), communication preferences, and working style.
- **2026-03-15** — Implemented GRO-17: self-improvement loop for suggestion accuracy review. Added `tools/append-lesson-learned.sh`, updated AGENTS.md PR review workflow step 6, and `docs/self-improvement-loop.md`. Grok runs the script after approving a PR to append lessons-learned bullets to MEMORY.md.
- **2026-03-15** — Implemented GRO-18: `tools/approve-suggestion.sh` orchestrates full approval flow (Linear ticket → status reply). `tools/approval-smoke.sh` validates the flow in dry-run. Updated linear-ticket.sh and notification tooling for portable workspace-root usage. AGENTS.md and cron/jobs.json now use approve-suggestion.sh. See `docs/approval-workflow.md`.
- **2026-03-16** — Linear board management: created `tools/linear-transition.sh` + `tools/_linear_transition.py` so Grok can move issues between workflow states. Updated AGENTS.md with full issue lifecycle: `In Progress` on approval → `In Review` when Grok hands PR to Ben → `Done` only when PR is merged. Added merge reconciliation step. Cleaned up all stale issues (GRO-1–10, 12, 13, 15 canceled; GRO-17, 18 moved to Done). Linear is now the source of truth for issue status.
- **2026-03-18** — Suggestion #9 approved: runtime changelog monitoring cron job. Linear GRO-20, PR #14. Script `tools/changelog-check.sh` + weekly cron `changelog-weekly-check` at 07:00 Mondays.
- **2026-03-19** — Migrated runtime to OpenClaw v2026.3.13. Migrated comms from Slack to Telegram forum group with per-topic sessions (daily-suggestions, polymarket, health-alerts, pr-reviews). Updated all tools, cron jobs, AGENTS.md, and MEMORY.md. Created `tools/telegram-post.sh` + `tools/_telegram_post.py`. Created `tools/run-openclaw-agent.sh`.

---

## Active integrations

| Integration | Status | Key detail |
|-------------|--------|-----------|
| Telegram | ✅ Active | Forum group `-1003831656556`, topics: suggestions(2), polymarket(3), health(4), pr-reviews(5) |
| Linear | ✅ Active | GrokClaw team ID `3f1b1054-07c6-4aad-a02c-89c78a43946b`, API key in `.env` |
| GitHub | ✅ Active | Repo `BenSheridanEdwards/GrokClaw`, `gh` CLI as `BenSheridanEdwards` |
| Cursor agent | ✅ Active | Linear user ID `ca233eb8-8630-49c9-8f7c-3708c1bd1c4b`, assigned via `delegateId` |

---

## Suggestion history

| # | Title | Status |
|---|-------|--------|
| 1 | (unknown — pre-memory) | Unknown |
| 2 | Install and integrate Linear skill for automated ticket creation | Approved → GRO-8 |
| 3 | Slack thread reply parsing for automatic approval handling | Rejected (already partially handled by CLI trigger) |
| 4 | Add health check alerting if gateway dies | Approved → GRO-14, PR #5 |
| 5 | Populate USER.md with Ben's preferences | Cancelled — USER.md is a user action, not a Cursor ticket. Filled directly. |
| 6 | Add Polymarket paper trading agent for daily prediction and P&L tracking | Approved → GRO-16, PR #8 |
| 7 | Implement self-improvement loop for suggestion accuracy review | Approved → GRO-17 |
| 8 | Test approval workflow reliability | Approved → GRO-18 |
| 9 | Add runtime changelog monitoring cron job | Approved → GRO-20, PR #14 |

**Next suggestion number: 10**

---

## Known gaps — backlog for future suggestions

Pick from this list when researching the next suggestion. Do not suggest anything already in "Completed work".

- No retry logic on failed tool calls (linear-ticket.sh or create-pr.sh)
- Session summarization threshold may need tuning
- OpenClaw changelog / release notes not yet regularly checked — **being addressed by GRO-20**
- Old Slack tools (`slack-post.sh`, `_slack_post.py`) still in repo — can be removed once Telegram is confirmed stable

---

## System configuration

| Setting | Value |
|---------|-------|
| Runtime | OpenClaw v2026.3.13 |
| Model | `xai/grok-4-1-fast-non-reasoning` (alias: `grok-fast`) |
| Workspace | `/Users/jarvis/Engineering/Projects/GrokClaw` |
| Config | `~/.openclaw/openclaw.json` |
| Cron job | `daily-grokclaw-suggestion`, runs 06:00 daily, job ID `4978a69dab9ec327` |
| GitHub repo | `BenSheridanEdwards/GrokClaw` |
| Linear team | `GrokClaw` (`3f1b1054-07c6-4aad-a02c-89c78a43946b`) |
| Telegram group | `-1003831656556` (topics: suggestions=2, polymarket=3, health=4, pr-reviews=5) |

---

## Lessons learned

- **2026-03-18** — GRO-20: Implementation exceeded spec. Cursor agent completed in under 3 minutes from ticket creation. GitHub API approach for release monitoring is better than local runtime version checks — detects releases before upgrade. The approve-suggestion.sh script failed due to complex description quoting; manual fallback worked. Fix: improve shell quoting in approve-suggestion.sh for multi-paragraph descriptions.
- **2026-03-15** — GRO-17: Implementation matched spec. Clear acceptance criteria reduced back-and-forth.

---

## Polymarket calibration notes

- **2026-03-19** — No trades to analyze this week.
- **2026-03-15** — No trades to analyze this week.
- **2026-03-19** — Suggestion #10 (nightly reliability report) approved: Linear GRO-21 created, PR pending. tools/reliability-report.sh + 7am cron to health-alerts topic.
<<<<<<< HEAD
- **2026-03-19** — Implemented GRO-21: `tools/reliability-report.sh` collects gateway status, log error/retry count (last 10k lines per log file), and merged PRs in last 24h (via `gh pr list` CLI). Posts formatted report to Telegram health topic (4). Cron job `reliability-report` at 07:00 daily via cron/jobs.json. Smoke test: `./tools/reliability-report.sh --dry-run`.
- **2026-03-19** — PR #17 merged for GRO-21 (reliability report). tools/reliability-report.sh + cron active. Linear closed.

