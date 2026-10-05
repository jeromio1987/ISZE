"""All pr00_groups H1 dashboard — commercial / ex-warranty CY H1 2025 vs 2026.

    python build_parts_groups_dashboard.py --db HUNGARY
    python build_parts_groups_dashboard.py --db IBX

Outputs under 09_meetings/<DB>_Sales_Review_2026/:
  <DB>_all_groups_H1_2025_2026.csv
  <DB>_All_parts_groups_H1_dashboard.html
"""
from __future__ import annotations

import io
import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
TOOLS = ROOT / "04_tools" / "db_sales_review"
CHART_JS = ROOT / "02_dashboards" / "_ui" / "chart.umd.min.js"

sys.path.insert(0, str(TOOLS))
import common as C  # noqa: E402

# Own tab if either year ≥ this; else fold into Other (still in CSV + Overview)
MAJOR_EUR_FLOOR = 3000.0
TOP_N = 15
GROWER_N = 10


def load_commercial_pn(db_key: str) -> tuple[pd.DataFrame, dict]:
    p = C.load_profile(db_key)
    d = p["defaults"]
    L25, L26 = d["window_label_prior"], d["window_label_current"]

    sales = C.load_sales(p)
    gross = sales[~sales["is_credit"]].copy()
    warr = C.load_warranty_claim_pns(p)
    claim_pns = warr["pns"]
    sap_by_mat = (
        gross.dropna(subset=["Material"])
        .assign(_a=lambda x: x["net_eur"].abs())
        .sort_values("_a", ascending=False)
        .drop_duplicates("Material")
        .set_index("Material")["sap_desc"]
        .to_dict()
    )
    gross["is_warranty"] = [
        C.is_warranty_pn(m, sap_by_mat.get(m, desc), claim_pns)
        for m, desc in zip(gross["Material"], gross["sap_desc"])
    ]
    commercial = gross[~gross["is_warranty"]].copy()

    # Catalog with level-3
    cat = pd.read_csv(
        C.DERIVED / "parts_catalog_dimension.csv", dtype=str, low_memory=False
    )
    cat["part_number"] = cat["part_number"].map(C.norm_pn)
    cat = cat.drop_duplicates("part_number")
    l3 = cat.set_index("part_number")["pr00_level3_type"].fillna("").to_dict()
    grp = cat.set_index("part_number")["pr00_group"].fillna("").to_dict()

    # Descriptions
    _, desc_by_newest = C.load_itc_map()
    model_by_pn = C.load_pn_vehicle_models()

    g = (
        commercial.groupby(["Material", "period"], dropna=False)
        .agg(qty=("qty", "sum"), net_eur=("net_eur", "sum"))
        .reset_index()
    )
    wide = g.pivot_table(
        index="Material",
        columns="period",
        values=["qty", "net_eur"],
        aggfunc="sum",
        fill_value=0,
    )
    wide.columns = [f"{a}|{b}" for a, b in wide.columns]
    wide = wide.reset_index()
    for col in [f"qty|{L25}", f"qty|{L26}", f"net_eur|{L25}", f"net_eur|{L26}"]:
        if col not in wide.columns:
            wide[col] = 0.0

    sap = (
        commercial.dropna(subset=["Material"])
        .assign(_a=lambda x: x["net_eur"].abs())
        .sort_values("_a", ascending=False)
        .drop_duplicates("Material")
        .set_index("Material")["sap_desc"]
        .to_dict()
    )

    c_e25, c_e26 = f"net_eur|{L25}", f"net_eur|{L26}"
    c_q25, c_q26 = f"qty|{L25}", f"qty|{L26}"
    rows = []
    for r in wide.to_dict("records"):
        pn = r.get("Material")
        if not pn:
            continue
        e25 = float(r.get(c_e25, 0) or 0)
        e26 = float(r.get(c_e26, 0) or 0)
        q25 = float(r.get(c_q25, 0) or 0)
        q26 = float(r.get(c_q26, 0) or 0)
        if e25 == 0 and e26 == 0 and q25 == 0 and q26 == 0:
            continue
        group = (grp.get(pn) or "").strip() or "UNCLASSIFIED"
        kind = (l3.get(pn) or "").strip() or "Unspecified"
        desc = desc_by_newest.get(pn, "") or sap.get(pn, "") or ""
        model = model_by_pn.get(pn, "") or ""
        rows.append(
            {
                "PN": pn,
                "description": desc,
                "pr00_group": group,
                "kind": kind,
                "vehicle_model": model,
                "H1'25 EUR": round(e25, 2),
                "H1'25 qty": round(q25, 2),
                "H1'26 EUR": round(e26, 2),
                "H1'26 qty": round(q26, 2),
                "Delta EUR": round(e26 - e25, 2),
                "Delta qty": round(q26 - q25, 2),
            }
        )
    df = pd.DataFrame(rows).sort_values(
        ["pr00_group", "H1'26 EUR"], ascending=[True, False]
    )

    meta = {
        "db": p["key"],
        "display": p.get("display") or p.get("name") or p["key"],
        "name": p.get("name") or p["key"],
        "sold_to": p.get("sold_to"),
        "L25": L25,
        "L26": L26,
        "commercial_prior": float(
            commercial.loc[commercial["period"] == L25, "net_eur"].sum()
        ),
        "commercial_current": float(
            commercial.loc[commercial["period"] == L26, "net_eur"].sum()
        ),
        "claim_pns": len(claim_pns),
        "n_claim_lines": warr.get("n_claim_lines", 0),
    }
    return df, meta


