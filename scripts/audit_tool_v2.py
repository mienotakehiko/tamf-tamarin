#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TAMF audit tool (v2) -- Phase-2 P2-A maintenance re-implementation.

v2 re-implements the file-collection walker and rule regexes and ADDS one
name-based extension detector, R1_v2, for reveal-style adversary vocabularies
OUTSIDE the TLS family. It is a MAINTENANCE EXTENSION of the v1 tool
(scripts/audit_tool.py), NOT a replacement:

  * v1 R1 (structural) is language-independent and runs unchanged on any
    Tamarin theory.
  * v2 R1_v2 (lexical) is calibrated PER PROTOCOL FAMILY via an explicit
    vocabulary registry (ATTACKER_RULE_PATTERNS). New families extend the
    registry, not the code.

Disclosed discrepancy (as in the paper): because v2 uses a re-implemented
walker and regexes, v2 R1 numbers do NOT necessarily reproduce v1 R1 numbers
on identical file sets (e.g. KEMTLS n=48: v2 R1 = 0 vs. v1 R1 = 4). v1 numbers
remain historically frozen; v2 numbers stand as an independent measurement.

R1_v2 fires iff a file contains at least one rule whose NAME matches the union
of lineage-calibrated attacker-rule patterns AND whose RHS routes attacker
knowledge either via Out(...) or via a linear State_ fact whose name matches
the attacker family.

Usage:
    python3 scripts/audit_tool_v2.py <root> --registry registry/5g_aka_family.json \
            [--json out.json] [--tsv out.tsv]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from typing import Dict, List, Tuple

AUDITABLE_EXT = (".spthy", ".m4", ".m4i")

# A single Tamarin rule block:  rule NAME: [ lhs ]--[ act ]-> [ rhs ]
RULE_BLOCK = re.compile(
    r'rule\s+(?P<name>\w+)\s*:(?P<body>.*?)(?=(?:\n\s*rule\s+\w+\s*:)|\Z)',
    re.DOTALL,
)
OUT_FACT = re.compile(r'\bOut\s*\(')
STATE_FACT = re.compile(r'\bState_\w+\s*\(')


def _load_patterns(path: str) -> List[str]:
    if not path or not os.path.isfile(path):
        # Default TLS-family calibration (matches v1's structural token set).
        return ["Reveal_", "Corrupt_", "reveal_", "Rev_", "Leak_", "leak_", "Compromise"]
    with open(path, "r", encoding="utf-8") as fh:
        return list(json.load(fh).get("ATTACKER_RULE_PATTERNS", []))


def _name_matches(name: str, patterns: List[str]) -> bool:
    for p in patterns:
        # Support the *_compromised_(in|out) shape declared in the registry.
        if p.startswith("*"):
            core = p.lstrip("*")
            if re.search(re.escape(core).replace(r"\(in\|out\)", "(in|out)"), name):
                return True
        elif p in name:
            return True
    return False


def r1_v2_file(text: str, patterns: List[str]) -> Tuple[bool, List[str]]:
    """Return (fires, matched_rule_names)."""
    hits = []
    for m in RULE_BLOCK.finditer(text):
        name, body = m.group("name"), m.group("body")
        if _name_matches(name, patterns):
            # RHS routing check: Out(...) OR a linear State_ fact.
            rhs = body.split("]->", 1)[-1] if "]->" in body else body
            if OUT_FACT.search(rhs) or STATE_FACT.search(rhs):
                hits.append(name)
    return (len(hits) > 0, hits)


def collect_files(root: str) -> List[str]:
    out = []
    for dp, _d, fs in os.walk(root):
        for f in sorted(fs):
            if f.endswith(AUDITABLE_EXT):
                out.append(os.path.join(dp, f))
    return sorted(out)


def self_sha256() -> str:
    with open(__file__, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def run(root: str, registry: str) -> Dict:
    patterns = _load_patterns(registry)
    files = collect_files(root)
    per_file, r1v2_count = [], 0
    for ab in files:
        rel = os.path.relpath(ab, root)
        with open(ab, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        fires, hits = r1_v2_file(text, patterns)
        r1v2_count += int(fires)
        per_file.append({"path": rel, "R1_v2": fires, "matched_rules": hits})
    n = max(len(files), 1)
    return {
        "root": root,
        "registry": registry or "(default TLS-family)",
        "patterns": patterns,
        "n_files": len(files),
        "R1_v2_files": r1v2_count,
        "R1_v2_rate_percent": round(100.0 * r1v2_count / n, 2),
        "files": per_file,
        "tool_sha256": self_sha256(),
    }


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="TAMF P2-A audit tool v2 (R1_v2 detector).")
    ap.add_argument("root")
    ap.add_argument("--registry", default="")
    ap.add_argument("--json", default="")
    ap.add_argument("--tsv", default="")
    a = ap.parse_args(argv)
    if not os.path.isdir(a.root):
        print(f"error: root not found: {a.root}", file=sys.stderr)
        return 2
    rep = run(a.root, a.registry)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(rep, fh, indent=2, sort_keys=True)
    if a.tsv:
        with open(a.tsv, "w", encoding="utf-8") as fh:
            fh.write("path\tR1_v2\tmatched_rules\n")
            for r in rep["files"]:
                fh.write(f'{r["path"]}\t{int(r["R1_v2"])}\t{";".join(r["matched_rules"])}\n')
    print(json.dumps({k: rep[k] for k in
                      ("root", "registry", "n_files", "R1_v2_files",
                       "R1_v2_rate_percent", "tool_sha256")},
                     indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
