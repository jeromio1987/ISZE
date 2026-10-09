# -*- coding: utf-8 -*-
from pathlib import Path
import re

html = Path(
    r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_uk_ks_delivery_info_20261007.html"
).read_text(encoding="utf-8", errors="replace")
m = re.search(
    r"<h3>Delivery.*?</h3>(.*?)(?:<h3>|</main>|page-footer)",
    html,
    re.I | re.S,
)
chunk = m.group(0) if m else ""
text = re.sub(r"<br\s*/?>", "\n", chunk, flags=re.I)
text = re.sub(r"</p>|</h4>|</h3>", "\n", text, flags=re.I)
text = re.sub(r"<[^>]+>", "", text)
text = text.replace("&nbsp;", " ").replace("&amp;", "&")
text = re.sub(r"&#\d+;", "GBP", text)
text = text.replace("\ufffd", "GBP")
text = re.sub(r"[ \t]+", " ", text)
text = re.sub(r"\n\s*\n+", "\n\n", text)
out = Path(
    r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_uk_ks_delivery_info_20261007_text.txt"
)
out.write_text(text.strip() + "\n", encoding="utf-8")
print(text.strip()[:4500])
print("WROTE", out)
