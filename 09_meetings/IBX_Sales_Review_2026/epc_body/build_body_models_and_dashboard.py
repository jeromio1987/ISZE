"""IBX Body parts: prepare Snap-on EPC scrape pack + enrich + dashboard.

Catalogue: https://isuzu.snaponepc.com/epc/#/
Agent browser cannot see Jerome's Chrome login — scrape runs in HIS Snap-on tab
via DevTools console (same pattern as pms-pilot/epc_scraper_install.js).

Usage:
  python build_body_models_and_dashboard.py                 # pack + dashboard (model blank)
  python build_body_models_and_dashboard.py --from-results  # after console JSON lands
  python build_body_models_and_dashboard.py --top 100

Outputs (meeting folder):
  IBX_Body_parts_with_models_H1_2025_2026.csv
  IBX_Body_parts_H1_dashboard.html
  epc_body/IBX_body_topN_pns.json
  epc_body/PASTE_IN_SNAPON_CONSOLE.js
  epc_body/README.md
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
MEET = ROOT / "09_meetings" / "IBX_Sales_Review_2026"
EPC_DIR = MEET / "epc_body"
BODY_CSV = MEET / "IBX_Body_parts_all_purchases_H1_2025_2026.csv"
OUT_CSV = MEET / "IBX_Body_parts_with_models_H1_2025_2026.csv"
OUT_HTML = MEET / "IBX_Body_parts_H1_dashboard.html"
OUT_JSON = MEET / "_body_canvas_data.json"
CHART_JS = ROOT / "02_dashboards" / "_ui" / "chart.umd.min.js"
SCRAPER_SRC = ROOT / "03_analytics" / "Isuzu" / "pms-pilot" / "epc_scraper_install.js"
PARSE_DIR = ROOT / "03_analytics" / "Isuzu" / "pms-pilot"

sys.path.insert(0, str(PARSE_DIR))
from parse_epc_results import enrich  # noqa: E402

KW_RULES = [
    ("Glass / window", r"GLASS|WINDSHIELD"),
    ("Bumper", r"BUMPER"),
    ("Fender", r"FENDER"),
    ("Panel", r"PANEL|HOOD|SIDE GATE|DEFLECTOR"),
    ("Door", r"DOOR"),
    ("Trim / molding", r"MOLDING|MOULDING|WEATHERSTRIP"),
    ("Grille", r"GRILLE|GRILL"),
    ("Step / guard", r"STEP"),
    ("Handle / lock", r"HANDLE|LATCH|LOCK|HINGE"),
    ("Body structure", r"RAIL|FRAME"),
]


def norm_pn(x) -> str:
    s = str(x).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return s


def kw_kind(desc: str) -> str:
    d = (desc or "").upper()
    for kind, pat in KW_RULES:
        if re.search(pat, d):
            return kind
    return "Other body"


def load_body() -> pd.DataFrame:
    df = pd.read_csv(BODY_CSV)
    df["pn"] = df["PN"].map(norm_pn)
    df["desc"] = df["description"].fillna("").astype(str)
    for c in ["H1'25 EUR", "H1'25 qty", "H1'26 EUR", "H1'26 qty", "Delta EUR", "Delta qty"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    cat = pd.read_csv(
        ROOT / "01_data/00_derived/parts_catalog_dimension.csv",
        dtype=str,
        low_memory=False,
    )
    cat["pn"] = cat["part_number"].map(norm_pn)
    l3 = cat.drop_duplicates("pn").set_index("pn")["pr00_level3_type"].fillna("").to_dict()
    df["kind"] = df["pn"].map(lambda p: (l3.get(p) or "").strip() or "Other body")
    mask = df["kind"].eq("Other body")
    df.loc[mask, "kind"] = df.loc[mask, "desc"].map(kw_kind)
    df["prio"] = df["H1'26 EUR"] + df["Delta EUR"].abs()
    return df


def write_scrape_pack(df: pd.DataFrame, top_n: int) -> list[str]:
    EPC_DIR.mkdir(parents=True, exist_ok=True)
    top = df.sort_values("prio", ascending=False).head(top_n)
    pns = top["pn"].tolist()
    e26 = float(df["H1'26 EUR"].sum())
    cov = float(top["H1'26 EUR"].sum() / e26 * 100) if e26 else 0.0
    (EPC_DIR / f"IBX_body_top{top_n}_pns.json").write_text(
        json.dumps(
            {
                "top_n": top_n,
                "eur26_coverage_pct": round(cov, 1),
                "estimated_minutes_at_12s": round(top_n * 12 / 60, 1),
                "pns": pns,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    scraper = SCRAPER_SRC.read_text(encoding="utf-8")
    # Strip the final console.log so we append our own boot block
    boot = f"""
