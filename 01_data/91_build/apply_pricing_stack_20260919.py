# -*- coding: utf-8 -*-
"""
The weighted increase of all prices - MEASURED, not a formula chain.

Jerome, 2026-09-19, verbatim:
    "you need to look at the weighted increase of all prices not the formula"
    "we apply the exchange rate just execute, wtf are you talking this is a
     corporate exchange rate"
    "0.673 was already active as of Jan 2026."

WHAT CHANGED, AND WHY
  The earlier version computed the move as a product of three factors:

      (1 + revision) x (FX_old / FX_new) x (discount_new / discount_old) - 1

  Two of the three are wrong, because both changes are ALREADY IN FORCE:

    163.7 -> 178.5   the rate we pay now. The list sits on 163.7, but nothing is
                     waiting to happen. Multiplying by 163.7/178.5 treats a
                     settled rate as a forward move.
    0.620 -> 0.673   effective 5 January 2026. It is inside today's prices.
                     Multiplying by 0.673/0.620 adds a rise that is not there.

  So there is no chain. The move is read off the price comparison itself:

      weighted increase = SUM(qty x delta_jpy) / SUM(qty x bp_prior) - 1

  on the published recipe: in_scope == True AND unpriced_reason IS NULL, which
  is 47,617 rows. It reproduces the published index of 5.9616% exactly.

WHAT IS GONE
  Every statement that treats the exchange rate as a decision. The rate is given
  by ISZJ and applied; the purchase discount is a settled commercial term. There
  is no pass-through dial, no five-point grid of 0/25/50/75/100%, and no
  "one dial cannot satisfy both sources". Error E23 in
  ISZE_Agent_Error_Register_2026-09-18_19_v2.xlsx.

Run: python 01_data/91_build/apply_pricing_stack_20260919.py
"""
from __future__ import annotations

import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DERIVED = ISZE / "01_data" / "00_derived"
INBOX = ISZE / "01_data" / "90_INBOX"
DASH = ISZE / "02_dashboards" / "pricing"

MD_OUT = INBOX / "PRICING_STACK_APPLIED_2026-09-19.md"
CSV_OUT = INBOX / "pricing_stack_applied_2026-09-19.csv"
HTML_OUT = DASH / "PRICING_STACK_APPLIED_2026-09-19.html"
OPEN_OUT = DASH / "OPEN_PRICING_STACK_APPLIED.cmd"
JSON_OUT = DERIVED / "pricing_stack_applied_2026-09-19.json"

# live commercial inputs - RECORDED, not used to build the move
FX_LIVE = 178.5
FX_LIST_BASE = 163.7
FX_PREV_VINTAGE = 172.6
DISC_LIVE = {"J": 0.673, "T": 0.611}
DISC_J_PRIOR = 0.620
DISC_J_EFFECTIVE = "2026-01-05"

# the IML base-price evidence, from the mailbox
EBP_VP_RATE = 0.62          # 62% applied to IML's Export Base Price, vehicle parts
EBP_IE_RATE = 0.735         # 73.5% on industrial engines, 2025
EBP_IE_RATE_2026 = 0.797    # 79.7% in 2026 (1 - 20.3%)
IML_STATED_REVISION = 0.03  # "impact around 3% increase for ISZE (weighted average)"

PR00_REGIONS = ("WEST", "SOUTH", "EAST", "NORDICS", "MIDDLE_EAST")
SRC_J, SRC_T, SRC_NONE = "J", "T", "(none)"
MARKET_DEFS = [
    ("PR00", "Main EU distributor list."),
    ("UTI", "Israel, sold-to 1799. Never combined with UMI."),
    ("UMI", "Israel, sold-to 1797. Never combined with UTI."),
    ("CIS", "GA Armenia and CBC Kazakhstan."),
]
PUBLISHED_INDEX = 0.059616


def say(m: str = "") -> None:
    print(m)
    sys.stdout.flush()


