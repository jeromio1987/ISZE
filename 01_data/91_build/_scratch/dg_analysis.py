# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import io, warnings
warnings.filterwarnings('ignore')

OUT = io.open(r'C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\dg_analysis.txt', 'w', encoding='utf-8')
def p(*a):
    print(*a, file=OUT)

XLSX = r'c:\Users\jerom\Downloads\UMIUTI_Logistics_Study_v2.xlsx'
BASE = r'C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived'

# ---- Load sheets ----
data = pd.read_excel(XLSX, sheet_name='Data (joined)', header=3)
dglist = pd.read_excel(XLSX, sheet_name='DG list (deduped)', header=3)
master = pd.read_excel(XLSX, sheet_name='Master data', header=0)

p('=== Data (joined) shape ===', data.shape)
p('=== columns ===', list(data.columns))
p('=== dtypes ===')
p(data.dtypes.to_string())

# Coerce Material to string
def s(x):
    if pd.isna(x):
        return ''
    if isinstance(x, float) and x.is_integer():
        return str(int(x))
    return str(x).strip()

data['Material'] = data['Material'].map(s)
data['BillT'] = data['BillT'].astype(str).str.strip()
data['Entity'] = data['Entity'].astype(str).str.strip()
data['MoT'] = data['MoT'].astype(str).str.strip()
data['Sold-to pt'] = data['Sold-to pt'].astype(str).str.strip()

p()
p('=== Is DG raw distinct values (first 20) ===', data['Is DG'].dropna().unique()[:20])
p('=== BillT values ===', data['BillT'].value_counts(dropna=False).to_dict())
p('=== MoT values ===', data['MoT'].value_counts(dropna=False).to_dict())
p('=== Entity values ===', data['Entity'].value_counts(dropna=False).to_dict())
p('=== Sold-to pt values ===', data['Sold-to pt'].value_counts(dropna=False).to_dict())
p('=== Year values ===', data['Year'].value_counts(dropna=False).sort_index().to_dict())
p('=== total rows ===', len(data))

# DG list
dglist['Material'] = dglist['Material'].map(s)
dglist['Newest material no.'] = dglist['Newest material no.'].map(s)
dglist['UN number'] = dglist['UN number'].map(s)
p()
p('=== DG list shape ===', dglist.shape)
p('=== DG list UN number value counts (non-empty) ===')
un = dglist[dglist['UN number'] != '']['UN number']
p(un.value_counts(dropna=False).to_dict() if len(un) else 'NONE populated')
p('=== DG list UN number null/empty count ===', (dglist['UN number'].isna() | (dglist['UN number']=='')).sum(), 'of', len(dglist))

# Master data
master['P/N'] = master['P/N'].map(s)
master['Newest P/N'] = master['Newest P/N'].map(s)
p()
p('=== Master data shape ===', master.shape)
p('=== Master columns ===', list(master.columns))

OUT.close()
print('done3')
