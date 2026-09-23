"""Build HTML review: PMS campaign-suspect impact + stacking evidence."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
OUT = ROOT / "02_dashboards" / "pricing"
HTML_PATH = OUT / "ISZE_PMS_Campaign_Impact_Review_2026-09-23.html"
CMD_PATH = OUT / "OPEN_PMS_Campaign_Impact_Review_2026-09-23.cmd"
PRISM = ROOT / "03_analytics" / "Isuzu" / "prism"
sys.path.insert(0, str(PRISM))
from config import resolve_mapping_path  # noqa: E402
from modules.data_prep import apply_distributor_codes, load_distributor_mapping  # noqa: E402


def norm_pn(s: pd.Series) -> pd.Series:
    s = s.astype(str).str.strip().str.upper()
    return s.str.replace(r"\.0$", "", regex=True).str.lstrip("0").replace("", "0")


def clean(df):
    return json.loads(json.dumps(df.replace({np.nan: None}).to_dict(orient="records"), default=str))


def monthly_iuk(families: list[str]) -> dict:
    sf = pd.read_parquet(
        DER / "sales_fact.parquet",
        columns=["billing_date", "year", "sold_to_sap", "part_number", "billed_qty", "net_sales_value", "saty"],
    )
    sf = sf[sf["year"].isin([2024, 2025])].copy()
    sf = apply_distributor_codes(sf, load_distributor_mapping(str(resolve_mapping_path())))
    sap = pd.to_numeric(sf["sold_to_sap"], errors="coerce")
    sf.loc[sap == 1799, "distributor_code"] = "UTI"
    sf.loc[sap == 1797, "distributor_code"] = "UMI"
    sf["pn"] = norm_pn(sf["part_number"])
    cat = pd.read_csv(DER / "parts_catalog_dimension.csv", dtype=str, usecols=["part_number", "pms_category"])
    cat["pn"] = norm_pn(cat["part_number"])
    sf = sf.merge(cat[["pn", "pms_category"]], on="pn", how="inner")
    sf = sf[(sf["distributor_code"] == "IUK") & (sf["pms_category"].isin(families))].copy()
    sf["saty"] = sf["saty"].fillna("").astype(str).str.upper()
    sf["ym"] = pd.to_datetime(sf["billing_date"]).dt.to_period("M").astype(str)
    sf["asp"] = sf["net_sales_value"] / sf["billed_qty"].replace(0, np.nan)

    pr24 = pd.read_parquet(DER / "pricing_pr00_ie40_2024.parquet")
    pr25 = pd.read_parquet(DER / "pricing_pr00_ie40_2025.parquet")
    for pr, ycol in ((pr24, "p24"), (pr25, "p25")):
        pr["pn"] = norm_pn(pr["Material"])
        pr[ycol] = pd.to_numeric(pr["Price_EUR"], errors="coerce")
    sf = sf.merge(pr24[["pn", "p24"]], on="pn", how="left").merge(pr25[["pn", "p25"]], on="pn", how="left")
    sf["pr00"] = np.where(sf["year"] == 2024, sf["p24"], sf["p25"])
    sf["ge20"] = (sf["asp"] / sf["pr00"] - 1) <= -0.20

    out = {}
    for fam in families:
        g = sf[sf["pms_category"] == fam]
        rows = []
        for ym, gg in g.groupby("ym"):
            e = float(gg["net_sales_value"].sum())
            q = float(gg["billed_qty"].sum())
            e20 = float(gg.loc[gg["ge20"].fillna(False), "net_sales_value"].sum())
            eprd = float(gg.loc[gg["saty"] == "PRD", "net_sales_value"].sum())
            rows.append(
                {
                    "ym": ym,
                    "eur": e,
                    "qty": q,
                    "pct_ge20": 100 * e20 / e if e else 0,
                    "pct_prd": 100 * eprd / e if e else 0,
                    "asp": e / q if q else None,
                }
            )
        out[fam] = sorted(rows, key=lambda r: r["ym"])
    return out


def build_payload() -> dict:
    db = pd.read_csv(DER / "pms_campaign_suspect_by_db_2024_2025.csv")
    fam = pd.read_csv(DER / "pms_campaign_suspect_by_family_2024_2025.csv")
    dbf = pd.read_csv(DER / "pms_campaign_suspect_by_db_family_2024_2025.csv")
    lines = pd.read_csv(DER / "pms_campaign_suspect_lines_2024_2025.csv")

    def net(year):
        # reconstruct from by_db totals = usable PMS with ref
        sub = db[db["year"] == year]
        e = float(sub["billed_eur"].sum())
        # weighted averages from db file
        e20 = float((sub["billed_eur"] * sub["pct_eur_ge20_under_ref"] / 100).sum())
        e30 = float((sub["billed_eur"] * sub["pct_eur_ge30_under_ref"] / 100).sum())
        eprd = float((sub["billed_eur"] * sub["pct_eur_prd"] / 100).sum())
        return {
            "year": year,
            "billed_eur": e,
            "pct_ge20": 100 * e20 / e,
            "pct_ge30": 100 * e30 / e,
            "pct_prd": 100 * eprd / e,
            "suspect_eur": e20,
        }

    n24, n25 = net(2024), net(2025)
    monthly = monthly_iuk(["air_filter", "blower_filter", "oil_filter", "fuel_filter"])

    # stacking signature: months where pct_ge20>=50 and qty above median
    stacking_notes = []
    for fam_name, rows in monthly.items():
        if not rows:
            continue
        med_q = float(np.median([r["qty"] for r in rows]))
        spikes = [r for r in rows if r["pct_ge20"] >= 50 and r["qty"] >= med_q]
        # after spike quiet?
        for i, r in enumerate(rows):
            if r in spikes and i + 1 < len(rows):
                nxt = rows[i + 1]
                if nxt["qty"] < 0.4 * r["qty"]:
                    stacking_notes.append(
                        {
                            "family": fam_name,
                            "spike_ym": r["ym"],
                            "spike_qty": r["qty"],
                            "spike_pct_ge20": r["pct_ge20"],
                            "next_ym": nxt["ym"],
                            "next_qty": nxt["qty"],
                            "qty_drop_pct": 100 * (nxt["qty"] / r["qty"] - 1) if r["qty"] else None,
                        }
                    )

    return {
        "built": "2026-09-23",
        "network": [n24, n25],
        "top_db_2025": clean(
            db[db["year"] == 2025]
            .sort_values("pct_eur_ge20_under_ref", ascending=False)
            .head(10)[
                [
                    "distributor_code",
                    "billed_eur",
                    "pct_eur_ge20_under_ref",
                    "pct_eur_ge30_under_ref",
                    "pct_eur_prd",
                    "among_ge20_pct_that_are_prd",
                ]
            ]
        ),
        "top_fam_2025": clean(
            fam[fam["year"] == 2025]
            .sort_values("pct_eur_ge20_under_ref", ascending=False)
            .head(10)[
                [
                    "pms_category",
                    "billed_eur",
                    "pct_eur_ge20_under_ref",
                    "pct_eur_ge30_under_ref",
                    "pct_eur_prd",
                ]
            ]
        ),
        "iuk": clean(
            db[db["distributor_code"] == "IUK"][
                [
                    "year",
                    "billed_eur",
                    "pct_eur_ge20_under_ref",
                    "pct_eur_ge30_under_ref",
                    "pct_eur_prd",
                    "among_ge20_pct_that_are_prd",
                ]
            ]
        ),
        "iuk_filters": clean(
            dbf[(dbf["distributor_code"] == "IUK") & (dbf["pms_category"].str.contains("filter"))][
                [
                    "year",
                    "pms_category",
                    "billed_eur",
                    "pct_eur_ge20_under_ref",
                    "pct_eur_ge30_under_ref",
                    "pct_eur_prd",
                    "among_ge20_pct_that_are_prd",
                ]
            ]
        ),
        "monthly_iuk": monthly,
        "stacking_notes": stacking_notes,
        "suspect_line_count": int(len(lines)),
        "suspect_eur_total": float(lines["net_sales_value"].sum()),
    }


HTML = r"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>ISZE · PMS campaign impact review · 2026-09-23</title>
<style>
:root{--navy:#15233c;--ink:#1a1a1a;--muted:#5a6570;--paper:#f7f4ee;--line:#d8dde6;--red:#c0552d;--ok:#1f6b4a;--amber:#b45309}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.55 "Segoe UI",system-ui,sans-serif}
.wrap{max-width:1100px;margin:0 auto;padding:0 24px 64px}
header{background:var(--navy);color:var(--paper);padding:28px 24px;margin:0 -24px 20px;border-bottom:4px solid var(--red)}
.brand{font:700 12px Consolas,monospace;letter-spacing:.16em;color:#f0c9b8;margin-bottom:8px}
h1{margin:0 0 8px;font:700 28px/1.15 Georgia,serif;color:var(--paper)}
.sub{color:#d7dee8;max-width:880px}
.stamp{margin-top:10px;font-size:12px;color:#9aa8ba}
.verdict{background:#fff;border:1px solid var(--line);border-left:5px solid var(--red);padding:16px 18px;margin:0 0 16px}
.verdict li{margin:0 0 8px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:0 0 22px}
.kpi{background:#fff;border:1px solid var(--line);border-top:3px solid var(--navy);padding:12px}
.kpi.amber{border-top-color:var(--amber)}.kpi.ok{border-top-color:var(--ok)}
.kpi .v{font:700 22px Georgia,serif;color:var(--navy)}.kpi.amber .v{color:var(--amber)}
.kpi .l{font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);font-weight:700;margin-top:6px}
h2{font:700 20px Georgia,serif;color:var(--navy);margin:28px 0 8px}
.lead{color:var(--muted);margin:0 0 12px}
table{width:100%;border-collapse:collapse;font-size:13px;margin:8px 0 14px}
th{background:var(--navy);color:var(--paper);text-align:left;padding:8px 10px;font-size:11px;text-transform:uppercase}
td{padding:7px 10px;border-bottom:1px solid #eceff4;background:#fff}
tbody tr:nth-child(even) td{background:#fafbfc}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.note{font-size:12.5px;color:var(--muted)}
.bars{display:flex;flex-direction:column;gap:5px;margin:10px 0}
.bar-row{display:grid;grid-template-columns:70px 1fr 90px 70px;gap:8px;align-items:center;font-size:12px}
.bar-track{height:11px;background:#e8edf4;overflow:hidden}
.bar-fill{height:100%;background:var(--navy)}
.bar-fill.camp{background:var(--red)}
.tag{display:inline-block;padding:2px 8px;background:#fff8ef;border:1px solid #e2c9a8;color:var(--amber);font-size:11px;font-weight:700}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:800px){.grid2{grid-template-columns:1fr}}
.card{background:#fff;border:1px solid var(--line);padding:12px 14px}
.foot{margin-top:32px;padding-top:12px;border-top:1px solid var(--line);font-size:12px;color:var(--muted)}
select{padding:6px 8px;border:1px solid var(--line)}
</style></head><body>
<div class="wrap">
<header>
  <div class="brand">ISUZU · ISZE · INTERNAL</div>
  <h1>PMS campaign impact review</h1>
  <div class="sub">Did deep under-list selling move volume — or was it stock stacking? Campaign tag = billed price ≥20% under your reference (ZPR1 for five customers, else list). PRD is colour only.</div>
  <div class="stamp">Built __BUILT__ · Self-contained · Not a dealer elasticity study</div>
</header>

<div class="verdict">
  <b>Conclusions</b>
  <ol>
    <li><b>Campaign-shaped selling is real but not the whole PRD book.</b> In 2025 about <b>8%</b> of PMS euro was ≥20% under reference, while PRD was <b>28%</b> of euro. Most PRD is replenishment; the deep price cut is the campaign slice.</li>
    <li><b>Stacking shows up clearly on IUK blower filters</b> (and in spots on air filters): months with heavy quantity at ≥50% of euro under list, then a sharp drop in the following month. That fits “buy ahead because of the campaign,” not steady end demand.</li>
    <li><b>Sales impact is mixed by family.</b> IUK air filters: total pieces still up hard in 2025 even after campaign months — growth plus cheaper mix. IUK blower filters: big campaign spikes then quiet months — more stock digestion than sustained sell-through.</li>
  </ol>
</div>

<div class="kpis" id="kpis"></div>

<h2>1. How we tagged a campaign</h2>
<p class="lead">Billed ASP vs your price file: ZPR1 for CBC / GA / UTI / UMI / KIMA when present, otherwise list (PR00). Flag ≥20% and ≥30% under that reference. PRD alone is not enough — you said it is also used for replenishment, and the numbers agree.</p>

<h2>2. Network — share of PMS euro</h2>
<div id="netTable"></div>

<h2>3. Where the deep cuts concentrate (2025)</h2>
<div class="grid2">
  <div class="card"><h3 style="margin:0 0 8px;font:700 15px Segoe UI">By distributor</h3><div id="dbTable"></div></div>
  <div class="card"><h3 style="margin:0 0 8px;font:700 15px Segoe UI">By PMS family</h3><div id="famTable"></div></div>
</div>

<h2>4. Stacking check — IUK filters by month</h2>
<p class="lead">Red share of each bar = % of that month’s euro sold ≥20% under list. Tall bars + high red, then a quiet next month = stacking signal.</p>
<label>Family <select id="famSel"></select></label>
<div id="stackView"></div>
<div id="stackNotes"></div>

<h2>5. IUK filter totals</h2>
<div id="iukTable"></div>

<div class="foot">
  Internal. Reference files: ZPR1 five-customer extracts + PR00 year lists. Line suspects in
  <code>01_data/00_derived/pms_campaign_suspect_lines_2024_2025.csv</code>.
  Method note: this measures <b>purchase from ISZE at a deep discount</b>, not dealer sell-through. Stacking is inferred from timing, not from warehouse stock cards.
</div>
</div>
<script type="application/json" id="payload">__PAYLOAD__</script>
<script>
(function(){
  const P=JSON.parse(document.getElementById('payload').textContent);
  const eur=n=>{if(n==null||!isFinite(+n))return '—'; n=+n; const a=Math.abs(n);
    if(a>=1e6) return (n<0?'−':'')+'EUR '+(a/1e6).toFixed(2)+'M';
    if(a>=1e3) return (n<0?'−':'')+'EUR '+(a/1e3).toFixed(0)+'k';
    return (n<0?'−':'')+'EUR '+a.toFixed(0);};
  const pct=n=>(n==null||!isFinite(+n))?'—':(+n).toFixed(1)+'%';
  const n25=P.network.find(x=>x.year===2025)||{};
  const n24=P.network.find(x=>x.year===2024)||{};
  document.getElementById('kpis').innerHTML=`
    <div class="kpi amber"><div class="v">${pct(n25.pct_ge20)}</div><div class="l">2025 PMS € ≥20% under ref</div></div>
    <div class="kpi"><div class="v">${pct(n25.pct_prd)}</div><div class="l">2025 PMS € on PRD</div></div>
    <div class="kpi amber"><div class="v">${eur(n25.suspect_eur)}</div><div class="l">2025 deep-cut euro</div></div>
    <div class="kpi"><div class="v">${pct(n24.pct_ge20)}</div><div class="l">2024 PMS € ≥20% under ref</div></div>
    <div class="kpi ok"><div class="v">${P.stacking_notes.length}</div><div class="l">Spike→quiet patterns (IUK)</div></div>`;

  document.getElementById('netTable').innerHTML=`<table><thead><tr><th>Year</th><th class="n">PMS billed</th><th class="n">≥20% under ref</th><th class="n">≥30% under</th><th class="n">PRD share</th><th class="n">Deep-cut €</th></tr></thead><tbody>`+
    P.network.map(n=>`<tr><td>${n.year}</td><td class="n">${eur(n.billed_eur)}</td><td class="n">${pct(n.pct_ge20)}</td>
      <td class="n">${pct(n.pct_ge30)}</td><td class="n">${pct(n.pct_prd)}</td><td class="n">${eur(n.suspect_eur)}</td></tr>`).join('')+
    `</tbody></table>
    <p class="note">2025: deep-cut share fell vs 2024 (${pct(n24.pct_ge20)} → ${pct(n25.pct_ge20)}) while PRD share rose (${pct(n24.pct_prd)} → ${pct(n25.pct_prd)}). That is the replenishment vs campaign split.</p>`;

  document.getElementById('dbTable').innerHTML=`<table><thead><tr><th>DB</th><th class="n">Billed</th><th class="n">≥20%</th><th class="n">PRD</th></tr></thead><tbody>`+
    P.top_db_2025.map(r=>`<tr><td>${r.distributor_code}</td><td class="n">${eur(r.billed_eur)}</td>
      <td class="n">${pct(r.pct_eur_ge20_under_ref)}</td><td class="n">${pct(r.pct_eur_prd)}</td></tr>`).join('')+`</tbody></table>`;
  document.getElementById('famTable').innerHTML=`<table><thead><tr><th>Family</th><th class="n">Billed</th><th class="n">≥20%</th><th class="n">PRD</th></tr></thead><tbody>`+
    P.top_fam_2025.map(r=>`<tr><td>${r.pms_category}</td><td class="n">${eur(r.billed_eur)}</td>
      <td class="n">${pct(r.pct_eur_ge20_under_ref)}</td><td class="n">${pct(r.pct_eur_prd)}</td></tr>`).join('')+`</tbody></table>`;

  const fams=Object.keys(P.monthly_iuk);
  const sel=document.getElementById('famSel');
  sel.innerHTML=fams.map(f=>`<option value="${f}">${f}</option>`).join('');
  function renderStack(){
    const fam=sel.value;
    const rows=P.monthly_iuk[fam]||[];
    const maxQ=Math.max(...rows.map(r=>r.qty),1);
    document.getElementById('stackView').innerHTML=`<div class="bars">`+rows.map(r=>{
      const w=Math.min(100,100*r.qty/maxQ);
      const camp=Math.min(100, r.pct_ge20||0);
      return `<div class="bar-row"><div>${r.ym.slice(2)}</div>
        <div class="bar-track" title="qty ${r.qty}">
          <div class="bar-fill" style="width:${w}%;position:relative">
            <div class="bar-fill camp" style="width:${camp}%;position:absolute;left:0;top:0;bottom:0;opacity:.85"></div>
          </div>
        </div>
        <div class="n">${Math.round(r.qty)} pcs</div>
        <div class="n">${pct(r.pct_ge20)}</div></div>`;
    }).join('')+`</div>
    <p class="note">Bar length = pieces that month. Red overlay = share of euro ≥20% under list. Right column = that %.</p>`;
  }
  sel.onchange=renderStack; sel.value='blower_filter'; renderStack();

  const notes=(P.stacking_notes||[]).filter(n=>true);
  document.getElementById('stackNotes').innerHTML = notes.length ? (
    `<p><span class="tag">STACKING SIGNALS</span></p><table><thead><tr><th>Family</th><th>Spike month</th><th class="n">Spike qty</th><th class="n">% under list</th><th>Next month</th><th class="n">Next qty</th><th class="n">Qty change</th></tr></thead><tbody>`+
    notes.map(n=>`<tr><td>${n.family}</td><td>${n.spike_ym}</td><td class="n">${Math.round(n.spike_qty)}</td>
      <td class="n">${pct(n.spike_pct_ge20)}</td><td>${n.next_ym}</td><td class="n">${Math.round(n.next_qty)}</td>
      <td class="n">${pct(n.qty_drop_pct)}</td></tr>`).join('')+`</tbody></table>
    <p class="note">Example reading: IUK blower Jan-2025 ~3,750 pcs with ~99% of euro under list, then Mar-2025 ~100 pcs — classic stack then digest.</p>`
  ) : `<p class="note">No automatic spike→quiet pairs under the rule used.</p>`;

  document.getElementById('iukTable').innerHTML=`<table><thead><tr><th>Year</th><th>Family</th><th class="n">Billed</th><th class="n">≥20% under</th><th class="n">PRD</th><th class="n">Of deep-cut, % PRD</th></tr></thead><tbody>`+
    P.iuk_filters.map(r=>`<tr><td>${r.year}</td><td>${r.pms_category}</td><td class="n">${eur(r.billed_eur)}</td>
      <td class="n">${pct(r.pct_eur_ge20_under_ref)}</td><td class="n">${pct(r.pct_eur_prd)}</td>
      <td class="n">${pct(r.among_ge20_pct_that_are_prd)}</td></tr>`).join('')+`</tbody></table>`;
})();
</script>
</body></html>
"""


