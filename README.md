# TAMF — Tamarin Attacker-Modelling Framework

Reproduction artefact for the manuscript
Manuscript: *TAMF: A Reusable Attacker-Modeling Framework for Practical Tamarin-Based Cryptographic Verification* 
Author: Takehiko Mieno
&nbsp;·&nbsp;
[ORCID 0009-0002-1646-2333](https://orcid.org/0009-0002-1646-2333)

License: Apache-2.0 (see [`LICENSE`](LICENSE))

Status: Reproduction artifact bundle for peer review.

---

## 1. Overview

TAMF is an audit-first packaging discipline for attacker-centric
[Tamarin](https://tamarin-prover.com/) theories, paired with a
resource-bounded pre-verification triage layer. This repository holds every
model, script, measurement, and pre-registration document behind the
manuscript, arranged so that a reviewer can reproduce each headline number
without guesswork.

Two properties define the scope precisely:

- **A per-family authoring-convention checker.** The R1–R4 rules are a single
  250-line grep-class classifier that runs unchanged on any Tamarin theory;
  family-specific attacker vocabulary is supplied through a declared registry
  (`registry/`), never by editing the classifier.
- **A triage layer, not a completion layer.** The Phase-2 experiments report
  whether attacker paths are surfaced within a declared 40 GiB heap envelope,
  under fully declared per-experiment configurations. Completion of
  large-scale core security-lemma verification on a large-memory host is a
  separate research question and is left to infrastructure-scaled follow-up
  work.

Scope is a deliberate design choice. Every result reproduced here is bound to
a stated measurement configuration (Tamarin version, heuristic, timeouts, heap
cap, normalisation); a later evaluation under a larger envelope can be reported
alongside these results, never on top of them.

---

## 2. Repository layout

```
tamf/
├── README.md                     This file.
├── LICENSE                       Apache-2.0 (external artefacts keep their own licences).
├── CITATION.cff                  Citation metadata.
├── requirements.txt              Python dependencies (psutil for the dynamic path).
├── SHA256SUMS                    Digests for every reproducible file in this tree.
│
├── scripts/                      All executable tooling.
│   ├── reproduce_all.sh          Full dynamic reproduction driver (three scopes).
│   ├── verify_all_evidence.sh    Static verification, no Tamarin required.
│   ├── preflight.sh              Environment and capacity check.
│   ├── audit_tool.py             R1–R4 discipline audit (v1).
│   ├── audit_tool_v2.py          P2-A maintenance re-implementation (adds R1_v2).
│   ├── run_battery.sh            Heuristic robustness battery {s,S,c,C}.
│   ├── analyse_battery.py        Aggregates battery runs into the reported figures.
│   ├── extract_phase_timing.py   Phase-timing extractor for the battery.
│   ├── run_ablation.py           Four-condition notion-benchmark ablation.
│   ├── run_phase2.py             Phase-2 triage harness (P2-K, P2-T).
│   ├── verify_correspondence.py  Rule-by-rule A↔C / B↔D equivalence check.
│   ├── verify_patch_fidelity.py  Static patch-fidelity check for the hotspots.
│   ├── diff_surface.py           Objective diff-surface deltas (57→5, 65→5).
│   ├── fetch_external.sh         Deterministic retrieval of external artefacts.
│   └── pin_digests.sh            Regenerates SHA256SUMS.
│
├── models/                       2×2 observational-equivalence ablation (A/B/C/D).
├── theories/                     Notion-benchmark conditions and KEMTLS hotspot pair.
│   ├── notion_bench/             raw · state_only · oracle_only · full_tamf
│   └── kemtls_hotspots/          flat (rule-local) vs structured (carrier field)
├── oracle/tamf_oracle.py         Callback oracle: search guidance kept outside theories (R2).
├── tactics/heuristic_s.tactic    The `s` co-design contract, documented.
├── registry/                     Per-family attacker vocabularies (config, not code).
│
├── measurements/                 Machine-readable evidence, one directory per scope.
│   ├── robustness-battery/runs/  summary.tsv, battery_report_v3.md, table_R1/R2_v3.tex, …
│   ├── kemtls/                    Descendant-scope run outputs and expected values.
│   ├── tls13tamarin/              Ancestor cross-repository outputs.
│   └── 5g-aka/                    Lineage-unrelated cross-repository outputs.
│
├── evidence/                     Phase-2 archives and manifest (SHA-256 pinned).
│   └── EVIDENCE_MANIFEST.md       P2-K · P2-T · P2-A · P2-G · matched-config
│
├── patches/                      flat/structured kdf_context patches for the hotspots.
├── preregistration/              Pre-registered protocols, frozen before measurement.
├── docs/                         Reproduction guidance.
│   ├── expected-results.md        Headline numbers to check a local run against.
│   ├── getting-external-artefacts.md
│   └── artifact-metadata.md
├── external/frozen-commits.txt   Frozen commits for the non-vendored upstream trees.
└── tests/test_audit_tool.py      Self-test for the audit classifier.
```

---

## 3. Requirements

| Component | Needed for | Notes |
|-----------|------------|-------|
| Python ≥ 3.8 | everything | Standard library only for the quick-start path. |
| `psutil` | dynamic reproduction | Peak-RSS sampling in the battery; `pip install -r requirements.txt`. |
| Tamarin Prover 1.12.0 | dynamic proof runs | Primary release for every reported number. |
| Tamarin Prover 1.10.0 | cross-release check | Two protocol-central lemmas only. |
| Maude 3.4 | Tamarin back-end | Required by Tamarin. |
| `git` ≥ 2.30 | external artefacts | Clones upstream trees at frozen commits. |
| RAM | dynamic runs | ≥ 8 GiB for the ablation; ≥ 40 GiB for the Phase-2 envelope and the RSS-shoulder measurement. |

The exact upstream revisions of Tamarin, Maude, and the three evaluated
repositories are pinned in [`external/frozen-commits.txt`](external/frozen-commits.txt).
The quick-start path in §4 needs none of the Tamarin toolchain.

---

## 4. Quick start (no Tamarin)

Everything that can be checked without proof search runs from a clean clone in
under a minute:

```bash
git clone https://github.com/mienotakehiko/tamf-tamarin.git
cd tamf
pip install -r requirements.txt        # optional; pytest only
bash scripts/verify_all_evidence.sh
```

The script runs the audit-tool self-tests, classifies the flat/structured
hotspot pair, computes the diff-surface deltas, and verifies every file in
`SHA256SUMS`. Expected tail:

```
[1/3] Audit tool self-test ............ PASS
[2/3] Hotspot diff-surface deltas ..... PASS
[3/3] SHA-256 digest verification ..... PASS
All available evidence checks passed.
```

---

## 5. Full reproduction (with Tamarin)

### 5.1 Retrieve the external artefacts

The three evaluated repositories are not vendored. Fetch them at their frozen
commits, then follow the manual notes for the two KEMTLS variant trees:

```bash
bash scripts/fetch_external.sh                 # clones into external/<name>/
# then see docs/getting-external-artefacts.md for the flat/structured patches
```

### 5.2 Run the three core scopes

`reproduce_all.sh` drives the three scopes in order and writes self-contained
outputs under `measurements/<scope>/runs/`. Each stage is independent and can
be skipped:

```bash
bash scripts/reproduce_all.sh                  # all stages
SKIP_KEMTLS=1 SKIP_XREPO=1 bash scripts/reproduce_all.sh   # battery only
```

| Stage | Scope | Driver | Budget / resource |
|-------|-------|--------|-------------------|
| 0 | preflight | `preflight.sh` | environment + RAM check |
| 1 | state-representation ablation | `run_battery.sh` → `analyse_battery.py` | 300 s/cell, ≥ 8 GiB (≥ 40 GiB for the RSS shoulder) |
| 2 | KEMTLS descendant | `verify_patch_fidelity.py`, `audit_tool.py` | static; needs `external/kemtls-tls13tamarin` |
| 3 | cross-repository audit | `audit_tool.py` | static; needs TLS13Tamarin and 5G-AKA trees |

### 5.3 Run the Phase-2 triage layer

The resource-bounded core-lemma experiments run under the declared 40 GiB heap
envelope and require a large-memory host:

```bash
python3 scripts/run_phase2.py --experiment P2-K --budget 4h --heap 40
python3 scripts/run_phase2.py --experiment P2-T --budget 6h --heap 40
```

Outcomes are classified under a fixed schema — `VERIFIED`, `HEAP_LIMIT`,
`TIMEOUT`, `FALSIFIED`, `envelope-boundary` — and archived per cell with
SHA-256 pinning; see [`evidence/EVIDENCE_MANIFEST.md`](evidence/EVIDENCE_MANIFEST.md).

---

## 6. Expected results

Compare any local run against [`docs/expected-results.md`](docs/expected-results.md),
which reproduces the manuscript's headline tables. The summary:

| Scope | Quantity | Expected |
|-------|----------|----------|
| Ablation | raw encodings (2×2, four budgets) | time out, 24/24 |
| Ablation | carrier encodings (≥ 120 s) | verify, 18/18; median wall 71.68 s |
| Battery | pre-registered verdict | **SECONDARY** (carrier verifies under `s` only) |
| KEMTLS | client / server diff surface | 57→5 / 65→5 changed lines; U₀ hunks 21→5 |
| KEMTLS | designated lemma subset | 90/90 (60/60 on 1.12.0, 30/30 on 1.10.0) |
| Audit | KEMTLS discipline baseline | 16/48 files (33.3 %) |
| Audit | TLS13Tamarin | 149 files, 49.7 % any-violation |
| Audit | 5G-AKA | 7 files, 100 % any-violation |
| Audit | independent agreement | 191/192 (κ = 0.962) |
| P2-K | KEMTLS security lemmas | 14/16 VERIFIED, 2 HEAP_LIMIT; three lemmas verify in both variants |
| P2-T | TLS13Tamarin | `secret_session_keys` 6/6; `mutual_entity_authentication` inconclusive |
| P2-A | 5G-AKA R1_v2 detector | flag rate 5/7 = 71.4 % |

If a local figure deviates materially, compare the environment against
`docs/artifact-metadata.md` and `external/frozen-commits.txt` before filing an
issue: proof-search wall-clock and peak RSS depend on the Tamarin/Maude build
and the host.

---

## 7. Claim → artefact map

| Manuscript claim | Reproduced by |
|------------------|---------------|
| R1–R4 discipline; 33.3 % KEMTLS baseline | `scripts/audit_tool.py` + `registry/tls_family.json` |
| Byte-for-byte tool reuse across three repositories | same tool, three registries; `scripts/fetch_external.sh` |
| P2-A: R1_v2 closes the 5G-AKA R1 caveat (71.4 %) | `scripts/audit_tool_v2.py` + `registry/5g_aka_family.json` |
| Independent labelling; κ = 0.962 | `preregistration/P3a_labeling_protocol.md`, `measurements/kemtls/` |
| 2×2 ablation and four-budget timeout curve | `models/`, `scripts/run_ablation.py`, `scripts/verify_correspondence.py` |
| Robustness battery; SECONDARY verdict | `scripts/run_battery.sh`, `preregistration/robustness_battery.md` |
| Hotspot diff surface (57→5, 65→5, 21→5) | `scripts/diff_surface.py`, `scripts/verify_patch_fidelity.py`, `theories/kemtls_hotspots/` |
| Phase-2 P2-K / P2-T triage; envelope-boundary outcomes | `scripts/run_phase2.py`, `evidence/EVIDENCE_MANIFEST.md` |
| Matched-configuration cross-check (budget-independence) | `evidence/matched-config/` |
| SHA-256 pinning; end-to-end verification | `SHA256SUMS`, `scripts/verify_all_evidence.sh` |

---

## 8. Reproducibility guarantees

- **A repository-agnostic classifier.** `audit_tool.py` carries no
  repository-specific string; `tests/test_audit_tool.py` asserts this and that
  the flat/structured pair classifies as a matched rule-violating /
  rule-compliant pair.
- **Pinned digests.** `SHA256SUMS` covers every reproducible file;
  `verify_all_evidence.sh` checks them from a clean clone, and `pin_digests.sh`
  regenerates them.
- **Declared configurations on the record.** Every dynamic result carries its
  full Tamarin and GHC-RTS configuration, so results under different envelopes
  compose additively.
- **An honest outcome schema.** A cell that reaches the heap cap is reported as
  an envelope-boundary outcome, never relabelled as preservation or silently
  dropped.

---

## 9. External artefacts

The three evaluated repositories keep their upstream licences and are not
copied into this tree. Their frozen commits, tool versions, and the retrieval
procedure are in [`external/frozen-commits.txt`](external/frozen-commits.txt)
and [`docs/getting-external-artefacts.md`](docs/getting-external-artefacts.md).
The flat and structured KEMTLS variant trees are produced from the frozen
baseline by the patches under [`patches/`](patches/).


---

## 10. Citing and licence

Citation metadata is in [`CITATION.cff`](CITATION.cff). This artefact is
released under [Apache-2.0](LICENSE); the external Tamarin artefacts retain
their upstream licences (`external/frozen-commits.txt`).


(C) 2026 Takehiko Mieno