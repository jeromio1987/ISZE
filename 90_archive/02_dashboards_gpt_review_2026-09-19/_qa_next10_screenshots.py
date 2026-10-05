#!/usr/bin/env python3
"""Headless first-viewport screenshots for next10 fixed suite."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_next10_fixed")
QA = OUT / "_qa"
QA.mkdir(parents=True, exist_ok=True)

HTMLS = sorted(OUT.glob("0*.html"))

CHROME_CANDIDATES = [
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Users\jerom\AppData\Local\Google\Chrome\Application\chrome.exe"),
]


def chrome() -> Path:
    for p in CHROME_CANDIDATES:
        if p.exists():
            return p
    raise SystemExit("Chrome not found")


def shot(html: Path) -> Path:
    png = QA / (html.stem + "_viewport.png")
    url = html.resolve().as_uri()
    cmd = [
        str(chrome()),
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--window-size=1440,900",
        f"--screenshot={png}",
        url,
    ]
    subprocess.run(cmd, check=False, capture_output=True, timeout=120)
    return png


def main() -> None:
    taken = []
    for h in HTMLS:
        print("shot", h.name, flush=True)
        png = shot(h)
        taken.append({"html": h.name, "png": str(png), "ok": png.exists() and png.stat().st_size > 1000})
    report = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "taken": len(taken),
        "ok": sum(1 for t in taken if t["ok"]),
        "items": taken,
    }
    (QA / "screenshot_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if report["ok"] < report["taken"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
