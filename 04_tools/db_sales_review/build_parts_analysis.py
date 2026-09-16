"""Parts-analysis workbook for one distributor.

    python build_parts_analysis.py --db ISD

Writes ISZE_<DB>_Parts_Analysis_<window>.xlsx plus a _<db>_summary.json that
build_deck.py consumes. Run preflight.py first.

Method (identical for every DB — see ..\\ppt_template_v2\\DB_SALES_REVIEW_BLUEPRINT.md):
  · window from db_profiles.yaml defaults; movers cut on GROSS parts lines only
  · credit memos signed negative and excluded from the mover lists
  · commercial / ex-warranty: PNs on warranty_raw_grain claims (plus campaign
    text heuristic) are stripped from category / PN / ITC movers — ERP has no
    warranty document type, so claim-matched PN exclusion is the line-level cut
  · parts rolled up to ITC family (Newest P/N) as well as raw PN
  · join on 'Material'; 'Material Number' holds the description, not a PN
  · Mode A movers carry largest-EUR PN drivers (increase and decrease);
    optional vehicle_model from BVP/PMS application tables when present
"""
from __future__ import annotations

import argparse
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

import common as C

TOP_N = 100
THIN = Side(style="thin", color="B0B0B0")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
HEADER_FILL = PatternFill("solid", fgColor="C00000")
HEADER_FONT = Font(bold=True, color="FFFFFF", name="Calibri", size=11)
TITLE_FONT = Font(bold=True, name="Calibri", size=12, color="C00000")
NUM_FMT, QTY_FMT, PCT_FMT = "#,##0.00", "#,##0.00", "0.0%"


# ----------------------------------------------------------------- xlsx utils --
def style_header(ws, row, ncol):
    for c in range(1, ncol + 1):
        cell = ws.cell(row, c)
        cell.fill, cell.font, cell.border = HEADER_FILL, HEADER_FONT, BORDER
        cell.alignment = Alignment(wrap_text=True, horizontal="center", vertical="center")


def autosize(ws, min_w=10, max_w=42):
    wide = {"description", "member pns"}
    headers = {}
    for r in (1, 2):
        for cell in ws[r]:
            if cell.value and cell.column not in headers:
                headers[cell.column] = str(cell.value)
    for col in ws.columns:
        hdr = headers.get(col[0].column, "").lower()
        length = 28 if hdr in wide else 0
        for cell in col[:80]:
            if cell.value is not None:
                length = max(length, min(len(str(cell.value)), 55 if hdr in wide else max_w))
        ws.column_dimensions[get_column_letter(col[0].column)].width = max(min_w, length + 2)


def write_df(ws, df, start_row=1, currency=None, qty=None, pct=None):
    currency, qty, pct = set(currency or []), set(qty or []), set(pct or [])
    headers = list(df.columns)
    for c, hh in enumerate(headers, 1):
        ws.cell(start_row, c, hh)
    style_header(ws, start_row, len(headers))
    for r_i, row in enumerate(df.itertuples(index=False), start_row + 1):
        for c_i, val in enumerate(row, 1):
            cell = ws.cell(r_i, c_i, None if (isinstance(val, float) and np.isnan(val)) else val)
            cell.border = BORDER
            hh = headers[c_i - 1]
            if isinstance(val, (int, float)):
                if hh in currency:
                    cell.number_format = NUM_FMT
                elif hh in qty:
                    cell.number_format = QTY_FMT
                elif hh in pct:
                    cell.number_format = PCT_FMT
    ws.auto_filter.ref = f"A{start_row}:{get_column_letter(len(headers))}{start_row + len(df)}"
    ws.freeze_panes = f"A{start_row + 1}"
    autosize(ws)


# ------------------------------------------------------------------ analytics --
def aggregate_pn(gross, catalog, desc_by_newest, itc, L25, L26):
    g = (gross.groupby(["Material", "period"], dropna=False)
         .agg(qty=("qty", "sum"), net_eur=("net_eur", "sum")).reset_index())
    wide = g.pivot_table(index="Material", columns="period",
                         values=["qty", "net_eur"], aggfunc="sum", fill_value=0)
    wide.columns = [f"{a}|{b}" for a, b in wide.columns]
    wide = wide.reset_index()
    for col in [f"qty|{L25}", f"qty|{L26}", f"net_eur|{L25}", f"net_eur|{L26}"]:
        if col not in wide.columns:
            wide[col] = 0.0

    wide["mapped"] = wide["Material"].isin(itc)
    wide["Newest_PN"] = wide["Material"].map(lambda m: itc.get(m, m) if m else m)
    wide["ITC_family"] = wide["Newest_PN"]
    wide["Description"] = wide["Newest_PN"].map(lambda p: desc_by_newest.get(p, "") if p else "")
    miss = wide["Description"].fillna("") == ""
    wide.loc[miss, "Description"] = wide.loc[miss, "Material"].map(
        lambda p: desc_by_newest.get(p, "") if p else "")

    sap = (gross.dropna(subset=["Material"]).assign(_a=lambda d: d["net_eur"].abs())
           .sort_values("_a", ascending=False).drop_duplicates("Material")
           .set_index("Material")["sap_desc"].to_dict())
    miss = wide["Description"].fillna("") == ""
    wide.loc[miss, "Description"] = wide.loc[miss, "Material"].map(lambda p: sap.get(p, ""))
    wide["Description"] = wide["Description"].replace({"nan": ""}).fillna("")

    wide = (wide.merge(catalog, left_on="Material", right_on="part_number", how="left")
            .drop(columns=["part_number"], errors="ignore")
            .rename(columns={"pr00_group": "Category", "pms_category": "PMS Category"}))
    wide.loc[wide["Category"].isna() | (wide["Category"] == ""), "Category"] = "UNCLASSIFIED"
    # Shell lubricants = 5500* (UMI/UTI convention) — do not leave in UNCLASSIFIED.
    shell_mask = wide["Material"].astype(str).str.startswith("5500")
    wide.loc[shell_mask, "Category"] = "Shell lubricants"
    wide["Delta_EUR"] = wide[f"net_eur|{L26}"] - wide[f"net_eur|{L25}"]
    wide["Delta_Qty"] = wide[f"qty|{L26}"] - wide[f"qty|{L25}"]
    wide["Delta_Pct"] = np.where(wide[f"net_eur|{L25}"] != 0,
                                 wide["Delta_EUR"] / wide[f"net_eur|{L25}"], np.nan)
    return wide