def euro(n: float) -> str:
    sign = "-" if n < 0 else ""
    v = abs(n)
    if v >= 1_000_000:
        return f"{sign}€{v/1_000_000:.2f}M"
    if v >= 1000:
        return f"{sign}€{v:,.0f}"
    return f"{sign}€{v:,.0f}"


def euro_delta(n: float) -> str:
    sign = "+" if n > 0 else ("-" if n < 0 else "")
    v = abs(n)
    return f"{sign}€{v:,.0f}"


def pct(de: float, base: float) -> float | None:
    if not base:
        return None
    return round(100.0 * de / base, 1)


def build_payload(df: pd.DataFrame, meta: dict) -> dict:
    e25 = float(df["H1'25 EUR"].sum())
    e26 = float(df["H1'26 EUR"].sum())
    de = e26 - e25
    q25 = float(df["H1'25 qty"].sum())
    q26 = float(df["H1'26 qty"].sum())
    mapped = df["vehicle_model"].astype(str).str.strip().ne("")
    model_cov = (
        round(float(df.loc[mapped, "H1'26 EUR"].sum() / e26 * 100), 1)
        if e26 and mapped.any()
        else 0.0
    )

    by_g = (
        df.groupby("pr00_group", as_index=False)
        .agg(
            e25=("H1'25 EUR", "sum"),
            e26=("H1'26 EUR", "sum"),
            q25=("H1'25 qty", "sum"),
            q26=("H1'26 qty", "sum"),
            n_pn=("PN", "nunique"),
            n_mapped=("vehicle_model", lambda s: int(s.astype(str).str.strip().ne("").sum())),
        )
        .sort_values("e26", ascending=False)
    )
    by_g["de"] = by_g["e26"] - by_g["e25"]
    by_g["dpct"] = by_g.apply(
        lambda r: pct(r["de"], r["e25"]) if r["e25"] else None, axis=1
    )
    by_g["max_e"] = by_g[["e25", "e26"]].max(axis=1)

    major = by_g[by_g["max_e"] >= MAJOR_EUR_FLOOR].copy()
    tiny = by_g[by_g["max_e"] < MAJOR_EUR_FLOOR].copy()
    other_names = set(tiny["pr00_group"].tolist())

    groups_payload = []
    for _, g in major.iterrows():
        name = str(g["pr00_group"])
        sub = df[df["pr00_group"] == name]
        groups_payload.append(group_block(name, sub, g))

    if len(tiny):
        sub = df[df["pr00_group"].isin(other_names)]
        # synthetic row for Other
        o = pd.Series(
            {
                "pr00_group": "Other",
                "e25": float(tiny["e25"].sum()),
                "e26": float(tiny["e26"].sum()),
                "q25": float(tiny["q25"].sum()),
                "q26": float(tiny["q26"].sum()),
                "n_pn": int(tiny["n_pn"].sum()),
                "n_mapped": int(tiny["n_mapped"].sum()),
                "de": float(tiny["de"].sum()),
                "dpct": pct(float(tiny["de"].sum()), float(tiny["e25"].sum())),
            }
        )
        block = group_block("Other", sub, o)
        block["folded_groups"] = [
            {
                "group": str(r.pr00_group),
                "e25": round(float(r.e25)),
                "e26": round(float(r.e26)),
                "de": round(float(r.de)),
            }
            for r in tiny.sort_values("e26", ascending=False).itertuples()
        ]
        groups_payload.append(block)

    overview_groups = [
        {
            "group": str(r.pr00_group),
            "e25": round(float(r.e25)),
            "e26": round(float(r.e26)),
            "de": round(float(r.de)),
            "dpct": r.dpct,
            "q25": int(round(float(r.q25))),
            "q26": int(round(float(r.q26))),
            "n_pn": int(r.n_pn),
            "tab": "Other" if r.pr00_group in other_names else str(r.pr00_group),
        }
        for r in by_g.itertuples()
    ]
    # Add Other rollup line for overview chart if folding
    if len(tiny):
        overview_chart = [
            {
                "group": str(r.pr00_group),
                "e26": round(float(r.e26)),
                "de": round(float(r.de)),
            }
            for r in major.itertuples()
        ] + [
            {
                "group": "Other",
                "e26": round(float(tiny["e26"].sum())),
                "de": round(float(tiny["de"].sum())),
            }
        ]
    else:
        overview_chart = [
            {
                "group": str(r.pr00_group),
                "e26": round(float(r.e26)),
                "de": round(float(r.de)),
            }
            for r in by_g.itertuples()
        ]

    return {
        "meta": {
            "db": meta["db"],
            "display": meta["display"],
            "name": meta.get("name") or meta["display"],
            "lens": "Commercial (ex-warranty) · Calendar H1 2025 vs H1 2026",
            "sold_to": meta.get("sold_to"),
            "L25": meta["L25"],
            "L26": meta["L26"],
            "claim_pns": meta["claim_pns"],
            "n_claim_lines": meta["n_claim_lines"],
            "folded_floor_eur": MAJOR_EUR_FLOOR,
        },
        "kpi": {
            "e25": round(e25, 2),
            "e26": round(e26, 2),
            "de": round(de, 2),
            "dpct": pct(de, e25),
            "q25": int(round(q25)),
            "q26": int(round(q26)),
            "pn_any": int(len(df)),
            "pn_active_26": int(
                ((df["H1'26 EUR"] > 0) | (df["H1'26 qty"] > 0)).sum()
            ),
            "n_groups": int(by_g.shape[0]),
            "n_major_tabs": int(major.shape[0]),
            "model_cov_eur26_pct": model_cov,
            "n_mapped_pn": int(mapped.sum()),
        },
        "overview_groups": overview_groups,
        "overview_chart": overview_chart,
        "groups": groups_payload,
    }


