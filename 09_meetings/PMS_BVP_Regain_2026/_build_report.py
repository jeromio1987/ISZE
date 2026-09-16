"""Build Mode A PDF: PMS gaps where catalog-paired BVP can regain sales (per DB)."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ISZE / "01_data" / "00_derived"
OUT_DIR = ISZE / "09_meetings" / "PMS_BVP_Regain_2026"
CHART_JS = ISZE / "02_dashboards" / "_ui" / "chart.umd.min.js"
YEAR = 2025

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


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    opp = pd.read_csv(DER / "pms_opportunity_matrix.csv")
    opp = opp[(opp["year"] == YEAR) & (opp["pms_category"].isin(CORE))].copy()

    spu = pd.read_csv(DER / "gps_spu_pms.csv")
    spu_tot = spu[
        (spu["year"] == YEAR)
        & (spu["line_type"] == "all")
        & (spu["pms_category"].isin(CORE))
    ][["distributor_code", "pms_category", "spu_eur"]].rename(
        columns={"spu_eur": "spu_total"}
    )

    mix = pd.read_csv(DER / "mix_genuine_bvp_pms.csv")
    mix = mix[mix["year"] == YEAR].copy()
    mix["pms_category"] = mix["product_subgroup"]
    mix = mix[mix["pms_category"].isin(CORE)]
    mix_agg = mix.groupby(["distributor_code", "pms_category"], as_index=False).agg(
        bvp_eur=("bvp_eur", "sum"),
        genuine_eur=("genuine_eur", "sum"),
        total_eur=("total_eur", "sum"),
    )
    mix_agg["bvp_share"] = mix_agg["bvp_eur"] / mix_agg["total_eur"].replace(0, pd.NA)

    df = opp.merge(spu_tot, on=["distributor_code", "pms_category"], how="left")
    df = df.merge(mix_agg, on=["distributor_code", "pms_category"], how="left")

    # Network medians
    med_cap = df.groupby("pms_category")["capture_rate_total"].median()
    med_spu = df.groupby("pms_category")["spu_total"].median()
    df["med_cap"] = df["pms_category"].map(med_cap)
    df["med_spu"] = df["pms_category"].map(med_spu)
    df["cap_vs"] = df["capture_rate_total"] / df["med_cap"]
    df["spu_vs"] = df["spu_total"] / df["med_spu"]

    df["weak"] = (
        ((df["cap_vs"] < 0.75) | (df["spu_vs"] < 0.75))
        & ((df["revenue_gap_eur"] >= 5000) | (df.get("total_eur", 0).fillna(0) >= 3000))
    )

    addr = pd.read_csv(
        DER / "bvp_addressable_basket.csv", dtype={"genuine_pn": str, "bvp_pn": str}
    )
    xref = pd.read_csv(
        DER / "genuine_bvp_crossref.csv", dtype={"genuine_pn": str, "bvp_pn": str}
    )
    xref_u = xref[
        ["genuine_pn", "bvp_pn", "pair_source", "vehicle_model", "engine_type"]
    ].drop_duplicates(["genuine_pn", "bvp_pn"])

    unsold = addr[addr["currently_selling_bvp"] == False].copy()
    unsold = unsold.merge(xref_u, on=["genuine_pn", "bvp_pn"], how="left", suffixes=("", "_x"))
    unsold["vm"] = unsold["vehicle_model"].fillna(unsold.get("vehicle_model_x"))
    unsold["eng"] = unsold["engine_type"].fillna(unsold.get("engine_type_x"))
    unsold["strict"] = (unsold["pair_source"] == "catalog_paired") & unsold["vm"].notna() & (
        unsold["vm"].astype(str).str.strip() != ""
    )
    strict = unsold[unsold["strict"] & unsold["product_subgroup"].isin(CORE)].copy()

    # Join weak cells that have ≥1 strict unsold pair
    customers = []
    for db, gweak in df[df["weak"]].groupby("distributor_code"):
        pairs = strict[strict["distributor_code"] == db]
        if pairs.empty:
            continue
        cats = []
        total_gap = 0.0
        for _, r in gweak.sort_values("revenue_gap_eur", ascending=False).iterrows():
            cat = r["pms_category"]
            cp = pairs[pairs["product_subgroup"] == cat]
            if cp.empty:
                continue
            gap = float(r["revenue_gap_eur"] or 0)
            total_gap += gap
            example = []
            for _, p in cp.head(5).iterrows():
                example.append(
                    {
                        "genuine": p["genuine_pn"],
                        "bvp": p["bvp_pn"],
                        "models": str(p["vm"]) if pd.notna(p["vm"]) else "",
                        "engine": str(p["eng"]) if pd.notna(p["eng"]) else "",
                    }
                )
            cats.append(
                {
                    "category": cat,
                    "category_label": cat_label(cat),
                    "gap_eur": gap,
                    "capture": float(r["capture_rate_total"])
                    if pd.notna(r["capture_rate_total"])
                    else None,
                    "cap_vs_med": float(r["cap_vs"]) if pd.notna(r["cap_vs"]) else None,
                    "spu": float(r["spu_total"]) if pd.notna(r["spu_total"]) else None,
                    "spu_vs_med": float(r["spu_vs"]) if pd.notna(r["spu_vs"]) else None,
                    "bvp_share": float(r["bvp_share"]) if pd.notna(r["bvp_share"]) else 0.0,
                    "n_pairs": int(cp["bvp_pn"].nunique()),
                    "examples": example,
                }
            )
        if not cats:
            continue
        # Count only pairs inside weak categories (not all catalog pairs on the DB)
        customers.append(
            {
                "db": db,
                "label": DB_LABEL.get(db, db),
                "total_gap": total_gap,
                "n_categories": len(cats),
                "n_pairs": int(sum(c["n_pairs"] for c in cats)),
                "categories": cats,
            }
        )

    customers.sort(key=lambda c: -c["total_gap"])

    payload = {
        "year": YEAR,
        "customers": customers,
        "network_gap": sum(c["total_gap"] for c in customers),
        "n_customers": len(customers),
        "n_pairs": int(sum(c["n_pairs"] for c in customers)),
    }
    (OUT_DIR / "payload.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )

    chart_js = CHART_JS.read_text(encoding="utf-8")
    chart_js = re.sub(r"//# sourceMappingURL=.*", "", chart_js)

    # Build HTML
    labels = [c["label"] for c in customers[:12]]
    gaps_k = [round(c["total_gap"] / 1000) for c in customers[:12]]
    colors = ["#c0552d" if i < 3 else "#2a78d6" for i in range(len(labels))]

    cust_html = []
    for i, c in enumerate(customers):
        # First customer continues after network chart; later ones start a new page
        page_break = ' style="break-before:page"' if i > 0 else ""
        if i == 0:
            page_break = ' style="break-before:page"'
        rows = []
        for cat in c["categories"][:6]:
            cap = f"{100*cat['capture']:.0f}%" if cat["capture"] is not None else "—"
            vs = (
                f"{100*cat['spu_vs_med']:.0f}% of network"
                if cat["spu_vs_med"] is not None
                else (
                    f"{100*cat['cap_vs_med']:.0f}% of network"
                    if cat["cap_vs_med"] is not None
                    else "—"
                )
            )
            rows.append(
                f"<tr><td>{cat['category_label']}</td>"
                f"<td>{eur(cat['gap_eur'])}</td>"
                f"<td>{cap}</td><td>{vs}</td>"
                f"<td>{100*cat['bvp_share']:.0f}%</td>"
                f"<td>{cat['n_pairs']}</td></tr>"
            )
        pair_rows = []
        shown = 0
        for cat in c["categories"]:
            for ex in cat["examples"]:
                if shown >= 8:
                    break
                pair_rows.append(
                    f"<tr><td>{cat['category_label']}</td>"
                    f"<td>{ex['genuine']}</td><td>{ex['bvp']}</td>"
                    f"<td>{ex['models']}</td><td>{ex['engine']}</td></tr>"
                )
                shown += 1
            if shown >= 8:
                break

        cust_html.append(
            f"""
