"""Read-only: save Natalie's 'Sales Backlog info file VP - update WK 41' attachment. Never Send.

Jerome asked (2026-10-07) to check the mailbox for the latest BO overview from Natalie.
Discovery was done in the agent browser (Outlook web is open there); this step only saves
the attachment he pointed at to 01_data/90_INBOX. Read-only, no send, no reply.
"""
from __future__ import annotations

import sys
from pathlib import Path

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_natalie_bo_wk41_20261007")
OUT.mkdir(parents=True, exist_ok=True)

SUBJECT_HINTS = ("sales backlog info file vp", "wk 41", "wk41")


def main() -> int:
    import win32com.client  # type: ignore

    ns = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
    hits = []

    for store in ns.Stores:
        try:
            root = store.GetRootFolder()
        except Exception:
            continue

        def walk(folder, depth=0):
            if depth > 4:
                return
            try:
                name = folder.Name
            except Exception:
                return
            if name in {"Sync Issues", "RSS Feeds", "Junk Email", "Deleted Items",
                        "Calendar", "Contacts", "Tasks", "Notes", "Conversation History"}:
                return
            try:
                items = folder.Items
                items.Sort("[ReceivedTime]", True)
                n = 0
                for it in items:
                    n += 1
                    if n > 3000:
                        break
                    try:
                        subj = str(getattr(it, "Subject", "") or "")
                    except Exception:
                        continue
                    low = subj.lower()
                    if "backlog" not in low:
                        continue
                    if not any(h in low for h in SUBJECT_HINTS):
                        continue
                    try:
                        rec = str(getattr(it, "ReceivedTime", "") or "")
                        sender = str(getattr(it, "SenderName", "") or "")
                        email = ""
                        try:
                            email = str(it.SenderEmailAddress or "")
                        except Exception:
                            pass
                        atts = []
                        for a in range(1, it.Attachments.Count + 1):
                            atts.append(it.Attachments.Item(a).FileName)
                    except Exception:
                        continue
                    hits.append((rec, store.DisplayName, name, sender, email, subj, atts, it))
            except Exception:
                pass
            try:
                for sub in folder.Folders:
                    walk(sub, depth + 1)
            except Exception:
                pass

        walk(root)

    hits.sort(key=lambda x: x[0], reverse=True)
    print(f"HITS {len(hits)}")
    saved = []
    for rec, store_name, folder, sender, email, subj, atts, it in hits[:6]:
        print("=" * 70)
        print(f"WHEN  {rec}")
        print(f"WHERE {store_name}/{folder}")
        print(f"FROM  {sender} <{email}>")
        print(f"SUBJ  {subj}")
        print(f"ATTS  {atts}")
        for a in range(1, it.Attachments.Count + 1):
            att = it.Attachments.Item(a)
            fn = att.FileName
            if not fn.lower().endswith((".xlsx", ".xls", ".csv")):
                continue
            stamp = rec.replace(":", "").replace(" ", "_")[:15] or "unknown"
            dest = OUT / f"{stamp}_Natalie_{fn}"
            att.SaveAsFile(str(dest))
            saved.append(str(dest))
            print(f"SAVED {dest}")
        try:
            body = str(it.Body or "")[:4000]
            (OUT / "Natalie_WK41_body.txt").write_text(
                f"Subject: {subj}\nFrom: {sender} <{email}>\nReceived: {rec}\n"
                f"Store: {store_name}/{folder}\n\n{body}",
                encoding="utf-8", errors="replace")
        except Exception as exc:
            print("body fail", exc)

    (OUT / "SOURCE.md").write_text(
        "# Natalie BO overview - WK 41\n\n"
        "Subject searched: 'Sales Backlog info file VP - update WK 41'.\n"
        "Discovery: agent browser (Outlook web open). Save: read-only MAPI. Never Send.\n\n"
        "Saved:\n" + "\n".join(f"- `{p}`" for p in saved) + "\n",
        encoding="utf-8")
    print("OUT", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
