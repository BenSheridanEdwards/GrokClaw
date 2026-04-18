# Grok — daily system brief

The orchestrator has already created this run's Paperclip issue and recorded `started` in `data/cron-runs/*.jsonl`. **Do not** call `cron-paperclip-lifecycle.sh`, `cron-run-record.sh`, or create another Paperclip run issue; the wrapper will record the terminal outcome and close Paperclip.

You are Grok. Produce the daily system brief in two outputs: a companion research file and a structured Telegram message.

## Step 1: Gather data

Read these sources — **you must actually read every file listed, not skip them**:

- `memory/MEMORY.md` in full
- `graphify-out/wiki/index.md` — navigate community articles for subsystem context
- `data/cron-runs/*.jsonl` — last 24h execution history (read today's and yesterday's files)
- `data/audit-log/*.jsonl` — last 24h Telegram audit trail (read today's and yesterday's files). **You MUST grep for `"polymarket"` topic lines and parse every Alpha hourly message.** Each line contains the market evaluated and the rejection reason — extract all of them, don't summarize as "not in audit-log."
- `data/agent-reports/*.json` — today's agent reports
- `data/alpha/research/*.md` — read the latest 2-3 research files to understand what markets Alpha is evaluating, what candidates it found, and what the decision rationale was. This feeds the Run Breakdown section.
- `data/linear-creations/*.jsonl` — flag any flow outside `suggestion` or `user_request`
- Run read-only health checks: gateway, Paperclip, Telegram, Ollama

**Discovery data is delivered pre-rendered, not raw.** Do not parse `data/github-discover/*.json` yourself. Run:

```
./tools/_brief_discovery_render.py $(date -u +%Y-%m-%d)
```

The output is an authoritative markdown block listing every repo in today's discovery JSON with its verbatim description, stars, language, and a `[NEW]` / `[IN_STACK]` label already determined (and `SEEN_RECENTLY` if it appeared in a brief in the last 7 days). Paste that block into the GitHub Discoveries section of the research file and add analysis under each entry. **Do not add, remove, or rename repos from the block.**

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

For Alpha specifically — **you must actually extract this from the audit-log, not summarize as "not in audit-log"**:
- Read `data/audit-log/*.jsonl` for today and yesterday — search for lines with `topic: "polymarket"` and `kind: "telegram_post"`
- Each Alpha hourly run posts a line like `"Alpha · Hourly · HOLD — evaluated \"Will BTC...?\"; rejected: no copy signal (status=unavailable)."`
- Parse EVERY such line from the last 24h and extract: the market question, the rejection reason, the selection source
- Group by rejection reason: how many were "no copy signal", how many were "insufficient bonding wallets", how many were "gate check failed"?
- If Alpha has been in a HOLD streak (no trades for 24h+), flag this explicitly with the count
- Also read `data/alpha/research/*.md` for the latest 2-3 research files to see what markets Alpha is evaluating and what the decision rationale was
- If any trades were executed, detail the market, side, edge, and whether it resolved

For Grok: note what the previous brief covered and any suggestions that were made or accepted.

## Health Status
Gateway, Paperclip, Telegram, Ollama — current state and any incidents in last 24h.
Include version numbers. If an update is available, include the exact command to update.

## Linear Audit
Any creation flow violations. If none, state "No violations."

## GitHub Discoveries

Paste the full output of `./tools/_brief_discovery_render.py <date>` as a block under this heading, then add an analysis paragraph under each repo. The block is authoritative:

- **Do not add repos that are not in the block.** Every `owner/repo` in the final brief must appear in today's discovery JSON. A post-hoc validator (`tools/_brief_validator.py`) runs after the brief and will fail the workflow if any repo is not in the JSON.
- **Do not remove or rename repos from the block.** Analysis goes under each entry, the entry itself stays verbatim.
- **Do not change the `[NEW]` / `[IN_STACK]` / `SEEN_RECENTLY` labels.** They are computed by the render tool from the stack reference files.

Under each repo write a 3-6 sentence analysis paragraph:
- **For `[IN_STACK]`** — state exactly where it is used (file path + line reference), and name one concrete improvement or gap in that integration.
- **For `[NEW]`** — name the specific GrokClaw gap it fills, the file(s) it would touch, and whether it warrants a SUGGESTION entry. If there is no integration path, say "No integration path — skip."
- **For `[SEEN_RECENTLY]`** — one sentence is fine: refer back to the earlier brief and skip re-analysis unless something material changed.

