"""
Build ISZE_GPS_Kosha_v4a / v4b  =  v3d/v3c re-solved on REVISED BP (row 186)
============================================================================
Supersedes the hard-coded BP in build_gps_kosha_v3d.py.  BP (車両部品 / VP
parts target) is now read LIVE from the uploaded PL-Plan, "IX study" sheet,
ROW 186, cols G..J = FY2027..FY2030.  FY2029/FY2030 were revised DOWN
(42.56→41.53M / 48.27→46.39M); FY2027/FY2028 unchanged.

Two modes from ONE builder (set env GPS_MODE):
  net   (v4a) — WARRANTY ON.  GPS% = NET (gross − warranty) ÷ effective cap.
                Net + warranty toward BP.  UTI on UIO v19.   == v3d, new BP.
  gross (v4b) — WARRANTY OFF. GPS% = GROSS ÷ full market cap.  == v3c, new BP,
                UTI on UIO v19 (matched pair: differs from v4a ONLY by warranty).

Math is identical across modes — gross mode simply zeroes warranty, so
net=gross, warr_avg=0, eff_cap=full market cap, SW=0.  Wallets/market caps
come from the v3c template (UTI overridden to v19).  CIS unchanged.
"""
import csv
import os
import sys
import openpyxl
from openpyxl.styles import PatternFill
from openpyxl.utils import column_index_from_string as CI
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DATA  = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data")
KOSHA = DATA / "14_dashboards" / "kosha"
SRC   = KOSHA / "ISZE_GPS_Kosha_v3c.xlsx"                         # gross template (formatting)
WARRCSV = DATA / "00_derived" / "distributor_warranty_expense_fiscal.csv"
PLAN  = DATA / "11_planning" / "ISZE PL Plan FY2026 2027 2028 20260205_2 -.xlsx"  # uploaded plan (moved into 11_planning/)

MODE  = os.environ.get("GPS_MODE", "net").lower()
assert MODE in ("net", "gross"), f"GPS_MODE must be net|gross, got {MODE!r}"
GROSS = (MODE == "gross")
OUT   = KOSHA / ("ISZE_GPS_Kosha_v4b.xlsx" if GROSS else "ISZE_GPS_Kosha_v4a.xlsx")

KOSHA.mkdir(parents=True, exist_ok=True)

# ---- BP target read LIVE from PL Plan row 186 (IX study) -------------------
def load_bp():
    wb = openpyxl.load_workbook(PLAN, data_only=True)
    ws = wb["IX study"]
    cols = {2027: 7, 2028: 8, 2029: 9, 2030: 10}   # G H I J
    bp = {yr: float(ws.cell(186, c).value) for yr, c in cols.items()}
    lbl = ws.cell(186, 2).value
    return bp, lbl

BP, BP_LABEL = load_bp()
CIS = {2027: 1.70e6, 2028: 1.80e6, 2029: 1.90e6, 2030: 2.00e6}

R = 739.2  # flat CV rate (UTI, ITUK)
UTI_UIO = {2024:10336, 2025:10336, 2026:10760, 2027:10972, 2028:11280, 2029:11581, 2030:11882}
UTI_MSACT = {y: UTI_UIO[y]*R for y in (2024,2025,2026)}
UTI_MS    = {y: UTI_UIO[y]*R for y in (2027,2028,2029,2030)}

GREEN = PatternFill('solid', fgColor='70AD47')
AMBER = PatternFill('solid', fgColor='FFC000')
RED   = PatternFill('solid', fgColor='C00000')
def band(p):
    if p is None: return None
    if p >= 1.0:  return RED
    if p >= 0.85: return AMBER
    return GREEN

def warr_avg(nm, w):
    return (w[2024] + w[2025] + w[2026]) / 3

def eff(ms, wavg):
    return max(ms - wavg, ms * 0.05) if ms else None

# ---- load sources ----------------------------------------------------------
if GROSS:
    WARR = {}                                          # warranty OFF
