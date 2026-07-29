#!/usr/bin/env bash
# Regenerate SHA256SUMS over every reproducible file in the artefact tree.
set -euo pipefail
cd "$(dirname "$0")/.."
HASH=sha256sum; command -v sha256sum >/dev/null 2>&1 || HASH="shasum -a 256"
find scripts oracle registry theories models tactics preregistration docs \
     measurements patches external \
     -type f \( -name '*.py'  -o -name '*.sh'  -o -name '*.json' -o -name '*.spthy' \
              -o -name '*.m4'  -o -name '*.m4i' -o -name '*.tactic' -o -name '*.md' \
              -o -name '*.txt' -o -name '*.tsv' -o -name '*.tex' \) \
  | LC_ALL=C sort | xargs "$HASH" > SHA256SUMS
echo "[ok] wrote SHA256SUMS ($(wc -l < SHA256SUMS) entries)"
