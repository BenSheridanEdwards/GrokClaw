# GrokClaw Self-Improvement Loop

After each approved suggestion and PR, Grok reviews its own accuracy and appends a lessons-learned bullet to `memory/MEMORY.md`.

## How it works

1. Grok approves a PR (PR review workflow step 5)
2. Grok updates `memory/MEMORY.md` with completed work and suggestion history
3. **Accuracy review**: Grok reflects on (1) did the implementation match the spec? (2) was the estimate right?
4. Grok runs `./tools/append-lesson-learned.sh <GRO-XX> "<assessment and lesson>"` to append the bullet

## Trigger: AGENTS.md PR review workflow

This is a post-approval operating practice, not a separate cron job. Grok executes it when approving a PR or closing a suggestion loop that produced a concrete lesson. The current `AGENTS.md` PR workflow no longer names this as a numbered step, so keep this document as the source of truth for when to run the helper.

## Tool: append-lesson-learned.sh

```
./tools/append-lesson-learned.sh <issue-id> "<lesson text>"
```

- Creates `## Lessons learned` section in `memory/MEMORY.md` if missing
- Appends a dated bullet: `- **YYYY-MM-DD** — GRO-XX: <lesson>`
- New entries appear at the top of the section (most recent first)

Example:
```sh
./tools/append-lesson-learned.sh GRO-17 "Implementation matched spec. Clear acceptance criteria reduced back-and-forth."
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WORKSPACE_ROOT` | Derived from script path | Workspace root |