**Do not paraphrase the `Description:` line from the render tool.** It is already the verbatim JSON description.

If the render tool prints `Discovery file not found` for today, run `./tools/github-discover.sh` and re-run the render tool. Do not proceed past this step without a discovery block.

## X Signals
Top 3 signals from X browsing (if browser step ran). For each:
- **Topic**: [what's happening]
- **Why it matters**: [relevance to GrokClaw]
- **Source**: [link or account if notable]

If browser was unavailable, state "Browser unavailable — skipped X browsing."

## Suggestion
Look at everything above. Is there ONE concrete improvement that would make GrokClaw meaningfully better?

**You MUST make a suggestion if any of these are true:**
- Gateway or any service is more than 1 version behind → suggest the update command
- Any CRITICAL security findings → suggest the specific remediation
- A NEW discovered repo has a clear, low-effort integration path → suggest it
- Alpha has been in a HOLD streak for 24+ hours → suggest parameter tuning or market diversification
- Any workflow has errors in the last 24h → suggest the fix

**"No suggestion today" is only acceptable when ALL systems are current, ALL services are healthy, ALL runs succeeded, AND no new discovery has a clear integration path.** The bar for silence is high — look harder before saying nothing.

Good suggestions:
- "Add lost-pixel visual regression to CI — catches Paperclip UI breaks after deploys"
- "Alpha evaluated 12 markets today but only looked at BTC — diversify to ETH/SOL near-resolution markets"
- "Gateway is 2 versions behind — update with: openclaw update"
- "amadeusprotocol/polymarket-trading-bot has a whale-tracking module that could replace our manual BONDING_TRADER_WALLETS list"

Bad suggestions (do not make these):
- Generic security improvements with no specific action
- "Add more tests" without identifying what's untested
- Suggestions that require major refactoring with unclear payoff

If you have a genuinely good suggestion, use `./tools/telegram-suggestion.sh <next-N> "<title>" "<reasoning>" "<impact>" "<description>"` to create an approvable suggestion.

If truly nothing rises to that bar, state "No suggestion today" — but this should be rare.
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
- [pull ONLY from entries labeled [NEW] by the render tool, excluding any [NEW · SEEN_RECENTLY] ones]
- [format: "owner/repo — one-line GrokClaw use case (Nk stars, starred|trending)"]
- [the description text must be grounded in the repo's JSON description — do not invent capabilities]
- [each entry MUST explain the specific GrokClaw connection — not just describe the repo]
- [PRIORITIZE: repos related to Polymarket/trading, OpenClaw/Claude Code ecosystem, agent memory, or multi-agent systems]
- [max 5 entries; prefer depth over count]
- [or "No new discoveries today" — valid when every [NEW] entry in the render block has no integration path]

X SIGNALS
- [one-line signal with substance, not hype]
- [or "Browser unavailable" / "No notable signals"]

SUGGESTION
[one-line actionable title — or "No suggestion today"]

Full details: data/briefs/YYYY-MM-DD.md' | ./tools/telegram-post.sh suggestions
```

If you have a suggestion worth approval, use `./tools/telegram-suggestion.sh` instead of the plain post.

## Step 5: Validate the brief

Before the Telegram post is considered final, run:

```
./tools/_brief_validator.py --date $(date -u +%Y-%m-%d)
```

Exit code 0 means the brief is hallucination-clean. Any other exit code means the research file mentions at least one `owner/repo` that is not in today's discovery JSON — fix the brief (remove the invented repo) and re-run the validator before posting.

## Rules

- **Read every data source listed in Step 1** — do not skip files or assume they're empty
- **NEEDS ATTENTION must be actionable** — include the exact command to run, file to check, or URL to visit. "openclaw update" alone is unacceptable; "Run: npm update openclaw (v2026.4.9 → v2026.4.11)" is correct.
- **DISCOVERED is driven by the render tool, not your memory.** The render tool is the single source of truth for which repos exist today. The Telegram DISCOVERED list is a filtered subset of the `[NEW]` entries in that block. Any `owner/repo` in your output that is not in today's `data/github-discover/*.json` is a hallucination and will fail validation.
- **X SIGNALS must have substance** — new tool launches, market events, or notable technical threads only. No engagement bait, no "AI is the future" takes.
- **Suggestions must be concrete** — include the command, file, or integration path. If you can't articulate the specific action, don't suggest it.
- The companion research file must be written BEFORE the Telegram message
- Never fabricate data — if a source file doesn't exist, say so explicitly
- The Telegram message is a summary. The research file is the depth. Both must be useful on their own.
