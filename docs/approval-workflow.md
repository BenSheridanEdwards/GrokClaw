# GrokClaw Approval Workflow

When Ben replies `approve` to a daily suggestion in Slack, Grok runs `tools/approve-suggestion.sh` to create a Linear ticket, scaffold a draft PR, and post both links to the thread.

## How it works

1. **Linear ticket** — Creates an issue in the GrokClaw workspace, delegates to the Cursor agent.
2. **Draft PR** — Creates `grok/GRO-XX` branch, pushes it, opens a draft PR linked to the Linear issue.
3. **Slack reply** — Posts both links to the original suggestion thread.

On any step failure, the script posts the error to the Slack thread and exits 1.

## Usage

```
tools/approve-suggestion.sh <N> "<title>" <thread_ts> [description]
```

- `N` — Suggestion number (e.g. 8)
- `title` — Suggestion title (quoted)
- `thread_ts` — Slack thread timestamp (e.g. `1234567890.123456`) from the suggestion message
- `description` — Optional PM-quality ticket body

## Dry-run

Validate the flow without calling Linear, GitHub, or Slack:

```
tools/approve-suggestion.sh --dry-run 8 "Test title" 1234567890.123456 "Test description"
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
| `PICOCLAW_WORKSPACE` | Derived from script path | Workspace root |
| `SLACK_CHANNEL_ID` | `C0ALE1S0LSF` | Slack channel |
| `APPROVAL_DRY_RUN` | `0` | If `1`, validate only, no API calls |

## Trigger

The approval workflow is triggered by Grok when the user replies `approve` in Slack. Documented in `AGENTS.md` and `cron/jobs.json` (daily suggestion job).
