"""Create Outlook DRAFT reply to Masumi Action plans update — do not send."""
from __future__ import annotations

import json
from pathlib import Path

import win32com.client

ENTRY_ID = (
    "00000000174BC82B22520D429348932087CC34F0070058934DF1ED3C4D4EA4EA4D7658026CCA"
    "00000000010C000058934DF1ED3C4D4EA4EA4D7658026CCA00097FB95DDE0000"
)
ATT_DIR = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\japan_week_mom_20260819")
PMS_MOM_DIR = Path(
    r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Preparation Meetings\IML_ITUK_PMS"
)
ATTACHMENTS = [
    ATT_DIR / "ISZE_PMS_Parts_Support_20260818.pptx",
    ATT_DIR / "PMS_Project_18_08_2026_Rev2.pptx",
    PMS_MOM_DIR / "DRAFT_MoM_ITUK_ISZE_ISZJ_PMS_Parts_Sales_Promotion_20260818_v4.docx",
    ATT_DIR / "MoM_ ITUK IML ISZE Meeting_Lubricants_20260819 R.docx",
]
RESULT = Path(
    r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\Data\90_INBOX\_masumi_action_plan_draft_result.json"
)

HTML = """
<div style="font-family:Calibri,Arial,sans-serif;font-size:11pt;color:#222;">
<p>Dear Masumi,</p>
<p>Thank you for the action-plan list. Happy to go through this tomorrow — I will check with the team on a slot and send the invite.</p>
<p>Below is my feedback, structured on your points.</p>
<p><b>1. Genuine parts share</b></p>
<ul>
<li><b>Target figures:</b> GPS Extended Target 3.1 is internally agreed (UIO V19, 1.8% stretch). We are communicating that number in the distributor reviews.</li>
<li><b>Distributor agreement status:</b>
<ul>
<li><b>Held:</b> Portugal, ISD, IUK, Ireland, Petros, UMI, UTI, ITUK, IBX, AutoWallis.</li>
<li><b>In the diary this week:</b> Iceland (25 Aug), Romania (25 Aug), Norway (26 Aug).</li>
<li><b>Not reachable</b> (no reply / no slot yet): Sweden, Finland, Cyprus.</li>
<li><b>Postponed:</b> Denmark — meeting moved to September.</li>
<li><b>Still being booked:</b> Malta (written to; date open).</li>
</ul>
</li>
<li><b>Distributors without a usable UIO / car-park base (KZK, GA, KIMA):</b> I am not fully clear yet on the best way to proceed for the genuine-share conversation. My proposal for tomorrow: <b>pivot the narrative to the sales target itself</b> (they are not aware of our internal business-plan / UIO model), and <b>ask about their car park out of interest</b> — as information, not as the basis we force into the target discussion. Happy to align the wording with you before we contact them.</li>
</ul>
<p><b>2. PMS</b></p>
<ul>
<li><b>ITUK meeting result (18 Aug):</b> Positive. One campaign — N75 fleet at 40,000 km, October go-live. ISZE complementary parts support agreed; we are proceeding with SPA. September build, October launch.</li>
<li>Suzuki san shared the <b>meeting minutes</b> — attached as a <b>DRAFT</b> for your review.</li>
<li>Attached for your reference:
<ul>
<li>Draft minutes of the meeting (<i>DRAFT_MoM_ITUK_ISZE_ISZJ_PMS_Parts_Sales_Promotion_20260818_v4.docx</i>)</li>
<li>ISZE presentation used in the meeting (<i>ISZE_PMS_Parts_Support_20260818.pptx</i>)</li>
<li>Duncan / ITUK pack (<i>PMS_Project_18_08_2026_Rev2.pptx</i>)</li>
</ul>
</li>
<li><b>Target setting for other distributors:</b> after ITUK go-live and once the minutes are finalised, we can propose the next markets. Happy to discuss sequencing tomorrow.</li>
</ul>
<p><b>3. Lubricant</b></p>
<ul>
<li><b>ITUK meeting result (19 Aug):</b> No supplier switch decided. ITUK agreed to join the Centralized Purchasing <b>opportunity study</b>. ITUK will provide unit price history (pre/post Iran conflict), vehicle park and service retention.</li>
<li>Attached: Ikeda san’s <b>draft MoM</b> (<i>MoM_ ITUK IML ISZE Meeting_Lubricants_20260819 R.docx</i>) — still a <b>DRAFT</b>. He asked me to comment before sharing with Duncan — I will revert to him after our alignment if needed.</li>
</ul>
<p><b>4. KPIs</b></p>
<ul>
<li>Distributor agreement status is being chased together with the GPS reviews (same round). Checkpoint remains end of August where a slot exists; Denmark moves with the September meeting.</li>
</ul>
<p><b>5. IDS</b></p>
<ul>
<li><b>IMG meeting result (19 Aug):</b> Compare tool + Kaizen approach accepted. Tomoe shared the updated DB allocation (<i>EU IDS Dealer Summary 20260819.xlsx</i>). Feedback to DBs starts from the week of 25 August.</li>
</ul>
<p><b>6. Parts training</b></p>
<ul>
<li>Iceland training date noted as 23 September (separate from the 25 Aug business review). Full schedule update — I will bring the latest view tomorrow.</li>
</ul>
<p>Please let me know if you want anything adjusted before the invite goes out.</p>
<p>Kind regards,<br>Jérôme</p>
</div>
"""


def main() -> None:
    ol = win32com.client.Dispatch("Outlook.Application")
    ns = ol.GetNamespace("MAPI")

    # Remove prior draft if we still have its entry id
    if RESULT.exists():
        try:
            old = json.loads(RESULT.read_text(encoding="utf-8"))
            drafts = ns.GetDefaultFolder(16)
            old_item = ns.GetItemFromID(old["entry_id"], drafts.StoreID)
            old_item.Delete()
            print("deleted_old_draft", flush=True)
        except Exception as exc:
            print("old_delete_skip", exc, flush=True)

    inbox = ns.GetDefaultFolder(6)
    try:
        mail = ns.GetItemFromID(ENTRY_ID, inbox.StoreID)
        draft = mail.ReplyAll()
        draft.Subject = "RE: Action plans update"
        draft.HTMLBody = HTML + draft.HTMLBody
    except Exception as exc:
        print("replyall_failed_fallback_new", exc, flush=True)
        draft = ol.CreateItem(0)  # olMailItem
        draft.To = "masumi.hayakawa@isuzu-e.com; hadewijch.tibos@isuzu-e.com; koen.matheussen@isuzu-e.com; bart.symons@isuzu-e.com; wei-ling.cheung@isuzu-e.com"
        draft.Subject = "RE: Action plans update"
        draft.HTMLBody = HTML
    for p in ATTACHMENTS:
        if not p.exists():
            raise FileNotFoundError(p)
        draft.Attachments.Add(str(p))
    draft.Save()
    RESULT.write_text(
        json.dumps(
            {
                "status": "draft_saved_not_sent",
                "subject": draft.Subject,
                "to": draft.To,
                "cc": draft.CC,
                "attachments": [a.name for a in ATTACHMENTS],
                "entry_id": str(draft.EntryID),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print("DRAFT_SAVED", draft.Subject, flush=True)
    print("TO:", draft.To, flush=True)
    print("ATTS:", [a.name for a in ATTACHMENTS], flush=True)
    draft.Display(False)


if __name__ == "__main__":
    main()
