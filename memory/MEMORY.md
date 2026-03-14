# Long-term Memory

This file stores important facts that must persist across sessions.
Grok must read this before proposing suggestions, and update it after every verified action.

## Completed work

- **2026-03-14** — Created private GitHub repo `BenSheridanEdwards/GrokClaw` and pushed the full workspace as the initial commit.
- **2026-03-14** — Connected GitHub to the GrokClaw Linear workspace (both `github` and `githubPersonal` integrations active alongside `slack`). Commits referencing `GRO-XXX` auto-link to Linear tickets.
- **2026-03-14** — Verified Cursor agent (user ID `ca233eb8-8630-49c9-8f7c-3708c1bd1c4b`) exists in the GrokClaw Linear workspace and can be delegated tickets via `delegateId`.
- **2026-03-14** — Upgraded `tools/linear-ticket.sh` to always set `delegateId` to Cursor on every new issue.
- **2026-03-14** — Created `tools/create-pr.sh`: creates a `grok/<issue-id>` branch off main, pushes it, and opens a draft GitHub PR linked back to the Linear issue. Verified working (produced PR #2).
- **2026-03-14** — Upgraded `AGENTS.md` approval workflow: on `approve`, Grok now runs linear-ticket.sh → create-pr.sh → posts both URLs in Slack. Full three-step flow tested and confirmed working.
- **2026-03-14** — Updated `cron/jobs.json` daily suggestion payload to include the three-step approval instructions.
- **2026-03-14** — All changes committed and pushed to `main` on `BenSheridanEdwards/GrokClaw`.

## Active integrations

- **Slack** — bot connected to workspace, posts to `grok-orchestrator` (channel `C0ALE1S0LSF`)
- **Linear** — API key in `.env`, GrokClaw team ID `3f1b1054-07c6-4aad-a02c-89c78a43946b`
- **GitHub** — `gh` CLI authenticated as `BenSheridanEdwards`, repo `BenSheridanEdwards/GrokClaw`

## Suggestion history

| # | Title | Status |
|---|-------|--------|
| 1 | (pre-memory) | Unknown |
| 2 | Install and integrate 'linear' skill for automated ticket creation | Approved → GRO-8 |
| 3 | Slack thread reply parsing for automatic approval handling | Pending |

## Known gaps (do not re-suggest without checking this list)

- Slack `approve` replies still require manual CLI trigger — Grok cannot listen for thread replies autonomously yet (Suggestion #3)
- `USER.md` is empty — no user preferences or context recorded
- No retry logic on failed tool calls
- No health check or alerting if the gateway process dies
- Session summarization threshold may be too aggressive (currently 200 messages)

## Configuration

- Model: `grok-4-1-fast-non-reasoning`
- Workspace: `/Users/jarvis/.picoclaw/workspace`
- Cron: daily suggestion at 06:00, job ID `4978a69dab9ec327`
