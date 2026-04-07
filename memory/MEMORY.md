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

- **2026-04-07** — Full OpenClaw setup audit and fixes: (1) Fixed cron drift — runtime had only 1 legacy job, repo had 3 correct jobs. Root cause: `sync-cron-jobs.sh` write was not surviving gateway restart. Fixed by updating `self-deploy.sh` to use `sync-cron-jobs.sh --restart` (already calls gateway-ctl restart internally), and hardening `cron-jobs-tool.py merge_runtime_fields` to preserve orphan old jobs. Manually synced 3 jobs to runtime. (2) OpenClaw already at v2026.4.5 (upgrade was done previously). `openclaw doctor --fix` shows no critical issues. (3) Rebuilt Alpha research loop — research files were empty (only section headers, no content), no self-improvement was happening. New alpha-polymarket prompt now requires 2-3 substantive sentences per research section, explicit self-correction analysis, whale+model probability blending, and actionable next questions. (4) Lowered MIN_VOLUME from $10k→$5k standard / $3k whale-backed (2+ traders) to capture more opportunities. (5) Added whale signal fields (whale_consensus_probability, whale_confidence, whale_traders, selection_source) to decision records for future analysis. Paperclip confirmed healthy. All `./tools/test-all.sh` tests pass.
- **2026-04-05** — Aligned the checked-in repo source of truth to the live 3-workflow runtime: removed stale Kimi cron jobs from `cron/jobs.json` and the core cron fixture, reduced workflow-health auditing and Paperclip gating to the active 3-workflow contract, and updated operator docs (`AGENTS.md`, `NorthStar.md`, `README.md`, `docs/multi-agent-setup.md`, `docs/agent-tasks.md`, `docs/gateway-health-check.md`, `docs/polymarket-paper-trading.md`) plus related tests to stop describing Kimi as an active scheduled worker. **Verify:** focused workflow suite (`python3 -m unittest ...` for prompts, workflow health, Paperclip lifecycle, cron-run-record, alert formatting), `python3 tools/cron-jobs-tool.py validate tests/fixtures/core-cron-jobs.json`, `git diff --check`.
- **2026-04-05** — Reconciled the local `main` checkout back to `origin/main` without losing local-only history (checkpointed on a backup branch first), audited the live `~/.openclaw` runtime against repo docs, and added `docs/system-architecture.md` as a diagrammatic map of the live system. Key drift found: runtime is currently on OpenClaw `2026.4.2`, runs 3 active OpenClaw cron workflows, uses Alpha on `openrouter/nvidia/nemotron-3-super-120b-a12b:free` with Grok fallback, and keeps Kimi as a placeholder shell that still inherits defaults if manually targeted.
- **2026-04-05** — Hardened OpenClaw workflow reliability: core cron prompts now write an early `started` record before long-running work, `cron-run-record.sh` supports `started` plus Paperclip-aware `audit-one --include-paperclip`, `_workflow_health.py` flags in-progress runs stuck past grace, `grokclaw-doctor.sh` validates the full workflow contract before declaring green, `run-openclaw-agent.sh` accepts timeout/retry env knobs, and Telegram posting now uses an explicit API timeout. Verified with `./tools/test-all.sh` including the reliability e2e smoke.

