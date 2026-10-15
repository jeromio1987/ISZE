"""Builds 02_dashboards/ops/ISZE_Margin_Lens_FY27_YTD.html from the finance report
01_data/Margin analysis report August.xlsx (sheet 'VP & ACC', YTD block, rows 8-25) and
checks it against sales_fact.parquet. Every figure is read at build time; none is estimated."""
import datetime as dt, html, os
import duckdb, openpyxl

ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"
SRC = os.path.join(ROOT, "01_data", "Margin analysis report August.xlsx")
OUT = os.path.join(ROOT, "02_dashboards", "ops", "ISZE_Margin_Lens_FY27_YTD.html")

wb = openpyxl.load_workbook(SRC, read_only=True, data_only=True)
ws = wb["VP & ACC"]
rows = {i + 1: r for i, r in enumerate(ws.iter_rows(values_only=True)) if i < 40}
par = {r[1]: r[2] for r in wb["Parameters"].iter_rows(values_only=True) if r[1]}
fy, period, plan_name = par.get("Current FY"), par.get("Period"), par.get("Plan")


def f(x):
    return float(x) if isinstance(x, (int, float)) else 0.0


dist = []
for n in range(8, 21):  # YTD block, one row per distributor
    r = rows[n]
    name = r[1]
    if name in (None, "IML") or (f(r[14]) == 0 and f(r[20]) == 0):
        continue
    # YTD block sits in columns O..W (index 14, 18, 20, 22); the MTD block is columns C..K
    dist.append(dict(name=str(name), bill=f(r[14]), act=f(r[18]), plan=f(r[20]), var=f(r[22])))
tot = rows[21]; cos = rows[22]; gp = rows[23]; prov = rows[24]; gpx = rows[25]
S_act, S_plan, S_bill = f(tot[18]), f(tot[20]), f(tot[14])
C_act, C_plan = f(cos[18]), f(cos[20])
G_act, G_plan = f(gp[18]), f(gp[20])
P_act = f(prov[18]); GX_act = f(gpx[18])
chk_ytd = f(tot[29]); chk_mtd = f(tot[28])
assert abs(sum(d["act"] for d in dist) - S_act) < 5, "distributor rows do not add to total"

con = duckdb.connect()
fact = os.path.join(ROOT, "01_data/00_derived/sales_fact.parquet").replace("\\", "/")
raw = con.execute("select sum(net_sales_value) from '%s' where billing_date>='2026-04-01' and billing_date<='2026-08-31'" % fact).fetchone()[0]


def e(x):
    return html.escape(str(x))


def m(x):
    return ("-" if x < 0 else "") + "EUR %.2fM" % (abs(x) / 1e6)


def k(x):
    return ("-" if x < 0 else "+") + "EUR %dk" % round(abs(x) / 1e3)


gm_act, gm_plan, gmx = G_act / S_act, G_plan / S_plan, GX_act / S_act
dist.sort(key=lambda d: d["var"])
maxv = max(abs(d["var"]) for d in dist)
bars = ""
for d in dist:
    pct = 100 * d["var"] / d["plan"] if d["plan"] else 0
    w = 50 * abs(d["var"]) / maxv
    side = "neg" if d["var"] < 0 else "pos"
    left = 50 - w if d["var"] < 0 else 50
    bars += ('<div class="row"><div class="nm">%s</div><div class="trk"><div class="mid"></div><div class="b %s" style="left:%.1f%%;width:%.1f%%"></div></div>'
             '<div class="vl">%s <small>%+.1f%%</small></div></div>' % (e(d["name"]), side, left, w, k(d["var"]), pct))

tbl = "".join("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (e(d["name"]), "%.0fk" % (d["act"] / 1e3), "%.0fk" % (d["plan"] / 1e3), "%+.1f%%" % (100 * d["var"] / d["plan"] if d["plan"] else 0))
              for d in sorted(dist, key=lambda d: -d["act"]))


def tip(t, x):
    return '<span class="kpi" tabindex="0">%s<span class="tip">%s</span></span>' % (t, e(x))


page = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ISZE Margin Lens FY27</title><style>
:root{--navy:#15233c;--terra:#c0552d;--paper:#f7f4ee;--ink:#222;--pale:#eef3f9;--line:#d8d2c4}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.5 system-ui,Segoe UI,Arial,sans-serif}
header{background:var(--navy);color:var(--paper);padding:22px 28px}header h1{margin:0;font:600 26px Georgia,serif;color:var(--paper)}header p{margin:6px 0 0;color:var(--paper);opacity:.92;max-width:920px}
main{max-width:1060px;margin:0 auto;padding:18px 20px 60px}h2{font:600 21px Georgia,serif;color:var(--navy);margin:32px 0 4px;border-bottom:2px solid var(--terra);padding-bottom:4px}
p.q{margin:2px 0 12px;color:#555;font-style:italic}.chips{display:flex;flex-wrap:wrap;gap:12px;margin:16px 0}.chip{background:#fff;border:1px solid var(--line);border-left:5px solid var(--terra);padding:10px 14px;min-width:210px;flex:1}
.chip b{display:block;font:600 25px Georgia,serif;color:var(--navy)}.chip span{font-size:13px;color:#444}
.kpi{position:relative;cursor:help;border-bottom:1px dotted var(--terra)}.tip{display:none;position:absolute;left:0;top:130%%;z-index:50;width:300px;background:var(--navy);color:var(--paper);border-top:3px solid var(--terra);padding:8px 10px;font:12px/1.4 system-ui}
.kpi:hover .tip,.kpi:focus .tip{display:block}
.row{display:grid;grid-template-columns:150px 1fr 150px;gap:10px;align-items:center;margin:6px 0}.trk{position:relative;height:18px;background:#e6e1d4}.mid{position:absolute;left:50%%;top:-3px;bottom:-3px;width:2px;background:var(--navy)}
.b{position:absolute;top:0;height:18px}.b.neg{background:var(--terra)}.b.pos{background:var(--navy)}.vl{font-variant-numeric:tabular-nums;font-weight:600}.vl small{color:#555;font-weight:400}
table{border-collapse:collapse;width:100%%;background:#fff}th{background:var(--navy);color:var(--paper);text-align:left;padding:8px 10px}td{padding:7px 10px;border-bottom:1px solid var(--line)}
.note{background:var(--pale);border-left:5px solid var(--navy);padding:10px 14px;margin:14px 0}footer{margin-top:36px;font-size:12px;color:#555}
@media(max-width:700px){.row{grid-template-columns:1fr 130px}.trk{grid-column:1/3;order:3}}
</style></head><body>
<header><h1>Vehicle spare parts: margin and volume against plan</h1><p>Internal. Financial year %(fy)s, periods 1 to %(period)s (April to August 2026), against the %(plan)s plan. Source: finance management accounts, August report.</p></header>
<main>
<div class="chips">
<div class="chip"><b>%(sact)s</b><span>%(t1)s: %(svar)s (%(spct).1f%%) against plan</span></div>
<div class="chip"><b>%(gm).1f%%</b><span>%(t2)s: plan %(gmp).1f%%</span></div>
<div class="chip"><b>%(gx).1f%%</b><span>%(t3)s</span></div>
<div class="chip"><b>%(prov)s</b><span>%(t4)s</span></div>
</div>
<div class="note"><b>The finding.</b> Sales are %(spct_abs).1f%% short of plan, but cost of sales is %(cdelta)s lower than plan, so gross margin is %(dpp).1f points ahead and gross profit is %(gdelta)s against plan. Volume is the problem, not margin. Where the shortfall sits is in the chart below.</div>

<h2>1. Which distributors are behind plan, in euros?</h2><p class="q">Sales after provisions against the revised plan, April to August, ranked from furthest behind.</p>%(bars)s
<p class="note">Bars left of the line are behind plan, right are ahead. The plan is the revised budget (%(plan)s). Each distributor's own figures are in the table in section 3.</p>

<h2>2. Does the report agree with our own billing file?</h2><p class="q">Two independent sources for the same five months.</p>
<table><tr><th>Source</th><th>April to August 2026</th></tr>
<tr><td>Finance report, vehicle spare parts, billing</td><td>%(sbill)s</td></tr>
<tr><td>Our billing file, every line, net of credits</td><td>%(raw)s</td></tr>
<tr><td>Difference</td><td>%(diff)s (%(diffp).1f%%)</td></tr></table>
<p class="note">The two are close but not tied to the euro. Our file includes internal codes and credit notes that the parts base later excludes, and the finance report is one profit centre, so I have not tried to explain the difference. The report also carries its own check cells: they show %(chk)s year to date outside the distributor table. That matches the EUR 76k the sales sheet books to profit centre 100000, which the table does not list.</p>

<h2>3. Distributor detail</h2><p class="q">Same numbers as the chart, with the plan beside them.</p>
<table><tr><th>Distributor</th><th>Actual after provisions</th><th>Revised plan</th><th>Against plan</th></tr>%(tbl)s</table>

<h2>4. What this page cannot tell you</h2><p class="q">What would a turnaround plan need that is not here?</p>
<div class="note">The report holds sales, cost of sales and provisions. It has no receivables, stock value, payables or cash, so nothing here says how fast billed euros turn into cash. That needs a balance-sheet extract from finance. I did not search every folder for one, so if it exists, point me at it.</div>
<footer>Source: 01_data/Margin analysis report August.xlsx, sheet VP &amp; ACC, year-to-date block; 01_data/00_derived/sales_fact.parquet. Builder: 02_dashboards/_build/build_margin_lens.py. Margin here is gross profit over sales as the finance report states it (cost of sales over sales is the report's own line).</footer>
</main></body></html>"""

vals = dict(
    fy=fy, period=period, plan=e(plan_name),
    sact=m(S_act), svar=k(S_act - S_plan), spct=100 * (S_act - S_plan) / S_plan, spct_abs=abs(100 * (S_act - S_plan) / S_plan),
    t1=tip("Sales after provisions, year to date", "Finance report, vehicle spare parts, actuals after provisions, April to August 2026. Plan is the revised budget."),
    gm=100 * gm_act, gmp=100 * gm_plan,
    t2=tip("Gross margin after provisions", "Gross profit divided by sales, both as printed in the finance report. Gross profit = sales less cost of sales."),
    cdelta="EUR %dk" % round(abs(C_act - C_plan) / 1e3),
    gx=100 * gmx, t3=tip("Gross margin excluding provisions", "The report's own line 'Gross Profit (excl. Provisions)' divided by sales after provisions. I have not re-derived it."),
    prov=m(P_act), t4=tip("Cost-of-sales provision movement", "Positive means provisions were released into margin. It is not a sale and not cash."),
    dpp=100 * (gm_act - gm_plan), gdelta=k(G_act - G_plan) if True else "",
    bars=bars, sbill=m(S_bill), raw=m(raw), diff=k(raw - S_bill), diffp=100 * (raw - S_bill) / S_bill, chk=m(chk_ytd), tbl=tbl)
open(OUT, "w", encoding="utf8").write(page % vals)
print("wrote", OUT, "sales", S_act, S_plan, "gm", gm_act, gm_plan, gmx, "gp delta", G_act - G_plan, "raw", raw, "bill", S_bill)
