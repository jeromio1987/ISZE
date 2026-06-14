#!/usr/bin/env python3
"""Build MIDI total and B.1 rankings for all countries in MIDI_FR.xlsx."""

from __future__ import annotations

import sys
from pathlib import Path

from midi_fr_ranking import MIDI_FILE, build_all_midi_rankings


def main() -> int:
    if not MIDI_FILE.is_file():
        print(f"Not found: {MIDI_FILE}", file=sys.stderr)
        return 1

    summary = build_all_midi_rankings(MIDI_FILE)
    if not summary:
        print("No MIDI country codes found in DLR SELF EVALUATION.", file=sys.stderr)
        return 2

    for label, n_total, n_b1 in summary:
        print(f"{label}: {n_total} total, {n_b1} B.1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
