#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TAMF callback-based oracle (external search guidance).

Tamarin invokes an oracle by piping the list of open goals (one per line,
each prefixed by an integer index) on stdin and expecting the reordered list
of indices on stdout. This oracle implements the R2 "oracle-and-search-guidance
separation" contract: guidance lives OUTSIDE the theory, as a reusable module.

Usage (referenced from a theory or CLI):
    tamarin-prover --prove --heuristic=O --oraclename=oracle/tamf_oracle.py theory.spthy

Policy: prioritise goals that instantiate the State_Progress carrier and the
kdf_ctx field early, deprioritise pure Fr/Out administrative goals. This is the
oracle_only / full_tamf guidance layer; on already-solved easy rows it is
reported as HARMFUL (10-25x slowdown), and as framework infrastructure for
future hard-notion regimes -- exactly the scope the paper claims.
"""
import re
import sys

PRIORITISE = [re.compile(r'State_Progress'), re.compile(r'kdf_ctx'),
              re.compile(r'State_\w+\(')]
DEPRIORITISE = [re.compile(r'^\s*Fr\('), re.compile(r'!KU\(\s*~')]


def rank(goal_line: str) -> int:
    for p in PRIORITISE:
        if p.search(goal_line):
            return 0
    for p in DEPRIORITISE:
        if p.search(goal_line):
            return 2
    return 1


def main() -> int:
    lines = [ln.rstrip("\n") for ln in sys.stdin if ln.strip()]
    indexed = []
    for ln in lines:
        m = re.match(r'\s*(\d+)\s*:\s*(.*)', ln)
        if m:
            indexed.append((int(m.group(1)), m.group(2)))
    indexed.sort(key=lambda t: (rank(t[1]), t[0]))
    for idx, _goal in indexed:
        print(idx)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
