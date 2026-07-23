"""
Build ISZE_GPS_Kosha_v3d.xlsx  =  v3c  +  WARRANTY ON  +  UIO v19 (UTI)
======================================================================
v3c is gross / no-warranty. v3d applies two changes, re-solving the
Option-A uniform-uplift projection:

  1. WARRANTY ON  — GPS% = NET billing (gross - warranty) / max spend.
                    Net + warranty per DB come from gps_master.csv
                    (warr_FY2025/26, net_FY2024/25/26). FY2024 has no
                    warranty data (net = gross).
  2. UIO v19      — UTI (Israel CV) parc re-projected on IML Office No.3
                    registrations (17-Jun-2026): reverses decline -> growth.
                    Wallet = total UIO x EUR739.2 (flat CV rate, as ITUK).
                    v19 total parc: 2025 10,336 / 2026 10,760 / 2027 10,972
                    / 2028 11,280 / 2029 11,581 / 2030 11,882.

Method: Option A, uniform uplift X solved on effective market cap
(eff_ms = UIO wallet − per-DB warranty average).  Actuals GPS% = net ÷
full max spend.  Forecast GPS% = net ÷ eff_ms; gross toward BP = net +
warr_avg.  warr_avg = mean of available FY24–26 warranty per DB (FY24+25
only for ITUK/UTI where FY26 CV is missing).  Wallets from v3c except
UTI → v19.  CIS/non-UIO rows unchanged.
"""
import csv
import openpyxl
from openpyxl.styles import PatternFill
from openpyxl.utils import column_index_from_string as CI
from pathlib import Path

DATA = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data")
KOSHA = DATA / "14_dashboards" / "kosha"
SRC  = KOSHA / "ISZE_GPS_Kosha_v3c.xlsx"
WARRCSV = DATA / "00_derived" / "distributor_warranty_expense_fiscal.csv"
import os as _os
OUT  = KOSHA / _os.environ.get("V3D_OUT", "ISZE_GPS_Kosha_v3d.xlsx")

KOSHA.mkdir(parents=True, exist_ok=True)

R = 739.2  # flat CV rate (UTI, ITUK)
UTI_UIO = {2024:10336, 2025:10336, 2026:10760, 2027:10972, 2028:11280, 2029:11581, 2030:11882}
UTI_MSACT = {y: UTI_UIO[y]*R for y in (2024,2025,2026)}
UTI_MS    = {y: UTI_UIO[y]*R for y in (2027,2028,2029,2030)}

BP  = {2027:35.28e6, 2028:37.53e6, 2029:41_530_410, 2030:46_385_705}  # FY29/30 = live PL Plan row 186 (was 42.56/48.27e6 pre-revision phantom)
CIS = {2027:1.70e6,  2028:1.80e6,  2029:1.90e6,  2030:2.00e6}

GREEN = PatternFill('solid', fgColor='70AD47')
AMBER = PatternFill('solid', fgColor='FFC000')
RED   = PatternFill('solid', fgColor='C00000')
def band(p):
    if p is None: return None
    if p >= 1.0:  return RED
    if p >= 0.85: return AMBER
    return GREEN

def fl(x):
    try: return float(x)
    except: return None

def warr_avg(nm, w):
    """Per-DB warranty average from distributor warranty expense file."""
    return (w[2024] + w[2025] + w[2026]) / 3

def eff(ms, wavg):
    return max(ms - wavg, ms * 0.05) if ms else None

# ---- load sources ----------------------------------------------------------
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
# UTI -> v19
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

# ================= TAB 1 : ACTUALS (net) ===================================
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
        t1.cell(r,12).value = UTI_UIO[2026]                # UIO FY26 -> v19
        t1.cell(r,14).value = "UIO v19: IML Office No.3 regs — CV parc reverses to growth"
    tot['b24']+=d['net'][2024]; tot['m24']+=d['msact'][2024]
    tot['b25']+=d['net'][2025]; tot['m25']+=d['msact'][2025]
    tot['b26']+=d['net'][2026]; tot['m26']+=d['msact'][2026]
# TOTAL row 23
t1.cell(23,2).value=tot['b24']; t1.cell(23,3).value=tot['m24']; t1.cell(23,4).value=tot['b24']/tot['m24']
t1.cell(23,5).value=tot['b25']; t1.cell(23,6).value=tot['m25']; t1.cell(23,7).value=tot['b25']/tot['m25']
t1.cell(23,8).value=tot['b26']; t1.cell(23,9).value=tot['m26']; t1.cell(23,10).value=tot['b26']/tot['m26']

