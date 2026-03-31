---
name: autoresearch-polymarket
description: AutoResearch-style Polymarket discovery — multi-page Gamma API fetch, evolved scoring (sim ROI backtest on resolved markets), external odds cross-checks via web_search. Use for alpha-daily-research topic (1), evolving discovery weights, or evaluating 50+ markets without the whale-only cap.
metadata:
  category: autoresearch
  security: stdlib Python only; HTTPS GET to gamma-api.polymarket.com; writes `data/autoresearch-polymarket-strategy.json` at runtime (gitignored; created by `evolve.py`)
  upstream_inspiration: https://github.com/aiming-lab/AutoResearchClaw (evolution methodology; this skill is a minimal domain fork)
---

# Autoresearch — Polymarket

## When to use

- Alpha (or any agent) is on **Polymarket market discovery** research.
- You need **paginated API discovery** beyond the whale-copy shortlist in `tools/_polymarket_trade.py`.
- You are running **dry evolution** (`evolve.py --dry`) or refreshing live weights.

## Security / sandbox

- **No subprocess, no extra pip packages** — stdlib only (`urllib`, `json`).
- Network: read-only JSON from `https://gamma-api.polymarket.com/markets`.
- Optional **browser/web_search** for external lines (e.g. Pinnacle) stays in the agent sandbox (`profile=openclaw`); scripts here do not launch browsers.

## Scripts

| Script | Purpose |
|--------|---------|
| `discovery.py` | Multi-page fetch, category filter (crypto + geopolitical keywords), scoring with `StrategyWeights`, candidate export. |
| `evolve.py` | Walk-forward **sim ROI** vs always-YES baseline on resolved binary markets; writes `data/autoresearch-polymarket-strategy.json`. |
| `alpha_context.py` | Prints a short markdown block for research notes using **current** evolved weights. |

```bash
python3 skills/autoresearch-polymarket/evolve.py --dry
python3 skills/autoresearch-polymarket/alpha_context.py
```

## Cron integration

- **`alpha-daily-research`**: When the chosen topic is Polymarket, run `./tools/autoresearch-polymarket-daily.sh` (evolve + Telegram), then `alpha_context.py`, then `web_search` for cross-venue checks as needed.
- OpenClaw audit: `openclaw security audit` (when CLI available) — expect **sandbox=full** compatible skill scripts (no shell-outs).

## Telegram format

Evolution posts to the **polymarket** topic:

`Evolved discovery: +X% backtest on Y markets`

(produced by `tools/autoresearch-polymarket-daily.sh` from `evolve.py` output).
