"""Create one Outlook draft to Jerome: DB-level IDS country dashboards only. Save — never Send."""
from __future__ import annotations

import zipfile
from pathlib import Path

import win32com.client  # type: ignore

ISZE = Path(__file__).resolve().parents[2]
PACK = ISZE / "09_meetings" / "IDS_2026_Country_Packs_v1.4"
ZIP_PATH = PACK / "IDS_2026_country_dashboards_DB_level.zip"
TO = "jerome.van.der.pluym@isuzu-e.com"
OL_FOLDER_DRAFTS = 16
SUBJECT = "IDS dashboards — country / DB level only (to self)"
OLD_SUBJECTS = {
    SUBJECT,
    "IDS dashboards — latest unique set (to self)",
}

# One HTML per market (v1.4). Skip network-wide studies and the Israel duplicate of Israel LCV.
COUNTRIES = [
    "Belgium",
    "Netherlands",
    "Luxembourg",
    "Denmark",
    "Poland",
    "Greece",
    "Norway",
    "Hungary",
    "Romania",
    "Malta",
    "Cyprus",
    "UK_CV",
    "UK_LCV",
    "Portugal",
    "Israel_LCV",
    "France",
    "Italy",
    "Spain",
    "Switzerland",
]

BODY = """Jerome,

Country / DB dashboards only (IDS 2026 v1.4). One HTML per market.

Unzip, then double-click the country file you need.

Left out of this mail (network-wide graphs / tables):
- full-network dealer compare
- explainer
- sales / market evaluation
- Kaizen / parts Kaizen / DB parts posture
- Masumi briefing
- Portugal standalone map
- dealer-fiche zip
- blank feedback templates

Draft only — please Send when ready.
"""


def _country_htmls() -> list[Path]:
    files: list[Path] = []
    missing: list[str] = []
    for name in COUNTRIES:
        p = PACK / name / f"IDS_2026_dealer_compare_{name}.html"
        if not p.is_file():
            missing.append(str(p))
        else:
            files.append(p)
    if missing:
        raise SystemExit("Missing country HTML:\n" + "\n".join(missing))
    return files


def _write_zip(files: list[Path]) -> Path:
    if ZIP_PATH.is_file():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in files:
            zf.write(p, arcname=p.name)
    return ZIP_PATH


def main() -> int:
    files = _country_htmls()
    zip_path = _write_zip(files)

    outlook = win32com.client.Dispatch("Outlook.Application")
    ns = outlook.GetNamespace("MAPI")
    drafts = ns.GetDefaultFolder(OL_FOLDER_DRAFTS)

    for item in list(drafts.Items):
        try:
            subj = str(getattr(item, "Subject", "") or "")
            if subj in OLD_SUBJECTS or subj.startswith("IDS dashboards"):
                item.Delete()
        except Exception:
            continue

    mail = outlook.CreateItem(0)
    mail.To = TO
    mail.CC = ""
    mail.BCC = ""
    mail.Subject = SUBJECT
    mail.Body = BODY
    mail.Attachments.Add(str(zip_path.resolve()))
    mail.Save()
    try:
        mail = mail.Move(drafts)
    except Exception as exc:
        print(f"move_warn: {exc}")
    mail.Display(False)
    print(
        f"DRAFT saved To={mail.To} Subject={mail.Subject} "
        f"Attachments={mail.Attachments.Count} zip={zip_path} "
        f"htmls={len(files)} bytes={zip_path.stat().st_size}"
    )
    print("Not sent. You send.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
