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

# 2. Trending repos (created in last 7 days, Python/TypeScript/AI-related, sorted by stars)
trending="$(gh api '/search/repositories' \
  --method GET \
  -f q="created:>=$WEEK_AGO stars:>100 language:python OR language:typescript" \
  -f sort=stars \
  -f order=desc \
  -f per_page=20 \
  --jq '
  [.items[] | {
    name: .full_name,
    description: .description,
    stars: .stargazers_count,
    language: .language,
    created_at: .created_at,
    url: .html_url,
    source: "trending"
  }]
' 2>/dev/null || echo "[]")"

# Merge and write
python3 - "$starred" "$trending" "$OUTPUT_FILE" <<'PY'
import json, sys
starred = json.loads(sys.argv[1]) if sys.argv[1] != "[]" else []
trending = json.loads(sys.argv[2]) if sys.argv[2] != "[]" else []
output = {"date": sys.argv[3].split("/")[-1].replace(".json", ""), "starred": starred, "trending": trending}
with open(sys.argv[3], "w") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)
print(sys.argv[3])
PY
