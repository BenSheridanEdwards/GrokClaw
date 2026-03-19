# GrokClaw Approval Workflow

When Ben taps the Telegram **Approve** button on a daily suggestion, `tools/dispatch-telegram-action.sh` handles the `approve_suggestion:N` token: it reads `data/pending-suggestion-N.json`, runs `tools/approve-suggestion.sh` to create a Linear ticket, transitions the issue to In Progress, and posts the result to the suggestions topic.

## How it works

1. **Linear ticket** — Creates an issue in the GrokClaw workspace, delegates to the Cursor agent.
2. **Telegram update** — Posts status with the Linear link in the suggestions topic.

On any step failure, the script posts the error to Telegram and exits 1.

## Usage

```
tools/approve-suggestion.sh <N> "<title>" suggestions [description]
```

- `N` — Suggestion number (e.g. 8)
- `title` — Suggestion title (quoted)
- `suggestions` — target Telegram topic shortcut
- `description` — Optional PM-quality ticket body

## Dry-run

Validate the flow without calling Linear or Telegram:

```
tools/approve-suggestion.sh --dry-run 8 "Test title" suggestions "Test description"
```

Or set `APPROVAL_DRY_RUN=1`.

## Smoke test

Run the approval workflow smoke test:

```
tools/approval-smoke.sh
```

Verifies that `approve-suggestion.sh --dry-run` runs correctly and prints the expected step sequence. Does not hit external APIs.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WORKSPACE_ROOT` | Derived from script path | Workspace root |
| `APPROVAL_DRY_RUN` | `0` | If `1`, validate only, no API calls |

## Trigger

The approval workflow is triggered when Ben taps the Approve button on a daily suggestion. Grok posts suggestions using `tools/telegram-suggestion.sh`, which writes `data/pending-suggestion-N.json` and sends a message with an inline Approve button. When the button is tapped, the message `approve_suggestion:N` is sent; the poller forwards it to `tools/dispatch-telegram-action.sh`, which runs the approval flow.