- **2026-04-02** — GRO-44: Alpha primary OpenRouter model and Kimi’s OpenRouter fallback (after Ollama) documented as `openrouter/qwen/qwen3.6-plus-preview:free` (Qwen3.6 Plus Preview free on OpenRouter). Updated `AGENTS.md`, `docs/multi-agent-setup.md`, `README.md`, and this file. Operators align `~/.openclaw/openclaw.json` with those ids; repo has no checked-in gateway JSON.
- **2026-04-02** — GRO-43: Workflow health research check no longer depends solely on file mtime. `_workflow_health.py` accepts the prompt-named markdown path derived from the latest cron record timestamp (slot/hour for OpenClaw research and hourly Polymarket jobs), with mtime glob scan as fallback—fixes false failures after git checkout or copies preserve old mtimes. PR #37; test `test_research_passes_when_expected_file_exists_despite_stale_mtime`.
- **2026-04-01** — `tests/test_polymarket_digest.py`: dry-run test now invokes `tools/polymarket-digest.sh` via repo root from `__file__` instead of a hardcoded Mac path so the suite passes in CI and other workspaces.
- **2026-04-01** — `.gitignore`: ignore `__pycache__/` and `*.py[cod]`; removed previously committed `tests/__pycache__` and `tools/__pycache__` bytecode from the repo.
- **2026-04-01** — GRO-42 workflow health: `cron-paperclip-lifecycle.sh start` now allows only the four core cron job names (blocks stray Paperclip issues from non-core jobs). `cron-run-record.sh` resolves `PAPERCLIP_ISSUE_UUID` from `.openclaw/<job>.issue` when the env var is unset so Paperclip issues still close if the agent omits exporting the variable. Added read-only `tools/_workflow_health_audit.py` and wired it into `grokclaw-doctor.sh` (no auto-repair; surfaces missing `data/cron-runs` evidence). Tests: `test_workflow_health_audit.py`, lifecycle non-core refusal, cron-run-record file fallback.
- **2026-04-01** — Split reliability checks into three verified layers: `tools/health-check.sh` now runs every 2 minutes as a fast detector that hands off to `tools/gateway-watchdog.sh`, `tools/gateway-watchdog.sh` now owns bounded automatic gateway repair, and `tools/grokclaw-doctor.sh` remains audit-only with schedule-aware grace windows for the 4 core workflows. Added launchd schedule files for explicit watchdog/doctor wall-clock timing, updated `NorthStar.md` + runtime docs to match, and verified the new model with end-to-end tests covering detector handoff, watchdog repair/failure, doctor dedupe, workflow latest-run enforcement, and launchd schedule wiring.
- **2026-04-01** — Synced the live OpenClaw runtime cron back to the North Star 4-workflow layout with `./tools/sync-cron-jobs.sh --restart`, created the missing evidence directories (`data/research/openclaw/`, `data/alpha/research/`, `data/kimi/research/`, `data/linear-creations/`, `data/audit-log/`), restored PR review intake with `.github/workflows/pr-review.yml`, and added `tools/pr-review-handler.sh` for `list`, `approve`, and `request-changes`.
- **2026-04-01** — Added a hard Linear creation gate on top of the Telegram draft flow. `tools/linear-ticket.sh` now refuses to create issues unless `LINEAR_CREATION_FLOW` and `LINEAR_DRAFT_ID` are set and the request exactly matches an approved `data/pending-linear-draft-*.json` record. This closes the bypass where direct script calls could still create Linear without Ben's explicit approval.
- **2026-04-01** — Aligned runtime and docs to `NorthStar.md`: `cron-run-record.sh` now posts Telegram health only on failures, skipped workflow runs close Paperclip issues as `cancelled`, daily suggestions now require a second Telegram approval of the drafted Linear ticket before real Linear creation, direct Telegram bug/feature intake can use `tools/linear-draft-approval.sh request ...`, and PR review now has a local launchd-ready watcher via `tools/pr-review-watch.sh`. Rewrote stale docs and removed obsolete `reliability-report`, `paperclip-sync`, and cron-scrutiny helper scripts.
- **2026-04-01** — Replaced the old 11-job cron layout with 4 core workflows: `grok-daily-brief`, `grok-openclaw-research`, `alpha-polymarket`, and `kimi-polymarket`. Added per-run Paperclip issue lifecycle tooling (`tools/cron-paperclip-lifecycle.sh`), upgraded `tools/cron-run-record.sh` to close Paperclip issues and post Telegram confirmations, added research output directories, and rewrote `cron/jobs.json` to the new schedules and prompts.
- **2026-04-01** — Added event-driven PR review intake with `.github/workflows/pr-review.yml` and `tools/pr-review-handler.sh`. PRs are now labeled for Grok review on GitHub first; Telegram merge/reject buttons are only sent after Grok has already approved the PR.
- **2026-04-01** — Added Linear creation flow enforcement and audit logging. `tools/linear-ticket.sh` now requires `LINEAR_CREATION_FLOW=suggestion|user_request`, writes creation records to `data/linear-creations/*.jsonl`, and `approve-suggestion.sh` now sets `LINEAR_CREATION_FLOW=suggestion`.
- **2026-04-01** — Fixed cron contract drift after OpenClaw scheduler jobs silently stopped running. Root cause: `cron/jobs.json` had been updated to `payload.kind: "agentTurn"` for the gateway, but repo tooling still only recognized legacy `agent_turn`. Updated `tools/cron-jobs-tool.py`, `tools/_cron_scrutiny_context.py`, `AGENTS.md`, `CURSOR.md`, `docs/multi-agent-setup.md`, `docs/agent-tasks.md`, and `docs/self-improvement-loop.md` so validation, scrutiny, and docs all match the live architecture again.
- **2026-03-19** — Created Linear GRO-28: verify Cursor cloud agent can post to Telegram when done. Delegated to Cursor; acceptance criteria: run `telegram-post.sh suggestions` and confirm message appears.
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
- **2026-03-19** — Wired Paperclip board to OpenClaw gateway: updated Grok agent from `picoclaw` to `openclaw_gateway` adapter, fixed duplicate dep in `server/package.json`, created `tools/paperclip-api.sh` helper and `tools/paperclip-sync.sh` sync tool, claimed API key, configured 6h heartbeat, added `paperclip-sync` cron job. Verified end-to-end: Paperclip creates issue → wakes Grok → Grok executes task → marks done. Created launchd service `com.grokclaw.paperclip.plist`.
- **2026-03-19** — Multi-agent setup: added Kimi (ollama/kimi-k2.5) and Alpha (openrouter/hunter-alpha) agents to `~/.openclaw/openclaw.json`. Configured Ollama provider. Added `tools/run-openclaw-agent-kimi.sh` and `OPENCLAW_AGENT_ID` support in `run-openclaw-agent.sh`. Routed polymarket-daily-trade, polymarket-daily-resolve, polymarket-weekly-digest, and reliability-report cron jobs to Kimi via `agentId`.
- **2026-03-19** — Hunter Alpha deprecated (replaced by paid MiMo-V2-Pro). Switched Alpha agent to `openrouter/arcee-ai/trinity-large-preview:free` (Trinity Large Preview, free, agentic). Kimi primary set to `ollama/kimi-k2.5:cloud` (verified working).
- **2026-03-19** — Added Alpha daily research cron job `alpha-daily-research` (07:30 daily): researches Known gaps, new free models, OpenClaw features, or agentic trends; reports to Grok via agent-report (no direct Telegram).
- **2026-03-19** — Alpha research priority order: (1) Polymarket discovery, (2) free models, (3) OpenClaw, (4) retry/reliability, (5) agentic tools. Created `docs/agent-tasks.md` with full task breakdown by agent.
- **2026-03-19** — Reporting chain: Kimi and Alpha report to Grok via `tools/agent-report.sh`; Grok runs `grok-daily-brief` (08:00) to synthesize and post to user. Reliability and Alpha research no longer post directly to Telegram. Polymarket keeps real-time posts + agent-report. Created `tools/agent-report.sh`, `tools/grok-daily-brief.sh`.
- **2026-03-19** — Fixed system crontab: health-check path updated from picoclaw to GrokClaw (`/Users/jarvis/Engineering/Projects/GrokClaw/tools/health-check.sh`). Log: `/tmp/openclaw-health.log`.
- **2026-03-21** — Paperclip launchd: versioned `launchd/com.grokclaw.paperclip.plist` + `tools/paperclip-ctl.sh` (`install` bootouts old job, copies plist, loads). Runs `pnpm --filter @paperclipai/server dev` (tsx) so workspace-linked `@paperclipai/*` resolves; `start`/`node dist` fails on TS exports. Loads parent `GrokClaw/.env`. Logs under `~/.openclaw/logs/paperclip-*.log`. Verified `http://127.0.0.1:3100/api/health`. AGENTS.md reliability section updated.
- **2026-03-21** — Cron Telegram silence fixed: OpenClaw maps `payload.deliver: false` + `channel`/`to` → `delivery.mode: none`, so isolated cron sent no completion messages. Migrated `cron/jobs.json` to job-level `delivery` (`announce` + telegram + `bestEffort` for user-facing jobs; `none` for reliability-report and alpha-daily-research). Added `tools/cron-jobs-tool.py` (validate + state-preserving sync), `tools/sync-cron-jobs.sh`, `self-deploy.sh` preflight validation, docs in `multi-agent-setup.md` / `CURSOR.md` / `AGENTS.md`, unittest hook. Synced to `~/.openclaw/cron/jobs.json` and restarted gateway.
- **2026-03-21** — Cron scrutiny pipeline: `tools/cron-run-record.sh` → `data/cron-runs/*.jsonl`; `tools/cron-scrutiny-context.sh` + `_cron_scrutiny_context.py` aggregate stats/tail; new OpenClaw job `grok-cron-scrutiny` (hourly :20) has Grok judge value vs hollow/missing data and post health-alerts (separate from pr-watch). All job prompts end with `cron-run-record`. Reliability + Alpha use `announce` + short health headline. Removed internal-only exception from `cron-jobs-tool.py`.
- **2026-03-30** — Major consistency hardening: (1) Fixed `.zshenv` pointing at stale OpenClawAgent config/tokens — was poisoning all CLI sessions with wrong `OPENCLAW_CONFIG_PATH` and `OPENCLAW_GATEWAY_TOKEN`. (2) Updated gateway v2026.3.13 → v2026.3.28 (fixed Telegram polling, LLM timeouts). (3) Started Ollama as persistent brew service (was down, killing all Kimi jobs). (4) Synced cron — 6/10 jobs had never fired; all 11 now loaded with valid schedules. (5) `self-deploy.sh` now runs `sync-cron-jobs.sh` after `git pull` so deploy auto-syncs cron. (6) Added `cron-jobs-tool.py strip` command + test to prevent scheduler state in git. (7) Built `tools/grokclaw-doctor.sh` — self-healing script that checks gateway, Paperclip, Ollama, Telegram, launchd, crontab, cron config, cron sync, and gateway auth; `--heal` auto-restarts downed services and re-syncs cron drift. (8) Wired doctor as `com.grokclaw.doctor` launchd agent (every 30min, `--heal --quiet`). (9) `health-check.sh` now calls doctor with `--heal` on gateway death. (10) Re-implemented `tools/changelog-check.sh` + `changelog-weekly-check` cron job (GRO-20 was in memory but script/job were missing from repo).

