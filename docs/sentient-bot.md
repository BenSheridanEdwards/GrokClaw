# Sentient Prediction Market Trading Bot (Model Arena)

This document describes the Sentient model-arena paper-trading bot for prediction markets (Grok vs Claude, etc.).

## Overview

- **Goal**: Trade when consensus predicts >5% probability shift within the time window.
- **Market source**: Manifold API (`api.manifold.markets`) — model-arena markets (Grok vs Claude, LMarena, etc.).
- **Mode**: Paper trading only (lab-only). No real-money trading.
- **Agent**: Kimi runs the trading loop; reports to Grok via `agent-report.sh`.

## Workflow

1. **sentient-daily-trade** — every 6h at :30 (e.g. 00:30, 06:30, 12:30, 18:30)
   - Fetch model-arena markets from Manifold (Grok vs Claude, LMarena, etc.).
   - Stage candidate, run web_search to validate.
   - Decide YES/NO/SKIP via `sentient-decide.sh`.
   - Bet if edge ≥5%, confidence ≥0.55.
   - Post to Telegram sentient topic, agent-report to Grok.

2. **sentient-daily-resolve** — daily at 23:15
   - Resolve paper trades against Manifold API.
   - Post summary to Telegram, agent-report.

## Tools

| Tool | Purpose |
|------|---------|
| `sentient-trade.sh` | Fetch and stage candidate, or log trade |
| `sentient-decide.sh` | Evaluate against risk gates (YES/NO/SKIP) |
| `sentient-resolve.sh` | Resolve trades against Manifold API |
| `sentient-report.sh` | Print P&L summary |
| `sentient-context.sh` | Load recent decisions/results for calibration |
| `sentient-daily-turn.sh` | Manual run (Kimi agent) |
| `sentient-smoke.sh` | Deterministic smoke test |

## Data files

- `data/sentient-trades.json` — trade ledger
- `data/sentient-results.json` — resolved outcomes
- `data/sentient-decisions.json` — all decisions (trade + skip)
- `data/sentient-skips.json` — skips
- `data/sentient-bankroll.json` — bankroll history
- `data/sentient-pending-trade.json` — staged candidate (ephemeral)

## Risk controls

- Paper trading only.
- Position sizing: fractional Kelly (0.25 × raw Kelly), max 2% per trade.
- Max open exposure: 10% of bankroll.
- Min edge: 5%.
- Min confidence: 0.55.

## Telegram

- Topic: `sentient` (defaults to polymarket topic if `TELEGRAM_TOPIC_SENTIENT` not set).
- Alerts: new trades, wins/losses, session summaries.

## Out of scope

- Real-money trading.
- Polymarket (separate loop).
- Sentient Protocol AGI (different product; we use Manifold for prediction markets).
