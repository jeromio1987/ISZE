import json, re
from pathlib import Path
outDir = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_mh_gps_mail_20260730")
p = outDir / "mh_restrict_hits.json"
hits = json.loads(p.read_text(encoding="utf-8"))
keys = re.compile(r"GPS|KPI_targets|Minutes ITUK|sales to dealer|Action plan|incentive|Lubricant|oil purchase|Wrap Up PMS|IDS Parts|IDS Feedback|waterfall|stretch|target", re.I)
sel = [h for h in hits if keys.search(h.get("Subject",""))]
print(f"selected {len(sel)} of {len(hits)}")
for h in sel:
    safe = re.sub(r"[^\w\-]+","_", h["Subject"])[:80]
    fn = f"{h['Received'][:10]}_{safe}.txt"
    text = f"FROM: {h.get('From')}\nRECV: {h.get('Received')}\nSUBJ: {h.get('Subject')}\nTO: {h.get('To','')}\n\n{h.get('Body','')}"
    (outDir/fn).write_text(text, encoding="utf-8")
    print(fn)
