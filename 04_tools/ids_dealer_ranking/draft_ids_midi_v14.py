#!/usr/bin/env python3
"""Create Outlook DRAFT for IDS 2026 MIDI packs v1.4 (Save — never Send).

To: Tomoe Baumann. Attach master zip of FR/IT/ES/CH dealer-compare packs.
Baumann average rule: FR/ES red-marked out; IT/CH all dealers in averages.
"""

from __future__ import annotations

import json

from ids_paths import ISZE_ROOT

PACK_ROOT = ISZE_ROOT / "09_meetings" / "IDS_2026_Country_Packs_v1.4"
ALL_ZIP = PACK_ROOT / "IDS_2026_Country_Packs_v1.4_ALL.zip"
INDEX = PACK_ROOT / "INDEX.md"
TO = "Tomoe.Baumann@isuzu.de"
BCC = "jerome.van.der.pluym@isuzu-e.com"
SUBJECT = (
    "IDS 2026 — MIDI dealer compare packs v1.4 "
    "(corrected IT/CH averages)"
)
SUBJECT_LEGACY = "IDS 2026 — MIDI dealer compare packs v1.4 (Baumann average rule)"
OL_FOLDER_DRAFTS = 16
OL_MAIL_ITEM = 0


def main() -> int:
    if not ALL_ZIP.is_file():
        raise SystemExit(f"Missing {ALL_ZIP}")

    body = (
        "Dear Tomoe,\n\n"
        "Please find attached the IDS 2026 MIDI dealer compare packs "
        "(France / Italy / Spain / Switzerland) — version v1.4 "
        "(corrected Italy / Switzerland averages).\n\n"
        "Average rule (your 31 Jul note)\n"
        "• France + Spain: red-marked dealers stay on the list and map, "
        "but are excluded from national / section averages "
        "(France 20 / Spain 5).\n"
        "• Italy + Switzerland: all dealers remain in the averages "
        "(including zero-score shells).\n\n"
        "Attachment\n"
        "• IDS_2026_Country_Packs_v1.4_ALL.zip — four country HTML packs + INDEX.md\n"
        "• Open a country zip → HTML + README. Map hover = dealer score vs "
        "that country’s national average (post-exclusion basis for FR/ES).\n\n"
        "Open the HTML with an internet connection so map tiles can load.\n\n"
        "Kind regards,\n"
        "Jérôme Van der Pluym\n"
    )

    import win32com.client  # type: ignore

    outlook = win32com.client.Dispatch("Outlook.Application")
    # Create first, then purge older matching drafts (Delete-before-Create
    # intermittently breaks CreateItem under win32com).
    mail = outlook.CreateItem(OL_MAIL_ITEM)
    mail.To = TO
    mail.BCC = BCC
    mail.Subject = SUBJECT
    mail.Body = body
    mail.Attachments.Add(str(ALL_ZIP.resolve()))
    if INDEX.is_file():
        mail.Attachments.Add(str(INDEX.resolve()))
    mail.Save()
    keep_id = str(getattr(mail, "EntryID", "") or "")

    ns = outlook.GetNamespace("MAPI")
    drafts = ns.GetDefaultFolder(OL_FOLDER_DRAFTS)
    purge = {SUBJECT, SUBJECT_LEGACY}
    for item in list(drafts.Items):
        try:
            subj = str(getattr(item, "Subject", "") or "")
            eid = str(getattr(item, "EntryID", "") or "")
            if subj in purge and eid and eid != keep_id:
                item.Delete()
        except Exception:  # noqa: BLE001
            pass

    try:
        mail.Display(False)
    except Exception:  # noqa: BLE001
        pass

    result = {
        "subject": SUBJECT,
        "to": TO,
        "bcc": BCC,
        "zip": str(ALL_ZIP),
        "draft_only": True,
        "sent": False,
    }
    out = PACK_ROOT / "outlook_draft_midi_v14_result.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"DRAFT saved (not sent): {SUBJECT}")
    print(f"  To: {TO}")
    print(f"  Attach: {ALL_ZIP.name}")
    print(f"  Meta: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
