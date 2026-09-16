"""Self-contained interactive HTML: PMS gaps + usable BVP pairs per distributor.

Period toggle: last full CY (Jan–Dec) and last full FY (Apr–Mar).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ISZE / "01_data" / "00_derived"
OUT_DIR = ISZE / "09_meetings" / "PMS_BVP_Regain_2026"
CACHE = OUT_DIR / "_cache"
CHART_JS = ISZE / "02_dashboards" / "_ui" / "chart.umd.min.js"
PRISM = ISZE / "03_analytics" / "Isuzu" / "prism"

# As of 2026-08: last full CY = 2025; last full FY = FY2025 (Apr 2025–Mar 2026).
CY_YEAR = 2025
FY_YEAR = 2025

CORE = {
    "oil_filter",
    "fuel_filter",
    "air_filter",
    "urea_filter",
    "blower_filter",
    "brake_pad",
    "brake_rotor",
    "brake_shoe",
    "clutch_kit",
    "clutch_disc",
    "clutch_pressure_plate",
    "release_bearing",
    "pilot_bearing",
    "clutch_booster",
}

DB_LABEL = {
    "BELGIUM": "IBX (Belgium)",
    "ITUK": "ITUK",
    "IUK": "IUK",
    "UTI": "UTI",
    "UMI": "UMI",
    "PORTUGAL": "Portugal",
    "GERMANY": "Germany (ISD)",
    "GREECE": "Greece",
    "IRELAND": "Ireland",
    "NORWAY": "Norway",
    "SWEDEN": "Sweden",
    "DENMARK": "Denmark",
    "FINLAND": "Finland",
    "HUNGARY": "Hungary",
    "ROMANIA": "Romania",
    "CYPRUS": "Cyprus",
    "MALTA": "Malta",
    "ICELAND": "Iceland",
}


def cat_label(c: str) -> str:
    return c.replace("_", " ").title()


def eur(v: float) -> str:
    if abs(v) >= 1_000_000:
        return f"€{v/1_000_000:.2f}M"
    if abs(v) >= 1000:
        return f"€{v/1000:.0f}k"
    return f"€{v:.0f}"


def load_strict_pairs() -> tuple[pd.DataFrame, dict[tuple[str, str], dict]]:
    """Strict unsold pairs + network attach map for each (genuine, bvp).

    Network attach = among distributors that sell the genuine (addressable row),
    share that already invoice this BVP.
    """
    addr = pd.read_csv(
        DER / "bvp_addressable_basket.csv", dtype={"genuine_pn": str, "bvp_pn": str}
    )
    # bool may arrive as string
    sell = addr["currently_selling_bvp"]
    if sell.dtype == object:
        addr["currently_selling_bvp"] = sell.astype(str).str.lower().isin(
            ["true", "1", "yes"]
        )
    xref = pd.read_csv(
        DER / "genuine_bvp_crossref.csv", dtype={"genuine_pn": str, "bvp_pn": str}
    )
    xref_u = xref[
        ["genuine_pn", "bvp_pn", "pair_source", "vehicle_model", "engine_type"]
    ].drop_duplicates(["genuine_pn", "bvp_pn"])

    # Network attach on full addressable basket (before unsold filter)
    net_map: dict[tuple[str, str], dict] = {}
    for (g, b), gdf in addr.groupby(["genuine_pn", "bvp_pn"]):
        n = int(gdf["distributor_code"].nunique())
        k = int(gdf.loc[gdf["currently_selling_bvp"], "distributor_code"].nunique())
        net_map[(str(g), str(b))] = {
            "network_bvp_pct": round(k / n, 4) if n else 0.0,
            "network_bvp_selling": k,
            "network_bvp_addressable": n,
        }

    unsold = addr[~addr["currently_selling_bvp"]].copy()
    unsold = unsold.merge(xref_u, on=["genuine_pn", "bvp_pn"], how="left", suffixes=("", "_x"))
    unsold["vm"] = unsold["vehicle_model"].fillna(unsold.get("vehicle_model_x"))
    unsold["eng"] = unsold["engine_type"].fillna(unsold.get("engine_type_x"))
    unsold["strict"] = (unsold["pair_source"] == "catalog_paired") & unsold["vm"].notna() & (
        unsold["vm"].astype(str).str.strip() != ""
    )
    strict = unsold[unsold["strict"] & unsold["product_subgroup"].isin(CORE)].copy()
    return strict, net_map


def customers_from_frames(
    opp: pd.DataFrame,
    spu_tot: pd.DataFrame,
    mix_agg: pd.DataFrame,
    strict: pd.DataFrame,
    net_map: dict[tuple[str, str], dict],
    *,
    year: int,
    period_key: str,
    period_label: str,
    period_note: str,
) -> dict:
    opp = opp[(opp["year"] == year) & (opp["pms_category"].isin(CORE))].copy()
    df = opp.merge(spu_tot, on=["distributor_code", "pms_category"], how="left")
    df = df.merge(mix_agg, on=["distributor_code", "pms_category"], how="left")

    med_cap = df.groupby("pms_category")["capture_rate_total"].median()
    med_spu = df.groupby("pms_category")["spu_total"].median()
    med_bvp = df.groupby("pms_category")["bvp_share"].median()
    df["med_cap"] = df["pms_category"].map(med_cap)
    df["med_spu"] = df["pms_category"].map(med_spu)
    df["med_bvp"] = df["pms_category"].map(med_bvp)
    df["cap_vs"] = df["capture_rate_total"] / df["med_cap"]
    df["spu_vs"] = df["spu_total"] / df["med_spu"]
    df["weak"] = (
        ((df["cap_vs"] < 0.75) | (df["spu_vs"] < 0.75))
        & ((df["revenue_gap_eur"] >= 5000) | (df.get("total_eur", 0).fillna(0) >= 3000))
    )

    customers = []
    for db, gweak in df[df["weak"]].groupby("distributor_code"):
        pairs = strict[strict["distributor_code"] == db]
        if pairs.empty:
            continue
        cats = []
        total_gap = 0.0
        all_pairs = []
        for _, r in gweak.sort_values("revenue_gap_eur", ascending=False).iterrows():
            cat = r["pms_category"]
            cp = pairs[pairs["product_subgroup"] == cat]
            if cp.empty:
                continue
            gap = float(r["revenue_gap_eur"] or 0)
            total_gap += gap
            for _, p in cp.drop_duplicates(["genuine_pn", "bvp_pn"]).iterrows():
                gpn, bpn = str(p["genuine_pn"]), str(p["bvp_pn"])
                net = net_map.get((gpn, bpn), {})
                row = {
                    "category": cat,
                    "category_label": cat_label(cat),
                    "genuine": gpn,
                    "bvp": bpn,
                    "models": str(p["vm"]) if pd.notna(p["vm"]) else "",
                    "engine": str(p["eng"]) if pd.notna(p["eng"]) else "",
                    "network_bvp_pct": net.get("network_bvp_pct", 0.0),
                    "network_bvp_selling": net.get("network_bvp_selling", 0),
                    "network_bvp_addressable": net.get("network_bvp_addressable", 0),
                }
                all_pairs.append(row)
            cats.append(
                {
                    "category": cat,
                    "category_label": cat_label(cat),
                    "gap_eur": round(gap, 2),
                    "capture": (
                        round(float(r["capture_rate_total"]), 4)
                        if pd.notna(r["capture_rate_total"])
                        else None
                    ),
                    "cap_vs_med": (
                        round(float(r["cap_vs"]), 4) if pd.notna(r["cap_vs"]) else None
                    ),
                    "spu": round(float(r["spu_total"]), 4) if pd.notna(r["spu_total"]) else None,
                    "spu_vs_med": (
                        round(float(r["spu_vs"]), 4) if pd.notna(r["spu_vs"]) else None
                    ),
                    "med_cap": (
                        round(float(r["med_cap"]), 4) if pd.notna(r["med_cap"]) else None
                    ),
                    "bvp_share": (
                        round(float(r["bvp_share"]), 4) if pd.notna(r["bvp_share"]) else 0.0
                    ),
                    "med_bvp": (
                        round(float(r["med_bvp"]), 4) if pd.notna(r["med_bvp"]) else None
                    ),
                    "n_pairs": int(cp["bvp_pn"].nunique()),
                }
            )
        if not cats:
            continue
        customers.append(
            {
                "db": db,
                "label": DB_LABEL.get(db, db),
                "total_gap": round(total_gap, 2),
                "n_categories": len(cats),
                "n_pairs": int(sum(c["n_pairs"] for c in cats)),
                "categories": cats,
                "pairs": all_pairs,
            }
        )

    customers.sort(key=lambda c: -c["total_gap"])
    return {
        "key": period_key,
        "label": period_label,
        "note": period_note,
        "year": year,
        "customers": customers,
        "network_gap": round(sum(c["total_gap"] for c in customers), 2),
        "n_customers": len(customers),
        "n_pairs": int(sum(c["n_pairs"] for c in customers)),
        "rule": (
            "Weak = capture or €/vehicle below 75% of network median, with material gap. "
            "Pairs = catalog-paired BVP with model fitment, for genuine PNs already sold, "
            "BVP not yet on invoices."
        ),
    }


def build_cy_period(strict: pd.DataFrame, net_map: dict) -> dict:
    opp = pd.read_csv(DER / "pms_opportunity_matrix.csv")
    spu = pd.read_csv(DER / "gps_spu_pms.csv")
    spu_tot = spu[
        (spu["year"] == CY_YEAR)
        & (spu["line_type"] == "all")
        & (spu["pms_category"].isin(CORE))
    ][["distributor_code", "pms_category", "spu_eur"]].rename(
        columns={"spu_eur": "spu_total"}
    )

    mix = pd.read_csv(DER / "mix_genuine_bvp_pms.csv")
    mix = mix[mix["year"] == CY_YEAR].copy()
    mix["pms_category"] = mix["product_subgroup"]
    mix = mix[mix["pms_category"].isin(CORE)]
    mix_agg = mix.groupby(["distributor_code", "pms_category"], as_index=False).agg(
        bvp_eur=("bvp_eur", "sum"),
        genuine_eur=("genuine_eur", "sum"),
        total_eur=("total_eur", "sum"),
    )
    mix_agg["bvp_share"] = mix_agg["bvp_eur"] / mix_agg["total_eur"].replace(0, pd.NA)

    return customers_from_frames(
        opp,
        spu_tot,
        mix_agg,
        strict,
        net_map,
        year=CY_YEAR,
        period_key="cy",
        period_label=f"CY{CY_YEAR} (Jan–Dec)",
        period_note=f"Last full calendar year · CY{CY_YEAR}",
    )


def build_fy_frames(fy: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Build opportunity + spu + mix for one fiscal year (Apr–Mar). Cached under _cache/."""
    CACHE.mkdir(parents=True, exist_ok=True)
    opp_p = CACHE / f"fy{fy}_opportunity.csv"
    spu_p = CACHE / f"fy{fy}_spu.csv"
    mix_p = CACHE / f"fy{fy}_mix.csv"
    if opp_p.exists() and spu_p.exists() and mix_p.exists():
        print(f"  FY{fy}: using cache {_cache_rel()}")
        return pd.read_csv(opp_p), pd.read_csv(spu_p), pd.read_csv(mix_p)

    if str(PRISM) not in sys.path:
        sys.path.insert(0, str(PRISM))

    from config import (  # noqa: E402
        resolve_mapping_path,
        resolve_uio_path,
    )
    from modules.data_prep import (  # noqa: E402
        load_distributor_mapping,
        load_uio_from_excel,
    )
    from modules.sales_loader import load_prism_sales  # noqa: E402
    from scripts.build_bvp_p0_p1 import (  # noqa: E402
        build_p1_capture,
        enrich_pms_from_dimension,
    )
    from scripts.build_pms_opportunity_matrix import (  # noqa: E402
        build_pms_opportunity_matrix,
    )

    print(f"  FY{fy}: loading sales …", flush=True)
    df_map = load_distributor_mapping(str(resolve_mapping_path()))
    df_sales, src = load_prism_sales(df_map)
    print(f"  FY{fy}: {len(df_sales):,} rows from {src}", flush=True)

    df_fy = df_sales[df_sales["fiscal_year"] == fy].copy()
    if df_fy.empty:
        raise RuntimeError(f"No sales rows for FY{fy}")
    # Re-label so P1 year loop + UIO lookup use the FY label year
    df_fy["year"] = fy
    months = sorted(df_fy["month"].dropna().unique().astype(int).tolist())
    if len(months) < 12:
        print(f"  WARNING FY{fy}: only months {months} present — incomplete FY", flush=True)

    df_dim = pd.read_parquet(DER / "bvp_pn_dimension.parquet")
    supp_path = PRISM / "data" / "pms_capture_supplement.csv"
    if supp_path.exists():
        df_supp = pd.read_csv(supp_path, dtype={"part_number": str})
        df_dim = pd.concat([df_dim, df_supp], ignore_index=True)

    df_uio = load_uio_from_excel(str(resolve_uio_path()))
    print(f"  FY{fy}: building P1 capture …", flush=True)
    df_p1 = build_p1_capture(df_fy, df_uio, df_dim)
    p1_path = CACHE / f"fy{fy}_p1_capture.csv"
    df_p1.to_csv(p1_path, index=False)

    # Temporary GPS stub for opportunity merge (country/region)
    gps = pd.read_csv(DER / "gps_spu_by_distributor.csv")
    gps_y = gps[gps["year"] == fy][
        ["year", "distributor_code", "country", "region"]
    ].drop_duplicates()
    if gps_y.empty:
        gps_y = gps[gps["year"] == CY_YEAR][
            ["year", "distributor_code", "country", "region"]
        ].drop_duplicates()
        gps_y = gps_y.assign(year=fy)

    # build_pms_opportunity_matrix reads files — write temp and call, or inline
    pms_tmp = CACHE / f"fy{fy}_pms_capture.csv"
    gps_tmp = CACHE / f"fy{fy}_gps_stub.csv"
    df_p1.to_csv(pms_tmp, index=False)
    gps_y.to_csv(gps_tmp, index=False)
    opp = build_pms_opportunity_matrix(pms_path=pms_tmp, gps_path=gps_tmp)
    opp.to_csv(opp_p, index=False)

    # Category €/UIO for FY
    tot = df_p1[(df_p1["line_type"] == "total") & (df_p1["pms_category"].isin(CORE))].copy()
    tot["spu_total"] = tot["actual_rev_eur"] / tot["uio_units"].replace(0, pd.NA)
    spu_tot = tot[["distributor_code", "pms_category", "spu_total"]].copy()
    spu_tot.to_csv(spu_p, index=False)

    # Mix from tagged FY sales
    print(f"  FY{fy}: building BVP mix …", flush=True)
    tagged = enrich_pms_from_dimension(df_fy, df_dim)
    tagged = tagged[tagged["is_pms"]].copy()
    if "is_credit_note" in tagged.columns:
        tagged = tagged[~tagged["is_credit_note"]]
    if "pms_capture_eligible" in tagged.columns:
        tagged = tagged[tagged["pms_capture_eligible"]]
    tagged = tagged[tagged["pms_category"].isin(CORE)]
    tagged["pms_type"] = tagged["pms_type"].fillna("genuine")

    rows = []
    for (db, cat), g in tagged.groupby(["distributor_code", "pms_category"]):
        bvp_eur = float(g.loc[g["pms_type"] == "bvp", "net_sales_value"].sum())
        gen_eur = float(g.loc[g["pms_type"] == "genuine", "net_sales_value"].sum())
        total = bvp_eur + gen_eur
        rows.append(
            {
                "distributor_code": db,
                "pms_category": cat,
                "bvp_eur": bvp_eur,
                "genuine_eur": gen_eur,
                "total_eur": total,
                "bvp_share": (bvp_eur / total) if total else 0.0,
            }
        )
    mix_agg = pd.DataFrame(rows)
    mix_agg.to_csv(mix_p, index=False)
    print(f"  FY{fy}: cached opportunity/spu/mix", flush=True)
    return opp, spu_tot, mix_agg


