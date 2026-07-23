"""
ISZE path discovery for non-PRISM tools.

Mirrors prism/config.py folder resolution (paths.yaml + legacy fallbacks).
Promoted from 04_tools/workspace/isze_paths.py — prefer importing from here.

Usage:
    from _shared.paths import ISZE_ROOT, DATA_ROOT, resolve_v3_workbook
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

_TOOLS = Path(__file__).resolve().parent.parent

V3_FILENAME = "ISZE_Parts_Intelligence_v3.xlsx"


def _find_isze_root(start: Path) -> Path:
    env = os.environ.get("ISZE_ROOT", "").strip()
    if env:
        candidate = Path(env).resolve()
        if (candidate / "FACTS.md").is_file() and (candidate / "paths.yaml").is_file():
            return candidate
    for candidate in [start, *start.parents]:
        if (candidate / "FACTS.md").is_file() and (candidate / "paths.yaml").is_file():
            return candidate
    raise FileNotFoundError(
        "ISZE root not found (expected FACTS.md + paths.yaml in an ancestor of 04_tools/)"
    )


ISZE_ROOT = _find_isze_root(_TOOLS)


@lru_cache(maxsize=1)
def _paths_doc() -> dict:
    path = ISZE_ROOT / "paths.yaml"
    if yaml is None or not path.is_file():
        return {}
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _resolve_folder(key: str, legacy: str) -> Path:
    mapped = (_paths_doc().get("folders") or {}).get(key, legacy)
    preferred = ISZE_ROOT / mapped
    legacy_path = ISZE_ROOT / legacy
    if preferred.exists():
        return preferred
    if legacy_path.exists():
        return legacy_path
    return preferred


DATA_ROOT = _resolve_folder("data", "Data")


def _resolve_data_subfolder(key: str) -> Path:
    """Numbered 01_data subfolder (paths.yaml data_subfolders) with legacy/junction fallback."""
    entry = (_paths_doc().get("data_subfolders") or {}).get(key) or {}
    numbered = entry.get("numbered")
    legacy = entry.get("legacy")
    if numbered:
        path = DATA_ROOT / numbered
        if path.exists():
            return path
    if legacy:
        path = DATA_ROOT / legacy
        if path.exists():
            return path
    if numbered:
        return DATA_ROOT / numbered
    if legacy:
        return DATA_ROOT / legacy
    return DATA_ROOT / key


DERIVED_DIR = _resolve_data_subfolder("derived")
_raw_root = _resolve_data_subfolder("raw")
RAW_SALES_DIR = _raw_root / "sales"
RAW_REFERENCE_DIR = _raw_root / "reference"
DASHBOARDS_JSON_DIR = _resolve_data_subfolder("dashboards")
GPT_SAFE_DIR = _resolve_data_subfolder("gpt_safe")
INBOX_DIR = _resolve_data_subfolder("inbox")

DASHBOARDS_DIR = _resolve_folder("dashboards", "Dashboards")
TOOLS_DIR = _resolve_folder("tools", "Tools")
MEMORY_DIR = _resolve_folder("memory", "memory")

DATA_BUILD_DIR = _resolve_data_subfolder("build")
EXPORTS_DIR = _resolve_data_subfolder("exports")
RAW_DEALER_SALES_DIR = _raw_root / "dealer_sales"
BRIEFS_DIR = MEMORY_DIR / "briefs"

TENDER_MONITOR_DIR = TOOLS_DIR / "ISZE_Tender_Monitor_Install"
AUTODOC_SCRAPER_DIR = TOOLS_DIR / "autodoc_scraper"

UIO_DIR = _resolve_folder("uio", "UIO")
ANALYTICS_DIR = _resolve_folder("analytics", "Projects")
DOCS_DIR = _resolve_folder("docs", "docs")

LEGACY_DIR = _resolve_folder("legacy", "91_legacy")

_deploy = (_paths_doc().get("deploy") or {})
_master = Path(_deploy.get("master_dashboard", "Master Dashboard"))
DEPLOY_DIR = ISZE_ROOT / _master


def resolve_first_existing(candidates: list[Path]) -> Optional[Path]:
    for path in candidates:
        if path.exists():
            return path.resolve()
    return None


def _v3_workbook_candidates(root: Path | None = None) -> list[Path]:
    """Return deterministic V3 workbook search candidates (first existing match wins)."""
    if root is None:
        autodoc = AUTODOC_SCRAPER_DIR
        data = DATA_ROOT
        gpt_safe = GPT_SAFE_DIR
        isze = ISZE_ROOT
        analytics = ANALYTICS_DIR
        legacy = LEGACY_DIR
    else:
        isze = Path(root).resolve()
        tools = isze / "04_tools"
        autodoc = tools / "autodoc_scraper"
        data = isze / "01_data"
        gpt_safe = data / "gpt_safe"
        analytics = isze / "03_analytics"
        legacy = isze / "91_legacy"

    return [
        autodoc / V3_FILENAME,
        autodoc / "_HANDOFF_BUNDLE" / V3_FILENAME,
        data / "models" / V3_FILENAME,
        gpt_safe / V3_FILENAME,
        # Legacy pre-reorg (transition only)
        isze / "Tools" / "autodoc_scraper" / V3_FILENAME,
        analytics / "Isuzu" / "data" / V3_FILENAME,
        legacy / "Isuzu" / "data" / V3_FILENAME,
    ]


def resolve_v3_workbook() -> Optional[Path]:
    """Return first existing ISZE_Parts_Intelligence_v3.xlsx from deterministic candidates."""
    return resolve_first_existing(_v3_workbook_candidates())