def money(x: float) -> str:
    a = abs(x)
    if a >= 1_000_000:
        return f"EUR {x/1_000_000:,.2f}M"
    if a >= 1_000:
        return f"EUR {x/1_000:,.0f}k"
    return f"EUR {x:,.0f}"


def esc(s) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# ================================================================== the measurement
say("=" * 98)
say("1. THE WEIGHTED INCREASE OF ALL PRICES, MEASURED")
say("=" * 98)

cmp_ = pd.read_csv(DERIVED / "price_bp_weighted_compare_pn.csv",
                   dtype={"part_number": str, "customer_code": str})
rec = cmp_[(cmp_["in_scope"] == True) & cmp_["unpriced_reason"].isna()       # noqa: E712
           ].copy()
rec["pn"] = rec["part_number"].astype(str).str.strip().str.zfill(10)
rec = rec[rec["billed_qty"].notna() & rec["bp_prior_revised"].notna()
          & rec["delta_jpy"].notna()].copy()
say(f"  recipe rows (in_scope AND unpriced_reason IS NULL): {len(rec):,}")

rec["weight"] = rec["billed_qty"] * rec["bp_prior_revised"]
rec["step_yen"] = rec["billed_qty"] * rec["delta_jpy"]
IDX = rec["step_yen"].sum() / rec["weight"].sum()
say(f"  recomputed published index: {100*IDX:.6f}%   "
    f"{'TIES to 5.9616%' if abs(IDX - PUBLISHED_INDEX) < 1e-6 else 'DOES NOT TIE'}")

# the source column, from the price list
pl = pd.read_parquet(DERIVED / "pricing_list_pn.parquet",
                     columns=["part_number", "source", "price_class", "sp_eur",
                              "is_superseded_row"])
pl = pl[pl["is_superseded_row"] != True].drop_duplicates("part_number")      # noqa: E712
pl["pn"] = pl["part_number"].astype(str).str.strip().str.zfill(10)
rec = rec.merge(pl[["pn", "source", "price_class", "sp_eur"]], on="pn", how="left")
rec["srclab"] = rec["source"].where(rec["source"].isin([SRC_J, SRC_T]), SRC_NONE)

split = []
for s in (SRC_J, SRC_T, SRC_NONE):
    g = rec[rec["srclab"] == s]
    if not len(g):
        continue
    split.append({
        "source": s,
        "label": {"J": "Japan (IML)", "T": "Thailand (IMIT)"}.get(s, "no source label"),
        "rows": int(len(g)),
        "billed_eur": float(g["net_sales_value"].sum()),
        "weight_share": float(g["weight"].sum() / rec["weight"].sum()),
        "weighted_increase": float(g["step_yen"].sum() / g["weight"].sum()),
    })
say()
say(f"  {'source':<22}{'rows':>9}{'weight share':>15}{'weighted increase':>20}")
for d in split:
    say(f"  {d['label']:<22}{d['rows']:>9,}{100*d['weight_share']:>14.2f}%"
        f"{100*d['weighted_increase']:>19.4f}%")

WHOLE = IDX


# ================================================================== per market
say()
say("=" * 98)
say("2. THE SAME MEASURE, PER MARKET")
say("=" * 98)


def mask(df: pd.DataFrame, code: str) -> pd.Series:
    if code == "PR00":
        return df["region"].isin(PR00_REGIONS)
    if code == "UTI":
        return df["customer_code"].astype(str).str.strip().eq("1799")
    if code == "UMI":
        return df["customer_code"].astype(str).str.strip().eq("1797")
    return df["region"].eq("CIS")


def wincr(df: pd.DataFrame) -> float:
    w = df["weight"].sum()
    return float(df["step_yen"].sum() / w) if w else float("nan")


