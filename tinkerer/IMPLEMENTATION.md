# Tinkerer Application Agent — Implementation Plan

**Date:** 2026-04-13
**Goal:** Build Tinkerer, GrokClaw's third OpenClaw agent — a browser-use application agent for the Stationed AI Tinkerer role (Challenge 1: "Let Your Agent Apply").

**Architecture:** Three-mode CLI tool (`--safe`, `--trial`, `--submit`). `--safe` generates answers with no browser. `--trial` uses a headed browser on the live URL with built-in test placeholders and stops before Submit (no `BUILDER.md` / `sensitive-data.md`). `--submit` uses your profile and optional `safe-trial.md`, prompts, then submits. Profile data for `--safe` / `--submit` comes from `tinkerer/BUILDER.md` (public) and `tinkerer/sensitive-data.md` (gitignored). Interview answers live in `tinkerer/tinkerer-interview.md` (gitignored).

**Tech Stack:** Python 3, browser-use SDK, xAI Grok API (`grok-4-1-fast-non-reasoning` for generation, `grok-3-fast` for browser), shell launcher.

**Spec:** [`tinkerer/DESIGN.md`](DESIGN.md)

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `AGENTS.md` | Modify | Register Tinkerer as third OpenClaw agent with model and routing |
| `NorthStar.md` | Modify | Add Tinkerer to system goal (3 agents) |
| `README.md` | Modify | Add `## Tinkerer` anchor section with design docs, architecture, quick start |
| `memory/MEMORY.md` | Modify | Update live status table, add completed work entry |
| `docs/system-architecture.md` | Modify | Add Tinkerer to mermaid diagram with gateway connection, xAI and browser-use edges |
| `docs/multi-agent-setup.md` | Modify | Add Tinkerer to agent table and manual runs section |
| `tools/run-openclaw-agent-tinkerer.sh` | Modify | Route `OPENCLAW_AGENT_ID=tinkerer` through gateway |
| `paperclip/packages/adapters/openclaw-gateway/src/server/execute.ts` | Modify | Add `tinkerer` to Paperclip agent name resolver |
| `paperclip/packages/adapters/cursor-local/src/index.ts` | Modify | Add `tinkerer` to model list |
| `.gitignore` | Modify | Add tinkerer workspace gitignore entries |
| `tinkerer/BUILDER.md` | Create | Ben's public profile |
| `tinkerer/sensitive-data.md.example` | Create | Template for sensitive fields |
| `tinkerer/tinkerer-interview.md.example` | Create | Template for interview questions |
| `tinkerer/DESIGN.md` | Create | Design spec |
| `tinkerer/IMPLEMENTATION.md` | Create | This implementation plan |
| `tools/tinkerer-apply.py` | Create | Main agent script (3 modes) |
| `tools/run-tinkerer-apply.sh` | Create | Thin shell launcher |

---

## Task 1: Register Tinkerer as an OpenClaw agent across the codebase

Register Tinkerer as the third OpenClaw agent with real model info and gateway routing across every file that references the agent lineup.

**Files:**
- `AGENTS.md` — Agent table: model `xai/grok-4-1-fast-non-reasoning`, routing docs for manual invoke
- `NorthStar.md` — System goal: "3 agents", Tinkerer with model and capabilities
- `README.md` — Agent table: model "xAI Grok Fast + browser-use", role description
- `docs/system-architecture.md` — Mermaid diagram: solid gateway connection, xAI API and browser-use edges, runtime snapshot
- `docs/multi-agent-setup.md` — Agent table with model info, manual runs section
- `paperclip/packages/adapters/openclaw-gateway/src/server/execute.ts` — Agent name resolver: `tinkerer` → OpenClaw agent ID
- `paperclip/packages/adapters/cursor-local/src/index.ts` — Model list: `tinkerer`
- `tools/run-openclaw-agent-tinkerer.sh` — `OPENCLAW_AGENT_ID="tinkerer"`
- `tools/grokclaw-doctor.sh` — Update Ollama check message
- `tools/grok-daily-brief.sh` — Update comment
- `tools/cron-run-record.sh` — Update agent list comment
- `tests/test_cron_run_record.py` — Update test fixture
- `tests/test_workflow_prompts.py` — Update assertions
- `memory/MEMORY.md` — Update live status table, add completed work entry

