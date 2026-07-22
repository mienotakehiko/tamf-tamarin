# TAMF -- Reproduction Artifact

Manuscript: *TAMF: A Reusable Attacker-Modeling Framework for Practical Tamarin-Based Cryptographic Verification* 
Author: Takehiko Mieno
&nbsp;·&nbsp;
[ORCID 0009-0002-1646-2333](https://orcid.org/0009-0002-1646-2333)

License: Apache-2.0 (see [`LICENSE`](LICENSE))

Status: Reproduction artifact bundle for peer review.

---

## 1. Scope of this artifact

This repository packages every reproducible artefact behind the three evaluation scopes reported in the manuscript:

1. State-representation ablation (scope A, heuristic-scoped).
   A bounded four-query pre/post-challenge observational-equivalence benchmark with four `.spthy` variants,
   run under the pre-registered heuristic robustness battery.
2. Descendant-artefact engineering case (scope B).
   A KEMTLS-TLS13Tamarin patch-fidelity study over the `kdf_context` metadata-propagation hotspot pair,
   with the designated `[sources]`-tagged lemma subset (PL-1 layer) as preservation target.
3. Tool-reuse cross-repository static audit (scope C).
   The R1--R4 static audit tool applied unchanged to KEMTLS,
   TLS13Tamarin `rev21`, and the Tamarin `ccs18-5G` examples.

Each scope has its own subdirectory under [`measurements/`](measurements),
its own expected numbers in [`docs/expected-results.md`](docs/expected-results.md), and its own pre-registered claim.
Nothing in this repository claims protocol-facing security-property preservation on KEMTLS or 5G AKA;
see the manuscript for the exact bounds.

## 2. Repository layout

```
tamf-tamarin/
├── README.md                         (this file)
├── LICENSE                           (Apache-2.0)
├── CITATION.cff                      (citation metadata)
├── .gitignore
│
├── models/                           (the four .spthy variants)
│   ├── README.md
│   ├── A_raw.spthy
│   ├── B_raw_priority.spthy
│   ├── C_state_carrier.spthy
│   └── D_state_priority.spthy
│
├── scripts/                          (all Python + Bash tooling)
│   ├── README.md
│   ├── preflight.sh                  (env + capacity check)
│   ├── run_battery.sh                (30-run robustness battery)
│   ├── extract_phase_timing.py       (derivation-check vs main-proof)
│   ├── analyse_battery.py            (aggregate + verdict)
│   ├── audit_tool.py                 (R1--R4 static audit; ~250 LOC)
│   ├── verify_correspondence.py      (offline rule-by-rule diff)
│   ├── verify_patch_fidelity.py      (KEMTLS patch-fidelity check)
│   └── reproduce_all.sh              (end-to-end driver)
│
├── measurements/                     (per-scope run artefacts)
│   ├── robustness-battery/
│   │   ├── README.md
│   │   └── runs/                     (summary.tsv, tables, reports)
│   ├── kemtls/          (README.md; populated by reproduce_all.sh)
│   ├── tls13tamarin/    (README.md; populated by reproduce_all.sh)
│   └── 5g-aka/          (README.md; populated by reproduce_all.sh)
│
├── patches/                          (KEMTLS kdf_context patches)
│   └── README.md
│
├── docs/                             (design & reproducibility docs)
│   ├── README.md                     (index)
│   ├── pre-registration.md
│   ├── deviation_notice_v3.md
│   ├── artifact-metadata.md
│   ├── getting-external-artifacts.md
│   ├── expected-results.md
│   └── P3a_labeling_protocol.md
│
└── external/                         (not vendored; retrieval procedure)
    └── frozen-commits.txt
```

## 3. Prerequisites

- Operating system: Linux (tested on Ubuntu 22.04 / 24.04).
  macOS and WSL2 should work but are not tested.
- Tamarin Prover: 1.12.0 for the robustness battery; both 1.10.0 and 1.12.0 for the KEMTLS PL-1 lemma re-verification.
  Install per [tamarin-prover.com](https://tamarin-prover.com/); frozen tags are listed in [`external/frozen-commits.txt`](external/frozen-commits.txt).
- Maude: 3.4 (Tamarin's rewriting back-end).
- Python: 3.9 or newer, plus `psutil`.  `preflight.sh` installs `psutil` if missing.
- RAM:
  - ≥ 8 GiB is the hard minimum (scope A -s carrier fits in ~1 GiB, but -S / -c can exceed 20 GiB peak RSS -- see below).
  - ≥ 32 GiB is required to reproduce the full RSS shoulder recorded in the manuscript (`C_state_carrier -c` peaks around 22 GiB).
- Disk: ≈ 500 MiB including `external/` clones.
- Time budget: approximately 100 minutes for the battery + KEMTLS audits on a modern desktop.
  Cross-repository audits complete in well under one minute.

Run `scripts/preflight.sh` at any time to check whether your machine satisfies the pre-registered thresholds.

## 4. Quick start (all three scopes)

```bash
# 1. Clone this repository
git clone https://github.com/mienotakehiko/tamf-tamarin.git
cd tamf-tamarin

# 2. Env check
bash scripts/preflight.sh

# 3. Retrieve external artefacts (KEMTLS, TLS13Tamarin, 5G-AKA)
#    see docs/getting-external-artifacts.md for details
#    or skip if you only want scope A
mkdir -p external && cd external
git clone https://github.com/kemtls/KEMTLS-TLS13Tamarin.git kemtls-tls13tamarin
(cd kemtls-tls13tamarin && git checkout 627744491482c497f853f69681dc67135ffa5e30)
# ... (see docs/getting-external-artifacts.md for the other two)
cd ..

# 4. End-to-end
bash scripts/reproduce_all.sh
```

Skip flags:

```bash
SKIP_BATTERY=1 bash scripts/reproduce_all.sh   # only scopes B + C
SKIP_KEMTLS=1  bash scripts/reproduce_all.sh   # only scopes A + C
SKIP_XREPO=1   bash scripts/reproduce_all.sh   # only scopes A + B
```

## 5. Reproducing individual scopes

### 5.1 State-representation ablation (scope A, ≈ 100 min)

```bash
bash   scripts/run_battery.sh
python scripts/analyse_battery.py \
       --runs-dir measurements/robustness-battery/runs \
       --output   measurements/robustness-battery/runs
```

The pre-registered verdict is written to
`measurements/robustness-battery/runs/battery_validation_v3.txt` and
should read `PASS_WITH_REGISTERED_DEVIATION` with verdict `SECONDARY`.
Full expected numbers: [`docs/expected-results.md`](docs/expected-results.md).

The `p` heuristic is not a supported ranking in Tamarin 1.12.0.
All six `{A,C} × p` runs terminate before main proof search with `Unknown proof method ranking 'p'` 
and are recorded as an invalid experimental factor rather than TIMEOUT/VERIFIED.
This is documented as a registered deviation in [`docs/deviation_notice_v3.md`](docs/deviation_notice_v3.md);
the pre-registered analysis targets the 24-run supported subset `{s, S, c, C}`.

### 5.2 KEMTLS engineering case (scope B)

After retrieving the KEMTLS baseline and applying the two `kdf_context` patches (see [`patches/README.md`](patches/README.md)):

```bash
python scripts/audit_tool.py \
       --root  external/kemtls-tls13tamarin \
       --output measurements/kemtls/audit.json

python scripts/verify_patch_fidelity.py \
       --baseline external/kemtls-tls13tamarin \
       --variant  external/kemtls-tls13tamarin-structured \
       --output   measurements/kemtls/patch-fidelity.json
```

Expected: `audit.json` with `n_files = 48`, `any_violation_count = 16` (33.3%),
`R = {R1: 4, R2: 4, R3: 3, R4: 11}`; `patch-fidelity.json` with `verdict = "PASS"` on all three sub-checks.

The 90/90 PL-1 lemma preservation runs are described in [`measurements/kemtls/README.md`](measurements/kemtls/README.md);
we do not vendor the log files themselves in this bundle.

### 5.3 Cross-repository static audit (scope C, < 1 min)

```bash
python scripts/audit_tool.py --root external/tls13tamarin \
       --output measurements/tls13tamarin/audit.json --quiet
python scripts/audit_tool.py --root external/5g-aka \
       --output measurements/5g-aka/audit.json --quiet
```

Expected `any_violation_count` values: 74/149 (49.7%) on
TLS13Tamarin `rev21`, 7/7 (100%) on 5G-AKA (with the disclosed R1
naming-convention caveat).

## 6. Machine-readable outputs and how they map to the manuscript

| Manuscript table / claim | File in this repository |
|---|---|
| Table on state-representation × priority ablation (§ Overall Outcomes) | `measurements/robustness-battery/runs/summary.tsv` |
| Table R1 (heuristic-scoped verdicts) | `measurements/robustness-battery/runs/table_R1_v3.tex` |
| Table R2 (derivation-check vs main-proof timing) | `measurements/robustness-battery/runs/table_R2_v3.tex` |
| Pre-registered SECONDARY verdict | `measurements/robustness-battery/runs/battery_validation_v3.txt` |
| KEMTLS hotspot line/hunk reductions (§ Hotspot Comparators) | `measurements/kemtls/hotspot-summary.tsv` (regenerated by the wrapper) |
| KEMTLS static R1--R4 audit (33.3% any-violation) | `measurements/kemtls/audit.json` |
| KEMTLS patch-fidelity PASS | `measurements/kemtls/patch-fidelity.json` |
| TLS13Tamarin static audit (49.7% any-violation) | `measurements/tls13tamarin/audit.json` |
| 5G-AKA static audit (100% any-violation, R1 caveat) | `measurements/5g-aka/audit.json` |
| Audit-tool validation on KEMTLS (191/192, κ = 0.962) | `docs/P3a_labeling_protocol.md` (protocol) + labeler outputs (external) |

## 7. Deliberate non-goals of this artifact

- No new Tamarin proofs.  We do not claim protocol-facing security properties on KEMTLS, TLS 1.3, or 5G AKA.
  The PL-1 layer verified on KEMTLS is the sponsor's `[sources]`-tagged lemma subset.
- No cross-tool comparison.  ProVerif, Scyther, AVISPA, DeepSec, and Verifpal each package attacker state differently; 
  a rule-discipline comparison across tools has no shared operational meaning.
  See §5.3 of the manuscript.
- No wall-clock claim outside `--heuristic=s`.  The state-representation separation is measured only under `--heuristic=s`;
  under `-S / -c / -C`, both encodings time out and the carrier's peak RSS rises to ~21--22 GiB.
  This asymmetry is disclosed as future work.
- No hardware-portability claim.  All numbers are for a single machine class documented in `docs/artifact-metadata.md`.
  We report medians of three repetitions specifically to hedge against per-run variance, but not against cross-hardware variance.
- No fully-unaided two-labeler audit-tool validation.
  The 191/192 KEMTLS agreement uses one structured source-assisted labeler and the audit tool as the second.
  A fully-blind two-labeler study is scoped in `docs/P3a_labeling_protocol.md` as future work.

## 8. Citing this artifact

If you use any part of this artifact, please cite both the manuscript and this repository.
Machine-readable citation metadata is provided in [`CITATION.cff`](CITATION.cff).

## 9. Contact

Questions, reproduction issues, and requests for the KEMTLS patch bodies (which are not vendored until manuscript acceptance) should be
directed to the corresponding author listed in `CITATION.cff`.


(C) 2026 Takehiko Mieno