def aggregate_itc(pn, desc_by_newest, L25, L26):
    pn = pn.copy()
    pn["_abs"] = pn[f"net_eur|{L25}"].abs() + pn[f"net_eur|{L26}"].abs()
    rows = []
    for fam_key, g in pn.groupby("ITC_family", dropna=False):
        g2 = g.sort_values("_abs", ascending=False)
        cat = next((c for c in g2["Category"] if c and c != "UNCLASSIFIED"),
                   g2["Category"].iloc[0] if len(g2) else "UNCLASSIFIED")
        pms = g2.dropna(subset=["PMS Category"])
        desc = desc_by_newest.get(fam_key, "") or next((d for d in g2["Description"] if d), "")
        rows.append({
            "Newest_PN": fam_key, "Description": desc, "Category": cat,
            "PMS Category": pms["PMS Category"].iloc[0] if len(pms) else None,
            "Member_PNs": "; ".join(sorted({m for m in g["Material"] if m})),
            "Member_count": len({m for m in g["Material"] if m}),
            f"Qty|{L25}": g[f"qty|{L25}"].sum(), f"Net|{L25}": g[f"net_eur|{L25}"].sum(),
            f"Qty|{L26}": g[f"qty|{L26}"].sum(), f"Net|{L26}": g[f"net_eur|{L26}"].sum(),
            "Delta_EUR": g["Delta_EUR"].sum(), "Delta_Qty": g["Delta_Qty"].sum(),
            "Any_unmapped_member": bool((~g["mapped"]).any()),
        })
    fam = pd.DataFrame(rows)
    fam["Delta_Pct"] = np.where(fam[f"Net|{L25}"] != 0, fam["Delta_EUR"] / fam[f"Net|{L25}"], np.nan)
    return fam


def netting(pn, fam, L25, L26):
    multi = fam[fam["Member_count"] > 1]
    cancelled, ex = 0.0, []
    for _, row in multi.iterrows():
        members = pn[pn["ITC_family"] == row["Newest_PN"]]
        cancel = members["Delta_EUR"].abs().sum() - abs(row["Delta_EUR"])
        if cancel > 1:
            cancelled += cancel
            ex.append({"Newest_PN": row["Newest_PN"], "Description": row["Description"],
                       "Category": row["Category"], "Member_PNs": row["Member_PNs"],
                       "Member_count": row["Member_count"],
                       "Sum_abs_member_Delta_EUR": round(members["Delta_EUR"].abs().sum(), 2),
                       "Family_Delta_EUR": round(row["Delta_EUR"], 2),
                       "Netted_away_EUR": round(cancel, 2)})
    df = pd.DataFrame(ex).sort_values("Netted_away_EUR", ascending=False) if ex else pd.DataFrame()
    return {"multi": int(len(multi)), "total": round(cancelled, 2), "examples": df}


