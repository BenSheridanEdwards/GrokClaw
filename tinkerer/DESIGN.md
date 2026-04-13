# Tinkerer Application Agent — Design Spec

**Date:** 2026-04-13

## Purpose

Tinkerer is GrokClaw's third OpenClaw agent — a browser-use application agent that applies to the Stationed AI Tinkerer role on Ben's behalf. It reads `BUILDER.md` (a pure profile of Ben), conducts an interactive interview for the Submission field, dynamically generates form answers via xAI Grok, and uses browser-use to navigate and submit the application at `https://jadan.zo.space/ai-tinkerer/apply`.

This is Challenge 1: "Let Your Agent Apply" — the submission itself demonstrates agent-steering capability.

Tinkerer is GrokClaw's third agent alongside Grok and Alpha. It uses the same xAI Grok infrastructure, is routable through the same OpenClaw gateway, and sits in the architecture as a peer. The difference: it's manually invoked, not cron-scheduled.

## Position in GrokClaw

| Agent | Model | Schedule | Role |
|-------|-------|----------|------|
| **Grok** | `xai/grok-4-1-fast-non-reasoning` | 08:00 UTC daily | Coordinator, daily brief, PR review |
| **Alpha** | `openrouter/nvidia/nemotron-3-super-120b-a12b:free` | Hourly | Polymarket research and trading |
| **Tinkerer** | `xai/grok-4-1-fast-non-reasoning` + `grok-3-fast` (browser) | Manual invoke | Application agent for Stationed AI Tinkerer role |

Tinkerer is registered in the OpenClaw gateway, routable via Paperclip's agent resolver, and documented across `AGENTS.md`, `NorthStar.md`, `README.md`, and the architecture docs as GrokClaw's third agent.

## Files

| File | Purpose |
|------|---------|
| `tinkerer/BUILDER.md` | Pure markdown profile of Ben — who he is, what he's built, his stack, philosophy. Committed, public. |
| `tinkerer/sensitive-data.md` | Gitignored. Contact info Ben doesn't want public. |
| `tinkerer/sensitive-data.md.example` | Committed template showing the expected format, no real values. |
| `tinkerer/tinkerer-interview.md` | Gitignored. Persisted answers from the interactive interview. Created on first `--safe` run, reused on subsequent runs. Editable by Ben. |
| `tinkerer/tinkerer-interview.md.example` | Committed template showing the interview questions and expected format. |
| `tinkerer/safe-trial.md` | Gitignored. Generated output from `--safe` mode. Every form field with the answer Tinkerer would give. Reviewed by Ben. |
| `tools/tinkerer-apply.py` | Agent script. Three modes: `--safe`, `--trial`, `--submit`. |
| `tools/run-tinkerer-apply.sh` | Thin launcher — sources `.env`, finds browser-use Python env, forwards args. |
| `tools/run-openclaw-agent-tinkerer.sh` | OpenClaw gateway routing — same pattern as Grok and Alpha. |

`tinkerer/sensitive-data.md`, `tinkerer/tinkerer-interview.md`, and `tinkerer/safe-trial.md` are gitignored.

## README Anchor

The `## Tinkerer` section in `README.md` is the landing page for Stationed reviewers. The GitHub link in the application form points to `https://github.com/BenSheridanEdwards/GrokClaw#tinkerer` — reviewers land directly on the explanation of what they're looking at, including links to this design spec and the implementation plan.

## BUILDER.md

Pure markdown. Sections about Ben — not structured around the form. Tinkerer reads this and figures out how to answer each field dynamically.

Sections:

- **Identity** — name (phone/email/location live in `sensitive-data.md`)
- **Online** — GitHub, website, portfolio links
- **Current Role** — what Ben does now, title, company
- **Technical Stack** — languages, frameworks, tools
- **What I've Built** — projects, systems, things Ben is proud of
- **AI Journey** — how Ben got into AI, what he's experimenting with, comfort level
- **Philosophy** — how Ben thinks about AI, what excites him

No form questions, no field labels, no application-specific framing. Just Ben.

## Interactive Interview

The Submission field asks four specific things:

1. What you built or wrote
2. Why you picked this challenge
3. What you'd do with another week
4. What you're most excited about in AI right now

These require Ben's authentic voice. Tinkerer handles this with an interactive interview baked into the `--safe` workflow.

### Interview Flow

On `--safe` run:

1. Check if `tinkerer-interview.md` exists
2. If not, prompt Ben with 4 questions in the terminal, one at a time:
   - "Tell me about GrokClaw — what is it, what did you build, what's interesting about it?"
   - "Why Challenge 1: Let Your Agent Apply?"
   - "What would you do with another week?"
   - "What excites you most about AI right now?"
3. Save raw answers to `tinkerer-interview.md`
4. On subsequent runs, read from `tinkerer-interview.md` (skip prompts)
5. To re-answer, delete `tinkerer-interview.md` or edit it directly

Tinkerer synthesizes the raw interview answers + BUILDER.md into the polished Submission response. The substance is Ben's; Tinkerer handles framing and flow.

## Form Fields

The Stationed application form at `https://jadan.zo.space/ai-tinkerer/apply` has these fields:

