# Cursor Agent Instructions

You are a Cursor agent assigned to implement work in the GrokClaw repository.

---

## When you are assigned a ticket

1. **Read the Linear ticket** — the description contains the full spec, acceptance criteria, and implementation notes. Read it before touching any code.
2. **Read `AGENTS.md`** — understand the system you are working on.
3. **Read `memory/MEMORY.md`** — understand what's already built so you don't duplicate work.
4. **Check out the branch** — your branch is `grok/<GRO-XX>` or `cursor/<GRO-XX-slug>`. It already exists on origin.
5. **Implement the work** — write real code, config, or documentation. No placeholders.
6. **Wire it up** — see "Every feature must be triggered" below.
7. **Test it** — run the thing and verify it works. See "Testing requirements" below.
8. **Update `memory/MEMORY.md`** — before committing, append a dated bullet under "Completed work" describing exactly what you built and how it runs. Example:
   ```
   - **2026-03-19** — GRO-XX: added tools/example.sh; wired via cron/jobs.json `example-job`; posts status to Telegram health topic.
   ```
9. **Commit** — clear messages referencing the issue (e.g. `feat: add health check GRO-14`).
10. **Push and mark ready** — `gh pr ready <number> --repo BenSheridanEdwards/GrokClaw`
    **Never merge your own PR.** Merging is Ben's decision.
11. **Post completion to Telegram**:
    ```
    ./tools/telegram-post.sh suggestions "🤖 GRO-XX complete. PR: <pr-url>"
    ```

---

## Every feature must be triggered

Writing a script is not enough. It must be wired to something that actually runs it. A script that is never called does nothing.

### Choosing the right trigger

| What you're building | Use |
|----------------------|-----|
| Something that checks on the agent/gateway itself (health checks, watchdogs) | **System crontab** — external checks keep working if gateway is unhealthy |
| Scheduled agent tasks (research, suggestions, reports) | **OpenClaw cron** — `cron/jobs.json` |
| Something triggered by a user message or approval | **AGENTS.md workflow** — document the command Grok should run |
| A one-off utility | **Document it** — add usage to the tool's header comment and to `docs/` |

### System crontab (macOS/Linux)

Use when the feature must work even if the OpenClaw gateway is down.

Add the entry programmatically in your PR:

```sh
# Add to system crontab — do this in your implementation
(crontab -l 2>/dev/null; echo "*/5 * * * * /Users/jarvis/Engineering/Projects/GrokClaw/tools/your-script.sh >> /tmp/your-script.log 2>&1") | crontab -
```

Verify it was added:
```sh
crontab -l | grep your-script
```

### OpenClaw cron (`cron/jobs.json`)

Use for scheduled agent tasks. Add a new job object to the `jobs` array:

```json
{
  "id": "<generate a random 16-char hex id>",
  "name": "descriptive-job-name",
  "enabled": true,
  "schedule": {
    "kind": "cron",
    "expr": "*/5 * * * *"
  },
  "payload": {
    "kind": "agent_turn",
    "message": "Your instruction to Grok here.",
    "deliver": true,
    "channel": "telegram",
    "to": "-1003831656556"
  },
  "deleteAfterRun": false
}
```

---

## Testing requirements

Before marking a PR ready, you must verify:

- [ ] The script runs without errors: `bash tools/your-script.sh`
- [ ] The trigger is wired: `crontab -l | grep your-script` or confirm `cron/jobs.json` has the entry
- [ ] The trigger fires correctly: manually invoke it and confirm the output
- [ ] If it posts to Telegram: confirm the message appears in the right topic
- [ ] If it creates files: confirm the files exist with correct permissions

Include the test output in your PR description under a **Verification** section.

---

## Repository layout

```
/Users/jarvis/Engineering/Projects/GrokClaw/
├── AGENTS.md              # Grok operating instructions
├── CURSOR.md              # This file
├── IDENTITY.md            # System identity
├── memory/MEMORY.md       # Persistent memory — read before starting
├── cron/jobs.json         # OpenClaw scheduled jobs
├── tools/
│   ├── telegram-post.sh       # Post to Telegram topics
│   ├── telegram-suggestion.sh # Post daily suggestions with Approve button
│   ├── telegram-inline.sh     # Post messages with inline action buttons
│   ├── linear-ticket.sh       # Create Linear tickets
│   ├── review-pr.sh           # Fetch PR diff for Grok to review
│   └── health-check.sh        # Health check for OpenClaw gateway process
└── docs/                  # Documentation for tools and integrations
```

**Key config file locations:**
- OpenClaw config: `~/.openclaw/openclaw.json`
- Gateway port: `18800` (from config — do not hardcode other values)
- Telegram group: `-1003831656556` (topic routing in `.env`)

---

## Coding standards

- Shell scripts: POSIX sh, `set -eu`, no bashisms.
- Python: stdlib only unless clearly warranted.
- No `TODO` or placeholder comments. Implement it or don't create the file.
- Every new script must be executable (`chmod +x`).
- Read `.env` and `~/.openclaw/openclaw.json` for config values — do not hardcode ports, paths, or tokens.
- Keep memory persistent: every verified change must be reflected in `memory/MEMORY.md`.

---

## What "done" means

- [ ] The feature works end-to-end, not just the script existing
- [ ] It is wired to a trigger (system cron, OpenClaw cron, or documented workflow step)
- [ ] The trigger has been verified to fire
- [ ] Real file changes in the PR (not just the scaffold commit)
- [ ] `memory/MEMORY.md` updated with a dated bullet describing what was built and how it runs
- [ ] Verification output included in PR description
- [ ] PR marked ready for review
- [ ] Completion posted to Telegram suggestions topic
