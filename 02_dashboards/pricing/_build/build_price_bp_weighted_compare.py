"""shared HTML overview — base-price impact weighted by the last 12 months of sales.

Reads the derived tables written by
01_data/91_build/build_price_bp_weighted_compare.py and renders a self-contained
HTML (Chart.js inlined, data embedded) so it paints on file:// with no server.

Question this page answers (chart-rule: title = business question):
  "What does the new base-price list do to each customer's L12M basket, in euro
   and in percent?"  +  "Where did those euros come from, by part family?"

Design (isze-best-chart):
  - Ranked bars, euro first, reference line = network weighted %.
  - UTI and UMI are two separate labelled rows. Never one blended Israel number.
  - The class lever is a ranked bar of the weighted step per pricing class
    (single series -> no pie-of-a-league, no spaghetti).
  - Every gap carries euro + family, per isze-gaps-need-context.

Run: python 02_dashboards/pricing/_build/build_price_bp_weighted_compare.py
"""
from __future__ import annotations

import html
import json
import math
from datetime import date
from pathlib import Path

import pandas as pd

ISZE = Path(__file__).resolve().parents[3]
DERIVED = ISZE / "01_data" / "00_derived"
OUT_DIR = ISZE / "02_dashboards" / "pricing"
HTML_PATH = OUT_DIR / "ISZE_Price_BP_Weighted_Compare.html"
CMD_PATH = OUT_DIR / "OPEN_ISZE_Price_BP_Weighted_Compare.cmd"
CHART_JS = ISZE / "02_dashboards" / "_ui" / "chart.umd.min.js"

META = DERIVED / "price_bp_weighted_compare_meta.json"
CUST = DERIVED / "price_bp_weighted_compare_customer.csv"
PN = DERIVED / "price_bp_weighted_compare_pn.csv"


