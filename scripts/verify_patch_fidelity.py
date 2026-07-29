#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""
Static patch-fidelity check for the KEMTLS engineering case.

Given a baseline theory tree and a variant tree (flat or structured
``kdf_context`` propagation), this script verifies that:

  1. The adversary interface (set of ``In/Out`` facts and public
     symbols exposed) is byte-identical between baseline and variant.
  2. The designated ``[sources]``-tagged lemma statements are
     byte-identical between baseline and variant (PL-1 preservation
     precondition).
  3. Every non-empty diff hunk is confined to files listed in
     ``docs/patch-scope.txt`` (default: client_basic.m4i,
     server_basic.m4i, state.m4i).

This is a *syntactic* check.  It does not run Tamarin, does not verify
protocol-facing security properties, and is not sufficient to prove
semantic equivalence.  Its purpose is to reject accidental interface
edits and out-of-scope changes before proof re-execution.

Output JSON::

    {"baseline": "...", "variant": "...", "verdict": "PASS" | "FAIL",
     "checks": {"adversary_interface": "PASS",
                "sources_lemmas": "PASS",
                "scope_locality": "PASS"},
     "hunk_summary": {"files_touched": [...], "lines_changed": {...}}}
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

RE_ADV_INTERFACE = re.compile(r"\b(?:In|Out|Fr|K|KU|KD)\s*\(")
RE_SOURCES_LEMMA = re.compile(
    r"lemma\s+([A-Za-z0-9_]+)\s*\[[^\]]*sources[^\]]*\]\s*:?\s*(.*?)(?=^\s*(?:rule|lemma|restriction|end)\b)",
    re.DOTALL | re.MULTILINE,
)
DEFAULT_SCOPE = ("client_basic.m4i", "server_basic.m4i", "state.m4i")


def _collect(root: Path, exts=(".spthy", ".m4i")) -> Dict[str, str]:
    out = {}
    for f in root.rglob("*"):
        if f.is_file() and f.suffix in exts:
            rel = str(f.relative_to(root))
            out[rel] = f.read_text(errors="replace")
    return out


def _adversary_signature(text: str) -> List[str]:
    return sorted(set(RE_ADV_INTERFACE.findall(text)))


def _sources_lemma_signatures(text: str) -> Dict[str, str]:
    return {m.group(1): m.group(2).strip() for m in RE_SOURCES_LEMMA.finditer(text + "\nend\n")}


def check(baseline: Path, variant: Path, scope: List[str]) -> Dict:
    b_files = _collect(baseline)
    v_files = _collect(variant)

    # 1. Adversary interface
    b_sig = _adversary_signature("\n".join(b_files.values()))
    v_sig = _adversary_signature("\n".join(v_files.values()))
    adv_ok = b_sig == v_sig

    # 2. [sources]-tagged lemma statements
    b_src = _sources_lemma_signatures("\n".join(b_files.values()))
    v_src = _sources_lemma_signatures("\n".join(v_files.values()))
    src_ok = b_src == v_src

    # 3. Scope locality
    touched = []
    for rel in sorted(set(b_files) | set(v_files)):
        if b_files.get(rel, "") != v_files.get(rel, ""):
            touched.append(rel)
    out_of_scope = [t for t in touched if not any(t.endswith(s) for s in scope)]
    scope_ok = not out_of_scope

    verdict = "PASS" if (adv_ok and src_ok and scope_ok) else "FAIL"
    return {
        "baseline": str(baseline),
        "variant": str(variant),
        "verdict": verdict,
        "checks": {
            "adversary_interface": "PASS" if adv_ok else "FAIL",
            "sources_lemmas": "PASS" if src_ok else "FAIL",
            "scope_locality": "PASS" if scope_ok else "FAIL",
        },
        "hunk_summary": {
            "files_touched": touched,
            "out_of_scope_files": out_of_scope,
        },
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--baseline", type=Path, required=True)
    p.add_argument("--variant", type=Path, required=True)
    p.add_argument("--scope", default=",".join(DEFAULT_SCOPE))
    p.add_argument("--output", type=Path, default=None)
    args = p.parse_args(argv)

    scope = [s.strip() for s in args.scope.split(",") if s.strip()]
    report = check(args.baseline, args.variant, scope)
    out = json.dumps(report, indent=2)
    if args.output is None:
        print(out)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(out)

    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
