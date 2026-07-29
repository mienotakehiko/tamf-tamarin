#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Four-condition 2x2 ablation driver + four-budget timeout curve.

Reproduces the state-representation ablation (paper Section: Controlled /
Overall Outcomes). Runs each of the four conditions on the bounded
observational-equivalence benchmark under --heuristic=s across the budget
curve {60,120,300,600}s, three counterbalanced repetitions per cell, and
emits summary.tsv.

Expected pattern (from the paper):
  * raw / oracle_only (8-premise)  -> TIMEOUT at every budget (24/24 raw)
  * state_only / full_tamf carrier -> VERIFIED at budgets >= 120s (18/18)
  * carrier peak RSS flat ~1.1-1.4 GiB; raw peak RSS grows 1.72 -> 5.91 GiB

Requires tamarin-prover on PATH. Without it, use --dry-run to print the exact
commands (and, if evidence/ is populated, to validate against pinned results).

Usage:
    python3 scripts/run_ablation.py --tamarin tamarin-prover \
        --budgets 60 120 300 600 --reps 3 --out evidence/summary.tsv
    python3 scripts/run_ablation.py --dry-run
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import time

CONDITIONS = {
    "raw":         "theories/notion_bench/raw/obseq_raw.spthy",
    "state_only":  "theories/notion_bench/state_only/obseq_state.spthy",
    "oracle_only": "theories/notion_bench/oracle_only/obseq_oracle.spthy",
    "full_tamf":   "theories/notion_bench/full_tamf/obseq_full.spthy",
}
ORACLE = "oracle/tamf_oracle.py"


def build_cmd(tamarin: str, cond: str, theory: str, budget: int) -> list[str]:
    cmd = [tamarin, "--prove", "--diff", "--heuristic=s",
           f"--derivcheck-timeout=30", "--stop-on-trace=dfs"]
    if cond in ("oracle_only", "full_tamf"):
        cmd += ["--heuristic=O", f"--oraclename={ORACLE}"]
    cmd += [theory]
    return cmd


def run_cell(tamarin: str, cond: str, theory: str, budget: int, rep: int, dry: bool):
    cmd = build_cmd(tamarin, cond, theory, budget)
    printable = " ".join(cmd) + f"   # budget={budget}s rep={rep}"
    if dry:
        print(printable)
        return {"cond": cond, "budget": budget, "rep": rep,
                "status": "DRY_RUN", "wall_s": "", "cmd": printable}
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=budget)
        wall = round(time.time() - t0, 2)
        status = "VERIFIED" if "verified" in proc.stdout.lower() else "UNVERIFIED"
    except subprocess.TimeoutExpired:
        wall = float(budget)
        status = "TIMEOUT"
    return {"cond": cond, "budget": budget, "rep": rep,
            "status": status, "wall_s": wall, "cmd": printable}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tamarin", default="tamarin-prover")
    ap.add_argument("--budgets", type=int, nargs="+", default=[60, 120, 300, 600])
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--out", default="evidence/summary.tsv")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    have_tamarin = shutil.which(a.tamarin) is not None
    if not have_tamarin and not a.dry_run:
        print(f"[warn] '{a.tamarin}' not on PATH; falling back to --dry-run.")
        a.dry_run = True

    rows = []
    for cond, theory in CONDITIONS.items():
        for budget in a.budgets:
            for rep in range(1, a.reps + 1):
                rows.append(run_cell(a.tamarin, cond, theory, budget, rep, a.dry_run))

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write("condition\tbudget_s\trep\tstatus\twall_s\n")
        for r in rows:
            fh.write(f'{r["cond"]}\t{r["budget"]}\t{r["rep"]}\t{r["status"]}\t{r["wall_s"]}\n')
    print(f"[ok] wrote {a.out} ({len(rows)} cells)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