def clean(v, default=None):
    """JSON cannot carry NaN; also stops Infinity leaking into the page."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return default
    return f if math.isfinite(f) else default


def chart_js_inline() -> str:
    raw = CHART_JS.read_text(encoding="utf-8")
    return "\n".join(ln for ln in raw.splitlines() if "sourceMappingURL" not in ln)


def load() -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    meta = json.loads(META.read_text(encoding="utf-8"))
    cust = pd.read_csv(CUST, dtype={"customer_code": str})
    pn = pd.read_csv(PN, dtype={"customer_code": str})
    return meta, cust, pn


def build_payload(meta: dict, cust: pd.DataFrame, pn: pd.DataFrame) -> dict:
    net = cust[cust["level"] == "network"].iloc[0]

    customers = cust[cust["level"] == "customer"].copy()
    customers = customers.sort_values("value_step_eur", ascending=False)

    # The ranking uses the distributor level, not the sold-to level: Germany and
    # Portugal each split across two sold-to codes, and the sold-to view would
    # list the same distributor twice.
    dist = cust[cust["level"] == "distributor"].copy()
    dist = dist.sort_values("value_step_eur", ascending=False)

    # Israel is always two rows (1797 UMI / 1799 UTI), shown inside the same
    # ranking so the reader can compare them against everyone else.
    rows = []
    for _, r in dist.iterrows():
        key = str(r["label"])
        israel = key in ("UMI", "UTI")
        rows.append({
            "code": key,
            "label": key,
            "pct": clean(r["weighted_increase_pct"]),
            "step_eur": clean(r["value_step_eur"]),
            "l12m_eur": clean(r["l12m_billed_eur"]),
            "cov": clean(r["qty_coverage_pct"]),
            "israel": israel,
            "n_codes": int(r["n_pn_total"]) and None,
            "combined_pct": float(net["weighted_increase_pct"]),
            "combined_eur": float(net["value_step_eur"]),
        })

    cust_rows = []
    for _, r in customers.iterrows():
        code = r["customer_code"]
        israel = code in ("1797", "1799")
        cust_rows.append({
            "code": code,
            "label": str(r["label"]).split(" - ", 1)[-1] + f" ({code})",
            "pct": clean(r["weighted_increase_pct"]),
            "step_eur": clean(r["value_step_eur"]),
            "l12m_eur": clean(r["l12m_billed_eur"]),
            "cov": clean(r["qty_coverage_pct"]),
            "israel": israel,
        })

    # Step per pricing class, euro-first, priced rows only, in scope.
    priced = pn[pn["in_scope"] & pn["bp_new_jpy"].notna() & pn["bp_prior_revised"].notna()].copy()
    by_class = []
    for cls, f in priced.groupby("bp_new_class"):
        prior_v = (f["billed_qty"] * f["bp_prior_revised"]).sum()
        new_v = (f["billed_qty"] * f["bp_new_jpy"]).sum()
        by_class.append({
            "cls": str(cls),
            "pct": round(100 * (new_v / prior_v - 1), 3) if prior_v else None,
            "step_eur": round(float(f["value_eur_step"].sum()), 2),
            "l12m_eur": round(float(f["net_sales_value"].sum()), 2),
            "qty": int(f["billed_qty"].sum()),
            "pn": int(f["part_number"].nunique()),
        })
    by_class.sort(key=lambda d: -(d["step_eur"] or 0))

    # Top part numbers by euro contribution, with family context.
    # The description shown next to a part number is the text as billed. It is the
    # fullest accurate source: present for every part number in the priced set,
    # where the pricing simulation covers only about three quarters of them, and
    # never truncated, where the price file cuts its own part names to 15
    # characters. Spacing is kept as billed ("PAD KIT; CALIPER,DISC BRK,FRT")
    # because it reads, and nothing is expanded into catalogue wording.
    def part_description(f: pd.DataFrame) -> str:
        for col in ("billed_description", "sim_description", "price_file_description"):
            if col in f.columns and f[col].notna().any():
                v = str(f[col].dropna().iloc[0]).strip()
                if v and v.lower() != "nan":
                    return v
        return ""

    top_pn = []
    for p, f in priced.groupby("part_number"):
        step = float(f["value_eur_step"].sum())
        prior_v = float((f["billed_qty"] * f["bp_prior_revised"]).sum())
        new_v = float((f["billed_qty"] * f["bp_new_jpy"]).sum())
        top_pn.append({
            "pn": str(p),
            "desc": part_description(f),
            "pct": round(100 * (new_v / prior_v - 1), 2) if prior_v else None,
            "step_eur": round(step, 2),
            "cls": str(f["bp_new_class"].iloc[0]),
            "qty": int(f["billed_qty"].sum()),
            "l12m_eur": round(float(f["net_sales_value"].sum()), 2),
        })
    top_pn.sort(key=lambda d: -d["step_eur"])

    return {
        "window": meta["window"],
        "fx": meta["fx"],
        "network": {
            "pct": clean(net["weighted_increase_pct"]),
            "step_eur": clean(net["value_step_eur"]),
            "l12m_eur": clean(net["l12m_billed_eur"]),
            "cov_qty": clean(net["qty_coverage_pct"]),
            "cov_eur": meta["coverage"]["eur_coverage_pct"],
            "n_pn_priced": int(net["n_pn_priced"]),
            "rev_prior_eur": clean(net["revenue_prior_eur"]),
            "rev_new_eur": clean(net["revenue_new_eur"]),
        },
        "customers": rows,
        "customer_codes": cust_rows,
        "israel": [r for r in rows if r["israel"]],
        "by_class": by_class,
        "top_pn": top_pn[:25],
        "unpriced": meta["unpriced_bucket"],
        "lubricant_rule": meta.get("lubricant_rule", {}),
        "non_parts": meta["non_parts_excluded"],
        "direct": meta["direct_account_excluded"],
        "class_mapping": meta["class_mapping"],
        "sensitivity": meta["sensitivity"],
    }


def fmt_eur(v) -> str:
    if v is None:
        return "n/a"
    return f"EUR {v:,.0f}"


def render(d: dict) -> str:
    net = d["network"]
    payload = json.dumps(d, ensure_ascii=False, allow_nan=False)

    israel_rows = "".join(
        f'<tr><td class="strong">{html.escape(r["label"])}</td>'
        f'<td class="num">{r["pct"]:.3f}%</td>'
        f'<td class="num">{fmt_eur(r["step_eur"])}</td>'
        f'<td class="num">{fmt_eur(r["l12m_eur"])}</td>'
        f'<td class="num">{r["cov"]:.1f}%</td></tr>'
        for r in d["israel"]
    )

    # Sold-to detail behind the distributor roll-up, so a doubled country is visible.
    by_dist: dict[str, list] = {}
    for r in d["customer_codes"]:
        nm = r["label"].split(" (", 1)[0]
        by_dist.setdefault(nm, []).append(r)
    code_rows = ""
    for nm in sorted(by_dist, key=lambda k: -sum(x["step_eur"] or 0 for x in by_dist[k])):
        for r in sorted(by_dist[nm], key=lambda x: -(x["step_eur"] or 0)):
            code_rows += (
                f'<tr><td class="strong">{html.escape(nm)}</td>'
                f'<td>{r["code"]}</td>'
                f'<td class="num">{r["pct"]:.3f}%</td>'
                f'<td class="num">{fmt_eur(r["step_eur"])}</td>'
                f'<td class="num">{fmt_eur(r["l12m_eur"])}</td>'
                f'<td class="num">{r["cov"]:.1f}%</td></tr>'
            )

    unp = d["unpriced"]
    unp_rows = ""
    lub = None

    def label_with_code(label, code) -> str:
        """Avoid "sold-to 2970 (2970)" where the label is already just the code."""
        label = html.escape(str(label))
        code = html.escape(str(code))
        return label if code and code in label else f"{label} ({code})"

    for b in unp["buckets"]:
        key = str(b["bucket"])
        what = b.get("what") or key.replace("_", " ")
        why = b.get("why", "")
        named = b.get("top_customers_named") or []
        who = ""
        if named:
            top = named[0]
            if b.get("n_customers") == 1 or len(named) == 1:
                who = f"{label_with_code(top['label'], top['code'])} &mdash; all of it"
            else:
                who = (f"{label_with_code(top['label'], top['code'])} "
                       f"{top['share_pct']:.0f}%, across {b['n_customers']} customers")
        unp_rows += (
            f'<tr><td><span class="bname">{html.escape(what)}</span>'
            f'<div class="bwho">Excluded because: {html.escape(why)}</div></td>'
            f'<td class="num">{b["rows"]:,}</td>'
            f'<td class="num">{fmt_eur(b["l12m_billed_eur"])}</td>'
            f'<td class="num">{b["l12m_qty"]:,}</td>'
            f'<td class="num">{b["pct_of_unpriced_eur"]:.1f}%</td>'
            f'<td>{who}</td></tr>\n'
        )
        if key == "lubricant_no_pr00_in_sap":
            lub = b

    sens = d["sensitivity"]
    class_map = d["class_mapping"]

    # The lubricant bucket is one customer's engine oil, so it gets its own small
    # table: the euro is attributable line by line rather than as a lump.
    lub_table = ""
    if lub and lub.get("pn_detail"):
        lub_details = "".join(
            f'<tr><td>{html.escape(str(p["pn"]))}</td>'
            f'<td>{html.escape(str(p["description"] or "n/a"))}</td>'
            f'<td class="num">{p["qty"]:,}</td>'
            f'<td class="num">{fmt_eur(p["eur"])}</td></tr>'
            for p in lub["pn_detail"]
        )
        lub_table = f"""
