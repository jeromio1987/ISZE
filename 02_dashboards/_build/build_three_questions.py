"""Builds 02_dashboards/ops/ISZE_Warranty_Mileage_Cash_Update_2026-10-16.html

Three open questions, one page:
  1. August truck warranty export wired in (warranty_cv_monthly_202504_202608.csv, built by
     01_data/91_build/build_cv_warranty_extension_202601_202608.py) and what it does to the warranty share of billing.
  2. UK oil-filter cover recomputed on the Japan mileage tables of 6 Oct 2026.
  3. What cash, stock and receivables data exists.
All figures are read at build time except the fleet counts and intervals, whose sources are named in the page.
"""
import html, json, os
import duckdb
import pandas as pd

ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"
D = ROOT + r"\01_data\00_derived"
OUT = ROOT + r"\02_dashboards\ops\ISZE_Warranty_Mileage_Cash_Update_2026-10-16.html"


def e(x):
    return html.escape(str(x), quote=True)


def eur(x, k=False):
    return ("EUR %dk" % round(x / 1e3)) if k else ("EUR %.2fM" % (x / 1e6))


def tip(t, x):
    return '<span class="kpi" tabindex="0">%s<span class="tip">%s</span></span>' % (t, e(x))


# ============ 1. warranty ==================================================
w = pd.read_csv(D + r"\warranty_cv_monthly_202504_202608.csv", dtype={"ym": str})
chk = json.load(open(D + r"\warranty_cv_extension_overlap_check.json", encoding="utf8"))
con = duckdb.connect()
con.execute("create view f as select * from '%s\\sales_fact.parquet'" % D)
con.execute("create view dim as select cast(sold_to_sap as varchar) s, distributor_code dc from read_csv_auto('%s\\distributor_dimension.csv', all_varchar=true) where network_role='network_db'" % D)
con.execute("""create view g as select f.billing_date, coalesce(dim.dc, case when cast(cast(f.sold_to_sap as bigint) as varchar)='2194' then 'ITUK' end) dc, f.net_sales_value v
 from f left join dim on cast(cast(f.sold_to_sap as bigint) as varchar)=dim.s where try_cast(f.part_number as bigint) is not null""")


def billed(dc, a, b):
    return con.execute("select sum(v) from g where dc='%s' and billing_date between '%s' and '%s'" % (dc, a, b)).fetchone()[0]


def wsum(dist, a, b):
    return float(w[(w.dist == dist) & (w.ym >= a) & (w.ym <= b)].parts_eur.sum())


rows = []
for dist, dc in [("ITUK", "ITUK"), ("UTI", "UTI")]:
    for lab, (wa, wb, ba, bb) in {"Apr-Aug 2025": ("202504", "202508", "2025-04-01", "2025-08-31"),
                                  "Apr-Aug 2026": ("202604", "202608", "2026-04-01", "2026-08-31"),
                                  "Apr 2025-Mar 2026": ("202504", "202603", "2025-04-01", "2026-03-31")}.items():
        wv, bv = wsum(dist, wa, wb), billed(dc, ba, bb)
        rows.append((dist, lab, bv, wv, 100 * wv / bv))
share = pd.DataFrame(rows, columns=["db", "period", "billed", "warr", "pct"])
canon = pd.read_csv(D + r"\warranty_by_db_FY_canonical.csv").set_index("db")

months = sorted(w.ym.unique())
piv = w[w.dist.isin(["ITUK", "UTI"])].pivot_table(index="ym", columns="dist", values="parts_eur", aggfunc="sum").reindex(months).fillna(0)
mx = float(piv.max().max())
bars = ""
for ym in months:
    if ym < "202604" and ym not in ("202504", "202505", "202506", "202507", "202508"):
        continue
    for d_, cls in (("ITUK", "a"), ("UTI", "b")):
        v = float(piv.loc[ym, d_])
        bars += ('<div class="mrow"><div class="mlab">%s %s</div><div class="mtrk"><div class="mb %s" style="width:%.1f%%"></div></div><div class="mval">%s</div></div>'
                 % (ym[:4] + "-" + ym[4:], d_, cls, 100 * v / mx, "EUR %dk" % round(v / 1e3)))
    bars += '<div class="msp"></div>'

