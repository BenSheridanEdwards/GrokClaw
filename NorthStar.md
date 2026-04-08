# North Star

This document is the source of truth for what GrokClaw is being built to do.

If another doc, comment, or habit disagrees with this file, **this file wins**. Update the other artifact to match North Star, not the reverse.

It defines:

- the 3 core workflows
- the supporting reliability and health workflows
- how Paperclip is used
- how Telegram is used
- how suggestions and user requests become Linear issues that are assigned to Cursor Cloud Agents.

The goal is a system that is simple, inspectable, and operationally honest. Every important workflow should leave evidence. Every human-facing action should be traceable. Every agent should have a clear job.

## System Goal

GrokClaw is a multi-agent OpenClaw system with 3 configured agents:

- `Grok` is the coordinator, reviewer, and system operator (xai/grok)
- `Alpha` is the hourly Polymarket research and trading agent (NVIDIA primary → Grok fallback)
- `Kimi` is an empty reusable shell retained for future reassignment

Every agent has a fallback chain so jobs never silently die when a free-tier provider hits rate limits. The gateway falls through automatically; the doctor reports fallback activity once per day.

The system should do four things well:

1. Tell Ben what happened in the system and what needs attention.
2. Keep the deployment current with OpenClaw and ecosystem changes.
3. Run one reliable Polymarket research and trading loop every hour.
4. Leave a clean operational trail in Paperclip, cron logs, Telegram, and Linear.

## The 3 Core Workflows

These are the only OpenClaw cron workflows that matter.

### 1. Grok Daily System Brief

Agent: `Grok`  
Schedule: `08:00 UTC daily`

Purpose:

- Produce one clear view of the last 24 hours of GrokClaw.
- Explain what succeeded, what failed, what looks weak, and what should be improved next.

What it reads:

- Paperclip run issues from the last 24 hours
- `data/cron-runs/*.jsonl`
- `data/audit-log/*.jsonl` when present
- `data/linear-creations/*.jsonl`
- agent reports from Alpha
- health signals for gateway, Paperclip, Telegram, and Ollama

What it produces:

- a daily brief posted to Telegram suggestions
- optionally one high-leverage suggestion for approval
- a concise summary of every PaperClip Issue created, the workflow, what happened.
- one Paperclip issue per run for itself
- one cron run record for itself

What "good" looks like:

- Ben can read one message and understand the state of the system
- invalid Linear usage is called out
- hollow or noisy activity is not hidden behind vague summaries

### 2. Grok OpenClaw Research

Agent: `Grok`  
Schedule: `07:00`, `13:00`, `19:00 UTC daily`

Purpose:

- Keep GrokClaw aligned with the current OpenClaw ecosystem.

What it does:

- checks the latest stable OpenClaw version
- tracks new features, integrations, and notable community movement
- captures morning, afternoon, and evening research snapshots

What it produces:

- markdown research files in `data/research/openclaw/`
- a health-topic Telegram headline
- one Paperclip issue per run
- one cron run record

What "good" looks like:

- GrokClaw is not surprised by upstream OpenClaw changes
- useful ecosystem intelligence is saved, not lost in chat

### 3. Alpha Polymarket Research and Trading

Agent: `Alpha`  
Schedule: `hourly`

Purpose:

- Run an autonomous Polymarket research and trading loop with its own model perspective. It uses autoresearch to self-improve.

What it does:

- loads Polymarket context and memory
- researches profitable traders and market signals
- evaluates candidate markets
- validates with web research
- decides whether to trade or skip
- resolves pending paper trades when needed
- Produces a self-improvement report on how auto-research was used to be better next time.

What it produces:

- markdown research files in `data/alpha/research/`
- a Telegram summary in the polymarket topic
- an agent report to Grok
- one saved autoresearch report
- one Paperclip issue per run
- one cron run record

What "good" looks like:

- Alpha leaves behind a readable research trail
- every run has a concrete outcome: trade, skip, or failure with reason

## Supporting Reliability And Health Workflows

These are not part of the 3 core OpenClaw jobs, but they are required to keep the system alive and trustworthy.

### Health Check

Script: `tools/health-check.sh`  
Schedule: system cron, every 2 minutes

Purpose:

- detect gateway death or obvious runtime failure
- hand off gateway repair to `tools/gateway-watchdog.sh`
- alert Telegram health only if the watchdog handoff is unavailable
- never own restart policy or workflow auditing
- stay focused on infrastructure liveness, not workflow correctness

### GrokClaw Doctor

Script: `tools/grokclaw-doctor.sh`  
Schedule: launchd at `02,17,32,47`

