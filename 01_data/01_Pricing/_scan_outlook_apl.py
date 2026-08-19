"""Scan Outlook for APL / recommended parts list ITUK; save zip/xlsx attachments."""
from __future__ import annotations

import json
import re
from pathlib import Path

import win32com.client

OUT_DIR = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\APL_ITUK_202607")
META = Path(
    r"C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_raw\outlook_APL_mail_scan_20260812.json"
)
MD = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\OUTLOOK_APL_MAIL_SCAN.md")

KEYWORDS = [
    "APL",
    "VR05",
    "Recommended parts list",
    "D-Gr",
    "20260714_1037",
    "recommended parts",
]


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
            if n > 10000:
                break
            try:
                if mail.Class != 43:
                    continue
                subj = str(mail.Subject or "")
                body = str(mail.Body or "")
                blob = (subj + " " + body).lower()
                atts: list[str] = []
                for i in range(1, mail.Attachments.Count + 1):
                    try:
                        atts.append(mail.Attachments.Item(i).FileName)
                    except Exception:
                        pass
                att_blob = " ".join(atts).lower()
                if not (
                    any(k.lower() in blob for k in KEYWORDS)
                    or "apl" in subj.lower()
                    or "recommended parts" in subj.lower()
                    or "apl" in att_blob
                    or "20260714" in att_blob
                    or "vr05" in att_blob
                ):
                    continue

                saved_here: list[str] = []
                for i in range(1, mail.Attachments.Count + 1):
                    try:
                        att = mail.Attachments.Item(i)
                        an = att.FileName
                        low = an.lower()
                        if low.endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp")):
                            continue
                        keep = (
                            low.endswith(
                                (".zip", ".xlsx", ".xls", ".xlsm", ".csv", ".pdf", ".docx")
                            )
                            or "apl" in low
                            or "20260714" in low
                            or "vr05" in low
                        )
                        if not keep:
                            continue
                        safe = re.sub(r"[^\w.\-]+", "_", an)
                        stamp = str(mail.ReceivedTime)[:10]
                        dest = OUT_DIR / f"{stamp}_{safe}"
                        if not dest.exists():
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
                        "sender": str(getattr(mail, "SenderName", "") or ""),
                        "attachments": atts,
                        "saved": saved_here,
                        "preview": " ".join(body.split())[:800],
                    }
                )
                if len(hits) >= 50:
                    break
            except Exception:
                continue
        if len(hits) >= 50:
            break

    META.parent.mkdir(parents=True, exist_ok=True)
    META.write_text(
        json.dumps({"hit_count": len(hits), "saved": saved, "hits": hits}, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# Outlook scan — APL / recommended parts list",
        "",
        "Prior scan used P700 / 2.2 / RZ4F / RG21 keywords — **missed APL**.",
        "This scan: **APL**, VR05, Recommended parts list, D-Gr.",
        "",
        "**Note:** RG21 = D-Max **2.2L**.",
        "",
        f"Hits: **{len(hits)}** · Files saved under `{OUT_DIR}`",
        "",
        "## Matches",
        "",
    ]
    for h in hits:
        atts = [
            a
            for a in h["attachments"]
            if not str(a).lower().endswith((".png", ".jpg", ".jpeg", ".gif"))
        ]
        lines.append(f"- {h['received'][:10]} | {h['subject']}")
        lines.append(f"  - from: {h['sender']}")
        if atts:
            lines.append(f"  - attachments: {', '.join(atts)}")
        if h["saved"]:
            lines.append(f"  - saved: {', '.join(h['saved'])}")
        if "APL" in (h.get("preview") or "") or "apl" in (h.get("preview") or "").lower():
            # short preview clip around APL
            prev = h["preview"]
            lines.append(f"  - preview: {prev[:220]}…")

    MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"hits={len(hits)} saved={len(saved)}")
    print(f"meta={META}")
    print(f"md={MD}")
    for s in saved[:20]:
        print("FILE", s)


if __name__ == "__main__":
    main()
