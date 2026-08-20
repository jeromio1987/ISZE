"""
Build 4 self-contained static HTML twins for the new PRISM BI pages.

Reads the derived CSVs fresh and inlines the numbers into standalone HTML
(no CDN, no fetch, no Chart.js) so each file opens by double-click. House style:
navy #15233c, terracotta #c0552d, Georgia headings, paper #f7f4ee.

Run:
    python 02_dashboards/bi/_build_bi_twins.py
Output: 02_dashboards/bi/{Warranty_Intelligence,Price_Realization,Parc_Cohorts,Dealer_Sellout}.html
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ISZE = Path(__file__).resolve().parents[2]
DERIVED = ISZE / "01_data" / "00_derived"
OUT = Path(__file__).resolve().parent

NAVY = "#15233c"
NAVY2 = "#1a2b4a"
PAPER = "#f7f4ee"
INK = "#222"
TERRA = "#c0552d"
MUTED = "#7a766c"
LINE = "#e5e0d6"

SNAPSHOT = "2026-08-20"

CSS = f"""
:root {{ --navy:{NAVY}; --navy2:{NAVY2}; --paper:{PAPER}; --ink:{INK}; --terra:{TERRA}; --muted:{MUTED}; --line:{LINE}; }}
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ background:var(--paper); color:var(--ink); font-family:-apple-system,"Segoe UI",system-ui,sans-serif; font-size:14px; }}
.hero {{ background:linear-gradient(120deg,var(--navy) 0%,var(--navy2) 60%,#24395c 100%); color:var(--paper); padding:1.7rem 2rem 1.4rem; border-bottom:4px solid var(--terra); }}
.hero .kick {{ font-size:.68rem; letter-spacing:.2em; text-transform:uppercase; color:#e8b48c; }}
.hero h1 {{ font-family:Georgia,'Times New Roman',serif; font-size:1.7rem; margin:.3rem 0 .2rem; font-weight:700; }}
.hero p {{ color:#c9cedb; font-size:.88rem; max-width:820px; line-height:1.45; }}
.hero .meta {{ margin-top:.6rem; font-size:.72rem; color:#8fa0bf; }}
.wrap {{ max-width:1060px; margin:0 auto; padding:1.4rem 1.5rem 2.6rem; }}
.kpis {{ display:grid; grid-template-columns:repeat(4,1fr); gap:.9rem; margin:1.1rem 0 1.3rem; }}
.kpi {{ background:#fff; border:1px solid var(--line); border-top:3px solid var(--terra); border-radius:8px; padding:.85rem 1rem; }}
.kpi .v {{ font-family:Georgia,serif; font-size:1.55rem; font-weight:700; color:var(--navy); line-height:1.05; }}
.kpi .l {{ font-size:.64rem; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); margin-top:.3rem; }}
h2 {{ font-family:Georgia,serif; font-size:1.05rem; color:var(--navy); margin:1.5rem 0 .7rem; padding-left:.6rem; border-left:4px solid var(--terra); }}
.card {{ background:#fff; border:1px solid var(--line); border-radius:8px; padding:1rem 1.1rem; }}
.note {{ font-size:.78rem; color:var(--muted); margin-top:.5rem; line-height:1.5; }}
.flag {{ background:#fff6ee; border:1px solid #e6c2ae; color:#8a3d1c; border-radius:6px; padding:.6rem .8rem; font-size:.8rem; margin:.8rem 0; }}
.row {{ display:flex; align-items:center; gap:.6rem; padding:.28rem 0; }}
.row .lbl {{ width:150px; font-size:.82rem; color:var(--ink); }}
.row .track {{ flex:1; background:#f0ece4; border-radius:4px; height:16px; overflow:hidden; }}
.row .fill {{ height:100%; background:var(--navy); border-radius:4px; }}
.row .fill.terra {{ background:var(--terra); }}
.row .fill.mid {{ background:#8fa9c9; }}
.row .val {{ width:110px; text-align:right; font-size:.82rem; font-weight:600; color:var(--navy); font-variant-numeric:tabular-nums; }}
table {{ width:100%; border-collapse:collapse; font-size:.82rem; }}
th {{ background:var(--navy); color:var(--paper); padding:7px 9px; text-align:left; font-weight:600; font-size:.7rem; text-transform:uppercase; letter-spacing:.04em; }}
td {{ padding:6px 9px; border-bottom:1px solid var(--line); }}
tr:nth-child(even) td {{ background:#faf7f1; }}
.foot {{ margin-top:1.8rem; padding-top:.8rem; border-top:1px solid var(--line); color:var(--muted); font-size:.72rem; }}
"""


def _eur(v, dec=0):
    if v is None or pd.isna(v):
        return "—"
    return f"€{v:,.{dec}f}"


def _pct(v, dec=1):
    if v is None or pd.isna(v):
        return "—"
    return f"{v:.{dec}f}%"


def _bar_rows(rows, maxv, color="", fmt=_eur):
    out = []
    for label, val in rows:
        if not val or maxv <= 0:
            continue
        w = min(100.0, val / maxv * 100)
        cls = "fill " + color if color else "fill"
        out.append(
            f'<div class="row"><div class="lbl">{label}</div>'
            f'<div class="track"><div class="{cls}" style="width:{w:.1f}%"></div></div>'
            f'<div class="val">{fmt(val)}</div></div>'
        )
    return "\n".join(out)


def _page(name, hero, body):
    return (
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
        f"<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{name}</title><style>{CSS}</style></head><body>"
        f'<div class="hero"><div class="kick">ISZE · New BI tools</div>'
        f"<h1>{hero['title']}</h1><p>{hero['sub']}</p>"
        f'<div class="meta">Static snapshot · {SNAPSHOT} · self-contained (no live data)</div></div>'
        f'<div class="wrap">{body}</div></body></html>'
    )


# ── 1 · Warranty ──────────────────────────────────────────────────────────────
def build_warranty() -> str:
    df = pd.read_csv(DERIVED / "distributor_warranty_expense_fiscal.csv")
    for c in ["warr_FY2024", "warr_FY2025", "warr_FY2026"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    view = df[df["db"] != "MIDI"]
    t24, t25, t26 = view["warr_FY2024"].sum(), view["warr_FY2025"].sum(), view["warr_FY2026"].sum()
    top = view.sort_values("warr_FY2026", ascending=False).head(12)
    rows = [(r["db"], float(r["warr_FY2026"])) for _, r in top.iterrows()]
    maxv = max(v for _, v in rows) if rows else 1
    tbl = view.sort_values("warr_FY2026", ascending=False)
    trs = "".join(
        f"<tr><td>{r['db']}</td><td>{_eur(r['warr_FY2024'])}</td>"
        f"<td>{_eur(r['warr_FY2025'])}</td><td>{_eur(r['warr_FY2026'])}</td></tr>"
        for _, r in tbl.iterrows()
    )
    body = (
        '<div class="kpis">'
        f'<div class="kpi"><div class="v">{_eur(t26)}</div><div class="l">FY2026 network warranty</div></div>'
        f'<div class="kpi"><div class="v">{_eur(t25)}</div><div class="l">FY2025</div></div>'
        f'<div class="kpi"><div class="v">{_eur(t24)}</div><div class="l">FY2024</div></div>'
        f'<div class="kpi"><div class="v">{len(view)}</div><div class="l">Distributors</div></div>'
        "</div>"
        '<div class="flag">Warranty-parts expense is the line that turns gross parts billing into retained net GPS '
        "(net GPS = gross billing − warranty expense). MIDI (non-GPS channel) is excluded from these totals.</div>"
        f'<h2>FY2026 warranty expense by distributor</h2><div class="card">{_bar_rows(rows, maxv)}</div>'
        f'<h2>Full table (fiscal years)</h2><div class="card"><table><thead><tr>'
        "<th>Distributor</th><th>FY2024</th><th>FY2025</th><th>FY2026</th></tr></thead>"
        f"<tbody>{trs}</tbody></table></div>"
        '<p class="note">Name map: RSA = Norway · Greece = Petros Petropoulos. JPY→EUR at 163.7. '
        'Live equivalent: PRISM page 20 — Warranty Intelligence.</p>'
    )
    return _page("Warranty Intelligence", {"title": "Warranty Intelligence", "sub": "Warranty-parts expense per distributor and fiscal year — the erosion of net GPS."}, body)


# ── 2 · Realization ───────────────────────────────────────────────────────────
def build_realization() -> str:
    net = pd.read_csv(DERIVED / "pr00_realization_network_cy.csv")
    by_db = pd.read_csv(DERIVED / "pr00_realization_by_db_cy.csv")
    zpr1 = pd.read_csv(DERIVED / "zpr1_vs_pr00_by_payer_year.csv")
    latest = net.iloc[-1]
    d25 = by_db[by_db["year"] == 2025].sort_values("realization_pct")
    rows = [(r["db"], float(r["realization_pct"])) for _, r in d25.iterrows()]
    maxv = max(v for _, v in rows) if rows else 1
    # colour: below 90 = terracotta
    rows_html = []
    for label, val in rows:
        color = "terra" if val < 90 else ""
        cls = "fill " + color if color else "fill"
        w = min(100.0, val / 140 * 100) if val else 0
        rows_html.append(
            f'<div class="row"><div class="lbl">{label}</div><div class="track">'
            f'<div class="{cls}" style="width:{w:.1f}%"></div></div>'
            f'<div class="val">{_pct(val)}</div></div>'
        )
    zrows = []
    for _, r in zpr1.iterrows():
        zrows.append(
            f'<div class="row"><div class="lbl">{r["payer"]} · {r["year"]}</div><div class="track">'
            f'<div class="fill terra" style="width:{min(100, abs(r["median_zpr1_vs_pr00_pct"])):.0f}%"></div></div>'
            f'<div class="val">{r["median_zpr1_vs_pr00_pct"]:.1f}%</div></div>'
        )
    body = (
        '<div class="kpis">'
        f'<div class="kpi"><div class="v">{_pct(latest["realization_pct"])}</div><div class="l">Realization (latest)</div></div>'
        f'<div class="kpi"><div class="v">{_pct(latest["coverage_pct"])}</div><div class="l">PR00 coverage</div></div>'
        f'<div class="kpi"><div class="v">{_eur(latest["no_list_eur"])}</div><div class="l">No-list € (blind spot)</div></div>'
        f'<div class="kpi"><div class="v">{latest["year"]} {latest["period"]}</div><div class="l">Period</div></div>'
        "</div>"
        '<div class="flag">Realization is list-vs-billed on <b>net</b> sales — gross / SPA / condition are not available '
        'on the billing extract (closed 2026-08-11). Read as directional until QA is signed.</div>'
        f'<h2>Realization by distributor — 2025 (billed ÷ list value)</h2><div class="card">{"".join(rows_html)}</div>'
        '<p class="note">Terracotta = realization below 90% (pocket erosion). Above 100% = billed above list (data/currency timing).</p>'
        f'<h2>ZPR1 dealer channel vs PR00 list — median gap</h2><div class="card">{"".join(zrows)}</div>'
        '<p class="note">Negative = dealer-channel price sits below list (discount/condition pressure). UTI (1799) ≠ UMI (1797). '
        'Live equivalent: PRISM page 21 — Price Realization.</p>'
    )
    return _page("Price Realization", {"title": "Price Realization", "sub": "List price → pocket (billed ÷ list) by distributor, plus the ZPR1 dealer-channel gap."}, body)


# ── 3 · Parc Cohorts ──────────────────────────────────────────────────────────
def build_parc() -> str:
    v = pd.read_csv(ISZE / "01_data" / "07_UIO" / "vin" / "VIN_register.csv", dtype={"invoice_year": "str"})
    n = len(v)
    pms = int(v["in_pms_rolling_60m"].sum())
    ser = v["series"].value_counts()
    gvw = v["gvw_t"].value_counts().sort_index()
    yr = v["invoice_year"].value_counts().sort_index()
    db = v["db_code"].value_counts().head(10)
    ser_rows = [(k, int(val)) for k, val in ser.items()]
    ser_max = max(val for _, val in ser_rows)
    yr_rows = [(k, int(val)) for k, val in yr.items()]
    yr_max = max(val for _, val in yr_rows)
    body = (
        '<div class="kpis">'
        f'<div class="kpi"><div class="v">{n:,}</div><div class="l">Vehicles in cohort</div></div>'
        f'<div class="kpi"><div class="v">{pms:,}</div><div class="l">In PMS rolling-60m</div></div>'
        f'<div class="kpi"><div class="v">{v["db_code"].nunique()}</div><div class="l">Distributors</div></div>'
        f'<div class="kpi"><div class="v">{pms/n*100:.0f}%</div><div class="l">PMS share</div></div>'
        "</div>"
        '<div class="flag">JP VIN shipment cohort (rolling 60m), <b>ex ITUK / UTI</b>. This is a cohort signal — not the '
        'registered UIO (v19) denominator. Do not compare these counts to UIO totals.</div>'
        f'<h2>Cohort aging — vehicles by invoice year</h2><div class="card">{_bar_rows(yr_rows, yr_max)}</div>'
        f'<h2>Series mix (N vs F)</h2><div class="card">{_bar_rows(ser_rows, ser_max)}</div>'
        f'<h2>Top distributors in cohort</h2><div class="card">{_bar_rows([(k, int(val)) for k, val in db.items()], int(db.iloc[0]))}</div>'
        '<p class="note">GVW classes: 7.5t 1,278 · 8.8t 941 · 8.5t 681 · 9.0t 314 · 8.7t 24. '
        'Live equivalent: PRISM page 22 — Parc Cohorts.</p>'
    )
    return _page("Parc Cohorts", {"title": "Parc Cohorts", "sub": "JP VIN shipment cohort — which vehicles age into the PMS-service window when."}, body)


# ── 4 · Dealer Sell-out ───────────────────────────────────────────────────────
def build_sellout() -> str:
    mix = pd.read_csv(DERIVED / "sellout_aim_network_mix_2025.csv")
    sub = pd.read_csv(DERIVED / "sellout_aim_by_subgroup_2025.csv")
    sell = mix[mix["layer"] == "sellout_db_dlr"]
    spu_rows = [(r["distributor_code"], float(r["sellout_spu_eur"])) for _, r in sell.iterrows()]
    spu_max = max(v for _, v in spu_rows)
    # genuine-only € by subgroup (top 12)
    only = sub[(sub["layer"] == "sellout_db_dlr") & (sub["aim_bucket"] == "genuine_only")]
    by = only.groupby("report_subgroup", as_index=False)["eur"].sum().sort_values("eur", ascending=False).head(12)
    sg_rows = [(r["report_subgroup"], float(r["eur"])) for _, r in by.iterrows()]
    sg_max = max(v for _, v in sg_rows)
    body = (
        '<div class="kpis">'
        f'<div class="kpi"><div class="v">{_eur(sell["total_eur"].sum())}</div><div class="l">Sell-out € (network)</div></div>'
        f'<div class="kpi"><div class="v">{sell["qty_year"].sum():,.0f}</div><div class="l">Sell-out qty</div></div>'
        f'<div class="kpi"><div class="v">{sell["distributor_code"].nunique()}</div><div class="l">Distributors</div></div>'
        f'<div class="kpi"><div class="v">{sell["bvp_pct"].mean()*100:.1f}%</div><div class="l">BVP share (mean)</div></div>'
        "</div>"
        '<div class="flag">Layer: <b>sell-out = DB→dealer</b> (network sell-through) vs billing = ISZE→DB. '
        'IUK ≠ ITUK ≠ IMIE (Ireland) — each is its own market, never blended.</div>'
        f'<h2>Sell-out spend-per-unit (€ per truck)</h2><div class="card">{_bar_rows(spu_rows, spu_max, fmt=lambda v: f"€{v:,.0f}")}</div>'
        f'<h2>Genuine-only € by part subgroup (sell-out)</h2><div class="card">{_bar_rows(sg_rows, sg_max, fmt=lambda v: f"€{v:,.0f}")}</div>'
        '<p class="note">Blue = genuine-only · Terracotta = contested. Live equivalent: PRISM page 23 — Dealer Sell-out.</p>'
    )
    return _page("Dealer Sell-out", {"title": "Dealer Sell-out", "sub": "Multi-DB sell-through vs billing: spend-per-unit and genuine-only mix by part subgroup."}, body)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = [
        ("Warranty_Intelligence.html", build_warranty),
        ("Price_Realization.html", build_realization),
        ("Parc_Cohorts.html", build_parc),
        ("Dealer_Sellout.html", build_sellout),
    ]
    for fname, fn in jobs:
        (OUT / fname).write_text(fn(), encoding="utf-8")
        print(f"wrote {fname}")


if __name__ == "__main__":
    main()
