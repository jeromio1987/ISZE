"""
GPS Billing Aggregator - FY2024 to FY2026
Exclusions: BillT in {S1,G2,RE,ZFD,S2} | SaTy in {CR,RE}
Data sources:
  CY2023-2024.XLSX  → use dates Jul 2023 - Dec 2023 only (FY2024 partial)
  CY2024-2025.XLSX  → Jan 2024 - Dec 2025 (authoritative, no overlap)
  sales_2026tillApril.XLSX → Jan - Apr 2026
  Sales_israel_1799&_1797.XLSX → UTI (soldto=1799) / UMI (payer=1797)
Output: 01_data/derived/gps_billing_clean.json
"""

import openpyxl, json, sys
from collections import defaultdict
from datetime import datetime

EXCL_BILLT = {'S1', 'G2', 'RE', 'ZFD', 'S2'}
EXCL_SATY  = {'CR', 'RE'}

PAYER_DB = {
    '2194': 'ITUK',   '89': 'IUK',      '90': 'IBX',
    '92':   'Imotors','93': 'ISD',      '66': 'RSA',
    '2181': 'Sverige','76': 'Ireland',  '393': 'Loutsios',
    '86':   'Norway', '396': 'ROM Auto','537': 'AutoWallis',
    '1759': 'GasanZammit','2679': 'Nordic FI','2027': 'Danmark',
    '1576': 'BL Iceland','88': 'MIDI',  '105': 'IMG',
    '2294': 'CIS-KTK','2731': 'GA',    '2732': 'CBC',
    '2372': 'KIMA',   '77':  'TR',     '2929': 'Sverige2'
}

def fy(dt):
    return dt.year + 1 if dt.month >= 4 else dt.year

results = defaultdict(lambda: defaultdict(float))

FILE_CONFIGS = [
    # (path, date_filter_fn, skip_israel_payers)
    ('/sessions/beautiful-kind-bell/mnt/ISZE/01_data/raw/sales/CY2023-2024.XLSX',
     lambda d: d < datetime(2024, 1, 1), True),   # only Jul-Dec 2023
    ('/sessions/beautiful-kind-bell/mnt/ISZE/01_data/CY2024-2025.XLSX',
     lambda d: True, True),                        # full file
    ('/sessions/beautiful-kind-bell/mnt/ISZE/01_data/sales_2026tillApril.XLSX',
     lambda d: True, True),                        # Jan-Apr 2026
]

for fpath, date_filter, skip_israel in FILE_CONFIGS:
    fname = fpath.split('/')[-1]
    print(f'Reading {fname}...', flush=True)
    wb = openpyxl.load_workbook(fpath, read_only=True, data_only=True)
    ws = wb.active
    header = None
    kept = excl = skip = 0
    for row in ws.iter_rows(values_only=True):
        if header is None:
            header = list(row)
            billt_i  = header.index('BillT')
            saty_i   = header.index('SaTy')
            netval_i = header.index('Net value')
            continue
        if not header[0]:  # pivot guard
            break
        dt = row[0]
        if not isinstance(dt, datetime):
            continue
        if not date_filter(dt):
            skip += 1; continue
        bt = row[billt_i]; st = row[saty_i]
        if bt in EXCL_BILLT or st in EXCL_SATY:
            excl += 1; continue
        payer = str(row[4])
        if skip_israel and payer in ('1797', '1799'):
            skip += 1; continue
        db = PAYER_DB.get(payer, f'UNK_{payer}')
        results[db][fy(dt)] += row[netval_i] or 0
        kept += 1
    wb.close()
    print(f'  kept={kept:,}  excl={excl:,}  skip={skip:,}', flush=True)

# Israel dedicated file
print('Reading Israel file...', flush=True)
wb = openpyxl.load_workbook(
    "/sessions/beautiful-kind-bell/mnt/ISZE/01_data/Sales_israel_1799&_1797.XLSX",
    read_only=True, data_only=True)
ws = wb.active
header = None; kept = excl = 0
for row in ws.iter_rows(values_only=True):
    if header is None:
        header = list(row)
        billt_i  = header.index('BillT')
        saty_i   = header.index('SaTy')
        netval_i = header.index('Net value')
        continue
    dt = row[0]
    if not isinstance(dt, datetime): continue
    bt = row[billt_i]; st = row[saty_i]
    if bt in EXCL_BILLT or st in EXCL_SATY:
        excl += 1; continue
    db = 'UTI' if str(row[5]) == '1799' else 'UMI'
    results[db][fy(dt)] += row[netval_i] or 0
    kept += 1
wb.close()
print(f'  kept={kept:,}  excl={excl:,}', flush=True)

# Save
out = {db: {str(y): round(v, 2) for y, v in fydata.items()}
       for db, fydata in results.items()}
outpath = '/sessions/beautiful-kind-bell/mnt/ISZE/01_data/derived/gps_billing_clean.json'
with open(outpath, 'w') as f:
    json.dump(out, f, indent=2)
print(f'\nSaved → {outpath}')

# Print summary
print(f'\n{"DB":<15} {"FY2024":>12} {"FY2025":>12} {"FY2026*":>12}')
print('-' * 57)
for db in sorted(results, key=lambda d: -results[d].get(2025, 0)):
    r = results[db]
    print(f'{db:<15} {r.get(2024,0)/1000:>10.1f}k  {r.get(2025,0)/1000:>10.1f}k  {r.get(2026,0)/1000:>10.1f}k')
