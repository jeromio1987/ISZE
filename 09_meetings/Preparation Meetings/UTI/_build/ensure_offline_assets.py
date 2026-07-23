#!/usr/bin/env python3
"""Ensure offline Chart.js bundle exists under UTI/assets/."""
from __future__ import annotations

import urllib.request
from pathlib import Path

UTI = Path(__file__).resolve().parent.parent
ASSETS = UTI / "assets"
CHART_JS = ASSETS / "chart.umd.min.js"
CHART_URL = "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"
MIN_BYTES = 150_000


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    if CHART_JS.exists() and CHART_JS.stat().st_size >= MIN_BYTES:
        print(f"OK: {CHART_JS} ({CHART_JS.stat().st_size:,} bytes)")
        return
    print(f"Downloading Chart.js 4.4.1 → {CHART_JS}")
    urllib.request.urlretrieve(CHART_URL, CHART_JS)
    size = CHART_JS.stat().st_size
    if size < MIN_BYTES:
        raise SystemExit(f"Download too small ({size} bytes) — check network")
    print(f"Saved {size:,} bytes")


if __name__ == "__main__":
    main()
