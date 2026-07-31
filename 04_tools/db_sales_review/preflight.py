"""Pre-flight for a distributor sales review.

    python preflight.py --db ISD

Resolves every field in the DB's profile against the live files and prints one
compact report: payer match, window completeness against canonical FY billing,
credit memos, GPS, PMS, UIO, FY27 target, IDS, warranty, and the DB's own watch
list. Run this before building anything — it is the whole of the discovery work
that used to be done by hand, in one call.

Exit code 1 if a blocking problem is found.
"""
from __future__ import annotations

import argparse
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import pandas as pd

import common as C


def h(title):
    print()
    print("=" * 84)
    print(title)
    print("-" * 84)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, help=f"one of: {', '.join(C.list_profiles())}")
    args = ap.parse_args()

    p = C.load_profile(args.db)
    d = p["defaults"]
    problems, warnings = [], []

    print("=" * 84)
    print(f"PRE-FLIGHT — {p['key']}  ·  {p['name']}  ·  {p['country']}  [{p['segment']}]")
    print("=" * 84)

    # ---------------------------------------------------------------- billing --
    h("1. Billing source — payer match and window completeness")
    sales = C.load_sales(p)
    L25, L26 = d["window_label_prior"], d["window_label_current"]
    gross = sales[~sales["is_credit"]]
    g25 = gross.loc[gross["period"] == L25, "net_eur"].sum()
    g26 = gross.loc[gross["period"] == L26, "net_eur"].sum()
    n25 = sales.loc[sales["period"] == L25, "net_eur"].sum()
    n26 = sales.loc[sales["period"] == L26, "net_eur"].sum()
    print(f"  payer                 {p['payer']}")
    print(f"  lines                 {len(sales):,}")
    print(f"  {L25:<21} gross EUR {g25:>14,.2f}   net EUR {n25:>14,.2f}")
    print(f"  {L26:<21} gross EUR {g26:>14,.2f}   net EUR {n26:>14,.2f}")
    if g25:
        print(f"  movement              gross {(g26/g25-1)*100:+.1f}%    net {(n26/n25-1)*100:+.1f}%")
    if g25 == 0 or g26 == 0:
        problems.append("One of the two windows has zero gross billing — wrong payer string?")

    gm = C.load_gps_master(p)
    derived_fy26 = C.fy_billing_derived(p)
    canon = gm["bill_FY2026"]
    drift = derived_fy26 / canon - 1 if canon else None
    print(f"\n  FY2026 completeness check (this is what proves the CY files are whole):")
    print(f"    derived Apr'25-Mar'26  EUR {derived_fy26:>14,.2f}")
    print(f"    canonical (gps_master) EUR {canon:>14,.2f}")
    print(f"    drift                  {drift*100:+.1f}%  (expect 0 to +5%: GPS exclusions)")
    if drift is None or abs(drift) > 0.10:
        problems.append(
            f"Derived FY2026 is {drift*100:+.1f}% off canonical — the source window is not "
            "complete for this DB. Do NOT cut PN detail until this is understood.")

    # ---------------------------------------------------------------- credits --
    h("2. Credit memos (G2 / CR) — signed negative by the loader")
    cr = sales[sales["is_credit"]]
    if cr.empty:
        print("  none in either window.")
    else:
        for per, grp in cr.groupby("period"):
            print(f"  {per:<12} {len(grp):>3} lines   EUR {grp['net_eur'].sum():>12,.2f}")
        big = cr[cr["net_eur"].abs() > 5000]
        for _, r in big.iterrows():
            print(f"     {r['period']}  {str(r['Material'])[:14]:<14} "
                  f"{str(r['sap_desc'])[:32]:<32} EUR {r['net_eur']:>11,.2f}")
        warnings.append(f"{len(cr)} credit line(s) present — excluded from the mover lists.")

    # -------------------------------------------------------------------- GPS --
    h("3. GPS")
    print(f"  gps_master row '{p['gps_key']}'  (flat rate EUR {gm['rate']:,.2f}/unit)")
    for fy in ("FY2024", "FY2025", "FY2026"):
        v = gm[f"gps_pct_{fy}"]
        print(f"    {fy}  {v*100:6.1f}%" if v is not None else f"    {fy}     n/a")

    fy = C.load_fy27(p)
    print(f"\n  FY27 Extended Target tab '{fy['tab']}'  (ISZE-to-DB internal reference)")
    for label, key in (("max spend", "max_spend"), ("actual / BP", "actual"),
                       ("GPS", "gps"), ("stretch EUR", "stretch_eur"),
                       ("ext. target", "ext_target"), ("GPS after stretch", "gps_new")):
        row = fy.get(key)
        if not row:
            continue
        def f(v):
            if v is None:
                return "        —"
            return f"{v*100:8.1f}%" if key in ("gps", "gps_new") else f"{v:>13,.0f}"
        print(f"    {label:<19} FY25 {f(row['fy25'])}   FY26 {f(row['fy26'])}   FY27 {f(row['fy27'])}")
    gps26 = (fy.get("gps") or {}).get("fy26")
    gps_new = (fy.get("gps_new") or {}).get("fy27")
    for v, lab in ((gps26, "FY2026"), (gps_new, "FY2027 after stretch")):
        if v and v > 1.0:
            warnings.append(
                f"GPS {lab} is {v*100:.0f}% — above theoretical max spend. "
                "Meeting slides use Sales-to-Dealer amounts, not a GPS %.")

    s2d = fy["s2d_target"]
    print("\n  Sales-to-Dealer target — Dashboard P:U method (meeting headline)")
    print(f"    Dashboard key          {s2d['dashboard_key']}")
    print(f"    S2D FY2026             EUR {s2d['fy26']:>13,.0f}"
          f"  ({'IMPUTED: FY26 billing / 0.65' if s2d['s2d_imputed'] else 'reported KPI'})")
    print(f"    UIO growth             {s2d['uio_growth']:>+13.1%}"
          f"  ({'deck-side corrected' if s2d['growth_overridden'] else 'Dashboard R'})")
    print(f"    price / additional     {s2d['price']:>13.1%} / {s2d['additional']:.1%}")
    print(f"    S2D FY2027 target      EUR {s2d['fy27']:>13,.0f}")

    print("\n  UIO by segment, from the FY27 tab:")
    for seg, vals in fy["segments"].items():
        print(f"    {seg:<9} FY25 {vals['fy25'] or 0:>8,.0f}   FY26 {vals['fy26'] or 0:>8,.0f}   "
              f"FY27 {vals['fy27'] or 0:>8,.0f}")

    # -------------------------------------------------------------------- UIO --
    h("4. Fleet (UIO _CURRENT)")
    uio = C.load_uio(p)
    yrs = [y for y in sorted(uio["total"]) if 2019 <= y <= 2026]
    print("    year      " + "".join(f"{y:>9}" for y in yrs))
    for seg in [s for s in uio if s != "total"] + ["total"]:
        vals = uio[seg]
        print(f"    {seg:<9} " + "".join(f"{vals.get(y, 0):>9,}" for y in yrs))

    # -------------------------------------------------------------------- PMS --
    h("5. PMS capture vs the rest of the network")
    year, pms = C.load_pms(p)
    peers = C.pms_vs_network(p, year=year)
    print(f"  year {year}, code '{p['pms_code']}'")
    print(f"    {'category':<22}{'this DB':>10}{'network':>10}{'best':>10}")
    for cat, v in peers.items():
        print(f"    {cat:<22}{v['db']:>9.1f}%{v['network']:>9.1f}%{v['best']:>9.1f}%")
    worst = sorted(peers.items(), key=lambda kv: kv[1]["db"] - kv[1]["network"])[:2]
    if worst:
        print("  furthest below network: " + ", ".join(
            f"{c} ({v['db']:.1f}% vs {v['network']:.1f}%)" for c, v in worst))

    # -------------------------------------------------------------------- IDS --
    h("6. IDS 2026")
    ids = C.load_ids(p)
    if ids is None:
        print(f"  no IDS 2026 data for this DB (ids_code = {p.get('ids_code')!r}) — skip that slide.")
    else:
        mine, net_avg, db_avg = ids
        print(f"  {len(mine)} dealers   DB avg {db_avg:.1f}%   network avg {net_avg:.1f}%")
        print(f"  best  {mine.iloc[0]['Dealer']} ({mine.iloc[0]['Points achieved %']:.1f}%, "
              f"global #{int(mine.iloc[0]['Global rank'])})")
        print(f"  worst {mine.iloc[-1]['Dealer']} ({mine.iloc[-1]['Points achieved %']:.1f}%, "
              f"global #{int(mine.iloc[-1]['Global rank'])})")

    # --------------------------------------------------------------- warranty --
    h("7. Warranty & incentive")
    w = p.get("warranty_cy2025_claim")
    if w:
        print(f"  CY2025 warranty parts   EUR {w:>12,.0f} (claim price basis)")
        print(f"    ISZE-net equivalent   EUR {w*0.74:>12,.0f} (x0.74)")
        print(f"    note: {p.get('warranty_note', '—')}")
    inc = p.get("incentive_fy27")
    print(f"  FY2027 incentive budget EUR {inc:>12,.0f}" if inc
          else "  FY2027 incentive budget none on record")
    if inc:
        warnings.append("Incentive is BUDGETED, not confirmed approved. Keep the amount off "
                        "the customer slide unless Jerome says otherwise.")

    # -------------------------------------------------------------------- PBI --
    h("8. Official quarter (Power BI)")
    pbi = p.get("pbi")
    pbi_complete = bool(
        pbi
        and pbi.get("sales")
        and pbi.get("budget")
        and pbi.get("prev_year")
        and all(v is not None for k in ("sales", "budget", "prev_year")
                for v in pbi.get(k, []))
        and len(pbi["sales"]) == len(pbi["months"])
        == len(pbi["budget"]) == len(pbi["prev_year"])
    )
    if not pbi:
        # Soft block: deck still builds, but the official Q1 FY2027 sales-review
        # slide is omitted (never invent it from the SAP extract).
        warnings.append(
            "No Power BI quarter in the profile — sales-review slide SKIPPED. "
            "Paste the Power BI cut into db_profiles.yaml before presenting.")
        print("  MISSING — sales-review slide will be skipped (not invented from SAP).")
    elif not pbi_complete:
        warnings.append(
            "Power BI quarter is partial (budget and/or prior year missing) — "
            "sales-review slide SKIPPED until the full cut is supplied.")
        print(f"  PARTIAL — {pbi['quarter']} sales EUR {sum(pbi.get('sales') or []):,.0f}; "
              "budget/prior-year cut incomplete; sales-review slide skipped.")
    else:
        tot_s, tot_b = sum(pbi["sales"]), sum(pbi["budget"])
        tot_p = sum(pbi["prev_year"])
        print(f"  {pbi['quarter']}   sales EUR {tot_s:,.0f}   budget EUR {tot_b:,.0f} "
              f"({tot_s/tot_b-1:+.1%})   prior year EUR {tot_p:,.0f} ({tot_s/tot_p-1:+.1%})")
        for i, m in enumerate(pbi["months"]):
            print(f"    {m}  sales {pbi['sales'][i]:>10,.0f}  budget {pbi['budget'][i]:>10,.0f} "
                  f"({pbi['sales'][i]/pbi['budget'][i]-1:+7.1%})  "
                  f"prior {pbi['prev_year'][i]:>10,.0f} ({pbi['sales'][i]/pbi['prev_year'][i]-1:+7.1%})")
        print(f"  source: {pbi['source']}")

    # ------------------------------------------------------------------ watch --
    h("9. Watch list for this DB — read before presenting")
    for w_ in p.get("watch", []) or ["(none recorded)"]:
        print(f"  ·  {w_}")

    # --------------------------------------------------------------- verdict --
    h("VERDICT")
    for w_ in warnings:
        print(f"  NOTE     {w_}")
    for pr in problems:
        print(f"  PROBLEM  {pr}")
    if not problems:
        print("  Clear to build.  ->  python build_parts_analysis.py --db "
              f"{p['key']}   then   python build_deck.py --db {p['key']}")
    print()
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
