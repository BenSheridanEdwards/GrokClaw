# Long-term Memory

Grok must read this file in full before proposing any suggestion, and update it after every verified action.

## Memory operating contract

- This file is the canonical long-term memory for GrokClaw.
- Update it after every verified workflow action (suggestion, approval, PR review, deploy, reliability fix).
- Keep `Completed work`, `Suggestion history`, and `Known gaps` synchronized with reality.
- Never re-suggest anything already listed in `Completed work`.
- Runtime state files (idempotency, guards) live in `~/.openclaw/state`; this file stores durable human-readable context.

---

## Completed work
- **2026-04-19** — **Alpha Polymarket Paperclip wake (20:02 GMT+7):** Agent woke for issue_assigned but found issue already completed by orchestrator (status: done). Added confirmation comment and marked issue done via Paperclip API.
- **2026-04-19** — **Alpha Polymarket Paperclip wake (12:02 GMT+7):** Agent woke for issue_assigned but found issue already completed by orchestrator (status: done). Added confirmation comment and marked issue done via Paperclip API.
- **2026-04-19** — **Alpha Polymarket hourly run (03:02 UTC):** Executed deterministic Polymarket research and trading workflow. Evaluated "Will the highest temperature in Hong Kong be 31°C or higher ..."; used volume_fallback selection, no copy signal (status=unavailable), resulted in HOLD decision. Research output written to data/alpha/research/2026-04-19-03.md. Paperclip issue 6aefcfb3-df49-48b2-9d6f-9e8a04432655 processed and marked complete.
- **2026-04-19** — **Alpha Polymarket hourly run (12:02 UTC):** Executed deterministic Polymarket research and trading workflow. Evaluated "Will the price of Ethereum be between $2,000 and $2,100 on April 19?"; used volume_fallback selection, no copy signal (status=unavailable), resulted in HOLD decision. Research output written to data/alpha/research/2026-04-19-12.md. Paperclip issue ccc8deb4-e76e-44f7-870b-47698431521d processed and marked complete.
- **2026-04-19** — **Alpha Polymarket hourly run (22:02 UTC):** Executed deterministic Polymarket research and trading workflow. Evaluated "Will Progressive Bulgaria (PB) win the most seats in the 202...?"; used volume_fallback selection, no copy signal (status=unavailable), resulted in HOLD decision. Research output written to data/alpha/research/2026-04-18-22.md. Paperclip issue 55bb9879-0949-42a2-8667-019fc9fd41b7 processed and marked complete.
- **2026-04-19** — **Alpha Polymarket Paperclip wake (17:02 GMT+7):** Agent woke for issue_assigned but found issue already completed by orchestrator (status: done). Added confirmation comment and marked issue done via Paperclip API.
- **2026-04-18** — **Alpha Polymarket Paperclip wake (09:05 UTC):** Agent woke for issue_assigned but found issue already completed by orchestrator (status: done). Added confirmation comment and marked issue done via Paperclip API.
- **2026-04-18** — **Alpha Polymarket hourly run (09:02 UTC):** Executed deterministic Polymarket research and trading workflow. Evaluated "Will the price of Bitcoin be above $74,000 on April 21?"; used whale_top_trader_copy selection, resulted in TRADE decision (edge: 0.0656, stake: 19.2). Research output written to data/alpha/research/2026-04-18-09.md. Paperclip issue e7fede33-ec41-4532-9d9f-19a4bddb2180 processed and marked complete.
- **2026-04-18** — **Alpha Polymarket Paperclip wake (02:02 GMT+7):** Agent woke for issue_assigned but found issue already completed by orchestrator (status: done). Added confirmation comment and marked issue done via Paperclip API.
- **2026-04-18** — **Alpha Polymarket hourly run (20:02 UTC):** Executed deterministic Polymarket research and trading workflow. Evaluated "Will the price of Bitcoin be above $76,000 on April 19?"; used whale_top_trader_copy selection, resulted in HOLD decision (rejected: edge_below_threshold, confidence_below_threshold, stake_non_positive.). Research output written to data/alpha/research/2026-04-18-20.md. Paperclip issue b2a08db7-2d79-4e6a-bcb4-01489b9cef2e processed and marked complete.
- **2026-04-18** — **Alpha Polymarket hourly run (14:02 UTC):** Executed deterministic Polymarket research and trading workflow. Evaluated "Will the price of Bitcoin be above $68,000 on April 19?"; used volume_fallback selection, resulted in HOLD decision (rejected: market_at_extreme, edge_below_threshold). Research output written to data/alpha/research/2026-04-18-14.md. Paperclip issue 80945b85-2f99-4633-8fad-1079d2f55fa3 processed and marked complete.
- **2026-04-16** — **Alpha Polymarket hourly run (18:02 UTC):** Executed deterministic Polymarket research and trading workflow. Evaluated \"Israel announces suspension of Lebanon offensive by April 17...\"; used whale_top_trader_copy selection, no copy signal (status=unavailable), resulted in HOLD decision. Research output written to data/alpha/research/2026-04-16-18.md. Paperclip issue db2d051f-91f9-40a7-a410-cb492fcaf0a8 processed and marked complete.

- **2026-04-16** — **Alpha Polymarket Paperclip wake (22:02 GMT+7):** Agent woke for issue_assigned but found issue already completed by orchestrator (status: done). Added confirmation comment and marked issue done via Paperclip API.
- **2026-04-16** — **Alpha Polymarket Paperclip wake (20:02 GMT+7):** Agent woke for issue_assigned but found issue already completed by orchestrator (status: done). Added confirmation comment and marked issue done via Paperclip API.
- **2026-04-16** — **grok-daily-brief cron (08:00 UTC):** Workflow executed via Paperclip wake (GRO-903). Reviewed MEMORY.md + last 24h: Alpha Polymarket HOLDs only, OpenClaw research no gaps vs v2026.4.9, no PRs/Linear todos, system healthy. No daily suggestion warranted. Run skipped (no recent activity), Telegram health summary posted, Paperclip issue closed as done.

- **2026-04-16** — **Alpha Polymarket hourly run (11:02 UTC):** Executed deterministic Polymarket research and trading workflow. Evaluated "Will the price of Bitcoin be between $68,000 and $70,000 on April 16?"; used volume_fallback selection, no copy signal (status=unavailable), resulted in HOLD decision. Research output written to data/alpha/research/2026-04-16-11.md. Paperclip issue 1fe5baf2-c26a-4c9f-952d-9493a3408419 processed and marked complete.

- **2026-04-16** — **Alpha Polymarket Paperclip wake (14:02 GMT+7):** Agent woke for issue_assigned but found issue already completed by orchestrator (status: done). Added confirmation comment and marked issue done via Paperclip API.

- **2026-04-16** — **Alpha Polymarket Paperclip wake (12:02 GMT+7):** Agent woke for issue_assigned but found issue already completed by orchestrator (status: done). Added confirmation comment and marked issue done via Paperclip API.

- **2026-04-16** — **Alpha Polymarket Paperclip wake (07:02 GMT+7):** Agent woke for issue_assigned but found issue already completed by orchestrator (status: done). Added confirmation comment and marked issue done via Paperclip API.

- **2026-04-17** — **Alpha Polymarket hourly run (16:02 UTC):** Executed deterministic Polymarket research and trading workflow. Evaluated \"Will Bitcoin reach $82,000 on April 17?\"; used whale_top_trader_copy selection, no copy signal (status=unavailable), resulted in HOLD decision. Research output written to data/alpha/research/2026-04-17-16.md. Paperclip issue 469b0f97-8a2a-4ac8-803d-19ac321f7676 processed and marked complete.
- **2026-04-17** — **Alpha Polymarket hourly run (17:02 UTC):** Executed deterministic Polymarket research and trading workflow. Evaluated \"Will the price of Bitcoin be above $72,000 on April 18?\"; used whale_top_trader_copy selection, no copy signal (status=unavailable), resulted in HOLD decision (rejected: edge_below_threshold, open_exposure_cap). Research output written to data/alpha/research/2026-04-17-17.md. Paperclip issue 35451239-2366-4d00-bab9-0a3114b7065d processed and marked complete.

- **2026-04-15** — **Tinkerer `generate_safe_answers`:** Single delimiter contract — `SAFE_ANSWER_FIELD_SEPARATOR = "===FIELD==="`; prompt and split logic both use only that (removed `---FIELD---` / markdown `---` fallbacks).

- **2026-04-15** — **Tinkerer `run_browser` free-text:** Replaced literal `\\n` textarea embedding with `json.dumps` of submission/journey/excitement plus instructions to parse JSON and paste decoded multi-line strings in one action.

- **2026-04-15** — **Tinkerer `run_browser` CV preflight:** Resolves `tinkerer/{CV_FILENAME}`; `--submit` exits early with a clear error if the PDF is missing. `--trial` prints a preflight note, omits the file from `available_file_paths`, instructs the agent to skip CV upload, and repeats a summary line after the run.

- **2026-04-15** — **Tinkerer parser tests:** Added `tests/test_tinkerer_apply_parsers.py` — unit tests for `parse_sensitive_data`, `extract_name`, and `parse_safe_trial` (including `safe-trial.md` header exact-match behavior) via `importlib` load of `tools/tinkerer-apply.py`.

- **2026-04-15** — **Tinkerer `tools/tinkerer-apply.py`:** ImportError for `browser_use` now points to https://github.com/browser-use/browser-use#readme and describes venv + pip after review; removed `curl | bash` install suggestion.

