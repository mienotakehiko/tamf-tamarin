# Phase-2 Evidence Manifest

Top-level index of the reproducibility archives. Every reported number is
traceable to one archive here; full SHA-256 digests are pinned in `SHA256SUMS`
at the release tag. The manuscript quotes short (8-hex) identifiers for
readability; this repository is the authoritative source for full-digest
verification.

| Archive | Scope | Declared configuration | Internal files | Key outcomes |
|---|---|---|---|---|
| `P2-K/` | KEMTLS-TLS13Tamarin security-lemma triage | Tamarin 1.12.0, heuristic `s`, 4 h outer, 40 GiB heap (`-N1 -M40G -c20`) | 274 | 4 lemmas × 2 variants; 14 VERIFIED, 2 ENVELOPE_BOUNDARY, 0 falsified |
| `P2-T/` | TLS13Tamarin rev21 security-lemma triage | Tamarin 1.12.0, heuristic `s`, 6 h outer, 40 GiB heap; `sg↔ClientSgState(sg)` normalisation; commit `67262370` | 113 | `secret_session_keys` VERIFIED (6/6); `mutual_entity_authentication` ENVELOPE_BOUNDARY |
| `P2-G/` | Per-GC follow-up to the B3 RSS-bound verdict | GC trace on the robustness-battery B3 configuration | 9 cells | peak RSS > observed live-heap bound on every cell (supersedes B3 upper-bound reading) |
| `P2-A/` | R1_v2 name-based attacker-rule detector | audit tool v2 + per-repository TSV | — | 5G-AKA R1_v2 = 5/7 = 71.4% (closes the disclosed R1 zero-rate caveat) |
| `matched-config/` | Matched-configuration cross-check (M-A1 + M-A2) | same heap cap; 4 h and 6 h both run | — | budget substitution ruled out for the two positive lemmas |

## Outcome schema (Phase-2)

`VERIFIED` · `HEAP_LIMIT` (≡ `ENVELOPE_BOUNDARY` under the triage terminology) ·
`TIMEOUT` · `FALSIFIED`.

`ENVELOPE_BOUNDARY` is **neither** preservation **nor** falsification: it is a
limit-behaviour data point under a declared envelope. TAMF is a **triage layer,
not a completion layer** — completion of large-scale core security-lemma
verification on a large-memory host is a separate research question, deferred to
infrastructure-scaled follow-up work.

## Regenerating the evidence

```bash
# Static, no Tamarin required:
python3 scripts/audit_tool.py    external/kemtls-tls13tamarin/src/kemtls \
        --registry registry/tls_family.json --json evidence/kemtls_audit.json
python3 scripts/audit_tool_v2.py external/tamarin-ccs18-5g \
        --registry registry/5g_aka_family.json --json evidence/P2-A/5gaka_r1v2.json

# Dynamic, requires tamarin-prover (+ a large-memory host for Phase-2):
python3 scripts/run_ablation.py           --out evidence/summary.tsv
python3 scripts/run_robustness_battery.py --out evidence/battery_report_v3.json
python3 scripts/run_phase2.py --experiment P2-K --outer-hours 4
python3 scripts/run_phase2.py --experiment P2-T --outer-hours 6
```