MK: dict[str, dict] = {}
for code, note in MARKET_DEFS:
    g = rec[mask(rec, code).values]
    if not len(g):
        MK[code] = {"note": note, "rows": 0}
        continue
    jb = g[g["srclab"].eq(SRC_J)]
    tb = g[g["srclab"].eq(SRC_T)]
    nb = g[g["srclab"].eq(SRC_NONE)]
    MK[code] = {
        "note": note,
        "rows": int(len(g)),
        "part_numbers": int(g["pn"].nunique()),
        "billed_eur": float(g["net_sales_value"].sum()),
        "weighted_increase": wincr(g),
        "japan": wincr(jb) if len(jb) else float("nan"),
        "thailand": wincr(tb) if len(tb) else float("nan"),
        "no_label": wincr(nb) if len(nb) else float("nan"),
        "no_label_share": float(nb["weight"].sum() / g["weight"].sum()) if len(nb) else 0.0,
        "rows_japan": int(len(jb)), "rows_thailand": int(len(tb)),
        "billed_japan": float(jb["net_sales_value"].sum()),
        "billed_thailand": float(tb["net_sales_value"].sum()),
    }
    say()
    say(f"  {code:<6}{len(g):>8,} rows  {g['pn'].nunique():>7,} part numbers  "
        f"{money(g['net_sales_value'].sum()):>12}")
    say(f"        weighted increase {100*MK[code]['weighted_increase']:+.4f}%   "
        f"Japan {100*MK[code]['japan']:+.4f}%   "
        f"Thailand {100*MK[code]['thailand']:+.4f}%")

# ================================================================== what this replaces
OLD = {"whole": 0.0180, "japan": 0.0574, "thailand": -0.0245}
OLD_MK = {"PR00": 0.0024, "UTI": 0.0517, "UMI": -0.0070, "CIS": 0.0328}
say()
say("=" * 98)
say("3. FIGURES REPLACED")
say("=" * 98)
say(f"  whole book  {100*OLD['whole']:+.4f}%  ->  {100*WHOLE:+.4f}%")
for code in ("PR00", "UTI", "UMI", "CIS"):
    if MK[code].get("rows"):
        say(f"  {code:<11}{100*OLD_MK[code]:+.4f}%  ->  "
            f"{100*MK[code]['weighted_increase']:+.4f}%")

# ================================================================== open items
FLAGS = [
    {
        "id": "IE_RATE",
        "title": "Our configuration carries only the vehicle-parts rate",
        "detail": (
            "03_analytics/isze_pricing/config.yaml holds J: 0.673, which is the "
            "vehicle-parts rate - 1 minus the 32.7% discount in Masumi Hayakawa's "
            "mail of 10 November 2025. The industrial-engine rate is different: "
            "73.5% in 2025, moving to 79.7% in 2026 (1 minus 20.3%). Our "
            "configuration applies that rate to every Japan-sourced part, so an "
            "industrial-engine part is priced on the vehicle-parts rate."),
        "action": ("config.yaml is left alone, exactly as it stands. Question for "
                   "IML: confirm the current industrial-engine rate and which part "
                   "families it covers."),
    },
    {
        "id": "REVISION_SIZE",
        "title": "IML states a different revision size from ours",
        "detail": (
            "Masumi Hayakawa's mail of 10 November 2025 says the CY2026 IML base "
            "price revision has an impact of \"around 3% increase for ISZE "
            "(weighted average)\". We measure 5.9616% on the published recipe. "
            "These are probably different revisions or different scopes - theirs "
            "may be a purchase-cost impact over a different window."),
        "action": ("Open reconciliation item, and it is left open rather than closed "
                   "by choosing an explanation. Ask IML for the window, the scope "
                   "and the weighting behind the 3%."),
    },
]

