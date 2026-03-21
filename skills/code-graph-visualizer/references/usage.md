# Code Graph Visualizer — Usage

## CLI

```bash
codegraph.sh [path] [--output FILE] [--format html|json|all]
```

- `path`: Repo root (default: `.`)
- `--output`, `-o`: Output path (default: `graph.html`)
- `--format`, `-f`: `html`, `json`, or `all` (default: `all`)

## Examples

```bash
# Current directory
./tools/codegraph.sh

# Explicit path
./tools/codegraph.sh /path/to/repo -o /tmp/graph.html

# JSON only (for piping to LLM)
./tools/codegraph.sh . -o graph.json -f json
```

## Supported languages

- Python (`.py`)
- JavaScript (`.js`, `.jsx`)
- TypeScript (`.ts`, `.tsx`)
- Rust (`.rs`)

## Token estimation

Uses tiktoken `cl100k_base` (GPT-4–style). Fallback: word count if tiktoken unavailable.

## Filters (future)

Planned: `--exclude`, `--include`, `--max-files`. Currently parses all supported files under the path.
