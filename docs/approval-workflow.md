# GrokClaw Approval Workflow

Daily suggestions no longer create Linear immediately. Ben now sees the drafted Linear ticket in Telegram before anything is created.

## Flow

1. Grok posts a daily suggestion with `tools/telegram-suggestion.sh`.
2. The suggestion state is stored in `data/pending-suggestion-N.json`.
3. Ben taps `Approve`.
4. `tools/dispatch-telegram-action.sh` handles `approve_suggestion:N` and runs `tools/approve-suggestion.sh`.
5. `tools/approve-suggestion.sh` calls `tools/linear-draft-approval.sh request ...`, which writes `data/pending-linear-draft-suggestion-N.json` and sends a second Telegram message showing the drafted Linear ticket with `Create Linear` and `Cancel` buttons.
6. If Ben taps `Create Linear`, `tools/dispatch-telegram-action.sh` handles `approve_linear_draft:suggestion-N` and runs `tools/linear-draft-approval.sh create suggestion-N`.
7. Only then does the system call `LINEAR_CREATION_FLOW=suggestion LINEAR_DRAFT_ID=suggestion-N tools/linear-ticket.sh ...`, post the Linear link to Telegram, and transition the issue to `In Progress`.

## Tools

| Tool | Purpose |
|------|---------|
| `tools/telegram-suggestion.sh` | Posts daily suggestions with the first-step Approve button and writes `data/pending-suggestion-N.json`. |
| `tools/approve-suggestion.sh` | Converts an approved suggestion into a Telegram reviewable Linear draft. |
| `tools/linear-draft-approval.sh` | Stores pending Linear drafts, sends draft approval buttons, creates the real Linear issue after approval, or cancels the draft. |
| `tools/dispatch-telegram-action.sh` | Handles `approve_suggestion:N`, `approve_linear_draft:<id>`, `reject_linear_draft:<id>`, `merge`, and `reject`. |

## Manual usage

### Suggestion draft request

```sh
tools/approve-suggestion.sh 8 "Test title" suggestions "Test description"
```

### Generic user-request draft approval

```sh
tools/linear-draft-approval.sh request user-req-123 user_request telegram-123 suggestions "Fix webhook retry issue" "Problem, acceptance criteria, implementation notes"
```

### Create the real Linear issue from an approved draft

```sh
tools/linear-draft-approval.sh create suggestion-8
```

## Dry-run

Validate the suggestion path without calling Telegram or Linear:

```sh
tools/approve-suggestion.sh --dry-run 8 "Test title" suggestions "Test description"
```

Or set `APPROVAL_DRY_RUN=1`.

## Smoke test

```sh
tools/approval-smoke.sh
```

This verifies that `approve-suggestion.sh --dry-run` prints the expected draft-approval sequence.

## Hard gate

`tools/linear-ticket.sh` now refuses to create a Linear issue unless all of these are true:

- `LINEAR_CREATION_FLOW` is set to `suggestion` or `user_request`
- `LINEAR_DRAFT_ID` is set
- `data/pending-linear-draft-<id>.json` exists
- the flow, reference ID, title, and description exactly match the approved pending draft

That makes the approved draft the final enforcement point, not just a caller convention.
