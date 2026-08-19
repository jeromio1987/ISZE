"""Peek Ireland candidate attachments + print targeted mail previews."""
from __future__ import annotations

import json
from pathlib import Path

import openpyxl

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_ireland_sales_mail_20260813")
ATT = ROOT / "attachments"
ATT2 = ROOT / "attachments_targeted"


def peek(path: Path, max_sheets: int = 8, max_rows: int = 12) -> None:
    print(f"\n===== {path.name} ({path.stat().st_size} bytes) =====")
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    print("sheets:", wb.sheetnames)
    for sn in wb.sheetnames[:max_sheets]:
        ws = wb[sn]
        print(f"--- sheet: {sn} ---")
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            print(row)
            if i >= max_rows:
                break
    wb.close()


def main() -> None:
    tgt = json.loads((ROOT / "outlook_ireland_targeted.json").read_text(encoding="utf-8"))
    print("=== TARGETED MAIL PREVIEWS (with atts or key) ===")
    for h in tgt["hits"]:
        print(
            f"\n{h['received'][:19]} | {h['sender']} <{h.get('sender_email','')}> | To: {h.get('to','')[:80]}"
        )
        print(f"  SUBJ: {h['subject']}")
        print(f"  ATTS: {h['attachments']}")
        print(f"  PREVIEW: {h.get('preview','')[:700]}")

    candidates = [
        ATT / "2026-08-13_IE_XT_-_2026-08-13T114222.149.xlsx",
        ATT2 / "2026-08-13_TGT_XT_-_2026-08-13T114222.149.xlsx",
        ATT2 / "2026-08-06_TGT_Template_SPA_05082026.xlsx",
        ATT / "2026-08-06_IE_Template_SPA_05082026.xlsx",
    ]
    # also any ireland-named non-BO xlsx
    for folder in (ATT, ATT2):
        if not folder.exists():
            continue
        for p in sorted(folder.glob("*.xlsx")):
            n = p.name.upper()
            if "BO_OVERVIEW" in n or "BO OVERVIEW" in n:
                continue
            if "AWARDS" in n or "UIO_GPS" in n or "SURVEY" in n:
                continue
            if p not in candidates:
                candidates.append(p)

    seen = set()
    for p in candidates:
        if not p.exists() or p.resolve() in seen:
            continue
        seen.add(p.resolve())
        peek(p)


if __name__ == "__main__":
    main()
