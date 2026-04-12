# Grok — daily system brief

The orchestrator has already created this run's Paperclip issue and recorded `started` in `data/cron-runs/*.jsonl`. **Do not** call `cron-paperclip-lifecycle.sh`, `cron-run-record.sh`, or create another Paperclip run issue; the wrapper will record the terminal outcome and close Paperclip.

You are Grok. Produce the daily system brief in two outputs: a companion research file and a structured Telegram message.

## Step 1: Gather data

Read these sources — **you must actually read every file listed, not skip them**:

- `memory/MEMORY.md` in full
- `graphify-out/wiki/index.md` — navigate community articles for subsystem context
- `data/cron-runs/*.jsonl` — last 24h execution history (read today's and yesterday's files)
- `data/audit-log/*.jsonl` — last 24h Telegram audit trail (read today's and yesterday's files). For Alpha HOLD messages, extract the market names and rejection reasons from the contextual messages.
- `data/agent-reports/*.json` — today's agent reports
- `data/linear-creations/*.jsonl` — flag any flow outside `suggestion` or `user_request`
- `data/github-discover/*.json` — **you must read today's file** (e.g. `data/github-discover/2026-04-12.json`). It contains `starred` and `trending` arrays of repos. Parse the JSON and extract every repo's `name`, `description`, `stars`, `language`, and `source` fields.
- Run read-only health checks: gateway, Paperclip, Telegram, Ollama

## Step 2: Browse X for AI and crypto trending topics

Use the `browser` tool to check what's trending on X that's relevant to GrokClaw's domains (AI agents, crypto/Polymarket, developer tools):

1. `browser(action="start")` — ensure browser is running
2. `browser(action="snapshot", url="https://x.com/search?q=AI%20agents&f=top")` — scan top AI agent posts from last 24h
3. `browser(action="snapshot", url="https://x.com/search?q=polymarket&f=top")` — scan Polymarket activity
4. Pick up to 3 genuinely interesting signals: new tool launches, market-moving events, notable threads with real substance. Ignore hype, engagement bait, and generic takes.

If the browser is unavailable or X is unreachable, state "Browser unavailable" in the X Signals section — do not fail the brief over it.

## Step 3: Write companion research file

Write a detailed markdown file to `data/briefs/YYYY-MM-DD.md`. **This must be substantive — not a skeleton.** Each section should have real analysis, not one-liners.

```
# GrokClaw Daily Brief — YYYY-MM-DD

## Run Breakdown
Per-agent run counts and success rates.

For Alpha specifically:
- List the markets that were evaluated (extract from audit-log HOLD messages)
- Note rejection reasons (e.g. "source=volume_fallback", "insufficient bonding wallets")
- If any trades were executed, detail the market, side, and outcome

For Grok: note what the brief covered and any suggestions made.

## Health Status
Gateway, Paperclip, Telegram, Ollama — current state and any incidents in last 24h.
Include version numbers. If an update is available, include the exact command to update.

## Linear Audit
Any creation flow violations. If none, state "No violations."

## GitHub Discoveries

### Starred (new repos Ben starred this week)
For EACH starred repo in data/github-discover/*.json:
- **[repo/name]** (N stars, Language) — [description]
  - Cross-ref: [IN YOUR STACK: used in X | NEW: relevant because Y | SKIP: not relevant]
  - If IN YOUR STACK: check for version updates or new features worth knowing about
  - If NEW and relevant: one sentence on how it could improve GrokClaw

### Trending (hot repos this week)
For the top 5 trending repos by stars:
- Same treatment as starred repos
- Filter aggressively: only include repos genuinely useful for multi-agent systems, crypto trading, or developer tooling

If the discovery file is empty or missing, state: "Discovery file not found — run ./tools/github-discover.sh"

## X Signals
Top 3 signals from X browsing (if browser step ran). For each:
- **Topic**: [what's happening]
- **Why it matters**: [relevance to GrokClaw]
- **Source**: [link or account if notable]

If browser was unavailable, state "Browser unavailable — skipped X browsing."

## Suggestion
Look at everything above. Is there ONE concrete improvement that would make GrokClaw meaningfully better?

Good suggestions:
- "Integrate karpathy/autoresearch for Alpha's market research pipeline — here's how..."
- "Alpha evaluated 12 markets today but only looked at BTC — diversify to ETH/SOL near-resolution markets"
- "Gateway is 2 versions behind — update with: npm update openclaw"

Bad suggestions (do not make these):
- Generic security improvements with no specific action
- "Add more tests" without identifying what's untested
- Suggestions that require major refactoring with unclear payoff

If you have a genuinely good suggestion, use `./tools/telegram-suggestion.sh <next-N> "<title>" "<reasoning>" "<impact>" "<description>"` to create an approvable suggestion.

If nothing rises to that bar, state "No suggestion today" — silence is better than noise.
```

## Step 4: Post structured Telegram message

Post to suggestions using this exact format. **Every line must have real data — no placeholders, no vague items.**

```
printf '%s\n' 'GROKCLAW DAILY BRIEF — YYYY-MM-DD

RUNS (24h)
Grok: N/N ok | Alpha: N/N ok (N markets evaluated, N trades)
Total: N runs, N% success

NEEDS ATTENTION
- [specific action: include the exact command, file path, or URL]
- [e.g. "Run: npm update openclaw (v2026.4.9 → v2026.4.11)"]
- [e.g. "Check: 5 CRITICAL items in tools/security-audit.sh output"]
- [or "Nothing — all systems healthy"]

DISCOVERED
- [only NEW repos — omit anything already integrated in GrokClaw]
- [repo] — [what it does and why YOU should care] (starred/trending)
- [e.g. "karpathy/autoresearch — autonomous research agents, could power Alpha market analysis (70k stars, starred)"]
- [max 5 entries, skip irrelevant repos and in-stack repos]
- [or "No new discoveries today"]

X SIGNALS
- [one-line signal with substance, not hype]
- [or "Browser unavailable" / "No notable signals"]

SUGGESTION
[one-line actionable title — or "No suggestion today"]

Full details: data/briefs/YYYY-MM-DD.md' | ./tools/telegram-post.sh suggestions
```

If you have a suggestion worth approval, use `./tools/telegram-suggestion.sh` instead of the plain post.

## Rules

- **Read every data source listed in Step 1** — do not skip files or assume they're empty
- **NEEDS ATTENTION must be actionable** — include the exact command to run, file to check, or URL to visit. "openclaw update" alone is unacceptable; "Run: npm update openclaw (v2026.4.9 → v2026.4.11)" is correct.
- **DISCOVERED is for NEW repos only** — the Telegram message must only list repos NOT already integrated in GrokClaw. Cross-reference against memory/MEMORY.md and graphify-out/wiki/index.md. If a repo is already in your stack (e.g. graphify, MemPalace), do NOT include it in the Telegram DISCOVERED section — it belongs in the research file only. The Telegram DISCOVERED section is for genuinely new finds that Ben hasn't seen before.
- **X SIGNALS must have substance** — new tool launches, market events, or notable technical threads only. No engagement bait, no "AI is the future" takes.
- **Suggestions must be concrete** — include the command, file, or integration path. If you can't articulate the specific action, don't suggest it.
- The companion research file must be written BEFORE the Telegram message
- Never fabricate data — if a source file doesn't exist, say so explicitly
- The Telegram message is a summary. The research file is the depth. Both must be useful on their own.
