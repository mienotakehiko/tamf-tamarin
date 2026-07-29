#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
#
# End-to-end reproduction driver for the three evaluation scopes reported
# in the manuscript.  Each stage is independent and can be skipped with
# the corresponding SKIP_* environment variable.
#
# Prerequisites:
#   - Tamarin Prover 1.10.0 and/or 1.12.0 on PATH
#     (see external/frozen-commits.txt for exact revisions)
#   - Maude 3.4 on PATH
#   - Python >= 3.9 with the `psutil` package
#   - >=8 GiB RAM  (scope A requires >=8 GiB; scope B pre-registration
#                   requires >=32 GiB for the RSS shoulder measurement)
#   - Optional: `git` to clone the external KEMTLS / TLS13Tamarin /
#               5G-AKA trees at frozen commits
#
# Usage:
#   ./scripts/reproduce_all.sh            # run all stages
#   SKIP_BATTERY=1 ./scripts/reproduce_all.sh
#   SKIP_KEMTLS=1  ./scripts/reproduce_all.sh
#   SKIP_XREPO=1   ./scripts/reproduce_all.sh
#
# Outputs are written under measurements/<scope>/runs/ and are
# self-contained (no absolute paths in emitted JSON/TSV).

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$HERE"

log() { printf '\n[reproduce_all] %s\n' "$*" ; }

# ---------------------------------------------------------------------------
# Stage 0: preflight
# ---------------------------------------------------------------------------
log "Stage 0: preflight (env + capacity)"
bash scripts/preflight.sh

# ---------------------------------------------------------------------------
# Stage 1: robustness battery (heuristic-scoped state-representation ablation)
# ---------------------------------------------------------------------------
if [ -z "${SKIP_BATTERY:-}" ]; then
  log "Stage 1: robustness battery (24 supported + 6 invalid-factor runs)"
  bash scripts/run_battery.sh
  python3 scripts/analyse_battery.py \
      --runs-dir measurements/robustness-battery/runs \
      --output   measurements/robustness-battery/runs
else
  log "Stage 1: skipped (SKIP_BATTERY set)"
fi

# ---------------------------------------------------------------------------
# Stage 2: KEMTLS engineering case (descendant scope)
# ---------------------------------------------------------------------------
if [ -z "${SKIP_KEMTLS:-}" ]; then
  log "Stage 2: KEMTLS patch-fidelity + audit"
  if [ -d external/kemtls-tls13tamarin ]; then
    python3 scripts/audit_tool.py \
        --root  external/kemtls-tls13tamarin \
        --output measurements/kemtls/audit.json
    python3 scripts/verify_patch_fidelity.py \
        --baseline external/kemtls-tls13tamarin \
        --variant  external/kemtls-tls13tamarin-structured \
        --output   measurements/kemtls/patch-fidelity.json \
        || true  # keep going even if variant tree is not checked out
  else
    log "  external/kemtls-tls13tamarin not present; see docs/getting-external-artefacts.md"
  fi
else
  log "Stage 2: skipped (SKIP_KEMTLS set)"
fi

# ---------------------------------------------------------------------------
# Stage 3: cross-repository static audit (tool-reuse scope)
# ---------------------------------------------------------------------------
if [ -z "${SKIP_XREPO:-}" ]; then
  log "Stage 3: cross-repository static audit"
  for target in tls13tamarin 5g-aka; do
    if [ -d "external/${target}" ]; then
      python3 scripts/audit_tool.py \
          --root  "external/${target}" \
          --output "measurements/${target}/audit.json"
    else
      log "  external/${target} not present; see docs/getting-external-artefacts.md"
    fi
  done
else
  log "Stage 3: skipped (SKIP_XREPO set)"
fi

log "All stages complete.  Aggregated summary:"
python3 - <<'PY'
import json, pathlib
for f in sorted(pathlib.Path("measurements").rglob("audit.json")):
    d = json.loads(f.read_text())
    print(f"  {f}: n={d['n_files']}  any-violation={d['any_violation_count']}"
          f" ({d['any_violation_rate']*100:.1f}%)  R={d['rule_counts']}")
PY
