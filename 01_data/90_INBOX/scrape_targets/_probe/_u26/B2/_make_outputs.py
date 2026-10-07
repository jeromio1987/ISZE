# -*- coding: utf-8 -*-
"""B2: merge per-host sweep parts into rows.csv + per-query tried, then build
host-level tried.csv and status.json."""
from __future__ import annotations
import csv, io, json, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
TODAY = "2026-10-07"
ROWCOLS = ["obs_id","part_no","match_method","competitor_brand","competitor_pn","description",
           "source","source_url","country","observed_at","vintage","price","price_avg","currency",
           "price_eur","fx_note","vat","price_type","stock","n_obs","loader",
           "page_file","crossref_grade","source_tried"]

# --- merge per-host parts ---------------------------------------------------
all_rows, all_tried, by_host = [], [], {}
for p in sorted(HERE.glob("_part_*.rows.csv")):
    with p.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            all_rows.append(r)
for p in sorted(HERE.glob("_part_*.tried.csv")):
    with p.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            all_tried.append(r)
for p in sorted(HERE.glob("_part_*.json")):
    d = json.loads(p.read_text(encoding="utf-8"))
    by_host[d["host"]] = d["counts"]

with (HERE / "rows.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=ROWCOLS); w.writeheader()
    for r in all_rows: w.writerow({k: r.get(k) for k in ROWCOLS})
with (HERE / "tried_queries.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["host","kind","pn","url","outcome","bytes","prices"]); w.writeheader()
    for r in all_tried: w.writerow(r)

# --- robots probe batches ---------------------------------------------------
robots = []
for p in sorted(HERE.glob("_robots_probe*.csv")):
    with p.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            r["batch"] = p.stem; robots.append(r)
with (HERE / "_robots_all.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["host","base","path","exit","verdict","detail","batch"]); w.writeheader()
    for r in robots: w.writerow(r)

# --- content probes ---------------------------------------------------------
content = []
for p in sorted(HERE.glob("_content_probe*.json")):
    try: data = json.loads(p.read_text(encoding="utf-8"))
    except Exception: continue
    for r in data:
        r["probe"] = p.stem; content.append(r)
(HERE / "_content_all.json").write_text(json.dumps(content, indent=1, ensure_ascii=False), encoding="utf-8")

# --- host-level tried.csv ---------------------------------------------------
hosts = {}
def bump(h, **kw):
    d = hosts.setdefault(h, {"host": h, "url_pattern": "", "robots_verdict": "allowed",
                             "http_status": "", "outcome": ""})
    for k, v in kw.items():
        if v: d[k] = v
    return d
for r in robots:
    if r["host"].endswith("]"): continue
    d = bump(r["host"])
    if r["verdict"] == "allowed": bump(r["host"], url_pattern=r["path"], robots_verdict="allowed")
    else: bump(r["host"], robots_verdict=r["verdict"])
for h, c in by_host.items():
    bump(h, url_pattern="search", robots_verdict="allowed",
         outcome=f"queried={c['queried']} empty={c['empty']} no_price={c['no_price']} priced={c['priced']} err={c['errors']}")
for r in content:
    lbl = r.get("label", ""); h = lbl.split("|")[0].split("[")[0]
    if not h: continue
    d = hosts.get(h)
    if not d: continue
    v = r.get("verdict", "")
    d["http_status"] = "200" if v not in ("no_body", "consent_refused") else "non-200"
    if not d["outcome"]: d["outcome"] = v
rows_out = sorted(hosts.values(), key=lambda x: x["host"])
with (HERE / "tried.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["host","url_pattern","robots_verdict","http_status","outcome"]); w.writeheader()
    for r in rows_out: w.writerow(r)

# --- status.json ------------------------------------------------------------
def uniq(key, val):
    return sorted({r["host"] for r in robots if r["verdict"] == val and not r["host"].endswith("]")})
oe = [l.strip() for l in (HERE / "seed_oe_pns.csv").read_text(encoding="utf-8").splitlines()[1:] if l.strip()]
comp = [l.strip() for l in (HERE / "seed_competitor_pns.csv").read_text(encoding="utf-8").splitlines()[1:] if l.strip()]
swept = set(by_host.keys())
with_rows = {r["part_no"] for r in all_rows if r.get("part_no")}
queried = sum(c["queried"] for c in by_host.values())
status = {
    "agent": "B2", "market": "Portugal", "date": TODAY,
    "hosts_tried_total": len(rows_out),
    "hosts_swept_for_prices": sorted(swept),
    "hosts_allowed_by_robots": uniq("x", "allowed"),
    "hosts_blocked_by_robots": uniq("x", "blocked"),
    "hosts_unknown_treated_blocked": uniq("x", "unknown"),
    "oe_numbers": len(oe), "competitor_numbers": len(comp),
    "queries_run": queried,
    "rows_written": len(all_rows),
    "priced_rows": sum(1 for r in all_rows if r.get("price")),
    "numbers_with_a_row": len(with_rows),
    "numbers_still_empty": sorted(set(oe) - with_rows),
    "per_host": by_host,
    "could_not_do": [
        "No reachable Portuguese host publishes an Isuzu parts catalogue with prices; all show a search page with no part matches.",
        "spareparts.pt is a domestic-appliance spares shop; 3 apparent prices were a price-filter widget and were discarded.",
        "pecauto.com returns a 127-byte JS shell (no server-rendered catalogue).",
        "b-parts.com search is POST-only: GET query URLs return HTTP 405.",
        "europart.net product search is a JS app; GET query returns the shop shell.",
        "Autodoc / Oscaro / Mister-Auto retired or robots-403 - not attempted.",
    ],
}
(HERE / "status.json").write_text(json.dumps(status, indent=1, ensure_ascii=False), encoding="utf-8")
print(json.dumps(status, indent=1, ensure_ascii=False))
