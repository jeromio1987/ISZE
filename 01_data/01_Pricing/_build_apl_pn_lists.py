"""
Build canonical APL / P700 / RG21 PN lists for forecast-weighted ambition (Book B).

internal · 2026-08-12 · no inventing · Shell/lube flagged out of Book B seeds.
Does not send mail, ship packs, or run alloc.
"""
from __future__ import annotations

import hashlib
import json
import re
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import openpyxl
import pandas as pd
import xlrd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
ITUK_DIR = ROOT / "01_data/90_INBOX/APL_ITUK_202607"
UTI_DIR = ROOT / "01_data/90_INBOX/APL_UTI_P700"
SUZUKI_XLS = ROOT / "01_data/90_INBOX/suzuki_pms_mail_pull/zip_20260714_1037/20260714_1037"
OUT_DERIVED = ROOT / "01_data/00_derived"
OUT_PRICING = ROOT / "01_data/01_Pricing"
WORK = OUT_PRICING / "_raw/apl_build_20260812"
STAMP = "20260812"

# Currency / price labels — keep raw; flag ambiguity
BP_FLAG = "BP_raw_currency_unclear"  # Suzuki/RG21 B/P — often JPY-like, not labelled
ACC_PRICE_LABEL = "accessory_list_fca_exw_eur"
BODY_FOB_LABEL = "body_fob_eur_raw"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def md5_file(p: Path) -> str:
    h = hashlib.md5()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_pn(raw) -> str | None:
    """Return 10-digit zero-padded PN, or None if not usable."""
    if raw is None:
        return None
    s = str(raw).strip()
    if not s or s.lower() in {"nan", "none", "-", "#n/a"}:
        return None
    # dashed catalogue form e.g. 1-8672-4050-1
    digits = re.sub(r"\D", "", s)
    if not digits:
        return None
    if len(digits) > 12:
        return None
    if len(digits) < 7:
        return None
    # Isuzu catalogue PNs are typically 10 digits
    if len(digits) <= 10:
        return digits.zfill(10)
    # 11–12: keep as-is padded only if already long (rare); skip inventing trim
    return digits


def expand_slash_pns(raw) -> list[str]:
    """Handle forms like 7475056740/60 → 7475056740 + 7475056760 when pattern clear."""
    if raw is None:
        return []
    s = str(raw).strip()
    m = re.match(r"^(\d{8,10})/(\d{2})$", s.replace(" ", ""))
    if m:
        base, suffix = m.group(1), m.group(2)
        p1 = normalize_pn(base)
        p2 = normalize_pn(base[:-2] + suffix) if len(base) >= 2 else None
        out = []
        for p in (p1, p2):
            if p and p not in out:
                out.append(p)
        return out
    p = normalize_pn(s)
    return [p] if p else []


# Do NOT match part-name "SHELL; CYL…" (clutch booster housing) or "HOSE; ATF" (lines).
# Lube / Shell oils only.
SHELL_LUBE_DESC = re.compile(
    r"(LUBRICANT|LUBRICATION|"
    r"\bENGINE OIL\b|\bGEAR OIL\b|\bDIFF OIL\b|\bAXLE OIL\b|"
    r"\bTRANSMISSION OIL\b|\bMOTOR OIL\b|"
    r"\bFLUID;?\s*ATF\b|\bATF;?\s*FLUID\b|\bOIL;?\s*ATF\b|"
    r"SHELL\s+(OIL|LUBE|LUBRICANT|HELIX)|"
    r"\bOIL\s+CAN\b|\bGREASE\s+CAN\b)",
    re.I,
)
SHELL_PN_PREFIX = re.compile(r"^5500")  # Shell oils convention in ISZE


def is_shell_lube(pn: str | None, desc: str | None) -> bool:
    if pn and SHELL_PN_PREFIX.match(pn):
        return True
    if not desc:
        return False
    # Caution plates / labels mentioning oil are not lube SKUs
    if re.search(r"\b(PLATE|LABEL|STICKER|DECAL|TAG)\b", desc, re.I):
        return False
    if SHELL_LUBE_DESC.search(desc):
        return True
    return False


