#!/usr/bin/env python3
"""Create Outlook DRAFT for IDS 2026 Belgium pack v1.4 (Save — never Send).

To: Jerome. Attach Belgium v1.4 zip (corrected network averages wave).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from ids_paths import ISZE_ROOT

PACK_ROOT = ISZE_ROOT / "09_meetings" / "IDS_2026_Belgium_v1.4"
BE_ZIP = PACK_ROOT / "IDS_2026_Belgium_v1.4.zip"
BE_HTML = PACK_ROOT / "Belgium" / "IDS_2026_dealer_compare_Belgium.html"
DASH_MIRROR = (
    ISZE_ROOT / "02_dashboards" / "ids" / "IDS_2026_dealer_compare_Belgium.html"
)
TO = "jerome.van.der.pluym@isuzu-e.com"
SUBJECT = "IDS 2026 — Belgium dealer compare v1.4 (corrected averages)"
SUBJECT_LEGACY = "IDS 2026 — Belgium dealer compare v1.4 (map)"
OL_FOLDER_DRAFTS = 16
OL_MAIL_ITEM = 0


def main() -> int:
    if not BE_ZIP.is_file():
        raise SystemExit(f"Missing {BE_ZIP}")

    body = (
        "Jerome,\n\n"
        "Belgium IDS dealer compare pack v1.4 — corrected network averages "
        "(same correction wave as MIDI Baumann / IDS v1.4).\n\n"
        "Averages vs previous Belgium v1.3\n"
        "• Belgium national average: unchanged at ~78.5% (34 dealers; "
        "no FR/ES-style red-mark exclusions for BE).\n"
        "• Anonymous full-network average: ~75.7% → ~79.0% "
        "(FR/ES red-marked out of network averages; IT/CH all in).\n\n"
        "Attachment\n"
        f"• {BE_ZIP.name}\n"
        "• Open zip → HTML + README. Map hover = dealer score vs Belgium "
        "national average.\n"
        f"• Dashboard mirror: {DASH_MIRROR}\n\n"
        "v1.3 left intact under IDS_2026_Country_Packs_v1.3\\Belgium.\n\n"
        "Draft only — not sent.\n\n"
        "Kind regards,\n"
        "Jérôme Van der Pluym\n"
    )

    import win32com.client  # type: ignore

    outlook = win32com.client.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(OL_MAIL_ITEM)
    mail.To = TO
    mail.Subject = SUBJECT
    mail.Body = body
    mail.Attachments.Add(str(BE_ZIP.resolve()))
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
        "zip": str(BE_ZIP),
        "html": str(BE_HTML),
        "dashboard_mirror": str(DASH_MIRROR),
        "draft_only": True,
        "sent": False,
        "saved_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "averages": {
            "national_v13_pct": 78.5,
            "national_v14_pct": 78.5,
            "network_v13_pct": 75.7,
            "network_v14_pct": 79.0,
            "note": "National unchanged; network avg corrected under Baumann wave",
        },
    }
    out = PACK_ROOT / "outlook_draft_belgium_v14_result.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"DRAFT saved (not sent): {SUBJECT}")
    print(f"  To: {TO}")
    print(f"  Attach: {BE_ZIP.name}")
    print(f"  Meta: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
