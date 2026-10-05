#!/usr/bin/env python3
from pathlib import Path

p = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\_build\build_exec_aftersales_paper.py")
t = p.read_text(encoding="utf-8")
reps = [
    ("target spend per truck × parc", "target spend per truck × trucks in service"),
    ("with parc", "with trucks in service"),
    ("of the parc", "of the trucks in service"),
    ("bucketed parc", "bucketed trucks in service"),
    ("without parc", "without trucks in service"),
    ("GPS parc", "GPS trucks in service"),
    (
        "We say OEM peer retail / dealer sell-out / reference dealer sell-out — never a slang label for the counter.",
        "We say OEM peer retail / reference dealer price — never slang for the counter.",
    ),
    (
        "Dealer sell-out longs exist only for five distributors (54.4% of GPS billed euro).",
        "Sales-to-dealer files exist for six distributors including Portugal (60.0% of GPS billed euro).",
    ),
    (
        "Sell-out files cover 54.4% of GPS billed euro (five distributors). Replenishment exceptions are therefore a half-the-book fact.",
        "Sales-to-dealer files cover 60.0% of GPS billed euro (six distributors including Portugal). Replenishment exceptions remain an observed-subset fact.",
    ),
    (
        "Sell-out files exist for ITUK, IUK, Ireland, UTI and Greece = <b>54.4% of GPS billed euro</b> (€16.74M of €30.76M). Germany + Belgium + Portugal would add €6.36M and lift visibility to <b>75.1%</b>.",
        "Sales-to-dealer files exist for ITUK, IUK, Ireland, UTI, Greece and Portugal = <b>60.0% of GPS billed euro</b> (€18.45M of €30.76M). Germany + Belgium would add €4.65M and lift visibility to <b>75.1%</b>.",
    ),
    (
        "1,595 CY2025 exception rows sit on five distributors only — 54.4% of billed euro, not the whole network",
        "1,595 CY2025 exception rows sit on the observed sales-to-dealer subset — not the whole network",
    ),
    ('("Billed, no matching sell-out", 500, "500", "#c0552d"),',
     '("Billed, no matching sales to dealer", 500, "500", "#c0552d"),'),
    ('("High sell-through vs bill", 400, "400", "#c48a16"),',
     '("High sales to dealer vs bill", 400, "400", "#c48a16"),'),
    ('("Low sell-through", 315, "315", "#8a6a4a"),',
     '("Low sales to dealer", 315, "315", "#8a6a4a"),'),
    ("['No sell-out','High ST','No bill','Low ST']",
     "['No sales to dealer','High vs bill','No bill','Low vs bill']"),
    ("Sell-out coverage", "Sales-to-dealer coverage"),
    (
        "Five DBs = 54.4% of GPS billed euro; DE+BE+PT would reach 75.1%",
        "Six DBs including Portugal = 60.0% of GPS billed euro; DE+BE would reach 75.1%",
    ),
    ("Book B (the price list we might change)", "The price list we might revise"),
    ("Book B alloc ambition", "price-list revision ambition"),
    ("and DE/BE/PT sell-out", "and DE/BE sales-to-dealer files"),
    ("three missing sell-out files", "two missing sales-to-dealer files (Germany, Belgium)"),
    (
        "DE+BE+PT sell-out would lift visibility 54.4% → 75.1%",
        "DE+BE sales-to-dealer files would lift visibility 60.0% → 75.1%",
    ),
    ("three verified sell-out longs", "verified sales-to-dealer longs"),
    ("reference dealer sell-out", "reference dealer price"),
    ("DE/BE/PT sell-out", "DE/BE sales-to-dealer files"),
    ("Germany or Belgium dealer sell-out long", "Germany or Belgium sales-to-dealer long"),
    (
        "Sell-out 54.4% of billed euro (to 75.1% with DE/BE/PT)",
        "Sales to dealer 60.0% of billed euro (to 75.1% with DE/BE)",
    ),
    ("Five DBs with sell-out longs / GPS billed", "Six DBs with sales-to-dealer longs / GPS billed"),
    ("Lead with what is already built: Book B alloc ambition",
     "Lead with what is already built: price-list revision ambition"),
    # leftover Sell-out with no bill bar if present as literal
    ("Sell-out with no bill", "Sales to dealer with no bill"),
]
for a, b in reps:
    c = t.count(a)
    print(("OK" if c else "MISS"), c, a[:70])
    t = t.replace(a, b)

t = t.replace(
    'for bad in ("street", "wallet", "iml v7", "model b", "prism lane", "jerome"):',
    'for bad in ("street", "wallet", "sell-out", "sell-through", "book b", "iml v7", "model b", "prism lane", "jerome"):',
)

import re
for pat in [r"Book B", r"sell-out", r"sell-through", r"\bparc\b"]:
    hits = list(re.finditer(pat, t))
    print("REMAIN", pat, len(hits))
    for h in hits[:8]:
        print(" ", repr(t[max(0, h.start() - 30) : h.end() + 40]))

p.write_text(t, encoding="utf-8")
print("wrote exec builder")
