"""
GPS / Kosha Excel Builder  —  generates two options:
  B  "GPS · Toggle"      single sheet with warranty ON/OFF toggle cell (A1)
  C  "GPS · Executive"   clean net-of-warranty view, no mechanics
     "GPS · Working"     full gross/net/warranty breakdown for analysts
  +  "Legend"            shared legend tab

Output: ISZE/01_data/14_dashboards/kosha/GPS_Kosha_FY2024_2030.xlsx
"""
import csv
import json
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import column_index_from_string as col_idx, get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from pathlib import Path
import sys

_TOOLS = Path(__file__).resolve().parent.parent / "04_tools"
sys.path.insert(0, str(_TOOLS))
from _shared.paths import DASHBOARDS_JSON_DIR, DERIVED_DIR, ISZE_ROOT  # noqa: E402

ROOT = ISZE_ROOT
BILLING_JSON = DERIVED_DIR / "gps_billing_clean.json"
OUT = DASHBOARDS_JSON_DIR / "kosha" / "GPS_Kosha_FY2024_2030.xlsx"

# ── BILLING ───────────────────────────────────────────────────────────────────
billing = json.loads(BILLING_JSON.read_text(encoding="utf-8"))
for fy in ("2024", "2025", "2026"):
    v = billing.get("UNK_146", {}).get(fy, 0)
    if v:
        billing.setdefault("ITUK", {})[fy] = billing["ITUK"].get(fy, 0) + v

def b(db, fy): return billing.get(db, {}).get(str(fy), 0) or 0

# ── WARRANTY (fiscal FY Apr–Mar, Distributor Warranty Expense) ───────────────
WARR_CSV = DERIVED_DIR / "distributor_warranty_expense_fiscal.csv"
# build_gps_kosha label quirks vs canonical v3c names
_WARR_ALIAS = {"RSA": "Norway", "Greece": "RSA"}


def _load_warranty_fy() -> tuple[dict, dict, dict]:
    f24, f25, f26 = {}, {}, {}
    for r in csv.DictReader(open(WARR_CSV, encoding="utf-8")):
        if r["db"] == "MIDI":
            continue
        db = _WARR_ALIAS.get(r["db"], r["db"])
        f24[db] = int(float(r["warr_FY2024"]))
        f25[db] = int(float(r["warr_FY2025"]))
        f26[db] = int(float(r["warr_FY2026"]))
    return f24, f25, f26


WARRANTY_FY24, WARRANTY_FY25, WARRANTY_FY26 = _load_warranty_fy()

# ── MAX SPEND ─────────────────────────────────────────────────────────────────
MAX_SPEND = {
    'ITUK':       {2025:14_290_704,2026:12_535_797,2027:13_049_973,2028:13_481_973,2029:13_857_339,2030:14_198_701},
    'IUK':        {2025:11_945_750,2026:12_320_000,2027:12_550_500,2028:12_774_000,2029:12_990_750,2030:13_201_000},
    'UMI':        {2025: 4_635_500,2026: 4_721_500,2027: 4_829_750,2028: 4_917_250,2029: 5_002_250,2030: 5_084_750},
    'UTI':        {2025: 8_272_683,2026: 8_642_579,2027: 8_836_101,2028: 9_105_022,2029: 9_369_508,2030: 9_634_437},  # UIO v19: CV re-projected on IML Office No.3 regs (LD x739.2 + MD+F x887.04); 2025 anchor LD6059/MDF4277
    'ISD':        {2025: 3_412_365,2026: 4_232_397,2027: 3_888_500,2028: 5_214_003,2029: 5_971_315,2030: 6_781_546},
    'IBX':        {2025: 2_454_417,2026: 2_609_184,2027: 2_752_015,2028: 2_920_275,2029: 3_068_712,2030: 3_212_660},
    'Imotors':    {2025: 3_494_598,2026: 3_608_386,2027: 4_680_193,2028: 4_675_515,2029: 5_178_778,2030: 5_666_499},
    'Sverige':    {2025: 2_110_750,2026: 2_272_500,2027: 2_434_250,2028: 2_580_000,2029: 2_721_250,2030: 2_858_250},
    'Norway':     {2025: 1_982_250,2026: 2_027_750,2027: 2_054_500,2028: 2_106_500,2029: 2_157_000,2030: 2_206_000},
    'Ireland':    {2025: 1_391_410,2026: 1_226_640,2027: 2_173_734,2028: 1_743_017,2029: 1_990_353,2030: 2_230_357},
    'RSA':        {2025:   953_600,2026: 1_101_830,2027: 1_226_232,2028: 1_385_062,2029: 1_520_564,2030: 1_651_428},
    'AutoWallis': {2025:   933_500,2026:   998_000,2027: 1_060_500,2028: 1_097_500,2029: 1_133_250,2030: 1_168_000},
    'ROM Auto':   {2025:   267_750,2026:   302_250,2027:   335_750,2028:   368_750,2029:   400_750,2030:   431_750},
    'Nordic FI':  {2025:   301_000,2026:   327_000,2027:   352_250,2028:   380_500,2029:   407_750,2030:   434_250},
    'Danmark':    {2025:   213_239,2026:   236_739,2027:   259_000,2028:   285_739,2029:   310_989,2030:   335_489},
    'GasanZammit':{2025:   378_876,2026:   404_192,2027:   445_911,2028:   472_096,2029:   501_684,2030:   530_772},
    'Loutsios':   {2025:   676_308,2026:   772_734,2027:   876_160,2028:   966_368,2029: 1_054_566,2030: 1_139_137},
    'BL Iceland': {2025:   101_500,2026:   109_750,2027:   117_750,2028:   137_250,2029:   156_250,2030:   174_500},
}

