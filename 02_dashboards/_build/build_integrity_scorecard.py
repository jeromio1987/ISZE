"""Builds 02_dashboards/ops/ISZE_Data_Integrity_Scorecard.html.

Reads live at build time: verification report, sales_fact end date, file ages, dashboard file counts.
Open-issue sizes are copied from 01_data/00_derived/_data_integrity_open_issues.md (read 2026-10-15);
nothing here is a new estimate. Items the register does not size say so.
"""
import datetime as dt, html, json, os, glob
import duckdb

ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"
OUT = os.path.join(ROOT, "02_dashboards", "ops", "ISZE_Data_Integrity_Scorecard.html")
TODAY = dt.date.today()


def age_days(path):
    return (TODAY - dt.date.fromtimestamp(os.path.getmtime(path))).days


# ---- live measurements -------------------------------------------------
rep = json.load(open(os.path.join(ROOT, "01_data/00_derived/_verification_report.json"), encoding="utf8"))
npass, nwarn, nfail = rep["summary"]["pass"], rep["summary"]["warn"], rep["summary"]["fail"]
rep_date = rep["generated_at"][:10]
sales_end = duckdb.connect().execute(
    "select max(billing_date) from '%s'" % os.path.join(ROOT, "01_data/00_derived/sales_fact.parquet").replace("\\", "/")
).fetchone()[0].date()

SOURCES = [  # (label, path, what a stale one costs)
    ("Sales to the distributors (billing file)", "01_data/00_derived/sales_fact.parquet", "every GPS and capture figure"),
    ("Headline figures snapshot", "01_data/00_derived/metrics_snapshot.json", "every quoted headline"),
    ("Verification report", "01_data/00_derived/_verification_report.json", "the green tick itself"),
    ("Pickup warranty extension (to Aug 2026)", "01_data/00_derived/warranty_lcv_extension_202510_202608.csv", "warranty pages other than the internal desk lack May-Aug 2026"),
    ("Order detail (create dates)", "01_data/12_raw/orders/Order_Detail_CY2025_2026YTD_Aug.xlsx", "order timing scores"),
    ("Trucks-in-service model (UIO v19)", "06_uio/_CURRENT/ISUZU_UIO_Overview_2026.xlsx", "every spend-per-truck rate"),
    ("Vehicle register (7 small markets)", "01_data/07_UIO/vin/VIN_register.parquet", "vehicle age and model mix"),
    ("Tender feed", "01_data/14_dashboards/tender_data.json", "live tender counts"),
]
src_rows = []
for lab, rel, cost in SOURCES:
    p = os.path.join(ROOT, rel)
    src_rows.append((lab, age_days(p) if os.path.exists(p) else None, cost, rel))
src_rows.sort(key=lambda r: -(r[1] if r[1] is not None else 9999))

PAGES = [
    ("Main GPS dashboard", "02_dashboards/fleet/ISZE_GPS_Dashboard.html"),
    ("GPS kickback proposal FY27", "02_dashboards/gps/ISZE_GPS_Kickback_Stretch_Proposal_FY27.html"),
    ("Managing director pack FY27-28", "02_dashboards/md_pack/ISZE_MD_Pack_Capture_FY27_FY28.html"),
    ("Risk cockpit", "02_dashboards/sales/ISZE_Risk_Cockpit.html"),
    ("Monthly sales tracker", "02_dashboards/sales/ISZE_Monthly_Sales_Tracker.html"),
    ("Trucks-in-service dashboard", "02_dashboards/fleet/ISUZU_UIO_Dashboard_2026.html"),
    ("AIM dashboard CY2026", "02_dashboards/sales/AIM_Dashboard_CY2026.html"),
]
page_rows = sorted(((n, age_days(os.path.join(ROOT, r))) for n, r in PAGES if os.path.exists(os.path.join(ROOT, r))), key=lambda r: -r[1])

dash_root = os.path.join(ROOT, "02_dashboards")
all_html = [p for p in glob.glob(dash_root + "/**/*.html", recursive=True) if "_archive" not in p.replace("\\", "/")]
qa_html = [p for p in all_html if any(s.startswith("_qa") for s in p.replace("\\", "/").split("/"))]
bak = glob.glob(dash_root + "/**/*.bak*", recursive=True)
receipts = glob.glob(dash_root + "/**/*.SHIP_RECEIPT.json", recursive=True)

