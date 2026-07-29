#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TAMF audit tool (v1) -- the frozen, ~250-line grep-class R1--R4 classifier.

This is the "v1" code path referenced throughout the manuscript
(Section: Discipline Audit; Figure: audit-regex). It reads *unmodified*
Tamarin sources (.spthy / .m4 / .m4i) and emits a JSON rule-status report.
It does NOT invoke Tamarin: the classifier is the unit of analysis, and its
behaviour is fully determined by the enumerated R1--R4 regexes below plus a
declared, per-family attacker-vocabulary registry.

Reuse claim (as stated in the paper) is deliberately scoped:
  * code-level reuse  -- the R1--R4 regex core and this driver are unchanged
                         byte-for-byte across the three test artefacts;
  * family-level cfg  -- the per-family attacker vocabulary is supplied by a
                         small declared registry (ATTACKER_RULE_PATTERNS),
                         NOT by editing this core.
Fully data-independent static analysis is NOT claimed.

Usage:
    python3 scripts/audit_tool.py <root-dir> [--registry registry/tls_family.json] \
            [--json out.json] [--tsv out.tsv]

Exit status is always 0 on a successful scan; a non-empty JSON report is the
deliverable. The tool is intended to be CI-gatable (parse the JSON).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from typing import Dict, List

# ---------------------------------------------------------------------------
# Verbatim classification core (Figure: audit-regex in the manuscript).
# No regex below contains a repository-specific identifier.
# ---------------------------------------------------------------------------
R1_ATT      = re.compile(r'\b(Reveal|Corrupt|Compromise|Leak|Attacker_\w+)\b')
R1_CARRIER  = re.compile(r'\bState_\w*\{[^}]*\}|\bState_\w+\(')
R2_SEC_LEMMA = re.compile(r'lemma\s+\w+\s*(\[(reuse|use_induction)\])?')
R2_SOURCES   = re.compile(r'lemma\s+\w+\s*\[sources\]')
R3_BARE_LEMMA = re.compile(r'^\s*lemma\s+\w+\s*:')          # no [..] annotation
R4_PROV_HDR   = re.compile(r'^(//|--)\s*(Origin|Derived-from|Ported-from):')
R4_SHARED_INC = re.compile(r'^\s*include\(')

# File extensions that constitute an auditable Tamarin source.
AUDITABLE_EXT = (".spthy", ".m4", ".m4i")

# A file is a "rule-introducing file" (relevant to R4) if it declares a rule.
RULE_DECL = re.compile(r'^\s*rule\s+\w+\s*:', re.MULTILINE)

# Directories whose files are considered adversary / PKI includes for R1:
# an attacker token appearing *inside* these modules is expected, not a flag.
ADVERSARY_MODULE_HINTS = ("adversary", "pki")

# R3 exemption: shared lemma-declaration home.
R3_EXEMPT_DIR = os.path.join("lemmas", "includes")


@dataclass
class FileVerdict:
    path: str
    R1: bool = False
    R2: bool = False
    R3: bool = False
    R4: bool = False
    any: bool = False
    subsystem: str = "other"


@dataclass
class AuditReport:
    root: str
    registry: str
    n_files: int = 0
    totals: Dict[str, int] = field(default_factory=lambda: {"R1": 0, "R2": 0, "R3": 0, "R4": 0, "any": 0})
    rates: Dict[str, float] = field(default_factory=dict)
    files: List[FileVerdict] = field(default_factory=list)
    tool_sha256: str = ""


def _subsystem_of(rel_path: str) -> str:
    parts = rel_path.replace("\\", "/").split("/")
    if os.path.join("lemmas", "includes").replace("\\", "/") in rel_path.replace("\\", "/"):
        return "lemmas_includes"
    for token in ("model", "lemmas", "attack", "tests"):
        if token in parts:
            return token
    return "other"


def _load_registry(path: str) -> List[str]:
    """Load the per-family attacker-rule vocabulary. The registry only adds
    family-specific *lexical* names; the R1 structural core is untouched."""
    if not path or not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return list(data.get("ATTACKER_RULE_PATTERNS", []))


def _r1_regex(registry_tokens: List[str]) -> re.Pattern:
    """R1 attacker-token regex = fixed TLS-family core UNION declared registry
    tokens. The core is never edited; the union is a configuration point."""
    core = ["Reveal", "Corrupt", "Compromise", "Leak", r"Attacker_\w+"]
    alt = "|".join(core + [re.escape(t) if not t.endswith(r"\w+") else t for t in registry_tokens])
    return re.compile(r"\b(" + alt + r")\b")


