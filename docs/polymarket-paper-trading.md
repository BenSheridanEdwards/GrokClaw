# Polymarket Workflow

`NorthStar.md` is the policy source of truth. This file documents the live Polymarket operating shape after the 3-workflow cleanup.

## Current runtime

The legacy three-job Polymarket schedule is retired.

The live system now runs one hourly workflow:

- `alpha-polymarket`

Alpha should:

1. research candidate markets and profitable traders
2. save markdown notes to their own research directory
3. decide whether to trade or skip based on current evidence and risk gates
4. post a concise operational summary to Telegram `polymarket`
5. report back to Grok for the daily brief

## Research outputs

- `data/alpha/research/`

These markdown files are part of the evidence trail and should explain what the agent saw, what it considered, and why it traded or skipped.

## Paperclip and cron evidence

Each hourly run should:

1. create a fresh Paperclip issue with `tools/cron-paperclip-lifecycle.sh start`
2. close it with `tools/cron-run-record.sh`
3. end as `done`, `failed`, or `cancelled` if the run is intentionally skipped

Normal runs should not spam Telegram health. Only failures belong there.

## Strategy

Alpha copies trades from three trusted professional wallets (Sharky6999, 033033033, ForesightOracle) on markets close to resolution. The logic: these traders provided early liquidity and have skin in the game, so their late-stage positions carry signal.

**Each hourly run:**

1. Fetches active markets sorted by volume, filters to those resolving within ~36 hours
2. Checks whether any of the three wallets hold positions on matching markets
3. If a candidate is found, evaluates it against risk gates:
   - Minimum edge: 0.5% over market odds
   - Minimum volume: $2,000
   - Position sized at 25% of Kelly fraction, capped at 1% of bankroll
   - Total open exposure capped at 8% of bankroll
4. If all gates pass → TRADE. If not → HOLD (no fallback to other strategies)
5. Logs the decision with full reasoning, resolves any prior trades, and feeds results back into memory

**Principles:**

- Skip when conviction is weak — forcing trades is worse than holding
- Write-ups must be grounded in observed data, not generic market commentary
- One matching wallet is enough to proceed, but more wallets raise confidence

## Verification

```sh
python3 -m unittest discover -s tests -q
python3 tools/cron-jobs-tool.py validate
```
