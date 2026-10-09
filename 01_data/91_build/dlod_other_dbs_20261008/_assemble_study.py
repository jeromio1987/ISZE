# -*- coding: utf-8 -*-
"""Assemble DLOD_OTHER_DISTRIBUTORS_STUDY_2026-10-08.md from payload.json + model.json (all tables computed, none typed)."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).parent
OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\01_Strategy\DLOD_OTHER_DISTRIBUTORS_STUDY_2026-10-08.md")
pl = json.loads((HERE / "payload.json").read_text(encoding="utf-8"))
md = json.loads((HERE / "model.json").read_text(encoding="utf-8"))
D = {d["code"]: d for d in pl["dists"]}
M = {r["code"]: r for r in md["rows"]}
R = pl["register"]
W = pl["windows"]
NAME = {"ITUK": "ITUK", "IUK": "IUK", "UTI": "UTI", "UMI": "UMI", "GERMANY": "Germany", "BELGIUM": "Belgium", "PORTUGAL": "Portugal",
        "NORWAY": "Norway", "SWEDEN": "Sweden", "IRELAND": "Ireland", "GREECE": "Greece", "CYPRUS": "Cyprus", "HUNGARY": "Hungary",
        "FINLAND": "Finland", "MALTA": "Malta", "ROMANIA": "Romania", "DENMARK": "Denmark", "ICELAND": "Iceland"}
ORDER = [x["code"] for x in sorted([d for d in pl["dists"] if d["code"] != "ITUK"], key=lambda d: -M[d["code"]]["P"])]
TIER_A = ["IUK", "UTI", "GERMANY", "BELGIUM", "PORTUGAL"]
TIER_B = ["NORWAY", "SWEDEN", "IRELAND"]
TIER_C = [c for c in ORDER if c not in TIER_A + TIER_B]
SCOPE = {"CV": "trucks", "LCV": "pickups/vans", "MIXED": "mixed"}


def e0(x):
    return "€{:,.0f}".format(x)


def ek(x):
    s = "−" if x < 0 else ""
    x = abs(x)
    return s + ("€{:,.1f}k".format(x / 1000) if x >= 1000 else "€{:,.0f}".format(x))


def er(x, base=1000):
    return "€{:,.0f}".format(round(x / base) * base)


def pc(x, n=0):
    return ("{:." + str(n) + "f}%").format(x * 100)


def table(head, rows, align=None):
    align = align or ["l"] + ["r"] * (len(head) - 1)
    sep = ["---:" if a == "r" else ":---" for a in align]
    out = ["| " + " | ".join(head) + " |", "| " + " | ".join(sep) + " |"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


# ---------------------------------------------------------------- tables
def t_pools():
    rows = []
    for c in ["ITUK"] + ORDER:
        d = D[c]
        rows.append([NAME[c] + (" (reference)" if c == "ITUK" else ""), SCOPE[d["scope"]], e0(d["billed"]),
                     "{} ({})".format(e0(d["warranty"]), pc(d["warranty_share"])), e0(d["profile"]), e0(d["profile_low"]),
                     pc(d["gm"]), "{:,.0f}".format(d["uio"]), d["dealers"] if d["dealers"] else "none on file",
                     d["std_file"] or "none"])
    return table(["Distributor", "Fleet type", "Billed FY2026", "Warranty inside billed", "Hard-part billing, warranty left in",
                  "Hard-part billing, warranty out", "ISZE margin", "Vehicles in service", "Dealers on file", "Sales-to-dealer data"], rows,
                 ["l", "l", "r", "r", "r", "r", "r", "r", "r", "l"])


def t_direct():
    rows = []
    for c in ["ITUK"] + ORDER:
        r = M[c]
        rows.append([NAME[c] + (" (ref.)" if c == "ITUK" else ""), e0(r["P"]), "{:.0f}".format(r["cases_central"]),
                     ("{:.1f}".format(r["cases_per_dealer"]) if r["cases_per_dealer"] else "n/a"), e0(r["cost_central"]),
                     e0(r["gain_central"]), e0(r["net_central"]), pc(r["p_star_phi50"]), pc(r["p_star_phi100"])])
    return table(["Distributor", "Hard-part billing (warranty out)", "Supported cases a year", "Cases per dealer a year",
                  "ISZE credit (cost)", "ISZE margin kept", "Net to ISZE", "Save rate needed, ISZE pays half",
                  "Save rate needed, ISZE pays all"], rows)


def t_grid():
    rows = []
    for u in (1, 3, 6, 10):
        rows.append(["{}%".format(u)] + [ek(md["totals"]["u{}_p{}".format(u, p)]) for p in (25, 50, 75)])
    return table(["Share of hard-part billing on supported cases", "25% of supported jobs really saved", "50% saved", "75% saved"], rows)


def t_indirect():
    rows = []
    for c in ["ITUK"] + ORDER:
        r = M[c]
        rows.append([NAME[c] + (" (ref.)" if c == "ITUK" else ""), e0(r["margin_per_vehicle"]), e0(r["direct_margin_per_saved_case"]),
                     e0(r["indirect_3y_per_saved_vehicle"]), pc(r["p_star_delta0"]), pc(r["p_star_delta25"]), pc(r["p_star_delta50"])])
    return table(["Distributor", "ISZE margin per truck per year", "ISZE margin on one saved job", "Three years of a kept truck",
                  "Save rate needed, jobs only", "…if 1 in 4 saved customers stays 3 years", "…if 1 in 2 stays 3 years"], rows)


def t_rebate():
    rows = []
    for c in ["ITUK"] + ORDER:
        d = D[c]
        if d["rebate_fy26"] <= 0 and d["rebate_fy25"] <= 0:
            continue
        cost = M[c]["cost_central"]
        by = {}
        for x in d["rebate_labelled"]:
            by[x["klass"]] = by.get(x["klass"], 0.0) + x["eur"]
        kick = by.get("kickback", 0.0)
        other = "; ".join("{} {}".format(k, e0(v)) for k, v in by.items() if k not in ("kickback",)) or "none"
        rows.append([NAME[c] + (" (ref.)" if c == "ITUK" else ""), e0(d["rebate_fy25"]), e0(d["rebate_fy26"]), e0(kick), other,
                     pc(d["rebate_fy26"] / d["billed"], 1), e0(cost), pc(cost / d["rebate_fy26"]) if d["rebate_fy26"] else "n/a"])
    tot25 = sum(D[c]["rebate_fy25"] for c in D)
    tot26 = sum(D[c]["rebate_fy26"] for c in D)
    rows.append(["**Total**", "**" + e0(tot25) + "**", "**" + e0(tot26) + "**", "**" + e0(pl["rebate_class_totals"]["kickback"]) + "**", "", "", "", ""])
    return table(["Distributor", "Year-end credits FY2025", "FY2026", "…of which labelled kickback", "Other labels in the order file",
                  "FY2026 as % of billed", "DLOD at the central case", "…as share of the FY2026 credits"], rows,
                 ["l", "r", "r", "r", "l", "r", "r", "r"])


def t_contest():
    rows = []
    for c in pl["contest"]:
        if c["markets"] == "all 18 distributors":
            continue
        rows.append([c["source"], c["markets"], "{} of {}".format(c["pns_hard_in_pool"], c["pns_priced"]), pc(c["coverage"], 1),
                     pc(c["share_below10"]), pc(c["share_below25"]), pc(c["share_above"]), ("0%" if abs(c["wtd_delta"]) < 0.005 else "{:+.0f}%".format(c["wtd_delta"] * 100))])
    return table(["Source", "Weighted by billing of", "Hard parts priced / parts in the file", "Share of hard-part billing covered",
                  "…where independent price is 10%+ below ISZE", "…25%+ below", "…above ISZE price", "Average gap (independent vs ISZE)"], rows)


def t_selffund():
    rows = []
    for s in md["selffund"]:
        marg = 1 - 1 / s["price_ratio"]
        rows.append([pc(marg), pc(s["retained_margin_on_offer"]), pc(s["isze_share_needed"])])
    return table(["Distributor's normal margin on its dealer price", "Margin left on the offer after a discount of 17.6%",
                  "Share of the discount ISZE must fund to leave the distributor 20% margin"], rows)


def t_verdict():
    rows = []
    why = {
        "IUK": "Largest vehicle base (47,783), 43 dealers on file and a sales-to-dealer file. Pickups, so a kept truck is worth less (€45 a year). 22% of its billing is warranty.",
        "UTI": "Closest to ITUK: trucks, margin per truck €123. Lowest parts spend against target of the A-markets (37%, warranty out). Sales-to-dealer data for only 8 months. A copy of ITUK's deal workbook sits in the UTI project folder, dated 23 Jul 2026.",
        "GERMANY": "Highest ISZE margin of the A-markets (49%) and a €1.3M hard-part base. No dealer list and no sales-to-dealer file, so nothing to measure against yet. 17% warranty.",
        "BELGIUM": "Dealer list of 34. Already bills 83% of its modelled target, so little is leaking. The Benelux billing covers more than the Belgian fleet, so per-truck figures are overstated.",
        "PORTUGAL": "Smallest A-market (45 cases). 16 dealers and a sales-to-dealer file make it the easiest to measure.",
        "NORWAY": "28 cases across 38 dealers is 0.7 a dealer a year. Not a habit. Highest rebate in the group (2.9% of billed).",
        "SWEDEN": "30 cases a year, no dealer list.",
        "IRELAND": "32 cases a year. Fleet base is unresolved (2,161 vs 3,056 trucks), so per-truck values carry a range.",
    }
    for c in TIER_A + TIER_B + TIER_C:
        r = M[c]
        tier = "A" if c in TIER_A else "B" if c in TIER_B else "C"
        step = {"A": "No-money log, two quarters", "B": "Not now. Revisit if the A-markets pass", "C": "No case-by-case programme"}[tier]
        w = why.get(c, "{:.0f} cases a year, {} of net at the central case.".format(r["cases_central"], ek(r["net_central"])))
        if c == "UMI":
            w = "Warranty is 54% of billing, which leaves only €0.3M of hard-part billing. 14 cases a year."
        rows.append([NAME[c], tier, "{:.0f}".format(r["cases_central"]), ek(r["net_central"]), step, w])
    return table(["Distributor", "Tier", "Cases a year", "Net, central case", "What to do", "Why"], rows, ["l", "l", "r", "r", "l", "l"])


def t_families():
    rows = [[f["fam"], f["lines"], e0(f["support_eur"]), pc(f["share"])] for f in R["families"][:8]]
    return table(["Part family (Isuzu parts tree)", "Supported lines", "Support (EUR at 1.17)", "Share of support"], rows)


# ---------------------------------------------------------------- numbers used in prose
others = [M[c] for c in ORDER]
tot_net = sum(r["net_central"] for r in others)
tot_cost = sum(r["cost_central"] for r in others)
tot_gain = sum(r["gain_central"] for r in others)
tot_ceiling = sum(r["ceiling_u3"] for r in others)
tot_pool = sum(r["P"] for r in others)
tot_billed = sum(D[c]["billed"] for c in ORDER)
gm_w = md["ctx"]["gm_weighted_others"]
cases = sum(r["cases_central"] for r in others)
cost_recip = sum(M[c]["cost_central"] for c in ORDER if D[c]["rebate_fy26"] > 0)
A_net = sum(M[c]["net_central"] for c in TIER_A)
A_cases = sum(M[c]["cases_central"] for c in TIER_A)
A_pool = sum(M[c]["P"] for c in TIER_A)
A_cost = sum(M[c]["cost_central"] for c in TIER_A)
reb26_others = sum(D[c]["rebate_fy26"] for c in ORDER)
reb26_all = sum(D[c]["rebate_fy26"] for c in D)
reb_recipients = [c for c in D if D[c]["rebate_fy26"] > 0]
u = pl["intensity"]
P_IT = M["ITUK"]["P"]
it = md["itcheck"]
pstar50 = M["ITUK"]["p_star_phi50"]
blank_pct = R["comment_blank"] / R["lines"]
eps = md["blanket_eps"]
mpv_cv = [M[c]["margin_per_vehicle"] for c in ("ITUK", "UTI")]
mpv_iuk = M["IUK"]["margin_per_vehicle"]

TEXT = f"""# Don't Lose the Deal at the other distributors: would it earn its money?

