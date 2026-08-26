import win32com.client, json, datetime
outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
cutoff = datetime.datetime(2026, 8, 18)
hits = []

def walk(folder, path=""):
    try:
        name = folder.Name
    except Exception:
        return
    p = f"{path}/{name}" if path else name
    try:
        items = folder.Items
        items.Sort("[ReceivedTime]", True)
        n = min(items.Count, 200)
        for i in range(1, n+1):
            try:
                m = items.Item(i)
                rt = m.ReceivedTime
                if hasattr(rt, 'year'):
                    rtd = datetime.datetime(rt.year, rt.month, rt.day, rt.hour, rt.minute, rt.second)
                else:
                    continue
                if rtd < cutoff:
                    break
                sender = ""
                try:
                    sender = str(m.SenderName or "")
                except Exception:
                    pass
                subj = str(m.Subject or "")
                blob = (sender + " " + subj).lower()
                if not any(k in blob for k in ["suzuki", "transcript", "mom", "minutes", "pms"]):
                    continue
                atts = []
                try:
                    for a in m.Attachments:
                        atts.append(a.FileName)
                except Exception:
                    pass
                preview = ""
                try:
                    preview = (m.Body or "")[:400]
                except Exception:
                    pass
                hits.append({
                    "folder": p,
                    "received": rtd.isoformat(sep=" "),
                    "from": sender,
                    "subject": subj,
                    "atts": atts,
                    "preview": preview.replace("\r"," ").replace("\n"," ")[:400],
                })
            except Exception:
                continue
    except Exception:
        pass
    try:
        for sf in folder.Folders:
            walk(sf, p)
    except Exception:
        pass

for i in range(1, outlook.Folders.Count+1):
    walk(outlook.Folders.Item(i))

# also filter to Suzuki specifically
suzuki = [h for h in hits if "suzuki" in h["from"].lower() or "suzuki" in h["subject"].lower()]
trans = [h for h in hits if "transcript" in h["subject"].lower() or "transcript" in " ".join(h["atts"]).lower() or "vtt" in " ".join(h["atts"]).lower()]
print("SUZUKI_COUNT", len(suzuki))
print(json.dumps(suzuki[:30], indent=2, ensure_ascii=False))
print("TRANSCRIPT_COUNT", len(trans))
print(json.dumps(trans[:20], indent=2, ensure_ascii=False))
with open("_suzuki_transcript_scan.json","w",encoding="utf-8") as f:
    json.dump({"suzuki":suzuki,"transcript":trans,"all_hits":hits[:80]}, f, indent=2, ensure_ascii=False)
print("WROTE _suzuki_transcript_scan.json")
