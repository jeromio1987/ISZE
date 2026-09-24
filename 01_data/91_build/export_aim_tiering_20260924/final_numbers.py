"""The final numbers, with an explicit 'Tier A but not defensible' carve-out."""
from __future__ import annotations
import pandas as pd
pd.set_option('display.width', 320); pd.set_option('display.max_rows', 300)
ROOT = r'C:\Users\jerom\Desktop\claude\ISZE'
OUT = ROOT + r'\01_data\91_build\export_aim_tiering_20260924'

q = pd.read_csv(OUT + r'\queue_final_tiered.csv', dtype=str, encoding='utf-8-sig')
for c in ('pr00', 'list', 'd_n', 'f_n'):
    q[c] = pd.to_numeric(q[c], errors='coerce')
q['tierA'] = q['tierA'] == 'True'
q['f_seen'] = q['f_seen'] == 'True'
A = q[q['tierA']].copy()
TOT, TOTE = len(q), q['pr00'].sum()

print("TOTAL queue: rows=%d PN=%d PR00 EUR=%.2f list EUR=%.2f" % (
    TOT, q['pn'].nunique(), q['pr00'].sum(), q['list'].sum()))
print()
print("TIER A (rule): rows=%d PN=%d PR00 EUR=%.2f (%.1f%%) list EUR=%.2f" % (
    len(A), A['pn'].nunique(), A['pr00'].sum(), A['pr00'].sum() / TOTE * 100, A['list'].sum()))
print("TIER B       : rows=%d PN=%d PR00 EUR=%.2f (%.1f%%) list EUR=%.2f" % (
    TOT - len(A), q[~q['tierA']]['pn'].nunique(), q[~q['tierA']]['pr00'].sum(),
    q[~q['tierA']]['pr00'].sum() / TOTE * 100, q[~q['tierA']]['list'].sum()))

print()
print("=== Tier A split: description alone vs description + figure key ===")
only_desc = A[~A['f_seen']]
both = A[A['f_seen']]
for tag, sub in [("description only (fig key has no master evidence)", only_desc),
                 ("description AND figure key agree", both)]:
    print("  %-52s rows=%3d PN=%3d PR00 EUR=%10.2f list EUR=%10.2f" % (
        tag, len(sub), sub['pn'].nunique(), sub['pr00'].sum(), sub['list'].sum()))

# ---- the rows I cannot defend -------------------------------------------------
BAD_TEXT = {
    'GASKET; CYL HD':        'master calls it Transmission; a cylinder-head gasket is an engine gasket',
    'GASKET SET; ENG OVERHAUL': 'master calls it Transmission; an engine overhaul gasket set is engine',
}
CONVENTION = {
    'LAMP ASM; HEAD':        'lamp rows are split between Accident & Body and Electrical by convention only',
    'LAMP ASM; RR COMB':     'lamp rows are split between Accident & Body and Electrical by convention only',
    'LAMP ASM; FRT COMB':    'lamp rows are split between Accident & Body and Electrical by convention only',
    'LAMP ASM; FOG':         'lamp rows are split between Accident & Body and Electrical by convention only',
    'LAMP ASM; SIDE COMB':   'lamp rows are split between Accident & Body and Electrical by convention only',
    'CYLINDER ASM; CLUTCH MASTER': 'master files it under Brakes; it is a clutch hydraulic part',
    'PUMP ASM; OIL,P/S':     'master files it under Fuel System; it is a power-steering pump',
}
A['undefendable'] = A['desc_norm'].map(BAD_TEXT).notna()
A['convention'] = A['desc_norm'].map(CONVENTION).notna()

bad = A[A['undefendable']]
con = A[A['convention']]
clean = A[~A['undefendable'] & ~A['convention']]
print()
print("=== Tier A, carved out ===")
print("  rows I cannot defend (master label is wrong)      : rows=%d PR00 EUR=%.2f" % (len(bad), bad['pr00'].sum()))
for _, r in bad.iterrows():
    print("      %s  %-34s -> %-14s list=%.2f  %s" % (r['pn'], str(r['desc_norm'])[:34], r['d_l1'], r['list'], BAD_TEXT[r['desc_norm']]))
print("  rows where the family is a convention, not a fact : rows=%d PR00 EUR=%.2f" % (len(con), con['pr00'].sum()))
for _, r in con.iterrows():
    print("      %s  %-34s -> %-18s list=%.2f  %s" % (r['pn'], str(r['desc_norm'])[:34], r['d_l1'], r['list'], CONVENTION[r['desc_norm']]))
print()
print("  TIER A CLEAN: rows=%d PN=%d PR00 EUR=%.2f (%.1f%%) list EUR=%.2f" % (
    len(clean), clean['pn'].nunique(), clean['pr00'].sum(), clean['pr00'].sum() / TOTE * 100, clean['list'].sum()))
print("  TIER A CARVED: rows=%d PR00 EUR=%.2f" % (len(bad) + len(con), bad['pr00'].sum() + con['pr00'].sum()))
print("  TIER B (all) : rows=%d PN=%d PR00 EUR=%.2f (%.1f%%) list EUR=%.2f" % (
    TOT - len(A), q[~q['tierA']]['pn'].nunique(), q[~q['tierA']]['pr00'].sum(),
    q[~q['tierA']]['pr00'].sum() / TOTE * 100, q[~q['tierA']]['list'].sum()))

print()
print("=== Tier A clean: triples, top 60 ===")
dA = (clean.groupby(['desc_norm', 'd_l1', 'fk'])
      .agg(rows=('pn', 'size'), eur=('pr00', 'sum'), d_n=('d_n', 'max'), f_n=('f_n', 'max'))
      .reset_index().sort_values('eur', ascending=False))
print("  triples=%d" % len(dA))
for i, (_, r) in enumerate(dA.head(60).iterrows(), 1):
    fn = 'n/a' if pd.isna(r['f_n']) else int(r['f_n'])
    print("  %3d. %-40s -> %-22s fk=%-9s rows=%3d EUR=%10.2f master(desc=%d, fk=%s)" % (
        i, str(r['desc_norm'])[:40], str(r['d_l1'])[:22], str(r['fk']), int(r['rows']),
        float(r['eur']), int(r['d_n']), fn))
print()
print("=== Tier A clean: family spread ===")
f = clean.groupby('d_l1').agg(rows=('pn', 'size'), eur=('pr00', 'sum')).sort_values('eur', ascending=False)
for k, r in f.iterrows():
    print("  %-26s rows=%4d EUR=%12.2f" % (str(k), int(r['rows']), float(r['eur'])))

A.to_csv(OUT + r'\tierA_audited.csv', index=False, encoding='utf-8-sig')
q.to_csv(OUT + r'\queue_final_tiered.csv', index=False, encoding='utf-8-sig')