- **2026-04-15** — **Tinkerer `tools/tinkerer-apply.py`:** `extract_name()` now finds `- **Name**:` case-insensitively; `validate_builder_name()` runs after loading `BUILDER.md` so `--safe` / `--submit` fail fast if name is missing or empty, with a pointer to `tinkerer/BUILDER.md.example`. Missing `BUILDER.md` copy hint uses `tinkerer/BUILDER.md.example`.

- **2026-04-15** — **Tinkerer `tools/tinkerer-apply.py`:** After `parse_sensitive_data()`, added `validate_sensitive_data()` so `--safe` and `--submit` exit early unless **Email**, **Phone**, and **Location** are non-empty (expected markdown list keys under `## Contact`, per `sensitive-data.md.example`). Prevents incomplete `safe-trial.md` and empty form fields.

- **2026-04-15** — **Alpha Polymarket hourly run (23:02 UTC):** Executed deterministic Polymarket research and trading workflow. Evaluated "Will Bitcoin dip to $71,000 on April 14?"; used volume_fallback selection, no copy signal (status=unavailable), resulted in HOLD decision. Research output written to data/alpha/research/2026-04-14-23.md. Paperclip issue 437d1c1a-c70a-4c24-a6ab-66b11b39a933 processed and marked complete.

- **2026-04-15** — **Alpha Polymarket Paperclip wake (02:02 GMT+7):** Agent woke for issue_assigned but found issue already completed by orchestrator (status: done). Added confirmation comment and marked issue done via Paperclip API.

- **2026-04-14** — **Alpha Polymarket Paperclip wake (21:02 UTC):** Agent woke for issue_assigned but found issue already completed by orchestrator (status: done). Added confirmation comment and marked issue done via Paperclip API.

- **2026-04-14** — **Alpha Polymarket Paperclip wake (16:02 UTC):** Agent woke for issue_assigned but found issue already completed by orchestrator (status: done). Added confirmation comment and marked issue done via Paperclip API.

- **2026-04-14** — **Alpha Polymarket Paperclip wake (13:02 UTC):** Agent woke for issue_assigned but found issue already completed by orchestrator (status: done). Added confirmation comment and marked issue done via Paperclip API.

- **2026-04-14** — **grok-daily-brief cron (08:00 UTC):** Workflow skipped (no recent activity). Reviewed MEMORY.md, last 24h: Alpha HOLDs only, OpenClaw research no gaps vs v2026.4.9, no PRs/Linear todos. System healthy. No daily suggestion.

- **2026-04-14** — **Alpha Polymarket Paperclip wake (15:02 UTC):** Agent woke for issue_assigned but found issue already completed by orchestrator (status: done). Added confirmation comment and marked issue done via Paperclip API.

- **2026-04-14** — **Alpha Polymarket Paperclip wake (06:02 UTC):** Agent woke for issue_assigned but found issue already completed by orchestrator (status: done). Added confirmation comment and marked issue done via Paperclip API.

- **2026-04-14** — **Alpha Polymarket hourly run (04:02 UTC):** Executed deterministic Polymarket research and trading workflow. Evaluated "Valorant: Trace Esports vs Dragon Ranger Gaming (BO3) - VCT..."; used volume_fallback selection, no copy signal (status=unavailable), resulted in HOLD decision. Research output written to data/alpha/research/2026-04-14-04.md. Paperclip issue 56328c6e-cd79-45a1-9624-66ea3196e924 processed and marked complete.

- **2026-04-14** — **Alpha Polymarket hourly run (00:02 UTC):** Executed deterministic Polymarket research and trading workflow. Evaluated "US x Iran diplomatic meeting by April 18, 2026?"; used whale_top_trader_copy selection, no copy signal found, resulted in HOLD decision. Research output written to data/alpha/research/2026-04-14-00.md. Paperclip issue ad38d3d2-8d02-494e-ba8c-a57fb1875cba processed and marked complete.

- **2026-04-13** — Renamed **Kimi** agent to **Tinkerer** across the codebase. Kimi's placeholder shell is now the one-shot application agent for the Stationed AI Tinkerer role (Challenge 1: "Let Your Agent Apply"). Historical Kimi references in memory remain unchanged.

- **2026-04-12** — **Alpha Polymarket Paperclip wake (23:02 UTC):** Executed deterministic Polymarket research and trading workflow via Paperclip wake. Evaluated Ethereum price market, used volume_fallback selection, no copy signal found, resulted in HOLD decision. Research output written to data/alpha/research/2026-04-12-23.md. Paperclip issue GRO-821 processed and marked complete.

- **2026-04-11** — **Graphify rebuild entrypoint:** Added `tools/graphify-rebuild.sh` (tries `python3` import, then `GRAPHIFY_SRC` / common clone paths). Updated `CLAUDE.md`, `CURSOR.md`, and `README.md` (Knowledge Graph) to use it instead of a raw `python3 -c` one-liner. Graphify is not on PyPI and the upstream repo is private from this agent environment; local rebuild: install Graphify (`pip install -e …`) or `export GRAPHIFY_SRC=/path/to/graphify-repo` then `./tools/graphify-rebuild.sh`.

- **2026-04-11** — **Unit test suite green:** `tools/_linear_workflow_health_cleanup.py` no longer reads `LINEAR_TEAM_ID` at import time (avoids `KeyError` in CI); team id is required inside `find_open_workflow_health_issues` when Linear is queried. `tests/test_linear_workflow_health_cleanup.py` patches `LINEAR_TEAM_ID` for those calls. `tests/test_self_deploy.py` dummy `.env` includes `TELEGRAM_GROUP_ID=-100…` so `cron-jobs-tool validate` expands `delivery.to` and `self-deploy` can reach “No deploy needed”. Verified: `./tools/test-all.sh` OK.

- **2026-04-11** — **OpenClaw cron scheduler dead (missing `job.state`):** Gateway logged `cron failed to start: TypeError: Cannot read properties of undefined (reading 'runningAtMs')` whenever `~/.openclaw/cron/jobs.json` contained a row without a dict `state` (e.g. legacy id `1` in `.bak`, or repo sync merging jobs that never had runtime state). OpenClaw’s `start()` reads `job.state.runningAtMs` before `normalizeJobTickState` runs. **Fix:** `tools/cron-jobs-tool.py` now calls `ensure_cron_job_state_dicts()` on every sync merge output (and when the target file is missing/corrupt) so each job gets `state: {}` at minimum. `tools/_cron_unstick_running.py` also normalizes missing/non-dict `state` and still clears `runningAtMs`. Tests: `tests/test_cron_unstick_running.py`, `tests/test_sync_cron_jobs.py`. **Live:** `./tools/sync-cron-jobs.sh --restart` — log shows `cron: running missed jobs after restart` for `alpha-polymarket` and `grok-openclaw-research`; scheduler running again.

- **2026-04-09** — **Paperclip OpenClaw adapter reliability cleanup:** In `paperclip/packages/adapters/openclaw-gateway/src/server/execute.ts`, session keys are now always agent-scoped (`agent:<id>:...`) using `agentId` precedence `payloadTemplate.agentId -> adapterConfig.agentId -> Paperclip agent name alias (alpha/kimi/grok) -> main`, and missing `agentParams.agentId` is auto-filled with the same normalized id to prevent Alpha/main mismatches. The adapter now treats lifecycle/error stream failures (including upstream provider rate limits) as terminal failures (`openclaw_gateway_lifecycle_error`) instead of reporting false `status=ok` success. Tests updated in `paperclip/server/src/__tests__/openclaw-gateway-adapter.test.ts`; Paperclip cleanup also removed duplicate dependency key in `paperclip/server/package.json`. Verification: `pnpm test:run server/src/__tests__/openclaw-gateway-adapter.test.ts`, `pnpm --filter @paperclipai/adapter-openclaw-gateway typecheck`, `pnpm --filter @paperclipai/server typecheck`; Paperclip service restarted (`./tools/paperclip-ctl.sh restart`) and in-progress issue queue is clean (`./tools/paperclip-api.sh list-issues in_progress` → none).

- **2026-04-09** — **Dexter strategy prompt/logic tightened to bonding-only:** Updated `docs/prompts/cron-work-alpha-polymarket.md` to remove whale-fallback language, require bonding-copy-first behavior, and explicitly HOLD when no valid bonding setup exists. Updated deterministic executor `tools/_alpha_polymarket_deterministic.py` to gate trades on `selection_source == bonding_copy` (no non-bonding copy trades), switch memory narrative to bonding terminology, and replace whale-accuracy prompting with bonding lookup query. Added regression in `tests/test_alpha_polymarket_deterministic.py` (`test_deterministic_flow_skips_non_bonding_copy_sources`) and prompt assertion in `tests/test_workflow_prompts.py`. Verification: `python3 -m unittest tests/test_alpha_polymarket_deterministic.py tests/test_workflow_prompts.py tests/test_cron_core_workflow_run.py` (19 tests OK).

- **2026-04-09** — **Alpha deterministic runtime hardening + 3x live verification:** Found live failure in deterministic Alpha runs where `polymarket-decide.sh` rejected boundary probabilities (`model probability must be a finite float in (0, 1)`) when copy consensus returned exact `1.0/0.0`. Added open-interval probability clamp in `tools/_alpha_polymarket_deterministic.py` and regression coverage in `tests/test_alpha_polymarket_deterministic.py` (`test_deterministic_flow_clamps_boundary_probability_for_decide`). Verified focused suite (`20 tests OK`) and re-ran `cron-core-workflow-run.sh alpha-polymarket alpha` three times (`alpha-live-verify-fixed-{1..3}-20260409`): all runs `started -> ok`, no evidence repairs, workflow checks healthy, deterministic research artifacts written, one deterministic HOLD Telegram line emitted per run delta, and agent reports posted.