else:
    WARR = {r['db']: (float(r['warr_FY2024']), float(r['warr_FY2025']), float(r['warr_FY2026']))
            for r in csv.DictReader(open(WARRCSV, encoding="utf-8"))}

wb = openpyxl.load_workbook(SRC)            # keep formatting
t1 = wb["GPS Actuals FY2024-26"]
t2 = wb["GPS Projection FY2027-30"]
t3 = wb["Kosha Gap"]
t4 = wb["Method"]

t2map = {t2.cell(r,1).value: r for r in range(11,30)}
DB, order = {}, []
for r in range(4,23):
    nm = t1.cell(r,1).value
    if not nm: continue
    order.append((nm, r))
    gross = {2024:t1.cell(r,2).value, 2025:t1.cell(r,5).value, 2026:t1.cell(r,8).value}
    w = WARR.get(nm, (0.0,0.0,0.0))
    d = dict(row1=r, row2=t2map.get(nm),
             gross=gross, warr={2024:w[0],2025:w[1],2026:w[2]},
             net={2024:max(0.0,gross[2024]-w[0]), 2025:max(0.0,gross[2025]-w[1]), 2026:max(0.0,gross[2026]-w[2])},
             msact={2024:t1.cell(r,3).value, 2025:t1.cell(r,6).value, 2026:t1.cell(r,9).value},
             ms={})
    rr = d['row2']
    for yr,(gc,rc) in {2027:('D','E'),2028:('G','H'),2029:('J','K'),2030:('M','N')}.items():
        gg = t2.cell(rr,CI(gc)).value; rev = t2.cell(rr,CI(rc)).value
        d['ms'][yr] = (rev/gg) if (gg and rev) else None
    DB[nm] = d
# UTI -> v19 (both modes: matched net/gross pair)
DB['UTI']['msact'] = dict(UTI_MSACT); DB['UTI']['ms'] = dict(UTI_MS)
# per-DB warranty average + effective market cap; base on eff wallet (FY25/FY26)
for nm, d in DB.items():
    w = d['warr']
    d['wavg'] = warr_avg(nm, w)
    d['effact'] = {yr: eff(d['msact'][yr], d['wavg']) for yr in (2024, 2025, 2026)}
    d['eff'] = {yr: eff(d['ms'].get(yr), d['wavg']) for yr in (2027, 2028, 2029, 2030)}
    d['base'] = (
        d['net'][2025] / d['effact'][2025] + d['net'][2026] / d['effact'][2026]
    ) / 2
SW = sum(d['wavg'] for d in DB.values())
net_warr = {yr: sum(DB[n]['warr'][yr] for n in DB) for yr in (2024, 2025, 2026)}

# Option A on effective market cap: Σ eff_ms·(base+X) + Σ wavg = BP − CIS
X = {}
for yr in (2027, 2028, 2029, 2030):
    names = [n for n in DB if DB[n]['eff'].get(yr)]
    se = sum(DB[n]['eff'][yr] for n in names)
    sb = sum(DB[n]['eff'][yr] * DB[n]['base'] for n in names)
    X[yr] = (BP[yr] - CIS[yr] - SW - sb) / se

def req(nm, yr):
    return DB[nm]['base'] + X[yr]

NETLBL = "GROSS billing" if GROSS else "NET billing (warranty deducted)"

# ================= TAB 1 : ACTUALS =========================================
if GROSS:
    t1['A1'] = "ISZE — GPS Capture Rate  |  FY2024–FY2026 Actuals  |  Gross billing (no warranty deduction)"
    t1['A2'] = ("Source: SAP billing (GPS-eligible; transport, rebates, credit notes, Shell Rimula Israel excluded).  "
                "Actuals GPS% = GROSS billing ÷ full max spend.  Projection GPS% = gross ÷ market cap (UIO wallet).  "
                "UTI wallet on UIO v19.  Ireland = SIMI hybrid.  "
                "Colour: Green <85%  ·  Amber 85–100%  ·  Red ≥100%")
    for c,txt in (('B','FY24 Bill €'),('E','FY25 Bill €'),('H','FY26 Bill €')):
        t1[f'{c}3'] = txt
