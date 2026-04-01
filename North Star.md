# North Star

This document is the source of truth for what GrokClaw is being built to do.

It defines:

- the 4 core workflows
- the supporting reliability and health workflows
- how Paperclip is used
- how Telegram is used
- how suggestions and user requests become Linear work

The goal is a system that is simple, inspectable, and operationally honest. Every important workflow should leave evidence. Every human-facing action should be traceable. Every agent should have a clear job.

## System Goal

GrokClaw is a multi-agent OpenClaw system with 3 operating agents:

- `Grok` is the coordinator, reviewer, and system operator
- `Alpha` is an hourly Polymarket research and trading agent
- `Kimi` is an hourly Polymarket research and trading agent

The system should do four things well:

1. Tell Ben what happened in the system and what needs attention.
2. Keep the deployment current with OpenClaw and ecosystem changes.
3. Run two independent Polymarket research and trading loops every hour.
4. Leave a clean operational trail in Paperclip, cron logs, Telegram, and Linear.

## The 4 Core Workflows

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
- agent reports from Alpha and Kimi
- health signals for gateway, Paperclip, Telegram, and Ollama

What it produces:

- a daily brief posted to Telegram suggestions
- optionally one high-leverage suggestion for approval
- one Paperclip issue for that run
- one cron run record

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

- Run an autonomous Polymarket research and trading loop with its own model perspective.

What it does:

- loads Polymarket context and memory
- researches profitable traders and market signals
- evaluates candidate markets
- validates with web research
- decides whether to trade or skip
- resolves pending paper trades when needed

What it produces:

- markdown research files in `data/alpha/research/`
- a Telegram summary in the polymarket topic
- an agent report to Grok
- one Paperclip issue per run
- one cron run record

What "good" looks like:

- Alpha leaves behind a readable research trail
- every run has a concrete outcome: trade, skip, or failure with reason

### 4. Kimi Polymarket Research and Trading

Agent: `Kimi`  
Schedule: `hourly`

Purpose:

- Run the same Polymarket workflow as Alpha on a second model for diversity and broader market coverage.

What it does:

- follows the same loop: context, research, candidate evaluation, trade or skip, resolve, report

What it produces:

- markdown research files in `data/kimi/research/`
- a Telegram summary in the polymarket topic
- an agent report to Grok
- one Paperclip issue per run
- one cron run record

What "good" looks like:

- Kimi and Alpha are complementary, not redundant
- model diversity improves market coverage and research quality

## Supporting Reliability And Health Workflows

These are not part of the 4 core OpenClaw jobs, but they are required to keep the system alive and trustworthy.

### Health Check

Script: `tools/health-check.sh`  
Schedule: system cron, every 5 minutes

Purpose:

- detect gateway death or obvious runtime failure
- alert Telegram health when the system is down
- trigger self-healing through the doctor

### GrokClaw Doctor

Script: `tools/grokclaw-doctor.sh`  
Schedule: launchd, every 30 minutes

Purpose:

- check gateway, Paperclip, Ollama, Telegram, cron sync, launchd, and auth state
- heal known failures automatically when possible

### Gateway Watchdog

Script: `tools/gateway-watchdog.sh`

Purpose:

- extra guard around gateway uptime and recoverability

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

## How Paperclip Is Used

Paperclip is the operational board for real work runs.

It is not noise storage. It should represent meaningful run lifecycles.

### Core Rule

Every core workflow run creates its own Paperclip issue.

That means:

- one run
- one Paperclip issue
- one lifecycle

The issue should move through:

- `in_progress` when the run starts
- `done` when the run completes successfully
- `failed` when the run fails

### Why Paperclip Exists

Paperclip gives Ben and Grok a clean way to inspect:

- what ran
- what happened
- what failed
- how runs evolved over time

It is the board for operational history, not just a generic task list.

### How The Lifecycle Works

Start of run:

- `tools/cron-paperclip-lifecycle.sh start <job> <agent>`
- creates the Paperclip issue
- returns the issue UUID
- moves the issue to `in_progress`

End of run:

- `tools/cron-run-record.sh ...`
- appends a record to `data/cron-runs/*.jsonl`
- closes the Paperclip issue through `tools/cron-paperclip-lifecycle.sh finish`
- posts a one-line Telegram confirmation
- adds extra Paperclip error detail when `CRON_ERROR_DETAILS` exists

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
- `polymarket` — Alpha and Kimi trading summaries
- `health` — health confirmations, OpenClaw research headlines, failures, deploy results
- `pr-reviews` — PRs that Grok has already reviewed and approved on GitHub

### Telegram Principles

- keep messages concise and operational
- post after real work, not before
- do not force Ben to infer system state from vague wording
- approval and merge actions must be deterministic and idempotent

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
3. Telegram for human-facing operational output
4. `data/linear-creations/*.jsonl` for Linear creation policy enforcement

If a workflow cannot be seen in those places, it is not operationally complete.

## Non-Goals

This document does not define:

- implementation details of every trading heuristic
- detailed OpenClaw prompt wording
- UI design details for Paperclip

It defines the operating model and the source-of-truth behavior.

## North Star Summary

GrokClaw should become a system where:

- the 4 core workflows are clear and stable
- every meaningful run is represented in Paperclip
- Telegram shows the right things to the right topic
- Linear only appears when work has actually been approved or explicitly requested
- Grok reviews before Ben is asked to merge
- health and reliability workflows keep the machine honest

That is the target state.