FAMILY_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("filter", re.compile(r"\bFILTER\b|ELEMENT;?\s*(OIL|FUEL|AIR|ACL)|CARTRIDGE", re.I)),
    ("brake", re.compile(r"\b(BRAKE|PAD KIT|DISC BRK|CALIPER|ROTOR|SHOES?)\b", re.I)),
    ("clutch", re.compile(r"\bCLUTCH\b", re.I)),
    ("sensor", re.compile(r"\bSENSOR\b|NOX|NOx", re.I)),
    ("scr_dpd", re.compile(r"\b(SCR|DPD|DEF|UREA|ADBLUE|AD BLUE)\b", re.I)),
    ("turbo", re.compile(r"\bTURBO", re.I)),
    ("injector", re.compile(r"\bINJECTOR\b", re.I)),
    ("body", re.compile(r"\b(BUMPER|GRILLE|PANEL|DOOR|CAB|MOLDING|FENDER|HOOD)\b", re.I)),
    ("lighting", re.compile(r"\b(LAMP|LED|HEADLAMP|TAIL|TURN SIGNAL)\b", re.I)),
    ("electrical", re.compile(r"\b(HARNESS|SWITCH|SOCKET|RELAY|ECU|CONTROLLER)\b", re.I)),
    ("belt", re.compile(r"\bBELT\b", re.I)),
    ("gasket_seal", re.compile(r"\b(GASKET|SEAL|O-RING|ORING)\b", re.I)),
]


def family_hint(desc: str | None) -> str:
    if not desc:
        return ""
    hits = [name for name, rx in FAMILY_RULES if rx.search(desc)]
    return "|".join(hits[:3])


def row(
    *,
    part_number: str,
    description: str = "",
    source_file: str,
    source_pack: str,
    market: str = "",
    db: str = "",
    price_raw: str = "",
    price_label: str = "",
    price_flag: str = "",
    family: str = "",
    shell_lube: bool = False,
    extra: str = "",
    fig: str = "",
    key: str = "",
    vehicle_code: str = "",
) -> dict:
    desc = (description or "").strip()
    fam = family or family_hint(desc)
    shell = shell_lube or is_shell_lube(part_number, desc)
    return {
        "part_number": part_number,
        "description": desc,
        "source_file": source_file,
        "source_pack": source_pack,
        "market": market,
        "db": db,
        "price_raw": price_raw,
        "price_label": price_label,
        "price_flag": price_flag,
        "family_hint": fam,
        "shell_lube_out": int(shell),
        "fig": fig,
        "key": key,
        "vehicle_code": vehicle_code,
        "extra": extra,
    }


def parse_suzuki_xls(path: Path, source_pack: str, market: str, db: str) -> list[dict]:
    rows: list[dict] = []
    # xlrd warns on OLE2 inconsistency — ignore
    book = xlrd.open_workbook(str(path), formatting_info=False)
    sh = book.sheet_by_index(0)
    headers = [str(sh.cell_value(0, c)).strip() for c in range(sh.ncols)]
    col = {h.upper(): i for i, h in enumerate(headers)}
    need = {"PNO", "PARTS NAME"}
    if not need.issubset(col):
        return rows
    for r in range(1, sh.nrows):
        pno = sh.cell_value(r, col["PNO"])
        pn = normalize_pn(pno)
        if not pn:
            continue
        name = str(sh.cell_value(r, col["PARTS NAME"])).strip()
        bp = sh.cell_value(r, col["BP"]) if "BP" in col else ""
        code = str(sh.cell_value(r, col["CODE"])).strip() if "CODE" in col else ""
        fig = str(sh.cell_value(r, col["FIG"])).strip() if "FIG" in col else ""
        key = str(sh.cell_value(r, col["KEY"])).strip() if "KEY" in col else ""
        price_raw = ""
        if bp != "" and bp is not None:
            try:
                price_raw = str(float(bp)) if not isinstance(bp, str) else bp
            except Exception:
                price_raw = str(bp)
        rows.append(
            row(
                part_number=pn,
                description=name,
                source_file=path.name,
                source_pack=source_pack,
                market=market,
                db=db,
                price_raw=price_raw,
                price_label="BP",
                price_flag=BP_FLAG if price_raw else "",
                fig=fig,
                key=key,
                vehicle_code=code,
            )
        )
    return rows


