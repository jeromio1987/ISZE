# -*- coding: utf-8 -*-
"""Parts Price Intelligence — the one dashboard over the price-observation ledger.

Built 2026-10-01 on Jerome's go ("build a new dashboard"). It replaces, for reading, the
two older pages that still sit in 02_dashboards/pricing/ (Scraped Price Intelligence,
1 Aug; Aftermarket Live Pricing, 17 Sep). Both read retired sources (Mekonomen,
Autodoc) and neither reads the ledger.

What it answers, in order:
  1. How much of our billed business can we price against a rival at all?   (coverage)
  2. Where do rivals sit against our price?                                   (position)
  3. Same shelf: genuine against aftermarket at KS                            (channel gap)
  4. Which high-value parts are most exposed?                                 (exposure)
  5. How fresh is what we know, and which sources still deliver?              (health)
  6. Where should the next search go?                                         (hunt list)
  7. Any part, every observation.                                             (explorer)

2026-10-02 consolidation (Jerome: "take the best from the older dashboards"): the two old
pages were retired to 01_data/92_archive/price_pages_retired_2026-10-02/. Ported from them,
recomputed on the ledger: definitions strip with hover formulas, headline median index and
share below the comparison price, the KS same-shelf genuine vs aftermarket view, the
fewer-than-3-parts grey rule and middle-half range on the family chart, the index per
source and market, the worked arithmetic behind every index (hover), the rank correlation of
billed value with index, the day-by-day source calendar, search yield, and the price-moves
table with a 15% flag. The comparison basis stays fixed at price list x 2.19 (provisional).

Comparison basis
----------------
Rival shop prices are end-customer prices. Our price list (PR00, IE40) sits before the
distributor and dealer margins, so the default comparison is against the **reference
dealer price**: price list x 2.19, the margins reading Jerome decided under D03
(37% margin, then 27.5%; DECISIONS.md 2026-09-19). The page can switch to the raw
price list. VAT: a VAT-inclusive price can be shown with standard VAT removed; prices
whose VAT basis the source does not state stay as recorded and are marked.

Data never leaves the machine: one self-contained HTML file, Chart.js inlined, no CDN,
no upload. (Eucon-derived rows are in it; the Eucon boundary applies.)

Inputs (all local):
  01_data/00_derived/price_observations.parquet          every observed price
  01_data/00_derived/pricing_pr00_ie40.parquet           our price list
  04_tools/delegation/state/refresh_tiers_LOCAL.csv      billed last 12 months + tier
  01_data/00_derived/parts_catalog_dimension.csv         parts family
  04_tools/aftermarket_intelligence/state/crossref_graded.csv   competitor numbers known
  04_tools/aftermarket_intelligence/state/price_movement.csv    re-checked prices
  02_dashboards/_ui/chart.umd.min.js                     Chart.js, inlined

Output:
  02_dashboards/pricing/ISZE_Parts_Price_Intelligence.html
  02_dashboards/pricing/OPEN_ISZE_Parts_Price_Intelligence.cmd

Run:  python 04_tools/aftermarket_intelligence/build_parts_price_dashboard.py
"""
from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

for _s in (sys.stdout, sys.stderr):
    if _s is not None and hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ISZE = Path(__file__).resolve().parents[2]
D = ISZE / "01_data" / "00_derived"
LEDGER = D / "price_observations.parquet"
LEDGER_META = D / "price_observations.meta.json"
PRICELIST = D / "pricing_pr00_ie40.parquet"
TIERS = ISZE / "04_tools" / "delegation" / "state" / "refresh_tiers_LOCAL.csv"
TIERS_META = ISZE / "04_tools" / "delegation" / "state" / "refresh_tiers.meta.json"
CATALOG = D / "parts_catalog_dimension.csv"
GRADED = ISZE / "04_tools" / "aftermarket_intelligence" / "state" / "crossref_graded.csv"
MOVES = ISZE / "04_tools" / "aftermarket_intelligence" / "state" / "price_movement.csv"
CHARTJS = ISZE / "02_dashboards" / "_ui" / "chart.umd.min.js"
OUT = ISZE / "02_dashboards" / "pricing" / "ISZE_Parts_Price_Intelligence.html"
OPEN_CMD = OUT.parent / "OPEN_ISZE_Parts_Price_Intelligence.cmd"

KS_WEEKLY = ISZE / "04_tools" / "autodoc_scraper" / "ks_results.csv"
MANIFEST = ISZE / "04_tools" / "price_ledger" / "page_manifest.csv"

# PROVISIONAL (Jerome, 2 Oct 2026: "only for now take the fixed 2,19"): one basis for every market.
# No per-market reference dealer price until he decides otherwise.
REF_MULTIPLE = 2.19          # D03 margins reading: 1 / (1-0.37) / (1-0.275) = 2.189
MIN_N = 3                    # parts per family below which a family bar is shown grey, directional only
TODAY = pd.Timestamp(datetime.now().date())

# Price groups. Kept apart everywhere; never averaged across.
GROUP = {
    "aftermarket_retail": "street", "online_median": "street", "marketplace": "street",
    "aftermarket_rrp": "rrp", "survey_list": "rrp",
    "aftermarket_trade": "trade", "survey_workshop": "trade",
    "genuine_grey": "genuine", "dealer": "genuine",
}
GROUP_LABEL = {
    "street": "Aftermarket shop price",
    "rrp": "Aftermarket list price (brand RRP)",
    "trade": "Aftermarket trade / workshop price",
    "genuine": "Genuine Isuzu, outside our network",
}
# Standard VAT rates, used only to strip VAT from prices the source marks VAT-inclusive.
VAT = {"UK": 0.20, "DE": 0.19, "NO": 0.25, "SE": 0.25, "DK": 0.25, "PT": 0.23, "FI": 0.255}
VAT_SOURCE = ("Standard national VAT rates, fixed in the page builder (not read from a data file); "
              "checked 2 Oct 2026 against the published 2026 rates: UK 20% (HMRC), Norway 25% (Storting 2026 "
              "VAT resolution), Germany 19%, Sweden 25%, Denmark 25%, Portugal 23% (mainland), Finland 25.5% "
              "(since 1 Sep 2024).")

# Where each loader stands today (from the ledger's own notes and the 2026-10-01 runs).
SOURCE_STATUS = {
    "ks": ("KS International", "live", "Weekly run; searched by our part number"),
    "ks_am": ("KS International", "live", "Weekly result file"),
    "ks_gen": ("KS International", "live", "Weekly result file"),
    "ks_crossref": ("KS International", "live", "Searched by competitor number; 2 of 286 found"),
    "amayama": ("Amayama", "live", "Part-number runner"),
    "omega": ("Omega Spare Parts", "live", "Part-number runner"),
    "geparden": ("Geparden", "thin", "Sitemap only; cannot be searched by part number"),
    "mekster": ("Mekster", "thin", "Sitemap only"),
    "tungen": ("Tungen Bil", "thin", "One static page"),
    "autoline": ("Autoline", "thin", "Listing page, not a part lookup"),
    "tandm_commercials": ("T&M Commercials", "category", "Product type only, no Isuzu number"),
    "tranzparts": ("Tranzparts", "retired", "Retired 24 Sep: carries no Isuzu"),
    "eucon_crossref": ("Eucon PartsPool", "file", "File of Mar 2026; contract ended 31 Jul 2026"),
    "eucon_online_2025": ("Eucon online export", "file", "File of Jul 2025; brand list prices"),
    "eucon_march_2024": ("Eucon online", "file", "File of Mar 2024; web-shop prices"),
    "eucon_survey_2023": ("Eucon UK survey", "file", "2023 survey"),
}

# KS has four loaders; the calendar needs to tell them apart.
CAL_SUFFIX = {"ks": " · part-number search", "ks_gen": " · weekly file, genuine",
              "ks_am": " · weekly file, aftermarket", "ks_crossref": " · competitor-number search"}


def pn10(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.replace(r"\.0$", "", regex=True)


def nice_family(s: str) -> str:
    return str(s).replace("_", " ").capitalize() if s and s == s else "Not classified"


def r2(x):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), 2)


