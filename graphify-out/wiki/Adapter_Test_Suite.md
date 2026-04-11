# Adapter Test Suite

> 58 nodes

## Key Concepts

- **server.ts** (22 connections) — `paperclip/cli/src/prompts/server.ts`
- **registry.ts** (9 connections) — `paperclip/cli/src/adapters/registry.ts`
- **.request()** (9 connections) — `paperclip/cli/src/client/http.ts`
- **http.ts** (7 connections) — `paperclip/cli/src/client/http.ts`
- **PaperclipApiClient** (7 connections) — `paperclip/cli/src/client/http.ts`
- **codex-local-skill-injection.test.ts** (4 connections) — `paperclip/server/src/__tests__/codex-local-skill-injection.test.ts`
- **openclaw-gateway-adapter.test.ts** (4 connections) — `paperclip/server/src/__tests__/openclaw-gateway-adapter.test.ts`
- **cursor-local-skill-injection.test.ts** (3 connections) — `paperclip/server/src/__tests__/cursor-local-skill-injection.test.ts`
- **safeParseJson()** (3 connections) — `paperclip/cli/src/client/http.ts`
- **toApiError()** (3 connections) — `paperclip/cli/src/client/http.ts`
- **codex-local-adapter.test.ts** (2 connections) — `paperclip/server/src/__tests__/codex-local-adapter.test.ts`
- **cursor-local-adapter-environment.test.ts** (2 connections) — `paperclip/server/src/__tests__/cursor-local-adapter-environment.test.ts`
- **cursor-local-execute.test.ts** (2 connections) — `paperclip/server/src/__tests__/cursor-local-execute.test.ts`
- **opencode-local-adapter.test.ts** (2 connections) — `paperclip/server/src/__tests__/opencode-local-adapter.test.ts`
- **gemini-local-adapter.test.ts** (2 connections) — `paperclip/server/src/__tests__/gemini-local-adapter.test.ts`
- **codex-local-execute.test.ts** (2 connections) — `paperclip/server/src/__tests__/codex-local-execute.test.ts`
- **gemini-local-adapter-environment.test.ts** (2 connections) — `paperclip/server/src/__tests__/gemini-local-adapter-environment.test.ts`
- **cursor-local-adapter.test.ts** (2 connections) — `paperclip/server/src/__tests__/cursor-local-adapter.test.ts`
- **gemini-local-execute.test.ts** (2 connections) — `paperclip/server/src/__tests__/gemini-local-execute.test.ts`
- **ApiRequestError** (2 connections) — `paperclip/cli/src/client/http.ts`
- **.get()** (2 connections) — `paperclip/cli/src/client/http.ts`
- **.post()** (2 connections) — `paperclip/cli/src/client/http.ts`
- **.patch()** (2 connections) — `paperclip/cli/src/client/http.ts`
- **.delete()** (2 connections) — `paperclip/cli/src/client/http.ts`
- **buildUrl()** (2 connections) — `paperclip/cli/src/client/http.ts`
- *... and 33 more nodes in this community*

## Relationships

- [[Adapter Build Configs]] (1 shared connections)
- [[Issue Documents Section]] (1 shared connections)
- [[Paperclip UI Components]] (1 shared connections)

## Source Files

- `paperclip/cli/src/adapters/registry.ts`
- `paperclip/cli/src/client/http.ts`
- `paperclip/cli/src/prompts/server.ts`
- `paperclip/server/src/__tests__/adapter-models.test.ts`
- `paperclip/server/src/__tests__/adapter-session-codecs.test.ts`
- `paperclip/server/src/__tests__/claude-local-adapter-environment.test.ts`
- `paperclip/server/src/__tests__/claude-local-adapter.test.ts`
- `paperclip/server/src/__tests__/codex-local-adapter-environment.test.ts`
- `paperclip/server/src/__tests__/codex-local-adapter.test.ts`
- `paperclip/server/src/__tests__/codex-local-execute.test.ts`
- `paperclip/server/src/__tests__/codex-local-skill-injection.test.ts`
- `paperclip/server/src/__tests__/cursor-local-adapter-environment.test.ts`
- `paperclip/server/src/__tests__/cursor-local-adapter.test.ts`
- `paperclip/server/src/__tests__/cursor-local-execute.test.ts`
- `paperclip/server/src/__tests__/cursor-local-skill-injection.test.ts`
- `paperclip/server/src/__tests__/gemini-local-adapter-environment.test.ts`
- `paperclip/server/src/__tests__/gemini-local-adapter.test.ts`
- `paperclip/server/src/__tests__/gemini-local-execute.test.ts`
- `paperclip/server/src/__tests__/openclaw-gateway-adapter.test.ts`
- `paperclip/server/src/__tests__/opencode-local-adapter-environment.test.ts`

## Audit Trail

- EXTRACTED: 135 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*