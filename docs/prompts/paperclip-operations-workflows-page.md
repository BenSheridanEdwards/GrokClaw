# Implementation prompt: Paperclip “Operations” / “Workflows” page

Use this document as the single spec when implementing the highest-ROI GrokClaw operator view inside the Paperclip UI (`paperclip/ui`).

## Goal

Give operators an **at-a-glance table** of the **three North Star scheduled workflows** (one row per workflow), grounded in **Paperclip issues** created by `tools/cron-paperclip-lifecycle.sh` / cron prompts — not in raw `data/cron-runs` JSONL (that stays the automation audit trail; this page is the human shell).

## Workflow identity

Fixed workflow keys (match OpenClaw cron job `name` / bracket prefix in issue titles):

| Workflow key              | Title prefix (regex group 1)   |
|---------------------------|---------------------------------|
| `grok-daily-brief`        | `[grok-daily-brief]`            |
| `grok-openclaw-research`| `[grok-openclaw-research]`      |
| `alpha-polymarket`        | `[alpha-polymarket]`            |

**Detection (v1):** Parse each issue `title` with:

```regexp
^\[(grok-daily-brief|grok-openclaw-research|alpha-polymarket)\]\s*
```

Capture group 1 is the workflow key. **Optional v2:** If the product adds **labels** per workflow (e.g. `workflow:grok-daily-brief`), prefer label match when present and fall back to title regex for backward compatibility.

## Data sources (existing APIs — prefer reuse)

- **Issues:** `issuesApi.list(companyId)` from `paperclip/ui/src/api/issues.ts` (filter client-side unless you add a dedicated server query param).
- **Comments (summary line):** `issuesApi.listComments(issueId)` — use the **chronologically last** comment’s `body` (trim, first line or first ~160 chars).
- **Linked heartbeat runs:** `activityApi.runsForIssue(issueId)` from `paperclip/ui/src/api/activity.ts` (see `IssueDetail.tsx` — `runsForIssue` / timeline). Pick the **latest** run by `createdAt` or `startedAt` (define one rule and document it).
- **Live / active run (optional enhancement):** `heartbeatsApi.liveRunsForIssue` / `activeRunForIssue` if you need “in flight” vs historical.

Do **not** invent new backend contracts unless necessary; if the UI would N+1 too hard, add a **single** aggregated endpoint (e.g. `GET /companies/:id/workflow-runs-summary`) as a follow-up — not required for v1 if performance is acceptable for three rows × a few issues.

## Row selection: “Last issue” per workflow

For each workflow key:

1. Consider all issues in the **current company** whose title matches the regex (or label, if v2).
2. **Last issue** = the one with the greatest `updatedAt` (or `createdAt` if you lack updates — pick one and stay consistent).
3. Always show **three rows** (one per workflow), even when **no** matching issue exists — empty cells + copy like “No run issue yet”.

## Table columns (exact semantics)

| Column            | Content |
|-------------------|---------|
| **Workflow**      | Human label + workflow key (e.g. “Daily brief · `grok-daily-brief`”). |
| **Last issue**    | Link to issue detail: internal route `/{companyPrefix}/issues/{issueId}` (match existing `Issues` / `IssueDetail` patterns). Show short title or identifier if available. |
| **Status**        | Paperclip issue status for **last issue** (`todo`, `in_progress`, `done`, etc.) — reuse `StatusBadge` / `StatusIcon` patterns. |
| **Last run state**| From **latest** linked heartbeat run for that issue: `status` from `RunForIssue` (or live widget status if you merge live + history). If no run: “—”. |
| **Finished**      | `finishedAt` of that latest run (relative time OK — reuse `relativeTime` from `lib/utils`). If null / no run: “—” or “Running”. |
| **One-line summary** | Last comment body, first line (strip markdown noise lightly if already done elsewhere). If no comments, try a **structured footer** in the issue description if you document a convention (e.g. `Summary: …`); otherwise “—”. |

## Links (required)

- **Issue:** always the last-issue link above.
- **Latest heartbeat run:** when a `runId` exists for the chosen latest run, link to the **same run view** the rest of the app uses (today: agent run route under `App.tsx`, e.g. `/agents/:agentId/runs/:runId` — **verify** against current router and how `IssueDetail` opens a run).

## UX / navigation

- Add a **sidebar / nav item** next to Dashboard / Activity (exact label: **“Operations”** or **“Workflows”** — pick one for ship; “Operations” reads broader if you add non-cron ops later).
- Route example: `/{companyPrefix}/operations` or `.../workflows`.
- Optional: manual **refresh** button or rely on React Query `refetchInterval` (e.g. 30–60s) for the three workflows.

## Edge cases

- **Multiple issues per workflow:** table shows only **last** by rule above; optional “+N older” link filtering `issues` list by `q=` title prefix if API supports search.
- **Title drift:** if an issue title is renamed and no longer matches, it **drops out** of the view unless labels exist (v2).
- **Permissions:** respect existing company gate / auth (same as other board pages).

## Acceptance criteria

1. Page loads for a selected company and shows **exactly three** workflow rows.
2. Columns match the table above; empty states are explicit, not blank confusion.
3. Issue and run links work in local dev (`paperclip` + gateway).
4. No regression to existing Issues / IssueDetail behavior.
5. Lightweight test or story optional; **manual QA checklist** in PR description is enough for v1.

## Out of scope (explicit)

- Editing cron, closing issues, or mutating runs from this page.
- Replacing `grokclaw-doctor` / `data/cron-runs` workflow health — this is **operator visibility**, not the health contract.

---

*Prompt version: 2026-04-08 — GrokClaw / Paperclip.*
