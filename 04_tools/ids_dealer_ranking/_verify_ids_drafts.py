#!/usr/bin/env python3
"""Verify IDS v1.3 drafts in default Outlook Drafts and rewrite result JSON."""
from __future__ import annotations

import json
from pathlib import Path

import win32com.client

PACK = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\IDS_2026_Country_Packs_v1.3")
OUT = PACK / "outlook_drafts_result.json"
MSG_DIR = PACK / "_outlook_msg_fallbacks"


def main() -> None:
    outlook = win32com.client.Dispatch("Outlook.Application")
    ns = outlook.GetNamespace("MAPI")
    drafts = ns.GetDefaultFolder(16)
    print("Drafts path:", drafts.FolderPath)
    print("Drafts count:", drafts.Items.Count)
    print("Store:", drafts.Store.DisplayName)

    for i in range(1, ns.Stores.Count + 1):
        s = ns.Stores.Item(i)
        try:
            df = s.GetDefaultFolder(16)
            print(
                f"  Store {s.DisplayName} Drafts count={df.Items.Count} "
                f"path={df.FolderPath}"
            )
        except Exception as exc:  # noqa: BLE001
            print(f"  Store {s.DisplayName} drafts err: {exc}")

    matches = []
    for item in drafts.Items:
        subj = str(getattr(item, "Subject", "") or "")
        if "IDS 2026" in subj and "v1.3" in subj:
            matches.append(
                {
                    "subject": subj,
                    "to": str(getattr(item, "To", "") or ""),
                    "bcc": str(getattr(item, "BCC", "") or ""),
                    "attachments": int(item.Attachments.Count),
                    "entryid": str(item.EntryID),
                    "modified": str(item.LastModificationTime),
                    "status": "draft_saved",
                }
            )

    print("IDS v1.3 count:", len(matches))
    payload = {
        "summary": {
            "store": drafts.Store.DisplayName,
            "folder_path": drafts.FolderPath,
            "drafts_total_after": drafts.Items.Count,
            "ids_v13_in_drafts": len(matches),
            "how_to_find": (
                f"Outlook -> mailbox '{drafts.Store.DisplayName}' -> Drafts. "
                "Search subject: IDS 2026 v1.3. "
                "Do not look under Sales/Parts shared-mailbox Drafts."
            ),
            "msg_fallbacks_dir": str(MSG_DIR),
        },
        "drafts": matches,
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Wrote", OUT)
    for m in matches:
        print(m["subject"], "| To=", m["to"], "| att=", m["attachments"])
        print("  EntryID=", m["entryid"])

    if MSG_DIR.is_dir():
        msgs = sorted(MSG_DIR.glob("*.msg"))
        print("msg fallbacks:", len(msgs))
        for p in msgs:
            print(" ", p.name, p.stat().st_size)
    else:
        print("msg dir missing")

    # Open Drafts folder in Outlook navigation so Jerome sees it
    try:
        explorer = outlook.ActiveExplorer()
        if explorer is None:
            explorer = outlook.Explorers.Add(drafts, 0)
        else:
            explorer.CurrentFolder = drafts
        print("Set ActiveExplorer CurrentFolder to Drafts")
    except Exception as exc:  # noqa: BLE001
        print("Could not navigate Outlook UI to Drafts:", exc)


if __name__ == "__main__":
    main()