def _cache_rel() -> str:
    return str(CACHE)


def build_fy_period(strict: pd.DataFrame, net_map: dict) -> dict:
    opp, spu_tot, mix_agg = build_fy_frames(FY_YEAR)
    return customers_from_frames(
        opp,
        spu_tot,
        mix_agg,
        strict,
        net_map,
        year=FY_YEAR,
        period_key="fy",
        period_label=f"FY{FY_YEAR} (Apr {FY_YEAR}–Mar {FY_YEAR + 1})",
        period_note=f"Last full fiscal year · FY{FY_YEAR} = Apr {FY_YEAR} – Mar {FY_YEAR + 1}",
    )


def write_html(payload: dict) -> Path:
    chart_js = CHART_JS.read_text(encoding="utf-8")
    chart_js = re.sub(r"//# sourceMappingURL=.*", "", chart_js)
    data_json = json.dumps(payload, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>PMS gaps · BVP regain</title>
<style>
:root {{
  --navy:#1a2b4a; --navy2:#15233c; --accent:#c0552d; --blue:#2a78d6;
  --green:#1d9e75; --paper:#f7f4ee; --line:#d9d3c8; --muted:#6b6256; --ink:#1c1b19;
  --bg:#eef0f3; --card:#fff;
}}
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0;background:var(--bg);color:var(--ink);
  font-family:"Segoe UI",Helvetica,Arial,sans-serif;font-size:14px;line-height:1.45}}
