"""Read-only: lift the embedded payload out of a built AIM page and report the classification KPIs.

Usage:  python probe_page_stats.py <html> [<html> ...]

Reproduces exactly what each builder's own coverage check computes, on what the page actually
carries, so the before and after figures are read from the rendered artefact rather than from the
builder's console.
"""
import json
import re
import sys

MARK_A = '<script type="application/json" id="data">'
TAG_END = "</script>"


def payload(path: str) -> dict:
    s = open(path, encoding="utf-8", errors="replace").read()
    i = s.index(MARK_A) + len(MARK_A)
    j = s.index(TAG_END, i)
    raw = s[i:j]
    raw = raw.replace("<\\/", "</").replace("<\\!--", "<!--")
    return json.loads(raw)


def stats(path: str) -> None:
    p = payload(path)
    pn = p["pn"]
    pns = pn["n"]
    a1 = pn["l1"]
    sp = pn["p"]
    l1lab = p["aim"]["l1"]
    rows = p["facts"]

    n_pn = len(pns)
    n_unclassified = sum(1 for v in a1 if v == 0)
    n_noprice = sum(1 for v in sp if v is None)
    unclass_pns = [pns[i] for i, v in enumerate(a1) if v == 0]

    # stage index: db, month, pn, ub, eb, us
    tot_b = tot_s = na_b = na_s = np_b = np_s = 0.0
    eur_na_b = 0.0
    for r in rows:
        pi = r[2]
        ub, eb, us = r[3], r[4], r[5]
        tot_b += ub
        tot_s += us
        if a1[pi] == 0:
            na_b += ub
            na_s += us
            eur_na_b += eb
        if sp[pi] is None:
            np_b += ub
            np_s += us

    print("=" * 92)
    print(path)
    print(f"  built            {p.get('built')}")
    print(f"  part numbers     {n_pn:,}")
    print(f"  not classified   {n_unclassified:,}  ({100*n_unclassified/n_pn:.2f}% of part numbers)")
    print(f"  no list price    {n_noprice:,}  ({100*n_noprice/n_pn:.2f}% of part numbers)")
    print(f"  billed units     {tot_b:,.0f}   not classified {na_b:,.0f} "
          f"({100*na_b/tot_b:.2f}%)   no price {np_b:,.0f} ({100*np_b/tot_b:.2f}%)")
    print(f"  sold units       {tot_s:,.0f}   not classified {na_s:,.0f} "
          f"({100*na_s/tot_s:.2f}%)   no price {np_s:,.0f} ({100*np_s/tot_s:.2f}%)")
    print(f"  billed euro on the not-classified rows  EUR {eur_na_b:,.0f}")
    print(f"  L1 labels on the page: {len(l1lab)}  (index 0 = {l1lab[0]!r})")
    if "coverage" in p:
        print(f"  coverage entries  {len(p['coverage'])}")
    print(f"  first 6 unclassified pns: {unclass_pns[:6]}")


if __name__ == "__main__":
    for a in sys.argv[1:]:
        stats(a)
