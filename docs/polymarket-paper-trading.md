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

## Strategy notes

The core research and risk posture still applies:

- prefer markets backed by strong evidence and notable trader behavior
- skip when conviction is weak instead of forcing trades
- keep the write-up grounded in observed data, not generic market commentary

## Verification

```sh
python3 -m unittest discover -s tests -q
python3 tools/cron-jobs-tool.py validate
```
