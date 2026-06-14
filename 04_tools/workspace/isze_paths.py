"""
Deprecated compatibility wrapper. Use 04_tools/_shared/paths.py.

Existing callers that add ``workspace/`` to sys.path and ``from isze_paths import ...``
continue to work unchanged.
"""

from __future__ import annotations

import sys
from pathlib import Path

_TOOLS = Path(__file__).resolve().parent.parent
_tools_str = str(_TOOLS)
if _tools_str not in sys.path:
    sys.path.insert(0, _tools_str)

from _shared.paths import (  # noqa: E402
    ANALYTICS_DIR,
    AUTODOC_SCRAPER_DIR,
    BRIEFS_DIR,
    DASHBOARDS_DIR,
    DASHBOARDS_JSON_DIR,
    DATA_BUILD_DIR,
    DATA_ROOT,
    DEPLOY_DIR,
    DERIVED_DIR,
    DOCS_DIR,
    EXPORTS_DIR,
    GPT_SAFE_DIR,
    INBOX_DIR,
    ISZE_ROOT,
    LEGACY_DIR,
    MEMORY_DIR,
    RAW_DEALER_SALES_DIR,
    RAW_REFERENCE_DIR,
    RAW_SALES_DIR,
    TENDER_MONITOR_DIR,
    TOOLS_DIR,
    UIO_DIR,
    V3_FILENAME,
    resolve_first_existing,
    resolve_v3_workbook,
)

__all__ = [
    "ANALYTICS_DIR",
    "AUTODOC_SCRAPER_DIR",
    "BRIEFS_DIR",
    "DASHBOARDS_DIR",
    "DASHBOARDS_JSON_DIR",
    "DATA_BUILD_DIR",
    "DATA_ROOT",
    "DEPLOY_DIR",
    "DERIVED_DIR",
    "DOCS_DIR",
    "EXPORTS_DIR",
    "GPT_SAFE_DIR",
    "INBOX_DIR",
    "ISZE_ROOT",
    "LEGACY_DIR",
    "MEMORY_DIR",
    "RAW_DEALER_SALES_DIR",
    "RAW_REFERENCE_DIR",
    "RAW_SALES_DIR",
    "TENDER_MONITOR_DIR",
    "TOOLS_DIR",
    "UIO_DIR",
    "V3_FILENAME",
    "resolve_first_existing",
    "resolve_v3_workbook",
]