else:
    t1['A1'] = "ISZE — GPS Capture Rate  |  FY2024–FY2026 Actuals  |  Net billing (warranty deducted)"
    t1['A2'] = ("Source: SAP billing (GPS-eligible; transport, rebates, credit notes, Shell Rimula Israel excluded).  "
                "Actuals GPS% = NET billing (gross − warranty) ÷ full max spend.  Projection GPS% = NET ÷ effective market cap "
                "(max spend − per-DB warranty average).  Warranty from distributor_warranty_expense_fiscal.csv "
                "(fiscal Apr–Mar; see 06_Warranty/DISTRIBUTOR_WARRANTY_EXPENSE.md), "
                "UTI wallet on UIO v19.  Ireland = SIMI hybrid.  "
                "Colour: Green <85%  ·  Amber 85–100%  ·  Red ≥100%")
    for c,txt in (('B','FY24 Net Bill €'),('E','FY25 Net Bill €'),('H','FY26 Net Bill €')):
        t1[f'{c}3'] = txt

tot = {k:0.0 for k in ('b24','m24','b25','m25','b26','m26')}
for nm,r in order:
    d = DB[nm]
    t1.cell(r,2).value = d['net'][2024]; t1.cell(r,3).value = d['msact'][2024]
    t1.cell(r,5).value = d['net'][2025]; t1.cell(r,6).value = d['msact'][2025]
    t1.cell(r,8).value = d['net'][2026]; t1.cell(r,9).value = d['msact'][2026]
    g24 = d['net'][2024]/d['msact'][2024]
    g25 = d['net'][2025]/d['msact'][2025]
    g26 = d['net'][2026]/d['msact'][2026]
    for col,val in ((4,g24),(7,g25),(10,g26),(11,d['base'])):
        cell = t1.cell(r,col); cell.value = val
        b = band(val);  cell.fill = b if b else cell.fill
    if nm == 'UTI':
        t1.cell(r,12).value = UTI_UIO[2026]
        t1.cell(r,14).value = "UIO v19: IML Office No.3 regs — CV parc reverses to growth"
    tot['b24']+=d['net'][2024]; tot['m24']+=d['msact'][2024]
    tot['b25']+=d['net'][2025]; tot['m25']+=d['msact'][2025]
    tot['b26']+=d['net'][2026]; tot['m26']+=d['msact'][2026]
t1.cell(23,2).value=tot['b24']; t1.cell(23,3).value=tot['m24']; t1.cell(23,4).value=tot['b24']/tot['m24']
t1.cell(23,5).value=tot['b25']; t1.cell(23,6).value=tot['m25']; t1.cell(23,7).value=tot['b25']/tot['m25']
t1.cell(23,8).value=tot['b26']; t1.cell(23,9).value=tot['m26']; t1.cell(23,10).value=tot['b26']/tot['m26']

# ================= TAB 2 : PROJECTION ======================================
def keyobs(nm, yr):
    d = DB[nm]
    r_ = req(nm, yr)
    em = d['eff'][yr]
    netc = em * r_
    if r_ > 1.0:
        cap = "market cap" if GROSS else f"eff. cap (max spend − warr avg €{d['wavg']/1e3:,.0f}K)"
        return (f"⚠ IMPOSSIBLE — {r_*100:.0f}% of {cap}.")
    if GROSS:
        return (f"market cap €{em/1e3:,.0f}K"
                f"   ·   gross €{netc/1e3:,.0f}K → BP"
                f"   ·   GPS% {d['base']*100:.0f}→{r_*100:.0f}%")
    return (f"eff cap €{em/1e3:,.0f}K (ms €{d['ms'][yr]/1e3:,.0f}K − warr €{d['wavg']/1e3:,.0f}K)"
            f"   ·   net €{netc/1e3:,.0f}K + warr → €{(netc+d['wavg'])/1e3:,.0f}K BP"
            f"   ·   GPS% {d['base']*100:.0f}→{r_*100:.0f}%")