<h2>What the lubricant exclusion actually is</h2>
<p class="sub">{lub["rows"]} billed lines &mdash; lubricants and engine oil, all of it UMI Israel.
The new price file carries no lubricant part numbers, so there is no
comparison to make; these lines are listed so the lump sum is attributable.</p>
<div class="scroll"><table>
<thead><tr><th>Part number</th><th>Description as billed</th>
<th class="num">L12M qty</th><th class="num">L12M billed</th></tr></thead>
<tbody>{lub_details}
<tr class="tot"><td class="strong">Total</td><td></td>
<td class="num strong">{lub["l12m_qty"]:,}</td>
<td class="num strong">{fmt_eur(lub["l12m_billed_eur"])}</td></tr>
</tbody></table></div>
"""

    def named_codes(block) -> str:
        items = block.get("customers_named") or []
        if not items:
            return "&mdash;"
        return ", ".join(label_with_code(x["label"], x["code"]) for x in items)

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Base-price impact on the last 12 months of sales</title>
<style>
  :root {{ --navy:#15233c; --terra:#c0552d; --paper:#f7f4ee; --ink:#222;
           --line:#d9d3c8; --muted:#6b6459; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--paper); color:var(--ink);
          font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif; }}
  .wrap {{ max-width:1180px; margin:0 auto; padding:34px 22px 60px; }}
  h1 {{ font-family:Georgia,serif; color:var(--navy); font-size:29px; margin:0 0 6px; }}
  h2 {{ font-family:Georgia,serif; color:var(--navy); font-size:20px; margin:38px 0 4px; }}
  .sub {{ color:var(--muted); font-size:14px; margin:0 0 22px; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); gap:14px; }}
  .kpi {{ background:#fff; border:1px solid var(--line); border-left:5px solid var(--terra);
          padding:14px 16px; position:relative; }}
  .kpi .lbl {{ font-size:12px; letter-spacing:.06em; text-transform:uppercase;
               color:var(--muted); }}
  .kpi .val {{ font-family:Georgia,serif; font-size:27px; color:var(--navy);
               margin-top:6px; line-height:1.1; }}
  .kpi .note {{ font-size:12px; color:var(--muted); margin-top:6px; }}
  .kpi[data-tip]:hover::after {{ content:attr(data-tip); position:absolute;
      left:0; top:100%; z-index:40; width:290px; background:var(--navy);
      color:var(--paper); font-size:12px; line-height:1.45; padding:10px 12px;
      border-left:4px solid var(--terra); }}
  .card {{ background:#fff; border:1px solid var(--line); padding:16px 18px; margin-top:12px; }}
  .chartbox {{ position:relative; height:440px; }}
  .chartbox.tall {{ height:520px; }}
  table {{ border-collapse:collapse; width:100%; font-size:13px; }}
  th {{ text-align:left; background:var(--navy); color:var(--paper); font-weight:600;
        padding:8px 10px; position:sticky; top:0; }}
  td {{ padding:6px 10px; border-bottom:1px solid #ece7de; }}
  td.num {{ text-align:right; font-variant-numeric:tabular-nums; }}
  tr.il td {{ background:#fdf1ea; }}
  tr.tot td {{ border-top:2px solid var(--line); background:#faf8f4; }}
  td.strong {{ font-weight:600; }}
  .bname {{ font-weight:600; color:var(--navy); }}
  .bwho {{ font-size:12px; color:var(--muted); margin-top:3px; line-height:1.45; }}
  table.ex {{ min-width:940px; }}
  table.ex td:first-child {{ width:300px; }}
  table.pn td.pn {{ font-variant-numeric:tabular-nums; white-space:nowrap; }}
  table.pn td.desc {{ min-width:260px; max-width:340px; }}
  table.pn td.desc span {{ display:block; overflow-wrap:anywhere; line-height:1.4; }}
  .scroll {{ overflow:auto; max-height:430px; border:1px solid var(--line); background:#fff; }}
  .ref {{ font-size:12px; color:var(--muted); margin-top:8px; }}
  .foot {{ margin-top:44px; padding-top:14px; border-top:1px solid var(--line);
           font-size:12px; color:var(--muted); line-height:1.6; }}
  .warn {{ background:#fff8f0; border:1px solid var(--terra); border-left:5px solid var(--terra);
           padding:12px 14px; font-size:13px; margin-top:12px; }}
  ul.small {{ margin:8px 0 0 18px; padding:0; }}
  ul.small li {{ margin:4px 0; font-size:13px; }}
  .lf {{ display:flex; gap:16px; flex-wrap:wrap; font-size:13px; margin:4px 0 0; }}
  .lf span {{ display:inline-flex; align-items:center; gap:7px; }}
  .sw {{ width:12px; height:12px; border-radius:2px; display:inline-block; }}
</style></head>
<body><div class="wrap">

<h1>What the new base price does to each customer's basket</h1>
<p class="sub">New PRICE CD (10 Sep 2026) against the CY2026 revised base price, weighted by
each customer's own sales in the last 12 months &mdash; {d["window"]["start"]} to {d["window"]["end"]}.
Base price only: no FX applied to the price, no list change, no elasticity.</p>

<div class="grid">
  <div class="kpi" data-tip="Sales-weighted base-price increase across all in-scope network customers. Weight = L12M billed quantity. Formula: sum(qty x new BP) / sum(qty x prior BP) - 1.">
    <div class="lbl">Network weighted</div>
    <div class="val">{net["pct"]:.2f}%</div>
    <div class="note">base-price increase, L12M weighted</div></div>
  <div class="kpi" data-tip="What the base-price step is worth on last year's volume. JPY move divided by 163.7 JPY/EUR. This is a base-price effect, not incremental revenue: no elasticity is applied because it is not quotable at ISZE-to-distributor level.">
    <div class="lbl">Value of the step</div>
    <div class="val">{fmt_eur(net["step_eur"])}</div>
    <div class="note">on L12M volume, at {d["fx"]["jpy_per_eur"]} JPY/EUR</div></div>
  <div class="kpi" data-tip="Share of L12M quantity and of L12M euro value where both the new and the prior base price exist. The residual is named in the coverage table below, never dropped.">
    <div class="lbl">Priced coverage</div>
    <div class="val">{net["cov_qty"]:.1f}%</div>
    <div class="note">{net["cov_eur"]:.1f}% of L12M value &middot; {net["n_pn_priced"]:,} part numbers</div></div>
  <div class="kpi" data-tip="Priceable basket before and after the base-price step, holding last year's quantity. Not a forecast.">
    <div class="lbl">Basket, prior &rarr; new</div>
    <div class="val">{net["rev_prior_eur"]/1e6:.1f}M &rarr; {net["rev_new_eur"]/1e6:.1f}M</div>
    <div class="note">EUR on L12M quantity, base price only</div></div>
</div>

<h2>Where the euro lands, by distributor</h2>
<p class="sub">Euro value of the base-price step on each distributor's last-12-month volume.
Sold-to codes are rolled up to the distributor a price conversation is actually held at:
Germany and Portugal each settle through two codes, so the sold-to view alone would list
the same country twice.</p>
<div class="card"><div class="chartbox tall"><canvas id="custChart"></canvas></div>
<div class="lf">
  <span><i class="sw" style="background:#15233c"></i>network distributor</span>
  <span><i class="sw" style="background:#c0552d"></i>Israel &mdash; UMI and UTI shown separately, never blended</span>
</div>
<div class="ref">Hover a bar for the percentage, the L12M basket and the priced coverage.</div></div>

<h2>Who sits above or below the network figure</h2>
<p class="sub">The same step as a rate. The dashed line is the network weighted increase of
{net["pct"]:.2f}% &mdash; a distributor left of it absorbed less than the network average, which is
the conversation a distributor actually has about a price revision.</p>
<div class="card"><div class="chartbox tall"><canvas id="pctChart"></canvas></div>
<div class="ref">A high euro step with a low percentage means a large basket, not an
unfavourable price move. Read the two charts together.</div></div>

<h2>Israel: two codes, two rows</h2>
<p class="sub">Split by ERP sold-to code, which is the authority. The local payer is the same
legal entity for both, so the customer NAME column cannot separate them.</p>
<div class="scroll"><table>
<thead><tr><th>Distributor</th><th class="num">Weighted increase</th>
<th class="num">Value of the step</th><th class="num">L12M basket</th>
<th class="num">Priced coverage</th></tr></thead>
<tbody>{israel_rows}</tbody></table></div>

<h2>Every sold-to code behind that</h2>
<p class="sub">The same numbers at sold-to level, so the roll-up is auditable. Four distributors
settle through more than one code &mdash; Germany 2516 and 601, Portugal 519 and 92, Denmark 2027
and 2751 &mdash; which is why the ranked charts use the distributor level.</p>
<div class="scroll"><table>
<thead><tr><th>Distributor</th><th>Sold-to</th><th class="num">Weighted increase</th>
<th class="num">Value of the step</th><th class="num">L12M basket</th>
<th class="num">Priced coverage</th></tr></thead>
<tbody>{code_rows}</tbody></table></div>

<h2>Which price classes carry the step</h2>
<p class="sub">The 7 pricing classes, ranked by euro contribution. Class is a margin lever:
the same base-price move lands very differently depending on the class factor behind it.</p>
<div class="card"><div class="chartbox"><canvas id="classChart"></canvas></div>
<div class="ref">T&nbsp;= 20% gross margin class in the IML formula; C&nbsp;= 53%. Euro is the
step on L12M volume; the percentage beside each bar is that class's own weighted increase.</div></div>

<h2>The part numbers that carry the most euro</h2>
<p class="sub">A base-price move is only actionable if you can name the lines. Top 25 by euro
contribution, with the description as billed, the class and the quantity behind each.</p>
<div class="scroll"><table class="pn">
<thead><tr><th>Part number</th><th>Description</th><th>Class</th>
<th class="num">Weighted increase</th>
<th class="num">Value of the step</th><th class="num">L12M qty</th></tr></thead>
<tbody id="pnBody"></tbody></table></div>

<h2>What this comparison does not cover</h2>
<p class="sub">A residual that is not named reads as an unexplained hole. Every euro left out is
listed here with what it is, whose it is, and why the two price lists cannot be compared on it.
Everything below is a data-coverage fact, not a pricing decision: none of it was moved on price.</p>
<div class="scroll"><table class="ex">
<thead><tr><th>What it is</th><th class="num">Rows</th><th class="num">L12M billed</th>
<th class="num">L12M qty</th><th class="num">Share of the excluded euro</th>
<th>Whose it is</th></tr></thead>
<tbody>{unp_rows}
<tr><td><span class="bname">{html.escape(d["non_parts"].get("what", "Non-part billing"))}</span>
<div class="bwho">Excluded because: {html.escape(d["non_parts"].get("why", ""))}</div></td>
    <td class="num">{d["non_parts"]["rows"]:,}</td>
    <td class="num">{fmt_eur(d["non_parts"]["l12m_billed_eur"])}</td>
    <td class="num">&mdash;</td>
    <td class="num">&mdash;</td>
    <td>{named_codes(d["non_parts"])}</td></tr>
<tr><td><span class="bname">{html.escape(d["direct"].get("what", "Outside the network"))}</span>
<div class="bwho">Excluded because: {html.escape(d["direct"].get("why", ""))}</div></td>
    <td class="num">{d["direct"]["rows"]:,}</td>
    <td class="num">{fmt_eur(d["direct"]["l12m_billed_eur"])}</td>
    <td class="num">&mdash;</td>
    <td class="num">&mdash;</td>
    <td>{named_codes(d["direct"])}</td></tr>
</tbody></table></div>
<div class="ref">The lubricant lines are the UMI Israel engine-oil family: they sit in the
excluded total because the price file carries no lubricant part numbers at all, so they can
never be priced on both sides. They are named and listed in full below rather than left as a
bucket called &ldquo;lubricant&rdquo;.</div>
{lub_table}

<div class="warn">
<strong>Two judgements to read with the number.</strong>
<ul class="small">
<li><strong>Which prior price.</strong> The 12-month window opens
{d["sensitivity"]["prior_vintage"]["pre_revision_days_in_window"]} days before the CY2026 revision took effect, so its first
weeks ran on the older price. Weighting the whole year on the revised price gives
{fmt_eur(sens["prior_vintage"]["value_step_eur_revised_basis"])}; weighting by the price actually billed gives
{fmt_eur(sens["prior_vintage"]["value_step_eur_billed_basis"])}. Billing carries no price, so the second is a bound, not a measurement.</li>
<li><strong>The weight base.</strong> On each customer's own billed quantity the network lands at
{sens["weight_base"]["weighted_increase_pct_billing_qty"]:.2f}%. Weighted instead by the quantity in the pricing simulation it lands at
{sens["weight_base"]["weighted_increase_pct_sim_l12m_qty"]:.2f}% &mdash; a {abs(sens["weight_base"]["weighted_increase_pct_sim_l12m_qty"]-sens["weight_base"]["weighted_increase_pct_billing_qty"]):.2f} point spread between the two weight bases.</li>
</ul>
</div>

<div class="foot">
<strong>Method.</strong> delta = new base price &minus; prior base price (JPY per unit).
Weighted increase = sum(quantity &times; new BP) / sum(quantity &times; prior BP) &minus; 1.
Prior price = CY2026 revision (PRICE CD 250912). New price = PRICE CD 2026-09-10.
Weight = last 12 months of billing, {d["window"]["start"]} to {d["window"]["end"]}.
FX {d["fx"]["jpy_per_eur"]} JPY/EUR as of {d["fx"]["as_of"]}, used to value the step in euro only.<br>
<strong>Class mapping.</strong> {class_map["raw_codes_seen"]} raw class codes seen,
{class_map["unmapped_pn_rows"]} rows unmapped, {class_map["null_or_blank_class_rows"]} rows with no class.
Method: {class_map["method"]}. Unmapped rows are reported, never forced into a class.<br>
<strong>Scope.</strong> Network distributors only. Non-part billing (service fee / demurrage)
and the direct account are excluded and listed above.<br>
<strong>What this is not.</strong> Not a revenue or margin forecast. No elasticity coefficient is
applied &mdash; elasticity is not quotable at ISZE-to-distributor level. This is step one of the
pricing work: the FX phase and the price-playing phase follow.
</div>

</div>
<script type="application/json" id="payload">{payload}</script>
<script>{chart_js_inline()}</script>
<script>
(function() {{
  var D;
  try {{ D = JSON.parse(document.getElementById('payload').textContent); }}
  catch (e) {{ document.body.insertAdjacentHTML('afterbegin',
    '<p style="padding:20px;color:#c0552d">Payload failed to parse.</p>'); return; }}
  var NAVY='#15233c', TERRA='#c0552d', LINE='#d9d3c8', MUTED='#6b6459';

  function esc(s) {{
    return String(s).replace(/[&<>"]/g, function(c) {{
      return {{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c];
    }});
  }}

  function paintCustomers() {{
    var rows = D.customers.filter(function(r) {{ return r.step_eur > 0; }});
    var el = document.getElementById('custChart');
    if (!el) return;
    new Chart(el, {{
      type:'bar',
      data:{{
        labels: rows.map(function(r){{ return r.label; }}),
        datasets:[{{
          label:'Value of the base-price step (EUR)',
          data: rows.map(function(r){{ return r.step_eur; }}),
          backgroundColor: rows.map(function(r){{ return r.israel ? TERRA : NAVY; }}),
          borderRadius:3, barPercentage:0.82
        }}]
      }},
      options:{{
        indexAxis:'y', responsive:true, maintainAspectRatio:false,
        plugins:{{
          legend:{{ display:false }},
          tooltip:{{ callbacks:{{ label:function(c){{
            var r=rows[c.dataIndex];
            return ['EUR '+Math.round(r.step_eur).toLocaleString()+' base-price step',
                    r.pct.toFixed(2)+'% weighted increase',
                    'L12M basket EUR '+Math.round(r.l12m_eur).toLocaleString(),
                    'priced coverage '+r.cov.toFixed(1)+'%'];
          }} }} }}
        }},
        scales:{{
          x:{{ title:{{display:true,text:'EUR value of the step on L12M volume'}},
               grid:{{color:'#ece7de'}} }},
          y:{{ grid:{{display:false}} }}
        }}
      }}
    }});
  }}

  function paintPct() {{
    var rows = D.customers.slice().sort(function(a,b){{ return b.pct - a.pct; }});
    var el = document.getElementById('pctChart');
    if (!el) return;
    var REF = D.network.pct;
    var refPlugin = {{
      id:'refLine',
      afterDatasetsDraw:function(chart){{
        var y = chart.scales.y.getPixelForValue(REF);
        var a = chart.chartArea;
        var ctx = chart.ctx;
        ctx.save();
        ctx.setLineDash([7,5]); ctx.lineWidth=2; ctx.strokeStyle=TERRA;
        ctx.beginPath(); ctx.moveTo(a.left, y); ctx.lineTo(a.right, y); ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle=TERRA; ctx.font='600 12px -apple-system,Segoe UI,Arial';
        ctx.textAlign='right'; ctx.textBaseline='bottom';
        ctx.fillText('network '+REF.toFixed(2)+'%', a.right-6, y-4);
        ctx.restore();
      }}
    }};
    new Chart(el, {{
      type:'bar',
      data:{{
        labels: rows.map(function(r){{ return r.label; }}),
        datasets:[{{
          label:'Weighted base-price increase (%)',
          data: rows.map(function(r){{ return r.pct; }}),
          backgroundColor: rows.map(function(r){{ return r.israel ? TERRA : NAVY; }}),
          borderRadius:3, barPercentage:0.82
        }}]
      }},
      options:{{
        indexAxis:'y', responsive:true, maintainAspectRatio:false,
        plugins:{{
          legend:{{display:false}},
          tooltip:{{ callbacks:{{ label:function(c){{
            var r=rows[c.dataIndex];
            var d=r.pct-REF;
            return [r.pct.toFixed(2)+'% weighted increase',
                    (d>=0?'+':'')+d.toFixed(2)+' pts vs the network',
                    'EUR '+Math.round(r.step_eur).toLocaleString()+' base-price step',
                    'L12M basket EUR '+Math.round(r.l12m_eur).toLocaleString()];
          }} }} }}
        }},
        scales:{{
          x:{{ title:{{display:true,text:'Weighted base-price increase (%)'}},
               grid:{{color:'#ece7de'}} }},
          y:{{ grid:{{display:false}} }}
        }}
      }},
      plugins:[refPlugin]
    }});
  }}

  function paintClasses() {{
    var rows = D.by_class.filter(function(r) {{ return r.step_eur > 0; }});
    var el = document.getElementById('classChart');
    if (!el) return;
    new Chart(el, {{
      type:'bar',
      data:{{
        labels: rows.map(function(r){{ return 'Class '+r.cls+'  ('+r.pct.toFixed(2)+'%)'; }}),
        datasets:[{{
          label:'Value of the step (EUR)',
          data: rows.map(function(r){{ return r.step_eur; }}),
          backgroundColor: TERRA, borderRadius:3, barPercentage:0.7
        }}]
      }},
      options:{{
        responsive:true, maintainAspectRatio:false,
        plugins:{{
          legend:{{display:false}},
          tooltip:{{ callbacks:{{ label:function(c){{
            var r=rows[c.dataIndex];
            return ['EUR '+Math.round(r.step_eur).toLocaleString()+' base-price step',
                    r.pct.toFixed(2)+'% weighted increase for this class',
                    r.pn+' part numbers, '+r.qty.toLocaleString()+' units L12M',
                    'L12M billed EUR '+Math.round(r.l12m_eur).toLocaleString()];
          }} }} }}
        }},
        scales:{{
          x:{{ grid:{{display:false}} }},
          y:{{ title:{{display:true,text:'EUR value of the step'}}, grid:{{color:'#ece7de'}} }}
        }}
      }}
    }});
  }}

  function fillPn() {{
    var body = document.getElementById('pnBody');
    if (!body) return;
    body.innerHTML = D.top_pn.map(function(r){{
      var d = (r.desc || '').trim();
      return '<tr><td class="pn">'+r.pn+'</td>'
        + '<td class="desc">'+(d ? '<span title="'+esc(d)+'">'+esc(d)+'</span>' : 'n/a')+'</td>'
        + '<td>'+r.cls+'</td>'
        + '<td class="num">'+(r.pct==null?'n/a':r.pct.toFixed(2)+'%')+'</td>'
        + '<td class="num">EUR '+Math.round(r.step_eur).toLocaleString()+'</td>'
        + '<td class="num">'+r.qty.toLocaleString()+'</td></tr>';
    }}).join('');
  }}

  function paint() {{ paintCustomers(); paintPct(); paintClasses(); fillPn(); }}
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', paint);
  else paint();
}})();
</script>
</body></html>
"""


