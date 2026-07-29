# Robustness Battery corrected post-processing (v3)

**Validation:** `PASS_WITH_REGISTERED_DEVIATION`
**Verdict:** `SECONDARY`
**Scope:** supported Tamarin 1.12.0 diff rankings `{s, S, c, C}`

## Registered deviation

The pre-registered `p` factor was rejected by the installed Tamarin
before main proof search with `Unknown proof method ranking 'p'`.
All six attempted `p` cells are retained as invalid-factor evidence;
they are not treated as proof outcomes.

## Supported-ranking result

- A: 0 verified, 12 timeout, 0 falsified / 12
- C: 3 verified, 9 timeout, 0 falsified / 12
- Verdict reason: original severe-flip absolute threshold reached on supported diff rankings: A_verified=0, C_timeout=9

## Phase evidence

- Derivation-check start/end markers: 24/24 valid cells
- Main proof-search output observed: 3/24 valid cells
- No timestamped derivation-check duration was emitted; numerical
  derivation-check and main-search durations are therefore not claimed.

## Per-cell breakdown

| Variant | Heuristic | Verified | Timeout | Falsified | Wall median (s) | RSS median (GiB) |
|---|---|---:|---:|---:|---:|---:|
| A | `s` | 0 | 3 | 0 | 297.81 | 4.89 |
| A | `S` | 0 | 3 | 0 | 298.07 | 5.14 |
| A | `c` | 0 | 3 | 0 | 296.43 | 4.87 |
| A | `C` | 0 | 3 | 0 | 295.39 | 5.09 |
| C | `s` | 3 | 0 | 0 | 58.4 | 1.02 |
| C | `S` | 0 | 3 | 0 | 297.22 | 21.22 |
| C | `c` | 0 | 3 | 0 | 295.63 | 22.08 |
| C | `C` | 0 | 3 | 0 | 294.96 | 8.07 |
