"""Fast Outlook Restrict / subject scan for APL recommended parts list."""
from __future__ import annotations

import re
from pathlib import Path

import win32com.client

OUT_DIR = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\APL_ITUK_202607")
MD = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\OUTLOOK_APL_MAIL_SCAN.md")


def save_useful(mail, out_dir: Path, found: list[str]) -> list[str]:
    saved = []
    stamp = str(mail.ReceivedTime)[:10]
    for i in range(1, mail.Attachments.Count + 1):
        att = mail.Attachments.Item(i)
        an = att.FileName
        low = an.lower()
        if not (
            low.endswith((".zip", ".xlsx", ".xls", ".xlsm", ".csv", ".pdf"))
            or "20260714" in low
            or "apl" in low
            or "vr05" in low
        ):
            continue
        safe = re.sub(r"[^\w.\-]+", "_", an)
        dest = out_dir / f"{stamp}_{safe}"
        att.SaveAsFile(str(dest))
        saved.append(str(dest))
        found.append(str(dest))
        print("SAVED", dest)
    return saved


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ol = win32com.client.Dispatch("Outlook.Application")
    ns = ol.GetNamespace("MAPI")
    inbox = ns.GetDefaultFolder(6)
    sent = ns.GetDefaultFolder(5)
    found: list[str] = []
    lines = [
        "# Outlook scan — APL (targeted, fast)",
        "",
        "**RG21 = D-Max 2.2L.**",
        "",
        "Prior broad scan missed this; screenshot mail is Suzuki / Recommended parts list ITUK / APL VR05.",
        "",
    ]

    for folder, name in [(inbox, "Inbox"), (sent, "Sent")]:
        items = folder.Items
        items.Sort("[ReceivedTime]", True)
        # Jet Restrict on subject
        for pattern in (
            "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001f\" LIKE '%Recommended parts list%'",
            "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001f\" LIKE '%Recommended parts%'",
        ):
            try:
                sub = items.Restrict(pattern)
                sub.Sort("[ReceivedTime]", True)
                print(name, "restrict count", sub.Count, pattern[-40:])
                c = 0
                for mail in sub:
                    c += 1
                    if c > 40:
                        break
                    if mail.Class != 43:
                        continue
                    subj = str(mail.Subject or "")
                    sender = str(getattr(mail, "SenderName", "") or "")
                    atts = [
                        mail.Attachments.Item(i).FileName
                        for i in range(1, mail.Attachments.Count + 1)
                    ]
                    print("HIT", str(mail.ReceivedTime)[:19], subj, sender)
                    saved = save_useful(mail, OUT_DIR, found)
                    lines.append(f"## {name} | {str(mail.ReceivedTime)[:19]} | {subj}")
                    lines.append(f"- from: {sender}")
                    lines.append(f"- attachments: {', '.join(atts)}")
                    if saved:
                        lines.append(f"- saved: {', '.join(saved)}")
                    prev = " ".join(str(mail.Body or "").split())[:400]
                    lines.append(f"- preview: {prev}")
                    lines.append("")
            except Exception as e:
                print("RESTRICT ERR", name, e)

        # fallback: first 4000 by subject contains
        print("--- brute subject", name)
        n = 0
        for mail in items:
            n += 1
            if n > 4000:
                break
            try:
                if mail.Class != 43:
                    continue
                subj = str(mail.Subject or "")
                sl = subj.lower()
                if "recommended parts" not in sl and not (
                    "apl" in sl and "ituk" in sl
                ):
                    # also catch zip name via attachment without opening all bodies
                    if mail.Attachments.Count == 0:
                        continue
                    att_names = []
                    for i in range(1, mail.Attachments.Count + 1):
                        try:
                            att_names.append(mail.Attachments.Item(i).FileName)
                        except Exception:
                            pass
                    att_l = " ".join(att_names).lower()
                    if "20260714_1037" not in att_l and "20260714" not in att_l:
                        continue
                sender = str(getattr(mail, "SenderName", "") or "")
                atts = [
                    mail.Attachments.Item(i).FileName
                    for i in range(1, mail.Attachments.Count + 1)
                ]
                print("BRUTE", str(mail.ReceivedTime)[:19], subj, atts)
                saved = save_useful(mail, OUT_DIR, found)
                lines.append(f"## {name} brute | {str(mail.ReceivedTime)[:19]} | {subj}")
                lines.append(f"- from: {sender}")
                lines.append(f"- attachments: {', '.join(atts)}")
                if saved:
                    lines.append(f"- saved: {', '.join(saved)}")
                lines.append("")
            except Exception:
                continue

    lines.append(f"## Files saved ({len(set(found))})")
    for f in sorted(set(found)):
        lines.append(f"- `{f}`")
    if not found:
        lines += [
            "",
            "No zip saved. Mail may sit outside Inbox/Sent (shared mailbox / folder).",
            "Forward Suzuki 23 Jul 2026 mail into Inbox or drop `20260714_1037.zip` into 90_INBOX.",
        ]
    MD.write_text("\n".join(lines), encoding="utf-8")
    print("DONE files", len(set(found)))


if __name__ == "__main__":
    main()
