#!/usr/bin/env python3
"""After a green verify: refresh isze_data.json + static HTML overlays."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PRISM_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = PRISM_ROOT / "scripts"


def _run(name: str) -> int:
    path = SCRIPTS / name
    print(f"\n>> python {path.name}", flush=True)
    r = subprocess.run([sys.executable, str(path)], cwd=str(PRISM_ROOT))
    return r.returncode


def main() -> int:
    steps = [
        "build_isze_dashboard_json.py",
        "inject_dashboard_overlays.py",
    ]
    for s in steps:
        if _run(s) != 0:
            return 1
    print(
        "\nStatic dashboards updated. Sync to publish targets:\n"
        "  Dashboards\\sync_to_deploys.ps1",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