def parse_rg21_rl(path: Path, market: str) -> list[dict]:
    rows: list[dict] = []
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    if "RL" not in wb.sheetnames:
        wb.close()
        return rows
    ws = wb["RL"]
    # header is row 2 (1-index) → index 1 in 0-based iter; row0 is OMC codes
    it = ws.iter_rows(values_only=True)
    next(it, None)  # skip OMC header row
    hdr = next(it, None)
    if not hdr:
        wb.close()
        return rows
    headers = [str(c).strip() if c is not None else "" for c in hdr]
    col = {h.upper(): i for i, h in enumerate(headers)}
    # expect P/NO. and P/NAME
    pno_i = col.get("P/NO.") or col.get("P/NO") or col.get("PNO")
    name_i = col.get("P/NAME") or col.get("PARTS NAME") or col.get("PNAME")
    bp_i = col.get("B/P") or col.get("BP")
    fig_i = col.get("FIG")
    key_i = col.get("KEY")
    if pno_i is None:
        wb.close()
        return rows
    for r in it:
        if not r or pno_i >= len(r):
            continue
        pn = normalize_pn(r[pno_i])
        if not pn:
            continue
        name = str(r[name_i]).strip() if name_i is not None and name_i < len(r) and r[name_i] else ""
        bp = r[bp_i] if bp_i is not None and bp_i < len(r) else ""
        price_raw = "" if bp is None or bp == "" else str(bp)
        fig = str(r[fig_i]).strip() if fig_i is not None and fig_i < len(r) and r[fig_i] else ""
        key = str(r[key_i]).strip() if key_i is not None and key_i < len(r) and r[key_i] else ""
        rows.append(
            row(
                part_number=pn,
                description=name,
                source_file=path.name,
                source_pack="RG21_2.2L",
                market=market,
                db="ITUK",
                price_raw=price_raw,
                price_label="B/P",
                price_flag=BP_FLAG if price_raw else "",
                fig=fig,
                key=key,
                extra="RL_sheet",
            )
        )
    wb.close()
    return rows


def parse_accessories(path: Path, tag: str) -> list[dict]:
    rows: list[dict] = []
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    # find header row with P/No.
    header_idx = None
    headers = None
    data_rows = []
    for i, r in enumerate(ws.iter_rows(values_only=True)):
        vals = [str(c).strip() if c is not None else "" for c in r]
        upper = [v.upper() for v in vals]
        if header_idx is None and any(v in {"P/NO.", "P/NO", "PNO"} for v in upper):
            header_idx = i
            headers = vals
            continue
        if header_idx is not None:
            data_rows.append(r)
    wb.close()
    if headers is None:
        return rows
    col = {h.upper(): i for i, h in enumerate(headers)}
    pno_i = col.get("P/NO.") or col.get("P/NO") or col.get("PNO")
    name_i = col.get("PARTS NAME") or col.get("PART NAME")
    price_i = None
    for k, i in col.items():
        if "LIST PRICE" in k or "FCA" in k or "EXW" in k:
            price_i = i
            break
    if pno_i is None:
        return rows
    for r in data_rows:
        if not r or pno_i >= len(r):
            continue
        raw_pn = r[pno_i]
        pns = expand_slash_pns(raw_pn)
        if not pns:
            # try dashed
            pn = normalize_pn(raw_pn)
            pns = [pn] if pn else []
        if not pns:
            continue
        name = str(r[name_i]).strip() if name_i is not None and name_i < len(r) and r[name_i] else ""
        price_raw = ""
        if price_i is not None and price_i < len(r) and r[price_i] is not None:
            price_raw = str(r[price_i]).strip()
        for pn in pns:
            rows.append(
                row(
                    part_number=pn,
                    description=name,
                    source_file=path.name,
                    source_pack="P700",
                    market="UK",
                    db="UTI",
                    price_raw=price_raw,
                    price_label=ACC_PRICE_LABEL,
                    price_flag="" if price_raw else "",
                    family=family_hint(name) or "accessory",
                    extra=tag,
                )
            )
    return rows


