"""Emit internal Action Ledger hub HTML + OPEN_*.cmd (no browser launch)."""

from __future__ import annotations

import html
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ISZE = Path(__file__).resolve().parents[2]
DERIVED = ISZE / "01_data" / "00_derived"
OPS = ISZE / "02_dashboards" / "ops"
BUILD = ISZE / "01_data" / "91_build"
DOCS = ISZE / "00_docs"

OUT_HTML = OPS / "ISZE_Action_Ledger_Hub.html"
OUT_CMD = OPS / "OPEN_ACTION_LEDGER_HUB.cmd"

NAVY = "#15233c"
TERRA = "#c0552d"
PAPER = "#f7f4ee"


def file_url(path: Path) -> str:
    """file:///C:/... absolute URL for Windows paths."""
    return path.resolve().as_uri()


def esc(s: object) -> str:
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return "—"
    t = str(s).strip()
    if not t or t.lower() in ("nan", "none", "null"):
        return "—"
    return html.escape(t)


def fmt_eur(v: object) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    try:
        n = float(v)
    except (TypeError, ValueError):
        return "—"
    if pd.isna(n):
        return "—"
    return f"€{n:,.2f}"


def fmt_int(n: int) -> str:
    return f"{n:,}"


def load_kpis() -> dict:
    meta_path = DERIVED / "action_ledger.meta.json"
    meta: dict = {}
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))

    open_count = int(meta.get("counts", {}).get("open", 0))
    rejects = int(meta.get("counts", {}).get("rejects", 0))
    outcomes = int(meta.get("counts", {}).get("outcomes", 0))
    horizon = meta.get("billing_horizon", "—")
    produced = meta.get("produced_at", "")
    run_id = meta.get("run_id", "")

    eur_open = 0.0
    price_revision_n = 0
    open_csv = DERIVED / "action_ledger_open.csv"
    if open_csv.exists():
        odf = pd.read_csv(open_csv)
        if "eur_at_stake" in odf.columns:
            eur_open = float(odf["eur_at_stake"].fillna(0).sum())
        if open_count == 0:
            open_count = len(odf)
        if "signal_type" in odf.columns:
            price_revision_n = int((odf["signal_type"].astype(str) == "PRICE_REVISION").sum())

    rej_csv = DERIVED / "action_ledger_rejects.csv"
    if rej_csv.exists():
        rejects = len(pd.read_csv(rej_csv))

    # NOT_MEASURABLE lives on outcomes; empty until ACTIONED + past horizon
    not_meas = 0
    hist = DERIVED / "action_ledger_history.parquet"
    if hist.exists():
        try:
            hdf = pd.read_parquet(hist)
            for col in ("outcome_status", "outcome_state", "status"):
                if col in hdf.columns:
                    vc = hdf[col].astype(str).str.upper()
                    not_meas = int((vc == "NOT_MEASURABLE").sum())
                    break
        except Exception:
            pass

    return {
        "open_count": open_count,
        "price_revision_n": price_revision_n,
        "eur_open": eur_open,
        "rejects": rejects,
        "not_meas": not_meas,
        "outcomes": outcomes,
        "horizon": horizon,
        "produced": produced,
        "run_id": run_id,
        "meta": meta,
    }


def load_top_open(n: int = 25) -> pd.DataFrame:
    cols = [
        "opportunity_id",
        "signal_type",
        "db_code",
        "entity_key",
        "eur_at_stake",
        "source_file",
        "source_column",
        "recommended_action",
    ]
    open_csv = DERIVED / "action_ledger_open.csv"
    parquet = DERIVED / "action_ledger.parquet"
    if open_csv.exists():
        df = pd.read_csv(open_csv, usecols=lambda c: c in cols)
    elif parquet.exists():
        df = pd.read_parquet(parquet, columns=[c for c in cols if True])
        df = df[[c for c in cols if c in df.columns]]
    else:
        return pd.DataFrame(columns=cols)

    for c in cols:
        if c not in df.columns:
            df[c] = None
    df["eur_at_stake"] = pd.to_numeric(df["eur_at_stake"], errors="coerce")
    df = df.sort_values("eur_at_stake", ascending=False, na_position="last").head(n)
    return df.reset_index(drop=True)


