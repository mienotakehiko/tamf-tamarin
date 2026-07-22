# Patches

Each patch here is one KEMTLS-TLS13Tamarin edit whose static properties
are measured in the manuscript.  Apply them against the baseline tree
checked out per `docs/getting-external-artifacts.md`
(commit `627744491482c497f853f69681dc67135ffa5e30`).

## `kemtls-kdfctx-flat.patch`

Flat encoding of `kdf_context` metadata propagation.  Introduces
per-rule `KdfContext(...)` facts on both client and server sides.
Reported hunk shape at U0: 21 hunks / 57 lines on the client, 21 hunks
/ 65 lines on the server.

Applying:

```bash
cd external/kemtls-tls13tamarin
git apply ../../patches/kemtls-kdfctx-flat.patch
```

## `kemtls-kdfctx-structured.patch`

Structured encoding of `kdf_context` propagation.  Adds a single field
`kdf_ctx` to the existing `state.m4i` macro; no new fact families are
introduced and the key schedule is unchanged.  Reported hunk shape at
U0: **5** hunks / **5** lines on each of the two hotspots.  Patch-fidelity
check via `scripts/verify_patch_fidelity.py` returns PASS on adversary
interface, `[sources]` lemma statements, and scope locality.

Applying:

```bash
cd external
cp -r kemtls-tls13tamarin kemtls-tls13tamarin-structured
cd kemtls-tls13tamarin-structured
git apply ../../patches/kemtls-kdfctx-structured.patch
```

## Note on distribution

The patch bodies themselves are not committed to this reproduction
repository until the manuscript is accepted, in order to respect the
KEMTLS upstream authors' review process.  Reviewers who need the patch
bodies for artefact evaluation should contact the corresponding author
listed in `CITATION.cff`.
