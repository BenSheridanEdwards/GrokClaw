# GrokClaw Self-Improvement Loop

After each approved suggestion and PR, Grok reviews its own accuracy and appends a lessons-learned bullet to `memory/MEMORY.md`.

## How it works

1. Grok approves a PR (PR review workflow step 5)
2. Grok updates `memory/MEMORY.md` with completed work and suggestion history
3. **Accuracy review**: Grok reflects on (1) did the implementation match the spec? (2) was the estimate right?
4. Grok runs `./tools/append-lesson-learned.sh <GRO-XX> "<assessment and lesson>"` to append the bullet

## Trigger: AGENTS.md PR review workflow

This runs as part of the PR review workflow in `AGENTS.md` step 6. No separate cron — Grok executes it when approving a PR.

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
| `PICOCLAW_WORKSPACE` | Derived from script path | Workspace root |
