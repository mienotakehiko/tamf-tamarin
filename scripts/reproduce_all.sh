#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
#
# End-to-end reproduction driver for the three core evaluation scopes.
# Each stage is independent and can be skipped with the matching SKIP_*
# variable. Stages 2 and 3 are static (no Tamarin) and run even when the
# preflight reports a missing Tamarin toolchain; only Stage 1 needs Tamarin.
#
# Prerequisites:
#   - Stage 1 (battery):  Tamarin Prover 1.12.0 + Maude 3.4 on PATH,
#                         Python >= 3.9 with psutil, >= 8 GiB RAM
#                         (>= 40 GiB for the RSS-shoulder measurement).
#   - Stages 2/3 (audit): Python >= 3.8 only, plus the external trees
#                         under external/ (see docs/getting-external-artefacts.md).
#
# Usage:
#   ./scripts/reproduce_all.sh                     # all stages
#   SKIP_BATTERY=1 ./scripts/reproduce_all.sh      # static audits only
#   SKIP_KEMTLS=1 SKIP_XREPO=1 ./scripts/reproduce_all.sh   # battery only
#
# Outputs are written under measurements/<scope>/ and carry no absolute paths.

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$HERE"

log() { printf '\n[reproduce_all] %s\n' "$*" ; }

TLS_REGISTRY="registry/tls_family.json"
FIVEG_REGISTRY="registry/5g_aka_family.json"

# ---------------------------------------------------------------------------
# Stage 0: preflight (advisory; failure does not abort the static stages)
# ---------------------------------------------------------------------------
log "Stage 0: preflight (env + capacity)"
bash scripts/preflight.sh || log "  preflight reported issues (expected without a Tamarin host); static stages will still run"

# ---------------------------------------------------------------------------
# Stage 1: robustness battery (heuristic-scoped state-representation ablation)
# ---------------------------------------------------------------------------
if [ -z "${SKIP_BATTERY:-}" ]; then
  log "Stage 1: robustness battery (24 supported + invalid-factor runs)"
  bash scripts/run_battery.sh
  python3 scripts/analyse_battery.py \
      --runs-dir measurements/robustness-battery/runs
else
  log "Stage 1: skipped (SKIP_BATTERY set)"
fi

# ---------------------------------------------------------------------------
# Stage 2: KEMTLS engineering case (descendant scope) -- static
# ---------------------------------------------------------------------------
if [ -z "${SKIP_KEMTLS:-}" ]; then
  log "Stage 2: KEMTLS audit + patch-fidelity"
  if [ -d external/kemtls-tls13tamarin ]; then
    python3 scripts/audit_tool.py external/kemtls-tls13tamarin \
        --registry "$TLS_REGISTRY" \
        --json measurements/kemtls/audit.json
    if [ -d external/kemtls-tls13tamarin-structured ]; then
      python3 scripts/verify_patch_fidelity.py \
          --baseline external/kemtls-tls13tamarin \
          --variant  external/kemtls-tls13tamarin-structured \
          --output   measurements/kemtls/patch-fidelity.json
    else
      log "  structured variant tree absent; see docs/getting-external-artefacts.md"
    fi
  else
    log "  external/kemtls-tls13tamarin absent; see docs/getting-external-artefacts.md"
  fi
else
  log "Stage 2: skipped (SKIP_KEMTLS set)"
fi

# ---------------------------------------------------------------------------
# Stage 3: cross-repository static audit (tool-reuse scope) -- static
# ---------------------------------------------------------------------------
if [ -z "${SKIP_XREPO:-}" ]; then
  log "Stage 3: cross-repository static audit"
  # Each family is audited with its own declared registry; the classifier
  # core is unchanged (see Contribution C1).
  audit_target() {  # <dir> <registry> <out>
    if [ -d "external/$1" ]; then
      python3 scripts/audit_tool.py "external/$1" --registry "$2" --json "$3"
    else
      log "  external/$1 absent; see docs/getting-external-artefacts.md"
    fi
  }
  audit_target tls13tamarin "$TLS_REGISTRY"   measurements/tls13tamarin/audit.json
  audit_target 5g-aka       "$FIVEG_REGISTRY" measurements/5g-aka/audit.json
else
  log "Stage 3: skipped (SKIP_XREPO set)"
fi

# ---------------------------------------------------------------------------
# Aggregated summary (parses the audit_tool.py JSON schema: n_files, totals)
# ---------------------------------------------------------------------------
log "Aggregated audit summary:"
python3 - <<'PY'
import json, pathlib
found = False
for f in sorted(pathlib.Path("measurements").rglob("audit.json")):
    found = True
    d = json.loads(f.read_text())
    t = d["totals"]
    n = d["n_files"] or 1
    print(f"  {f}: n={d['n_files']}  any-violation={t['any']} ({100*t['any']/n:.1f}%)"
          f"  R={{R1:{t['R1']}, R2:{t['R2']}, R3:{t['R3']}, R4:{t['R4']}}}")
if not found:
    print("  (no audit.json yet -- retrieve the external trees, then re-run stages 2/3)")
PY

log "Reproduction driver finished."
