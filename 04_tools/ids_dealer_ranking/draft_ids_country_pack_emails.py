#!/usr/bin/env python3
"""Create Outlook draft emails for IDS 2026 country packs (Save — do NOT Send).

Reads draft_emails.json from the pack root produced by build_ids_country_packs_v13.py.
Attaches the country zip + HTML. Uses Outlook COM CreateItem(0).Save().

Forces items into the default store's Drafts folder (Move after Save) so they
appear under the primary mailbox Drafts, not a secondary store.

By default replaces any existing Drafts with the same subject (avoids duplicates
after a pack rebuild). Never Sends.

Also writes .msg fallbacks under the pack folder when --msg-fallback is set
(or automatically if Save fails).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ids_paths import ISZE_ROOT

PACK_ROOT_DEFAULT = ISZE_ROOT / "09_meetings" / "IDS_2026_Country_Packs_v1.3"
JEROME_EMAIL = "jerome.van.der.pluym@isuzu-e.com"
OL_FOLDER_DRAFTS = 16
OL_MSG = 3  # olMSG


def _get_outlook():
    try:
        import win32com.client  # type: ignore
    except ImportError:
        print("pywin32 not available — trying comtypes / EnsureDispatch path", flush=True)
        try:
            import win32com.client.gencache as gencache  # type: ignore

            return gencache.EnsureDispatch("Outlook.Application")
        except Exception as exc:  # noqa: BLE001
            raise SystemExit(
                "Cannot create Outlook drafts: install pywin32 "
                f"(pip install pywin32). Detail: {exc}"
            ) from exc
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


def delete_matching_drafts(drafts_folder, subjects: set[str]) -> int:
    """Delete Drafts folder items whose Subject is in subjects. Returns count deleted."""
    if not subjects:
        return 0
    deleted = 0
    items = list(drafts_folder.Items)
    for item in items:
        try:
            subj = str(getattr(item, "Subject", "") or "")
        except Exception:  # noqa: BLE001
            continue
        if subj in subjects:
            try:
                item.Delete()
                deleted += 1
            except Exception as exc:  # noqa: BLE001
                print(f"WARN could not delete draft '{subj}': {exc}", flush=True)
    return deleted


def _save_msg_fallback(mail, msg_path: Path) -> str | None:
    try:
        msg_path.parent.mkdir(parents=True, exist_ok=True)
        # 3 = olMSG
        mail.SaveAs(str(msg_path), OL_MSG)
        return str(msg_path)
    except Exception as exc:  # noqa: BLE001
        return f"FAILED: {exc}"


def create_drafts(
    manifest_path: Path,
    *,
    dry_run: bool = False,
    replace_existing: bool = True,
    msg_fallback: bool = True,
    display_first: bool = False,
) -> list[dict]:
    rows = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise SystemExit(f"Expected list in {manifest_path}")

    results: list[dict] = []
    if dry_run:
        for r in rows:
            results.append(
                {
                    "country": r["country"],
                    "subject": r["subject"],
                    "to": r.get("to_email") or "",
                    "bcc": r.get("bcc") or JEROME_EMAIL,
                    "attach": r.get("zip_path"),
                    "status": "dry_run",
                    "replace_existing": replace_existing,
                }
            )
        return results

    outlook = _get_outlook()
    drafts_folder, store_info = _default_drafts_folder(outlook)
    print(
        f"Target Drafts: {store_info['folder_path']} "
        f"(store={store_info['store']})",
        flush=True,
    )

    subjects = {r["subject"] for r in rows if r.get("subject")}
    replaced = 0
    if replace_existing:
        replaced = delete_matching_drafts(drafts_folder, subjects)
        print(f"Removed {replaced} existing draft(s) with matching subjects", flush=True)

    pack_root = manifest_path.parent
    msg_dir = pack_root / "_outlook_msg_fallbacks"
    first_displayed = False

    for r in rows:
        to_email = (r.get("to_email") or "").strip()
        bcc = (r.get("bcc") or JEROME_EMAIL).strip()
        row_out: dict = {
            "country": r["country"],
            "subject": r["subject"],
            "to": to_email or "(blank — fill To)",
            "bcc": bcc,
            "attach_zip": r.get("zip_path"),
            "attach_html": r.get("html_path"),
            "store": store_info["store"],
            "folder_path": store_info["folder_path"],
            "replaced_prior": replaced > 0,
        }
        try:
            mail = outlook.CreateItem(0)  # olMailItem
            mail.Subject = r["subject"]
            if to_email:
                mail.To = to_email
            mail.BCC = bcc
            mail.Body = r["body"]
            if not to_email:
                mail.Body = (
                    "[NOTE: fill To — no documented colleague address for this country]\n\n"
                    + mail.Body
                )
            zip_path = Path(r["zip_path"])
            if zip_path.is_file():
                mail.Attachments.Add(str(zip_path))
            else:
                mail.Body = f"[WARNING: zip missing: {zip_path}]\n\n" + mail.Body
                row_out["zip_missing"] = True
            html_path = Path(r["html_path"])
            if html_path.is_file():
                mail.Attachments.Add(str(html_path))
            else:
                row_out["html_missing"] = True

            # Save first (creates draft), then Move into default Drafts explicitly.
            mail.Save()
            try:
                moved = mail.Move(drafts_folder)
                mail = moved
            except Exception as move_exc:  # noqa: BLE001
                row_out["move_warn"] = str(move_exc)
                # Re-save in place if Move fails
                mail.Save()

            row_out["entryid"] = str(getattr(mail, "EntryID", "") or "")
            row_out["attachments"] = int(mail.Attachments.Count)
            row_out["status"] = "draft_saved"

            if msg_fallback:
                slug = r.get("slug") or r["country"].replace(" ", "_")
                msg_path = msg_dir / f"IDS_2026_{slug}_v1.3_draft.msg"
                msg_result = _save_msg_fallback(mail, msg_path)
                row_out["msg_fallback"] = msg_result

            if display_first and not first_displayed:
                try:
                    # Modal=False — opens inspector so Jerome can see it
                    mail.Display(False)
                    first_displayed = True
                    row_out["displayed"] = True
                except Exception as disp_exc:  # noqa: BLE001
                    row_out["display_warn"] = str(disp_exc)

            print(
                f"Draft saved: {r['country']} -> To={to_email or '(blank)'} "
                f"BCC={bcc} EntryID={row_out['entryid'][:24]}… "
                f"att={row_out['attachments']}",
                flush=True,
            )
        except Exception as exc:  # noqa: BLE001
            row_out["status"] = "FAILED"
            row_out["error"] = str(exc)
            print(f"FAILED {r['country']}: {exc}", flush=True)
            # Hint for Outlook Object Model Guard / security prompt
            err_l = str(exc).lower()
            if any(
                k in err_l
                for k in ("operation aborted", "blocked", "access", "security", "denied")
            ):
                row_out["blocker_hint"] = (
                    "Outlook security / Object Model Guard may be blocking Save. "
                    "Fallback: open drafts with Display(False) then Save manually, "
                    f"or double-click .msg files in {msg_dir}."
                )
                print(row_out["blocker_hint"], flush=True)

        results.append(row_out)

    # Refresh count
    try:
        count_after = drafts_folder.Items.Count
    except Exception:  # noqa: BLE001
        count_after = None
    ids_count = 0
    try:
        for item in drafts_folder.Items:
            subj = str(getattr(item, "Subject", "") or "")
            if "IDS 2026" in subj and "v1.3" in subj:
                ids_count += 1
    except Exception:  # noqa: BLE001
        ids_count = -1

    summary = {
        "store": store_info,
        "drafts_total_after": count_after,
        "ids_v13_in_drafts": ids_count,
        "created": len([x for x in results if x.get("status") == "draft_saved"]),
        "failed": len([x for x in results if x.get("status") == "FAILED"]),
        "how_to_find": (
            f"Outlook -> mailbox '{store_info['store']}' -> Drafts "
            f"({store_info['folder_path']}). "
            "Filter/search subject: IDS 2026 v1.3. "
            f"Do not look under Sales/Parts shared-mailbox Drafts. "
            f".msg fallbacks: {msg_dir}"
        ),
    }
    results_payload = {"summary": summary, "drafts": results}
    try:
        print(json.dumps(summary, indent=2, ensure_ascii=False), flush=True)
    except UnicodeEncodeError:
        print(json.dumps(summary, indent=2, ensure_ascii=True), flush=True)
    return results_payload  # type: ignore[return-value]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=PACK_ROOT_DEFAULT / "draft_emails.json",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned drafts without calling Outlook",
    )
    parser.add_argument(
        "--no-replace",
        action="store_true",
        help="Do not delete existing Drafts with the same subject before creating",
    )
    parser.add_argument(
        "--no-msg-fallback",
        action="store_true",
        help="Do not write .msg files under _outlook_msg_fallbacks/",
    )
    parser.add_argument(
        "--display-first",
        action="store_true",
        help="Open the first draft inspector (non-modal) so it is visible",
    )
    args = parser.parse_args()
    if not args.manifest.is_file():
        print(f"Missing {args.manifest} — run build_ids_country_packs_v13.py first")
        return 1
    results = create_drafts(
        args.manifest,
        dry_run=args.dry_run,
        replace_existing=not args.no_replace,
        msg_fallback=not args.no_msg_fallback,
        display_first=args.display_first,
    )
    out = args.manifest.parent / "outlook_drafts_result.json"
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    n = len(results["drafts"]) if isinstance(results, dict) else len(results)
    print(f"Wrote {out} ({n} drafts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
