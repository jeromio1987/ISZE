from pathlib import Path
import re
from html import unescape

p = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\ks_pms_scan_20260818\seed_html\isuzu-4x4-and-truck-parts_isuzu-truck-parts_isuzu-3-5-ton.html.html")
if not p.exists():
    print("no 3.5 seed")
else:
    t = p.read_text(encoding="utf-8", errors="replace")
    hrefs = re.findall(r'href="([^"]+)"', t)
    keep = []
    for h in hrefs:
        h = unescape(h).split("?")[0]
        if "isuzu-3-5-ton" in h and h.endswith(".html"):
            if any(x in h for x in ("filter", "brake", "clutch", "fuel", "engine.html")):
                keep.append(h)
    for x in sorted(set(keep)):
        print(x)
    print("n", len(set(keep)))