KOSHA_DB = {
    'ITUK':       {2027:7_425_511,2028:7_123_723,2029:8_079_225,2030:9_162_888},
    'IUK':        {2027:7_004_984,2028:6_822_800,2029:7_737_939,2030:8_775_826},
    'UMI':        {2027:3_815_301,2028:4_474_311,2029:5_074_448,2030:5_755_082},
    'UTI':        {2027:3_830_292,2028:4_153_932,2029:4_711_097,2030:5_342_994},
    'ISD':        {2027:2_902_192,2028:3_060_628,2029:3_471_148,2030:3_936_732},
    'IBX':        {2027:2_413_780,2028:2_732_110,2029:3_098_567,2030:3_514_177},
    'Imotors':    {2027:1_928_355,2028:2_089_018,2029:2_369_217,2030:2_687_000},
    'Sverige':    {2027:1_451_769,2028:1_452_174,2029:1_646_953,2030:1_867_859},
    'Norway':     {2027:1_619_512,2028:1_515_414,2029:1_718_676,2030:1_949_201},
    'Ireland':    {2027:1_366_406,2028:1_556_401,2029:1_765_160,2030:2_001_920},
    'RSA':        {2027:  594_892,2028:  623_498,2029:  707_128,2030:  801_975},
    'AutoWallis': {2027:  371_567,2028:  333_509,2029:  378_242,2030:  428_976},
    'ROM Auto':   {2027:  199_588,2028:  208_478,2029:  236_441,2030:  268_155},
    'Nordic FI':  {2027:  321_896,2028:  313_229,2029:  355_242,2030:  402_890},
    'Danmark':    {2027:  169_124,2028:  186_302,2029:  211_291,2030:  239_631},
    'GasanZammit':{2027:  232_492,2028:  248_595,2029:  281_939,2030:  319_755},
    'Loutsios':   {2027:  483_569,2028:  530_071,2029:  601_169,2030:  681_804},
    'BL Iceland': {2027:   98_242,2028:  105_923,2029:  120_130,2030:  136_243},
}

# FY2027 bottom-up — reviewed budget 24 Apr 2026 (overrides legacy Kosha proxy rows above)
_BUILD = ISZE_ROOT / "01_data" / "91_build"
sys.path.insert(0, str(_BUILD))
from load_bp_fy27 import load_bp_fy27_reviewed  # noqa: E402

_KOSHA_BP_GPS = {
    "ITUK": "ITUK", "IUK": "IUK", "UMI": "UMI", "UTI": "UTI",
    "ISD": "GERMANY", "IBX": "BELGIUM", "Imotors": "PORTUGAL",
    "Sverige": "SWEDEN", "Norway": "NORWAY", "Ireland": "IRELAND",
    "RSA": "GREECE", "AutoWallis": "HUNGARY", "ROM Auto": "ROMANIA",
    "Nordic FI": "FINLAND", "Danmark": "DENMARK",
    "GasanZammit": "MALTA", "Loutsios": "CYPRUS", "BL Iceland": "ICELAND",
}
_bp27 = load_bp_fy27_reviewed()
for _kosha, _gps in _KOSHA_BP_GPS.items():
    if _kosha in KOSHA_DB and _gps in _bp27:
        KOSHA_DB[_kosha][2027] = round(_bp27[_gps])

SCOPE = {
    'ITUK':'CV','IUK':'LCV','UMI':'LCV','UTI':'CV',
    'ISD':'CV+LCV','IBX':'LCV','Imotors':'CV+LCV','Sverige':'LCV',
    'Norway':'LCV','Ireland':'CV+LCV','RSA':'CV+LCV','AutoWallis':'LCV',
    'ROM Auto':'LCV','Nordic FI':'LCV','Danmark':'CV+LCV',
    'GasanZammit':'CV+LCV','Loutsios':'CV+LCV','BL Iceland':'LCV',
}

DB_ORDER = [
    'ITUK','IUK','UTI','UMI','ISD','IBX','Imotors','Sverige','Norway',
    'Ireland','RSA','AutoWallis','ROM Auto','Nordic FI','Danmark',
    'GasanZammit','Loutsios','BL Iceland',
]

# ── REVISED VP TARGET (PL Plan row 186, 車両部品) ──────────────────────────────
# FY2029/FY2030 VP target revised DOWN in the uploaded plan (42.56→41.53M /
# 48.27→46.39M).  KOSHA_DB FY2028–FY2030 is a fixed-share top-down allocation,
# so rescale FY2029/FY2030 per-DB to the new totals — preserves every DB's share
# exactly.  FY2027 (bespoke bottom-up) and FY2028 (already on target) untouched.
_PLAN = ISZE_ROOT / "01_data" / "11_planning" / "ISZE PL Plan FY2026 2027 2028 20260205_2 -.xlsx"
def _revised_vp():
    ws = openpyxl.load_workbook(_PLAN, data_only=True)["IX study"]
    return {2029: float(ws.cell(186, 9).value), 2030: float(ws.cell(186, 10).value)}  # I186, J186
_VP_NEW = _revised_vp()
for _y in (2029, 2030):
    _cur = sum(KOSHA_DB[db][_y] for db in DB_ORDER)
    _f = _VP_NEW[_y] / _cur
    for db in DB_ORDER:
        KOSHA_DB[db][_y] = round(KOSHA_DB[db][_y] * _f)

# ── STYLES ────────────────────────────────────────────────────────────────────
DARK_BLUE  = PatternFill('solid', fgColor='1F3864')
MID_BLUE   = PatternFill('solid', fgColor='2F5496')
FY25_BLUE  = PatternFill('solid', fgColor='2F75B6')
GOLD       = PatternFill('solid', fgColor='FFC000')
GOLD_LIGHT = PatternFill('solid', fgColor='FFF2CC')
GREEN_FILL = PatternFill('solid', fgColor='E2EFDA')
GREEN_DARK = PatternFill('solid', fgColor='375623')
RED_FILL   = PatternFill('solid', fgColor='FFE0E0')
AMBER_FILL = PatternFill('solid', fgColor='FFE0CC')
PURPLE     = PatternFill('solid', fgColor='7030A0')
PURPLE_L   = PatternFill('solid', fgColor='D9D2E9')
GREY       = PatternFill('solid', fgColor='F2F2F2')
DB_FILL    = PatternFill('solid', fgColor='E9EFF8')
TOGGLE_ON  = PatternFill('solid', fgColor='E2EFDA')
TOGGLE_OFF = PatternFill('solid', fgColor='FCE4D6')

WH  = Font(name='Calibri', bold=True, color='FFFFFF', size=9)
BLD = Font(name='Calibri', bold=True, size=9)
NRM = Font(name='Calibri', size=9)
RED_F  = Font(name='Calibri', bold=True, color='C00000', size=9)
GRN_F  = Font(name='Calibri', bold=True, color='375623', size=9)
AMB_F  = Font(name='Calibri', color='C55A00', size=9)
PUR_F  = Font(name='Calibri', bold=True, color='4C1160', size=9)