YCOL = {2027:('D','E','F'),2028:('G','H','I'),2029:('J','K','L'),2030:('M','N','O')}
net_tot = {yr:0.0 for yr in (2027,2028,2029,2030)}
eff_tot = {yr:0.0 for yr in (2027,2028,2029,2030)}
imposs  = {yr:[] for yr in (2027,2028,2029,2030)}
for nm,d in DB.items():
    r = d['row2']
    t2.cell(r,2).value = d['base']
    for yr,(gc,rc,kc) in YCOL.items():
        rr = req(nm, yr)
        em = d['eff'][yr]
        netc = em * rr
        grossrev = netc + d['wavg']
        t2.cell(r,CI(gc)).value = rr
        t2.cell(r,CI(rc)).value = grossrev
        t2.cell(r,CI(kc)).value = keyobs(nm,yr)
        eff_tot[yr] += em
        net_tot[yr] += netc
        if rr > 1.0:
            imposs[yr].append(nm)
capword = "mkt cap" if GROSS else "eff cap"
for gc,rc,yr in [('D','E',2027),('G','H',2028),('J','K',2029),('M','N',2030)]:
    t2.cell(10,CI(gc)).value = f"FY{yr}\nGPS%\n({capword})"
    t2.cell(10,CI(rc)).value = f"FY{yr}\nGross €\n→ BP"
for yr,(gc,rc,kc) in YCOL.items():
    t2.cell(40,CI(gc)).value = net_tot[yr] / eff_tot[yr]
    t2.cell(40,CI(rc)).value = net_tot[yr] + SW
if GROSS:
    t2['A1'] = ("ISZE  ·  GPS Projection FY2027–FY2030  ·  Option A (uniform uplift)  ·  "
                "Gross ÷ market cap (UIO wallet)  ·  No cap")
else:
    t2['A1'] = ("ISZE  ·  GPS Projection FY2027–FY2030  ·  Option A (uniform uplift)  ·  "
                "Net ÷ effective market cap (max spend − warr avg)  ·  No cap")
def pct(nm,yr): return req(nm,yr)*100
imp30 = ', '.join(f'{n} ({pct(n,2030):.0f}%)' for n in imposs[2030]) or 'none'
capnote = "" if GROSS else " (UIO wallet − warranty avg €%.1fM/yr from Distributor Warranty Expense)" % (SW/1e6)
t2['A2'] = f"  FY2027  |  X = {X[2027]*100:+.2f}pp  |  {'✓ All within 100%' if not imposs[2027] else '⚠ '+str(len(imposs[2027]))+' DB(s) IMPOSSIBLE'}"
t2['A3'] = (f"  Required GPS% uplift X = {X[2027]*100:+.2f}pp on {capword}{capnote}.  UTI GROWS (UIO v19).")
t2['A4'] = f"  FY2028 — X = {X[2028]*100:+.2f}pp  |  {'✓ All within 100%' if not imposs[2028] else '⚠ '+str(len(imposs[2028]))+' DB(s) IMPOSSIBLE'}"
t2['A5'] = "  Modest, network-wide. Large fleets absorb it; IBX edges toward its penetration ceiling."
t2['A6'] = f"  FY2029 — X = {X[2029]*100:+.2f}pp  |  {'✓ All within 100%' if not imposs[2029] else '⚠ '+str(len(imposs[2029]))+' DB(s) IMPOSSIBLE'}"
t2['A7'] = (f"  Required GPS% uplift X = {X[2029]*100:+.2f}pp on {capword}. "
            f"{'No DB exceeds 100%' if not imposs[2029] else ', '.join(imposs[2029])+' exceed 100%'}.")
