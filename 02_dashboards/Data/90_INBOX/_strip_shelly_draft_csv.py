"""Remove the customer CSV attachment from the Shelly draft. Do not Send."""
from __future__ import annotations

import json
from pathlib import Path

import win32com.client

RESULT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_umi_shelly_followup_draft_result.json")
CSV_NAME = "UMI_commercial_PN_declines_CYH1_for_SPA.csv"


def main() -> None:
    ol = win32com.client.Dispatch("Outlook.Application")
    ns = ol.GetNamespace("MAPI")
    drafts = ns.GetDefaultFolder(16)
    removed = []
    for item in list(drafts.Items):
        try:
            subj = str(getattr(item, "Subject", "") or "")
            to = str(getattr(item, "To", "") or "")
        except Exception:
            continue
        if "Meeting" not in subj:
            continue
        if "Shelly" not in to and "shelly" not in to.lower():
            continue
        atts = item.Attachments
        for i in range(atts.Count, 0, -1):
            try:
                name = str(atts.Item(i).FileName)
            except Exception:
                continue
            if name == CSV_NAME:
                atts.Item(i).Delete()
                removed.append(name)
        try:
            item.Save()
        except Exception:
            pass
    out = {"removed": removed, "sent": False}
    RESULT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
