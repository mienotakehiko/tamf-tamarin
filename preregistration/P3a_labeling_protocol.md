# Blind Labeling Protocol (audit-tool validation)

**Purpose.** Validate the R1–R4 audit classifier against an independent,
source-assisted classification on the 48 tracked `src/kemtls/` files.

## Procedure (blind w.r.t. tool output)
1. For each file, classify R1/R2/R3/R4 **from the source text alone**, using a
   structured source browser, **before** running `scripts/audit_tool.py` on that
   file. Tool output for the file is not consulted during labelling.
2. Record one decision per (file, rule) = 192 rule-level decisions.
3. Only after all labels are fixed, run the audit tool and compute agreement.

## Reported outcome
- Aggregate agreement: **191 / 192**.
- Macro Cohen's κ = **0.962** (per-rule κ: R1/R2/R4 = 1.00, R3 = 0.846).
- Single disagreement: `tests/reachability.m4` — an m4 macro-generated bare
  lemma the line-oriented R3 regex cannot match. Disclosed as a regex-boundary
  false negative, **not** absorbed into the aggregate.

## Scope of the independence claim
Independence is **w.r.t. the audit tool's per-file output**, not w.r.t.
authorship. A fully-blind two-labeller study with an external labeller is future
work.