**2026-04-02** — grok-openclaw-research cron: Local OpenClaw v2026.3.28 (npm latest v2026.4.1), git 85d4807, status healthy. No major ecosystem changes; security warnings noted but no immediate action. No daily suggestion.

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
| 10 | Polymarket market discovery: evaluate 50 markets, better API/scoring | Pending approval |

**Next suggestion number: 11**

---

## Known gaps — backlog for future suggestions

Pick from this list when researching the next suggestion. Do not suggest anything already in "Completed work".

- **Polymarket market discovery (priority)** — Grok must research and propose a better way to discover profitable markets. Goal: evaluate ~50 markets per session instead of 5. No arbitrary limits. Be intelligent: research Polymarket API (filters, tag_id, category IDs, sorting), multi-page fetching, clustering/scoring by whale alignment + volume + edge potential, alternative data sources, and any other discovery strategies. Propose a concrete implementation.
- No retry logic on failed tool calls (linear-ticket.sh or create-pr.sh)
- Session summarization threshold may need tuning
- ~~OpenClaw changelog / release notes~~ — addressed: `tools/changelog-check.sh` + `changelog-weekly-check` cron job (re-implemented 2026-03-30)
- ~~Cron observability still depends on jobs reaching `tools/cron-run-record.sh`~~ — mitigated 2026-04-05 by writing an early `started` record before long-running workflow work, then validating final completion against Paperclip and audit evidence.