Purpose:

- act as the missed-run and drift catch-all when event-driven checks could not fire
- verify the runtime environment stays trustworthy: gateway, Paperclip, Ollama, Telegram connectivity, launchd, crontab, cron validation, cron sync, and gateway auth
- detect when the 3 core workflows missed their expected schedule windows
- detect model fallbacks (rate limits, timeouts) and notify once per day
- escalate from missed-run detection into a full workflow audit when needed
- report failures to Telegram health immediately
- self-heal only low-risk infrastructure problems when explicitly running in repair mode
- turn meaningful workflow failures into approval-gated fix suggestions instead of repairing them automatically

### Gateway Watchdog

Script: `tools/gateway-watchdog.sh`
Schedule: launchd at `01,06,11,16,21,26,31,36,41,46,51,56`

Purpose:

- own bounded automatic gateway repair
- restart the gateway and refresh runtime dependencies when liveness fails
- avoid repair storms with lock/cooldown behavior
- alert Telegram health only after automatic repair is exhausted
- post a recovery notice if the gateway later returns after a reported watchdog failure

### Self Deploy

Script: `tools/self-deploy.sh`

Purpose:

- pull latest main
- sync cron configuration
- restart the gateway
- verify system health
- report deploy outcomes

This matters because merges are not enough. Merged code must actually become running code.

### Cron Validation

Script: `tools/cron-jobs-tool.py`

Purpose:

- validate that cron jobs use the correct OpenClaw shape
- validate Telegram delivery config
- keep runtime cron config in sync with repo state

## Workflow Health Contract

Workflow health is not just process health.

The question that matters is:

- did the workflow run when it was meant to
- did it produce the data, audit logs, and research it was meant to produce
- did it leave the expected Paperclip evidence

A core workflow run is only healthy when its full contract is satisfied.

The preferred architecture is:

- event-driven workflow validation at the end of each core run
- self-healing only for low-risk infrastructure failures
- doctor as the missed-run and drift catch-all
- approval-gated Linear remediation for workflow failures with code risk

### Per-Workflow Health Requirements

For each core workflow, GrokClaw should be able to verify the most recent expected run.

`grok-daily-brief`

- a recent `data/cron-runs/*.jsonl` record exists for the run
- the daily brief or suggestion was posted to Telegram suggestions
- the run created and closed a Paperclip issue
- the run was able to inspect the evidence it is responsible for summarizing, including `data/linear-creations/*.jsonl` and `data/audit-log/*.jsonl` when present

`grok-openclaw-research`

- a recent `data/cron-runs/*.jsonl` record exists for the run
- a markdown brief exists in `data/research/openclaw/`
- the health-topic Telegram headline was posted
- the run created and closed a Paperclip issue

`alpha-polymarket`

- a recent `data/cron-runs/*.jsonl` record exists for the run
- a markdown research file exists in `data/alpha/research/`
- a Telegram summary was posted to polymarket
- an agent report was written for Grok
- the run created and closed a Paperclip issue

### Workflow Health Outcomes

If any required evidence is missing, the workflow is not healthy.

That includes:

- the run did not happen on schedule
- the run happened but did not write the required artifacts
- the run happened but did not leave a cron run record
- the run happened but did not leave a Paperclip lifecycle
- the run touched the wrong Telegram surface or left no human-facing output

### Workflow Health Verification

This contract must stay executable, not just descriptive.

That means GrokClaw should keep:

- mocked happy-path and sad-path tests for each of the 3 core workflows
- tests that exercise the gateway detector, watchdog, and doctor separately
- a Husky pre-commit gate that runs `tools/test-all.sh` and blocks commits when shell checks, Python checks, unit tests, or end-to-end smoke fail

The verification stack should prove both:

- the core workflows are judged healthy when they leave the expected cron, research, audit, agent-report, and Paperclip evidence
- the health system reacts correctly when any required part of that contract is missing

The implementation path should prefer:

- job-scoped event-driven checks after `cron-run-record.sh`
- a lightweight missed-run detector inside the doctor
- escalation to the full workflow audit only when the quick path finds something wrong

### What Health Monitoring Should Do

When workflow health fails:

1. tell Ben clearly in Telegram health what failed and which evidence is missing
2. suggest a concrete fix (the exact command or the nature of the problem)
3. offer an inline "Rerun <workflow>" button so Ben can trigger the fix with one tap
4. send an approval-gated Linear draft for the fix in Telegram suggestions
5. wait for approval before any Linear ticket is created

Health alerts are deduped to once per day per failure set. The same missed workflow does not produce 30 alerts — it produces one, with a button.

