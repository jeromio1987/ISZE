"""Map SAP SaTy codes on CY billing to strategic dashboard order_type buckets."""

from __future__ import annotations

# Observed on CY2023–2025 exports: SOR, VOR, RUSH, PRD, SVOR, DR, CR, RE, FD, ZDR
VOR_CODES = frozenset({"VOR", "SVOR"})
URGENT_CODES = frozenset({"RUSH"})
BACKORDER_CODES = frozenset({"BO", "BK", "BACKORDER"})
STANDARD_CODES = frozenset({"SOR", "PRD", "DR", "CR", "RE", "FD", "ZDR"})


def normalize_saty(value) -> str:
    if value is None:
        return ""
    s = str(value).strip().upper()
    return "" if s in ("", "NAN", "NONE", "<NA>") else s


def saty_to_order_type(saty) -> str:
    s = normalize_saty(saty)
    if not s:
        return "other"
    if s in VOR_CODES:
        return "vor"
    if s in URGENT_CODES:
        return "urgent"
    if s in BACKORDER_CODES:
        return "backorder"
    if s in STANDARD_CODES:
        return "standard"
    return "other"


def is_vor_urgent(saty) -> bool:
    return saty_to_order_type(saty) in ("vor", "urgent")


def is_backorder(saty) -> bool:
    return saty_to_order_type(saty) == "backorder"
