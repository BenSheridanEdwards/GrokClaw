# Long-term Memory

Grok must read this file in full before proposing any suggestion, and update it after every verified action.

---

## Completed work

- **2026-03-14** — Created private GitHub repo `BenSheridanEdwards/GrokClaw` and pushed the full workspace as the initial commit.
- **2026-03-14** — Connected GitHub to the GrokClaw Linear workspace (`github` + `githubPersonal` integrations active). Commits referencing `GRO-XXX` auto-link to Linear tickets.
- **2026-03-14** — Verified Cursor agent exists in the GrokClaw Linear workspace (ID: `ca233eb8-8630-49c9-8f7c-3708c1bd1c4b`) and can be delegated tickets via `delegateId` on `IssueCreateInput`.
- **2026-03-14** — Upgraded `tools/linear-ticket.sh` to always set `delegateId` to Cursor on every new issue. Verified working.
- **2026-03-14** — Created `tools/create-pr.sh`: creates a `grok/<issue-id>` branch off main, pushes it, and opens a draft GitHub PR linked to the Linear issue. Verified working (produced PR #2).
- **2026-03-14** — Full approval flow confirmed working end-to-end: `approve` → Linear ticket (with Cursor delegated) → GitHub PR → Slack reply with both links.
- **2026-03-14** — Rewrote `AGENTS.md` and `IDENTITY.md` to fully document the system, integrations, and complete suggestion → approval → implementation → Slack report flow.
- **2026-03-14** — Updated `cron/jobs.json` payload to include memory-read step and full three-step approval flow.
- **2026-03-14** — Implemented GRO-14: `tools/gateway-health-check.sh` detects PicoClaw gateway death and alerts to Slack. Runs via system cron; see `docs/gateway-health-check.md`.

---

## Active integrations

| Integration | Status | Key detail |
|-------------|--------|-----------|
| Slack | ✅ Active | Bot in `grok-orchestrator`, channel `C0ALE1S0LSF` |
| Linear | ✅ Active | GrokClaw team ID `3f1b1054-07c6-4aad-a02c-89c78a43946b`, API key in `.env` |
| GitHub | ✅ Active | Repo `BenSheridanEdwards/GrokClaw`, `gh` CLI as `BenSheridanEdwards` |
| Cursor agent | ✅ Active | Linear user ID `ca233eb8-8630-49c9-8f7c-3708c1bd1c4b`, assigned via `delegateId` |

---

## Suggestion history

| # | Title | Status |
|---|-------|--------|
| 1 | (unknown — pre-memory) | Unknown |
| 2 | Install and integrate Linear skill for automated ticket creation | Approved → GRO-8 |
| 3 | Slack thread reply parsing for automatic approval handling | Rejected (already partially handled by CLI trigger) |

**Next suggestion number: 4**

---

## Known gaps — backlog for future suggestions

Pick from this list when researching the next suggestion. Do not suggest anything already in "Completed work".

- `USER.md` is empty — user preferences, timezone, communication style not recorded
- No retry logic on failed tool calls (linear-ticket.sh or create-pr.sh)
- Session summarization threshold may need tuning (currently 200 messages / 95% token fill)
- Cursor agent has no instructions for what to do once assigned a ticket — no `CURSOR.md` or equivalent
- No automated tests for the approval flow scripts
- PicoClaw changelog / release notes not yet regularly checked — need to confirm how to fetch these

---

## System configuration

| Setting | Value |
|---------|-------|
| Model | `grok-4.1-fast` (alias: `grok-4-1-fast-non-reasoning`) |
| Workspace | `/Users/jarvis/.picoclaw/workspace` |
| Cron job | `daily-grokclaw-suggestion`, runs 06:00 daily, job ID `4978a69dab9ec327` |
| GitHub repo | `BenSheridanEdwards/GrokClaw` |
| Linear team | `GrokClaw` (`3f1b1054-07c6-4aad-a02c-89c78a43946b`) |
| Slack channel | `grok-orchestrator` (`C0ALE1S0LSF`) |
