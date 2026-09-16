import json, re
from pathlib import Path
outDir = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_mh_gps_mail_20260730")
for name in ["mh_restrict_hits.json", "mh_gps_deep.json"]:
    p = outDir / name
    if not p.exists():
        continue
    hits = json.loads(p.read_text(encoding="utf-8-sig"))
    if isinstance(hits, dict):
        hits = [hits]
    print(f"=== {name}: {len(hits)} ===")
    for h in hits:
        subj = h.get("Subject","")
        if not re.search(r"GPS|KPI_targets|Minutes|sales to dealer|Action plan|incentive|Lubricant|oil purchase|Wrap Up|IDS Parts|IDS Feedback|waterfall|stretch|target|SPA", subj, re.I):
            continue
        safe = re.sub(r"[^\w\-]+","_", subj)[:70]
        fn = f"{(h.get('Received') or 'nodate')[:10]}_{h.get('Folder','')}_{safe}.txt"
        text = f"FROM: {h.get('From')}\nRECV: {h.get('Received')}\nSUBJ: {subj}\nTO: {h.get('To','')}\n\n{h.get('Body','')}"
        (outDir/fn).write_text(text, encoding="utf-8")
        print(" ", fn)