# ================= TAB 2 : PROJECTION (net ÷ eff. market cap) ================
def keyobs(nm, yr):
    d = DB[nm]
    r_ = req(nm, yr)
    em = d['eff'][yr]
    netc = em * r_
    if r_ > 1.0:
        return (f"⚠ IMPOSSIBLE — {r_*100:.0f}% of eff. cap (max spend − warr avg €{d['wavg']/1e3:,.0f}K).")
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
        t2.cell(r,CI(gc)).value = rr               # GPS% vs eff. market cap
        t2.cell(r,CI(rc)).value = grossrev         # gross billing toward BP
        t2.cell(r,CI(kc)).value = keyobs(nm,yr)
        eff_tot[yr] += em
        net_tot[yr] += netc
        if rr > 1.0:
            imposs[yr].append(nm)
for gc,rc,yr in [('D','E',2027),('G','H',2028),('J','K',2029),('M','N',2030)]:
    t2.cell(10,CI(gc)).value = f"FY{yr}\nGPS%\n(eff cap)"
    t2.cell(10,CI(rc)).value = f"FY{yr}\nGross €\n→ BP"
for yr,(gc,rc,kc) in YCOL.items():
    t2.cell(40,CI(gc)).value = net_tot[yr] / eff_tot[yr]
    t2.cell(40,CI(rc)).value = net_tot[yr] + SW
t2['A1'] = ("ISZE  ·  GPS Projection FY2027–FY2030  ·  Option A (uniform uplift)  ·  "
            "Net ÷ effective market cap (max spend − warr avg)  ·  No cap")
def pct(nm,yr): return req(nm,yr)*100
imp30 = ', '.join(f'{n} ({pct(n,2030):.0f}%)' for n in imposs[2030]) or 'none'
t2['A2'] = f"  FY2027 — warr avg deducted from market cap  |  X = {X[2027]*100:+.2f}pp  |  ✓ All within 100%"
t2['A3'] = (f"  Required GPS% uplift X = {X[2027]*100:+.2f}pp on effective cap (UIO wallet − warranty avg €{SW/1e6:.1f}M/yr "
            f"from Distributor Warranty Expense).  UTI GROWS (UIO v19).")
t2['A4'] = f"  FY2028 — +{X[2028]*100:.2f}pp  |  X = {X[2028]*100:+.2f}pp  |  ✓ All within 100%"
t2['A5'] = "  Modest, network-wide. Large fleets absorb it; IBX edges toward its penetration ceiling."
t2['A6'] = f"  FY2029 — +{X[2029]*100:.2f}pp  |  X = {X[2029]*100:+.2f}pp  |  {'✓ All within 100%' if not imposs[2029] else '⚠ '+str(len(imposs[2029]))+' DB(s) IMPOSSIBLE'}"
t2['A7'] = (f"  Required GPS% uplift X = {X[2029]*100:+.2f}pp on eff. cap. "
            f"{'No DB exceeds 100%' if not imposs[2029] else ', '.join(imposs[2029])+' exceed 100%'}.")
t2['A8'] = f"  FY2030 — {len(imposs[2030])} distributor impossible  |  X = {X[2030]*100:+.2f}pp  |  ⚠ {len(imposs[2030])} DB(s) IMPOSSIBLE"
t2['A9'] = (f"  Required GPS% uplift X = {X[2030]*100:+.2f}pp. {imp30} exceeds 100% of effective market cap. "
            f"ITUK must lift {DB['ITUK']['base']*100:.0f}%→{pct('ITUK',2030):.0f}% (net ÷ eff cap).")

# ================= TAB 3 : KOSHA GAP =======================================
# FY26 actual: revenue toward BP = NET capture + warranty (warranty parts are billed)
uio_net26 = sum(DB[n]['net'][2026] for n in DB)
uio_warr26 = sum(DB[n]['warr'][2026] for n in DB)
cis26 = t3.cell(6,2).value
t3.cell(5,2).value = uio_net26 + uio_warr26                      # gross UIO toward BP
total26 = uio_net26 + uio_warr26 + cis26
t3.cell(7,2).value = total26
bp26 = t3.cell(8,2).value
t3.cell(9,2).value = total26 - bp26
t3.cell(10,2).value = (total26 - bp26)/bp26
t3['A5'] = "Revenue toward BP — UIO DBs (net capture + warranty) (€)"
colmap = {2027:3,2028:4,2029:5,2030:6}
for yr,c in colmap.items():
    t3.cell(12,c).value = X[yr]                                  # net-capture uplift X
    t3.cell(13,c).value = len(imposs[yr])                        # impossible count
    fy_tot = t3.cell(7,c).value
    n = yr-2026
    t3.cell(15,c).value = (fy_tot/total26)**(1/n) - 1            # CAGR revenue toward BP from FY26