**Written:** 8 October 2026
**Status:** internal study for the business owner. Not for forwarding. Shared wording would need a separate pass.
**Programme name (locked):** Don't Lose the Deal (DLOD), the name used throughout.
**Companions (not overwritten):** `DLOD_NETWORK_FEASIBILITY_2026-10-08.md`, `DLOD_NETWORK_ROLLOUT_2026-09-23.md`
**This file:** `C:\\Users\\jerom\\Desktop\\claude\\ISZE\\Isuzu Universe\\01_Strategy\\DLOD_OTHER_DISTRIBUTORS_STUDY_2026-10-08.md`
**Visual version with a calculator:** `C:\\Users\\jerom\\Desktop\\claude\\ISZE\\Isuzu Universe\\01_Strategy\\DLOD_OTHER_DISTRIBUTORS_STUDY_2026-10-08.html`

---

## The short answer

**No, not as a way to grow sales.** Don't Lose the Deal protects a repair job that is about to go to a cheaper independent quote. It does not create demand that was not there. At the 17 distributors in your book other than ITUK it is a small defensive tool, and only a few of them are big enough to be worth running it in.

The size of it, using ITUK's floor for every market (about 3% of a distributor's hard-part billing ends up on a supported case; this is generous to markets with less independent competition than the UK), with ISZE funding half of the discount and half of the supported jobs really being saves:

- It earns ISZE about **{er(tot_net)} of margin a year across all 17**, on a cost of about {er(tot_cost)} in credits.
- It loses money if fewer than about a third of the supported jobs really would have gone elsewhere: a loss of **{ek(-md['totals']['u3_p25'])}** a year at a quarter saved, a gain of **{ek(md['totals']['u3_p75'])}** at three quarters saved.
- The ceiling, with every supported job saved and ISZE paying nothing, is about **{er(tot_ceiling)} a year**. ISZE earns roughly {er(tot_billed*gm_w, 100000)} of margin on all parts at these 17 distributors, so the ceiling is about 1% of it.

**Customers who stay do not change that answer.** A truck kept in the network for another year is worth ISZE {e0(mpv_cv[1])} to {e0(mpv_cv[0])} of margin for a truck distributor, and €32 to €65 for the larger pickup distributors (UMI, IUK, Sweden, Norway). For trucks, three years of that is as much as ISZE earns on the saved job itself; for IUK and UMI it is a third to a half. That lowers the save rate ISZE needs from about {pc(pstar50)} to about 21% to 32%, but only if half of the customers you save would otherwise have left for good. Nothing on disk measures that.

Three other findings change how to approach this:

1. **Only five markets are big enough to run it.** UTI, IUK, Germany, Belgium and Portugal each carry roughly 45 or more supported cases a year at the central case. Together they are {pc(A_pool/tot_pool)} of the hard-part billing. The other twelve would see fewer than 35 cases a year each; nine of them fewer than 15. That is not a habit a dealer forms.
2. **ISZE already pays year-end credits to nine distributors: {er(reb26_all)} in FY2026** ({er(reb26_others)} excluding ITUK), and the order file labels them: {er(pl['rebate_class_totals']['kickback'])} is kickback (eight distributors), ITUK also gets €35,000 "scrap support" and the €30,000 DLOD, UMI gets €20,000 "sales support". The central-case DLOD cost in the eight other markets that receive credits would be {er(cost_recip)}, about {pc(cost_recip/reb26_others)} of what they already get. The question is therefore not "add a new credit" but "can a slice of the kickback be tied to evidenced cases?" The kickback terms are not in the data.
3. **Nobody can say how often hard parts lose to an independent quote outside the UK.** Competitor price evidence on hard parts covers between under 1% and 11% of the relevant billing and exists only for the UK and for Germany/Norway. For Israel, Portugal, Ireland, Belgium, Sweden and every smaller market there is none.

**Recommendation.** Do not put money behind it anywhere new yet. Run a no-money log of at-risk hard-part jobs (competitor price, outcome, order number) for two quarters in the five larger markets (tier A in section 12). The log is the cheapest thing in this study and the most valuable: its competitor prices would also test the list price on a hard-part base of {er(tot_pool,100000)}, where one percentage point of price is {er(tot_pool*0.01)} a year. If the log shows a save rate above the break-even for a market, fund a share of the discount there by making part of the kickback case-based, not by adding a new credit.

**One decision for you:** do you want the no-money log started in the five larger markets now, or held until ITUK's 2025 deal workbook is in so the ITUK numbers are cleaned first?

---

## 1. Scope, and how to read the labels

**In.** The 17 distributors in your book other than ITUK: IUK, UTI, UMI, Germany, Belgium, Portugal, Norway, Sweden, Ireland, Greece, Cyprus, Hungary, Finland, Malta, Romania, Denmark, Iceland. ITUK is the reference because it is the only place the programme runs.

**Out.** MIDI markets (France, Spain, Italy, Switzerland, Poland), Turkey, and the lubricants track. Ukraine, Armenia, Kazakhstan and Palestine are billed but have no service-parts model and no fleet base, so they cannot be sized. Service-schedule parts (PMS) are out because the register shows DLOD does not touch them; they belong to the SPA and promotion work. UTI and UMI are never blended; IUK and ITUK are never blended.

**Conditional.** Warranty is taken out of every base. Ireland's fleet base is unresolved (2,161 or 3,056 trucks), so its per-truck values are a range. Belgium's billing covers more than the Belgian fleet, so its per-truck values are overstated.

**Labels.** Every claim is one of: **Measured** (counted in a named file on 8 October 2026), **Inferred** (reasoned from measured inputs, reasoning shown), **Proposed** (a design or assumption, not yet decided), **Unknown** (left open). The central case uses Proposed assumptions and is labelled as such.

