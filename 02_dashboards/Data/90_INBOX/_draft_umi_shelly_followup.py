"""Create ONE Outlook draft to Shelly Cohen (UMI 1797). Save — do NOT Send.

Reply on her 12 Aug 'Re: Meeting' request for the presentation.
Attaches: shared presentation, Israel LCV dealer-standards HTML pack, commercial PN declines.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import win32com.client

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT = ISZE / "01_data" / "90_INBOX" / "_umi_shelly_followup_draft_result.json"

PPTX = ISZE / "09_meetings" / "UMI_Sales_Review_2026" / "ISZE_UMI_Sales_Review_FY2027_ModeA_only.pptx"
ZIP_IDS = (
    ISZE
    / "09_meetings"
    / "IDS_2026_Country_Packs_v1.4"
    / "Israel_LCV"
    / "IDS_2026_Israel_LCV_v1.4.zip"
)
CSV_PN = (
    ISZE
    / "09_meetings"
    / "UMI_Sales_Review_2026"
    / "UMI_commercial_PN_declines_CYH1_for_SPA.csv"
)

# Shelly 12 Aug 22:58 — asked for the presentation
ENTRY_ID = (
    "00000000174BC82B22520D429348932087CC34F0070058934DF1ED3C4D4EA4EA4D7658026CCA"
    "00000000010C000058934DF1ED3C4D4EA4EA4D7658026CCA00094DC5E8910000"
)

TO_FALLBACK = "shelly@umi.co.il"
CC_EXTRA = [
    "Netanelbuc@umi.co.il",
    "hadewijch.tibos@isuzu-e.com",
    "bart.symons@isuzu-e.com",
]

BODY = """Dear Shelly,

Thank you again for the meeting on 12 August, and for your note afterwards.

As requested, please find attached:
1. The presentation from our meeting
2. The Isuzu Dealer Standards overview and heat-map for the Israel network (zip: open the HTML; double-click OPEN_IDS_2026_Israel_LCV.cmd, or open the HTML directly — an internet connection is needed for the map)
3. The part numbers with the largest euro decline versus last year on our billing (commercial, excluding warranty) — to support the special-price discussion

A few points we can already follow up from our side:

Dealer Standards
The attached tool shows dealer scores versus the Israel average. Section E (vehicle sales) was not completed in this round, which is the main reason the network average sits below the wider dealer-standards average. Completing Section E is for UMI to consider; we can update the picture once that is done.

Special price agreements
Please send the part numbers you would like us to review, with estimated 12-month quantities and your target prices. We will then review internally and come back. The attached decline list is only a starting point from our billing — it is not a proposed agreement.

Shell / 5-litre packaging
We have received the Rimula R4L 15W40 CK4 table (5L / 20L / 209L). The 5-litre pack we supply is part number 550047337 (3 x 5L). We are checking current availability and will come back separately. If you have a fuller oil list, please send it so we can review packaging options. This mail does not change any price.

Genuine parts share incentive
The incentive linked to the extended genuine-share target is still pending approval. I will confirm as soon as we have a decision.

Aftersales Awards 2026
We have your question on the survey sheet you submitted. We are checking with the awards team whether anything further is required, and will confirm.

Sales-to-dealer
If you can share a monthly part-level extract from 1 January 2025 (part number, invoice date, quantity — prices not required), that will help demand and replenishment on our side.

Parts training on Wednesday 26 August at 11:00 Belgian time is already confirmed with Netanel; Bart will send the meeting invite two days before.

Kind regards,

Jérôme Van der Pluym
Assistant Manager // Pricing analyst
Sales – Vehicle Parts | Isuzu Motors Europe NV
"""


def log(m: str) -> None:
    print(m, flush=True)


def main() -> None:
    for p in (PPTX, ZIP_IDS, CSV_PN):
        if not p.exists():
            raise SystemExit(f"missing {p}")

    outlook = win32com.client.Dispatch("Outlook.Application")
    ns = outlook.GetNamespace("MAPI")
    how = "new_mail"
    mail = None
    try:
        src = ns.GetItemFromID(ENTRY_ID)
        mail = src.Reply()
        how = "reply"
        log(f"REPLY on {src.Subject}")
    except Exception as e:
        log(f"REPLY fail ({e}) — new mail")
        mail = outlook.CreateItem(0)
        mail.To = TO_FALLBACK
        mail.Subject = "UMI follow-up — presentation and Dealer Standards tool (12 August)"

    existing_cc = str(getattr(mail, "CC", "") or "")
    for addr in CC_EXTRA:
        if addr.lower() not in existing_cc.lower():
            existing_cc = (existing_cc + "; " + addr).strip("; ")
    mail.CC = existing_cc
    mail.Body = BODY
    mail.BodyFormat = 1  # olFormatPlain

    for p in (PPTX, ZIP_IDS, CSV_PN):
        mail.Attachments.Add(str(p))
        log(f"ATTACH {p.name}")

    mail.Save()
    try:
        mail.Display(False)
    except Exception as e:
        log(f"DISPLAY warn {e}")

    result = {
        "status": "draft_saved_not_sent",
        "how": how,
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "to": str(getattr(mail, "To", "") or ""),
        "cc": str(getattr(mail, "CC", "") or ""),
        "subject": str(getattr(mail, "Subject", "") or ""),
        "attachments": [PPTX.name, ZIP_IDS.name, CSV_PN.name],
        "sent": False,
        "note": "Save only. Jerome sends.",
    }
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    log("DRAFT SAVED (not sent)")
    log(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
