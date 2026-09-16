"""GPS / PMS addressable-opportunity linkage for tender opportunities (Phase 3).

Hard rules:
- Never invent numbers. Missing fleet_size or mapping => null fields.
- Never label outputs as expected/forecast revenue — addressable only.
- Never emit capture_rate > 1.0 (100%); surface as data-quality error.
- Product-fit gate: GPS € only for pickup/truck segments. Pure van/LCV /
  postal/courier gets null + "van/LCV — not pickup GPS" (no N-Series SPU
  in gps_spu_by_distributor.csv — do not invent a smaller wallet).
"""
from __future__ import annotations

import csv
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent
ISZE_ROOT = ROOT.parents[1]  # .../ISZE
GPS_CSV = ISZE_ROOT / "01_data" / "00_derived" / "gps_spu_by_distributor.csv"
PMS_CSV = ISZE_ROOT / "01_data" / "00_derived" / "pms_capture_by_db_year.csv"
MAP_YAML = ROOT / "country_distributor_map.yaml"

# Import product-fit helpers (same package dir)
try:
    from isze_core_v3 import (
        GPS_ELIGIBLE_SEGMENTS,
        PRODUCT_SEGMENT_LABELS,
        attach_product_segment,
    )
except ImportError:  # pragma: no cover
    GPS_ELIGIBLE_SEGMENTS = frozenset({"pickup", "truck"})
    PRODUCT_SEGMENT_LABELS = {
        "pickup": "Pickup / D-Max-shaped",
        "lcv_van": "Postal van / LCV",
        "truck": "Truck / chassis",
        "rm_only": "R&M only — no vehicle buy",
        "weak": "Generic vehicle — weak fit",
    }

    def attach_product_segment(row: Dict[str, Any]) -> Dict[str, Any]:
        row.setdefault("product_segment", "weak")
        row.setdefault("product_segment_label", PRODUCT_SEGMENT_LABELS["weak"])
        return row


_SEGMENT_GPS_BLOCK_REASON = {
    "lcv_van": "van/LCV — not pickup GPS",
    "rm_only": "R&M-only — no vehicle-buy GPS wallet",
    "weak": "weak product signal — GPS not applied",
}


def _load_yaml_map() -> Dict[str, Any]:
    text = MAP_YAML.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text) or {}
    except Exception:
        # Minimal fallback parser for our simple key: value file
        country: Dict[str, Optional[str]] = {}
        iso3: Dict[str, str] = {}
        section = None
        for line in text.splitlines():
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            if s.endswith(":") and not s.startswith(" "):
                section = s[:-1]
                continue
            if ":" in s:
                k, v = s.split(":", 1)
                k, v = k.strip(), v.split("#")[0].strip()
                if v == "null":
                    val: Optional[str] = None
                else:
                    val = v
                if section == "country_to_distributor":
                    country[k] = val
                elif section == "iso3_to_country":
                    iso3[k] = val or ""
        return {"country_to_distributor": country, "iso3_to_country": iso3}


@lru_cache(maxsize=1)
def _maps() -> Tuple[Dict[str, Optional[str]], Dict[str, str]]:
    data = _load_yaml_map()
    return (
        dict(data.get("country_to_distributor") or {}),
        dict(data.get("iso3_to_country") or {}),
    )


@lru_cache(maxsize=1)
def _gps_latest() -> Dict[str, Dict[str, Any]]:
    """distributor_code -> GPS wallet rates for latest year with usable SPU.

    Addressable SPU = max_spend_eur / uio_units (full genuine wallet per unit).
    Actual SPU = spend_per_unit_eur (what the network currently captures per unit).
    The design range ~EUR 250–800 matches addressable SPU, not actual capture SPU.
    """
    if not GPS_CSV.exists():
        return {}
    best: Dict[str, Dict[str, Any]] = {}
    with GPS_CSV.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            code = (row.get("distributor_code") or "").strip()
            spu_raw = (row.get("spend_per_unit_eur") or "").strip()
            if not code or not spu_raw:
                continue
            try:
                year = int(row.get("year") or 0)
                spu_actual = float(spu_raw)
            except ValueError:
                continue
            uio = _f(row.get("uio_units"))
            max_spend = _f(row.get("max_spend_eur"))
            addressable_spu: Optional[float] = None
            if uio and uio > 0 and max_spend and max_spend > 0:
                addressable_spu = max_spend / uio
            cap_raw = (row.get("gps_capture_vs_max") or "").strip()
            cap: Optional[float] = None
            if cap_raw:
                try:
                    cap = float(cap_raw)
                except ValueError:
                    cap = None
            prev = best.get(code)
            if prev is None or year > int(prev["year"]):
                best[code] = {
                    "year": year,
                    "country": (row.get("country") or "").strip(),
                    "spend_per_unit_eur": spu_actual,
                    "addressable_spu_eur": addressable_spu if addressable_spu is not None else spu_actual,
                    "uio_units": uio,
                    "max_spend_eur": max_spend,
                    "gps_capture_vs_max": cap,
                    "distributor_code": code,
                }
    return best


