# Cursor Superpowers Workflow

GRO-27 integrates the [obra/superpowers](https://github.com/obra/superpowers) (MIT) workflow into GrokClaw's Cursor delegation.

## What It Is

Superpowers is an agentic skills framework that enforces a structured development workflow:

1. **Brainstorm** — Clarify requirements, propose approaches, get design approval before code.
2. **Plan** — Break work into bite-sized TDD tasks (2–5 min each).
3. **TDD** — RED-GREEN-REFACTOR. No production code without a failing test first.
4. **Execute** — Subagent per task or inline; two-stage review (spec compliance, then code quality).
5. **Review** — Request code review after each task and before merge.

## Where It Lives

| Path | Purpose |
|------|---------|
| `skills/superpowers/` | Core skills (forked from obra/superpowers) |
| `skills/superpowers/SKILL.md` | Entry point and workflow overview |
| `tools/cursor-superpowers.sh` | Outputs preamble for Cursor sessions |

## How It's Triggered

- **PR creation:** `create-pr.sh` auto-injects superpowers instructions into the PR body. Cursor reads the PR when assigned.
- **Manual:** Run `./tools/cursor-superpowers.sh` to output the preamble; prepend to task context when delegating.

## Upstream

- **Repository:** https://github.com/obra/superpowers
- **License:** MIT
- **Skills:** brainstorming, writing-plans, test-driven-development, subagent-driven-development, requesting-code-review, using-superpowers
