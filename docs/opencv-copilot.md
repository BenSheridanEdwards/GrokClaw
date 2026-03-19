# opencv-copilot: Local Semantic Code Search (GRO-22)

Tree-sitter based semantic search for GrokClaw (TS/Shell/Python). No external APIs or embeddings.

## Setup

```sh
pip install -r requirements-opencv-copilot.txt
```

Dependencies: `tree-sitter`, `tree-sitter-python`, `tree-sitter-bash`, `tree-sitter-typescript`.

## Usage

### Search

```sh
./tools/opencv-copilot search "query" [--limit N]
./tools/oc-semantic-search.sh "query" [--limit N]
```

Returns top files/chunks with scores. Searches function names, class names, and symbols extracted via AST.

### Git diff

```sh
./tools/oc-git-diff.sh [branch]
```

Default branch: `main`. Output: changed files, stats, diff summary. Use in PR reviews.

### Smoke test

```sh
./tools/oc-search-smoke.sh
```

Validates >80% accuracy on known GrokClaw queries (telegram, health, polymarket, linear).

## Performance

- Sub-second queries on full GrokClaw repo
- On-demand parsing (no persistent index)
- Excludes: `.git`, `node_modules`, `__pycache__`, `.venv`, `venv`

## Grok workflow

- **PR reviews (GRO-21+)**: Use `oc-semantic-search.sh` to find relevant code before reviewing; use `oc-git-diff.sh` for structured branch changes.
- **Memory gaps**: Search for symbols when recalling implementation details.

## Trigger

- Manual: run scripts as needed
- Cron: `oc-search-daily` (05:00) runs smoke test to validate pipeline

## Out of scope

- Full VSCode integration
- Non-GrokClaw repos
- Remote MCP servers
