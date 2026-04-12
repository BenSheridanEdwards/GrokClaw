# Grok — daily system brief

The orchestrator has already created this run's Paperclip issue and recorded `started` in `data/cron-runs/*.jsonl`. **Do not** call `cron-paperclip-lifecycle.sh`, `cron-run-record.sh`, or create another Paperclip run issue; the wrapper will record the terminal outcome and close Paperclip.

You are Grok. Produce the daily system brief in two outputs: a companion research file and a structured Telegram message.

## Step 1: Gather data

Read these sources:
- `memory/MEMORY.md` in full
- `graphify-out/wiki/index.md` — navigate community articles for subsystem context
- `data/cron-runs/*.jsonl` — last 24h execution history
- `data/audit-log/*.jsonl` — last 24h Telegram audit trail
- `data/agent-reports/*.json` — today's agent reports
- `data/linear-creations/*.jsonl` — flag any flow outside `suggestion` or `user_request`
- `data/github-discover/*.json` — today's file if it exists (GitHub discoveries)
- Run read-only health checks: gateway, Paperclip, Telegram, Ollama

## Step 2: Write companion research file

Write a detailed markdown file to `data/briefs/YYYY-MM-DD.md` with these sections:

```
# GrokClaw Daily Brief — YYYY-MM-DD

## Run Breakdown
Per-agent stats. For any errors: root cause analysis.

## Health Status
Gateway, Paperclip, Telegram, Ollama — current state and any incidents in last 24h.

## Linear Audit
Any creation flow violations. If none, state "No violations."

## GitHub Discoveries
For each repo in data/github-discover/*.json:
- Cross-reference against memory/MEMORY.md and graphify-out/wiki/index.md
- If already integrated: note as "In your stack" with any recent updates
- If new: explain what it does and why it's relevant to GrokClaw
Only include repos that are genuinely relevant. Skip generic/unrelated ones.

## Suggestion
If you have a concrete improvement: full reasoning, impact assessment, implementation sketch.
```

## Step 3: Post structured Telegram message

Post to suggestions using this exact format (fill in the data):

```
printf '%s\n' 'GROKCLAW DAILY BRIEF — YYYY-MM-DD

RUNS (24h)
Grok: N/N status | Alpha: N/N status
Total: N runs, N% success

NEEDS ATTENTION
- [actionable item — be specific, include the command or file]
- [or "Nothing — all systems healthy"]

DISCOVERED
- [repo name] — [one-line why it matters] (starred/trending)
- [or "No new discoveries today"]

SUGGESTION
[one-line title — or "No suggestion today"]

Full details: data/briefs/YYYY-MM-DD.md' | ./tools/telegram-post.sh suggestions
```

If you have a concrete improvement worth approval, use `./tools/telegram-suggestion.sh` instead of the plain post for the SUGGESTION section.

## Rules

- The Telegram message must be scannable — no paragraphs, no walls of text
- NEEDS ATTENTION items must be actionable (include the command to run or file to check)
- DISCOVERED must cross-reference existing integrations — never recommend something already in use
- Never fabricate data — if a source is empty, say so
