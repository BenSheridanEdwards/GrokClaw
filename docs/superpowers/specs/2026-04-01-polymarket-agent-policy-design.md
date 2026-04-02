# Polymarket Agent Policy Design

Date: 2026-04-01

## Goal

Keep Alpha and Kimi on the same Polymarket toolchain while giving them different trading policies and separate bankrolls.

The desired end state is:

- Kimi keeps the current market restrictions and continues from the current bankroll history
- Alpha uses the same Polymarket workflow but without the current market-category restriction
- Alpha and Kimi no longer share bankroll state, summaries, or promotion metrics
- `NorthStar.md` and the supporting docs describe this split explicitly

## Current State

Today the market restriction logic lives inside `tools/_polymarket_trade.py`.

Current behavior:

- markets are filtered to geopolitical + crypto only
- sports and entertainment are excluded
- recently evaluated markets are excluded
- the same filtering applies regardless of which agent is running

Today bankroll state is shared through `tools/_polymarket_metrics.py` using a single bankroll file:

- `data/polymarket-bankroll.json`

This means Alpha and Kimi currently share:

- bankroll balance
- P&L history
- drawdown and summary metrics
- promotion gating inputs

## Desired Policy Split

### Kimi

Kimi remains the conservative calibrated agent.

Rules:

- keep the current market restrictions
- keep using the existing bankroll history
- continue excluding recently evaluated markets
- continue using Kimi's own recent trade/decision history to avoid revisiting markets

Operationally this means Kimi is the continuity path for the current paper-trading record.

### Alpha

Alpha becomes the broader exploration agent.

Rules:

- no category restriction on market selection
- still use the same candidate-selection and trading pipeline
- get a brand-new bankroll ledger independent of Kimi
- do not inherit Kimi's recent trade/decision exclusions
- do not use its own repeat-exclusion filter for now; Alpha may revisit markets it evaluated before

Alpha should still respect the general trading mechanics already enforced elsewhere in the toolchain, but it should not inherit Kimi's category filter.

## Design

### 1. Agent-aware policy

The Polymarket toolchain should accept an explicit agent or policy identity.

That identity should drive:

- market filtering behavior
- bankroll file selection
- reporting context where bankroll metrics are shown

Recommendation:

- treat policy as code-owned configuration, not prompt-only guidance
- keep one shared trading pipeline and branch on agent policy at the selection and metrics layers

### 2. Restriction enforcement

Move from implicit shared restriction behavior to explicit agent policy checks.

Recommended behavior:

- Kimi policy: current restricted filter
- Alpha policy: unrestricted category filter

The category restriction should remain inside the Python trading code so prompts cannot silently drift from the real policy.

### 3. Separate bankroll ledgers

Persistent Polymarket state should become agent-scoped anywhere it affects selection, accounting, summaries, or promotion.

Recommended behavior:

- Kimi continues using the current bankroll ledger as the continuity ledger
- Alpha writes to a separate new ledger file
- Alpha starts from the same default starting bankroll the current system uses today

To avoid mixed accounting and shared pending-state races, the implementation should make these state paths agent-aware:

- bankroll ledger
- trade ledger
- decision ledger
- result ledger
- pending trade / staged candidate file
- promotion alert / promotion state file

Recommended shape:

- keep Kimi on the current file paths for continuity
- add Alpha-specific parallel file paths

The implementation should make all reads and writes agent-aware, including:

- current bankroll lookup
- bankroll event recording
- trade/decision/result writes
- pending trade staging and consumption
- summaries and reporting
- any promotion or threshold checks based on bankroll

### 4. Prompt and workflow updates

Alpha and Kimi cron prompts should both continue using the same operational tools, but with language that matches the actual policy:

- Kimi prompt should continue to reflect the restricted strategy
- Alpha prompt should reflect broader market exploration

The prompts should not be the primary enforcement mechanism. They should only describe the code-enforced behavior.

### 5. Repeat-exclusion behavior

Repeat-exclusion policy should diverge by agent:

- Kimi keeps the current behavior and excludes recently evaluated/traded markets using Kimi's own history
- Alpha does not apply a repeat-exclusion filter right now

This is intentionally asymmetric:

- Kimi remains the conservative calibrated agent
- Alpha is the broader exploratory agent

### 6. Identity contract

The entire toolchain should use a single explicit agent identity from cron prompt through shell wrappers into Python helpers.

Recommendation:

- use the agent identity already present in the scheduled workflow context (`alpha` or `kimi`)
- pass that identity explicitly through the Polymarket scripts rather than inferring from prompts alone

This identity should select both:

- market policy
- state file paths

### 7. Documentation updates

Update the policy docs so they reflect the split:

- `NorthStar.md`
- `AGENTS.md`
- `docs/agent-tasks.md`

At minimum the docs should describe:

- Kimi as the restricted calibrated agent
- Alpha as the broader unrestricted exploration agent
- separate bankrolls by agent

## Testing

Add targeted automated coverage for:

1. Kimi still rejecting markets outside the current restricted set
2. Alpha being allowed to select markets Kimi would reject
3. Kimi continuing to use the current bankroll ledger
4. Alpha writing to a separate new bankroll ledger
5. summaries and bankroll metrics staying isolated by agent
6. Kimi keeping repeat exclusions while Alpha does not
7. pending-trade state not colliding across Alpha and Kimi

These tests should focus on the selection and metrics layers where the policy actually lives.

## Out of Scope

This change does not redesign:

- the overall Polymarket candidate-selection pipeline
- trading heuristics unrelated to restriction policy
- the health-check architecture
- the cron workflow layout

## Recommendation

Implement this as a shared pipeline with agent-aware policy and agent-scoped bankroll files.

That gives:

- minimal duplication
- deterministic enforcement in code
- clean operational separation between Alpha and Kimi
- a straightforward doc story for the NorthStar
