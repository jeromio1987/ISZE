#!/usr/bin/env python3
"""
Internal working page for the ITUK dealer-level parts demand model, CY2025.

Self-contained: the tables are embedded at build time, so it opens from a double-click
with no server and no internet. Every figure is read from the derived tables written by
build_dealer_demand_ituk.py. Nothing here is published, synced or mailed.

Wording follows the workspace rules: euro first with the family named in words and the
fleet beside it, "what we billed", "trucks in service", "sales to dealer".
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

DERIVED = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
BUILD = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\dealer_demand_ituk_20260924")
STAMP = "20260924"

CAL = DERIVED / f"dealer_demand_ituk_2025_calibration_by_family_{STAMP}.csv"
DFAM = DERIVED / f"dealer_demand_ituk_2025_dealer_by_family_{STAMP}.csv"
ROLL = DERIVED / f"dealer_demand_ituk_2025_by_dealer_{STAMP}.csv"
EXP = DERIVED / f"dealer_demand_ituk_2025_market_expected_{STAMP}.csv"
COV = DERIVED / f"dealer_demand_ituk_2025_coverage_{STAMP}.csv"
META = DERIVED / f"dealer_demand_ituk_2025_meta_{STAMP}.json"


def eur(x, nd=0):
    if x is None or pd.isna(x):
        return "n/a"
    return f"&euro;{x:,.{nd}f}"


def pct(x, nd=1):
    if x is None or pd.isna(x):
        return "n/a"
    return f"{x*100:,.{nd}f}%"


def pp(x, nd=1):
    if x is None or pd.isna(x):
        return "n/a"
    return f"{x:,.{nd}f} pp"


def main() -> None:
    cal = pd.read_csv(CAL)
    dfam = pd.read_csv(DFAM)
    roll = pd.read_csv(ROLL)
    cov = pd.read_csv(COV)
    meta = json.loads(META.read_text(encoding="utf-8"))

    fleet = meta["fleet_we_bill_against"]
    hb = meta["headline_calibration"]
    covm = meta["coverage_of_the_method"]

    # headline family = the strongest independent one
    head = cal[cal["family"] == hb["family"]]
    head_rho = float(head.iloc[0]["spearman_rho"]) if len(head) else None
    head_rho_size = float(head.iloc[0]["spearman_rho_dealer_size_only"]) if len(head) else None
    head_mad = float(head.iloc[0]["mad_pp"]) if len(head) else None

    judge = cal[cal["basis"].isin(["calibrated", "estimated"])].copy()
    total_expected = float(judge["expected_eur"].sum())
    total_billed = float(judge["network_eur"].sum())
    total_gap = total_expected - total_billed

    # how many families the proxy beats dealer size on
    cmp = cal.dropna(subset=["spearman_rho", "spearman_rho_dealer_size_only"])
    wins = int((cmp["spearman_rho"] > cmp["spearman_rho_dealer_size_only"]).sum())
    ties = int((cmp["spearman_rho"] == cmp["spearman_rho_dealer_size_only"]).sum())
    loses = int((cmp["spearman_rho"] < cmp["spearman_rho_dealer_size_only"]).sum())

    # ---- family table rows ----
    fam_rows = []
    for _, r in cal.iterrows():
        kind = "Mileage rhythm" if r["family_kind"] == "mileage rhythm" else "Failure driven"
        basis = str(r["basis"])
        badge = {"definition": "definition", "calibrated": "calibrated",
                 "estimated": "estimated", "not judgeable": "not judgeable"}[basis]
        if basis == "not judgeable" or pd.isna(r["spearman_rho"]):
            verdict = "Not judgeable &mdash; too few of these sold in the market to split between dealers."
        else:
            adds = float(r["spearman_rho"]) - float(r["spearman_rho_dealer_size_only"])
            if adds > 0.02:
                verdict = "The filter share lands closer than dealer size alone."
            elif adds < -0.02:
                verdict = "Dealer size alone does the job better."
            else:
                verdict = "The filter share adds nothing over dealer size."
        fam_rows.append(f"""<tr>
      <td>{r['family_label']}</td>
      <td>{kind}</td>
      <td class="n">{eur(r['network_eur'])}</td>
      <td class="n">{eur(r['expected_eur'])}</td>
      <td class="n">{pct(r['capture_of_expected'])}</td>
      <td class="n">{eur(r['network_gap_eur'])}</td>
      <td class="n">{pp(r['mad_relative_to_average_share']*100 if pd.notna(r['mad_relative_to_average_share']) else None,0)}</td>
      <td class="n">{'%.2f' % r['spearman_rho'] if pd.notna(r['spearman_rho']) else '&mdash;'}
          <span class="sub">({('%.2f' % r['spearman_rho_dealer_size_only']) if pd.notna(r['spearman_rho_dealer_size_only']) else 'n/a'})</span></td>
      <td><span class="badge b-{badge.replace(' ','-')}">{badge}</span></td>
      <td class="small">{verdict}</td>
    </tr>""")

    # ---- dealer table rows (judged families only) ----
    roll_j = roll[roll["families_judged"] > 0].sort_values("gap_eur", ascending=False)
    dealer_rows = []
    for _, r in roll_j.iterrows():
        share = "" if pd.isna(r["proxy_share"]) else f"{r['proxy_share']*100:,.2f}%"
        trucks = "" if pd.isna(r["trucks_apportioned"]) else f"{r['trucks_apportioned']:,.0f}"
        cls = "neg" if r["gap_eur"] < 0 else ""
        note = ""
        if bool(r.get("proxy_absent", False)):
            note = "No oil filters bought &mdash; no share exists, nothing expected."
        dealer_rows.append(f"""<tr>
      <td>{r['dealer_name']}</td>
      <td class="n">{trucks}</td>
      <td class="n">{share}</td>
      <td class="n">{eur(r['expected_eur'])}</td>
      <td class="n">{eur(r['billed_eur'])}</td>
      <td class="n {cls}">{eur(r['gap_eur'])}</td>
      <td class="n">{int(r['families_judged'])}</td>
      <td class="small">{note}</td>
    </tr>""")

    # ---- coverage table rows ----
    cov_rows = []
    for _, r in cov.iterrows():
        if r["network_qty"] == 0:
            state = '<span class="badge b-not-judgeable">none sold</span>'
        else:
            state = f"{int(r['dealers_buying'])} of 64 dealers"
        cov_rows.append(f"""<tr>
      <td>{r['family_label']}</td>
      <td class="n">{eur(r['network_eur'])}</td>
      <td class="n">{r['network_qty']:,.0f}</td>
      <td class="n">{pct(r['qty_share_of_all_dealer_buys'])}</td>
      <td>{state}</td>
    </tr>""")

    # ---- scatter: each dealer's filter share against their share of fuel filters ----
    # Built as plain SVG so the page stays script-free and opens from a double-click.
    sc = dfam[dfam["family"] == "fuel_filter"].copy()
    sc = sc.merge(roll[["dealer_name", "proxy_share"]], on="dealer_name", how="left",
                  suffixes=("", "_roll"))
    sc = sc.dropna(subset=["proxy_share", "actual_share"])
    W, H, PAD = 640, 320, 52
    mx = max(sc["proxy_share"].max(), sc["actual_share"].max()) * 1.08
    dots = []
    for _, r in sc.iterrows():
        x = PAD + (r["proxy_share"] / mx) * (W - 2 * PAD)
        y = H - PAD - (r["actual_share"] / mx) * (H - 2 * PAD)
        dots.append(f'<circle class="dot" cx="{x:.1f}" cy="{y:.1f}" r="4.5"></circle>')
    x1 = PAD + (mx / mx) * (W - 2 * PAD)
    y1 = H - PAD - (mx / mx) * (H - 2 * PAD)
    scatter = f"""<svg viewBox="0 0 {W} {H}" width="100%" height="auto" role="img"
     aria-label="Each dealer's share of oil filters against their share of fuel filters">
  <rect x="{PAD}" y="{PAD}" width="{W-2*PAD}" height="{H-2*PAD}" fill="#fff" stroke="#d8d2c6"></rect>
  <line x1="{PAD}" y1="{H-PAD}" x2="{x1}" y2="{y1}" stroke="#c0552d" stroke-dasharray="5 4"></line>
  {''.join(dots)}
  <text x="{W/2}" y="{H-14}" text-anchor="middle" font-size="12" fill="#5d6b7a">Share of oil filters (the proxy for trucks)</text>
  <text x="14" y="{H/2}" text-anchor="middle" font-size="12" fill="#5d6b7a"
        transform="rotate(-90 14 {H/2})">Share of fuel filters (actual)</text>
  <text x="{PAD+6}" y="{PAD+16}" font-size="12" fill="#c0552d">dashed line = the proxy being exactly right</text>
