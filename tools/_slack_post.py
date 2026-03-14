#!/usr/bin/env python3
import json, sys, urllib.request

token, channel, thread_ts, message = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]

payload = {"channel": channel, "text": message}
if thread_ts:
    payload["thread_ts"] = thread_ts

req = urllib.request.Request(
    "https://slack.com/api/chat.postMessage",
    data=json.dumps(payload).encode(),
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(req) as resp:
    data = json.load(resp)

if not data.get("ok"):
    print(f"ERROR: {data.get('error', 'unknown')}", file=sys.stderr)
    sys.exit(1)

print(data["ts"])
