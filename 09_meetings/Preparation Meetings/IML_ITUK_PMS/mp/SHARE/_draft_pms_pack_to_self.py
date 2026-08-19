"""Outlook DRAFT to Jerome only. Save. Never Send."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
MEET = ROOT / "09_meetings"
PPT = MEET / "ISZE_PMS_How_We_Proceed_DRAFT.pptx"
X1 = MEET / "ITUK_PMS_Coverage_1pct_DRAFT.xlsx"
X2 = MEET / "ITUK_PMS_Aftermarket_Compare_DRAFT.xlsx"

TO = "jerome.van.der.pluym@isuzu-e.com"
SUBJECT = "DRAFT for you: ITUK PMS parts pack (PPT + 2 Excel) before IML"
OL_FOLDER_DRAFTS = 16
OL_MAIL_ITEM = 0

BODY = """Duncan,

Short note on the complementary pack. Your slides stay the programme. This is only the parts.

18 August is the operational kick-off: BVP, a special price if we need it, and a complete filter set.

The goal in one number. One extra point on all PMS parts, ITUK to the dealer, is about 368 units, roughly EUR 7,530 at our ASP. Not a filter-only story.

Coverage is N75, calendar 2025. Fuel is already at the service level. Air is not. Oil is on the truck. We are not making a campaign of it.

Then the real part numbers and quantities, your sales to dealers and ours to you.

Three moves, in that order:
1. BVP where genuine is not moving (fuel and air twins exist; oil BVP is already in the market).
2. SPA if price is still the problem.
3. The filter set: one oil, one fuel, one air. Genuine first. BVP only if genuine does not take.

The back slides are marked DRAFT. Brakes: the pad is the wear item, no BVP, so SPA only. We compare your projected price to dealers with aftermarket workshop purchase. Same step, not our list versus a shop. Clutch: we can sell a kit, manuals only. Urea: not on the 56; what sold is the DEF pump filter kit.

Aftermarket page: the pad is the problem. Filters are close. Clutch is not.

Close: October, N75 first.

Can you live with this in front of IML? And is the 40 percent mark-up on your buy-in in the right area?

Attachments
- ISZE_PMS_How_We_Proceed_DRAFT.pptx (12 slides)
- ITUK_PMS_Coverage_1pct_DRAFT.xlsx
- ITUK_PMS_Aftermarket_Compare_DRAFT.xlsx

Jerome
"""


def main() -> int:
    for p in (PPT, X1, X2):
        if not p.is_file():
            raise SystemExit(f"Missing {p}")

    import win32com.client  # type: ignore

    outlook = win32com.client.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(OL_MAIL_ITEM)
    mail.To = TO
    mail.Subject = SUBJECT
    mail.Body = BODY
    mail.Attachments.Add(str(PPT.resolve()))
    mail.Attachments.Add(str(X1.resolve()))
    mail.Attachments.Add(str(X2.resolve()))
    mail.Save()
    keep_id = str(getattr(mail, "EntryID", "") or "")

    ns = outlook.GetNamespace("MAPI")
    drafts = ns.GetDefaultFolder(OL_FOLDER_DRAFTS)
    for item in list(drafts.Items):
        try:
            subj = str(getattr(item, "Subject", "") or "")
            eid = str(getattr(item, "EntryID", "") or "")
            if subj == SUBJECT and eid and eid != keep_id:
                item.Delete()
        except Exception:
            pass

    try:
        mail.Display(False)
    except Exception:
        pass

    print("Draft saved. Not sent.")
    print("To:", TO)
    print("Subject:", SUBJECT)
    print("Attachments:", PPT.name, X1.name, X2.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
