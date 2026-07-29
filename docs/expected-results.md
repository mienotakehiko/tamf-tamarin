# Expected results

The tables below reproduce the headline numbers reported in the
manuscript.  If your local run deviates materially from these values,
please compare your environment against `docs/artifact-metadata.md` and
`external/frozen-commits.txt` before filing a reproduction issue.

## 1. Robustness battery (state-representation ablation, heuristic-scoped)

Pre-registered budget = **300 s**, three counterbalanced repetitions per
cell.  Supported heuristics are `{s, S, c, C}`; `p` is recorded as an
invalid experimental factor (`Unknown proof method ranking 'p'`).

| Variant / heuristic | verified | timeout | median wall-clock (s) | peak RSS |
|---------------------|:--------:|:-------:|-----------------------:|---------:|
| A_raw   `-s`        |  0/3     |  3/3    |  297.81                | ~4.89 GiB |
| A_raw   `-S`        |  0/3     |  3/3    |  298.07                | ~5.14 GiB |
| A_raw   `-c`        |  0/3     |  3/3    |  296.43                | ~4.87 GiB |
| A_raw   `-C`        |  0/3     |  3/3    |  295.39                | ~5.09 GiB |
| C_state_carrier `-s`|  3/3     |  0/3    |  **58.40**             | **~1.02 GiB** |
| C_state_carrier `-S`|  0/3     |  3/3    |  297.22                | ~21.22 GiB |
| C_state_carrier `-c`|  0/3     |  3/3    |  295.63                | ~22.08 GiB |
| C_state_carrier `-C`|  0/3     |  3/3    |  294.96                | ~8.07 GiB  |

Pre-registered verdict: **SECONDARY** (24 valid runs; C_timeout = 9,
threshold = 8; A_verified = 0).  Deviation notice for the invalid `p`
factor: [`measurements/robustness-battery/runs/deviation_notice_v3.md`](../measurements/robustness-battery/runs/deviation_notice_v3.md).

Machine-readable evidence:

- `measurements/robustness-battery/runs/summary.tsv`
- `measurements/robustness-battery/runs/phase_evidence_v3.tsv`
- `measurements/robustness-battery/runs/battery_report_v3.md`
- `measurements/robustness-battery/runs/battery_validation_v3.txt`
- `measurements/robustness-battery/runs/table_R1_v3.tex`
- `measurements/robustness-battery/runs/table_R2_v3.tex`

## 2. KEMTLS engineering case (descendant scope)

| Hotspot                        | flat lines | flat hunks (U0) | structured lines | structured hunks (U0) |
|--------------------------------|-----------:|----------------:|-----------------:|----------------------:|
| `model/client_basic.m4i`       |     57     |       21        |         **5**    |          **5**        |
| `model/server_basic.m4i`       |     65     |       21        |         **5**    |          **5**        |

Designated `[sources]`-tagged lemma subset (PL-1 preservation):
**90/90** proof runs verified across variants on Tamarin 1.10.0 and 1.12.0.

Static patch-fidelity check (`scripts/verify_patch_fidelity.py`):
- adversary interface: unchanged
- `[sources]` lemma statements: unchanged
- scope-locality: all diff hunks confined to
  `client_basic.m4i`, `server_basic.m4i`, `state.m4i`.

## 3. Cross-repository static audit (tool-reuse scope)

| Scope         | files | R1  | R2  | R3  | R4  | any-violation |
|---------------|:-----:|:---:|:---:|:---:|:---:|:-------------:|
| KEMTLS        |  48   |  4  |  4  |  3  | 11  | 16 (33.3%)    |
| TLS13Tamarin  | 149   |  7  | 42  | 17  | 24  | 74 (49.7%)    |
| 5G-AKA        |   7   |  0  |  0  | (\*)| (\*)| 7 (100%)      |

(\*) On 5G-AKA the R1/R2 patterns match zero files because the models
follow a different naming convention; the manuscript documents this as a
disclosed R1 caveat.  R3 and R4 still fire on every file.

KEMTLS audit-tool validation against an independent source-assisted
classifier: **191/192** rule-level agreements, macro-averaged Cohen's
κ = **0.962**.  This corresponds to "almost perfect" agreement under the
Landis--Koch scale.
