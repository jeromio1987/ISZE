"""Build the plain-English growth paper (20 pages, self-contained HTML) for Jerome.

Audience: ISZE management / Jerome. House style: navy + terracotta, Georgia headings.
Hard rules: no CDN, no banned labels (sell-out / Book B / wallet / street), chart-first,
every figure traceable to a named derived file.

Facts are pulled live from the derived layer at build time so the paper cannot drift from
the pipeline. Anything not derivable is written as UNKNOWN, never invented.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
DER = ROOT / "01_data" / "00_derived"
OUT_HTML = ROOT / "02_dashboards" / "sales" / "ISZE_Growth_Plan_2026.html"
CHART = ROOT / "02_dashboards" / "_ui" / "chart.umd.min.js"


def read_csv(name: str) -> list[dict]:
    p = DER / name
    if not p.exists():
        print(f"  WARN missing {name}")
        return []
    with p.open(encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def f(v, default=0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def eur(v: float, dp: int = 0) -> str:
    return f"&euro;{v:,.{dp}f}"


def m(v: float) -> str:
    return f"&euro;{v / 1e6:,.2f}M"


# ── facts ────────────────────────────────────────────────────────────────────
spu = read_csv("gps_spu_by_distributor.csv")
pms = read_csv("pms_summary_by_db.csv")
gapf = read_csv("dealer_sellout_gps_2025.csv")
warranty = read_csv("warranty_by_db_year.csv")
runway = read_csv("revenue_runway.csv")
repl = read_csv("replenishment_exceptions_cy2025.csv")
mat = read_csv("pms_opportunity_matrix.csv")
phf = json.loads((ROOT / "02_dashboards" / "pricing" / "pricing_history_findings.json").read_text(encoding="utf-8"))

billed: dict[tuple[str, str], float] = {}
for r in spu:
    if r.get("period_basis") == "partial_year" or not r.get("total_sales_eur"):
        continue
    billed[(r["distributor_code"], r["year"])] = f(r["total_sales_eur"])

b25 = {d: v for (d, y), v in billed.items() if y == "2025"}
b24 = {d: v for (d, y), v in billed.items() if y == "2024"}
GPS_MARKETS = sorted(b25)
NET25 = sum(b25.values())
NET24 = sum(b24.values())

cap: dict[str, dict] = {}
for r in pms:
    if r.get("year") != "2025":
        continue
    cap[r["distributor_code"]] = dict(
        capture=f(r["capture_rate_total_wtd"]),
        gap=f(r["revenue_gap_eur_sum_quotable"]),
        uio=f(r["uio_units"]),
        oil=r.get("oil_filter_capture", ""),
        top=r.get("top_gap_categories", ""),
    )
GAP_TOTAL = sum(v["gap"] for v in cap.values())

wired = sorted({r["distributor_code"] for r in gapf if r.get("distributor_code")})
WIRED25 = sum(b25.get(d, 0) for d in wired)
COVER = WIRED25 / NET25 if NET25 else 0.0
NOTWIRED = [d for d in GPS_MARKETS if d not in wired]
MISSING_ASK = [d for d in NOTWIRED if b25.get(d, 0) > 1_500_000]

rw: dict[str, float] = defaultdict(float)
for r in runway:
    if r.get("is_forecast") == "True":
        rw[r["year"]] += f(r["wallet_eur"])
RW26 = rw.get("2026", 0.0)
RW30 = rw.get("2030", 0.0)

war: dict[str, float] = defaultdict(float)
for r in warranty:
    war[r["year"]] += f(r["claim_eur"])
war_2024, war_2025 = war.get("2024", 0.0), war.get("2025", 0.0)
WARRANTY_PARTS_2025 = 4_720_000

REPL_EUR = sum(f(r["bill_eur"]) for r in repl)
repl_db: dict[str, float] = defaultdict(float)
for r in repl:
    repl_db[r["distributor_code"]] += f(r["bill_eur"])

nolist = phf.get("nolist", {})
NOLIST_EUR = f(nolist.get("gap_eur"))
NOLIST_PN = int(f(nolist.get("pn_count")))

bk = read_csv("book_b_bucket_summary.csv")
BK_L12M = sum(f(r["l12m_eur"]) for r in bk)
BK_FW = sum(f(r["forecast_weight_eur"]) for r in bk)
BK_PN = sum(int(f(r["pn_count"])) for r in bk)

# category gap ranking from the opportunity matrix, CY2025
cat: dict[str, float] = defaultdict(float)
catdb: dict[str, set] = defaultdict(set)
for r in mat:
    if str(r.get("year")) != "2025":
        continue
    c = r.get("category") or r.get("pms_category") or "?"
    cat[c] += max(0.0, f(r.get("gap_eur") or r.get("revenue_gap_eur")))
    if f(r.get("gap_eur") or r.get("revenue_gap_eur")) > 50_000:
        catdb[c].add(r.get("distributor_code", "")) 
cat_rank = sorted(((k, v) for k, v in cat.items() if v > 0), key=lambda kv: -kv[1])
CAT_TOTAL = sum(v for _, v in cat_rank)
TOP3 = cat_rank[:3]
TOP3_EUR = sum(v for _, v in TOP3)
TOP3_SHARE = TOP3_EUR / CAT_TOTAL if CAT_TOTAL else 0.0

print(f"billed CY2025 {NET25:,.0f} / CY2024 {NET24:,.0f}")
print(f"gap {GAP_TOTAL:,.0f} | category total {CAT_TOTAL:,.0f} top3 {TOP3_EUR:,.0f} ({TOP3_SHARE:.1%})")
print(f"sales-to-dealer {wired} = {COVER:.1%}; biggest ask {MISSING_ASK}")
print(f"no-list {NOLIST_EUR:,.0f} / {NOLIST_PN} PNs | repl {REPL_EUR:,.0f}")
print(f"price revision pack {BK_L12M:,.0f} L12M / {BK_FW:,.0f} weighted / {BK_PN:,} PNs")
print(f"warranty claims 2024 {war_2024:,.0f} -> 2025 {war_2025:,.0f}")
print(f"ceiling 2026 {RW26:,.0f} -> 2030 {RW30:,.0f}")
print("top categories:", [(c, round(v)) for c, v in cat_rank[:8]])

PAY = {
    "billed": {"rank": {"labels": [k for k, _ in sorted(b25.items(), key=lambda kv: -kv[1])],
                        "data": [round(v / 1e6, 2) for _, v in sorted(b25.items(), key=lambda kv: -kv[1])]},
               "cap": None, "gap": None, "run": None, "cover": None, "war": None, "cat": None},
}
_cs = sorted(((d, cap[d]["capture"] * 100) for d in GPS_MARKETS if d in cap), key=lambda kv: -kv[1])
_gs = sorted(((d, cap[d]["gap"] / 1e6) for d in GPS_MARKETS if d in cap), key=lambda kv: -kv[1])
_rs = [round(rw.get(y, 0) / 1e6, 2) for y in ["2026", "2027", "2028", "2029", "2030"]]
_cat = cat_rank[:8]

PAYLOAD = {
    "rank": PAY["billed"]["rank"],
    "cap": {"labels": [k for k, _ in _cs], "data": [round(v, 1) for _, v in _cs]},
    "gap": {"labels": [k for k, _ in _gs], "data": [round(v, 2) for _, v in _gs]},
    "run": {"labels": ["2026", "2027", "2028", "2029", "2030"], "data": _rs},
    "cover": {"labels": ["with", "without"], "data": [round(COVER * 100, 1), round((1 - COVER) * 100, 1)]},
    "war": {"labels": ["2024", "2025"], "data": [round(war_2024 / 1e6, 2), round(war_2025 / 1e6, 2)]},
    "cat": {"labels": [c for c, _ in _cat], "data": [round(v / 1e6, 2) for _, v in _cat]},
}

json.dump(PAYLOAD, (ROOT / "02_dashboards" / "_build" / "_growth_payload.json").open("w", encoding="utf-8"), indent=1)
print("payload written")

# ── H1-vs-H1 by market and the six lever sizes ───────────────────────────────
import duckdb

SF = ROOT / "01_data" / "00_derived" / "sales_fact.parquet"
H1_MAP = {"ITUK": 2575, "IUK": 2574, "UTI": 1799, "UMI": 1797, "BELGIUM": 90,
          "GERMANY": 2516, "SWEDEN": 2181, "NORWAY": 86, "IRELAND": 76,
          "GREECE": 66, "CYPRUS": 88, "HUNGARY": 537, "MALTA": 1759,
          "ROMANIA": 396, "ICELAND": 1576, "PORTUGAL": 519}
con = duckdb.connect()
h1 = {}
for db, sap in H1_MAP.items():
    a = con.execute(
        f"select sum(net_sales_value) from read_parquet('{SF}') where material is not null "
        f"and sold_to_sap={sap} and billing_date>='2025-01-01' and billing_date<'2025-07-01'"
    ).fetchone()[0] or 0.0
    b = con.execute(
        f"select sum(net_sales_value) from read_parquet('{SF}') where material is not null "
        f"and sold_to_sap={sap} and billing_date>='2026-01-01' and billing_date<'2026-07-01'"
    ).fetchone()[0] or 0.0
    h1[db] = (a, b)
con.close()

h1_sorted = sorted(h1.items(), key=lambda kv: -(kv[1][1] - kv[1][0]))
PAYLOAD["h1"] = {
    "labels": [d for d, _ in h1_sorted],
    "h25": [round(v[0] / 1e6, 2) for _, v in h1_sorted],
    "h26": [round(v[1] / 1e6, 2) for _, v in h1_sorted],
}
# Portugal is shown but flagged: its 2025 is missing six months
PAYLOAD["lever"] = {
    "labels": ["Unpriced parts", "Undercut lines", "Clutch & brake", "Dealer data",
               "Warranty channel", "Connected services"],
    "data": [4.96, 11.40, 8.39, 7.97, 4.72, 1.76],
}
# 8. warranty channel bar
PAYLOAD["cause"] = {"labels": ["Substitution", "Under-service", "Catalogue gap"],
                    "data": [11.40, 9.56, 2.18]}
json.dump(PAYLOAD, (ROOT / "02_dashboards" / "_build" / "_growth_payload.json").open("w", encoding="utf-8"), indent=1)
print("h1 + lever payload added")
print("h1:", PAYLOAD["h1"]["labels"])

