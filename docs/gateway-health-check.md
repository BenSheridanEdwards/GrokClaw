# GrokClaw Gateway Health Check

`tools/health-check.sh` is the fast gateway detector. It checks liveness every 2 minutes and hands off recovery to `tools/gateway-watchdog.sh`.

## How it works

- Checks HTTP probe on `http://127.0.0.1:18800/health`
- Uses `.gateway-health-state` to track status
- Runs `tools/gateway-watchdog.sh health-check` when the gateway is down
- Alerts Telegram only when the watchdog handoff is unavailable
- Runs `tools/telegram-poller-guard.sh` to detect and auto-fix Telegram poller conflicts
- Exit 0 if healthy, exit 1 if not
- No LLM involved — pure shell
- Does not decide restart policy itself

## Repair ownership

Gateway recovery is split cleanly:

- `health-check.sh` detects failure fast and hands off
- `gateway-watchdog.sh` owns bounded automatic repair, cooldowns, and failure alerts
- `grokclaw-doctor.sh` is the workflow cron-evidence catch-all; under `--heal` it may perform low-risk infrastructure repairs, but it is not the fast automatic repair loop

## Relationship to workflow health

This script is only the fast liveness probe.

- `health-check.sh` answers: is the gateway up right now, and should the watchdog be asked to repair it?
- `gateway-watchdog.sh` answers: can the runtime recover automatically right now?
- `grokclaw-doctor.sh` answers: did the 4 core workflows actually run, write their evidence, and leave their Paperclip lifecycle, especially when the per-run audit path could not fire?

If a workflow is unhealthy but the gateway is technically up, `health-check.sh` will still pass and the doctor will raise the failure separately.

## Trigger: system crontab only

This runs via **system crontab**, not agent cron or heartbeat. Agent cron requires the gateway to be alive — it cannot detect its own death.

Current crontab entry:
```
*/2 * * * * /Users/jarvis/Engineering/Projects/GrokClaw/tools/health-check.sh >> /tmp/openclaw-health.log 2>&1
```

Verify:
```sh
crontab -l | grep health-check
```

Logs: `/tmp/openclaw-health.log`

## Watchdog schedule

`tools/gateway-watchdog.sh` runs via launchd at wall-clock minutes:

- `1,6,11,16,21,26,31,36,41,46,51,56`

Its plist is `launchd/com.grokclaw.gateway-watchdog.plist`.

## Doctor schedule

`tools/grokclaw-doctor.sh --check --quiet` runs via launchd at wall-clock minutes:

- `2,17,32,47`

This keeps workflow auditing separate from gateway repair and aligned after the core workflow grace windows. The doctor runs `tools/_workflow_health.py audit-quick` first, then escalates to the full workflow audit plus `tools/_workflow_health_handle.py` only when the quick path finds a missed run, stale cron evidence, or an error run record.

## Test gate

The health model is protected by a repo-managed test runner:

```sh
./tools/run-health-e2e-tests.sh
```

That runner covers the mocked happy and sad paths for the 4 core workflow contracts plus the detector, watchdog, and doctor layers. Husky's pre-commit hook runs `tools/test-all.sh` which includes this suite.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WORKSPACE_ROOT` | Derived from script path | Workspace root |
| `OPENCLAW_GATEWAY_PORT` | `18800` | Gateway HTTP port |
| `TELEGRAM_GROUP_ID` | From `.env` | Telegram group ID for alerts |
