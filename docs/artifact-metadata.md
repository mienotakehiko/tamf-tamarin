# Robustness Battery — Artefact Metadata

## Model file provenance

All four `.spthy` models are byte-identical copies from the frozen evidence bundle
(the frozen evidence bundle distributed with the manuscript).

| File                       | Purpose                                                   |
|----------------------------|-----------------------------------------------------------|
| `A_raw.spthy`              | eight-premise raw encoding, no priority annotation         |
| `B_raw_priority.spthy`     | eight-premise raw + `RawPhase[+]` priority annotation      |
| `C_state_carrier.spthy`    | one-carrier `State_Progress` encoding, no priority         |
| `D_state_priority.spthy`   | one-carrier `State_Progress` + `State_Progress[+]` priority |

All four models encode the same bounded four-query pre/post-challenge
observational-equivalence obligation. The rule-by-rule correspondence check
(§3.4 in the manuscript, `scripts/verify_correspondence.py`)
reports `overall = PASS` for A↔C and B↔D with `diff = 0` on all 11 rules.

## Reproducing the timeout-curve command line

The exact command line used for the timeout-curve baseline was:

```
tamarin-prover \
    --diff \
    --prove \
    --heuristic=s \
    --stop-on-trace=dfs \
    --derivcheck-timeout=30 \
    <model>.spthy \
    +RTS -N2 -RTS
```

The Robustness Battery reproduces this command byte-for-byte, changing only
the `--heuristic` argument (sweep of `s S c C p`) and repeating each cell 3
times. All other flags and RTS options are held constant.

## Tamarin heuristic letters (from `tamarin-prover --help`)

Tamarin 1.12.0 exposes the following heuristic letters:

```
--heuristic[=(C|I|O|P|S|c|i|o|p|s|{.})+]
```

| Letter | Meaning                                                | Used in Battery?                                |
|--------|--------------------------------------------------------|------------------------------------------------|
| `s`    | Smart (default for most benchmarks)                    | Yes                                             |
| `S`    | Smart, "consecutive" variant                           | Yes                                             |
| `c`    | Consecutive, no look-ahead                             | Yes                                             |
| `C`    | Fair-goals, "consecutive" variant                      | Yes                                             |
| `p`    | Priority-driven                                        | Yes                                             |
| `i`    | Only-injective ranking                                 | Excluded: not defined for `--diff` mode        |
| `I`    | Only-injective, alternative                            | Excluded: not defined for `--diff` mode        |
| `o`    | Oracle-driven                                          | Excluded: requires a `.oracle` file which the benchmark does not ship |
| `O`    | Oracle-driven, alternative                             | Excluded: same reason as `o`                    |
| `p`    | Priority-driven                                        | Included above                                  |
| `P`    | Priority-driven, alternative                           | Excluded to keep the sweep at 5 distinct policies |

Reference: Tamarin Prover manual §11 "Search heuristics",
`https://tamarin-prover.com/manual/`.

## GHC RTS options

Every run uses `+RTS -N2 -RTS`. This matches the frozen baseline. No memory cap
(`+RTS -M`) is imposed; peak RSS is therefore an upper bound on
live-heap-plus-GC-watermark. The B3 disclosure documents this bound
in the manuscript.

## Environment recording

At the start of each run, `run_battery.sh` writes to `battery.log`:

- UTC timestamp
- hostname
- `tamarin-prover --version` output
- `maude --version` output
- kernel `uname -srm`
- `nproc` core count
- `/proc/meminfo` MemTotal / MemAvailable
- battery configuration (BUDGET, DERIVCHECK, RTS_CORES, HEURISTICS, REPS)

At the end of each run, per-cell peak RSS and wall-clock are captured from
`/usr/bin/time -v` output in each `<tag>.meta` file.

## What "same as the frozen baseline" means

The Battery is designed to be a **strict superset** of the timeout-curve
data at the 300 s budget: the (A, `s`) and (C, `s`) cells reproduce the frozen baseline
cell values within GC/scheduler noise, providing an internal consistency
check between the two experiments. If those two cells deviate materially
from the frozen-baseline medians (71.68 s for C, 300 s TIMEOUT for A), the
battery result should be treated as suspect and the environmental delta
should be investigated before manuscript integration.
