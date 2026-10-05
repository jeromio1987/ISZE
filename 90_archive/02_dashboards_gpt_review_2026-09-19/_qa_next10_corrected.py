#!/usr/bin/env python3
"""Headless screenshots for the corrected next10 suite (all files, 01-10)."""
from __future__ import annotations
import json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_next10_brief_corrected")
QA = OUT / "_qa"
QA.mkdir(parents=True, exist_ok=True)
HTMLS = sorted([p for p in OUT.glob("*.html")])
CHROME = [Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
          Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
          Path(r"C:\Users\jerom\AppData\Local\Google\Chrome\Application\chrome.exe")]

def chrome():
    for p in CHROME:
        if p.exists(): return p
    raise SystemExit("Chrome not found")

def main():
    taken = []
    for h in HTMLS:
        png = QA / (h.stem + "_viewport.png")
        subprocess.run([str(chrome()), "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--window-size=1440,900", f"--screenshot={png}", h.resolve().as_uri()],
                       check=False, capture_output=True, timeout=180)
        ok = png.exists() and png.stat().st_size > 1000
        taken.append({"html": h.name, "png": str(png), "ok": ok})
        print(("OK   " if ok else "FAIL ") + h.name, flush=True)
    rep = {"generated": datetime.now(timezone.utc).isoformat(), "taken": len(taken),
           "ok": sum(1 for t in taken if t["ok"]), "items": taken}
    (QA / "screenshot_report.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print(json.dumps({"taken": rep["taken"], "ok": rep["ok"]}, indent=2))
    if rep["ok"] < rep["taken"]: sys.exit(1)

if __name__ == "__main__":
    main()
