"""Proof that the guard fires on a quarantined code and stays silent on an ordinary one.

Runs the builder's own `pending_codes_in_text` against the real strings on disk, and shows the
carry-forward decision for one parked row and one ordinary row, side by side. No test data is
written to any file; the demonstration is in-memory.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
BUILDER = ROOT / "01_data" / "91_build" / "pn_ammo_probe_20260918" / "_vehicle_band_applicability.py"

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

spec = importlib.util.spec_from_file_location("_vba_probe", BUILDER)
mod = importlib.util.module_from_spec(spec)
sys.modules["_vba_probe"] = mod
spec.loader.exec_module(mod)

print("=" * 100)
print("GUARD FIRES - a quarantined code, written the way the EPC actually writes it")
print("=" * 100)
fires = [
    ("2016 NLR/NMR-LHD EURO6 EUROPE 16.0 - 17.0", "glued to a suffix: the token would be 'NMR-LHD'"),
    ("18- NLR/NMR-RHD EURO6 EUROPE 18.0 -", "glued to a suffix: the token would be 'NMR-RHD'"),
    ("NKR、NMR,NLR", "separated by an ideographic comma, not in the split set"),
    ("2021 NLR/NMR RHD EURO6 EUROPE 21.0 - 23.0", "space-separated (this one the old split DID catch)"),
    ("15- NLR/NMR/NMS85 EURO5B+ LHD 15.0 -", "slash-separated"),
]
for txt, why in fires:
    found = mod.pending_codes_in_text(txt)
    tok, wild = mod.tokens_from_text(txt)
    print(f"  {txt!r}")
    print(f"      exact-token split finds : {tok}   (wildcards {wild})")
    print(f"      pending_codes_in_text   : {found}   <- {why}")
    print(f"      fires: {bool(found)}")
    print()

print("=" * 100)
print("GUARD SILENT - ordinary codes, including the two the old build got wrong")
print("=" * 100)
silent = [
    ("2018 NNR/NPR-LHD EURO6 EUROPE 18.0 - 20.0", "ordinary N-series codes, no pending code"),
    ("2017 TFR/TFS(LHD)EXP 17.0 - 17.0", "the D-Max pickup pair; F* must not match TF*"),
    ("2018- NHR EURO6 18.0 -", "NHR is unresolved but NOT pending_ruling"),
    ("180 FRR(RHD)SPACECAB EURO6 18.0 -", "heavy truck family, no pending code"),
    ("", "empty string"),
]
for txt, why in silent:
    found = mod.pending_codes_in_text(txt)
    tok, wild = mod.tokens_from_text(txt)
    print(f"  {txt!r}")
    print(f"      exact-token split finds : {tok}")
    print(f"      pending_codes_in_text   : {found}   <- {why}")
    print(f"      fires: {bool(found)}   (must be False)")
    print()

print("=" * 100)
print("THE TWO CARRY-FORWARD DECISIONS, SIDE BY SIDE")
print("=" * 100)
print("  A parked row (5876103260, evidence 'NKR、NMR,NLR'):")
print("      pending_codes_in_text('NKR、NMR,NLR') -> "
      f"{mod.pending_codes_in_text('NKR、NMR,NLR')}")
print("      decision: carry the pre-change band forward (3.5t+5.5t), do NOT recompute")
print()
print("  An ordinary row (1876100570, evidence names only NLR):")
print("      pending_codes_in_text('NLR') -> "
      f"{mod.pending_codes_in_text('NLR')}")
print("      decision: recompute as before (7.5t) - the guard never enters")
