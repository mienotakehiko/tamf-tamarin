# Robustness Battery — Pre-registration for STTI2026 rev084 §3.4bis

This document freezes the design of the Robustness Battery **before any
measurement is taken**, so that reviewers can verify the outcome was not
selected post-hoc.

## Motivation

The rev083r2 strict review flagged three residual confounds for the
state-representation causal claim (Contribution C2):

1. **Heuristic dependence** — the 2×2 ablation of §3.4 fixes `--heuristic=s`.
2. **Derivation-check phase interference** — outer 300 s budgets could be consumed
   by derivation-check precomputation rather than main proof-search.
3. **Memory-observation confounding** — peak RSS could reflect GHC watermark
   rather than state-space expansion.

## Pre-registered design

### B1 — Heuristic sweep

- **Factors under test**: variant × heuristic (2 × 5 crossed).
- **Variants**: A (`raw`, eight-premise) and C (`state_carrier`, one-carrier `State_Progress`).
  B and D differ from A/C only by priority annotation; §3.4 already showed
  that the priority factor does not flip the outcome, so B/D are omitted
  from the battery to save compute budget while preserving the causal test.
- **Heuristics**: `s S c C p` (5 heuristics).
  These are the five static heuristics accepted by Tamarin 1.12.0 for
  observational-equivalence models. The letter `i / I` (only-injective)
  is not accepted for `--diff` mode and is excluded, not cherry-picked;
  the `o / O` letter is an oracle-driven heuristic requiring a `.oracle`
  file and is excluded because the benchmark ships no such file (adding
  one would introduce a new experimental factor).
- **Repetitions**: 3 counter-balanced repetitions per (variant, heuristic) cell.
  Counter-balancing: on odd-numbered reps, C is run before A within a heuristic;
  on even-numbered reps, A is run before C. Prevents cache-warming bias.
- **Outer budget**: 300 s wall-clock (identical to the §3.4 middle budget).
  Not a curve: this asks whether raw needs a *different heuristic*, not more time.
- **Fixed side-conditions**: `--diff --prove --stop-on-trace=dfs`,
  `--derivcheck-timeout=30`, `+RTS -N2 -RTS`, Tamarin 1.12.0.
  These match rev082's timeout-curve baseline exactly so that the sweep is
  strictly comparable to §3.4 data.
- **Total runs**: 2 × 5 × 3 = **30**.

### B2 — Derivation-check phase timing

- **Extractor**: `scripts/extract_phase_timing.py` parses Tamarin's stderr
  for the following markers (in order):
  1. `Analysing` or `Loading` — parse phase start
  2. `well-formedness` — well-formedness check completion
  3. `Precomputation` or `Starting derivation` — derivation-check phase start
  4. `End of precomputation` or `Derivation checks complete` — derivation-check
     phase end
  5. `Proving lemmas` — main proof-search phase start
- **Explicit timing**: if Tamarin prints an explicit duration
  (`Precomputation completed in 3.42s` and variants), the extractor uses it.
  Otherwise the extractor records `< 10 (marker seen)` iff the "end of
  precomputation" or "proving lemmas" marker is present in the stderr,
  which is the operational fact §3.4bis needs.
- **No new measurement**: B2 reuses the stderr already produced by the B1
  runs. The extractor is a pure post-processing step.

### B3 — RSS confound disclosure

- **No measurement**. The manuscript will state that peak RSS is reported
  without `+RTS -M` cap; the monotone growth on A/B is therefore an upper
  bound on live-heap-plus-GC-watermark, and the qualitative asymmetry
  (raw: growth; carrier: flat) is what is claimed, not the interpretation
  of absolute magnitude. This disclosure is pre-committed here.

## Pre-registered interpretation rules

| Empirical outcome                                                    | Verdict            | Impact on Contribution C2                                                                                              |
|-----------------------------------------------------------------------|--------------------|-------------------------------------------------------------------------------------------------------------------------|
| A: 15/15 timeout **AND** C: 15/15 verified                            | `PRIMARY`          | C2 upgrades to "bounded and heuristic-robust across `{s, S, c, C, p}`"                                                  |
| A: 15/15 timeout **AND** C: 13–14/15 verified                         | `PARTIAL_PRIMARY`  | C2 keeps causal reading; add "C verifies in 13(or 14)/15 attempts; residual 1–2 timeouts occur in cells {…}"            |
| Any A verifies **OR** C timeout count ≥ 3                              | `MIXED`            | C2 narrows to a specific heuristic subset {…} and adds one entry to the forbidden-overclaim list                       |
| A verifies in ≥ 8 cells **OR** C times out in ≥ 8 cells                | `SECONDARY`        | Design revision required; report as a null result and re-consult reviewer before manuscript submission                 |

All four verdicts are covered a priori; there is no verdict category
without a pre-committed manuscript action. The `analyse_battery.py` script
computes the verdict mechanically from `summary.tsv`.

## Pre-committed manuscript text sketch (subject only to verdict category)

- **§3.4bis intro**: three-sentence statement of B1/B2/B3 design and its
  three-confound remit; unchanged regardless of verdict.
- **§3.4bis B1 results**: one paragraph reporting the 5×2 outcome matrix;
  wording template selected by verdict.
- **§3.4bis B2 results**: one paragraph reporting phase-timing summary
  (`< 10 s` in all A/B/C/D cells if the marker fires; else explicit numbers).
- **§3.4bis B3 disclosure**: one sentence stating the peak-RSS bound.
- **§3.4bis closing**: one sentence stating the residual bounds
  ("under the tested heuristic set {`s, S, c, C, p`} and the tested budget"),
  never claiming heuristic invariance beyond that set.

## Deviations and how they are handled

- **Any script change during the run**: the run is invalidated and restarted
  from scratch. Pre-registration does not permit adaptive design.
- **Machine crash / power loss mid-run**: partial `summary.tsv` is discarded;
  battery is restarted after fixing the hardware condition.
- **Tamarin version mismatch**: if `preflight.sh` reports a version other
  than 1.10.0 or 1.12.0, the run proceeds only if the version is >=1.12.0
  (never below 1.10.0); the actual version is recorded in every `.meta`
  file's environment header and in `battery.log`.

## Sign-off

Pre-registration frozen at:  **[user to append UTC timestamp when the
battery is launched, in `battery.log` first line]**
