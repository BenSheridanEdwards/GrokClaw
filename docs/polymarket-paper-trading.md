# Polymarket Paper Trading Loop

This document describes the GrokClaw Polymarket paper-trading loop.

## Goal

Use Kimi's reasoning to evaluate one Polymarket candidate per session (every 4h), then enforce deterministic risk gates before recording a paper trade. The system starts with a fake bankroll of `$1000` and only flags for live trading after the promotion gate passes.

## Runtime jobs

The intended OpenClaw scheduler should contain these jobs:

- `polymarket-daily-trade` at `0 */4 * * *` (every 4 hours)
- `polymarket-daily-resolve` at `45 23 * * *`
- `polymarket-weekly-digest` at `0 1 * * 1`

These jobs are also represented in `cron/jobs.json`.

Manual fallback wrappers exist if you ever need to trigger the loop outside OpenClaw cron:

- `./tools/polymarket-daily-turn.sh`
- `./tools/polymarket-resolve-turn.sh`
- `./tools/polymarket-digest.sh`

## Market selection

Only **geopolitical** and **crypto** markets are considered. Sports, entertainment, and other categories are excluded. Markets already evaluated (traded or skipped) in the last 2 days are excluded to avoid repeat evaluation.

Candidate selection focuses on **whale top traders** (leaderboard top 5). The system prefers markets where these traders have active positions, then falls back to highest-volume within 7 days.

## Trade flow (every 4 hours)

1. Kimi reads `memory/MEMORY.md` Polymarket section and runs `./tools/polymarket-context.sh` to load recent decisions and results for calibration.
2. **Loop until a bet is placed or options exhausted:**
   - `./tools/polymarket-trade.sh` fetches and stages the next candidate (whale-backed first, then volume fallback). If no candidate is returned, stop and post to Telegram.
   - Kimi researches the market and chooses one of:
     - `./tools/polymarket-decide.sh YES <probability> <confidence> "<reasoning>"`
     - `./tools/polymarket-decide.sh NO <probability> <confidence> "<reasoning>"`
     - `./tools/polymarket-decide.sh SKIP "<reasoning>"`
   - The decision engine writes a structured decision record, then either appends a trade to `data/polymarket-trades.json` or a skip to `data/polymarket-skips.json`.
   - If SKIP: the skipped market is excluded for the next run; go back to the previous step to fetch the next candidate. If trade: exit the loop.
3. Kimi posts a session summary to the polymarket Telegram topic via `./tools/telegram-post.sh polymarket "<what it did and why>"` and reports to Grok via `./tools/agent-report.sh kimi polymarket-daily-trade "<summary>"`

## Risk gates

Default gates:

- minimum expected edge: `6%`
- minimum confidence: `0.60`
- minimum market volume: `10,000`
- sizing: `min(0.25 Kelly, 2% bankroll)`
- maximum open exposure: `10% bankroll`

If any gate fails, the system records a skip instead of forcing a trade.

## Ledgers

All ledgers live under `data/` and are JSONL:

- `polymarket-decisions.json`
- `polymarket-trades.json`
- `polymarket-skips.json`
- `polymarket-results.json`
- `polymarket-bankroll.json`

## Resolution and reporting

- `./tools/polymarket-resolve.sh`
  resolves closed markets, calculates P&L in dollars, and updates the bankroll ledger
- `./tools/polymarket-report.sh`
  prints the current bankroll, expectancy, drawdown, calibration, and promotion gate state
- `./tools/polymarket-digest.sh`
  posts a weekly Telegram digest and appends a calibration note to `memory/MEMORY.md`

## Promotion gate

Live trading is blocked unless all of these pass:

- bankroll `>= $100,000`
- at least `200` resolved trades
- positive expectancy over the last `100` resolved trades
- max drawdown `<= 25%`
- Brier score `<= 0.20`

The gate is advisory only. The system alerts Ben in Telegram for manual approval rather than going live automatically.

## Local verification

Deterministic smoke test:

```sh
./tools/polymarket-smoke.sh
```

Alias:

```sh
./tools/polymarket-dry-run.sh
```

Current verification also includes:

- `python3 -m unittest discover -s tests`
- `python3 -m py_compile ...`
- `sh -n tools/polymarket-*.sh`