t2['A8'] = f"  FY2030 — X = {X[2030]*100:+.2f}pp  |  {'✓ All within 100%' if not imposs[2030] else '⚠ '+str(len(imposs[2030]))+' DB(s) IMPOSSIBLE'}"
t2['A9'] = (f"  Required GPS% uplift X = {X[2030]*100:+.2f}pp. "
            f"{('Impossible: '+imp30) if imposs[2030] else 'No DB exceeds 100% of '+capword}. "
            f"ITUK must lift {DB['ITUK']['base']*100:.0f}%→{pct('ITUK',2030):.0f}%.")

# ================= TAB 3 : KOSHA GAP =======================================
uio_net26 = sum(DB[n]['net'][2026] for n in DB)
uio_warr26 = sum(DB[n]['warr'][2026] for n in DB)
cis26 = t3.cell(6,2).value
t3.cell(5,2).value = uio_net26 + uio_warr26
total26 = uio_net26 + uio_warr26 + cis26
t3.cell(7,2).value = total26
bp26 = t3.cell(8,2).value
t3.cell(9,2).value = total26 - bp26
t3.cell(10,2).value = (total26 - bp26)/bp26
t3['A5'] = ("Revenue toward BP — UIO DBs (gross billing) (€)" if GROSS
            else "Revenue toward BP — UIO DBs (net capture + warranty) (€)")
colmap = {2027:3,2028:4,2029:5,2030:6}
for yr,c in colmap.items():
    t3.cell(12,c).value = X[yr]
    t3.cell(13,c).value = len(imposs[yr])
    fy_tot = t3.cell(7,c).value
    n = yr-2026
    t3.cell(15,c).value = (fy_tot/total26)**(1/n) - 1
t3.cell(13,2).value = 0
t3.cell(18,5).value = "\n".join(f"⚠ {n}" for n in imposs[2029]) if imposs[2029] else "✓ None"
t3.cell(18,6).value = "\n".join(f"⚠ {n}" for n in imposs[2030]) if imposs[2030] else "✓ None"
if GROSS:
    t3['A2'] = ("⚠  INTERNAL — NOT FOR EXTERNAL DISTRIBUTION  |  Forecast: GPS% = gross ÷ market cap (UIO wallet).  "
                f"FY26 runs {'+' if total26>=bp26 else ''}€{(total26-bp26)/1e3:.0f}K vs BP; {len(imposs[2030])} DB"
                f"{' impossible' if imposs[2030] else ' feasible'} by FY2030.  UTI on UIO v19.  BP = row 186 (revised).")
else:
    t3['A2'] = ("⚠  INTERNAL — NOT FOR EXTERNAL DISTRIBUTION  |  Forecast: GPS% = net ÷ (max spend − warranty avg).  "
                f"Per-DB warranty avg from Distributor Warranty Expense (Σ €{SW/1e6:.1f}M/yr).  Gross toward BP = net + warranty avg.  "
                f"FY26 runs +€{(total26-bp26)/1e3:.0f}K vs BP; {len(imposs[2030])} DB"
                f"{' impossible (IBX)' if imposs[2030] else ' feasible'} by FY2030.  UTI on UIO v19.  BP = row 186 (revised).")

# ================= TAB 4 : METHOD ==========================================
if GROSS:
    t4['B2'] = ("WHAT:  For each UIO distributor, FY2024–FY2026 GPS-eligible billing from the SAP extract.  "
                "GROSS basis — warranty is NOT deducted (v4b is the gross twin of v4a).  GPS% = gross ÷ max spend.  "
                "EXCLUSIONS (upstream): transport, Shell Rimula (Israel), credit notes (G2/CR), rebates, late-payment "
                "interest, service fees.")
