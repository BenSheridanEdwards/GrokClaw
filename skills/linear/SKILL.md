---
name: linear
description: Create and update Linear issues for OpenClaw. Use when the user asks to create a Linear ticket, mentions OpenClaw's Linear skill, asks to file approved suggestions in Linear, or needs help with the project's Linear workflow.
---

# Linear Skill

Use the OpenClaw Linear workflow used by GrokClaw.

In the OpenClaw Telegram runtime, prefer the local `./tools/linear-ticket.sh` helper from the workspace root. It loads credentials from `.env` and creates the Linear issue through Linear's GraphQL API.

## Core Workflow

1. If the request is an approved Grok suggestion, extract the suggestion number and title from the current thread context.
2. Prefer running `/Users/jarvis/Engineering/Projects/GrokClaw/tools/linear-ticket.sh "<number>" "<title>"` directly with the exec tool.
3. Return or post the issue URL after creation.

## Approved Suggestion Workflow

When a user taps the Approve button on a daily Grok suggestion, `tools/dispatch-telegram-action.sh` runs `tools/approve-suggestion.sh`, which creates the Linear issue via `linear-ticket.sh` and posts the result to Telegram. No manual intervention needed.

For manual ticket creation from an approved suggestion:

1. Do not implement the approved work directly.
2. Use `tools/approve-suggestion.sh <N> "<title>" suggestions "<description>"` or `tools/linear-ticket.sh` with the title format `Implement Grok Suggestion #N - <title>`.
3. Use the workspace default GrokClaw team unless the user explicitly requests a different team.
4. Delegate to Cursor agent via the script.

## Manual Ticket Creation

For direct requests like "create a Linear ticket for this":

1. Gather the minimum required fields: title and, when relevant, the target team.
2. If the request matches the Grok suggestion approval flow, prefer the helper script.
3. For other ticket requests, use the helper script when it fits or explain what additional implementation is needed.
4. Confirm the created issue by sharing the URL and any key identifier.

## Runtime Notes

- The helper script expects `LINEAR_API_KEY` in `.env`.
- `LINEAR_TEAM_ID` is optional because the GrokClaw team default is baked into the script.
- `LINEAR_ASSIGNEE_NAME` is optional.
- Prefer the absolute script path `/Users/jarvis/Engineering/Projects/GrokClaw/tools/linear-ticket.sh ...`.
- Do not prepend `cd /Users/jarvis/Engineering/Projects/GrokClaw && ...`; use the tool `working_directory` instead.

## Failure Handling

If issue creation fails:

1. Explain exactly what is missing or what failed.
2. If `.env` is missing `LINEAR_API_KEY`, say that explicitly.
3. If the script returns a Linear API error, include the key error text.
