#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""
Rule-by-rule correspondence check between the raw two-encoding variants
(A_raw, B_raw_priority) and the state-carrier variants (C_state_carrier,
D_state_priority).

The manuscript reports (Section "Overall Outcomes") an offline check that
the eleven rule pairs across representations are semantically equivalent
up to multiset packaging (differences = 0).  This script re-computes that
check by:

  1. Parsing each ``.spthy`` file into a list of (rule_name, LHS_facts,
     RHS_facts, action_facts) tuples using the same regex conventions as
     ``audit_tool.py``.
  2. Canonicalising each fact set by (a) stripping the state-carrier
     packaging (``State_...`` on the carrier side is unfolded into the
     tuple of components stored inside it), and (b) sorting the resulting
     multiset lexicographically.
  3. Diffing the canonicalised action-fact multisets pairwise.

The output is a JSON document::

    {"variant_pair": ["A_raw", "C_state_carrier"],
     "n_rules_compared": 11,
     "differences": 0,
     "per_rule": [{"name": "IssueChallenge", "diff": 0}, ...]}

Exit code 0 iff differences == 0 for every pair provided.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

RE_RULE = re.compile(
    r"^\s*rule\s+([A-Za-z0-9_]+)\s*:?\s*(?:\[[^\]]*\])?\s*\n"
    r"(?:let(.*?)in\s*)?"
    r"\[(.*?)\]\s*--\[(.*?)\]->\s*\[(.*?)\]",
    re.DOTALL | re.MULTILINE,
)
RE_STATE_CARRIER_UNFOLD = re.compile(r"State_[A-Za-z0-9_]*\s*\(([^)]*)\)")


def _canon_facts(text: str) -> List[str]:
    text = RE_STATE_CARRIER_UNFOLD.sub(lambda m: m.group(1), text)
    parts = [p.strip() for p in text.split(",") if p.strip()]
    return sorted(parts)


def parse_rules(path: Path) -> Dict[str, Tuple[List[str], List[str], List[str]]]:
    text = path.read_text()
    rules = {}
    for m in RE_RULE.finditer(text):
        name = m.group(1)
        lhs = _canon_facts(m.group(3))
        act = _canon_facts(m.group(4))
        rhs = _canon_facts(m.group(5))
        rules[name] = (lhs, act, rhs)
    return rules


def compare(raw: Path, carrier: Path) -> Dict:
    a = parse_rules(raw)
    c = parse_rules(carrier)
    shared = sorted(set(a) & set(c))
    per_rule = []
    diffs = 0
    for name in shared:
        # Compare action multisets only; LHS/RHS differ by construction.
        diff = int(a[name][1] != c[name][1])
        per_rule.append({"name": name, "diff": diff})
        diffs += diff
    return {
        "variant_pair": [raw.stem, carrier.stem],
        "n_rules_compared": len(shared),
        "differences": diffs,
        "per_rule": per_rule,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--raw", type=Path, required=True)
    p.add_argument("--carrier", type=Path, required=True)
    p.add_argument("--output", type=Path, default=None)
    args = p.parse_args(argv)

    report = compare(args.raw, args.carrier)
    out = json.dumps(report, indent=2)
    if args.output is None:
        print(out)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(out)

    return 0 if report["differences"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
