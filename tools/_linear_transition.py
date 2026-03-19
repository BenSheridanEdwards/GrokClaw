#!/usr/bin/env python3
"""Transition a Linear issue to a new workflow state."""
import json, sys, urllib.request

api_key    = sys.argv[1]
issue_id   = sys.argv[2]  # e.g. "GRO-17"
target_state = sys.argv[3]  # e.g. "Done", "In Progress", "Canceled"

TEAM_ID = "3f1b1054-07c6-4aad-a02c-89c78a43946b"

STATE_MAP = {
    "backlog":     "984f610b-9331-4398-8ad5-5a89dc71e4e3",
    "todo":        "e9022bd9-7739-4c24-bf80-f9c56cf989d7",
    "in progress": "908ea71e-f018-4fbe-aa6f-592dcbcbc8e2",
    "in review":   "5dfbb082-161c-40e9-a1ad-e4bd601b6d42",
    "done":        "047f6e71-4f34-4184-b6c7-694d762401eb",
    "canceled":    "5d76684c-266f-4057-930f-975e76daaedd",
    "duplicate":   "366c1448-dd21-4f62-942f-366fd578485e",
}

state_id = STATE_MAP.get(target_state.lower())
if not state_id:
    valid = ", ".join(STATE_MAP.keys())
    print(f"ERROR: unknown state '{target_state}'. Valid: {valid}", file=sys.stderr)
    sys.exit(1)

# Resolve issue identifier → internal ID
resolve_query = """
query IssueByIdentifier($identifier: String!) {
  issueVcsBranchSearch(branchName: $identifier) { id identifier }
}
"""

# Linear's identifier search via the issues filter is more reliable
resolve_query = """
query FindIssue($filter: IssueFilter!) {
  issues(filter: $filter, first: 1) {
    nodes { id identifier }
  }
}
"""

# Extract team key and number from identifier (e.g. GRO-17)
parts = issue_id.split("-")
if len(parts) != 2:
    print(f"ERROR: invalid issue identifier '{issue_id}'", file=sys.stderr)
    sys.exit(1)

issue_number = int(parts[1])

resolve_payload = json.dumps({
    "query": resolve_query,
    "variables": {
        "filter": {
            "team": {"id": {"eq": TEAM_ID}},
            "number": {"eq": issue_number},
        }
    }
}).encode()

req = urllib.request.Request(
    "https://api.linear.app/graphql",
    data=resolve_payload,
    headers={"Authorization": api_key, "Content-Type": "application/json"},
    method="POST",
)

with urllib.request.urlopen(req) as resp:
    data = json.load(resp)

nodes = (data.get("data") or {}).get("issues", {}).get("nodes", [])
if not nodes:
    print(f"ERROR: issue {issue_id} not found", file=sys.stderr)
    sys.exit(1)

internal_id = nodes[0]["id"]

# Transition the issue
update_mutation = """
mutation UpdateIssue($id: String!, $stateId: String!) {
  issueUpdate(id: $id, input: { stateId: $stateId }) {
    success
    issue { identifier url state { name } }
  }
}
"""

update_payload = json.dumps({
    "query": update_mutation,
    "variables": {"id": internal_id, "stateId": state_id},
}).encode()

req2 = urllib.request.Request(
    "https://api.linear.app/graphql",
    data=update_payload,
    headers={"Authorization": api_key, "Content-Type": "application/json"},
    method="POST",
)

with urllib.request.urlopen(req2) as resp2:
    data2 = json.load(resp2)

errors = data2.get("errors") or []
if errors:
    print(f"ERROR: {errors[0].get('message')}", file=sys.stderr)
    sys.exit(1)

result = (data2.get("data") or {}).get("issueUpdate") or {}
if not result.get("success"):
    print("ERROR: issueUpdate returned success=false", file=sys.stderr)
    sys.exit(1)

issue = result.get("issue") or {}
state_name = (issue.get("state") or {}).get("name", target_state)
print(f"{issue.get('identifier', issue_id)} → {state_name}")