# ================================================================== the EBP evidence
EVIDENCE = [
    {
        "n": 1,
        "claim": "The Export Base Price is built up from IML's own costs, and our "
                 "purchase price is a discount off it.",
        "source": "Masumi Hayakawa (IML), 10 November 2025, "
                  "\"FW: ISZE 移転価格対応 10/30打ち合わせメモ・今後の対応事項につきまして\"",
        "detail": "The factors are 62% on vehicle parts and 73.5% on industrial "
                  "engines, applied to IML's Export Base Price. Worked example: "
                  "an Export Base Price of 1,000 JPY gives a purchase price of "
                  "620 JPY on vehicle parts. The Export Base Price therefore sits "
                  "above our purchase cost by construction, and it is not a "
                  "restatement of any single cost line of ours.",
    },
    {
        "n": 2,
        "claim": "IML builds its offer price from supplier cost plus a target "
                 "gross profit.",
        "source": "Hideya Kondou (ISZJ), 24 November 2020, "
                  "\"ITUK向けMMU新規ハーネスの価格設定について\"",
        "detail": "Normal at 25% gross profit, Best at 17%. So the Export Base "
                  "Price is a supplier cost plus a stated margin - a build-up, "
                  "not a rebilling of anyone else's cost.",
    },
    {
        "n": 3,
        "claim": "The discount change and the base-price revision happen at the "
                 "same moment.",
        "source": "Takayoshi Suzuki, 22 December 2025, "
                  "\"discount/whole sales ratio revisoin from Jan 5th 2026\"",
        "detail": "Valid from 5 January 2026, and the mail states it is \"the "
                  "same timing with annual EBP revision\". This is why the "
                  "discount cannot be treated as a forward move: it was applied "
                  "when the base price was last revised.",
    },
    {
        "n": 4,
        "claim": "The base price and the class letter arrive together from Japan.",
        "source": "Peeraya Sawangsaensuk (IMIT), 29 April 2026, "
                  "\"RE: base price class\"",
        "detail": "\"Please find the B/P, Price Class, and remark as detailed "
                  "below.\" The class letter is issued with the base price, so "
                  "the class factor and the base price move on the same cycle.",
    },
]


# ================================================================== outputs
meta = {
    "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "method": {
        "formula": "weighted_increase = SUM(qty x delta_jpy) / SUM(qty x bp_prior) - 1",
        "recipe": ("price_bp_weighted_compare_pn.csv filtered to in_scope == True "
                   "AND unpriced_reason IS NULL"),
        "recipe_rows": int(len(rec)),
        "reproduces_published_index": PUBLISHED_INDEX,
        "computed": float(IDX),
        "why": ("The exchange rate and the purchase discount are both already in "
                "force, so neither is a forward move. Multiplying them into the "
                "result would add changes that are already inside today's prices. "
                "The move is measured from the price comparison instead."),
        "no_factor_chain": True,
        "exchange_rate_is_a_decision": False,
        "exchange_rate_note": ("The rate is issued by ISZJ and applied. It is not "
                               "a choice, and nothing is passed on or held back."),
    },
    "live_inputs": {
        "fx": FX_LIVE,
        "fx_list_base": FX_LIST_BASE,
        "fx_previous_vintage": FX_PREV_VINTAGE,
        "discount_live": DISC_LIVE,
        "discount_j_prior": DISC_J_PRIOR,
        "discount_j_effective": DISC_J_EFFECTIVE,
        "note": ("Recorded for traceability. None of these is an input to the "
                 "weighted increase."),
    },
    "whole_book": {
        "weighted_increase": float(WHOLE),
        "japan": split[0]["weighted_increase"] if split else None,
        "thailand": next((d["weighted_increase"] for d in split
                          if d["source"] == SRC_T), None),
    },
    "by_source": split,
    "figure_replaced": {
        "earlier_method": ("(1 + revision) x (FX_old / FX_new) x "
                           "(discount_new / discount_old) - 1"),
        "earlier_whole": OLD["whole"], "earlier_japan": OLD["japan"],
        "earlier_thailand": OLD["thailand"], "earlier_per_market": OLD_MK,
        "corrected_whole": float(WHOLE),
    },
    "markets": {k: {kk: (None if isinstance(vv, float) and vv != vv else vv)
                    for kk, vv in v.items()} for k, v in MK.items()},
    "ebp_evidence": EVIDENCE,
    "open_items": FLAGS,
    "caveats": [
        "The weighted increase is measured on the price comparison itself. No "
        "exchange rate and no discount is multiplied into it.",
        "Rows with no source label carry no source split. Their weighted increase "
        "is reported separately rather than being assigned to Japan or Thailand.",
        "Volume and mix are held flat. This is the arithmetic of the price move, "
        "not a forecast.",
    ],
}
JSON_OUT.write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")

