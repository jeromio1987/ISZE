"""
Build UTI P700 recommended parts list (Excel + CSV) from harvested APL rows.

shared list · internal advise notes · 2026-08-12
- Prefer VL27 Recommended / ITUK PRD / accessories / body P700 over VL27 All Parts
- No invented per-PN qty or € demand
- UTI ≠ UMI; RG21 2.2L not mixed in
- Shell/lube out (none in P700 pack)
"""
from __future__ import annotations

import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils.dataframe import dataframe_to_rows

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DERIVED = ROOT / "01_data/00_derived"
PRICING = ROOT / "01_data/01_Pricing"
STAMP = "20260812"

P700_LONG = DERIVED / f"apl_pn_list_P700_{STAMP}.csv"
ITUK_LONG = DERIVED / f"apl_pn_list_ITUK_{STAMP}.csv"
UNIQUE = DERIVED / f"apl_pn_list_unique_{STAMP}.csv"

OUT_XLSX = PRICING / f"UTI_P700_Recommended_Parts_List_{STAMP}.xlsx"
OUT_CSV = PRICING / f"UTI_P700_Recommended_Parts_List_{STAMP}.csv"
OUT_MD = PRICING / f"UTI_P700_Recommended_Parts_List_{STAMP}_ADVISE.md"
OUT_META = PRICING / f"UTI_P700_Recommended_Parts_List_{STAMP}.meta.json"
OUT_DERIVED_CSV = DERIVED / f"uti_p700_recommended_parts_list_{STAMP}.csv"

# Volume context (Jerome): no mix breakdown
CY2025_UNITS = 800
CY2026_UNITS = 1000
SCALE = CY2026_UNITS / CY2025_UNITS  # 1.25

# Source priority for dedupe (lower = preferred when filling description/price)
SOURCE_RANK = {
    "initial_PRD": 0,
    "accessories_ITUK_feedback": 1,
    "accessories_2026": 2,
    "VL27_recommended": 3,
    "body_P700": 4,
    "VL27_all_parts": 90,
    "body_old_N75": 99,
}

WEAR_FAM = re.compile(
    r"\b(filter|brake|clutch|sensor|scr_dpd|turbo|injector|belt)\b", re.I
)
NEW_ONLY_HINT = re.compile(
    r"\b(ISIM|DCT|ADAS|BSIS|DWS|TSR|TPMS|LED|HARNESS|CONTROLLER|ECU)\b", re.I
)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sanitize_xlsx_for_excel_desktop(path: Path) -> None:
    with zipfile.ZipFile(path, "r") as zin:
        files = {name: zin.read(name) for name in zin.namelist()}
    wb_xml = files["xl/workbook.xml"].decode("utf-8")
    wb_xml = re.sub(r"<workbookProtection\b[^/]*/>", "", wb_xml)
    wb_xml = re.sub(
        r"<workbookProtection\b[^>]*>.*?</workbookProtection>",
        "",
        wb_xml,
        flags=re.DOTALL,
    )
    files["xl/workbook.xml"] = wb_xml.encode("utf-8")
    styles = files["xl/styles.xml"].decode("utf-8")
    styles = styles.replace("<patternFill/>", '<patternFill patternType="none"/>')
    styles = styles.replace("<patternFill />", '<patternFill patternType="none"/>')
    styles = re.sub(r'rgb="00([0-9A-Fa-f]{6})"', r'rgb="FF\1"', styles)
    styles = re.sub(r'\s+pivotButton="0"', "", styles)
    styles = re.sub(r'\s+quotePrefix="0"', "", styles)
    files["xl/styles.xml"] = styles.encode("utf-8")
    rels = files["xl/_rels/workbook.xml.rels"].decode("utf-8")
    rels = rels.replace('Target="/xl/worksheets/', 'Target="worksheets/')
    rels = rels.replace('Target="/xl/theme/', 'Target="theme/')
    rels = rels.replace('Target="/xl/styles.xml"', 'Target="styles.xml"')
    rels = rels.replace('Target="/xl/sharedStrings.xml"', 'Target="sharedStrings.xml"')
    files["xl/_rels/workbook.xml.rels"] = rels.encode("utf-8")
    tmp = path.with_suffix(".sanitize.tmp.xlsx")
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for name, data in files.items():
            zout.writestr(name, data)
    tmp.replace(path)


