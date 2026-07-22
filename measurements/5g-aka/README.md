# 5G-AKA measurements (cross-repository static audit)

Populated by `scripts/reproduce_all.sh` (stage 3) after retrieving the
Tamarin `ccs18-5G` example subtree per
[`../../docs/getting-external-artifacts.md`](../../docs/getting-external-artifacts.md).

Expected `audit.json` (macro-level):

```json
{
  "n_files": 7,
  "any_violation_count": 7,
  "any_violation_rate": 1.0,
  "rule_counts": {"R1": 0, "R2": 0, "R3": ..., "R4": ...}
}
```

## R1 caveat (disclosed in the manuscript)

The 5G-AKA models use a state-carrier naming convention that does not
match the regex used by R1/R2 (which was calibrated on the KEMTLS naming
convention `[Client|Server|Peer]State*`).  As a result R1 and R2 report
zero flagged files.  This is a **portability limitation of R1/R2, not a
security property of 5G-AKA**.  R3 and R4 fire on every file, which is
why the "any-violation" rate is 100%.

The manuscript uses this observation deliberately as a probe of
portability robustness: it shows that the audit runs to completion on an
externally-authored repository with a different modelling style, that
the tool produces non-trivial output, and that a naming-convention
mismatch propagates cleanly into a single disclosed caveat rather than
into a silent failure.

## What this scope does *not* claim

- No proof preservation on 5G-AKA is asserted.
- No performance measurement of Tamarin on 5G-AKA is reported.
- No security-property preservation on 5G AKA is claimed.
