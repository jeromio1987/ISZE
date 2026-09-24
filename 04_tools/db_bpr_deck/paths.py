"""Path discovery for the BPR deck tool.

Delegates to 04_tools/_shared/paths.py so this tool runs from anywhere and honours
$env:ISZE_ROOT, unlike the older hand-rolled builders that hardcode the drive letter.
"""
from __future__ import annotations

import sys
from pathlib import Path

_TOOLS = Path(__file__).resolve().parent.parent          # 04_tools/
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from _shared.paths import (  # noqa: E402  (import after sys.path fix, deliberately)
    ANALYTICS_DIR,
    DATA_ROOT,
    DERIVED_DIR,
    GPT_SAFE_DIR,
    INBOX_DIR,
    ISZE_ROOT,
    RAW_DEALER_SALES_DIR,
    TOOLS_DIR,
)

TOOL_DIR = Path(__file__).resolve().parent
CONFIG_DIR = TOOL_DIR / "config"
MEETINGS_DIR = ISZE_ROOT / "09_meetings"
PLANNING_DIR = DATA_ROOT / "11_planning"
PRISM_DIR = ANALYTICS_DIR / "Isuzu" / "prism"
SALES_FACT = DERIVED_DIR / "sales_fact.parquet"
KPI_MASTER = DATA_ROOT / "KPI Master File.xlsx"
VERIFICATION_REPORT = DERIVED_DIR / "_verification_report.json"
BP_WORKBOOK = PLANNING_DIR / "FY2027  BP VP&ACC.xlsx"
KPI_TARGETS_WORKBOOK = PLANNING_DIR / "ISZE_DB_KPI_Targets_FY2627_v1.xlsx"
CATALOG = DERIVED_DIR / "parts_catalog_dimension.csv"
VENV_PYTHON = ISZE_ROOT / "04_tools" / "workspace" / "venv" / "Scripts" / "python.exe"

_ASSETS = TOOLS_DIR / "ppt_template_v2" / "assets"
LOGO_WHITE = _ASSETS / ".." / "assets" / "isuzu_logo_red.png"      # red logo reads on both themes
LOGO_RED = _ASSETS / "isuzu_logo_red.png"


def logo_for(name: str) -> Path | None:
    """Map a theme's logo nickname to a file. Returns None when it is not on disk."""
    if name == "white":
        candidate = Path("C:/Users/jerom/Desktop/claude/ISZE/Isuzu Universe/_assets/isuzu_logo_white.png")
    else:
        candidate = LOGO_RED
    if not candidate.is_file():
        candidate = LOGO_RED
    return candidate if candidate.is_file() else None


def output_dir(db_key: str, fy_label: str) -> Path:
    """09_meetings/<KEY>_BPR_<FY>/ - created by the caller, never overwritten silently."""
    return MEETINGS_DIR / f"{db_key}_BPR_{fy_label}"


def log_dir(db_key: str, fy_label: str) -> Path:
    return output_dir(db_key, fy_label) / "_logs"


def rel(path: Path | None) -> str:
    """Show a path relative to the workspace when we can, full path when we cannot."""
    if path is None:
        return ""
    try:
        return str(Path(path).resolve().relative_to(ISZE_ROOT))
    except Exception:
        return str(path)