# ---- the register, ranked ---------------------------------------------
# tier A = moves a headline by more than a fifth, or makes a published number unusable
# tier B = bounded, sized, or already contained; tier C = missing input that blocks a score
ITEMS = [
 ("A", "Trucks-in-service forecast 2026-2030", "UIO-FCAST",
  "The 2030 fleet is 45% to 59% too high (it scraps 3% a year where history implies 10% for trucks, 12% for pickups). Poland pickups +102%, UK pickups +55%. Israel trucks are about 25% too low in every year.",
  "Every spend-per-truck rate, capture vs maximum, and the FY27 growth plan for 2026 onward.",
  "A V20 candidate (version c) was built on 22 Sep. An independent check failed it on 3 of 11 tests: two pickup rows (Portugal, Cyprus) that scrap about 3% a year, and an overstatement curve that the register says does not reproduce. V19 is still the live file. Your call: promote c, or one more pass.", "Jerome"),
 ("A", "UK truck annual mileage: new evidence, not yet applied", "ITUK-MILEAGE",
  "The register (24 Sep) shows a 35 point swing in oil-filter cover: 24% at 50,000 km a year, 60% on measured mileage. On 6 Oct Isuzu Japan (Shimauchi) sent mileage tables for 4,883 N-series trucks: median about 21,250 km a year, mean about 28,400, 14% above 50,000. They are modelled from warranty odometers and cut readings under 5,000 km. The files do not say which market, and there is no N35 / N75 split.",
  "The 50,000 km assumption is contradicted by a second source. Cover has not been recomputed.",
  "Confirm the market with Shimauchi, then re-run cover. Duncan only needs to supply the N35 / N75 split.", "Jerome"),
 ("A", "Three service-interval factors are guesses", "UNSOURCED-FACTORS",
  "Air filter 0.5 (marked provisional since 2 Jul), brake pad and shoe 0.5 (the file says 'old unsourced guess'), brake rotor 0.25 (provisional). The register does not size them.",
  "Every demand and gap figure for air, brake pad, shoe and rotor.",
  "Ask IML for the three numbers; make the check fail while any is unconfirmed.", "IML via Jerome"),
 ("A", "Warranty claims turned into euro three ways", "LCV-CURRENCY-RULE",
  "Year averages (162 / 158 yen per euro), a flat 163.7 plus pounds at 1.12, and one file with dollars added up with no conversion. The register does not size the difference.",
  "MIDI's euro and the fiscal-year and monthly warranty totals.",
  "Jerome picks one method before the fiscal-year file is refreshed.", "Jerome"),
 ("B", "Parts billed on the old part number", "EPC-SUPERSESSION",
  "925 part numbers worth EUR 2.48M on the price map; we cannot say if they are genuinely superseded or wrongly billed.",
  "Price list and capture on those parts.", "Check against Japan's parts catalogue.", "IML / ISZJ"),
 ("B", "Pickup claims May-Aug 2026: wired in on 15 Oct, internal desk only", "LCV-EXT",
  "5,048 claim lines, EUR 1,078,462 (EUR 929,438 outside MIDI). The internal desk was rebuilt on 15 Oct and now shows them inside the FY2027 part-year bar. The customer desk carries no warranty by design.",
  "Other pages that show warranty were not rebuilt.", "Rebuild any other warranty page you want current.", "Internal"),
 ("B", "Credit-note netting Apr-Jun 2026 cannot be checked", "CR/RE-FY26",
  "That quarter's file has no sales-type column, so credits are caught by sign only. Earlier years held 266 such rows / EUR 1,458,105.",
  "Parts base and GPS for FY26 Q2.", "Next SAP extract that includes the column.", "SAP extract owner"),
 ("B", "2026 spend-per-truck compares part year with full year", "SPU-PARTIAL",
  "Contained: false capture % and red lights blanked. The true end of the 2026 column was unverified.",
  "Any 2026 vs 2025 rate.", "Re-cut 2026 from a dated extract (sales now run to %s)." % sales_end.isoformat(), "Internal"),
 ("C", "No vehicle age or model for Israel and the UK", "VIN-IL / VIN-ITUK",
  "The register holds 3,238 vehicles in seven small markets. UK has 29,935 vehicles with no mileage. Israel has none.",
  "The two largest aftersales books have no measured fleet age.", "Israel vehicle list; Duncan mileage.", "Jerome"),
 ("C", "Distributor order cut-off weekday unknown", "ORDER-CUTOFF",
  "Order create dates exist; without each cut-off we cannot call an order late. Israel may place several orders a week and that is allowed.",
  "The order-placement ranking.", "One line from each distributor, Israel first.", "Jerome"),
 ("C", "Sales to dealer covers 5 of 18 distributors", "NETWORK-SALES-TO-DEALER",
  "Canonical files exist for UK truck, UK pickup, Ireland, Greece and Israel (UTI).",
  "Price-volume response cannot be quoted network-wide.", "Ask the other distributors in the one long format.", "Distributors"),
 ("C", "Part numbers missing in claim files by market", "WARR-SAMPLE",
  "No real part number on 95% of Czech, 90% Swiss, 87% Italian, 83% French claim lines, against 8% in Ireland.",
  "Every part-level warranty ranking is biased toward the markets that record part numbers.", "Ask the claim owner why; disclose coverage on every use.", "Claim owner"),
]

