#!/bin/sh
set -eu

LABEL="com.grokclaw.pr-review-watch"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PLIST_SRC="$WORKSPACE_ROOT/launchd/com.grokclaw.pr-review-watch.plist"
PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"
LOG_FILE="/tmp/grokclaw-pr-review-watch.log"

usage() {
  echo "usage: pr-review-watch-ctl.sh <install|load|unload|restart|status|logs>" >&2
  exit 1
}

[ "$#" -eq 1 ] || usage

cmd="$1"

case "$cmd" in
  install)
    [ -f "$PLIST_SRC" ] || {
      echo "pr-review-watch-ctl: missing $PLIST_SRC" >&2
      exit 1
    }
    mkdir -p "$HOME/Library/LaunchAgents"
    launchctl bootout "gui/$(id -u)" "$PLIST" 2>/dev/null || true
    cp "$PLIST_SRC" "$PLIST"
    echo "Installed $PLIST"
    launchctl bootstrap "gui/$(id -u)" "$PLIST" 2>/dev/null || true
    launchctl enable "gui/$(id -u)/$LABEL" || true
    launchctl kickstart -k "gui/$(id -u)/$LABEL"
    ;;
  load)
    launchctl bootstrap "gui/$(id -u)" "$PLIST" 2>/dev/null || true
    launchctl enable "gui/$(id -u)/$LABEL" || true
    launchctl kickstart -k "gui/$(id -u)/$LABEL"
    ;;
  unload)
    launchctl bootout "gui/$(id -u)" "$PLIST" 2>/dev/null || true
    ;;
  restart)
    launchctl kickstart -k "gui/$(id -u)/$LABEL"
    ;;
  status)
    launchctl print "gui/$(id -u)/$LABEL"
    ;;
  logs)
    echo "log: $LOG_FILE"
    [ -f "$LOG_FILE" ] && tail -n 50 "$LOG_FILE" || true
    ;;
  *)
    usage
    ;;
esac