_thin = Side(style='thin', color='BFBFBF')
BORDER = Border(left=_thin, right=_thin, top=_thin, bottom=_thin)

EUR0 = '#,##0'; PCT = '0.0%'; PCT0 = '0%'


def sc(ws, r, c, val, fill=None, font=None, align='center', fmt=None, border=None):
    if isinstance(c, str):
        c = col_idx(c)
    cell = ws.cell(row=r, column=c, value=val)
    if fill:  cell.fill = fill
    cell.font = font or NRM
    cell.alignment = Alignment(horizontal=align, vertical='center', wrap_text=True)
    if fmt:   cell.number_format = fmt
    if border: cell.border = border
    return cell


def gps_pct(net, ms):
    if ms and ms > 0: return net / ms
    return None


def gps_color(pct):
    if pct is None: return None
    if pct >= 0.55: return GREEN_FILL
    if pct >= 0.35: return AMBER_FILL
    return RED_FILL


def delta_color_font(d):
    if d is None: return None, NRM
    if d <= 0.05: return GREEN_FILL, GRN_F
    if d <= 0.15: return AMBER_FILL, AMB_F
    return RED_FILL, RED_F


def dev_note(db, g27_need, d27):
    parts = []
    if d27 is not None:
        label = 'reachable' if d27 <= 0.05 else 'moderate stretch' if d27 <= 0.15 else 'HIGH RISK'
        parts.append(f'Kosha FY27 gap: +{d27*100:.1f}pp — {label}')
    if g27_need and g27_need > 1.0:
        parts.append('⚠ Kosha >100% wallet — mathematically impossible')
    elif g27_need and g27_need > 0.90:
        parts.append('⚠ >90% wallet ceiling')
    if db == 'UMI':
        parts.append('★ UMI warranty filled (was gap=0 → now €1.79M CY2025)')
    if db == 'Ireland':
        parts.append('⚠ UIO v18 revised down (SIMI). FY27 max spend step-change vs recent actuals')
    if db == 'UTI':
        parts.append('★ UIO v19: CV re-projected on IML registrations — decline→growth (wallet FY30 €5.94M→€9.63M)')
        parts.append('⚠ Q4-2025 warranty spike: +€226K in 3 months vs €256K prior 9 months')
    return ' | '.join(parts) if parts else '—'


# ── COMPUTED VALUES (shared across sheets) ────────────────────────────────────
def compute_db(db):
    ms = MAX_SPEND.get(db, {})
    kd = KOSHA_DB.get(db, {})

    b24 = b(db, 2024); w24 = WARRANTY_FY24.get(db, 0); n24 = b24 - w24
    ms24 = ms.get(2025)
    g24  = gps_pct(n24, ms24)

    b25 = b(db, 2025); w25 = WARRANTY_FY25.get(db, 0); n25 = b25 - w25
    ms25 = ms.get(2025); g25 = gps_pct(n25, ms25)
    g25g = gps_pct(b25, ms25)  # gross

    b26 = b(db, 2026); w26 = WARRANTY_FY26.get(db, 0); n26 = b26 - w26
    ms26 = ms.get(2026)
    g26  = gps_pct(n26, ms26)
    g26g = gps_pct(b26, ms26)  # gross (for working sheet)

    # 2yr avg (net)
    if g25 is not None and g26 is not None: avg2 = (g25 + g26) / 2
    elif g25 is not None: avg2 = g25
    elif g26 is not None: avg2 = g26
    else: avg2 = None

    t27=kd.get(2027); ms27=ms.get(2027)
    t28=kd.get(2028); ms28=ms.get(2028)
    t29=kd.get(2029); ms29=ms.get(2029)
    t30=kd.get(2030); ms30=ms.get(2030)

    g27n=gps_pct(t27,ms27); g28n=gps_pct(t28,ms28)
    g29n=gps_pct(t29,ms29); g30n=gps_pct(t30,ms30)

    d27 = (g27n - avg2) if (g27n and avg2) else None
    d28 = (g28n - g27n) if (g28n and g27n) else None
    d29 = (g29n - g28n) if (g29n and g28n) else None
    d30 = (g30n - g29n) if (g30n and g29n) else None

    return dict(
        b24=b24, w24=w24, n24=n24, ms24=ms24, g24=g24,
        b25=b25, w25=w25, n25=n25, ms25=ms25, g25=g25, g25g=g25g,
        b26=b26, w26=w26, n26=n26, ms26=ms26, g26=g26, g26g=g26g,
        avg2=avg2,
        t27=t27, ms27=ms27, g27n=g27n, d27=d27,
        t28=t28, ms28=ms28, g28n=g28n, d28=d28,
        t29=t29, ms29=ms29, g29n=g29n, d29=d29,
        t30=t30, ms30=ms30, g30n=g30n, d30=d30,
    )

DATA = {db: compute_db(db) for db in DB_ORDER}


