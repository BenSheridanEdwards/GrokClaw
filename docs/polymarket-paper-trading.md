# Polymarket Paper Trading Loop

This document describes the GrokClaw Polymarket paper-trading loop.

## Goal

Use Grok's reasoning to evaluate one Polymarket candidate per day, then enforce deterministic risk gates before recording a paper trade. The system starts with a fake bankroll of `$1000` and only flags for live trading after the promotion gate passes.

## Runtime jobs

The intended PicoClaw scheduler should contain these jobs:

- `polymarket-daily-trade` at `30 23 * * *`
- `polymarket-daily-resolve` at `45 23 * * *`
- `polymarket-weekly-digest` at `0 1 * * 1`

These jobs are also represented in `cron/jobs.json`.

Because the current PicoClaw gateway is reverting cron state back to the default single-job file, GrokClaw also installs resilient local system cron wrappers:

- `./tools/polymarket-daily-turn.sh`
- `./tools/polymarket-resolve.sh`
- `./tools/polymarket-digest.sh`

Install them with:

```sh
./tools/install-polymarket-cron.sh
```

This preserves the actual daily loop even while the internal PicoClaw cron persistence bug exists.

## Daily trade flow

1. `./tools/polymarket-trade.sh`
   Fetches the highest-volume market closing within 7 days and stages it.
2. Grok researches the market and chooses one of:
   - `./tools/polymarket-decide.sh YES <probability> <confidence> "<reasoning>"`
   - `./tools/polymarket-decide.sh NO <probability> <confidence> "<reasoning>"`
   - `./tools/polymarket-decide.sh SKIP "<reasoning>"`
3. The decision engine writes a structured decision record, then either:
   - appends a trade to `data/polymarket-trades.json`, or
   - appends a skip to `data/polymarket-skips.json`

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
  posts a weekly Slack digest and appends a calibration note to `memory/MEMORY.md`

## Promotion gate

Live trading is blocked unless all of these pass:

- bankroll `>= $100,000`
- at least `200` resolved trades
- positive expectancy over the last `100` resolved trades
- max drawdown `<= 25%`
- Brier score `<= 0.20`

The gate is advisory only. Grok should alert Ben in Slack for manual approval rather than going live automatically.

## Local verification

Deterministic smoke test:

```sh
./tools/polymarket-smoke.sh
```

Alias:

```sh
./tools/polymarket-dry-run.sh
```

Live cron installation:

```sh
./tools/install-polymarket-cron.sh
crontab -l | rg polymarket
```

Current verification also includes:

- `python3 -m unittest discover -s tests`
- `python3 -m py_compile ...`
- `sh -n tools/polymarket-*.sh`
