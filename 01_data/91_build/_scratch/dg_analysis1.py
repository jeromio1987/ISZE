import sys, io, csv, openpyxl
import pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

P = r'c:\Users\jerom\Downloads\UMIUTI_Logistics_Study_v2.xlsx'

# ---------- DG list (deduped) ----------
dg = pd.read_excel(P, sheet_name='DG list (deduped)', header=3)
dg.columns = [str(c).strip() for c in dg.columns]
print("DG list (deduped) shape:", dg.shape)
print("columns:", list(dg.columns))
print("n unique Material:", dg['Material'].nunique())
print("n unique Newest material no.:", dg['Newest material no.'].nunique())
mat = set(dg['Material'].astype(str).str.strip())
new = set(dg['Newest material no.'].astype(str).str.strip())
union = mat | new
print("n union Material+Newest:", len(union))

# Family via description keywords
def fam(desc):
    d = str(desc).upper()
    if 'AIR BAG' in d or 'AIRBAG' in d: return 'Airbag'
    if 'BELT' in d or 'PRETENS' in d or 'SEAT' in d and 'BELT' in d: return 'Seatbelt pretensioner'
    if 'CONTROL UNIT' in d or 'SRS' in d or 'AIR BAG UNIT' in d: return 'SRS control unit'
    if 'OIL' in d or 'LUB' in d or 'FLUID' in d or 'CLEAN' in d or 'ATF' in d or 'GREASE' in d or 'DEF' in d or 'ADBLUE' in d: return 'Bulk lubricant'
    return 'Other'
dg['fam'] = dg['Description'].map(fam)
print("\nDG list (deduped) family distribution:")
print(dg['fam'].value_counts())
print("\nSample 'Other' descriptions:")
oth = dg[dg['fam']=='Other']['Description'].drop_duplicates().head(40)
for d in oth: print("  ", d)

# ---------- Data (joined) ----------
dj = pd.read_excel(P, sheet_name='Data (joined)', header=3)
dj.columns = [str(c).strip() for c in dj.columns]
print("\nData (joined) shape:", dj.shape)
print("columns:", list(dj.columns))
print("MoT values:", dj['MoT'].value_counts(dropna=False).to_dict())
print("Is DG values:", dj['Is DG'].value_counts(dropna=False).to_dict())
print("Entity values:", dj['Entity'].value_counts(dropna=False).to_dict())
print("Sold-to pt values:", dj['Sold-to pt'].value_counts(dropna=False).to_dict())

# normalize Is DG
def isdg(v):
    if v is None: return False
    if isinstance(v, bool): return v
    s = str(v).strip().lower()
    return s in ('true','1','yes','y','x','dg')
dj['_dg'] = dj['Is DG'].map(isdg)
print("DG lines (bool):", int(dj['_dg'].sum()))

dgd = dj[dj['_dg']]
print("distinct DG materials shipped:", dgd['Material'].nunique())
print("distinct DG Bill.Doc:", dgd['Bill.Doc.'].nunique())
print("Air docs:", dgd[dgd['MoT']=='Air']['Bill.Doc.'].nunique())
print("Sea docs:", dgd[dgd['MoT']=='Sea']['Bill.Doc.'].nunique())
print("Truck docs:", dgd[dgd['MoT']=='Truck']['Bill.Doc.'].nunique())
print("MoT x doc:", dgd.groupby('MoT')['Bill.Doc.'].nunique().to_dict())
print("MoT x line count:", dgd.groupby('MoT').size().to_dict())
print("\nDG EUR by Entity x MoT:")
print(dgd.groupby(['Entity','MoT']).agg(lines=('Material','size'), eur=('EUR Amount','sum'), kg=('Gross weight (kg)','sum')).round(2))