def review_links() -> list[tuple[str, Path]]:
    reviews = sorted(DERIVED.glob("ACTION_LEDGER_REVIEW_*.md"), reverse=True)
    return [(p.name, p) for p in reviews]


def artefact_rows() -> list[dict]:
    """Label, href, note for link list."""
    rows = [
        {
            "label": "Main Action Ledger (4-view HTML)",
            "path": OPS / "ISZE_Action_Ledger.html",
            "href": "ISZE_Action_Ledger.html",
            "note": "Open / triage / outcomes / rejects views",
        },
        {
            "label": "OPEN_ACTION_LEDGER.cmd",
            "path": OPS / "OPEN_ACTION_LEDGER.cmd",
            "href": "OPEN_ACTION_LEDGER.cmd",
            "note": "Double-click launcher for the main ledger",
        },
    ]
    for name, p in review_links():
        rows.append(
            {
                "label": name,
                "path": p,
                "href": file_url(p),
                "note": "Plain-English review of this ledger run",
            }
        )
    rows.extend(
        [
            {
                "label": "action_ledger_open.csv",
                "path": DERIVED / "action_ledger_open.csv",
                "href": file_url(DERIVED / "action_ledger_open.csv"),
                "note": "Current open book (NEW / TRIAGED / ACTIONED)",
            },
            {
                "label": "action_ledger_decisions.csv",
                "path": DERIVED / "action_ledger_decisions.csv",
                "href": file_url(DERIVED / "action_ledger_decisions.csv"),
                "note": "Human-editable — triage and close decisions here",
            },
            {
                "label": "action_ledger_rejects.csv",
                "path": DERIVED / "action_ledger_rejects.csv",
                "href": file_url(DERIVED / "action_ledger_rejects.csv"),
                "note": "Rows dropped this run with reason",
            },
            {
                "label": "action_ledger.meta.json",
                "path": DERIVED / "action_ledger.meta.json",
                "href": file_url(DERIVED / "action_ledger.meta.json"),
                "note": "Run id, horizon, adapter counts",
            },
            {
                "label": "action_ledger.parquet",
                "path": DERIVED / "action_ledger.parquet",
                "href": file_url(DERIVED),
                "note": "May not open in browser — link opens the derived folder in Explorer",
            },
            {
                "label": "action_ledger_history.parquet",
                "path": DERIVED / "action_ledger_history.parquet",
                "href": file_url(DERIVED),
                "note": "History spine — open derived folder (Explorer)",
            },
            {
                "label": "build_action_ledger.py",
                "path": BUILD / "build_action_ledger.py",
                "href": file_url(BUILD / "build_action_ledger.py"),
                "note": "Ledger builder",
            },
            {
                "label": "action_ledger_adapters.py",
                "path": BUILD / "action_ledger_adapters.py",
                "href": file_url(BUILD / "action_ledger_adapters.py"),
                "note": "Nine surface adapters",
            },
            {
                "label": "PROMPT_ACTION_LEDGER_P8.md",
                "path": DOCS / "PROMPT_ACTION_LEDGER_P8.md",
                "href": file_url(DOCS / "PROMPT_ACTION_LEDGER_P8.md"),
                "note": "P8 closed-loop prompt / contract",
            },
        ]
    )
    return rows


