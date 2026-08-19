"""Build Belgium IDS Kaizen HTML from live v1.4 country compare. No Send."""
from __future__ import annotations

import csv
import json
import re
from html import escape
from pathlib import Path

from ids_paths import ISZE_ROOT

SRC = ISZE_ROOT / "02_dashboards" / "ids" / "IDS_2026_dealer_compare_Belgium.html"
OUT = ISZE_ROOT / "02_dashboards" / "ids" / "IDS_2026_Kaizen_Belgium.html"
CMD = ISZE_ROOT / "02_dashboards" / "ids" / "OPEN_IDS_2026_Kaizen_Belgium.cmd"
PACK = (
    ISZE_ROOT
    / "09_meetings"
    / "IDS_2026_Country_Packs_v1.4"
    / "Belgium"
    / "IDS_2026_Kaizen_Belgium.html"
)
PMS = ISZE_ROOT / "01_data" / "00_derived" / "pms_summary_by_db.csv"

BAND_GOOD = 0.80
BAND_MED = 0.60


def pct(v: float | None) -> str:
    return "—" if v is None else f"{v * 100:.1f}%"


def pp(v: float | None) -> str:
    return "—" if v is None else f"{v * 100:+.1f} pp"


def pts(score: float, mx: float) -> str:
    def fmt(x: float) -> str:
        if abs(x - round(x)) < 1e-6:
            return str(int(round(x)))
        return f"{x:.1f}".rstrip("0").rstrip(".")

    return f"{fmt(score)}/{fmt(mx)}"


def band_of(p: float | None) -> str:
    if p is None:
        return "—"
    if p >= BAND_GOOD:
        return "Good"
    if p >= BAND_MED:
        return "Medium"
    return "Needs improvement"


def load_data() -> dict:
    text = SRC.read_text(encoding="utf-8")
    m = re.search(r"const DATA = (\{.*?\});\s*\n", text, re.S)
    if not m:
        raise SystemExit("No DATA in Belgium compare HTML")
    return json.loads(m.group(1))


def pms_context() -> tuple[float, float, int]:
    rows = list(csv.DictReader(PMS.open(encoding="utf-8")))
    be = next(r for r in rows if r["distributor_code"] == "BELGIUM" and r["year"] == "2025")
    be_c = float(be["capture_rate_total_wtd"])
    others = [
        float(r["capture_rate_total_wtd"])
        for r in rows
        if r["year"] == "2025" and r["capture_rate_total_wtd"] not in ("", None)
    ]
    return be_c, sum(others) / len(others), len(others)


def q_gaps(data: dict, dealer: dict, section: str, n: int = 5) -> list[tuple]:
    qs = data["questions"]
    scores = dealer["q"]
    gaps = []
    for i, q in enumerate(qs):
        if q["section"] != section:
            continue
        mx = float(q["max"] or 0)
        sc = scores[i]
        if sc is None or not mx:
            continue
        if sc < mx:
            gaps.append((mx - sc, q["id"], sc, mx, q["text"]))
    gaps.sort(reverse=True)
    return gaps[:n]


def country_weak_questions(data: dict, section: str, thresh: float = 0.55) -> list[tuple]:
    qs = data["questions"]
    qpct = data["country_profiles"]["Belgium"]["q_pct"]
    out = []
    for i, q in enumerate(qs):
        if q["section"] != section:
            continue
        p = qpct[i]
        if p < thresh:
            out.append((p, q["id"], q["text"]))
    out.sort()
    return out


