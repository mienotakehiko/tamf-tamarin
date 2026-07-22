# Registered deviation record

The original pre-registration listed `p` as a fifth static heuristic for
the Tamarin `--diff` battery. During the frozen run, Tamarin 1.12.0 rejected
all six `p` attempts with:

    Unknown proof method ranking 'p'

The error occurred after derivation checks and before main proof search.
Accordingly:

1. the original `summary.tsv` and all six stderr/meta files are preserved;
2. the six `p` attempts are classified as an invalid experimental factor,
   not as VERIFIED, TIMEOUT, FALSIFIED, or OOM results;
3. no substitute heuristic is introduced post hoc;
4. the complete supported subset `{s,S,c,C}` (24 runs) is analysed;
5. the original severe-flip absolute threshold is retained.

This is a protocol correction and registered deviation, not a silent
rewriting of the pre-registration.
