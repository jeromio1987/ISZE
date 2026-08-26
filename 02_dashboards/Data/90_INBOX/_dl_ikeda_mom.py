"""Download Ikeda lubricants MoM attachments from Outlook."""
from __future__ import annotations

from pathlib import Path

import win32com.client

ENTRY_IDS = [
    "00000000174BC82B22520D429348932087CC34F0070058934DF1ED3C4D4EA4EA4D7658026CCA00000000010C000058934DF1ED3C4D4EA4EA4D7658026CCA00097FB95DA40000",  # RE: Draft MoM ITUK Meeting (24 Aug)
]
OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\japan_week_mom_20260819")


def main() -> None:
    ol = win32com.client.Dispatch("Outlook.Application")
    ns = ol.GetNamespace("MAPI")
    inbox = ns.GetDefaultFolder(6)
    for eid in ENTRY_IDS:
        try:
            mail = ns.GetItemFromID(eid, inbox.StoreID)
        except Exception as exc:
            print("getitem failed", exc)
            continue
        print("MAIL:", mail.Subject, "| atts:", mail.Attachments.Count)
        for i in range(1, mail.Attachments.Count + 1):
            att = mail.Attachments.Item(i)
            fn = str(att.FileName)
            dest = OUT / fn
            att.SaveAsFile(str(dest))
            print("saved", dest, att.Size, "bytes")


if __name__ == "__main__":
    main()