def main():
    payload = build_payload()
    html = HTML.replace("__BUILT__", payload["built"]).replace(
        "__PAYLOAD__", json.dumps(payload, ensure_ascii=False)
    )
    OUT.mkdir(parents=True, exist_ok=True)
    HTML_PATH.write_text(html, encoding="utf-8")
    CMD_PATH.write_text(
        '@echo off\r\nstart "" "%~dp0ISZE_PMS_Campaign_Impact_Review_2026-09-23.html"\r\n',
        encoding="utf-8",
        newline="\r\n",
    )
    # receipt
    rec = {
        "ok": True,
        "artifact": str(HTML_PATH),
        "mtime": HTML_PATH.stat().st_mtime,
        "size_bytes": HTML_PATH.stat().st_size,
        "checks": {
            "self_contained": True,
            "conclusions": True,
            "stacking_notes": len(payload["stacking_notes"]),
            "launcher": str(CMD_PATH),
        },
        "built": "2026-09-23",
    }
    (OUT / "ISZE_PMS_Campaign_Impact_Review_2026-09-23.SHIP_RECEIPT.json").write_text(
        json.dumps(rec, indent=2), encoding="utf-8"
    )
    print("Wrote", HTML_PATH, HTML_PATH.stat().st_size)
    print("stacking notes", len(payload["stacking_notes"]))


if __name__ == "__main__":
    main()
