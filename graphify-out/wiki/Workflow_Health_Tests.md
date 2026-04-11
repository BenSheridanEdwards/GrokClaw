# Workflow Health Tests

> 33 nodes

## Key Concepts

- **WorkflowHealthTests** (30 connections) — `tests/test_workflow_health.py`
- **._seed_core_jobs()** (19 connections) — `tests/test_workflow_health.py`
- **._run_audit()** (16 connections) — `tests/test_workflow_health.py`
- **._seed_full_evidence()** (16 connections) — `tests/test_workflow_health.py`
- **.test_research_passes_when_expected_file_exists_despite_stale_mtime()** (7 connections) — `tests/test_workflow_health.py`
- **.test_daily_brief_accepts_health_topic_fallback_prefix()** (6 connections) — `tests/test_workflow_health.py`
- **.test_daily_brief_sad_path_flags_missing_audit()** (6 connections) — `tests/test_workflow_health.py`
- **.test_alpha_sad_path_flags_missing_agent_report()** (6 connections) — `tests/test_workflow_health.py`
- **._run_json_command()** (4 connections) — `tests/test_workflow_health.py`
- **._read_audit_events()** (4 connections) — `tests/test_workflow_health.py`
- **._write_audit_events()** (4 connections) — `tests/test_workflow_health.py`
- **.test_accepts_extra_non_core_cron_jobs_when_core_workflows_exist()** (4 connections) — `tests/test_workflow_health.py`
- **.test_accepts_paperclip_issue_timestamps_with_milliseconds()** (4 connections) — `tests/test_workflow_health.py`
- **.test_daily_brief_requires_the_latest_expected_run_after_grace()** (4 connections) — `tests/test_workflow_health.py`
- **.test_openclaw_research_requires_the_latest_expected_run_after_grace()** (4 connections) — `tests/test_workflow_health.py`
- **.test_alpha_requires_the_latest_expected_run_after_grace()** (4 connections) — `tests/test_workflow_health.py`
- **.test_daily_brief_happy_path_satisfies_contract()** (4 connections) — `tests/test_workflow_health.py`
- **.test_openclaw_research_happy_path_satisfies_contract()** (4 connections) — `tests/test_workflow_health.py`
- **.test_openclaw_research_sad_path_flags_missing_markdown()** (4 connections) — `tests/test_workflow_health.py`
- **.test_alpha_happy_path_satisfies_contract()** (4 connections) — `tests/test_workflow_health.py`
- **.test_audit_one_uses_local_evidence_for_single_workflow()** (4 connections) — `tests/test_workflow_health.py`
- **.test_audit_one_can_include_paperclip_checks()** (3 connections) — `tests/test_workflow_health.py`
- **.test_audit_quick_flags_missing_hourly_run()** (3 connections) — `tests/test_workflow_health.py`
- **.test_started_run_after_grace_is_reported_as_stuck()** (3 connections) — `tests/test_workflow_health.py`
- **.test_audit_one_alpha_polymarket_accepts_new_telegram_prefix_and_trim()** (3 connections) — `tests/test_workflow_health.py`
- *... and 8 more nodes in this community*

## Relationships

- No strong cross-community connections detected

## Source Files

- `tests/test_workflow_health.py`

## Audit Trail

- EXTRACTED: 182 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*