- **2026-04-09** — **Alpha memory backend failover + paper-trading reset:** Added backend dispatcher `tools/alpha-memory.py` and new JSONL memory backend `tools/mempalace-alpha.py`; then removed legacy memory scripts and moved runtime paths to `tools/alpha-memory-query.sh` and `tools/alpha-memory-ingest.sh` so Alpha uses MemPalace only. Added health-check validation in `alpha-memory.py` and confirmed backend state in `data/alpha/memory/backend.json`. Added `tools/polymarket-reset-state.sh` to archive prior ledgers/memory and reset Alpha paper trading to a clean baseline (`$1000`, zero decisions/results). Verification: post-reset metrics `current_bankroll=1000`, `resolved_count=0`, `wins=0`, `total_pnl=0`; memory queries return no prior trades/whale history.

- **2026-04-09** — **Grok OpenClaw research deterministic executor (cron):** Added `tools/_grok_openclaw_research_deterministic.py` + `tools/grok-openclaw-research-deterministic.sh`; `cron-core-workflow-run.sh` now routes `grok-openclaw-research` through deterministic command orchestration (version signals + artifact write + one Telegram headline) instead of free-form LLM execution. It tolerates API/CLI rate limits by falling back to `unknown` values while still writing `data/research/openclaw/YYYY-MM-DD-{slot}.md` and posting `OpenClaw research (<slot>): ...`. Added tests `tests/test_grok_openclaw_research_deterministic.py` and `test_research_uses_deterministic_script_path` in `tests/test_cron_core_workflow_run.py`. Verification: reliability suite `75 tests OK`; live run `research-det-live-1775725532` recorded `started -> ok`, evidence repairs `[]`, workflow check `healthy: true`, and exactly one research headline in-run window.

- **2026-04-09** — **Alpha deterministic executor (cron):** Added `tools/_alpha_polymarket_deterministic.py` + `tools/alpha-polymarket-deterministic.sh`; `cron-core-workflow-run.sh` now routes `alpha-polymarket` through deterministic command orchestration instead of free-form LLM prompt execution. Sequence is fixed: context + memory queries → candidate selection → gate decision (`polymarket-decide.sh`) → resolve + memory ingest → research markdown write → Telegram polymarket line → `agent-report.sh`. Added tests `tests/test_alpha_polymarket_deterministic.py` and `test_alpha_uses_deterministic_script_path` in `tests/test_cron_core_workflow_run.py`. Verification: reliability suite `72 tests OK`; live run `alpha-det-live-1775724463` recorded `started -> ok`, evidence repairs `[]`, workflow check `healthy: true`.

- **2026-04-09** — **Alpha strategy hardening (Dexter-style bonding copy):** `tools/_polymarket_trade.py` now prioritizes a bonding-copy selector before whale/volume fallback (seed wallets: Sharky6999, 033033033, ForesightOracle), targets near-resolution high-probability setups (97-100c), and filters 15-minute latency-arb style markets. `tools/_polymarket_decide.py` adds a dedicated `bonding_copy` risk profile (lower edge/confidence thresholds but tighter stake/exposure caps) so copied late-stage edges can be taken with controlled sizing. Prompt updated at `docs/prompts/cron-work-alpha-polymarket.md`. Tests added/updated: `tests/test_polymarket_trade.py`, `tests/test_polymarket_decide.py`. Verification: `python3 -m unittest tests/test_polymarket_trade.py tests/test_polymarket_decide.py tests/test_workflow_prompts.py tests/test_workflow_health.py`.

- **2026-04-12** — **Alpha primary model → Nemotron free:** `~/.openclaw/openclaw.json` — Alpha `model.primary` set to `openrouter/nvidia/nemotron-3-super-120b-a12b:free` (no fallback). Docs: `AGENTS.md`, `NorthStar.md`, `README.md`, `docs/multi-agent-setup.md`, `docs/system-architecture.md`. Restart gateway to apply.

- **2026-04-09** — **OpenClaw CLI upgrade:** `npm install -g openclaw@latest` — **2026.4.5 → 2026.4.9** (git `0512059`). Operator: restart gateway with `./tools/gateway-ctl.sh restart` and confirm `./tools/health-check.sh` when launchd is running (`openclaw cron list` needs a healthy gateway).

- **2026-04-09** — **Alpha Polymarket Telegram tone:** Hourly lines often read as failures (“skip”, cautionary “Why”). Updated `docs/prompts/cron-work-alpha-polymarket.md` to require **TRADE** / **HOLD**, neutral discipline framing, and avoid alarmist wording unless a command truly failed. Workflow-health audit accepts `Alpha · Hourly ·`, `Alpha (hourly):`, and legacy `Alpha session:`; audit log matching **strips** message whitespace. Tests: `test_workflow_health`, `test_work_prompts`; doc note in `docs/multi-agent-setup.md`; `telegram-post.sh` examples updated.

- **2026-04-08** — **openclaw-gateway session-key verification:** Moved session key helpers to `paperclip/packages/adapters/openclaw-gateway/src/server/session-key.ts`; added Vitest `session-key.test.ts` (11 cases). Commands run: `pnpm run typecheck` and `pnpm run test` in that package; GrokClaw `./tools/test-all.sh` — all green.

- **2026-04-08** — **Paperclip Alpha “invalid agent params” / session mismatch:** OpenClaw only parses agent id from session keys shaped **`agent:<openclawAgentId>:<rest>`**; keys like `paperclip:issue:…` or `paperclip-alpha` resolve to default session agent **`main`**, so `agentId: "alpha"` fails validation. **Code:** `paperclip/packages/adapters/openclaw-gateway/src/server/execute.ts` — `resolveSessionKey` now emits `agent:<id>:paperclip:issue|run|…`, infers `<id>` from `adapterConfig.agentId` or agent display name (`alpha`/`kimi`/`grok`), and sets `agentParams.agentId` to the same normalized id when absent. Restart Paperclip after deploy. (Prior live PATCH `sessionKey=paperclip-alpha` was a partial workaround; issue-assignment runs still needed the adapter fix.)

- **2026-04-08** — **Paperclip org: Alpha (Research Worker):** Created via `POST /api/companies/.../agents` — **Alpha**, title **Research Worker**, role `researcher`, **reportsTo** Grok, `openclaw_gateway` adapter cloned from Grok with **`agentId: "alpha"`** and Alpha-specific wake message. UUID appended to `.env` as **`PAPERCLIP_ALPHA_AGENT_ID`** for `cron-paperclip-lifecycle` assignee routing.

- **2026-04-08** — **Paperclip Alpha as separate employee:** Explained that Paperclip only shows multiple workers when multiple **agents** exist on the company, and that `tools/paperclip-api.sh` always used Grok’s hardcoded `AGENT_ID` for `create-issue`. Fix: `PAPERCLIP_ASSIGNEE_AGENT_ID` override in `paperclip-api.sh`; `cron-paperclip-lifecycle.sh` sets it from **`PAPERCLIP_ALPHA_AGENT_ID`** (`.env`) when `start … alpha`. Docs: `AGENTS.md`, `docs/multi-agent-setup.md`. Tests: `tests/test_cron_paperclip_lifecycle.py`.

- **2026-04-08** — **Paperclip takeover of stalled alpha-polymarket cron run:** Handled GRO-722 ([alpha-polymarket] 2026-04-08 13:19 UTC) directly: ran `./tools/cron-core-workflow-run.sh alpha-polymarket alpha`, reviewed research output (skipped ETH >$1600 due to no edge), posted Telegram summary to polymarket(3) topic, marked Paperclip issue done. Verified research file created at `data/alpha/research/2026-04-08-13.md`. Alpha session still running in background (pid 3975).

- **2026-04-08** — Polymarket Telegram “something went wrong”: OpenClaw cron **completion announce** for `alpha-polymarket` was posting the full agent transcript, exceeding Telegram **4096** char `sendMessage` limit. Fix: `cron/jobs.json` + fixture set **`alpha-polymarket` `delivery.mode: "none"`** (hourly user-visible line remains `tools/telegram-post.sh polymarket` per work prompt); `cron-jobs-tool.py` whitelists that job for `none`; `tools/_telegram_post.py` truncates oversized bodies as a safety net. Docs: `AGENTS.md`, `docs/multi-agent-setup.md`. Tests: `test_workflow_prompts`, `test_telegram_post`, validate temp job with `none` on Grok must fail.

- **2026-04-08** — **Orchestrator-owned core cron lifecycle:** Added `tools/cron-core-workflow-run.sh` (trap EXIT → always terminal `cron-run-record.sh` + `rm` `.issue`) and `tools/_cron_openclaw_agent.py` (file-backed message to `openclaw agent`). Work-only prompts live in `docs/prompts/cron-work-*.md`; `cron/jobs.json` messages are thin “run the wrapper” instructions (Path A). Docs: `NorthStar.md`, `AGENTS.md`, `docs/agent-tasks.md`, `CURSOR.md`, `docs/multi-agent-setup.md`. Tests: `tests/test_cron_core_workflow_run.py` (ok/error/timeout-exit stub), `tests/test_workflow_prompts.py`. Verified: `./tools/test-all.sh` OK.

