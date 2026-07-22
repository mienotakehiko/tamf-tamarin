# KEMTLS measurements

This directory receives the per-run artefacts of the descendant-artifact
scope (Section "KEMTLS Engineering Case" of the manuscript).  The
external KEMTLS-TLS13Tamarin tree is not vendored here; retrieve it per
[`../../docs/getting-external-artifacts.md`](../../docs/getting-external-artifacts.md).

Populated by `scripts/reproduce_all.sh` (stage 2):

- `audit.json` -- static R1--R4 audit over the 48-file KEMTLS tree.
  Expected: `n_files = 48`, `any_violation_count = 16` (33.3%),
  `R = {R1: 4, R2: 4, R3: 3, R4: 11}`.
- `patch-fidelity.json` -- output of
  `scripts/verify_patch_fidelity.py --baseline external/kemtls-tls13tamarin --variant external/kemtls-tls13tamarin-structured`.
  Expected: `verdict = "PASS"` with all three sub-checks PASS.
- `hotspot-summary.tsv` (produced manually or by the artefact-eval
  wrapper) -- one line per hotspot × variant:
  ```
  file                     variant       lines  hunks_U0
  model/client_basic.m4i   flat          57     21
  model/client_basic.m4i   structured    5      5
  model/server_basic.m4i   flat          65     21
  model/server_basic.m4i   structured    5      5
  ```

## PL-1 lemma preservation

The 90/90 proof runs across variants and Tamarin 1.10.0 / 1.12.0 are
executed by:

```bash
for tam in tamarin-prover-1.10.0 tamarin-prover-1.12.0; do
    for variant in baseline flat structured; do
        for rep in 1 2 3; do
            $tam --prove="[sources]" \
                 external/kemtls-tls13tamarin/${variant}/theory.spthy \
                 > measurements/kemtls/pl1_${tam}_${variant}_rep${rep}.log 2>&1
        done
    done
done
```

The manuscript reports every one of these 90 log files with verified
`[sources]` lemmas.
