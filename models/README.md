# Models used by the state-representation ablation

The four `.spthy` files here are the primary benchmark of the manuscript
(Section "Overall Outcomes").  They encode the same four-query
observational-equivalence problem in four different ways so that a
2 × 2 factor design can be run over them:

| File                     | representation | rule priority |
|--------------------------|:--------------:|:-------------:|
| `A_raw.spthy`            |  raw (8 premises)          | default   |
| `B_raw_priority.spthy`   |  raw (8 premises)          | prioritised |
| `C_state_carrier.spthy`  |  one-carrier `State_Progress` | default   |
| `D_state_priority.spthy` |  one-carrier `State_Progress` | prioritised |

Each theory declares the same public key, adversary, and challenge
oracle; the only differences are (a) whether the challenger-side state
is exposed as eight separate premise facts or as a single
`State_Progress` carrier fact, and (b) whether the modeller has manually
annotated rule priorities.  The offline rule-by-rule correspondence
check (`scripts/verify_correspondence.py`) shows that A and C (and B
and D) are semantically equivalent up to multiset packaging.

## Reproduced results

Under `--heuristic=s` and a 300-s outer budget, the manuscript reports:

- A_raw:            0/3 verified, 3/3 timeout, ~5 GiB peak RSS
- B_raw_priority:   0/3 verified, 3/3 timeout, ~5 GiB peak RSS
- C_state_carrier:  3/3 verified, median 58.4 s, ~1 GiB peak RSS
- D_state_priority: 3/3 verified, median 75.6 s, ~1 GiB peak RSS

See [`../measurements/robustness-battery/runs/battery_report_v3.md`](../measurements/robustness-battery/runs/battery_report_v3.md)
for the full 24-run supported-heuristic table.