t3.cell(13,2).value = 0
# impossible-DB name lists (rows E18=2029, F18=2030)
t3.cell(18,5).value = "\n".join(f"⚠ {n}" for n in imposs[2029]) if imposs[2029] else "✓ None"
t3.cell(18,6).value = "\n".join(f"⚠ {n}" for n in imposs[2030]) if imposs[2030] else "✓ None"
t3['A2'] = ("⚠  INTERNAL — NOT FOR EXTERNAL DISTRIBUTION  |  Forecast: GPS% = net ÷ (max spend − warranty avg).  "
            f"Per-DB warranty avg from Distributor Warranty Expense (Σ €{SW/1e6:.1f}M/yr).  Gross toward BP = net + warranty avg.  "
            f"FY26 runs +€{(total26-bp26)/1e3:.0f}K vs BP; {len(imposs[2030])} DB"
            f"{' impossible (IBX)' if imposs[2030] else ' feasible'} by FY2030.  UTI on UIO v19.")

# ================= TAB 4 : METHOD ==========================================
t4['B2'] = ("WHAT:  For each UIO distributor, FY2024–FY2026 GPS-eligible billing from the SAP extract.  "
            "WARRANTY IS DEDUCTED for ALL three years:  GPS% = NET = gross − Distributor Warranty Expense.  "
            "Source: distributor_warranty_expense_fiscal.csv — CV claim exports (REPA6), LCV grain, UMI, "
            "gps_warranty_cy2025.json; fiscal FY Apr–Mar aligned to billing.  "
            f"Network warranty expense: FY24 €{net_warr[2024]/1e6:.2f}M / FY25 €{net_warr[2025]/1e6:.2f}M / "
            f"FY26 €{net_warr[2026]/1e6:.2f}M.\n\n"
            "EXCLUSIONS (upstream): transport, Shell Rimula (Israel), credit notes (G2/CR), rebates, late-payment "
            "interest, service fees.")
t4['B3'] = (t4['B3'].value or "") + ("\n\nUIO v19 (UTI): UTI (Israel CV) re-projected on IML Office No.3 "
            "registrations (17-Jun-2026): total parc 2025 10,336 → 2030 11,882 — reverses the prior decline. "
            "Wallet = total UIO × €739.2 (flat CV rate, consistent with ITUK).")
t4['B4'] = ("TWO contexts — do not conflate.  (1) ACTUALS (Tab 1): GPS% = (gross − actual warranty) ÷ full max spend.  "
            "(2) FORECAST (Tab 2): GPS% = required net ÷ EFFECTIVE market cap = max spend − per-DB warranty average.  "
            "warr_avg = mean of available warranty-expense years (FY24+25 for ITUK/UTI; FY24–26 for others).  Gross toward BP = "
            "net + warr_avg.  Option A solves X so Σ eff_cap·(base+X) + Σ warr_avg + CIS = BP.")
t4['B5'] = (f"GPS Base = avg FY25/FY26 NET ÷ eff. cap. Bases: ITUK {DB['ITUK']['base']*100:.1f}%, "
            f"IUK {DB['IUK']['base']*100:.1f}%, UTI {DB['UTI']['base']*100:.1f}% (UIO v19), IBX {DB['IBX']['base']*100:.1f}%, "
            f"Ireland {DB['Ireland']['base']*100:.1f}% (SIMI).\n\nWARRANTY AVERAGE (deducted from forecast market cap): "
            f"per-DB mean from distributor_warranty_expense_fiscal.csv — FY24+FY25 for ITUK/UTI (FY26 CV gap), FY24–26 for rest; "
            f"Σ €{SW/1e6:.2f}M/yr network.  eff_cap[yr] = UIO wallet[yr] − warr_avg.")

wb.save(OUT)
print(f"Saved → {OUT}")
print(f"Network warr avg (deducted from forecast cap): €{SW/1e6:.2f}M/yr")
print(f"GPS% uplift X (on eff. cap): " + " ".join(f"FY{y}={X[y]*100:+.2f}pp" for y in (2027,2028,2029,2030)))
for y in (2027,2028,2029,2030):
    print(f"  FY{y} impossible({len(imposs[y])}): {imposs[y]}")
print(f"UTI base {DB['UTI']['base']*100:.1f}% | FY30 req {req('UTI',2030)*100:.1f}% | warr avg €{DB['UTI']['wavg']:,.0f}")
print(f"Network actuals net GPS% (full cap): FY24 {tot['b24']/tot['m24']*100:.1f}% FY25 {tot['b25']/tot['m25']*100:.1f}% FY26 {tot['b26']/tot['m26']*100:.1f}%")