def main() -> int:
    if not CHART_JS.is_file():
        raise SystemExit(f"missing Chart.js: {CHART_JS}")
    meta, cust, pn = load()
    payload = build_payload(meta, cust, pn)
    if not payload["customers"]:
        raise SystemExit("no customer rows - refusing to write an empty page")
    html_doc = render(payload)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    HTML_PATH.write_text(html_doc, encoding="utf-8")

    cmd = ("@echo off\r\n"
           "setlocal\r\n"
           'cd /d "%~dp0"\r\n'
           'set "HTML=%~dp0ISZE_Price_BP_Weighted_Compare.html"\r\n'
           'if not exist "%HTML%" (\r\n'
           "  echo HTML is not next to this launcher:\r\n"
           "  echo %HTML%\r\n"
           "  pause\r\n"
           "  exit /b 1\r\n"
           ")\r\n"
           'start "" "%HTML%"\r\n'
           "if errorlevel 1 (\r\n"
           "  echo Browser did not start. Opening the folder instead.\r\n"
           '  explorer.exe "%~dp0"\r\n'
           "  pause\r\n"
           ")\r\n"
           "endlocal\r\n")
    CMD_PATH.write_bytes(cmd.encode("ascii"))

    print(f"wrote {HTML_PATH} ({HTML_PATH.stat().st_size:,} bytes)")
    print(f"wrote {CMD_PATH}")
    print(f"customers: {len(payload['customers'])} | classes: {len(payload['by_class'])} "
          f"| top pn: {len(payload['top_pn'])}")
    print(f"network {payload['network']['pct']:.2f}%  step "
          f"{payload['network']['step_eur']:,.0f} EUR")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
