"""
PRISM - Data Integrity dashboard.

Single page consuming:
  - Data/derived/_verification_report.json (pipeline checks)
  - prism/data/sap_sold_to_mapping.csv (canonical distributor master)
  - prism/data/distributor_master_mapping.csv (richer reference)
  - selected derived CSVs (cross-system distributor_code reconciliation)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from config import DERIVED_DIR, MISLABELLED_SKU_AUDIT_CSV  # noqa: E402

PRISM_DATA = APP_DIR / "data"
REPORT_JSON = DERIVED_DIR / "_verification_report.json"

st.title("Data Integrity")
st.caption(
    "One-stop view: pipeline verification + cross-system reconciliation. "
    "Rebuild source: `prism/scripts/run_pipeline_and_verify.ps1`."
)


# --- 1. PIPELINE VERIFICATION SUMMARY ----------------------------------------

if not REPORT_JSON.exists():
    st.error(f"Missing {REPORT_JSON.name}. Run the pipeline first.")
    st.stop()

with REPORT_JSON.open(encoding="utf-8") as f:
    report = json.load(f)

summary = report.get("summary", {})
gen_at = report.get("generated_at", "unknown")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Generated", gen_at.replace("T", " ").replace("Z", " UTC"))
col2.metric("Pass", summary.get("pass", 0))
col3.metric("Warn", summary.get("warn", 0), delta_color="off")
col4.metric("Fail", summary.get("fail", 0), delta_color="inverse")

if summary.get("ok"):
    st.success(f"Pipeline OK - {summary.get('pass', 0)} checks passed.")
else:
    st.error("Pipeline has failures - see details below.")

# --- 2. FAILED / WARNED CHECKS (top of page) ---------------------------------

checks = report.get("checks", [])
problems = [c for c in checks if c.get("status") in ("warn", "fail")]
if problems:
    st.subheader("Issues to address")
    for c in problems:
        icon = "❌" if c["status"] == "fail" else "⚠️"
        with st.expander(f"{icon} {c['id']} - {c['message']}", expanded=True):
            st.code(json.dumps(c.get("detail", {}), indent=2), language="json")

# --- 3. ALL CHECKS (collapsed by default) ------------------------------------

with st.expander(f"All {len(checks)} pipeline checks", expanded=False):
    rows = []
    for c in checks:
        rows.append({
            "status": c.get("status"),
            "id": c.get("id"),
            "message": c.get("message"),
        })
    st.dataframe(pd.DataFrame(rows), width='stretch', hide_index=True)


# --- 4. CROSS-SYSTEM DISTRIBUTOR CODE RECONCILIATION (DI-10) -----------------

st.subheader("Cross-system distributor_code reconciliation (DI-10)")

sap_path = PRISM_DATA / "sap_sold_to_mapping.csv"
master_path = PRISM_DATA / "distributor_master_mapping.csv"

if not sap_path.exists():
    st.warning(f"Missing {sap_path.name}")
else:
    sap_codes = set(pd.read_csv(sap_path)["distributor_code"].dropna().astype(str))

    master_codes = set()
    if master_path.exists():
        mdf = pd.read_csv(master_path)
        if "distributor_code" in mdf.columns:
            master_codes = set(mdf["distributor_code"].dropna().astype(str))

    derived_sources = [
        "gps_spu_by_distributor.csv",
        "pms_capture_by_db_year.csv",
        "pms_opportunity_matrix.csv",
        "network_percentile.csv",
        "aim_exposure_by_db_year.csv",
        "substitution_by_db_year.csv",
        "bvp_addressable_basket.csv",
        "ituk_pms_pn_audit.csv",
    ]
    used_in_derived: set[str] = set()
    for name in derived_sources:
        p = DERIVED_DIR / name
        if not p.exists():
            continue
        d = pd.read_csv(p)
        col = "distributor_code" if "distributor_code" in d.columns else (
              "db_code" if "db_code" in d.columns else None)
        if col:
            used_in_derived |= set(d[col].dropna().astype(str))

    c1, c2, c3 = st.columns(3)
    c1.metric("Codes in sap_sold_to_mapping", len(sap_codes))
    c2.metric("Codes in distributor_master_mapping", len(master_codes))
    c3.metric("Distinct codes used in derived files", len(used_in_derived))

    extra_in_master = master_codes - sap_codes
    ghost_in_derived = used_in_derived - sap_codes - master_codes
    unused_in_master = sap_codes - used_in_derived

    if extra_in_master:
        st.warning(
            f"⚠️ In `distributor_master_mapping.csv` but NOT in `sap_sold_to_mapping.csv`: "
            f"{sorted(extra_in_master)}. Confirm whether these are reference-only countries "
            f"(no ISZE customer yet) or a mapping omission."
        )
    if ghost_in_derived:
        st.error(
            f"❌ Codes appear in derived files but in NO mapping: {sorted(ghost_in_derived)}. "
            f"This is a real defect."
        )
    if unused_in_master:
        st.info(
            f"ℹ️ In mapping but never referenced in any derived file: {sorted(unused_in_master)}. "
            f"Probably fine, but worth knowing."
        )
    if not (extra_in_master or ghost_in_derived):
        st.success("✅ No referential defects between mappings and derived files.")


# --- 5. MISLABELLED SKU AUDIT -------------------------------------------------

st.subheader("Mislabelled SKU audit (description vs spec)")
if MISLABELLED_SKU_AUDIT_CSV.exists():
    mis = pd.read_csv(MISLABELLED_SKU_AUDIT_CSV)
    st.caption(f"Source: `{MISLABELLED_SKU_AUDIT_CSV.name}` · fixes applied in `sales_loader.py` DESCRIPTION_OVERRIDES")
    st.dataframe(mis, width="stretch", hide_index=True)
    if not mis.empty and "rev_eur" in mis.columns:
        st.metric("Revenue on flagged PNs (all years)", f"€{mis['rev_eur'].sum():,.0f}")
else:
    st.info("Run `python scripts/audit_mislabelled_skus.py` to generate the audit file.")


# --- 6. KNOWN DI ITEMS NOT COVERED BY PIPELINE -------------------------------

st.subheader("DI items the pipeline does not yet check")
st.markdown(
    """
- **DI-2** Canonical UIO is **v19** (`06_uio/_CURRENT/`). Duplicate-path cross-check is still not automated.
- **DI-7** Two parallel "Competitiveness" definitions (static HTML vs ISZE_Dashboard) — no cross-system check
- **DI-8** AIM CY2026 billing dashboard shipped 2026-07-02 (`sales/AIM_Dashboard_CY2026.html`). Country-pack vintage labels still need a rebuild/ship when asked.
- **DI-9** `isze-tools` and `prism` don't share `sales_fact.parquet` — risk of dual price. ✅ **Fixed 2026-08-20** — `isze-tools/pages/6_Competitive_Parts.py` now reads `01_data/00_derived/sales_fact.parquet` (was a dead legacy TSV).
- **DI-11** Kosha plan tracker missing realistic trajectory line

See `docs/REFERENCE.md` for the full open list (tooling map archived 2026-06-13).
"""
)
