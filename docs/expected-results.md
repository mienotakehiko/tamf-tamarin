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
| 5G-AKA        |   7   |  0  |  1  |  7  |  7  | 7 (100%)      |

On 5G-AKA the R1 pattern matches zero files because the models follow a
different attacker-rule naming convention; the manuscript documents this as a
disclosed R1 caveat, addressed by the R1_v2 detector in Phase-2 P2-A (see §4).
R2 fires on one file (`5G_AKA.spthy`), while R3 and R4 fire on all seven, so
every file raises at least one rule.

## 4. Phase-2 resource-bounded triage layer

All Phase-2 runs use Tamarin 1.12.0, heuristic `s`, GHC RTS `-N1 -M40G -c20`,
and a common `sg <-> ClientSgState(sg)` normalisation where applicable.
`HEAP_LIMIT` is an envelope-boundary outcome: neither falsification nor
preservation. Per-cell archives with SHA-256 digests are indexed in
[`evidence/EVIDENCE_MANIFEST.md`](../evidence/EVIDENCE_MANIFEST.md).

### P2-K — KEMTLS-TLS13Tamarin security lemmas (4 h budget)

16 cells (Stage-A 8, Stage-B-core 8): **14 VERIFIED, 2 HEAP_LIMIT**, 0
falsified, 0 uncontrolled failures.

| Lemma                                    | baseline | state-carrier |
|------------------------------------------|:--------:|:-------------:|
| `secret_session_keys`                    | VERIFIED (×3) | VERIFIED (×3) |
| `mutual_entity_authentication`           | VERIFIED (×3) | VERIFIED (×3) |
| `injective_mutual_entity_authentication` | VERIFIED (n=1) | VERIFIED (n=1) |
| `session_key_agreement`                  | HEAP_LIMIT | HEAP_LIMIT |

`session_key_agreement` reaches the 40 GiB bound in both variants at an
identical 46.79 GiB peak RSS (a bit-identical cap-approach signature).

### P2-T — TLS13Tamarin `rev21` security lemmas (6 h budget)

| Lemma                          | outcome |
|--------------------------------|---------|
| `secret_session_keys`          | preserved, 6/6 runs (3 per variant) |
| `mutual_entity_authentication` | resource-bounded inconclusive (HEAP_LIMIT) |

`mutual_entity_authentication` shows an asymmetric cap-approach: peak RSS
42.49 GiB (baseline) vs 48.64 GiB (state-carrier). Static preflight over the
three changed source files: rules 54/54, lemmas 63/63, wrappers 26/26, zero
mismatches.

### P2-A — R1_v2 name-based detector

The v2 audit tool adds one name-based detector for reveal-style vocabularies
outside the TLS family. On 5G-AKA the R1_v2 flag rate is **5/7 = 71.4 %**,
addressing the disclosed R1 zero-rate caveat of §3; the v1 rates are preserved
historically.

### P2-G — per-GC follow-up

A per-GC trace on the B3 configuration shows peak RSS exceeding
`max_observed_live` on **all 9 measured cells**, superseding the earlier
"live-heap plus GC-watermark" upper-bound reading of the robustness battery.

### Matched-configuration cross-check (M-A1 + M-A2)

The two positive outcomes are budget-independent: the descendant
`mutual_entity_authentication` verifies at both 4 h and 6 h, and the ancestor
`secret_session_keys` verifies at both 6 h and 4 h. The two open cells remain
`INCONCLUSIVE_RESOURCE_BOUND` at the 40 GiB cap under both budgets.

## 5. Audit-tool validation

KEMTLS audit-tool validation against an independent source-assisted
classifier: **191/192** rule-level agreements (per-rule Cohen's κ = 1.00 for
R1/R2/R4 and 0.846 for R3), macro-averaged κ = **0.962** — "almost perfect"
agreement under the Landis--Koch scale.