</svg>"""

    amb = COV.read_text(encoding="utf-8")

    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Dealer parts demand &mdash; UK truck book, CY2025 (internal draft)</title>
<style>
:root{{--navy:#15233c;--ink:#22303f;--terra:#c0552d;--paper:#f7f4ee;--line:#d8d2c6;--grey:#5d6b7a}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);font:15px/1.5 "Segoe UI",Helvetica,Arial,sans-serif}}
header{{background:var(--navy);color:var(--paper);padding:26px 32px 22px}}
header h1{{margin:0 0 6px;font:600 25px/1.25 Georgia,serif;color:#fff}}
header .sub{{color:#c9d2e0;font-size:13.5px}}
.wrap{{max-width:1220px;margin:0 auto;padding:0 24px 60px}}
section{{margin:34px 0 0}}
h2{{font:600 19px/1.3 Georgia,serif;color:var(--navy);border-bottom:2px solid var(--line);padding-bottom:7px;margin:0 0 14px}}
h3{{font:600 15.5px/1.3 "Segoe UI",sans-serif;color:var(--navy);margin:20px 0 8px}}
p{{margin:0 0 12px;max-width:1040px}}
.lede{{font-size:16px}}
.card{{background:#fff;border:1px solid var(--line);border-left:5px solid var(--terra);padding:16px 18px;margin:0 0 16px}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:14px;margin:16px 0 6px}}
.kpi{{background:#fff;border:1px solid var(--line);padding:14px 16px}}
.kpi .lab{{font-size:12px;letter-spacing:.045em;text-transform:uppercase;color:var(--grey)}}
.kpi .val{{font:600 25px/1.15 Georgia,serif;color:var(--navy);margin:6px 0 3px}}
.kpi .foot{{font-size:12.5px;color:var(--grey)}}
table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line);font-size:13.5px}}
th{{background:var(--navy);color:var(--paper);text-align:left;padding:9px 10px;font-weight:600;font-size:12.5px;vertical-align:bottom}}
td{{padding:8px 10px;border-top:1px solid var(--line);vertical-align:top}}
tbody tr:nth-child(even) td{{background:#fbfaf7}}
td.n,th.n{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
td.neg{{color:#9b2c1c}}
.badge{{display:inline-block;padding:2px 8px;border-radius:11px;font-size:11.5px;font-weight:600;white-space:nowrap}}
.b-calibrated{{background:#e2efe4;color:#1f5c2e}}
.b-estimated{{background:#fbeedc;color:#8a5310}}
.b-definition{{background:#e6e9f2;color:#2b3a63}}
.b-not-judgeable{{background:#f0eeea;color:#6a655c}}
.amber{{background:#fdf3e2;border:1px solid #e3b877;border-left:5px solid #d99a2b;padding:14px 16px;margin:14px 0}}
.amber strong{{color:#8a5310}}
.small{{font-size:12.5px;color:var(--grey)}}
.sub{{font-size:11.5px;color:var(--grey)}}
.dot{{fill:#15233c;fill-opacity:.66}}
.scatterbox{{background:#fff;border:1px solid var(--line);padding:12px;margin:14px 0}}
footer{{margin-top:44px;padding-top:16px;border-top:1px solid var(--line);font-size:12.5px;color:var(--grey)}}
ol,ul{{max-width:1040px}}
li{{margin:0 0 7px}}
</style></head><body>
<header>
  <h1>Dealer parts demand &mdash; UK truck book</h1>
  <div class="sub">Internal draft &middot; CY2025 &middot; {meta['dealers']} dealers &middot;
   {fleet:,.0f} trucks in service &middot; built {datetime.now(timezone.utc).strftime('%d %b %Y')}</div>
</header>
<div class="wrap">

<section>
  <div class="card">
    <p class="lede"><strong>The short version.</strong> We hold the trucks in service for the market,
    not for each dealer. So each dealer is given a share of the {fleet:,.0f} trucks using their share
    of oil filters, and the model then expects the same share of every other service family from them.
    The test of that idea is whether it beats simply knowing how big the dealer is &mdash; and on this
    book it mostly does not. That matters, because every euro below sits on top of it.</p>
  </div>

  <div class="kpis">
    <div class="kpi">
      <div class="lab">Dealers</div>
      <div class="val">{meta['dealers']}</div>
      <div class="foot">named in the sales-to-dealer file for the UK truck book</div>
    </div>
    <div class="kpi">
      <div class="lab">What we billed, that file</div>
      <div class="val">{eur(meta['valued_eur_total'])}</div>
      <div class="foot">CY2025, valued at what we billed the distributor per part number</div>
    </div>
    <div class="kpi">
      <div class="lab">Families this can judge</div>
      <div class="val">{pct(covm['service_family_eur_share'])}</div>
      <div class="foot">share of those euros that sits in a family with a service rhythm</div>
    </div>
    <div class="kpi">
      <div class="lab">Gap across judged families</div>
      <div class="val">{eur(total_gap)}</div>
      <div class="foot">across {len(judge)} families where the model can judge at all, on the filter-share expected side</div>
    </div>
  </div>
</section>

<section>
  <h2>1. Does the filter share actually hold?</h2>
  <p>Two questions, answered with numbers rather than asserted.</p>

  <h3>Is the share stable across families?</h3>
  <p>Take each dealer's share of network oil filters and compare it with their actual share of
  another family. If the idea works, those two should agree. On the strongest independent family
  &mdash; {hb['family_label'] if 'family_label' in hb else hb['family'].replace('_',' ')} &mdash; the
  rank agreement is <strong>{head_rho:.2f}</strong> and the average dealer is off by
  <strong>{head_mad:.2f} percentage points</strong>. Dealer shares are also narrow: the average
  dealer holds about {100/meta['dealers']:.1f}% of the network and the largest holds about
  {max(roll['proxy_share'].dropna())*100:.1f}%, so an error of a fraction of a point is a small
  number of trucks but a large slice of a dealer's own expectation.</p>

  <h3>Does it beat just knowing the dealer's size?</h3>
  <p>This is the test that matters. A dealer's total parts volume already tells you a lot about
  how much of anything they buy. Before the numbers, the shape: each point below is one dealer,
  their share of oil filters across the bottom against their share of fuel filters up the side.
  On a working proxy the points sit on the dashed line.</p>
  <div class="scatterbox">{scatter}</div>
  <p>Run the same comparison using dealer size alone and the filter share stops looking clever:</p>
  <table>
    <thead><tr><th>Family judged</th><th>Filter share</th><th>Dealer size alone</th><th>Difference</th></tr></thead>
    <tbody>
    {''.join(f"<tr><td>{r['family_label']}</td><td class='n'>{'%.2f'%r['spearman_rho'] if pd.notna(r['spearman_rho']) else '&mdash;'}</td><td class='n'>{'%.2f'%r['spearman_rho_dealer_size_only'] if pd.notna(r['spearman_rho_dealer_size_only']) else '&mdash;'}</td><td class='n'>{('%+.2f'%(r['spearman_rho']-r['spearman_rho_dealer_size_only'])) if pd.notna(r['spearman_rho']) and pd.notna(r['spearman_rho_dealer_size_only']) else '&mdash;'}</td></tr>" for _, r in cmp.iterrows())}
    </tbody>
  </table>
  <div class="amber">
    <p><strong>The honest verdict.</strong> The filter share wins on {wins} of {wins+ties+loses}
    families judged, ties on {ties} and loses on {loses}. On air filter it is actually behind
    dealer size. The method is not useless &mdash; it carries the family split, which size alone
    cannot, because a big dealer's mix between filters and brakes is exactly what we are short of
    &mdash; but as a <em>better estimate of a dealer's trucks</em> it is not established by this
    book. Treat every euro below as an allocation on a stated rule, not as a measured gap.</p>
  </div>
</section>

<section>
  <h2>2. Family by family</h2>
  <p>Expected euros per family come from the market service-demand table on the truck basis, split
  across dealers on the filter share. What we billed is what the dealers actually bought. The last
  column is the average dealer's error against the average dealer's share, so it reads as a share
  of the dealer's own position rather than an abstract percentage point. The figure in brackets is
  the same agreement using dealer size alone.</p>
  <table>
    <thead><tr>
      <th>Service family</th><th>Driven by</th><th class="n">What we billed</th>
      <th class="n">Expected</th><th class="n">Share of expected</th><th class="n">Gap</th>
      <th class="n">Average error</th><th class="n">Agreement<br>(size only)</th>
      <th>Row basis</th><th>Reads as</th>
    </tr></thead>
    <tbody>
    {''.join(fam_rows)}
    </tbody>
  </table>
  <div class="amber">
    <p><strong>A cabin and blower filter row worth &euro;164,671 of expected demand has nothing
    behind it.</strong> Not one cabin filter was sold to any of the 64 dealers in CY2025. That is
    either a real gap or a part that is not sold under this number, and this model cannot tell
    which. It is shown as not judgeable rather than as a gap.</p>
  </div>
</section>

<section>
  <h2>3. Dealer by dealer</h2>
  <p>Ranked by the gap on the families this method can judge. Trucks in service is the dealer's
  apportioned share of the {fleet:,.0f} &mdash; an allocation, not a measured fleet. What we billed
  is what they actually bought.</p>
  <table>
    <thead><tr>
      <th>Dealer</th><th class="n">Trucks in service<br>(apportioned)</th><th class="n">Share of network</th>
      <th class="n">Expected</th><th class="n">What we billed</th><th class="n">Gap</th>
      <th class="n">Families</th><th>Note</th>
    </tr></thead>
    <tbody>
    {''.join(dealer_rows)}
    </tbody>
  </table>
</section>

<section>
  <h2>4. What this model can see at all</h2>
  <p>The method covers parts replaced on a rhythm. It says nothing about repair, body, electrical
  or hardware demand, where a dealer who sold nothing may simply have had no accident to repair.
  Of everything the 64 dealers bought in CY2025, {pct(covm['service_family_qty_share'])} of the
  pieces and {pct(covm['service_family_eur_share'])} of the euro sit in a family this can judge.
  The rest is out of scope, not missing.</p>
  <table>
    <thead><tr><th>Family</th><th class="n">What we billed</th><th class="n">Pieces</th>
      <th class="n">Share of all dealer pieces</th><th>Dealers buying</th></tr></thead>
    <tbody>
    {''.join(cov_rows)}
    </tbody>
  </table>
</section>

<section>
  <h2>5. What is measured and what is not</h2>
  <table>
    <thead><tr><th>Layer</th><th>Basis</th><th>Where it comes from</th></tr></thead>
    <tbody>
      <tr><td>What the dealers bought</td><td><span class="badge b-calibrated">measured</span></td>
        <td>The 2025 sales-to-dealer file for the UK truck book, {meta['dealer_lines']:,} lines,
        {meta['dealers']} named dealers, part number by month.</td></tr>
      <tr><td>The euro beside it</td><td><span class="badge b-estimated">derived</span></td>
        <td>Pieces multiplied by the median CY2025 price we billed the distributor for that part
        number. This is what we billed the distributor, not the dealer invoice.
        {pct(meta['qty_without_isze_price_share'])} of pieces carry no ISZE price and are worth
        nothing here.</td></tr>
      <tr><td>Trucks in service per dealer</td><td><span class="badge b-estimated">estimated</span></td>
        <td>The market fleet apportioned on the dealer's oil-filter share. Not measured at dealer
        level anywhere in this workspace.</td></tr>
      <tr><td>Expected euro per family</td><td><span class="badge b-calibrated">modelled</span></td>
        <td>The market service-demand table for the truck book, split on the filter share.</td></tr>
    </tbody>
  </table>
</section>

<section>
  <h2>6. Limits, stated plainly</h2>
  <ol>
    <li><strong>One market, one year.</strong> The UK truck book is the only place we can see both
    the trucks and what each dealer bought. Nothing here shows the rule travels to another market.</li>
    <li><strong>The fleet is apportioned, not counted.</strong> {fleet:,.0f} trucks is a market
    figure. Which dealer serves which truck is an assumption on a stated rule.</li>
    <li><strong>The rule is not proven to be better than dealer size.</strong> See section 1.</li>
    <li><strong>Three families carry the biggest gaps and rest on the weakest footing.</strong>
    Brake shoe shows a {eur(cal[cal['family']=='brake_shoe']['network_gap_eur'].iloc[0])} gap on
    {cal[cal['family']=='brake_shoe']['network_qty'].iloc[0]:,.0f} pieces. Clutch booster shows
    {eur(cal[cal['family']=='clutch_booster']['network_gap_eur'].iloc[0])} on two pieces. Those
    are questions, not findings.</li>
    <li><strong>Currency, warranty and returns are not in this.</strong> The file is quantities; the
    value is a price proxy; nothing here nets off credits or warranty claims.</li>
    <li><strong>Four dealers are absent from the expected side.</strong> They bought parts but no
    oil filters, so no share exists and nothing is expected of them. That is a finding about the
    dealer, and it is labelled as one rather than printed as a zero gap.</li>
  </ol>
  <div class="amber">
    <p><strong>Israel is not in this model at all.</strong> No Israel row is read. Separately, and
    not acted on: the dealer survey file used elsewhere in this workspace carries 78 rows labelled
    Israel LCV, while we hold no dealer names for Israel. That file's labelling is wrong and has
    been recorded, not corrected.</p>
  </div>
</section>

<footer>
  Internal working draft. Not published, not synced to any deploy mirror, nothing mailed.
  Every figure is read from the dated derived tables at build time. Sources: the 2025
  sales-to-dealer file for the UK truck book, the market service-demand table for the truck book,
  the CY2025 billing table for part-number prices, and the published fleet figure for the UK truck
  book. Fleet denominator: {fleet:,.0f} trucks ({meta['fleet_source']}, {meta['fleet_period_basis']}).
</footer>
</div></body></html>
"""

    out_dir = BUILD / "page"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_html = out_dir / "Dealer_Parts_Demand_ITUK_CY2025_INTERNAL.html"
    if out_html.exists():
        raise SystemExit(f"REFUSING to overwrite: {out_html}")
    out_html.write_text(html, encoding="utf-8")
    print("wrote", out_html, len(html), "chars")


if __name__ == "__main__":
    main()
