# TLS13Tamarin measurements (cross-repository static audit)

Populated by `scripts/reproduce_all.sh` (stage 3) after retrieving the
TLS13Tamarin `rev21` subtree per
[`../../docs/getting-external-artefacts.md`](../../docs/getting-external-artefacts.md).

Expected `audit.json` (macro-level):

```json
{
  "n_files": 149,
  "any_violation_count": 74,
  "any_violation_rate": 0.4966,
  "rule_counts": {"R1": 7, "R2": 42, "R3": 17, "R4": 24}
}
```

Interpretation (Section "TLS13Tamarin Ancestor" of the manuscript):

- The 49.7% "any-violation" rate on the ancestor is comparable to the
  33.3% rate on the KEMTLS descendant.  A two-sample Fisher exact test
  (KEMTLS vs. TLS13Tamarin) gives `p = 0.066` (h = 0.333); an R2-only
  test is significant at `p = 0.005` (h = 0.534).
- The static audit reproduces on this externally-authored repository
  without any modification to `scripts/audit_tool.py`, supporting the
  input-independence claim.
- No proof re-execution is attempted on TLS13Tamarin.  The manuscript
  explicitly disclaims proof-preservation on this scope.