else:
    t4['B2'] = ("WHAT:  For each UIO distributor, FY2024–FY2026 GPS-eligible billing from the SAP extract.  "
                "WARRANTY IS DEDUCTED for ALL three years:  GPS% = NET = gross − Distributor Warranty Expense.  "
                "Source: distributor_warranty_expense_fiscal.csv — CV claim exports (REPA6), LCV grain, UMI, "
                "gps_warranty_cy2025.json; fiscal FY Apr–Mar aligned to billing.  "
                f"Network warranty expense: FY24 €{net_warr[2024]/1e6:.2f}M / FY25 €{net_warr[2025]/1e6:.2f}M / "
                f"FY26 €{net_warr[2026]/1e6:.2f}M.\n\n"
                "EXCLUSIONS (upstream): transport, Shell Rimula (Israel), credit notes (G2/CR), rebates, late-payment "
                "interest, service fees.")
t4['B3'] = ("UIO v19 (UTI): UTI (Israel CV) re-projected on IML Office No.3 "
            "registrations (17-Jun-2026): total parc 2025 10,336 → 2030 11,882 — reverses the prior decline. "
            "Wallet = total UIO × €739.2 (flat CV rate, consistent with ITUK).")
if GROSS:
    t4['B4'] = ("ACTUALS & FORECAST both gross.  Actuals (Tab 1): GPS% = gross ÷ full max spend.  "
                "Forecast (Tab 2): GPS% = required gross ÷ market cap (UIO wallet).  "
                "Option A solves X so Σ market_cap·(base+X) + CIS = BP.")
else:
    t4['B4'] = ("TWO contexts — do not conflate.  (1) ACTUALS (Tab 1): GPS% = (gross − actual warranty) ÷ full max spend.  "
                "(2) FORECAST (Tab 2): GPS% = required net ÷ EFFECTIVE market cap = max spend − per-DB warranty average.  "
                "warr_avg = mean of available warranty-expense years (FY24+25 for ITUK/UTI; FY24–26 for others).  Gross toward BP = "
                "net + warr_avg.  Option A solves X so Σ eff_cap·(base+X) + Σ warr_avg + CIS = BP.")
t4['B5'] = (f"BP TARGET (車両部品 / VP parts) read LIVE from PL Plan row 186: "
            f"FY27 €{BP[2027]/1e6:.2f}M · FY28 €{BP[2028]/1e6:.2f}M · FY29 €{BP[2029]/1e6:.2f}M · FY30 €{BP[2030]/1e6:.2f}M.  "
            f"GPS Base = avg FY25/FY26 {NETLBL} ÷ {'market cap' if GROSS else 'eff. cap'}. Bases: "
            f"ITUK {DB['ITUK']['base']*100:.1f}%, IUK {DB['IUK']['base']*100:.1f}%, UTI {DB['UTI']['base']*100:.1f}% (UIO v19), "
            f"IBX {DB['IBX']['base']*100:.1f}%, Ireland {DB['Ireland']['base']*100:.1f}% (SIMI)."
            + ("" if GROSS else
               f"\n\nWARRANTY AVERAGE (deducted from forecast market cap): per-DB mean from "
               f"distributor_warranty_expense_fiscal.csv; Σ €{SW/1e6:.2f}M/yr network. eff_cap[yr] = UIO wallet[yr] − warr_avg."))

wb.save(OUT)
print(f"MODE={MODE}  Saved → {OUT}")
print(f"BP row 186 ({BP_LABEL}): " + " ".join(f"FY{y}=€{BP[y]/1e6:.3f}M" for y in (2027,2028,2029,2030)))
print(f"Network warr avg (Σ, deducted from forecast cap): €{SW/1e6:.2f}M/yr")
print(f"GPS% uplift X: " + " ".join(f"FY{y}={X[y]*100:+.2f}pp" for y in (2027,2028,2029,2030)))
for y in (2027,2028,2029,2030):
    print(f"  FY{y} impossible({len(imposs[y])}): {imposs[y]}")
print(f"Network actuals {MODE} GPS% (full cap): "
      f"FY24 {tot['b24']/tot['m24']*100:.1f}% FY25 {tot['b25']/tot['m25']*100:.1f}% FY26 {tot['b26']/tot['m26']*100:.1f}%")
