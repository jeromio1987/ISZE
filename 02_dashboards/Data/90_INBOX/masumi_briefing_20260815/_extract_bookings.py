#!/usr/bin/env python3
import json, re
from pathlib import Path

d = json.loads(Path(__file__).with_name("gps_db_mail_scan.json").read_text(encoding="utf-8"))
out = Path(__file__).with_name("_gps_booking_extract.txt")

def dump(title, pred, n=15):
    lines = [f"\n======== {title} ========\n"]
    rows = [r for r in d["mails"] if pred(r)]
    rows = sorted(rows, key=lambda x: x["when"], reverse=True)[:n]
    for r in rows:
        lines.append(f"{r['when']} [{r['folder']}] {r['subject']}")
        lines.append(r["preview"][:500])
        lines.append("")
    return lines

lines = []
lines += dump("ICELAND / SALES MEETING TEAMS", lambda r: "Sales meeting teams" in r["subject"] or (
    "iceland" in r["hits"] and re.search(r"September|25/08|23 September|book", r["subject"] + r["preview"], re.I)
))
lines += dump("DENMARK BUSINESS REVIEW", lambda r: "denmark" in r["hits"] and re.search(r"business review", r["subject"], re.I))
lines += dump("CYPRUS / LOUTSIOS DATES", lambda r: re.search(r"cyprus|loutsios|23rd of September", r["subject"] + r["preview"][:250], re.I) and re.search(r"business review|september|23rd", r["subject"] + r["preview"], re.I))
lines += dump("FINLAND / BUSINESS REVIEWS FW", lambda r: re.search(r"business reviews", r["subject"], re.I) or ("finland" in r["hits"] and re.search(r"business review|teams meeting|august", r["subject"], re.I)))
lines += dump("AUTOWALLIS", lambda r: re.search(r"Autowallis", r["subject"], re.I))
lines += dump("IBX", lambda r: re.search(r"IBX|260812_IBX", r["subject"], re.I))
lines += dump("CAL", lambda r: False)
lines.append("\n======== CALENDAR ========\n")
for r in d["calendar"]:
    lines.append(f"{r['start']} {r['hits']} | {r['subject']} | {r.get('required','')[:200]}")

out.write_text("\n".join(lines), encoding="utf-8")
print("wrote", out, "chars", out.stat().st_size)