def audit_file(path: str, rel_path: str, r1_att: re.Pattern) -> FileVerdict:
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    lines = text.splitlines()
    v = FileVerdict(path=rel_path, subsystem=_subsystem_of(rel_path))

    in_adv_module = any(h in rel_path.lower() for h in ADVERSARY_MODULE_HINTS)

    # R1: attacker-observable identifier outside adversary/PKI includes AND
    #     without a co-occurring State_ carrier tuple in the same file.
    if not in_adv_module:
        if r1_att.search(text) and not R1_CARRIER.search(text):
            v.R1 = True

    # R2: a security-lemma macro co-located with a [sources]-tagged macro in
    #     the same include, outside dedicated guidance modules.
    if R2_SOURCES.search(text) and R2_SEC_LEMMA.search(text):
        if v.subsystem not in ("lemmas_includes",):
            v.R2 = True

    # R3: a bare `lemma NAME:` (no annotation bracket) outside lemmas/includes/.
    if _subsystem_of(rel_path) != "lemmas_includes":
        for ln in lines:
            if R3_BARE_LEMMA.match(ln) and "[" not in ln:
                v.R3 = True
                break

    # R4: rule-introducing file with neither a provenance header nor a
    #     shared-header include( directive.
    if RULE_DECL.search(text):
        has_prov = any(R4_PROV_HDR.match(ln) for ln in lines)
        has_inc = any(R4_SHARED_INC.match(ln) for ln in lines)
        if not has_prov and not has_inc:
            v.R4 = True

    v.any = v.R1 or v.R2 or v.R3 or v.R4
    return v


def collect_files(root: str) -> List[str]:
    out = []
    for dirpath, _dirs, files in os.walk(root):
        for f in sorted(files):
            if f.endswith(AUDITABLE_EXT):
                out.append(os.path.join(dirpath, f))
    return sorted(out)


def self_sha256() -> str:
    with open(__file__, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def run_audit(root: str, registry_path: str) -> AuditReport:
    tokens = _load_registry(registry_path)
    r1_att = _r1_regex(tokens)
    report = AuditReport(root=root, registry=registry_path or "(none)", tool_sha256=self_sha256())
    for abspath in collect_files(root):
        rel = os.path.relpath(abspath, root)
        v = audit_file(abspath, rel, r1_att)
        report.files.append(v)
        for rule in ("R1", "R2", "R3", "R4"):
            if getattr(v, rule):
                report.totals[rule] += 1
        if v.any:
            report.totals["any"] += 1
    report.n_files = len(report.files)
    n = max(report.n_files, 1)
    report.rates = {k: round(100.0 * val / n, 2) for k, val in report.totals.items()}
    return report


def to_tsv(report: AuditReport) -> str:
    rows = ["path\tsubsystem\tR1\tR2\tR3\tR4\tany"]
    for v in report.files:
        rows.append("\t".join([
            v.path, v.subsystem,
            *("1" if getattr(v, r) else "0" for r in ("R1", "R2", "R3", "R4", "any")),
        ]))
    return "\n".join(rows) + "\n"


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="TAMF R1--R4 discipline audit (v1).")
    ap.add_argument("root", help="Root directory of the Tamarin theory to audit.")
    ap.add_argument("--registry", default="", help="Per-family attacker-vocabulary registry JSON.")
    ap.add_argument("--json", default="", help="Write JSON report to this path.")
    ap.add_argument("--tsv", default="", help="Write per-file TSV to this path.")
    args = ap.parse_args(argv)

    if not os.path.isdir(args.root):
        print(f"error: root not found: {args.root}", file=sys.stderr)
        return 2

    report = run_audit(args.root, args.registry)
    payload = asdict(report)

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True)
    if args.tsv:
        with open(args.tsv, "w", encoding="utf-8") as fh:
            fh.write(to_tsv(report))

    # Human-readable summary to stdout (also valid as a CI gate on the JSON).
    print(json.dumps({
        "root": report.root,
        "registry": report.registry,
        "n_files": report.n_files,
        "totals": report.totals,
        "rates_percent": report.rates,
        "tool_sha256": report.tool_sha256,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
