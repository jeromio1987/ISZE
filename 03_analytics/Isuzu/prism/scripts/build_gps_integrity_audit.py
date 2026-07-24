#!/usr/bin/env python3
"""
Cross-dashboard integrity audit: GPS warranty, PMS per-DB, BVP 0% sanity.

Outputs:
  Data/derived/_gps_integrity_audit.json
  Data/derived/_gps_integrity_audit.md
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import (  # noqa: E402
    DASHBOARDS_JSON_DIR,
    DATA_BUILD_DIR,
    DERIVED_DIR,
    GPS_SPU_BY_DB_CSV,
)
from modules.gps_warranty import warranty_data_gaps, warranty_notes, warranty_table  # noqa: E402

AUDIT_JSON = DERIVED_DIR / "_gps_integrity_audit.json"
AUDIT_MD = DERIVED_DIR / "_gps_integrity_audit.md"
AUDIT_CSV = DERIVED_DIR / "_gps_integrity_audit_rows.csv"
PMS_SUMMARY = DERIVED_DIR / "pms_summary_by_db.csv"
DB_MIX = DERIVED_DIR / "db_parts_mix_classification.csv"
V9_SNAPSHOT = DATA_BUILD_DIR / "gps_v9_snapshot.json"
ISZE_JSON = DASHBOARDS_JSON_DIR / "isze_data.json"


def _load_v9_sales() -> dict[str, float]:
    if not V9_SNAPSHOT.exists():
        return {}
    payload = json.loads(V9_SNAPSHOT.read_text(encoding="utf-8"))
    out: dict[str, float] = {}
    # base25 rows: [db, uio_2025, max_spend_2025, sales_cy2025]
    for row in payload.get("base25") or []:
        if isinstance(row, (list, tuple)) and len(row) >= 4:
            out[str(row[0])] = float(row[3])
    return out


def build_audit() -> dict:
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    issues: list[dict] = []
    rows: list[dict] = []

    if not GPS_SPU_BY_DB_CSV.exists():
        return {"generated_at": generated, "error": "gps_spu_by_distributor.csv missing", "rows": []}

    gps = pd.read_csv(GPS_SPU_BY_DB_CSV)
    # Audit the latest year the warranty basis actually covers (CY2025), not gps["year"].max():
    # a newer partial year (e.g. 2026 Jan-Mar only) has no warranty match and would otherwise
    # flood every DB with false "warranty_not_in_pipeline" / "v9_sales_delta" issues.
    from modules.gps_warranty import WARRANTY_YEAR  # noqa: E402
    available_years = gps["year"].dropna().astype(int)
    yr = WARRANTY_YEAR if WARRANTY_YEAR in available_years.values else int(available_years.max())
    gps_y = gps[gps["year"] == yr].copy()

    mix = pd.read_csv(DB_MIX) if DB_MIX.exists() else pd.DataFrame()
    mix_y = mix[mix["year"] == yr] if not mix.empty and "year" in mix.columns else pd.DataFrame()

    pms = pd.read_csv(PMS_SUMMARY) if PMS_SUMMARY.exists() else pd.DataFrame()
    v9_sales = _load_v9_sales()
    warr = warranty_table()
    gaps = warranty_data_gaps()

    for _, g in gps_y.iterrows():
        db = str(g["distributor_code"])
        sales = float(g.get("total_sales_eur") or 0)
        w_eur = g.get("warranty_parts_eur")
        w_val = float(w_eur) if pd.notna(w_eur) else None
        spu = float(g.get("spend_per_unit_eur") or 0)
        spu_ex = g.get("spend_per_unit_ex_warranty_eur")
        spu_ex_f = float(spu_ex) if pd.notna(spu_ex) else None
        cap = g.get("gps_capture_vs_max")
        cap_ex = g.get("gps_capture_ex_warranty_vs_max")

        m = mix_y[mix_y["distributor_code"] == db]
        bvp_cap = float(m["contested_bvp_capture"].iloc[0]) if not m.empty else None
        contested = float(m["contested_eur"].iloc[0]) if not m.empty else None

        p = pms[pms["distributor_code"] == db]
        oil_cap = float(p["oil_filter_capture"].iloc[0]) if not p.empty and pd.notna(p["oil_filter_capture"].iloc[0]) else None
        pms_gap = float(p["revenue_gap_eur_sum"].iloc[0]) if not p.empty else None

        v9 = v9_sales.get(db)
        sales_delta_pct = round(100 * (sales - v9) / v9, 2) if v9 and v9 > 0 else None

        # Traffic light shift ex-warranty
        tl_shift = None
        if pd.notna(g.get("traffic_light_v9")) and pd.notna(g.get("traffic_light_v9_ex_warranty")):
            if g["traffic_light_v9"] != g["traffic_light_v9_ex_warranty"]:
                tl_shift = f"{g['traffic_light_v9']} -> {g['traffic_light_v9_ex_warranty']}"

        # BVP 0% sanity: low contested BVP + warranty is expected (warranty = genuine)
        bvp_verdict = None
        if bvp_cap is not None and contested and contested > 5000:
            if bvp_cap < 0.05:
                if w_val and w_val > 5000:
                    bvp_verdict = "plausible_genuine_defence"
                else:
                    bvp_verdict = "low_bvp_no_large_warranty"
            elif bvp_cap > 0.7:
                bvp_verdict = "bvp_winning_contested"

        if db in gaps:
            issues.append({"db": db, "type": "warranty_gap", "detail": warranty_notes().get(db, "UMI LCV missing")})
        if w_val is None and db in warr:
            issues.append({"db": db, "type": "warranty_not_in_pipeline", "detail": "GPS CSV missing warranty columns"})
        if sales_delta_pct is not None and abs(sales_delta_pct) > 2:
            issues.append({"db": db, "type": "v9_sales_delta", "detail": f"Pipeline vs v9 sales {sales_delta_pct:+.1f}%"})

        rows.append(
            {
                "distributor_code": db,
                "year": yr,
                "total_sales_eur": round(sales, 0),
                "warranty_parts_eur": round(w_val, 0) if w_val is not None else None,
                "sales_ex_warranty_eur": round(float(g["sales_ex_warranty_eur"]), 0)
                if pd.notna(g.get("sales_ex_warranty_eur"))
                else None,
                "spend_per_unit_eur": round(spu, 1),
                "spend_per_unit_ex_warranty_eur": round(spu_ex_f, 1) if spu_ex_f is not None else None,
                "gps_capture_vs_max": round(float(cap), 3) if pd.notna(cap) else None,
                "gps_capture_ex_warranty_vs_max": round(float(cap_ex), 3) if pd.notna(cap_ex) else None,
                "traffic_light_v9": g.get("traffic_light_v9"),
                "traffic_light_v9_ex_warranty": g.get("traffic_light_v9_ex_warranty"),
                "traffic_light_shift_ex_warranty": tl_shift,
                "contested_bvp_capture": round(bvp_cap, 3) if bvp_cap is not None else None,
                "contested_eur": round(contested, 0) if contested else None,
                "bvp_low_capture_verdict": bvp_verdict,
                "oil_filter_capture": round(oil_cap, 3) if oil_cap is not None else None,
                "pms_revenue_gap_eur": round(pms_gap, 0) if pms_gap is not None else None,
                "v9_sales_delta_pct": sales_delta_pct,
            }
        )

    # Stale JSON feed check
    feed_stale = None
    if ISZE_JSON.exists():
        meta = json.loads(ISZE_JSON.read_text(encoding="utf-8")).get("_meta", {})
        gps_block = json.loads(ISZE_JSON.read_text(encoding="utf-8")).get("gps", {})
        has_warranty_in_json = "warranty_parts_eur" in str(gps_block)
        feed_stale = {
            "prism_refreshed": meta.get("prism_refreshed"),
            "has_warranty_fields": has_warranty_in_json,
            "has_pms_all_dbs": "by_distributor" in json.loads(ISZE_JSON.read_text(encoding="utf-8")).get("pms", {}),
        }

    return {
        "generated_at": generated,
        "gps_year": yr,
        "warranty_year": 2025,
        "distributors_audited": len(rows),
        "pms_distributors": int(len(pms)) if not pms.empty else 0,
        "issue_count": len(issues),
        "issues": issues,
        "isze_data_json": feed_stale,
        "rows": rows,
    }


def write_md(audit: dict) -> None:
    lines = [
        "# GPS / PMS / BVP integrity audit",
        "",
        f"**Generated:** {audit.get('generated_at')}",
        f"**GPS year:** {audit.get('gps_year')} | **Warranty basis:** CY{audit.get('warranty_year')}",
        "",
        f"Distributors: **{audit.get('distributors_audited')}** | PMS summaries: **{audit.get('pms_distributors')}** | Issues: **{audit.get('issue_count')}**",
        "",
    ]
    if audit.get("issues"):
        lines.append("## Issues")
        lines.append("")
        for i in audit["issues"]:
            lines.append(f"- **{i['db']}** ({i['type']}): {i['detail']}")
        lines.append("")

    lines.extend(
        [
            "## Per distributor (latest GPS year)",
            "",
            "| DB | SPU incl | SPU ex-warr | Warr € | BVP contested | Verdict | PMS oil cap |",
            "|---|--:|--:|--:|--:|---|--:|",
        ]
    )
    for r in audit.get("rows", []):
        lines.append(
            f"| {r['distributor_code']} | {r.get('spend_per_unit_eur', '—')} | "
            f"{r.get('spend_per_unit_ex_warranty_eur', '—')} | "
            f"{r.get('warranty_parts_eur', '—')} | "
            f"{(r.get('contested_bvp_capture') or 0)*100:.1f}% | "
            f"{r.get('bvp_low_capture_verdict') or '—'} | "
            f"{(r.get('oil_filter_capture') or 0)*100:.1f}% |"
        )

    lines.extend(
        [
            "",
            "## Reading guide",
            "",
            "- **Ex-warranty SPU** subtracts CY2025 claim-file warranty parts from total sales (embedded in ERP genuine revenue).",
            "- **Low BVP % + warranty** is usually *not* contradictory — warranty parts bill as genuine; contested capture measures BVP vs genuine on paired PNs.",
            "- **UMI warranty resolved 2026-07-03** from a dedicated claim-file export — see gps_warranty_cy2025.json notes.",
            "- Dashboards without `warranty_parts_eur` in `isze_data.json` are stale relative to GPS v9 / PRISM pipeline.",
            "",
        ]
    )
    AUDIT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    audit = build_audit()
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_JSON.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    if audit.get("rows"):
        pd.DataFrame(audit["rows"]).to_csv(AUDIT_CSV, index=False)
    write_md(audit)
    print(f"Wrote {AUDIT_JSON} ({audit.get('issue_count', 0)} issues)")
    print(f"Wrote {AUDIT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