---

## System configuration

| Setting | Value |
|---------|-------|
| Runtime | OpenClaw v2026.4.2 |
| Grok model | `xai/grok-4-1-fast-non-reasoning` (alias: `grok-fast`) |
| Kimi model | placeholder shell only; no active scheduled work or dedicated model block |
| Alpha model | `openrouter/nvidia/nemotron-3-super-120b-a12b:free` with Grok fallback (requires `OPENROUTER_API_KEY`) |
| Workspace | `/Users/jarvis/Engineering/Projects/GrokClaw` |
| Config | `~/.openclaw/openclaw.json` |
| Cron jobs | 3 active OpenClaw cron jobs across 2 active agents (Grok, Alpha) plus Kimi placeholder shell; see `docs/system-architecture.md` |
| GitHub repo | `BenSheridanEdwards/GrokClaw` |
| Linear team | `GrokClaw` (`3f1b1054-07c6-4aad-a02c-89c78a43946b`) |
| Telegram group | `-1003831656556` (topics: suggestions=2, polymarket=3, health=4, pr-reviews=5) |
| Paperclip | `http://127.0.0.1:3100`, company `GrokClaw`, adapter `openclaw_gateway`, heartbeat 6h |

---

## Lessons learned

- **2026-03-18** — GRO-20: Implementation exceeded spec. Cursor agent completed in under 3 minutes from ticket creation. GitHub API approach for release monitoring is better than local runtime version checks — detects releases before upgrade. The approve-suggestion.sh script failed due to complex description quoting; manual fallback worked. Fix: improve shell quoting in approve-suggestion.sh for multi-paragraph descriptions.
- **2026-03-15** — GRO-17: Implementation matched spec. Clear acceptance criteria reduced back-and-forth.