CONTRADICTIONS = [
 ("Sales end date", "The data map (00_docs/ISZE_OS_DATA_MAP.yaml, order-latency item) says the sales file ends 31 March 2026. The file itself ends %s." % sales_end.strftime("%d %b %Y"),
  "The data map line is out of date. Whether the order-latency measure itself still stops at 31 March is not verified."),
 ("Warranty export chase", "The contact page dated 22 Sep asks Germany for the pickup export 'from May 2026'. The register of 24 Sep says it arrived and runs to August 2026.",
  "Contact page is out of date. Generate it from the register."),
 ("Green tick vs do-not-quote", "The report passes %d checks; the same register says not to quote the 2026-2030 fleet to anyone." % npass,
  "Passing means files and links work. It says nothing about whether the numbers are true."),
 ("A source that does not exist", "Nine files cite a Duncan Young brake-and-interval deck at a path that is not on this machine, and no deck here has that slide.",
  "Every figure resting on 'slide 14' is unsourced until the deck is found or the figure is re-sourced."),
 ("Mileage status", "The register (24 Sep) and the contact page (22 Sep) still say UK mileage is unconfirmed and wait for Duncan. Japan's mileage tables arrived on 6 Oct (01_data/90_INBOX/_shimauchi_mileage_20261006).",
  "The register predates the mail. Nothing has been re-based on the new tables yet."),
 ("Fleet forecast status", "The register says the V20 fleet forecast is 'per spec', as if not built. Three candidates exist in 06_uio/_CURRENT (a, b, c, built 22-23 Sep) and c failed an independent check.",
  "The register line should say 'candidate c built, failed 3 of 11, awaiting decision'."),
 ("The register was overwritten", "A script replaced the register with a 39-line template on 24 Sep 07:42; the full version was recovered from a backup.",
  "Keep the register under version control and write-protect it from builders."),
 ("A guard that nothing calls", "The check that the default fleet denominator matches the period is called by no build step and targets a retired page.",
  "Wire it into the pre-ship check or delete it."),
]


# ---- html --------------------------------------------------------------
def esc(s):
    return html.escape(str(s), quote=True)


def tip(text, tipt):
    return '<span class="kpi" tabindex="0">%s<span class="tip">%s</span></span>' % (text, esc(tipt))


maxage = max([r[1] or 0 for r in src_rows] + [1])
src_html = ""
for lab, age, cost, rel in src_rows:
    a = age if age is not None else 0
    cls = "old" if a >= 21 else ("mid" if a >= 7 else "new")
    src_html += ('<div class="barrow"><div class="blab">%s<small>%s</small></div><div class="btrack"><div class="bfill %s" style="width:%.1f%%"></div></div><div class="bval">%s</div></div>'
                 % (esc(lab), esc("If stale: " + cost), cls, 100.0 * a / max(maxage, 30), ("%d days" % age) if age is not None else "missing"))
