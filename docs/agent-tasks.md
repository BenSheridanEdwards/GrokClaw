# Agent Tasks

All scheduled agent work is now organized around four core workflows.

## Core model

- Only the 4 core workflows are allowed to create Paperclip issues, and they do so with `tools/cron-paperclip-lifecycle.sh`.
- Every scheduled workflow run appends a structured line to `data/cron-runs/*.jsonl` via `tools/cron-run-record.sh`.
- Telegram posts and inline button messages append audit records to `data/audit-log/*.jsonl`.
- Telegram health posts are failure-only; normal `ok` and `skipped` runs leave evidence in Paperclip and `data/cron-runs/*.jsonl`.
- Kimi and Alpha still report to Grok with `tools/agent-report.sh`.
- Linear is only created from approved daily suggestions or direct user-requested bug/feature intake.
- Gateway uptime is protected by a split health path: `tools/health-check.sh` detects quickly, `tools/gateway-watchdog.sh` repairs the gateway, and `tools/grokclaw-doctor.sh` audits workflow contracts.
- Workflow-health failures do not auto-repair. `tools/grokclaw-doctor.sh` alerts Telegram health and sends an approval-gated Linear draft to suggestions when a core workflow misses its contract.

## Shared workspace

All agents share `/Users/jarvis/Engineering/Projects/GrokClaw`.

Runtime outputs:

- `data/cron-runs/` — one JSONL file per UTC day for cron execution history
- `data/audit-log/` — Telegram output audit trail used for workflow-health checks
- `data/linear-creations/` — one JSONL file per UTC day for Linear creation audit
- `data/research/openclaw/` — Grok OpenClaw research markdown briefs
- `data/alpha/research/` — Alpha hourly Polymarket research markdown files
- `data/kimi/research/` — Kimi hourly Polymarket research markdown files
- `data/agent-reports/` — agent reports consumed by Grok daily brief

## The four workflows

### Grok

| Job | Schedule | Task |
|-----|----------|------|
| `grok-daily-brief` | 08:00 daily | Review the last 24h of Paperclip issues, cron logs, audit logs, health checks, and agent reports; summarize success/failure/fixes/improvements; flag invalid Linear creation flows; optionally post one approveable suggestion |
| `grok-openclaw-research` | 07:00, 13:00, 19:00 daily | Research latest stable OpenClaw version, new features, notable integrations, and ecosystem movement across X/GitHub/npm; save markdown brief and post headline to health |

### Alpha

| Job | Schedule | Task |
|-----|----------|------|
| `alpha-polymarket` | Hourly | Autoresearch profitable traders and candidate markets, validate with web research, make trade/skip decisions, resolve pending paper trades when needed, save markdown research, post to polymarket, report to Grok |

### Kimi

| Job | Schedule | Task |
|-----|----------|------|
| `kimi-polymarket` | Hourly | Same workflow as Alpha but on Kimi for model diversity and broader market coverage; save markdown research, post to polymarket, report to Grok |

## Paperclip lifecycle

Each scheduled run is a distinct Paperclip issue lifecycle:

1. `tools/cron-paperclip-lifecycle.sh start <job> <agent>` creates the issue and moves it to `in_progress`
2. Each workflow prompt writes the returned issue UUID to `.openclaw/<job>.issue` immediately so the final record step can recover it safely
3. The agent performs the workflow
4. `PAPERCLIP_ISSUE_UUID=$(cat "$ISSUE_FILE") tools/cron-run-record.sh ...` records the result
5. `cron-run-record.sh` closes the Paperclip issue as `done`, `failed`, or `cancelled` for a skipped run
6. On errors, `CRON_ERROR_DETAILS` can add an extra Paperclip comment with failure context

Non-core jobs must not call `cron-paperclip-lifecycle.sh start`; the script now rejects them.

## Workflow health auditing

- `tools/grokclaw-doctor.sh --check` audits whether each core workflow ran within its expected window
- It uses schedule-aware grace windows so the doctor checks the latest expected run, not just any recent artifact inside a broad time window
- It verifies cron evidence, required research files, required Telegram audit-log evidence, agent reports, and recent Paperclip lifecycle evidence
- If a core workflow fails that contract, the doctor posts a Telegram health alert and sends a draft Linear fix ticket to suggestions for approval
- The doctor does not repair runtime drift or restart services automatically
- `tests/test_workflow_health.py` keeps mocked happy and sad path coverage for each of the 4 core workflows
- `tools/run-health-e2e-tests.sh` runs the health suite, and `.githooks/pre-commit` uses it as the commit gate

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
| polymarket (3) | Alpha and Kimi hourly trading/research summaries |
| health (4) | Grok OpenClaw research headlines, failures, and reliability anomalies |
| pr-reviews (5) | Grok after GitHub approval is complete |

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

# Grok PR review queue watcher
./tools/pr-review-watch.sh
```
