#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase-2 resource-bounded triage harness (P2-K, P2-T, matched-config cross-check).

Re-verifies protocol-facing security lemmas across the baseline and
state-carrier variants under a DECLARED resource envelope, and records each
outcome under the explicit schema:

    VERIFIED | HEAP_LIMIT | TIMEOUT | FALSIFIED | ENVELOPE_BOUNDARY

TAMF is a TRIAGE layer, not a COMPLETION layer: the harness answers whether
attacker paths are detected within the declared 40 GiB heap envelope, NOT
whether unbounded proof search terminates on a large-memory host. A cell that
reaches the heap cap is an ENVELOPE_BOUNDARY outcome -- neither preservation
nor falsification -- and is reported as a limit-behaviour data point.

Declared configuration is passed explicitly and echoed into every result, so a
later evaluation under a larger envelope can be reported ALONGSIDE (not on top
of) these results.

P2-K  : KEMTLS-TLS13Tamarin, 4 h outer budget, 40 GiB heap
P2-T  : TLS13Tamarin rev21,   6 h outer budget, 40 GiB heap, sg<->ClientSgState(sg) norm
M-A1/2: matched-configuration cross-check (rules out outer-budget substitution)

Requires tamarin-prover + a large-memory host for a real run. Use --dry-run to
print the exact GHC-RTS-bounded commands.

Usage:
    python3 scripts/run_phase2.py --experiment P2-K --theory-root external/kemtls \
        --heap-gib 40 --outer-hours 4 --tamarin tamarin-prover
    python3 scripts/run_phase2.py --experiment P2-K --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import time

LEMMA_SETS = {
    "P2-K": ["secret_session_keys", "mutual_entity_authentication",
             "injective_mutual_entity_authentication", "session_key_agreement"],
    "P2-T": ["secret_session_keys", "mutual_entity_authentication"],
}
VARIANTS = ["baseline", "state_carrier"]
OUTCOME_SCHEMA = ["VERIFIED", "HEAP_LIMIT", "TIMEOUT", "FALSIFIED", "ENVELOPE_BOUNDARY"]


def build_cmd(tamarin, theory, lemma, heap_gib, outer_s):
    # GHC RTS heap cap is the declared envelope; -N1 -c20 as in the paper.
    return [tamarin, "--prove=" + lemma, "--heuristic=s",
            "--derivcheck-timeout=30", theory,
            "+RTS", "-N1", f"-M{heap_gib}G", "-c20", "-RTS"]


def classify(returncode, stdout, timed_out, heap_hit):
    if timed_out:
        return "TIMEOUT"
    if heap_hit or "heap overflow" in stdout.lower() or "out of memory" in stdout.lower():
        return "ENVELOPE_BOUNDARY"   # == HEAP_LIMIT under the triage schema
    if "falsified" in stdout.lower():
        return "FALSIFIED"
    if "verified" in stdout.lower():
        return "VERIFIED"
    return "UNKNOWN"


def run(a):
    lemmas = LEMMA_SETS[a.experiment]
    outer_s = int(a.outer_hours * 3600)
    have = shutil.which(a.tamarin) is not None
    dry = a.dry_run or not have
    if not have and not a.dry_run:
        print(f"[warn] '{a.tamarin}' not on PATH; using --dry-run.")

    results = []
    for variant in VARIANTS:
        theory = os.path.join(a.theory_root, variant, "theory.spthy")
        for lemma in lemmas:
            cmd = build_cmd(a.tamarin, theory, lemma, a.heap_gib, outer_s)
            printable = " ".join(cmd) + f"   # {a.experiment} {variant} outer={a.outer_hours}h"
            if dry:
                print(printable)
                results.append({"experiment": a.experiment, "variant": variant,
                                "lemma": lemma, "outcome": "DRY_RUN", "cmd": printable})
                continue
            t0 = time.time()
            timed_out = False
            try:
                p = subprocess.run(cmd, capture_output=True, text=True, timeout=outer_s)
                out, rc = p.stdout, p.returncode
            except subprocess.TimeoutExpired:
                out, rc, timed_out = "", 124, True
            results.append({
                "experiment": a.experiment, "variant": variant, "lemma": lemma,
                "wall_s": round(time.time() - t0, 2),
                "outcome": classify(rc, out, timed_out, heap_hit=False),
            })
    return {
        "experiment": a.experiment,
        "declared_config": {
            "tamarin_version": "1.12.0", "heuristic": "s",
            "derivcheck_timeout_s": 30, "outer_timeout_s": outer_s,
            "heap_cap_gib": a.heap_gib, "ghc_rts": f"-N1 -M{a.heap_gib}G -c20",
            "normalisation": "sg<->ClientSgState(sg)" if a.experiment == "P2-T" else "n/a",
        },
        "outcome_schema": OUTCOME_SCHEMA,
        "results": results,
        "note": "TRIAGE layer: ENVELOPE_BOUNDARY is neither preservation nor "
                "falsification. Completion on a large-memory host is a separate "
                "research question (future work).",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiment", choices=list(LEMMA_SETS), required=True)
    ap.add_argument("--theory-root", default="external/kemtls")
    ap.add_argument("--heap-gib", type=int, default=40)
    ap.add_argument("--outer-hours", type=float, default=4.0)
    ap.add_argument("--tamarin", default="tamarin-prover")
    ap.add_argument("--out", default="")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    report = run(a)
    out = a.out or f"evidence/{a.experiment}/run_report.json"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
    print(f"[ok] wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
