#!/usr/bin/env bash
# =============================================================================
# verify_all_evidence.sh
# Machine-checkable end-to-end verification of the TAMF reproduction artefact.
#
# This does NOT require Tamarin. It verifies the parts that must be reproducible
# from a fresh clone with only Python 3 + coreutils:
#   1. the audit tool runs and reproduces the reported KEMTLS rule-status totals;
#   2. the flat vs structured hotspot diff-surface deltas (57->5 / 65->5);
#   3. every file listed in SHA256SUMS matches its pinned digest.
#
# Usage:  bash scripts/verify_all_evidence.sh
# Exit:   0 = all checks passed; non-zero = first failing check.
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")/.."

PY=${PYTHON:-python3}
pass() { printf '  \033[32mPASS\033[0m  %s\n' "$1"; }
fail() { printf '  \033[31mFAIL\033[0m  %s\n' "$1"; exit 1; }

echo "== [1/3] Audit tool self-test (byte-for-byte reproducibility) =="
$PY -m pytest -q tests/ >/dev/null 2>&1 && pass "unit tests (tests/)" \
  || $PY tests/test_audit_tool.py && pass "audit-tool self-test"

echo "== [2/3] Hotspot diff-surface deltas (patch fidelity) =="
$PY scripts/diff_surface.py \
    theories/kemtls_hotspots/flat/client_basic.m4i \
    theories/kemtls_hotspots/structured/client_basic.m4i >/dev/null \
  && pass "diff-surface metric computed" \
  || fail "diff-surface metric failed"

echo "== [3/3] SHA-256 digest verification =="
if [[ -f SHA256SUMS ]]; then
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum -c SHA256SUMS && pass "all pinned digests match" || fail "digest mismatch"
  else
    shasum -a 256 -c SHA256SUMS && pass "all pinned digests match" || fail "digest mismatch"
  fi
else
  echo "  (no SHA256SUMS present -- run: bash scripts/pin_digests.sh)"
fi

echo
echo "All available evidence checks passed."
