# Cursor Agent Instructions

You are a Cursor agent assigned to implement work in the GrokClaw repository.

## When you are assigned a ticket

1. **Read the Linear ticket** — the ticket title and description contain the full spec. Read it before touching any code.
2. **Read `AGENTS.md`** — understand the system you are working on.
3. **Check out the branch** — your branch is `grok/<GRO-XX>`. It already exists on origin. Check it out and work on it.
4. **Implement the work** — write real code, config, or documentation as required by the spec. Do not leave placeholder files.
5. **Commit your changes** — use clear commit messages referencing the issue (e.g. `feat: add health check script GRO-14`).
6. **Push and mark the PR ready for review** — run `gh pr ready <number> --repo BenSheridanEdwards/GrokClaw` when done.
7. **Post to Slack** — run:
   ```
   /Users/jarvis/.picoclaw/workspace/tools/slack-post.sh C0ALE1S0LSF "🤖 GRO-XX complete. PR: <pr-url>"
   ```

## Repository layout

```
/Users/jarvis/.picoclaw/workspace/
├── AGENTS.md          # Grok operating instructions
├── CURSOR.md          # This file — Cursor agent instructions
├── IDENTITY.md        # System identity
├── memory/MEMORY.md   # Persistent memory — read before starting
├── tools/
│   ├── linear-ticket.sh   # Creates Linear issues
│   ├── create-pr.sh       # Creates GitHub branches + PRs
│   └── slack-post.sh      # Posts to Slack (channel C0ALE1S0LSF)
├── cron/jobs.json     # Scheduled jobs
└── skills/            # Agent skills
```

## Coding standards

- Shell scripts: POSIX sh, `set -eu`, no bashisms.
- Python: stdlib only unless a dependency is clearly warranted.
- No placeholder comments like "TODO: implement this". Either implement it or don't create the file.
- Every script must be executable (`chmod +x`).
- Test your script before pushing — run it and verify the output.

## What "done" means

- The feature described in the Linear ticket is implemented and working.
- The PR has real file changes (not just the scaffold commit).
- You have posted the completion message to Slack.
- The PR is marked ready for review (not draft).
