#!/bin/zsh
set -euo pipefail

UDID="${GRIDDLE_UDID:-00008140-001278E80244801C}"
BUNDLE_ID="${GRIDDLE_BUNDLE_ID:-com.games.griddle}"

echo "== Device =="
xcrun devicectl device info details --device "$UDID" | sed -n '1,60p'

echo
echo "== App =="
xcrun devicectl device info apps \
  --device "$UDID" \
  --bundle-id "$BUNDLE_ID" \
  --include-all-apps \
  --columns '*'

echo
echo "== Running process =="
xcrun devicectl device info processes --device "$UDID" --columns '*' \
  | rg -i "griddle|PID" || true
