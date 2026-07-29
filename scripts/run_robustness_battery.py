#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pre-registered heuristic robustness battery.

Re-executes conditions A (raw) and C (state carrier) under the four SUPPORTED
Tamarin --diff rankings {s, S, c, C} at a 300s outer budget, three
counterbalanced repetitions per cell, with --derivcheck-timeout=30 and
--stop-on-trace=dfs.

Pre-registered protocol (see preregistration/robustness_battery.md):
  * the 'p' ranking is REJECTED by Tamarin 1.12.0 as unknown and is retained
    as an INVALID-FACTOR record, NOT classified as VERIFIED/TIMEOUT/FALSIFIED;
  * only the supported subset {s,S,c,C} (24 valid runs = 2 variants x 4
    heuristics x 3 reps) is analysed against the pre-registered thresholds.

Expected pattern (paper): C verifies ONLY under s (3/3); A times out in all 12
A-cells; C times out in the other 9 C-cells. Verdict: SECONDARY. A 21-22 GiB
peak-RSS shoulder appears on the carrier under S/c and is disclosed as future
work (P2-G refines the RSS-bound reading).

Usage:
    python3 scripts/run_robustness_battery.py --tamarin tamarin-prover
    python3 scripts/run_robustness_battery.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import time

VARIANTS = {
    "A_raw":     "theories/notion_bench/raw/obseq_raw.spthy",
    "C_carrier": "theories/notion_bench/state_only/obseq_state.spthy",
}
SUPPORTED = ["s", "S", "c", "C"]
PREREG_INVALID = ["p"]  # rejected by Tamarin; retained as invalid-factor record
BUDGET = 300
REPS = 3


def cell(tamarin, variant, theory, heur, rep, dry):
    cmd = [tamarin, "--prove", "--diff", f"--heuristic={heur}",
           "--derivcheck-timeout=30", "--stop-on-trace=dfs", theory]
    printable = " ".join(cmd) + f"   # rep={rep}"
    if dry:
        print(printable)
        return {"variant": variant, "heuristic": heur, "rep": rep,
                "status": "DRY_RUN", "wall_s": ""}
    t0 = time.time()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=BUDGET)
        wall = round(time.time() - t0, 2)
        status = "VERIFIED" if "verified" in p.stdout.lower() else "UNVERIFIED"
    except subprocess.TimeoutExpired:
        wall, status = float(BUDGET), "TIMEOUT"
    return {"variant": variant, "heuristic": heur, "rep": rep,
            "status": status, "wall_s": wall}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tamarin", default="tamarin-prover")
    ap.add_argument("--out", default="evidence/battery_report_v3.json")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if not shutil.which(a.tamarin) and not a.dry_run:
        print(f"[warn] '{a.tamarin}' not on PATH; using --dry-run.")
        a.dry_run = True

    valid_rows, invalid_records = [], []
    for variant, theory in VARIANTS.items():
        for heur in SUPPORTED:
            for rep in range(1, REPS + 1):
                valid_rows.append(cell(a.tamarin, variant, theory, heur, rep, a.dry_run))
        for heur in PREREG_INVALID:
            invalid_records.append({
                "variant": variant, "heuristic": heur,
                "note": "Unknown proof method ranking 'p' -- rejected before "
                        "main proof-search; retained as invalid-factor record, "
                        "not classified.",
            })

    report = {
        "budget_s": BUDGET, "reps_per_cell": REPS,
        "supported_rankings": SUPPORTED,
        "valid_runs": valid_rows,
        "invalid_factor_records": invalid_records,
        "prereg": "preregistration/robustness_battery.md",
        "expected_verdict": "SECONDARY",
    }
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
    print(f"[ok] wrote {a.out} ({len(valid_rows)} valid runs, "
          f"{len(invalid_records)} invalid-factor records)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