@lru_cache(maxsize=1)
def _pms_latest() -> Dict[str, List[Dict[str, Any]]]:
    """distributor_code -> list of genuine category rows for latest year."""
    if not PMS_CSV.exists():
        return {}
    # collect max year per distributor first
    rows: List[Dict[str, Any]] = []
    with PMS_CSV.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if (row.get("line_type") or "").strip().lower() != "genuine":
                continue
            try:
                year = int(row.get("year") or 0)
            except ValueError:
                continue
            rows.append({**row, "_year": year})
    max_year: Dict[str, int] = {}
    for row in rows:
        code = (row.get("distributor_code") or "").strip()
        if not code:
            continue
        max_year[code] = max(max_year.get(code, 0), row["_year"])
    out: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        code = (row.get("distributor_code") or "").strip()
        if not code or row["_year"] != max_year.get(code):
            continue
        uio = _f(row.get("uio_units"))
        expected = _f(row.get("expected_qty"))
        avg_sp = _f(row.get("avg_sp_eur"))
        capture = _f(row.get("capture_rate"))
        if uio is None or uio <= 0 or expected is None or avg_sp is None:
            continue
        out.setdefault(code, []).append(
            {
                "pms_category": row.get("pms_category"),
                "category_label": row.get("category_label"),
                "expected_qty_per_uio": expected / uio,
                "avg_sp_eur": avg_sp,
                "capture_rate": capture,
                "year": row["_year"],
            }
        )
    return out


def _f(v: Any) -> Optional[float]:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def resolve_distributor(country: str, country_code: str = "") -> Optional[str]:
    cmap, iso = _maps()
    name = (country or "").strip()
    code = (country_code or "").strip().upper()
    if not name and code:
        name = iso.get(code, "")
    if code and not name:
        name = iso.get(code, "")
    if name in cmap:
        return cmap.get(name)
    # try iso -> name -> map
    if code in iso:
        return cmap.get(iso[code])
    return None


