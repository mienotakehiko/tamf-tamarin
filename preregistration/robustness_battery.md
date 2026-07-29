# Pre-registration: Heuristic Robustness Battery

**Registered before execution. Not amended post hoc.**

## Factors
- Variants: `A` (raw, 8-premise) and `C` (state carrier, 1-premise).
- Heuristics (search rankings): `s`, `S`, `c`, `C` (supported) and `p` (registered but **rejected** by Tamarin 1.12.0 as an unknown ranking).
- Outer budget: 300 s. Repetitions: 3 per cell (counterbalanced order).
- Fixed flags: `--diff --derivcheck-timeout=30 --stop-on-trace=dfs`.

## Registered thresholds
- Primary: does the representation-level separation (A timeout vs C verified) hold under a given ranking?
- Verdict rubric: `PRIMARY` if the separation holds under >= 2 supported rankings; `SECONDARY` if it holds under exactly one; `NULL` if under none.

## Registered handling of the `p` factor
`p` is retained as an **invalid-factor record** (the six runs are NOT classified as VERIFIED/TIMEOUT/FALSIFIED). No substitute heuristic is introduced. Only the supported subset `{s,S,c,C}` (24 valid runs) is analysed.

## Result (for reference; see evidence/)
Separation holds under `s` only (C: 3/3 verified; A: 12/12 timeout; C under S/c/C: 9/9 timeout). **Verdict: SECONDARY.** A 21–22 GiB peak-RSS shoulder on the carrier under `S`/`c` is disclosed as future work; P2-G later refines the RSS upper-bound reading.
