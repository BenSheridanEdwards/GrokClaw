#!/usr/bin/env python3
"""Create a Linear ticket for an approved Grok suggestion."""
import json
import re
import sys
import time
import urllib.error
import urllib.request

api_key          = sys.argv[1]
suggestion_num   = sys.argv[2]
suggestion_title = sys.argv[3]
description      = sys.argv[4] if len(sys.argv) > 4 else ""

TEAM_ID          = "3f1b1054-07c6-4aad-a02c-89c78a43946b"
CURSOR_DELEGATE  = "ca233eb8-8630-49c9-8f7c-3708c1bd1c4b"

def compact_title(raw_title: str, max_len: int = 72) -> str:
    """Return a concise PR-style one-liner title."""
    normalized = re.sub(r"\s+", " ", raw_title).strip()
    if not normalized:
        normalized = "Grok suggestion"
    if len(normalized) <= max_len:
        return normalized
    return normalized[: max_len - 1].rstrip() + "..."


title = compact_title(suggestion_title)

# Build description: always include the original ask and full implementation brief.
if not description:
    description = f"""## What to implement

{suggestion_title}

## Plan

1. Translate the suggestion into concrete implementation tasks.
2. Implement in small, reviewable commits.
3. Validate behavior with deterministic tests.

## Acceptance criteria

1. Feature behavior matches the original ask in this ticket.
2. Tests are added or updated to protect the behavior.
3. Any required ops/docs updates are included.

## Implementation notes

- Follow current repository conventions and existing workflow scripts.
- Prefer deterministic, idempotent scripts for operational actions.
- Keep user-facing messages concise and actionable.

## Out of scope

- New unrelated features beyond this ticket.
- Broad refactors not required for this implementation.

## Instructions for Cursor

1. Read `CURSOR.md` in the repo root before starting.
2. Implement the feature described in the title.
3. Commit with a message referencing the issue identifier.
4. Mark the PR ready for review when done.
5. Post completion to Telegram: `tools/telegram-post.sh suggestions "🤖 <issue-id> complete. PR: <url>"`
"""
else:
    description = f"""## Original ask

{suggestion_title}

## Full implementation brief

{description}
"""

mutation = """
mutation CreateIssue($teamId: String!, $title: String!, $description: String!, $delegateId: String!) {
  issueCreate(input: {
    teamId: $teamId
    title: $title
    description: $description
    delegateId: $delegateId
  }) {
    success
    issue { id identifier title url }
  }
}
"""

payload = json.dumps({
    "query": mutation,
    "variables": {
        "teamId": TEAM_ID,
        "title": title,
        "description": description,
        "delegateId": CURSOR_DELEGATE,
    }
}).encode()

req = urllib.request.Request(
    "https://api.linear.app/graphql",
    data=payload,
    headers={
        "Authorization": api_key,
        "Content-Type": "application/json",
    },
    method="POST",
)

data = None
last_error = ""
for attempt in range(1, 4):
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.load(resp)
        break
    except urllib.error.URLError as exc:
        last_error = str(exc)
    except urllib.error.HTTPError as exc:
        last_error = str(exc)
    except json.JSONDecodeError as exc:
        last_error = str(exc)
    if attempt < 3:
        time.sleep(2 ** (attempt - 1))

if data is None:
    print(f"ERROR: Linear API request failed after retries: {last_error}", file=sys.stderr)
    sys.exit(1)

errors = data.get("errors") or []
if errors:
    print(f"ERROR: {errors[0].get('message')}", file=sys.stderr)
    sys.exit(1)

result = (data.get("data") or {}).get("issueCreate") or {}
if not result.get("success"):
    print("ERROR: issueCreate returned success=false", file=sys.stderr)
    sys.exit(1)

issue = result.get("issue") or {}
url = issue.get("url", "")
if not url:
    print("ERROR: missing issue URL in response", file=sys.stderr)
    sys.exit(1)

print(url)
