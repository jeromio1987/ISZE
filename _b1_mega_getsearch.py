import re
import sys
from pathlib import Path

sys.path.insert(0, "04_tools/delegation/parsers")
from fetch_polite import PoliteFetcher, ConsentRefused   # noqa: E402

B1 = Path("01_data/90_INBOX/scrape_targets/_probe/_u26/B1")
f = PoliteFetcher()
PN = "8982447940"
tries = [
    f"https://megapecas.pt/pt/ProductListForm?Search={PN}",
    f"https://megapecas.pt/pt/ProductListForm?Search={PN}&Make=ISUZU",
    f"https://megapecas.pt/pt/produtos?Search={PN}",
]
for u in tries:
    try:
        h = f.get(u)
    except ConsentRefused as e:
        print("REFUSED", u, e)
        continue
    if not h:
        print("err", u)
        continue
    pr = re.findall(r"\d{1,4}[.,]\d{2}\s?€", h)
    print(f"{u}\n  {len(h):,}B  pn={PN in h}  prices={len(pr)}{pr[:5]}")
print(f.stats)