def parse_vl27(path: Path) -> list[dict]:
    rows: list[dict] = []
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    for sheet, tag in (("All Parts List", "all_parts"), ("Recommended Class", "recommended")):
        if sheet not in wb.sheetnames:
            continue
        ws = wb[sheet]
        it = ws.iter_rows(values_only=True)
        # find header with PNO
        headers = None
        for r in it:
            vals = [str(c).strip() if c is not None else "" for c in r]
            upper = [v.upper() for v in vals]
            if "PNO" in upper:
                headers = vals
                break
        if not headers:
            continue
        col = {h.upper(): i for i, h in enumerate(headers)}
        pno_i = col.get("PNO")
        name_i = col.get("PARTS NAME") or col.get("NAME")
        fig_i = col.get("FIG")
        key_i = col.get("KEY")
        for r in it:
            if not r or pno_i is None or pno_i >= len(r):
                continue
            pn = normalize_pn(r[pno_i])
            if not pn:
                continue
            name = str(r[name_i]).strip() if name_i is not None and name_i < len(r) and r[name_i] else ""
            fig = str(r[fig_i]).strip() if fig_i is not None and fig_i < len(r) and r[fig_i] else ""
            key = str(r[key_i]).strip() if key_i is not None and key_i < len(r) and r[key_i] else ""
            rows.append(
                row(
                    part_number=pn,
                    description=name,
                    source_file=path.name,
                    source_pack="P700",
                    market="Belgium",
                    db="IBX",
                    fig=fig,
                    key=key,
                    extra=f"VL27_{tag}",
                )
            )
    wb.close()
    return rows


def parse_prd(path: Path) -> list[dict]:
    rows: list[dict] = []
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    it = ws.iter_rows(values_only=True)
    hdr = next(it, None)
    if not hdr:
        wb.close()
        return rows
    headers = [str(c).strip() if c is not None else "" for c in hdr]
    col = {h.upper(): i for i, h in enumerate(headers)}
    pno_i = col.get("ORDER MATERIAL")
    name_i = col.get("DESCRIPTION")
    if pno_i is None:
        wb.close()
        return rows
    for r in it:
        if not r or pno_i >= len(r):
            continue
        pn = normalize_pn(r[pno_i])
        if not pn:
            continue
        name = str(r[name_i]).strip() if name_i is not None and name_i < len(r) and r[name_i] else ""
        rows.append(
            row(
                part_number=pn,
                description=name,
                source_file=path.name,
                source_pack="P700",
                market="UK",
                db="ITUK",
                extra="initial_PRD",
            )
        )
    wb.close()
    return rows


def parse_body_parts(path: Path) -> list[dict]:
    """Hebrew SAP dump + small OLD vs P700 FOB compare sheet — extract carefully."""
    rows: list[dict] = []
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    # Prefer the comparison sheet (usually sheet 2) with English labels N/7.5 / P700
    for sn in wb.sheetnames:
        ws = wb[sn]
        collected = list(ws.iter_rows(values_only=True))
        # detect compare layout: row0 has P700 somewhere
        if not collected:
            continue
        flat0 = " ".join(str(c) for c in (collected[0] or []) if c is not None).upper()
        if "P700" not in flat0 and "FOB" not in flat0:
            continue
        # columns: desc | old_pn | old_fob | p700_pn | p700_fob
        for r in collected[2:]:
            if not r:
                continue
            desc = str(r[0]).strip() if r[0] else ""
            old_pn_raw = r[1] if len(r) > 1 else None
            old_fob = r[2] if len(r) > 2 else None
            p700_raw = r[3] if len(r) > 3 else None
            p700_fob = r[4] if len(r) > 4 else None
            for raw, fob, which in (
                (old_pn_raw, old_fob, "old_N75"),
                (p700_raw, p700_fob, "P700"),
            ):
                for pn in expand_slash_pns(raw):
                    price_raw = "" if fob is None or fob == "" else str(fob)
                    rows.append(
                        row(
                            part_number=pn,
                            description=desc or which,
                            source_file=path.name,
                            source_pack="P700",
                            market="Israel",
                            db="UTI",
                            price_raw=price_raw,
                            price_label=BODY_FOB_LABEL,
                            price_flag="body_compare_sheet_small_sample",
                            family="body",
                            extra=f"body_{which}",
                        )
                    )
    wb.close()
    return rows


def unpack_vk05_dgr() -> Path:
    zpath = ITUK_DIR / "2026-07-13_ITUK_VK05_UK_D_Gr.zip"
    dest = WORK / "vk05_uk_d_gr"
    dest.mkdir(parents=True, exist_ok=True)
    marker = dest / "_extracted.ok"
    if not marker.exists():
        with zipfile.ZipFile(zpath) as z:
            z.extractall(dest)
        marker.write_text("ok", encoding="utf-8")
    # find folder with xls
    xls_dirs = [p for p in dest.rglob("*.xls")]
    if not xls_dirs:
        raise FileNotFoundError("VK05 unpack produced no .xls")
    return xls_dirs[0].parent


