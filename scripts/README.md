# Scripts

All scripts here are self-contained and use only the Python standard
library plus `psutil` (installed by `scripts/preflight.sh`).  None of
them invokes Tamarin or Maude, with the sole exception of
`run_battery.sh`.

| Script                          | Purpose                                                                                     |
|---------------------------------|---------------------------------------------------------------------------------------------|
| `preflight.sh`                  | Check env (Tamarin, Maude, Python, RAM ≥ 8 GiB) before starting a run.                       |
| `run_battery.sh`                | Execute the 30-run robustness battery (24 supported + 6 invalid-factor).                     |
| `extract_phase_timing.py`       | Parse Tamarin stderr to separate derivation-check phase from main-proof phase.               |
| `analyse_battery.py`            | Aggregate `runs/*.stdout/stderr/meta` into `summary.tsv`, tables and a validation verdict.   |
| `audit_tool.py`                 | Apply R1--R4 static rules to a repository tree.  Independent of Tamarin.  ~250 lines.        |
| `verify_correspondence.py`      | Offline rule-by-rule diff between raw and carrier representations.                           |
| `verify_patch_fidelity.py`      | Static PL-1 patch-fidelity check for the KEMTLS engineering case.                            |
| `reproduce_all.sh`              | End-to-end driver: preflight -> battery -> KEMTLS -> cross-repository audit.                 |

## Design notes

- **No hidden globals.**  Every script accepts inputs via `--flag` and
  writes outputs to `--output`; there are no environment variables that
  silently change semantics.  Exceptions (skip flags in
  `reproduce_all.sh`) are documented inline.
- **No pinning of exact Tamarin binaries in the code.**  The binary
  paths come from `$PATH`; frozen commits/tags are recorded in
  `external/frozen-commits.txt`.
- **JSON schemas are documented in each script's docstring.**  This is
  intentional so that an artefact-evaluation committee can consume the
  outputs without reading the source.
