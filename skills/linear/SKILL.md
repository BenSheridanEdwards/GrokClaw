---
name: linear
description: Create and update Linear issues for OpenClaw. Use when the user asks to create a Linear ticket, mentions OpenClaw's Linear skill, asks to file approved suggestions in Linear, or needs help with the project's Linear workflow.
---

# Linear Skill

Use the OpenClaw Linear workflow used by GrokClaw.

In the OpenClaw Telegram runtime, Linear creation is gated by Telegram draft approval. Use the local helpers from the workspace root.

## Core Workflow

1. If the request is an approved Grok suggestion, extract the suggestion number and title from the current thread context.
2. Send the draft first with `tools/approve-suggestion.sh` or `tools/linear-draft-approval.sh request ...`.
3. Only create the real issue after explicit approval, using `LINEAR_CREATION_FLOW=suggestion|user_request tools/linear-ticket.sh ...`.
4. Return or post the issue URL after creation.

## Approved Suggestion Workflow

When a user taps the Approve button on a daily Grok suggestion, `tools/dispatch-telegram-action.sh` runs `tools/approve-suggestion.sh`, which sends the drafted Linear ticket back to Telegram. The real Linear issue is only created after the follow-up `Create Linear` approval.

For manual ticket creation from an approved suggestion:

1. Do not implement the approved work directly.
2. Use `tools/approve-suggestion.sh <N> "<title>" suggestions "<description>"` to request the draft approval.
3. Only after approval, use `tools/linear-draft-approval.sh create suggestion-<N>` or `LINEAR_CREATION_FLOW=suggestion tools/linear-ticket.sh ...`.
4. Use the workspace default GrokClaw team unless the user explicitly requests a different team.
5. Delegate to Cursor agent via the script.

## Manual Ticket Creation

For direct requests like "create a Linear ticket for this":

1. Gather the minimum required fields: title and, when relevant, the target team.
2. For direct Telegram bug/feature intake, send the draft first with `tools/linear-draft-approval.sh request <draft-id> user_request <reference-id> suggestions "<title>" "<description>"`.
3. Only after approval should the real Linear issue be created.
4. Confirm the created issue by sharing the URL and any key identifier.

## Runtime Notes

- The helper script expects `LINEAR_API_KEY` in `.env`.
- `LINEAR_TEAM_ID` is optional because the GrokClaw team default is baked into the script.
- `LINEAR_ASSIGNEE_NAME` is optional.
- Prefer the absolute workspace helper paths when scripting the flow.
- Do not prepend `cd /Users/jarvis/Engineering/Projects/GrokClaw && ...`; use the tool `working_directory` instead.

## Failure Handling

If issue creation fails:

1. Explain exactly what is missing or what failed.
2. If `.env` is missing `LINEAR_API_KEY`, say that explicitly.
3. If the script returns a Linear API error, include the key error text.