**Words used.**
- *Hard parts*: repair parts such as engine, fuel, exhaust cleaning (DPF), driveline, steering, electrical. Defined in the data as parts that are not in the service-schedule list (PMS), not in the Isuzu value line (BVP), and that ISZE bills the distributor at €100 or more a unit.
- *Supported case*: one part line on which the distributor gave a dealer a price below its normal dealer price (DN) because the job was about to go elsewhere.
- *Save rate*: the share of supported cases that really would have been lost without the offer.
- *Independent*: a non-Isuzu parts maker or seller (IAM in the files).

---

## 2. What ITUK actually shows

ITUK is the only market with a register. Duncan's 2026 workbook has 218 regional lines in three regions plus a fleet block of £14,879.

**It is a hard-part tool.** Of the 218 lines, none is a service-schedule part, and one is a value-line part (Measured, parts-catalog flags). Don't Lose the Deal and the PMS/SPA work therefore cover different parts. The value line does not offer a cheaper Isuzu alternative on these parts either, so at the counter DLOD is the only tool aimed at single jobs on these parts.

{t_families()}

*Measured: 217 of 218 lines matched to the Isuzu parts tree, GBP converted at 1.17.*

**Who funds it.** ITUK buys the part from ISZE, sells it to a dealer at its normal dealer price, and for a supported case sells below that. The register's cost column matches what ISZE actually invoiced ITUK for the same part numbers to within about 4% (median ratio {R['pur_vs_isze_ratio_median']:.2f}, middle half {R['pur_vs_isze_ratio_p25']:.2f} to {R['pur_vs_isze_ratio_p75']:.2f}, {R['matched_lines']} of 218 lines matched). So ITUK's cost is ISZE's price. *(Measured)*

- ITUK's normal margin on these lines is about **{pc(R.get('median_normal_margin_on_dn', R['normal_margin_on_dn']))}** of its dealer price (euro-weighted pool **{pc(R['normal_margin_on_dn'])}**). After the offer, retained margin is about **{pc(R.get('median_retained_margin_on_offer', 0.43))} median** (avg **{pc(R.get('avg_retained_margin_on_offer', 0.41))}**; euro-weighted pool **{pc(R['retained_margin_on_offer'])}** because large discounts weigh more). **{R.get('lines_below_cost', 0)}** lines are sold below cost.
- The support is **{pc(R['support_over_dn'],1)}** of the normal dealer price, and **{R['support_over_isze_bill']:.2f} euro for every euro ISZE billed** on those lines. The model below uses that second number.
- ISZE's billing on the 218 lines, at ISZE's own prices, is about {e0(R['isze_bill_eur'])}.

**How often it happens.** Dividing the ISZE billing on supported lines by ITUK's hard-part billing after warranty ({e0(P_IT)}) gives the share of hard-part billing that sits on a supported case. *(Measured, three windows, all incomplete)*

| Window | ISZE billing on supported lines | Share of ITUK hard-part billing |
|---|---:|---:|
| North region only, calendar 2025 | {e0(W['north_cy2025']['isze_bill_eur'])} | {pc(u['u_north_cy2025'],1)} |
| All dated lines, FY2026 window | {e0(W['fy26_visible']['isze_bill_eur'])} | {pc(u['u_fy26_visible'],1)} |
| South West + South East, Jan–Mar 2026, times four | {e0(4*W['q1_2026_sw_se']['isze_bill_eur'])} | {pc(u['u_q1_annualised'],1)} |

All three understate ITUK: the file has no fleet billing, no South West / South East / fleet for 2025, and nothing after 9 March 2026. So **3% is a floor for ITUK**. I use it as the central case for every other market, which is generous to any market with less independent competition than the UK.

**How it is spread.** Per 1,000 trucks in service, the FY2026 window shows {pl['rate']['vehicles_per_1000_uio_fy26_visible']:.1f} vehicles and {pl['rate']['cases_per_1000_uio_fy26_visible']:.1f} supported lines. *(Measured)*

- The top 10% of lines carry {pc(R['top10pct_lines_support_share'])} of the support. {R['lines_ge500_n']} lines with £500 or more of support carry £{R['lines_ge500_support_gbp']:,.0f}; {R['lines_lt150_n']} lines under £150 carry £{R['lines_lt150_support_gbp']:,.0f}, which is 64% of the cases and 20% of the money.
- {R['dealers']} dealers appear. The top 3 take {pc(R['top3_dealer_share'])} and the top 5 {pc(R['top5_dealer_share'])}.
- The same part numbers come back. 158 different part numbers cover the 218 lines; the 34 that appear twice or more are 94 lines and 55% of the support; the top 20 part numbers are 60% of it. *(Measured, register_lines_classified.csv)*
- The fleet block is one customer: J&R Foods is £12,126 of the £14,879 (82%). That is a fleet price agreement, not a counter case.
- {R['comment_blank']} of 218 lines ({pc(blank_pct)}) have no comment, one has a competitor price, four say "second hand", one "internet", two say the vehicle is still in warranty.

**What ITUK does not show.** Whether the supported jobs would have been lost. Every line carries an invoice number and revenue, so these are sales that happened; the jobs that were lost are not in the file. That is the denominator problem: the register can show how much was given, not how much was saved.

---

## 3. How the money works for ISZE

One supported case, in five lines. Everything in sections 6 to 8 is this arithmetic.

- ISZE billing on supported cases: **R** = touch share × hard-part billing.
- Support given at the distributor's price: **{R['support_over_isze_bill']:.2f} × R** (measured at ITUK).
- ISZE's credit: **ISZE share of the discount × support.** ITUK's visible window suggests ISZE pays at most about {pc(it['phi_if_visible_only'])}; the real share is lower because the file is incomplete.
- ISZE's gain: **save rate × ISZE margin × R.**
- Break-even save rate = **ISZE share × {R['support_over_isze_bill']:.2f} ÷ ISZE margin.**

| ISZE funds | Save rate needed (ISZE margin 47%) |
|---|---:|
| a quarter of the discount | {pc(M['ITUK']['p_star_phi25'])} |
| half | {pc(M['ITUK']['p_star_phi50'])} |
| all of it | {pc(M['ITUK']['p_star_phi100'])} |

Funding the whole discount needs about seven in ten supported jobs to be real saves. Funding half needs about one in three. That one design choice moves the answer more than any market difference.

