#!/bin/sh
# Manage the Paperclip board LaunchAgent (macOS launchd).
# Runs `pnpm --filter @paperclipai/server dev` (tsx): workspace packages export TS sources, so `start` (node dist) breaks under pnpm link.
#
# Usage:
#   paperclip-ctl.sh install   — copy plist from repo → ~/Library/LaunchAgents, then load
#   paperclip-ctl.sh load|unload|restart|status|logs
set -eu

LABEL="com.grokclaw.paperclip"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PLIST_SRC="$WORKSPACE_ROOT/launchd/com.grokclaw.paperclip.plist"
PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"
LOG_OUT="$HOME/.openclaw/logs/paperclip-stdout.log"
LOG_ERR="$HOME/.openclaw/logs/paperclip-stderr.log"

usage() {
  echo "usage: paperclip-ctl.sh <install|load|unload|restart|status|logs>" >&2
  exit 1
}

[ "$#" -eq 1 ] || usage

cmd="$1"
mkdir -p "$HOME/.openclaw/logs"

case "$cmd" in
  install)
    [ -f "$PLIST_SRC" ] || {
      echo "paperclip-ctl: missing $PLIST_SRC" >&2
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
    echo "stdout: $LOG_OUT"
    echo "stderr: $LOG_ERR"
    [ -f "$LOG_OUT" ] && tail -n 50 "$LOG_OUT" || true
    [ -f "$LOG_ERR" ] && tail -n 50 "$LOG_ERR" || true
    ;;
  *)
    usage
    ;;
esac
