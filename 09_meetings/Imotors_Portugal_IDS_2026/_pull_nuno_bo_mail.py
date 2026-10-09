"""Pull Nuno 'Backordered lines 2026.xlsx' from Outlook if present."""
import win32com.client
from pathlib import Path
import datetime as dt

out = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_nuno_backordered_lines_20261006")
out.mkdir(parents=True, exist_ok=True)
log = []

outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
stores = []
for i in range(outlook.Stores.Count):
    stores.append(outlook.Stores.Item(i + 1))

hits = []
for store in stores:
    name = store.DisplayName
    for folder_name in ["Inbox", "Sent Items", "Archive"]:
        try:
            folder = store.GetDefaultFolder(6) if folder_name == "Inbox" else None
        except Exception as e:
            folder = None
        # walk a few key folders by name
    # Prefer Restrict on Inbox + Archive recursively shallow
    try:
        root = store.GetRootFolder()
    except Exception as e:
        log.append(f"store fail {name}: {e}")
        continue

    def walk(f, depth=0):
        if depth > 3:
            return
        try:
            fname = f.Name
        except Exception:
            return
        # skip huge system folders
        if fname in {"Sync Issues", "RSS Feeds", "Junk Email", "Deleted Items", "Calendar", "Contacts", "Tasks", "Notes"}:
            return
        try:
            items = f.Items
            items.Sort("[ReceivedTime]", True)
            # Restrict by sender / subject keywords
            try:
                restricted = items.Restrict(
                    "@SQL=("
                    "\"urn:schemas:httpmail:fromemail\" LIKE '%machado%' "
                    "OR \"urn:schemas:httpmail:subject\" LIKE '%Backorder%' "
                    "OR \"urn:schemas:httpmail:subject\" LIKE '%Questions before the meeting%'"
                    ")"
                )
            except Exception:
                restricted = items
            count = 0
            for it in restricted:
                count += 1
                if count > 200:
                    break
                try:
                    subj = str(getattr(it, "Subject", "") or "")
                    sender = str(getattr(it, "SenderEmailAddress", "") or getattr(it, "SenderName", "") or "")
                    received = getattr(it, "ReceivedTime", None)
                    att_count = it.Attachments.Count if it.Attachments else 0
                except Exception:
                    continue
                subj_l = subj.lower()
                sender_l = sender.lower()
                interesting = (
                    "machado" in sender_l
                    or "backorder" in subj_l
                    or "questions before the meeting" in subj_l
                )
                if not interesting:
                    continue
                att_names = []
                for a in range(1, att_count + 1):
                    try:
                        att_names.append(it.Attachments.Item(a).FileName)
                    except Exception:
                        pass
                has_bo = any("backorder" in n.lower() for n in att_names)
                if has_bo or "questions before" in subj_l or ("machado" in sender_l and "backorder" in " ".join(att_names).lower()):
                    hits.append((received, store.DisplayName, fname, subj, sender, att_names, it))

        except Exception as e:
            pass
        try:
            for sf in f.Folders:
                walk(sf, depth + 1)
        except Exception:
            pass

    walk(root, 0)
    log.append(f"store {name} walk done, hits so far {len(hits)}")

# dedupe by subject+received
seen = set()
saved = []
for received, store_name, folder, subj, sender, att_names, it in sorted(hits, key=lambda x: str(x[0] or ""), reverse=True):
    key = (str(received), subj, tuple(att_names))
    if key in seen:
        continue
    seen.add(key)
    print(f"HIT {received} | {store_name}/{folder} | {subj} | atts={att_names}")
    for a in range(1, it.Attachments.Count + 1):
        att = it.Attachments.Item(a)
        fn = att.FileName
        if "backorder" in fn.lower() or fn.lower().endswith((".xlsx", ".xls", ".csv")):
            stamp = ""
            try:
                stamp = received.strftime("%Y%m%d_%H%M")
            except Exception:
                stamp = "unknown"
            safe = f"{stamp}_Nuno_{fn}"
            dest = out / safe
            att.SaveAsFile(str(dest))
            saved.append(str(dest))
            # also body
            body_path = out / f"{stamp}_Nuno_body.txt"
            try:
                body_path.write_text(
                    f"Subject: {subj}\nFrom: {sender}\nReceived: {received}\nStore: {store_name}/{folder}\n\n{it.Body}",
                    encoding="utf-8",
                    errors="replace",
                )
            except Exception as e:
                print("body fail", e)

# SOURCE
(out / "SOURCE.md").write_text(
    "# Nuno Backordered lines 2026\n\nPulled from Outlook after Jerome screenshot of mail RE: Questions before the meeting.\n\nSaved:\n"
    + "\n".join(f"- `{p}`" for p in saved)
    + f"\n\nHits logged: {len(seen)}\n",
    encoding="utf-8",
)
print("SAVED", saved)
print("OUT", out)
