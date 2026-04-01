#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: find-sessions.sh [-L socket-name|-S socket-path|-A] [-q pattern] [--json]

List tmux sessions on a socket (default tmux socket if none provided).

Options:
  -L, --socket       tmux socket name (passed to tmux -L)
  -S, --socket-path  tmux socket path (passed to tmux -S)
  -A, --all          scan all sockets under NANOBOT_TMUX_SOCKET_DIR
  -q, --query        case-insensitive substring to filter session names
  --json             print JSON array: objects with id, title, state (requires jq)
  -h, --help         show this help
USAGE
}

socket_name=""
socket_path=""
query=""
scan_all=false
json_output=false
socket_dir="${NANOBOT_TMUX_SOCKET_DIR:-${TMPDIR:-/tmp}/nanobot-tmux-sockets}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    -L|--socket)      socket_name="${2-}"; shift 2 ;;
    -S|--socket-path) socket_path="${2-}"; shift 2 ;;
    -A|--all)         scan_all=true; shift ;;
    -q|--query)       query="${2-}"; shift 2 ;;
    --json)           json_output=true; shift ;;
    -h|--help)        usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ "$scan_all" == true && ( -n "$socket_name" || -n "$socket_path" ) ]]; then
  echo "Cannot combine --all with -L or -S" >&2
  exit 1
fi

if [[ -n "$socket_name" && -n "$socket_path" ]]; then
  echo "Use either -L or -S, not both" >&2
  exit 1
fi

if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux not found in PATH" >&2
  exit 1
fi

if [[ "$json_output" == true ]] && ! command -v jq >/dev/null 2>&1; then
  echo "jq not found in PATH (required for --json)" >&2
  exit 1
fi

# Optional prefix so session ids stay unique when scanning multiple sockets (--all).
list_sessions() {
  local label="$1"; shift
  local id_prefix="${1-}"; shift
  local tmux_cmd=(tmux "$@")

  if ! sessions="$("${tmux_cmd[@]}" list-sessions -F $'#{session_name}\t#{session_attached}\t#{session_created_string}' 2>/dev/null)"; then
    echo "No tmux server found on $label" >&2
    return 1
  fi

  if [[ -n "$query" ]]; then
    sessions="$(printf '%s\n' "$sessions" | grep -i -- "$query" || true)"
  fi

  if [[ -z "$sessions" ]]; then
    if [[ "$json_output" == true ]]; then
      printf '%s\n' '[]'
    else
      echo "No sessions found on $label"
    fi
    return 0
  fi

  if [[ "$json_output" == true ]]; then
    local lines=()
    while IFS=$'\t' read -r name attached _created; do
      [[ -z "$name" ]] && continue
      local state
      state=$([[ "$attached" == "1" ]] && echo "attached" || echo "detached")
      local id="${id_prefix}${name}"
      lines+=("$(jq -nc --arg id "$id" --arg title "$name" --arg state "$state" '{id:$id,title:$title,state:$state}')")
    done <<< "$sessions"
    if [[ "${#lines[@]}" -eq 0 ]]; then
      printf '%s\n' '[]'
      return 0
    fi
    printf '%s\n' "${lines[@]}" | jq -s '.'
    return 0
  fi

  echo "Sessions on $label:"
  printf '%s\n' "$sessions" | while IFS=$'\t' read -r name attached created; do
    attached_label=$([[ "$attached" == "1" ]] && echo "attached" || echo "detached")
    printf '  - %s (%s, started %s)\n' "$name" "$attached_label" "$created"
  done
}

if [[ "$scan_all" == true ]]; then
  if [[ ! -d "$socket_dir" ]]; then
    echo "Socket directory not found: $socket_dir" >&2
    exit 1
  fi

  shopt -s nullglob
  sockets=("$socket_dir"/*)
  shopt -u nullglob

  if [[ "${#sockets[@]}" -eq 0 ]]; then
    echo "No sockets found under $socket_dir" >&2
    exit 1
  fi

  if [[ "$json_output" == true ]]; then
    combined="[]"
    for sock in "${sockets[@]}"; do
      if [[ ! -S "$sock" ]]; then
        continue
      fi
      if ! chunk="$(list_sessions "socket path '$sock'" "${sock}#" -S "$sock")"; then
        continue
      fi
      combined="$(jq -s '.[0] + .[1]' <<<"$combined"$'\n'"$chunk")"
    done
    printf '%s\n' "$combined"
    exit 0
  fi

  exit_code=0
  for sock in "${sockets[@]}"; do
    if [[ ! -S "$sock" ]]; then
      continue
    fi
    list_sessions "socket path '$sock'" "" -S "$sock" || exit_code=$?
  done
  exit "$exit_code"
fi

tmux_cmd=(tmux)
socket_label="default socket"

if [[ -n "$socket_name" ]]; then
  tmux_cmd+=(-L "$socket_name")
  socket_label="socket name '$socket_name'"
elif [[ -n "$socket_path" ]]; then
  tmux_cmd+=(-S "$socket_path")
  socket_label="socket path '$socket_path'"
fi

list_sessions "$socket_label" "" "${tmux_cmd[@]:1}"
