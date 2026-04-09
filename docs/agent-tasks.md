# Agent Tasks

All scheduled agent work is now organized around three core workflows.

## Core model

- Only the 3 core workflows are allowed to create Paperclip issues. **`tools/cron-core-workflow-run.sh`** calls `cron-paperclip-lifecycle.sh start` and **`tools/cron-run-record.sh`** for `started` and terminal lines — the LLM prompt files under `docs/prompts/cron-work-*.md` contain **work only** (no lifecycle).
- Every scheduled workflow run appends structured lines to `data/cron-runs/*.jsonl` via `cron-run-record.sh` (orchestrator-owned).
- Telegram outbound posts/inline messages and inbound action messages append audit records to `data/audit-log/*.jsonl`.
- Telegram health posts are failure-only; normal `ok` and `skipped` runs leave evidence in Paperclip and `data/cron-runs/*.jsonl`.
- Alpha still reports to Grok with `tools/agent-report.sh`.
- Linear is only created from approved daily suggestions or direct user-requested bug/feature intake.
- Gateway uptime is protected by a split health path: `tools/health-check.sh` detects quickly, `tools/gateway-watchdog.sh` repairs the gateway, and `tools/grokclaw-doctor.sh` acts as the missed-run/drift catch-all for workflow contracts.
- Workflow-health failures do not auto-repair. `tools/cron-run-record.sh` runs `tools/_workflow_health.py audit-one <job>` after each core workflow and passes the JSON into `tools/_workflow_health_handle.py`. The doctor runs `audit-quick` and escalates to the full `audit` plus the same handler only when the quick path finds a missed run, stale cron evidence, or an error run record.

## Shared workspace

All agents share `/Users/jarvis/Engineering/Projects/GrokClaw`.

Runtime outputs:

- `data/cron-runs/` — one JSONL file per UTC day for cron execution history
- `data/audit-log/` — Telegram output audit trail used for workflow-health checks
- `data/linear-creations/` — one JSONL file per UTC day for Linear creation audit
- `data/research/openclaw/` — Grok OpenClaw research markdown briefs
- `data/alpha/research/` — Alpha hourly Polymarket research markdown files
- `data/agent-reports/` — agent reports consumed by Grok daily brief

## The three workflows

### Grok

| Job | Schedule | Task |
|-----|----------|------|
| `grok-daily-brief` | 08:00 daily | Review the last 24h of Paperclip issues, cron logs, audit logs, health checks, and agent reports; summarize success/failure/fixes/improvements; flag invalid Linear creation flows; optionally post one approveable suggestion |
| `grok-openclaw-research` | 07:00, 13:00, 19:00 daily | Research latest stable OpenClaw version, new features, notable integrations, and ecosystem movement across X/GitHub/npm; save markdown brief and post headline to health |

### Alpha

| Job | Schedule | Task |
|-----|----------|------|
| `alpha-polymarket` | Hourly | Run bonding-first Polymarket research/trading: prioritize near-resolution bonding-copy candidates (evaluation range 95-100c, with 97-99c preferred), use an expanded near-resolution window (~36h) for higher sample throughput, allow single-wallet alignment with confidence uplift from broader alignment, HOLD when no valid bonding setup exists, then save markdown research, post to polymarket, and report to Grok |

## Paperclip lifecycle (orchestrator)

Each scheduled run is a distinct Paperclip issue lifecycle, owned by **`tools/cron-core-workflow-run.sh`**:

1. `cron-paperclip-lifecycle.sh start <job> <agent>` creates the issue and moves it to `in_progress`
2. Orchestrator writes `.openclaw/<job>.issue` and runs `cron-run-record.sh … started`
3. `openclaw agent` runs the body from `docs/prompts/cron-work-<job>.md` (must not call `cron-paperclip-lifecycle.sh` or `cron-run-record.sh`)
4. On **any** exit, a shell `trap` runs terminal `cron-run-record.sh` (`ok` if the agent exited 0, else `error` with `CRON_ERROR_DETAILS`). That closes Paperclip via `cron-paperclip-lifecycle.sh finish`, reads **`.openclaw/<job>.issue` first** then env for the UUID, runs `audit-one`, then removes the issue file
5. On errors, `CRON_ERROR_DETAILS` can add an extra Paperclip comment (via `cron-run-record.sh` when status is `error`)

OpenClaw **`cron/jobs.json`** payload is only the instruction to execute `./tools/cron-core-workflow-run.sh <job> <agent>` from the repo root.

Non-core jobs must not call `cron-paperclip-lifecycle.sh start`; the script rejects them.

## Workflow health auditing

- `tools/cron-run-record.sh` performs the first workflow-health check immediately after each core run with `tools/_workflow_health.py audit-one <job>`
- `tools/grokclaw-doctor.sh --check` is the catch-all. It runs `tools/_workflow_health.py audit-quick` to detect missed runs or stale cron evidence, then escalates into the full `audit` only when needed
- The full audit verifies cron evidence, required research files, required Telegram audit-log evidence, agent reports, and recent Paperclip lifecycle evidence
- `tools/_workflow_health_handle.py` owns Telegram health alerting, approval-gated draft creation, and failure dedup state
- If a core workflow fails that contract, the handler posts to Telegram health and requests a draft Linear fix ticket in suggestions for approval
- The doctor does not repair workflow failures automatically; it only self-heals low-risk infrastructure issues under `--heal`
- `tests/test_workflow_health.py` keeps mocked happy and sad path coverage for each of the 3 core workflows
- `tools/run-health-e2e-tests.sh` runs the health suite; Husky's pre-commit hook runs the full `tools/test-all.sh` gate

## PR review

PR review is no longer a cron workflow.

- `.github/workflows/pr-review.yml` marks PRs with `needs-grok-review` on `opened`, `ready_for_review`, and `synchronize`
- `tools/pr-review-watch.sh` runs locally every 5 minutes and wakes Grok only when the review queue changes
- `tools/pr-review-handler.sh list` shows queued PRs
- `tools/pr-review-handler.sh approve ...` approves on GitHub first, swaps labels, then posts Telegram merge/reject buttons
- `tools/pr-review-handler.sh request-changes ...` requests changes on GitHub and keeps Telegram quiet

## Topic routing

| Telegram topic | Agent(s) |
|----------------|----------|
| suggestions (2) | Grok daily brief and approveable suggestions |
| polymarket (3) | Alpha hourly trading/research summaries |
| health (4) | Grok OpenClaw research headlines, failures, and reliability anomalies |
| pr-reviews (5) | Grok after GitHub approval is complete |

## Manual runs

```bash
# Grok (default)
./tools/run-openclaw-agent.sh

# Alpha
OPENCLAW_AGENT_ID=alpha ./tools/run-openclaw-agent.sh

# Grok PR review queue watcher
./tools/pr-review-watch.sh
```
