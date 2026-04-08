#!/usr/bin/env python3
"""Cancel open Linear issues created for workflow-health remediation spam.

Also removes stale `data/pending-linear-draft-workflow-health-*.json` files and
resets ~/.openclaw/state/workflow-health-failures.json when present.

Load LINEAR_API_KEY from the environment (source GrokClaw/.env before running).

Dry-run by default; pass --apply to mutate Linear, delete files, reset state.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

LINEAR_TEAM_ID = "3f1b1054-07c6-4aad-a02c-89c78a43946b"
# Must match tools/_workflow_health.py build_draft title
WORKFLOW_HEALTH_ISSUE_TITLE = "Fix workflow health failure in core cron workflows"
TERMINAL_LINEAR_STATES = frozenset(
    {"done", "canceled", "cancelled", "duplicate", "completed"}
)
CANCELED_STATE_ID = "5d76684c-266f-4057-930f-975e76daaedd"


def workspace_root() -> Path:
    return Path(os.environ.get("WORKSPACE_ROOT", Path(__file__).resolve().parents[1]))


def state_file() -> Path:
    override = os.environ.get("WORKFLOW_HEALTH_STATE_FILE")
    if override:
        return Path(override)
    return Path.home() / ".openclaw" / "state" / "workflow-health-failures.json"


def graphql(api_key: str, query: str, variables: dict) -> dict:
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.linear.app/graphql",
        data=payload,
        headers={"Authorization": api_key, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


def find_open_workflow_health_issues(api_key: str) -> list[dict]:
    """Return issue nodes {id, identifier, title} that are still open."""
    q = """
query WhIssues($teamId: ID!, $needle: String!) {
  issues(
    first: 50
    filter: {
      team: { id: { eq: $teamId } }
      title: { containsIgnoreCase: $needle }
    }
  ) {
    nodes {
      id
      identifier
      title
      state { name }
    }
  }
}
"""
    data = graphql(
        api_key,
        q,
        {"teamId": LINEAR_TEAM_ID, "needle": WORKFLOW_HEALTH_ISSUE_TITLE},
    )
    errors = data.get("errors") or []
    if errors:
        raise RuntimeError(errors[0].get("message", "Linear GraphQL error"))
    nodes = (data.get("data") or {}).get("issues", {}).get("nodes", [])
    out = []
    for node in nodes:
        if (node.get("title") or "").strip() != WORKFLOW_HEALTH_ISSUE_TITLE:
            continue
        st = ((node.get("state") or {}).get("name") or "").strip().lower()
        if st in {s.lower() for s in TERMINAL_LINEAR_STATES}:
            continue
        out.append(node)
    return out


def cancel_issue(api_key: str, internal_id: str) -> dict:
    m = """
mutation CancelWh($id: String!, $stateId: String!) {
  issueUpdate(id: $id, input: { stateId: $stateId }) {
    success
    issue { identifier state { name } }
  }
}
"""
    data = graphql(
        api_key,
        m,
        {"id": internal_id, "stateId": CANCELED_STATE_ID},
    )
    errors = data.get("errors") or []
    if errors:
        raise RuntimeError(errors[0].get("message", "Linear GraphQL error"))
    return (data.get("data") or {}).get("issueUpdate") or {}


def pending_workflow_health_drafts(root: Path) -> list[Path]:
    data_dir = root / "data"
    if not data_dir.is_dir():
        return []
    return sorted(data_dir.glob("pending-linear-draft-workflow-health-*.json"))


def reset_workflow_health_state(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": "resolved",
        "note": "cleared by linear-workflow-health-cleanup --apply",
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def plan_and_apply(
    *,
    api_key: str | None,
    root: Path,
    apply: bool,
    skip_linear: bool,
    skip_drafts: bool,
    skip_state: bool,
) -> int:
    issues: list[dict] = []

    if not skip_linear:
        if not api_key:
            print("linear-workflow-health: LINEAR_API_KEY not set; skipping Linear", file=sys.stderr)
        else:
            try:
                issues = find_open_workflow_health_issues(api_key)
            except (urllib.error.URLError, urllib.error.HTTPError, RuntimeError, json.JSONDecodeError) as e:
                print(f"linear-workflow-health: Linear query failed: {e}", file=sys.stderr)
                return 1
            for node in issues:
                ident = node.get("identifier", node.get("id"))
                print(f"issue {ident} title={node.get('title')!r}")
            if apply and issues:
                for node in issues:
                    iid = node.get("id")
                    if not iid:
                        continue
                    res = cancel_issue(api_key, str(iid))
                    if not res.get("success"):
                        print(f"linear-workflow-health: cancel failed for {iid}", file=sys.stderr)
                        return 1
                    issue = res.get("issue") or {}
                    print(
                        f"  canceled {issue.get('identifier', iid)} → {(issue.get('state') or {}).get('name')}"
                    )
            elif issues:
                print(f"linear-workflow-health: dry-run ({len(issues)} issue(s)); use --apply")

    draft_paths = [] if skip_drafts else pending_workflow_health_drafts(root)
    for p in draft_paths:
        try:
            rel = p.relative_to(root)
        except ValueError:
            rel = p
        print(f"draft {rel}")
    if apply and draft_paths and not skip_drafts:
        for p in draft_paths:
            p.unlink()
        print(f"linear-workflow-health: removed {len(draft_paths)} draft file(s)")

    sf = state_file()
    has_state = (not skip_state) and sf.exists()
    if has_state:
        print(f"state {sf}")
        if apply:
            reset_workflow_health_state(sf)
            print("linear-workflow-health: reset workflow-health state file")

    if not issues and not draft_paths and not has_state:
        print("linear-workflow-health: nothing to do")

    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Clean workflow-health Linear noise")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--skip-linear", action="store_true")
    parser.add_argument("--skip-drafts", action="store_true")
    parser.add_argument("--skip-state", action="store_true")
    args = parser.parse_args(argv)
    root = workspace_root()
    api_key = os.environ.get("LINEAR_API_KEY", "").strip() or None

    return plan_and_apply(
        api_key=api_key,
        root=root,
        apply=args.apply,
        skip_linear=args.skip_linear,
        skip_drafts=args.skip_drafts,
        skip_state=args.skip_state,
    )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
