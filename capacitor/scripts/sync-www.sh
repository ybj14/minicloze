#!/usr/bin/env bash
# Copy minicloze-web/static into Capacitor webDir (www), including data JSON.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO_ROOT="$(cd "$ROOT/.." && pwd)"

CANDIDATES=(
  "${STATIC_SRC:-}"
  "$REPO_ROOT/minicloze-work/minicloze-web/static"
  "$ROOT/../minicloze-web/static"
  "$ROOT/../minicloze-work/minicloze-web/static"
  "$REPO_ROOT/minicloze-web/static"
)

SRC=""
for c in "${CANDIDATES[@]}"; do
  if [[ -n "$c" && -d "$c" && -f "$c/index.html" ]]; then
    SRC="$c"
    break
  fi
done

if [[ -z "$SRC" ]]; then
  echo "ERROR: could not find minicloze-web/static (need index.html)." >&2
  echo "Set STATIC_SRC=/path/to/minicloze-web/static or keep minicloze-web/static next to this project." >&2
  exit 1
fi

DEST="$ROOT/www"
mkdir -p "$DEST"

echo "Syncing: $SRC -> $DEST"
if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete --exclude '.git' "$SRC"/ "$DEST"/
else
  find "$DEST" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
  cp -a "$SRC"/. "$DEST"/
fi

test -f "$DEST/index.html"
test -f "$DEST/service-worker.js"
test -d "$DEST/data"

# Apply Capacitor offline enhancements (SW precache of data, registration scope)
bash "$ROOT/scripts/patch-capacitor-offline.sh"

echo "Synced shell + data into www/ ($(du -sh "$DEST" | awk '{print $1}'))"
