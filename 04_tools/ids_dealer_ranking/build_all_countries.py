#!/usr/bin/env python3
"""Build dealer rankings for all country folders under Data/_INBOX/IDS_2026/."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

COUNTRIES = (
    "BE",
    "NL",
    "Denmark",
    "Poland",
    "Petros",
    "RSA",
    "IUK",
    "Romania",
    "Portugal",
    "Hungary",
    "Malta",
    "Cyprus",
    "Israel",
)


from ids_paths import DATA_ROOT, resolve_input_dir as _resolve_input_dir


def resolve_input_dir(root: Path, country: str) -> Path:
    return _resolve_input_dir(country, root)


def main() -> int:
    data_root = DATA_ROOT
    script = Path(__file__).with_name("build_country_ranking.py")
    rankings_dir = data_root / "rankings"
    rankings_dir.mkdir(parents=True, exist_ok=True)

    exit_code = 0
    for country in COUNTRIES:
        input_dir = resolve_input_dir(data_root, country)
        if not input_dir.is_dir():
            print(f"SKIP {country}: missing {input_dir}")
            exit_code = 1
            continue
        n = len([p for p in input_dir.glob("*.xlsx") if not p.name.startswith("~$")])
        if n == 0:
            print(f"SKIP {country}: no xlsx in {input_dir}")
            exit_code = 1
            continue

        output = rankings_dir / f"{country}_dealer_ranking.xlsx"
        print(f"\n=== {country} ({n} files) ===")
        result = subprocess.run(
            [
                sys.executable,
                str(script),
                "--input-dir",
                str(input_dir),
                "--country",
                country,
                "--output",
                str(output),
            ],
            check=False,
        )
        if result.returncode != 0:
            exit_code = result.returncode

    ituk_script = Path(__file__).with_name("build_ituk_ranking.py")
    ituk_input = data_root / "ITUK" / "IDS ITUK self evaluations.xlsx"
    if ituk_input.is_file():
        print("\n=== ITUK (consolidated workbook) ===")
        result = subprocess.run([sys.executable, str(ituk_script)], check=False)
        if result.returncode != 0:
            exit_code = result.returncode
    else:
        print("\nSKIP ITUK: missing consolidated workbook")

    print(f"\nRankings folder: {rankings_dir}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
