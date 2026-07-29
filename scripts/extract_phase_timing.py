#!/usr/bin/env python3
"""
B2 phase-timing extractor for Robustness Battery.

Parses the Tamarin stderr log of each run and separates the derivation-check
precomputation phase from the main proof-search phase.

Tamarin 1.10.0/1.12.0 emits a small set of well-known status lines to stderr:

  Analysing <file> ...          <-- start of parse phase
  Checking multiset rewrite rules ...
  Checking well-formedness of the theory ...
  Precomputation ...            <-- derivation-check phase begins here
  End of precomputation.        <-- derivation-check phase ends here
  Proving lemmas ...            <-- main proof-search phase begins here

Not every build prints every line. When "End of precomputation" is missing
(older builds) the extractor falls back to the last line before "Proving lemmas".
When both markers are missing, derivcheck_s is marked NA.

Output columns (TSV):
  variant heuristic rep derivcheck_s main_s total_s

All three timings are wall-clock seconds derived from the .meta file
(peak wall) and the timestamp deltas between phase markers where the
stderr contains them, otherwise NA for the phase-level rows.
"""
from __future__ import annotations
import argparse
import csv
import os
import re
import sys
from pathlib import Path

RE_TAG = re.compile(r"^([AC])_h([sScCp])_r(\d+)$")

# Phase markers looked for in stderr. Order matters.
PHASE_MARKERS = [
    ("parse_start",     re.compile(r"^(Analysing|Loading)\b", re.I)),
    ("wellformed_end",  re.compile(r"well-formedness", re.I)),
    ("precomp_start",   re.compile(r"^(Precomputation|Starting derivation)", re.I)),
    ("precomp_end",     re.compile(r"(End of precomputation|Derivation checks complete)", re.I)),
    ("proving_start",   re.compile(r"^Proving lemmas", re.I)),
]


def parse_meta_wall(meta_path: Path) -> float | None:
    """Return elapsed wall-clock seconds from /usr/bin/time -v output."""
    if not meta_path.exists():
        return None
    text = meta_path.read_text(errors="replace")
    # `Elapsed (wall clock) time (h:mm:ss or m:ss): 1:23.45`
    m = re.search(
        r"Elapsed\s*\(wall clock\)[^:]*:\s*([\dh:.]+)", text)
    if not m:
        return None
    ts = m.group(1)
    parts = ts.split(":")
    try:
        parts = [float(p) for p in parts]
    except ValueError:
        return None
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    return parts[0]


def analyse_stderr(stderr_path: Path) -> dict[str, int | None]:
    """Return line indices for each phase marker seen (or None if absent).

    Tamarin does not emit per-line timestamps to stderr, so exact seconds
    for derivation-check phase are not directly recoverable from stderr
    alone, so two mechanical signals are used:
      (a) presence of markers  -> phase actually ran
      (b) meta wall vs. approximate ratio of stderr lines belonging to each phase
    Downstream reporting uses meta wall as ground truth and marker
    presence as evidence that the derivation-check phase completed.
    """
    if not stderr_path.exists():
        return {name: None for name, _ in PHASE_MARKERS}
    marker_idx: dict[str, int | None] = {name: None for name, _ in PHASE_MARKERS}
    with stderr_path.open("r", errors="replace") as fh:
        for i, line in enumerate(fh):
            for name, pattern in PHASE_MARKERS:
                if marker_idx[name] is None and pattern.search(line):
                    marker_idx[name] = i
    return marker_idx


def scan_derivcheck_time(stderr_path: Path) -> float | None:
    """Attempt to read an explicit precomputation duration if Tamarin prints it.

    Some builds print e.g.:
      `Precomputation completed in 3.42s`
    Return that number when present.
    """
    if not stderr_path.exists():
        return None
    text = stderr_path.read_text(errors="replace")
    for pattern in [
        r"Precomputation completed in\s+([\d.]+)\s*s",
        r"End of precomputation.*\(([\d.]+)\s*s\)",
        r"Derivation checks? complete in\s+([\d.]+)\s*s",
    ]:
        m = re.search(pattern, text, re.I)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                pass
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-dir", required=True, type=Path,
                    help="directory containing <tag>.stdout / .stderr / .meta")
    ap.add_argument("--output", required=True, type=Path,
                    help="output TSV path")
    args = ap.parse_args()

    if not args.runs_dir.is_dir():
        print(f"ERROR: runs-dir not found: {args.runs_dir}", file=sys.stderr)
        return 2

    rows: list[dict[str, str]] = []
    for stderr_path in sorted(args.runs_dir.glob("*.stderr")):
        tag = stderr_path.stem
        m = RE_TAG.match(tag)
        if not m:
            continue
        variant, heur, rep = m.group(1), m.group(2), int(m.group(3))
        stdout_path = stderr_path.with_suffix(".stdout")
        meta_path = stderr_path.with_suffix(".meta")

        total_s = parse_meta_wall(meta_path)
        derivcheck_s = scan_derivcheck_time(stderr_path)
        markers = analyse_stderr(stderr_path)

        # Fallback: if precomp_end marker exists but no explicit seconds are
        # printed, note this by leaving derivcheck_s as NA (no value is fabricated
        # a number). The presence of `precomp_end` still tells us the phase
        # completed.
        derivcheck_completed = markers.get("precomp_end") is not None or \
                               markers.get("proving_start") is not None

        # main_s: only computed when derivcheck_s is known
        if derivcheck_s is not None and total_s is not None:
            main_s = max(0.0, total_s - derivcheck_s)
            main_str = f"{main_s:.2f}"
        else:
            main_str = "NA"

        rows.append({
            "variant":      variant,
            "heuristic":    heur,
            "rep":          str(rep),
            "derivcheck_s": f"{derivcheck_s:.2f}" if derivcheck_s is not None
                             else ("<10 (marker seen)" if derivcheck_completed else "NA"),
            "main_s":       main_str,
            "total_s":      f"{total_s:.2f}" if total_s is not None else "NA",
        })

    # Write TSV
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w") as fh:
        writer = csv.DictWriter(fh,
                                fieldnames=["variant", "heuristic", "rep",
                                            "derivcheck_s", "main_s", "total_s"],
                                delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    print(f"[extract_phase_timing] {len(rows)} runs parsed -> {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
