#!/usr/bin/env python3
"""Create ONE Outlook draft for all IDS 2026 country packs v1.3 (Save — do NOT Send).

Attaches IDS_2026_Country_Packs_v1.3_ALL.zip (+ optional INDEX.md).
Deletes prior individual country v1.3 drafts (subject pattern) to avoid clutter.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from ids_paths import ISZE_ROOT

PACK_ROOT_DEFAULT = ISZE_ROOT / "09_meetings" / "IDS_2026_Country_Packs_v1.3"
JEROME_EMAIL = "jerome.van.der.pluym@isuzu-e.com"
OL_FOLDER_DRAFTS = 16
OL_MSG = 3

# Distribution: Bart / Tomoe / Koen (prior owners) — all in To
TO_RECIPIENTS = [
    "bart.symons@isuzu-e.com",
    "Tomoe.Baumann@isuzu.de",
    "koen.matheussen@isuzu-e.com",
]

COMBINED_SUBJECT = "IDS 2026 — Country dealer compare packs v1.3 (map)"

# Individual drafts from the previous 12-mail batch
INDIVIDUAL_SUBJECT_RE = re.compile(
    r"^IDS 2026 — .+ dealer compare v1\.3 \(map\)$"
)


def _get_outlook():
    import win32com.client  # type: ignore

    return win32com.client.Dispatch("Outlook.Application")


def _default_drafts_folder(outlook):
    ns = outlook.GetNamespace("MAPI")
    drafts = ns.GetDefaultFolder(OL_FOLDER_DRAFTS)
    store = ns.DefaultStore
    return drafts, {
        "store": store.DisplayName,
        "folder_path": drafts.FolderPath,
        "file_path": str(getattr(store, "FilePath", "") or ""),
    }


def delete_individual_v13_drafts(drafts_folder) -> list[str]:
    """Delete old per-country IDS v1.3 drafts; keep combined subject if present."""
    deleted: list[str] = []
    items = list(drafts_folder.Items)
    for item in items:
        try:
            subj = str(getattr(item, "Subject", "") or "")
        except Exception:  # noqa: BLE001
            continue
        if subj == COMBINED_SUBJECT:
            try:
                item.Delete()
                deleted.append(subj + " (prior combined)")
            except Exception as exc:  # noqa: BLE001
                print(f"WARN could not delete '{subj}': {exc}", flush=True)
            continue
        if INDIVIDUAL_SUBJECT_RE.match(subj):
            try:
                item.Delete()
                deleted.append(subj)
            except Exception as exc:  # noqa: BLE001
                print(f"WARN could not delete '{subj}': {exc}", flush=True)
    return deleted


def combined_body(manifest_rows: list[dict]) -> str:
    countries = [r["country"] for r in manifest_rows]
    country_lines = "\n".join(f"  • {c}" for c in countries)
    return (
        "Dear colleagues,\n\n"
        "Please find attached the IDS 2026 country dealer compare packs "
        "(v1.3, with map).\n\n"
        "Attachment\n"
        "• IDS_2026_Country_Packs_v1.3_ALL.zip — contains the 12 individual "
        "country zips plus INDEX.md and manifest.json (no unpacked folders).\n"
        "• INDEX.md is also attached separately for a quick overview.\n"
        "• Open one country zip to get that market’s HTML + README.\n\n"
        "Included countries (country-only files; no Benelux rollup)\n"
        f"{country_lines}\n\n"
        "Not included in this pack set\n"
        "  • UK LCV (IUK)\n"
        "  • Portugal (Imotors pack — separate)\n"
        "  • Israel LCV (UMI IDS pack)\n"
        "  • MIDI networks (France / Italy / Spain / Switzerland)\n"
        "  • Benelux combined rollup (Belgium, Netherlands and Luxembourg "
        "are each a separate pack)\n\n"
        "What each country HTML includes\n"
        "  • Map tab (Leaflet) — hover shows dealer score vs that country’s "
        "national average\n"
        "  • National average and anonymous full-network average benchmarks\n"
        "  • Single-market scope — no Country filter tab\n"
        "  • Changelog tab removed (colleague / shared packs)\n\n"
        "Open the HTML with an internet connection so map tiles can load.\n\n"
        "Kind regards,\n"
        "Jérôme Van der Pluym\n"
    )


def create_one_draft(
    pack_root: Path,
    *,
    dry_run: bool = False,
    clean_old: bool = True,
    display: bool = True,
) -> dict:
    manifest_path = pack_root / "manifest.json"
    drafts_meta = pack_root / "draft_emails.json"
    all_zip = pack_root / "IDS_2026_Country_Packs_v1.3_ALL.zip"
    index_md = pack_root / "INDEX.md"

    if drafts_meta.is_file():
        rows = json.loads(drafts_meta.read_text(encoding="utf-8"))
    elif manifest_path.is_file():
        rows = json.loads(manifest_path.read_text(encoding="utf-8")).get("countries") or []
    else:
        raise SystemExit(f"Missing {drafts_meta} / {manifest_path} — rebuild packs first")

    if not all_zip.is_file():
        raise SystemExit(f"Missing {all_zip} — rebuild packs first")

    body = combined_body(rows)
    to_line = "; ".join(TO_RECIPIENTS)
    result: dict = {
        "subject": COMBINED_SUBJECT,
        "to": to_line,
        "bcc": JEROME_EMAIL,
        "attach_all_zip": str(all_zip),
        "attach_index": str(index_md) if index_md.is_file() else None,
        "countries": [r["country"] for r in rows],
    }

    if dry_run:
        result["status"] = "dry_run"
        return result

    outlook = _get_outlook()
    drafts_folder, store_info = _default_drafts_folder(outlook)
    result["store"] = store_info
    print(
        f"Target Drafts: {store_info['folder_path']} (store={store_info['store']})",
        flush=True,
    )

    deleted: list[str] = []
    if clean_old:
        deleted = delete_individual_v13_drafts(drafts_folder)
        result["deleted_prior_drafts"] = deleted
        print(f"Removed {len(deleted)} prior IDS v1.3 draft(s)", flush=True)

    mail = outlook.CreateItem(0)
    mail.Subject = COMBINED_SUBJECT
    mail.To = to_line
    mail.BCC = JEROME_EMAIL
    mail.Body = body
    mail.Attachments.Add(str(all_zip))
    if index_md.is_file():
        mail.Attachments.Add(str(index_md))

    mail.Save()
    try:
        mail = mail.Move(drafts_folder)
    except Exception as move_exc:  # noqa: BLE001
        result["move_warn"] = str(move_exc)
        mail.Save()

    result["entryid"] = str(getattr(mail, "EntryID", "") or "")
    result["attachments"] = int(mail.Attachments.Count)
    result["status"] = "draft_saved"

    msg_path = pack_root / "IDS_2026_Country_Packs_v1.3_ALL_draft.msg"
    try:
        mail.SaveAs(str(msg_path), OL_MSG)
        result["msg_fallback"] = str(msg_path)
    except Exception as exc:  # noqa: BLE001
        result["msg_fallback"] = f"FAILED: {exc}"

    if display:
        try:
            mail.Display(False)
            result["displayed"] = True
        except Exception as disp_exc:  # noqa: BLE001
            result["display_warn"] = str(disp_exc)

    # Count remaining IDS v1.3 drafts
    ids_count = 0
    try:
        for item in drafts_folder.Items:
            subj = str(getattr(item, "Subject", "") or "")
            if "IDS 2026" in subj and "v1.3" in subj:
                ids_count += 1
    except Exception:  # noqa: BLE001
        ids_count = -1
    result["ids_v13_in_drafts_after"] = ids_count
    result["how_to_find"] = (
        f"Outlook -> mailbox '{store_info['store']}' -> Drafts "
        f"({store_info['folder_path']}). Subject: {COMBINED_SUBJECT}. "
        f".msg fallback: {msg_path}"
    )
    print(
        f"Draft saved: To={to_line} BCC={JEROME_EMAIL} "
        f"att={result['attachments']} EntryID={result['entryid'][:24]}…",
        flush=True,
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack-root", type=Path, default=PACK_ROOT_DEFAULT)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--no-clean-old",
        action="store_true",
        help="Do not delete prior individual country v1.3 drafts",
    )
    parser.add_argument(
        "--no-display",
        action="store_true",
        help="Do not open the draft inspector",
    )
    args = parser.parse_args()
    result = create_one_draft(
        args.pack_root,
        dry_run=args.dry_run,
        clean_old=not args.no_clean_old,
        display=not args.no_display,
    )
    out = args.pack_root / "outlook_one_draft_result.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False), flush=True)
    print(f"Wrote {out}", flush=True)
    return 0 if result.get("status") in ("draft_saved", "dry_run") else 1


if __name__ == "__main__":
    raise SystemExit(main())
