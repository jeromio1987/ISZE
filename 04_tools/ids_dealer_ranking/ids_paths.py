"""Shared path helpers for IDS_2026 country folders."""

from __future__ import annotations

import sys
from pathlib import Path

_WORKSPACE = Path(__file__).resolve().parents[1] / "workspace"
if str(_WORKSPACE) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE))

from isze_paths import INBOX_DIR, ISZE_ROOT  # noqa: E402

REPO = ISZE_ROOT
DATA_ROOT = INBOX_DIR / "IDS_2026"
RANKINGS_DIR = DATA_ROOT / "rankings"

RSA_TEMPLATE = DATA_ROOT / "RSA" / "IDS Evaluation Sheet_rev11 Alta Motorsenter.xlsx"
BE_TEMPLATE = DATA_ROOT / "BE" / "BE" / "IDS Evaluation Sheet - De Corte.xlsx"
NL_OUTPUT = DATA_ROOT / "IDS Evaluation Sheet 2026 - NL.xlsx"
ITUK_INPUT = DATA_ROOT / "ITUK" / "IDS ITUK self evaluations.xlsx"
ITUK_OUTPUT = RANKINGS_DIR / "ITUK_dealer_ranking.xlsx"
MIDI_FILE = DATA_ROOT / "MIDI" / "MIDI_FR.xlsx"

SKIP_DIRS = {"rankings", "reports", "__pycache__", "MIDI"}

# On-disk folder name -> output country / tab label
COUNTRY_LABELS: dict[str, str] = {
    "Gasanzammit": "Malta",
    "Loutsios": "Cyprus",
}

LABEL_TO_FOLDER: dict[str, str] = {v: k for k, v in COUNTRY_LABELS.items()}


def country_label(folder_name: str) -> str:
    return COUNTRY_LABELS.get(folder_name, folder_name)


def data_folder_for_country(country: str) -> str:
    return LABEL_TO_FOLDER.get(country, country)


def resolve_input_dir(country: str, data_root: Path = DATA_ROOT) -> Path:
    """Find the folder that contains dealer .xlsx files for a country."""
    folder = data_folder_for_country(country)
    base = data_root / folder
    nested = base / country
    if nested.is_dir() and _has_xlsx(nested):
        return nested
    if _has_xlsx(base):
        return base
    if base.is_dir():
        for child in sorted(base.iterdir(), key=lambda p: p.name.casefold()):
            if child.is_dir() and _has_xlsx(child):
                return child
    return base


def _has_xlsx(folder: Path) -> bool:
    return any(
        p.is_file() and not p.name.startswith("~$")
        for p in folder.glob("*.xlsx")
    )


def discover_country_folders(data_root: Path = DATA_ROOT) -> list[str]:
    """Country folder names that contain at least one dealer workbook."""
    if not data_root.is_dir():
        return []

    countries: list[str] = []
    for p in sorted(data_root.iterdir(), key=lambda x: x.name.casefold()):
        if not p.is_dir() or p.name in SKIP_DIRS:
            continue
        if p.name.upper() == "ITUK":
            if (p / "IDS ITUK self evaluations.xlsx").is_file():
                countries.append("ITUK")
            continue
        if _has_xlsx(resolve_input_dir(p.name, data_root)):
            countries.append(country_label(p.name))
    if "ITUK" in countries:
        countries = [c for c in countries if c != "ITUK"] + ["ITUK"]
    return countries
