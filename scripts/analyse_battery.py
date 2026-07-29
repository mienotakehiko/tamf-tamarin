#!/usr/bin/env python3
"""
Aggregate Robustness Battery results into the numbers that feed
the manuscript.

Consumes:
  runs/summary.tsv         (from run_battery.sh)
  runs/phase_timing.tsv    (from extract_phase_timing.py)

Emits:
  runs/battery_report.json    machine-readable summary
  runs/battery_report.md      human-readable report ready to paste into a
                              cover letter / evidence bundle
  runs/table_R1.tex           LaTeX fragment for Table R1 (heuristic sweep matrix)
  runs/table_R2.tex           LaTeX fragment for Table R2 (phase-timing split)
  runs/battery_verdict.txt    one of PRIMARY / PARTIAL_PRIMARY / MIXED / SECONDARY

Verdict rules (matches the pre-registered §3.4bis interpretation logic):
  PRIMARY          : all A cells TIMEOUT (15/15) AND all C cells VERIFIED (15/15)
  PARTIAL_PRIMARY  : all A TIMEOUT AND >=13/15 C VERIFIED (or symmetric)
  MIXED            : any A VERIFIED  OR  any C TIMEOUT (bounded to specific heuristics)
  SECONDARY        : both sides mostly flip -> re-inspect design
"""
from __future__ import annotations
import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-dir", required=True, type=Path)
    args = ap.parse_args()

    summary_rows = read_tsv(args.runs_dir / "summary.tsv")
    phase_rows   = read_tsv(args.runs_dir / "phase_timing.tsv")

    if not summary_rows:
        print(f"ERROR: no summary rows found in {args.runs_dir}/summary.tsv")
        return 2

    # ------------------------------------------------------------------
    # Aggregate per (variant, heuristic)
    # ------------------------------------------------------------------
    cells: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for r in summary_rows:
        cells[(r["variant"], r["heuristic"])].append(r)

    heuristics_order = ["s", "S", "c", "C", "p"]
    variants_order   = ["A", "C"]

    per_cell: dict[str, dict] = {}
    a_all_timeout = True
    c_all_verified = True
    n_a_verified = n_c_timeout = 0
    all_walls_c: list[float] = []

    for v in variants_order:
        for h in heuristics_order:
            cell = cells.get((v, h), [])
            outcomes = [r["outcome"] for r in cell]
            walls    = [float(r["wall_s"]) for r in cell if r["wall_s"] not in ("", "NA")]
            rss_kb   = [int(r["rss_kb"]) for r in cell
                        if r["rss_kb"] not in ("", "NA")]
            key = f"{v}_h{h}"
            n_ver = outcomes.count("VERIFIED")
            n_to  = outcomes.count("TIMEOUT")
            n_oth = len(outcomes) - n_ver - n_to

            per_cell[key] = {
                "variant":   v,
                "heuristic": h,
                "n_reps":    len(outcomes),
                "n_verified": n_ver,
                "n_timeout":  n_to,
                "n_other":    n_oth,
                "wall_s_median": round(statistics.median(walls), 2) if walls else None,
                "wall_s_min":    round(min(walls), 2) if walls else None,
                "wall_s_max":    round(max(walls), 2) if walls else None,
                "rss_kb_median": int(statistics.median(rss_kb)) if rss_kb else None,
                "rss_gib_median": round(statistics.median(rss_kb) / (1024 * 1024), 2)
                                  if rss_kb else None,
            }

            if v == "A" and n_ver > 0:
                a_all_timeout = False
                n_a_verified += n_ver
            if v == "C" and n_to > 0:
                c_all_verified = False
                n_c_timeout += n_to
            if v == "C":
                all_walls_c.extend(walls if outcomes.count("VERIFIED") == len(outcomes) else [])

    # ------------------------------------------------------------------
    # Verdict
    # ------------------------------------------------------------------
    if a_all_timeout and c_all_verified:
        verdict = "PRIMARY"
    elif a_all_timeout and n_c_timeout <= 2:
        verdict = "PARTIAL_PRIMARY"
    elif n_a_verified >= 1 or n_c_timeout >= 3:
        verdict = "MIXED"
    else:
        verdict = "SECONDARY"

    a_verified_cells = [k for k, v in per_cell.items()
                        if v["variant"] == "A" and v["n_verified"] > 0]
    c_timeout_cells  = [k for k, v in per_cell.items()
                        if v["variant"] == "C" and v["n_timeout"] > 0]

    # ------------------------------------------------------------------
    # JSON report
    # ------------------------------------------------------------------
    report = {
        "verdict":            verdict,
        "n_A_verified_total": n_a_verified,
        "n_C_timeout_total":  n_c_timeout,
        "a_verified_cells":   a_verified_cells,
        "c_timeout_cells":    c_timeout_cells,
        "per_cell":           per_cell,
        "phase_timing_summary": {
            "rows": phase_rows,
        },
    }
    out_json = args.runs_dir / "battery_report.json"
    out_json.write_text(json.dumps(report, indent=2))
    print(f"[analyse] wrote {out_json}")

    # ------------------------------------------------------------------
    # Verdict file
    # ------------------------------------------------------------------
    verdict_txt = f"""VERDICT: {verdict}
A(raw) verified count total (out of 15): {n_a_verified}
C(carrier) timeout count total (out of 15): {n_c_timeout}
A verified cells: {a_verified_cells or 'none'}
C timeout cells:  {c_timeout_cells or 'none'}
"""
    (args.runs_dir / "battery_verdict.txt").write_text(verdict_txt)

    # ------------------------------------------------------------------
    # LaTeX Table R1 (heuristic sweep matrix)
    # ------------------------------------------------------------------
    tex_r1 = []
    tex_r1.append("% Table R1: Heuristic sweep matrix (auto-generated)")
    tex_r1.append(r"\begin{table}[tb]")
    tex_r1.append(r"\centering")
    tex_r1.append(r"\caption{Robustness Battery B1: heuristic sweep on A (raw) and C (carrier) variants. Three counter-balanced repetitions per cell at 300\,s outer budget with \texttt{--derivcheck-timeout=30}, \texttt{--stop-on-trace=dfs}, Tamarin~1.12.0.}")
    tex_r1.append(r"\label{tab:robustness-battery-r1}")
    tex_r1.append(r"\scriptsize")
    tex_r1.append(r"\setlength{\tabcolsep}{4pt}")
    tex_r1.append(r"\renewcommand{\arraystretch}{1.1}")
    tex_r1.append(r"\begin{tabular}{@{}lcccc@{}}")
    tex_r1.append(r"\hline")
    tex_r1.append(r"Heuristic & \multicolumn{2}{c}{A (raw)} & \multicolumn{2}{c}{C (carrier)} \\")
    tex_r1.append(r" & Outcome & Wall (s) & Outcome & Wall (s) \\")
    tex_r1.append(r"\hline")
    for h in heuristics_order:
        a = per_cell.get(f"A_h{h}", {})
        c = per_cell.get(f"C_h{h}", {})
        a_out = f"{a.get('n_verified', 0)}/{a.get('n_reps', 0)} verified" \
                if a.get("n_verified", 0) > 0 \
                else f"{a.get('n_timeout', 0)}/{a.get('n_reps', 0)} timeout"
        c_out = f"{c.get('n_verified', 0)}/{c.get('n_reps', 0)} verified" \
                if c.get("n_verified", 0) > 0 \
                else f"{c.get('n_timeout', 0)}/{c.get('n_reps', 0)} timeout"
        a_wall = "---" if a.get("n_verified", 0) == 0 \
                       else f"{a['wall_s_median']:.2f}"
        c_wall = "---" if c.get("n_verified", 0) == 0 \
                       else f"{c['wall_s_median']:.2f}"
        tex_r1.append(f"\\texttt{{{h}}} & {a_out} & {a_wall} & {c_out} & {c_wall} \\\\")
    tex_r1.append(r"\hline")
    tex_r1.append(r"\end{tabular}")
    tex_r1.append(r"\end{table}")
    (args.runs_dir / "table_R1.tex").write_text("\n".join(tex_r1) + "\n")

    # ------------------------------------------------------------------
    # LaTeX Table R2 (phase-timing split)
    # ------------------------------------------------------------------
    tex_r2 = []
    tex_r2.append("% Table R2: Phase-timing split (auto-generated)")
    tex_r2.append(r"\begin{table}[tb]")
    tex_r2.append(r"\centering")
    tex_r2.append(r"\caption{Robustness Battery B2: derivation-check phase vs.\ main proof-search phase, aggregated per (variant, heuristic). ``$<10$ (marker seen)'' means the phase completed before Tamarin printed an explicit timing.}")
    tex_r2.append(r"\label{tab:robustness-battery-r2}")
    tex_r2.append(r"\scriptsize")
    tex_r2.append(r"\setlength{\tabcolsep}{4pt}")
    tex_r2.append(r"\renewcommand{\arraystretch}{1.1}")
    tex_r2.append(r"\begin{tabular}{@{}llccc@{}}")
    tex_r2.append(r"\hline")
    tex_r2.append(r"Variant & Heuristic & Deriv-check (s) & Main proof (s) & Total (s) \\")
    tex_r2.append(r"\hline")
    # Aggregate phase rows by (variant, heuristic) using the median of the 3 reps
    by_cell: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for r in phase_rows:
        by_cell[(r["variant"], r["heuristic"])].append(r)
    for v in variants_order:
        for h in heuristics_order:
            reps = by_cell.get((v, h), [])
            if not reps:
                continue
            def med(field: str) -> str:
                vals = []
                sentinel = None
                for r in reps:
                    x = r.get(field, "NA")
                    try:
                        vals.append(float(x))
                    except ValueError:
                        sentinel = x
                if vals:
                    return f"{statistics.median(vals):.2f}"
                return sentinel or "NA"
            tex_r2.append(f"\\texttt{{{v}}} & \\texttt{{{h}}} & {med('derivcheck_s')} & {med('main_s')} & {med('total_s')} \\\\")
    tex_r2.append(r"\hline")
    tex_r2.append(r"\end{tabular}")
    tex_r2.append(r"\end{table}")
    (args.runs_dir / "table_R2.tex").write_text("\n".join(tex_r2) + "\n")

    # ------------------------------------------------------------------
    # Markdown report
    # ------------------------------------------------------------------
    md = []
    md.append("# Robustness Battery report")
    md.append("")
    md.append(f"**Verdict**: `{verdict}`")
    md.append("")
    md.append(f"- A (raw) verifications across all 15 attempts: **{n_a_verified}**")
    md.append(f"- C (carrier) timeouts across all 15 attempts: **{n_c_timeout}**")
    md.append("")
    md.append("## Interpretation guide")
    md.append("")
    md.append("| Verdict | Meaning | Manuscript impact |")
    md.append("|---|---|---|")
    md.append("| `PRIMARY`         | A all timeout (15/15) AND C all verified (15/15) | C2 upgrades to heuristic-robust bounded claim |")
    md.append("| `PARTIAL_PRIMARY` | A all timeout AND C fails in ≤2 cells             | C2 keeps causal reading; add narrow disclosure |")
    md.append("| `MIXED`           | Some A verify or ≥3 C timeout                     | C2 narrows to specific heuristic subset {…}     |")
    md.append("| `SECONDARY`       | Both sides largely flip                            | Redesign required, discuss with reviewer         |")
    md.append("")
    md.append("## Per-cell breakdown")
    md.append("")
    md.append("| Variant | Heuristic | Reps | Verified | Timeout | Other | Wall median (s) | Peak RSS median (GiB) |")
    md.append("|---|---|---|---|---|---|---|---|")
    for v in variants_order:
        for h in heuristics_order:
            c = per_cell[f"{v}_h{h}"]
            md.append(f"| {v} | `{h}` | {c['n_reps']} | {c['n_verified']} | {c['n_timeout']} | {c['n_other']} | {c['wall_s_median']} | {c['rss_gib_median']} |")
    md.append("")
    md.append("## Phase timing")
    md.append("")
    md.append("See `phase_timing.tsv` for raw per-run data and `table_R2.tex` for the paper-ready table.")
    md.append("")
    (args.runs_dir / "battery_report.md").write_text("\n".join(md))
    print(f"[analyse] wrote {args.runs_dir}/battery_report.md")
    print(f"[analyse] verdict: {verdict}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