def attach_gps_pms(row: Dict[str, Any]) -> Dict[str, Any]:
    """Add GPS/PMS addressable fields onto a notice or opportunity dict. Mutates and returns row."""
    # defaults — always present for schema stability
    row.setdefault("distributor_code", None)
    row.setdefault("gps_addressable_per_year_eur", None)
    row.setdefault("pms_demand_by_category", None)
    row.setdefault("capture_at_current_rate_eur", None)
    row.setdefault("capture_under_rm_eur", None)
    row.setdefault("opportunity_basis", None)
    row.setdefault("gps_spu_year", None)
    row.setdefault("gps_capture_rate", None)
    row.setdefault("data_quality_error", None)
    row.setdefault("product_segment", None)
    row.setdefault("product_segment_label", None)

    # Product-fit first — always classify so dashboard chips work even when unsized
    attach_product_segment(row)
    segment = row.get("product_segment") or "weak"
    seg_label = row.get("product_segment_label") or PRODUCT_SEGMENT_LABELS.get(segment, segment)

    # Commercial MAP: distributor + IDS dealer even when fleet is unknown (no GPS € invented).
    country = row.get("Country") or row.get("country") or ""
    ccode = row.get("Country Code") or row.get("country_code") or ""
    dist = resolve_distributor(str(country), str(ccode))
    row["distributor_code"] = dist
    try:
        from ids_dealer_linkage import attach_ids_dealer

        attach_ids_dealer(row)
        dist = row.get("distributor_code") or dist
    except Exception:
        pass

    fleet = row.get("fleet_size")
    if fleet in (None, "", 0, "0"):
        fleet = row.get("FleetSize")
    try:
        fleet_n = int(fleet) if fleet not in (None, "") else 0
    except (TypeError, ValueError):
        fleet_n = 0
    if fleet_n <= 0:
        return row

    # Product-fit gate: keep fleet visible; GPS € only for pickup/truck.
    # No N-Series SPU in GPS CSV — do not invent a van wallet.
    if segment not in GPS_ELIGIBLE_SEGMENTS:
        reason = _SEGMENT_GPS_BLOCK_REASON.get(segment, "product segment not GPS-eligible")
        row["gps_addressable_per_year_eur"] = None
        row["capture_at_current_rate_eur"] = None
        row["capture_under_rm_eur"] = None
        row["pms_demand_by_category"] = None
        row["gps_spu_year"] = None
        row["gps_capture_rate"] = None
        map_note = f", distributor={dist}" if dist else f", country={country!r} (no distributor map)"
        row["opportunity_basis"] = (
            f"fleet_size={fleet_n}{map_note}; product_segment={segment} ({seg_label}). "
            f"GPS € suppressed: {reason}. "
            f"GPS SPU is pickup/network UIO wallet — not applied to pure van/LCV/postal. "
            f"No N-Series SPU in gps_spu_by_distributor.csv (null, not 0)."
        )
        return row

    if not dist:
        row["opportunity_basis"] = (
            f"fleet_size={fleet_n}, product_segment={segment} ({seg_label}), "
            f"but no distributor mapping for country={country!r} code={ccode!r}"
        )
        return row

    gps = _gps_latest().get(dist)
    if not gps:
        row["opportunity_basis"] = (
            f"fleet_size={fleet_n}, product_segment={segment} ({seg_label}), "
            f"distributor={dist}, but no SPU row in gps_spu_by_distributor.csv"
        )
        return row

    spu_actual = float(gps["spend_per_unit_eur"])
    spu_addressable = float(gps.get("addressable_spu_eur") or spu_actual)
    year = int(gps["year"])
    cap = gps.get("gps_capture_vs_max")
    if cap is not None and cap > 1.0:
        row["data_quality_error"] = (
            f"gps_capture_vs_max={cap} > 1.0 for {dist} year={year} — denominator wrong; rates suppressed"
        )
        row["opportunity_basis"] = (
            f"fleet_size({fleet_n}) * addressable_spu({spu_addressable:.2f}) from {dist} {year}; "
            f"product_segment={segment} ({seg_label}); "
            f"capture rate suppressed due to data-quality error"
        )
        row["gps_addressable_per_year_eur"] = round(fleet_n * spu_addressable, 2)
        row["gps_spu_year"] = year
        row["capture_under_rm_eur"] = row["gps_addressable_per_year_eur"]
        return row

    # Addressable = full genuine wallet per unit (max_spend/uio), NOT current capture spend.
    addressable = round(fleet_n * spu_addressable, 2)
    row["gps_addressable_per_year_eur"] = addressable
    row["gps_spu_year"] = year
    row["gps_capture_rate"] = cap
    row["capture_under_rm_eur"] = addressable
    # At today's capture: fleet × actual spend/UIO (same as addressable × capture when consistent)
    row["capture_at_current_rate_eur"] = round(fleet_n * spu_actual, 2)

    # PMS category demand scaled by fleet / network UIO is already per-uio in _pms_latest
    cats = _pms_latest().get(dist) or []
    demand = []
    for c in cats:
        qty = fleet_n * float(c["expected_qty_per_uio"])
        rev = qty * float(c["avg_sp_eur"])
        demand.append(
            {
                "pms_category": c["pms_category"],
                "category_label": c["category_label"],
                "expected_qty": round(qty, 2),
                "addressable_eur": round(rev, 2),
                "avg_sp_eur": c["avg_sp_eur"],
                "year": c["year"],
            }
        )
    row["pms_demand_by_category"] = demand or None
    row["opportunity_basis"] = (
        f"gps_addressable_per_year_eur = fleet_size({fleet_n}) * "
        f"addressable_spu({spu_addressable:.2f} EUR) where addressable_spu = max_spend_eur/uio_units "
        f"for distributor {dist}, year {year}. "
        f"product_segment={segment} ({seg_label}) — GPS-eligible. "
        f"capture_at_current_rate_eur = fleet_size * actual spend_per_unit_eur ({spu_actual:.2f}). "
        f"capture_under_rm_eur = full addressable wallet (authorised R&M ceiling). "
        f"Label: addressable opportunity if won (no win-rate applied)."
    )
    return row


def enrich_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Attach linkage fields to every notice and opportunity in a tender_data payload."""
    for n in payload.get("notices") or []:
        attach_gps_pms(n)
    for o in payload.get("opportunities") or []:
        attach_gps_pms(o)
    try:
        from ids_dealer_linkage import enrich_payload_ids, export_derived_csv, ids_source_status

        # Idempotent second pass + meta status; export derived CSV when rankings exist
        enrich_payload_ids(payload)
        st = ids_source_status()
        if st.get("ids_rankings_xlsx_exists"):
            export_derived_csv()
    except Exception as exc:
        meta = payload.setdefault("meta", {})
        meta["ids_dealer"] = {"error": str(exc)}
    return payload


if __name__ == "__main__":
    # smoke: 10 vehicles in Belgium
    sample = {"fleet_size": 10, "Country": "Belgium", "Country Code": "BEL"}
    print(json.dumps(attach_gps_pms(sample), indent=2, ensure_ascii=False)[:1200])