def qualitative_priority(extra_tags: set[str], family: str, desc: str) -> str:
    """P0 first-stock / P1 wear / P2 body / P3 other recommended — not qty."""
    if "initial_PRD" in extra_tags or any(t.startswith("accessories") for t in extra_tags):
        return "P0_first_stock"
    if "body_P700" in extra_tags or (family and "body" in family.lower()):
        return "P2_body"
    if family and WEAR_FAM.search(family):
        return "P1_wear"
    if desc and NEW_ONLY_HINT.search(desc):
        return "P0_first_stock"
    return "P3_other_recommended"


def book_b_bucket(extra_tags: set[str], family: str, desc: str, in_ituk: bool) -> str:
    if any(t.startswith("accessories") for t in extra_tags):
        return "P700_new_seed_accessory"
    if "initial_PRD" in extra_tags and not in_ituk:
        return "P700_new_seed_prd"
    if desc and NEW_ONLY_HINT.search(desc):
        return "P700_new_only_hint"
    if family and WEAR_FAM.search(family):
        return "P700_carryover_wear"
    if "body_P700" in extra_tags or (family and "body" in family.lower()):
        return "P700_body"
    return "P700_carryover_or_launch"


def dedupe_recommended(df: pd.DataFrame, ituk_set: set[str]) -> pd.DataFrame:
    """Keep recommended-source rows only; one row per PN."""
    rec_extras = {
        "VL27_recommended",
        "initial_PRD",
        "accessories_2026",
        "accessories_ITUK_feedback",
        "body_P700",
    }
    sub = df[df["extra"].isin(rec_extras)].copy()
    sub["_rank"] = sub["extra"].map(lambda x: SOURCE_RANK.get(x, 50))
    # Prefer non-empty price, then better source rank, then longer description
    sub["_has_price"] = (sub["price_raw"].astype(str).str.strip() != "").astype(int)
    sub["_desc_len"] = sub["description"].astype(str).str.len()
    sub = sub.sort_values(
        ["part_number", "_rank", "_has_price", "_desc_len"],
        ascending=[True, True, False, False],
    )

    rows = []
    for pn, g in sub.groupby("part_number", sort=True):
        first = g.iloc[0]
        extras = set(g["extra"].astype(str))
        files = sorted(set(g["source_file"].astype(str)))
        markets = sorted({m for m in g["market"].astype(str) if m})
        dbs = sorted({d for d in g["db"].astype(str) if d})
        # Prefer accessory EUR price if any row has it
        price_raw, price_label, price_flag = "", "", ""
        for _, r in g.iterrows():
            if str(r.get("price_label", "")).startswith("accessory") and str(r["price_raw"]).strip():
                price_raw = str(r["price_raw"]).strip()
                price_label = str(r["price_label"])
                price_flag = str(r.get("price_flag", "") or "")
                break
        if not price_raw:
            for _, r in g.iterrows():
                if str(r["price_raw"]).strip():
                    price_raw = str(r["price_raw"]).strip()
                    price_label = str(r.get("price_label", "") or "")
                    price_flag = str(r.get("price_flag", "") or "")
                    break
        desc = str(first["description"] or "")
        if not desc:
            descs = g.loc[g["description"].astype(str).str.len() > 0, "description"]
            desc = str(descs.iloc[0]) if len(descs) else ""
        fam = str(first.get("family_hint") or "")
        in_ituk = pn in ituk_set
        tags = extras
        roles = []
        if "VL27_recommended" in tags:
            roles.append("VL27_Belgium_recommended")
        if "initial_PRD" in tags:
            roles.append("ITUK_P700_initial_PRD")
        if any(t.startswith("accessories") for t in tags):
            roles.append("accessories_list")
        if "body_P700" in tags:
            roles.append("body_P700_sample")
        notes = []
        if in_ituk:
            notes.append("Also in ITUK APL")
        if "accessories_ITUK_feedback" in tags and "accessories_2026" in tags:
            notes.append("Accessory in both base + ITUK feedback lists")
        if price_label == "body_fob_eur_raw":
            notes.append("Body FOB sample — small compare sheet, not full catalogue")
        if not price_raw:
            notes.append("No usable price on recommended sources")
        shell = int(g["shell_lube_out"].astype(int).max()) if "shell_lube_out" in g else 0
        if shell:
            continue  # Shell/lube out
        rows.append(
            {
                "part_number": pn,
                "description": desc,
                "source_file": "|".join(files),
                "source_roles": "|".join(roles),
                "family_hint": fam,
                "price_raw": price_raw,
                "price_label_currency_basis": price_label,
                "price_flag": price_flag,
                "list_flag": "recommended",
                "qualitative_priority": qualitative_priority(tags, fam, desc),
                "book_b_bucket_hint": book_b_bucket(tags, fam, desc, in_ituk),
                "in_ituk_apl": int(in_ituk),
                "market": "|".join(markets),
                "db_tag": "|".join(dbs),
                "n_source_files": len(files),
                "notes": "; ".join(notes),
                "volume_note": "No per-PN qty — scale network demand index ×1.25 only (see Volume_context)",
            }
        )
    out = pd.DataFrame(rows)
    # Stable sort: priority then PN
    prio_order = {
        "P0_first_stock": 0,
        "P1_wear": 1,
        "P2_body": 2,
        "P3_other_recommended": 3,
    }
    out["_p"] = out["qualitative_priority"].map(lambda x: prio_order.get(x, 9))
    out = out.sort_values(["_p", "part_number"]).drop(columns=["_p"]).reset_index(drop=True)
    return out


