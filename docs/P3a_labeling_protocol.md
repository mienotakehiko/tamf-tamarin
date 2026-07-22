# P3a: Blind human-labeling protocol for audit-tool validation

This document defines the two-labeler protocol used to establish the
audit tool's rule-level agreement on KEMTLS (191/192, macro κ = 0.962).
It is intended to be re-executed by an independent reviewer with no prior
exposure to `scripts/audit_tool.py`.

## 1. Inputs

- A copy of the KEMTLS-TLS13Tamarin tree at commit
  `627744491482c497f853f69681dc67135ffa5e30`
  (see `external/frozen-commits.txt`).
- The rule descriptions R1--R4 exactly as they appear in the manuscript
  (Section "TAMF Design", Table for R1--R4).  Labelers must read these
  descriptions but **must not** read the regex bodies in
  `scripts/audit_tool.py`.

## 2. Unit of analysis

Each `.spthy` / `.m4i` file is one unit.  A file may exhibit zero, one,
or multiple rule violations; each rule is labeled independently.

## 3. Labeler roles

- **Labeler A** (structured source-assisted):
  labels each file as "R_i present" or "R_i absent" from the source text
  alone.  May inspect the surrounding rule context but not the audit
  tool's regex bodies or its output.

- **Labeler B** (audit tool):
  runs `scripts/audit_tool.py --root external/kemtls-tls13tamarin
  --output artifact/audit.json --quiet` and reads the boolean flags per
  file.

Labelers work independently; they exchange their JSON labels only after
both have completed all 48 files.

## 4. Recording format

Each labeler produces a `labels.jsonl` file with one line per file:

```json
{"path": "model/client_basic.m4i", "R1": true, "R2": false, "R3": false, "R4": true}
```

The pair of files is analysed by
`scripts/compute_kappa.py --labeler-a labels_A.jsonl --labeler-b labels_B.jsonl`
which emits, per rule and macro-averaged:

- observed agreement (fraction of files with the same boolean)
- expected agreement under label marginals
- Cohen's κ (two-labeler)
- 95% CI via bootstrap (default: 2000 resamples)

## 5. Pre-registered thresholds

The manuscript's audit-tool validation claim is:

> On KEMTLS the tool and the structured source-assisted classifier
> agree on 191/192 rule decisions; macro-averaged Cohen's κ = 0.962.

We regard the audit tool as "validated against structured source
assistance on KEMTLS" iff:

- observed agreement per rule >= 95%, AND
- macro-averaged κ >= 0.80 ("substantial", Landis--Koch).

Both thresholds are pre-committed at this document's writing.

## 6. Deviations

Any deviation (different labeler background, different rule wording,
missing file) is recorded in the free-text field
`deviations` of the aggregate report.  The fully-unaided two-labeler
study (both labelers without source assistance) is scoped as future work
in the manuscript and is not implemented by this protocol.