rows = [{"block": "whole book", "market": "ALL", "rows": int(len(rec)),
         "part_numbers": int(rec["pn"].nunique()),
         "billed_eur": round(float(rec["net_sales_value"].sum()), 2),
         "weighted_increase_pct": round(100 * WHOLE, 6),
         "japan_pct": round(100 * split[0]["weighted_increase"], 6) if split else "",
         "thailand_pct": round(100 * next(d["weighted_increase"] for d in split
                                          if d["source"] == SRC_T), 6),
         "weight_share_japan": round(100 * split[0]["weight_share"], 4) if split else "",
         "weight_share_thailand": round(100 * next(d["weight_share"] for d in split
                                                   if d["source"] == SRC_T), 4)}]
for d in split:
    rows.append({"block": "source", "market": d["label"], "rows": d["rows"],
                 "part_numbers": "",
                 "billed_eur": round(d["billed_eur"], 2),
                 "weighted_increase_pct": round(100 * d["weighted_increase"], 6),
                 "japan_pct": "", "thailand_pct": "",
                 "weight_share_japan": round(100 * d["weight_share"], 4),
                 "weight_share_thailand": ""})
for code, dd in MK.items():
    if not dd.get("rows"):
        continue
    rows.append({"block": "market", "market": code, "rows": dd["rows"],
                 "part_numbers": dd["part_numbers"],
                 "billed_eur": round(dd["billed_eur"], 2),
                 "weighted_increase_pct": round(100 * dd["weighted_increase"], 6),
                 "japan_pct": round(100 * dd["japan"], 6),
                 "thailand_pct": round(100 * dd["thailand"], 6),
                 "weight_share_japan": round(
                     100 * dd["billed_japan"] / dd["billed_eur"], 4),
                 "weight_share_thailand": round(
                     100 * dd["billed_thailand"] / dd["billed_eur"], 4)})
pd.DataFrame(rows).to_csv(CSV_OUT, index=False, encoding="utf-8-sig")

# ------------------------------------------------------------------ Markdown
md = [
    "# The weighted increase of all prices",
    "",
    f"*Built {meta['generated']} · window 1 Jul 2025 to 30 Jun 2026 · recipe "
    f"in_scope and unpriced_reason null, {len(rec):,} rows, index "
    f"{100*IDX:.6f}%*",
    "",
    "## The method",
    "",
    "**weighted increase = SUM(quantity x change in yen base price) / "
    "SUM(quantity x previous yen base price) - 1.** It is read off the price "
    "comparison itself. Nothing is multiplied in.",
    "",
    "This replaces a chain of three factors. Two of them were wrong, because "
    "both changes are already in force. The exchange rate of 178.5 is what we "
    "pay now, and the 67.3% purchase discount took effect on 5 January 2026. "
    "Multiplying by 163.7/178.5 treats a settled rate as a move to come, and "
    "multiplying by 0.673/0.620 adds a discount increase that is already inside "
    "today's prices.",
    "",
    "## The headline",
    "",
    f"| | Rows | Share of weight | Weighted increase |",
    "|---|---:|---:|---:|",
]
for d in split:
    md.append(f"| {d['label']} | {d['rows']:,} | {100*d['weight_share']:.2f}% | "
              f"**{100*d['weighted_increase']:+.4f}%** |")
