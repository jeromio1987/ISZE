"""Verify Tomoe-flagged MIDI dealers after rebuild."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\04_tools\ids_dealer_ranking")
sys.path.insert(0, str(ROOT))

from build_ids_result_report import parse_midi_dealers  # noqa: E402
from midi_fr_ranking import collect_midi_total_dealers  # noqa: E402

# Tomoe 27 Jul: name fragment -> expected points (None = accept 0)
EXPECT = [
    ("FR", "ATELIER REPARATION POIDS", 212),
    ("FR", "AUBERT DIFFUSION", 0),
    ("FR", "ESSONNE POIDS LOURDS", 0),
    ("FR", "LOGIC AUTOMOBILES", 0),
    ("FR", "MDH SA", 0),
    ("FR", "SORELOC", 0),
    ("FR", "THEOBALD AUTOMOBILES", 46),
    ("CH", "BIRRER", 247),
    ("CH", "ERNST MOSER", 224),
    ("IT", "CORPORATION MOTOR SUD", 256),
    ("IT", "SUN CAR", 0),
    ("IT", "TOTANI", 251),
    ("ES", "CEAO MOTOR", 216),
    ("ES", "TRUCK MOBILITY", 256),
]


def find(dealers, needle: str):
    n = needle.upper()
    hits = [d for d in dealers if n in d.name.upper()]
    return hits


def main() -> None:
    for cod in ["FR", "IT", "ES", "CH"]:
        rows = collect_midi_total_dealers(cod)
        dealers = parse_midi_dealers(cod)
        zeros_r = sum(1 for r in rows if (r["assessed_points"] or 0) == 0)
        print(
            f"{cod}: ranking={len(rows)} (zeros={zeros_r}) "
            f"result={len(dealers)}"
        )

    print("\n--- Tomoe checklist ---")
    by_cod = {c: parse_midi_dealers(c) for c in ["FR", "IT", "ES", "CH"]}
    ok = True
    for cod, needle, exp in EXPECT:
        hits = find(by_cod[cod], needle)
        if not hits:
            print(f"FAIL MISSING [{cod}] {needle}")
            ok = False
            continue
        for d in hits:
            tot = round(sum(d.question_scores.values()), 1)
            status = "OK" if tot == float(exp) else f"MISMATCH got={tot}"
            if tot != float(exp):
                ok = False
            print(f"{status}: [{cod}] {d.name}: {tot} (expect {exp})")
    print("ALL_OK" if ok else "HAS_FAILURES")


if __name__ == "__main__":
    main()