| Field | Type | How Tinkerer handles it |
|-------|------|------------------------|
| Name | text input, required | From BUILDER.md Identity |
| Email Address | text input, required | From `sensitive-data.md` |
| Phone Number | text input, required | From `sensitive-data.md` |
| Location | text input | From `sensitive-data.md` |
| GitHub / Projects | text input | `https://github.com/BenSheridanEdwards/GrokClaw#tinkerer` |
| Which challenge | dropdown, required | Fixed: "1. Let Your Agent Apply" |
| Submission | textarea, required | Synthesized from `tinkerer-interview.md` + BUILDER.md |
| Attach a file | file upload | Not used (GitHub link covers it) |
| AI journey | textarea, required | Generated from BUILDER.md AI Journey + What I've Built |
| What keeps you excited | textarea, required | Generated from BUILDER.md Philosophy |

## Three Modes

### `--safe`

No browser. Pure generation (calls xAI API for text synthesis).

1. Read `BUILDER.md` (exit with error if missing)
2. Read `sensitive-data.md` (exit with error if missing, point to example)
3. Run interactive interview if `tinkerer-interview.md` doesn't exist
4. Read `tinkerer-interview.md`
5. Generate form answers via `grok-4-1-fast-non-reasoning`
6. Write `safe-trial.md` with every form field and its generated answer
7. Print path to `safe-trial.md` and exit

Ben reviews, tweaks `BUILDER.md` or `tinkerer-interview.md` if needed, runs `--safe` again until satisfied.

### `--trial`

**Pipeline check (not an offline dry run):** launches a **headed** browser against the **live** application URL, fills every field with **hardcoded test placeholders** (does not read `BUILDER.md` or `sensitive-data.md`), then stops before Submit. Use this to prove browser-use end-to-end before you run `--submit` with real answers.

1. Launch browser-use agent with headed browser (visible)
2. Agent navigates to application URL
3. Agent fills every field with hardcoded test data
4. Agent stops before clicking Submit
5. Agent extracts all filled values and prints structured summary

### `--submit`

Real submission with approval gate.

1. Read `BUILDER.md` and `tinkerer-interview.md` (both must exist — run `--safe` first)
2. Read `safe-trial.md` if it exists (use pre-generated answers for consistency)
3. Launch browser-use agent with headed browser (visible)
4. Agent navigates to application URL and fills every field with real data
5. Agent stops before clicking Submit
6. Ben reviews the filled form in the browser
7. CLI prompts `Submit this application? [y/N]`
8. On `y`: agent clicks Submit and confirms the success screen
9. On anything else: exits without submitting

## Agent Task Prompt Strategy

The browser-use Agent receives a natural language task. The task prompt includes:

- The full contents of `BUILDER.md` (inlined)
- The interview answers from `tinkerer-interview.md` (inlined)
- The pre-generated answers from `safe-trial.md` if available (for consistency)
- The target URL
- Instructions to navigate to the form, fill every field, select Challenge 1
- For `--trial`: instructions to fill but not submit
- For `--submit`: instructions to fill and submit

The agent decides how to interact with the form dynamically — which elements to click, how to handle dropdowns, how to type into textareas. Tinkerer navigates like a human, not via a deterministic script.

## Model

For `--safe` mode, Tinkerer uses `grok-4-1-fast-non-reasoning` via `XAI_API_KEY` from `.env` — same xAI API the other GrokClaw agents use.

For `--trial` and `--submit` modes, Tinkerer uses browser-use Agent with `grok-3-fast` (configurable via `BROWSER_USE_MODEL` env var) through `ChatOpenAILike` from `browser_use.llm.openai.like`. Vision is not supported with xAI models yet (text-mode only, which works fine). Browser is always headed so Ben can watch the form being filled.

**Smoke-tested 2026-04-13:** Both browser-use CLI and browser-use Agent + Grok successfully navigated to the form and filled the Name field. Evidence: `tinkerer/smoke-test-form-fill.png`, `tinkerer/test-grok-browser.py`.

## Error Handling

- If `BUILDER.md` doesn't exist or is empty, exit with clear error message
- If `sensitive-data.md` doesn't exist, exit with message pointing to `sensitive-data.md.example`
- If `tinkerer-interview.md` doesn't exist in `--submit` mode, exit with message: "Run --safe first to complete the interview" (`--trial` does not use the interview)
- If browser-use fails to navigate or fill, the agent's built-in retry/recovery handles it
- `--trial` and `--submit` modes require `browser-use` to be installed; `--safe` does not

## What Success Looks Like

1. Ben fills in `BUILDER.md` with his profile
2. `./tools/run-tinkerer-apply.sh --safe` asks 4 interview questions, saves answers, generates `safe-trial.md`
3. Ben reviews `safe-trial.md`, tweaks inputs, re-runs `--safe` until satisfied
4. `./tools/run-tinkerer-apply.sh --trial` exercises the live form in a visible browser with test placeholders only — Ben watches
5. `./tools/run-tinkerer-apply.sh --submit` sends the application
6. Stationed reviewers click the GitHub link, land on `README.md#tinkerer`, and see exactly how this was built