- **2026-04-08** — Telegram “Paperclip issue left open” for `grok-openclaw-research`: `cron-run-record.sh` preferred `PAPERCLIP_ISSUE_UUID` over `.openclaw/<job>.issue`, so a **stale env** could `finish` an older issue while a newer `start` left another issue `in_progress` → `open_paperclip`. Fix: **read `.openclaw/<job>.issue` first**, then env (`tests/test_cron_run_record.py`, `docs/agent-tasks.md`). Removed temporary debug logging. Cancelled **14** orphan `in_progress` Paperclip issues for the three core jobs (cleanup comment on each). Verified: `python3 tools/_workflow_health.py audit` → `healthy: true`; unittest `test_cron_run_record` + `test_workflow_health` OK.

- **2026-04-08** — grok-openclaw-research cron: Local OpenClaw v2026.4.5 (latest). Git 3e72c03. Healthy. Releases v2026.4.7 (media fallback, memory-wiki, dreaming, Arcee/Gemma providers); v2026.4.5 (video/music gen, ComfyUI, multilingual). Security warnings noted (Telegram open group, Alpha small model) — known/handled. No daily suggestion.

- **2026-04-08** — Stuck cron manual recovery: `tools/_cron_unstick_running.py` + `tools/cron-unstick-and-run.sh` disable all three core OpenClaw cron jobs, strip `runningAtMs`, restart gateway, enqueue requested job ids, re-enable jobs (avoids post-restart auto-fire racing `already-running`). Tests: `tests/test_cron_unstick_running.py`. Enqueued manual runs for `alpha-polymarket` and `grok-daily-brief` after prior `already-running` deadlock.

- **2026-04-08** — Maintenance tooling: `tools/_cron_runs_cleanup.py` removes duplicate same-job `started` rows (keep the last before a terminal) and removes a job’s latest `started` when it is older than `--grace-hours` (default 2) and still no `ok|error|skipped` after it globally. `tools/_linear_workflow_health_cleanup.py` cancels **open** Linear issues whose title exactly matches the workflow-health draft title, deletes `data/pending-linear-draft-workflow-health-*.json`, resets `workflow-health-failures.json`. Wrapper: `tools/grokclaw-maintenance.sh`. Tests: `tests/test_cron_runs_cleanup.py`, `tests/test_linear_workflow_health_cleanup.py`. Ran cron cleanup on `data/cron-runs/2026-04-07.jsonl` and `linear-workflow-health --apply` locally.

- **2026-04-08** — OpenClaw setup hardening: (1) Root cause of chronic workflow-health “stale” false alarms: gateway cron used the Mac system timezone while `_workflow_health.py` expects UTC slot times. Added `TZ=UTC` to `~/Library/LaunchAgents/com.grokclaw.gateway.plist` and checked in `launchd/com.grokclaw.gateway.plist` + `docs/multi-agent-setup.md` / `AGENTS.md` guidance. (2) `tools/gateway-port.sh` resolves HTTP probe port from `OPENCLAW_GATEWAY_PORT` or `gateway.port` in `openclaw.json`; `grokclaw-doctor.sh`, `health-check.sh`, and `gateway-watchdog.sh` use it (health-check loads `.env` before resolving). (3) Restarted gateway via `gateway-ctl.sh restart` after plist change.

- **2026-04-08** — Documented Paperclip **Operations/Workflows** page build spec in `docs/prompts/paperclip-operations-workflows-page.md` (three North Star workflows, last issue + heartbeat run state + one-line summary from last comment).

- **2026-04-07** — OpenClaw cron fix: runtime had a duplicate legacy `grok-daily-brief` row (`id` `1`, `agentTurn` without `message`) alongside the repo-defined job; OpenClaw threw `TypeError: Cannot read properties of undefined (reading 'startsWith')` on that row. `cron-jobs-tool.py` `merge_runtime_fields` now skips orphan jobs whose `name` matches any repo job (still keeps orphans with distinct names). Ran `./tools/sync-cron-jobs.sh --restart` so `~/.openclaw/cron/jobs.json` has only the three North Star workflows. Verified `openclaw cron list` and `tests.test_sync_cron_jobs.TestCronJobsToolSync`.

- **2026-04-07** — Git pull ergonomics: `.gitignore` now covers `.gateway-watchdog-state` and `.gateway-watchdog-lock` (watchdog runtime files, aligned with `.gateway-health-state`). Added `tools/git-pull-main.sh` — same auto-stash pattern as `self-deploy.sh` — so `git pull --rebase --tags origin main` succeeds on a dirty tree without manual stash.

- **2026-04-07** — Full OpenClaw setup audit and legacy-memory integration: (1) Fixed cron drift — runtime had only 1 legacy job, repo had 3 correct jobs. Fixed `self-deploy.sh` to use `sync-cron-jobs.sh --restart`, hardened `cron-jobs-tool.py merge_runtime_fields` to preserve orphan old jobs. (2) OpenClaw at v2026.4.5 confirmed clean. (3) Rebuilt Alpha research loop — research files were empty, no self-improvement. New prompt requires substantive sections, self-correction analysis, whale+model probability blending. (4) Lowered MIN_VOLUME $10k→$5k standard / $3k whale-backed (2+ traders). (5) Added whale signal fields to decision records. (6) Legacy persistent memory was introduced (`data/alpha/memory/alpha-polymarket.mv2` + wrappers) before later migration to MemPalace-only runtime. Ingested 11 decisions + 11 results from history. All `./tools/test-all.sh` tests pass.

- **2026-04-05** — Aligned the checked-in repo source of truth to the live 3-workflow runtime: removed stale Kimi cron jobs from `cron/jobs.json` and the core cron fixture, reduced workflow-health auditing and Paperclip gating to the active 3-workflow contract, and updated operator docs (`AGENTS.md`, `NorthStar.md`, `README.md`, `docs/multi-agent-setup.md`, `docs/agent-tasks.md`, `docs/gateway-health-check.md`, `docs/polymarket-paper-trading.md`) plus related tests to stop describing Kimi as an active scheduled worker. **Verify:** focused workflow suite (`python3 -m unittest ...` for prompts, workflow health, Paperclip lifecycle, cron-run-record, alert formatting), `python3 tools/cron-jobs-tool.py validate cron/jobs.json`, `git diff --check`.

- **2026-04-05** — Reconciled the local `main` checkout back to `origin/main` without losing local-only history (checkpointed on a backup branch first), audited the live `~/.openclaw` runtime against repo docs, and added `docs/system-architecture.md` as a diagrammatic map of the live system. Key drift found: runtime is currently on OpenClaw `2026.4.2`, runs 3 active OpenClaw cron workflows, uses Alpha on `openrouter/nvidia/nemotron-3-super-120b-a12b:free` with Grok fallback, and keeps Kimi as a placeholder shell that still inherits defaults if manually targeted.

- **2026-04-05** — Hardened OpenClaw workflow reliability: core cron prompts now write an early `started` record before long-running work, `cron-run-record.sh` supports `started` plus Paperclip-aware `audit-one --include-paperclip`, `_workflow_health.py` flags in-progress runs stuck past grace, `grokclaw-doctor.sh` validates the full workflow contract before declaring green, `run-openclaw-agent.sh` accepts timeout/retry env knobs, and Telegram posting now uses an explicit API timeout. Verified with `./tools/test-all.sh` including the reliability e2e smoke.

- **2026-04-02** — GRO-44: Alpha primary OpenRouter model and Kimi’s OpenRouter fallback (after Ollama) documented as `openrouter/qwen/qwen3.6-plus-preview:free` (Qwen3.6 Plus Preview free on OpenRouter). Updated `AGENTS.md`, `docs/multi-agent-setup.md`, `README.md`, and this file. Operators align `~/.openclaw/openclaw.json` with those ids; repo has no checked-in gateway JSON.

- **2026-04-02** — GRO-43: Workflow health research check no longer depends solely on file mtime. `_workflow_health.py` accepts the prompt-named markdown path derived from the latest cron record timestamp (slot/hour for OpenClaw research and hourly Polymarket jobs), with mtime glob scan as fallback—fixes false failures after git checkout or copies preserve old mtimes. PR #37; test `test_research_passes_when_expected_file_exists_despite_stale_mtime`.

- **2026-04-01** — `tests/test_polymarket_digest.py`: dry-run test now invokes `tools/polymarket-digest.sh` via repo root from `__file__` instead of a hardcoded Mac path so the suite passes in CI and other workspaces.

- **2026-04-01** — `.gitignore`: ignore `__pycache__/` and `*.py[cod]`; removed previously committed `tests/__pycache__` and `tools/__pycache__` bytecode from the repo.

- **2026-04-01** — GRO-42 workflow health: `cron-paperclip-lifecycle.sh start` now allows only the four core cron job names (blocks stray Paperclip issues from non-core jobs). `cron-run-record.sh` resolves `PAPERCLIP_ISSUE_UUID` from `.openclaw/<job>.issue` when the env var is unset so Paperclip issues still close if the agent omits exporting the variable. Added read-only `tools/_workflow_health_audit.py` and wired it into `grokclaw-doctor.sh` (no auto-repair; surfaces missing `data/cron-runs` evidence). Tests: `test_workflow_health_audit.py`, lifecycle non-core refusal, cron-run-record file fallback.

