"""Pull newest ISZE daily/monthly sales report with IMOTORS from Outlook."""
import win32com.client
from pathlib import Path
import re

out = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_imotors_sales_check_20261006")
out.mkdir(parents=True, exist_ok=True)

outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
hits = []

def walk(folder, depth=0):
    if depth > 2:
        return
    name = folder.Name
    if name in {"Sync Issues", "RSS Feeds", "Junk Email", "Deleted Items", "Calendar", "Contacts", "Tasks"}:
        return
    try:
        items = folder.Items
        items.Sort("[ReceivedTime]", True)
        try:
            restricted = items.Restrict(
                "@SQL=("
                "\"urn:schemas:httpmail:subject\" LIKE '%SALES REPORT%' "
                "OR \"urn:schemas:httpmail:subject\" LIKE '%Daily Sales%' "
                "OR \"urn:schemas:httpmail:subject\" LIKE '%MONTHLY SALES%'"
                ")"
            )
        except Exception:
            restricted = items
        n = 0
        for it in restricted:
            n += 1
            if n > 80:
                break
            try:
                subj = str(it.Subject or "")
                received = it.ReceivedTime
                atts = []
                for a in range(1, it.Attachments.Count + 1):
                    atts.append(it.Attachments.Item(a).FileName)
            except Exception:
                continue
            if not any(re.search(r"sales.?report|daily.?sales", x, re.I) for x in atts + [subj]):
                continue
            hits.append((received, folder.Name, subj, atts, it))
    except Exception:
        pass
    try:
        for sf in folder.Folders:
            walk(sf, depth + 1)
    except Exception:
        pass

for i in range(1, outlook.Stores.Count + 1):
    store = outlook.Stores.Item(i)
    try:
        walk(store.GetRootFolder(), 0)
    except Exception as e:
        print("store fail", store.DisplayName, e)

hits.sort(key=lambda x: str(x[0]), reverse=True)
print("HITS", len(hits))
saved = []
seen = set()
for received, folder, subj, atts, it in hits[:15]:
    key = (str(received), subj)
    if key in seen:
        continue
    seen.add(key)
    print(f"{received} | {folder} | {subj} | {atts}")
    for a in range(1, it.Attachments.Count + 1):
        att = it.Attachments.Item(a)
        fn = att.FileName
        if not fn.lower().endswith((".xlsx", ".xls")):
            continue
        if not re.search(r"sales|report|daily|monthly", fn, re.I):
            continue
        stamp = received.strftime("%Y%m%d_%H%M")
        dest = out / f"{stamp}_{fn}"
        att.SaveAsFile(str(dest))
        saved.append(str(dest))
        print("SAVED", dest)

(out / "SOURCE.md").write_text("# Latest sales reports pulled\n\n" + "\n".join(f"- `{s}`" for s in saved), encoding="utf-8")
print("DONE saved", len(saved))
