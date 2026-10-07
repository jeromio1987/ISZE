# -*- coding: utf-8 -*-
"""B2 per-host sweep. Env B2_HOST selects one host; writes _part_<host>.{tried,rows}.csv."""
from __future__ import annotations
import csv, io, json, os, re, sys, time
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
WT = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26")
sys.path.insert(0, str(WT / "04_tools" / "delegation" / "parsers"))
from fetch_polite import PoliteFetcher, ConsentRefused  # noqa: E402
from ledger_schema import COLUMNS, make_row, issue_obs_id  # noqa: E402

HERE = Path(__file__).resolve().parent
PAGES = HERE / "pages"; PAGES.mkdir(exist_ok=True)
TODAY = "2026-10-07"
ROWCOLS = COLUMNS + ["page_file", "crossref_grade", "source_tried"]

HOSTS = {
    "www.truckparts.pt": ("https://www.truckparts.pt/?s={q}",
                          ["Não foi possível encontrar", "não foi possível encontrar", "Não foram encontrados"]),
    "www.turbopecas.pt": ("https://www.turbopecas.pt/?s={q}&post_type=product",
                          ["Nothing Found", "nothing matched"]),
    "www.isuzu.pt": ("https://www.isuzu.pt/?s={q}",
                     ["Não foi possível encontrar", "não foi possível encontrar"]),
    "www.ascendum.pt": ("https://www.ascendum.pt/?s={q}",
                        ["couldn't find any results", "We couldn"]),
    "www.sotecnica.pt": ("https://www.sotecnica.pt/?s={q}", []),
    "spareparts.pt": ("https://spareparts.pt/search?q={q}", []),
}
HOST = os.environ["B2_HOST"]
tmpl, empties = HOSTS[HOST]
safe = re.sub(r"[^a-zA-Z0-9._-]", "_", HOST)

def read_pns(p):
    return [l.strip() for l in p.read_text(encoding="utf-8").splitlines()[1:] if l.strip()]

OE = read_pns(HERE / "seed_oe_pns.csv")
COMP = read_pns(HERE / "seed_competitor_pns.csv")
TAG = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.I | re.S)
PRICE = re.compile(r"\u20ac\s*\d[\d.,]*|\d[\d.,]*\s*\u20ac|\bEUR\s*\d", re.I)

f = PoliteFetcher()
rows, tried = [], []
c = {"queried": 0, "empty": 0, "no_price": 0, "priced": 0, "errors": 0, "non200": 0}
t0 = time.time()
for kind, pns in (("oe", OE), ("comp", COMP)):
    for pn in pns:
        url = tmpl.format(q=pn)
        c["queried"] += 1
        try:
            html = f.get(url)
        except ConsentRefused:
            tried.append({"host": HOST, "kind": kind, "pn": pn, "url": url, "outcome": "consent_refused", "bytes": 0, "prices": 0})
            continue
        if html is None:
            c["errors"] += 1
            tried.append({"host": HOST, "kind": kind, "pn": pn, "url": url, "outcome": "http_error_or_non200", "bytes": 0, "prices": 0})
            continue
        txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", TAG.sub(" ", html)))
        low = txt.lower()
        is_empty = any(m.lower() in low for m in empties) if empties else (pn not in html.replace("-", ""))
        prices = PRICE.findall(txt)
        if prices:
            c["priced"] += 1
            outcome = "priced"
            fn = PAGES / f"{safe}__{pn}.html"
            fn.write_text(html, encoding="utf-8")
            r = make_row(obs_id=issue_obs_id("b2_pt_sweep", pn, TODAY, "aftermarket_retail"),
                         part_no=pn if (len(pn) == 10 and pn.isdigit()) else None,
                         match_method="crossref", competitor_brand=None, competitor_pn=pn,
                         description=None, source=HOST, source_url=url, country="PT",
                         observed_at=TODAY, vintage=TODAY, price=None, price_avg=None,
                         currency="EUR", price_eur=None, fx_note=None, vat=None,
                         price_type="aftermarket_retail", stock=None, n_obs=1, loader="b2_pt_sweep")
            r.update({"page_file": fn.name, "crossref_grade": "candidate", "source_tried": HOST})
            rows.append(r)
        elif is_empty:
            c["empty"] += 1; outcome = "empty_marker"
        else:
            c["no_price"] += 1; outcome = "page_no_price"
        tried.append({"host": HOST, "kind": kind, "pn": pn, "url": url, "outcome": outcome,
                      "bytes": len(html), "prices": len(prices)})

with (HERE / f"_part_{safe}.tried.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["host", "kind", "pn", "url", "outcome", "bytes", "prices"]); w.writeheader()
    for t in tried: w.writerow(t)
with (HERE / f"_part_{safe}.rows.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=ROWCOLS); w.writeheader()
    for r in rows: w.writerow({k: r.get(k) for k in ROWCOLS})
(HERE / f"_part_{safe}.json").write_text(json.dumps({"host": HOST, "counts": c, "seconds": round(time.time()-t0)}, indent=1), encoding="utf-8")
print(HOST, json.dumps(c), f"{time.time()-t0:.0f}s", "stats:", f.stats, flush=True)