---

## Polymarket calibration notes

- **2026-03-19** — Fixed gateway auth: added `gateway.remote.token` to ~/.openclaw/openclaw.json and `OPENCLAW_GATEWAY_TOKEN` to .env so `openclaw agent` can connect. polymarket-daily-turn.sh now loads .env and forces OPENCLAW_CONFIG_PATH for correct config.
- **2026-03-19** — Docs updated: approval-workflow.md (Tools table, telegram-suggestion usage), AGENTS.md (approve_suggestion action, Telegram behavior), CURSOR.md (tools list), README.md (suggestion flow), skills/linear/SKILL.md (button-based approval).
- **2026-03-19** — Daily suggestions now use telegram-suggestion.sh: posts with inline Approve button (plain text); writes data/pending-suggestion-N.json; dispatch-telegram-action.sh approve_suggestion:N runs approve-suggestion.sh and transitions to In Progress.
- **2026-03-19** — Polymarket: loop until bet placed — if SKIP, run polymarket-trade.sh again (skipped market excluded); iterate through whale-backed markets until trade or exhaust.
- **2026-03-19** — Polymarket: geopolitical + crypto only; whale top 5 traders; exclude already-evaluated markets (last 2 days). No sports/entertainment.
- **2026-03-19** — Polymarket runs every 4h (`0 */4 * * *`). Session learning via `polymarket-context.sh` (recent decisions/results). Bias toward trading; gates relaxed (MIN_EDGE 0.05, MIN_CONFIDENCE 0.55). Each session posts summary to Telegram polymarket topic.
- **2026-03-19** — No trades to analyze this week.
- **2026-03-15** — No trades to analyze this week.
- **2026-03-19** — Suggestion #10 (nightly reliability report) approved: Linear GRO-21 created, PR pending. tools/reliability-report.sh + 7am cron to health-alerts topic.
- **2026-03-19** — Implemented GRO-21: `tools/reliability-report.sh` collects gateway status, log error/retry count (last 10k lines per log file), and merged PRs in last 24h (via `gh pr list` CLI). Posts formatted report to Telegram health topic (4). Cron job `reliability-report` at 07:00 daily via cron/jobs.json. Smoke test: `./tools/reliability-report.sh --dry-run`.
- **2026-03-19** — PR #17 merged for GRO-21 (reliability report). tools/reliability-report.sh + cron active. Linear closed.
- **2026-03-20** — GRO-29: Browser automation. Added docs/browser-automation.md, config/browser-snippet.json, skills/browser-automation/SKILL.md, tools/browser-e2e-test.sh. Documented when to use browser tool in AGENTS.md (research >3 tabs, authenticated flows, UI automation). E2E test: fetch docs.openclaw.ai → snapshot → extract headings → post to Telegram. Run: ./tools/browser-e2e-test.sh. Requires browser enabled in ~/.openclaw/openclaw.json.
- **2026-03-20** — Ben approved browser automation feature (GRO-29). Linear → In Progress; Telegram status posted.
- **2026-03-21** — Ben feature idea: Sentient prediction market trading bot (Grok vs Claude). Created Linear ticket (GRO-??), delegated to Cursor.
- **2026-03-21** — Ben feature idea: Claude Code Graph Visualizer. Created Linear ticket (GRO-31), delegated to Cursor.
