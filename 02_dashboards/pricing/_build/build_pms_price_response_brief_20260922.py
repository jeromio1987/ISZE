"""Build ISZE_PMS_Price_Response_Brief_2026-09-22.html — click path to part number."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
OUT_DIR = ROOT / "02_dashboards" / "pricing"
OUT_HTML = OUT_DIR / "ISZE_PMS_Price_Response_Brief_2026-09-22.html"
OUT_CMD = OUT_DIR / "OPEN_PMS_Price_Response_Brief_2026-09-22.cmd"

FIVE = {1797: "UMI", 1799: "UTI", 2372: "KIMA", 2733: "GA", 2734: "CBC"}


def clean(df: pd.DataFrame) -> list[dict]:
    return json.loads(json.dumps(df.replace({np.nan: None}).to_dict(orient="records"), default=str))


def norm_pn(s: pd.Series) -> pd.Series:
    s = s.astype(str).str.strip().str.upper()
    return s.str.replace(r"\.0$", "", regex=True).str.lstrip("0").replace("", "0")


def bucket_for(fam: str) -> str:
    fl = str(fam).lower()
    if "filter" in fl:
        return "filters"
    if "brake" in fl:
        return "brakes"
    if "clutch" in fl or "bearing" in fl:
        return "clutch"
    if "lubric" in fl or "maintenance" in fl:
        return "maintenance_wear"
    return "other_pms"


def build_payload() -> dict:
    five = pd.read_csv(DER / "zpr1_five_customer_vs_pr00_pms_2024_2025.csv")
    five_fam = pd.read_csv(DER / "zpr1_five_customer_vs_pr00_pms_by_family_2024_2025.csv")
    mos = pd.read_csv(DER / "zpr1_five_customer_kpi_mos_2024_2025.csv")
    pv = pd.read_csv(DER / "pms_price_volume_response_2024_2025.csv")
    pv_pn = pd.read_csv(DER / "pms_price_volume_response_pn_2024_2025.csv")
    bvp = pd.read_csv(DER / "pms_genuine_bvp_vs_price_2024_2025.csv")
    pt = pd.read_csv(DER / "pms_passthrough_db_dlr_2024_2025.csv")
    cov = pd.read_csv(DER / "pms_passthrough_coverage_inventory_2026-09-22.csv")

    aim = pd.read_csv(
        DER / "aim_pn_classification.csv",
        dtype=str,
        usecols=["part_number", "description_norm", "aim_l1", "aim_l2", "aim_l3"],
    )
    aim["pn"] = norm_pn(aim["part_number"])
    aim = aim.drop_duplicates("pn")

    cat = pd.read_csv(
        DER / "parts_catalog_dimension.csv",
        dtype=str,
        usecols=["part_number", "pms_category"],
    )
    cat["pn"] = norm_pn(cat["part_number"])
    cat = cat.drop_duplicates("pn")

    # Enrich stocking PN pairs
    pv_pn = pv_pn.copy()
    pv_pn["pn"] = norm_pn(pv_pn["part_number"])
    pv_pn = pv_pn.merge(aim[["pn", "description_norm", "aim_l1", "aim_l2", "aim_l3"]], on="pn", how="left")
    pv_pn = pv_pn.merge(cat[["pn", "pms_category"]], on="pn", how="left")

    # Five-customer condition prices at PN (2025), for drawer
    five_pn_rows = []
    for year, path in [
        (2024, DER / "pricing_zpr1_five_2024.parquet"),
        (2025, DER / "pricing_zpr1_five_2025.parquet"),
    ]:
        if not path.exists():
            continue
        z = pd.read_parquet(path, columns=["customer", "customer_label", "pn", "Price", "list_year"])
        z["pn"] = norm_pn(z["pn"])
        z = z[z["customer"].isin(FIVE)]
        # only keep PNs that appear in pv_pn to bound size
        keep_pns = set(pv_pn["pn"])
        z = z[z["pn"].isin(keep_pns)]
        five_pn_rows.append(z.assign(year=year)[["year", "customer", "customer_label", "pn", "Price"]])
    five_pn = pd.concat(five_pn_rows, ignore_index=True) if five_pn_rows else pd.DataFrame()

    # PR00 for drawer context
    pr00_25 = pd.read_parquet(DER / "pricing_pr00_ie40_2025.parquet")
    pr00_25["pn"] = norm_pn(pr00_25["Material"])
    pr00_25 = pr00_25[["pn", "Price_EUR"]].drop_duplicates("pn").rename(columns={"Price_EUR": "pr00_2025"})

    # AIM tree with PN lists under subgroup (via pms_category == subgroup)
    # Aggregate pv_pn by pn for impact ranking within subgroup
    pn_agg = (
        pv_pn.groupby("pn", as_index=False)
        .agg(
            description=("description_norm", "first"),
            aim_l1=("aim_l1", "first"),
            aim_l2=("aim_l2", "first"),
            aim_l3=("aim_l3", "first"),
            pms_category=("pms_category", "first"),
            family=("family", "first"),
            eur_impact=("eur_volume_impact", "sum"),
            rev_2025=("rev_2025", "sum"),
            n_pairs=("part_number", "count"),
        )
    )
    pn_agg["abs_impact"] = pn_agg["eur_impact"].abs()

    aim_tree = []
    for (grp, fam), g in bvp.groupby(["product_group_label", "product_family"], dropna=False):
        subs = []
        for sub, sg in g.groupby("product_subgroup"):
            elig = sg[(sg["signal"] == "substitution_signal") & (sg["eligible"] == True)]
            # PNs in this service subgroup
            pns = pn_agg[pn_agg["pms_category"].astype(str) == str(sub)].nlargest(40, "abs_impact")
            if pns.empty:
                # fallback: family string match on pv family
                pns = pn_agg[pn_agg["family"].astype(str) == str(sub)].nlargest(40, "abs_impact")
            subs.append(
                {
                    "subgroup": sub,
                    "n_cells": int(len(sg)),
                    "total_eur_2025": float(sg["total_eur_2025"].sum()),
                    "sub_gain_eur": float(elig["bvp_share_gain_eur"].sum()) if len(elig) else 0.0,
                    "n_sub_signals": int(len(elig)),
                    "db_rows": clean(
                        sg.sort_values("total_eur_2025", ascending=False)[
                            [
                                "distributor_code",
                                "signal",
                                "eligible",
                                "total_eur_2025",
                                "genuine_asp_yoy_pct",
                                "bvp_share_eur_yoy_pp",
                                "bvp_share_gain_eur",
                            ]
                        ].head(25)
                    ),
                    "parts": clean(
                        pns[
                            [
                                "pn",
                                "description",
                                "aim_l1",
                                "aim_l2",
                                "aim_l3",
                                "eur_impact",
                                "rev_2025",
                                "n_pairs",
                            ]
                        ]
                    ),
                }
            )
        aim_tree.append(
            {
                "group": grp if pd.notna(grp) else "(blank)",
                "family": fam if pd.notna(fam) else "(blank)",
                "total_eur_2025": float(g["total_eur_2025"].sum()),
                "subgroups": sorted(subs, key=lambda x: -x["total_eur_2025"]),
            }
        )
    aim_tree.sort(key=lambda x: -x["total_eur_2025"])

    pms_families = []
    for _, r in pv.sort_values("eur_billed_2024", ascending=False).iterrows():
        fam = r["family"]
        bucket = bucket_for(fam)
        five_rows = five_fam[five_fam["pms_family"] == bucket]
        pn_rows = pv_pn[pv_pn["family"] == fam].copy()
        pn_rows["abs_impact"] = pn_rows["eur_volume_impact"].abs()
        pn_rows = pn_rows.nlargest(40, "abs_impact")  # more rows; all clickable
        pms_families.append(
            {
                "family": fam,
                "bucket": bucket,
                "eur_billed_2024": float(r["eur_billed_2024"]),
                "eur_billed_2025": float(r["eur_billed_2025"]),
                "eur_volume_impact": float(r["eur_volume_impact"]),
                "eur_leak_flat": float(r["eur_leak_price_flat_vol_down"]),
                "eur_sensitive": float(r["eur_sensitive_price_up_vol_down"]),
                "median_pct_price_yoy": float(r["median_pct_price_yoy"])
                if pd.notna(r["median_pct_price_yoy"])
                else None,
                "median_pct_qty_yoy": float(r["median_pct_qty_yoy"])
                if pd.notna(r["median_pct_qty_yoy"])
                else None,
                "beta": float(r["beta_elasticity"]) if pd.notna(r["beta_elasticity"]) else None,
                "beta_identified": bool(r["beta_identified"]),
                "reading": r["reading"],
                "five_customer": clean(five_rows),
                "parts": clean(
                    pn_rows[
                        [
                            "pn",
                            "part_number",
                            "distributor_code",
                            "customer",
                            "description_norm",
                            "aim_l1",
                            "aim_l2",
                            "aim_l3",
                            "pms_category",
                            "quadrant",
                            "pct_price_yoy",
                            "pct_qty_yoy",
                            "price_2024",
                            "price_2025",
                            "qty_2024",
                            "qty_2025",
                            "rev_2024",
                            "rev_2025",
                            "eur_volume_impact",
                        ]
                    ]
                ),
            }
        )

    # PN master for drawer: all pairs + five prices + pr00
    drawer_pairs = clean(
        pv_pn[
            [
                "pn",
                "part_number",
                "distributor_code",
                "customer",
                "family",
                "description_norm",
                "aim_l1",
                "aim_l2",
                "aim_l3",
                "pms_category",
                "quadrant",
                "pct_price_yoy",
                "pct_qty_yoy",
                "price_2024",
                "price_2025",
                "qty_2024",
                "qty_2025",
                "rev_2024",
                "rev_2025",
                "eur_volume_impact",
            ]
        ]
    )
    five_pn_c = clean(five_pn) if len(five_pn) else []
    pr00_c = clean(pr00_25[pr00_25["pn"].isin(pv_pn["pn"])])

    sub_top = bvp[(bvp["signal"] == "substitution_signal") & (bvp["eligible"] == True)].sort_values(
        "bvp_share_gain_eur", ascending=False
    ).head(12)
    ituk_pt = pt[pt["distributor_code"] == "ITUK"].copy()

    return {
        "built": "2026-09-22",
        "verdict": (
            "On PMS, about EUR 1.1M of volume impact sits where list price barely moved — "
            "that is capture or stocking, not a clean elasticity slope. "
            "Five-customer condition books: CBC and Grand Avto still ~+29% above list; "
            "Israel mid-discount; KIMA deep under list. "
            "Click any family or part number — drill ends at the part."
        ),
        "agenda": [
            {
                "id": "interest",
                "q": "Are 2024/2025 customer prices useful?",
                "a": "Yes — for condition vs list, stocking response, and revision risk. Not for a single network elasticity number.",
            },
            {
                "id": "elast",
                "q": "Can we check price elasticity on PMS?",
                "a": "Directionally only. Most euro sits in volume-down with flat list (~EUR 1.08M). Betas only identify on four families and are noisy.",
            },
            {
                "id": "files",
                "q": "What did the downloads actually contain?",
                "a": "2024_PR00 and both ZPR1 years are real. Root 2025_PR00 was misnamed CY2026 billing. True 2025 list already lived in parquet.",
            },
            {
                "id": "five",
                "q": "What about CBC, GA, UTI, UMI, KIMA only?",
                "a": "CBC/GA ~+29% above list; UTI ~−12%; UMI ~−16%; KIMA ~−33%. UTI≠UMI throughout.",
            },
            {
                "id": "mos",
                "q": "Does MOS help?",
                "a": "Yes for Israel and KIMA. UTI ~143 days stock (2025), UMI ~147, KIMA ~30. Fat stock + soft volume = warehouse story. CBC/GA not in KPI.",
            },
            {
                "id": "pass",
                "q": "What about pass-through to dealers?",
                "a": "Price pass-through blocked (no dealer invoices). Volume YoY only for ITUK (+5.4% PMS qty).",
            },
            {
                "id": "bvp",
                "q": "Did genuine price rises push BVP?",
                "a": "Sometimes, small euro: ~EUR 45k share-gain on 13 eligible cells. Led by IUK air filters.",
            },
        ],
        "kpis": [
            {"label": "Flat-list volume impact (PMS)", "value": "EUR 1.08M", "tone": "amber"},
            {"label": "Price-up volume-down (PMS)", "value": "EUR 0.41M", "tone": "amber"},
            {"label": "BVP share-gain signal", "value": "EUR 45k", "tone": "ok"},
            {"label": "Sales-to-dealer YoY markets", "value": "ITUK only", "tone": "amber"},
            {"label": "ZPR1 customers in scope", "value": "5", "tone": "ok"},
        ],
        "five_customer": clean(five),
        "five_family": clean(five_fam),
        "mos": clean(mos),
        "pms_families": pms_families,
        "aim_tree": aim_tree[:40],
        "pn_pairs": drawer_pairs,
        "five_pn_prices": five_pn_c,
        "pr00_2025": {r["pn"]: r["pr00_2025"] for r in pr00_c},
        "bvp_top": clean(
            sub_top[
                [
                    "distributor_code",
                    "product_subgroup",
                    "genuine_asp_yoy_pct",
                    "bvp_share_eur_yoy_pp",
                    "bvp_share_gain_eur",
                    "total_eur_2025",
                ]
            ]
        ),
        "passthrough_coverage": clean(cov),
        "ituk_passthrough": clean(ituk_pt),
        "next": [
            "Network billed ASP vs list for distributors not in the five ZPR1 books",
            "More CY2024 sales-to-dealer files (UTI file named 2024 is Jan-2025 YTD)",
            "Dealer invoice prices if you want true pass-through",
            "Quarantine or rename the mislabeled root 2025_PR00 billing export",
        ],
    }


HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>ISZE · PMS price response brief · 2026-09-22</title>
<style>
:root{--navy:#15233c;--ink:#1a1a1a;--muted:#5a6570;--paper:#f7f4ee;--line:#d8dde6;--red:#c0552d;--ok:#1f6b4a;--amber:#b45309;--link:#1a4f8b}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.55 "Segoe UI",system-ui,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:0 24px 72px}
header{background:var(--navy);color:var(--paper);padding:28px 24px 22px;margin:0 -24px 22px;border-bottom:4px solid var(--red)}
.brand{font:700 12px/1 Consolas,monospace;letter-spacing:.18em;color:#f0c9b8;margin-bottom:10px}
h1{margin:0 0 8px;font:700 28px/1.15 Georgia,"Times New Roman",serif;color:var(--paper)}
.sub{max-width:900px;color:#d7dee8;font-size:14.5px}
.stamp{margin-top:12px;font-size:12px;color:#9aa8ba}
.verdict{background:#fff;border:1px solid var(--line);border-left:5px solid var(--red);padding:16px 18px;margin:0 0 20px}
.verdict b{color:var(--navy)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin:0 0 22px}
.kpi{background:#fff;border:1px solid var(--line);border-top:3px solid var(--navy);padding:12px 14px}
.kpi.amber{border-top-color:var(--amber)}.kpi.ok{border-top-color:var(--ok)}
.kpi .v{font:700 22px/1.1 Georgia,serif;color:var(--navy)}
.kpi.amber .v{color:var(--amber)}.kpi.ok .v{color:var(--ok)}
.kpi .l{margin-top:6px;font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);font-weight:700}
h2{font:700 20px/1.2 Georgia,serif;color:var(--navy);margin:28px 0 8px}
h3{font:700 15px/1.3 Segoe UI,sans-serif;color:var(--navy);margin:16px 0 8px}
.lead{color:var(--muted);margin:0 0 12px;max-width:920px}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 18px}
.chip{border:1px solid var(--line);background:#fff;color:var(--navy);padding:8px 12px;border-radius:999px;cursor:pointer;font-size:13px;font-weight:600}
.chip:hover,.chip.on{background:var(--navy);color:var(--paper);border-color:var(--navy)}
.panel{background:#fff;border:1px solid var(--line);padding:14px 16px;margin:0 0 14px;display:none}
.panel.on{display:block}
.zoombar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:0 0 12px}
.zoombar label{font-size:12px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
select{padding:8px 10px;border:1px solid var(--line);background:#fff;font:14px Segoe UI,sans-serif;min-width:180px}
.crumbs{font-size:13px;color:var(--muted);margin:0 0 10px}
.crumbs button{border:0;background:none;color:var(--link);font:inherit;font-weight:700;cursor:pointer;text-decoration:underline;padding:0}
.btn{border:1px solid var(--navy);background:var(--navy);color:var(--paper);padding:7px 12px;cursor:pointer;font-weight:600;font-size:13px}
.btn.ghost{background:#fff;color:var(--navy)}
table{width:100%;border-collapse:collapse;font-size:13px;margin:8px 0}
th{background:var(--navy);color:var(--paper);text-align:left;padding:8px 10px;font-size:11px;text-transform:uppercase;letter-spacing:.04em}
td{padding:7px 10px;border-bottom:1px solid #eceff4;background:#fff;color:var(--ink)}
tbody tr:nth-child(even) td{background:#fafbfc}
tr.clickable{cursor:pointer} tr.clickable:hover td{background:#eef3f9}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.pos{color:var(--ok);font-weight:700}.neg{color:var(--red);font-weight:700}
.bars{display:flex;flex-direction:column;gap:6px;margin:10px 0 4px}
.bar-row{display:grid;grid-template-columns:160px 1fr 80px;gap:8px;align-items:center;font-size:13px;cursor:pointer;padding:4px 6px;border-radius:4px}
.bar-row:hover{background:#eef3f9}
.bar-track{height:12px;background:#e8edf4;border-radius:2px;overflow:hidden}
.bar-fill{height:100%;background:var(--navy)}.bar-fill.amber{background:var(--amber)}
.note{font-size:12.5px;color:var(--muted);margin:8px 0}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:800px){.grid2{grid-template-columns:1fr}}
ul.clean{margin:8px 0 0 18px;padding:0} ul.clean li{margin:0 0 6px}
.foot{margin-top:36px;padding-top:14px;border-top:1px solid var(--line);font-size:12px;color:var(--muted)}
.tag{display:inline-block;padding:2px 8px;border:1px solid #e2c9a8;background:#fff8ef;color:var(--amber);font-size:11px;font-weight:700}
a.pn,button.pn{border:0;background:none;color:var(--link);font:inherit;font-weight:700;cursor:pointer;text-decoration:underline;padding:0;font-family:Consolas,monospace;font-size:12.5px}
.hint{font-size:12px;color:var(--muted);margin:0 0 8px}
#drawer{position:fixed;top:0;right:0;width:min(480px,100%);height:100%;background:#fff;border-left:1px solid var(--line);box-shadow:-8px 0 24px rgba(21,35,60,.18);transform:translateX(100%);transition:transform .2s;z-index:40;overflow:auto;padding:18px 18px 40px}
#drawer.open{transform:translateX(0)}
#drawer h2{margin-top:8px;font-size:18px}
#mask{position:fixed;inset:0;background:rgba(21,35,60,.35);z-index:30;display:none}
#mask.on{display:block}
.close{float:right;border:1px solid var(--line);background:#fff;padding:4px 10px;cursor:pointer;font-weight:700}
</style>
</head>
<body>
<div class="wrap">
<header>
  <div class="brand">ISUZU · ISZE · INTERNAL</div>
  <h1>PMS price response brief</h1>
  <div class="sub">Stocking response, five-customer condition books, MOS, sales to dealer, genuine vs BVP.
  Standard drill: classification group → family → subgroup → <b>part number</b> (click the blue part links).</div>
  <div class="stamp">Built __BUILT__ · Self-contained · UTI ≠ UMI · CBC ≠ Grand Avto · AIM path clickable to PN</div>
</header>

<div class="verdict"><b>Verdict.</b> __VERDICT__</div>
<div class="kpis" id="kpis"></div>

<h2>Ask a question</h2>
<p class="lead">Click a chip — answers from the files on disk.</p>
<div class="chips" id="qchips"></div>
<div id="qpanels"></div>

<h2>1. Zoom — PMS → part number</h2>
<p class="lead">Click a bar or family row to open the family. Then click any <span style="color:var(--link);font-weight:700">blue part number</span> for the part card (AIM path, all DBs, five-customer conditions when present).</p>
<div class="zoombar">
  <label>PMS family</label>
  <select id="pmsSel"></select>
  <button class="btn ghost" type="button" id="pmsReset">All families</button>
</div>
<div class="crumbs" id="pmsCrumbs"></div>
<div id="pmsView"></div>

<h2>2. Zoom — AIM group → family → subgroup → part</h2>
<p class="lead">Same rule: every level is clickable; the last step is the part number.</p>
<div class="zoombar">
  <label>AIM group</label><select id="aimGroup"></select>
  <label>Family</label><select id="aimFam"></select>
  <label>Subgroup</label><select id="aimSub"></select>
</div>
<div class="crumbs" id="aimCrumbs"></div>
<div id="aimView"></div>

<h2>3. Five customers — condition vs list</h2>
<div id="fiveView"></div>

<h2>4. MOS — days of parts in stock</h2>
<div id="mosView"></div>

<h2>5. Sales to dealer / pass-through</h2>
<div id="passView"></div>

<h2>6. Genuine vs BVP</h2>
<div id="bvpView"></div>

<h2>7. Next</h2>
<ul class="clean" id="nextList"></ul>
<div class="foot">Internal. Stocking ≠ dealer elasticity. Click part numbers for AIM L1→L3 path.</div>
</div>

<div id="mask"></div>
<aside id="drawer" aria-label="Part detail"></aside>

<script type="application/json" id="payload">__PAYLOAD__</script>
<script>
(function(){
  const P = JSON.parse(document.getElementById('payload').textContent);
  const eur = n => {
    if(n==null || !isFinite(+n)) return '—';
    n=+n; const a=Math.abs(n);
    if(a>=1e6) return (n<0?'−':'')+'EUR '+(a/1e6).toFixed(2)+'M';
    if(a>=1e3) return (n<0?'−':'')+'EUR '+(a/1e3).toFixed(0)+'k';
    return (n<0?'−':'')+'EUR '+a.toFixed(0);
  };
  const pct = n => (n==null||!isFinite(+n)) ? '—' : ((+n>0?'+':'')+(+n).toFixed(1)+'%');
  const pctPts = n => (n==null||!isFinite(+n)) ? '—' : ((+n>0?'+':'')+(+n).toFixed(1)+' pp');
  const esc = s => String(s??'').replace(/[&<>"']/g, c=>({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c]));

  document.getElementById('kpis').innerHTML = P.kpis.map(k=>
    `<div class="kpi ${k.tone||''}"><div class="v">${k.value}</div><div class="l">${k.label}</div></div>`
  ).join('');

  // Q chips
  const chips=document.getElementById('qchips'), panels=document.getElementById('qpanels');
  P.agenda.forEach((a,i)=>{
    const b=document.createElement('button'); b.type='button'; b.className='chip'+(i===0?' on':''); b.textContent=a.q; b.dataset.id=a.id; chips.appendChild(b);
    const d=document.createElement('div'); d.className='panel'+(i===0?' on':''); d.id='panel-'+a.id;
    d.innerHTML=`<h3>${esc(a.q)}</h3><p>${esc(a.a)}</p>`; panels.appendChild(d);
  });
  chips.onclick=e=>{ const t=e.target.closest('.chip'); if(!t) return;
    chips.querySelectorAll('.chip').forEach(c=>c.classList.toggle('on',c===t));
    panels.querySelectorAll('.panel').forEach(p=>p.classList.toggle('on',p.id==='panel-'+t.dataset.id));
  };

  // ---- Part drawer ----
  const drawer=document.getElementById('drawer'), mask=document.getElementById('mask');
  function closePn(){ drawer.classList.remove('open'); mask.classList.remove('on'); }
  mask.onclick=closePn;
  function openPn(pn){
    pn=String(pn).replace(/^0+/,'') || '0';
    const pairs=(P.pn_pairs||[]).filter(r=>String(r.pn)===pn || String(r.part_number).replace(/^0+/,'')===pn);
    const meta=pairs[0]||{};
    const five=(P.five_pn_prices||[]).filter(r=>String(r.pn)===pn);
    const pr00=(P.pr00_2025||{})[pn];
    let path=[meta.aim_l1, meta.aim_l2, meta.aim_l3].filter(Boolean).join(' → ') || 'AIM path not on this row';
    let html=`<button type="button" class="close" id="drawerClose">Close</button>
      <div class="tag">PART NUMBER</div>
      <h2 style="font-family:Consolas,monospace">${esc(meta.part_number||pn)}</h2>
      <p>${esc(meta.description_norm||'No description')}</p>
      <p class="note"><b>AIM:</b> ${esc(path)}<br><b>PMS category:</b> ${esc(meta.pms_category||meta.family||'—')}
      <br><b>List 2025 (PR00):</b> ${pr00!=null? ('EUR '+(+pr00).toFixed(2)) : '—'}</p>
      <h3>Stocking pairs (ISZE → distributor)</h3>
      <table><thead><tr><th>DB</th><th class="n">Price YoY</th><th class="n">Qty YoY</th><th class="n">Impact</th><th>Quadrant</th></tr></thead><tbody>`+
      (pairs.length? pairs.map(r=>`<tr><td>${esc(r.distributor_code)}</td><td class="n">${pct(r.pct_price_yoy)}</td>
        <td class="n">${pct(r.pct_qty_yoy)}</td><td class="n">${eur(r.eur_volume_impact)}</td>
        <td class="note">${esc(r.quadrant)}</td></tr>`).join('') : '<tr><td colspan="5">No stocking pair in the top-impact extract for this part.</td></tr>')+
      `</tbody></table>
      <h3>Five customers — condition price</h3>`;
    if(!five.length) html += `<p class="note">Not in the five-customer ZPR1 extract for this part (or not in the impact shortlist join).</p>`;
    else {
      const byY={2024:{},2025:{}};
      five.forEach(r=>{ byY[r.year]=byY[r.year]||{}; byY[r.year][r.customer_label]=r.Price; });
      html += `<table><thead><tr><th>Customer</th><th class="n">2024 ZPR1</th><th class="n">2025 ZPR1</th><th class="n">vs list 2025</th></tr></thead><tbody>`+
        ['CBC','GA','UTI','UMI','KIMA'].map(lab=>{
          const p24=byY[2024][lab], p25=byY[2025][lab];
          const vs = (p25!=null && pr00) ? (100*(p25/pr00-1)) : null;
          const cls = vs!=null && vs>0 ? 'neg':'pos';
          return `<tr><td>${lab}</td><td class="n">${p24!=null?('EUR '+(+p24).toFixed(2)):'—'}</td>
            <td class="n">${p25!=null?('EUR '+(+p25).toFixed(2)):'—'}</td>
            <td class="n ${cls}">${vs!=null?pct(vs):'—'}</td></tr>`;
        }).join('')+`</tbody></table>`;
    }
    drawer.innerHTML=html;
    document.getElementById('drawerClose').onclick=closePn;
    drawer.classList.add('open'); mask.classList.add('on');
  }
  document.body.addEventListener('click', e=>{
    const t=e.target.closest('[data-pn]');
    if(t){ e.preventDefault(); e.stopPropagation(); openPn(t.getAttribute('data-pn')); }
  });

  function pnBtn(pn, label){
    const lab=label||pn;
    return `<button type="button" class="pn" data-pn="${esc(pn)}">${esc(lab)}</button>`;
  }

  // ---- PMS zoom ----
  const pmsSel=document.getElementById('pmsSel');
  pmsSel.innerHTML=`<option value="">All families (overview)</option>`+P.pms_families.map((f,i)=>`<option value="${i}">${esc(f.family)}</option>`).join('');

  function renderPmsOverview(){
    document.getElementById('pmsCrumbs').innerHTML='Level: <b>all PMS families</b> → click a family → click a part';
    const max=Math.max(...P.pms_families.map(f=>Math.abs(f.eur_leak_flat||0)),1);
    const bars=P.pms_families.map((f,i)=>{
      const w=Math.min(100,100*Math.abs(f.eur_leak_flat||0)/max);
      return `<div class="bar-row" data-fam="${i}"><div>${esc(f.family)}</div><div class="bar-track"><div class="bar-fill amber" style="width:${w}%"></div></div><div class="n">${eur(f.eur_leak_flat)}</div></div>`;
    }).join('');
    document.getElementById('pmsView').innerHTML=
      `<p class="hint">Click a bar or table row to open that family.</p><div class="bars">${bars}</div>
       <table><thead><tr><th>Family</th><th class="n">Billed 2024</th><th class="n">Qty YoY</th><th class="n">Price YoY</th><th class="n">Flat-list impact</th><th>Beta?</th></tr></thead><tbody>`+
      P.pms_families.map((f,i)=>`<tr class="clickable" data-fam="${i}"><td>${esc(f.family)}</td><td class="n">${eur(f.eur_billed_2024)}</td>
        <td class="n">${pct(f.median_pct_qty_yoy)}</td><td class="n">${pct(f.median_pct_price_yoy)}</td>
        <td class="n">${eur(f.eur_leak_flat)}</td><td>${f.beta_identified?(f.beta!=null?f.beta.toFixed(1):'yes'):'n/a'}</td></tr>`).join('')+
      `</tbody></table>`;
    document.getElementById('pmsView').onclick=e=>{
      const row=e.target.closest('[data-fam]'); if(!row) return;
      pmsSel.value=row.getAttribute('data-fam'); renderPmsFamily(+pmsSel.value);
    };
  }

  function renderPmsFamily(i){
    const f=P.pms_families[i];
    document.getElementById('pmsCrumbs').innerHTML=
      `Level: <button type="button" id="crumbPmsAll">all PMS</button> → <b>${esc(f.family)}</b> <span class="tag">${esc(f.bucket)}</span> → click a part`;
    document.getElementById('crumbPmsAll').onclick=()=>{pmsSel.value=''; renderPmsOverview();};
    const five=(f.five_customer||[]).filter(r=>r.year===2025);
    let html=`<div class="grid2"><div class="panel on"><h3>Stocking move</h3>
      <p>Billed ${eur(f.eur_billed_2024)} → ${eur(f.eur_billed_2025)}. Volume impact ${eur(f.eur_volume_impact)}.
      Flat-list ${eur(f.eur_leak_flat)}; price-up sensitive ${eur(f.eur_sensitive)}.</p>
      <p class="note">${esc(f.reading||'')}</p></div>
      <div class="panel on"><h3>Five customers on this bucket (2025)</h3>`;
    if(!five.length) html+=`<p class="note">No five-customer rows for bucket ${esc(f.bucket)}.</p>`;
    else html+=`<table><thead><tr><th>Customer</th><th class="n">vs list</th><th class="n">Billed</th><th class="n">PNs</th></tr></thead><tbody>`+
      five.map(r=>`<tr><td>${esc(r.customer_label)}</td><td class="n ${r.median_zpr1_vs_pr00_pct>0?'neg':'pos'}">${pct(r.median_zpr1_vs_pr00_pct)}</td>
        <td class="n">${eur(r.billed_eur)}</td><td class="n">${r.n_pns}</td></tr>`).join('')+`</tbody></table>`;
    html+=`</div></div><h3>Parts in this family — click the part number</h3>
      <p class="hint">Blue part numbers open the part card (AIM path + all DB pairs + five-customer conditions).</p>
      <table><thead><tr><th>Part</th><th>Description</th><th>DB</th><th>AIM L3</th><th class="n">Price YoY</th><th class="n">Qty YoY</th><th class="n">Impact</th></tr></thead><tbody>`+
      (f.parts||[]).map(r=>`<tr>
        <td>${pnBtn(r.pn, r.part_number)}</td>
        <td class="note">${esc((r.description_norm||'').slice(0,48))}</td>
        <td>${esc(r.distributor_code)}</td>
        <td class="note">${esc(r.aim_l3||'—')}</td>
        <td class="n">${pct(r.pct_price_yoy)}</td>
        <td class="n">${pct(r.pct_qty_yoy)}</td>
        <td class="n">${eur(r.eur_volume_impact)}</td></tr>`).join('')+`</tbody></table>`;
    document.getElementById('pmsView').innerHTML=html;
    document.getElementById('pmsView').onclick=null;
  }
  pmsSel.onchange=()=>{ if(pmsSel.value==='') renderPmsOverview(); else renderPmsFamily(+pmsSel.value); };
  document.getElementById('pmsReset').onclick=()=>{pmsSel.value=''; renderPmsOverview();};
  renderPmsOverview();

  // ---- AIM zoom ----
  const aimGroup=document.getElementById('aimGroup');
  const aimFam=document.getElementById('aimFam');
  const aimSub=document.getElementById('aimSub');
  const groups=[...new Set(P.aim_tree.map(x=>x.group))];
  aimGroup.innerHTML=`<option value="">All groups</option>`+groups.map(g=>`<option>${esc(g)}</option>`).join('');

  function famsFor(g){ return P.aim_tree.filter(x=>!g || x.group===g); }
  function fillFam(){
    const rows=famsFor(aimGroup.value);
    const fams=[...new Set(rows.map(r=>r.family))];
    aimFam.innerHTML=`<option value="">All families</option>`+fams.map(f=>`<option>${esc(f)}</option>`).join('');
    fillSub();
  }
  function fillSub(){
    const rows=famsFor(aimGroup.value).filter(r=>!aimFam.value || r.family===aimFam.value);
    const subs=[]; rows.forEach(r=>r.subgroups.forEach(s=>subs.push(s.subgroup)));
    aimSub.innerHTML=`<option value="">All subgroups</option>`+[...new Set(subs)].map(s=>`<option>${esc(s)}</option>`).join('');
    renderAim();
  }
  function renderAim(){
    let rows=famsFor(aimGroup.value).filter(r=>!aimFam.value || r.family===aimFam.value);
    const bits=['<button type="button" data-aim-reset="1">AIM</button>'];
    if(aimGroup.value) bits.push(`<b>${esc(aimGroup.value)}</b>`);
    if(aimFam.value) bits.push(`<b>${esc(aimFam.value)}</b>`);
    if(aimSub.value) bits.push(`<b>${esc(aimSub.value)}</b>`);
    bits.push('→ click a part');
    document.getElementById('aimCrumbs').innerHTML='Level: '+bits.join(' → ');
    document.getElementById('aimCrumbs').onclick=e=>{
      if(e.target.getAttribute('data-aim-reset')){ aimGroup.value=''; fillFam(); }
    };

    if(!aimFam.value){
      const max=Math.max(...rows.map(r=>r.total_eur_2025),1);
      document.getElementById('aimView').innerHTML=`<p class="hint">Click a row to open that AIM family.</p><div class="bars">`+
        rows.slice(0,25).map(r=>{
          const w=Math.min(100,100*r.total_eur_2025/max);
          return `<div class="bar-row" data-aim-g="${esc(r.group)}" data-aim-f="${esc(r.family)}"><div>${esc(r.group)} / ${esc(r.family)}</div>
            <div class="bar-track"><div class="bar-fill" style="width:${w}%"></div></div><div class="n">${eur(r.total_eur_2025)}</div></div>`;
        }).join('')+`</div>`;
      document.getElementById('aimView').onclick=e=>{
        const row=e.target.closest('[data-aim-g]'); if(!row) return;
        aimGroup.value=row.getAttribute('data-aim-g'); fillFam();
        aimFam.value=row.getAttribute('data-aim-f'); fillSub();
      };
      return;
    }
    const node=rows[0]; if(!node){ document.getElementById('aimView').innerHTML='<p class="note">No rows.</p>'; return; }
    let subs=node.subgroups; if(aimSub.value) subs=subs.filter(s=>s.subgroup===aimSub.value);
    if(!aimSub.value){
      document.getElementById('aimView').innerHTML=`<p class="hint">Click a subgroup to see parts.</p>
        <table><thead><tr><th>Subgroup</th><th class="n">2025 €</th><th class="n">Parts listed</th><th class="n">BVP share-gain</th></tr></thead><tbody>`+
        subs.map(s=>`<tr class="clickable" data-aim-s="${esc(s.subgroup)}"><td>${esc(s.subgroup)}</td>
          <td class="n">${eur(s.total_eur_2025)}</td><td class="n">${(s.parts||[]).length}</td>
          <td class="n">${eur(s.sub_gain_eur)}</td></tr>`).join('')+`</tbody></table>`;
      document.getElementById('aimView').onclick=e=>{
        const row=e.target.closest('[data-aim-s]'); if(!row) return;
        aimSub.value=row.getAttribute('data-aim-s'); renderAim();
      };
      return;
    }
    const s=subs[0]; if(!s){ document.getElementById('aimView').innerHTML='<p class="note">No subgroup.</p>'; return; }
    document.getElementById('aimView').innerHTML=`<h3>Distributor cells</h3>
      <table><thead><tr><th>DB</th><th>Signal</th><th class="n">2025 €</th><th class="n">ASP YoY</th><th class="n">BVP Δ</th></tr></thead><tbody>`+
      (s.db_rows||[]).map(r=>`<tr><td>${esc(r.distributor_code)}</td><td>${esc(r.signal)}</td><td class="n">${eur(r.total_eur_2025)}</td>
        <td class="n">${pct(r.genuine_asp_yoy_pct)}</td><td class="n">${pctPts(r.bvp_share_eur_yoy_pp)}</td></tr>`).join('')+
      `</tbody></table>
      <h3>Parts in this subgroup — click the part number</h3>
      <p class="hint">${(s.parts||[]).length ? '' : 'No part-level stocking pairs matched this subgroup in the impact extract.'}</p>
      <table><thead><tr><th>Part</th><th>Description</th><th>AIM L3</th><th class="n">Impact</th><th class="n">2025 billed</th></tr></thead><tbody>`+
      (s.parts||[]).map(r=>`<tr><td>${pnBtn(r.pn)}</td><td class="note">${esc((r.description||'').slice(0,48))}</td>
        <td class="note">${esc(r.aim_l3||'—')}</td><td class="n">${eur(r.eur_impact)}</td><td class="n">${eur(r.rev_2025)}</td></tr>`).join('')+
      `</tbody></table>`;
    document.getElementById('aimView').onclick=null;
  }
  aimGroup.onchange=fillFam; aimFam.onchange=fillSub; aimSub.onchange=renderAim; fillFam();

  // Five / MOS / pass / bvp (same as before, compact)
  const byCust={}; P.five_customer.forEach(r=>{ byCust[r.customer_label]=byCust[r.customer_label]||{code:r.customer,name:r.customer_name,y:{}}; byCust[r.customer_label].y[r.year]=r; });
  const order=['CBC','GA','UTI','UMI','KIMA'];
  document.getElementById('fiveView').innerHTML=`<table><thead><tr><th>Customer</th><th class="n">2024</th><th class="n">2025</th><th class="n">Δ</th><th class="n">2025 billed</th></tr></thead><tbody>`+
    order.map(lab=>{ const c=byCust[lab]; if(!c) return ''; const a=c.y[2024],b=c.y[2025]; const d=(a&&b)?b.median_zpr1_vs_pr00_pct-a.median_zpr1_vs_pr00_pct:null;
      return `<tr><td><b>${lab}</b> (${c.code})<div class="note">${esc(c.name)}</div></td>
        <td class="n">${pct(a&&a.median_zpr1_vs_pr00_pct)}</td><td class="n ${b&&b.median_zpr1_vs_pr00_pct>0?'neg':'pos'}">${pct(b&&b.median_zpr1_vs_pr00_pct)}</td>
        <td class="n">${pctPts(d)}</td><td class="n">${eur(b&&b.billed_eur_pms_matched)}</td></tr>`; }).join('')+`</tbody></table>`;

  const mosBy={}; P.mos.forEach(r=>{ mosBy[r.customer_label]=mosBy[r.customer_label]||{}; mosBy[r.customer_label][r.year]=r; });
  document.getElementById('mosView').innerHTML=`<table><thead><tr><th>Customer</th><th class="n">MOS 2024</th><th class="n">MOS 2025</th><th class="n">Fill 2025</th><th>Note</th></tr></thead><tbody>`+
    order.map(lab=>{ const a=mosBy[lab]&&mosBy[lab][2024], b=mosBy[lab]&&mosBy[lab][2025];
      const fm=v=>(v==null||!isFinite(v))?'n/a':(+v).toFixed(0);
      const ff=v=>(v==null||!isFinite(v))?'n/a':(100*v).toFixed(0)+'%';
      return `<tr><td><b>${lab}</b></td><td class="n">${fm(a&&a.mos_days_avg)}</td><td class="n">${fm(b&&b.mos_days_avg)}</td>
        <td class="n">${ff(b&&b.fill_rate_avg)}</td><td class="note">${esc((b&&b.kpi_note)||'')}</td></tr>`; }).join('')+`</tbody></table>`;

  document.getElementById('passView').innerHTML=`<table><thead><tr><th>Market</th><th>Years</th><th>YoY</th><th>Price pass-through</th><th>Note</th></tr></thead><tbody>`+
    (P.passthrough_coverage||[]).map(r=>`<tr><td><b>${esc(r.distributor_code)}</b></td><td>${esc(r.years_present||'')}</td>
      <td>${r.yoy_2024_2025_possible?'<span class="pos">Yes</span>':'<span class="neg">No</span>'}</td>
      <td>${esc(r.price_passthrough_status||'blocked')}</td><td class="note">${esc(r.yoy_reason||'')}</td></tr>`).join('')+`</tbody></table>`+
    (P.ituk_passthrough&&P.ituk_passthrough.length? `<h3>ITUK PMS qty</h3><table><thead><tr><th>Family</th><th class="n">2024</th><th class="n">2025</th><th class="n">Wtd %</th></tr></thead><tbody>`+
      P.ituk_passthrough.map(r=>`<tr><td>${esc(r.pms_family)}</td><td class="n">${r.sales_to_dealer_qty_y0??'—'}</td>
        <td class="n">${r.sales_to_dealer_qty_y1??'—'}</td><td class="n">${pct(r.wtd_qty_pct_chg)}</td></tr>`).join('')+`</tbody></table>`:'');

  document.getElementById('bvpView').innerHTML=`<p class="hint">Click a subgroup name to jump into AIM zoom at that leaf, then open parts.</p>
    <table><thead><tr><th>DB</th><th>Subgroup</th><th class="n">ASP YoY</th><th class="n">BVP Δ</th><th class="n">Share-gain</th></tr></thead><tbody>`+
    (P.bvp_top||[]).map(r=>`<tr class="clickable" data-jump-sub="${esc(r.product_subgroup)}"><td>${esc(r.distributor_code)}</td>
      <td><button type="button" class="pn" style="font-family:inherit" data-jump-sub="${esc(r.product_subgroup)}">${esc(r.product_subgroup)}</button></td>
      <td class="n">${pct(r.genuine_asp_yoy_pct)}</td><td class="n">${pctPts(r.bvp_share_eur_yoy_pp)}</td>
      <td class="n">${eur(r.bvp_share_gain_eur)}</td></tr>`).join('')+`</tbody></table>`;
  document.getElementById('bvpView').onclick=e=>{
    const t=e.target.closest('[data-jump-sub]'); if(!t) return;
    const sub=t.getAttribute('data-jump-sub');
    // find group/family containing this subgroup
    for(const node of P.aim_tree){
      if(node.subgroups.some(s=>s.subgroup===sub)){
        aimGroup.value=node.group; fillFam(); aimFam.value=node.family; fillSub(); aimSub.value=sub; renderAim();
        document.getElementById('aimView').scrollIntoView({behavior:'smooth',block:'start'});
        break;
      }
    }
  };

  document.getElementById('nextList').innerHTML=P.next.map(x=>`<li>${esc(x)}</li>`).join('');
})();
</script>
</body>
</html>
"""


def main() -> None:
    payload = build_payload()
    html = (
        HTML.replace("__BUILT__", payload["built"])
        .replace("__VERDICT__", payload["verdict"])
        .replace("__PAYLOAD__", json.dumps(payload, ensure_ascii=False))
    )
    OUT_HTML.write_text(html, encoding="utf-8")
    OUT_CMD.write_text(
        '@echo off\r\nstart "" "%~dp0ISZE_PMS_Price_Response_Brief_2026-09-22.html"\r\n',
        encoding="utf-8",
        newline="\r\n",
    )
    print("Wrote", OUT_HTML, "bytes", OUT_HTML.stat().st_size)


if __name__ == "__main__":
    main()
