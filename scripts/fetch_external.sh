#!/usr/bin/env bash
# Deterministically retrieve the three non-vendored external artefacts at
# their frozen commits, as recorded in external/frozen-commits.txt. Tool
# binaries (Tamarin, Maude) are installed globally and are not fetched here;
# see docs/getting-external-artefacts.md for the full manual procedure.
set -euo pipefail
cd "$(dirname "$0")/.."

# Only the three artefact trees are cloned. Path-style entries such as
# "master:src/rev21" name a branch and a sub-tree; the sub-tree is left in
# place after checkout and the manuscript's audited file set is scoped to it.
fetch() {
  local name="$1" url="$2" ref="$3"
  echo "== ${name} @ ${ref} =="
  [[ -d "external/${name}/.git" ]] || git clone "${url}" "external/${name}"
  ( cd "external/${name}" \
      && git fetch --all --quiet \
      && git checkout --quiet "${ref%%:*}" ) \
    || echo "  [warn] verify the frozen ref for ${name} in external/frozen-commits.txt"
}

fetch kemtls-tls13tamarin https://github.com/kemtls/KEMTLS-TLS13Tamarin.git      627744491482c497f853f69681dc67135ffa5e30
fetch tls13tamarin        https://github.com/tls13tamarin/TLS13Tamarin.git       master
fetch 5g-aka              https://github.com/tamarin-prover/tamarin-prover.git   develop

echo
echo "Retrieved. Next: follow docs/getting-external-artefacts.md to apply the"
echo "flat/structured patches (patches/) and to scope each audited file set."