def catalogue_all_vl27(df: pd.DataFrame, rec_pns: set[str], ituk_set: set[str]) -> pd.DataFrame:
    """VL27 All Parts — catalogue reference; flag which are also recommended."""
    sub = df[df["extra"] == "VL27_all_parts"].copy()
    sub = sub.sort_values(["part_number", "description"])
    rows = []
    for pn, g in sub.groupby("part_number", sort=True):
        first = g.iloc[0]
        desc = str(first["description"] or "")
        fam = str(first.get("family_hint") or "")
        in_rec = pn in rec_pns
        rows.append(
            {
                "part_number": pn,
                "description": desc,
                "source_file": str(first["source_file"]),
                "source_roles": "VL27_Belgium_all_parts",
                "family_hint": fam,
                "price_raw": "",
                "price_label_currency_basis": "",
                "price_flag": "",
                "list_flag": "recommended" if in_rec else "catalogue_all",
                "also_on_recommended_sheet": int(in_rec),
                "in_ituk_apl": int(pn in ituk_set),
                "notes": "Full VL27 All Parts catalogue — prefer Recommended sheet for shortlist",
            }
        )
    return pd.DataFrame(rows)


def write_sheet(ws, df: pd.DataFrame, header_fill: str = "1F4E79") -> None:
    for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True), 1):
        for c_idx, val in enumerate(row, 1):
            cell = ws.cell(row=r_idx, column=c_idx, value=val if val is not None else "")
            if r_idx == 1:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill("solid", fgColor=header_fill)
                cell.alignment = Alignment(wrap_text=True, vertical="center")
            else:
                cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    # Reasonable widths
    for col in ws.columns:
        letter = col[0].column_letter
        maxlen = 12
        for cell in col[:80]:
            maxlen = max(maxlen, min(48, len(str(cell.value or ""))))
        ws.column_dimensions[letter].width = maxlen + 2