# ----------------------------------------------------------------------- main --
def build(dbkey: str):
    p = C.load_profile(dbkey)
    d = p["defaults"]
    L25, L26 = d["window_label_prior"], d["window_label_current"]
    out_dir = C.OUT_ROOT / f"{p['key']}_Sales_Review_2026"
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = L26.replace(" ", "")
    out_xlsx = out_dir / f"ISZE_{p['key']}_{slug}_Parts_Analysis.xlsx"
    out_json = out_dir / "_summary.json"

    print(f"[{p['key']}] loading ...")
    itc_map, desc_by_newest = C.load_itc_map()
    sales = C.load_sales(p)
    # Freight / surcharge pseudo-materials (e.g. TRANSPORT "Transporting Cost")
    # are revenue but not parts. Drop them here so they cannot inflate the
    # category / mover / UNCLASSIFIED rollups. PBI reconciliation in the QA gate
    # uses load_sales directly (freight included) — which is why the two agree.
    sales = sales[~sales["Material"].isin(C.FREIGHT_MATERIAL_CODES)].copy()
    catalog = C.load_catalog()
    bvp_pns = C.load_bvp_pns()

    gross = sales[~sales["is_credit"]].copy()
    g25 = float(gross.loc[gross["period"] == L25, "net_eur"].sum())
    g26 = float(gross.loc[gross["period"] == L26, "net_eur"].sum())
    n25 = float(sales.loc[sales["period"] == L25, "net_eur"].sum())
    n26 = float(sales.loc[sales["period"] == L26, "net_eur"].sum())
    cr25, cr26 = n25 - g25, n26 - g26
    print(f"  gross {g25:,.0f} -> {g26:,.0f} ({(g26/g25-1)*100:+.1f}%)   "
          f"net {n25:,.0f} -> {n26:,.0f} ({(n26/n25-1)*100:+.1f}%)")

    warr_meta = C.load_warranty_claim_pns(p)
    claim_pns = warr_meta["pns"]
    # Line-level commercial cut: claim-matched PN or campaign/recall text heuristic
    sap_by_mat = (gross.dropna(subset=["Material"])
                  .assign(_a=lambda d: d["net_eur"].abs())
                  .sort_values("_a", ascending=False)
                  .drop_duplicates("Material")
                  .set_index("Material")["sap_desc"].to_dict())
    gross["is_warranty"] = [
        C.is_warranty_pn(m, sap_by_mat.get(m, d), claim_pns)
        for m, d in zip(gross["Material"], gross["sap_desc"])
    ]
    commercial = gross[~gross["is_warranty"]].copy()
    c25 = float(commercial.loc[commercial["period"] == L25, "net_eur"].sum())
    c26 = float(commercial.loc[commercial["period"] == L26, "net_eur"].sum())
    w25 = g25 - c25
    w26 = g26 - c26
    c_pct = f"{(c26 / c25 - 1) * 100:+.1f}%" if c25 else "n/a"
    print(f"  commercial (ex-warranty) {c25:,.0f} -> {c26:,.0f} ({c_pct})   "
          f"warranty/campaign stripped {w25:,.0f} / {w26:,.0f}   "
          f"claim PNs {len(claim_pns):,} ({warr_meta['n_claim_lines']:,} claim lines)")

    # Full PN table (blended) keeps warranty flags for New Business / Warranty sheet
    pn_all = aggregate_pn(gross, catalog, desc_by_newest, itc_map, L25, L26)
    pn_all["Warranty_campaign"] = [
        C.is_warranty_pn(a, b, claim_pns)
        for a, b in zip(pn_all["Material"], pn_all["Description"])
    ]
    pn_all["Warranty_source"] = np.where(
        pn_all["Material"].isin(claim_pns),
        "claim grain",
        np.where(pn_all["Warranty_campaign"], "text heuristic", ""),
    )

    # Movers / categories / BVP = commercial only (ex-warranty / campaign)
    pn = aggregate_pn(commercial, catalog, desc_by_newest, itc_map, L25, L26)
    pn["Warranty_campaign"] = False
    pn["Warranty_source"] = ""
    model_by_pn = C.load_pn_vehicle_models()
    pn["Vehicle_model"] = pn["Material"].map(
        lambda m: model_by_pn.get(m) or model_by_pn.get(itc_map.get(m, m), "") or ""
    )
    fam = aggregate_itc(pn, desc_by_newest, L25, L26)
    fam["Warranty_campaign"] = False
    fam["Vehicle_model"] = fam["Newest_PN"].map(
        lambda m: model_by_pn.get(m, "") if m else ""
    )
    # Prefer a member PN's model when the newest PN itself is unmapped
    if model_by_pn:
        for i, row in fam.iterrows():
            if row.get("Vehicle_model"):
                continue
            members = [x.strip() for x in str(row.get("Member_PNs") or "").split(";") if x.strip()]
            for m in members:
                hit = model_by_pn.get(m)
                if hit:
                    fam.at[i, "Vehicle_model"] = hit
                    break
    net = netting(pn, fam, L25, L26)
    assert abs(fam[f"Net|{L25}"].sum() - pn[f"net_eur|{L25}"].sum()) < 0.05
    assert abs(fam[f"Net|{L26}"].sum() - pn[f"net_eur|{L26}"].sum()) < 0.05

    cat = (fam.groupby("Category", dropna=False)
           .agg(**{f"Net|{L25}": (f"Net|{L25}", "sum"), f"Net|{L26}": (f"Net|{L26}", "sum"),
                   f"Qty|{L25}": (f"Qty|{L25}", "sum"), f"Qty|{L26}": (f"Qty|{L26}", "sum")})
           .reset_index())
    cat["Delta_EUR"] = cat[f"Net|{L26}"] - cat[f"Net|{L25}"]
    cat["Delta_Pct"] = np.where(cat[f"Net|{L25}"] != 0, cat["Delta_EUR"] / cat[f"Net|{L25}"], np.nan)
    cat = cat.sort_values("Delta_EUR")

    def not_rebate(m, ds):
        return "REBATE" not in str(m or "").upper() and "REBATE" not in str(ds or "").upper()

    pn_ex = pn[[not_rebate(a, b) for a, b in zip(pn["Material"], pn["Description"])]]
    fam_ex = fam[[not_rebate(a, b) for a, b in zip(fam["Newest_PN"], fam["Description"])]]
    grow_pn = pn_ex[(pn_ex[f"net_eur|{L25}"] > 0) & (pn_ex["Delta_EUR"] > 0)]
    grow_fam = fam_ex[(fam_ex[f"Net|{L25}"] > 0) & (fam_ex["Delta_EUR"] > 0)]

    # BVP split — commercial basis (same cut as movers)
    pn["is_bvp"] = pn["Material"].isin(bvp_pns)
    bvp = {"bvp_prior": float(pn.loc[pn["is_bvp"], f"net_eur|{L25}"].sum()),
           "bvp_current": float(pn.loc[pn["is_bvp"], f"net_eur|{L26}"].sum()),
           "gen_prior": float(pn.loc[~pn["is_bvp"], f"net_eur|{L25}"].sum()),
           "gen_current": float(pn.loc[~pn["is_bvp"], f"net_eur|{L26}"].sum())}

    # Prior-zero lines are quarantined from growth. They may be genuinely new,
    # but may equally be a supersession, timing effect, or warranty campaign.
    # Use blended PN table so claim-matched first sales still surface for review.
    new_biz = pn_all[
        (pn_all[f"net_eur|{L25}"] == 0) & (pn_all[f"net_eur|{L26}"] > 0)
    ].copy()
    new_biz["Review_reason"] = np.where(
        new_biz["Warranty_campaign"],
        "Warranty / campaign PN (claim grain or heuristic) — not commercial growth",
        "Review as new model, supersession or timing before classifying",
    )
    new_biz = new_biz.nlargest(40, f"net_eur|{L26}")
    # Freight / surcharge codes are not commercial "new business".
    pn_u = new_biz["Material"].astype(str).str.strip().str.upper()
    desc_l = new_biz["Description"].astype(str).str.lower()
    new_biz = new_biz[
        ~pn_u.isin(["TRANSPORT", "FREIGHT", "SHIPPING"])
        & ~desc_l.str.contains("transport", na=False)
    ].copy()

    pms_year, pms = C.load_pms(p)
    peers = C.pms_vs_network(p, year=pms_year)
    gm = C.load_gps_master(p)
    fy = C.load_fy27(p)
    uio = C.load_uio(p)
    ids = C.load_ids(p)

    # -------------------------------------------------------------- workbook --
    wb = Workbook()
    ws = wb.active
    ws.title = "Notes"
    notes = [
        f"{p['key']} — {p['name']} ({p['country']}) — {L26} vs {L25} parts sales analysis, ITC rollup",
        "",
        f"Windows: {L26} = {d['window_current'][0]} to {d['window_current'][1]} (exclusive); "
        f"{L25} = {d['window_prior'][0]} to {d['window_prior'][1]} (exclusive).",
        "Basis: raw SAP Net value, ISZE->DB billing. Not GPS-signed/filtered.",
        "",
        "RECONCILIATION (all billing lines in the windows):",
        f"  Gross parts billing   {L25} EUR {g25:,.2f}   {L26} EUR {g26:,.2f}   ({(g26/g25-1)*100:+.1f}%)",
        f"  of which warranty/campaign PN (stripped from movers)",
        f"                         {L25} EUR {w25:,.2f}   {L26} EUR {w26:,.2f}",
        (
            f"  Commercial (ex-warr.) {L25} EUR {c25:,.2f}   {L26} EUR {c26:,.2f}   "
            f"({(c26 / c25 - 1) * 100:+.1f}%)"
            if c25 else
            f"  Commercial (ex-warr.) {L25} EUR {c25:,.2f}   {L26} EUR {c26:,.2f}"
        ),
        f"  Credit memos (G2/CR)  {L25} EUR {cr25:,.2f}   {L26} EUR {cr26:,.2f}",
        f"  Net billing           {L25} EUR {n25:,.2f}   {L26} EUR {n26:,.2f}   ({(n26/n25-1)*100:+.1f}%)",
        "  Credit memos carry a POSITIVE Net value in the raw SAP export but are economically",
        "  negative — signed here, matching net_value_gps_signed in the tagged extract. Credits",
        "  stay on the net bridge and are kept out of mover lists as a commercial adjustment.",
        "  Category / PN / ITC mover sheets use COMMERCIAL gross (ex-warranty/campaign) only.",
        "",
        "Sources:",
        rf"- {L26}: 01_data\00_derived\cy2026_q1.csv (Payer.1 = '{p['payer']}')",
        rf"- {L25}: 01_data\00_derived\cy2025_raw.csv (DB = '{p['payer']}')",
        r"- Category: 01_data\00_derived\parts_catalog_dimension.csv (pr00_group)",
        r"- ITC map: 01_data\01_Pricing\Price file 2026_full.xlsx, P/N -> Newest P/N",
        rf"- PMS: 01_data\00_derived\pms_capture_by_db_year.csv, distributor_code='{p['pms_code']}'",
        rf"- GPS: 01_data\00_derived\gps_master.csv row '{p['gps_key']}'",
        rf"- FY2027 target: 01_data\ISZE_GPS_Extended_Target_FY27_V3.1.xlsx tab '{p['fy27_tab']}'",
        r"- UIO: 06_uio\_CURRENT\ISUZU_UIO_Overview_2026.xlsx, '1.UIO Overview'",
        r"- Warranty claims (PN cut): 01_data\00_derived\warranty_raw_grain.csv",
        r"- Warranty CY totals: 01_data\06_Warranty\Warranty_CY2025_by_DB.md",
        "",
        f"Warranty exclusion: {len(claim_pns):,} claim PNs from grain names "
        f"{', '.join(warr_meta['db_names']) or '(none mapped)'}; "
        f"assess {warr_meta['assess_month_from']}–{warr_meta['assess_month_to']} "
        f"({warr_meta['n_claim_lines']:,} lines, claim-price EUR {warr_meta['claim_eur']:,.0f}); "
        f"plus PN/description text heuristic (PM sensor / warranty / campaign / recall).",
        f"ITC coverage (commercial): PN rows {len(pn):,} | unmapped {int((~pn['mapped']).sum()):,} | "
        f"families {len(fam):,} | multi-member {net['multi']:,} | "
        f"|Delta| cancelled EUR {net['total']:,.2f}",
        "",
        "WATCH LIST FOR THIS DB:",
    ] + [f"  · {w}" for w in (p.get("watch") or ["(none recorded)"])] + [
        "",
        "Caveats:",
        "  - ERP has no warranty document type; warranty parts ride normal orders. Exclusion is",
        "    PN-level from claim grain (+ text heuristic), not a true warranty-flagged invoice line.",
        "  - Claim-matched PNs drop ALL billing of that PN in the window (commercial + warranty).",
        "    Preferable to blended demand for a sales review; residual unmapped warranty may remain.",
        "  - Claim assessment months lag billing; prior window opens 3 months early on the grain.",
        "  - Grain coverage is uneven by year/DB (e.g. sparse H1 2025 assess months for some markets).",
        "  - Some sold PNs are absent from the price file -> ITC family = self.",
        "  - Mover lists exclude REBATE lines and warranty/campaign PNs.",
        "  - Growth requires prior-period sales > 0.",
        "  - Prior-zero/current-positive lines are quarantined on New Business, not counted as growth.",
        "",
        "Rebuild:  python build_parts_analysis.py --db " + p["key"],
    ]
    for i, line in enumerate(notes, 1):
        ws.cell(i, 1, line)
    ws.column_dimensions["A"].width = 118

    # Official quarter
    pbi = p.get("pbi")
    ws = wb.create_sheet("Official Quarter")
    pbi_complete = bool(
        pbi
        and pbi.get("sales")
        and pbi.get("budget")
        and pbi.get("prev_year")
        and all(v is not None for k in ("sales", "budget", "prev_year") for v in pbi.get(k, []))
        and len(pbi["sales"]) == len(pbi["months"]) == len(pbi["budget"]) == len(pbi["prev_year"])
    )
    if pbi_complete:
        ws.cell(1, 1, f"{p['key']} — {pbi['quarter']}, official Power BI cut").font = TITLE_FONT
        rows = [[""] + pbi["months"] + ["Total"],
                ["Sales amount (EUR)"] + pbi["sales"] + [sum(pbi["sales"])],
                ["Budget / original BP (EUR)"] + pbi["budget"] + [sum(pbi["budget"])],
                ["vs budget"] + [s / b - 1 for s, b in zip(pbi["sales"], pbi["budget"])]
                + [sum(pbi["sales"]) / sum(pbi["budget"]) - 1],
                ["Sales prev. year (EUR)"] + pbi["prev_year"] + [sum(pbi["prev_year"])],
                ["vs prev. year"] + [s / v - 1 for s, v in zip(pbi["sales"], pbi["prev_year"])]
                + [sum(pbi["sales"]) / sum(pbi["prev_year"]) - 1]]
        for r, row in enumerate(rows, 3):
            for c, v in enumerate(row, 1):
                cell = ws.cell(r, c, v)
                cell.border = BORDER
                if r == 3:
                    cell.fill, cell.font = HEADER_FILL, HEADER_FONT
                elif isinstance(v, float):
                    cell.number_format = PCT_FMT
                elif isinstance(v, int) and c > 1:
                    cell.number_format = "#,##0"
        ws.cell(10, 1, f"Source: {pbi['source']}. Authoritative — the SAP extract for the same "
                       "quarter is not used here.")
    elif pbi and pbi.get("sales"):
        ws.cell(1, 1, f"{p['key']} — {pbi['quarter']}, partial Power BI cut").font = TITLE_FONT
        rows = [[""] + pbi["months"] + ["Total"],
                ["Sales amount (EUR)"] + pbi["sales"] + [sum(pbi["sales"])]]
        for r, row in enumerate(rows, 3):
            for c, v in enumerate(row, 1):
                cell = ws.cell(r, c, v)
                cell.border = BORDER
                if r == 3:
                    cell.fill, cell.font = HEADER_FILL, HEADER_FONT
                elif isinstance(v, (int, float)) and c > 1:
                    cell.number_format = "#,##0"
        ws.cell(7, 1, "Budget and/or prior-year monthly values are incomplete. "
                       "The sales-review slide must be skipped until the full cut is supplied.")
    else:
        ws.cell(1, 1, "No Power BI quarter on record for this DB.").font = TITLE_FONT
        ws.cell(2, 1, "Ask Jerome for the cut and paste it into db_profiles.yaml under pbi:.")
    ws.column_dimensions["A"].width = 34

    ren_pn = {"Newest_PN": "Newest P/N", f"qty|{L25}": f"Qty {L25}", f"net_eur|{L25}": f"Net EUR {L25}",
              f"qty|{L26}": f"Qty {L26}", f"net_eur|{L26}": f"Net EUR {L26}", "Delta_EUR": "Delta EUR",
              "Delta_Qty": "Delta Qty", "Delta_Pct": "Delta %", "mapped": "In price file",
              "is_bvp": "BVP line", "Warranty_campaign": "Warranty / campaign",
              "Warranty_source": "Warranty source"}
    ren_fam = {"Newest_PN": "Newest P/N", f"Qty|{L25}": f"Qty {L25}", f"Net|{L25}": f"Net EUR {L25}",
               f"Qty|{L26}": f"Qty {L26}", f"Net|{L26}": f"Net EUR {L26}", "Delta_EUR": "Delta EUR",
               "Delta_Qty": "Delta Qty", "Delta_Pct": "Delta %", "Member_PNs": "Member PNs",
               "Member_count": "Member count", "Any_unmapped_member": "Any unmapped member",
               "Warranty_campaign": "Warranty / campaign"}
    CUR = {f"Net EUR {L25}", f"Net EUR {L26}", "Delta EUR"}
    QTY = {f"Qty {L25}", f"Qty {L26}", "Delta Qty"}

    ws = wb.create_sheet("PN Detail")
    ws.cell(1, 1, f"Commercial PNs only (warranty/campaign excluded) — {L26} vs {L25}").font = TITLE_FONT
    write_df(ws, pn.rename(columns=ren_pn)[
        ["Material", "Newest P/N", "Description", "Category", "PMS Category", "BVP line",
         f"Qty {L25}", f"Net EUR {L25}", f"Qty {L26}", f"Net EUR {L26}",
         "Delta EUR", "Delta Qty", "Delta %", "In price file"]].sort_values("Delta EUR"),
        start_row=2, currency=CUR, qty=QTY, pct={"Delta %"})

    ws = wb.create_sheet("ITC Family Detail")
    ws.cell(1, 1, f"Commercial ITC families (warranty/campaign excluded) — {L26} vs {L25}").font = TITLE_FONT
    write_df(ws, fam.rename(columns=ren_fam)[
        ["Newest P/N", "Description", "Category", "PMS Category", "Member count", "Member PNs",
         f"Qty {L25}", f"Net EUR {L25}", f"Qty {L26}", f"Net EUR {L26}",
         "Delta EUR", "Delta Qty", "Delta %", "Any unmapped member"]].sort_values("Delta EUR"),
        start_row=2, currency=CUR, qty=QTY, pct={"Delta %"})

    stripped = pn_all[pn_all["Warranty_campaign"]].copy()
    stripped["is_bvp"] = stripped["Material"].isin(bvp_pns)
    ws = wb.create_sheet("Warranty PNs Stripped")
    ws.cell(1, 1, "PNs removed from commercial movers (claim grain and/or text heuristic)").font = TITLE_FONT
    if len(stripped):
        write_df(ws, stripped.rename(columns=ren_pn)[
            ["Material", "Newest P/N", "Description", "Category", "Warranty source",
             f"Qty {L25}", f"Net EUR {L25}", f"Qty {L26}", f"Net EUR {L26}",
             "Delta EUR", "Delta Qty"]].sort_values("Delta EUR"),
            start_row=2, currency=CUR, qty=QTY)
    else:
        ws.cell(3, 1, "No warranty/campaign PNs matched for this DB in the claim window.")

    def movers(name, decl, grow, ren, cols, label):
        w = wb.create_sheet(name)
        dd, gg = decl.rename(columns=ren)[cols], grow.rename(columns=ren)[cols]
        w.cell(1, 1, f"TOP {TOP_N} DECLINING {label} — commercial / ex-warranty "
                     f"({L26} vs {L25})").font = TITLE_FONT
        write_df(w, dd, start_row=2, currency=CUR, qty=QTY)
        sg = 2 + len(dd) + 3
        w.cell(sg - 1, 1, f"TOP {TOP_N} GROWING {label} — commercial / ex-warranty "
                          f"({L26} vs {L25}, excl. REBATE)").font = TITLE_FONT
        write_df(w, gg, start_row=sg, currency=CUR, qty=QTY)
        w.auto_filter.ref = f"A2:{get_column_letter(len(cols))}{2 + len(dd)}"

    cols_itc = ["Newest P/N", "Description", "Category", "Member count",
                f"Qty {L25}", f"Net EUR {L25}", f"Qty {L26}", f"Net EUR {L26}", "Delta EUR", "Delta Qty"]
    movers("Top Movers ITC", fam_ex.nsmallest(TOP_N, "Delta_EUR"),
           grow_fam.nlargest(TOP_N, "Delta_EUR"), ren_fam, cols_itc, "ITC FAMILIES")
    cols_pn = ["Material", "Newest P/N", "Description", "Category",
               f"Qty {L25}", f"Net EUR {L25}", f"Qty {L26}", f"Net EUR {L26}", "Delta EUR", "Delta Qty"]
    movers("Top Movers PN", pn_ex.nsmallest(TOP_N, "Delta_EUR"),
           grow_pn.nlargest(TOP_N, "Delta_EUR"), ren_pn, cols_pn, "PNs")

    ws = wb.create_sheet("ITC Netted Away")
    ws.cell(1, 1, "ITC families where PN-level deltas partly cancel after the rollup").font = TITLE_FONT
    ws.cell(2, 1, f"Total |Delta| cancelled: EUR {net['total']:,.2f}")
    if len(net["examples"]):
        write_df(ws, net["examples"], start_row=4,
                 currency={"Sum_abs_member_Delta_EUR", "Family_Delta_EUR", "Netted_away_EUR"})
    else:
        ws.cell(4, 1, "No material multi-member cancellations found.")

    ws = wb.create_sheet("Category Summary")
    ws.cell(1, 1, "Commercial category rollup (warranty/campaign PNs excluded)").font = TITLE_FONT
    write_df(ws, cat.rename(columns={f"Net|{L25}": f"Net EUR {L25}", f"Net|{L26}": f"Net EUR {L26}",
                                     f"Qty|{L25}": f"Qty {L25}", f"Qty|{L26}": f"Qty {L26}",
                                     "Delta_EUR": "Delta EUR", "Delta_Pct": "Delta %"}),
             start_row=2, currency=CUR, qty={f"Qty {L25}", f"Qty {L26}"}, pct={"Delta %"})

    ws = wb.create_sheet("Genuine vs BVP")
    ws.cell(1, 1, "Genuine vs value-tier (BVP) — commercial / ex-warranty basis").font = TITLE_FONT
    rows = [["Line type", f"Net EUR {L25}", f"Net EUR {L26}", "Delta EUR", "Delta %"],
            ["Genuine", bvp["gen_prior"], bvp["gen_current"],
             bvp["gen_current"] - bvp["gen_prior"],
             (bvp["gen_current"] / bvp["gen_prior"] - 1) if bvp["gen_prior"] else None],
            ["BVP (value tier)", bvp["bvp_prior"], bvp["bvp_current"],
             bvp["bvp_current"] - bvp["bvp_prior"],
             (bvp["bvp_current"] / bvp["bvp_prior"] - 1) if bvp["bvp_prior"] else None]]
    for r, row in enumerate(rows, 2):
        for c, v in enumerate(row, 1):
            cell = ws.cell(r, c, v)
            cell.border = BORDER
            if r == 2:
                cell.fill, cell.font = HEADER_FILL, HEADER_FONT
            elif c == 5 and isinstance(v, float):
                cell.number_format = PCT_FMT
            elif isinstance(v, float):
                cell.number_format = NUM_FMT
    ws.cell(6, 1, "If genuine falls and BVP rises, that is a value-tier switch. If BOTH fall, it is "
                  "real volume loss — that is the distinction the decline slides must make.")
    ws.column_dimensions["A"].width = 22
    for c in "BCDE":
        ws.column_dimensions[c].width = 18

    ws = wb.create_sheet("New Business")
    ws.cell(1, 1, f"New Business quarantine — prior EUR 0, current EUR >0 ({L26} vs {L25})").font = TITLE_FONT
    nb = new_biz.rename(columns=ren_pn)[["Material", "Newest P/N", "Description", "Category",
                                         f"Qty {L26}", f"Net EUR {L26}", "Review_reason"]]
    write_df(ws, nb, start_row=2, currency={f"Net EUR {L26}"}, qty={f"Qty {L26}"})
    ws.cell(2 + len(nb) + 2, 1, "A PN here can still be a re-numbered supersession rather than new "
                                "business — check the Newest P/N column before calling it a win.")

    ws = wb.create_sheet("PMS Capture")
    ws.cell(1, 1, f"{p['key']} — PMS category capture, {pms_year}").font = TITLE_FONT
    write_df(ws, pms.rename(columns={
        "pms_category": "PMS category", "category_label": "Label", "uio_units": "UIO units",
        "expected_qty": "Expected qty", "actual_qty": "Actual qty", "actual_rev_eur": "Actual EUR",
        "capture_rate": "Capture rate", "avg_sp_eur": "Avg SP EUR",
        "revenue_gap_eur": "Revenue gap EUR", "revenue_gap_quotable": "Gap quotable"})[
        ["PMS category", "Label", "UIO units", "Expected qty", "Actual qty", "Actual EUR",
         "Capture rate", "Avg SP EUR", "Revenue gap EUR", "Gap quotable"]], start_row=2,
        currency={"Actual EUR", "Avg SP EUR", "Revenue gap EUR"},
        qty={"Expected qty", "Actual qty"}, pct={"Capture rate"})
    r0 = 2 + len(pms) + 2
    ws.cell(r0, 1, "vs the rest of the network, same expected-quantity model:").font = TITLE_FONT
    for i, (k, v) in enumerate(peers.items(), 1):
        ws.cell(r0 + i, 1, k)
        ws.cell(r0 + i, 2, v["db"] / 100).number_format = PCT_FMT
        ws.cell(r0 + i, 3, v["network"] / 100).number_format = PCT_FMT
        ws.cell(r0 + i, 4, v["best"] / 100).number_format = PCT_FMT
    ws.cell(r0, 2, "this DB"); ws.cell(r0, 3, "network"); ws.cell(r0, 4, "best")
    ws.cell(r0 + len(peers) + 2, 1,
            "Only oil and fuel filter intervals are OEM-confirmed. Air filter is a derived "
            "provisional ratio; urea and blower have no OEM-sourced interval — directional only.")

    ws = wb.create_sheet("GPS & FY27 Target")
    r = 1

    def block(title, items):
        nonlocal r
        ws.cell(r, 1, title).font = TITLE_FONT
        r += 1
        ws.cell(r, 1, "Item").fill = HEADER_FILL; ws.cell(r, 1).font = HEADER_FONT
        ws.cell(r, 2, "Value").fill = HEADER_FILL; ws.cell(r, 2).font = HEADER_FONT
        r += 1
        for lab, val, fmt in items:
            ws.cell(r, 1, lab).border = BORDER
            c = ws.cell(r, 2, val); c.number_format = fmt; c.border = BORDER
            r += 1
        r += 1

    block(f"GPS — gps_master row '{p['gps_key']}' (flat EUR {gm['rate']:,.0f}/unit — reference only)",
          [("UIO CY2025", gm["uio_2025"], "#,##0"),
           ("Max spend (flat rate)", gm["max_spend"], NUM_FMT),
           ("GPS FY2024", gm["gps_pct_FY2024"], PCT_FMT),
           ("GPS FY2025", gm["gps_pct_FY2025"], PCT_FMT),
           ("GPS FY2026", gm["gps_pct_FY2026"], PCT_FMT)])
    seg_items = []
    for seg, v in fy["segments"].items():
        seg_items.append((f"UIO {seg} FY2027", v["fy27"], "#,##0"))
    block(f"ISZE-to-DB reference — Extended Target tab '{fy['tab']}' (internal reconciliation)",
          seg_items + [
              ("Max spend FY2027", fy["max_spend"]["fy27"], NUM_FMT),
              ("Actual FY2026", fy["actual"]["fy26"], NUM_FMT),
              ("BP FY2027", fy["actual"]["fy27"], NUM_FMT),
              ("GPS FY2026", (fy.get("gps") or {}).get("fy26"), PCT_FMT),
              ("Stretch %", (fy.get("stretch_pct") or {}).get("fy27"), PCT_FMT),
              ("Stretch EUR", (fy.get("stretch_eur") or {}).get("fy27"), NUM_FMT),
              ("EXTENDED TARGET FY2027", fy["ext_target"]["fy27"], NUM_FMT),
              ("GPS after stretch", (fy.get("gps_new") or {}).get("fy27"), PCT_FMT),
              ("Incentive budgeted FY2027", p.get("incentive_fy27"), NUM_FMT)])
    s2d = fy["s2d_target"]
    block("Sales-to-Dealer target — meeting headline (Dashboard P:U method)",
          [("Sales-to-Dealer FY2025", s2d["fy25"], NUM_FMT),
           ("Sales-to-Dealer FY2026", s2d["fy26"], NUM_FMT),
           ("UIO growth", s2d["uio_growth"], PCT_FMT),
           ("Price adjustment", s2d["price"], PCT_FMT),
           ("Additional growth", s2d["additional"], PCT_FMT),
           ("SALES-TO-DEALER FY2027 TARGET", s2d["fy27"], NUM_FMT),
           ("S2D base imputed", "Yes — FY2026 ISZE billing / 0.65"
            if s2d["s2d_imputed"] else "No — KPI S2D", "@")])
    ws.column_dimensions["A"].width = 44
    ws.column_dimensions["B"].width = 20

    if ids is not None:
        mine, net_avg, db_avg, n_skipped = ids
        ws = wb.create_sheet("IDS 2026")
        skip_note = (f" {n_skipped} dealer(s) excluded — assessment not returned."
                     if n_skipped else "")
        ws.cell(1, 1, f"IDS 2026 — {p['key']} dealers ({len(mine)} assessed). DB average "
                      f"{db_avg:.1f}% vs network average {net_avg:.1f}%.{skip_note}").font = TITLE_FONT
        write_df(ws, mine[["Rank (country)", "Global rank", "Dealer",
                           "Points achieved %", "Items scored %"]], start_row=2)

    ws = wb.create_sheet("Warranty")
    w = p.get("warranty_cy2025_claim")
    lines = [["Warranty exclusion for commercial movers — " + p["name"]], [],
             ["Question", "Answer"],
             ["Can warranty be split by ERP document type?",
              "No — ERP has no warranty document type; warranty parts flow through normal orders."],
             ["How movers are made commercial / ex-warranty",
              "Exclude billing of PNs that appear on warranty_raw_grain claim lines for this DB "
              f"(assess {warr_meta['assess_month_from']}–{warr_meta['assess_month_to']}, "
              f"{C.WARRANTY_CLAIM_LAG_MONTHS}m lag before prior window) plus PN/description "
              "text heuristic (PM sensor / warranty / campaign / recall)."],
             ["Grain DB names used", ", ".join(warr_meta["db_names"]) or "(none mapped)"],
             ["Claim lines in window", warr_meta["n_claim_lines"]],
             ["Claim-price EUR in window", round(warr_meta["claim_eur"], 2)],
             ["Distinct claim PNs", len(claim_pns)],
             ["Billing stripped (gross) " + L25, round(w25, 2)],
             ["Billing stripped (gross) " + L26, round(w26, 2)],
             ["Commercial gross " + L25, round(c25, 2)],
             ["Commercial gross " + L26, round(c26, 2)],
             ["SaTy codes observed", ", ".join(sorted(sales["SaTy"].dropna().unique()))],
             ["CY2025 warranty parts, claim-price basis (EUR)", w],
             ["  approx. ISZE-net equivalent (x0.74) (EUR)", round(w * 0.74, 2) if w else None],
             ["Note at source", p.get("warranty_note", "—")],
             ["Claim grain source", r"01_data\00_derived\warranty_raw_grain.csv"],
             ["CY total source", r"01_data\06_Warranty\Warranty_CY2025_by_DB.md"],
             [f"{L25} Net EUR (blended, with credits)", round(n25, 2)],
             [f"{L26} Net EUR (blended, with credits)", round(n26, 2)], [],
             ["Limitation",
              "PN-level exclusion removes all billing of a claim PN in the window, including any "
              "genuine commercial demand for that PN. Residual warranty on unmapped PNs can remain. "
              "Grain assess-month coverage is uneven (some H1 prior windows are thin). Credits stay "
              "on the net bridge and are not re-labelled as warranty."]]
    for r_i, row in enumerate(lines, 1):
        for c_i, v in enumerate(row, 1):
            cell = ws.cell(r_i, c_i, v)
            if r_i == 3:
                cell.fill, cell.font = HEADER_FILL, HEADER_FONT
            elif isinstance(v, float) and c_i == 2:
                cell.number_format = NUM_FMT
    ws.column_dimensions["A"].width = 50
    ws.column_dimensions["B"].width = 105

    ws = wb.create_sheet("SaTy Mix")
    mix = (sales.groupby(["period", "SaTy"]).agg(net_eur=("net_eur", "sum"),
                                                 lines=("net_eur", "size")).reset_index()
           .rename(columns={"period": "Period", "net_eur": "Net EUR", "lines": "Lines"}))
    mix["Share of period Net EUR"] = mix["Net EUR"] / mix.groupby("Period")["Net EUR"].transform("sum")
    write_df(ws, mix.sort_values(["Period", "Net EUR"], ascending=[True, False]),
             currency={"Net EUR"}, pct={"Share of period Net EUR"})

    wb.save(out_xlsx)
    print(f"  wrote {out_xlsx}")

    # ------------------------------------------------------------ summary json --
    def _model(r, pn_key="Newest_PN"):
        m = str(r.get("Vehicle_model") or "").strip()
        if m:
            return m
        return model_by_pn.get(r.get(pn_key)) or ""

    def famrows(df, n):
        return [{"pn": r["Newest_PN"], "desc": r["Description"], "cat": r["Category"],
                 "model": _model(r, "Newest_PN"),
                 "prior": round(float(r[f"Net|{L25}"]), 2),
                 "current": round(float(r[f"Net|{L26}"]), 2),
                 "d": round(float(r["Delta_EUR"]), 2), "dq": round(float(r["Delta_Qty"]), 1)}
                for _, r in df.head(n).iterrows()]

    def pnrows(df, n):
        return [{"pn": r["Material"], "newest": r["Newest_PN"], "desc": r["Description"],
                 "cat": r["Category"], "model": _model(r, "Material") or _model(r, "Newest_PN"),
                 "prior": round(float(r[f"net_eur|{L25}"]), 2),
                 "current": round(float(r[f"net_eur|{L26}"]), 2),
                 "d": round(float(r["Delta_EUR"]), 2), "dq": round(float(r["Delta_Qty"]), 1)}
                for _, r in df.head(n).iterrows()]

    decl_pn = pn_ex.nsmallest(TOP_N, "Delta_EUR")
    grow_pn_ranked = grow_pn.nlargest(TOP_N, "Delta_EUR")

    # Per-category largest EUR PN drivers (commercial) for Mode A deep-dives
    category_pn_drivers = {}
    for cat_name, g in pn_ex.groupby("Category", dropna=False):
        if not cat_name or cat_name in {"UNCLASSIFIED"}:
            continue
        d_sub = g[g["Delta_EUR"] < 0].nsmallest(5, "Delta_EUR")
        # Prefer largest EUR growers including first-seen-in-window (prior=0).
        g_sub = g[g["Delta_EUR"] > 0].nlargest(5, "Delta_EUR")
        if d_sub.empty and g_sub.empty:
            continue
        category_pn_drivers[str(cat_name)] = {
            "decl": pnrows(d_sub, 5),
            "grow": pnrows(g_sub, 5),
        }

    summary = {
        "db": p["key"], "name": p["name"], "country": p["country"], "display": p["display"],
        "segment": p["segment"], "label_prior": L25, "label_current": L26,
        "gross_prior": round(g25, 2), "gross_current": round(g26, 2),
        "gross_delta_pct": round(g26 / g25 - 1, 4) if g25 else None,
        "commercial_prior": round(c25, 2), "commercial_current": round(c26, 2),
        "commercial_delta_pct": round(c26 / c25 - 1, 4) if c25 else None,
        "warranty_stripped_prior": round(w25, 2), "warranty_stripped_current": round(w26, 2),
        "movers_basis": "commercial_ex_warranty",
        "credits_prior": round(cr25, 2), "credits_current": round(cr26, 2),
        "net_prior": round(n25, 2), "net_current": round(n26, 2),
        "net_delta_pct": round(n26 / n25 - 1, 4) if n25 else None,
        "pbi": p.get("pbi"),
        "categories": [{"cat": r["Category"], "prior": round(float(r[f"Net|{L25}"]), 2),
                        "current": round(float(r[f"Net|{L26}"]), 2),
                        "d": round(float(r["Delta_EUR"]), 2),
                        "dp": None if pd.isna(r["Delta_Pct"]) else round(float(r["Delta_Pct"]), 4)}
                       for _, r in cat.iterrows()],
        "top_decl_itc": famrows(fam_ex.nsmallest(TOP_N, "Delta_EUR"), 15),
        "top_grow_itc": famrows(grow_fam.nlargest(TOP_N, "Delta_EUR"), 15),
        "top_decl_pn": pnrows(decl_pn, 15),
        "top_grow_pn": pnrows(grow_pn_ranked, 15),
        "category_pn_drivers": category_pn_drivers,
        "model_attribution": {
            "source": "genuine_bvp_crossref + bvp_addressable_basket (vehicle_model)",
            "coverage": "BVP/PMS addressable basket only - not full EPC/GIDSS",
            "n_mapped_pns": len(model_by_pn),
            "browser_catalogue_required": False,
            "note": (
                "PN EUR drivers come from SAP billing. Model is filled only when the PN "
                "appears in the BVP/PMS application tables; blank otherwise. Full fitment "
                "for arbitrary PNs would need EPC/GIDSS - not required for the movers slides."
            ),
        },
        "new_business": [{"pn": r["Material"], "desc": r["Description"], "cat": r["Category"],
                          "current": round(float(r[f"net_eur|{L26}"]), 2),
                          "qty": round(float(r[f"qty|{L26}"]), 1),
                          "warranty_campaign": bool(r["Warranty_campaign"]),
                          "review_reason": r["Review_reason"]}
                         for _, r in new_biz.head(12).iterrows()],
        "bvp": {k: round(v, 2) for k, v in bvp.items()},
        "pms_year": pms_year,
        "pms_peers": peers,
        "gps_master": gm, "fy27": fy, "uio": {k: v for k, v in uio.items()},
        "gps_segmented": C.load_segmented_gps(p),
        "ids": None if ids is None else {
            "n": int(len(ids[0])), "network_avg": round(ids[1], 1), "db_avg": round(ids[2], 1),
            "n_not_assessed": int(ids[3]),
            "top": [{"dealer": r["Dealer"], "pts": float(r["Points achieved %"]),
                     "grank": int(r["Global rank"])} for _, r in ids[0].head(3).iterrows()],
            "bottom": [{"dealer": r["Dealer"], "pts": float(r["Points achieved %"]),
                        "grank": int(r["Global rank"])} for _, r in ids[0].tail(3).iterrows()]},
        "warranty_claim": p.get("warranty_cy2025_claim"),
        "warranty_note": (
            "Movers exclude claim-matched PNs from warranty_raw_grain (+ text heuristic). "
            "CY2025 claim-price total below is from Warranty_CY2025_by_DB.md — distinct from "
            "fiscal GPS warranty expense in distributor_warranty_expense_fiscal.csv."
        ),
        "warranty_exclusion": {
            "method": warr_meta["method"],
            "available": warr_meta["available"],
            "db_names": warr_meta["db_names"],
            "n_claim_pns": len(claim_pns),
            "n_claim_lines": warr_meta["n_claim_lines"],
            "claim_eur": round(warr_meta["claim_eur"], 2),
            "assess_month_from": warr_meta["assess_month_from"],
            "assess_month_to": warr_meta["assess_month_to"],
            "billing_stripped_prior": round(w25, 2),
            "billing_stripped_current": round(w26, 2),
        },
        "incentive_fy27": p.get("incentive_fy27"),
        "watch": p.get("watch") or [],
        "defaults": d,
        "xlsx": str(out_xlsx),
    }
    out_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str),
                        encoding="utf-8")
    print(f"  wrote {out_json}")

    print("\n  commercial category movers (>|5,000| EUR):")
    for _, r in cat.iterrows():
        if abs(r["Delta_EUR"]) > 5000:
            dp = "" if pd.isna(r["Delta_Pct"]) else f"{r['Delta_Pct']*100:+.1f}%"
            print(f"    {str(r['Category'])[:36]:<36} {r['Delta_EUR']:>12,.0f} {dp:>9}")
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, help=f"one of: {', '.join(C.list_profiles())}")
    build(ap.parse_args().db)
