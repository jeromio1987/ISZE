"""Outlook draft to Jerome: IMG pack — 3 dashboards + 1 dealer sheet. Save only."""
from __future__ import annotations

from pathlib import Path

import win32com.client  # type: ignore

ISZE = Path(__file__).resolve().parents[2]
TO = "jerome.van.der.pluym@isuzu-e.com"
OL_FOLDER_DRAFTS = 16
SUBJECT = "IDS pack for IMG — compare, Kaizen, explainer, one dealer sheet"

ATTACH = [
    ISZE / "02_dashboards" / "ids" / "IDS_2026_dealer_compare.html",
    ISZE / "02_dashboards" / "ids" / "IDS_2026_Explainer.html",
    ISZE / "02_dashboards" / "ids" / "IDS_2026_Kaizen_Belgium.html",
    ISZE
    / "09_meetings"
    / "IDS_2026_DB_Feedback_Sheet_v0.4"
    / "Belgium"
    / "dealers"
    / "IDS_2026_Dealer_Feedback_Belgium_Garage_Degroote_v0.4_workshop_pack.html",
]

BODY = """Jerome,

Pack for the IMG discussion (draft only — you send).

Four files
1. IDS_2026_dealer_compare.html — reading layer (map, dealer vs country, anonymous network).
2. IDS_2026_Explainer.html — executive overview (timeline, roadmap, talking line).
3. IDS_2026_Kaizen_Belgium.html — DB as lever (hit list, 3–5 blank actions, monthly pull). Belgium is the example.
4. Garage Degroote workshop pack — visit annex. Owner / date / proof blank.

Network average
• On 1–3 (v1.4, 15 Aug): anonymous IDS network = 79.3% (France/Spain red-marks out of the average; Israel LCV Section E not scored and excluded). That figure is current.
• On the dealer sheet (v0.4, 11 Aug): Belgium average = 78.5% (34 of 34). That is the country bar for the visit. It did not need to move to 79.3%. Mixing those two bars would put the dealer against the wrong number.

Proposal in one page (for the room)
• Self-audit: IBX told us their top-scoring dealer was not operationally strong. Do not punish optimistic filling — we lose the next round. Calibrate with sample visits that include high scores, not only the bottom.
• Participation: not every ISZE market sat IDS 2026. Next round, attach an incentive to a complete evaluation submitted — not to a high score.
• Power: multi-brand DBs do not have to share. Keep friction low. Incentive we already pay should stay on KPI + sales-to-dealer files arriving (their layout). Do not put IDS action-closure on kickback.
• Kaizen: compare stays; one country at a time; dealer sheet only for names we visit; monthly 20 minutes on what closed.
• IT (Forms / Automate): KPI as he is building; sales-to-dealer as file upload to the same folder pattern; IDS as a 5-row action list + reminder — not 180 checklist questions in Forms.

Private speaking notes (second screen, not attached):
09_meetings\\IMG_IDS_briefing_2026-08-19\\OPEN_DRAAIBOEK_IMG_IDS.cmd
"""


def main() -> int:
    missing = [p for p in ATTACH if not p.is_file()]
    if missing:
        raise SystemExit("Missing:\n" + "\n".join(str(p) for p in missing))

    outlook = win32com.client.Dispatch("Outlook.Application")
    ns = outlook.GetNamespace("MAPI")
    drafts = ns.GetDefaultFolder(OL_FOLDER_DRAFTS)

    for item in list(drafts.Items):
        try:
            subj = str(getattr(item, "Subject", "") or "")
            if subj == SUBJECT:
                item.Delete()
        except Exception:
            continue

    mail = outlook.CreateItem(0)
    mail.To = TO
    mail.CC = ""
    mail.BCC = ""
    mail.Subject = SUBJECT
    mail.Body = BODY
    for p in ATTACH:
        mail.Attachments.Add(str(p.resolve()))
    mail.Save()
    try:
        mail = mail.Move(drafts)
    except Exception as exc:
        print("move_warn", exc)
    mail.Display(False)
    print(f"DRAFT To={mail.To} Attachments={mail.Attachments.Count} Not sent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
