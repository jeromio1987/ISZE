import pandas as pd
pd.set_option('display.width', 320); pd.set_option('display.max_rows', 300)
ROOT = r'C:\Users\jerom\Desktop\claude\ISZE'
q = pd.read_csv(ROOT + r'\01_data\91_build\export_aim_tiering_20260924\queue_final_tiered.csv', dtype=str, encoding='utf-8-sig')
for c in ('pr00', 'list', 'd_n', 'f_n'):
    q[c] = pd.to_numeric(q[c], errors='coerce')
m = pd.read_csv(ROOT + r'\01_data\00_derived\aim_master_v2.csv', dtype=str, low_memory=False)
m['desc'] = m['description'].fillna('').str.strip().str.upper()

print("=== the suspicious Tier A rules ===")
for d in ['GASKET; CYL HD', 'GASKET SET; ENG OVERHAUL', 'SEAL; OIL,FINAL PINION',
          'GEAR SET; FINAL DRIVE,FRT', 'LAMP ASM; HEAD', 'LAMP ASM; FOG', 'LAMP ASM; RR COMB']:
    sub = m[m['desc'] == d]
    print("\n%s : master rows=%d" % (d, len(sub)))
    print("   family:", dict(sub['aim_l1'].value_counts()))
    print("   l2    :", dict(sub['aim_l2'].value_counts().head(3)))
    for _, r in sub.head(3).iterrows():
        print("      %s %s -> %s > %s > %s" % (r['part_number'], str(r['description'])[:28],
                                               r['aim_l1'], r['aim_l2'], r['aim_l3']))

print()
print("=== how the master splits LAMP descriptions ===")
lamps = m[m['desc'].str.startswith('LAMP')]
print(lamps.groupby(['desc', 'aim_l1']).size().to_string())