Health monitoring should not silently repair workflow failures.

If a workflow breaks, the right next step is:

- an immediate, actionable Telegram health alert with a rerun button
- then an approval-gated Linear draft that can create a Linear ticket and delegate Cursor only after Ben approves it

### Linear For Workflow Failures

Workflow failures should not bypass the normal approval model.

That means:

- no automatic Linear ticket creation from health checks
- no automatic Cursor kickoff from the doctor
- fix work should enter Linear only through an approval-gated draft sent to Telegram suggestions

This preserves the main policy:

- Telegram tells Ben what failed now
- Linear only appears after explicit approval

## How Paperclip Is Used

Paperclip is the operational board for real work runs.

It is not noise storage. It should represent meaningful run lifecycles.

### Core Rule

Every core workflow run creates its own Paperclip issue.

Only the 3 core workflows are allowed to touch Paperclip.

That means:

- one run
- one Paperclip issue
- one lifecycle

Any non-core script or background check writing to Paperclip is a policy violation.

**Executable health check (how this rule is enforced):** `tools/_workflow_health.py` treats a non-core Paperclip issue as an **ongoing** policy breach only when the issue is **not** in a terminal state (`done`, `failed`, `cancelled`, and equivalent). Issues that are already closed still reflect historical mistakes or retired paths (for example legacy Kimi runs), but they must not keep the doctor red forever or drown out current misses. **Open** non-core issues still fail the audit and should be closed or remediated.

The issue should move through:

- `in_progress` when the run starts
- `done` when the run completes successfully
- `failed` when the run fails
- `cancelled` when the run is intentionally skipped

### Why Paperclip Exists

Paperclip gives Ben and Grok a clean way to inspect:

- what ran
- what happened
- what failed
- how runs evolved over time

It is the board for operational history, not just a generic task list.

### How The Lifecycle Works

Scheduled core runs are driven by **`tools/cron-core-workflow-run.sh`** (invoked by the thin OpenClaw cron message). The shell orchestrator — not the LLM — owns reliability:

- **Start:** `tools/cron-paperclip-lifecycle.sh start <job> <agent>` creates the Paperclip issue, returns the UUID, moves it to `in_progress`; the orchestrator writes `.openclaw/<job>.issue` and appends `started` via `tools/cron-run-record.sh`.
- **Work:** one `openclaw agent` turn using the work-only prompt in `docs/prompts/cron-work-<job>.md` (no lifecycle commands in that prompt).
- **End (always, including timeout/non-zero exit):** an `EXIT` trap runs terminal `tools/cron-run-record.sh` (`ok` or `error` with a fixed orchestrator summary / `CRON_ERROR_DETAILS`), which appends to `data/cron-runs/*.jsonl`, closes Paperclip via `tools/cron-paperclip-lifecycle.sh finish`, runs `audit-one`, and removes `.openclaw/<job>.issue`.

Manual debugging may still call `cron-paperclip-lifecycle.sh` / `cron-run-record.sh` directly; scheduled runs should go through the orchestrator.

### What Must Be Visible In Paperclip

For each run, Paperclip should make it easy to answer:

- which workflow ran
- which agent ran it
- whether it succeeded, skipped, or failed
- what the summary outcome was
- what the error details were if it failed

## How Telegram Is Used

Telegram is the human operating surface.

It is where Ben sees the outputs that matter.

### Topics

- `suggestions` — daily brief, suggestions, approval outcomes
- `polymarket` — Alpha trading summaries
- `health` — health confirmations, OpenClaw research headlines, failures, deploy results
- `pr-reviews` — PRs that Grok has already reviewed and approved on GitHub

### Telegram Principles

- keep messages concise and operational
- post after real work, not before
- do not force Ben to infer system state from vague wording
- outbound posts default to plain text — opt in to Markdown only when the body is safe
- messages containing $ amounts must use heredocs, `printf`, or `TELEGRAM_MESSAGE` to avoid shell expansion
- approval and merge actions must be deterministic and idempotent
- health failures should say exactly which workflow failed, what evidence is missing, and offer a rerun button

### Telegram Audit Trail

Telegram messaging should be fully auditable in both directions.

- outbound sends are logged to `data/audit-log/*.jsonl` as `telegram_post` / `telegram_inline`
- outbound delivery failures are also logged as `telegram_post_failed` / `telegram_inline_failed`
- inbound action messages are logged as `telegram_incoming`
- action dispatch remains idempotent, but duplicate inbound actions still appear in the audit trail

Operators should use:

- `tools/telegram-audit-report.sh`

