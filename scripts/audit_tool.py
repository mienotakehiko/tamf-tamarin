#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""
TAMF audit tool.

Applies four pre-committed static rules (R1--R4) to Tamarin theory sources
(``.spthy``, ``.m4i`` and other text files under a repository tree).

The rules are the ones described in the manuscript (Section "Discipline
Audit").  They are grep-class regular-expression checks; no Tamarin binary
is invoked, no proof is executed.  The tool is deliberately simple
(~250 lines) so that reviewers can re-implement it independently and
compare rule-status decisions.

Exit codes:
    0   audit completed (results written to --output).
    2   invocation / IO error.

Typical usage::

    python3 scripts/audit_tool.py --root /path/to/kemtls-repo \\
        --output measurements/kemtls/audit.json

The output is a single JSON document with the following shape::

    {
      "tool_version": "1.0.0",
      "root": "...",
      "n_files": 48,
      "any_violation_count": 16,
      "any_violation_rate": 0.3333,
      "rule_counts": {"R1": 4, "R2": 4, "R3": 3, "R4": 11},
      "files": [
        {"path": "model/client_basic.m4i",
         "R1": true, "R2": false, "R3": false, "R4": true,
         "any": true, "evidence": {...}},
        ...
      ]
    }

The reported statistics (48/16, 149/74, 7/7) are reproducible from the
KEMTLS-TLS13Tamarin, TLS13Tamarin ``rev21``, and Tamarin 5G-AKA sources
at the commit hashes recorded in ``external/frozen-commits.txt``.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

TOOL_VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# Rule definitions (pre-committed at design stage; not tuned per repository).
#
# R1 -- Attacker-visible state on the wire.
#       A rule whose left-hand-side (LHS) contains an ``In(...)`` fact and
#       whose right-hand-side (RHS) exposes a state-carrier fact directly
#       to the network via ``Out(...)`` without going through a designated
#       state-carrier fact (``State_...`` or a ``!Ltk``-like persistent
#       fact).  Files matching this heuristic have attacker-visible state
#       that is neither packaged into a carrier nor protected as a
#       persistent secret.
#
# R2 -- Split-state premise inflation.
#       A rule LHS containing three or more distinct pattern-matched
#       state components of the same handshake instance (e.g. multiple
#       ``ClientState_*`` facts, or ``HA(...) HB(...) EA(...)`` split
#       across multiple facts on the LHS).  The threshold ``>= 3`` is
#       the pre-committed inflation threshold from the manuscript.
#
# R3 -- Unpackaged fresh nonces.
#       ``Fr(~n)`` bound in the LHS but consumed by an ``Out(...)`` fact
#       without being wrapped in an existing state carrier or key
#       schedule.  This exposes fresh values directly to the attacker
#       and typically signals ad-hoc modelling.
#
# R4 -- Restrictions/lemmas leaking model internals.
#       ``restriction`` or ``lemma`` blocks whose formulas reference a
#       state fact defined only for internal indexing (matched by the
#       pattern ``[A-Z][a-zA-Z_]*State[a-zA-Z_]*``) rather than a
#       protocol-level event.  This is the "leaky test" rule.
#
# The rules are intentionally coarse: they are meant to be replayed by an
# independent reviewer, not to serve as a semantic analyser.  Section
# "Threats to Validity" of the manuscript discusses tool bias explicitly.
# ---------------------------------------------------------------------------

RE_RULE_BLOCK = re.compile(
    r"^\s*rule\s+([A-Za-z0-9_]+)\s*:?\s*(?:\[[^\]]*\])?\s*\n(.*?)(?=^\s*(?:rule|lemma|restriction|end)\b)",
    re.DOTALL | re.MULTILINE,
)
RE_LHS_RHS = re.compile(r"\[(.*?)\]\s*--\[.*?\]->\s*\[(.*?)\]", re.DOTALL)
RE_IN_FACT = re.compile(r"\bIn\s*\(")
RE_OUT_FACT = re.compile(r"\bOut\s*\(")
RE_STATE_CARRIER = re.compile(r"\bState[_A-Za-z0-9]*\s*\(")
RE_LTK = re.compile(r"!\s*Ltk|!\s*Pk\b")
RE_FR = re.compile(r"\bFr\s*\(\s*~([A-Za-z0-9_]+)\s*\)")
RE_CLIENT_SERVER_STATE = re.compile(r"\b(?:Client|Server|Peer)State[A-Za-z0-9_]*\s*\(")
RE_HANDSHAKE_SPLIT = re.compile(
    r"\b(?:HA|HB|EA|EB|MA|MB|CH|SH|EE|CV|SF|CF|CT|EK|MK|HK|AK|K1|K2|K3)\s*\(", re.MULTILINE
)
RE_RESTRICTION_OR_LEMMA = re.compile(
    r"^\s*(restriction|lemma)\s+([A-Za-z0-9_]+)\s*:?\s*(?:\[[^\]]*\])?\s*\n(.*?)(?=^\s*(?:rule|lemma|restriction|end)\b)",
    re.DOTALL | re.MULTILINE,
)
RE_INTERNAL_STATE_REF = re.compile(r"\b[A-Z][a-zA-Z_]*State[a-zA-Z_]*\b")
RE_PROTOCOL_EVENT_HINT = re.compile(
    r"\b(?:Commit|Running|Secret|Auth|Origin|Finished|Accept|Complete|Sent|Received)[A-Za-z]*\b"
)


@dataclass
class FileVerdict:
    path: str
    R1: bool = False
    R2: bool = False
    R3: bool = False
    R4: bool = False
    evidence: Dict[str, List[str]] = field(default_factory=dict)

    @property
    def any(self) -> bool:
        return self.R1 or self.R2 or self.R3 or self.R4

    def to_json(self) -> Dict:
        return {
            "path": self.path,
            "R1": self.R1,
            "R2": self.R2,
            "R3": self.R3,
            "R4": self.R4,
            "any": self.any,
            "evidence": self.evidence,
        }


def _split_lhs_rhs(rule_body: str) -> Optional[Tuple[str, str]]:
    m = RE_LHS_RHS.search(rule_body)
    if not m:
        return None
    return m.group(1), m.group(2)


def _check_r1(rule_name: str, lhs: str, rhs: str, evidence: Dict[str, List[str]]) -> bool:
    if not RE_IN_FACT.search(lhs):
        return False
    if not RE_OUT_FACT.search(rhs):
        return False
    if RE_STATE_CARRIER.search(rhs) or RE_LTK.search(rhs):
        return False
    evidence.setdefault("R1", []).append(rule_name)
    return True


def _check_r2(rule_name: str, lhs: str, evidence: Dict[str, List[str]]) -> bool:
    hits = len(RE_CLIENT_SERVER_STATE.findall(lhs)) + len(RE_HANDSHAKE_SPLIT.findall(lhs))
    if hits >= 3:
        evidence.setdefault("R2", []).append(f"{rule_name}(n={hits})")
        return True
    return False


def _check_r3(rule_name: str, lhs: str, rhs: str, evidence: Dict[str, List[str]]) -> bool:
    fresh_names = RE_FR.findall(lhs)
    if not fresh_names:
        return False
    if not RE_OUT_FACT.search(rhs):
        return False
    # If any fresh name appears verbatim inside Out(...) not wrapped by
    # a State_ / senc / aenc / kdf pattern, flag R3.
    for n in fresh_names:
        pattern = re.compile(rf"Out\s*\([^)]*~{re.escape(n)}[^)]*\)")
        m = pattern.search(rhs)
        if m and "State_" not in m.group(0) and "senc" not in m.group(0) and "aenc" not in m.group(0):
            evidence.setdefault("R3", []).append(f"{rule_name}(~{n})")
            return True
    return False


def _check_r4(block_kind: str, block_name: str, body: str, evidence: Dict[str, List[str]]) -> bool:
    if not RE_INTERNAL_STATE_REF.search(body):
        return False
    # If the block also references a protocol-level event, it is not
    # considered purely internal.
    if RE_PROTOCOL_EVENT_HINT.search(body):
        return False
    evidence.setdefault("R4", []).append(f"{block_kind}:{block_name}")
    return True


def audit_file(path: Path) -> FileVerdict:
    verdict = FileVerdict(path=str(path))
    try:
        text = path.read_text(errors="replace")
    except OSError as exc:
        verdict.evidence["error"] = [f"read failed: {exc}"]
        return verdict

    for m in RE_RULE_BLOCK.finditer(text + "\nend\n"):
        rule_name = m.group(1)
        body = m.group(2)
        parts = _split_lhs_rhs(body)
        if parts is None:
            continue
        lhs, rhs = parts
        if _check_r1(rule_name, lhs, rhs, verdict.evidence):
            verdict.R1 = True
        if _check_r2(rule_name, lhs, verdict.evidence):
            verdict.R2 = True
        if _check_r3(rule_name, lhs, rhs, verdict.evidence):
            verdict.R3 = True

    for m in RE_RESTRICTION_OR_LEMMA.finditer(text + "\nend\n"):
        kind = m.group(1)
        name = m.group(2)
        body = m.group(3)
        if _check_r4(kind, name, body, verdict.evidence):
            verdict.R4 = True

    return verdict


def _iter_source_files(root: Path, patterns: Tuple[str, ...]) -> List[Path]:
    results: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip common vendor/build directories.
        dirnames[:] = [
            d for d in dirnames
            if d not in {".git", "node_modules", "build", "dist", "__pycache__", ".venv", "venv"}
        ]
        for fn in filenames:
            if any(fn.endswith(ext) for ext in patterns):
                results.append(Path(dirpath) / fn)
    return sorted(results)


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="TAMF R1--R4 static audit tool (pre-committed rules).",
    )
    p.add_argument("--root", type=Path, required=True, help="Repository root to audit")
    p.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Path to write the JSON report (default: stdout).",
    )
    p.add_argument(
        "--extensions",
        default=".spthy,.m4i",
        help="Comma-separated file extensions to audit (default: .spthy,.m4i).",
    )
    p.add_argument("--quiet", action="store_true", help="Do not print progress to stderr.")
    args = p.parse_args(argv)

    if not args.root.exists():
        print(f"error: --root does not exist: {args.root}", file=sys.stderr)
        return 2

    patterns = tuple(x.strip() for x in args.extensions.split(",") if x.strip())
    files = _iter_source_files(args.root, patterns)

    if not args.quiet:
        print(f"[audit_tool] {len(files)} files under {args.root}", file=sys.stderr)

    verdicts = [audit_file(f) for f in files]
    counts = {"R1": 0, "R2": 0, "R3": 0, "R4": 0}
    any_hits = 0
    for v in verdicts:
        for r in ("R1", "R2", "R3", "R4"):
            if getattr(v, r):
                counts[r] += 1
        if v.any:
            any_hits += 1

    report = {
        "tool_version": TOOL_VERSION,
        "root": str(args.root.resolve()),
        "n_files": len(verdicts),
        "any_violation_count": any_hits,
        "any_violation_rate": (any_hits / len(verdicts)) if verdicts else 0.0,
        "rule_counts": counts,
        "files": [v.to_json() for v in verdicts],
    }

    out = json.dumps(report, indent=2)
    if args.output is None:
        print(out)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(out)
        if not args.quiet:
            print(f"[audit_tool] wrote {args.output}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
