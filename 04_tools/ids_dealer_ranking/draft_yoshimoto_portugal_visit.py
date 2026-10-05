#!/usr/bin/env python3
"""Create Outlook DRAFT: approval request to Yoshimoto san for Portugal / IMOTORS visit.

Save only. Never Send.
Requested by Jerome 2026-09-21.
"""

from __future__ import annotations

OL_MAIL_ITEM = 0
OL_FOLDER_DRAFTS = 16

TO = "Norihiro_Yoshimoto@isuzu.com"
SUBJECT = "Approval request: Portugal / IMOTORS visit (IDS and Kaizen)"

BODY = """Dear Yoshimoto san,

I would like to ask your approval for a visit to Portugal (IMOTORS) around 12-16 October, together with Uematsu san.

Purpose

* Dealer visits: three dealers, one strong, one average and one weaker. The selection is still being confirmed with IMOTORS.
* IDS and Kaizen: perform the IDS assessment at each of the three dealers with the IDS 2026 tool we built for Portugal, and use the outcome for Kaizen activities on Isuzu dealer standards.
* Dealer talks during the visits: how they see sales, whether their prices are competitive, whether they are happy with IMOTORS and the cooperation with them.
* Distributor meeting (separate), to discuss:
  - Lubricants
  - Sales review
  - GPS and PMS
  - Outlook
  - SPA
* Sales situation:
  - Slightly behind, mainly due to low order intake in August, possibly summer related
  - We would like to verify GPS and PMS with IMOTORS in detail during the visit
* Physical dealer visits are needed to complete the picture and to move the Kaizen actions forward

May I proceed with this visit?

Kind regards,
"""


def main() -> int:
    import win32com.client  # type: ignore

    outlook = win32com.client.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(OL_MAIL_ITEM)
    mail.To = TO
    mail.Subject = SUBJECT
    mail.Body = BODY
    mail.Save()
    entry_id = str(getattr(mail, "EntryID", "") or "")

    ns = outlook.GetNamespace("MAPI")
    drafts = ns.GetDefaultFolder(OL_FOLDER_DRAFTS)
    matches = []
    removed = 0
    for item in list(drafts.Items):
        try:
            subj = str(getattr(item, "Subject", "") or "")
            eid = str(getattr(item, "EntryID", "") or "")
            if subj == SUBJECT:
                if eid and eid != entry_id:
                    item.Delete()
                    removed += 1
                    continue
                matches.append((eid, eid == entry_id))
        except Exception:  # noqa: BLE001
            pass

    print(f"SAVED draft: {SUBJECT}")
    print(f"To: {TO}")
    print(f"EntryID: {entry_id}")
    print(f"Superseded drafts removed: {removed}")
    print(f"Drafts with this subject: {len(matches)} (new={sum(1 for _, n in matches if n)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