def dedupe_unique(df: pd.DataFrame) -> pd.DataFrame:
    """One row per PN; keep first non-shell-preferring description; list all sources."""
    # Prefer Book-B-eligible (shell_lube_out==0) as first if possible
    df = df.copy()
    df["_ord"] = df["shell_lube_out"].astype(int)
    df = df.sort_values(["part_number", "_ord", "source_pack", "source_file"])
    groups = []
    for pn, g in df.groupby("part_number", sort=False):
        first = g.iloc[0]
        packs = sorted(set(g["source_pack"].astype(str)))
        files = sorted(set(g["source_file"].astype(str)))
        markets = sorted({m for m in g["market"].astype(str) if m})
        dbs = sorted({d for d in g["db"].astype(str) if d})
        # best description: longest non-empty among non-shell first
        descs = g.loc[g["description"].astype(str).str.len() > 0, "description"].astype(str)
        desc = descs.iloc[0] if len(descs) else ""
        # price: prefer labelled accessory EUR, else first non-empty
        price_raw, price_label, price_flag = "", "", ""
        for _, r in g.iterrows():
            if r["price_label"] == ACC_PRICE_LABEL and str(r["price_raw"]).strip():
                price_raw, price_label, price_flag = r["price_raw"], r["price_label"], r["price_flag"]
                break
        if not price_raw:
            for _, r in g.iterrows():
                if str(r["price_raw"]).strip():
                    price_raw, price_label, price_flag = r["price_raw"], r["price_label"], r["price_flag"]
                    break
        shell = int(g["shell_lube_out"].max())
        groups.append(
            {
                "part_number": pn,
                "description": desc,
                "source_pack_first": first["source_pack"],
                "source_file_first": first["source_file"],
                "source_packs": "|".join(packs),
                "source_files": "|".join(files),
                "n_sources": len(files),
                "market": "|".join(markets),
                "db": "|".join(dbs),
                "price_raw": price_raw,
                "price_label": price_label,
                "price_flag": price_flag,
                "family_hint": first["family_hint"] or family_hint(desc),
                "shell_lube_out": shell,
                "book_b_seed_ok": int(shell == 0),
            }
        )
    return pd.DataFrame(groups)


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    OUT_DERIVED.mkdir(parents=True, exist_ok=True)
    all_rows: list[dict] = []
    inventory: list[dict] = []

    # --- ITUK Suzuki APL (10 xls) ---
    suzuki_files = sorted(SUZUKI_XLS.glob("*.xls"))
    inventory.append(
        {
            "role": "ITUK_APL_Suzuki_VR05_DGr",
            "path": str(SUZUKI_XLS),
            "n_files": len(suzuki_files),
            "note": "Unpacked from 20260714_1037.zip (ITUK). Same zip also in UTI folder — skipped as UTI.",
        }
    )
    for f in suzuki_files:
        all_rows.extend(parse_suzuki_xls(f, "ITUK_APL", "UK", "ITUK"))

    # --- VK05 UK D-Gr (same schema; ITUK) ---
    vk05_dir = unpack_vk05_dgr()
    vk05_files = sorted(vk05_dir.glob("*.xls"))
    inventory.append(
        {
            "role": "ITUK_APL_VK05_UK_D_Gr",
            "path": str(ITUK_DIR / "2026-07-13_ITUK_VK05_UK_D_Gr.zip"),
            "n_files": len(vk05_files),
            "note": "Byte-identical copy exists under APL_UTI_P700 — counted once as ITUK.",
        }
    )
    for f in vk05_files:
        all_rows.extend(parse_suzuki_xls(f, "ITUK_APL", "UK", "ITUK"))

    # --- RG21 (= D-Max 2.2L) recommended lists ---
    rg21_files = [
        (ITUK_DIR / "2026-05-07_ITUK_RL_for_RG21_Norway_20251028.xlsx", "Norway"),
        (ITUK_DIR / "2026-07-01_ITUK_RL_for_RG21_Greece.xlsx", "Greece"),
    ]
    for path, market in rg21_files:
        inventory.append(
            {
                "role": "RG21_2.2L_RL",
                "path": str(path),
                "market": market,
                "note": "Sheet RL; B/P currency unclear (flagged).",
            }
        )
        all_rows.extend(parse_rg21_rl(path, market))

    # --- P700 real material ---
    acc = UTI_DIR / "2026-02-05_UTI_P700_RHD_P700_N-series_accessories_part_no_2026_price_list.xlsx"
    acc_fb = UTI_DIR / "2026-07-20_UTI_P700_RHD_P700_N-series_accessories_part_no_2026_price_list_-_ITUK_Feedback.xlsx"
    vl27 = UTI_DIR / "2026-05-20_UTI_P700_All_Parts_and_Recommended_Items_list_for_New_Project_VL27_Belgium_.xlsx"
    body = UTI_DIR / "2026-07-15_UTI_P700_body_parts_p-700.xlsx"
    prd = UTI_DIR / "2026-07-31_UTI_P700_ITUK_P700_initial_PRD.xlsx"

    for path, tag in ((acc, "accessories_2026"), (acc_fb, "accessories_ITUK_feedback")):
        inventory.append({"role": "P700_accessories", "path": str(path), "tag": tag})
        all_rows.extend(parse_accessories(path, tag))

    inventory.append(
        {
            "role": "P700_VL27_Belgium",
            "path": str(vl27),
            "note": "New project VL27 (IBX). Identical file also in ITUK folder — counted once as P700.",
        }
    )
    all_rows.extend(parse_vl27(vl27))

    inventory.append(
        {
            "role": "P700_body_parts",
            "path": str(body),
            "note": "Small OLD vs P700 FOB compare; Hebrew SAP sheet skipped for PN harvest.",
        }
    )
    all_rows.extend(parse_body_parts(body))

    inventory.append(
        {
            "role": "P700_ITUK_initial_PRD",
            "path": str(prd),
            "note": "Order Material = PN; first-stock PRD lines.",
        }
    )
    all_rows.extend(parse_prd(prd))

    # Explicit skips
    skips = [
        {
            "path": str(UTI_DIR / "2026-07-23_UTI_P700_20260714_1037.zip"),
            "reason": "MD5-identical to ITUK Suzuki APL zip — not a UTI-only list.",
        },
        {
            "path": str(UTI_DIR / "2026-05-28_UTI_P700_For_N-series.xlsx"),
            "reason": "FIGKEY + Name only — no part_number column.",
        },
        {
            "path": str(UTI_DIR / "2026-05-28_UTI_P700_For_F-series.xlsx"),
            "reason": "FIGKEY + Name only — no part_number column.",
        },
        {
            "path": str(UTI_DIR / "2026-05-12_UTI_P700_VK05_UK_B_Gr.zip"),
            "reason": "MD5-identical to ITUK VK05 B-Gr; D-Gr used instead for ITUK_APL.",
        },
        {
            "path": str(UTI_DIR / "2026-07-13_UTI_P700_VK05_UK_D_Gr.zip"),
            "reason": "MD5-identical to ITUK VK05 D-Gr — counted once under ITUK_APL.",
        },
    ]
    inventory.append({"role": "skipped", "items": skips})

    df = pd.DataFrame(all_rows)
    if df.empty:
        raise SystemExit("No rows parsed — abort")

    # Pack-specific long files
    paths_out: dict[str, Path] = {}
    for pack, name in (
        ("ITUK_APL", f"apl_pn_list_ITUK_{STAMP}.csv"),
        ("P700", f"apl_pn_list_P700_{STAMP}.csv"),
        ("RG21_2.2L", f"apl_pn_list_RG21_2.2L_{STAMP}.csv"),
    ):
        sub = df[df["source_pack"] == pack].copy()
        outp = OUT_DERIVED / name
        sub.to_csv(outp, index=False, encoding="utf-8-sig")
        paths_out[pack] = outp
        # also copy under Pricing for filing
        sub.to_csv(OUT_PRICING / name, index=False, encoding="utf-8-sig")

    # Combined long
    long_path = OUT_DERIVED / f"apl_pn_list_long_{STAMP}.csv"
    df.to_csv(long_path, index=False, encoding="utf-8-sig")
    df.to_csv(OUT_PRICING / long_path.name, index=False, encoding="utf-8-sig")

    # Unique
    uniq = dedupe_unique(df)
    uniq_path = OUT_DERIVED / f"apl_pn_list_unique_{STAMP}.csv"
    uniq.to_csv(uniq_path, index=False, encoding="utf-8-sig")
    uniq.to_csv(OUT_PRICING / uniq_path.name, index=False, encoding="utf-8-sig")

    # Book B seed view (shell out)
    seed = uniq[uniq["book_b_seed_ok"] == 1].copy()
    seed_path = OUT_DERIVED / f"apl_pn_list_book_b_seeds_{STAMP}.csv"
    seed.to_csv(seed_path, index=False, encoding="utf-8-sig")
    seed.to_csv(OUT_PRICING / seed_path.name, index=False, encoding="utf-8-sig")

    # Meta
    def pack_stats(pack: str) -> dict:
        sub = df[df["source_pack"] == pack]
        return {
            "rows": int(len(sub)),
            "unique_pn": int(sub["part_number"].nunique()),
            "shell_lube_rows": int(sub["shell_lube_out"].sum()),
        }

    meta = {
        "built_utc": utc_now(),
        "stamp": STAMP,
        "inventory": inventory,
        "outputs": {
            "long": str(long_path),
            "unique": str(uniq_path),
            "book_b_seeds": str(seed_path),
            "by_pack": {k: str(v) for k, v in paths_out.items()},
        },
        "counts": {
            "long_rows": int(len(df)),
            "unique_pn": int(uniq["part_number"].nunique()),
            "book_b_seed_pn": int(seed["part_number"].nunique()),
            "shell_lube_unique_pn": int(uniq.loc[uniq["shell_lube_out"] == 1, "part_number"].nunique()),
            "by_pack": {p: pack_stats(p) for p in ("ITUK_APL", "P700", "RG21_2.2L")},
            "unique_by_first_pack": uniq.groupby("source_pack_first").size().astype(int).to_dict(),
            "unique_touching_pack": {
                p: int(uniq["source_packs"].str.contains(p, regex=False).sum())
                for p in ("ITUK_APL", "P700", "RG21_2.2L")
            },
        },
        "caveats": [
            "UTI folder 20260714_1037.zip is MD5-identical to ITUK Suzuki APL — not a separate UTI list.",
            "No dedicated UTI-only APL found; P700 PN coverage is accessories + VL27 Belgium + body sample + ITUK PRD.",
            "N-series / F-series xlsx have FIGKEY only (no PN column) — not harvested.",
            "Suzuki/RG21 BP and B/P values stored raw with flag BP_raw_currency_unclear.",
            "Accessory prices labelled accessory_list_fca_exw_eur (as printed on sheet).",
            "VK05 B-Gr not separately parsed (D-Gr used); B-Gr zip identical across ITUK/UTI folders.",
            "Shell/lube excluded from book_b_seeds via description/PN heuristics (5500* + keyword).",
        ],
        "dup_hash_checks": {
            "suzuki_zip_ituk_vs_uti": md5_file(ITUK_DIR / "2026-07-23_20260714_1037.zip")
            == md5_file(UTI_DIR / "2026-07-23_UTI_P700_20260714_1037.zip"),
            "vk05_dgr_ituk_vs_uti": md5_file(ITUK_DIR / "2026-07-13_ITUK_VK05_UK_D_Gr.zip")
            == md5_file(UTI_DIR / "2026-07-13_UTI_P700_VK05_UK_D_Gr.zip"),
            "vl27_ituk_vs_uti": md5_file(
                ITUK_DIR
                / "2026-05-20_ITUK_All_Parts_and_Recommended_Items_list_for_New_Project_VL27_Belgium_.xlsx"
            )
            == md5_file(vl27),
        },
    }
    meta_path = OUT_DERIVED / f"apl_pn_list_{STAMP}.meta.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    (OUT_PRICING / meta_path.name).write_text(json.dumps(meta, indent=2), encoding="utf-8")
    (WORK / "inventory.json").write_text(json.dumps(inventory, indent=2), encoding="utf-8")

    print(json.dumps(meta["counts"], indent=2))
    print("WROTE", long_path)
    print("WROTE", uniq_path)
    print("WROTE", seed_path)


if __name__ == "__main__":
    main()
