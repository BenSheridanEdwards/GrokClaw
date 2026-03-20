# Browser Automation

GrokClaw uses OpenClaw's built-in **browser tool** for agentic workflows: research pages, authenticated flows, and UI automation. The tool uses a sandbox profile (`openclaw`) by default — no manual setup.

## When to use

| Use case | Prefer |
|----------|--------|
| Research across >3 tabs, JS-heavy pages | `browser` tool |
| Authenticated flows (login, form-fill) | `browser` tool |
| UI automation, click/type flows | `browser` tool |
| Simple text fetch, single URL | `web_fetch` |

## Configuration

The browser tool is configured in `~/.openclaw/openclaw.json`. Merge `config/browser-snippet.json` or add:

```json
{
  "browser": {
    "enabled": true,
    "defaultProfile": "openclaw",
    "profiles": {
      "openclaw": {
        "color": "#FF4500"
      }
    }
  }
}
```

- **`openclaw`** profile: isolated sandbox, no user data. Use for automation.
- **`user`** profile: attaches to your Chrome session. Out of scope for GrokClaw.

After changing config, restart the gateway: `./tools/gateway-ctl.sh restart`.

## Browser tool actions

Grok calls the `browser` tool with these actions:

| Action | Purpose |
|--------|---------|
| `status` | Check if browser is running |
| `start` | Start the sandbox browser |
| `snapshot` | Capture page DOM + element refs (e.g. `e1`, `e2`) |
| `act` | Click, type, fill using refs from snapshot |
| `screenshot` | Capture visual screenshot |

Examples:

- `browser(action="snapshot", url="https://docs.openclaw.ai")` — navigate and snapshot
- `browser(action="act", kind="click", ref="aria-login")` — click element by ref

After DOM changes (clicks, form fills), take a fresh snapshot — refs become stale.

## E2E test

Run the browser E2E test to verify the full flow:

```bash
./tools/browser-e2e-test.sh
```

This runs Grok with instructions to: fetch https://docs.openclaw.ai → snapshot → extract headings → post summary to Telegram suggestions.

Requires: gateway running, browser enabled in config, `.env` with Telegram credentials.