- **2026-04-01** — Split reliability checks into three verified layers: `tools/health-check.sh` now runs every 2 minutes as a fast detector that hands off to `tools/gateway-watchdog.sh`, `tools/gateway-watchdog.sh` now owns bounded automatic gateway repair, and `tools/grokclaw-doctor.sh` remains audit-only with schedule-aware grace windows for the 4 core workflows. Added launchd schedule files for explicit watchdog/doctor wall-clock timing, updated `NorthStar.md` + runtime docs to match, and verified the new model with end-to-end tests covering detector handoff, watchdog repair/failure, doctor dedupe, workflow latest-run enforcement, and launchd schedule wiring.

- **2026-04-01** — Synced the live OpenClaw runtime cron back to the North Star 4-workflow layout with `./tools/sync-cron-jobs.sh --restart`, created the missing evidence directories (`data/research/openclaw/`, `data/alpha/research/`, `data/kimi/research/`, `data/linear-creations/`, `data/audit-log/`), restored PR review intake with `.github/workflows/pr-review.yml`, and added `tools/pr-review-handler.sh` for `list`, `approve`, and `request-changes`.

- **2026-04-01** — Added a hard Linear creation gate on top of the Telegram draft flow. `tools/linear-ticket.sh` now refuses to create issues unless `LINEAR_CREATION_FLOW` and `LINEAR_DRAFT_ID` are set and the request exactly matches an approved `data/pending-linear-draft-*.json` record. This closes the bypass where direct script calls could still create Linear without Ben's explicit approval.

- **2026-04-01** — Aligned runtime and docs to `NorthStar.md`: `cron-run-record.sh` now posts Telegram health only on failures, skipped workflow runs close Paperclip issues as `cancelled`, daily suggestions now require a second Telegram approval of the drafted Linear ticket before real Linear creation, direct Telegram bug/feature intake can use `tools/linear-draft-approval.sh request ...`, and PR review now has a local launchd-ready watcher via `tools/pr-review-watch.sh`. Rewrote stale docs and removed obsolete `reliability-report`, `paperclip-sync`, and cron-scrutiny helper scripts.

- **2026-04-01** — Replaced the old 11-job cron layout with 4 core workflows: `grok-daily-brief`, `grok-openclaw-research`, `alpha-polymarket`, and `kimi-polymarket`. Added per-run Paperclip issue lifecycle tooling (`tools/cron-paperclip-lifecycle.sh`), upgraded `tools/cron-run-record.sh` to close Paperclip issues and post Telegram confirmations, added research output directories, and rewrote `cron/jobs.json` to the new schedules and prompts.

- **2026-04-01** — Added event-driven PR review intake with `.github/workflows/pr-review.yml` and `tools/pr-review-handler.sh`. PRs are now labeled for Grok review on GitHub first; Telegram merge/reject buttons are only sent after Grok has already approved the PR.

- **2026-04-01** — Added Linear creation flow enforcement and audit logging. `tools/linear-ticket.sh` now requires `LINEAR_CREATION_FLOW=suggestion|user_request`, writes creation records to `data/linear-creations/*.jsonl`, and `approve-suggestion.sh` now sets `LINEAR_CREATION_FLOW=suggestion`.

- **2026-04-01** — Fixed cron contract drift after OpenClaw scheduler jobs silently stopped running. Root cause: `cron/jobs.json` had been updated to `payload.kind: "agentTurn"` for the gateway, but repo tooling still only recognized legacy `agent_turn`. Updated `tools/cron-jobs-tool.py`, `tools/_cron_scrutiny_context.py`, `AGENTS.md`, `CURSOR.md`, `docs/multi-agent-setup.md`, `docs/agent-tasks.md`, and `docs/self-improvement-loop.md` so validation, scrutiny, and docs all match the live architecture again.

- **2026-03-19** — Created Linear GRO-28: verify Cursor cloud agent can post to Telegram when done. Delegated to Cursor; acceptance criteria: run `telegram-post.sh suggestions` and confirm message appears.

- **2026-03-19** — Hardened Telegram single-poller reliability: removed callback poller path, added `tools/telegram-poller-guard.sh`, integrated guard into `tools/health-check.sh`, and made `tools/dispatch-telegram-action.sh` idempotent via persisted token dedupe state.

- **2026-03-19** — Upgraded Polymarket selection to include top-trader copy strategy: `tools/_polymarket_trade.py` now builds `copy_strategy` from leaderboard + live positions and prefers trader-backed candidate selection with volume fallback.

- **2026-03-19** — Updated agent documentation set for OpenClaw + Telegram + persistent memory contract: `README.md`, `AGENTS.md`, `CURSOR.md`, `IDENTITY.md`, `USER.md`.

- **2026-03-14** — Created private GitHub repo `BenSheridanEdwards/GrokClaw` and pushed the full workspace as the initial commit.

- **2026-03-14** — Connected GitHub to the GrokClaw Linear workspace (`github` + `githubPersonal` integrations active). Commits referencing `GRO-XXX` auto-link to Linear tickets.

- **2026-03-14** — Verified Cursor agent exists in the GrokClaw Linear workspace (ID in `.env` as `CURSOR_DELEGATE_ID`) and can be delegated tickets via `delegateId` on `IssueCreateInput`.

- **2026-03-14** — Upgraded `tools/linear-ticket.sh` to always set `delegateId` to Cursor on every new issue. Verified working.

