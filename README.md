# GrokClaw

GrokClaw is an OpenClaw-powered multi-agent system with three active agents and two core workflows.

## Agents

![PaperClip Org Chart](docs/images/paperclip-org-chart.png)

| Agent | Model | Fallback | Role |
|-------|-------|----------|------|
| **Grok** | xAI Grok Fast | OpenRouter Nemotron 3 Super (free) | Coordinator, daily brief, PR review, Linear intake |
| **Alpha** | OpenRouter Nemotron 3 Super (free) | — | Hourly Polymarket research and trading |
| **Tinkerer** | xAI Grok Fast + browser-use | — | Application agent for Stationed AI Tinkerer role (manual invoke) |

Grok has a fallback chain so daily briefs never silently die when a provider hits rate limits. Alpha and Tinkerer run on single providers without fallbacks.

## Grok

Grok is the coordinator, reviewer, and system operator. It runs the daily system brief, reviews PRs on GitHub before Telegram asks Ben to merge, and turns approved suggestions into PM-quality Linear tickets delegated to Cursor.

**Schedule:** 08:00 UTC daily

Produces one Telegram message covering the last 24 hours: what succeeded, what failed, what needs attention.

## Alpha

Alpha is the hourly Polymarket research and paper trading agent. Purely for fun.

**Schedule:** Hourly

Every hour, Alpha looks for prediction markets that are close to resolving (within ~36 hours) and checks whether three trusted professional traders have taken positions. If they have, and the risk checks pass, Alpha copies the trade. If not, it records HOLD. All trades are simulated — no real money.

**How it works:**

1. **Find a candidate** — fetch active Polymarket markets sorted by volume, filter to those near resolution, and check if any of three known profitable wallets have positions
2. **Evaluate risk** — the candidate must clear minimum edge (0.5%), confidence, and volume gates, then gets sized using a conservative Kelly fraction (25% of optimal) capped at 1% of bankroll
3. **Decide** — TRADE if all gates pass, HOLD if not. Every decision is logged with full reasoning
4. **Learn** — results are tracked and fed back into memory so Alpha can self-correct over time

Decision tools: `polymarket-trade.sh` → `polymarket-decide.sh` → `polymarket-resolve-turn.sh`

## Tinkerer