def render_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "<p class=\"lead\">No open rows found.</p>"
    parts = [
        '<div class="table-scroll"><table class="matrix">',
        "<thead><tr>",
        "<th>Signal</th><th>DB</th><th>Entity</th>",
        '<th class="num">€ at stake</th>',
        "<th>Source file</th><th>Source column</th>",
        "<th>Recommended action</th><th>Opportunity id</th>",
        "</tr></thead><tbody>",
    ]
    for _, r in df.iterrows():
        parts.append(
            "<tr>"
            f"<td>{esc(r.get('signal_type'))}</td>"
            f"<td>{esc(r.get('db_code'))}</td>"
            f"<td>{esc(r.get('entity_key'))}</td>"
            f'<td class="num">{fmt_eur(r.get("eur_at_stake"))}</td>'
            f"<td>{esc(r.get('source_file'))}</td>"
            f"<td>{esc(r.get('source_column'))}</td>"
            f"<td>{esc(r.get('recommended_action'))}</td>"
            f"<td><code>{esc(r.get('opportunity_id'))}</code></td>"
            "</tr>"
        )
    parts.append("</tbody></table></div>")
    return "\n".join(parts)


def render_links(rows: list[dict]) -> str:
    items = []
    for row in rows:
        exists = row["path"].exists()
        badge = "" if exists else ' <span class="miss">missing</span>'
        path_txt = html.escape(str(row["path"].resolve()))
        items.append(
            "<li>"
            f'<a href="{html.escape(row["href"])}">{html.escape(row["label"])}</a>{badge}'
            f'<div class="path">{path_txt}</div>'
            f'<div class="note">{html.escape(row["note"])}</div>'
            "</li>"
        )
    return '<ul class="artefacts">\n' + "\n".join(items) + "\n</ul>"


# Honest programme scorecard (0–100). Same numbers as Full Project Audit exec radar.
SCORECARD = [
    ("Core data integrity", 90, 95, "Spine on PRISM is production-grade. Not the commercial blocker."),
    ("Freshness", 58, 90, "Billing through Jun 2026; Jul–Aug SAP extract still missing."),
    ("Sell-out coverage", 28, 90, "5 DBs only. UMI + DE/BE/PT/Nordics missing — SoW/elasticity blocked."),
    ("Price honesty", 55, 85, "Lists landed; list-to-pocket joins not signed off."),
    ("Mail→action", 48, 85, "G0a live; PartSales/StD intake still manual."),
    ("Ops loop", 22, 90, "Ledger built; 0 outcomes until Monday triage closes loops."),
    ("Tender honesty", 45, 85, "Thin sized set + incomplete portals — not market potential."),
    ("Quote / verify gate", 82, 95, "Verify green 116/0/0; keep process bar for external decks."),
]


def _polar(cx: float, cy: float, r: float, i: int, n: int) -> tuple[float, float]:
    ang = -math.pi / 2 + (2 * math.pi * i / n)
    return cx + r * math.cos(ang), cy + r * math.sin(ang)


