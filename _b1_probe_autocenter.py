import re
import sys
from pathlib import Path

sys.path.insert(0, "04_tools/delegation/parsers")
from fetch_polite import PoliteFetcher, ConsentRefused   # noqa: E402

B1 = Path("01_data/90_INBOX/scrape_targets/_probe/_u26/B1")
f = PoliteFetcher()
SEEDS = [ln.strip() for ln in (B1 / "seed_oe_pns.csv").read_text(encoding="utf-8").splitlines()
         if ln.strip()]
COMPS = [ln.strip() for ln in (B1 / "seed_competitor_pns.csv").read_text(encoding="utf-8")
         .splitlines() if ln.strip()]
PICK = SEEDS[:3] + [c for c in COMPS if c in ("ADBP420136", "F 026 407 349", "ADZ92130",
                                              "MDB4120", "BP3513")][:5]
for term in PICK:
    u = f"https://autocenter.pt/?s={term}&post_type=product"
    try:
        h = f.get(u)
    except ConsentRefused as e:
        print("REFUSED", u, e)
        continue
    if not h:
        print("err", u)
        continue
    on = term in h
    pr = re.findall(r"\d{1,4}[.,]\d{2}\s?€", h)
    prodlinks = sorted(set(re.findall(r'href="(https://autocenter\.pt/shop/[^"]+)"', h)))[:3]
    print(f"{term!r:20} {len(h):>8,}B term_on_page={on} prices={len(pr)}{pr[:4]}")
    for pl in prodlinks:
        print("     ", pl)
print(f.stats)
