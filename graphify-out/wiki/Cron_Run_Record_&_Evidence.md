# Cron Run Record & Evidence

> 26 nodes

## Key Concepts

- **heartbeat.ts** (25 connections) — `paperclip/packages/shared/src/types/heartbeat.ts`
- **readNonEmptyString()** (8 connections) — `paperclip/server/src/services/heartbeat.ts`
- **deriveTaskKey()** (4 connections) — `paperclip/server/src/services/heartbeat.ts`
- **deriveCommentId()** (4 connections) — `paperclip/server/src/services/heartbeat.ts`
- **enrichWakeContextSnapshot()** (4 connections) — `paperclip/server/src/services/heartbeat.ts`
- **resolveNextSessionState()** (4 connections) — `paperclip/server/src/services/heartbeat.ts`
- **resolveRuntimeSessionParamsForWorkspace()** (2 connections) — `paperclip/server/src/services/heartbeat.ts`
- **shouldResetTaskSessionForWake()** (2 connections) — `paperclip/server/src/services/heartbeat.ts`
- **describeSessionResetReason()** (2 connections) — `paperclip/server/src/services/heartbeat.ts`
- **mergeCoalescedContextSnapshot()** (2 connections) — `paperclip/server/src/services/heartbeat.ts`
- **runTaskKey()** (2 connections) — `paperclip/server/src/services/heartbeat.ts`
- **truncateDisplayId()** (2 connections) — `paperclip/server/src/services/heartbeat.ts`
- **normalizeSessionParams()** (2 connections) — `paperclip/server/src/services/heartbeat.ts`
- **appendExcerpt()** (1 connections) — `paperclip/server/src/services/heartbeat.ts`
- **normalizeMaxConcurrentRuns()** (1 connections) — `paperclip/server/src/services/heartbeat.ts`
- **withAgentStartLock()** (1 connections) — `paperclip/server/src/services/heartbeat.ts`
- **normalizeUsageTotals()** (1 connections) — `paperclip/server/src/services/heartbeat.ts`
- **readRawUsageTotals()** (1 connections) — `paperclip/server/src/services/heartbeat.ts`
- **deriveNormalizedUsageDelta()** (1 connections) — `paperclip/server/src/services/heartbeat.ts`
- **formatCount()** (1 connections) — `paperclip/server/src/services/heartbeat.ts`
- **parseSessionCompactionPolicy()** (1 connections) — `paperclip/server/src/services/heartbeat.ts`
- **parseIssueAssigneeAdapterOverrides()** (1 connections) — `paperclip/server/src/services/heartbeat.ts`
- **isSameTaskScope()** (1 connections) — `paperclip/server/src/services/heartbeat.ts`
- **normalizeAgentNameKey()** (1 connections) — `paperclip/server/src/services/heartbeat.ts`
- **getAdapterSessionCodec()** (1 connections) — `paperclip/server/src/services/heartbeat.ts`
- *... and 1 more nodes in this community*

## Relationships

- No strong cross-community connections detected

## Source Files

- `paperclip/packages/shared/src/types/heartbeat.ts`
- `paperclip/server/src/services/heartbeat.ts`

## Audit Trail

- EXTRACTED: 76 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*