page_html = ""
pmax = max([r[1] for r in page_rows] + [1])
for n, a in page_rows:
    cls = "old" if a >= 60 else ("mid" if a >= 21 else "new")
    page_html += ('<div class="barrow"><div class="blab">%s</div><div class="btrack"><div class="bfill %s" style="width:%.1f%%"></div></div><div class="bval">%d days</div></div>'
                  % (esc(n), cls, 100.0 * a / max(pmax, 30), a))

TIERS = {"A": "Moves a headline by more than a fifth, or makes a number unusable",
         "B": "Sized or already contained; needs a decision or a wiring job",
         "C": "A missing input that blocks a score"}
item_html = ""
for t in "ABC":
    item_html += '<h3><span class="tier t%s">%s</span> %s</h3>' % (t, t, esc(TIERS[t]))
    for tt, title, code, size, moves, nxt, owner in [i for i in ITEMS if i[0] == t]:
        item_html += ('<div class="item"><div class="ih"><b>%s</b> <code>%s</code></div><p class="sz">%s</p>'
                      '<p><span class="lbl">What it moves</span> %s</p><p><span class="lbl">Next step</span> %s <span class="own">Owner: %s</span></p></div>'
                      % (esc(title), esc(code), esc(size), esc(moves), esc(nxt), esc(owner)))
