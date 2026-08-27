"""Wider lubricant-SKU audit — follow-up on data-integrity flag B.

Read-only. Flag B (`DATA_INTEGRITY_FLAGS_2026-05-28.md`) fixed one mislabelled
SKU (`550047337` "Rim ..." = Shell Rimula 15W40) and left a standing note that a
"wider lubricant-SKU audit is still advisable". This is that audit.

The GPS exclusion rule keys on the part-number prefixes ``55004*`` / ``55007*``
(Shell Rimula, historically Israel-only). That rule cannot see fluids sold under
other part-number families, so this script looks at the *description* instead:

  fluid markers   BESCO, RIMULA, ATF, COOLANT, LLC, GREASE, BRAKE FLUID,
                  ENGINE/GEAR OIL, CLEAN SUPER, WSI, DEXRON, ADBLUE, UREA,
                  or an SAE viscosity grade (15W40, 5W-30, ...)
  minus hardware  FILTER, ELEMENT, PUMP, GASKET, SENSOR, NIPPLE, ... — parts
                  *about* oil are not oil. "ELEMENT; OIL FILTER" and
                  "NIPPLE; GREASE" are hardware and must not be counted.

It reports what the prefix rule misses, per year and per distributor, and checks
whether those SKUs also sit in the PMS/BVP catalogue (which would contaminate
capture, not just the GPS parts base).

This script computes NO GPS percentage. It sizes an exclusion gap; applying it is
a pipeline change and a separate decision.

Usage:
    python 01_data/91_build/audit_lubricant_skus.py
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

_TOOLS = Path(__file__).resolve().parents[2] / "04_tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from _shared.paths import DERIVED_DIR  # noqa: E402

SALES_FACT = DERIVED_DIR / "sales_fact.parquet"
CATALOGUE = DERIVED_DIR / "parts_catalog_dimension.parquet"
DISTRIBUTORS = DERIVED_DIR / "distributor_dimension.csv"
OUT_JSON = DERIVED_DIR / "lubricant_sku_audit.json"
OUT_META = DERIVED_DIR / "lubricant_sku_audit.meta.json"
OUT_CSV = DERIVED_DIR / "lubricant_sku_audit_uncovered.csv"

# The prefixes the current GPS exclusion rule keys on (Shell Rimula).
KNOWN_PREFIX = re.compile(r"^(55004|55007)")

FLUID = re.compile(
    r"\b(BESCO|RIMULA|ATF|COOLANT|ANTIFREEZE|ANTI-FREEZE|GREASE|LLC|BRAKE\s*FLUID|"
    r"ENGINE\s*OIL|GEAR\s*OIL|CLEAN\s*SUPER|LUBRICAN|WSI|DEXRON|ADBLUE|UREA)\b",
    re.I,
)
VISCOSITY = re.compile(r"\b\d{1,2}W[-\s]?\d{2}\b", re.I)
# A part *about* oil is not oil. Without this the sweep is 98% oil filters.
HARDWARE = re.compile(
    r"\b(FILTER|ELEMENT|PUMP|GASKET|SENSOR|PAN|STRAINER|SEAL|COOLER|GAUGE|PIPE|HOSE|"
    r"CAP|SWITCH|RING|JET|DIPSTICK|LEVEL|BRACKET|COVER|VALVE|TANK|NOZZLE|TUBE|CASE|"
    r"BOLT|PLUG|SCREEN|GUIDE|ASM|KIT|BEARING|SHAFT|BODY|LINE|JOINT|NIPPLE|DISPLAY|RACK)\b",
    re.I,
)


def main() -> int:
    sales = pd.read_parquet(SALES_FACT)
    sales["pn"] = sales["part_number"].astype(str).str.strip()
    sales["desc"] = sales["description"].astype(str)

    is_fluid = (
        sales["desc"].str.contains(FLUID) | sales["desc"].str.contains(VISCOSITY)
    ) & ~sales["desc"].str.contains(HARDWARE)
    covered = sales["pn"].str.match(KNOWN_PREFIX)

    fluids = sales[is_fluid]
    uncovered = sales[is_fluid & ~covered]

    # Which distributors, by canonical key (sold_to_sap — never payer_code).
    dim = pd.read_csv(DISTRIBUTORS)
    dim["sold_to_sap"] = pd.to_numeric(dim["sold_to_sap"], errors="coerce")
    unc = uncovered.copy()
    unc["sold_to_sap_num"] = pd.to_numeric(unc["sold_to_sap"], errors="coerce")
    unc = unc.merge(
        dim[["sold_to_sap", "distributor_code", "gps_db_label"]],
        left_on="sold_to_sap_num",
        right_on="sold_to_sap",
        how="left",
        suffixes=("", "_dim"),
    )
    unc["db"] = unc["distributor_code"].fillna("UNMAPPED")

    by_db = (
        unc.groupby("db")["net_sales_value"].agg(eur="sum", rows="size")
        .sort_values("eur", ascending=False)
    )
    by_year = uncovered.groupby("year")["net_sales_value"].agg(eur="sum", rows="size")

    # Do these SKUs also sit in the PMS/BVP catalogue? That would hit capture too.
    catalogue = pd.read_parquet(CATALOGUE)
    catalogue["pn"] = catalogue["part_number"].astype(str).str.strip()
    pns = uncovered[["pn"]].drop_duplicates().merge(
        catalogue[["pn", "pms_category", "in_bvp_catalog"]], on="pn", how="left"
    )
    in_catalogue = int(pns["pms_category"].notna().sum())

    per_sku = (
        uncovered.groupby(["pn", "desc"])["net_sales_value"]
        .agg(eur="sum", rows="size")
        .reset_index()
        .sort_values("eur", ascending=False)
    )

    summary = {
        "scope": "sales_fact.parquet, all years present in the file",
        "rule_audited": "GPS lubricant exclusion keyed on part-number prefix 55004*/55007*",
        "fluids_total": {
            "part_numbers": int(fluids["pn"].nunique()),
            "eur": round(float(fluids["net_sales_value"].sum()), 2),
        },
        "covered_by_prefix_rule": {
            "part_numbers": int(fluids.loc[covered.loc[fluids.index], "pn"].nunique()),
            "eur": round(
                float(fluids.loc[covered.loc[fluids.index], "net_sales_value"].sum()), 2
            ),
        },
        "not_covered": {
            "part_numbers": int(uncovered["pn"].nunique()),
            "eur": round(float(uncovered["net_sales_value"].sum()), 2),
            "rows": int(len(uncovered)),
            "by_year": {
                str(int(y)): round(float(r.eur), 2) for y, r in by_year.iterrows()
            },
            "by_distributor": {
                str(k): round(float(v), 2) for k, v in by_db["eur"].items()
            },
            "distributors_touched": int(by_db.shape[0]),
        },
        "pms_catalogue_contamination": {
            "uncovered_pns_in_pms_catalogue": in_catalogue,
            "note": (
                "0 means these fluids sit in the GPS parts base only and do not "
                "inflate PMS capture actuals."
            ),
        },
        "caveats": [
            "Description-based detection. A fluid with no fluid marker in its "
            "description is not caught; a hardware part named like a fluid is.",
            "Sizes an exclusion gap only. No GPS percentage is computed or restated here.",
        ],
    }

    OUT_JSON.write_text(json.dumps(summary, indent=1), encoding="utf-8")

    root = DERIVED_DIR.parents[1]
    OUT_META.write_text(
        json.dumps(
            {
                "measured_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "source": "sales_fact.parquet description sweep vs 55004*/55007* prefix rule",
                "builder": "01_data/91_build/audit_lubricant_skus.py",
                "read_only": True,
                "follow_up_to": "DATA_INTEGRITY_FLAGS_2026-05-28.md flag B",
                "uncovered_pns": summary["not_covered"]["part_numbers"],
                "uncovered_eur": summary["not_covered"]["eur"],
                "outputs": {
                    "findings": str(OUT_JSON.relative_to(root).as_posix()),
                    "uncovered_skus": str(OUT_CSV.relative_to(root).as_posix()),
                },
            },
            indent=1,
        ),
        encoding="utf-8",
    )
    per_sku.rename(columns={"pn": "part_number", "desc": "description"}).to_csv(
        OUT_CSV, index=False
    )

    print(json.dumps(summary, indent=1))
    print(f"\nwrote {OUT_JSON}\nwrote {OUT_META}\nwrote {OUT_CSV}  ({len(per_sku)} SKUs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