def main() -> None:
    p700 = pd.read_csv(P700_LONG, dtype=str).fillna("")
    for col in ("shell_lube_out",):
        if col in p700.columns:
            p700[col] = pd.to_numeric(p700[col], errors="coerce").fillna(0).astype(int)

    ituk = pd.read_csv(ITUK_LONG, dtype=str, usecols=["part_number"]).fillna("")
    ituk_set = set(ituk["part_number"].astype(str))

    rec = dedupe_recommended(p700, ituk_set)
    cat = catalogue_all_vl27(p700, set(rec["part_number"]), ituk_set)

    # Priority counts
    prio_counts = rec["qualitative_priority"].value_counts().to_dict()
    role_counts = (
        rec["source_roles"]
        .str.split("|")
        .explode()
        .value_counts()
        .to_dict()
        if len(rec)
        else {}
    )

    # --- Excel ---
    wb = Workbook()

    # Advise first (shared + clear need/continue)
    ws_a = wb.active
    ws_a.title = "Advise"
    advise_lines = [
        ["UTI P700 recommended parts list — advise brief"],
        ["Built (UTC)", utc_now()],
        ["Scope", "UTI P700 only — do not blend with UMI / IDS Israel"],
        ["RG21 / D-Max 2.2L", "Separate LCV story — not mixed into this list"],
        ["Shell / lube", "Out of scope (none flagged in these P700 APL rows)"],
        [],
        ["What we built"],
        [
            "Recommended sheet",
            f"{len(rec)} unique PNs from VL27 Recommended + ITUK P700 initial PRD + accessories + body P700 sample",
        ],
        [
            "How recommended was chosen",
            "Prefer VL27 'Recommended Class', PRD first-stock, accessory price lists, and P700 body sample. VL27 'All Parts List' kept only on Catalogue_all_VL27 (not the shortlist).",
        ],
        ["Catalogue_all_VL27", f"{len(cat)} unique PNs — full VL27 All Parts for reference"],
        ["ITUK APL overlap (recommended)", int(rec["in_ituk_apl"].sum())],
        ["Volume context", f"{CY2025_UNITS} CY2025 → {CY2026_UNITS} CY2026 units (×{SCALE:.2f}) — no per-PN qty invented"],
        [],
        ["Can continue building without detail"],
        ["1", "PN universe from APL (recommended + catalogue reference)"],
        ["2", "Family prioritisation (P0 first-stock / P1 wear / P2 body / P3 other) — qualitative only"],
        ["3", "Book B forecast weight hooks: growth 1.25 on UTI P700 seed € when ambition % is set"],
        ["4", "Crosswalk to ITUK P700 / ITUK APL overlap (in_ituk_apl column)"],
        ["5", "New-only hints (ISIM/ADAS/LED/cab) vs carryover wear families from description heuristics"],
        [],
        ["Still need (ask Jerome / UTI)"],
        ["1", "Model mix (3.5t / 6.5t / 7.5t / 13.5t) or even rough %"],
        ["2", "Gearbox mix (ISIM DCT vs manual) if known"],
        ["3", "Which market the 800 / 1000 are (Israel UTI only?)"],
        ["4", "Preferred currency / price basis for the list (FCA accessory vs PR00)"],
        ["5", "Ambition % for Book B"],
        [],
        ["Do not invent"],
        ["—", "Per-PN order qty or € demand from thin air"],
        ["—", "Equal-mix unit splits as if they were real forecasts"],
    ]
    for r_idx, row in enumerate(advise_lines, 1):
        for c_idx, val in enumerate(row, 1):
            cell = ws_a.cell(row=r_idx, column=c_idx, value=val)
            if r_idx == 1 or (len(row) == 1 and val):
                cell.font = Font(bold=True, size=12 if r_idx == 1 else 11)
            if c_idx == 1 and len(row) >= 2 and str(row[0]) in {
                "What we built",
                "Can continue building without detail",
                "Still need (ask Jerome / UTI)",
                "Do not invent",
            }:
                cell.font = Font(bold=True)
    ws_a.column_dimensions["A"].width = 36
    ws_a.column_dimensions["B"].width = 100

    ws_r = wb.create_sheet("Recommended")
    write_sheet(ws_r, rec)

    ws_v = wb.create_sheet("Volume_context")
    vol_rows = [
        ["Metric", "Value", "Note"],
        ["CY2025 units (UTI P700 context)", CY2025_UNITS, "Jerome — no detailed mix"],
        ["CY2026 units (plan)", CY2026_UNITS, "Jerome — no detailed mix"],
        ["Growth / scale factor", round(SCALE, 4), "1000/800 = 1.25"],
        [
            "How to use on parts",
            "Apply ×1.25 to network parc / demand index or Book B seed € for UTI P700",
            "Not a per-PN quantity",
        ],
        [
            "Equal-mix illustration",
            "If mix were equal across models, each share would grow ×1.25 — illustrative only",
            "Do NOT treat as a forecast",
        ],
        [
            "Qualitative priority (families)",
            "P0 first-stock (PRD/accessories) · P1 wear · P2 body · P3 other recommended",
            "From APL role / description — not fake qty",
        ],
        ["Market confirmation", "TBD — confirm Israel UTI only?", "Still need from Jerome"],
        ["UTI ≠ UMI", "This list is UTI P700 only", "Never blend with IDS Israel / UMI"],
    ]
    for r_idx, row in enumerate(vol_rows, 1):
        for c_idx, val in enumerate(row, 1):
            cell = ws_v.cell(row=r_idx, column=c_idx, value=val)
            if r_idx == 1:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill("solid", fgColor="1F4E79")
    ws_v.column_dimensions["A"].width = 40
    ws_v.column_dimensions["B"].width = 55
    ws_v.column_dimensions["C"].width = 40
    ws_v.freeze_panes = "A2"

    # Family priority summary (qualitative)
    ws_f = wb.create_sheet("Family_priority")
    fam = (
        rec.groupby(["qualitative_priority", "family_hint"], dropna=False)
        .size()
        .reset_index(name="unique_pn")
        .sort_values(["qualitative_priority", "unique_pn"], ascending=[True, False])
    )
    write_sheet(ws_f, fam, header_fill="2E7D32")

    ws_c = wb.create_sheet("Catalogue_all_VL27")
    write_sheet(ws_c, cat, header_fill="5D6D7E")

    wb.save(OUT_XLSX)
    sanitize_xlsx_for_excel_desktop(OUT_XLSX)

    # CSV (recommended only)
    rec.to_csv(OUT_CSV, index=False)
    rec.to_csv(OUT_DERIVED_CSV, index=False)

    # Sibling advise MD (internal OK)
    md = f"""# UTI P700 recommended parts list — advise

**internal notes · {utc_now()} · UTI ≠ UMI · Shell out · RG21 not mixed**

## Deliverables

| File | Role |
|------|------|
| `{OUT_XLSX.name}` | Excel: Advise · Recommended · Volume_context · Family_priority · Catalogue_all_VL27 |
| `{OUT_CSV.name}` | Recommended sheet only (CSV) |
| `{OUT_DERIVED_CSV.name}` | Same CSV under derived |

## Counts

- **Recommended unique PN:** {len(rec)}
- **Catalogue_all VL27 unique PN:** {len(cat)}
- **Recommended ∩ ITUK APL:** {int(rec['in_ituk_apl'].sum())}
- **Priority split:** {json.dumps(prio_counts, ensure_ascii=True)}
- **Source roles (exploded):** {json.dumps(role_counts, ensure_ascii=True)}

## How “recommended” was chosen

1. **VL27 Belgium — Recommended Class** (not All Parts)  
2. **ITUK P700 initial PRD** (first-stock)  
3. **Accessories** 2026 list + ITUK feedback (FCA/EXW EUR where printed)  
4. **Body P700** sample rows only (not old N75 column)  

VL27 **All Parts** stays on `Catalogue_all_VL27` with `list_flag=catalogue_all` unless the PN is also on Recommended.

## Volume

- **800** CY2025 → **1000** CY2026 units → scale **1.25** on network demand index / Book B seed €  
- **No per-PN qty** invented

## Can continue without detail

- PN universe from APL  
- Family prioritisation (P0/P1/P2/P3 qualitative)  
- Book B growth hook **1.25** on UTI P700 seed € once ambition % is set  
- ITUK APL overlap crosswalk  

## Still need (ask Jerome)

1. Model mix (3.5t / 6.5t / 7.5t / 13.5t) or rough %  
2. Gearbox mix (ISIM DCT vs manual) if known  
3. Market for 800/1000 (Israel UTI only?)  
4. Preferred price basis (FCA accessory vs PR00)  
5. Ambition % for Book B  
"""
    OUT_MD.write_text(md, encoding="utf-8")

    meta = {
        "built_utc": utc_now(),
        "stamp": STAMP,
        "scope": "UTI_P700_only",
        "outputs": {
            "xlsx": str(OUT_XLSX),
            "csv": str(OUT_CSV),
            "derived_csv": str(OUT_DERIVED_CSV),
            "advise_md": str(OUT_MD),
        },
        "counts": {
            "recommended_unique_pn": int(len(rec)),
            "catalogue_vl27_unique_pn": int(len(cat)),
            "recommended_in_ituk_apl": int(rec["in_ituk_apl"].sum()),
            "priority": {k: int(v) for k, v in prio_counts.items()},
            "source_roles": {k: int(v) for k, v in role_counts.items()},
        },
        "volume": {
            "cy2025_units": CY2025_UNITS,
            "cy2026_units": CY2026_UNITS,
            "scale_factor": SCALE,
            "per_pn_qty": None,
        },
        "recommended_sources": sorted(SOURCE_RANK.keys()),
        "caveats": [
            "No per-PN quantity invented from 800/1000 unit totals",
            "UTI ≠ UMI — do not blend with IDS Israel",
            "RG21 2.2L not included in this list",
            "Accessory EUR = FCA/EXW as printed; body FOB = small sample",
            "Family / priority heuristics from description — not official PMS categories",
        ],
    }
    OUT_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps(meta["counts"], indent=2))
    print("Wrote", OUT_XLSX)
    print("Wrote", OUT_CSV)


if __name__ == "__main__":
    main()
