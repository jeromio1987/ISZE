#!/usr/bin/env python3
"""Fill ISZE/IMG in Charge on the IDS 26 follow-up summary from Awards owners."""

from __future__ import annotations

import shutil
from pathlib import Path

from openpyxl import load_workbook

from ids_paths import DATA_ROOT, RANKINGS_DIR

AWARDS = RANKINGS_DIR / "DB Evaluation for Awards 26.xlsx"
SUMMARY_SRC = Path(r"C:\Users\jerom\Downloads\26 summary.xlsx")
SUMMARY_OUT = DATA_ROOT / "reports" / "2026_IDS_FollowUp_Summary.xlsx"
DOWNLOADS_OUT = Path(r"C:\Users\jerom\Downloads\26 summary_filled.xlsx")

# Map summary "DB Name" → Awards owner (IMG/ISZE Responsible).
# Benelux/IBX left blank in Awards for BE/NL/LX child rows — use IBX programme lead.
OWNER_BY_DB: dict[str, str] = {
    "Autowallis": "Tomoe",
    "Isuzu Rom": "Bart",
    "GazanSammit": "Tomoe",
    "Isuzu Danmark": "Tomoe",
    "Loutsios": "Tomoe",
    "Petros": "Jerome",
    "Isuzu Benelux": "Bart",  # Astara Western / IBX (BE+NL+LX)
    "UMI": "Koen",
    "ITUK": "Jerome",
    "MIDI": "Tomoe",
    "Isuzu Polska": "Bart",
    "Astara Portugal": "Jerome",
    "RSA": "Koen",
    "IUK": "Koen",
    "BL": "-",
    "Isuzu Ireland": "-",
    "ISD": "-",
    "Isuzu Sweden": "-",
    "KIMA": "-",
    "Nordic": "-",
    "UTI": "-",
    "AIOS": "-",
}


def load_awards_owners() -> dict[str, str]:
    """Prefer live Awards column C when a DB name is present."""
    out = dict(OWNER_BY_DB)
    if not AWARDS.is_file():
        return out
    wb = load_workbook(AWARDS, data_only=True)
    ws = wb["Awards"]
    for r in range(6, ws.max_row + 1):
        db = ws.cell(r, 1).value
        owner = ws.cell(r, 3).value
        if db and owner and str(owner).strip() not in {"", "-"}:
            out[str(db).strip()] = str(owner).strip()
    wb.close()
    return out


def fill_summary(src: Path, dest: Path, owners: dict[str, str]) -> None:
    wb = load_workbook(src)
    ws = wb[wb.sheetnames[0]]
    # Col A = DB Name, Col I = ISZE/IMG in Charge (index 9)
    for r in range(5, 40):
        db = ws.cell(r, 1).value
        if not db:
            continue
        key = str(db).strip()
        owner = owners.get(key)
        if owner is None:
            # fuzzy: Isuzu Danmark vs ISZ Danmark
            for k, v in owners.items():
                if k.lower() in key.lower() or key.lower() in k.lower():
                    owner = v
                    break
        if owner is not None:
            ws.cell(r, 9, value=owner)
    dest.parent.mkdir(parents=True, exist_ok=True)
    wb.save(dest)


def main() -> int:
    owners = load_awards_owners()
    # Alias summary names
    owners.setdefault("Isuzu Danmark", owners.get("ISZ Danmark", "Tomoe"))
    owners.setdefault("Isuzu Polska", owners.get("Astara Western", "Bart"))
    if not SUMMARY_SRC.is_file():
        print(f"Missing {SUMMARY_SRC}")
        return 1
    fill_summary(SUMMARY_SRC, SUMMARY_OUT, owners)
    shutil.copy2(SUMMARY_OUT, DOWNLOADS_OUT)
    print(f"Wrote {SUMMARY_OUT}")
    print(f"Copied {DOWNLOADS_OUT}")
    for k in sorted(owners):
        print(f"  {k}: {owners[k]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
