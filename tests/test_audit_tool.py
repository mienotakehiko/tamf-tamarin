#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Self-test: the audit tool must classify the flat vs structured hotspot
comparators as a matched rule-violating / rule-compliant pair, reproducing the
paper's stated join (flat raises R1/R4; structured clears them).

Runs standalone (python3 tests/test_audit_tool.py) or under pytest.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import audit_tool  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")


def _audit_single(relfile, registry="registry/tls_family.json"):
    import re
    tokens = audit_tool._load_registry(os.path.join(ROOT, registry))
    r1 = audit_tool._r1_regex(tokens)
    abspath = os.path.join(ROOT, relfile)
    return audit_tool.audit_file(abspath, relfile, r1)


def test_flat_raises_r1_r4():
    v = _audit_single("theories/kemtls_hotspots/flat/client_basic.m4i")
    assert v.R1, "flat variant must raise R1 (attacker token, no carrier)"
    assert v.R4, "flat variant must raise R4 (no provenance, no include)"


def test_structured_clears_r1_r4():
    v = _audit_single("theories/kemtls_hotspots/structured/client_basic.m4i")
    assert not v.R1, "structured variant must clear R1 (carrier co-occurs)"
    assert not v.R4, "structured variant must clear R4 (provenance header present)"


def test_regex_core_has_no_repo_identifier():
    src = open(os.path.join(ROOT, "scripts", "audit_tool.py"), encoding="utf-8").read()
    for banned in ("kemtls", "KEMTLS", "TLS13", "5G_AKA"):
        # the token may appear in comments/docstrings, but never inside a compiled regex line
        for line in src.splitlines():
            if line.strip().startswith(("R1_", "R2_", "R3_", "R4_")) and "re.compile" in line:
                assert banned.lower() not in line.lower(), \
                    f"regex core must contain no repo identifier: {banned}"


def _run_all():
    fns = [test_flat_raises_r1_r4, test_structured_clears_r1_r4,
           test_regex_core_has_no_repo_identifier]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print("all self-tests passed")


if __name__ == "__main__":
    _run_all()
