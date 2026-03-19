---
name: superpowers
description: Use when implementing Linear tickets or PRs delegated to Cursor. Mandatory workflow: brainstorm → plan → TDD tasks → subagent exec → review. Use when starting any Cursor implementation task.
---

# Superpowers — GrokClaw Cursor Workflow

**Upstream:** [obra/superpowers](https://github.com/obra/superpowers) (MIT)

You are a Cursor agent implementing work for GrokClaw. Follow the superpowers workflow for consistent quality and depth.

## Mandatory Workflow

1. **Brainstorm** — Use `skills/superpowers/brainstorming/SKILL.md`. Clarify requirements, propose approaches, get design approval before code.
2. **Plan** — Use `skills/superpowers/writing-plans/SKILL.md`. Break work into bite-sized TDD tasks (2–5 min each). Exact file paths, complete code, verification steps.
3. **TDD** — Use `skills/superpowers/test-driven-development/SKILL.md`. RED-GREEN-REFACTOR. No production code without a failing test first.
4. **Execute** — Use `skills/superpowers/subagent-driven-development/SKILL.md` or execute inline. Fresh subagent per task, two-stage review (spec compliance, then code quality).
5. **Review** — Use `skills/superpowers/requesting-code-review/SKILL.md`. Review after each task and before merge.

## Core Skills (in this repo)

| Skill | Path | When |
|-------|------|------|
| using-superpowers | `skills/superpowers/using-superpowers/SKILL.md` | Session start — how to invoke skills |
| brainstorming | `skills/superpowers/brainstorming/SKILL.md` | Before any creative work |
| writing-plans | `skills/superpowers/writing-plans/SKILL.md` | After design approval |
| test-driven-development | `skills/superpowers/test-driven-development/SKILL.md` | Before implementation code |
| subagent-driven-development | `skills/superpowers/subagent-driven-development/SKILL.md` | Executing plans |
| requesting-code-review | `skills/superpowers/requesting-code-review/SKILL.md` | After tasks, before merge |

## GrokClaw Conventions

- Read `CURSOR.md` for full operating instructions.
- Read `memory/MEMORY.md` before starting — never duplicate completed work.
- Commit with messages referencing the Linear issue (e.g. `feat: add X GRO-27`).
- Wire triggers: system cron, OpenClaw cron, or documented workflow.
- Update `memory/MEMORY.md` with a dated bullet when done.

## Red Flags

- Jumping to code without design approval
- Writing code before tests
- Skipping review between tasks
- Rationalizing "just this once" for TDD
