"""Scan Outlook for PMS history subjects (metadata + short preview)."""
from __future__ import annotations

from pathlib import Path

import win32com.client  # type: ignore

OUT = Path(__file__).with_name("_pms_email_history.txt")
KEYS = (
    "pms",
    "periodical maintenance",
    "periodic maintenance",
    "kick off",
    "kick-off",
    "wrap up",
    "vin",
    "cbu",
    "clutch",
    "filter pack",
    "ituk\\iml",
    "ituk/iml",
)


def main() -> None:
    outlook = win32com.client.Dispatch("Outlook.Application")
    ns = outlook.GetNamespace("MAPI")
    inbox = ns.GetDefaultFolder(6)
    sent = ns.GetDefaultFolder(5)
    lines = ["PMS email history (inbox+sent, 2026, keyword hit)"]
    rows = []
    for folder, label in ((inbox, "IN"), (sent, "OUT")):
        items = folder.Items
        items.Sort("[ReceivedTime]", True)
        n = 0
        for it in items:
            n += 1
            if n > 800:
                break
            try:
                t = it.ReceivedTime if label == "IN" else it.SentOn
                if t.year != 2026:
                    if n > 200 and t.year < 2026:
                        break
                    continue
                subj = str(getattr(it, "Subject", "") or "")
                who = str(getattr(it, "SenderName", "") or "") if label == "IN" else str(getattr(it, "To", "") or "")
                sl = subj.lower()
                if not any(k in sl for k in KEYS):
                    continue
                preview = str(getattr(it, "Body", "") or "").replace("\r", " ").replace("\n", " ")[:280]
                rows.append((t, label, who, subj, preview))
            except Exception:
                continue
    rows.sort(key=lambda r: r[0])
    for t, label, who, subj, preview in rows:
        lines.append(f"{t:%Y-%m-%d %H:%M} | {label} | {who} | {subj}")
        lines.append(f"    {preview}")
        lines.append("")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("wrote", OUT, "hits", len(rows))


if __name__ == "__main__":
    main()
