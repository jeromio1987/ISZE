"""Diagnose MIDI dealers vs Tomoe 27 Jul list after source install."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\04_tools\ids_dealer_ranking")
sys.path.insert(0, str(ROOT))

from build_ids_result_report import parse_midi_dealers  # noqa: E402
from midi_fr_ranking import (  # noqa: E402
    MIDI_FILE,
    collect_midi_total_dealers,
    discover_midi_cod_divs,
    load_network_names,
)

TARGETS = [
    "ATELIER REPARATION",
    "BIRRER",
    "ERNST MOSER",
    "CORPORATION MOTOR",
    "SUN CAR",
    "TOTANI",
    "CEAO",
    "TRUCK MOBILITY",
    "POIDS",
    "MOTOR SUD",
]

# Exact fragments from Tomoe IDS MIDI Data mail (27 Jul)
TOMOE_NAMES = [
    "ATELIER REPARATION POIDS",
    "BIRRER",
    "ERNST MOSER",
    "CORPORATION MOTOR SUD",
    "SUN CAR",
    "TOTANI",
    "CEAO MOTOR",
    "TRUCK MOBILITY",
]


def main() -> None:
    print("MIDI_FILE", MIDI_FILE, MIDI_FILE.exists(), MIDI_FILE.stat().st_size)
    print("cods", discover_midi_cod_divs())
    names = load_network_names(MIDI_FILE)
    print("network names", len(names))

    print("--- network matches ---")
    for k, v in sorted(names.items(), key=lambda x: x[1].lower()):
        u = v.upper()
        if any(t in u for t in TARGETS):
            print(repr(k), "->", v)

    for cod in ["CH", "IT", "ES", "FR"]:
        rows = collect_midi_total_dealers(cod)
        dealers = parse_midi_dealers(cod)
        zeros = [d for d in dealers if sum(d.question_scores.values()) == 0]
        print(
            f"\n=== {cod} ranking_rows={len(rows)} "
            f"result_dealers={len(dealers)} zero_total={len(zeros)} ==="
        )
        for d in dealers:
            u = d.name.upper()
            if any(t in u for t in TARGETS):
                tot = sum(d.question_scores.values())
                ana = d.meta.get("cod_ana")
                print(f"  FOUND {d.name}: {tot:.1f} pts  ana={ana}")
        if zeros:
            print(f"  zero sample ({min(10, len(zeros))}):")
            for d in zeros[:10]:
                print(
                    f"    {d.name} ana={d.meta.get('cod_ana')} "
                    f"qs={len(d.question_scores)}"
                )

    print("\n--- Tomoe name search across all MIDI result dealers ---")
    all_d = []
    for cod in ["FR", "IT", "ES", "CH"]:
        all_d.extend((cod, d) for d in parse_midi_dealers(cod))
    for needle in TOMOE_NAMES:
        hits = [
            (cod, d)
            for cod, d in all_d
            if needle.upper() in d.name.upper() or d.name.upper() in needle.upper()
        ]
        # fuzzy: all tokens present
        tokens = [t for t in needle.upper().split() if len(t) > 2]
        if not hits:
            hits = [
                (cod, d)
                for cod, d in all_d
                if all(t in d.name.upper() for t in tokens)
            ]
        if not hits:
            print(f"  MISSING: {needle}")
        else:
            for cod, d in hits:
                tot = sum(d.question_scores.values())
                print(f"  {needle} -> [{cod}] {d.name}: {tot:.1f}")


if __name__ == "__main__":
    main()