h1,h2,h3{{font-family:Georgia,"Times New Roman",serif;color:var(--navy);margin:0}}
button,select,input{{font:inherit}}
.top{{
  position:sticky;top:0;z-index:40;
  background:linear-gradient(135deg,var(--navy2),#203759 55%,#2b4a78);
  color:#eef1f6;padding:14px 20px 16px;
  box-shadow:0 8px 24px rgba(21,35,60,.28);
}}
.top-row{{display:flex;flex-wrap:wrap;gap:14px 22px;align-items:flex-end;justify-content:space-between}}
.top h1{{color:#fff;font-size:22px;line-height:1.15;max-width:520px}}
.top .sub{{opacity:.82;font-size:12.5px;margin-top:4px;max-width:560px}}
.kpis{{display:flex;gap:10px;flex-wrap:wrap}}
.kpi{{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.12);
  padding:8px 14px;min-width:110px;border-radius:6px}}
.kpi b{{display:block;font-family:Georgia,serif;font-size:20px;color:#fff}}
.kpi span{{font-size:10px;letter-spacing:.04em;text-transform:uppercase;opacity:.8}}
.controls{{display:flex;gap:10px;flex-wrap:wrap;align-items:end;margin-top:14px}}
.controls label{{display:flex;flex-direction:column;gap:4px;font-size:11px;
  text-transform:uppercase;letter-spacing:.05em;opacity:.85}}
.controls select,.controls input{{
  background:#fff;color:var(--ink);border:0;border-radius:6px;
  padding:9px 12px;min-width:200px;outline:none;
}}
.controls input{{min-width:180px}}
.period-seg{{display:flex;background:rgba(255,255,255,.12);border-radius:8px;padding:3px;gap:2px}}
.period-seg button{{
  border:0;background:transparent;color:#eef1f6;padding:8px 14px;border-radius:6px;
  cursor:pointer;font-size:12.5px;font-weight:600;opacity:.85;
}}
.period-seg button.on{{background:#fff;color:var(--navy);opacity:1}}
.shell{{max-width:1280px;margin:0 auto;padding:16px 18px 40px;display:grid;
  grid-template-columns:340px 1fr;gap:14px}}
@media (max-width:980px){{.shell{{grid-template-columns:1fr}}}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px}}
.card h2{{font-size:15px;margin-bottom:8px;display:flex;align-items:baseline;gap:8px}}
.card h2 .no{{color:var(--accent)}}
.hint{{color:var(--muted);font-size:12px;margin:0 0 10px}}
.rank-list{{display:flex;flex-direction:column;gap:7px;max-height:calc(100vh - 240px);overflow:auto;padding-right:4px}}
.rank-row{{
  display:grid;grid-template-columns:28px 1fr 64px;gap:8px;align-items:center;
  padding:8px 10px;border-radius:8px;border:1px solid transparent;cursor:pointer;
  background:var(--paper);transition:border-color .15s, background .15s;
}}
.rank-row:hover{{border-color:#c9c2b4}}
.rank-row.active{{border-color:var(--accent);background:#fff4ee}}
.rank-row .ix{{font-size:11px;color:var(--muted);font-weight:600}}
.rank-row .nm{{font-weight:600;font-size:13px;color:var(--navy)}}
.rank-row .gv{{font-weight:700;text-align:right;font-variant-numeric:tabular-nums;color:var(--accent)}}
.bar-track{{grid-column:2 / 4;height:7px;background:#e6e2d8;border-radius:99px;overflow:hidden;margin-top:-2px}}
.bar-fill{{height:100%;border-radius:99px;background:var(--blue)}}
.rank-row.active .bar-fill,.rank-row:nth-child(-n+3) .bar-fill{{background:var(--accent)}}
.detail-head{{display:flex;flex-wrap:wrap;gap:12px;justify-content:space-between;align-items:flex-start;margin-bottom:10px}}
.detail-head h2{{font-size:22px}}
.pill{{display:inline-flex;align-items:center;gap:6px;background:var(--paper);
  border:1px solid var(--line);border-radius:999px;padding:4px 10px;font-size:12px;color:var(--muted)}}
.metric-row{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:10px 0 14px}}
@media (max-width:720px){{.metric-row{{grid-template-columns:repeat(2,1fr)}}}}
.metric{{background:var(--paper);border-radius:8px;padding:10px 12px;border:1px solid var(--line)}}
.metric b{{display:block;font-family:Georgia,serif;font-size:20px;color:var(--navy)}}
.metric span{{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}}
.charts{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px}}
.charts-wide{{display:grid;grid-template-columns:1fr;gap:12px;margin-bottom:12px}}
@media (max-width:900px){{.charts{{grid-template-columns:1fr}}}}
.chart-box{{position:relative;height:280px}}
.chart-box.tall{{height:300px}}
.chart-box.mix{{height:260px}}
table{{width:100%;border-collapse:collapse;font-size:12.5px}}
th{{background:var(--navy);color:#fff;text-align:left;padding:8px 9px;font-size:11px;
  text-transform:uppercase;letter-spacing:.03em;position:sticky;top:0}}
td{{padding:7px 9px;border-bottom:1px solid var(--line);vertical-align:top}}
tbody tr:nth-child(even){{background:var(--paper)}}
.pn{{font-family:Consolas,"Courier New",monospace;font-size:12px;letter-spacing:.02em}}
.tag{{display:inline-block;background:#e8f1fb;color:#1a4f8a;border-radius:4px;padding:1px 6px;font-size:11px}}
.tag.warn{{background:#fde8d8;color:#8a3b12}}
.table-wrap{{max-height:420px;overflow:auto;border:1px solid var(--line);border-radius:8px}}
.foot{{max-width:1280px;margin:0 auto;padding:0 18px 28px;font-size:11px;color:var(--muted)}}
.empty{{padding:28px;text-align:center;color:var(--muted)}}
.cat-btn{{
  border:1px solid var(--line);background:#fff;border-radius:999px;padding:5px 10px;
  font-size:12px;cursor:pointer;color:var(--navy);
}}
.cat-btn.on{{background:var(--navy);color:#fff;border-color:var(--navy)}}
.cat-filters{{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 10px}}
</style>
</head>
<body>
<header class="top">
  <div class="top-row">
    <div>
      <h1>Where capture is low — and a BVP already exists</h1>
      <div class="sub">Pick period + distributor. Biggest PMS gaps, then exact genuine → BVP pairs (same model / engine). Catalog-paired only.</div>
    </div>
    <div class="kpis" id="netKpis"></div>
  </div>
  <div class="controls">
    <label>Period
      <div class="period-seg" id="periodSeg" role="group" aria-label="Period">
        <button type="button" data-period="cy" class="on">Last full CY</button>
        <button type="button" data-period="fy">Last full FY</button>
      </div>
    </label>
    <label>Distributor
      <select id="dbSelect"></select>
    </label>
    <label>Filter pairs
      <input id="q" type="search" placeholder="PN, model, category…" autocomplete="off"/>
    </label>
  </div>
</header>

<main class="shell">
  <aside class="card">
    <h2><span class="no">01</span> Network ranking</h2>
    <p class="hint" id="periodHint">Gap € in weak categories with an unsold catalog-paired BVP.</p>
    <div class="rank-list" id="rankList"></div>
  </aside>
  <section class="card" id="detail">
    <div class="empty">Select a distributor</div>
  </section>
</main>
<p class="foot" id="foot"></p>

<script type="application/json" id="payload">{data_json}</script>
<script>{chart_js}</script>
<script>
(function(){{
  const ROOT = JSON.parse(document.getElementById('payload').textContent);
  let periodKey = ROOT.default_period || 'cy';
  let DATA = ROOT.periods[periodKey];
  let customers = DATA.customers;
  let byDb = Object.fromEntries(customers.map(c => [c.db, c]));
  let activeDb = customers[0] ? customers[0].db : null;
  let catFilter = null;
  let catChart = null;
  let capChart = null;
  let mixChart = null;

  const eur = (v) => {{
    if (v == null || isNaN(v)) return '—';
    const a = Math.abs(v);
    if (a >= 1e6) return '€' + (v/1e6).toFixed(2) + 'M';
    if (a >= 1e3) return '€' + Math.round(v/1e3) + 'k';
    return '€' + Math.round(v);
  }};
  const pct = (v) => (v == null || isNaN(v)) ? '—' : Math.round(100*v) + '%';

  const sel = document.getElementById('dbSelect');
  const periodSeg = document.getElementById('periodSeg');

  function paintNet() {{
    document.getElementById('netKpis').innerHTML = `
      <div class="kpi"><b>${{eur(DATA.network_gap)}}</b><span>Network gap</span></div>
      <div class="kpi"><b>${{DATA.n_customers}}</b><span>Distributors</span></div>
      <div class="kpi"><b>${{DATA.n_pairs}}</b><span>Usable BVP PNs</span></div>`;
    document.getElementById('periodHint').textContent =
      DATA.label + ' · Gap € in weak categories with an unsold catalog-paired BVP. Click a row.';
    document.getElementById('foot').textContent =
      DATA.note + ' · Total capture · ' + DATA.rule +
      ' UTI and UMI shown separately. Indicative — not a forecast.';
    periodSeg.querySelectorAll('button').forEach(b => {{
      b.classList.toggle('on', b.dataset.period === periodKey);
      const p = ROOT.periods[b.dataset.period];
      if (p) b.title = p.label;
    }});
  }}

  function fillSelect() {{
    const prev = activeDb;
    sel.innerHTML = '';
    customers.forEach(c => {{
      const o = document.createElement('option');
      o.value = c.db; o.textContent = c.label + ' · ' + eur(c.total_gap);
      sel.appendChild(o);
    }});
    if (prev && byDb[prev]) activeDb = prev;
    else activeDb = customers[0] ? customers[0].db : null;
    if (activeDb) sel.value = activeDb;
  }}

  function paintRank() {{
    const maxGap = Math.max(...customers.map(c => c.total_gap), 1);
    const rankList = document.getElementById('rankList');
    rankList.innerHTML = customers.map((c,i) => {{
      const w = Math.max(2, Math.round(100 * c.total_gap / maxGap));
      const on = c.db === activeDb ? ' active' : '';
      return `<div class="rank-row${{on}}" data-db="${{c.db}}">
        <div class="ix">${{String(i+1).padStart(2,'0')}}</div>
        <div>
          <div class="nm">${{c.label}}</div>
          <div class="bar-track"><div class="bar-fill" style="width:${{w}}%"></div></div>
        </div>
        <div class="gv">${{eur(c.total_gap)}}</div>
      </div>`;
    }}).join('');
    rankList.querySelectorAll('.rank-row').forEach(el => {{
      el.addEventListener('click', () => setDb(el.dataset.db));
    }});
  }}

  function destroyCharts() {{
    if (catChart) {{ catChart.destroy(); catChart = null; }}
    if (capChart) {{ capChart.destroy(); capChart = null; }}
    if (mixChart) {{ mixChart.destroy(); mixChart = null; }}
  }}

  const valueLabels = {{
    id: 'valueLabels',
    afterDatasetsDraw(chart) {{
      const {{ctx, data}} = chart;
      const x = chart.scales.x;
      const meta = chart.getDatasetMeta(0);
      ctx.save();
      ctx.fillStyle = '#1a2b4a';
      ctx.font = '600 11px Segoe UI, sans-serif';
      ctx.textBaseline = 'middle';
      meta.data.forEach((bar, i) => {{
        const v = data.datasets[0].data[i];
        if (v == null) return;
        const label = chart.config._labelFn ? chart.config._labelFn(v) : String(v);
        const px = Math.min(bar.x + 6, x.right - 4);
        ctx.textAlign = 'left';
        ctx.fillText(label, px, bar.y);
      }});
      ctx.restore();
    }}
  }};

  function renderDetail() {{
    const c = byDb[activeDb];
    const root = document.getElementById('detail');
    if (!c) {{ root.innerHTML = '<div class="empty">No data for this period</div>'; return; }}
    destroyCharts();
    catFilter = null;
    const cats = c.categories;
    root.innerHTML = `
      <div class="detail-head">
        <div>
          <h2>${{c.label}}</h2>
          <div class="pill" style="margin-top:6px">${{DATA.label}} · ${{c.n_categories}} weak categories · ${{c.n_pairs}} unsold paired BVP PNs</div>
        </div>
      </div>
      <div class="metric-row">
        <div class="metric"><b>${{eur(c.total_gap)}}</b><span>Capture gap with BVP lever</span></div>
        <div class="metric"><b>${{eur(cats[0] ? cats[0].gap_eur : 0)}}</b><span>Largest category gap</span></div>
        <div class="metric"><b>${{cats[0] ? cats[0].category_label : '—'}}</b><span>Top priority category</span></div>
        <div class="metric"><b>${{pct(cats[0] ? cats[0].bvp_share : 0)}}</b><span>Current BVP € mix (top cat)</span></div>
      </div>
      <div class="charts">
        <div>
          <h2 style="font-size:14px;margin-bottom:6px"><span class="no">A</span> Gap by category</h2>
          <p class="hint">Click a bar (or chip below) to filter the pair list.</p>
          <div class="chart-box tall"><canvas id="catChart"></canvas></div>
        </div>
        <div>
          <h2 style="font-size:14px;margin-bottom:6px"><span class="no">B</span> Capture vs network</h2>
          <p class="hint">Their capture % vs network median for the same category.</p>
          <div class="chart-box tall"><canvas id="capChart"></canvas></div>
        </div>
      </div>
      <div class="charts-wide">
        <div>
          <h2 style="font-size:14px;margin-bottom:6px"><span class="no">C</span> BVP € mix by category</h2>
          <p class="hint">Share of this distributor’s category € already on BVP vs network median. High mix + still a gap = volume/attach problem, not “no BVP.”</p>
          <div class="chart-box mix"><canvas id="mixChart"></canvas></div>
        </div>
      </div>
      <h2 style="font-size:14px;margin:4px 0 8px"><span class="no">D</span> Catalog pairs to push</h2>
      <div class="cat-filters" id="catFilters"></div>
      <div class="table-wrap">
        <table>
          <thead><tr>
            <th>Category</th><th>Genuine PN</th><th>BVP PN</th><th>Models</th><th>Engine</th>
            <th title="Among distributors who sell this genuine, % that already invoice this BVP">Network on BVP</th>
            <th>Note</th>
          </tr></thead>
          <tbody id="pairBody"></tbody>
        </table>
      </div>`;

    const filters = document.getElementById('catFilters');
    filters.innerHTML = `<button type="button" class="cat-btn on" data-cat="">All</button>` +
      cats.map(x => `<button type="button" class="cat-btn" data-cat="${{x.category}}">${{x.category_label}} (${{x.n_pairs}})</button>`).join('');
    filters.querySelectorAll('.cat-btn').forEach(btn => {{
      btn.addEventListener('click', () => {{
        catFilter = btn.dataset.cat || null;
        filters.querySelectorAll('.cat-btn').forEach(b => b.classList.toggle('on', b === btn));
        paintPairs();
      }});
    }});

    const labels = cats.map(x => x.category_label);
    const gaps = cats.map(x => Math.round(x.gap_eur / 1000));
    const maxG = Math.max(...gaps, 1);
    catChart = new Chart(document.getElementById('catChart'), {{
      type: 'bar',
      data: {{
        labels,
        datasets: [{{
          data: gaps,
          backgroundColor: cats.map((_,i) => i < 3 ? '#c0552d' : '#2a78d6'),
          borderRadius: 5,
          barThickness: 22
        }}]
      }},
      options: {{
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        layout: {{ padding: {{ right: 52 }} }},
        onClick: (e, els) => {{
          if (!els.length) return;
          const cat = cats[els[0].index].category;
          catFilter = cat;
          filters.querySelectorAll('.cat-btn').forEach(b => b.classList.toggle('on', b.dataset.cat === cat));
          paintPairs();
        }},
        plugins: {{
          legend: {{ display: false }},
          tooltip: {{ callbacks: {{ label: (ctx) => ' Gap ' + eur(ctx.raw * 1000) }} }}
        }},
        scales: {{
          x: {{
            min: 0,
            max: Math.ceil(maxG * 1.18 / 10) * 10 || 10,
            title: {{ display: true, text: 'Gap (€ thousands)', color: '#6b6256', font: {{ size: 11 }} }},
            grid: {{ color: '#e8e4da' }},
            ticks: {{ color: '#6b6256', font: {{ size: 11 }} }}
          }},
          y: {{ grid: {{ display: false }}, ticks: {{ color: '#1a2b4a', font: {{ size: 12, weight: '600' }} }} }}
        }}
      }},
      plugins: [valueLabels]
    }});
    catChart.config._labelFn = (v) => (v >= 1000 ? (v/1000).toFixed(1)+'M' : v + 'k');

    const their = cats.map(x => x.capture == null ? 0 : +(100 * x.capture).toFixed(1));
    const med = cats.map(x => x.med_cap == null ? 0 : +(100 * x.med_cap).toFixed(1));
    capChart = new Chart(document.getElementById('capChart'), {{
      type: 'bar',
      data: {{
        labels,
        datasets: [
          {{ label: 'This distributor', data: their, backgroundColor: '#c0552d', borderRadius: 4, barThickness: 14 }},
          {{ label: 'Network median', data: med, backgroundColor: '#85b7eb', borderRadius: 4, barThickness: 14 }}
        ]
      }},
      options: {{
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
          legend: {{ position: 'bottom', labels: {{ boxWidth: 12, font: {{ size: 11 }} }} }},
          tooltip: {{ callbacks: {{ label: (ctx) => ctx.dataset.label + ': ' + ctx.raw + '%' }} }}
        }},
        scales: {{
          x: {{
            min: 0, max: 100,
            title: {{ display: true, text: 'Capture %', color: '#6b6256', font: {{ size: 11 }} }},
            grid: {{ color: '#e8e4da' }},
            ticks: {{ color: '#6b6256', callback: (v) => v + '%' }}
          }},
          y: {{ grid: {{ display: false }}, ticks: {{ color: '#1a2b4a', font: {{ size: 12, weight: '600' }} }} }}
        }}
      }}
    }});

    const theirMix = cats.map(x => +(100 * (x.bvp_share || 0)).toFixed(1));
    const medMix = cats.map(x => x.med_bvp == null ? 0 : +(100 * x.med_bvp).toFixed(1));
    mixChart = new Chart(document.getElementById('mixChart'), {{
      type: 'bar',
      data: {{
        labels,
        datasets: [
          {{ label: 'This distributor BVP € mix', data: theirMix, backgroundColor: '#1d9e75', borderRadius: 4, barThickness: 16 }},
          {{ label: 'Network median', data: medMix, backgroundColor: '#888780', borderRadius: 4, barThickness: 16 }}
        ]
      }},
      options: {{
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
          legend: {{ position: 'bottom', labels: {{ boxWidth: 12, font: {{ size: 11 }} }} }},
          tooltip: {{ callbacks: {{ label: (ctx) => ctx.dataset.label + ': ' + ctx.raw + '%' }} }}
        }},
        scales: {{
          x: {{
            min: 0, max: 100,
            title: {{ display: true, text: 'BVP share of category €', color: '#6b6256', font: {{ size: 11 }} }},
            grid: {{ color: '#e8e4da' }},
            ticks: {{ color: '#6b6256', callback: (v) => v + '%' }}
          }},
          y: {{ grid: {{ display: false }}, ticks: {{ color: '#1a2b4a', font: {{ size: 12, weight: '600' }} }} }}
        }}
      }}
    }});
    paintPairs();
  }}

  function paintPairs() {{
    const c = byDb[activeDb];
    if (!c) return;
    const q = (document.getElementById('q').value || '').trim().toLowerCase();
    const body = document.getElementById('pairBody');
    const catMap = Object.fromEntries(c.categories.map(x => [x.category, x]));
    let rows = c.pairs.slice();
    if (catFilter) rows = rows.filter(r => r.category === catFilter);
    if (q) {{
      rows = rows.filter(r =>
        (r.genuine + ' ' + r.bvp + ' ' + r.models + ' ' + r.engine + ' ' + r.category_label)
          .toLowerCase().includes(q));
    }}
    if (!rows.length) {{
      body.innerHTML = '<tr><td colspan="7" class="empty">No pairs for this filter</td></tr>';
      return;
    }}
    body.innerHTML = rows.map(r => {{
      const share = catMap[r.category] ? catMap[r.category].bvp_share : 0;
      const note = share >= 0.5
        ? '<span class="tag warn">Already high BVP mix — gap is volume</span>'
        : '<span class="tag">Introduce BVP</span>';
      const netPct = Math.round(100 * (r.network_bvp_pct || 0));
      const netN = (r.network_bvp_selling || 0) + '/' + (r.network_bvp_addressable || 0);
      const netCls = netPct >= 50 ? 'tag' : 'tag warn';
      return `<tr>
        <td>${{r.category_label}}</td>
        <td class="pn">${{r.genuine}}</td>
        <td class="pn"><strong>${{r.bvp}}</strong></td>
        <td>${{r.models || '—'}}</td>
        <td>${{r.engine || '—'}}</td>
        <td title="${{netN}} distributors already sell this BVP">
          <span class="${{netCls}}">${{netPct}}%</span>
          <span style="color:#6b6256;font-size:11px;margin-left:4px">${{netN}}</span>
        </td>
        <td>${{note}}</td>
      </tr>`;
    }}).join('');
  }}

  function setDb(db) {{
    activeDb = db;
    if (db) sel.value = db;
    paintRank();
    renderDetail();
  }}

  function setPeriod(key) {{
    if (!ROOT.periods[key]) return;
    periodKey = key;
    DATA = ROOT.periods[periodKey];
    customers = DATA.customers;
    byDb = Object.fromEntries(customers.map(c => [c.db, c]));
    paintNet();
    fillSelect();
    setDb(activeDb && byDb[activeDb] ? activeDb : (customers[0] && customers[0].db));
  }}

  periodSeg.querySelectorAll('button').forEach(btn => {{
    btn.addEventListener('click', () => setPeriod(btn.dataset.period));
  }});
  sel.addEventListener('change', () => setDb(sel.value));
  document.getElementById('q').addEventListener('input', paintPairs);

  setPeriod(periodKey);
}})();
</script>
</body>
</html>
"""
    out = OUT_DIR / "PMS_BVP_Regain.html"
    out.write_text(html, encoding="utf-8")
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Strict pairs …", flush=True)
    strict, net_map = load_strict_pairs()
    print("CY period …", flush=True)
    cy = build_cy_period(strict, net_map)
    print(f"  CY gap {cy['network_gap']:.0f} / {cy['n_customers']} DBs / {cy['n_pairs']} pairs")
    print("FY period …", flush=True)
    fy = build_fy_period(strict, net_map)
    print(f"  FY gap {fy['network_gap']:.0f} / {fy['n_customers']} DBs / {fy['n_pairs']} pairs")

    payload = {
        "default_period": "cy",
        "periods": {"cy": cy, "fy": fy},
    }
    (OUT_DIR / "payload.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    out = write_html(payload)
    n_https = len(
        re.findall(r'(?:src|href)\s*=\s*["\']https?://', out.read_text(encoding="utf-8"))
    )
    print(f"HTML {out}")
    print(f"alias {OUT_DIR / 'PMS_BVP_Regain.html'}")
    print(f"size_kb {out.stat().st_size/1024:.0f} external_src_href {n_https}")
    for key in ("cy", "fy"):
        p = payload["periods"][key]
        print(f"== {p['label']} ==")
        for c in p["customers"][:5]:
            print(f"  {c['label']}: {c['total_gap']:.0f} / {c['n_pairs']} pairs")


if __name__ == "__main__":
    main()