Tinkerer is GrokClaw's third agent — built for [Stationed's AI Tinkerer Challenge 1: "Let Your Agent Apply"](https://jadan.zo.space/ai-tinkerer).

Instead of filling out a job application by hand, I built an AI agent that does it autonomously. Tinkerer reads a builder profile ([`tinkerer/BUILDER.md`](tinkerer/BUILDER.md)), conducts an interactive interview to capture authentic answers, and uses [browser-use](https://github.com/browser-use/browser-use) to dynamically navigate and submit the real application form.

Tinkerer is a proper OpenClaw agent — it uses the same xAI Grok infrastructure as Grok, is routable through the same gateway, and sits in the architecture as a peer to Grok and Alpha. The difference: it's manually invoked, not cron-scheduled.

### How it works

```
INTERVIEW.md / interactive CLI
         ↓
    --safe (Grok generates answers)
         ↓
    safe-trial.md  ← review & iterate
         ↓
    --trial (browser fills form with test data)
         ↓
    --submit (browser fills form with real data + CV)
         ↓
    "submit" or "close" prompt (human-in-the-loop)
```

| Mode | What happens | Browser? |
|------|-------------|----------|
| `--safe` | Reads your profile + interview answers, sends them to Grok to generate form-ready text. Outputs `safe-trial.md` for review. Re-run until satisfied. | No |
| `--trial` | Opens a headed browser on the live form. Fills every field with test placeholders and uploads a CV. Stops before Submit. | Yes |
| `--submit` | Same as trial but uses your real data from `safe-trial.md`, `BUILDER.md`, and `sensitive-data.md`. Uploads your CV. Prompts for explicit `submit` or `close` before acting. | Yes |

**Models:** `--safe` uses `grok-4-1-fast-non-reasoning` for answer generation. `--trial` and `--submit` use `grok-3-fast` via [browser-use](https://github.com/browser-use/browser-use) for autonomous form navigation.

### Safety workflow

The entire pipeline is designed so no real submission can happen without explicit human approval:

1. **`--safe`** — generates answers offline, no browser, no form interaction. You review `safe-trial.md` and iterate.
2. **`--trial`** — proves the browser automation works on the live form with fake data. You watch it fill fields and upload files.
3. **`--submit`** — fills the real form with your real data, then stops and waits. You inspect every field in the browser. Only typing `submit` at the prompt triggers the click. `close` or Ctrl+C keeps the browser open without submitting.

### Interview system

Tinkerer captures your authentic voice through a structured interview, either interactively or from a pre-written file:

| Source | When used |
|--------|-----------|
| `tinkerer/INTERVIEW.md` | Pre-written answers organised by form field (see `INTERVIEW.md.example`). **Takes precedence** when present alongside `tinkerer-interview.md`. |
| `tinkerer/tinkerer-interview.md` | Written by the interactive CLI interview (4 questions, editor-based input); uses the same `# Field - …` structure (see `tinkerer-interview.md.example`). |
| Interactive CLI | Runs automatically on first `--safe` if neither file exists. Opens each question in `$EDITOR` to avoid terminal paste-buffer limits. |

The interview maps directly to the three form textareas:
- `# Field - Submission` → Submission textarea (what you built, why this challenge, next steps, what excites you)
- `# Field - Where are you on your AI journey?` → AI Journey textarea
- `# Field - What keeps you excited about the future?` → Excitement textarea

### Quick start

```bash
# 1. Create your profile and contact info from the templates
cp tinkerer/BUILDER.md.example tinkerer/BUILDER.md
cp tinkerer/sensitive-data.md.example tinkerer/sensitive-data.md
# Edit both files with your details

# 2. Write your interview answers (or let the CLI interview you)
cp tinkerer/INTERVIEW.md.example tinkerer/INTERVIEW.md
# Edit with your answers

# 3. Generate form-ready answers
./tools/run-tinkerer-apply.sh --safe

# 4. Review tinkerer/safe-trial.md — tweak INTERVIEW.md and re-run --safe until satisfied

# 5. Test the browser pipeline with fake data
./tools/run-tinkerer-apply.sh --trial

# 6. Fill the real form and review before submitting
./tools/run-tinkerer-apply.sh --submit
```

### Architecture

```
tinkerer/
├── BUILDER.md                 ← Your public profile (see BUILDER.md.example)
├── INTERVIEW.md               ← Pre-written answers by form field (see INTERVIEW.md.example)
├── DESIGN.md                  ← Design spec: field mapping, modes, model choices
├── IMPLEMENTATION.md          ← Implementation plan with verification gates
├── test-grok-browser.py       ← Smoke test: name fill + CV upload on the live form
├── smoke-test-form-fill.png   ← Evidence: browser-use smoke test
├── submit-dry-run-form-top.png ← Evidence: --submit dry run with real data
├── sensitive-data.md          ← Contact info: email, phone, location (gitignored)
├── tinkerer-interview.md      ← CLI-generated interview answers (gitignored)
├── safe-trial.md              ← Grok-generated form answers for review (gitignored)
└── BenSheridanEdwards-CV-2026.pdf ← CV uploaded to the form's file attachment (gitignored)

tools/
├── tinkerer-apply.py          ← Agent script (3 modes: --safe, --trial, --submit)
└── run-tinkerer-apply.sh      ← Shell launcher (sources .env, activates venv)
```

### Design documentation

- [`tinkerer/DESIGN.md`](tinkerer/DESIGN.md) — Design spec: form field mapping, three-mode architecture, interview flow, model choices, error handling
- [`tinkerer/IMPLEMENTATION.md`](tinkerer/IMPLEMENTATION.md) — Implementation plan: 7 tasks with step-by-step instructions, file-level change tracking, verification gates
- [`tinkerer/BUILDER.md.example`](tinkerer/BUILDER.md.example) — Template for your public profile
- [`tinkerer/INTERVIEW.md.example`](tinkerer/INTERVIEW.md.example) — Template showing the interview structure expected by `--safe`
- [`tinkerer/sensitive-data.md.example`](tinkerer/sensitive-data.md.example) — Template for contact info (email, phone, location)
- [`tinkerer/tinkerer-interview.md.example`](tinkerer/tinkerer-interview.md.example) — Template for CLI-generated interview output

### Why this exists

The Stationed application asks applicants to "show how you think" and "use agents." Challenge 1 specifically says: let your agent apply. This is that — an agent that reads who you are and applies for you. The agent steering, the profile-to-form pipeline, the CV upload, and the three-mode safety workflow are the submission.

## OpenClaw System Architecture

```
Telegram ←→ OpenClaw Gateway ←→ Grok / Alpha agents
                  ↓
            Cron scheduler → cron-core-workflow-run.sh → agent turn
                  ↓
            Paperclip (per-run issue lifecycle)
            data/cron-runs/*.jsonl (execution history)
            data/audit-log/*.jsonl (Telegram audit trail)
            data/linear-creations/*.jsonl (Linear policy enforcement)
```

Every workflow run creates a Paperclip issue, writes a cron record, and posts to Telegram. If any of those are missing, the workflow health audit flags it.

## Integrations

| Integration | Purpose |
|-------------|---------|
| **Telegram** | Human operating surface — topic-based forum group |
| **Linear** | Engineering work tracking — only created after explicit approval |
| **GitHub** | Source control and PR review |
| **Paperclip** | Per-run operational dashboard |
| **OpenClaw** | Gateway, cron, and agent runtime |

### Telegram Topics

| Topic | Content |
|-------|---------|
| `suggestions` (2) | Daily brief, improvement proposals, approval outcomes |
| `polymarket` (3) | Alpha trading summaries |
| `health` (4) | Incidents, watchdog alerts, deploy results |
| `pr-reviews` (5) | Grok-reviewed PRs ready for merge |

## PaperClip — Operational Dashboard

[PaperClip](https://paperclip.dev) is the control plane for GrokClaw's agents. Every workflow run, every issue, and every cost event flows through it.

![PaperClip Dashboard](docs/images/paperclip-dashboard.png)

### How GrokClaw uses PaperClip

Every cron workflow run automatically creates a PaperClip issue, giving full traceability from trigger to completion. The dashboard surfaces what matters: which runs succeeded, which failed, and what needs attention — without digging through logs.

| Capability | How it's used |
|------------|---------------|
| **Run tracking** | Each agent run is recorded with status, run ID, and type — viewable in the Runs tab |
| **Issue lifecycle** | Workflow runs create issues; priorities (Critical → Low) and statuses (Done, Cancelled) track operational health |
| **Agent control** | Assign tasks, trigger heartbeats, and pause agents directly from the UI |
| **Cost visibility** | Per-agent and company-level cost tracking across all runs |
| **Activity feed** | Chronological log of everything that happened across the system |

### The org

PaperClip models GrokClaw as a company with an org chart. Grok is the CEO coordinating daily operations; Alpha reports in as a Research Worker running the Polymarket loop; Tinkerer is the Application Agent for the Stationed AI Tinkerer role.

All three agents run through the OpenClaw Gateway — PaperClip sees the same execution layer that powers the cron scheduler and Telegram integration.

## Reliability Stack

| Layer | Tool | Schedule |
|-------|------|----------|
| Health probe | `tools/health-check.sh` | Every 2 min (system cron) |
| Gateway watchdog | `tools/gateway-watchdog.sh` | Every 5 min (launchd) |
| Workflow doctor | `tools/grokclaw-doctor.sh` | `:02, :17, :32, :47` (launchd) |
| Self-deploy | `tools/self-deploy.sh` | On merge |
| Cron validation | `tools/cron-jobs-tool.py` | On sync |

Health monitoring alerts Telegram once per failure with a one-tap rerun button. Workflow failures enter Linear only through an approval-gated draft — no automatic ticket creation.

### Evidence Contract

Every workflow run is checked post-completion for required artifacts (Telegram posts, research files, agent reports). Missing artifacts are auto-repaired and classified by severity:

| Severity | Meaning | Effect on run status |
|----------|---------|---------------------|
| **error** | Primary deliverable missing (Telegram post fabricated) | Run marked as `error` |
| **warning** | Secondary artifact missing (agent report, research file) | Run stays `ok` |

### Dedup Guards

- **Health alerts** — same job+error combination is only posted to Telegram once per hour
- **Telegram posts** — during cron runs, duplicate posts to the same topic for the same run ID are suppressed

## Knowledge Graph

GrokClaw uses [Graphify](https://github.com/BenSheridanEdwards/graphify) to maintain a navigable knowledge graph of the codebase. Graphify makes building with Claude Code and other coding agents more efficient — agents query the graph instead of scanning raw files, using ~28x fewer tokens per codebase question.

- `graphify-out/wiki/index.md` — agent-crawlable wiki with community articles
- `graphify-out/graph.html` — interactive HTML visualization
- `graphify-out/graph.json` — GraphRAG-ready JSON
- `graphify-out/GRAPH_REPORT.md` — god nodes, communities, surprising connections

Rebuild after code changes: `./tools/graphify-rebuild.sh` (install [Graphify](https://github.com/BenSheridanEdwards/graphify) with `pip install -e /path/to/graphify`, or set `GRAPHIFY_SRC` to that repo root if the package is not already importable).

## Linear Policy

Linear issues are only created in two flows:

1. Ben approves a daily suggestion (two-step: approve suggestion → approve drafted ticket)
2. Ben explicitly requests a bug fix or feature in Telegram

All creations are logged to `data/linear-creations/*.jsonl`. The daily brief flags any violations.

## Key Docs

| Doc | Purpose |
|-----|---------|
| `NorthStar.md` | Source of truth for the operating model |
| `AGENTS.md` | Agent operating instructions and multi-agent layout |
| `CURSOR.md` | Cursor implementation contract |
| `docs/multi-agent-setup.md` | Multi-agent technical setup |
| `docs/system-architecture.md` | Architecture overview |
