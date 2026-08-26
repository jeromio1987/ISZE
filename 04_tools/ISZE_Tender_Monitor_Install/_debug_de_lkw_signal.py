#!/usr/bin/env python3
"""Test German LKW titles against selection + truck classification."""
from __future__ import annotations

import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from isze_core_v3 import (
    passes_isuzu_selection_gate,
    classify_product_segment,
    text_has_lcv_signal,
    text_has_isuzu_noise,
    ISUZU_LCV_SIGNAL_RE,
    _TRUCK_SHAPE_RE,
)

titles = [
    "Lieferung von einem LKW Einzelkabine mit Pritsche bis 3,5t zGM",
    "Reparatur Lkw B-BA 9850 AM HE",
    "Kauf von einem LKW-Fahrgestell mit einem Aufbau Gerätewagen",
    "Rahmenvereinbarung zur Durchführung von Fahrzeugkonservierungen",
    "8 Stück Nutzkraftwagen (NKW)",
    "Kauf E-LKW mit Kofferaufbau 7.5t",
]
for t in titles:
    print("---", t[:70])
    print("  lcv_signal", text_has_lcv_signal(t), "noise", text_has_isuzu_noise(t))
    print("  truck_re", bool(_TRUCK_SHAPE_RE.search(t)), "lcv_re", bool(ISUZU_LCV_SIGNAL_RE.search(t)))
    print("  selection", passes_isuzu_selection_gate(t, "", "", ""))
    print("  segment", classify_product_segment(t, "", "", ""))