to review recent Telegram activity and message quality flags, including the flagged bad message and a suggested "improve to" rewrite.

### Suggestions In Telegram

Grok can post a suggestion using:

- `tools/telegram-suggestion.sh`

That suggestion includes:

- the suggestion number
- the title
- the reasoning
- the impact
- the implementation description
- an Approve button

Workflow-health failures that need engineering work should use this same suggestion path.

The pending suggestion state is written to:

- `data/pending-suggestion-N.json`

### Telegram Action Handling

Button actions are processed by:

- `tools/dispatch-telegram-action.sh`

Important properties:

- duplicate actions are ignored safely
- failed suggestion approvals are not marked as complete
- Linear drafts must be explicitly approved before Linear is created
- merge actions trigger deployment after merge
- rerun buttons trigger the named cron workflow immediately on the correct agent

## How Suggestions Become Linear Work

Linear is intentionally constrained.

It should only be created in two flows:

1. Ben approves a daily suggestion.
2. Ben explicitly asks for a bug fix or feature in Telegram.

Anything outside those two flows is a process violation.

### Approved Suggestion Flow

1. Grok posts a suggestion to Telegram suggestions.
2. Ben taps Approve.
3. `tools/dispatch-telegram-action.sh` runs `tools/approve-suggestion.sh`.
4. `tools/approve-suggestion.sh` sends the drafted Linear ticket back to Telegram for review.
5. Ben taps `Create Linear` on that draft.
6. Only then is the real Linear ticket created.
7. The issue is delegated to Cursor.
8. Telegram gets the success message with the Linear link.
9. The issue is moved to `In Progress`.

The creation must use:

- `LINEAR_CREATION_FLOW=suggestion`

### Direct User Request Flow

When Ben asks for a bug fix or feature directly in Telegram:

1. Grok summarizes the request.
2. Grok writes the PM-quality ticket.
3. Grok sends the drafted Linear ticket to Telegram for approval.
4. Ben approves the draft.
5. Only then does Grok create the Linear issue.
6. The issue is delegated to Cursor.
7. Telegram gets the status update.

The creation must use:

- `LINEAR_CREATION_FLOW=user_request`

### Linear Logging

All Linear creations are logged to:

- `data/linear-creations/*.jsonl`

This log exists so the system can verify that Linear is only being created through the two approved flows.

The daily brief should check this log and flag any violations.

Workflow-health failures do not create an exception to this rule.

If GrokClaw detects a broken workflow and wants a Cursor cloud agent to fix it, that still begins as a suggestion requiring approval before Linear is created.

## How PR Review Works

PR review is event-driven, not cron-driven.

### Intake

- `.github/workflows/pr-review.yml` listens for PR events
- it adds `needs-grok-review`
- it writes a machine-readable review request comment

### Grok Review

Grok uses:

- `tools/pr-review-handler.sh list`
- `tools/pr-review-watch.sh`

Then chooses one of two paths:

- `approve` — approve on GitHub first, mark as Grok-approved, then notify Telegram `pr-reviews`
- `request-changes` — request changes on GitHub only, no Telegram ping

### Ben Merge Step

Ben should only see a PR in Telegram after:

- Grok has already reviewed it
- Grok has already approved it on GitHub

When Ben taps Merge:

- the PR is merged
- the Linear issue moves to `Done`
- `tools/self-deploy.sh` runs

## Evidence Model

The system should always leave evidence in four places:

1. Paperclip for per-run lifecycle visibility
2. `data/cron-runs/*.jsonl` for cron execution history
3. Telegram evidence in `data/audit-log/*.jsonl` (inbound + outbound) for human-facing operational output and auditability
4. `data/linear-creations/*.jsonl` for Linear creation policy enforcement

If a workflow cannot be seen in those places, it is not operationally complete.

If a workflow is missing expected research files, audit logs, or agent reports for its contract, it is also not operationally complete even if a process technically ran.

## Non-Goals

This document does not define:

- implementation details of every trading heuristic
- detailed OpenClaw prompt wording
- UI design details for Paperclip

It defines the operating model and the source-of-truth behavior.

## North Star Summary

GrokClaw should become a system where:

- the 3 core workflows are clear and stable
- every meaningful run is represented in Paperclip
- workflow health means complete evidence, not just a live process
- Telegram shows the right things to the right topic
- Linear only appears when work has actually been approved or explicitly requested
- broken workflows alert Telegram once with a one-tap rerun button, not 30 times
- Grok reviews before Ben is asked to merge
- health and reliability workflows keep the machine honest
- no free-tier outage silently kills a job — fallbacks and alerting always fire

That is the target state.