def build() -> Path:
    data = load_data()
    dealers = data["dealers"]
    prof = data["country_profiles"]["Belgium"]
    net = data["network"]
    cavg = prof["total_pct"]
    built = data.get("built_at", "")

    hit = []
    for d in dealers:
        tot = d["total_pct"]
        b = band_of(tot)
        below = tot is not None and tot < cavg
        needs = b == "Needs improvement"
        if below or needs:
            hit.append(d)
    hit.sort(
        key=lambda d: (
            0 if band_of(d["total_pct"]) == "Needs improvement" else 1,
            d["total_pct"] if d["total_pct"] is not None else 9,
        )
    )

    pms_be, pms_net, pms_n = pms_context()
    weak_d = country_weak_questions(data, "D", 0.55)

    def sec_bar(label: str, be: float, nw: float) -> str:
        be_w = f"{be * 100:.1f}"
        nw_w = f"{nw * 100:.1f}"
        color = "#c0552d" if be + 0.005 < nw else "#1d9e75" if be > nw + 0.005 else "#2a78d6"
        return f"""
<div class="barrow">
  <div class="n">{escape(label)}</div>
  <div class="track">
    <div class="fill net" style="width:{nw_w}%"></div>
    <div class="fill" style="width:{be_w}%;background:{color}"></div>
  </div>
  <div class="v">{be_w}</div>
</div>"""

    secs = [("A Premises", "A"), ("B Organisation", "B"), ("C Service", "C"), ("D Parts", "D"), ("E Vehicle sales", "E")]
    bars = "".join(
        sec_bar(lab, prof["sections_pct"][k], net["sections_pct"][k]) for lab, k in secs
    )

    rows_html = []
    for d in hit:
        tot = d["total_pct"]
        b = band_of(tot)
        pill = {"Good": "good", "Medium": "medium", "Needs improvement": "weak"}[b]
        ds = d["sections"]
        d_pct = ds["D"]["pct"]
        c_pct = ds["C"]["pct"]
        gaps = q_gaps(data, d, "D", 3)
        if not gaps:
            gaps = q_gaps(data, d, "C", 3)
        gap_txt = "; ".join(f"{g[1]} ({pts(g[2], g[3])})" for g in gaps) or "—"
        rows_html.append(
            f"<tr>"
            f"<td>{escape(d['name'])}</td>"
            f"<td class='num'>{pct(tot)}</td>"
            f"<td class='num'>{pp(tot - cavg)}</td>"
            f"<td><span class='pill {pill}'>{escape(b)}</span></td>"
            f"<td class='num'>{pct(d_pct)}</td>"
            f"<td class='num'>{pct(c_pct)}</td>"
            f"<td>{escape(gap_txt)}</td>"
            f"</tr>"
        )

    start_cards = []
    for name in ("Garage Degroote", "Garage Fayt"):
        d = next(x for x in dealers if x["name"] == name)
        gaps = q_gaps(data, d, "D", 4)
        lis = "".join(
            f"<li><b>{escape(g[1])}</b> — {escape(re.sub(r'\s+', ' ', g[4])[:140])} "
            f"<span class='muted'>({pts(g[2], g[3])})</span></li>"
            for g in gaps
        )
        start_cards.append(
            f"<div class='card'><h3>{escape(name)}</h3>"
            f"<p class='muted'>Total {pct(d['total_pct'])} · Parts {pct(d['sections']['D']['pct'])} · "
            f"Service {pct(d['sections']['C']['pct'])} · Needs improvement</p>"
            f"<ul class='tight'>{lis}</ul></div>"
        )

    weak_lis = "".join(
        f"<li><b>{escape(q[1])}</b> — country {pct(q[0])} · "
        f"{escape(re.sub(r'\s+', ' ', q[2])[:120])}</li>"
        for q in weak_d[:6]
    )

    blank_actions = "".join(
        f"<tr><td>{i}</td><td></td><td></td><td></td><td></td><td></td></tr>"
        for i in range(1, 6)
    )
    blank_pull = "".join(
        "<tr><td></td><td></td><td></td><td></td><td></td></tr>" for _ in range(4)
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>IDS 2026 Kaizen — Belgium</title>
<style>
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0;background:#e8e4dc;color:#222;font-family:"Segoe UI",Helvetica,Arial,sans-serif;font-size:14px;line-height:1.45}}
h1,h2,h3{{font-family:Georgia,"Times New Roman",serif;font-weight:400;margin:0;color:#1a2b4a}}
.banner{{background:#15233c;color:#f7f4ee;padding:28px 32px 32px}}
.banner .k{{font-size:11px;letter-spacing:.08em;text-transform:uppercase;opacity:.8}}
.banner h1{{color:#f7f4ee;font-size:30px;margin:8px 0 10px;max-width:22ch}}
.banner .rule{{width:56px;height:3px;background:#c0552d;margin:0 0 12px}}
.banner p{{margin:0;max-width:72ch;color:#f7f4ee}}
.wrap{{max-width:1120px;margin:0 auto;padding:18px 20px 48px}}
.page{{background:#fff;padding:26px 28px 32px;margin:0 0 16px;box-shadow:0 1px 6px rgba(0,0,0,.08)}}
h2.sec{{font-size:20px;margin:0 0 8px;padding-bottom:8px;border-bottom:2px solid #1a2b4a}}
h2.sec .no{{color:#c0552d}}
.lead{{color:#6b6256;margin:0 0 14px}}
.kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:12px 0}}
.kpi{{background:#f7f4ee;border-top:3px solid #1a2b4a;padding:12px 14px;position:relative;cursor:help}}
.kpi.gap{{border-top-color:#c0552d}}
.kpi.ok{{border-top-color:#1d9e75}}
.kpi.amber{{border-top-color:#eda100}}
.kpi .l{{font-size:10px;text-transform:uppercase;letter-spacing:.04em;color:#6b6256}}
.kpi .v{{font-family:Georgia,serif;font-size:24px;color:#1a2b4a;margin-top:4px}}
.kpi.gap .v{{color:#c0552d}}
.kpi .s{{font-size:12px;color:#6b6256;margin-top:4px}}
.tip{{display:none;position:absolute;left:10px;right:10px;top:100%;z-index:20;margin-top:8px;background:#15233c;color:#f7f4ee;padding:10px 12px;font-size:12px;line-height:1.45;border-top:3px solid #c0552d}}
.kpi:hover .tip{{display:block}}
.callout{{border-left:3px solid #c0552d;background:#f7f4ee;padding:12px 14px;margin:0 0 14px;color:#222}}
.callout.navy{{border-left-color:#1a2b4a;background:#f3f5f8}}
.callout.ok{{border-left-color:#1d9e75;background:#eef7f3}}
.callout b{{color:#1a2b4a}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
.barrow{{display:flex;align-items:center;gap:10px;margin:7px 0}}
.barrow .n{{width:130px;font-size:12px;color:#1a2b4a}}
.barrow .track{{flex:1;height:20px;background:#eeeae3;position:relative}}
.barrow .fill{{height:20px;position:relative;z-index:1}}
.barrow .fill.net{{background:#15233c;opacity:.35;position:absolute;top:0;z-index:0}}
.barrow .v{{width:48px;text-align:right;font-variant-numeric:tabular-nums;font-size:12px}}
table{{width:100%;border-collapse:collapse;margin:10px 0 4px;font-size:13px}}
th{{background:#1a2b4a;color:#f7f4ee;text-align:left;padding:8px 10px;font-size:11px;text-transform:uppercase;letter-spacing:.03em}}
td{{padding:8px 10px;border-bottom:1px solid #d9d3c8;color:#222}}
tbody tr:nth-child(even){{background:#f7f4ee}}
td.num,th.num{{text-align:right;font-variant-numeric:tabular-nums}}
.pill{{display:inline-block;font-size:10px;font-weight:700;letter-spacing:.03em;text-transform:uppercase;padding:2px 7px}}
.pill.good{{background:#d7efe4;color:#1d6b4a}}
.pill.medium{{background:#f8e6c0;color:#8a5a00}}
.pill.weak{{background:#f3d4d0;color:#8a2a22}}
.tight{{margin:6px 0 0;padding-left:18px}}
.tight li{{margin:5px 0}}
.muted{{color:#6b6256;font-size:12px}}
.card{{background:#f7f4ee;padding:12px 14px}}
.card h3{{font-size:15px;margin:0 0 4px}}
.blank td{{height:36px;background:#fff}}
.foot{{margin-top:18px;padding-top:10px;border-top:1px solid #d9d3c8;font-size:11px;color:#6b6256}}
@media(max-width:900px){{.kpis,.grid2{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<div class="banner">
  <div class="k">IDS 2026 · Kaizen · Belgium · v1.4 snapshot {escape(built)}</div>
  <h1>Belgium — use the distributor as the lever</h1>
  <div class="rule"></div>
  <p>Not a score argument. Open the country compare, walk the hit list, agree three to five actions, come back next month and see what closed. Map stays on the dealer-compare file.</p>
</div>
<div class="wrap">

<div class="page">
  <h2 class="sec"><span class="no">1.</span> Where Belgium sits</h2>
  <p class="lead">Country total is in line with the network. Service is the strength. The work is dealer-level — two names in Needs improvement, fifteen below the Belgium average.</p>
  <div class="kpis">
    <div class="kpi"><div class="l">Belgium average</div><div class="v">{pct(cavg)}</div><div class="s">34 dealers · all in the average</div>
      <div class="tip">Mean of 34 Belgium dealer totals on sections A–E. Snapshot {escape(built)}. No dealer excluded from this average.</div></div>
    <div class="kpi"><div class="l">Network average</div><div class="v">{pct(net['total_pct'])}</div><div class="s">anonymous · {net['avg_basis_count']} in the average</div>
      <div class="tip">Anonymous full-network average after France/Spain red-marked dealers are left out of the average. Israel LCV Section E is not scored and is excluded from this average. Belgium itself scored Section E (34/34).</div></div>
    <div class="kpi ok"><div class="l">Parts (D)</div><div class="v">{pct(prof['sections_pct']['D'])}</div><div class="s">vs network {pct(net['sections_pct']['D'])}</div>
      <div class="tip">Belgium country average on Section D versus the anonymous network Section D. Belgium is not a Parts-soft market at country level. The Parts gaps sit at named dealers.</div></div>
    <div class="kpi amber"><div class="l">PMS total capture</div><div class="v">{pct(pms_be)}</div><div class="s">CY2025 · context, not causal</div>
      <div class="tip">Primary lens = total capture (not genuine-only). Complete calendar 2025, Belgium distributor book. Network mean of {pms_n} markets with a row: {pct(pms_net)}. This chip does not prove that raising IDS will move capture. Do not quote it as a forecast.</div></div>
  </div>
  {bars}
  <p class="muted">Solid bar = Belgium. Pale navy = network. Green = above network, terracotta = below.</p>
</div>

<div class="page">
  <h2 class="sec"><span class="no">2.</span> In the room</h2>
  <div class="callout">
    <b>Talking line</b>
    <p>We are not here to argue a total score. We are here to pick the dealers who are below the country average, agree three actions, and come back next month to see what closed. Belgium as a market is close to the network; the work is the names on the hit list — start with the two in Needs improvement.</p>
  </div>
  <div class="grid2">
    <div class="callout navy">
      <b>Do</b>
      <ul class="tight">
        <li>Open the Belgium dealer-compare HTML. Map first, then this hit list.</li>
        <li>Agree 3–5 actions from the largest checklist gaps. Owner, target date, proof — blank until they fill them.</li>
        <li>Walk Parts and Service on the two Needs improvement dealers. Country Parts is not the headline.</li>
        <li>Monthly pull: % visited, % actions closed, incomplete still open, escalations.</li>
      </ul>
    </div>
    <div class="callout ok">
      <b>Do not</b>
      <ul class="tight">
        <li>Promise that a higher IDS score will move GPS or fill rate. Those files stay separate.</li>
        <li>Treat this list as a blacklist. It is the call list for the next 90 days.</li>
        <li>Lead with a network correlation lecture. Stay on named dealers and named checklist items.</li>
        <li>Drop Parts from the conversation because country D is near the network. Degroote and Fayt are still soft on D.</li>
      </ul>
    </div>
  </div>
</div>

<div class="page">
  <h2 class="sec"><span class="no">3.</span> Hit list — below Belgium average</h2>
  <p class="lead">{len(hit)} of 34 dealers. Sorted Needs improvement first, then furthest below the country average ({pct(cavg)}). Good / Medium / Needs improvement = 80% / 60% bands.</p>
  <table>
    <thead>
      <tr>
        <th>Dealer</th>
        <th class="num">Total</th>
        <th class="num">vs Belgium</th>
        <th>Band</th>
        <th class="num">Parts</th>
        <th class="num">Service</th>
        <th>Largest Parts gaps</th>
      </tr>
    </thead>
    <tbody>
      {''.join(rows_html)}
    </tbody>
  </table>
  <p class="muted">Gaps are the biggest unfinished Parts checklist items for that dealer (points left on the table). Drill the full list in the dealer-compare file.</p>
</div>

<div class="page">
  <h2 class="sec"><span class="no">4.</span> Start here — two dealers</h2>
  <p class="lead">Both sit in Needs improvement. Use the items below as the conversation, not as a script they must sign today.</p>
  <div class="grid2">{''.join(start_cards)}</div>
  <h3 style="margin:18px 0 8px">Country-soft Parts items (whole Belgium)</h3>
  <p class="lead">Checklist items where Belgium as a market scores under 55%. Useful if the distributor wants one network action on top of dealer visits.</p>
  <ul class="tight">{weak_lis or '<li>No Parts item under 55% at country level.</li>'}</ul>
</div>

<div class="page">
  <h2 class="sec"><span class="no">5.</span> Actions — they fill this</h2>
  <p class="lead">Three to five. Leave owner, date and proof blank in the room until they write them.</p>
  <table>
    <thead>
      <tr>
        <th>#</th>
        <th>Dealer / scope</th>
        <th>Action</th>
        <th>Owner</th>
        <th>Target date</th>
        <th>Proof</th>
      </tr>
    </thead>
    <tbody class="blank">{blank_actions}</tbody>
  </table>
</div>

<div class="page">
  <h2 class="sec"><span class="no">6.</span> Monthly pull</h2>
  <p class="lead">Empty until the first return. This is the measure — not a new graph pack.</p>
  <table>
    <thead>
      <tr>
        <th>Month</th>
        <th class="num">Visited %</th>
        <th class="num">Actions closed %</th>
        <th class="num">Still open</th>
        <th>Escalations</th>
      </tr>
    </thead>
    <tbody class="blank">{blank_pull}</tbody>
  </table>
</div>

<p class="foot">Sources: IDS 2026 Belgium dealer compare v1.4 ({escape(built)}); PMS total capture calendar 2025, Belgium book, total lens. Map and full checklist live on the Belgium dealer-compare HTML. No GPS% on this page. Confidential — meeting pack for the Belgium distributor conversation.</p>
</div>
</body>
</html>
"""
    OUT.write_text(html, encoding="utf-8")
    CMD.write_text('@echo off\r\nstart "" "%~dp0IDS_2026_Kaizen_Belgium.html"\r\n', encoding="ascii")
    PACK.parent.mkdir(parents=True, exist_ok=True)
    PACK.write_text(html, encoding="utf-8")
    pack_cmd = PACK.parent / "OPEN_IDS_2026_Kaizen_Belgium.cmd"
    pack_cmd.write_text('@echo off\r\nstart "" "%~dp0IDS_2026_Kaizen_Belgium.html"\r\n', encoding="ascii")
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes) hit={len(hit)}")
    return OUT


if __name__ == "__main__":
    build()