def render_scorecard_svg() -> str:
    """Self-contained SVG radar — no CDN / Chart.js."""
    n = len(SCORECARD)
    cx = cy = 160.0
    r_max = 110.0
    rings = [25, 50, 75, 100]

    parts = [
        '<svg class="radar-svg" viewBox="0 0 320 320" role="img" '
        'aria-label="Programme scorecard radar 0 to 100">',
    ]
    for ring in rings:
        rr = r_max * ring / 100
        pts = " ".join(
            f"{_polar(cx, cy, rr, i, n)[0]:.1f},{_polar(cx, cy, rr, i, n)[1]:.1f}"
            for i in range(n)
        )
        stroke = "rgba(192,85,45,0.35)" if ring == 100 else "#e1e0d9"
        parts.append(f'<polygon points="{pts}" fill="none" stroke="{stroke}" stroke-width="1"/>')
        if ring in (50, 100):
            parts.append(
                f'<text x="{cx + 4:.0f}" y="{cy - rr + 3:.0f}" class="ring-lab">{ring}</text>'
            )

    for i in range(n):
        x2, y2 = _polar(cx, cy, r_max, i, n)
        parts.append(
            f'<line x1="{cx}" y1="{cy}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#e1e0d9" stroke-width="1"/>'
        )

    def poly(vals: list[int]) -> str:
        return " ".join(
            f"{_polar(cx, cy, r_max * v / 100, i, n)[0]:.1f},"
            f"{_polar(cx, cy, r_max * v / 100, i, n)[1]:.1f}"
            for i, v in enumerate(vals)
        )

    today = [a[1] for a in SCORECARD]
    target = [a[2] for a in SCORECARD]
    parts.append(
        f'<polygon points="{poly(today)}" fill="rgba(42,120,214,0.14)" stroke="#2a78d6" stroke-width="2.5"/>'
    )
    parts.append(
        f'<polygon points="{poly(target)}" fill="none" stroke="#c0552d" stroke-width="2.5" '
        'stroke-dasharray="6 4"/>'
    )
    for i, (label, today_v, tgt_v, tip) in enumerate(SCORECARD):
        tx, ty = _polar(cx, cy, r_max * today_v / 100, i, n)
        gx, gy = _polar(cx, cy, r_max * tgt_v / 100, i, n)
        lx, ly = _polar(cx, cy, r_max + 22, i, n)
        short = (
            label.replace("Core data integrity", "Core data")
            .replace("Sell-out coverage", "Sell-out")
            .replace("Quote / verify gate", "Quote gate")
        )
        tip_esc = html.escape(f"{label}: Today {today_v}/100 · Target {tgt_v}/100 — {tip}")
        parts.append(
            f'<g tabindex="0">'
            f'<title>{tip_esc}</title>'
            f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="4.5" fill="#2a78d6"/>'
            f'<circle cx="{gx:.1f}" cy="{gy:.1f}" r="3.5" fill="#c0552d"/>'
            f'<text x="{lx:.1f}" y="{ly:.1f}" class="axis-lab" text-anchor="middle">'
            f"{html.escape(short)}</text>"
            f"</g>"
        )
    parts.append("</svg>")
    return "\n".join(parts)


def render_scorecard_block() -> str:
    rows = []
    for label, today_v, tgt_v, tip in SCORECARD:
        rows.append(
            "<tr>"
            f"<td>{html.escape(label)}</td>"
            f'<td class="num tip-chip" tabindex="0">{today_v}'
            f'<div class="tip">{html.escape(tip)}</div></td>'
            f'<td class="num">{tgt_v}</td>'
            f"<td>{html.escape(tip)}</td>"
            "</tr>"
        )
    return f"""
  <h2><span class="no">01b</span> Executive scorecard</h2>
  <p class="lead">
    Scale is 0–100. Blue = honest Today. Orange dashed = best-in-class ambition (outer ring, usually 85–95) —
    not a sad mid-chart ring. Hover an axis or score for what is dragging it. Maturity is not painted green.
  </p>
  <div class="score-grid">
    <div class="radar-panel">
      <div class="legend"><span class="lg today"></span> Today &nbsp; <span class="lg target"></span> Best-in-class target</div>
      {render_scorecard_svg()}
    </div>
    <div class="table-scroll"><table class="matrix axis-tips">
      <thead><tr><th>Axis</th><th class="num">Today</th><th class="num">Target</th><th>What is dragging it</th></tr></thead>
      <tbody>
        {"".join(rows)}
      </tbody>
    </table></div>
  </div>
"""


def build_html(kpis: dict, top: pd.DataFrame) -> str:
    produced = kpis["produced"] or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    adapters = kpis["meta"].get("adapter_stats") or []
    n_surfaces = len(adapters) if adapters else 9
    link_block = render_links(artefact_rows())
    table_block = render_table(top)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>ISZE Action Ledger Hub · internal</title>
