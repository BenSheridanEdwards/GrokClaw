#!/bin/sh
set -eu

LABEL="com.grokclaw.gateway"
PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"
LOG_OUT="$HOME/.openclaw/logs/gateway-stdout.log"
LOG_ERR="$HOME/.openclaw/logs/gateway-stderr.log"

usage() {
  echo "usage: gateway-ctl.sh <load|unload|restart|status|logs>" >&2
  exit 1
}

[ "$#" -eq 1 ] || usage

cmd="$1"
mkdir -p "$HOME/.openclaw/logs"

case "$cmd" in
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