# ═══════════════════════════════════════════════════════════════════════════════
# OPTION B — Toggle sheet
# ═══════════════════════════════════════════════════════════════════════════════
def build_toggle_sheet(wb):
    ws = wb.create_sheet("GPS · Toggle")
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = 'D6'

    # ── Row 1: Toggle control ─────────────────────────────────────────────────
    # A1 = toggle value (1=ON, 0=OFF); custom number format shows ON/OFF label
    toggle_cell = ws.cell(row=1, column=1, value=1)
    toggle_cell.number_format = r'[=1]"◉  WARRANTY ON";[=0]"◯  WARRANTY OFF"'
    toggle_cell.font = Font(name='Calibri', bold=True, size=11, color='375623')
    toggle_cell.fill = TOGGLE_ON
    toggle_cell.alignment = Alignment(horizontal='center', vertical='center')
    toggle_cell.border = Border(
        left=Side(style='medium', color='375623'),
        right=Side(style='medium', color='375623'),
        top=Side(style='medium', color='375623'),
        bottom=Side(style='medium', color='375623'),
    )
    ws.column_dimensions['A'].width = 20
    ws.row_dimensions[1].height = 20

    # B1:AK1 merged = banner text (static — user sees current mode in A1 cell)
    ws.merge_cells('B1:AK1')
    banner = ws.cell(row=1, column=2,
        value=('Change A1 to 0 → GPS% switches to GROSS (warranty not deducted)  |  '
               'A1 = 1 → GPS% NET of warranty  |  '
               'FY2026: fiscal FY warranty (Distributor Warranty Expense, Apr25–Mar26 incl. CV)  |  '
               'Billing: raw SAP, TRANSPORT + RUSH/VOR surcharge stripped'))
    banner.font = Font(name='Calibri', italic=True, size=8, color='375623')
    banner.fill = TOGGLE_ON
    banner.alignment = Alignment(horizontal='left', vertical='center')

    # Data validation: only 0 or 1 allowed in A1
    dv = DataValidation(type='whole', operator='between', formula1='0', formula2='1',
                        showErrorMessage=True,
                        errorTitle='Invalid', error='Enter 0 (OFF) or 1 (ON)')
    dv.add(ws['A1'])
    ws.add_data_validation(dv)

    # ── Row 2: Title ──────────────────────────────────────────────────────────
    ws.merge_cells('A2:AK2')
    sc(ws,2,'A','GPS / Kosha  |  ISZE IE40 Billing (net of warranty)  |  FY2024–FY2030',
       fill=DARK_BLUE, font=Font(name='Calibri',bold=True,color='FFFFFF',size=11), align='left')
    ws.row_dimensions[2].height = 16

    # ── Row 3: Sources ────────────────────────────────────────────────────────
    ws.merge_cells('A3:AK3')
    sc(ws,3,'A',
       'Warranty: FY2024 full year (new) · FY2025 complete Jan–Dec incl. Q4 (new) + UMI filled · '
       'FY2026 fiscal warranty (Distributor Warranty Expense)  |  Billing: gps_billing_clean.json  |  '
       'Toggle A1: 1=net GPS%, 0=gross GPS%  |  FY2024 partial (Jul23–Mar24, 9 months)  |  '
       'UIO: v19 (UTI CV re-projected on IML regs; other DBs = v18)',
       fill=MID_BLUE, font=Font(name='Calibri',italic=True,color='FFFFFF',size=8), align='left')
    ws.row_dimensions[3].height = 14

    # ── Row 4: Section headers ────────────────────────────────────────────────
    sections = [
        ('A','C','',DARK_BLUE),
        ('D','H','◀  FY2024 (partial 9 months) ▶', PatternFill('solid',fgColor='4472C4')),
        ('I','M','◀  FY2025 (full year) ▶', FY25_BLUE),
        ('N','R','◀  FY2026 ▶', GOLD),
        ('S','S','2yr avg', PURPLE),
        ('T','W','◀  FY2027 Kosha ▶', GREEN_DARK),
        ('X','AA','◀  FY2028 ▶', GREEN_DARK),
        ('AB','AE','◀  FY2029 ▶', GREEN_DARK),
        ('AF','AI','◀  FY2030 ▶', GREEN_DARK),
        ('AJ','AK','Notes', PatternFill('solid',fgColor='595959')),
    ]
    for c1,c2,lbl,fill in sections:
        i1,i2 = col_idx(c1), col_idx(c2)
        if i1 < i2: ws.merge_cells(start_row=4,start_column=i1,end_row=4,end_column=i2)
        sc(ws,4,i1,lbl,fill=fill,font=Font(name='Calibri',bold=True,color='FFFFFF',size=8))
    ws.row_dimensions[4].height = 14

    # ── Row 5: Column headers ─────────────────────────────────────────────────
    HDR = PatternFill('solid', fgColor='1F3864')
    cols = [
        ('A','Distributor',14),('B','Basis\n(UIO)',14),('C','Scope',8),
        ('D','Billing €\n(9mo)',9),('E','Warr €\n(new)',8),('F','Net GPS €',9),('G','Max Spend €',9),('H','GPS%\n[toggle]',7),
        ('I','Billing €',9),('J','Warr €\n(complete)',9),('K','Net GPS €',9),('L','Max Spend €',9),('M','GPS%\n[toggle]',7),
        ('N','Billing €',9),('O','Warr €\n(*partial)',8),('P','Net GPS €',9),('Q','Max Spend €',9),('R','GPS%\n[toggle]',7),
        ('S','2yr avg\nGPS%',7),
        ('T','Kosha €',9),('U','Max Spend €',9),('V','GPS%\nneeded',7),('W','Δ pp\nvs 2yr',7),
        ('X','Kosha €',9),('Y','Max Spend €',9),('Z','GPS%',7),('AA','Δ pp',7),
        ('AB','Kosha €',9),('AC','Max Spend €',9),('AD','GPS%',7),('AE','Δ pp',7),
        ('AF','Kosha €',9),('AG','Max Spend €',9),('AH','GPS%',7),('AI','Δ pp',7),
        ('AJ','Deviation / Risk',42),('AK','Notes',14),
    ]
    for c_ltr,lbl,wid in cols:
        ci = col_idx(c_ltr)
        sc(ws,5,ci,lbl,fill=HDR,font=Font(name='Calibri',bold=True,color='FFFFFF',size=8))
        ws.column_dimensions[c_ltr].width = wid
    ws.row_dimensions[5].height = 36

    # ── Data rows (Row 6+) ────────────────────────────────────────────────────
    BASIS = {
        'ITUK':'DVLA car park','IUK':'UIO v18 (LCV)','UMI':'UIO v18 (LCV)',
        'UTI':'UIO v19 (CV)','ISD':'UIO v18 (CV+LCV)','IBX':'UIO v18 (LCV)',
        'Imotors':'UIO v18 (CV+LCV)','Sverige':'UIO v18 (LCV)','Norway':'UIO v18 (LCV)',
        'Ireland':'SIMI cohort','RSA':'UIO v18 (CV+LCV)','AutoWallis':'UIO v18 (LCV)',
        'ROM Auto':'UIO v18 (LCV)','Nordic FI':'UIO v18 (LCV)','Danmark':'UIO v18 (CV+LCV)',
        'GasanZammit':'UIO v18 (CV+LCV)','Loutsios':'UIO v18 (CV+LCV)','BL Iceland':'UIO v18 (LCV)',
    }

    row = 6
    for db in DB_ORDER:
        d = DATA[db]
        rf = GREY if row % 2 == 0 else None

        def rc(cl, val, fmt=None, fill=None, font=None, align='center'):
            sc(ws, row, col_idx(cl), val, fill=fill or rf, font=font, align=align,
               fmt=fmt, border=BORDER)

        # Toggle-aware GPS% formula refs: $A$1 is the toggle
        def gps_f(bill_col, warr_col, ms_col):
            r = row
            return (f'=IF($A$1=1,'
                    f'IFERROR(MAX(0,({bill_col}{r}-{warr_col}{r})/{ms_col}{r}),0),'
                    f'IFERROR({bill_col}{r}/{ms_col}{r},0))')

        def net_f(bill_col, warr_col):
            r = row
            return f'=IF($A$1=1,MAX(0,{bill_col}{r}-{warr_col}{r}),{bill_col}{r})'

        rc('A', db,              fill=DB_FILL, font=BLD, align='left')
        rc('B', BASIS.get(db,'UIO v18'), align='left')
        rc('C', SCOPE.get(db,'—'))

        rc('D', d['b24'], EUR0);  rc('E', d['w24'], EUR0)
        rc('F', net_f('D','E'),   EUR0)
        rc('G', d['ms24'],EUR0)
        rc('H', gps_f('D','E','G'), PCT)

        rc('I', d['b25'], EUR0);  rc('J', d['w25'], EUR0)
        rc('K', net_f('I','J'),   EUR0)
        rc('L', d['ms25'],EUR0)
        rc('M', gps_f('I','J','L'), PCT, fill=None)  # color handled below

        rc('N', d['b26'], EUR0);  rc('O', d['w26'], EUR0)
        rc('P', net_f('N','O'),   EUR0, fill=GOLD_LIGHT)
        rc('Q', d['ms26'],EUR0,   fill=GOLD_LIGHT)
        rc('R', gps_f('N','O','Q'), PCT, fill=GOLD_LIGHT)

        rc('S', gps_f('I','J','L') if False else d['avg2'], PCT,
           fill=PURPLE_L, font=PUR_F)

        g27_fill, g27_font = delta_color_font(d['d27'])
        for ltr,val,fmt in [('T',d['t27'],EUR0),('U',d['ms27'],EUR0),
                              ('V',d['g27n'],PCT),('W',d['d27'],'+0.0%;-0.0%;—')]:
            rc(ltr, val, fmt, fill=GREEN_FILL)

        for ltr,val,fmt in [('X',d['t28'],EUR0),('Y',d['ms28'],EUR0),
                              ('Z',d['g28n'],PCT),('AA',d['d28'],'+0.0%;-0.0%;—'),
                              ('AB',d['t29'],EUR0),('AC',d['ms29'],EUR0),
                              ('AD',d['g29n'],PCT),('AE',d['d29'],'+0.0%;-0.0%;—'),
                              ('AF',d['t30'],EUR0),('AG',d['ms30'],EUR0),
                              ('AH',d['g30n'],PCT),('AI',d['d30'],'+0.0%;-0.0%;—')]:
            rc(ltr, val, fmt, fill=GREEN_FILL)

        d27f, d27font = delta_color_font(d['d27'])
        sc(ws, row, col_idx('W'), d['d27'], fill=d27f or GREEN_FILL, font=d27font,
           fmt='+0.0%;-0.0%;—', border=BORDER)

        note = dev_note(db, d['g27n'], d['d27'])
        c_note = ws.cell(row=row, column=col_idx('AJ'), value=note)
        c_note.font = RED_F if 'HIGH RISK' in note or '>100%' in note else NRM
        c_note.fill = rf or PatternFill()
        c_note.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
        c_note.border = BORDER

        w26_note = '' if d['w26'] > 0 else '⚠ no warranty in expense file'
        sc(ws, row, col_idx('AK'), w26_note, fill=GOLD_LIGHT if w26_note else rf, font=NRM,
           align='left', border=BORDER)

        ws.row_dimensions[row].height = 20
        row += 1

    # ── Totals row ────────────────────────────────────────────────────────────
    ws.merge_cells(f'A{row}:C{row}')
    ws.row_dimensions[row].height = 20
    tot_b25 = sum(DATA[db]['b25'] for db in DB_ORDER)
    tot_w25 = sum(DATA[db]['w25'] for db in DB_ORDER)
    tot_n25 = tot_b25 - tot_w25
    tot_ms25 = sum(DATA[db]['ms25'] for db in DB_ORDER if DATA[db]['ms25'])
    tot_b26 = sum(DATA[db]['b26'] for db in DB_ORDER)
    tot_w26 = sum(DATA[db]['w26'] for db in DB_ORDER)
    tot_n26 = tot_b26 - tot_w26
    tot_ms26 = sum(DATA[db]['ms26'] for db in DB_ORDER if DATA[db]['ms26'])
    tot_t27 = sum(DATA[db]['t27'] or 0 for db in DB_ORDER)
    tot_ms27 = sum(DATA[db]['ms27'] or 0 for db in DB_ORDER)

    def rt(cl, val, fmt=None):
        sc(ws, row, col_idx(cl), val, fill=DARK_BLUE, font=WH, fmt=fmt, border=BORDER)

    rt('A', 'TOTAL (GPS base)')
    rt('I', tot_b25, EUR0); rt('J', tot_w25, EUR0); rt('K', tot_n25, EUR0)
    rt('L', tot_ms25, EUR0)
    rt('M', gps_pct(tot_n25, tot_ms25), PCT)
    rt('N', tot_b26, EUR0); rt('O', tot_w26, EUR0); rt('P', tot_n26, EUR0)
    rt('Q', tot_ms26, EUR0); rt('R', gps_pct(tot_n26, tot_ms26), PCT)
    rt('T', tot_t27, EUR0); rt('U', tot_ms27, EUR0)
    rt('V', gps_pct(tot_t27, tot_ms27), PCT)

    row += 1
    ws.merge_cells(f'A{row}:AK{row}')
    sc(ws, row, 'A',
       '* FY2026 warranty: Jan–May LCV available for most DBs; ITUK/UTI CV warranty not yet in partial export → FY2026 GPS% slightly overstated for those two',
       fill=GOLD_LIGHT, font=Font(name='Calibri', italic=True, size=8, color='7F6000'), align='left')