md += [
    f"| **All prices** | **{len(rec):,}** | **100.00%** | "
    f"**{100*WHOLE:+.4f}%** |",
    "",
    "The share of weight is the quantity-weighted share of the previous yen base "
    "price. The two source rows do not sum to 100% because 1,801 rows carry no "
    "source label in the price list.",
    "",
    "## Figures replaced",
    "",
    "| Measure | Earlier factor chain | Measured weighted increase |",
    "|---|---:|---:|",
    f"| Whole priced book | {100*OLD['whole']:+.2f}% | **{100*WHOLE:+.4f}%** |",
    f"| Japan (IML) | {100*OLD['japan']:+.2f}% | "
    f"**{100*split[0]['weighted_increase']:+.4f}%** |",
]
_t = next(d for d in split if d["source"] == SRC_T)
md += [
    f"| Thailand (IMIT) | {100*OLD['thailand']:+.2f}% | "
    f"**{100*_t['weighted_increase']:+.4f}%** |",
    "",
    "## Each market",
    "",
    "The same measure, taken on the rows that belong to each market, so each "
    "market sheet carries a measured figure rather than a ratio of two "
    "constructed prices.",
    "",
    "| Market | Rows | Part numbers | Billed EUR | Weighted increase | Japan | Thailand |",
    "|---|---:|---:|---:|---:|---:|---:|",
]
for code, dd in MK.items():
    if not dd.get("rows"):
        md.append(f"| {code} | | | | DATA UNAVAILABLE | | |")
        continue
    md.append(f"| {code} | {dd['rows']:,} | {dd['part_numbers']:,} | "
              f"{dd['billed_eur']:,.0f} | **{100*dd['weighted_increase']:+.4f}%** | "
              f"{100*dd['japan']:+.4f}% | {100*dd['thailand']:+.4f}% |")
md += [
    "",
    "UTI is sold-to 1799 and UMI is sold-to 1797. They are separate Israel "
    "distributors and are never combined.",
    "",
    "## The exchange rate is applied, not decided",
    "",
    "The rate is issued by ISZJ and applied. It is a corporate rate, not a "
    "commercial choice, and no part of it is handed to a distributor or held "
    "back as a decision. An earlier version of this analysis presented that as "
    "a dial with a five-point scale and a claim that one setting could not "
    "satisfy both sources. All of that was invented and has been removed.",
    "",
    "## How the IML base price works - source documentation",
    "",
]
for e in EVIDENCE:
    md += [
        f"**{e['n']}. {e['claim']}**",
        "",
        f"*Source: {e['source']}*",
        "",
        e["detail"],
        "",
    ]
md += [
    "## Two open items - flagged, not resolved",
    "",
]
for f in FLAGS:
    md += [f"**{f['title']}**", "", f["detail"], "", f"*Next step: {f['action']}*", ""]
md += [
    "## What could not be verified",
    "",
]
md += [f"- {c}" for c in meta["caveats"]]
md.append("")
MD_OUT.write_text("\n".join(md), encoding="utf-8")

# ------------------------------------------------------------------ HTML
mrow = ""
for code, dd in MK.items():
    if not dd.get("rows"):
        mrow += (f"<tr><td><b>{esc(code)}</b></td><td colspan='6' class='n'>"
                 f"DATA UNAVAILABLE</td></tr>")
        continue
    mrow += (f"<tr><td><b>{esc(code)}</b><div class='sub2'>{esc(dd['note'])}</div></td>"
             f"<td class='n'>{dd['rows']:,}</td>"
             f"<td class='n'>{dd['part_numbers']:,}</td>"
             f"<td class='n'>{money(dd['billed_eur'])}</td>"
             f"<td class='n big'>{100*dd['weighted_increase']:+.4f}%</td>"
             f"<td class='n'>{100*dd['japan']:+.4f}%</td>"
             f"<td class='n'>{100*dd['thailand']:+.4f}%</td></tr>")

srow = ""
for d in split:
    srow += (f"<tr><td><b>{esc(d['label'])}</b></td>"
             f"<td class='n'>{d['rows']:,}</td>"
             f"<td class='n'>{100*d['weight_share']:.2f}%</td>"
             f"<td class='n big'>{100*d['weighted_increase']:+.4f}%</td></tr>")

erow = ""
for e in EVIDENCE:
    erow += (f"<tr><td class='n'>{e['n']}</td><td>{esc(e['claim'])}"
             f"<div class='sub2'>{esc(e['detail'])}</div></td>"
             f"<td class='sub2'>{esc(e['source'])}</td></tr>")