ov = chk["by_month"]
ov_rows = "".join("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
    ym[:4] + "-" + ym[4:], "{:,}".format(v["master_lines"]), "{:,}".format(v["new_lines"]),
    ("+" if v["new_minus_master_eur"] >= 0 else "-") + "EUR {:,}".format(abs(v["new_minus_master_eur"])))
    for ym, v in ov.items())


def r_(db, per):
    x = share[(share.db == db) & (share.period == per)].iloc[0]
    return x


# ============ 2. oil filter cover ==========================================
js = json.load(open(ROOT + r"\01_data\90_INBOX\_shimauchi_mileage_20261006\shimauchi_mileage_quantiles.json", encoding="utf8"))
N = js["N-series"]
mean_km, med_km, gt50 = N["midpoint"]["mean_km"], N["midpoint"]["p50"], N["share_gt_50000"]
FLEET_N35, FLEET_N = 10900, 21584            # UIO workbook sheet 2, section B, via 03_analytics/Isuzu/prism/data/uio_ld_n35_share.csv
FLEET_N75 = FLEET_N - FLEET_N35
INT35, INT75 = 20000, 40000                  # oil-service intervals, N35 and N75 (register ITUK-MILEAGE; GIDSS)
WARR35, WARR75 = 12891, 35478                # warranty odometer deltas, register ITUK-MILEAGE
ACT_GEN_DECK = 9818                          # iml_v7_ituk_cy2025.yaml, oil_filter actual_sales (genuine)
pm = pd.read_csv(D + r"\pms_capture_by_db_year.csv")
pm = pm[(pm.distributor_code == "ITUK") & (pm.pms_category == "oil_filter") & (pm.year == 2025)].set_index("line_type")
ACT_GEN, ACT_TOT = float(pm.loc["genuine", "actual_qty"]), float(pm.loc["total", "actual_qty"])
s = FLEET_N35 / FLEET_N
r = WARR75 / WARR35
m35_6 = mean_km / (s + (1 - s) * r)
m75_6 = m35_6 * r


def exp_(k35, k75):
    return FLEET_N35 * k35 / INT35 + FLEET_N75 * k75 / INT75


SC = [
 ("The deck today: 50,000 km a year, one interval of 40,000 km for every truck", 22389 * 1.25, "Deck figure. 22,389 trucks x 1.25 visits. Source: iml_v7_ituk_cy2025.yaml."),
 ("50,000 km a year, interval by truck class (the register's 24% case)", exp_(50000, 50000), "N35 trucks at 20,000 km, N75 at 40,000 km, 50,000 km a year for both."),
 ("Japan table, average 28,400 km, same for both classes", exp_(mean_km, mean_km), "Average of Shimauchi's 4,883 N-series trucks. Expected demand grows with the average, not the middle truck."),
 ("Japan table split by class (my derived case)", exp_(m35_6, m75_6), "Same average, split between N35 and N75 in the ratio the warranty odometers show (N75 drives 2.75 times as far). The split is my assumption; the files do not give one."),
 ("Japan table, middle truck 21,250 km", exp_(med_km, med_km), "Uses the median. Understates expected demand when some trucks drive far more, so treat it as the optimistic end."),
 ("Warranty odometers by class: N35 12,891, N75 35,478", exp_(WARR35, WARR75), "The register's 59.5% case. Odometers come from trucks that claimed, not the whole fleet."),
]
sc_rows, cbars = "", ""
SHORT = ["Deck today: 50,000 km, one 40,000 km interval", "50,000 km, interval by truck class", "Japan average 28,400 km, both classes",
         "Japan average split by class (central)", "Japan middle truck 21,250 km", "Warranty odometers by class"]
