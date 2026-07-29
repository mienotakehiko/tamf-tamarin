#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Objective, machine-measurable diff-surface metric for the KEMTLS hotspots.

Computes the two deltas the paper reports for the flat vs structured encoding
of the same kdf_context propagation obligation:
  * changed lines  (git diff --numstat equivalent)
  * U0 hunks       (git diff --unified=0 equivalent)

These are OBJECTIVE deltas only. No maintainability, readability, or
reviewer-effort claim is attached to them (as stated in the paper). A
human-subject reviewer-effort study is explicitly future work.

Usage:
    python3 scripts/diff_surface.py <flat_file> <structured_file>
"""
from __future__ import annotations

import difflib
import json
import sys


def changed_lines_and_hunks(a_path: str, b_path: str):
    a = open(a_path, encoding="utf-8").read().splitlines()
    b = open(b_path, encoding="utf-8").read().splitlines()
    sm = difflib.SequenceMatcher(a=a, b=b)
    changed, hunks = 0, 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != "equal":
            changed += (i2 - i1) + (j2 - j1)
            hunks += 1
    return changed, hunks


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: diff_surface.py <flat> <structured>", file=sys.stderr)
        return 2
    changed, hunks = changed_lines_and_hunks(sys.argv[1], sys.argv[2])
    print(json.dumps({
        "flat": sys.argv[1], "structured": sys.argv[2],
        "changed_lines": changed, "u0_hunks": hunks,
        "note": "Objective machine-measurable diff-surface delta; no "
                "maintainability/reviewer-effort claim attached.",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