**Verification:**
```bash
python3 -m pytest tests/ -v  # 224 tests pass
```

---

## Task 2: Create Tinkerer workspace and templates

**Files:**
- `.gitignore` — Add `tinkerer/sensitive-data.md`, `tinkerer/tinkerer-interview.md`, `tinkerer/safe-trial.md`
- `tinkerer/BUILDER.md` — Ben's profile (filled in by Ben)
- `tinkerer/sensitive-data.md.example` — Template with example contact fields
- `tinkerer/tinkerer-interview.md.example` — Template with the 4 interview questions
- `tinkerer/DESIGN.md` — Design spec
- `tinkerer/IMPLEMENTATION.md` — This plan

---

## Task 3: Create the shell launcher

**File:** `tools/run-tinkerer-apply.sh`

Thin shell launcher that sources `.env` for API keys, finds the browser-use Python environment at `~/.browser-use-env/bin/python`, and forwards all args to `tinkerer-apply.py`.

**Verification:**
```bash
chmod +x tools/run-tinkerer-apply.sh
sh -n tools/run-tinkerer-apply.sh  # clean syntax
```

---

## Task 4: Implement tinkerer-apply.py (all three modes)

**File:** `tools/tinkerer-apply.py`

The core script with all three modes:

- `--safe`: Interactive interview (if needed) → answer generation via `grok-4-1-fast-non-reasoning` → `safe-trial.md`
- `--trial`: browser-use Agent with `grok-3-fast`, headed browser, live form, test placeholders, stops before Submit
- `--submit`: browser-use Agent with real profile / `safe-trial.md`, confirm prompt, then Submit

Key implementation details:
- `parse_sensitive_data()` extracts `**Key**: value` fields from markdown
- `generate_safe_answers()` calls xAI API with builder profile + interview, returns structured form answers
- `run_browser()` launches browser-use `Agent` with `ChatOpenAILike` pointing at xAI API
- Browser is always headed (visible) so Ben can watch

**Verification:**
```bash
python3 -c "import ast; ast.parse(open('tools/tinkerer-apply.py').read()); print('OK')"
./tools/run-tinkerer-apply.sh --safe  # should error: sensitive-data.md not found
```

---

## Task 5: Add Tinkerer section to README.md

Add the `## Tinkerer` anchor section that Stationed reviewers land on via the GitHub link. Includes:

- What Tinkerer is and its position in GrokClaw
- How it works (table of 3 modes with model info)
- Quick start guide
- Architecture file layout
- Links to `DESIGN.md`, `IMPLEMENTATION.md`, smoke test evidence

---

## Task 6: Browser-use smoke test

Pre-implementation smoke test confirming browser-use + xAI Grok works against the real Stationed form.

- [x] browser-use CLI: navigated to form, filled Name field
- [x] browser-use Agent + `grok-3-fast`: autonomous navigation, found Name field, typed test value
- [x] Evidence: `tinkerer/smoke-test-form-fill.png`, `tinkerer/test-grok-browser.py`

**Findings:**
- Python agent env: `~/.browser-use-env/bin/python`
- Must use `browser_use.llm.openai.like.ChatOpenAILike` (library's own wrapper)
- `grok-3-fast` works, vision not supported yet (text-mode only, which is fine)
- `Browser(headless=False)` for visible browser

---

## Task 7: End-to-end verification

```bash
# Full test suite
python3 -m pytest tests/ -v  # 224 tests pass

# Shell syntax
sh -n tools/run-tinkerer-apply.sh
sh -n tools/run-openclaw-agent-tinkerer.sh
sh -n tools/grokclaw-doctor.sh
sh -n tools/grok-daily-brief.sh
sh -n tools/cron-run-record.sh

# Python syntax
python3 -c "import ast; ast.parse(open('tools/tinkerer-apply.py').read())"

# browser-use available
~/.browser-use-env/bin/python -c "from browser_use import Agent; print('OK')"

# --safe mode (requires BUILDER.md and sensitive-data.md filled)
./tools/run-tinkerer-apply.sh --safe

# --trial mode (no BUILDER.md / interview required; optional any time before --submit)
./tools/run-tinkerer-apply.sh --trial
```
