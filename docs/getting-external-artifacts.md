# Getting the external artefacts

The three cross-repository / descendant-artefact scopes referenced in the
manuscript rely on upstream Tamarin projects that are **not vendored** in
this repository (to respect their own licenses and to avoid staleness).
This document is the deterministic retrieval procedure.  All commits are
frozen in [`external/frozen-commits.txt`](../external/frozen-commits.txt).

## Prerequisites

- `git` >= 2.30
- Approximately 200 MiB of free disk under `external/`.

## 1. KEMTLS-TLS13Tamarin (descendant scope, §"KEMTLS Engineering Case")

```bash
cd external
git clone https://github.com/kemtls/KEMTLS-TLS13Tamarin.git kemtls-tls13tamarin
cd kemtls-tls13tamarin
git checkout 627744491482c497f853f69681dc67135ffa5e30
```

The two variant trees used by the hotspot comparator (`flat` and
`structured` `kdf_context` propagation) are produced from this baseline
by the patches under [`patches/`](../patches/):

```bash
cd external
cp -r kemtls-tls13tamarin kemtls-tls13tamarin-structured
cd kemtls-tls13tamarin-structured
git apply ../../patches/kemtls-kdfctx-structured.patch
```

## 2. TLS13Tamarin `rev21` (tool-reuse scope, §"TLS13Tamarin Ancestor")

```bash
cd external
git clone https://github.com/tls13tamarin/TLS13Tamarin.git tls13tamarin
cd tls13tamarin
# The manuscript targets the rev21 subtree under master
git checkout master
```

The audit reads files under `src/rev21/`; other subtrees are ignored by
`scripts/audit_tool.py` by default because they do not match the
`.spthy`/`.m4i` extension filter.

## 3. Tamarin `ccs18-5G` (portability scope, §"5G-AKA Portability")

```bash
cd external
mkdir -p 5g-aka
git clone --depth=1 --branch develop \
    https://github.com/tamarin-prover/tamarin-prover.git \
    tamarin-prover-tmp
cp -r tamarin-prover-tmp/examples/ccs18-5G/* 5g-aka/
rm -rf tamarin-prover-tmp
```

Only the seven `.spthy` files under `examples/ccs18-5G/` are audited.

## Sanity check

After completing the three steps above:

```bash
python3 scripts/audit_tool.py --root external/kemtls-tls13tamarin  --output measurements/kemtls/audit.json --quiet
python3 scripts/audit_tool.py --root external/tls13tamarin         --output measurements/tls13tamarin/audit.json --quiet
python3 scripts/audit_tool.py --root external/5g-aka               --output measurements/5g-aka/audit.json --quiet
```

Expected orders of magnitude (see also `docs/expected-results.md`):

| Scope           | files | any-violation | rate  |
|-----------------|-------|---------------|-------|
| KEMTLS          |  48   | 16            | 33.3% |
| TLS13Tamarin    | 149   | 74            | 49.7% |
| 5G-AKA          |   7   |  7            | 100%  |

Deviations from these ranges are expected if you audit against a different
commit than the one recorded in `frozen-commits.txt`.
