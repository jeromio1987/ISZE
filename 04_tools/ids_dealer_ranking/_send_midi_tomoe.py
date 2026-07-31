#!/usr/bin/env python3
"""Zip MIDI FR/IT/ES/CH Excel+HTML and Send to Tomoe via Outlook COM."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import zipfile

from ids_paths import ISZE_ROOT

OUT_DIR = ISZE_ROOT / "09_meetings" / "IDS_2026_MIDI_Packs"
ZIP_PATH = OUT_DIR / "IDS_2026_MIDI_FR_IT_ES_CH_Excel_HTML.zip"

TO = "Tomoe.Baumann@isuzu.de"
BCC = "jerome.van.der.pluym@isuzu-e.com"
SUBJECT = "IDS 2026 — MIDI dealer files (Excel + HTML)"
BODY = """Dear Tomoe,

Please find attached the IDS 2026 MIDI dealer files for France, Italy, Spain and Switzerland (MIDI network).

What is included (one zip)
• Excel — MIDI source workbook (MIDI_FR.xlsx), evaluation result reports for MIDI FR/IT/ES/CH, and dealer ranking workbooks (total + B.1) for France / Italy / Spain / Switzerland
• HTML — offline dealer compare packs (single-country) for France, Italy, Spain and Switzerland (map included; open with internet so map tiles can load)

Scope: MIDI = France / Italy / Spain / Switzerland only. Other IDS markets are not included in this mail.

Kind regards,
Jérôme Van der Pluym
"""


def main() -> int:
    excel_files = [
        ISZE_ROOT / "01_data/90_INBOX/IDS_2026/MIDI/MIDI_FR.xlsx",
        ISZE_ROOT
        / "01_data/90_INBOX/IDS_2026/reports/2026 IDS Evaluation Result Report_MIDI_FR.xls",
        ISZE_ROOT
        / "01_data/90_INBOX/IDS_2026/reports/2026 IDS Evaluation Result Report_MIDI_IT.xls",
        ISZE_ROOT
        / "01_data/90_INBOX/IDS_2026/reports/2026 IDS Evaluation Result Report_MIDI_ES.xls",
        ISZE_ROOT
        / "01_data/90_INBOX/IDS_2026/reports/2026 IDS Evaluation Result Report_MIDI_CH.xls",
        ISZE_ROOT / "01_data/90_INBOX/IDS_2026/rankings/France_dealer_ranking.xlsx",
        ISZE_ROOT / "01_data/90_INBOX/IDS_2026/rankings/Italy_dealer_ranking.xlsx",
        ISZE_ROOT / "01_data/90_INBOX/IDS_2026/rankings/Spain_dealer_ranking.xlsx",
        ISZE_ROOT / "01_data/90_INBOX/IDS_2026/rankings/Switzerland_dealer_ranking.xlsx",
        ISZE_ROOT / "01_data/90_INBOX/IDS_2026/rankings/France_B1_dealer_ranking.xlsx",
        ISZE_ROOT / "01_data/90_INBOX/IDS_2026/rankings/Italy_B1_dealer_ranking.xlsx",
        ISZE_ROOT / "01_data/90_INBOX/IDS_2026/rankings/Spain_B1_dealer_ranking.xlsx",
        ISZE_ROOT / "01_data/90_INBOX/IDS_2026/rankings/Switzerland_B1_dealer_ranking.xlsx",
    ]
    html_files = [
        OUT_DIR / "France" / "IDS_2026_dealer_compare_France.html",
        OUT_DIR / "Italy" / "IDS_2026_dealer_compare_Italy.html",
        OUT_DIR / "Spain" / "IDS_2026_dealer_compare_Spain.html",
        OUT_DIR / "Switzerland" / "IDS_2026_dealer_compare_Switzerland.html",
    ]

    missing = [str(p) for p in excel_files + html_files if not p.is_file()]
    if missing:
        raise SystemExit("Missing files:\n" + "\n".join(missing))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in excel_files:
            zf.write(p, arcname=f"Excel/{p.name}")
        for p in html_files:
            zf.write(p, arcname=f"HTML/{p.parent.name}/{p.name}")

    size_mb = ZIP_PATH.stat().st_size / (1024 * 1024)
    print(f"ZIP: {ZIP_PATH}")
    print(f"Size: {size_mb:.2f} MB")

    import win32com.client  # type: ignore

    outlook = win32com.client.Dispatch("Outlook.Application")
    ns = outlook.GetNamespace("MAPI")
    mail = outlook.CreateItem(0)
    mail.To = TO
    mail.BCC = BCC
    mail.Subject = SUBJECT
    mail.Body = BODY
    mail.Attachments.Add(str(ZIP_PATH))

    result = {
        "attempted_at": datetime.now().isoformat(timespec="seconds"),
        "to": TO,
        "bcc": BCC,
        "subject": SUBJECT,
        "zip_path": str(ZIP_PATH),
        "zip_mb": round(size_mb, 2),
        "excel": [str(p) for p in excel_files],
        "html": [str(p) for p in html_files],
        "status": None,
        "entryid": None,
        "error": None,
        "msg_fallback": None,
        "store": str(getattr(ns.DefaultStore, "DisplayName", "") or ""),
    }

    try:
        mail.Send()
        result["status"] = "sent"
        try:
            result["entryid"] = str(getattr(mail, "EntryID", "") or "")
        except Exception:  # noqa: BLE001
            result["entryid"] = ""
        print("SENT OK")
    except Exception as exc:  # noqa: BLE001
        result["error"] = str(exc)
        print(f"SEND FAILED: {exc}")
        try:
            mail2 = outlook.CreateItem(0)
            mail2.To = TO
            mail2.BCC = BCC
            mail2.Subject = SUBJECT
            mail2.Body = BODY
            mail2.Attachments.Add(str(ZIP_PATH))
            mail2.Save()
            drafts = ns.GetDefaultFolder(16)
            try:
                moved = mail2.Move(drafts)
                result["entryid"] = str(
                    getattr(moved, "EntryID", "") or getattr(mail2, "EntryID", "") or ""
                )
            except Exception:  # noqa: BLE001
                result["entryid"] = str(getattr(mail2, "EntryID", "") or "")
            msg_dir = OUT_DIR / "_outlook_msg_fallbacks"
            msg_dir.mkdir(parents=True, exist_ok=True)
            msg_path = msg_dir / "IDS_2026_MIDI_to_Tomoe.msg"
            try:
                item = (
                    ns.GetItemFromID(result["entryid"])
                    if result["entryid"]
                    else mail2
                )
                item.SaveAs(str(msg_path), 3)
                result["msg_fallback"] = str(msg_path)
            except Exception as exc2:  # noqa: BLE001
                result["msg_fallback"] = f"FAILED: {exc2}"
            result["status"] = "draft_after_send_fail"
            print(f"DRAFT SAVED EntryID={(result['entryid'] or '')[:40]}…")
        except Exception as exc3:  # noqa: BLE001
            result["status"] = "failed"
            result["error"] = f"send: {exc}; draft: {exc3}"
            print(f"DRAFT ALSO FAILED: {exc3}")

    out_json = OUT_DIR / "outlook_send_midi_tomoe_result.json"
    out_json.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "sent" else 1


if __name__ == "__main__":
    raise SystemExit(main())
