# Robustness Battery — Pre-registration

This document freezes the design of the Robustness Battery **before any
measurement is taken**, so that reviewers can verify the outcome was not
selected post-hoc.

## Motivation

An internal strict review flagged three residual confounds for the
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
  These match the timeout-curve baseline exactly so that the sweep is
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
| A verifies in ≥ 8 cells **OR** C times out in ≥ 8 cells                | `SECONDARY`        | Design revision required; report as a null result               |

All four verdicts are covered a priori; there is no verdict category
without a pre-committed manuscript action. The `analyse_battery.py` script
computes the verdict mechanically from `summary.tsv`.

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

---

## Post-hoc addendum

The pre-registered design and its four-verdict interpretation rules above
are **not amended**. This addendum records two post-hoc analyses added
after the pre-registered battery had completed and after the SECONDARY
verdict had been assigned. Neither analysis changes the SECONDARY verdict
or the pre-registered manuscript action; both address strict-review
comments on the mechanism-level attribution of Contribution C2.

### A1 — Wall-clock co-growth analysis for the timeout-curve

**Trigger**: An internal strict review comment that peak-RSS monotone growth on A
(raw) could be a GHC generational-GC watermark artefact rather than
proof-search state expansion.

**Analysis**: For the timeout-curve measurements already collected under
the pre-registered protocol, the wall-clock consumed on A
at the four budgets alongside the pre-registered peak-RSS values.
Observed (from
`measurements/timeout-curve/A_raw-{60,120,300,600}s-rep{1,2,3}.time.txt`):

| Budget (s) | Mean wall-clock A (s) | Peak-RSS range A (GiB) |
|-----------:|----------------------:|------------------------:|
| 60         | 61.4                  | 1.68 – 1.97             |
| 120        | 122.7                 | 2.06 – 2.13             |
| 300        | 306.8                 | 3.24 – 3.76             |
| 600        | 610.5                 | 5.45 – 5.94             |

Wall-clock scales as ≈100 % of the outer budget in every cell, which is
consistent with active proof-search throughout each timeout and
inconsistent with the process idling in a GC pause. Under joint
interpretation with the peak-RSS growth, the direction of RSS change is
attributable to proof-search state expansion rather than to
generational-GC watermark accumulation. **The pre-committed B3 caveat
("peak RSS is an upper bound on live-heap-plus-GC-watermark; absolute
magnitudes are not tight state-space measurements") is unchanged** and
applies to absolute magnitudes; the addendum concerns only the direction
of change.

**Impact on verdict**: none. The SECONDARY verdict is unchanged. The
manuscript text of §3 (Overall Outcomes, timeout-curve paragraph) is
revised to state both quantities (wall-clock and RSS) jointly, with the
B3 caveat referenced inline.

### A2 — Mechanism-level attribution of the RSS shoulder under `-S`/`-c`

**Trigger**: An internal strict review comment that the wording
("plausible cache-inflation mechanism" for the 21–22 GiB peak RSS on the
carrier under `-S` and `-c`) attributes an internal mechanism to Tamarin
without evidence that could be gathered from `--diff`-mode observations
alone.

**Analysis**: No new experiment is added. Instead, the
mechanistic attribution is removed from the manuscript. The 21–22 GiB peak RSS
observed on the carrier under `-S`/`-c` is reported as an empirical
pattern only; identifying its internal mechanism would require
instrumenting Tamarin's proof-search kernel (goal-ranking traces,
substitution-cache statistics via GHC's `+RTS -s`), which was not part
of the pre-registered battery and is disclosed as future work.

**Impact on verdict**: none. The SECONDARY verdict, the four-verdict
interpretation table, and the pre-committed manuscript action are all
unchanged. The manuscript text of §3.4 (Robustness Battery
Verdict paragraph) records the RSS shoulder as an empirical pattern and
disclaims mechanistic attribution.

### Files affected by this addendum

The following files ship with the evidence bundle for this pre-registration:

- `measurements/timeout-curve/A_raw-*.time.txt` and
  `measurements/timeout-curve/C_state_carrier-*.time.txt` — the
  wall-clock and peak-RSS raw data underlying A1 (already collected
  under the original pre-registration; no re-execution).
- `runs/battery_report_v3.md` and `runs/battery_validation_v3.txt` —
  unchanged; verdict remains `SECONDARY`, validation remains
  `PASS_WITH_REGISTERED_DEVIATION`.
- `docs/deviation_notice_v3.md` — unchanged; documents the invalid `p`
  factor rejected by Tamarin 1.12.0.

### Compliance statement

Neither A1 nor A2 modifies any measurement, any verdict, or any
pre-committed manuscript action. Both are strict-review-driven
refinements of how the pre-registered data is discussed in the
manuscript, not changes to the data or its interpretation rules.