# ═══════════════════════════════════════════════════════════════════════════════
# OPTION C — Executive sheet (clean net view)
# ═══════════════════════════════════════════════════════════════════════════════
def build_executive_sheet(wb):
    ws = wb.create_sheet("GPS · Executive")
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = 'C5'

    ws.merge_cells('A1:L1')
    sc(ws,1,'A','GPS / Kosha — ISZE IE40  |  Net of warranty  |  FY2024–FY2030',
       fill=DARK_BLUE, font=Font(name='Calibri',bold=True,color='FFFFFF',size=11), align='left')
    ws.row_dimensions[1].height = 16

    ws.merge_cells('A2:L2')
    sc(ws,2,'A',
       'All GPS% exclude warranty parts (see "GPS · Working" for mechanics).  '
       'FY2024 = 9 months Jul23–Mar24.  FY2026 = partial warranty adj (Jan–May LCV).  '
       'UMI FY2025 warranty filled (€1.79M, previously a data gap).',
       fill=MID_BLUE, font=Font(name='Calibri',italic=True,color='FFFFFF',size=8), align='left')
    ws.row_dimensions[2].height = 14

    ESECTIONS = [
        ('A','B','',DARK_BLUE),
        ('C','E','◀  Actuals ▶',PatternFill('solid',fgColor='4472C4')),
        ('F','F','2yr avg',PURPLE),
        ('G','H','◀  FY2027 Kosha ▶',GREEN_DARK),
        ('I','J','◀  FY2028–29 ▶',GREEN_DARK),
        ('K','K','FY2030',GREEN_DARK),
        ('L','L','Risk',PatternFill('solid',fgColor='595959')),
    ]
    for c1,c2,lbl,fill in ESECTIONS:
        i1,i2=col_idx(c1),col_idx(c2)
        if i1<i2: ws.merge_cells(start_row=3,start_column=i1,end_row=3,end_column=i2)
        sc(ws,3,i1,lbl,fill=fill,font=Font(name='Calibri',bold=True,color='FFFFFF',size=8))
    ws.row_dimensions[3].height = 14

    ECOLS = [
        ('A','Distributor',14),('B','Scope',9),
        ('C','FY24\nNet GPS%',8),('D','FY25\nNet GPS%',8),('E','FY26\nGPS%*',8),
        ('F','2yr avg\nnet',7),
        ('G','FY27\nKosha €',10),('H','FY27\nGPS% needed',8),
        ('I','FY28\nGPS%',7),('J','FY29\nGPS%',7),('K','FY30\nGPS%',7),
        ('L','Deviation / Risk',38),
    ]
    HDR=PatternFill('solid',fgColor='1F3864')
    for c_ltr,lbl,wid in ECOLS:
        sc(ws,4,col_idx(c_ltr),lbl,fill=HDR,font=Font(name='Calibri',bold=True,color='FFFFFF',size=8))
        ws.column_dimensions[c_ltr].width=wid
    ws.row_dimensions[4].height=32

    row=5
    for db in DB_ORDER:
        d=DATA[db]
        rf=GREY if row%2==0 else None

        def re(cl,val,fmt=None,fill=None,font=None,al='center'):
            sc(ws,row,col_idx(cl),val,fill=fill or rf,font=font,fmt=fmt,align=al,border=BORDER)

        re('A',db,fill=DB_FILL,font=BLD,al='left')
        re('B',SCOPE.get(db,'—'))
        re('C',d['g24'],PCT,fill=gps_color(d['g24']))
        re('D',d['g25'],PCT,fill=gps_color(d['g25']))
        re('E',d['g26'],PCT,fill=GOLD_LIGHT)
        re('F',d['avg2'],PCT,fill=PURPLE_L,font=PUR_F)

        re('G',d['t27'],EUR0,fill=GREEN_FILL)
        re('H',d['g27n'],PCT,fill=GREEN_FILL)
        re('I',d['g28n'],PCT,fill=GREEN_FILL)
        re('J',d['g29n'],PCT,fill=GREEN_FILL)
        re('K',d['g30n'],PCT,fill=GREEN_FILL)

        note=dev_note(db,d['g27n'],d['d27'])
        cn=ws.cell(row=row,column=col_idx('L'),value=note)
        cn.font=RED_F if 'HIGH RISK' in note or '>100%' in note else NRM
        cn.fill=rf or PatternFill()
        cn.alignment=Alignment(horizontal='left',vertical='center',wrap_text=True)
        cn.border=BORDER

        ws.row_dimensions[row].height=20
        row+=1

    ws.merge_cells(f'A{row}:L{row}')
    sc(ws,row,'A',
       '* FY2026 GPS% uses partial warranty (Jan–May LCV). Slightly overstated for ITUK/UTI (no CV in partial file). '
       'Green ≥55% · Amber 35–55% · Red <35%',
       fill=GOLD_LIGHT,font=Font(name='Calibri',italic=True,size=8,color='7F6000'),align='left')


