"""Build UK-only hand-collect worklist for delivery_basis / tax_basis.

Source: U29-B worktree evidence results + price_observations (UK focus only).
Does not invent delivery, tax, or eligible euros. Portugal skipped.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

W = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b")
DERIVED = W / "01_data" / "00_derived"
OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX")
OUT.mkdir(parents=True, exist_ok=True)

focus = pd.read_csv(DERIVED / "epc_decode_worklist.csv", dtype={"part_number": str})
focus = focus[focus["pms_category"].isin(["brake_pad", "oil_filter"])]
pn_meta = focus.set_index("part_number")[["pms_category", "eur_all"]].to_dict("index")
focus_pns = set(focus["part_number"].astype(str))

po = pd.read_parquet(DERIVED / "price_observations.parquet")
po["part_no"] = po["part_no"].astype(str)
po = po.set_index("obs_id", drop=False)

ev = json.loads(
    (W / "01_data" / "91_build" / "_u19_evidence_results_20261007.json").read_text(
        encoding="utf-8"
    )
)
rows = [r for r in ev["rows"] if r.get("market") == "UK"]
print("UK evidence rows", len(rows))

rc: Counter = Counter()
only_del = 0
only_del_tax = 0
for r in rows:
    codes = tuple(sorted(r.get("reason_codes") or []))
    rc[codes] += 1
    if codes == ("DELIVERY_BASIS_NOT_STATED",):
        only_del += 1
    if set(codes) <= {"DELIVERY_BASIS_NOT_STATED", "TAX_BASIS_NOT_STATED"} and codes:
        only_del_tax += 1
print("reason combos:")
for k, v in rc.most_common():
    print(f"  {v:3d}  {k or '(eligible)'}")
print("only delivery:", only_del, "only delivery and/or tax:", only_del_tax)

OFF = pd.read_csv(
    W / "04_tools" / "price_ledger" / "OFFERED_ROWS.csv", dtype=str, low_memory=False
)
off_by_id = OFF.set_index("obs_id", drop=False)


def host_of(url) -> str:
    if url is None or (isinstance(url, float) and pd.isna(url)) or str(url).strip() == "":
        return ""
    try:
        return urlparse(str(url)).netloc.lower()
    except Exception:
        return ""


def map_tax_stated(vat) -> bool:
    if vat is None or (isinstance(vat, float) and pd.isna(vat)):
        return False
    s = str(vat).strip().lower()
    return s in {
        "excl",
        "excluded",
        "exclusive",
        "ex",
        "incl",
        "included",
        "inclusive",
        "inc",
    }


def blankish(v) -> bool:
    if v is None:
        return True
    if isinstance(v, float) and pd.isna(v):
        return True
    return str(v).strip() == ""


out_rows = []
for r in rows:
    oid = r["observation_id"]
    codes = sorted(r.get("reason_codes") or [])
    ledger_snip = r.get("ledger") or {}

    if oid in po.index:
        lr = po.loc[oid]
        if isinstance(lr, pd.DataFrame):
            lr = lr.iloc[0]
        part = str(lr.get("part_no") or r.get("part_number") or "")
        url = lr.get("source_url")
        source = lr.get("source")
        loader = lr.get("loader")
        competitor_pn = lr.get("competitor_pn")
        competitor_brand = lr.get("competitor_brand")
        price = lr.get("price")
        currency = lr.get("currency")
        vat = lr.get("vat")
        delivery_included = lr.get("delivery_included")
        delivery_note = lr.get("delivery_note")
        description = lr.get("description")
        match_method = lr.get("match_method")
    else:
        part = str(r.get("part_number") or "")
        url = ledger_snip.get("source_url")
        source = ledger_snip.get("source")
        loader = ledger_snip.get("loader")
        competitor_pn = ledger_snip.get("competitor_pn") or ledger_snip.get(
            "alternative_reference"
        )
        competitor_brand = ledger_snip.get("competitor_brand") or ledger_snip.get(
            "seller"
        )
        price = ledger_snip.get("price")
        currency = ledger_snip.get("currency")
        vat = ledger_snip.get("vat")
        delivery_included = ledger_snip.get("delivery_included")
        delivery_note = ledger_snip.get("delivery_note")
        description = ledger_snip.get("description")
        match_method = ledger_snip.get("match_method")

    page_file = ""
    if oid in off_by_id.index:
        pf = off_by_id.loc[oid]
        if isinstance(pf, pd.DataFrame):
            pf = pf.iloc[0]
        page_file = pf.get("page_file") or ""

    del_stated = (
        str(delivery_included).strip().lower() in {"yes", "no"}
        if not blankish(delivery_included)
        else False
    )
    tax_stated = map_tax_stated(vat)
    has_price = not blankish(price)

    code_set = set(codes)
    only_basis = (
        code_set <= {"DELIVERY_BASIS_NOT_STATED", "TAX_BASIS_NOT_STATED"} and bool(code_set)
    )
    if has_price and only_basis:
        priority = 1
    elif has_price and "DELIVERY_BASIS_NOT_STATED" in code_set:
        priority = 2
    else:
        priority = 3

    meta = pn_meta.get(part, {})
    blockers = ";".join(codes) if codes else ("ELIGIBLE" if r.get("eligible") else "")

    needs_hand = (not del_stated) or (
        not tax_stated and "TAX_BASIS_NOT_STATED" in code_set
    )
    if not needs_hand:
        continue

    notes_bits = []
    if only_basis:
        notes_bits.append("almost_qualify: blocked only on delivery/tax basis")
    if not del_stated:
        notes_bits.append("ledger delivery_included blank")
    else:
        notes_bits.append(f"ledger already has delivery_included={delivery_included}")
    if not tax_stated:
        notes_bits.append("tax/vat not mapped (unknown/blank)")
    else:
        notes_bits.append(f"ledger vat={vat} (tax already stated for evidence)")
    if loader == "eucon_survey_2023":
        notes_bits.append(
            "file-backed Eucon UK survey — no shop URL; need seller policy note or skip"
        )
    if page_file:
        notes_bits.append(f"saved_page={page_file}")
    if blankish(url):
        notes_bits.append("no source_url")

    out_rows.append(
        {
            "priority": priority,
            "obs_id": oid,
            "part_number": part,
            "oe_competitor_pn": "" if blankish(competitor_pn) else str(competitor_pn),
            "pms_category": meta.get("pms_category", ""),
            "competitor_brand": (
                "" if blankish(competitor_brand) else str(competitor_brand)
            ),
            "source": source or "",
            "loader": loader or "",
            "host": host_of(url),
            "url": "" if blankish(url) else str(url),
            "price": price if has_price else "",
            "currency": currency or "",
            "current_blocker": blockers,
            "ledger_vat": "" if blankish(vat) else str(vat),
            "ledger_delivery_included": (
                "" if blankish(delivery_included) else str(delivery_included)
            ),
            "ledger_delivery_note": (
                "" if blankish(delivery_note) else str(delivery_note)
            ),
            # FILL columns — leave blank; never invent
            "delivery_basis": "",
            "tax_basis": "",
            "delivery_note_hand": "",
            "delivery_cost_if_stated": "",
            "match_method": match_method or "",
            "description": (
                "" if blankish(description) else str(description)[:180]
            ),
            "notes": " | ".join(notes_bits),
        }
    )

df = pd.DataFrame(out_rows)
df = df.sort_values(["priority", "host", "part_number", "obs_id"]).reset_index(drop=True)
csv_path = OUT / "UNIVERSE_UK_DELIVERY_TAX_HAND_COLLECT_20261007.csv"
df.to_csv(csv_path, index=False)

print("\nWrote", csv_path, "rows", len(df))
print("by priority:", df["priority"].value_counts().to_dict())
print("top hosts:")
print(df["host"].replace("", "(no url)").value_counts().head(10).to_string())
print("by loader:")
print(df["loader"].value_counts().to_string())

uk_po = po[(po["country"] == "UK") & (po["part_no"].isin(focus_pns))]
stated = uk_po[uk_po["delivery_included"].isin(["yes", "no"])]
print(
    "UK focus ledger rows with delivery already stated:",
    len(stated),
    stated["loader"].value_counts().to_dict() if len(stated) else {},
)
print("priority1 blockers:", df[df.priority == 1]["current_blocker"].value_counts().to_dict())
print("cols", list(df.columns))