**Check on ITUK's own €30,000.** ISZE's billing on supported lines in the visible window is {e0(it['bill_visible'])}. At a 47.7% margin, €30,000 pays back if {pc(it['p_star_if_visible_only'])} of those jobs would otherwise have been lost; if the true supported billing is double (likely, given the gaps above), **{pc(it['p_star_if_bill_doubles'])}**. So ITUK's credit is plausible, between a quarter and a half, and unproven. *(Inferred)*

**Can the distributor pay for it itself?** ITUK keeps about {pc(R.get('median_retained_margin_on_offer', 0.43))} median on the offer (pool {pc(R['retained_margin_on_offer'])}), so it can. Whether others can depends on their normal margin on the dealer price, which is not in any file. *(Unknown)*

{t_selffund()}

*Proposed: 20% as the margin a distributor needs to keep. Mechanics: support = 17.6% of the normal dealer price, as measured at ITUK.*

A distributor with a normal margin of 38% or more can fund an ITUK-sized discount itself. At 29% it needs ISZE for about 4 in 10 euros of the discount; at 23% for about 8 in 10. ISZE's money is only needed where the distributor's own margin is thin, and it should stop there.

---

## 4. Where it could apply, distributor by distributor

Hard-part billing is the part of FY2026 billing that DLOD could ever touch. Warranty is taken out using the share of each distributor's warranty claims that sit on hard parts (80% to 99%, measured on the claim lines). *(Measured; warranty claims file does not cover every month for every distributor, so the share is applied to the full-year warranty figure.)*

{t_pools()}

*Measured: sales_fact.parquet (FY2026 = 1 Apr 2025 to 31 Mar 2026, credit documents excluded), warranty from distributor_warranty_expense_fiscal.csv, margin from order_headers_from_Order_Detail.csv (orders with a cost), vehicles from gps_spu_by_distributor.csv (2025), dealers from the dealer-standards file.*

Three things stand out:

- **Hard parts are 35% to 66% of billing, about 60% in most of the larger markets.** The base tells the markets apart mainly by size.
- **UMI has almost no commercial hard-part base left.** Warranty is 54% of its billing, and nearly all warranty is hard parts, so only {e0(D['UMI']['profile_low'])} remains.
- **The ISZE margin is 43% to 49% everywhere** (network 46%), so it is not what separates the markets either.

---

## 5. Is there competition on hard parts in these markets?

This is the question the whole case rests on, and the answer is that the evidence is thin, mixed, and absent for most markets.

Three competitor price sources on disk reach hard parts (not service, not value line, €100+). I weighted each by what the distributor billed on that part number in FY2026.

{t_contest()}

*Measured. Negative gap means the independent price is lower. Listings are not workshop quotes and the brand tiers are not separated, so a low listing may be a budget brand.*

What it says:

- **In the UK the independent price is often lower.** In ITUK's covered hard-part billing, 41% to 82% sits on parts where independents are 10% or more cheaper. That fits a programme that exists there.
- **In Germany and Norway it is mixed and mostly the other way.** On the parts priced online, independents are 10% or more cheaper on only 31% of the billing and on average 22% *dearer* than ISZE. Injectors, EGR valves, water pumps and some turbochargers are dearer from independents. The exposed ones are exhaust cleaning (DPD/DPF assembly 39% cheaper), front drive shaft (60% cheaper) and the fuel supply pump (14% cheaper).
- **Coverage is under 1% to 11% of the relevant billing**, and for IUK just 0.4% (workshop prices) and 2% (trade-shop listings). Nothing here prices hard parts for Israel, Portugal, Ireland, Belgium, Sweden or the smaller markets. *(Unknown for all of them.)*
- **Service-parts capture cannot stand in for it.** Belgium's modelled service-parts gap (€2.0M) is larger than its entire modelled spend gap (€0.3M), and Germany's is also larger. The two models do not share a base, so I cannot subtract one from the other to isolate a hard-part leak. I will not present a figure that is not real.

Taken together: the one market where we can see the programme is also, on these thin samples, the market where independents most clearly undercut ISZE on hard parts. Outside it the case is unproven, and in Germany and Norway the available evidence argues against a broad problem.

---

## 6. Direct effects