// === IBX Body parts pack (top {top_n} by H1'26 EUR + |Δ|) ===
// Expected H1'26 EUR coverage if all succeed: ~{cov:.0f}%
// Paste this ENTIRE file into DevTools console on https://isuzu.snaponepc.com/epc/#/
// (must already be logged in and on the EPC home / part search UI)

window.__IBX_BODY_PNS = {json.dumps(pns)};
console.log('IBX Body PNs loaded:', window.__IBX_BODY_PNS.length);
console.log('Start: window.__bgRun(window.__IBX_BODY_PNS, 12000)');
console.log('Progress: window.__bgState');
console.log('When done: window.__downloadResults(\"IBX_body_epc_results.json\")');
console.log('Save the download into: {str(EPC_DIR).replace(chr(92), "/")}');
"""
    (EPC_DIR / "PASTE_IN_SNAPON_CONSOLE.js").write_text(scraper + "\n" + boot, encoding="utf-8")
    readme = f"""# IBX Body → Snap-on EPC model scrape

## Blocker (agent)

Cursor's agent browser has **no tab / cannot attach** to your Chrome session.
Your login at Snap-on EPC is only visible in **your** browser.

## Exact steps (you)

1. Open (or focus) **https://isuzu.snaponepc.com/epc/#/** — stay logged in on the EPC part-search UI.
2. Press **F12** → **Console**.
3. Open `PASTE_IN_SNAPON_CONSOLE.js` in an editor, copy **all**, paste into the console, Enter.
4. Run:
   ```js
   window.__bgRun(window.__IBX_BODY_PNS, 12000)
   ```
   Top {top_n} PNs ≈ {round(top_n * 12 / 60, 1)} min at 12s spacing (~{cov:.0f}% of H1'26 Body EUR).
5. Watch `window.__bgState` until `running: false`.
6. Run:
   ```js
   window.__downloadResults("IBX_body_epc_results.json")
   ```
7. Move the downloaded JSON into this folder:
   `{EPC_DIR}`
8. Tell the agent (or run):
   ```
   python build_body_models_and_dashboard.py --from-results
   ```

## Notes

- Never invent models. Blank = not found / not scraped yet.
- Snap-on may throttle; if many `poll timeout`, stop and resume later with remaining PNs.
- Autodoc scrapers do **not** provide OEM vehicle application for these PNs.
"""
    (EPC_DIR / "README.md").write_text(readme, encoding="utf-8")
    print(f"Scrape pack: top {top_n} PNs (~{cov:.1f}% H1'26 EUR) -> {EPC_DIR}")
    return pns


def find_results() -> Path | None:
    candidates = [
        EPC_DIR / "IBX_body_epc_results.json",
        EPC_DIR / "epc_results.json",
        *sorted(EPC_DIR.glob("*epc*results*.json"), key=lambda p: p.stat().st_mtime, reverse=True),
        *sorted(Path.home().joinpath("Downloads").glob("IBX_body_epc_results*.json"), key=lambda p: p.stat().st_mtime, reverse=True),
    ]
    for p in candidates:
        if p.exists() and p.stat().st_size > 2:
            return p
    return None


def load_epc_map(results_path: Path | None) -> dict[str, dict]:
    if not results_path:
        return {}
    raw = json.loads(results_path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        return {}
    seen: dict[str, dict] = {}
    for r in raw:
        pn = norm_pn(r.get("pn") or "")
        if not pn:
            continue
        if pn not in seen or (seen[pn].get("error") and not r.get("error")):
            seen[pn] = r
    out = {}
    for pn, r in seen.items():
        e = enrich(r)
        # Prefer model series; else vehicle families; never invent
        model = (e.get("epc_model_series") or "").strip()
        fam = (e.get("epc_vehicle_families") or "").strip()
        label = model or fam
        if e.get("epc_error") and not e.get("epc_found") == "Y":
            label = ""
        if e.get("epc_found") != "Y":
            label = label  # keep empty if not found
            if e.get("epc_found") == "N":
                label = ""
        out[pn] = {
            "vehicle_model": label,
            "epc_found": e.get("epc_found", ""),
            "epc_vehicle_families": fam,
            "epc_model_series": model,
            "epc_buckets": e.get("epc_buckets", ""),
            "epc_year_span": e.get("epc_year_span", ""),
            "epc_error": e.get("epc_error", ""),
            "source": f"snaponepc:{results_path.name}",
        }
    print(f"Loaded EPC results: {len(out)} PNs from {results_path}")
    return out


def write_enriched_csv(df: pd.DataFrame, epc: dict[str, dict]) -> pd.DataFrame:
    rows = df.copy()
    rows["vehicle_model"] = rows["pn"].map(lambda p: (epc.get(p) or {}).get("vehicle_model", ""))
    rows["epc_found"] = rows["pn"].map(lambda p: (epc.get(p) or {}).get("epc_found", ""))
    rows["epc_vehicle_families"] = rows["pn"].map(
        lambda p: (epc.get(p) or {}).get("epc_vehicle_families", "")
    )
    rows["epc_model_series"] = rows["pn"].map(lambda p: (epc.get(p) or {}).get("epc_model_series", ""))
    rows["epc_buckets"] = rows["pn"].map(lambda p: (epc.get(p) or {}).get("epc_buckets", ""))
    rows["epc_year_span"] = rows["pn"].map(lambda p: (epc.get(p) or {}).get("epc_year_span", ""))
    rows["model_source"] = rows["pn"].map(lambda p: (epc.get(p) or {}).get("source", ""))
    out = rows[
        [
            "PN",
            "description",
            "kind",
            "vehicle_model",
            "epc_model_series",
            "epc_vehicle_families",
            "epc_buckets",
            "epc_year_span",
            "epc_found",
            "model_source",
            "H1'25 EUR",
            "H1'25 qty",
            "H1'26 EUR",
            "H1'26 qty",
            "Delta EUR",
            "Delta qty",
        ]
    ].sort_values("H1'26 EUR", ascending=False)
    out.to_csv(OUT_CSV, index=False)
    mapped = out["vehicle_model"].astype(str).str.strip().ne("")
    e26 = float(out["H1'26 EUR"].sum())
    cov_pn = float(mapped.mean() * 100) if len(out) else 0.0
    cov_eur = float(out.loc[mapped, "H1'26 EUR"].sum() / e26 * 100) if e26 else 0.0
    print(f"Wrote {OUT_CSV}")
    print(f"Model coverage: {mapped.sum()}/{len(out)} PNs ({cov_pn:.1f}%) · {cov_eur:.1f}% of H1'26 EUR")
    return out


def aggregate(df: pd.DataFrame) -> dict:
    e25 = float(df["H1'25 EUR"].sum())
    e26 = float(df["H1'26 EUR"].sum())
    de = e26 - e25
    mapped = df["vehicle_model"].astype(str).str.strip().ne("")
    by_kind = (
        df.groupby("kind", as_index=False)
        .agg(
            e25=("H1'25 EUR", "sum"),
            e26=("H1'26 EUR", "sum"),
            q26=("H1'26 qty", "sum"),
            n_pn=("pn", "nunique"),
        )
        .sort_values("e26", ascending=False)
    )
    by_kind["de"] = by_kind["e26"] - by_kind["e25"]
    top = df.sort_values("H1'26 EUR", ascending=False).head(15)
    # Model mix: known only; plus explicit unknown bucket for honesty
    tmp = df.copy()
    tmp["model_label"] = tmp["vehicle_model"].where(mapped, "model unknown")
    by_model = (
        tmp.groupby("model_label", as_index=False)
        .agg(e25=("H1'25 EUR", "sum"), e26=("H1'26 EUR", "sum"), n_pn=("pn", "nunique"))
        .sort_values("e26", ascending=False)
    )
    by_model["de"] = by_model["e26"] - by_model["e25"]
    known = by_model[by_model["model_label"] != "model unknown"]
    return {
        "kpi": {
            "e25": round(e25, 2),
            "e26": round(e26, 2),
            "de": round(de, 2),
            "dpct": round(100.0 * de / e25, 1) if e25 else None,
            "q25": int(round(float(df["H1'25 qty"].sum()))),
            "q26": int(round(float(df["H1'26 qty"].sum()))),
            "pn_any": int(len(df)),
            "pn_active_26": int(((df["H1'26 EUR"] > 0) | (df["H1'26 qty"] > 0)).sum()),
            "model_cov_pn_pct": round(float(mapped.mean() * 100), 1),
            "model_cov_eur26_pct": round(float(df.loc[mapped, "H1'26 EUR"].sum() / e26 * 100), 1)
            if e26 and mapped.any()
            else 0.0,
            "n_mapped_pn": int(mapped.sum()),
            "epc_status": "enriched" if mapped.any() else "awaiting_snaponepc_console",
        },
        "by_kind": [
            {
                "kind": r.kind,
                "e25": round(float(r.e25)),
                "e26": round(float(r.e26)),
                "de": round(float(r.de)),
                "q26": int(round(float(r.q26))),
                "n_pn": int(r.n_pn),
            }
            for r in by_kind.itertuples()
        ],
        "top15": [
            {
                "pn": str(r["pn"]),
                "desc": str(r["desc"]),
                "kind": str(r["kind"]),
                "model": (str(r.get("vehicle_model") or "").strip() or "model unknown"),
                "e25": round(float(r["H1'25 EUR"])),
                "e26": round(float(r["H1'26 EUR"])),
                "de": round(float(r["Delta EUR"])),
                "q26": int(round(float(r["H1'26 qty"]))),
            }
            for _, r in top.iterrows()
        ],
        "by_model": [
            {
                "model": r.model_label,
                "e25": round(float(r.e25)),
                "e26": round(float(r.e26)),
                "de": round(float(r.de)),
                "n_pn": int(r.n_pn),
            }
            for r in by_model.itertuples()
        ],
        "known_models": [
            {
                "model": r.model_label,
                "e25": round(float(r.e25)),
                "e26": round(float(r.e26)),
                "de": round(float(r.de)),
                "n_pn": int(r.n_pn),
            }
            for r in known.head(12).itertuples()
        ],
    }


def write_html(data: dict) -> None:
    chart_src = CHART_JS.read_text(encoding="utf-8")
    # strip sourcemap
    chart_src = re.sub(r"//# sourceMappingURL=.*$", "", chart_src).strip()
    kpi = data["kpi"]
    by_kind = data["by_kind"]
    top15 = data["top15"]
    known = data["known_models"]
    has_models = kpi["n_mapped_pn"] > 0

    kind_labels = json.dumps([r["kind"] for r in by_kind if r["e26"] >= 1000])
    kind_e26 = json.dumps([r["e26"] for r in by_kind if r["e26"] >= 1000])
    kind_de = json.dumps([r["de"] for r in by_kind])
    kind_de_labels = json.dumps([r["kind"] for r in sorted(by_kind, key=lambda x: -x["de"])])
    kind_de_vals = json.dumps([r["de"] for r in sorted(by_kind, key=lambda x: -x["de"])])

    model_block = ""
    if has_models:
        ml = json.dumps([r["model"] for r in known])
        mv = json.dumps([r["e26"] for r in known])
        model_block = f"""
    <section class="card">
      <h2>Model mix (EPC-known only)</h2>
      <p class="sub">Coverage: {kpi['model_cov_pn_pct']}% of PNs · {kpi['model_cov_eur26_pct']}% of H1'26 EUR. Blank rows not invented.</p>
      <canvas id="cModel" height="280"></canvas>
    </section>
    <script>
    new Chart(document.getElementById('cModel'), {{
      type: 'bar',
      data: {{ labels: {ml}, datasets: [{{ label: "H1'26 EUR", data: {mv}, backgroundColor: '#c4652a' }}] }},
      options: {{ indexAxis: 'y', plugins: {{ legend: {{ display: false }} }},
        scales: {{ x: {{ title: {{ display: true, text: 'EUR' }}, ticks: {{ callback: v => '€'+(v/1000).toFixed(0)+'k' }} }} }} }}
    }});
    </script>
"""
    else:
        model_block = """
    <section class="card warn">
      <h2>Model / vehicle fitment</h2>
      <p><strong>0% coverage so far.</strong> BVP/PMS tables have no Body fitment.
      Snap-on EPC login is in your Chrome — not visible to the agent browser.
      Run the console pack in <code>epc_body/PASTE_IN_SNAPON_CONSOLE.js</code> on
      <code>https://isuzu.snaponepc.com/epc/#/</code>, then re-run the enricher.</p>
    </section>
"""

    top_rows = "".join(
        f"<tr><td>{r['pn']}</td><td>{r['desc']}</td><td>{r['kind']}</td>"
        f"<td>{r['model']}</td><td class='n'>€{r['e26']:,}</td>"
        f"<td class='n'>{'+' if r['de']>=0 else ''}€{r['de']:,}</td></tr>"
        for r in top15
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>IBX Body parts — H1 2025 vs H1 2026</title>
<style>
:root {{ --navy:#0f2744; --terra:#c4652a; --bg:#f7f5f2; --ink:#1a1a1a; --muted:#5c6570; --line:#d9d3c9; }}
* {{ box-sizing: border-box; }}
body {{ margin:0; font-family: "Segoe UI", Calibri, sans-serif; background:var(--bg); color:var(--ink); }}
header {{ background:var(--navy); color:#fff; padding:28px 36px; }}
header h1 {{ margin:0 0 6px; font-size:26px; font-weight:650; }}
header p {{ margin:0; opacity:.85; font-size:14px; }}
main {{ max-width:1120px; margin:0 auto; padding:24px 20px 48px; }}
.kpis {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin:18px 0 22px; }}
.kpi {{ background:#fff; border:1px solid var(--line); padding:14px 16px; }}
.kpi .l {{ font-size:11px; text-transform:uppercase; letter-spacing:.04em; color:var(--muted); }}
.kpi .v {{ font-size:22px; font-weight:700; color:var(--navy); margin-top:4px; }}
.kpi .v.up {{ color:#1f6b3a; }}
.card {{ background:#fff; border:1px solid var(--line); padding:18px 20px; margin-bottom:16px; }}
.card h2 {{ margin:0 0 4px; font-size:17px; color:var(--navy); }}
.card .sub {{ margin:0 0 12px; font-size:12px; color:var(--muted); }}
.card.warn {{ border-left:4px solid var(--terra); }}
.grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; }}
th, td {{ padding:7px 8px; border-bottom:1px solid var(--line); text-align:left; }}
th {{ font-size:11px; text-transform:uppercase; color:var(--muted); }}
td.n {{ text-align:right; font-variant-numeric:tabular-nums; }}
footer {{ font-size:11px; color:var(--muted); margin-top:20px; }}
@media (max-width:800px) {{ .kpis,.grid2 {{ grid-template-columns:1fr 1fr; }} }}
@media (max-width:520px) {{ .kpis,.grid2 {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body>
<header>
  <h1>IBX — Body parts purchases</h1>
  <p>Commercial (ex-warranty) · Calendar H1 2025 vs H1 2026 · pr00_group Body parts</p>
</header>
<main>
  <div class="kpis">
    <div class="kpi"><div class="l">H1'25 EUR</div><div class="v">€{kpi['e25']:,.0f}</div></div>
    <div class="kpi"><div class="l">H1'26 EUR</div><div class="v">€{kpi['e26']:,.0f}</div></div>
    <div class="kpi"><div class="l">Δ EUR</div><div class="v up">+€{kpi['de']:,.0f} ({kpi['dpct']}%)</div></div>
    <div class="kpi"><div class="l">Model coverage (EUR)</div><div class="v">{kpi['model_cov_eur26_pct']}%</div></div>
  </div>
  <p class="sub" style="margin:-8px 0 16px;color:var(--muted);font-size:12px;">
    {kpi['pn_any']} PNs with any H1 activity · {kpi['pn_active_26']} active in H1'26 ·
    qty {kpi['q25']:,} → {kpi['q26']:,} · model mapped PNs: {kpi['n_mapped_pn']}
  </p>

  <div class="grid2">
    <section class="card">
      <h2>H1'26 EUR by part kind</h2>
      <p class="sub">Keyword / level-3 classification — not model fitment</p>
      <canvas id="cKind" height="300"></canvas>
    </section>
    <section class="card">
      <h2>Δ EUR by part kind</h2>
      <p class="sub">H1'26 − H1'25 · Glass and panels lead the +€102k net</p>
      <canvas id="cDelta" height="300"></canvas>
    </section>
  </div>

  {model_block}

  <section class="card">
    <h2>Top 15 PNs by H1'26 EUR</h2>
    <p class="sub">Model column filled only from Snap-on EPC scrape — never guessed</p>
    <table>
      <thead><tr><th>PN</th><th>Description</th><th>Kind</th><th>Model / family</th><th>H1'26</th><th>Δ EUR</th></tr></thead>
      <tbody>{top_rows}</tbody>
    </table>
  </section>

  <footer>
    Source: IBX commercial billing H1 cuts · Body = pr00_group Body parts ·
    Model source: Snap-on EPC when scraped · EPC status: {kpi['epc_status']}
  </footer>
</main>
<script>
{chart_src}
</script>
<script>
const euro = v => '€' + (Math.abs(v)>=1000 ? (v/1000).toFixed(0)+'k' : Math.round(v));
new Chart(document.getElementById('cKind'), {{
  type: 'bar',
  data: {{ labels: {kind_labels}, datasets: [{{ label: "H1'26 EUR", data: {kind_e26}, backgroundColor: '#0f2744' }}] }},
  options: {{ indexAxis: 'y', plugins: {{ legend: {{ display: false }} }},
    scales: {{ x: {{ title: {{ display: true, text: 'EUR' }}, ticks: {{ callback: euro }} }} }} }}
}});
new Chart(document.getElementById('cDelta'), {{
  type: 'bar',
  data: {{ labels: {kind_de_labels}, datasets: [{{
    label: 'Δ EUR', data: {kind_de_vals},
    backgroundColor: {kind_de_vals}.map(v => v>=0 ? '#1f6b3a' : '#a33')
  }}] }},
  options: {{ indexAxis: 'y', plugins: {{ legend: {{ display: false }} }},
    scales: {{ x: {{ title: {{ display: true, text: 'Δ EUR' }}, ticks: {{ callback: euro }} }} }} }}
}});
</script>
</body>
</html>
"""
    OUT_HTML.write_text(html, encoding="utf-8")
    # verify no external src/href with https
    https_hits = re.findall(r'(?:src|href)\s*=\s*["\']https?://', html, flags=re.I)
    print(f"Wrote {OUT_HTML} · external https src/href count={len(https_hits)}")


def write_canvas_json(data: dict) -> None:
    OUT_JSON.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_JSON}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=100, help="Top N PNs for Snap-on scrape pack")
    ap.add_argument("--from-results", action="store_true", help="Require EPC results JSON")
    ap.add_argument("--results", type=str, default="", help="Path to epc results JSON")
    args = ap.parse_args()

    df = load_body()
    write_scrape_pack(df, args.top)

    results_path = Path(args.results) if args.results else find_results()
    if args.from_results and not results_path:
        raise SystemExit(
            "No EPC results JSON found. Paste console pack on Snap-on, download "
            f"IBX_body_epc_results.json into {EPC_DIR}, then re-run."
        )
    epc = load_epc_map(results_path)
    # need pn/desc on enriched for aggregate
    enriched = write_enriched_csv(df, epc)
    work = df.merge(
        enriched[["PN", "vehicle_model"]],
        left_on="PN",
        right_on="PN",
        how="left",
        suffixes=("", "_e"),
    )
    if "vehicle_model_e" in work.columns:
        work["vehicle_model"] = work["vehicle_model_e"].fillna("")
    elif "vehicle_model" not in work.columns:
        work["vehicle_model"] = ""
    work["vehicle_model"] = work["vehicle_model"].fillna("").astype(str)
    data = aggregate(work)
    write_canvas_json(data)
    write_html(data)
    print("Done.")


if __name__ == "__main__":
    main()
