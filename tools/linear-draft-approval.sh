#!/bin/sh
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
DATA_DIR="$WORKSPACE_ROOT/data"
TELEGRAM_INLINE="$WORKSPACE_ROOT/tools/telegram-inline.sh"
TELEGRAM_POST="$WORKSPACE_ROOT/tools/telegram-post.sh"
LINEAR_TICKET="$WORKSPACE_ROOT/tools/linear-ticket.sh"
LINEAR_TRANSITION="$WORKSPACE_ROOT/tools/linear-transition.sh"

usage() {
  cat >&2 <<'EOF'
usage:
  linear-draft-approval.sh request <draft-id> <suggestion|user_request> <reference-id> <topic-id|name> "<title>" "<description>" [transition-state]
  linear-draft-approval.sh create <draft-id>
  linear-draft-approval.sh reject <draft-id>
EOF
  exit 1
}

pending_file() {
  printf '%s/data/pending-linear-draft-%s.json\n' "$WORKSPACE_ROOT" "$1"
}

json_field() {
  python3 -c 'import json,sys; data=json.load(open(sys.argv[1], encoding="utf-8")); print(data.get(sys.argv[2], ""))' "$1" "$2"
}

parse_linear_issue_id() {
  python3 -c 'import re,sys; text=sys.stdin.read(); match=re.search(r"/(GRO-[0-9]+)", text); print(match.group(1) if match else "")'
}

[ "$#" -ge 1 ] || usage

command="$1"
shift

case "$command" in
  request)
    [ "$#" -ge 6 ] || usage
    draft_id="$1"
    flow="$2"
    reference_id="$3"
    topic_id="$4"
    title="$5"
    description="$6"
    transition_to="${7:-}"

    case "$flow" in
      suggestion|user_request) ;;
      *)
        echo "flow must be suggestion or user_request" >&2
        exit 1
        ;;
    esac

    mkdir -p "$DATA_DIR"
    pending_path="$(pending_file "$draft_id")"
    python3 - "$pending_path" "$flow" "$reference_id" "$topic_id" "$title" "$description" "$transition_to" <<'PY'
import json
import sys

path, flow, reference_id, topic_id, title, description, transition_to = sys.argv[1:8]
with open(path, "w", encoding="utf-8") as handle:
    json.dump(
        {
            "flow": flow,
            "referenceId": reference_id,
            "topic": topic_id,
            "title": title,
            "description": description,
            "transitionTo": transition_to,
        },
        handle,
    )
PY

    message="Linear draft ready for approval

Flow: $flow
Reference: $reference_id
Title: $title

Description:
$description

Create the real Linear ticket only if this draft looks right."
    buttons=$(printf '[{"text":"Create Linear","callback_data":"approve_linear_draft:%s"},{"text":"Cancel","callback_data":"reject_linear_draft:%s"}]' "$draft_id" "$draft_id")
    "$TELEGRAM_INLINE" "$topic_id" "$message" "$buttons" plain
    ;;
  create)
    [ "$#" -eq 1 ] || usage
    draft_id="$1"
    pending_path="$(pending_file "$draft_id")"
    [ -f "$pending_path" ] || {
      echo "missing pending linear draft: $pending_path" >&2
      exit 1
    }

    flow="$(json_field "$pending_path" flow)"
    reference_id="$(json_field "$pending_path" referenceId)"
    topic_id="$(json_field "$pending_path" topic)"
    title="$(json_field "$pending_path" title)"
    description="$(json_field "$pending_path" description)"
    transition_to="$(json_field "$pending_path" transitionTo)"

    linear_output=$(env LINEAR_CREATION_FLOW="$flow" LINEAR_DRAFT_ID="$draft_id" "$LINEAR_TICKET" "$reference_id" "$title" "$description")
    linear_url=$(printf '%s\n' "$linear_output" | tail -n1)
    linear_issue_id=$(printf '%s\n' "$linear_url" | parse_linear_issue_id)

    if [ -n "$transition_to" ] && [ -n "$linear_issue_id" ]; then
      "$LINEAR_TRANSITION" "$linear_issue_id" "$transition_to"
    fi

    "$TELEGRAM_POST" "$topic_id" "Linear created: $linear_url"
    rm -f "$pending_path"
    printf '%s\n' "$linear_output"
    ;;
  reject)
    [ "$#" -eq 1 ] || usage
    draft_id="$1"
    pending_path="$(pending_file "$draft_id")"
    [ -f "$pending_path" ] || {
      echo "missing pending linear draft: $pending_path" >&2
      exit 1
    }
    topic_id="$(json_field "$pending_path" topic)"
    rm -f "$pending_path"
    "$TELEGRAM_POST" "$topic_id" "Linear draft rejected. No ticket was created."
    ;;
  *)
    usage
    ;;
esac
