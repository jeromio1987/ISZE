import pandas as pd

DER = '01_data/00_derived/'
UNK = ['', 'unknown', 'unknown review', 'nan']


def stats(path, label):
    d = pd.read_csv(path, dtype=str, low_memory=False)
    col = 'aim_l1' if 'aim_l1' in d.columns else 'aim_level_1'
    v = d[col].fillna('').str.strip().str.lower()
    real = int((~v.isin(UNK)).sum())
    marker = int(v.isin(['unknown', 'unknown review']).sum())
    blank = int((v == '').sum())
    print('%-52s rows %8s  real %8s  marker %7s  blank %7s' % (label, format(len(d), ','), format(real, ','), format(marker, ','), format(blank, ',')))


stats(DER + 'aim_master_v2.csv.bak_pre_export_aim_eq_20260924_20260924_142051', 'master BEFORE the fork (14:08 backup)')
stats(DER + 'aim_master_v2.csv', 'master NOW')
stats(DER + 'AIM_Master_PN_Categories_Figkey_20260921.csv', 'Power BI csv (2021 name, newest content)')
stats(DER + 'AIM_Master_PN_Categories_Figkey_20260924.csv', 'Power BI csv (2024 name)')

m = pd.read_csv(DER + 'aim_master_v2.csv', dtype=str, low_memory=False)
f = m['aim_l1_fixed'].fillna('').str.strip().str.lower()
print()
print('master aim_l1_fixed -> real:', int((~f.isin(UNK)).sum()), ' marker:', int(f.isin(['unknown', 'unknown review']).sum()))