<section class="cust"{page_break}>
  <h2 class="sec"><span class="no">{i+1:02d}</span> {c['label']}</h2>
  <p class="lede">Capture gap with a catalog BVP alternative: <strong>{eur(c['total_gap'])}</strong>
  across <strong>{c['n_categories']}</strong> weak categories ·
  <strong>{c['n_pairs']}</strong> paired BVP part numbers not yet sold.</p>
  <h3>Weak categories (priority)</h3>
  <table>
    <thead><tr><th>Category</th><th>Gap</th><th>Capture</th><th>vs network €/UIO</th><th>Current BVP € mix</th><th>Unsold BVP pairs</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
  <h3>Catalog pairs to push (same application)</h3>
  <p class="hint">Each line is a genuine part this distributor already sells, with a catalog-paired BVP for the same model/engine family that is not yet on their invoices.</p>
  <table>
    <thead><tr><th>Category</th><th>Genuine PN</th><th>BVP PN</th><th>Models</th><th>Engine</th></tr></thead>
    <tbody>{''.join(pair_rows)}</tbody>
  </table>
</section>
"""
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>PMS capture gaps — BVP regain opportunities CY{YEAR}</title>
<style>
*{{box-sizing:border-box;}}
html,body{{margin:0;padding:0;-webkit-print-color-adjust:exact;print-color-adjust:exact;}}
body{{font-family:"Segoe UI",Helvetica,Arial,sans-serif;color:#222;font-size:10.3px;line-height:1.5;}}
h1,h2,h3,h4{{font-family:Georgia,"Times New Roman",serif;color:#1a2b4a;margin:0;}}
@page{{size:A4;margin:16mm 15mm 21mm 15mm;}}
.cover{{position:relative;min-height:267mm;margin:-16mm -15mm 0;padding:26mm 22mm;
  background:linear-gradient(155deg,#15233c 0%,#203759 60%,#2b4a78 100%);color:#eef1f6;break-after:page;}}
.cover h1{{color:#fff;font-size:36px;line-height:1.12;max-width:160mm;}}
.cover .rule{{width:54mm;height:3px;background:#c0552d;margin:9mm 0 8mm;}}
.cover .meta{{font-size:12px;opacity:.9;max-width:150mm;}}
.cover .kpis{{display:flex;gap:8mm;margin-top:14mm;}}
.cover .kpi{{background:rgba(255,255,255,.08);padding:5mm 6mm;min-width:42mm;}}
.cover .kpi b{{display:block;font-size:22px;color:#fff;font-family:Georgia,serif;}}
.cover .kpi span{{font-size:9px;opacity:.85;text-transform:uppercase;letter-spacing:.04em;}}
h2.sec{{font-size:17px;margin:0 0 2mm;padding-bottom:2.5mm;border-bottom:2px solid #1a2b4a;break-after:avoid;}}
h2.sec .no{{color:#c0552d;}}
h3{{font-size:12px;margin:4mm 0 1.5mm;color:#1a2b4a;}}
.lede{{margin:2mm 0 3mm;font-size:10.5px;}}
.hint{{color:#6b6256;font-size:9px;margin:0 0 2mm;}}
.callout{{border-left:3px solid #c0552d;background:#f7f4ee;padding:3.2mm 4mm;margin:3mm 0 5mm;break-inside:avoid;}}
table{{width:100%;border-collapse:collapse;margin:2mm 0 4mm;font-size:9.2px;break-inside:avoid;}}
th{{background:#1a2b4a;color:#fff;text-align:left;padding:2.2mm;font-size:8.5px;text-transform:uppercase;}}
td{{padding:2mm;border-bottom:.5px solid #d9d3c8;vertical-align:top;}}
tbody tr:nth-child(even){{background:#f7f4ee;}}
tr{{break-inside:avoid;}}
.chart-wrap{{position:relative;width:100%;height:420px;margin:3mm 0 6mm;}}
.sources{{font-size:8px;color:#6b6256;margin-top:6mm;border-top:.5px solid #d9d3c8;padding-top:2mm;}}
.footer{{position:fixed;bottom:9mm;left:15mm;right:15mm;font-size:7.6px;color:#6b6256;
  display:flex;justify-content:space-between;border-top:.5px solid #d9d3c8;padding-top:1.5mm;}}
.cust{{margin-bottom:6mm;}}
</style>
</head>
<body>
<div class="footer"><span>ISZE · PMS / BVP regain · CY{YEAR}</span><span>Internal commercial briefing</span></div>

<section class="cover">
  <div style="font-size:11px;letter-spacing:.08em;text-transform:uppercase;opacity:.75;">Aftermarket · PMS basket</div>
  <h1>Where capture is low and a BVP alternative already exists</h1>
  <div class="rule"></div>
  <p class="meta">Per distributor: biggest PMS gaps versus the network, limited to cases where
  the catalog pairs a BVP to a genuine part that distributor already sells — and that BVP is not yet on their invoices.</p>
  <div class="kpis">
    <div class="kpi"><b>{eur(payload['network_gap'])}</b><span>Gap with usable BVP pair</span></div>
    <div class="kpi"><b>{payload['n_customers']}</b><span>Distributors</span></div>
    <div class="kpi"><b>{payload['n_pairs']}</b><span>Unsold paired BVP PNs</span></div>
  </div>
  <p class="meta" style="margin-top:18mm;opacity:.7;">CY{YEAR} · Total capture lens · Catalog-paired + model fitment only</p>
</section>

<section>
  <h2 class="sec"><span class="no">01</span> Network view</h2>
  <div class="callout">
    <strong>Rule used.</strong> Weak = capture or € per vehicle below 75% of the network median for that category,
    with a material revenue gap. Action list = only <em>catalog-paired</em> BVP lines with a model family filled in,
    for genuine part numbers that distributor already buys. Softer registry-only links are excluded.
  </div>
  <p class="lede">Largest regain opportunities by distributor (sum of weak categories that still have an unsold paired BVP).</p>
  <div class="chart-wrap">
    <canvas id="rank" role="img" aria-label="Distributor ranking by PMS gap with usable unsold BVP">Ranking chart</canvas>
  </div>
</section>

<section>
  <h2 class="sec"><span class="no">02</span> Per distributor</h2>
  <p class="lede">For each customer: priority categories, then the concrete genuine → BVP pairs to introduce.</p>
</section>

{''.join(cust_html)}

<section style="break-before:page">
  <h2 class="sec"><span class="no">03</span> Reading notes</h2>
  <div class="callout">
    This is not “list a random BVP.” Every pair below is tied to a genuine part already sold by that distributor,
    with the same catalog application (model / engine family). The gap figure is the PMS capture shortfall versus expected demand —
    BVP is the commercial lever to win back volume that today leaves the Isuzu channel or stays on genuine only.
  </div>
  <p class="sources">Sources: CY{YEAR} PMS capture &amp; €/UIO by distributor and category; genuine–BVP catalog pairs;
  distributor billing for which genuine parts they already sell and which BVP parts are not yet billed.
  Israel UTI and UMI are shown separately. Indicative commercial briefing — not a forecast.</p>
</section>

<script>{chart_js}</script>
<script>
new Chart(document.getElementById('rank'), {{
  type: 'bar',
  data: {{
    labels: {json.dumps(labels)},
    datasets: [{{
      data: {json.dumps(gaps_k)},
      backgroundColor: {json.dumps(colors)},
      borderRadius: 4,
      barThickness: 22
    }}]
  }},
  options: {{
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{
      legend: {{ display: false }},
      tooltip: {{
        callbacks: {{
          label: function(ctx) {{ return ' Gap ' + ctx.parsed.x + 'k EUR'; }}
        }}
      }}
    }},
    scales: {{
      x: {{
        title: {{ display: true, text: 'Capture gap with usable unsold BVP (EUR thousands)', color: '#52514e' }},
        grid: {{ color: '#e1e0d9' }},
        ticks: {{ color: '#52514e' }}
      }},
      y: {{
        grid: {{ display: false }},
        ticks: {{ color: '#52514e', font: {{ size: 11 }} }}
      }}
    }}
  }}
}});
</script>
</body>
</html>
"""
    html_path = OUT_DIR / "PMS_BVP_Regain.html"
    html_path.write_text(html, encoding="utf-8")
    print(f"HTML {html_path}")
    print(f"Customers {len(customers)} network_gap {payload['network_gap']:.0f}")
    for c in customers[:8]:
        print(f"  {c['label']}: {c['total_gap']:.0f} / {c['n_pairs']} pairs")


if __name__ == "__main__":
    main()
