"""Read-only: latest Duncan Young mail. Never Send."""
from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).with_name("_duncan_latest_mail.txt")


def main() -> int:
    import win32com.client  # type: ignore

    outlook = win32com.client.Dispatch("Outlook.Application")
    ns = outlook.GetNamespace("MAPI")
    folders = [
        ("Inbox", ns.GetDefaultFolder(6)),
        ("Sent", ns.GetDefaultFolder(5)),
        ("Drafts", ns.GetDefaultFolder(16)),
    ]
    found = []
    for fname, folder in folders:
        items = folder.Items
        items.Sort("[ReceivedTime]", True)
        n = 0
        for it in items:
            n += 1
            if n > 400:
                break
            try:
                sender = str(getattr(it, "SenderName", "") or "")
                try:
                    email = str(it.SenderEmailAddress or "")
                except Exception:
                    email = ""
                to = ""
                try:
                    to = str(it.To or "")
                except Exception:
                    pass
                subj = str(getattr(it, "Subject", "") or "")
                rec = str(getattr(it, "ReceivedTime", "") or "")
                blob = f"{sender} {email} {to} {subj}".lower()
                if "duncan" not in blob and "duncan.young" not in blob:
                    continue
                atts = []
                try:
                    for a in range(1, it.Attachments.Count + 1):
                        atts.append(it.Attachments.Item(a).FileName)
                except Exception:
                    pass
                body = ""
                try:
                    body = str(it.Body or "")[:6000]
                except Exception:
                    pass
                found.append((fname, rec, sender, email, to, subj, atts, body))
            except Exception:
                continue
    found.sort(key=lambda x: x[1], reverse=True)
    found = found[:12]

    lines = [f"FOUND {len(found)}", ""]
    for fname, rec, sender, email, to, subj, atts, body in found:
        lines.append("=" * 72)
        lines.append(f"FOLDER {fname}")
        lines.append(f"WHEN {rec}")
        lines.append(f"FROM {sender} | {email}")
        lines.append(f"TO {to}")
        lines.append(f"SUBJ {subj}")
        lines.append(f"ATTS {atts}")
        lines.append("--- BODY ---")
        lines.append(body)
        lines.append("")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT} n={len(found)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
