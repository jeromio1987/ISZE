from pathlib import Path
import re
from html import unescape

p = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\ks_pms_scan_20260818\seed_html\isuzu-4x4-and-truck-parts_isuzu-truck-parts_isuzu-7-5-ton.html.html")
t = p.read_text(encoding="utf-8", errors="replace")
hrefs = re.findall(r'href="([^"]+)"', t)
paths = set()
for h in hrefs:
    h = unescape(h).split("?")[0]
    if "isuzu-7-5-ton" in h and h.endswith(".html"):
        paths.add(h)
out = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\ks_pms_scan_20260818\_urls_7_5.txt")
out.write_text("\n".join(sorted(paths)), encoding="utf-8")
print("n", len(paths))
for x in sorted(paths):
    print(x)
