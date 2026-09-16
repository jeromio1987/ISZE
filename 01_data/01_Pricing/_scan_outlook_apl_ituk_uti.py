"""Outlook APL hunt: ITUK Recommended parts list + UTI P700 APL.

RG21 = D-Max 2.2L.
Saves zip/xlsx/pdf under 90_INBOX/APL_ITUK_202607 and 90_INBOX/APL_UTI_P700.
Does not invent part numbers.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import win32com.client

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data")
ITUK_DIR = ROOT / "90_INBOX" / "APL_ITUK_202607"
UTI_DIR = ROOT / "90_INBOX" / "APL_UTI_P700"
META = ROOT / "01_Pricing" / "_raw" / "outlook_APL_ITUK_UTI_scan_20260812.json"
MD = ROOT / "01_Pricing" / "OUTLOOK_APL_MAIL_SCAN.md"

SUBJ_FILTERS = [
    "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001f\" LIKE '%Recommended parts list%'",
    "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001f\" LIKE '%Recommended parts%'",
    "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001f\" LIKE '%APL%'",
    "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001f\" LIKE '%P700%'",
    "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001f\" LIKE '%VR05%'",
]


def classify(subj: str, body: str, sender: str, atts: list[str]) -> list[str]:
    blob = f"{subj} {body} {sender} {' '.join(atts)}".lower()
    tags: list[str] = []
    if "ituk" in blob or "recommended parts list" in blob or "vr05" in blob or "d-gr" in blob:
        if re.search(r"\bapl\b", blob) or "recommended parts" in blob or "20260714" in blob:
            tags.append("ITUK_APL")
    if ("uti" in blob and ("p700" in blob or "apl" in blob)) or (
        "p700" in blob and re.search(r"\bapl\b", blob)
    ):
        tags.append("UTI_P700_APL")
    if "p700" in blob and "apl" in blob and "UTI_P700_APL" not in tags:
        tags.append("UTI_P700_APL")
    if not tags:
        # attachment-driven
        att_l = " ".join(atts).lower()
        if "20260714" in att_l or ("apl" in att_l and "ituk" in blob):
            tags.append("ITUK_APL")
        if "p700" in att_l and ("apl" in att_l or "uti" in blob):
            tags.append("UTI_P700_APL")
    return tags


def save_atts(mail, dest_dir: Path, prefix: str, found: list[str]) -> list[str]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    stamp = str(mail.ReceivedTime)[:10]
    saved = []
    for i in range(1, mail.Attachments.Count + 1):
        try:
            att = mail.Attachments.Item(i)
            an = att.FileName
            low = an.lower()
            if low.endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp")):
                continue
            keep = low.endswith(
                (".zip", ".xlsx", ".xls", ".xlsm", ".csv", ".pdf", ".7z")
            ) or any(k in low for k in ("20260714", "apl", "vr05", "p700", "parts"))
            if not keep:
                continue
            safe = re.sub(r"[^\w.\-]+", "_", an)
            dest = dest_dir / f"{stamp}_{prefix}_{safe}"
            att.SaveAsFile(str(dest))
            saved.append(str(dest))
            found.append(str(dest))
            print("SAVED", dest)
        except Exception as e:
            print("SAVE_ERR", e)
    return saved


def process_mail(mail, folder_name: str, hits: list, found: list) -> None:
    if mail.Class != 43:
        return
    subj = str(mail.Subject or "")
    body = str(mail.Body or "")
    sender = str(getattr(mail, "SenderName", "") or "")
    atts = []
    for i in range(1, mail.Attachments.Count + 1):
        try:
            atts.append(mail.Attachments.Item(i).FileName)
        except Exception:
            pass
    tags = classify(subj, body, sender, atts)
    # also force-include if subject strongly matches
    sl = subj.lower()
    if "recommended parts list" in sl and "ITUK_APL" not in tags:
        tags.append("ITUK_APL")
    if not tags:
        return

    saved_all = []
    if "ITUK_APL" in tags:
        saved_all += save_atts(mail, ITUK_DIR, "ITUK", found)
    if "UTI_P700_APL" in tags:
        saved_all += save_atts(mail, UTI_DIR, "UTI_P700", found)
    # if tagged but nothing saved yet, still try both dirs for zip/xlsx
    if not saved_all:
        if "ITUK_APL" in tags:
            saved_all += save_atts(mail, ITUK_DIR, "ITUK", found)
        if "UTI_P700_APL" in tags:
            saved_all += save_atts(mail, UTI_DIR, "UTI_P700", found)

    hits.append(
        {
            "folder": folder_name,
            "received": str(mail.ReceivedTime),
            "subject": subj,
            "sender": sender,
            "tags": tags,
            "attachments": atts,
            "saved": saved_all,
            "preview": " ".join(body.split())[:500],
        }
    )
    print(
        "HIT",
        folder_name,
        str(mail.ReceivedTime)[:19],
        tags,
        subj[:90],
    )


def scan_folder(folder, name: str, hits: list, found: list, seen_ids: set) -> None:
    items = folder.Items
    items.Sort("[ReceivedTime]", True)

    # Restrict passes
    for filt in SUBJ_FILTERS:
        try:
            sub = items.Restrict(filt)
            sub.Sort("[ReceivedTime]", True)
            print(f"{name} restrict ~{sub.Count} :: {filt[-50:]}")
            c = 0
            for mail in sub:
                c += 1
                if c > 60:
                    break
                try:
                    mid = str(mail.EntryID)
                    if mid in seen_ids:
                        continue
                    seen_ids.add(mid)
                    process_mail(mail, name, hits, found)
                except Exception as e:
                    print("mail err", e)
        except Exception as e:
            print("restrict err", name, e)

    # Brute: first N for attachment zip names / strong subjects
    n = 0
    for mail in items:
        n += 1
        if n > 3500:
            break
        try:
            if mail.Class != 43:
                continue
            mid = str(mail.EntryID)
            if mid in seen_ids:
                continue
            subj = str(mail.Subject or "").lower()
            att_names = []
            for i in range(1, mail.Attachments.Count + 1):
                try:
                    att_names.append(mail.Attachments.Item(i).FileName)
                except Exception:
                    pass
            att_l = " ".join(att_names).lower()
            interesting = (
                "recommended parts" in subj
                or ("apl" in subj and ("ituk" in subj or "uti" in subj or "p700" in subj))
                or "20260714_1037" in att_l
                or "20260714" in att_l
                or ("apl" in att_l and att_l.endswith((".zip", ".xlsx")))
                or ("p700" in subj and "apl" in subj)
                or ("uti" in subj and "p700" in subj and "part" in subj)
            )
            if not interesting:
                continue
            seen_ids.add(mid)
            process_mail(mail, name + "_brute", hits, found)
        except Exception:
            continue


def main() -> None:
    ITUK_DIR.mkdir(parents=True, exist_ok=True)
    UTI_DIR.mkdir(parents=True, exist_ok=True)

    ol = win32com.client.Dispatch("Outlook.Application")
    ns = ol.GetNamespace("MAPI")
    inbox = ns.GetDefaultFolder(6)
    sent = ns.GetDefaultFolder(5)

    hits: list[dict] = []
    found: list[str] = []
    seen: set[str] = set()

    scan_folder(inbox, "Inbox", hits, found, seen)
    scan_folder(sent, "Sent", hits, found, seen)

    # Try a few top-level folders by name
    try:
        root = ns.Folders
        for i in range(1, min(root.Count, 6) + 1):
            store = root.Item(i)
            try:
                for j in range(1, min(store.Folders.Count, 30) + 1):
                    f = store.Folders.Item(j)
                    name = str(f.Name)
                    nl = name.lower()
                    if any(
                        k in nl
                        for k in (
                            "inbox",
                            "parts",
                            "isuzu",
                            "imit",
                            "ituk",
                            "uti",
                            "apl",
                            "planning",
                        )
                    ):
                        print("extra folder", name)
                        scan_folder(f, f"Folder:{name}", hits, found, seen)
            except Exception as e:
                print("store walk err", e)
    except Exception as e:
        print("stores err", e)

    ituk = [h for h in hits if "ITUK_APL" in h["tags"]]
    uti = [h for h in hits if "UTI_P700_APL" in h["tags"]]

    META.parent.mkdir(parents=True, exist_ok=True)
    META.write_text(
        json.dumps(
            {
                "rg21_note": "RG21 = D-Max 2.2L",
                "hit_count": len(hits),
                "ituk_hits": len(ituk),
                "uti_p700_hits": len(uti),
                "saved": sorted(set(found)),
                "hits": hits,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    lines = [
        "# Outlook APL hunt — ITUK + UTI P700",
        "",
        "**RG21 = D-Max 2.2L.**",
        "",
        f"Total tagged hits: **{len(hits)}**",
        f"- ITUK APL / recommended parts: **{len(ituk)}**",
        f"- UTI P700 APL: **{len(uti)}**",
        f"- Files saved: **{len(set(found))}**",
        "",
        "## ITUK APL (Suzuki / Recommended parts list / VR05 / 20260714)",
        "",
    ]
    if not ituk:
        lines.append(
            "**Not found** in Inbox/Sent (and sampled folders) under these filters. "
            "Drop `20260714_1037.zip` into `90_INBOX/APL_ITUK_202607` or forward the Suzuki mail."
        )
        lines.append("")
    for h in ituk:
        lines.append(f"- {h['received'][:19]} | {h['subject']}")
        lines.append(f"  - from: {h['sender']} · folder: {h['folder']}")
        atts = [
            a
            for a in h["attachments"]
            if not str(a).lower().endswith((".png", ".jpg", ".jpeg", ".gif"))
        ]
        if atts:
            lines.append(f"  - attachments: {', '.join(atts)}")
        if h["saved"]:
            lines.append(f"  - saved: {', '.join(h['saved'])}")
        lines.append(f"  - preview: {h['preview'][:220]}")
        lines.append("")

    lines += ["## UTI P700 APL", ""]
    if not uti:
        lines.append(
            "**Not found** in Inbox/Sent (and sampled folders) for UTI + P700 + APL / parts list. "
            "If it lives in another mailbox/folder, forward into Inbox or save zip/xlsx under "
            "`90_INBOX/APL_UTI_P700`."
        )
        lines.append("")
    for h in uti:
        lines.append(f"- {h['received'][:19]} | {h['subject']}")
        lines.append(f"  - from: {h['sender']} · folder: {h['folder']}")
        atts = [
            a
            for a in h["attachments"]
            if not str(a).lower().endswith((".png", ".jpg", ".jpeg", ".gif"))
        ]
        if atts:
            lines.append(f"  - attachments: {', '.join(atts)}")
        if h["saved"]:
            lines.append(f"  - saved: {', '.join(h['saved'])}")
        lines.append(f"  - preview: {h['preview'][:220]}")
        lines.append("")

    lines += ["## Saved files", ""]
    for f in sorted(set(found)):
        lines.append(f"- `{f}`")
    if not found:
        lines.append("_None saved this pass._")

    MD.write_text("\n".join(lines), encoding="utf-8")
    print("DONE", "hits", len(hits), "ituk", len(ituk), "uti", len(uti), "files", len(set(found)))
    print("MD", MD)


if __name__ == "__main__":
    main()
