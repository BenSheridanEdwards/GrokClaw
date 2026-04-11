# Model Response Parsing

> 30 nodes

## Key Concepts

- **parse.ts** (30 connections) — `paperclip/packages/adapters/pi-local/src/server/parse.ts`
- **parseGeminiJsonl()** (5 connections) — `paperclip/packages/adapters/gemini-local/src/server/parse.ts`
- **parseCursorJsonl()** (4 connections) — `paperclip/packages/adapters/cursor-local/src/server/parse.ts`
- **extractClaudeErrorMessages()** (4 connections) — `paperclip/packages/adapters/claude-local/src/server/parse.ts`
- **asErrorText()** (3 connections) — `paperclip/packages/adapters/gemini-local/src/server/parse.ts`
- **readSessionId()** (3 connections) — `paperclip/packages/adapters/gemini-local/src/server/parse.ts`
- **extractGeminiErrorMessages()** (3 connections) — `paperclip/packages/adapters/gemini-local/src/server/parse.ts`
- **detectClaudeLoginRequired()** (3 connections) — `paperclip/packages/adapters/claude-local/src/server/parse.ts`
- **parsePiJsonl()** (3 connections) — `paperclip/packages/adapters/pi-local/src/server/parse.ts`
- **collectAssistantText()** (2 connections) — `paperclip/packages/adapters/cursor-local/src/server/parse.ts`
- **errorText()** (2 connections) — `paperclip/packages/adapters/opencode-local/src/server/parse.ts`
- **parseOpenCodeJsonl()** (2 connections) — `paperclip/packages/adapters/opencode-local/src/server/parse.ts`
- **collectMessageText()** (2 connections) — `paperclip/packages/adapters/gemini-local/src/server/parse.ts`
- **accumulateUsage()** (2 connections) — `paperclip/packages/adapters/gemini-local/src/server/parse.ts`
- **describeGeminiFailure()** (2 connections) — `paperclip/packages/adapters/gemini-local/src/server/parse.ts`
- **detectGeminiAuthRequired()** (2 connections) — `paperclip/packages/adapters/gemini-local/src/server/parse.ts`
- **extractClaudeLoginUrl()** (2 connections) — `paperclip/packages/adapters/claude-local/src/server/parse.ts`
- **describeClaudeFailure()** (2 connections) — `paperclip/packages/adapters/claude-local/src/server/parse.ts`
- **isClaudeUnknownSessionError()** (2 connections) — `paperclip/packages/adapters/claude-local/src/server/parse.ts`
- **asRecord()** (2 connections) — `paperclip/packages/adapters/pi-local/src/server/parse.ts`
- **extractTextContent()** (2 connections) — `paperclip/packages/adapters/pi-local/src/server/parse.ts`
- **isCursorUnknownSessionError()** (1 connections) — `paperclip/packages/adapters/cursor-local/src/server/parse.ts`
- **isOpenCodeUnknownSessionError()** (1 connections) — `paperclip/packages/adapters/opencode-local/src/server/parse.ts`
- **isGeminiUnknownSessionError()** (1 connections) — `paperclip/packages/adapters/gemini-local/src/server/parse.ts`
- **isGeminiTurnLimitResult()** (1 connections) — `paperclip/packages/adapters/gemini-local/src/server/parse.ts`
- *... and 5 more nodes in this community*

## Relationships

- [[Agent Skills & Onboarding]] (1 shared connections)

## Source Files

- `paperclip/packages/adapters/claude-local/src/server/parse.ts`
- `paperclip/packages/adapters/codex-local/src/server/parse.ts`
- `paperclip/packages/adapters/cursor-local/src/server/parse.ts`
- `paperclip/packages/adapters/gemini-local/src/server/parse.ts`
- `paperclip/packages/adapters/opencode-local/src/server/parse.ts`
- `paperclip/packages/adapters/pi-local/src/server/parse.ts`

## Audit Trail

- EXTRACTED: 91 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*