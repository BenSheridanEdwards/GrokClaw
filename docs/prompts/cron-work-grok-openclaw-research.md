# Grok — OpenClaw research (work only)

The orchestrator has already created this run’s Paperclip issue and recorded `started` in `data/cron-runs/*.jsonl`. **Do not** call `cron-paperclip-lifecycle.sh`, `cron-run-record.sh`, or create another Paperclip run issue; the wrapper will record the terminal outcome and close Paperclip.

You are Grok. Read `memory/MEMORY.md`. Determine the run slot from the current UTC hour: 07=morning, 13=afternoon, 19=evening. Research OpenClaw status and ecosystem: are we on the latest stable version, what new features or integrations are shipping, and what is happening on X, GitHub, and npm. Save a markdown brief to `data/research/openclaw/YYYY-MM-DD-{morning|afternoon|evening}.md` with sections: latest stable, notable changes, interesting integrations, and recommended action. Post a one-line headline to health-alerts: `printf '%s\n' 'OpenClaw research (<slot>): <one-line headline>' | ./tools/telegram-post.sh health-alerts`.