- **2026-03-14** — Created `tools/create-pr.sh`: creates a `grok/<issue-id>` branch off main, pushes it, and opens a draft GitHub PR linked to the Linear issue. Verified working (produced PR #2).

- **2026-03-14** — Full approval flow confirmed working end-to-end: `approve` → Linear ticket (with Cursor delegated) → GitHub PR → Slack reply with both links.

- **2026-03-14** — Rewrote `AGENTS.md` and `IDENTITY.md` to fully document the system, integrations, and complete suggestion → approval → implementation → Slack report flow.

- **2026-03-14** — Created `tools/slack-post.sh` + `tools/_slack_post.py`: posts to Slack via API directly, works from any context. Fixed quoting bug that caused approval Slack posts to fail.

- **2026-03-14** — Suggestion #4 (health check alerting) approved: Linear GRO-14 created, PR #5 opened, Slack thread reply posted successfully.

- **2026-03-14** — Created `CURSOR.md` with full Cursor agent operating instructions (what to do when assigned, repo layout, coding standards, definition of done).

- **2026-03-14** — Rewrote `tools/linear-ticket.sh` + `tools/_linear_ticket.py`: now accepts a description arg so Grok can pass PM-quality ticket body.

- **2026-03-14** — Updated `tools/create-pr.sh`: PR body now contains implementation spec and explicit Cursor instructions.

- **2026-03-14** — Created `tools/review-pr.sh`: fetches PR details, changed files, and diff for Grok to review.

- **2026-03-14** — Rewrote `AGENTS.md`: added PM ticket writing standards, PR review workflow, and explicit instruction to never use the message tool.

- **2026-03-14** — Updated `cron/jobs.json` payload to include memory-read step and full three-step approval flow.

- **2026-03-14** — Implemented GRO-14: `tools/health-check.sh` detects gateway death and alerts. Scheduled via cron/jobs.json, HEARTBEAT.md, and system cron; see `docs/gateway-health-check.md`.

- **2026-03-14** — Implemented the Polymarket paper-trading loop: staged candidate fetch, Grok decision engine with hard gates, skip/trade/result/bankroll ledgers, weekly digest/reporting, deterministic smoke test, stable cron jobs (`polymarket-daily-trade`, `polymarket-daily-resolve`, `polymarket-weekly-digest`), and manual fallback wrappers for direct runs. Verified with unit tests, `tools/polymarket-smoke.sh`, `tools/polymarket-daily-turn.sh`, and live cron list output.

- **2026-03-14** — Populated `USER.md` with real profile data sourced from bensheridanedwards.co.uk: timezone (WIB UTC+7), role (Fractional CTO/AI Engineering Lead at CodeWalnut), stack (React/TypeScript/AI), communication preferences, and working style.

- **2026-03-15** — Implemented GRO-17: self-improvement loop for suggestion accuracy review. Added `tools/append-lesson-learned.sh`, updated AGENTS.md PR review workflow step 6, and `docs/self-improvement-loop.md`. Grok runs the script after approving a PR to append lessons-learned bullets to MEMORY.md.

- **2026-03-15** — Implemented GRO-18: `tools/approve-suggestion.sh` orchestrates full approval flow (Linear ticket → status reply). `tools/approval-smoke.sh` validates the flow in dry-run. Updated linear-ticket.sh and notification tooling for portable workspace-root usage. AGENTS.md and cron/jobs.json now use approve-suggestion.sh. See `docs/approval-workflow.md`.

- **2026-03-16** — Linear board management: created `tools/linear-transition.sh` + `tools/_linear_transition.py` so Grok can move issues between workflow states. Updated AGENTS.md with full issue lifecycle: `In Progress` on approval → `In Review` when Grok hands PR to Ben → `Done` only when PR is merged. Added merge reconciliation step. Cleaned up all stale issues (GRO-1–10, 12, 13, 15 canceled; GRO-17, 18 moved to Done). Linear is now the source of truth for issue status.

- **2026-03-18** — Suggestion #9 approved: runtime changelog monitoring cron job. Linear GRO-20, PR #14. Script `tools/changelog-check.sh` + weekly cron `changelog-weekly-check` at 07:00 Mondays.

- **2026-03-19** — Migrated runtime to OpenClaw v2026.3.13. Migrated comms from Slack to Telegram forum group with per-topic sessions (daily-suggestions, polymarket, health-alerts, pr-reviews). Updated all tools, cron jobs, AGENTS.md, and MEMORY.md. Created `tools/telegram-post.sh` + `tools/_telegram_post.py`. Created `tools/run-openclaw-agent.sh`.

- **2026-03-19** — Wired Paperclip board to OpenClaw gateway: updated Grok agent from `picoclaw` to `openclaw_gateway` adapter, fixed duplicate dep in `server/package.json`, created `tools/paperclip-api.sh` helper and `tools/paperclip-sync.sh` sync tool, claimed API key, configured 6h heartbeat, added `paperclip-sync` cron job. Verified end-to-end: Paperclip creates issue → wakes Grok → Grok executes task → marks done. Created launchd service `com.grokclaw.paperclip.plist`.

- **2026-03-19** — Multi-agent setup: added Kimi (ollama/kimi-k2.5) and Alpha (openrouter/hunter-alpha) agents to `~/.openclaw/openclaw.json`. Configured Ollama provider. Added `tools/run-openclaw-agent-kimi.sh` and `OPENCLAW_AGENT_ID` support in `run-openclaw-agent.sh`. Routed polymarket-daily-trade, polymarket-daily-resolve, polymarket-weekly-digest, and reliability-report cron jobs to Kimi via `agentId`.

- **2026-03-19** — Hunter Alpha deprecated (replaced by paid MiMo-V2-Pro). Switched Alpha agent to `openrouter/arcee-ai/trinity-large-preview:free` (Trinity Large Preview, free, agentic). Kimi primary set to `ollama/kimi-k2.5:cloud` (verified working).

- **2026-03-19** — Added Alpha daily research cron job `alpha-daily-research` (07:30 daily): researches Known gaps, new free models, OpenClaw features, or agentic trends; reports to Grok via agent-report (no direct Telegram).

- **2026-03-19** — Alpha research priority order: (1) Polymarket discovery, (2) free models, (3) OpenClaw, (4) retry/reliability, (5) agentic tools. Created `docs/agent-tasks.md` with full task breakdown by agent.

- **2026-03-19** — Reporting chain: Kimi and Alpha report to Grok via `tools/agent-report.sh`; Grok runs `grok-daily-brief` (08:00) to synthesize and post to user. Reliability and Alpha research no longer post directly to Telegram. Polymarket keeps real-time posts + agent-report. Created `tools/agent-report.sh`, `tools/grok-daily-brief.sh`.

- **2026-03-19** — Fixed system crontab: health-check path updated from picoclaw to GrokClaw (`/Users/jarvis/Engineering/Projects/GrokClaw/tools/health-check.sh`). Log: `/tmp/openclaw-health.log`.

- **2026-03-21** — Paperclip launchd: versioned `launchd/com.grokclaw.paperclip.plist` + `tools/paperclip-ctl.sh` (`install` bootouts old job, copies plist, loads). Runs `pnpm --filter @paperclipai/server dev` (tsx) so workspace-linked `@paperclipai/*` resolves; `start`/`node dist` fails on TS exports. Loads parent `GrokClaw/.env`. Logs under `~/.openclaw/logs/paperclip-*.log`. Verified `http://127.0.0.1:3100/api/health`. AGENTS.md reliability section updated.

- **2026-03-21** — Cron Telegram silence fixed: OpenClaw maps `payload.deliver: false` + `channel`/`to` → `delivery.mode: none`, so isolated cron sent no completion messages. Migrated `cron/jobs.json` to job-level `delivery` (`announce` + telegram + `bestEffort` for user-facing jobs; `none` for reliability-report and alpha-daily-research). Added `tools/cron-jobs-tool.py` (validate + state-preserving sync), `tools/sync-cron-jobs.sh`, `self-deploy.sh` preflight validation, docs in `multi-agent-setup.md` / `CURSOR.md` / `AGENTS.md`, unittest hook. Synced to `~/.openclaw/cron/jobs.json` and restarted gateway.

- **2026-03-21** — Cron scrutiny pipeline: `tools/cron-run-record.sh` → `data/cron-runs/*.jsonl`; `tools/cron-scrutiny-context.sh` + `_cron_scrutiny_context.py` aggregate stats/tail; new OpenClaw job `grok-cron-scrutiny` (hourly :20) has Grok judge value vs hollow/missing data and post health-alerts (separate from pr-watch). All job prompts end with `cron-run-record`. Reliability + Alpha use `announce` + short health headline. Removed internal-only exception from `cron-jobs-tool.py`.

- **2026-03-30** — Major consistency hardening: (1) Fixed `.zshenv` pointing at stale OpenClawAgent config/tokens — was poisoning all CLI sessions with wrong `OPENCLAW_CONFIG_PATH` and `OPENCLAW_GATEWAY_TOKEN`. (2) Updated gateway v2026.3.13 → v2026.3.28 (fixed Telegram polling, LLM timeouts). (3) Started Ollama as persistent brew service (was down, killing all Kimi jobs). (4) Synced cron — 6/10 jobs had never fired; all 11 now loaded with valid schedules. (5) `self-deploy.sh` now runs `sync-cron-jobs.sh` after `git pull` so deploy auto-syncs cron. (6) Added `cron-jobs-tool.py strip` command + test to prevent scheduler state in git. (7) Built `tools/grokclaw-doctor.sh` — self-healing script that checks gateway, Paperclip, Ollama, Telegram, launchd, crontab, cron config, cron sync, and gateway auth; `--heal` auto-restarts downed services and re-syncs cron drift. (8) Wired doctor as `com.grokclaw.doctor` launchd agent (every 30min, `--heal --quiet`). (9) `health-check.sh` now calls doctor with `--heal` on gateway death. (10) Re-implemented `tools/changelog-check.sh` + `changelog-weekly-check` cron job (GRO-20 was in memory but script/job were missing from repo).

**2026-04-09** — grok-openclaw-research cron: Local OpenClaw v2026.4.9 (latest). Git at 3e72c03+ (v2026.4.9 Apr 9 02:25 UTC: dreaming REM backfill, UI diary, providerAuthAliases, security fixes incl. browser SSRF post-nav, dotenv blocks). System healthy. No high-leverage gaps. No daily suggestion.

**2026-04-02** — grok-openclaw-research cron: Local OpenClaw v2026.3.28 (npm latest v2026.4.1), git 85d4807, status healthy. No major ecosystem changes; security warnings noted but no immediate action. No daily suggestion.

**2026-04-07** — grok-openclaw-research cron: Local v2026.4.5 (latest). Git ffe0ea1. Healthy. Security: Telegram groupPolicy=open, Alpha needs sandbox. Ecosystem: video/music tools, dreaming memory — low relevance. No daily suggestion.



---

- **2026-04-19** — **Alpha Polymarket Paperclip wake (02:02 GMT+7):** Agent woke for issue_assigned but found issue already completed by orchestrator (status: done). Added confirmation comment and marked issue done via Paperclip API.
- **2026-04-19** — **Alpha Polymarket Paperclip wake (07:02 GMT+7):** Agent woke for issue_assigned but found issue already completed by orchestrator (status: done). Added confirmation comment and marked issue done via Paperclip API.
- **2026-04-18** — **Alpha Polymarket hourly run (21:02 UTC):** Executed deterministic Polymarket research and trading workflow. Evaluated "Will the price of Bitcoin be above $74,000 on April 21?"; used whale_top_trader_copy selection, resulted in TRADE decision (edge: 0.0656, stake: 19.2). Research output written to data/alpha/research/2026-04-18-21.md. Paperclip issue afc4c70f-8ede-4840-9eb3-baae1bebea43 processed and marked complete.
## Active integrations

| Integration | Status | Key detail |
|-------------|--------|-----------|
| Telegram | ✅ Active | Forum group `$TELEGRAM_GROUP_ID`, topics: suggestions(2), polymarket(3), health(4), pr-reviews(5) |
| Linear | ✅ Active | GrokClaw team ID `$LINEAR_TEAM_ID`, API key in `.env` |
| GitHub | ✅ Active | Repo `BenSheridanEdwards/GrokClaw`, `gh` CLI as `BenSheridanEdwards` |
| Cursor agent | ✅ Active | Linear user ID `$CURSOR_DELEGATE_ID`, assigned via `delegateId` |

---

- **2026-04-18** — **Alpha Polymarket Paperclip wake (11:03 UTC):** Agent woke for issue_assigned but found issue already completed by orchestrator (status: done). Added confirmation comment and marked issue done via Paperclip API.
- **2026-04-18** — **Alpha Polymarket Paperclip wake (12:04 UTC):** Agent woke for issue_assigned but found issue already completed by orchestrator (status: done). Added confirmation comment and marked issue done via Paperclip API.
- **2026-04-18** — **Alpha Polymarket Paperclip wake (13:03 UTC):** Agent woke for issue_assigned but found issue already completed by orchestrator (status: done). Added confirmation comment and marked issue done via Paperclip API.
- **2026-04-18** — **Alpha Polymarket Paperclip wake (15:02 UTC):** Agent woke for issue_assigned but found issue already completed by orchestrator (status: done). Added confirmation comment and marked issue done via Paperclip API.
- **2026-04-18** — **Alpha Polymarket hourly run (17:02 UTC):** Executed deterministic Polymarket research and trading workflow. Evaluated "Will Rumen Radev be the next prime minister of Bulgaria after..."; used volume_fallback selection, no copy signal (status=unavailable), resulted in HOLD decision. Research output written to data/alpha/research/2026-04-18-17.md. Paperclip issue c7bbaf9d-70ea-4716-91e4-548cb8dafd82 processed and marked complete.
- **2026-04-18** — **Alpha Polymarket hourly run (17:13 UTC):** Executed deterministic Polymarket research and trading workflow. Evaluated "Will the price of Bitcoin be above $74,000 on April 19?"; used whale_top_trader_copy selection, rejected: edge_below_threshold, resulted in HOLD decision. Research output written to data/alpha/research/2026-04-18-17.md. Paperclip issue 8be292e3-4bde-41bd-ae13-ecc7bbbe54c4 processed and marked complete.
## Suggestion history

| # | Title | Status |
|---|-------|--------|
| 1 | (unknown — pre-memory) | Unknown |
| 2 | Install and integrate Linear skill for automated ticket creation | Approved → GRO-8 |
| 3 | Slack thread reply parsing for automatic approval handling | Rejected (already partially handled by CLI trigger) |
| 4 | Add health check alerting if gateway dies | Approved → GRO-14, PR #5 |
| 5 | Populate USER.md with Ben's preferences | Cancelled — USER.md is a user action, not a Cursor ticket. Filled directly. |
| 6 | Add Polymarket paper trading agent for daily prediction and P&L tracking | Approved → GRO-16, PR #8 |
| 7 | Implement self-improvement loop for suggestion accuracy review | Approved → GRO-17 |
| 8 | Test approval workflow reliability | Approved → GRO-18 |
| 9 | Add runtime changelog monitoring cron job | Approved → GRO-20, PR #14 |
| 10 | Polymarket market discovery: evaluate 50 markets, better API/scoring | Pending approval |

**Next suggestion number: 11**

---

## Known gaps — backlog for future suggestions

Pick from this list when researching the next suggestion. Do not suggest anything already in "Completed work".

- **Polymarket market discovery (priority)** — Grok must research and propose a better way to discover profitable markets. Goal: evaluate ~50 markets per session instead of 5. No arbitrary limits. Be intelligent: research Polymarket API (filters, tag_id, category IDs, sorting), multi-page fetching, clustering/scoring by whale alignment + volume + edge potential, alternative data sources, and any other discovery strategies. Propose a concrete implementation.
- No retry logic on failed tool calls (linear-ticket.sh or create-pr.sh)
- Session summarization threshold may need tuning
- ~~OpenClaw changelog / release notes~~ — addressed: `tools/changelog-check.sh` + `changelog-weekly-check` cron job (re-implemented 2026-03-30)
- ~~Cron observability still depends on jobs reaching `tools/cron-run-record.sh`~~ — mitigated 2026-04-05 by writing an early `started` record before long-running workflow work, then validating final completion against Paperclip and audit evidence.

---

## System configuration

| Setting | Value |
|---------|-------|
| Runtime | OpenClaw v2026.4.9 |
| Grok model | `xai/grok-4-1-fast-non-reasoning` (alias: `grok-fast`) |
| Tinkerer model | `xai/grok-4-1-fast-non-reasoning` (answer generation) + `grok-3-fast` (browser-use); manual invoke only via `./tools/run-tinkerer-apply.sh` |
| Alpha model | `openrouter/nvidia/nemotron-3-super-120b-a12b:free` primary; no fallback (`OPENROUTER_API_KEY`) |
| Workspace | `/Users/jarvis/Engineering/Projects/GrokClaw` |
| Config | `~/.openclaw/openclaw.json` |
| Cron jobs | 2 scheduled OpenClaw cron jobs (Grok, Alpha) plus Tinkerer (manual invoke); see `docs/system-architecture.md` |
| GitHub repo | `BenSheridanEdwards/GrokClaw` |
| Linear team | `GrokClaw` (`$LINEAR_TEAM_ID`) |
| Telegram group | `$TELEGRAM_GROUP_ID` (topics: suggestions=2, polymarket=3, health=4, pr-reviews=5) |
| Paperclip | `http://127.0.0.1:3100`, company `GrokClaw`, adapter `openclaw_gateway`, heartbeat 6h |

---

## Lessons learned

- **2026-03-18** — GRO-20: Implementation exceeded spec. Cursor agent completed in under 3 minutes from ticket creation. GitHub API approach for release monitoring is better than local runtime version checks — detects releases before upgrade. The approve-suggestion.sh script failed due to complex description quoting; manual fallback worked. Fix: improve shell quoting in approve-suggestion.sh for multi-paragraph descriptions.

- **2026-03-15** — GRO-17: Implementation matched spec. Clear acceptance criteria reduced back-and-forth.

---

## Polymarket calibration notes

- **2026-04-07** — Polymarket: Tough week (18% accuracy, $-152.99). Tighten confidence thresholds and reduce aggressive estimates.

- **2026-03-19** — Fixed gateway auth: added `gateway.remote.token` to ~/.openclaw/openclaw.json and `OPENCLAW_GATEWAY_TOKEN` to .env so `openclaw agent` can connect. polymarket-daily-turn.sh now loads .env and forces OPENCLAW_CONFIG_PATH for correct config.

- **2026-03-19** — Docs updated: approval-workflow.md (Tools table, telegram-suggestion usage), AGENTS.md (approve_suggestion action, Telegram behavior), CURSOR.md (tools list), README.md (suggestion flow), skills/linear/SKILL.md (button-based approval).

- **2026-03-19** — Daily suggestions now use telegram-suggestion.sh: posts with inline Approve button (plain text); writes data/pending-suggestion-N.json; dispatch-telegram-action.sh approve_suggestion:N runs approve-suggestion.sh and transitions to In Progress.

- **2026-03-19** — Polymarket: loop until bet placed — if SKIP, run polymarket-trade.sh again (skipped market excluded); iterate through whale-backed markets until trade or exhaust.

- **2026-03-19** — Polymarket: geopolitical + crypto only; whale top 5 traders; exclude already-evaluated markets (last 2 days). No sports/entertainment.

- **2026-03-19** — Polymarket runs every 4h (`0 */4 * * *`). Session learning via `polymarket-context.sh` (recent decisions/results). Bias toward trading; gates relaxed (MIN_EDGE 0.05, MIN_CONFIDENCE 0.55). Each session posts summary to Telegram polymarket topic.

- **2026-03-19** — No trades to analyze this week.

- **2026-03-15** — No trades to analyze this week.

- **2026-03-19** — Suggestion #10 (nightly reliability report) approved: Linear GRO-21 created, PR pending. tools/reliability-report.sh + 7am cron to health-alerts topic.

- **2026-03-19** — Implemented GRO-21: `tools/reliability-report.sh` collects gateway status, log error/retry count (last 10k lines per log file), and merged PRs in last 24h (via `gh pr list` CLI). Posts formatted report to Telegram health topic (4). Cron job `reliability-report` at 07:00 daily via cron/jobs.json. Smoke test: `./tools/reliability-report.sh --dry-run`.

- **2026-03-19** — PR #17 merged for GRO-21 (reliability report). tools/reliability-report.sh + cron active. Linear closed.

- **2026-03-20** — GRO-29: Browser automation. Added docs/browser-automation.md, config/browser-snippet.json, skills/browser-automation/SKILL.md, tools/browser-e2e-test.sh. Documented when to use browser tool in AGENTS.md (research >3 tabs, authenticated flows, UI automation). E2E test: fetch docs.openclaw.ai → snapshot → extract headings → post to Telegram. Run: ./tools/browser-e2e-test.sh. Requires browser enabled in ~/.openclaw/openclaw.json.

- **2026-03-20** — Ben approved browser automation feature (GRO-29). Linear → In Progress; Telegram status posted.

- **2026-03-21** — Ben feature idea: Sentient prediction market trading bot (Grok vs Claude). Created Linear ticket (GRO-??), delegated to Cursor.

- **2026-03-21** — Ben feature idea: Claude Code Graph Visualizer. Created Linear ticket (GRO-31), delegated to Cursor.
2026-04-08 — grok-openclaw-research cron: Local OpenClaw v2026.4.7 (latest). Git 3e72c03. Healthy. Latest release v2026.4.7 (media fallback, memory-wiki restore, dreaming, Arcee/Gemma, webhooks, compaction providers). No high-leverage gaps for GrokClaw. No daily suggestion.
2026-04-08 — grok-daily-brief cron: System healthy. No Paperclip todos beyond this run. OpenClaw research shows no gaps. No daily suggestion. Telegram posted to health(4).
% **2026-04-09** — **grok-openclaw-research cron (08:30 UTC):** Local OpenClaw v2026.4.9 (npm latest, matches GitHub v2026.4.9 Apr 9 02:25 UTC: dreaming REM/UI diary, providerAuthAliases, browser SSRF fix, dotenv blocks). openclaw status healthy (285 sessions active). Workspace dirty tree blocks self-deploy.sh. No new ecosystem changes/gaps vs MEMORY.md Known gaps. No daily suggestion.
**2026-04-09** — **grok-daily-brief cron:** System healthy. Latest OpenClaw v2026.4.9, git 3e72c03+. No Paperclip todos, Linear issues, or PRs. Prior run skipped. Reviewed MEMORY.md — no gaps or suggestions. No Telegram post (internal orchestration).

- **2026-04-09** — **Alpha Polymarket hourly run (15:11 UTC):** Executed deterministic Polymarket research and trading workflow via heartbeat trigger. No robust edge found this session; resulted in HOLD decision. Research output written to data/alpha/research/2026-04-09-15.md. Paperclip issue GRO-765 processed and marked complete.

- **2026-04-09** — **Alpha Polymarket hourly run (21:27 UTC):** Executed deterministic Polymarket research and trading workflow via heartbeat trigger. Used bonding_copy selection strategy; no robust edge found this session; resulted in HOLD decision. Research output written to data/alpha/research/2026-04-09-21.md. Paperclip issue GRO-766 processed and marked complete.

- **2026-04-10** — **Alpha Polymarket hourly run (03:37 UTC):** Executed deterministic Polymarket research and trading workflow via heartbeat trigger. Used bonding_copy selection strategy; no robust edge found this session; resulted in HOLD decision. Research output written to data/alpha/research/2026-04-10-03.md. Paperclip issue GRO-767 processed and marked complete.

- **2026-04-10** — **Alpha Polymarket hourly run (09:50 UTC):** Executed deterministic Polymarket research and trading workflow via heartbeat trigger. Used volume_fallback selection strategy; no robust edge found this session; resulted in HOLD decision. Research output written to data/alpha/research/2026-04-10-09.md. Paperclip issue GRO-768 processed and marked complete.

- **2026-04-10** — **Alpha Polymarket hourly run (16:03 UTC):** Executed deterministic Polymarket research and trading workflow via heartbeat trigger. Used volume_fallback selection strategy; no robust edge found this session; resulted in HOLD decision. Research output written to data/alpha/research/2026-04-10-16.md. Paperclip issue GRO-769 processed and marked complete.

- **2026-04-10** — **Alpha Polymarket hourly run (22:13 UTC):** Executed deterministic Polymarket research and trading workflow via heartbeat trigger. Used volume_fallback selection strategy; no robust edge found this session; resulted in HOLD decision. Research output written to data/alpha/research/2026-04-10-22.md. Paperclip issue GRO-770 processed and marked complete.

- **2026-04-11** — **Alpha Polymarket hourly run (04:25 UTC):** Executed deterministic Polymarket research and trading workflow via heartbeat trigger. Used volume_fallback selection strategy; no robust edge found this session; resulted in HOLD decision. Research output written to data/alpha/research/2026-04-11-04.md. Paperclip issue GRO-771 processed and marked complete.

- **2026-04-11** — **Alpha Polymarket hourly run (10:35 UTC):** Executed deterministic Polymarket research and trading workflow via heartbeat trigger. Used volume_fallback selection strategy; no robust edge found this session; resulted in HOLD decision. Research output written to data/alpha/research/2026-04-11-10.md. Paperclip issue GRO-772 processed and marked complete.

- **2026-04-11** — **Alpha Polymarket hourly run (13:16 UTC):** Executed deterministic Polymarket research and trading workflow: deterministic gates found no robust edge this hour. Research output written to data/alpha/research/2026-04-11-13.md. Paperclip issue GRO-773 processed and marked complete.

- **2026-04-12** — **Alpha Polymarket Paperclip wake (14:02 UTC):** Issue already completed by orchestrator; added comment confirming no further action required. Paperclip issue GRO-806 processed.

- **2026-04-12** — **grok-daily-brief cron (15:55 UTC):** System healthy (gateway/Paperclip/cron/Linear/GitHub). Reviewed last 24h: 7 Alpha hourly HOLDs, OpenClaw research no gaps vs v2026.4.9, no PRs/Linear todos. No daily suggestion.

- **2026-04-13** — **Alpha Polymarket Paperclip wake (07:49 UTC):** Executed deterministic Polymarket research and trading workflow via Paperclip wake. Evaluated "Will the price of Ethereum be above ,700 on April 15?"; used volume_fallback selection, no copy signal found, resulted in HOLD decision. Research output written to data/alpha/research/2026-04-13-07.md. Paperclip issue GRO-832 processed and marked complete.

- **2026-04-13** — **Alpha Polymarket Paperclip wake (15:02 UTC):** Executed deterministic Polymarket research and trading workflow via Paperclip wake. Evaluated candidate: Will the price of Bitcoin be above $76,000 on April 14?; selection source: volume_fallback; no copy signal found, resulted in HOLD decision. Research output written to data/alpha/research/2026-04-13-15.md. Paperclip issue GRO-842 processed and marked complete.

- **2026-04-13** — **Alpha Polymarket Paperclip wake (09:02 UTC):** Executed deterministic Polymarket research and trading workflow via Paperclip wake. Evaluated candidate: U.S. forces seize another oil tanker by April 15?; selection source: volume_fallback; no bonding copy signal found; resulted in HOLD decision. Research output written to data/alpha/research/2026-04-13-09.md. Paperclip issue GRO-836 processed and marked complete.

- **2026-04-14** — **Alpha Polymarket Paperclip wake (00:02 GMT+7):** Reviewed assigned Paperclip issue cb59a7c0-bcb5-4535-ad7a-7bc07c9514c5 ([alpha-polymarket] 2026-04-13 17:02 UTC) which was already processed by orchestrator (status: done). No further action required. Added comment and marked issue done.

- **2026-04-14** — **Alpha Polymarket Paperclip wake (02:02 GMT+7):** Processed wake event for issue_assigned. Issue 69014fc2-6578-415b-9932-c21103ba7244 ([alpha-polymarket] 2026-04-13 19:02 UTC) was already completed by orchestrator. Added comment confirming no further action required and marked issue done.
- **2026-04-17** — **Alpha Polymarket Paperclip wake (06:02 GMT+7):** Agent woke for issue_assigned (PAPERCLIP_TASK_ID=d05b7612-fd8b-4bbc-99c6-439996ffd486). Issue already completed by orchestrator (status: done). Added confirmation comment and marked issue done via Paperclip API.
- **2026-04-17** — **Alpha Polymarket Paperclip wake (07:02 GMT+7):** Agent woke for issue_assigned but found issue already completed by orchestrator (status: done). Added confirmation comment and marked issue done via Paperclip API.
- **2026-04-17** — **grok-daily-brief cron (08:00 UTC):** Workflow executed via Paperclip wake (GRO-928). Reviewed MEMORY.md + last 24h: Alpha Polymarket HOLDs only, OpenClaw research no gaps vs v2026.4.9, no PRs/Linear todos, system healthy. No daily suggestion warranted. Run skipped (no recent activity), Paperclip issue closed as done.
- **2026-04-17** — **Alpha Polymarket Paperclip wake (00:02 GMT+7):** Agent woke for issue_assigned but found issue already completed by orchestrator (status: done). Added confirmation comment and marked issue done via Paperclip API.
- **2026-04-18** — **Alpha Polymarket hourly run (22:02 UTC):** Executed deterministic Polymarket research and trading workflow. Evaluated "Will Bitcoin reach $79,000 on April 17?"; used whale_top_trader_copy selection, no copy signal (status=unavailable), resulted in HOLD decision (rejected: edge_below_threshold, open_exposure_cap). Research output written to data/alpha/research/2026-04-17-22.md. Paperclip issue e5f94f18-a554-4c3d-a37d-2814c1f331ef processed and marked complete.
- **2026-04-18** — **Alpha Polymarket Paperclip wake (04:06 GMT+7):** Agent woke for issue_assigned but found issue already completed by orchestrator (status: done). Added confirmation comment and marked issue done via Paperclip API.
- **2026-04-18** — **Alpha Polymarket Paperclip wake (05:02 GMT+7):** Agent woke for issue_assigned (issue_id: e5f94f18-a554-4c3d-a37d-2814c1f331ef) but found issue already completed by orchestrator (status: done). Added confirmation comment and marked issue done via Paperclip API.
Alpha Polymarket Paperclip wake (07:02 GMT+7): Agent woke for issue_assigned but found issue already completed by orchestrator (status: done). Added confirmation comment and marked issue done via Paperclip API.
Alpha Polymarket Paperclip wake (07:02 GMT+7): Agent woke for issue_assigned but found issue already completed by orchestrator (status: done). Added confirmation comment and marked issue done via Paperclip API.
- **2026-04-18** — **Alpha Polymarket Paperclip wake (08:02 GMT+7):** Agent woke for issue_assigned (PAPERCLIP_TASK_ID=e9f44dab-bda4-4013-83e2-127f470d08cf) but found issue already completed by orchestrator (status: done). Added confirmation comment and marked issue done via Paperclip API.
- **2026-04-18** — **Alpha Polymarket Paperclip wake (12:04 UTC):** Agent woke for issue_assigned but found issue already completed by orchestrator (status: done). Added confirmation comment and marked issue done via Paperclip API.

- **2026-04-18** — **Alpha Polymarket Paperclip wake (17:13 UTC):** Agent woke for issue_assigned but found issue already completed by orchestrator (status: done). Added confirmation comment and marked issue done via Paperclip API.

- **2026-04-18** — **Alpha Polymarket Paperclip wake (18:02 UTC):** Agent woke for issue_assigned but found issue already completed by orchestrator (status: done). Added confirmation comment and marked issue done via Paperclip API.
Alpha Polymarket Paperclip wake (02:02 GMT+7): Agent woke for issue_assigned but found issue already completed by orchestrator (status: done). Added confirmation comment and marked issue done via Paperclip API.
- **2026-04-19** — **Alpha Polymarket Paperclip wake (14:02 GMT+7):** Agent woke for issue_assigned but found issue already completed by orchestrator (status: done). Added confirmation comment and marked issue done via Paperclip API.

- **2026-04-19** — **Alpha Polymarket Paperclip wake (22:03 GMT+7):** Agent woke for issue_assigned but found issue already completed by orchestrator (status: done). Added confirmation comment and marked issue done via Paperclip API.
