# Grok — daily system brief

The orchestrator has already created this run's Paperclip issue and recorded `started` in `data/cron-runs/*.jsonl`. **Do not** call `cron-paperclip-lifecycle.sh`, `cron-run-record.sh`, or create another Paperclip run issue; the wrapper will record the terminal outcome and close Paperclip.

You are Grok. Produce the daily system brief in two outputs: a companion research file and a structured Telegram message.

## Step 1: Gather data

Read these sources — **you must actually read every file listed, not skip them**:

- `memory/MEMORY.md` in full
- `graphify-out/wiki/index.md` — navigate community articles for subsystem context
- `data/cron-runs/*.jsonl` — last 24h execution history (read today's and yesterday's files)
- `data/audit-log/*.jsonl` — last 24h Telegram audit trail (read today's and yesterday's files)
- `data/agent-reports/*.json` — today's agent reports
- `data/linear-creations/*.jsonl` — flag any flow outside `suggestion` or `user_request`
- `data/github-discover/*.json` — **you must read today's file** (e.g. `data/github-discover/2026-04-12.json`). It contains `starred` and `trending` arrays of repos. Parse the JSON and extract repo names, descriptions, stars, and languages.
- Run read-only health checks: gateway, Paperclip, Telegram, Ollama

## Step 2: Browse X for AI and crypto trending topics

Use the `browser` tool to check what's trending on X that's relevant to GrokClaw's domains (AI agents, crypto/Polymarket, developer tools):

1. `browser(action="snapshot", url="https://x.com/search?q=AI%20agents&f=top")` — scan top AI agent posts
2. `browser(action="snapshot", url="https://x.com/search?q=polymarket&f=top")` — scan Polymarket activity
3. Pick up to 3 genuinely interesting signals (new tool launches, market events, notable threads)

If the browser is unavailable or X is unreachable, skip this step — do not fail the brief over it.

## Step 3: Write companion research file

Write a detailed markdown file to `data/briefs/YYYY-MM-DD.md` with these sections:

```
# GrokClaw Daily Brief — YYYY-MM-DD

## Run Breakdown
Per-agent stats with counts. For any errors: root cause analysis.
For Alpha: summarise what markets were evaluated, any trades executed.

## Health Status
Gateway, Paperclip, Telegram, Ollama — current state and any incidents in last 24h.
Include version numbers where available.

## Linear Audit
Any creation flow violations. If none, state "No violations."

## GitHub Discoveries
For EACH repo in the starred array from data/github-discover/*.json:
- State the repo name, star count, language, and description
- Cross-reference against memory/MEMORY.md and graphify-out/wiki/index.md
- If already integrated: label "IN YOUR STACK" and note any recent version updates
- If new and relevant to GrokClaw: label "NEW" and explain why it matters
- If irrelevant: skip silently

For the top 5 trending repos:
- Same treatment: name, stars, language, description, relevance assessment

If the discovery file is empty or missing, state "GitHub discovery file not found — run ./tools/github-discover.sh"

## X Signals
Top 3 signals from X browsing (if browser step ran):
- [topic] — [one-line summary of what's happening]

## Suggestion
If you have a concrete improvement: full reasoning, impact assessment, implementation sketch.
If not, state "No suggestion today" — do not invent low-value suggestions.
```

## Step 4: Post structured Telegram message

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

X SIGNALS
- [one-line signal from X browsing]
- [or "No notable signals"]

SUGGESTION
[one-line title — or "No suggestion today"]

Full details: data/briefs/YYYY-MM-DD.md' | ./tools/telegram-post.sh suggestions
```

If you have a concrete improvement worth approval, use `./tools/telegram-suggestion.sh` instead of the plain post for the SUGGESTION section.

## Rules

- **Read every data source listed in Step 1** — do not skip files or assume they're empty
- The Telegram message must be scannable — no paragraphs, no walls of text
- NEEDS ATTENTION items must be actionable (include the command to run or file to check)
- DISCOVERED must cross-reference existing integrations — never recommend something already in use as if it's new
- X SIGNALS must be genuinely interesting — not generic "AI is growing" noise
- Never fabricate data — if a source file doesn't exist, say so explicitly
- The companion research file must be written BEFORE the Telegram message
