#!/usr/bin/env python3
"""Create a Linear ticket for an approved Grok suggestion."""
import json
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

title = f"Implement Grok Suggestion #{suggestion_num} - {suggestion_title}"

# Build description: prepend Cursor instructions if no custom description given
if not description:
    description = f"""## What to implement

{suggestion_title}

## Instructions for Cursor

1. Read `CURSOR.md` in the repo root before starting.
2. Implement the feature described in the title.
3. Commit with a message referencing the issue identifier.
4. Mark the PR ready for review when done.
5. Post completion to Telegram: `tools/telegram-post.sh suggestions "🤖 <issue-id> complete. PR: <url>"`
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
