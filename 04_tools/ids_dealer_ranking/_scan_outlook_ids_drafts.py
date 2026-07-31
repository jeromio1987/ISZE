#!/usr/bin/env python3
"""Scan Outlook stores for IDS 2026 v1.3 drafts (diagnostic)."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import win32com.client

OUT = Path(__file__).resolve().parents[2] / "09_meetings" / "IDS_2026_Country_Packs_v1.3" / "_outlook_draft_scan.json"


def main() -> None:
    outlook = win32com.client.Dispatch("Outlook.Application")
    ns = outlook.GetNamespace("MAPI")

    report: dict = {
        "default_store": {},
        "stores": [],
        "ids_v13_matches": [],
        "recent_drafts": [],
        "deleted_ids": [],
        "outbox": [],
    }

    default_store = ns.DefaultStore
    report["default_store"] = {
        "DisplayName": default_store.DisplayName,
        "FilePath": str(getattr(default_store, "FilePath", "") or ""),
        "ExchangeStoreType": getattr(default_store, "ExchangeStoreType", None),
    }
    drafts = ns.GetDefaultFolder(16)
    report["default_store"]["DraftsFolderPath"] = drafts.FolderPath
    report["default_store"]["DraftsCount"] = drafts.Items.Count
    report["default_store"]["DraftsStore"] = drafts.Store.DisplayName
    try:
        cu = ns.CurrentUser
        report["current_user"] = {
            "Name": cu.Name,
            "Address": str(getattr(cu, "Address", "") or ""),
        }
    except Exception as exc:  # noqa: BLE001
        report["current_user"] = {"error": str(exc)}

    cutoff = datetime.now() - timedelta(days=14)

    def find_drafts(folder, depth: int = 0):
        hits = []
        try:
            fname = (folder.Name or "").lower()
            if fname in ("drafts", "concepten", "brouillons", "entwürfe", "entwuerfe"):
                hits.append(folder)
            if depth < 3:
                for j in range(1, folder.Folders.Count + 1):
                    try:
                        hits.extend(find_drafts(folder.Folders.Item(j), depth + 1))
                    except Exception:  # noqa: BLE001
                        pass
        except Exception:  # noqa: BLE001
            pass
        return hits

    for i in range(1, ns.Stores.Count + 1):
        store = ns.Stores.Item(i)
        name = store.DisplayName
        store_info = {
            "index": i,
            "DisplayName": name,
            "ExchangeStoreType": getattr(store, "ExchangeStoreType", None),
            "FilePath": str(getattr(store, "FilePath", "") or ""),
            "draft_folders": [],
        }
        try:
            root = store.GetRootFolder()
        except Exception as exc:  # noqa: BLE001
            store_info["error"] = str(exc)
            report["stores"].append(store_info)
            continue

        draft_folders = find_drafts(root)
        try:
            sdf = store.GetDefaultFolder(16)
            if sdf is not None:
                paths = {f.FolderPath for f in draft_folders}
                if sdf.FolderPath not in paths:
                    draft_folders.append(sdf)
        except Exception:  # noqa: BLE001
            pass

        for df in draft_folders:
            try:
                count = df.Items.Count
            except Exception as exc:  # noqa: BLE001
                store_info["draft_folders"].append(
                    {"path": "?", "error": str(exc)}
                )
                continue
            df_info = {"path": df.FolderPath, "count": count, "ids_hits": 0}
            items = df.Items
            try:
                items.Sort("[LastModificationTime]", True)
            except Exception:  # noqa: BLE001
                pass
            scanned = 0
            for item in items:
                scanned += 1
                if scanned > 800:
                    break
                try:
                    subj = str(getattr(item, "Subject", "") or "")
                    mod = getattr(item, "LastModificationTime", None)
                    created = getattr(item, "CreationTime", None)
                    eid = str(getattr(item, "EntryID", "") or "")
                    att = 0
                    try:
                        att = item.Attachments.Count
                    except Exception:  # noqa: BLE001
                        pass
                    entry = {
                        "store": name,
                        "folder": df.FolderPath,
                        "subject": subj,
                        "modified": str(mod),
                        "created": str(created),
                        "entryid": eid,
                        "attachments": att,
                    }
                    if "IDS 2026" in subj and "v1.3" in subj:
                        report["ids_v13_matches"].append(entry)
                        df_info["ids_hits"] += 1
                    try:
                        mod_naive = mod.replace(tzinfo=None) if hasattr(mod, "replace") else mod
                        if mod_naive and mod_naive >= cutoff:
                            report["recent_drafts"].append(
                                {
                                    "store": name,
                                    "folder": df.FolderPath,
                                    "subject": subj[:120],
                                    "modified": str(mod),
                                    "attachments": att,
                                }
                            )
                    except Exception:  # noqa: BLE001
                        pass
                except Exception:  # noqa: BLE001
                    pass
            store_info["draft_folders"].append(df_info)
        report["stores"].append(store_info)

    try:
        deleted = ns.GetDefaultFolder(3)
        report["deleted_folder"] = {
            "path": deleted.FolderPath,
            "count": deleted.Items.Count,
        }
        n = 0
        for item in deleted.Items:
            n += 1
            if n > 400:
                break
            subj = str(getattr(item, "Subject", "") or "")
            if "IDS 2026" in subj:
                report["deleted_ids"].append(
                    {
                        "subject": subj,
                        "modified": str(getattr(item, "LastModificationTime", None)),
                    }
                )
    except Exception as exc:  # noqa: BLE001
        report["deleted_folder"] = {"error": str(exc)}

    try:
        outbox = ns.GetDefaultFolder(4)
        report["outbox_count"] = outbox.Items.Count
        for item in outbox.Items:
            report["outbox"].append(str(getattr(item, "Subject", "") or ""))
    except Exception as exc:  # noqa: BLE001
        report["outbox_error"] = str(exc)

    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Wrote", OUT)
    print("Default Drafts:", report["default_store"].get("DraftsFolderPath"),
          "count=", report["default_store"].get("DraftsCount"))
    print("IDS v1.3 matches:", len(report["ids_v13_matches"]))
    for m in report["ids_v13_matches"]:
        print(" ", m["folder"], "|", m["subject"], "| att=", m["attachments"])
    print("Recent drafts (14d):", len(report["recent_drafts"]))
    for m in report["recent_drafts"][:25]:
        print(" ", m["store"], "|", m["subject"], "|", m["modified"])
    print("Deleted IDS:", len(report["deleted_ids"]))
    for m in report["deleted_ids"][:20]:
        print(" ", m["subject"])


if __name__ == "__main__":
    main()
