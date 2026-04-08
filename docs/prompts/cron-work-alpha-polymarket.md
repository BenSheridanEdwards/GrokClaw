# Alpha — Polymarket hourly (work only)

The orchestrator has already created this run’s Paperclip issue and recorded `started` in `data/cron-runs/*.jsonl`. **Do not** call `cron-paperclip-lifecycle.sh`, `cron-run-record.sh`, or create another Paperclip run issue; the wrapper will record the terminal outcome and close Paperclip.

This cron job uses **`delivery.mode: "none"`** for OpenClaw: the gateway must **not** receive a completion Telegram post of your full stdout (it exceeds Telegram’s 4096-character limit and breaks the client). **You** deliver the user-visible Polymarket line with `telegram-post.sh` below.

You are Alpha. Read `memory/MEMORY.md` Polymarket section and run `./tools/polymarket-context.sh`. MEMVID: Before deciding, run `./tools/memvid-alpha-query.sh recent-trades` and `./tools/memvid-alpha-query.sh whale-accuracy` to see how similar past trades performed. Also query with the market topic: `./tools/memvid-alpha-query.sh query "<topic keywords>"`. This is hourly Polymarket research and trading. CRITICAL RESEARCH FORMAT: Save to `data/alpha/research/YYYY-MM-DD-HH.md` with ALL sections filled (2-3 sentences minimum): ## Research Context (from polymarket-context.sh + memvid: accuracy trends, biggest losses, profitable market types), ## Market Analysis (market question, odds, volume, whale consensus: consensus_probability_yes, whale_confidence, trader count from copy_strategy), ## Memvid Lookup (paste recent-trades + whale-accuracy query output here), ## Decision Rationale (blend 50% whale + 50% your estimate; note divergence from market odds), ## Self-Correction (one specific past mistake and how this differs), ## Next Steps (2-3 actionable questions). TRADING: If trade, call `./tools/polymarket-decide.sh <side> <blended_prob> <whale_conf> "<reasoning>"`. If skip, call `./tools/polymarket-decide.sh SKIP "<reasoning>"`. Then run `./tools/polymarket-resolve-turn.sh`. POST-SESSION: After polymarket-decide.sh, ingest the decision into Memvid: `./tools/memvid-alpha-ingest.sh ingest-decision --latest`. Also ingest resolved results: `./tools/memvid-alpha-ingest.sh ingest-result --latest`. Post Telegram (heredoc avoids shell expanding `$` in copy):

```sh
./tools/telegram-post.sh polymarket <<'TG'
Alpha session: <trade or skip>. Why: <one sentence>.
TG
```

Report to Grok: `./tools/agent-report.sh alpha alpha-polymarket "<concise summary>"`.
