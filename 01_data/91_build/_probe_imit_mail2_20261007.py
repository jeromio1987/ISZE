"""Second probe: list all MAPI stores, and every mail from Peeraya (any subject),
plus any subject containing 'fill rate', across a deeper tree. Read-only.
Writes results to _probe2_hits.txt.
"""
from __future__ import annotations

import re

SKIP_FOLDERS = {"Sync Issues", "RSS Feeds", "Junk Email", "Deleted Items",
                "Calendar", "Contacts", "Tasks", "Notes", "Conversation History",
                "Outbox"}

OUT_TXT = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_kpi_panel_20261007\imit_fill_rate\_probe2_hits.txt"
OUT_STORES = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_kpi_panel_20261007\imit_fill_rate\_stores.txt"


def main() -> int:
    import win32com.client  # type: ignore

    ns = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
    lines: list[str] = []
    store_lines: list[str] = []

    stores = []
    for store in ns.Stores:
        try:
            stores.append(store)
        except Exception:
            continue
    store_lines.append(f"stores: {len(stores)}")
    for s in stores:
        try:
            store_lines.append(f"  {s.DisplayName!r}")
        except Exception as e:
            store_lines.append(f"  <err {e}>")

    for store in stores:
        try:
            sname = store.DisplayName
            root = store.GetRootFolder()
        except Exception:
            continue

        def walk(folder, depth=0):
            if depth > 6:
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
                    if cnt > 6000:
                        break
                    try:
                        subj = str(getattr(it, "Subject", "") or "")
                        sender = str(getattr(it, "SenderName", "") or "")
                    except Exception:
                        continue
                    low = subj.lower()
                    if ("peeraya" in sender.lower()) or ("fill rate" in low) or ("imit fill" in low):
                        try:
                            rec = str(getattr(it, "ReceivedTime", "") or "")[:19]
                        except Exception:
                            rec = ""
                        atts = []
                        try:
                            for a in range(1, it.Attachments.Count + 1):
                                atts.append(str(it.Attachments.Item(a).FileName))
                        except Exception:
                            pass
                        lines.append(
                            f"{rec} | {sname[:16]:16s} | depth{depth} {name[:20]:20s} "
                            f"| {sender[:26]:26s} | {subj[:62]:62s} | {atts}")
            except Exception:
                pass
            try:
                for sub in folder.Folders:
                    walk(sub, depth + 1)
            except Exception:
                pass

        walk(root)

    lines.sort(reverse=True)
    open(OUT_STORES, "w", encoding="utf-8").write("\n".join(store_lines))
    open(OUT_TXT, "w", encoding="utf-8").write("\n".join(lines))
    print("\n".join(store_lines))
    print(f"hits: {len(lines)}")
    print("\n".join(lines[:60]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