con_html = "".join('<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % (esc(a), esc(b), esc(c)) for a, b, c in CONTRADICTIONS)

page = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ISZE Data Integrity Scorecard</title><style>
:root{--navy:#15233c;--terra:#c0552d;--paper:#f7f4ee;--ink:#222;--pale:#eef3f9;--line:#d8d2c4;--ok:#3d7a4f;--mid:#b8892b}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.5 system-ui,Segoe UI,Arial,sans-serif}
header{background:var(--navy);color:var(--paper);padding:22px 28px}header h1{margin:0;font:600 26px Georgia,serif;color:var(--paper)}header p{margin:6px 0 0;color:var(--paper);opacity:.9;max-width:900px}
main{max-width:1080px;margin:0 auto;padding:18px 20px 60px}h2{font:600 21px Georgia,serif;color:var(--navy);margin:34px 0 4px;border-bottom:2px solid var(--terra);padding-bottom:4px}
h2+p.q{margin:2px 0 12px;color:#555;font-style:italic}h3{font:600 15px system-ui;margin:22px 0 8px;color:var(--navy)}
.chips{display:flex;flex-wrap:wrap;gap:12px;margin:16px 0}.chip{background:#fff;border:1px solid var(--line);border-left:5px solid var(--terra);padding:10px 14px;min-width:200px;flex:1}
.chip b{display:block;font:600 26px Georgia,serif;color:var(--navy)}.chip span{font-size:13px;color:#444}
.kpi{position:relative;cursor:help;border-bottom:1px dotted var(--terra)}.tip{display:none;position:absolute;left:0;top:130%%;z-index:50;width:290px;background:var(--navy);color:var(--paper);border-top:3px solid var(--terra);padding:8px 10px;font:12px/1.4 system-ui;font-weight:400}
.kpi:hover .tip,.kpi:focus .tip{display:block}
.barrow{display:grid;grid-template-columns:minmax(180px,330px) 1fr 80px;gap:10px;align-items:center;margin:7px 0}.blab small{display:block;color:#666;font-size:12px}
.btrack{background:#e6e1d4;height:16px;border-radius:2px}.bfill{height:16px;border-radius:2px}.bfill.old{background:var(--terra)}.bfill.mid{background:var(--mid)}.bfill.new{background:var(--navy)}
.bval{text-align:right;font-variant-numeric:tabular-nums;font-weight:600}
.tier{display:inline-block;color:var(--paper);background:var(--navy);padding:1px 9px;border-radius:2px;font-family:Georgia,serif}.tA{background:var(--terra)}.tB{background:var(--navy)}.tC{background:#5b6b82}
.item{background:#fff;border:1px solid var(--line);padding:10px 14px;margin:8px 0}.item p{margin:4px 0}.ih code{background:var(--pale);color:var(--navy);padding:1px 6px;font-size:12px;margin-left:6px}
.lbl{display:inline-block;min-width:96px;font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--terra);font-weight:700}.own{float:right;color:#555;font-size:13px}
table{border-collapse:collapse;width:100%%;background:#fff}th{background:var(--navy);color:var(--paper);text-align:left;padding:8px 10px;font-weight:600}td{padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}td:first-child{font-weight:600;white-space:nowrap}
.note{background:var(--pale);border-left:5px solid var(--navy);padding:10px 14px;margin:14px 0;color:var(--ink)}footer{margin-top:40px;font-size:12px;color:#555}
@media(max-width:700px){.barrow{grid-template-columns:1fr 70px}.btrack{grid-column:1/3;order:3}.own{float:none;display:block}}
</style></head><body>
<header><h1>Data integrity scorecard</h1><p>Internal. Built %(today)s. Is the data fresh, is it measured rather than assumed, and which open item hurts a published number the most.</p></header>
<main>
<div class="chips">
<div class="chip"><b>%(npass)d / %(nwarn)d / %(nfail)d</b><span>%(t1)s, report of %(rep)s</span></div>
<div class="chip"><b>%(nA)d</b><span>%(t2)s</span></div>
<div class="chip"><b>%(sales)s</b><span>%(t3)s</span></div>
<div class="chip"><b>%(nqa)d of %(nall)d</b><span>%(t4)s</span></div>
</div>
<div class="note"><b>How to read the green.</b> The existing checks confirm that files exist, columns match and derived files are newer than their inputs. They do not confirm that a number is true. The sections below are the part the green tick does not cover.</div>

<h2>1. How old is each source today?</h2><p class="q">Which numbers are we quoting from files that nobody has refreshed?</p>%(src)s
<h2>2. How old is each main page?</h2><p class="q">Which pages still show last quarter's world?</p>%(pages)s
<p class="note">Days since the file was last written, measured on %(today)s. The three oldest pages still run on the fleet forecast that section 3 says is too high.</p>

<h2>3. Which open items hurt a published number most?</h2><p class="q">Ranked by what they move, not by ID. Sizes are copied from the register of 24 Sep; the register does not size every item, and where it does not, this page says so.</p>%(items)s

<h2>4. Where the integrity files contradict each other</h2><p class="q">What would embarrass us if someone read both files side by side?</p>
<table><tr><th>Where</th><th>What the files say</th><th>What it means</th></tr>%(con)s</table>

<h2>5. Housekeeping that hides the live pages</h2><p class="q">Can anyone tell which page is the real one?</p>
<table><tr><th>Measured</th><th>Count</th></tr>
<tr><td>HTML pages outside the archive</td><td>%(nall)d</td></tr>
<tr><td>Of those, test and QA copies inside the live folders</td><td>%(nqa)d</td></tr>
<tr><td>Backup copies (.bak) in the dashboard folders</td><td>%(nbak)d</td></tr>
<tr><td>Ship receipts (prove a page paints, not that its numbers are right)</td><td>%(nrec)d</td></tr></table>
<footer>Sources: 01_data/00_derived/_verification_report.json, _data_integrity_open_issues.md (24 Sep 2026), sales_fact.parquet, file modification dates on this machine. Builder: 02_dashboards/_build/build_integrity_scorecard.py.</footer>
</main></body></html>"""

vals = dict(
    today=TODAY.strftime("%d %b %Y"), npass=npass, nwarn=nwarn, nfail=nfail, rep=rep_date,
    t1=tip("checks passed / warned / failed", "Counts from the verification report. Most checks confirm a file exists or a column matches. They do not test whether a figure is true."),
    t2=tip("open items that move a headline", "Tier A items in section 3. Sizes are copied from the open-issues register; nothing here is a new estimate."),
    t3=tip("sales file runs to", "Latest billing date in sales_fact.parquet, read at build time. The data map still says 31 March 2026."),
    t4=tip("pages are test or QA copies", "QA and test HTML files sitting inside live dashboard folders, excluding the archive. Counted by folder name at build time."),
    nA=len([i for i in ITEMS if i[0] == "A"]), sales=sales_end.strftime("%d %b %Y"),
    nqa=len(qa_html), nall=len(all_html), nbak=len(bak), nrec=len(receipts),
    src=src_html, pages=page_html, items=item_html, con=con_html)
open(OUT, "w", encoding="utf8").write(page % vals)
print("wrote", OUT, os.path.getsize(OUT))
