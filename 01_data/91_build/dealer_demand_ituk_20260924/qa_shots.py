#!/usr/bin/env python3
"""Headless Chrome screenshots of the built page. QA-internal, not a user open."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BUILD = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\dealer_demand_ituk_20260924")
PAGE = BUILD / "page" / "Dealer_Parts_Demand_ITUK_CY2025_INTERNAL.html"
QA = BUILD / "page" / "_qa"

CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]


def find_browser() -> str:
    for c in CANDIDATES:
        if Path(c).exists():
            return c
    raise SystemExit("No Chrome or Edge found")


def main() -> None:
    QA.mkdir(parents=True, exist_ok=True)
    for old in QA.glob("*.png"):
        old.unlink()
    exe = find_browser()
    print("browser:", exe)

    # one tall full-page capture per page. The URL must be the last argument and there
    # must be no second target, or headless refuses.
    shots = [
        ("full", 5200),
    ]
    for name, height in shots:
        out = QA / f"{name}.png"
        cmd = [exe, "--headless=new", "--disable-gpu", "--hide-scrollbars",
               f"--window-size=1400,{height}", "--force-device-scale-factor=1",
               "--user-data-dir=" + str(QA / ("_profile_" + name)),
               "--virtual-time-budget=5000",
               "--screenshot=" + str(out),
               "file:///" + str(PAGE).replace("\\", "/")]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
        print(name, "exit", r.returncode, "->", out.exists(),
              (r.stderr or "")[-200:])
    print("shots:", [p.name for p in QA.glob("*.png")])


if __name__ == "__main__":
    main()