for (lab, ex, note), short in zip(SC, SHORT):
    cg, ct = 100 * ACT_GEN_DECK / ex, 100 * ACT_TOT / ex
    sc_rows += "<tr><td>%s<small>%s</small></td><td>{:,.0f}</td><td>%.1f%%</td><td>%.1f%%</td></tr>".format(ex) % (e(lab), e(note), cg, ct)
    cbars += ('<div class="mrow"><div class="mlab wide">%s</div><div class="mtrk"><div class="mb a" style="width:%.1f%%"></div></div><div class="mval">%.0f%%</div></div>'
              % (e(short), min(cg, 100), cg))
central = 100 * ACT_GEN_DECK / SC[3][1]

# ============ 3. cash / stock ===============================================
k = pd.read_csv(ROOT + r"\01_data\90_INBOX\_stock_insights_20261007\kpi_parts_handling_tidy.csv", dtype={"ym": str})
sd = k[k.kpi == "Days of Parts in Stock"].copy()
sd["value"] = pd.to_numeric(sd.value, errors="coerce")
last = sd.dropna(subset=["value"]).sort_values("ym").groupby("distributor").tail(1).set_index("distributor")
stock_rows = ""
for dist, rr in last.sort_values("value", ascending=False).iterrows():
    ym = rr.ym
    prev_ym = str(int(ym[:4]) - 1) + ym[4:]
    pv = sd[(sd.distributor == dist) & (sd.ym == prev_ym)].value
    pvv = float(pv.iloc[0]) if len(pv) and pd.notna(pv.iloc[0]) else None
    if int(ym) < 202605 or dist in ("MIDI", "AIOS"):  # MIDI and AIOS are not ISZE distributors
        continue
    stock_rows += "<tr><td>%s</td><td>%s</td><td>%.0f</td><td>%s</td></tr>" % (e(dist), ym[:4] + "-" + ym[4:], rr.value, ("%.0f" % pvv) if pvv is not None else "n/a")
wc = pd.read_csv(ROOT + r"\01_data\90_INBOX\_stock_insights_20261007\working_capital_stock_change.csv")
wc_rows = "".join("<tr><td>%s</td><td>%d to %d</td><td>%s</td></tr>" % (e(r_.distributor), r_.stock_dec24, r_.stock_dec25,
                  ("+" if r_.stock_change_eur >= 0 else "-") + "EUR %dk" % round(abs(r_.stock_change_eur) / 1e3)) for r_ in wc.sort_values("stock_change_eur", ascending=False).itertuples())

page = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ISZE Warranty Mileage Cash</title><style>
:root{--navy:#15233c;--terra:#c0552d;--paper:#f7f4ee;--ink:#222;--pale:#eef3f9;--line:#d8d2c4}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.5 system-ui,Segoe UI,Arial,sans-serif}
header{background:var(--navy);color:var(--paper);padding:22px 28px}header h1{margin:0;font:600 26px Georgia,serif;color:var(--paper)}header p{margin:6px 0 0;color:var(--paper);opacity:.92;max-width:940px}
main{max-width:1060px;margin:0 auto;padding:18px 20px 60px}h2{font:600 21px Georgia,serif;color:var(--navy);margin:34px 0 4px;border-bottom:2px solid var(--terra);padding-bottom:4px}
p.q{margin:2px 0 12px;color:#555;font-style:italic}.chips{display:flex;flex-wrap:wrap;gap:12px;margin:16px 0}.chip{background:#fff;border:1px solid var(--line);border-left:5px solid var(--terra);padding:10px 14px;min-width:220px;flex:1}
.chip b{display:block;font:600 25px Georgia,serif;color:var(--navy)}.chip span{font-size:13px;color:#444}
.kpi{position:relative;cursor:help;border-bottom:1px dotted var(--terra)}.tip{display:none;position:absolute;left:0;top:130%%;z-index:50;width:300px;background:var(--navy);color:var(--paper);border-top:3px solid var(--terra);padding:8px 10px;font:12px/1.4 system-ui}
.kpi:hover .tip,.kpi:focus .tip{display:block}
.mrow{display:grid;grid-template-columns:130px 1fr 80px;gap:10px;align-items:center;margin:3px 0}.mlab.wide{grid-column:auto}.mtrk{background:#e6e1d4;height:15px}.mb{height:15px}.mb.a{background:var(--terra)}.mb.b{background:var(--navy)}.mval{text-align:right;font-variant-numeric:tabular-nums;font-weight:600}.msp{height:8px}
.scen .mrow{grid-template-columns:minmax(220px,420px) 1fr 60px}
table{border-collapse:collapse;width:100%%;background:#fff;margin:8px 0}th{background:var(--navy);color:var(--paper);text-align:left;padding:8px 10px;font-weight:600}td{padding:7px 10px;border-bottom:1px solid var(--line);vertical-align:top}td small{display:block;color:#666;font-size:12px}
.note{background:var(--pale);border-left:5px solid var(--navy);padding:10px 14px;margin:14px 0}.warn{border-left-color:var(--terra)}footer{margin-top:36px;font-size:12px;color:#555}
.legend span{display:inline-block;width:12px;height:12px;margin:0 4px 0 12px;vertical-align:middle}
@media(max-width:700px){.mrow{grid-template-columns:1fr 70px}.mtrk{grid-column:1/3;order:3}.scen .mrow{grid-template-columns:1fr 60px}}
</style></head><body>
<header><h1>Warranty, mileage and cash: what the new data says</h1><p>Internal. 16 Oct 2026. Three open questions from the turnaround read, each answered as far as the files allow.</p></header>
<main>
<div class="chips">
<div class="chip"><b>%(uti_pct26).0f%% vs %(uti_pct25).0f%%</b><span>%(t1)s, Apr to Aug 2026 vs 2025, UTI (Israel trucks)</span></div>
<div class="chip"><b>%(central).0f%%</b><span>%(t2)s, UK oil-filter cover on the Japan mileage tables (the deck says 35%%)</span></div>
<div class="chip"><b>0 of 4</b><span>%(t3)s: receivables, own stock, payables, cash found</span></div>
</div>

<h2>1. August truck warranty export: wired in</h2><p class="q">Does the new file tie to what we already hold, and what does it change?</p>
<div class="note"><b>Result.</b> The export holds %(newrows)s truck claim lines with bill months December 2025 to August 2026. January and February 2026 tie to the euro with the older file. December is a partial month in the export (78 lines against 1,160 already held), so the older file stays the source for December. March differs: the export has 61 more lines, worth EUR %(extra)s of parts, than the older file, so the older file understated March 2026. April to August 2026 are new.</div>
<table><tr><th>Bill month</th><th>Lines already held</th><th>Lines in export</th><th>Parts euro, export minus held</th></tr>%(ovrows)s</table>
<p>Euro rule is the audited one used for the commercial datasets: EUR as is, GBP x 1.12, JPY / 163.7, parts lines with a real part number only. Output file: <code>01_data/00_derived/warranty_cv_monthly_202504_202608.csv</code>. The older files and their pages are untouched.</p>

<h3>Monthly truck warranty parts, euros</h3>
<div class="legend"><span style="background:var(--terra)"></span>ITUK (UK trucks)<span style="background:var(--navy)"></span>UTI (Israel trucks)</div>
%(bars)s

<h3>Warranty parts as a share of what we billed (same basis, same lines)</h3>
<table><tr><th>Distributor</th><th>Period</th><th>Billed</th><th>Warranty parts</th><th>Share</th></tr>%(sharerows)s</table>
<div class="note warn"><b>Two truck warranty totals disagree, and this matters.</b> On the canonical file (<code>warranty_by_db_FY_canonical.csv</code>) UTI's April 2025 to March 2026 warranty is EUR %(c_uti)s and ITUK's EUR %(c_ituk)s. On the bill-month truck claims used here the same twelve months are EUR %(m_uti)s for UTI and EUR %(m_ituk)s for ITUK, %(ratio_uti).1f times and %(ratio_ituk).1f times higher. The README of the commercial datasets says the two cover different workbooks and market sets, and I have not found which is right. My earlier note that UTI warranty is 8%% of billing used the canonical file; on this basis it is %(uti_fy).0f%%. Until the owner settles it, quote UTI warranty as a range.</div>
<p><b>What it says.</b> ITUK warranty parts fell %(ituk_chg).0f%% year on year (April to August) while billing rose; UTI warranty rose %(uti_chg).0f%% while billing fell. At UTI roughly a quarter of what we billed in the last five months was warranty parts on this basis, against under a fifth a year earlier. This does not yet say who pays for those claims: the files hold the part euros, not the funding.</p>

<h2>2. UK oil-filter cover on the Japan mileage tables</h2><p class="q">With real mileage instead of an assumed 50,000 km, how much of the expected oil-filter demand did we bill?</p>
<div class="note"><b>Result.</b> On Japan's tables the genuine oil-filter cover is between %(lo).0f%% and %(hi).0f%%, with %(central).0f%% as the central case. The deck's 35%% rests on 50,000 km a year, and only %(gt50).0f%% of the 4,883 trucks in Japan's tables drive more than that. The old range of 24%% to 60%% was too wide to use; this narrows it to roughly 43%% to 60%%.</div>
<div class="scen">%(cbars)s</div>
<table><tr><th>Case</th><th>Expected filters a year</th><th>Genuine cover (9,818 billed, the deck's count)</th><th>Genuine and Best Value (%(at)s billed, pipeline)</th></tr>%(scrows)s</table>
<p><b>How the cases are built.</b> Expected filters = N35 trucks (10,900) x km / 20,000 plus N75 trucks (10,684) x km / 40,000. Fleet counts from the UIO workbook (via <code>03_analytics/Isuzu/prism/data/uio_ld_n35_share.csv</code>). Billed filters for 2025 from <code>01_data/00_derived/pms_capture_by_db_year.csv</code> (genuine %(ag)s, genuine plus Best Value %(at)s) and the deck's own genuine figure of 9,818 for the genuine column. Mileage from <code>01_data/90_INBOX/_shimauchi_mileage_20261006/shimauchi_mileage_quantiles.json</code>.</p>
<div class="note warn"><b>What the Japan tables cannot settle.</b> The files do not say which market they cover, there is no N35 and N75 split, they are modelled from warranty-claim odometers, and readings under 5,000 km were removed, which pushes the average up and so pushes cover down. The central case therefore leans conservative. The interval is a ceiling set by the dashboard indicator, not a fixed schedule, so real visits per truck can be lower than km divided by interval. Confirm the market with Shimauchi before any number leaves the building.</div>

<h2>3. Cash, stock and receivables: what exists</h2><p class="q">What would a turnaround plan have, and what is still missing?</p>
<div class="note warn"><b>Not found.</b> I looked for receivables, ageing, payment terms, ISZE's own stock value, payables, cash and balance sheet in file names across the data, docs, meetings and memory folders and in the finance report's sheets. None of it is there. The finance report has sales, cost of sales and provisions only. I read file names and sheet names, not every cell of every workbook, so a balance sheet could sit inside a file named for something else.</div>
<p><b>The closest thing that exists</b> is stock held by the distributors, from the monthly parts-handling KPI. It is the distributors' working capital, not ISZE's, but it shows where billing runs ahead of what dealers sell.</p>
<table><tr><th>Distributor</th><th>Latest month</th><th>Days of parts in stock</th><th>Same month a year earlier</th></tr>%(stockrows)s</table>
<p>Estimated change in distributor stock, December 2024 to December 2025, valued at what we bill them (prepared 7 Oct, <code>01_data/90_INBOX/_stock_insights_20261007/working_capital_stock_change.csv</code>):</p>
<table><tr><th>Distributor</th><th>Stock days</th><th>Estimated change</th></tr>%(wcrows)s</table>
<p><b>What to ask Finance for</b> (draft only, not sent): receivables by distributor with ageing and agreed payment terms; ISZE stock value by part with ageing; amounts owed to Japan; the monthly cash position. One extract, month-end, April 2025 to date.</p>

<footer>Sources: 01_data/CV_Warranty_01-08_2026.xlsx; 01_data/06_Warranty files; 01_data/00_derived/sales_fact.parquet and distributor_dimension.csv; 01_data/00_derived/pms_capture_by_db_year.csv; 01_data/90_INBOX/_shimauchi_mileage_20261006; 01_data/90_INBOX/_stock_insights_20261007. Builders: 01_data/91_build/build_cv_warranty_extension_202601_202608.py and 02_dashboards/_build/build_three_questions.py.</footer>
</main></body></html>"""

x = lambda db, p: r_(db, p)
v = dict(
    uti_pct26=x("UTI", "Apr-Aug 2026").pct, uti_pct25=x("UTI", "Apr-Aug 2025").pct,
    t1=tip("Warranty parts as share of billing", "Truck warranty parts euros by bill month (EUR as is, GBP x 1.12, JPY / 163.7) divided by parts billed to UTI in the same months."),
    central=central, t2=tip("Central case", "My derived split of Japan's average mileage between N35 and N75 using the warranty-odometer ratio. The split is an assumption."),
    t3=tip("Balance-sheet data", "Searched by file and sheet name in the data, docs, meetings and memory folders."),
    newrows="{:,}".format(chk["new_rows"]), extra="{:,}".format(chk["eur_only_in_new_for_shared_months"]), ovrows=ov_rows, bars=bars,
    sharerows="".join("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%.1f%%</td></tr>" % (e(a.db), e(a.period), eur(a.billed), eur(a.warr, True), a.pct) for a in share.itertuples()),
    c_uti="{:,.0f}".format(canon.loc["UTI", "warr_FY2026"]), c_ituk="{:,.0f}".format(canon.loc["ITUK", "warr_FY2026"]),
    m_uti="{:,.0f}".format(x("UTI", "Apr 2025-Mar 2026").warr), m_ituk="{:,.0f}".format(x("ITUK", "Apr 2025-Mar 2026").warr),
    ratio_uti=x("UTI", "Apr 2025-Mar 2026").warr / canon.loc["UTI", "warr_FY2026"], ratio_ituk=x("ITUK", "Apr 2025-Mar 2026").warr / canon.loc["ITUK", "warr_FY2026"],
    uti_fy=x("UTI", "Apr 2025-Mar 2026").pct,
    ituk_chg=abs(100 * (x("ITUK", "Apr-Aug 2026").warr / x("ITUK", "Apr-Aug 2025").warr - 1)), uti_chg=100 * (x("UTI", "Apr-Aug 2026").warr / x("UTI", "Apr-Aug 2025").warr - 1),
    lo=min(100 * ACT_GEN_DECK / SC[2][1], 100 * ACT_GEN_DECK / SC[3][1]), hi=100 * ACT_GEN_DECK / SC[5][1], gt50=100 * gt50,
    cbars=cbars, scrows=sc_rows, ag="{:,.0f}".format(ACT_GEN), at="{:,.0f}".format(ACT_TOT), stockrows=stock_rows, wcrows=wc_rows)
open(OUT, "w", encoding="utf8").write(page % v)
print("wrote", OUT, os.path.getsize(OUT))
print("scenarios:", [(round(s_[1]), round(100 * ACT_GEN_DECK / s_[1], 1)) for s_ in SC], "central", round(central, 1), "m35,m75", round(m35_6), round(m75_6))
print(share.round(1).to_string())
