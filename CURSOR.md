# Cursor Agent — Linear Ticket Instructions

When assigned a Linear ticket (e.g. GRO-XX), follow these steps:

## 1. Read this file

You're doing it. Proceed to the ticket.

## 2. Implement the feature

- Parse the ticket title and description for what to build
- Follow the codebase style and conventions
- Run and test your changes when helpful

## 3. Commit and push

- Commit with a message that references the issue: `GRO-XX: <description>`
- Push to the feature branch (e.g. `cursor/GRO-XX-...` or `grok/GRO-XX`)

## 4. Mark PR ready for review

- Use `gh pr ready` or the GitHub UI to mark the draft PR as ready for review

## 5. Post completion to Slack

```
tools/slack-post.sh C0ALE1S0LSF "🤖 GRO-XX complete. PR: <url>"
```

Use the workspace-relative path for the script (e.g. `tools/slack-post.sh` from repo root).

---

## Context

- **GrokClaw**: Grok suggests improvements; Cursor implements them.
- **Integrations**: Linear (tickets), GitHub (PRs), Slack (notifications).
- **Memory**: Grok maintains `memory/MEMORY.md`; Cursor does not update it.