def group_block(name: str, sub: pd.DataFrame, g: pd.Series) -> dict:
    by_kind = (
        sub.groupby("kind", as_index=False)
        .agg(
            e25=("H1'25 EUR", "sum"),
            e26=("H1'26 EUR", "sum"),
            q26=("H1'26 qty", "sum"),
            n_pn=("PN", "nunique"),
        )
        .sort_values("e26", ascending=False)
    )
    by_kind["de"] = by_kind["e26"] - by_kind["e25"]
    # keep kinds with meaningful spend for charts
    kind_chart = by_kind[(by_kind["e26"] >= 500) | (by_kind["e26"].abs() + by_kind["e25"].abs() >= 1000)].head(12)

    top = sub.sort_values("H1'26 EUR", ascending=False).head(TOP_N)
    growers = sub.sort_values("Delta EUR", ascending=False).head(GROWER_N)
    decliners = sub.sort_values("Delta EUR", ascending=True).head(GROWER_N)

    mapped = sub["vehicle_model"].astype(str).str.strip().ne("")
    e26 = float(g["e26"])
    cov = (
        round(float(sub.loc[mapped, "H1'26 EUR"].sum() / e26 * 100), 1)
        if e26 and mapped.any()
        else 0.0
    )

    def pn_rows(frame: pd.DataFrame) -> list[dict]:
        out = []
        for _, r in frame.iterrows():
            out.append(
                {
                    "pn": str(r["PN"]),
                    "desc": str(r["description"] or "")[:60],
                    "kind": str(r["kind"] or ""),
                    "model": (str(r["vehicle_model"] or "").strip() or "model unknown"),
                    "e25": round(float(r["H1'25 EUR"])),
                    "e26": round(float(r["H1'26 EUR"])),
                    "de": round(float(r["Delta EUR"])),
                    "q26": int(round(float(r["H1'26 qty"]))),
                }
            )
        return out

    return {
        "id": re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "other",
        "name": name,
        "kpi": {
            "e25": round(float(g["e25"]), 2),
            "e26": round(float(g["e26"]), 2),
            "de": round(float(g["de"]), 2),
            "dpct": g["dpct"] if pd.notna(g.get("dpct")) else None,
            "q25": int(round(float(g["q25"]))),
            "q26": int(round(float(g["q26"]))),
            "n_pn": int(g["n_pn"]),
            "model_cov_eur26_pct": cov,
            "n_mapped_pn": int(mapped.sum()),
        },
        "by_kind": [
            {
                "kind": str(r.kind),
                "e25": round(float(r.e25)),
                "e26": round(float(r.e26)),
                "de": round(float(r.de)),
                "q26": int(round(float(r.q26))),
                "n_pn": int(r.n_pn),
            }
            for r in kind_chart.itertuples()
        ],
        "top": pn_rows(top),
        "growers": pn_rows(growers),
        "decliners": pn_rows(decliners),
    }


