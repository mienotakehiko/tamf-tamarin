# Robustness battery -- measurements

This directory holds the pre-registered heuristic robustness battery
(Section "Robustness Battery" of the manuscript).  It measures whether
the state-representation ablation reported in the primary benchmark
(scope A) generalises across Tamarin's supported `--diff` rankings.

## Design (as pre-registered)

- Factors: variant ∈ {A_raw, C_state_carrier} × heuristic ∈ {s, S, c, C, p}
- Repetitions per cell: 3
- Outer wall-clock budget: 300 s
- Tamarin: 1.12.0
- Total: 2 × 5 × 3 = **30** runs

`p` is not a supported ranking in Tamarin 1.12.0.  All six `A/C × p`
runs terminate before main proof search with
`Unknown proof method ranking 'p'` and are recorded as an
**invalid experimental factor** rather than TIMEOUT/VERIFIED.  See
[`../../docs/deviation_notice_v3.md`](../../docs/deviation_notice_v3.md).

The pre-registered analysis targets the **24-run supported subset**
{s, S, c, C}.

## Pre-registered verdict thresholds

| Verdict          | Rule                                                |
|------------------|-----------------------------------------------------|
| PRIMARY          | C_timeout ≤ 3 AND A_verified ≤ 3                    |
| PARTIAL_PRIMARY  | 3 < C_timeout ≤ 8 AND A_verified ≤ 3                |
| MIXED            | A_verified > 3                                      |
| **SECONDARY**    | **C_timeout ≥ 8 AND A_verified ≤ 3**                |

## Observed outcome

- Valid runs: **24/24**
- C_timeout = **9** (C times out under S, c, C in every repetition)
- A_verified = **0** (A always times out)
- Verdict: **SECONDARY**

## Files

- `runs/summary.tsv` -- one line per run (variant, heuristic, rep, wall,
  outcome, peak RSS)
- `runs/phase_evidence_v3.tsv` -- derivation-check vs main-proof timing
  where extractable from stderr
- `runs/battery_report_v3.md` -- human-readable report
- `runs/battery_validation_v3.txt` -- machine-checked validation
  (`PASS_WITH_REGISTERED_DEVIATION`)
- `runs/table_R1_v3.tex`, `runs/table_R2_v3.tex` -- LaTeX-ready tables
  cited by the manuscript
- `runs/deviation_notice_v3.md` -- registered deviation record for the
  invalid `p` factor

Re-running the battery is described in
[`../../README.md#3-reproducing-the-robustness-battery`](../../README.md).
