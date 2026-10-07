import re, csv, hashlib, sys
from pathlib import Path
from urllib.parse import urlparse
PARS = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26\04_tools\delegation\parsers")
sys.path.insert(0, str(PARS))
import fetch_polite
from fetch_polite import PoliteFetcher, ConsentRefused
from ledger_schema import normalise_pn

PRIV = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26\01_data\90_INBOX\scrape_targets\_probe\passes\u26_a3_omega_20261007\cache_diag")

class PF(PoliteFetcher):
    def get(self, url, force=False):
        from urllib.parse import urlparse as up
        host = re.sub(r"[^a-zA-Z0-9._-]", "_", up(url).netloc)
        cp = PRIV / host / (hashlib.sha256(url.encode()).hexdigest()[:16] + ".html")
        if cp.exists() and not force:
            self.stats["cached"] += 1
            return cp.read_text(encoding="utf-8", errors="replace")
        html = super().get(url, force=True)
        if html:
            cp.parent.mkdir(parents=True, exist_ok=True)
            cp.write_text(html, encoding="utf-8")
        return html

NAMES = [f"pa_part-manufacturer-number-sitemap{s}.xml" for s in ["", "2", "3"]] + \
        [f"pa_manufacturer-part-number-sitemap{s}.xml" for s in ["", "2", "3", "4"]] + \
        [f"pa_mpn-sitemap{s}.xml" for s in ["", "2", "3", "4"]] + \
        [f"pa_other-part-number-sitemap{s}.xml" for s in ["", "2"]]
f = PF()
seed = [r["part_no"] for r in csv.DictReader(Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26\01_data\90_INBOX\scrape_targets\_probe\_u26\A3\seed_oe_pns.csv").open(encoding="utf-8-sig"))]
seedset = set(seed)
total_terms = 0
found = {}
by_name = {}
for n in NAMES:
    u = "https://omegaspareparts.com/" + n
    try:
        t = f.get(u)
    except ConsentRefused:
        print(n, "REFUSED"); continue
    if not t:
        print(n, "no body"); continue
    locs = re.findall(r"<loc>(.*?)</loc>", t)
    terms = set()
    for L in locs:
        for m in re.finditer(r"[0-9][0-9\s\-\./]{5,}[0-9]", L):
            pn = normalise_pn(m.group(0))
            if pn: terms.add(pn)
        # also the raw last path segment
        seg = urlparse(L).path.rstrip("/").split("/")[-1]
        pn = normalise_pn(seg)
        if pn: terms.add(pn)
    total_terms += len(terms)
    hit = seedset & terms
    by_name[n] = (len(locs), len(terms), len(hit))
    for pn in hit:
        found.setdefault(pn, []).append(n)
    print(f"{n:<42} locs={len(locs):<6} 10-digit terms={len(terms):<6} seed_hits={len(hit)}")
print("="*70)
print("total distinct 10-digit terms across attribute sitemaps:", total_terms)
print("seed numbers present anywhere:", len(found))
for pn, where in list(found.items())[:30]:
    print(" ", pn, "->", where)
