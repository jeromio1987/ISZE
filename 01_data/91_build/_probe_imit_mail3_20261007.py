"""Deep, uncapped probe for any 'fill rate' subject across all stores/folders.
No item cap (folder item counts are 23k/34k). Skips only the noisy system folders.
Also reports folders that contain the word 'archive' so we know wat is scanned.
Read-only. Writes _probe3_hits.txt.
"""
from __future__ import annotations

import re

SKIP_FOLDERS = {"Sync Issues", "RSS Feeds", "Conversation History", "Outbox"}

RX = re.compile(r"fill\s*rate", re.I)
OUT_TXT = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_kpi_panel_20261007\imit_fill_rate\_probe3_hits.txt"


def main() -> int:
    import win32com.client  # type: ignore

    ns = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
    lines: list[str] = []
    scanned: list[str] = []

    for store in ns.Stores:
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
                cnt_items = folder.Items.Count
            except Exception:
                cnt_items = -1
            scanned.append(f"{sname} | d{depth} | {name} | {cnt_items}")
            try:
                items = folder.Items
                items.Sort("[ReceivedTime]", True)
                seen = 0
                for it in items:
                    seen += 1
                    try:
                        subj = str(getattr(it, "Subject", "") or "")
                    except Exception:
                        continue
                    if not RX.search(subj):
                        continue
                    try:
                        rec = str(getattr(it, "ReceivedTime", "") or "")[:19]
                        sender = str(getattr(it, "SenderName", "") or "")
                        atts = []
                        try:
                            for a in range(1, it.Attachments.Count + 1):
                                atts.append(str(it.Attachments.Item(a).FileName))
                        except Exception:
                            pass
                        lines.append(
                            f"{rec} | {sname[:16]:16s} | d{depth} {name[:22]:22s} "
                            f"| {sender[:28]:28s} | {subj[:66]:66s} | {atts}")
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

    lines.sort(reverse=True)
    open(OUT_TXT, "w", encoding="utf-8").write(
        "\n".join(lines) + "\n\n--- SCANNED FOLDERS ---\n" + "\n".join(scanned))
    print(f"fill-rate subject hits: {len(lines)}")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