def write_html(payload: dict, out_html: Path) -> None:
    chart_src = CHART_JS.read_text(encoding="utf-8")
    chart_src = re.sub(r"//# sourceMappingURL=.*$", "", chart_src).strip()
    data_json = json.dumps(payload, ensure_ascii=False)
    # Escape </script> in JSON
    data_json = data_json.replace("</", "<\\/")

    kpi = payload["kpi"]
    de_cls = "up" if kpi["de"] >= 0 else "down"
    de_txt = f"{euro_delta(kpi['de'])} ({kpi['dpct']}%)" if kpi["dpct"] is not None else euro_delta(kpi["de"])

    tab_btns = ['<button class="tab active" data-tab="overview">Overview</button>']
    for g in payload["groups"]:
        tab_btns.append(
            f'<button class="tab" data-tab="{g["id"]}">{g["name"]}</button>'
        )
    tabs_html = "\n    ".join(tab_btns)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>{payload["meta"]["display"]} — All parts groups · H1 2025 vs H1 2026</title>
<style>
:root {{ --navy:#0f2744; --terra:#c4652a; --bg:#f7f5f2; --ink:#1a1a1a; --muted:#5c6570; --line:#d9d3c9; --ok:#1f6b3a; --bad:#a33; }}
* {{ box-sizing: border-box; }}
body {{ margin:0; font-family: "Segoe UI", Calibri, sans-serif; background:var(--bg); color:var(--ink); }}
header {{ background:var(--navy); color:#fff; padding:28px 36px 18px; }}
header h1 {{ margin:0 0 6px; font-size:26px; font-weight:650; }}
header p {{ margin:0; opacity:.85; font-size:14px; }}
.tabs {{ display:flex; flex-wrap:wrap; gap:6px; margin-top:16px; }}
.tab {{ background:rgba(255,255,255,.1); color:#fff; border:1px solid rgba(255,255,255,.25);
  padding:7px 12px; font-size:12px; cursor:pointer; border-radius:2px; }}
.tab:hover {{ background:rgba(255,255,255,.2); }}
.tab.active {{ background:#fff; color:var(--navy); font-weight:600; border-color:#fff; }}
main {{ max-width:1180px; margin:0 auto; padding:24px 20px 48px; }}
.panel {{ display:none; }}
.panel.active {{ display:block; }}
.kpis {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin:0 0 18px; }}
.kpi {{ background:#fff; border:1px solid var(--line); padding:14px 16px; }}
.kpi .l {{ font-size:11px; text-transform:uppercase; letter-spacing:.04em; color:var(--muted); }}
.kpi .v {{ font-size:22px; font-weight:700; color:var(--navy); margin-top:4px; }}
.kpi .v.up {{ color:var(--ok); }}
.kpi .v.down {{ color:var(--bad); }}
.card {{ background:#fff; border:1px solid var(--line); padding:18px 20px; margin-bottom:16px; }}
.card h2 {{ margin:0 0 4px; font-size:17px; color:var(--navy); }}
.card .sub, .note {{ margin:0 0 12px; font-size:12px; color:var(--muted); }}
.card.warn {{ border-left:4px solid var(--terra); }}
.grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; }}
th, td {{ padding:7px 8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }}
th {{ font-size:11px; text-transform:uppercase; color:var(--muted); }}
td.n {{ text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }}
td.de-up {{ color:var(--ok); }}
td.de-down {{ color:var(--bad); }}
footer {{ font-size:11px; color:var(--muted); margin-top:20px; }}
@media (max-width:900px) {{ .kpis,.grid2 {{ grid-template-columns:1fr 1fr; }} }}
@media (max-width:560px) {{ .kpis,.grid2 {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body>
<header>
  <h1>{payload["meta"]["display"]} — All parts groups</h1>
  <p>Commercial (ex-warranty) · Calendar H1 2025 vs H1 2026 · {payload["meta"]["name"]} · sold-to {payload["meta"].get("sold_to")} · pr00_group tabs</p>
  <div class="tabs" id="tabs">
    {tabs_html}
  </div>
</header>
<main>
  <div id="overview" class="panel active">
    <div class="kpis">
      <div class="kpi"><div class="l">H1'25 EUR</div><div class="v">{euro(kpi['e25'])}</div></div>
      <div class="kpi"><div class="l">H1'26 EUR</div><div class="v">{euro(kpi['e26'])}</div></div>
      <div class="kpi"><div class="l">Δ EUR</div><div class="v {de_cls}">{de_txt}</div></div>
      <div class="kpi"><div class="l">Model coverage (EUR)</div><div class="v">{kpi['model_cov_eur26_pct']}%</div></div>
    </div>
    <p class="note">{kpi['pn_any']:,} PNs with any H1 activity · {kpi['pn_active_26']:,} active in H1'26 ·
      qty {kpi['q25']:,} → {kpi['q26']:,} · {kpi['n_groups']} pr00 groups ·
      model mapped PNs: {kpi['n_mapped_pn']}</p>
    <div class="grid2">
      <section class="card">
        <h2>H1'26 EUR by parts group</h2>
        <p class="sub">Commercial spend · groups below €{MAJOR_EUR_FLOOR:,.0f} folded into Other on tabs</p>
        <canvas id="ovSpend" height="420"></canvas>
      </section>
      <section class="card">
        <h2>Δ EUR by parts group</h2>
        <p class="sub">H1'26 − H1'25 · net commercial move</p>
        <canvas id="ovDelta" height="420"></canvas>
      </section>
    </div>
    <section class="card">
      <h2>Group scorecard</h2>
      <p class="sub">Click a group tab above for PN detail</p>
      <table>
        <thead><tr><th>Group</th><th class="n">H1'25</th><th class="n">H1'26</th><th class="n">Δ EUR</th><th class="n">Δ %</th><th class="n">PNs</th></tr></thead>
        <tbody id="ovTable"></tbody>
      </table>
    </section>
    <section class="card warn">
      <h2>Model / vehicle fitment</h2>
      <p id="modelNote"></p>
    </section>
  </div>
  <div id="groupPanels"></div>
  <footer>
    Source: {payload["meta"]["display"]} commercial billing H1 cuts (warranty/campaign PNs excluded via claim grain + text heuristic) ·
    Category = pr00_group from parts catalog · Kind = pr00_level3_type ·
    Model labels only when present on BVP/PMS application tables — never guessed ·
    shared shareable view.
  </footer>
</main>
<script>
{chart_src}
</script>
<script>
const DATA = {data_json};
const euroTick = v => {{
  const a = Math.abs(v);
  if (a >= 1e6) return (v<0?'-':'') + '€' + (a/1e6).toFixed(1) + 'M';
  if (a >= 1000) return (v<0?'-':'') + '€' + Math.round(a/1000) + 'k';
  return (v<0?'-':'') + '€' + Math.round(a);
}};
const fmtEuro = n => {{
  const sign = n < 0 ? '-' : '';
  return sign + '€' + Math.abs(n).toLocaleString('en-US', {{maximumFractionDigits:0}});
}};
const fmtDelta = n => (n>0?'+':'') + fmtEuro(n);

const charts = {{}};
function killChart(id) {{
  if (charts[id]) {{ charts[id].destroy(); delete charts[id]; }}
}}

function renderOverview() {{
  const chart = DATA.overview_chart.slice().sort((a,b)=>b.e26-a.e26);
  const delta = DATA.overview_chart.slice().sort((a,b)=>b.de-a.de);
  killChart('ovSpend'); killChart('ovDelta');
  charts.ovSpend = new Chart(document.getElementById('ovSpend'), {{
    type: 'bar',
    data: {{
      labels: chart.map(r=>r.group),
      datasets: [{{ label: "H1'26 EUR", data: chart.map(r=>r.e26), backgroundColor: '#0f2744' }}]
    }},
    options: {{
      indexAxis: 'y',
      plugins: {{ legend: {{ display: false }} }},
      scales: {{ x: {{ title: {{ display:true, text:'EUR' }}, ticks: {{ callback: euroTick }} }} }}
    }}
  }});
  charts.ovDelta = new Chart(document.getElementById('ovDelta'), {{
    type: 'bar',
    data: {{
      labels: delta.map(r=>r.group),
      datasets: [{{
        label: 'Δ EUR',
        data: delta.map(r=>r.de),
        backgroundColor: delta.map(r => r.de>=0 ? '#1f6b3a' : '#a33')
      }}]
    }},
    options: {{
      indexAxis: 'y',
      plugins: {{ legend: {{ display: false }} }},
      scales: {{ x: {{ title: {{ display:true, text:'Δ EUR' }}, ticks: {{ callback: euroTick }} }} }}
    }}
  }});
  const tb = document.getElementById('ovTable');
  tb.innerHTML = DATA.overview_groups.map(r => {{
    const cls = r.de>=0 ? 'de-up' : 'de-down';
    const dp = r.dpct==null ? '—' : ((r.dpct>0?'+':'') + r.dpct + '%');
    return `<tr><td>${{r.group}}</td><td class="n">${{fmtEuro(r.e25)}}</td><td class="n">${{fmtEuro(r.e26)}}</td>
      <td class="n ${{cls}}">${{fmtDelta(r.de)}}</td><td class="n ${{cls}}">${{dp}}</td><td class="n">${{r.n_pn}}</td></tr>`;
  }}).join('');
  const k = DATA.kpi;
  document.getElementById('modelNote').innerHTML =
    k.model_cov_eur26_pct === 0
      ? `<strong>0% of H1'26 EUR has a vehicle-model label.</strong> BVP/PMS application tables cover only a thin addressable basket.
         Body and many structural/lighting PNs have no fitment here. Treat model columns as blank until Snap-on EPC enrichment is run for a group.`
      : `Model labels cover <strong>${{k.model_cov_eur26_pct}}%</strong> of H1'26 EUR (${{k.n_mapped_pn}} PNs). Unmapped rows show as “model unknown” — never guessed.`;
}}

function pnTable(rows) {{
  return `<table><thead><tr><th>PN</th><th>Description</th><th>Kind</th><th>Model</th><th class="n">H1'26</th><th class="n">Δ EUR</th></tr></thead>
  <tbody>${{rows.map(r => {{
    const cls = r.de>=0 ? 'de-up' : 'de-down';
    return `<tr><td>${{r.pn}}</td><td>${{r.desc}}</td><td>${{r.kind}}</td><td>${{r.model}}</td>
      <td class="n">${{fmtEuro(r.e26)}}</td><td class="n ${{cls}}">${{fmtDelta(r.de)}}</td></tr>`;
  }}).join('')}}</tbody></table>`;
}}

function buildGroupPanels() {{
  const host = document.getElementById('groupPanels');
  host.innerHTML = DATA.groups.map(g => {{
    const k = g.kpi;
    const deCls = k.de>=0 ? 'up' : 'down';
    const deTxt = k.dpct==null ? fmtDelta(k.de) : `${{fmtDelta(k.de)}} (${{k.dpct}}%)`;
    const folded = g.folded_groups
      ? `<p class="sub">Folded groups (each under €${{DATA.meta.folded_floor_eur.toLocaleString()}} peak): ` +
        g.folded_groups.map(f => `${{f.group}} ${{fmtDelta(f.de)}}`).join(' · ') + `</p>`
      : '';
    const modelWarn = k.model_cov_eur26_pct === 0
      ? `<section class="card warn"><h2>Model / vehicle fitment</h2>
         <p><strong>0% coverage</strong> for this group on BVP/PMS tables. PN rows show “model unknown”.</p></section>`
      : `<section class="card"><h2>Model / vehicle fitment</h2>
         <p class="sub">${{k.model_cov_eur26_pct}}% of H1'26 EUR · ${{k.n_mapped_pn}} mapped PNs</p></section>`;
    return `<div id="${{g.id}}" class="panel" data-group="${{g.id}}">
      <div class="kpis">
        <div class="kpi"><div class="l">H1'25 EUR</div><div class="v">${{fmtEuro(k.e25)}}</div></div>
        <div class="kpi"><div class="l">H1'26 EUR</div><div class="v">${{fmtEuro(k.e26)}}</div></div>
        <div class="kpi"><div class="l">Δ EUR</div><div class="v ${{deCls}}">${{deTxt}}</div></div>
        <div class="kpi"><div class="l">Qty H1'25 → H1'26</div><div class="v">${{k.q25.toLocaleString()}} → ${{k.q26.toLocaleString()}}</div></div>
      </div>
      <p class="note">${{g.name}} · ${{k.n_pn}} PNs · model coverage ${{k.model_cov_eur26_pct}}% of H1'26 EUR</p>
      ${{folded}}
      <div class="grid2">
        <section class="card">
          <h2>H1'26 EUR by kind / level-3</h2>
          <p class="sub">pr00_level3_type (catalog)</p>
          <canvas id="kind-${{g.id}}" height="300"></canvas>
        </section>
        <section class="card">
          <h2>Δ EUR by kind / level-3</h2>
          <p class="sub">H1'26 − H1'25</p>
          <canvas id="dkind-${{g.id}}" height="300"></canvas>
        </section>
      </div>
      ${{modelWarn}}
      <section class="card">
        <h2>Top ${{g.top.length}} PNs by H1'26 EUR</h2>
        ${{pnTable(g.top)}}
      </section>
      <div class="grid2">
        <section class="card">
          <h2>Top growers (Δ EUR)</h2>
          ${{pnTable(g.growers)}}
        </section>
        <section class="card">
          <h2>Top decliners (Δ EUR)</h2>
          ${{pnTable(g.decliners)}}
        </section>
      </div>
    </div>`;
  }}).join('');
}}

function renderGroupCharts(id) {{
  const g = DATA.groups.find(x => x.id === id);
  if (!g) return;
  const kinds = g.by_kind.slice().sort((a,b)=>b.e26-a.e26);
  const dkind = g.by_kind.slice().sort((a,b)=>b.de-a.de);
  killChart('kind-'+id); killChart('dkind-'+id);
  const c1 = document.getElementById('kind-'+id);
  const c2 = document.getElementById('dkind-'+id);
  if (!c1 || !kinds.length) return;
  charts['kind-'+id] = new Chart(c1, {{
    type: 'bar',
    data: {{
      labels: kinds.map(r=>r.kind),
      datasets: [{{ label: "H1'26 EUR", data: kinds.map(r=>r.e26), backgroundColor: '#0f2744' }}]
    }},
    options: {{
      indexAxis: 'y',
      plugins: {{ legend: {{ display: false }} }},
      scales: {{ x: {{ ticks: {{ callback: euroTick }} }} }}
    }}
  }});
  charts['dkind-'+id] = new Chart(c2, {{
    type: 'bar',
    data: {{
      labels: dkind.map(r=>r.kind),
      datasets: [{{
        label: 'Δ EUR',
        data: dkind.map(r=>r.de),
        backgroundColor: dkind.map(r => r.de>=0 ? '#1f6b3a' : '#a33')
      }}]
    }},
    options: {{
      indexAxis: 'y',
      plugins: {{ legend: {{ display: false }} }},
      scales: {{ x: {{ ticks: {{ callback: euroTick }} }} }}
    }}
  }});
}}

function showTab(id) {{
  document.querySelectorAll('.tab').forEach(b => b.classList.toggle('active', b.dataset.tab===id));
  document.querySelectorAll('.panel').forEach(p => p.classList.toggle('active', p.id===id));
  if (id === 'overview') renderOverview();
  else renderGroupCharts(id);
}}

document.getElementById('tabs').addEventListener('click', e => {{
  const b = e.target.closest('.tab');
  if (!b) return;
  showTab(b.dataset.tab);
}});

buildGroupPanels();
showTab('overview');
</script>
</body>
</html>
"""
    out_html.write_text(html, encoding="utf-8")
    https_hits = re.findall(r'(?:src|href)\s*=\s*["\']https?://', html, flags=re.I)
    internal = "INTERNAL" in html.upper() and "shared" not in html  # soft check
    print(f"Wrote {out_html}")
    print(f"  external https src/href count={len(https_hits)}")
    print(f"  size={out_html.stat().st_size:,} bytes")
    if https_hits:
        raise SystemExit("HTML has external CDN refs — not allowed")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, help="Profile key e.g. HUNGARY, IBX")
    ap.add_argument("--floor", type=float, default=None,
                    help="Min EUR peak for own tab")
    args = ap.parse_args()
    db_key = args.db.upper()
    global MAJOR_EUR_FLOOR
    if args.floor is not None:
        MAJOR_EUR_FLOOR = float(args.floor)

    meet = C.OUT_ROOT / f"{db_key}_Sales_Review_2026"
    meet.mkdir(parents=True, exist_ok=True)
    out_csv = meet / f"{db_key}_all_groups_H1_2025_2026.csv"
    out_html = meet / f"{db_key}_All_parts_groups_H1_dashboard.html"

    print(f"Loading {db_key} commercial H1 …")
    df, meta = load_commercial_pn(db_key)
    prior = meta["commercial_prior"]
    curr = meta["commercial_current"]
    if prior:
        print(f"  commercial {prior:,.0f} → {curr:,.0f} ({(curr/prior-1)*100:+.1f}%)")
    else:
        print(f"  commercial prior=0 → {curr:,.0f}")
    print(f"  PN rows: {len(df):,} · groups: {df['pr00_group'].nunique()}")

    df.to_csv(out_csv, index=False)
    print(f"Wrote {out_csv}")

    payload = build_payload(df, meta)
    (meet / "_all_groups_payload_kpi.json").write_text(
        json.dumps({"kpi": payload["kpi"], "meta": payload["meta"],
                     "tabs": [g["name"] for g in payload["groups"]]}, indent=2),
        encoding="utf-8",
    )
    write_html(payload, out_html)
    print("Tabs:", "Overview |", " | ".join(g["name"] for g in payload["groups"]))
    print(
        f"Headline Δ: {payload['kpi']['de']:+,.0f} EUR ({payload['kpi']['dpct']}%) · "
        f"model cov {payload['kpi']['model_cov_eur26_pct']}%"
    )
    print(f"OPEN: {out_html}")


if __name__ == "__main__":
    main()