# ═══════════════════════════════════════════════════════════════════════════════
# OPTION C — Working sheet (full mechanics, gross vs net)
# ═══════════════════════════════════════════════════════════════════════════════
def build_working_sheet(wb):
    ws = wb.create_sheet("GPS · Working")
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = 'D5'

    ws.merge_cells('A1:AN1')
    sc(ws,1,'A','GPS / Kosha — Working Sheet  |  Full warranty mechanics & gross/net breakdown  |  FY2024–FY2030',
       fill=DARK_BLUE, font=Font(name='Calibri',bold=True,color='FFFFFF',size=11), align='left')
    ws.row_dimensions[1].height=16

    ws.merge_cells('A2:AN2')
    sc(ws,2,'A',
       'FY2025 warranty: Jan–Sep (original methodology) + Q4 Oct–Dec (new file) + UMI full year (new, was gap=0).  '
       'FY2026: partial Jan–May LCV only.  FY2024: full year from new CV+LCV+UMI files.',
       fill=MID_BLUE,font=Font(name='Calibri',italic=True,color='FFFFFF',size=8),align='left')
    ws.row_dimensions[2].height=14

    WSEC=[
        ('A','C','',DARK_BLUE),
        ('D','J','◀  FY2024 (9 months, new warranty data) ▶',PatternFill('solid',fgColor='4472C4')),
        ('K','Q','◀  FY2025 (full year, complete warranty) ▶',FY25_BLUE),
        ('R','X','◀  FY2026 (partial warranty Jan–May LCV*) ▶',GOLD),
        ('Y','Z','2yr avg',PURPLE),
        ('AA','AH','◀  Kosha Outlook FY2027–2030 ▶',GREEN_DARK),
        ('AI','AN','Notes',PatternFill('solid',fgColor='595959')),
    ]
    for c1,c2,lbl,fill in WSEC:
        i1,i2=col_idx(c1),col_idx(c2)
        if i1<i2: ws.merge_cells(start_row=3,start_column=i1,end_row=3,end_column=i2)
        sc(ws,3,i1,lbl,fill=fill,font=Font(name='Calibri',bold=True,color='FFFFFF',size=8))
    ws.row_dimensions[3].height=14

    WCOLS=[
        ('A','Distributor',14),('B','Basis',13),('C','Scope',8),
        # FY24
        ('D','Billing €',9),('E','Warr €\n(new)',8),('F','Net GPS €',9),
        ('G','Max Spend €',9),('H','Net GPS%',7),('I','Gross GPS%',7),('J','Δ pp\nwarr impact',7),
        # FY25
        ('K','Billing €',9),('L','Warr €\n(complete)',9),('M','Net GPS €',9),
        ('N','Max Spend €',9),('O','Net GPS%',7),('P','Gross GPS%',7),('Q','Δ pp\nwarr impact',7),
        # FY26
        ('R','Billing €',9),('S','Warr €\n(*partial)',8),('T','Net GPS €',9),
        ('U','Max Spend €',9),('V','Net GPS%',7),('W','Gross GPS%',7),('X','Δ pp\n(*partial)',7),
        # 2yr
        ('Y','2yr avg\nnet GPS%',7),('Z','2yr avg\ngross GPS%',7),
        # Outlook
        ('AA','FY27\nKosha €',9),('AB','FY27\nMax Spend',9),('AC','FY27\nGPS% need',7),('AD','FY27\nΔ pp vs avg',7),
        ('AE','FY28\nGPS%',7),('AF','FY29\nGPS%',7),('AG','FY30\nGPS%',7),
        ('AH','FY28-30\nΔ trend',7),
        # Notes
        ('AI','Deviation / Risk',38),('AJ','Method',14),('AK','Warr FY24',9),
        ('AL','Warr FY25',9),('AM','Warr FY26',9),('AN','UMI note',14),
    ]
    HDR=PatternFill('solid',fgColor='1F3864')
    for c_ltr,lbl,wid in WCOLS:
        sc(ws,4,col_idx(c_ltr),lbl,fill=HDR,font=Font(name='Calibri',bold=True,color='FFFFFF',size=8))
        ws.column_dimensions[c_ltr].width=wid
    ws.row_dimensions[4].height=36

    BASIS={
        'ITUK':'DVLA car park','IUK':'UIO v18 (LCV)','UMI':'UIO v18 (LCV)',
        'UTI':'UIO v19 (CV)','ISD':'UIO v18 (CV+LCV)','IBX':'UIO v18 (LCV)',
        'Imotors':'UIO v18 (CV+LCV)','Sverige':'UIO v18 (LCV)','Norway':'UIO v18 (LCV)',
        'Ireland':'SIMI cohort','RSA':'UIO v18 (CV+LCV)','AutoWallis':'UIO v18 (LCV)',
        'ROM Auto':'UIO v18 (LCV)','Nordic FI':'UIO v18 (LCV)','Danmark':'UIO v18 (CV+LCV)',
        'GasanZammit':'UIO v18 (CV+LCV)','Loutsios':'UIO v18 (CV+LCV)','BL Iceland':'UIO v18 (LCV)',
    }

    row=5
    for db in DB_ORDER:
        d=DATA[db]
        rf=GREY if row%2==0 else None

        def rw(cl,val,fmt=None,fill=None,font=None,al='center'):
            sc(ws,row,col_idx(cl),val,fill=fill or rf,font=font,fmt=fmt,align=al,border=BORDER)

        g24g=gps_pct(d['b24'],d['ms24'])
        g25g=d['g25g']
        g26g=d['g26g']
        d24_delta=(d['g24']-g24g) if (d['g24'] and g24g) else None
        d25_delta=(d['g25']-g25g) if (d['g25'] and g25g) else None
        d26_delta=(d['g26']-g26g) if (d['g26'] and g26g) else None

        avg2g=None
        if g25g and g26g: avg2g=(g25g+g26g)/2
        elif g25g: avg2g=g25g
        elif g26g: avg2g=g26g

        rw('A',db,fill=DB_FILL,font=BLD,al='left')
        rw('B',BASIS.get(db,'UIO v18'),al='left')
        rw('C',SCOPE.get(db,'—'))

        rw('D',d['b24'],EUR0); rw('E',d['w24'],EUR0); rw('F',d['n24'],EUR0)
        rw('G',d['ms24'],EUR0)
        rw('H',d['g24'],PCT,fill=gps_color(d['g24']))
        rw('I',g24g,PCT,fill=GREY)
        rw('J',d24_delta,'0.0pp%' if False else '+0.0%;-0.0%;—',
           fill=RED_FILL if (d24_delta and d24_delta<-0.05) else rf)

        rw('K',d['b25'],EUR0); rw('L',d['w25'],EUR0); rw('M',d['n25'],EUR0)
        rw('N',d['ms25'],EUR0)
        rw('O',d['g25'],PCT,fill=gps_color(d['g25']))
        rw('P',g25g,PCT,fill=GREY)
        rw('Q',d25_delta,'+0.0%;-0.0%;—',
           fill=RED_FILL if (d25_delta and d25_delta<-0.05) else rf)

        rw('R',d['b26'],EUR0); rw('S',d['w26'],EUR0); rw('T',d['n26'],EUR0)
        rw('U',d['ms26'],EUR0)
        rw('V',d['g26'],PCT,fill=GOLD_LIGHT)
        rw('W',g26g,PCT,fill=GREY)
        rw('X',d26_delta,'+0.0%;-0.0%;—',fill=GOLD_LIGHT)

        rw('Y',d['avg2'],PCT,fill=PURPLE_L,font=PUR_F)
        rw('Z',avg2g,PCT,fill=GREY)

        df,dft=delta_color_font(d['d27'])
        rw('AA',d['t27'],EUR0,fill=GREEN_FILL); rw('AB',d['ms27'],EUR0,fill=GREEN_FILL)
        rw('AC',d['g27n'],PCT,fill=GREEN_FILL)
        rw('AD',d['d27'],'+0.0%;-0.0%;—',fill=df or GREEN_FILL,font=dft)
        rw('AE',d['g28n'],PCT,fill=GREEN_FILL)
        rw('AF',d['g29n'],PCT,fill=GREEN_FILL)
        rw('AG',d['g30n'],PCT,fill=GREEN_FILL)
        d3039=(d['g30n']-d['g27n']) if (d['g30n'] and d['g27n']) else None
        rw('AH',d3039,'+0.0%;-0.0%;—',fill=GREEN_FILL)

        note=dev_note(db,d['g27n'],d['d27'])
        cn=ws.cell(row=row,column=col_idx('AI'),value=note)
        cn.font=RED_F if 'HIGH RISK' in note or '>100%' in note else NRM
        cn.fill=rf or PatternFill()
        cn.alignment=Alignment(horizontal='left',vertical='center',wrap_text=True)
        cn.border=BORDER

        rw('AJ',BASIS.get(db,'UIO v18'),al='left')
        rw('AK',d['w24'],EUR0)
        rw('AL',d['w25'],EUR0,fill=PatternFill('solid',fgColor='DDEEFF') if db=='UMI' else rf,
           font=Font(name='Calibri',bold=True,size=9,color='0000CC') if db=='UMI' else NRM)
        rw('AM',d['w26'],EUR0,fill=GOLD_LIGHT)
        umi_note='★ Filled (was gap=0)' if db=='UMI' else ''
        rw('AN',umi_note,fill=PatternFill('solid',fgColor='DDEEFF') if db=='UMI' else rf,
           font=Font(name='Calibri',bold=True,size=9,color='0000CC') if db=='UMI' else NRM,al='left')

        ws.row_dimensions[row].height=20
        row+=1

    ws.merge_cells(f'A{row}:AN{row}')
    sc(ws,row,'A',
       '* FY2026 warranty partial: Jan–May LCV from ExportClaimAssessment file + UMI full Jan–May. '
       'ITUK/UTI CV component not in this partial file → their FY2026 GPS% slightly overstated. '
       'Net GPS% = Gross − Warranty. Green col = gross (for reference only).',
       fill=GOLD_LIGHT,font=Font(name='Calibri',italic=True,size=8,color='7F6000'),align='left')


