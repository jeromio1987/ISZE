"""Frozen ITUK pilot-side dealer list for Universe parts pages."""
from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

ISZE_ROOT = Path(__file__).resolve().parents[3]
PILOT_CSV = (
    ISZE_ROOT
    / "Isuzu Universe"
    / "06_Working"
    / "PILOT_BASELINE_ITUK_2026-09-24"
    / "pilot_pairs_proposal.csv"
)
EXPECTED_HASH_PREFIX = "908c5a5259622d0d"

# Exact strings from the brief - do not edit.
DEALERS: list[dict[str, object]] = [
    {
        "code": "P1",
        "pair": 1,
        "sales_name": "FERNDOWN COMMERCIALS LTD",
        "ids_name": "Ferndown Commercials Ltd",
        "page_name": "Ferndown Commercials",
    },
    {
        "code": "P2",
        "pair": 2,
        "sales_name": "CORDWALLIS COMMERCIALS (HEATHROW)",
        "ids_name": "Cordwallis Commercials Heathrow",
        "page_name": "Cordwallis Commercials, Heathrow",
    },
    {
        "code": "P3",
        "pair": 3,
        "sales_name": "NORFOLK TRUCK & VAN LTD (NORWICH)",
        "ids_name": "Norfolk Truck & Van Norwich",
        "page_name": "Norfolk Truck & Van, Norwich",
    },
    {
        "code": "P4",
        "pair": 4,
        "sales_name": "AQUILA TRUCK CENTRES LTD (TIPTON)",
        "ids_name": "Aquila Truck Centres Ltd Tipton",
        "page_name": "Aquila Truck Centres, Tipton",
    },
    {
        "code": "P5",
        "pair": 5,
        "sales_name": "TRUCK & BUS CYMRU LTD",
        "ids_name": "Truck and Bus Cymru",
        "page_name": "Truck & Bus Cymru",
    },
    {
        "code": "R6",
        "pair": 6,
        "sales_name": "CUMBRIA TRUCK CENTRE LTD",
        "ids_name": "Cumbria Truck Centre Ltd",
        "page_name": "Cumbria Truck Centre",
    },
    {
        "code": "R7",
        "pair": 7,
        "sales_name": "RH COMMERCIAL VEHICLES LTD (NORTHAMPTON)",
        "ids_name": "RH Commercials Northampton",
        "page_name": "RH Commercial Vehicles, Northampton",
    },
    {
        "code": "R8",
        "pair": 8,
        "sales_name": "ALLPORTS GARAGES LIMITED (STOKE)",
        "ids_name": "Allports Stoke",
        "page_name": "Allports Garages, Stoke",
    },
]


def folder_slug(page_name: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch == " " else " " for ch in page_name)
    return "_".join(cleaned.split())


def pages_dir_for(dealer: dict[str, object], root: Path | None = None) -> Path:
    root = root or (Path(__file__).resolve().parents[1] / "pages")
    return root / f"{dealer['code']}_{folder_slug(str(dealer['page_name']))}"


def _sha256_prefix(path: Path, n: int = 16) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()[:n]


def assert_pilot_design() -> None:
    if not PILOT_CSV.exists():
        raise FileNotFoundError(PILOT_CSV)
    prefix = _sha256_prefix(PILOT_CSV)
    if prefix != EXPECTED_HASH_PREFIX:
        raise AssertionError(
            f"pilot design hash prefix {prefix} != {EXPECTED_HASH_PREFIX}"
        )
    df = pd.read_csv(PILOT_CSV)
    pilots = df[df["arm"].astype(str).str.strip().str.lower() == "pilot"].copy()
    if len(pilots) != 8:
        raise AssertionError(f"expected 8 pilot rows, got {len(pilots)}")
    by_pair = {
        int(r["pair"]): str(r["dealer_name"]).strip() for _, r in pilots.iterrows()
    }
    for d in DEALERS:
        pair = int(d["pair"])
        expected = str(d["sales_name"])
        actual = by_pair.get(pair)
        if actual != expected:
            raise AssertionError(
                f"pair {pair}: sales name {actual!r} != expected {expected!r}"
            )


assert_pilot_design()

if __name__ == "__main__":
    print(len(DEALERS))