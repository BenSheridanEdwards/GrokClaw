#!/bin/sh
# Discover relevant GitHub repos from starred + trending.
# Output: data/github-discover/YYYY-MM-DD.json
#
# Usage: ./tools/github-discover.sh
# Env: WORKSPACE_ROOT, GITHUB_USER (default: BenSheridanEdwards)
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
GITHUB_USER="${GITHUB_USER:-BenSheridanEdwards}"
TODAY="$(date -u +%Y-%m-%d)"
WEEK_AGO="$(date -u -v-7d +%Y-%m-%d 2>/dev/null || date -u -d '7 days ago' +%Y-%m-%d)"
OUTPUT_DIR="$WORKSPACE_ROOT/data/github-discover"
OUTPUT_FILE="$OUTPUT_DIR/$TODAY.json"

mkdir -p "$OUTPUT_DIR"

# 1. Recent starred repos (last 7 days, up to 30)
starred="$(gh api "/users/$GITHUB_USER/starred" \
  --header 'Accept: application/vnd.github.v3.star+json' \
  --paginate --jq "
  [.[] | select(.starred_at >= \"${WEEK_AGO}T00:00:00Z\") | {
    name: .repo.full_name,
    description: .repo.description,
    stars: .repo.stargazers_count,
    language: .repo.language,
    starred_at: .starred_at,
    url: .repo.html_url,
    source: \"starred\"
  }] | .[0:30]
" 2>/dev/null || echo "[]")"

# 2. Trending repos (created in last 7 days, sorted by stars, Python then TypeScript)
JQ_TRENDING='[.items[] | {name: .full_name, description: .description, stars: .stargazers_count, language: .language, created_at: .created_at, url: .html_url, source: "trending"}]'
trending_py="$(gh api '/search/repositories' --method GET \
  -f q="created:>=$WEEK_AGO stars:>100 language:python" \
  -f sort=stars -f order=desc -f per_page=10 \
  --jq "$JQ_TRENDING" 2>/dev/null || echo "[]")"
trending_ts="$(gh api '/search/repositories' --method GET \
  -f q="created:>=$WEEK_AGO stars:>100 language:typescript" \
  -f sort=stars -f order=desc -f per_page=10 \
  --jq "$JQ_TRENDING" 2>/dev/null || echo "[]")"
trending="${trending_py}
${trending_ts}"

# Merge and write (--paginate may produce concatenated JSON arrays per page)
python3 - "$OUTPUT_FILE" <<PY
import json, re, sys

def parse_concat_json(raw):
    """Parse potentially concatenated JSON arrays from gh --paginate."""
    raw = raw.strip()
    if not raw or raw == "[]":
        return []
    # Try single parse first
    try:
        result = json.loads(raw)
        return result if isinstance(result, list) else [result]
    except json.JSONDecodeError:
        pass
    # Split concatenated arrays and merge
    items = []
    for chunk in re.split(r'(?<=\])\s*(?=\[)', raw):
        try:
            parsed = json.loads(chunk)
            if isinstance(parsed, list):
                items.extend(parsed)
        except json.JSONDecodeError:
            continue
    return items

starred = parse_concat_json('''$starred''')
trending = parse_concat_json('''$trending''')
output = {"date": sys.argv[1].split("/")[-1].replace(".json", ""), "starred": starred, "trending": trending}
with open(sys.argv[1], "w") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)
print(sys.argv[1])
PY