# ═══════════════════════════════════════════════════════════════════════════════
# LEGEND
# ═══════════════════════════════════════════════════════════════════════════════
def build_legend_sheet(wb):
    ws = wb.create_sheet("Legend")
    ws.sheet_view.showGridLines = False
    ws.merge_cells('A1:E1')
    sc(ws,1,'A','Legend & Key Caveats',fill=DARK_BLUE,font=Font(name='Calibri',bold=True,color='FFFFFF',size=10),align='left')
    ws.column_dimensions['A'].width=20; ws.column_dimensions['B'].width=60
    ws.column_dimensions['C'].width=14; ws.column_dimensions['D'].width=14; ws.column_dimensions['E'].width=14

    rows=[
        ('GPS · Toggle (B1)',     'Cell A1 = 1 → warranty deducted (net GPS%). A1 = 0 → gross billing. All GPS% columns update automatically.'),
        ('GPS · Executive (C1)',  'Clean net view. All GPS% net of warranty. No gross columns. For presentation / IML briefing.'),
        ('GPS · Working (C2)',    'Full mechanics: billing, warranty, net, gross side-by-side for each year. Analyst view.'),
        ('',None),
        ('Green GPS%',            'Net GPS% ≥55% vs max spend — strong performance'),
        ('Amber GPS%',            'Net GPS% 35–55% — acceptable, watch trend'),
        ('Red GPS%',              'Net GPS% <35% — underperformance vs wallet'),
        ('Gold columns (FY2026)', 'Partial warranty Jan–May LCV. GPS% slightly overstated for ITUK/UTI (no CV in partial).'),
        ('Purple 2yr avg',        'FY2025 net + FY2026 net avg. Used as baseline for Kosha FY2027 gap calc.'),
        ('Green Δpp',             'Kosha FY2027 uplift ≤5pp vs 2yr avg — realistic'),
        ('Amber Δpp',             'Uplift 5–15pp — stretch'),
        ('Red Δpp',               'Uplift >15pp — HIGH RISK / structural gap'),
        ('',None),
        ('UMI warranty FY2025',   '★ Now €1,791,020 (full year from new UMI warranty file). Previously gap=0 → UMI GPS overstated. Correction lowers UMI net GPS%.'),
        ('FY2025 completeness',   'FY2025 = Jan–Sep (existing ISZE-price methodology) + Q4 Oct–Dec (new raw file) + UMI full year.'),
        ('FY2024 warranty',       'Now available for all DBs from new CV+LCV+UMI files. Notable: UMI €1.37M, UTI €846K, ITUK €788K.'),
        ('FY2024 billing',        'Jul 2023 – Mar 2024 only (9 months). Apr–Jun 2023 absent from source. Max spend = FY2025 proxy.'),
        ('Ireland UIO',           '⚠ V18 revised sharply downward (SIMI). Creates FY27 max spend jump vs FY26 → artificial Δpp spike.'),
        ('UTI UIO v19',           '★ CV parc re-projected on IML Office No.3 registrations (email 17-Jun-2026): 2026–30 reverses decline→growth. 2025 re-anchored LD6,059/MD+F4,277=€8.27M. Wallet FY27–30 up €0.4M→€3.7M vs v18 → GPS% needed for Kosha drops sharply.'),
        ('Kosha VP source',       'FY2027 €35.28M reviewed VP turnover (budget_per_DB_reviewed_24042026 · 24 Apr 2026). FY2028+ top-down from PL Plan row 186.'),
        ('ITUK method',           'Unique: DVLA car park actuals (22,389 CV CY2025). Own plan €7.4M FY27. Not Kosha-allocated.'),
    ]
    r=2
    for label, desc in rows:
        ws.row_dimensions[r].height=18
        if desc is None:
            r+=1; continue
        sc(ws,r,1,label,fill=GREY,font=BLD,align='left')
        ws.merge_cells(f'B{r}:E{r}')
        sc(ws,r,2,desc,fill=GREY,font=NRM,align='left')
        r+=1


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    build_toggle_sheet(wb)     # Option B
    build_executive_sheet(wb)  # Option C – executive
    build_working_sheet(wb)    # Option C – working
    build_legend_sheet(wb)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(OUT))
    print(f"Saved -> {OUT}")
    print(f"Sheets: {[ws.title for ws in wb.worksheets]}")
    print(f"UMI FY25 warranty: €{WARRANTY_FY25['UMI']:,.0f}  (was 0)")
    print(f"Network FY25 total warranty: €{sum(WARRANTY_FY25.values()):,.0f}")
    print(f"Network FY24 total warranty: €{sum(WARRANTY_FY24.values()):,.0f}")

if __name__ == "__main__":
    main()
