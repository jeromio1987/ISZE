"""Wider probe for the IMIT April 2026 fill-rate mail (read-only).

Same proven scan pattern, but:
  - matches any subject containing 'fill rate' or 'imit'
  - no sender filter (we just list hits and their senders)
  - skips the 'Sales' store's known-public folders only
Prints subject / sender / date / folder / attachment names so we can find the one
that did not come through the first pull.
"""
from __future__ import annotations

import re

SKIP_FOLDERS = {"Sync Issues", "RSS Feeds", "Junk Email", "Deleted Items",
                "Calendar", "Contacts", "Tasks", "Notes", "Conversation History",
                "Outbox"}

RX = re.compile(r"imit\s+fill\s+rate|fill\s*rate\s+to\s+isze", re.I)

MAX = 250

OUT_TXT = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_kpi_panel_20261007\imit_fill_rate\_probe_hits.txt"


def main() -> int:
    import win32com.client  # type: ignore

    ns = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
    hits: list[dict] = []

    for store in ns.Stores:
        try:
            sname = store.DisplayName
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
            if name in SKIP_FOLDERS:
                return
            try:
                items = folder.Items
                items.Sort("[ReceivedTime]", True)
                cnt = 0
                for it in items:
                    cnt += 1
                    if cnt > 4000:
                        break
                    try:
                        subj = str(getattr(it, "Subject", "") or "")
                    except Exception:
                        continue
                    if not RX.search(subj):
                        continue
                    try:
                        rec = str(getattr(it, "ReceivedTime", "") or "")[:19]
                        sender = str(getattr(it, "SenderName", "") or "")
                        email = ""
                        try:
                            email = str(it.SenderEmailAddress or "")
                        except Exception:
                            pass
                        atts = []
                        try:
                            for a in range(1, it.Attachments.Count + 1):
                                atts.append(str(it.Attachments.Item(a).FileName))
                        except Exception:
                            pass
                        hits.append((rec, sname, name, sender, email, subj, atts))
                    except Exception:
                        continue
            except Exception:
                pass
            try:
                for sub in folder.Folders:
                    walk(sub, depth + 1)
            except Exception:
                pass

        walk(root)

    hits.sort(reverse=True)
    lines = [f"total IMIT-fill-rate mails: {len(hits)}"]
    for h in hits[:MAX]:
        rec, sname, folder, sender, email, subj, atts = h
        lines.append(f"{rec} | {sname[:14]:14s} | {folder[:16]:16s} | {sender[:26]:26s} | {subj[:60]:60s} | {atts}")
    text = "\n".join(lines)
    open(OUT_TXT, "w", encoding="utf-8").write(text)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