Central case *(Proposed)*: 3% of hard-part billing on supported cases (ITUK's floor), ISZE funds half of the discount, half of supported jobs really would have been lost, no extra parts on the same job.

{t_direct()}

*Support per euro billed 0.32 (measured at ITUK). A "case" is one supported line at the average ticket: about €665 of ISZE billing at ITUK, scaled to each market's average hard-part price. 17 distributors total: {cases:.0f} cases a year, {e0(tot_cost)} cost, {e0(tot_gain)} gain, {e0(tot_net)} net.*

The picture across all 17, by how much of the hard-part billing is on supported cases and how many supported jobs are real saves:

{t_grid()}

*Net to ISZE a year, ISZE funding half the discount. Proposed grid.*

What this means:

- **Even at a 10% touch share (more than three times ITUK's floor) and three quarters saved, the 17 markets together earn about {ek(md['totals']['u10_p75'])} a year.** To reach €100,000 a year at half saved, the touch share would have to be about {pc(100000/(tot_net/0.03))}, four times ITUK's floor. Nothing suggests that.
- **A quarter saved loses money everywhere.** That is the risk if the offers are given to jobs that would have stayed anyway, which is what the empty comment fields and the missing competitor prices invite.
- **Volume decides practicality.** The A-markets would see roughly 45 to 144 cases a year each, 2 to 3 a dealer where the dealer count is known; Norway would see 0.7 a dealer. A tool nobody uses more than once a year per dealer does not become a habit. *(Inferred)*
- **Basket pull-through is not measured.** In the register, 42 of 119 vehicles have more than one supported line, so jobs are often several parts. Whether unsupported parts ride along is not in the file. Treat any "extra parts on the job" uplift as Unknown.

---

## 7. Indirect effects: customers who stay

This is where a retention case would have to be made. I tested four channels.

**7.1 A kept truck is worth money, but not a lot.** ISZE's margin on one truck's parts spend in a year, from FY2026 billing after warranty divided by vehicles in service and multiplied by the market's margin:

{t_indirect()}

*Proposed: three years, and that the saved customer would otherwise have been lost for good. Ireland's fleet base is unresolved; Belgium's is overstated.*

- A saved job brings ISZE margin of €209 to €317 straight away. For trucks (ITUK, UTI) three years of a kept truck adds €368 to €411, as much again. For the two large pickup markets, IUK and UMI, it adds €134 and €95, a third to a half. Smaller markets with fewer trucks and higher spend per truck sit in between.
- That moves the break-even save rate from about {pc(pstar50)} to {pc(M['ITUK']['p_star_delta25'])} (a quarter stay) or {pc(M['ITUK']['p_star_delta50'])} (half stay) at ITUK. For IUK the move is {pc(M['IUK']['p_star_delta0'])} to {pc(M['IUK']['p_star_delta50'])}.
- **Retention alone does not repay the programme.** At the central case ITUK would have to keep about 134 truck-years of average spend, which is 1.4 times the number of trucks the programme touches in a year. Retention is a top-up on the saved job, not a reason on its own.

**7.2 The register cannot show retention.** Of 119 vehicles, 13 appear on two or more dates, and 2 at more than one dealer. Over a 14-month window that is neither evidence of loyalty nor of its absence, and the file only records supported jobs. *(Unknown)*

**7.3 Outside context, not used in any number.** Studies of passenger-car owners in the United States, not trucks, point the same way as common sense: J.D. Power's 2009 study found dealers with superior service kept more than 80% of owners' service spending against under 60% for weaker ones, and owners who rated dealer service unacceptable spent eight times as much at non-dealer shops. Cox Automotive data reported in November 2025 puts the share of owners of 0 to 2 year old cars who return to the selling dealer at 54%, down from 72% two years earlier. I found no controlled study showing that a price-match programme raises retention; the claims for them come from the vendors that sell them. I found no usable truck-specific figure at all. Sources: [WardsAuto on J.D. Power 2009](https://wardsauto.com/finance-insurance/after-the-warranty-ends), [Daily Dealer on Cox Automotive data, 25 Nov 2025](https://news.dealershipguy.com/p/automaker-price-markups-are-driving-service-customers-to-independents-warns-dave-rogers-2025-11-25).

**7.4 Dealer relationship.** In ITUK the programme reaches {R['dealers']} dealers but a third of the support goes to three of them. Whether it makes dealers more loyal, or merely makes three dealers expect a discount, is not measurable from this file. *(Unknown)*

**7.5 The competitor price log has its own value.** Today competitor price is filled on 1 of 218 lines. A register that records the independent price for every at-risk hard-part job is the only systematic hard-part price evidence ISZE would have outside the UK. The hard-part billing at the 17 distributors is {er(tot_pool,100000)} and one percentage point of price on it is {er(tot_pool*0.01)} a year, more than the central-case programme earns. That is arithmetic, not a forecast, but it explains why the log is worth more than the credit.

**7.6 Negative indirect effects.**
- *Price creep:* once dealers learn an offer is possible, requests rise. Every extra percent of hard-part billing on supported cases costs ISZE the same credit and earns nothing if the jobs were not at risk.
- *Double payment:* the open SPAs and the existing rebates may already cover the same parts.
- *Reference price:* a discount that becomes normal is a price cut.
- *Accounting:* credit documents are excluded from GPS billing under the audit rules, so the credit will not show in GPS %. It shows in margin. *(Inferred from audit rules)*

---

## 8. The money ISZE already pays

Billing shows year-end credit documents ("Rebate Material") to nine distributors, and the order file carries a label on most of them. In FY2026 the labels read: {e0(pl['rebate_class_totals']['kickback'])} kickback, {e0(pl['rebate_class_totals']['scrap support'])} "scrap support" and {e0(pl['rebate_class_totals']['DLOD'])} DLOD (all three to ITUK), {e0(pl['rebate_class_totals']['sales support'])} "sales support" (UMI), {e0(pl['rebate_class_totals']['correction'])} for a correction (Sweden), and {e0(pl['rebate_class_totals']['no label in order file'])} with no label (two Norway credits of €15,568 dated 30 March, the day before Norway's labelled kickback). *(Measured)*

{t_rebate()}

*Measured: sales_fact.parquet (credit documents, SaTy CR, with "Rebate" in the part number; sold-to 2194 counted as ITUK) matched on sold-to, date and euro to the Purchase Order Number in order_headers_from_Order_Detail.csv. Fiscal years as in the rest of the study.*

- **It is a kickback system.** In FY2026 eight distributors received kickback credits (ITUK, IUK, UTI, Germany, Belgium, Portugal, Sweden, Norway); UMI received "sales support". The set moves from year to year: in FY2025 Ireland and Greece were in and Portugal and Sweden were out. The GPS files also contain a kickback proposal for FY27 that is still being built.
- **ITUK's package.** ITUK received {e0(D['ITUK']['rebate_fy26'])} in FY2026 and {e0(D['ITUK']['rebate_fy25'])} in FY2025: a kickback ({e0(77000)} in FY2026, €80,000 in FY2025), "scrap support" (€35,000 both years) and DLOD (€30,000 both years). DLOD is one of three lumps, not a freestanding line.
- Almost all are paid in the last eight days of March, in round amounts.
- The central-case DLOD cost for each market is 6% to 24% of what that market already receives.

What it means: **the sensible way to add DLOD is not a new credit but a case-based part of the kickback.** A kickback pays a distributor for billing more; a saved hard-part job raises billing, so a distributor with both would be paid twice for the same job. The kickback's formula and conditions are not in the data. *(Unknown)* The FY27 kickback proposal is being built now, which is the natural place to attach an evidence-based DLOD component.

---

## 9. Other ways to reach the same jobs

| Tool | Costs ISZE | Works on | Weak spot | Evidence here |
|---|---|---|---|---|
| **Don't Lose the Deal, case by case** | Only the share of the discount ISZE funds, only on supported cases | Hard parts with a live competing quote | Needs proof the job was at risk; admin; creep | ITUK register; no save rate |
| **Standing price corridor on the repeat part numbers** *(new)* | Same discount, set once | The 20 to 30 part numbers that repeat | Less flexible; dealers learn the price | In ITUK 20 part numbers are 60% of support |
| **Permanent list-price cut on hard parts** | The cut on every unit sold | All hard parts | To pay for itself a 5% cut needs volume to rise by about 12%, an elasticity of {eps['5']:.1f} | Elasticity files disagree ({'-0.3 vs -2'}) and both carry low-power warnings; neither supports {eps['5']:.1f} |
| **Special price agreement (SPA)** | A defined discount on a defined basket | Fleets, baskets, known customers | Not for single at-risk jobs | In ITUK the fleet block (82% one customer) behaves like one |
| **Isuzu value line (BVP)** | Lower price, lower margin on the swap | Service-type parts | None exists for these hard parts | 1 of 218 supported lines is in the value line |
| **Year-end kickback as today** | {e0(pl['rebate_class_totals']['kickback'])} kickback in FY2026 (of {e0(reb26_all)} year-end credits) | Total billing, whatever the terms say | Not tied to jobs saved; terms not in the data | Section 8 |
| **Do nothing** | Nothing | | Lose the jobs that really walk | Unmeasured outside the UK |

**On elasticity.** One file puts the ITUK price response of hard-part families at −0.3 to −0.4 (a cross-section of price against volume, flagged as a proxy); another puts engine, transmission and fuel parts at about −2 (a YoY billing regression flagged low-power, with mix and demand shocks not controlled). They disagree by a factor of five and neither is a reliable estimate. I do not use either. A blanket cut breaks even only above an elasticity of about {eps['5']:.1f}; nothing in the files shows a hard-part elasticity that high, which is the case for a targeted tool rather than a cut. *(Inferred)*

---

## 10. Risks and how to contain them

| Risk | Evidence | Control |
|---|---|---|
| Support given to jobs that would have stayed | {pc(blank_pct)} of ITUK lines have no comment; 1 of 218 has a competitor price; two are vehicles still in warranty | Competitor price or a quote screenshot above a floor; no cases on vehicles in warranty |
| Concentration | Top 3 of {R['dealers']} dealers take {pc(R['top3_dealer_share'])} | Cap per dealer per year |
| Admin swamps the value | 64% of ITUK lines are under £150 of support and add 20% of the money | Floor of about £150 / €175 of support per case |
| Double payment | A kickback already rewards a distributor for billing more, and a saved job raises billing; open SPAs may cover the same parts | Make DLOD a case-based part of the kickback, not an extra; exclusion list of parts under an open SPA |
| Funding the wrong thing | ITUK keeps ~{pc(R.get('median_retained_margin_on_offer', 0.43))} median after the offer and might fund it anyway | ISZE funds only where the distributor's own margin is thin; withhold the credit where it would be offered anyway |
| Competition law | Supplier funding a discount that depends on what the dealer charges the customer can look like resale price control | Credit based on ISZE's price to the distributor, not on the dealer's price to the customer; local counsel *(Unknown per market)* |
| Year-end timing | The rebates are paid in the last ten days of March | Monthly claim pack so credits follow cases |
| Currency | UK cases in pounds, credits in euros | Envelope in euros, distributor carries local currency |

---

## 11. If money flows: design rules

*(Proposed, drawn from the ITUK pattern.)*

1. **No-money log first**, with these fields: date, dealer, vehicle number, part number and description, normal dealer price, offer, competitor price or quote evidence, and the outcome (won, lost, unknown), plus the distributor's invoice number. Lost jobs are logged too; that is what the ITUK file lacks.
2. **Floor.** No case under about £150 / €175 of support.
3. **Cap** per dealer per year.
4. **ISZE funds a share, not all.** The share is the lower of a half or what is needed to leave the distributor 20% margin.
5. **Pre-agree a price corridor** on the part numbers that repeat (in ITUK, 20 part numbers carry 60% of the support). Case-by-case approval is for the rest.
6. **Exclusions:** service-schedule parts, value-line parts, parts under an open SPA, vehicles in warranty.
7. **Monthly claim pack** that lists cases and reconciles to the credit. No year-end lump.
8. **Test the save rate, do not assume it.** Of the cases that meet the rule, hold back one in three at the normal price for two quarters and compare win rates; that is the only way to get a save rate that is not the dealer's opinion. This costs the margin on the held-back jobs that are lost. *(Proposed; you may prefer the log alone.)*

---

## 12. Verdict by distributor, and the next step

Tiers are set by operating volume at the central case: A is 40 or more supported cases a year, B is 25 to 40, C is under 25. *(Proposed rule; the cut-offs are judgment.)*

{t_verdict()}

- **Tier A** (5 markets, {pc(A_pool/tot_pool)} of the hard-part billing, {A_cases:.0f} cases a year, {e0(A_net)} net and {e0(A_cost)} cost at the central case): start the no-money log. Decide on money after two quarters using the rule below.
- **Tier B** (3 markets): not now. They add {e0(sum(M[c]['net_central'] for c in TIER_B))} at the central case on 89 cases a year in total.
- **Tier C** (9 markets): no case-by-case programme. If an independent price problem turns up on a specific part, treat it as a price-list item.

**Decision rule after the log.** In a market, with at least about 100 logged cases with outcomes, fund a share of the discount if the lower end of the observed save rate is above the break-even in section 3 or 7 for the share ISZE would pay. If it is not, keep the log and stop the credit. 100 cases with a true 50% save rate gives an observed rate within about ±10 points, enough to tell 50% from 34%. At the central case the five A-markets produce about {A_cases:.0f} cases a year, so six months should give about 200. *(Inferred)*

**Sequence.**
1. Get Duncan's 2025 workbook and any cases after 9 March 2026 so the ITUK numbers cover a clean year.
2. Get the kickback terms (what triggers them, who gets them in FY27) and see whether an evidence-based DLOD part can sit inside the FY27 kickback proposal instead of a new credit.
3. Start the log in the A-markets. UTI first: a copy of ITUK's deal workbook is already in its project folder.
4. Re-run this study with the logged save rates.

---

## 13. What would change this verdict

- A logged save rate above the break-even in a B or C market, or evidence of heavy independent undercutting on hard parts in Israel, Portugal or Ireland.
- A measured touch share well above 3% outside the UK. At a 10% touch share and 75% saved the 17 markets earn about {ek(md['totals']['u10_p75'])}.
- Learning that the kickback terms are contractual and cannot be reshaped for FY27, which makes DLOD a true addition and raises its cost.
- Distributor margins in the other markets that are thin enough that ISZE must fund most of the discount, which pushes the break-even save rate to 50% to 75%.
- A measured retention effect: if half of saved customers stay three years, the break-even drops to about 21% to 32%.

**Unknown today:** the save rate in any market; whether ITUK would run DLOD without the credit; the kickback formula and whether it can change for FY27; distributor margins on hard parts outside the UK; competitor prices on hard parts outside the UK, Germany and Norway; retention effect; basket pull-through; Duncan's 2025 and post-March 2026 cases; local competition-law advice.

---

## 14. Corrections to the 8 October feasibility study

Found while building this one. The feasibility study is not changed.

1. **The £54,922 is not one year.** North covers Nov 2024 to Dec 2025; South West and South East only Jan to Mar 2026; the fleet block Jan to Feb 2026. It cannot be compared with a year of ISZE credit.
2. **The fleet note is wrong.** The sheet's raw column sums to £29,758, exactly double £14,878.95, because the sheet's own total row sits in the column. The Overall figure is complete.
3. **ITUK never sells below cost** and keeps about **41–43% median** after the offer (~47% normal before). "Support" is margin given up, not a loss.
4. **The 0.5% base included warranty.** IUK billed €5.95M of which €1.34M is warranty; UMI €3.0M of which €1.63M. A 0.5% rule on billed overstates both. This study removes warranty.
5. **"€30,000 per year"** is one of three year-end credits to ITUK in FY2026 (€142,000 in total: kickback incentive €77,000, scrap support €35,000, DLOD €30,000), and the DLOD credit is a lump, not tied to cases.
6. **The billed figures differ.** The distributor dimension file shows ITUK FY2026 at €6,957,525; excluding €146,656 of credit documents it is €6,810,869, which matches the billed-versus-sales-to-dealer file. This study uses the second.

---

## 15. Method, sources, data problems

**Method.** `01_data/91_build/dlod_other_dbs_20261008/_analysis.py` builds `payload.json` (register, billing, warranty, margin, rebates, contest evidence). `_model.py` builds `model.json` (scenarios). `_assemble_study.py` writes this file; every table is computed from those two files. Hard-part billing = FY2026 billing (1 Apr 2025 to 31 Mar 2026, excluding credit documents) on part numbers that are not in the PMS registry, not in the value-line catalogue, and whose average price in that market is €100 or more; warranty removed by the share of claims on such parts. ISZE margin = gross margin on orders with a recorded cost, FY2026. GBP to EUR 1.17 for conversion only. Break-even: save rate = ISZE share × support per euro billed ÷ margin.

**Sources** (all under `C:\\Users\\jerom\\Desktop\\claude\\ISZE\\`):
- `01_data\\90_INBOX\\ituk_std_mail_hunt_20260903\\pulled_attachments\\2026-03-10_1026_Duncan_DLAD - All regions 2026 Overall.xlsx`
- `01_data\\00_derived\\sales_fact.parquet`, `distributor_dimension.csv`, `distributor_warranty_expense_fiscal.csv`, `warranty_raw_grain.csv`, `order_headers_from_Order_Detail.csv`, `gps_spu_by_distributor.csv`, `parts_catalog_dimension.parquet`, `aim_pn_classification_20260920.csv`, `eucon_price_gap.csv`, `eucon_uk_survey_2023_price_gap.csv`, `iam_ks_price_gap.csv`, `ids_dealer_network_cleaned_2026-09-20.csv`, `wallet_waterfall.csv`, `pms_opportunity_matrix.csv`, `price_elasticity_db_dlr_network.csv`, `price_volume_elasticity.csv`, `billed_vs_std_warranty_fy2026.csv`
- `01_data\\ISZE_Leakage_Review_2025_INTERNAL.md`, `01_data\\02_GPS\\HANDOVER_GPS_Extended_Target_FY27.md`
- `01_data\\90_INBOX\\APL_UTI_P700\\2026-07-23_UTI_P700_DLAD_-_All_regions_2026_Overall_005_.xlsx` (identical to the ITUK workbook)

**Data problems met.**
- Greece's billing label is "RSA", the same name the warranty file uses for Norway. I used distributor codes, not the label, so Greece and Norway are not merged.
- Ireland's fleet is 2,161 in the target model and 3,056 in the spend file; Ireland's billing is larger than its modelled target, which means the fleet base is wrong. Per-truck values for Ireland are a range.
- Belgium's billing covers Belgium, the Netherlands, Luxembourg and Poland; the fleet counts Belgium only.
- The modelled service-parts gap is larger than the total modelled spend gap in Belgium and Germany, so the two cannot be subtracted.
- Cyprus and Malta have a single dealer entry each in the standards file; I treat that as no dealer list.
- The South West sheet carries month names without a year; read as January to March 2026.
- The warranty claims file does not cover every month for every distributor, so I applied the share of claims that sit on hard parts to the full-year warranty figure.
- The sales-to-dealer files cover different periods (see `billed_vs_std_warranty_fy2026.csv`), so no cross-market sales-to-dealer comparison is used here.

**External sources** (context only, no number depends on them):
- [WardsAuto, "After the Warranty Ends", 1 Apr 2009, on the J.D. Power 2009 Customer Service Index study](https://wardsauto.com/finance-insurance/after-the-warranty-ends)
- [Daily Dealer, 25 Nov 2025, Cox Automotive retention figures](https://news.dealershipguy.com/p/automaker-price-markups-are-driving-service-customers-to-independents-warns-dave-rogers-2025-11-25)

---

## Revision record

| Date | Change |
|---|---|
| 2026-10-08 | First version. New study on the 17 other distributors. Does not overwrite the 8 Oct feasibility study or the 23 Sep rollout note. |
"""

OUT.write_text(TEXT, encoding="utf-8")
print("written", OUT, len(TEXT))
