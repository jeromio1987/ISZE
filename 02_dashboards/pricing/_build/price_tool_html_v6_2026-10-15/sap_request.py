"""Parts that are billed on a price list but have no price in the 10 Aug 2026 export: the list to pull fresh from SAP."""
import json, csv
from pathlib import Path
H = Path(__file__).parent; INBOX = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX")
D = json.loads((H / "payload6.json").read_text(encoding="utf-8"))
P = D["parts"]; bill = {}
for l in D["lines"]:
    if l[2] < 3: bill[(l[0], l[2])] = bill.get((l[0], l[2]), 0) + l[3]
names = ["PR00 (EU and UK distributors)", "UTI 1799 (Israel trucks)", "UMI 1797 (Israel D-Max)"]
rows = []
for (pi, k), b in bill.items():
    if not (P[pi][8 + k] and P[pi][8 + k] > 0):
        rows.append([names[k], P[pi][0], P[pi][1], round(b, 2), P[pi][11] or "", P[pi][12] or ""])
rows.sort(key=lambda r: (r[0], -r[3]))
out = INBOX / "SAP_price_export_request_missing_prices_2026-10-15.csv"
with open(out, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f, delimiter=";"); w.writerow(["Price list", "Part number", "Description", "Billed EUR Jul 2025 to Jun 2026 on this list", "Newest per older price table (hint, may lag)", "Newest per Power BI"])
    for r in rows: w.writerow([r[0], r[1], r[2], str(r[3]).replace(".", ","), r[4], r[5]])
for n in names:
    rr = [r for r in rows if r[0] == n]; tot = sum(bill[(i, k)] for (i, k) in bill if names[k] == n)
    print(n, "parts without a price:", len(rr), "billed EUR %.0f of %.0f (%.1f%%)" % (sum(r[3] for r in rr), tot, 100 * sum(r[3] for r in rr) / tot))
print("written", out)
chg = sum(1 for p in P if p[6] != p[7]); print("parts with a base price change:", chg, "of", len(P))
