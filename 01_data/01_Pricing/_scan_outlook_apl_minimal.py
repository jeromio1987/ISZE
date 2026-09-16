"""Minimal Outlook Restrict-only APL find (flush prints; no brute loop)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import win32com.client

ITUK = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\APL_ITUK_202607")
UTI = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\APL_UTI_P700")
META = Path(
    r"C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_raw\outlook_APL_minimal_20260812.json"
)
MD = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\OUTLOOK_APL_MAIL_SCAN.md")


def log(msg: str) -> None:
    print(msg, flush=True)


def save_mail(mail, dest: Path, tag: str, found: list[str]) -> list[str]:
    dest.mkdir(parents=True, exist_ok=True)
    stamp = str(mail.ReceivedTime)[:10]
    saved = []
    for i in range(1, mail.Attachments.Count + 1):
        att = mail.Attachments.Item(i)
        name = att.FileName
        low = name.lower()
        if low.endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp")):
            continue
        if not (
            low.endswith((".zip", ".xlsx", ".xls", ".xlsm", ".csv", ".pdf", ".7z"))
            or "20260714" in low
            or "apl" in low
        ):
            continue
        safe = re.sub(r"[^\w.\-]+", "_", name)
        path = dest / f"{stamp}_{tag}_{safe}"
        att.SaveAsFile(str(path))
        saved.append(str(path))
        found.append(str(path))
        log(f"SAVED {path}")
    return saved


def main() -> None:
    log("starting Outlook COM…")
    ol = win32com.client.Dispatch("Outlook.Application")
    ns = ol.GetNamespace("MAPI")
    log("MAPI ok")

    filters = [
        ("rec_parts", "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001f\" LIKE '%Recommended parts%'"),
        ("apl_subj", "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001f\" LIKE '%APL%'"),
        ("p700", "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001f\" LIKE '%P700%'"),
        ("vr05", "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001f\" LIKE '%VR05%'"),
        ("uti_p700", "@SQL=\"http://schemas.microsoft.com/mapi/proptag/0x0037001f\" LIKE '%UTI%P700%'"),
    ]

    hits = []
    found: list[str] = []
    seen = set()

    for folder, fname in [
        (ns.GetDefaultFolder(6), "Inbox"),
        (ns.GetDefaultFolder(5), "Sent"),
    ]:
        items = folder.Items
        items.Sort("[ReceivedTime]", True)
        for label, filt in filters:
            try:
                sub = items.Restrict(filt)
                # Count can hang on huge folders — iterate with cap instead
                log(f"{fname}/{label} iterating…")
                c = 0
                for mail in sub:
                    c += 1
                    if c > 40:
                        break
                    try:
                        eid = str(mail.EntryID)
                        if eid in seen:
                            continue
                        seen.add(eid)
                        if mail.Class != 43:
                            continue
                        subj = str(mail.Subject or "")
                        body = str(mail.Body or "")
                        sender = str(getattr(mail, "SenderName", "") or "")
                        atts = [
                            mail.Attachments.Item(i).FileName
                            for i in range(1, mail.Attachments.Count + 1)
                        ]
                        blob = f"{subj} {body} {sender} {' '.join(atts)}".lower()
                        tags = []
                        if (
                            "recommended parts" in blob
                            or "20260714" in blob
                            or ("vr05" in blob and "apl" in blob)
                            or ("suzuki" in blob and "apl" in blob)
                            or ("ituk" in blob and ("apl" in blob or "recommended parts" in blob))
                        ):
                            tags.append("ITUK_APL")
                        if (
                            ("uti" in blob and "p700" in blob)
                            or ("p700" in blob and re.search(r"\bapl\b", blob))
                            or ("uti" in blob and re.search(r"\bapl\b", blob) and "p700" in blob)
                        ):
                            tags.append("UTI_P700_APL")
                        if not tags and label in ("rec_parts", "vr05"):
                            tags.append("ITUK_APL")
                        if not tags and label == "uti_p700":
                            tags.append("UTI_P700_APL")
                        if not tags and label == "p700" and "apl" not in blob and "uti" not in blob:
                            continue  # generic P700 order noise
                        if not tags:
                            continue

                        log(f"HIT {fname} {str(mail.ReceivedTime)[:19]} {tags} {subj[:80]}")
                        saved = []
                        if "ITUK_APL" in tags:
                            saved += save_mail(mail, ITUK, "ITUK", found)
                        if "UTI_P700_APL" in tags:
                            saved += save_mail(mail, UTI, "UTI_P700", found)
                        hits.append(
                            {
                                "folder": fname,
                                "filter": label,
                                "received": str(mail.ReceivedTime),
                                "subject": subj,
                                "sender": sender,
                                "tags": tags,
                                "attachments": atts,
                                "saved": saved,
                                "preview": " ".join(body.split())[:400],
                            }
                        )
                    except Exception as e:
                        log(f"mail err {e}")
                log(f"{fname}/{label} done scanned={c}")
            except Exception as e:
                log(f"restrict fail {fname}/{label}: {e}")

    ituk = [h for h in hits if "ITUK_APL" in h["tags"]]
    uti = [h for h in hits if "UTI_P700_APL" in h["tags"]]

    META.parent.mkdir(parents=True, exist_ok=True)
    META.write_text(
        json.dumps(
            {
                "rg21": "RG21 = D-Max 2.2L",
                "hits": hits,
                "ituk": len(ituk),
                "uti_p700": len(uti),
                "saved": sorted(set(found)),
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
        f"- ITUK APL hits: **{len(ituk)}**",
        f"- UTI P700 APL hits: **{len(uti)}**",
        f"- Files saved: **{len(set(found))}**",
        "",
        "## ITUK APL",
        "",
    ]
    if not ituk:
        lines.append(
            "**Not found** via Restrict on Inbox/Sent for Recommended parts / APL / VR05. "
            "Please forward Suzuki 23 Jul 2026 mail or drop `20260714_1037.zip` into "
            "`01_data/90_INBOX/APL_ITUK_202607/`."
        )
        lines.append("")
    for h in ituk:
        lines.append(f"- {h['received'][:19]} | {h['subject']}")
        lines.append(f"  - from: {h['sender']}")
        lines.append(
            f"  - attachments: {', '.join(a for a in h['attachments'] if not str(a).lower().endswith(('.png','.jpg','.gif')))}"
        )
        if h["saved"]:
            lines.append(f"  - saved: {', '.join(h['saved'])}")
        lines.append("")

    lines += ["## UTI P700 APL", ""]
    if not uti:
        lines.append(
            "**Not found** via Restrict on Inbox/Sent for UTI+P700+APL. "
            "Forward the mail or drop files into `01_data/90_INBOX/APL_UTI_P700/`."
        )
        lines.append("")
    for h in uti:
        lines.append(f"- {h['received'][:19]} | {h['subject']}")
        lines.append(f"  - from: {h['sender']}")
        lines.append(
            f"  - attachments: {', '.join(a for a in h['attachments'] if not str(a).lower().endswith(('.png','.jpg','.gif')))}"
        )
        if h["saved"]:
            lines.append(f"  - saved: {', '.join(h['saved'])}")
        lines.append("")

    lines += ["## Saved files", ""]
    for f in sorted(set(found)):
        lines.append(f"- `{f}`")
    if not found:
        lines.append("_None this pass._")

    MD.write_text("\n".join(lines), encoding="utf-8")
    log(f"DONE ituk={len(ituk)} uti={len(uti)} files={len(set(found))}")
    log(str(MD))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"FATAL {e}")
        sys.exit(1)
