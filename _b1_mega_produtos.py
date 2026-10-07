import re
import sys
from pathlib import Path

sys.path.insert(0, "04_tools/delegation/parsers")
from fetch_polite import PoliteFetcher   # noqa: E402

B1 = Path("01_data/90_INBOX/scrape_targets/_probe/_u26/B1")
f = PoliteFetcher()
PN = "8982447940"
h = f.get(f"https://megapecas.pt/pt/produtos?Search={PN}")
(B1 / "pages" / f"megapecas__produtos_Search_{PN}.html").write_text(
    h or "", encoding="utf-8", errors="replace")
h = h or ""
print("bytes", len(h))
for i, m in enumerate(re.finditer(re.escape(PN), h)):
    print(f"--- hit {i} @{m.start()} ---")
    print("   ", re.sub(r"\s+", " ", h[max(0, m.start() - 200): m.start() + 200]))
    if i >= 5:
        break
print("\n--- first product-ish names near prices ---")
for m in list(re.finditer(r"\d{1,4}[.,]\d{2}\s?€", h))[:6]:
    print("   ", re.sub(r"\s+", " ", h[max(0, m.start() - 260): m.start() + 40])[-240:])
