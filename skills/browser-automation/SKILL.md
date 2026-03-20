---
name: browser-automation
description: Use the OpenClaw browser tool for research, form-filling, and UI automation. Use when web_fetch is insufficient (JS-heavy pages, multi-tab research, authenticated flows).
metadata: {"nanobot":{"emoji":"🌐","os":["darwin","linux"]}}
---

# Browser Automation

Use the `browser` tool for agentic web workflows. Default profile: `openclaw` (sandbox).

## When to use

- Research across >3 tabs or JS-heavy pages
- Authenticated flows (login, form-fill)
- UI automation (click, type, screenshot, PDF export)

Prefer `web_fetch` for simple text from a single URL.

## Common patterns

### Screenshot page

1. `browser(action="start")` if needed
2. `browser(action="snapshot", url="https://example.com")` — navigate and snapshot
3. `browser(action="screenshot")` — capture visual

### Click + type flows

1. `browser(action="snapshot", url="...")` — get element refs (e.g. `e1`, `e2`)
2. `browser(action="act", kind="click", ref="e1")` — click
3. `browser(action="act", kind="type", ref="e2", text="...")` — type into field
4. Re-snapshot after DOM changes — refs become stale

### PDF export

1. Navigate to page
2. Snapshot to confirm content loaded
3. Use browser print-to-PDF if available, or screenshot as fallback

## Workflow

- **Snapshot first** — generates refs before any act
- **Re-snapshot after mutations** — clicks, form fills invalidate refs
- **Profile** — use `profile="openclaw"` (default sandbox)

## Examples

```
browser(action="snapshot", url="https://docs.openclaw.ai")
browser(action="act", kind="click", ref="aria-login")
browser(action="act", kind="type", ref="e3", text="username")
```

## References

- `docs/browser-automation.md` — config and E2E test
