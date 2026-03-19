# Long-term Memory

Grok must read this file in full before proposing any suggestion, and update it after every verified action.

---

## Completed work

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
- **2026-03-14** — Implemented GRO-14: `tools/health-check.sh` detects PicoClaw gateway death and alerts to Slack. Scheduled via cron/jobs.json, HEARTBEAT.md, and system cron; see `docs/gateway-health-check.md`.
- **2026-03-14** — Implemented the Polymarket paper-trading loop: staged candidate fetch, Grok decision engine with hard gates, skip/trade/result/bankroll ledgers, weekly digest/reporting, deterministic smoke test, stable PicoClaw cron jobs (`polymarket-daily-trade`, `polymarket-daily-resolve`, `polymarket-weekly-digest`), and manual fallback wrappers for direct runs. Verified with unit tests, `tools/polymarket-smoke.sh`, `tools/polymarket-daily-turn.sh`, and live `picoclaw cron list` output.
- **2026-03-14** — Populated `USER.md` with real profile data sourced from bensheridanedwards.co.uk: timezone (WIB UTC+7), role (Fractional CTO/AI Engineering Lead at CodeWalnut), stack (React/TypeScript/AI), communication preferences, and working style.
- **2026-03-15** — Implemented GRO-17: self-improvement loop for suggestion accuracy review. Added `tools/append-lesson-learned.sh`, updated AGENTS.md PR review workflow step 6, and `docs/self-improvement-loop.md`. Grok runs the script after approving a PR to append lessons-learned bullets to MEMORY.md.
- **2026-03-15** — Implemented GRO-18: `tools/approve-suggestion.sh` orchestrates full approval flow (Linear ticket → create PR → Slack reply). `tools/approval-smoke.sh` validates the flow in dry-run. Updated linear-ticket.sh, create-pr.sh, slack-post.sh to use PICOCLAW_WORKSPACE for portability. AGENTS.md and cron/jobs.json now use approve-suggestion.sh. See `docs/approval-workflow.md`.
- **2026-03-16** — Linear board management: created `tools/linear-transition.sh` + `tools/_linear_transition.py` so Grok can move issues between workflow states. Updated AGENTS.md with full issue lifecycle: `In Progress` on approval → `In Review` when Grok hands PR to Ben → `Done` only when PR is merged. Added merge reconciliation step. Cleaned up all stale issues (GRO-1–10, 12, 13, 15 canceled; GRO-17, 18 moved to Done). Linear is now the source of truth for issue status.
- **2026-03-18** — Suggestion #9 approved: PicoClaw changelog monitoring cron job. Linear GRO-20, PR #14. Script `tools/changelog-check.sh` + weekly cron `changelog-weekly-check` at 07:00 Mondays.
- **2026-03-19** — Migrated runtime from PicoClaw to OpenClaw v2026.3.13. Migrated comms from Slack to Telegram forum group with per-topic sessions (daily-suggestions, polymarket, health-alerts, pr-reviews). Updated all tools, cron jobs, AGENTS.md, and MEMORY.md. Created `tools/telegram-post.sh` + `tools/_telegram_post.py`. Created `tools/run-openclaw-agent.sh`.

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
| 4 | Add health check alerting if PicoClaw gateway dies | Approved → GRO-14, PR #5 |
| 5 | Populate USER.md with Ben's preferences | Cancelled — USER.md is a user action, not a Cursor ticket. Filled directly. |
| 6 | Add Polymarket paper trading agent for daily prediction and P&L tracking | Approved → GRO-16, PR #8 |
| 7 | Implement self-improvement loop for suggestion accuracy review | Approved → GRO-17 |
| 8 | Test approval workflow reliability | Approved → GRO-18 |
| 9 | Add PicoClaw changelog monitoring cron job | Approved → GRO-20, PR #14 |

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

- **2026-03-18** — GRO-20: Implementation exceeded spec. Cursor agent completed in under 3 minutes from ticket creation. GitHub API approach for release monitoring is better than local picoclaw version check — detects releases before upgrade. The approve-suggestion.sh script failed due to complex description quoting; manual fallback worked. Fix: improve shell quoting in approve-suggestion.sh for multi-paragraph descriptions.
- **2026-03-15** — GRO-17: Implementation matched spec. Clear acceptance criteria reduced back-and-forth.

---

## Polymarket calibration notes

- **2026-03-15** — No trades to analyze this week.