def main() -> int:
    for p in (LEDGER, PRICELIST, TIERS, CATALOG, GRADED, CHARTJS):
        if not p.exists():
            print(f"REFUSED — missing input: {p}")
            return 1

    # ── inputs ────────────────────────────────────────────────────────────────
    obs = pd.read_parquet(LEDGER)
    obs = obs[obs["price_eur"].notna()].copy()
    obs["grp"] = obs["price_type"].map(GROUP)
    obs = obs[obs["grp"].notna()]
    obs["observed_at"] = obs["observed_at"].astype(str).str[:10]
    obs_pn = obs[obs["part_no"].notna()].copy()
    obs_pn["part_no"] = pn10(obs_pn["part_no"])

    pl = pd.read_parquet(PRICELIST, columns=["part_number", "sp_eur", "valid_start", "valid_end", "description",
                                             "source_file"])
    pl = pl[(pl["valid_start"] <= TODAY) & (pl["valid_end"] >= TODAY) & (pl["sp_eur"] > 0)]
    pl = pl.sort_values("valid_start").drop_duplicates("part_number", keep="last").set_index("part_number")
    list_eur = pl["sp_eur"]
    list_desc = pl["description"]
    list_file = str(pl["source_file"].mode().iat[0]) if len(pl) else ""

    t = pd.read_csv(TIERS, dtype={"part_no": str})
    t = t[t["part_no"].str.fullmatch(r"\d{10}")].copy()           # drops transport and other non-parts
    t["billed_eur_t12m"] = pd.to_numeric(t["billed_eur_t12m"])
    tmeta = json.loads(TIERS_META.read_text(encoding="utf-8")) if TIERS_META.exists() else {}

    cat = pd.read_csv(CATALOG, dtype=str, usecols=["part_number", "pms_category", "pr00_family"])
    cat = cat.drop_duplicates("part_number").set_index("part_number")
    fam = cat["pms_category"].where(cat["pms_category"].notna() & (cat["pms_category"].str.strip() != ""))
    fam = fam.map(lambda x: nice_family(x) if isinstance(x, str) else None)
    fam = fam.fillna(cat["pr00_family"].map(lambda x: f"{x} (other)" if isinstance(x, str) else None))

    g = pd.read_csv(GRADED, dtype=str)
    usable_pn = set(g[g["tier"].isin(["confirmed", "likely"])]["part_no"])
    # Jerome 4 Oct 2026: a number seen only on one Spareto page (edge_origin spareto_only, always
    # graded doubtful, upstream source unstated) is not "on file" for the coverage funnel; it is
    # counted on its own line instead, so the funnel is not inflated by single-source data.
    if "edge_origin" in g.columns:
        any_edge_pn = set(g[g["edge_origin"] != "spareto_only"]["part_no"])
        spareto_only_pn = set(g[g["edge_origin"] == "spareto_only"]["part_no"]) - any_edge_pn
    else:
        any_edge_pn = set(g["part_no"])
        spareto_only_pn = set()
    usable_cpn_n = g[g["tier"].isin(["confirmed", "likely"])].groupby("part_no")["competitor_pn"].nunique()

    lmeta = json.loads(LEDGER_META.read_text(encoding="utf-8")) if LEDGER_META.exists() else {}

    # ── per-observation payload ───────────────────────────────────────────────
    def vat_rate(row):
        return VAT.get(str(row["country"])) if row["vat"] == "incl" else None

    obs["vat_rate"] = obs.apply(vat_rate, axis=1)
    cols = ["part_no", "grp", "price_type", "source", "country", "observed_at", "price", "currency",
            "price_eur", "competitor_brand", "competitor_pn", "vat", "vat_rate", "source_url", "loader", "stock"]
    O = []
    for r in obs[cols].itertuples(index=False):
        pn = None if r.part_no is None or (isinstance(r.part_no, float) and math.isnan(r.part_no)) else str(r.part_no)
        O.append([
            pn, r.grp, r.price_type, r.source, r.country, r.observed_at, r2(r.price), r.currency,
            r2(r.price_eur), None if pd.isna(r.competitor_brand) else str(r.competitor_brand),
            None if pd.isna(r.competitor_pn) else str(r.competitor_pn), r.vat,
            None if pd.isna(r.vat_rate) else r.vat_rate,
            None if pd.isna(r.source_url) else str(r.source_url), r.loader,
            None if pd.isna(r.stock) else r.stock,
        ])

    # ── per-part payload (every part with an observation, plus the Tier A hunt list) ──
    billed = t.set_index("part_no")["billed_eur_t12m"]
    tier = t.set_index("part_no")["tier"]
    observed_pns = sorted(set(obs_pn["part_no"]))
    am_pns = set(obs_pn[obs_pn["grp"].isin(["street", "rrp", "trade"])]["part_no"])
    hunt = t[(t["tier"] == "A") & ~t["part_no"].isin(am_pns)].sort_values("billed_eur_t12m", ascending=False)
    gen_pns = set(obs_pn[obs_pn["grp"] == "genuine"]["part_no"])

    def part_row(pn):
        return {
            "pn": pn,
            "d": str(list_desc.get(pn, "") or ""),
            "f": fam.get(pn) or "Not classified",
            "t": tier.get(pn, ""),
            "b": r2(billed.get(pn)) or 0,
            "l": r2(list_eur.get(pn)),
            "x": 2 if pn in usable_pn else (1 if pn in any_edge_pn else (3 if pn in spareto_only_pn else 0)),
            "xn": int(usable_cpn_n.get(pn, 0)),
        }

    P = [part_row(pn) for pn in observed_pns]
    H = []
    for r in hunt.head(60).itertuples(index=False):
        row = part_row(r.part_no)
        row["g"] = r.part_no in gen_pns
        H.append(row)

    # ── coverage funnel over billed parts ─────────────────────────────────────
    tot = float(t["billed_eur_t12m"].sum())
    fresh_cut = (TODAY - pd.Timedelta(days=365)).strftime("%Y-%m-%d")
    am_fresh = set(obs_pn[obs_pn["grp"].isin(["street", "rrp", "trade"]) & (obs_pn["observed_at"] >= fresh_cut)]["part_no"])
    steps = [
        ("Billed in the last 12 months", set(t["part_no"])),
        ("Competitor number on file", any_edge_pn),
        ("…of which a trusted competitor number", usable_pn),
        ("Any price observed", set(obs_pn["part_no"])),
        ("Aftermarket price observed", am_pns),
        ("Aftermarket price seen in the last 12 months", am_fresh),
        # last on purpose: the page text reads funnel rows by position (F[3], F[4], F[5])
        ("Memo: single-source number only (Spareto)", spareto_only_pn),
    ]
    funnel = []
    for name, S in steps:
        m = t["part_no"].isin(S)
        row = {"step": name, "parts": int(m.sum()), "value_pct": round(100 * t.loc[m, "billed_eur_t12m"].sum() / tot, 1)}
        for k in ("A", "B", "C"):
            mk = m & (t["tier"] == k)
            row[k] = int(mk.sum())
            row[k + "_all"] = int((t["tier"] == k).sum())
        funnel.append(row)

    # ── sources ───────────────────────────────────────────────────────────────
    S = []
    for loader, gdf in obs.groupby("loader"):
        name, status, note = SOURCE_STATUS.get(loader, (loader, "unknown", ""))
        S.append({
            "loader": loader, "name": name, "status": status, "note": note,
            "rows": int(len(gdf)), "parts": int(gdf["part_no"].dropna().nunique()),
            "first": str(gdf["observed_at"].min()), "last": str(gdf["observed_at"].max()),
            "groups": sorted(set(gdf["grp"])),
        })
    S.sort(key=lambda s: ({"live": 0, "file": 1, "category": 2, "thin": 3, "retired": 4}.get(s["status"], 5), -s["rows"]))

    # Re-checked prices. The movement file repeats some rows verbatim (same part, offer, dates and
    # prices listed twice); those are counted once, as the 1 Aug page did with repeat-reported moves.
    moves = []
    if MOVES.exists():
        mv = pd.read_csv(MOVES, dtype={"part_no": str})
        keep = ["part_no", "source", "price_type", "currency", "first_date", "first_price", "last_date",
                "last_price", "change_pct", "n_observations", "description", "offer"]
        mv = mv[[c for c in keep if c in mv.columns]].drop_duplicates()
        moves = [{k: (None if (isinstance(v, float) and math.isnan(v)) else v) for k, v in m.items()}
                 for m in mv.to_dict("records")]

    # Run calendar: on which days did each source write prices (last 21 days). This is what the
    # data shows was written, not the schedule.
    cal_from = (TODAY - pd.Timedelta(days=20)).strftime("%Y-%m-%d")
    recent = obs[obs["observed_at"] >= cal_from]
    calendar = {
        "days": [(TODAY - pd.Timedelta(days=i)).strftime("%Y-%m-%d") for i in range(20, -1, -1)],
        "rows": [{"loader": ld, "name": SOURCE_STATUS.get(ld, (ld,))[0] + CAL_SUFFIX.get(ld, ""),
                  "by_day": {d: int(n) for d, n in gdf.groupby("observed_at").size().items()}}
                 for ld, gdf in recent.groupby("loader")],
    }
    calendar["rows"].sort(key=lambda r: -sum(r["by_day"].values()))

    # Search yield: how many of our part numbers were looked up per site, and how many came back priced.
    yld = []
    if KS_WEEKLY.exists():
        k = pd.read_csv(KS_WEEKLY, dtype={"PN": str})
        yld.append({"site": "KS International (weekly run file)", "searched": int(k["PN"].nunique()),
                    "priced": int(k.loc[k["Status"] == "ok", "PN"].nunique()),
                    "last": str(k["Scraped_At"].astype(str).str[:10].max())})
    if MANIFEST.exists():
        man = pd.read_csv(MANIFEST, dtype=str)
        man["pn"] = man["source_url"].astype(str).str.extract(r"(\d{10})", expand=False)
        for site, gdf in man.groupby("site"):
            looked = set(gdf["pn"].dropna())
            if not looked:
                continue
            priced = set(obs_pn.loc[obs_pn["loader"] == site, "part_no"]) & looked
            yld.append({"site": f"{SOURCE_STATUS.get(site, (site,))[0]} (page runs)", "searched": len(looked),
                        "priced": len(priced), "last": str(gdf["fetched_at"].dropna().astype(str).str[:10].max())})

    # VAT: which markets have a VAT-inclusive price at all, so the page can say what the strip touches.
    vat_use = []
    for cty, gdf in obs.groupby("country"):
        vc = gdf["vat"].value_counts()
        vat_use.append({"country": str(cty), "rate": VAT.get(str(cty)), "incl": int(vc.get("incl", 0)),
                        "excl": int(vc.get("excl", 0)), "unknown": int(vc.get("unknown", 0))})
    vat_use.sort(key=lambda r: -(r["incl"] + r["excl"] + r["unknown"]))

    data = {
        "built": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "today": TODAY.strftime("%Y-%m-%d"),
        "ledger_built": lmeta.get("built_at", ""),
        "price_list_file": list_file,
        "billed_window": tmeta.get("window", ""),
        "billed_total": round(tot),
        "ref_multiple": REF_MULTIPLE,
        "group_label": GROUP_LABEL,
        "vat": VAT,
        "funnel": funnel,
        "parts": P,
        "hunt": H,
        "hunt_total": int(len(hunt)),
        "hunt_value_pct": round(100 * hunt["billed_eur_t12m"].sum() / tot, 1),
        "obs": O,
        "sources": S,
        "moves": moves,
        "fresh_cut": fresh_cut,
        "calendar": calendar,
        "yield": yld,
        "vat_use": vat_use,
        "vat_source": VAT_SOURCE,
        "ledger_rows": int(lmeta.get("rows", 0)),
        "min_n": MIN_N,
    }

    chartjs = CHARTJS.read_text(encoding="utf-8")
    chartjs = "\n".join(l for l in chartjs.splitlines() if not l.startswith("//# sourceMappingURL"))
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = TEMPLATE.replace("/*__CHARTJS__*/", chartjs).replace("/*__DATA__*/null", payload)
    OUT.write_text(html, encoding="utf-8")
    OPEN_CMD.write_text('@echo off\r\nstart "" "%~dp0ISZE_Parts_Price_Intelligence.html"\r\n', encoding="utf-8")

    print(f"parts with an observation : {len(P)}")
    print(f"observations              : {len(O)}")
    print(f"Tier A hunt list          : {len(hunt)} parts, {data['hunt_value_pct']}% of billed value")
    for f in funnel:
        print(f"   {f['step']:<46} {f['parts']:>6}  {f['value_pct']:>5.1f}% of billed value")
    print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes)")
    print(f"wrote {OPEN_CMD}")
    return 0


TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ISZE Parts Price Intelligence</title>
<style>
:root{--navy:#1a2b4a;--navy2:#2b4a78;--terra:#c0552d;--paper:#f7f4ee;--line:#d9d3c8;--muted:#6b6256;--ink:#222;
--red:#e24b4a;--amber:#eda100;--green:#1d9e75;--blue:#2a78d6;--grey:#888780;--bg:#fff;--card:#fff}
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:var(--bg);color:var(--ink);font:14px/1.5 "Segoe UI",Helvetica,Arial,sans-serif}
h1,h2,h3{font-family:Georgia,"Times New Roman",serif;color:var(--navy);margin:0}
header.cover{background:linear-gradient(155deg,#15233c 0%,#203759 60%,#2b4a78 100%);color:#eef1f6;padding:30px 0 26px}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px}
header.cover h1{color:#fff;font-size:32px;line-height:1.1}
header.cover .rule{width:120px;height:3px;background:var(--terra);margin:14px 0 12px}
header.cover .sub{color:#c9d3e3;font-size:13px}
header.cover .lead{font-size:15.5px;max-width:880px;margin-top:10px;color:#eef1f6}
.controls{position:sticky;top:0;z-index:5;background:#fff;border-bottom:1px solid var(--line);padding:9px 0}
.controls .wrap{display:flex;flex-wrap:wrap;gap:14px;align-items:center;font-size:13px}
.controls label{color:var(--muted)}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:6px;overflow:hidden}
.seg button{border:0;background:#fff;padding:5px 10px;font:inherit;cursor:pointer;color:var(--ink)}
.seg button.on{background:var(--navy);color:#fff}
select,input[type=search]{font:inherit;padding:4px 8px;border:1px solid var(--line);border-radius:6px;background:#fff}
section{padding:26px 0 6px}
h2.sec{font-size:21px;padding-bottom:6px;border-bottom:2px solid var(--navy);margin-bottom:6px}
h2.sec .no{color:var(--terra)}
p.q{margin:4px 0 12px;color:var(--muted);max-width:900px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px;margin:18px 0 4px}
.tile{background:var(--paper);border-radius:8px;padding:12px 14px;border-left:3px solid var(--navy)}
.tile.warn{border-left-color:var(--terra)}
.tile .v{font-size:26px;font-weight:600;color:var(--navy);font-family:Georgia,serif}
.tile .l{font-size:12.5px;color:var(--ink);margin-top:2px}
.tile .n{font-size:11.5px;color:var(--muted);margin-top:4px}
.grid2{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:18px}
@media(max-width:900px){.grid2{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:14px 16px}
.card h3{font-size:15.5px;margin-bottom:2px}
.card .h{font-size:12.5px;color:var(--muted);margin-bottom:8px}
.chart{position:relative;width:100%}
.callout{border-left:3px solid var(--terra);background:var(--paper);padding:10px 14px;margin:12px 0;font-size:13.5px}
table{width:100%;border-collapse:collapse;font-size:12.8px}
th{background:var(--navy);color:#fff;text-align:left;padding:6px 8px;font-weight:600;font-size:11.5px;position:sticky;top:44px;cursor:pointer;white-space:nowrap}
td{padding:5px 8px;border-bottom:1px solid var(--line);vertical-align:top}
tbody tr:nth-child(even){background:#fbf9f5}
td.r,th.r{text-align:right}
.chip{display:inline-block;padding:1px 7px;border-radius:10px;font-size:11px;border:1px solid var(--line);background:#fff;white-space:nowrap}
.chip.live{border-color:#1d9e75;color:#17785a}.chip.file{border-color:#2a78d6;color:#1f5ea8}
.chip.thin,.chip.category{border-color:#eda100;color:#8a6000}.chip.retired{border-color:#b23b3b;color:#b23b3b}
.chip.red{background:#fdecec;border-color:#e24b4a;color:#a12f2e}.chip.amber{background:#fff5df;border-color:#eda100;color:#7a5600}
.chip.green{background:#e6f5ef;border-color:#1d9e75;color:#17785a}.chip.grey{color:var(--muted)}
.dash{color:var(--muted)}
.tablewrap{max-height:560px;overflow:auto;border:1px solid var(--line);border-radius:6px}
.tablewrap th{top:0}
#drill{display:none;margin-top:14px}
#drill.on{display:block}
.legend{display:flex;flex-wrap:wrap;gap:12px;font-size:12px;color:var(--muted);margin:4px 0 8px}
.legend i{display:inline-block;width:11px;height:11px;border-radius:2px;margin-right:5px;vertical-align:-1px}
svg text{font-family:"Segoe UI",Helvetica,Arial,sans-serif}
footer{margin:34px 0 40px;padding-top:10px;border-top:1px solid var(--line);font-size:12px;color:var(--muted)}
a{color:var(--navy2)}
.defs{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:8px;margin:6px 0 4px}
.def{border:1px solid var(--line);border-radius:6px;padding:8px 10px;background:#fff;cursor:help}
.def b{display:block;font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--navy)}
.def .f{font-family:Consolas,monospace;font-size:11.5px;color:var(--terra);margin:2px 0}
.def .p{font-size:11.8px;color:var(--muted)}
table.cal td,table.cal th{padding:3px 4px;text-align:center;font-size:11px}
table.cal th{position:static;cursor:default}
table.cal td.nm{text-align:left;white-space:nowrap;font-size:12px}
.dot{display:inline-block;width:10px;height:10px;border-radius:50%;background:#1d9e75}
[data-ex]{cursor:help}
.tip{position:fixed;pointer-events:none;background:#15233c;color:#fff;font-size:12px;padding:6px 8px;border-radius:5px;max-width:320px;display:none;z-index:20}
</style></head><body>

<header class="cover"><div class="wrap">
  <h1>Parts Price Intelligence</h1>
  <div class="rule"></div>
  <div class="sub" id="sub"></div>
  <div class="lead" id="lead"></div>
  <div class="tiles" id="tiles" style="color:var(--ink)"></div>
</div></header>

<div class="controls"><div class="wrap">
  <label>Compare against</label>
  <span class="seg" id="basis"><button data-v="ref" class="on" title="Our price list x 2.19: the reference dealer price on the margins reading (D03)">Reference dealer price</button><button data-v="list" title="Our price list (PR00), before distributor and dealer margins">Our price list</button></span>
  <label>Rival price</label>
  <span class="seg" id="grp"><button data-v="street" class="on">Shop price</button><button data-v="rrp">Brand list price</button><button data-v="trade">Trade</button></span>
  <label>Prices dated</label>
  <span class="seg" id="age"><button data-v="12m" class="on" title="Only prices dated in the last 12 months. Keeps the Eucon PartsPool file of March 2026 and the live searches.">last 12 months</button><button data-v="all" title="Every price we hold, including Eucon files from 2023 and 2024 and brand list prices dated back to 2002">all dates</button></span>
  <label><input type="checkbox" id="vat" checked> strip VAT where a price includes it</label>
  <label>Tier</label>
  <select id="tier"><option value="">All billed</option><option>A</option><option>B</option><option>C</option></select>
</div></div>

<div class="wrap">

<section id="s1">
  <h2 class="sec"><span class="no">1</span> How much of our business can we price against a rival?</h2>
  <p class="q">Each bar is a share of what we billed in the last 12 months. Read it top to bottom: every step needs the one above it.</p>
  <div class="grid2">
    <div class="card"><h3>Coverage, by share of billed value</h3><div class="h" id="funnel-h"></div>
      <div class="chart" style="height:300px"><canvas id="cFunnel" role="img" aria-label="Coverage funnel by share of billed value"></canvas></div></div>
    <div class="card"><h3>Parts with an aftermarket price, by tier</h3><div class="h">Tier A is the top part numbers that make 62% of billed value</div>
      <div class="chart" style="height:300px"><canvas id="cTier" role="img" aria-label="Share of parts with an aftermarket price per tier"></canvas></div></div>
  </div>
  <div class="callout" id="funnel-call"></div>
</section>

<section id="s2">
  <h2 class="sec"><span class="no">2</span> Where do rivals sit against our price?</h2>
  <p class="q" id="pos-q"></p>
  <div class="defs" id="defs"></div>
  <div class="tiles" id="posTiles"></div>
  <div class="grid2">
    <div class="card"><h3>Price index per parts family</h3><div class="h" id="fam-h"></div>
      <div class="legend"><span><i style="background:#e24b4a"></i>rival below 80%: strong pressure</span><span><i style="background:#eda100"></i>80–100%: close</span><span><i style="background:#1d9e75"></i>above 100%: we are cheaper</span><span><i style="background:#cfccc4"></i>fewer than 3 parts: directional only</span></div>
      <div class="chart" id="famWrap"><canvas id="cFam" role="img" aria-label="Median price index per parts family"></canvas></div></div>
    <div class="card"><h3>How the index spreads, per price type</h3><div class="h" id="dist-h">Share of observations in each band. Each price type is kept apart; they are never averaged together.</div>
      <div class="chart" style="height:340px"><canvas id="cDist" role="img" aria-label="Distribution of price index per price type"></canvas></div></div>
  </div>
  <div class="grid2" style="margin-top:18px">
    <div class="card"><h3>Aftermarket brands we see most</h3><div class="h" id="brand-h"></div>
      <div class="chart" id="brandWrap"><canvas id="cBrand" role="img" aria-label="Aftermarket brands by number of our parts they cover"></canvas></div></div>
    <div class="card"><h3>Where each source sits</h3><div class="h" id="src-h"></div>
      <div class="chart" id="srcWrap"><canvas id="cSrc" role="img" aria-label="Median price index per source and market"></canvas></div></div>
  </div>
</section>

<section id="s3">
  <h2 class="sec"><span class="no">3</span> Same shelf: genuine against aftermarket at one shop</h2>
  <p class="q">KS International (UK) lists many of our part numbers twice: a genuine Isuzu part and an aftermarket part. Putting both against our comparison price on the same shelf shows how wide the gap between the two channels is. This is genuine against aftermarket at one shop, not ISZE against KS.</p>
  <div class="tiles" id="shelfTiles"></div>
  <div class="card"><h3>Genuine and aftermarket on the same shelf</h3><div class="h" id="shelf-h"></div>
    <div class="legend"><span><i style="background:#c0552d"></i>genuine at KS</span><span><i style="background:#2a78d6"></i>aftermarket at KS</span><span><i style="background:#15233c;width:2px"></i>our comparison price = 100%</span></div>
    <div id="shelf"></div></div>
</section>

<section id="s4">
  <h2 class="sec"><span class="no">4</span> Which high-value parts are most exposed?</h2>
  <p class="q">Each dot is one of our parts with a rival price. Right = more billed. Down = the rival is cheaper. The parts in the shaded lower-right corner carry the most business at the lowest rival price; the ten largest are ringed and listed.</p>
  <div class="grid2">
    <div class="card"><h3>Billed value against price index</h3><div class="h" id="sc-h"></div><div id="scatter"></div></div>
    <div class="card"><h3>The ten most exposed</h3><div class="h">Largest billed value with the rival below 100% of our comparison price</div><div id="expo"></div></div>
  </div>
</section>

<section id="s5">
  <h2 class="sec"><span class="no">5</span> How fresh is what we know, and which sources still deliver?</h2>
  <p class="q">A price is only useful while it is current. Most of what we hold comes from files, not from live searching.</p>
  <div class="grid2">
    <div class="card"><h3>Observations by the year the price was dated</h3><div class="h">Brand list prices carry their own date, some of them years old</div>
      <div class="chart" style="height:300px"><canvas id="cYear" role="img" aria-label="Observations per year by price type"></canvas></div></div>
    <div class="card"><h3>Sources</h3><div class="h">Live = searched on a schedule. File = a one-off file. Thin = cannot be searched by part number.</div>
      <div class="tablewrap" style="max-height:330px"><table id="srcT"></table></div></div>
  </div>
  <div class="card" style="margin-top:18px"><h3>Did each source write prices, day by day?</h3><div class="h" id="cal-h"></div>
    <div style="overflow-x:auto"><table id="calT" class="cal"></table></div></div>
  <div class="grid2" style="margin-top:18px">
    <div class="card"><h3>Search yield</h3><div class="h">Of the part numbers we looked up at each site, how many came back with a price for that part</div>
      <div class="tablewrap" style="max-height:360px"><table id="yldT"></table></div></div>
    <div class="card"><h3>VAT applied per market</h3><div class="h" id="vat-h"></div>
      <div class="tablewrap" style="max-height:360px"><table id="vatT"></table></div></div>
  </div>
  <div class="card" style="margin-top:18px"><h3>Price moves on re-checked prices</h3><div class="h" id="mv-h"></div>
    <div class="tiles" id="mvTiles" style="margin-top:6px"></div>
    <div class="tablewrap" style="max-height:360px"><table id="mvT"></table></div></div>
</section>

<section id="s6">
  <h2 class="sec"><span class="no">6</span> Where should the next search go?</h2>
  <p class="q" id="hunt-q"></p>
  <div class="tablewrap"><table id="huntT"></table></div>
</section>

<section id="s7">
  <h2 class="sec"><span class="no">7</span> Any part, every observation</h2>
  <p class="q">Search a part number or a description. The date switch at the top applies here too. The columns Shop, Brand list, Trade and Genuine show each part's median price index against the comparison price chosen at the top. Click a row to see every price we hold for it, with its source, date and VAT basis.</p>
  <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:8px">
    <input type="search" id="q" placeholder="part number or description" style="min-width:260px">
    <select id="famSel"><option value="">All families</option></select>
    <label style="font-size:13px;color:var(--muted)"><input type="checkbox" id="onlyAm"> only parts with an aftermarket price</label>
    <span id="cnt" style="font-size:13px;color:var(--muted);align-self:center"></span>
  </div>
  <div class="tablewrap"><table id="partT"></table></div>
  <div id="drill" class="card"></div>
</section>

<footer id="foot"></footer>
</div>
<div class="tip" id="tip"></div>

<script>/*__CHARTJS__*/</script>
<script>
const DATA=/*__DATA__*/null;
const OI={pn:0,grp:1,type:2,src:3,cty:4,date:5,price:6,cur:7,eur:8,brand:9,cpn:10,vat:11,vr:12,url:13,loader:14,stock:15};
const ST={basis:"ref",grp:"street",vat:true,tier:"",age:"12m"};
const C={};
const fmtE=(v,d=0)=>v==null?"—":"€"+Number(v).toLocaleString("en-GB",{minimumFractionDigits:d,maximumFractionDigits:d});
const fmtP=v=>v==null?"—":Math.round(v*100)+"%";
const esc=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const fmtD=s=>{if(!s)return"—";const d=new Date(s+"T00:00:00");return isNaN(d)?s:d.toLocaleDateString("en-GB",{day:"numeric",month:"short",year:"numeric"});};
const PART=Object.fromEntries(DATA.parts.map(p=>[p.pn,p]));
const OBS_BY=new Map();DATA.obs.forEach(o=>{if(o[OI.pn]){if(!OBS_BY.has(o[OI.pn]))OBS_BY.set(o[OI.pn],[]);OBS_BY.get(o[OI.pn]).push(o);}});
const median=a=>{if(!a.length)return null;const s=[...a].sort((x,y)=>x-y),m=s.length>>1;return s.length%2?s[m]:(s[m-1]+s[m])/2;};
const bandColor=r=>r==null?"#888780":r<0.8?"#e24b4a":r<1?"#eda100":"#1d9e75";
const bandChip=r=>r==null?`<span class="chip grey">no list price</span>`:`<span class="chip ${r<0.8?"red":r<1?"amber":"green"}">${fmtP(r)}</span>`;

function eurOf(o){let e=o[OI.eur];if(ST.vat&&o[OI.vat]==="incl"&&o[OI.vr])e=e/(1+o[OI.vr]);return e;}
function compOf(p){if(!p||!p.l)return null;return ST.basis==="ref"?p.l*DATA.ref_multiple:p.l;}
function ratioOf(o){const p=PART[o[OI.pn]];const c=compOf(p);return c?eurOf(o)/c:null;}
function inTier(p){return !ST.tier||p.t===ST.tier;}
function okDate(o){return ST.age==="all"||String(o[OI.date])>=DATA.fresh_cut;}
const ageLabel=()=>ST.age==="all"?"all dates":`prices dated since ${fmtD(DATA.fresh_cut)}`;
function partRatio(pn,grp){const os=(OBS_BY.get(pn)||[]).filter(o=>o[OI.grp]===grp&&okDate(o));const rs=os.map(ratioOf).filter(x=>x!=null);return rs.length?median(rs):null;}
const basisLabel=()=>ST.basis==="ref"?`reference dealer price (our price list × ${DATA.ref_multiple})`:"our price list";

/* ── header ── */
function header(){
  const F=DATA.funnel;const am=F[4],fr=F[5],tn=F[2];
  document.getElementById("sub").textContent=`Internal · built ${DATA.built} · price data built ${DATA.ledger_built.slice(0,16).replace("T"," ")} UTC (${DATA.ledger_rows.toLocaleString("en-GB")} rows) · billed window ${DATA.billed_window}`;
  document.getElementById("lead").innerHTML=`We hold <b>${DATA.obs.length.toLocaleString("en-GB")}</b> observed prices on <b>${DATA.parts.length}</b> of our part numbers. An aftermarket price exists for parts worth <b>${am.value_pct}%</b> of what we billed in the last 12 months, and only <b>${fr.value_pct}%</b> has one dated in the last year.`;
  const live=DATA.sources.filter(s=>s.status==="live").map(s=>s.name);
  const T=[
    [`${am.value_pct}%`,"of billed value has an aftermarket price",`${am.parts} part numbers of ${F[0].parts.toLocaleString("en-GB")} billed`,false],
    [`${fr.value_pct}%`,"has one dated in the last 12 months",`since ${fmtD(DATA.fresh_cut)}`,true],
    [`${tn.parts}`,"parts with a trusted competitor number",`${tn.value_pct}% of billed value; the base for searching by competitor number`,true],
    [`${DATA.hunt_total}`,"Tier A parts with no aftermarket price",`${DATA.hunt_value_pct}% of billed value; section 6`,true],
    [`${[...new Set(live)].length}`,"sources searched live",[...new Set(live)].join(", "),false],
  ];
  document.getElementById("tiles").innerHTML=T.map(t=>`<div class="tile ${t[3]?"warn":""}"><div class="v">${t[0]}</div><div class="l">${t[1]}</div><div class="n">${esc(t[2])}</div></div>`).join("");
}

/* ── section 1 ── */
function s1(){
  const F=DATA.funnel;
  document.getElementById("funnel-h").textContent=`100% = ${fmtE(DATA.billed_total)} billed across ${F[0].parts.toLocaleString("en-GB")} part numbers`;
  const cols=["#1a2b4a","#2b4a78","#85b7eb","#888780","#2a78d6","#c0552d","#b4b2a9"];
  C.funnel=new Chart(cFunnel,{type:"bar",data:{labels:F.map(f=>f.step),datasets:[{data:F.map(f=>f.value_pct),backgroundColor:cols,borderRadius:4,barThickness:24}]},
    options:{indexAxis:"y",maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>` ${c.raw}% of billed value · ${F[c.dataIndex].parts.toLocaleString("en-GB")} parts`}}},
      scales:{x:{min:0,max:112,afterBuildTicks:a=>{a.ticks=[0,25,50,75,100].map(v=>({value:v}));},ticks:{callback:v=>v+"%"},grid:{color:"#ece8e0"}},y:{grid:{display:false},ticks:{font:{size:11.5}}}}},
    plugins:[{id:"vals",afterDatasetsDraw(ch){const c=ch.ctx;c.save();c.font="600 11.5px Segoe UI";c.fillStyle="#222";ch.getDatasetMeta(0).data.forEach((b,i)=>{c.fillText(F[i].value_pct+"%",b.x+6,b.y+4);});c.restore();}}]});
  const am=F[4];
  C.tier=new Chart(cTier,{type:"bar",data:{labels:["Tier A","Tier B","Tier C"],datasets:[
    {label:"aftermarket price",data:["A","B","C"].map(k=>100*am[k]/am[k+"_all"]),backgroundColor:"#2a78d6",borderRadius:4,barThickness:44},
  ]},options:{maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>{const k="ABC"[c.dataIndex];return ` ${am[k]} of ${am[k+"_all"].toLocaleString("en-GB")} parts`;}}}},
    scales:{y:{min:0,max:30,ticks:{callback:v=>v+"%",stepSize:10},grid:{color:"#ece8e0"}},x:{grid:{display:false}}}},
    plugins:[{id:"vals",afterDatasetsDraw(ch){const c=ch.ctx;c.save();c.font="600 12px Segoe UI";c.fillStyle="#222";c.textAlign="center";ch.getDatasetMeta(0).data.forEach((b,i)=>{const k="ABC"[i];c.fillText(`${(100*am[k]/am[k+"_all"]).toFixed(1)}%  (${am[k]})`,b.x,b.y-7);});c.restore();}}]});
  const any=F[3];
  document.getElementById("funnel-call").innerHTML=`<b>Reading it.</b> Any price exists for ${any.value_pct}% of billed value, but much of that is a genuine Isuzu part sold outside our network. That is not a rival. Aftermarket brands reach ${am.value_pct}%. The trusted competitor numbers reach only ${F[2].value_pct}%, so searching by competitor number cannot close the gap by itself. Tier A with an aftermarket price: ${am.A} of ${am.A_all}.`;
}

/* ── section 2 ── */
function famRows(){
  const by={};
  DATA.parts.forEach(p=>{if(!inTier(p))return;const r=partRatio(p.pn,ST.grp);if(r==null)return;(by[p.f]=by[p.f]||[]).push(r);});
  return Object.entries(by).map(([f,a])=>({f,n:a.length,m:median(a),q1:quant(a,.25),q3:quant(a,.75)})).sort((a,b)=>a.m-b.m);
}
const quant=(a,q)=>{if(!a.length)return null;const s=[...a].sort((x,y)=>x-y),i=(s.length-1)*q,lo=Math.floor(i),hi=Math.ceil(i);return s[lo]+(s[hi]-s[lo])*(i-lo);};
function spearman(xs,ys){const n=xs.length;if(n<5)return null;const rk=a=>{const idx=a.map((v,i)=>[v,i]).sort((p,q)=>p[0]-q[0]);const r=new Array(n);let i=0;while(i<n){let j=i;while(j+1<n&&idx[j+1][0]===idx[i][0])j++;for(let k=i;k<=j;k++)r[idx[k][1]]=(i+j)/2+1;i=j+1;}return r;};
  const rx=rk(xs),ry=rk(ys),mx=(n+1)/2;let sxy=0,sxx=0,syy=0;for(let i=0;i<n;i++){sxy+=(rx[i]-mx)*(ry[i]-mx);sxx+=(rx[i]-mx)**2;syy+=(ry[i]-mx)**2;}return sxy/Math.sqrt(sxx*syy);}
/* worked arithmetic for one observation: what the index is made of */
function howBuilt(o){
  const p=PART[o[OI.pn]]||{};const c=compOf(p);const e0=o[OI.eur],e=eurOf(o);
  const L=[`<b>How this index is built · ${esc(o[OI.pn])}</b>`];
  L.push(`1. Our price list: ${fmtE(p.l,2)}`);
  if(ST.basis==="ref")L.push(`2. × ${DATA.ref_multiple} = reference dealer price ${fmtE(c,2)} <span style="color:#c9d3e3">(provisional fixed basis, same for every market)</span>`);
  else L.push(`2. Compared against the price list itself: ${fmtE(c,2)}`);
  L.push(`3. Rival price: ${o[OI.price]} ${esc(o[OI.cur])} · ${esc(o[OI.src])}, ${esc(o[OI.cty])}, ${fmtD(o[OI.date])}`);
  L.push(`4. In euro (dated ECB rate stored with the price): ${fmtE(e0,2)}`);
  if(o[OI.vat]==="incl")L.push(ST.vat&&o[OI.vr]?`5. VAT-inclusive: ÷ ${(1+o[OI.vr]).toFixed(3)} (${o[OI.cty]} ${Math.round(o[OI.vr]*1000)/10}%) = ${fmtE(e,2)}`:`5. VAT-inclusive, kept as is (strip switched off or no rate for ${esc(o[OI.cty])})`);
  else if(o[OI.vat]==="excl")L.push(`5. Price is ex VAT: nothing removed`);
  else L.push(`5. Source does not state VAT: used as recorded`);
  L.push(c?`6. Index = ${fmtE(e,2)} ÷ ${fmtE(c,2)} = <b>${fmtP(e/c)}</b>`:`6. No current price-list price: no index`);
  return L.join("<br>");
}
function partBuilt(p,r,grp){const c=compOf(p);if(!c||r==null)return"";
  return `<b>${esc(p.pn)} · ${esc(DATA.group_label[grp])}</b><br>1. Our price list: ${fmtE(p.l,2)}<br>`+
    (ST.basis==="ref"?`2. × ${DATA.ref_multiple} = reference dealer price ${fmtE(c,2)}<br>`:`2. Compared against the price list itself<br>`)+
    `3. Each rival price for this part ÷ ${fmtE(c,2)}, VAT handled per price (click the row for each one)<br>4. Median of those indexes = <b>${fmtP(r)}</b> ≈ rival ${fmtE(c*r,2)}`;}
function s2(){
  const rows=famRows();
  document.getElementById("pos-q").innerHTML=`Price index = rival price ÷ ${basisLabel()}. Below 100% the rival is cheaper. Shown: <b>${esc(DATA.group_label[ST.grp])}</b>${ST.vat?", VAT removed where the price includes it":""}. One value per part (its median), then the median across the family's parts. Using <b>${ageLabel()}</b>.`;
  const MN=DATA.min_n;
  document.getElementById("fam-h").textContent=`Every family with a priced part · ${rows.reduce((a,r)=>a+r.n,0)} parts · grey = fewer than ${MN} parts, directional only`;
  document.getElementById("famWrap").style.height=Math.max(200,rows.length*30+70)+"px";
  if(C.fam)C.fam.destroy();
  const mx=Math.max(1.2,...rows.map(r=>r.m))*1.12;
  C.fam=new Chart(cFam,{type:"bar",data:{labels:rows.map(r=>`${r.f} (${r.n})`),datasets:[{data:rows.map(r=>+(r.m*100).toFixed(0)),backgroundColor:rows.map(r=>r.n<MN?"#cfccc4":bandColor(r.m)),borderRadius:3,barThickness:20}]},
    options:{indexAxis:"y",maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>{const r=rows[c.dataIndex];return [` median index ${c.raw}% over ${r.n} part${r.n>1?"s":""}`,` middle half of parts: ${fmtP(r.q1)} to ${fmtP(r.q3)}`,r.n<MN?` fewer than ${MN} parts: directional only`:` usable sample (${MN} or more parts)`];}}}},
      scales:{x:{min:0,max:Math.ceil(mx*2)*50,ticks:{callback:v=>v+"%",stepSize:50},grid:{color:"#ece8e0"}},y:{grid:{display:false},ticks:{font:{size:11.5}}}}},
    plugins:[{id:"ref",afterDatasetsDraw(ch){const x=ch.scales.x.getPixelForValue(100),c=ch.ctx;c.save();c.strokeStyle="#15233c";c.setLineDash([4,3]);c.beginPath();c.moveTo(x,ch.chartArea.top);c.lineTo(x,ch.chartArea.bottom);c.stroke();c.restore();}}]});

  // distribution per price type
  const bands=[[0,.5,"<50%"],[.5,.8,"50–80%"],[.8,1,"80–100%"],[1,1.25,"100–125%"],[1.25,1.6,"125–160%"],[1.6,99,">160%"]];
  const G=["street","rrp","trade","genuine"],GC={street:"#2a78d6",rrp:"#85b7eb",trade:"#888780",genuine:"#c0552d"};
  const ds=G.map(gk=>{const rs=DATA.obs.filter(o=>o[OI.grp]===gk&&okDate(o)&&o[OI.pn]&&PART[o[OI.pn]]&&inTier(PART[o[OI.pn]])).map(ratioOf).filter(x=>x!=null);
    return{label:`${DATA.group_label[gk]} (${rs.length})`,data:bands.map(b=>rs.length?100*rs.filter(r=>r>=b[0]&&r<b[1]).length/rs.length:0),backgroundColor:GC[gk],borderRadius:2,barPercentage:.86,categoryPercentage:.8};});
  document.getElementById("dist-h").textContent=`Share of observations in each band, ${ageLabel()}. Each price type is kept apart; they are never averaged together.`;
  const dmax=Math.min(100,Math.ceil(Math.max(20,...ds.flatMap(d=>d.data))/20)*20);
  if(C.dist)C.dist.destroy();
  C.dist=new Chart(cDist,{type:"bar",data:{labels:bands.map(b=>b[2]),datasets:ds},options:{maintainAspectRatio:false,
    plugins:{legend:{position:"bottom",labels:{boxWidth:11,font:{size:11}}},tooltip:{callbacks:{label:c=>` ${c.dataset.label.split(" (")[0]}: ${c.raw.toFixed(0)}%`}}},
    scales:{y:{min:0,max:dmax,ticks:{callback:v=>v+"%",stepSize:20},grid:{color:"#ece8e0"}},x:{grid:{display:false}}}}});

  // brands
  const bb={};
  DATA.obs.forEach(o=>{if(o[OI.grp]!==ST.grp||!okDate(o)||!o[OI.brand]||!o[OI.pn])return;const p=PART[o[OI.pn]];if(!p||!inTier(p))return;
    const b=String(o[OI.brand]).split("|")[0].replace(/\s*\(.*\)$/,"").trim().toUpperCase();if(!b)return;(bb[b]=bb[b]||{pn:new Set(),r:[]});bb[b].pn.add(o[OI.pn]);const r=ratioOf(o);if(r!=null)bb[b].r.push(r);});
  const br=Object.entries(bb).map(([b,v])=>({b,n:v.pn.size,m:median(v.r)})).sort((a,b)=>b.n-a.n).slice(0,15);
  document.getElementById("brand-h").textContent=br.length?`Top ${br.length} by number of our parts priced · colour = the brand's median price index · ${DATA.group_label[ST.grp]} · ${ageLabel()}`:"No brand is recorded for this price type";
  document.getElementById("brandWrap").style.height=Math.max(120,br.length*30+60)+"px";
  if(C.brand)C.brand.destroy();
  C.brand=new Chart(cBrand,{type:"bar",data:{labels:br.map(r=>r.b),datasets:[{data:br.map(r=>r.n),backgroundColor:br.map(r=>bandColor(r.m)),borderRadius:3,barThickness:20}]},
    options:{indexAxis:"y",maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>` ${c.raw} parts · median index ${fmtP(br[c.dataIndex].m)}`}}},
      scales:{x:{grace:"10%",ticks:{precision:0},grid:{color:"#ece8e0"},title:{display:true,text:"our parts priced"}},y:{grid:{display:false}}}},
    plugins:[{id:"vals",afterDatasetsDraw(ch){const c=ch.ctx;c.save();c.font="11.5px Segoe UI";c.fillStyle="#222";ch.getDatasetMeta(0).data.forEach((b,i)=>{c.fillText(fmtP(br[i].m),b.x+6,b.y+4);});c.restore();}}]});
}

/* ── section 2 extras: headline indexes and per-source position (ported from the 17 Sep and 1 Aug pages) ── */
function posExtras(){
  const per=g=>DATA.parts.filter(inTier).map(p=>partRatio(p.pn,g)).filter(x=>x!=null);
  const a=per(ST.grp),gn=per("genuine");
  const below=a.filter(r=>r<1).length;
  const T=[
    [a.length?fmtP(median(a)):"—",`median index, ${DATA.group_label[ST.grp].toLowerCase()}`,`one value per part, ${a.length} parts`],
    [a.length?Math.round(100*below/a.length)+"%":"—","of those parts: rival below our comparison price",`${below} of ${a.length} parts`],
    [gn.length?fmtP(median(gn)):"—","median index, genuine Isuzu outside our network",`${gn.length} parts`],
  ];
  document.getElementById("posTiles").innerHTML=T.map(t=>`<div class="tile"><div class="v">${t[0]}</div><div class="l">${esc(t[1])}</div><div class="n">${esc(t[2])} · ${esc(ageLabel())}</div></div>`).join("");
  // per source + market: index per observation, then per part median, then median across parts
  const by={};
  DATA.obs.forEach(o=>{if(o[OI.grp]!==ST.grp||!okDate(o)||!o[OI.pn])return;const p=PART[o[OI.pn]];if(!p||!inTier(p))return;const r=ratioOf(o);if(r==null)return;
    const k=`${o[OI.src]} · ${o[OI.cty]}`;((by[k]=by[k]||{})[o[OI.pn]]=by[k][o[OI.pn]]||[]).push(r);});
  const rows=Object.entries(by).map(([k,v])=>{const m=Object.values(v).map(median);return{k,n:m.length,m:median(m),q1:quant(m,.25),q3:quant(m,.75)};}).sort((a,b)=>b.n-a.n).slice(0,14).sort((a,b)=>a.m-b.m);
  document.getElementById("src-h").textContent=rows.length?`Median index per source and market · ${DATA.group_label[ST.grp]} · ${ageLabel()} · bar label = parts. Different shops carry different parts, so compare the shape, not the ranking.`:"No source holds this price type for the selection";
  document.getElementById("srcWrap").style.height=Math.max(120,rows.length*30+60)+"px";
  if(C.src)C.src.destroy();
  const MN=DATA.min_n;
  C.src=new Chart(cSrc,{type:"bar",data:{labels:rows.map(r=>r.k),datasets:[{data:rows.map(r=>+(r.m*100).toFixed(0)),backgroundColor:rows.map(r=>r.n<MN?"#cfccc4":bandColor(r.m)),borderRadius:3,barThickness:20}]},
    options:{indexAxis:"y",maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>{const r=rows[c.dataIndex];return[` median index ${c.raw}% over ${r.n} parts`,` middle half: ${fmtP(r.q1)} to ${fmtP(r.q3)}`];}}}},
      scales:{x:{min:0,grace:"12%",ticks:{callback:v=>v+"%"},grid:{color:"#ece8e0"}},y:{grid:{display:false},ticks:{font:{size:11}}}}},
    plugins:[{id:"vals",afterDatasetsDraw(ch){const c=ch.ctx;c.save();c.font="11px Segoe UI";c.fillStyle="#222";ch.getDatasetMeta(0).data.forEach((b,i)=>{c.fillText(`${rows[i].n}`,b.x+6,b.y+4);});
      const x=ch.scales.x.getPixelForValue(100);c.strokeStyle="#15233c";c.setLineDash([4,3]);c.beginPath();c.moveTo(x,ch.chartArea.top);c.lineTo(x,ch.chartArea.bottom);c.stroke();c.restore();}}]});
}

/* ── section 3: same shelf at KS ── */
function shelf(){
  const KS=new Set(["ks","ks_gen","ks_am","ks_crossref"]);
  const rows=[];
  DATA.parts.forEach(p=>{if(!inTier(p)||!compOf(p))return;const os=(OBS_BY.get(p.pn)||[]).filter(o=>KS.has(o[OI.loader])&&okDate(o));
    const g=os.filter(o=>o[OI.grp]==="genuine").map(ratioOf).filter(x=>x!=null),a=os.filter(o=>o[OI.grp]==="street"||o[OI.grp]==="trade").map(ratioOf).filter(x=>x!=null);
    if(g.length&&a.length)rows.push({p,g:median(g),a:median(a),s:median(g)-median(a)});});
  const n=rows.length;
  document.getElementById("shelfTiles").innerHTML=[
    [n?fmtP(median(rows.map(r=>r.g))):"—","genuine at KS, median index",`${n} parts listed both ways`],
    [n?fmtP(median(rows.map(r=>r.a))):"—","aftermarket at KS, median index",`same ${n} parts`],
    [n?Math.round(100*median(rows.map(r=>r.s)))+" pts":"—","median gap between the two channels","genuine index minus aftermarket index, per part"],
  ].map(t=>`<div class="tile"><div class="v">${t[0]}</div><div class="l">${esc(t[1])}</div><div class="n">${esc(t[2])} · against ${esc(basisLabel())}</div></div>`).join("");
  const top=rows.sort((x,y)=>y.p.b-x.p.b).slice(0,18);
  document.getElementById("shelf-h").textContent=n?`The ${top.length} largest by billed value of ${n} parts KS lists both genuine and aftermarket · ${ageLabel()} · log scale · hover a row for the arithmetic, click it for every price`:"No part has both a genuine and an aftermarket KS price for this selection";
  if(!n){document.getElementById("shelf").innerHTML="";return;}
  const W=760,L=250,R=20,T=24,rowH=24,Hh=T+top.length*rowH+30;
  const lo=0.1,hi=4,X=v=>L+(Math.log10(Math.max(lo,Math.min(hi,v)))-Math.log10(lo))/(Math.log10(hi)-Math.log10(lo))*(W-L-R);
  let s=`<svg viewBox="0 0 ${W} ${Hh}" width="100%" role="img" aria-label="Genuine and aftermarket index per part at KS">`;
  top.forEach((r,i)=>{if(i%2)s+=`<rect x="0" y="${T+i*rowH}" width="${W}" height="${rowH}" fill="#fbf9f5"/>`;});
  [0.1,0.25,0.5,1,2,4].forEach(v=>{s+=`<line x1="${X(v)}" x2="${X(v)}" y1="${T}" y2="${T+top.length*rowH}" stroke="${v===1?"#15233c":"#e2ddd3"}" ${v===1?'stroke-dasharray="4 3"':""}/><text x="${X(v)}" y="${Hh-8}" font-size="11" text-anchor="middle" fill="#52514e">${Math.round(v*100)}%</text>`;});
  top.forEach((r,i)=>{const y=T+i*rowH+rowH/2;const lab=`${r.p.pn} ${r.p.d}`.slice(0,38);
    const ex=esc(`<b>${r.p.pn} · same shelf at KS</b><br>Comparison price: ${fmtE(compOf(r.p),2)} (${basisLabel()})<br>Genuine at KS: index ${fmtP(r.g)} ≈ ${fmtE(compOf(r.p)*r.g,2)}<br>Aftermarket at KS: index ${fmtP(r.a)} ≈ ${fmtE(compOf(r.p)*r.a,2)}<br>Gap between channels: ${Math.round(100*r.s)} pts<br>Billed: ${fmtE(r.p.b)}`);
    s+=`<g data-ex="${ex}" data-pn="${r.p.pn}" style="cursor:pointer"><rect x="0" y="${y-rowH/2}" width="${W}" height="${rowH}" fill="transparent"/>`+
      `<text x="${L-8}" y="${y+4}" font-size="11" text-anchor="end" fill="#222">${esc(lab)}</text>`+
      `<line x1="${X(r.a)}" x2="${X(r.g)}" y1="${y}" y2="${y}" stroke="#bdb8ad" stroke-width="3"/>`+
      `<circle cx="${X(r.a)}" cy="${y}" r="6" fill="#2a78d6"/><circle cx="${X(r.g)}" cy="${y}" r="6" fill="#c0552d"/></g>`;});
  s+=`</svg>`;
  const el=document.getElementById("shelf");el.innerHTML=s;
  el.querySelectorAll("g[data-pn]").forEach(g=>g.addEventListener("click",()=>drill(g.dataset.pn)));
}

/* ── section 4: SVG scatter, log axes with fixed ticks ── */
function s3(){
  const pts=DATA.parts.filter(p=>inTier(p)&&p.b>0).map(p=>({p,r:partRatio(p.pn,ST.grp)})).filter(x=>x.r!=null);
  const W=560,Hh=380,L=56,R=16,T=14,B=44;
  const xT=[1000,10000,100000,1000000],yT=[0.25,0.5,1,2,4];
  const xmin=500,xmax=1200000,ymin=0.2,ymax=5;
  const X=v=>L+(Math.log10(Math.max(xmin,Math.min(xmax,v)))-Math.log10(xmin))/(Math.log10(xmax)-Math.log10(xmin))*(W-L-R);
  const Y=v=>T+(Math.log10(ymax)-Math.log10(Math.max(ymin,Math.min(ymax,v))))/(Math.log10(ymax)-Math.log10(ymin))*(Hh-T-B);
  const expo=pts.filter(x=>x.r<1).sort((a,b)=>b.p.b-a.p.b).slice(0,10);const ex=new Set(expo.map(x=>x.p.pn));
  let s=`<svg viewBox="0 0 ${W} ${Hh}" width="100%" role="img" aria-label="Scatter of billed value against price index">`;
  s+=`<rect x="${X(50000)}" y="${Y(1)}" width="${X(xmax)-X(50000)}" height="${Y(ymin)-Y(1)}" fill="rgba(226,75,74,0.08)"/>`;
  xT.forEach(v=>{s+=`<line x1="${X(v)}" x2="${X(v)}" y1="${T}" y2="${Hh-B}" stroke="#ece8e0"/><text x="${X(v)}" y="${Hh-B+16}" font-size="11" text-anchor="middle" fill="#52514e">${v>=1e6?"€1M":"€"+(v/1000)+"k"}</text>`;});
  yT.forEach(v=>{s+=`<line x1="${L}" x2="${W-R}" y1="${Y(v)}" y2="${Y(v)}" stroke="${v===1?"#15233c":"#ece8e0"}" ${v===1?'stroke-dasharray="4 3"':""}/><text x="${L-6}" y="${Y(v)+4}" font-size="11" text-anchor="end" fill="#52514e">${Math.round(v*100)}%</text>`;});
  s+=`<text x="${(L+W-R)/2}" y="${Hh-6}" font-size="11.5" text-anchor="middle" fill="#52514e">billed, last 12 months (log scale)</text>`;
  s+=`<text x="12" y="${(T+Hh-B)/2}" font-size="11.5" text-anchor="middle" fill="#52514e" transform="rotate(-90 12 ${(T+Hh-B)/2})">price index (log)</text>`;
  pts.forEach(x=>{if(ex.has(x.p.pn))return;s+=`<circle cx="${X(x.p.b).toFixed(1)}" cy="${Y(x.r).toFixed(1)}" r="4" fill="${bandColor(x.r)}" fill-opacity=".75" data-pn="${x.p.pn}"/>`;});
  expo.forEach((x,i)=>{s+=`<circle cx="${X(x.p.b).toFixed(1)}" cy="${Y(x.r).toFixed(1)}" r="7" fill="${bandColor(x.r)}" stroke="#c0552d" stroke-width="2.2" data-pn="${x.p.pn}"/>`;});
  s+=`</svg>`;
  document.getElementById("scatter").innerHTML=s;
  const rho=spearman(pts.map(x=>x.p.b),pts.map(x=>x.r));
  document.getElementById("sc-h").textContent=`${pts.length} parts · ${DATA.group_label[ST.grp]} vs ${basisLabel()} · ${ageLabel()}`+
    (rho==null?"":` · rank correlation of billed value with index: ${rho>=0?"+":""}${rho.toFixed(2)} (${Math.abs(rho)<0.2?"no real link: exposure is spread, not sitting on the big lines":rho<0?"bigger parts tend to face cheaper rivals":"bigger parts tend to face dearer rivals"})`);
  document.querySelectorAll("#scatter circle").forEach(c=>{c.style.cursor="pointer";
    c.addEventListener("mousemove",e=>{const p=PART[c.dataset.pn];tipShow(e,`<b>${p.pn}</b> ${esc(p.d)}<br>billed ${fmtE(p.b)} · index ${fmtP(partRatio(p.pn,ST.grp))}<br>${esc(p.f)} · tier ${p.t||"—"}`);});
    c.addEventListener("mouseleave",tipHide);c.addEventListener("click",()=>drill(c.dataset.pn));});
  document.getElementById("expo").innerHTML=expo.length?`<table><thead><tr><th>Part</th><th class="r">Billed</th><th class="r">Index</th><th class="r">${ST.basis==="ref"?"Reference dealer price":"Our list"}</th><th class="r">Rival (median)</th></tr></thead><tbody>${
    expo.map(x=>{const c=compOf(x.p);return`<tr style="cursor:pointer" onclick="drill('${x.p.pn}')"><td><b>${x.p.pn}</b><br><span class="dash">${esc(x.p.d)}</span></td><td class="r">${fmtE(x.p.b)}</td><td class="r" data-ex="${esc(partBuilt(x.p,x.r,ST.grp))}">${bandChip(x.r)}</td><td class="r">${fmtE(c,2)}</td><td class="r">${fmtE(c*x.r,2)}</td></tr>`;}).join("")}</tbody></table>`
    :`<div class="callout">No part with a rival below 100% for this selection.</div>`;
}
const tip=document.getElementById("tip");
function tipShow(e,h){tip.innerHTML=h;tip.style.display="block";tip.style.left=Math.min(innerWidth-330,e.clientX+12)+"px";tip.style.top=(e.clientY+12)+"px";}
function tipHide(){tip.style.display="none";}

/* ── section 4 ── */
function s4(){
  const yrs={};const G=["street","rrp","trade","genuine"],GC={street:"#2a78d6",rrp:"#85b7eb",trade:"#888780",genuine:"#c0552d"};
  DATA.obs.forEach(o=>{let y=parseInt(String(o[OI.date]).slice(0,4));if(!y)return;const k=y<2020?"before 2020":String(y);(yrs[k]=yrs[k]||{});yrs[k][o[OI.grp]]=(yrs[k][o[OI.grp]]||0)+1;});
  const labels=Object.keys(yrs).sort((a,b)=>a==="before 2020"?-1:b==="before 2020"?1:a.localeCompare(b));
  C.year=new Chart(cYear,{type:"bar",data:{labels,datasets:G.map(g=>({label:DATA.group_label[g],data:labels.map(l=>yrs[l][g]||0),backgroundColor:GC[g],barThickness:30}))},
    options:{maintainAspectRatio:false,plugins:{legend:{position:"bottom",labels:{boxWidth:11,font:{size:11}}}},scales:{x:{stacked:true,grid:{display:false}},y:{stacked:true,grid:{color:"#ece8e0"},ticks:{precision:0}}}}});
  document.getElementById("srcT").innerHTML=`<thead><tr><th>Source</th><th>Status</th><th class="r">Prices</th><th class="r">Our parts</th><th>Latest</th></tr></thead><tbody>${
    DATA.sources.map(s=>`<tr title="${esc(s.note)}"><td>${esc(s.name)}<br><span class="dash" style="font-size:11.5px">${esc(s.note)}</span></td><td><span class="chip ${s.status}">${s.status}</span></td><td class="r">${s.rows.toLocaleString("en-GB")}</td><td class="r">${s.parts}</td><td>${fmtD(s.last)}</td></tr>`).join("")}</tbody>`;
  // run calendar
  const K=DATA.calendar;
  document.getElementById("cal-h").textContent=`Last 21 days, ${fmtD(K.days[0])} to ${fmtD(K.days[K.days.length-1])}. A dot = that source wrote prices dated that day (hover for the count). A blank = nothing written that day. This shows what reached the price data, not the run schedule.`;
  document.getElementById("calT").innerHTML=`<thead><tr><th style="text-align:left">Source</th>${K.days.map(d=>`<th title="${fmtD(d)}">${d.slice(8)}</th>`).join("")}</tr></thead><tbody>${
    K.rows.map(r=>`<tr><td class="nm">${esc(r.name)}</td>${K.days.map(d=>r.by_day[d]?`<td title="${r.by_day[d]} prices on ${fmtD(d)}"><span class="dot" style="opacity:${Math.min(1,.35+Math.log10(r.by_day[d])/3).toFixed(2)}"></span></td>`:`<td class="dash">·</td>`).join("")}</tr>`).join("")||`<tr><td class="nm dash">no prices written in the last 21 days</td></tr>`}</tbody>`;
  // search yield
  document.getElementById("yldT").innerHTML=`<thead><tr><th>Site</th><th class="r">Part numbers looked up</th><th class="r">Came back priced</th><th class="r">Yield</th><th>Latest</th></tr></thead><tbody>${
    DATA.yield.map(y=>`<tr><td>${esc(y.site)}</td><td class="r">${y.searched.toLocaleString("en-GB")}</td><td class="r">${y.priced.toLocaleString("en-GB")}</td><td class="r">${y.searched?Math.round(100*y.priced/y.searched)+"%":"—"}</td><td>${fmtD(y.last)}</td></tr>`).join("")}</tbody>`;
  // VAT per market
  document.getElementById("vat-h").textContent=DATA.vat_source+" The strip only touches prices the source marks VAT-inclusive; a market with none of those is not changed by it.";
  document.getElementById("vatT").innerHTML=`<thead><tr><th>Market</th><th class="r">Rate used</th><th class="r">Incl. VAT (stripped)</th><th class="r">Ex VAT</th><th class="r">Not stated (as recorded)</th></tr></thead><tbody>${
    DATA.vat_use.map(v=>`<tr><td>${esc(v.country)}</td><td class="r">${v.rate==null?`<span class="dash">none set</span>`:Math.round(v.rate*1000)/10+"%"}</td><td class="r">${v.incl.toLocaleString("en-GB")}</td><td class="r">${v.excl.toLocaleString("en-GB")}</td><td class="r">${v.unknown.toLocaleString("en-GB")}</td></tr>`).join("")}</tbody>`;
}
/* price moves, filtered by the date switch; ±15% flag as on the 1 Aug page */
function moves(){
  const M=DATA.moves.filter(m=>ST.age==="all"||String(m.last_date)>=DATA.fresh_cut);
  const mv=M.filter(m=>m.change_pct&&Math.abs(m.change_pct)>0).sort((a,b)=>Math.abs(b.change_pct)-Math.abs(a.change_pct));
  const big=mv.filter(m=>Math.abs(m.change_pct)>=15);
  document.getElementById("mv-h").textContent=`Prices we have seen more than once, ${ageLabel()}. Identical repeated rows are counted once. Changes of 15% or more are flagged; smaller moves stay listed, because a small move on a big part still matters.${mv.length>300?` The 300 largest of ${mv.length} moves are listed.`:""}`+
    (()=>{const am=mv.filter(m=>m.source==="Amayama"&&m.currency==="USD");if(am.length<10)return"";const sm=am.filter(m=>Math.abs(m.change_pct)<1).length;
      return ` ${sm} of ${am.length} Amayama moves are under 1% and mostly the same small step across unrelated parts; Amayama quotes in US dollars, so this looks like the shop's own currency conversion rather than a price change (not confirmed).`;})();
  document.getElementById("mvTiles").innerHTML=[
    [M.length.toLocaleString("en-GB"),"prices re-checked",""],
    [M.length?Math.round(100*(M.length-mv.length)/M.length)+"%":"—","did not move",`${M.length-mv.length} of ${M.length}`],
    [String(big.length),"moved 15% or more",""],
  ].map(t=>`<div class="tile"><div class="v">${t[0]}</div><div class="l">${t[1]}</div><div class="n">${t[2]}</div></div>`).join("");
  document.getElementById("mvT").innerHTML=mv.length?`<thead><tr><th>Source</th><th>Part</th><th>Price type</th><th>First seen</th><th class="r">Was</th><th>Last seen</th><th class="r">Now</th><th class="r">Change</th><th>Flag</th></tr></thead><tbody>${
    mv.slice(0,300).map(m=>`<tr style="cursor:pointer" onclick="drill('${esc(m.part_no)}')"><td>${esc(m.source)}</td><td><b>${esc(m.part_no)}</b><br><span class="dash">${esc(String(m.description||"").slice(0,70))}${m.offer&&String(m.offer).startsWith("sku:")?" · "+esc(String(m.offer).slice(4)):""}</span></td><td>${esc(DATA.group_label[{aftermarket_rrp:"rrp",genuine_grey:"genuine",aftermarket_retail:"street",aftermarket_trade:"trade",dealer:"genuine"}[m.price_type]]||m.price_type)}</td><td>${fmtD(m.first_date)}</td><td class="r">${m.first_price} ${esc(m.currency)}</td><td>${fmtD(m.last_date)}</td><td class="r">${m.last_price} ${esc(m.currency)}</td><td class="r">${m.change_pct>0?"+":""}${(+m.change_pct).toFixed(1)}%</td><td>${Math.abs(m.change_pct)>=15?`<span class="chip red">15% or more</span>`:`<span class="chip grey">below 15%</span>`}</td></tr>`).join("")}</tbody>`
    :`<tbody><tr><td class="dash">No re-checked price moved in this window.</td></tr></tbody>`;
}

/* ── section 5 ── */
function s5(){
  const H=DATA.hunt;
  document.getElementById("hunt-q").innerHTML=`${DATA.hunt_total} Tier A parts, worth ${DATA.hunt_value_pct}% of billed value, have no aftermarket price. The 60 largest are listed. The column <b>route</b> says what can find a price: a known competitor number can be searched; without one, the number has to come from a paid cross-reference first.`;
  document.getElementById("huntT").innerHTML=`<thead><tr><th>#</th><th>Part</th><th>Family</th><th class="r">Billed</th><th class="r">Our list</th><th>Route</th><th>Also seen</th></tr></thead><tbody>${
    H.map((p,i)=>`<tr style="cursor:pointer" onclick="drill('${p.pn}')"><td class="dash">${i+1}</td><td><b>${p.pn}</b><br><span class="dash">${esc(p.d)}</span></td><td>${esc(p.f)}</td><td class="r">${fmtE(p.b)}</td><td class="r">${fmtE(p.l,2)}</td><td>${
      p.x===2?`<span class="chip green">search by competitor number (${p.xn})</span>`:p.x===1?`<span class="chip amber">competitor number unconfirmed</span>`:p.x===3?`<span class="chip amber">single-source doubtful number (Spareto only)</span>`:`<span class="chip red">no competitor number</span>`}</td><td>${p.g?`<span class="chip grey">genuine price only</span>`:`<span class="dash">nothing</span>`}</td></tr>`).join("")}</tbody>`;
}

/* ── section 6 ── */
let sortK="b",sortD=-1;
function s6(){
  const q=document.getElementById("q").value.trim().toLowerCase(),f=document.getElementById("famSel").value,only=document.getElementById("onlyAm").checked;
  let rows=DATA.parts.filter(p=>inTier(p)&&(!f||p.f===f)&&(!q||p.pn.includes(q.replace(/\D/g,"")||"~~")||p.d.toLowerCase().includes(q)));
  rows=rows.map(p=>({...p,rs:partRatio(p.pn,"street"),rr:partRatio(p.pn,"rrp"),rt:partRatio(p.pn,"trade"),rg:partRatio(p.pn,"genuine"),n:(OBS_BY.get(p.pn)||[]).length}));
  if(only)rows=rows.filter(p=>p.rs!=null||p.rr!=null||p.rt!=null);
  rows.sort((a,b)=>{const x=a[sortK],y=b[sortK];if(x==null)return 1;if(y==null)return -1;return (x>y?1:x<y?-1:0)*sortD;});
  document.getElementById("cnt").textContent=`${rows.length} parts`;
  const th=(k,l,r)=>`<th class="${r?"r":""}" data-k="${k}">${l}${sortK===k?(sortD<0?" ▼":" ▲"):""}</th>`;
  document.getElementById("partT").innerHTML=`<thead><tr>${th("pn","Part")}${th("f","Family")}${th("t","Tier")}${th("b","Billed",1)}${th("l","Our list",1)}${th("rs","Shop",1)}${th("rr","Brand list",1)}${th("rt","Trade",1)}${th("rg","Genuine",1)}${th("n","Prices",1)}</tr></thead><tbody>${
    rows.slice(0,400).map(p=>`<tr style="cursor:pointer" onclick="drill('${p.pn}')"><td><b>${p.pn}</b><br><span class="dash">${esc(p.d)}</span></td><td>${esc(p.f)}</td><td>${p.t||"—"}</td><td class="r">${fmtE(p.b)}</td><td class="r">${fmtE(p.l,2)}</td><td class="r">${p.rs==null?"<span class='dash'>—</span>":bandChip(p.rs)}</td><td class="r">${p.rr==null?"<span class='dash'>—</span>":bandChip(p.rr)}</td><td class="r">${p.rt==null?"<span class='dash'>—</span>":bandChip(p.rt)}</td><td class="r">${p.rg==null?"<span class='dash'>—</span>":fmtP(p.rg)}</td><td class="r">${p.n}</td></tr>`).join("")}</tbody>`;
  document.querySelectorAll("#partT th").forEach(h=>h.onclick=()=>{const k=h.dataset.k;if(sortK===k)sortD=-sortD;else{sortK=k;sortD=(k==="pn"||k==="f"||k==="t")?1:-1;}s6();});
}
function drill(pn){
  const p=PART[pn]||DATA.hunt.find(h=>h.pn===pn)||{pn,d:"",f:"",t:"",b:0,l:null};
  const os=(OBS_BY.get(pn)||[]).slice().sort((a,b)=>String(b[OI.date]).localeCompare(String(a[OI.date])));
  const c=compOf(p);
  const el=document.getElementById("drill");el.classList.add("on");
  el.innerHTML=`<h3>${esc(pn)} · ${esc(p.d)}</h3><div class="h">${esc(p.f)} · tier ${p.t||"—"} · billed ${fmtE(p.b)} · our list ${fmtE(p.l,2)} · ${basisLabel()} ${fmtE(c,2)}</div>${
    os.length?`<div class="h">Every price we hold is listed. Hover an index for the arithmetic behind it. ${ST.age==="all"?"":"Greyed rows are older than 12 months and are left out of the charts."}</div><div class="tablewrap" style="max-height:420px"><table><thead><tr><th>Date</th><th>Price type</th><th>Source</th><th>Country</th><th>Brand / number</th><th class="r">Price</th><th class="r">€${ST.vat?" ex VAT*":""}</th><th class="r">Index</th><th>VAT</th></tr></thead><tbody>${
      os.map(o=>{const r=ratioOf(o);return`<tr style="${okDate(o)?"":"opacity:.5"}" title="${okDate(o)?"":"Older than 12 months: left out of the charts while the date switch is on last 12 months"}"><td>${fmtD(o[OI.date])}</td><td>${esc(DATA.group_label[o[OI.grp]])}</td><td>${o[OI.url]?`<a href="${esc(o[OI.url])}" target="_blank" rel="noopener">${esc(o[OI.src])}</a>`:esc(o[OI.src])}</td><td>${esc(o[OI.cty])}</td><td>${esc(o[OI.brand]||"")} ${esc(o[OI.cpn]||"")}</td><td class="r">${o[OI.price]} ${esc(o[OI.cur])}</td><td class="r">${fmtE(eurOf(o),2)}</td><td class="r" data-ex="${esc(howBuilt(o))}">${r==null?"—":(o[OI.grp]==="genuine"?fmtP(r):bandChip(r))}</td><td>${esc(o[OI.vat])}</td></tr>`;}).join("")}</tbody></table></div>`
    :`<div class="callout">No observed price for this part yet.</div>`}`;
  el.scrollIntoView({behavior:"smooth",block:"start"});
}

/* ── wiring ── */
function seg(id,key){document.querySelectorAll(`#${id} button`).forEach(b=>b.onclick=()=>{document.querySelectorAll(`#${id} button`).forEach(x=>x.classList.toggle("on",x===b));ST[key]=b.dataset.v;refresh();});}
function defs(){
  const D=[
    ["Reference dealer price",`price list × ${DATA.ref_multiple}`,"What the part should cost at the dealer counter after distributor and dealer margins. Provisional: one fixed basis for every market for now.",
      `Our price list × ${DATA.ref_multiple}. The margins reading decided under D03: a 37% distributor margin, then a 27.5% dealer margin (1 ÷ 0.63 ÷ 0.725 = 2.189). Provisional: the same basis is used for every market until a per-market basis is decided.`],
    ["Price index","rival € ÷ comparison €","Below 100% the rival is cheaper. Near 100% neutral, not a target. Above 100% the rival is dearer, which can be a fair genuine premium.",
      "Rival price in euro (VAT removed where the source shows it included and the strip is on) ÷ the comparison price chosen at the top. One value per part: the median of its prices."],
    ["Genuine index","genuine € ÷ comparison €","A genuine Isuzu part sold outside our network. Not a rival brand; it shows where the grey channel sits.",
      "Genuine Isuzu price seen at an outside seller ÷ comparison price."],
    ["Channel gap","genuine index − aftermarket index","On one shop's shelf: how far the aftermarket copy sits below the genuine part (section 3).",
      "Per part listed both ways at KS: genuine index minus aftermarket index, in percentage points. Median across parts."],
  ];
  document.getElementById("defs").innerHTML=D.map(d=>`<div class="def" data-ex="${esc(`<b>${d[0]}</b><br><span style='font-family:Consolas,monospace'>${d[1]}</span><br>${d[3]}`)}"><b>${esc(d[0])}</b><div class="f">${esc(d[1])}</div><div class="p">${esc(d[2])}</div></div>`).join("");
}
document.addEventListener("mousemove",e=>{const el=e.target.closest&&e.target.closest("[data-ex]");if(el&&el.dataset.ex){tipShow(e,el.dataset.ex);}else if(!(e.target.closest&&e.target.closest("#scatter circle")))tipHide();});
function refresh(){s2();posExtras();shelf();s3();moves();s6();const d=document.getElementById("drill");if(d.classList.contains("on")){const pn=d.querySelector("h3").textContent.split(" ")[0];drill(pn);}}
function foot(){
  const vin=DATA.vat_use.filter(v=>v.incl>0);
  document.getElementById("foot").innerHTML=`<b>Provisional assumption: one fixed comparison basis.</b> The reference dealer price is our price list × ${DATA.ref_multiple} for every market, the margins reading decided under D03 (a 37% distributor margin, then a 27.5% dealer margin). It is a single fixed basis for now: whether it fits every market has not been decided, and no per-market basis is applied until it is. Read every index on this page with that in mind.<br>
  <b>How to read this page.</b> Price index = rival price ÷ comparison price. Rival shop prices are end-customer prices, so the reference dealer price is the fairer comparison; the raw price list is offered for reference. Euro values use the dated ECB rates the price data stores. "Strip VAT" removes standard VAT only where the source shows a VAT-inclusive price. Rates set: ${Object.entries(DATA.vat).map(([k,v])=>k+" "+Math.round(v*1000)/10+"%").join(", ")}. In the current price data it actually applies to ${vin.map(v=>`${esc(v.country)} (${v.rate==null?"no rate set":Math.round(v.rate*1000)/10+"%"}, ${v.incl.toLocaleString("en-GB")} prices)`).join(", ")||"no market"}. ${esc(DATA.vat_source)} Prices whose VAT basis the source does not state are used as recorded (table in section 5). Price types are never averaged together. By default the charts use only prices dated in the last 12 months (since ${fmtD(DATA.fresh_cut)}); "all dates" adds the older Eucon files (2023 survey, March 2024 web shops, brand list prices dated 2002 to 2025). Billed = parts billed ${DATA.billed_window}, credit notes and returns excluded; a ranking, not an audited figure.<br>
  <b>Sources.</b> Our price list (${esc(DATA.price_list_file)}); billed parts from the sales data; prices from Eucon files (2023 survey, Mar 2024, Jul 2025, Mar 2026), KS International, Amayama, Omega, T&amp;M Commercials and three thin Nordic sites; competitor numbers from the graded cross-reference. Eucon-derived prices stay on this machine.`;
}
function init(){
  header();defs();s1();s4();s5();
  const fams=[...new Set(DATA.parts.map(p=>p.f))].sort();document.getElementById("famSel").innerHTML+=fams.map(f=>`<option>${esc(f)}</option>`).join("");
  seg("basis","basis");seg("grp","grp");seg("age","age");
  document.getElementById("vat").onchange=e=>{ST.vat=e.target.checked;refresh();};
  document.getElementById("tier").onchange=e=>{ST.tier=e.target.value;refresh();};
  ["q","famSel","onlyAm"].forEach(id=>document.getElementById(id).addEventListener("input",s6));
  // Link to one part: ...html#pn=8983767550 (optionally &grp=rrp&basis=list)
  const hp=new URLSearchParams(location.hash.slice(1));
  if(hp.get("grp")){ST.grp=hp.get("grp");document.querySelectorAll("#grp button").forEach(b=>b.classList.toggle("on",b.dataset.v===ST.grp));}
  if(hp.get("age")){ST.age=hp.get("age");document.querySelectorAll("#age button").forEach(b=>b.classList.toggle("on",b.dataset.v===ST.age));}
  if(hp.get("basis")){ST.basis=hp.get("basis");document.querySelectorAll("#basis button").forEach(b=>b.classList.toggle("on",b.dataset.v===ST.basis));}
  refresh();foot();
  if(hp.get("pn"))drill(hp.get("pn"));
}
Chart.defaults.font.family='"Segoe UI",Helvetica,Arial,sans-serif';Chart.defaults.color="#52514e";
init();
</script></body></html>
"""

if __name__ == "__main__":
    raise SystemExit(main())
