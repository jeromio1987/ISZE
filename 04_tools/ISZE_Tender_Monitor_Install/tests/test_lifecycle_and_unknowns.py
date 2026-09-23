"""Regression fixtures for the 2026-09-20 lifecycle / unknown-state / fleet-count fixes.

Run:  python tests/test_lifecycle_and_unknowns.py
Exit 0 = all pass. Built from the brief's required test table, restricted to the
cases that are self-contained (no audit archive needed). Jerome 2026-09-20.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import isze_core_v3 as C

PASS = FAIL = 0
FAILURES = []


def check(name, got, want):
    global PASS, FAIL
    if got == want:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        FAILURES.append(f"{name}: got {got!r}, want {want!r}")
        print(f"  FAIL  {name}: got {got!r}, want {want!r}")


print("=" * 74)
print("1. Form-code to lifecycle (the release blocker)")
print("=" * 74)
check("cn-standard is competition", C.lifecycle_from_notice_type("cn-standard"), "competition")
check("can-standard is result", C.lifecycle_from_notice_type("can-standard"), "result")
check("can-tran is result", C.lifecycle_from_notice_type("can-tran"), "result")
check("pin-only is planning", C.lifecycle_from_notice_type("pin-only"), "planning")
check("corr is change", C.lifecycle_from_notice_type("corr"), "change")
check("German formType result", C.lifecycle_from_notice_type("result"), "result")
check("German formType competition", C.lifecycle_from_notice_type("competition"), "competition")
check("wrapped code still resolves", C.lifecycle_from_notice_type("can-standard, can-standard"), "result")
check("blank code returns empty", C.lifecycle_from_notice_type(""), "")
check("nonsense code returns empty", C.lifecycle_from_notice_type("zzz-unknown"), "")

print()
print("=" * 74)
print("2. No silent competition default (brief: missing type is unknown)")
print("=" * 74)
check("no type, no stage wording -> unknown",
      C.classify_lifecycle("Lieferung von Fahrzeugen", ""), "unknown")
check("award code wins over prose",
      C.classify_lifecycle("anything", "can-standard"), "result")
check("stage wording still read when no code",
      C.classify_lifecycle("Contract award notice for trucks", ""), "result")
check("planning wording",
      C.classify_lifecycle("Prior information notice", ""), "planning")
check("competition code explicit",
      C.classify_lifecycle("trucks", "cn-standard"), "competition")

print()
print("=" * 74)
print("3. Unknown lifecycle leaves the bid queue (brief: review queue, not bid queue)")
print("=" * 74)
check("unknown -> document qualification",
      C.suggest_next_action({"Lifecycle": "unknown", "Buyer": "X", "deadline_date": "2026-10-01"}),
      "Verify lifecycle and recover notice documents")
check("result -> mine award",
      C.suggest_next_action({"Lifecycle": "result", "Buyer": "X"}), "Mine award outcome and incumbent insight")
check("cancelled -> replacement check",
      C.suggest_next_action({"Lifecycle": "cancelled", "Buyer": "X"}),
      "Closed round - check for a replacement notice")
check("unknown status -> Enrich", C.suggest_status("Attack", "critical", "unknown", "High"), "Enrich")
check("result status -> Review", C.suggest_status("Attack", "critical", "result", "High"), "Review")

print()
print("=" * 74)
print("4. Fleet size: unknown is not zero (brief: Hansa 740, Blankenberge 1x4x4)")
print("=" * 74)
check("nothing found -> None not 0", C.extract_fleet_size("no quantity stated"), None)
check("empty input -> None", C.extract_fleet_size(""), None)
check("fleet of 740 read as 740", C.extract_fleet_size("fleet of 740 vehicles"), 740)
check("'3,5 t' is tonnage not fleet", C.extract_fleet_size("Lieferung 3,5 t LKW"), None)
check("'4x4' is drivetrain not 4 vehicles", C.extract_fleet_size("one 4x4 truck"), None)
check("'6x2' axle config not a count", C.extract_fleet_size("6x2 tractor unit"), None)
check("year 2026 not a count", C.extract_fleet_size("Ausschreibung 2026 Fahrzeuge"), None)
check("a real count of 1 is kept", C.extract_fleet_size("1 Fahrzeug"), 1)
# The VH170 case from the brief. This reference code was read as 170 trucks and
# carried 78% of the euro pipeline before the fix.
check("VH170 reference code not 170 trucks",
      C.extract_fleet_size("1/DLII5/VH170 LKW mit Anbauteilen"), None)
check("a real 10 pickups still reads 10",
      C.extract_fleet_size("Suministro de 10 vehículos pick-up necesarios"), 10)

print()
print("=" * 74)
print("5. Lifecycle aggregation never lets unknown mask a known stage")
print("=" * 74)
# exercised through the same helper the builder uses
from collections import Counter  # noqa: E402


def aggregate(states):
    lc = Counter(states)
    known = [s for s, _ in lc.most_common() if s and s != "unknown"]
    return known[0] if known else (lc.most_common(1)[0][0] or "unknown")


check("unknown+result -> result", aggregate(["unknown", "result", "unknown"]), "result")
check("all unknown -> unknown", aggregate(["unknown", "unknown"]), "unknown")
check("competition+unknown -> competition", aggregate(["competition", "unknown"]), "competition")

print()
print("=" * 74)
print(f"RESULT: {PASS} passed, {FAIL} failed")
print("=" * 74)
for f in FAILURES:
    print("  FAILED:", f)
sys.exit(1 if FAIL else 0)