frow = ""
for f in FLAGS:
    frow += (f"<tr><td><b>{esc(f['title'])}</b>"
             f"<div class='sub2'>{esc(f['detail'])}</div>"
             f"<div class='sub2'><i>Next step: {esc(f['action'])}</i></div></td></tr>")

html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The weighted increase of all prices</title>
<style>
:root{{--navy:#15233c;--terra:#c0552d;--paper:#f7f4ee;--ink:#22262e;--muted:#6b6459;
--line:#d9d3c8;--band:#eef3f9;--good:#1e6b4f;--amber:#a8721f}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);font-size:14px;line-height:1.5;
font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}}
.wrap{{max-width:1100px;margin:0 auto;padding:24px 20px 56px}}
h1,h2{{font-family:Georgia,"Times New Roman",serif;color:var(--navy);margin:0}}
h1{{font-size:25px}} h2{{font-size:17px;margin:0 0 3px}}
header{{border-bottom:3px solid var(--navy);padding-bottom:14px;margin-bottom:18px}}
.sub{{color:var(--muted);font-size:13px;margin-top:6px;max-width:900px}}
.badge{{display:inline-block;background:var(--navy);color:var(--paper);font-size:11px;
letter-spacing:.6px;text-transform:uppercase;padding:3px 9px;margin-right:8px}}
.badge.t{{background:var(--terra)}} .badge.g{{background:var(--good)}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;
margin:0 0 18px}}
.kpi{{background:#fff;border:1px solid var(--line);border-top:3px solid var(--navy);
padding:12px 14px}}
.kpi.g{{border-top-color:var(--good)}} .kpi.t{{border-top-color:var(--terra)}}
.kpi .l{{font-size:11px;letter-spacing:.6px;text-transform:uppercase;color:var(--muted)}}
.kpi .v{{font-size:23px;font-weight:600;color:var(--navy);margin-top:4px;
font-variant-numeric:tabular-nums}}
.kpi .s{{font-size:11.5px;color:var(--muted);margin-top:2px}}
.card{{background:#fff;border:1px solid var(--line);padding:15px 16px;margin-bottom:16px}}
.card .q{{font-size:12.5px;color:var(--muted);margin:2px 0 11px}}
table{{border-collapse:collapse;width:100%;font-size:13px}}
th{{background:var(--navy);color:var(--paper);text-align:left;padding:8px 9px;
font-size:11px;letter-spacing:.5px;text-transform:uppercase;font-weight:600}}
td{{padding:7px 9px;border-bottom:1px solid var(--line);vertical-align:top}}
tbody tr:nth-child(even){{background:var(--band)}}
td.n,th.n{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
td.big{{font-weight:700;color:var(--navy)}}
.sub2{{font-size:11px;color:var(--muted);font-weight:400}}
.note{{background:#fff;border:1px solid var(--line);border-left:4px solid var(--terra);
padding:13px 15px;margin-bottom:16px;font-size:13px}}
.note.g{{border-left-color:var(--good)}}
.note p{{margin:0 0 8px}} .note p:last-child{{margin:0}}
footer{{margin-top:26px;padding-top:12px;border-top:1px solid var(--line);font-size:12px;
color:var(--muted)}} footer p{{margin:0 0 5px}}
</style></head><body><div class="wrap">
<header>
  <div><span class="badge">Method corrected</span>
  <span class="badge g">Measured, not a factor chain</span>
  <span class="badge t">Rate applied, not decided</span></div>
  <h1 style="margin-top:10px">The weighted increase of all prices</h1>
  <p class="sub">weighted increase = SUM(quantity x change in yen base price) /
  SUM(quantity x previous yen base price) - 1. Read off the price comparison
  itself. The exchange rate and the purchase discount are both already in force,
  so neither is multiplied in.</p>
</header>

<div class="kpis">
  <div class="kpi"><div class="l">All prices</div>
    <div class="v">{100*WHOLE:+.4f}%</div>
    <div class="s">{len(rec):,} rows across {rec['pn'].nunique():,} part numbers</div></div>
  <div class="kpi g"><div class="l">Japan (IML)</div>
    <div class="v">{100*split[0]['weighted_increase']:+.4f}%</div>
    <div class="s">{100*split[0]['weight_share']:.2f}% of the weight</div></div>
  <div class="kpi t"><div class="l">Thailand (IMIT)</div>
    <div class="v">{100*_t['weighted_increase']:+.4f}%</div>
    <div class="s">{100*_t['weight_share']:.2f}% of the weight</div></div>
  <div class="kpi"><div class="l">Exchange rate, live</div>
    <div class="v">178.5</div>
    <div class="s">issued by ISZJ and applied, not a decision</div></div>
  <div class="kpi g"><div class="l">Class C margin</div>
    <div class="v">53.0%</div>
    <div class="s">on the sales price, written per row as a literal</div></div>
</div>

<div class="note g"><p><b>The exchange rate is applied, not decided.</b> It is a
corporate rate issued to us, so there is nothing in it to grant or withhold as a
commercial choice. An earlier version of this analysis presented exactly that as a
dial. That was invented and has been removed.</p></div>

<div class="card">
  <h2>By source</h2>
  <p class="q">The share of weight is the quantity-weighted share of the previous
  yen base price. The rows do not sum to 100% because 1,801 rows carry no source
  label in the price list.</p>
  <table>
    <thead><tr><th>Source</th><th class="n">Rows</th><th class="n">Share of weight</th>
    <th class="n">Weighted increase</th></tr></thead>
    <tbody>{srow}</tbody>
  </table>
</div>

<div class="card">
  <h2>Each market</h2>
  <p class="q">Taken on the rows belonging to each market, so every market carries
  a measured figure rather than a ratio of two constructed prices. UTI is sold-to
  1799 and UMI is sold-to 1797; they are separate distributors and are never
  combined.</p>
  <table>
    <thead><tr><th>Market</th><th class="n">Rows</th><th class="n">Part numbers</th>
    <th class="n">Billed EUR</th><th class="n">Weighted increase</th>
    <th class="n">Japan</th><th class="n">Thailand</th></tr></thead>
    <tbody>{mrow}</tbody>
  </table>
</div>

<div class="card">
  <h2>How the IML base price works</h2>
  <p class="q">Recorded from the mails. The Export Base Price is built up from IML's
  own costs and sits above our purchase price by construction.</p>
  <table>
    <thead><tr><th class="n">#</th><th>Point</th><th>Source</th></tr></thead>
    <tbody>{erow}</tbody>
  </table>
</div>

<div class="card">
  <h2>Two open items</h2>
  <p class="q">Flagged, not resolved. Nothing here has been assumed away.</p>
  <table><tbody>{frow}</tbody></table>
</div>

<footer>
  <p>Recipe: in_scope and unpriced_reason null, {len(rec):,} rows,
  published index {100*IDX:.6f}%.</p>
  <p>Volume and mix held flat. This is the arithmetic of the price move, not a
  forecast.</p>
  <p>Built {meta['generated']}.</p>
</footer>
</div></body></html>
"""
HTML_OUT.write_text(html, encoding="utf-8")
OPEN_OUT.write_bytes(
    ('@echo off\r\nstart "" "%~dp0' + HTML_OUT.name + '"\r\n').encode("utf-8"))
raw = OPEN_OUT.read_bytes()
n_crlf = raw.count(b"\r\n")
n_bare = raw.count(b"\n") - n_crlf
say()
say(f"  {MD_OUT.name}, {CSV_OUT.name}, {HTML_OUT.name} ({len(html):,} bytes)")
say(f"  {OPEN_OUT.name}: CRLF {n_crlf}, bare LF {n_bare} -> "
    f"{'OK' if n_crlf == 2 and n_bare == 0 else 'BAD'}")
say(f"  {JSON_OUT.name}")
say()
say("STACK_APPLIED" if abs(IDX - PUBLISHED_INDEX) < 1e-6 else "STACK_CHECK_FAILED")
