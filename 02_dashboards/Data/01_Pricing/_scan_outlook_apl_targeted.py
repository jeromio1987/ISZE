"""Targeted Outlook find: Recommended parts list ITUK / APL zip from Suzuki."""
from __future__ import annotations

import json
import re
from pathlib import Path

import win32com.client

OUT_DIR = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\APL_ITUK_202607")
META = Path(
    r"C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_raw\outlook_APL_targeted_20260812.json"
)
MD = Path(
    r"C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\OUTLOOK_APL_MAIL_SCAN.md"
)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ol = win32com.client.Dispatch("Outlook.Application")
    ns = ol.GetNamespace("MAPI")
    folders = [(ns.GetDefaultFolder(6), "Inbox"), (ns.GetDefaultFolder(5), "Sent")]

    hits: list[dict] = []
    saved: list[str] = []

    for folder, fname in folders:
        items = folder.Items
        items.Sort("[ReceivedTime]", True)
        n = 0
        for mail in items:
            n += 1
            if n > 12000:
                break
            try:
                if mail.Class != 43:
                    continue
                subj = str(mail.Subject or "")
                body = str(mail.Body or "")
                sender = str(getattr(mail, "SenderName", "") or "")
                from_addr = ""
                try:
                    from_addr = str(mail.SenderEmailAddress or "")
                except Exception:
                    pass
                atts = []
                for i in range(1, mail.Attachments.Count + 1):
                    try:
                        atts.append(mail.Attachments.Item(i).FileName)
                    except Exception:
                        pass

                subj_l = subj.lower()
                body_l = body.lower()
                att_l = " ".join(atts).lower()
                sender_l = (sender + " " + from_addr).lower()

                score_reasons = []
                if "recommended parts list" in subj_l:
                    score_reasons.append("subject:recommended parts list")
                if "ituk" in subj_l and "part" in subj_l:
                    score_reasons.append("subject:ituk+part")
                if "20260714_1037" in att_l or "20260714" in att_l:
                    score_reasons.append("att:20260714")
                if any("apl" in a.lower() and a.lower().endswith((".zip", ".xlsx", ".xls")) for a in atts):
                    score_reasons.append("att:apl_file")
                # whole-word APL in body (Suzuki mail: "created APL")
                if re.search(r"\bapl\b", body_l) and (
                    "vr05" in body_l or "d-gr" in body_l or "suzuki" in sender_l or "is zj" in sender_l or "isuzu.com" in from_addr.lower()
                ):
                    score_reasons.append("body:APL+ISZJ/VR05")
                if "suzuki" in sender_l and ("apl" in body_l or "recommended parts" in subj_l):
                    score_reasons.append("from:Suzuki+APL")
                if "natalie" in body_l and re.search(r"\bapl\b", body_l) and "vr05" in body_l:
                    score_reasons.append("body:Natalie+APL+VR05")

                if not score_reasons:
                    continue

                saved_here = []
                for i in range(1, mail.Attachments.Count + 1):
                    try:
                        att = mail.Attachments.Item(i)
                        an = att.FileName
                        low = an.lower()
                        if low.endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp")):
                            continue
                        keep = low.endswith(
                            (".zip", ".xlsx", ".xls", ".xlsm", ".csv", ".pdf")
                        ) or "20260714" in low or "apl" in low or "vr05" in low
                        if not keep:
                            continue
                        safe = re.sub(r"[^\w.\-]+", "_", an)
                        stamp = str(mail.ReceivedTime)[:10]
                        dest = OUT_DIR / f"{stamp}_{safe}"
                        if not dest.exists() or dest.stat().st_size == 0:
                            att.SaveAsFile(str(dest))
                        saved_here.append(str(dest))
                        saved.append(str(dest))
                    except Exception as e:
                        saved_here.append(f"ERR:{e}")

                hits.append(
                    {
                        "folder": fname,
                        "received": str(mail.ReceivedTime),
                        "subject": subj,
                        "sender": sender,
                        "from_addr": from_addr,
                        "reasons": score_reasons,
                        "attachments": atts,
                        "saved": saved_here,
                        "preview": " ".join(body.split())[:900],
                    }
                )
                if len(hits) >= 30:
                    break
            except Exception:
                continue
        if len(hits) >= 30:
            break

    META.write_text(
        json.dumps({"hit_count": len(hits), "saved": saved, "hits": hits}, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# Outlook scan — APL (targeted)",
        "",
        "First keyword scan was too loose (false hits). This pass targets:",
        "- subject **Recommended parts list** / ITUK parts",
        "- attachment **20260714_1037** / APL files",
        "- body whole-word **APL** + VR05 / Suzuki / ISZJ",
        "",
        "**RG21 = D-Max 2.2L.**",
        "",
        f"Hits: **{len(hits)}** · Saved under `{OUT_DIR}`",
        "",
    ]
    if not hits:
        lines += [
            "## No targeted hit in Inbox/Sent scan",
            "",
            "Please forward or move the Suzuki mail into Inbox, or confirm mailbox.",
            "Screenshot showed: Takayoshi Suzuki → Natalie Vernimmen, 23 Jul 2026,",
            "subject RE: Recommended parts list ITUK, zip `20260714_1037.zip`.",
            "",
        ]
    for h in hits:
        lines.append(f"## {h['received'][:19]} | {h['subject']}")
        lines.append(f"- from: {h['sender']} <{h.get('from_addr','')}>")
        lines.append(f"- reasons: {', '.join(h['reasons'])}")
        atts = [
            a
            for a in h["attachments"]
            if not str(a).lower().endswith((".png", ".jpg", ".jpeg", ".gif"))
        ]
        if atts:
            lines.append(f"- attachments: {', '.join(atts)}")
        if h["saved"]:
            lines.append(f"- saved: {', '.join(h['saved'])}")
        lines.append(f"- preview: {h['preview'][:350]}")
        lines.append("")

    MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"hits={len(hits)} saved={len(set(saved))}")
    for h in hits:
        print(h["received"][:19], h["subject"][:80], h["reasons"])
        print(" saved", h["saved"])


if __name__ == "__main__":
    main()