<style>
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0}}
body{{font-family:"Segoe UI",Helvetica,Arial,sans-serif;color:#222;background:{PAPER};font-size:15px;line-height:1.5}}
h1,h2,h3{{font-family:Georgia,"Times New Roman",serif;color:#1a2b4a;margin:0}}
.hero{{background:linear-gradient(155deg,{NAVY} 0%,#203759 55%,#2b4a78 100%);color:#eef1f6;padding:42px 28px 28px}}
.hero-inner{{max-width:1180px;margin:0 auto}}
.brand{{font-family:Georgia,serif;font-size:13px;letter-spacing:.18em;text-transform:uppercase;color:#c9d4e6;margin-bottom:14px}}
.hero h1{{color:#fff;font-size:34px;line-height:1.12;margin:0 0 12px;font-weight:400}}
.hero .rule{{width:64px;height:3px;background:{TERRA};margin:0 0 16px}}
.hero .lead{{max-width:820px;font-size:15.5px;color:#d5dce8;margin:0 0 22px}}
.hero-kpis{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px}}
.hk{{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.12);padding:14px 16px;position:relative;cursor:help}}
.hk .v{{font-size:28px;font-weight:700;letter-spacing:-.5px;color:#fff}}
.hk .v.sm{{font-size:20px;line-height:1.2}}
.hk .l{{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:#aeb9cb;margin-top:4px}}
.hk .tip{{display:none;position:absolute;left:0;top:calc(100% + 8px);width:min(320px,70vw);
  background:{NAVY};color:{PAPER};border-top:3px solid {TERRA};padding:12px 14px;
  font-size:12.5px;line-height:1.45;z-index:50;box-shadow:0 8px 24px rgba(0,0,0,.25)}}
.hk:hover .tip,.hk:focus-within .tip{{display:block}}
.hk .sub{{font-size:11px;color:#c9d4e6;margin-top:6px;line-height:1.35;font-weight:400}}
.wrap{{max-width:1180px;margin:0 auto;padding:28px 28px 80px}}
h2{{font-size:22px;margin:28px 0 8px;padding-bottom:8px;border-bottom:2px solid #1a2b4a}}
h2 .no{{color:{TERRA}}}
.lead{{color:#6b6256;margin:0 0 18px;max-width:900px}}
.callout{{border-left:3px solid {TERRA};background:#fff;padding:14px 16px;margin:0 0 20px;font-size:14px;color:#222}}
.steps{{margin:0;padding-left:1.2em;color:#222}}
.steps li{{margin-bottom:8px}}
.artefacts{{list-style:none;margin:0;padding:0}}
.artefacts li{{background:#fff;border:1px solid #d9d3c8;border-left:3px solid {TERRA};padding:12px 14px;margin-bottom:10px}}
.artefacts a{{color:{NAVY};font-weight:600;text-decoration:underline}}
.artefacts a:hover{{color:{TERRA}}}
.artefacts .path{{font-size:12px;color:#6b6256;margin-top:4px;word-break:break-all;font-family:Consolas,"Courier New",monospace}}
.artefacts .note{{font-size:13px;color:#6b6256;margin-top:4px}}
.miss{{display:inline-block;margin-left:8px;font-size:11px;text-transform:uppercase;letter-spacing:.04em;
  background:#f8e4dc;color:#8a3030;padding:2px 8px;font-weight:700}}
table.matrix{{width:100%;border-collapse:collapse;font-size:13px;background:#fff}}
.matrix thead th{{background:#1a2b4a;color:{PAPER};text-align:left;padding:8px 10px;font-size:11px;
  text-transform:uppercase;letter-spacing:.05em;position:sticky;top:0;z-index:6}}
.matrix thead th.num,.matrix td.num{{text-align:right;font-variant-numeric:tabular-nums}}
.matrix td{{padding:8px 10px;border-bottom:1px solid #e8e4dc;color:#222;vertical-align:top}}
.matrix tbody tr:nth-child(even) td{{background:#faf8f4;color:#222}}
.matrix tbody tr:hover td{{background:#eef3f9}}
.table-scroll{{overflow-x:auto;margin-bottom:8px;-webkit-overflow-scrolling:touch}}
.score-grid{{display:grid;grid-template-columns:minmax(280px,380px) 1fr;gap:20px;align-items:start;margin:0 0 24px}}
.radar-panel{{background:#fff;border:1px solid #d9d3c8;padding:12px 14px 8px}}
.radar-panel .legend{{font-size:12px;color:#6b6256;margin:0 0 8px}}
.radar-panel .lg{{display:inline-block;width:18px;height:3px;vertical-align:middle;margin-right:4px}}
.radar-panel .lg.today{{background:#2a78d6}}
.radar-panel .lg.target{{background:#c0552d;background-image:repeating-linear-gradient(90deg,#c0552d 0 6px,transparent 6px 10px)}}
.radar-svg{{width:100%;max-width:360px;height:auto;display:block;margin:0 auto}}
.radar-svg .ring-lab{{font-size:9px;fill:#6b6256}}
.radar-svg .axis-lab{{font-size:9px;fill:#15233c;font-family:Georgia,serif}}
.tip-chip{{position:relative;cursor:help}}
.tip-chip .tip{{display:none;position:absolute;left:0;bottom:calc(100% + 8px);width:min(320px,70vw);
  background:{NAVY};color:{PAPER};border-top:3px solid {TERRA};padding:12px 14px;
  font-size:12.5px;line-height:1.45;z-index:50;box-shadow:0 8px 24px rgba(0,0,0,.25)}}
.tip-chip:hover .tip,.tip-chip:focus-within .tip{{display:block}}
.axis-tips td.num{{font-weight:700;color:#15233c}}
code{{font-size:12px;background:#eceae4;padding:1px 5px;color:#222}}
.foot{{margin-top:40px;padding-top:14px;border-top:1px solid #d9d3c8;font-size:11.5px;color:#6b6256;line-height:1.65}}
@media(max-width:900px){{.hero-kpis{{grid-template-columns:1fr 1fr}}.hero h1{{font-size:26px}}.wrap,.hero{{padding-left:16px;padding-right:16px}}.score-grid{{grid-template-columns:1fr}}}}
@media(max-width:560px){{.hero-kpis{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<header class="hero">
  <div class="hero-inner">
    <div class="brand">ISZE · internal · Ops</div>
    <h1>Action Ledger Hub</h1>
    <div class="rule"></div>
    <p class="lead">
      P8 closed the loop: one opportunity → decision → outcome spine over {n_surfaces} existing
      surfaces. Source euros are re-stated unchanged (no re-estimation). Billing horizon for
      measurable outcomes is <strong style="color:#fff">{html.escape(str(kpis["horizon"]))}</strong>.
      This hub is the door — click artefacts below; you do not need to read raw CSVs first.
    </p>
    <div class="hero-kpis" tabindex="0">
      <div class="hk" tabindex="0">
        <div class="v">{fmt_int(kpis["open_count"])}</div>
        <div class="l">Open action rows</div>
        <div class="sub">Not euros — triage inventory</div>
        <div class="tip">Open action rows (NEW / TRIAGED / ACTIONED) — not a euro figure.
          {fmt_int(kpis["price_revision_n"])} of {fmt_int(kpis["open_count"])} are PRICE_REVISION
          exception-queue lines. € at stake is the neighbouring KPI ({fmt_eur(kpis["eur_open"])}, mixed bases).
          Source: action_ledger.meta.json · {html.escape(str(produced))}.</div>
      </div>
      <div class="hk" tabindex="0">
        <div class="v sm">{fmt_eur(kpis["eur_open"])}</div>
        <div class="l">€ at stake (open)</div>
        <div class="tip">Sum of eur_at_stake on open rows — mixed bases (L12M, CY2025, annualised, trailing). Not one wallet; nulls treated as 0 in the sum. Snapshot from action_ledger_open.csv · {html.escape(str(produced))}.</div>
      </div>
      <div class="hk" tabindex="0">
        <div class="v">{fmt_int(kpis["rejects"])}</div>
        <div class="l">Rejects</div>
        <div class="tip">Rows rejected this build run (action_ledger_rejects.csv / meta counts.rejects). Zero means adapters passed lineage without drops this run.</div>
      </div>
      <div class="hk" tabindex="0">
        <div class="v">{fmt_int(kpis["not_meas"])}</div>
        <div class="l">Not measurable</div>
        <div class="tip">Outcome rows marked NOT_MEASURABLE when the billing window cannot close past the horizon. Outcomes stay empty until a decision is ACTIONED and billing is past the horizon — realised_eur is never estimated. Current outcomes count: {kpis["outcomes"]}.</div>
      </div>
      <div class="hk" tabindex="0">
        <div class="v sm">{html.escape(str(kpis["horizon"]))}</div>
        <div class="l">Billing horizon</div>
        <div class="tip">sales_fact billing horizon used for outcome measurability (meta billing_horizon). Past this date, closed windows can score; before it, unmeasurable outcomes stay NOT_MEASURABLE with realised_eur NULL.</div>
      </div>
    </div>
  </div>
</header>

<main class="wrap">
  <h2><span class="no">01</span> What this is / what changed</h2>
  <p class="lead">
    Before P8, signals lived on separate surfaces. The Action Ledger co-moved those into one
    spine so triage and later outcomes share the same opportunity_id. Euros on the ledger are
    the source cells re-stated as-is — attribution stays co-movement language only.
  </p>
  <div class="callout">
    Run <code>{html.escape(str(kpis["run_id"] or "—"))}</code> · produced
    <code>{html.escape(str(produced))}</code> · {n_surfaces} adapters · internal only.
  </div>

  {render_scorecard_block()}

  <h2><span class="no">02</span> Artefacts (clickable)</h2>
  <p class="lead">Links work when this page is opened via OPEN_ACTION_LEDGER_HUB.cmd.</p>
  {link_block}

  <h2><span class="no">03</span> Top open by € (readable preview)</h2>
  <p class="lead">
    Top {len(top)} open opportunities by eur_at_stake — not a substitute for the full ledger,
    just enough to see what is on the book without opening the CSV.
  </p>
  {table_block}

  <h2><span class="no">04</span> Your next step</h2>
  <div class="callout">
    <ol class="steps">
      <li>Open <strong>action_ledger_decisions.csv</strong> (human-editable) and set states:
        <code>TRIAGED</code> → <code>ACTIONED</code> → <code>CLOSED_*</code>.</li>
      <li>Re-run the ledger builder after edits so the open book and history pick up decisions.</li>
      <li>Outcomes stay empty until a row is <code>ACTIONED</code> and billing is past the horizon
        ({html.escape(str(kpis["horizon"]))}). Unmeasurable windows land as
        <code>NOT_MEASURABLE</code> with realised_eur NULL — never estimated.</li>
      <li>Use the main 4-view ledger HTML for day-to-day review; use this hub to find files fast.</li>
    </ol>
  </div>

  <p class="foot">
    internal · internal ops hub · no CDN · house navy/terra · attribution: co-moved, never delivered/caused/drove.
    Rebuild: <code>python 02_dashboards/_build/build_action_ledger_hub.py</code>
  </p>
</main>
</body>
</html>
"""


def main() -> None:
    OPS.mkdir(parents=True, exist_ok=True)
    kpis = load_kpis()
    top = load_top_open(25)
    OUT_HTML.write_text(build_html(kpis, top), encoding="utf-8")
    OUT_CMD.write_text(
        '@echo off\r\nstart "" "%~dp0ISZE_Action_Ledger_Hub.html"\r\n',
        encoding="utf-8",
    )
    print(f"Wrote {OUT_HTML}")
    print(f"Wrote {OUT_CMD}")
    print(
        f"KPIs open={kpis['open_count']} eur={kpis['eur_open']:.2f} "
        f"rejects={kpis['rejects']} not_meas={kpis['not_meas']} "
        f"horizon={kpis['horizon']}"
    )


if __name__ == "__main__":
    main()
