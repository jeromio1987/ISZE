# -*- coding: utf-8 -*-
"""Build ISZE_KPI_Dashboard.html  --  the per-distributor KPI instrument panel.

Ten growth KPIs + five Competitive-parts (BVP) KPIs, measured per distributor (DB).
Anchor: per DB. Three working toggles (period / direction / warranty) that RECOMPUTE.

Read-only on every source. Writes only: this file's output HTML, plus QA artefacts
written by the QA script under sales\\_qa_kpi.

House rules applied:
  ISZE\\.cursor\\rules\\isze-gaps-need-context.mdc   euro leads, family named, fleet denominator
  dashboard-contrast-kpi.mdc                        navy / terracotta / Georgia + CSS hover tooltips
  a1-visual-delivery-qa.mdc                         chart-first, QA before any claim of done
"""
import pandas as pd, numpy as np, json, os, sys, io, datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = r'C:\Users\jerom\Desktop\claude\ISZE'
D = os.path.join(ROOT, '01_data', '00_derived')
SALES = os.path.join(ROOT, r'02_dashboards\sales')
OUT_HTML = os.path.join(SALES, 'ISZE_KPI_Dashboard.html')
SNAP = '2026-09-16'


def rd(name, **kw):
    return pd.read_csv(os.path.join(D, name), **kw)


def rdp(name, **kw):
    return pd.read_parquet(os.path.join(D, name), **kw)


# ===================================================================== 1. loads
sf = pd.read_parquet(os.path.join(D, 'sales_fact.parquet'),
                     columns=['billing_date', 'sold_to', 'sold_to_sap', 'net_sales_value',
                              'billed_qty', 'part_number'])
sf['bd'] = pd.to_datetime(sf.billing_date)
sf['cy'] = sf.bd.dt.year
sf['ym'] = sf.bd.dt.strftime('%Y-%m')
sf['fy'] = np.where(sf.bd.dt.month >= 4, sf.bd.dt.year, sf.bd.dt.year - 1)
sf['fykey'] = np.where(
    sf.bd.dt.month >= 4,
    sf.bd.dt.year.astype(str) + '/' + ((sf.bd.dt.year + 1) % 100).astype(str).str.zfill(2),
    (sf.bd.dt.year - 1).astype(str) + '/' + (sf.bd.dt.year % 100).astype(str).str.zfill(2))

dim = rd('distributor_dimension.csv')
gps = rd('gps_spu_by_distributor.csv')
warr = rd('warranty_by_db_year.csv')
warr_fy = rd('warranty_by_db_FY_canonical.csv')
cap = rd('pms_capture_by_db_year.csv')
opp = rd('pms_opportunity_matrix.csv')
traj = rd('capture_trajectory.csv')
wfall = rd('wallet_waterfall.csv')
revw = rd('revenue_waterfall.csv')
defe = rd('defection_alerts.csv')
aimx = rd('aim_exposure_by_db_year.csv')
prem = rd('price_premium.csv')
mix = rd('mix_genuine_bvp_pms.csv')
cls = rdp('db_parts_mix_classification.parquet')
basket = rd('bvp_addressable_basket.csv')
subst = rd('substitution_by_pair_year.csv')
aimfam = rd('aim_bvp_family_risk.csv')
sellout = rd('dealer_sellout_gps_2025.csv')
uio_b = rd(os.path.join(ROOT, r'03_analytics\Isuzu\prism\data\uio_by_model_bucket.csv'))
cat = rdp('parts_catalog_dimension.parquet',
          columns=['part_number', 'in_bvp_catalog', 'pms_category', 'fig_key'])
cat = cat.drop_duplicates('part_number')
cat['is_bvp'] = cat.in_bvp_catalog.fillna(False).astype(bool)

# ===================================================================== 2. attribution
# Israel trap: payer 1797 covers BOTH UMI and UTI; the split exists only at sold_to_sap
# level (UMI 1797 / UTI 1799). sold_to_sap is therefore loaded for every row FIRST and the
# payer code is added only where that key is not already claimed -- otherwise one Israeli
# distributor overwrites the other. Portugal is split over codes 519 and 92 and sums to one
# distributor through the same map.
cmap = {}
for col in ('sold_to_sap', 'payer_code'):
    for _, r in dim.iterrows():
        dc = r.distributor_code
        if not isinstance(dc, str) or not dc:
            continue
        v = r[col]
        if pd.notna(v):
            k = str(int(v))
            if col == 'sold_to_sap' or k not in cmap:
                cmap[k] = dc


def key_of(a, b):
    s = str(a)
    s = None if s in ('nan', 'None', '') else s.replace('.0', '')
    t = str(b).replace('.0', '')
    if s and s in cmap:
        return cmap[s]
    return cmap.get(t)


sf['code'] = [key_of(a, b) for a, b in zip(sf.sold_to_sap, sf.sold_to)]
sf = sf.merge(cat[['part_number', 'is_bvp', 'fig_key', 'pms_category']], on='part_number', how='left')
sf['is_bvp'] = sf.is_bvp.fillna(False).astype(bool)
sf['pfx'] = sf.fig_key.astype(str).str[:3].replace({'nan': None})

cy25 = sf[(sf.cy == 2025) & sf.code.notna()]
cy_all = sf[sf.cy == 2025]
fymask = (sf.bd >= '2025-04-01') & (sf.bd < '2026-04-01')
fy_all = sf[fymask]
fy26 = sf[fymask & sf.code.notna()]

cy25_attr = cy25.net_sales_value.sum()
cy25_unattr = cy_all[cy_all.code.isna()].net_sales_value.sum()
fy26_attr = fy26.net_sales_value.sum()
fy26_unattr = fy_all[fy_all.code.isna()].net_sales_value.sum()
billed_cy = cy25.groupby('code').net_sales_value.sum()
billed_fy = fy26.groupby('code').net_sales_value.sum()

KNOWN = {'IUK': 6221920, 'ITUK': 5769868, 'UTI': 3402117, 'UMI': 3388801,
         'GERMANY': 2577766, 'BELGIUM': 2143952, 'PORTUGAL': 1712791}
print('=' * 78)
print('ATTRIBUTION CHECK (Calendar 2025)')
print('  attributed total : EUR %s' % f'{cy25_attr:,.0f}')
print('  unattributed     : EUR %s  (four CIS markets + MIDI trade without a distributor code)' % f'{cy25_unattr:,.0f}')
ok = True
for k, v in KNOWN.items():
    got = billed_cy.get(k, 0)
    flag = 'OK' if abs(got - v) < 1 else 'MISMATCH'
    ok = ok and flag == 'OK'
    print(f'  {k:10s} {got:>12,.0f}   expected {v:>12,.0f}   {flag}')
print('  ALL KNOWN VALUES MATCH' if ok else '  *** ATTRIBUTION MAP IS WRONG ***')
if not ok or abs(cy25_attr - 33321625) > 5:
    raise SystemExit('attribution map failed the known-good check')
print('=' * 78)

# ===================================================================== 3. helpers
CIS4 = ['UKRAINE', 'ARMENIA', 'KAZAKHSTAN', 'PALESTINE']
# The spend file carries all 22 attributed codes; the four CIS markets sit outside the
# modelled denominators (no fleet denominator, no warranty), so the league and every
# modelled network figure must use the other 18 only.
MODEL18 = [c for c in gps[gps.year == 2025].distributor_code if c not in CIS4]
assert len(MODEL18) == 18, 'expected 18 modelled distributors, got %d' % len(MODEL18)
LABEL = {'IUK': 'IUK', 'ITUK': 'ITUK', 'GERMANY': 'Germany', 'BELGIUM': 'Belgium',
         'UMI': 'UMI', 'UTI': 'UTI', 'PORTUGAL': 'Portugal', 'IRELAND': 'Ireland',
         'NORWAY': 'Norway', 'SWEDEN': 'Sweden', 'GREECE': 'Greece', 'CYPRUS': 'Cyprus',
         'FINLAND': 'Finland', 'HUNGARY': 'Hungary', 'ROMANIA': 'Romania', 'MALTA': 'Malta',
         'DENMARK': 'Denmark', 'ICELAND': 'Iceland', 'UKRAINE': 'Ukraine',
         'ARMENIA': 'Armenia', 'KAZAKHSTAN': 'Kazakhstan', 'PALESTINE': 'Palestine'}
NETNAME = {'IUK': 'Isuzu (UK) Ltd', 'ITUK': 'Isuzu Truck (UK) Ltd',
           'UMI': 'Universal Motors Israel', 'UTI': 'Universal Trucks Israel',
           'GERMANY': 'Isuzu Sales Deutschland', 'BELGIUM': 'Isuzu Benelux',
           'PORTUGAL': 'Imotors', 'IRELAND': 'Isuzu Ireland',
           'NORWAY': 'Rutebileiernes Standardisering', 'SWEDEN': 'Isuzu Sverige',
           'GREECE': 'Petros Petropoulos', 'CYPRUS': 'A. Loutsios & Sons',
           'FINLAND': 'Isuzu Motor Finland', 'HUNGARY': 'AutoWallis / WAE',
           'ROMANIA': 'Isuzu Rom Auto', 'MALTA': 'GasanZammit Motors',
           'DENMARK': 'Isuzu Danmark', 'ICELAND': 'BL ehf.',
           'UKRAINE': 'Komtranskomplekt', 'ARMENIA': 'Grand Avto',
           'KAZAKHSTAN': 'CBC-Trans', 'PALESTINE': 'KIMA'}
# warranty expense file names -> distributor code
WARRMAP = {'ITUK': 'ITUK', 'IUK': 'IUK', 'UTI': 'UTI', 'UMI': 'UMI', 'ISD': 'GERMANY',
           'RSA': 'NORWAY', 'Sverige': 'SWEDEN', 'IBX': 'BELGIUM', 'Imotors': 'PORTUGAL',
           'Ireland': 'IRELAND', 'Greece': 'GREECE', 'AutoWallis': 'HUNGARY',
           'ROM Auto': 'ROMANIA', 'Loutsios': 'CYPRUS', 'GasanZammit': 'MALTA',
           'Nordic FI': 'FINLAND', 'Danmark': 'DENMARK', 'BL Iceland': 'ICELAND'}
# measured annual distance, km/yr. IUK = N35 Grafter odometer deltas (18,277 intervals,
# 5,421 vehicles). UTI = CV warranty odometer, confirmed against the market's own 50,000.
# Mainland LCV = IMIT service data (RG/D-Max only, no IUK row). Everything else = flat 20,000.
MILEAGE = {
    'IUK': (14494, 'N35 Grafter odometer deltas: 18,277 intervals across 5,421 vehicles'),
    'UTI': (51680, 'CV warranty odometer on N75, confirmed against the market'),
    'BELGIUM': (22842, 'IMIT service data, RG/D-Max, 1,405 VINs'),
    'CYPRUS': (18581, 'IMIT service data, RG/D-Max, 501 VINs'),
    'DENMARK': (22444, 'IMIT service data, RG/D-Max, 163 VINs'),
    'FINLAND': (24811, 'IMIT service data, RG/D-Max, 376 VINs'),
    'GERMANY': (17819, 'IMIT service data, RG/D-Max, 3,464 VINs'),
    'GREECE': (20328, 'IMIT service data, RG/D-Max, 1,045 VINs'),
    'HUNGARY': (26334, 'IMIT service data, RG/D-Max, 1,250 VINs'),
    'ICELAND': (20836, 'IMIT service data, RG/D-Max, 148 VINs'),
    'IRELAND': (27998, 'IMIT service data, RG/D-Max, 426 VINs'),
    'MALTA': (11749, 'IMIT service data, RG/D-Max, 323 VINs'),
    'NORWAY': (21375, 'IMIT service data, RG/D-Max, 3,382 VINs'),
    'PORTUGAL': (22742, 'IMIT service data, RG/D-Max, 1,596 VINs'),
    'ROMANIA': (24726, 'IMIT service data, RG/D-Max, 248 VINs'),
    'SWEDEN': (26670, 'IMIT service data, RG/D-Max, 3,378 VINs'),
    'UMI': (34443, 'IMIT service data, RG/D-Max, 13,611 VINs'),
}
FLAT_KM = 20000


def val(x, col):
    if x is None:
        return None
    v = getattr(x, col, None) if not isinstance(x, dict) else x.get(col)
    if v is None:
        return None
    try:
        if isinstance(v, float) and np.isnan(v):
            return None
    except Exception:
        return None
    return float(v)


# ===================================================================== 4. per-source cuts
G = {}
for _, r in gps.iterrows():
    G.setdefault(r.distributor_code, {})[int(r.year)] = r
U = {r.distributor_code: r for _, r in uio_b.iterrows()}

# --- capture by distributor and family, 2025 (calendar-tagged source)
C = {}
c25 = cap[cap.year == 2025]
for db, grp in c25.groupby('distributor_code'):
    t = grp[grp.line_type == 'total']
    b = grp[grp.line_type == 'bvp']
    g = grp[grp.line_type == 'genuine']
    if not len(t):
        continue
    exp, act = t.expected_qty.sum(), t.actual_qty.sum()
    top = t.sort_values('revenue_gap_eur', ascending=False).iloc[0]
    C[db] = dict(exp=exp, act=act, rate=(act / exp * 100 if exp else None),
                 gap=t.revenue_gap_eur.sum(), rev=t.actual_rev_eur.sum(),
                 gen_rev=gg if False else g.actual_rev_eur.sum(), bvp_rev=b.actual_rev_eur.sum(),
                 top_fam=top.category_label, top_gap=float(top.revenue_gap_eur),
                 top_rate=(float(top.capture_rate) * 100 if pd.notna(top.capture_rate) else None),
                 cats=int(t.category_label.nunique()))
O25 = opp[opp.year == 2025].groupby('distributor_code').tam_eur.sum().to_dict()
OPF = {}
for _, r in opp[opp.year == 2025].iterrows():
    OPF.setdefault(r.distributor_code, []).append(
        dict(fam=r.pms_category, gap=float(r.revenue_gap_eur), tam=float(r.tam_eur),
             rate=float(r.capture_rate_total) * 100))

# --- capture trend (rising / falling per DB x family)
TR = {}
for _, r in traj[traj.year == 2025].iterrows():
    TR.setdefault(r.distributor_code, []).append(
        dict(fam=r.pms_category, slope=float(r.trend_slope_pp_per_year) * 100,
             r2=float(r.trend_r2), dec=bool(r.alert_declining)))
CAPR = {}
for _, r in traj.iterrows():
    CAPR.setdefault(r.distributor_code, {}).setdefault(r.pms_category, []).append(
        (int(r.year), float(r.capture_rate) * 100))
for db in CAPR:
    for fam in CAPR[db]:
        CAPR[db][fam] = sorted(CAPR[db][fam])

# --- BVP mix by family, service-part universe (2025)
FAMBVP = {}
m25 = mix[mix.year == 2025]
for _, r in m25.iterrows():
    FAMBVP.setdefault(r.distributor_code, []).append(
        dict(fam=r.product_group_label, bvp=float(r.bvp_eur), total=float(r.total_eur)))

# --- defection, distributor level, euro allocated to the named family from the billing fact
TRAIL = sf[(sf.bd >= '2025-04-01') & (sf.bd < '2026-03-01') & sf.code.notna()
           & sf.pms_category.notna()]
DF = {}
dl = defe[defe.level == 'distributor']
for _, r in dl[dl.alert == True].iterrows():
    x = TRAIL[(TRAIL.code == r.distributor_code) & (TRAIL.pms_category == r.pms_category)]
    rec = DF.setdefault(r.distributor_code, dict(n_alert=0, silent_eur=0.0, tops=[]))
    rec['n_alert'] += 1
    rec['silent_eur'] += float(x.net_sales_value.sum())
    rec['tops'].append(dict(fam=r.pms_category, eur=float(x.net_sales_value.sum()),
                            silent=float(r.silent_months),
                            gap=float(r.median_gap_months),
                            mult=(float(r.silent_months) / float(r.median_gap_months)
                                  if r.median_gap_months else None),
                            last=str(r.last_order_month)))
for db in DF:
    DF[db]['tops'].sort(key=lambda z: -z['eur'])
    DF[db]['rows'] = int((dl.distributor_code == db).sum())
    if not DF[db]['n_alert']:
        DF[db] = None

# --- breadth: goods-classification (fig_key) prefixes actually bought
BR = {}
for db, grp in sf[sf.code.notna() & sf.pfx.notna()].groupby('code'):
    cy_s = set(grp.loc[grp.cy == 2025, 'pfx'])
    fy_s = set(grp.loc[grp.fykey == '2025/26', 'pfx'])
    BR[db] = dict(cy=sorted(cy_s), fy=sorted(fy_s))
FIGCOV = float(sf[sf.code.notna()].fig_key.notna().mean() * 100)

# --- exposure / price
A = {r.distributor_code: r for _, r in aimx[aimx.year == 2025].iterrows()}
P = {}
for db, grp in prem[prem.year == 2025].groupby('distributor_code'):
    w = grp.genuine_units + grp.bvp_units
    P[db] = dict(prem=float(np.average(grp.price_premium_pct, weights=w) * 100) if w.sum() else None,
                 cats=int(len(grp)), units=int(w.sum()),
                 gen_a=float(np.average(grp.genuine_asp_eur, weights=np.maximum(grp.genuine_units, 1))),
                 bvp_a=float(np.average(grp.bvp_asp_eur, weights=np.maximum(grp.bvp_units, 1))),
                 top=(grp.sort_values('price_premium_pct', ascending=False).iloc[0].pms_category
                      if len(grp) else None))
K = {r.distributor_code: r for _, r in cls[cls.year == 2025].iterrows()}
B2 = {}
for db, grp in basket.groupby('distributor_code'):
    tot = grp[['genuine_pn', 'bvp_pn']].drop_duplicates().shape[0]
    sel = grp[grp.currently_selling_bvp == True][['genuine_pn', 'bvp_pn']].drop_duplicates().shape[0]
    B2[db] = dict(pairs=int(tot), selling=int(sel), pct=(sel / tot * 100 if tot else None))
SB = {}
for db, grp in subst[subst.year == 2025].groupby('distributor_code'):
    SB[db] = dict(pairs=int(len(grp)), eur=float(grp.total_eur.sum()), bvp=float(grp.bvp_eur.sum()))
SUB_Y = {}
for y in (2023, 2024, 2025):
    s = subst[subst.year == y]
    SUB_Y[str(y)] = dict(bvp=float(s.bvp_eur.sum()), tot=float(s.total_eur.sum()),
                         pairs=int(len(s)), dbs=int(s.distributor_code.nunique()),
                         qtyb=float(s.bvp_qty.sum()), qtyt=float(s.total_qty.sum()))
B4 = {}
for _, r in aimfam[aimfam.year == 2025].iterrows():
    B4.setdefault(r.distributor_code, []).append(
        dict(fam=r.product_family, risk=float(r.aim_high_risk_rev_pct) * 100,
             bvp=float(r.bvp_share_eur) * 100, cat=float(r.catalog_sales_eur),
             bvpeur=float(r.bvp_eur), netmed=float(r.network_median_risk_pct) * 100))
DLR = {}
for db, grp in sellout.groupby('distributor_code'):
    DLR[db] = dict(eur=float(grp.total_eur.sum()), ents=int(len(grp)),
                   bvp=float(grp.bvp_eur.sum()), uio=float(grp.uio_units.iloc[0]),
                   cont=float(grp.bvp_eur.sum() + grp.genuine_contested_eur.sum()),
                   gencont=float(grp.genuine_contested_eur.sum()),
                   genonly=float(grp.genuine_only_eur.sum()))
# FY warranty expense (canonical, fiscal-tagged); CY warranty comes from the spend file
WARRF = {}
for _, r in warr_fy.iterrows():
    dc = WARRMAP.get(r.db)
    if dc:
        WARRF[dc] = dict(fy25=float(r.warr_FY2025), fy26=float(r.warr_FY2026))

# --- monthly billing model per distributor (eur, qty, competitive-parts eur)
MON = {}
ag = sf[sf.code.notna()].groupby(['code', 'ym']).agg(e=('net_sales_value', 'sum'),
                                                     q=('billed_qty', 'sum'))
agb = sf[sf.code.notna() & sf.is_bvp].groupby(['code', 'ym']).net_sales_value.sum()
for (db, ym), r in ag.iterrows():
    MON.setdefault(db, {})[ym] = [round(float(r.e), 2), float(r.q),
                                  round(float(agb.get((db, ym), 0.0)), 2)]

# growth split: calendar leg from revenue_waterfall (2024 -> 2025); fiscal leg computed from
# the billing fact with the two-leg formula. delta_mix_eur is ZERO in the source -- a
# non-separable residual, not a measured zero -- so it is published as unavailable.
RW = {}
for _, r in revw[revw.year_to == 2025].iterrows():
    d = RW.setdefault(r.distributor_code, dict(vol=0.0, price=0.0, mix=0.0,
                                               base=0.0, end=0.0, fams=[]))
    d['vol'] += float(r.delta_volume_eur)
    d['price'] += float(r.delta_price_eur)
    d['mix'] += float(r.delta_mix_eur)
    d['base'] += float(r.revenue_base_eur)
    d['end'] += float(r.revenue_end_eur)
    d['fams'].append(dict(fam=r.product_family, vol=float(r.delta_volume_eur),
                          price=float(r.delta_price_eur)))
FYS = {}
for db in MODEL18 + CIS4:
    a = sf[(sf.code == db) & (sf.fykey == '2024/25')]
    b = sf[(sf.code == db) & (sf.fykey == '2025/26')]
    q0, q1 = a.billed_qty.sum(), b.billed_qty.sum()
    p0 = a.net_sales_value.sum() / q0 if q0 else 0.0
    p1 = b.net_sales_value.sum() / q1 if q1 else 0.0
    FYS[db] = dict(vol=float((q1 - q0) * p0), price=float((p1 - p0) * q1),
                   base=float(a.net_sales_value.sum()), end=float(b.net_sales_value.sum()))
FAMB = {}
gf = rd('gps_spu_pms.csv')
for _, r in gf[(gf.year == 2025) & (gf.line_type == 'all')].iterrows():
    FAMB.setdefault(r.distributor_code, []).append(
        dict(fam=r.pms_category, eur=float(r.net_sales_eur), spu=float(r.spu_eur)))

# ===================================================================== 5. rows
DBS = []
for db in MODEL18 + CIS4:
    gr = G.get(db, {}).get(2025)
    u = U.get(db)
    k = K.get(db)
    wt, buckets = None, {}
    if u is not None:
        buckets = {'Truck': float(u.cv_std_uio or 0) + float(u.f_series_uio or 0),
                   'LCV': float(u.lcv_uio or 0)}
        wt = max(buckets, key=buckets.get)
    d = dict(
        code=db, label=LABEL.get(db, db), name=NETNAME.get(db, db),
        scope=(str(dim[dim.distributor_code == db].scope.iloc[0])
               if len(dim[dim.distributor_code == db]) else ''),
        region=(str(dim[dim.distributor_code == db].region.iloc[0])
                if len(dim[dim.distributor_code == db]) else ''),
        inModel=db in MODEL18,
        cy=float(billed_cy.get(db, 0)), fy=float(billed_fy.get(db, 0)),
        m=MON.get(db, {}),
        uio=val(gr, 'uio_units'), uio24=val(G.get(db, {}).get(2024), 'uio_units'),
        uio23=val(G.get(db, {}).get(2023), 'uio_units'),
        uioSrc=(str(gr.uio_source) if gr is not None and pd.notna(gr.uio_source) else None),
        spu=val(gr, 'spend_per_unit_eur'), spuXw=val(gr, 'spend_per_unit_ex_warranty_eur'),
        maxSpend=val(gr, 'max_spend_eur'),
        gpsVsMax=(val(gr, 'gps_capture_vs_max') * 100 if val(gr, 'gps_capture_vs_max') is not None else None),
        warr=val(gr, 'warranty_parts_eur'),
        warrShare=((val(gr, 'warranty_parts_eur') / val(gr, 'total_sales_eur') * 100)
                   if val(gr, 'warranty_parts_eur') is not None and val(gr, 'total_sales_eur') else None),
        gpsTotal=val(gr, 'total_sales_eur'),
        warrGap=(bool(gr.warranty_data_gap) if gr is not None and pd.notna(gr.warranty_data_gap) else None),
        warrFy=WARRF.get(db),
        cvUio=(float(u.cv_std_uio) if u is not None else None),
        fUio=(float(u.f_series_uio) if u is not None else None),
        lcvUio=(float(u.lcv_uio) if u is not None else None),
        weight=wt, cap=C.get(db), tam=(float(O25[db]) if db in O25 else None),
        famGap=OPF.get(db), famBvp=FAMBVP.get(db), famB=FAMB.get(db),
        traj=TR.get(db), defn=DF.get(db), b2=B2.get(db), b3=SB.get(db),
        dealer=DLR.get(db), mileage=MILEAGE.get(db),
        breadth=BR.get(db, {'cy': [], 'fy': []}),
        aim=(dict(risk=float(A[db].high_risk_rev_pct) * 100,
                  match=float(A[db].aim_match_rate_rev) * 100,
                  strategic=float(A[db].strategic_rev_eur)) if db in A else None),
        prem=P.get(db),
        bvp=(dict(rev=float(k.total_eur), bvp=float(k.bvp_eur), pct=float(k.bvp_pct) * 100,
                  cont=float(k.contested_eur), gencont=float(k.genuine_contested_eur),
                  genonly=float(k.genuine_only_eur),
                  capr=(float(k.contested_bvp_capture) * 100
                        if pd.notna(k.contested_bvp_capture) else None),
                  genonlyPct=float(k.genuine_only_pct) * 100) if k is not None else None),
        splitCy=None, splitFy=FYS.get(db),
        b4=B4.get(db), suby=None,
    )
    if db in RW:
        rr = RW[db]
        dd = dict(rr)
        dd['fams'] = sorted(rr['fams'], key=lambda z: -(abs(z['vol']) + abs(z['price'])))[:4]
        d['splitCy'] = dd
    if d['splitCy'] is None and d['cap'] is not None:
        # no calendar waterfall row (the four CIS markets and MIDI are outside it) ->
        # unavailable, never a copy of the fiscal number
        d['splitCy'] = 'na'
    DBS.append(d)

for d in DBS:
    s = subst[(subst.distributor_code == d['code'])]
    d['suby'] = {str(y): dict(bvp=float(s[s.year == y].bvp_eur.sum()),
                              tot=float(s[s.year == y].total_eur.sum()))
                 for y in (2023, 2024, 2025)}
DBS.sort(key=lambda r: -r['cy'])
# D08: overlay worksheet fleet (wallet_waterfall CY2025) on modelled markets.
# Keeps the ceiling from the same file it always did; does not re-run the wallet engine.
_w25_uio = {
    str(r.distributor_code): float(r.uio_units)
    for _, r in wfall[wfall.year == 2025].iterrows()
    if float(r.uio_units or 0) > 0
}
for _d in DBS:
    if _d['inModel'] and _d['code'] in _w25_uio:
        _wu = _w25_uio[_d['code']]
        _d['uio'] = _wu
        if _d.get('gpsTotal'):
            _d['spu'] = float(_d['gpsTotal']) / _wu
# Every modelled network figure uses the 18 modelled distributors only, so no numerator
# is on a 22-code basis while its denominator is on 18.
g25 = gps[(gps.year == 2025) & (~gps.distributor_code.isin(CIS4))]
g24 = gps[(gps.year == 2024) & (~gps.distributor_code.isin(CIS4))]
g23 = gps[(gps.year == 2023) & (~gps.distributor_code.isin(CIS4))]
N = dict(
    cyAll=float(cy_all.net_sales_value.sum()), cyAttr=float(cy25_attr), cyUn=float(cy25_unattr),
    fyAll=float(fy_all.net_sales_value.sum()), fyAttr=float(fy26_attr), fyUn=float(fy26_unattr),
    gpsCy=float(g25.total_sales_eur.sum()), gpsFy=float(sum(r['fy'] for r in DBS if r['inModel'])),
    uio=float(sum(_w25_uio.values())), uio24=float(g24.uio_units.sum()),
    uio23=float(g23.uio_units.sum()),
    spuCy=float(g25.total_sales_eur.sum() / sum(_w25_uio.values())),
    # The modelled network median on the billing fact, so the story text quotes the same
    # basis as the league table and the hero tile rather than the narrower spend file.
    spuFactMed=float(np.median([r['cy'] / r['uio'] for r in DBS
                                if r['inModel'] and r['uio']])),
    warrCy=float(g25.warranty_parts_eur.sum()),
    warrShare=float(g25.warranty_parts_eur.sum() / g25.total_sales_eur.sum() * 100),
    # The settled CY2025 warranty figure (EUR 4,719,992 = 14.6%) is measured against the
    # whole spend file, the only basis on which the four CIS markets' sales sit in the
    # denominator. Both bases are carried so the page can state which one it is showing.
    gpsCyAll=float(gps[gps.year == 2025].total_sales_eur.sum()),
    warrShareAll=float(g25.warranty_parts_eur.sum() / gps[gps.year == 2025].total_sales_eur.sum() * 100),
    warrFy=float(sum(v['fy26'] for v in WARRF.values())),
    capGap=float(opp[opp.year == 2025].revenue_gap_eur.sum()),
    capTam=float(opp[opp.year == 2025].tam_eur.sum()),
    capRate=float(c25[c25.line_type == 'total'].actual_qty.sum()
                  / c25[c25.line_type == 'total'].expected_qty.sum() * 100),
    capRev=float(c25[c25.line_type == 'total'].actual_rev_eur.sum()),
    capExp=float(c25[c25.line_type == 'total'].expected_qty.sum()),
    capAct=float(c25[c25.line_type == 'total'].actual_qty.sum()),
    capBvpRev=float(c25[c25.line_type == 'bvp'].actual_rev_eur.sum()),
    capShareBvp=float(c25[c25.line_type == 'bvp'].actual_rev_eur.sum()
                      / c25[c25.line_type == 'total'].actual_rev_eur.sum() * 100),
    breadthNet=int(sf[sf.code.notna() & (sf.cy == 2025)].pfx.nunique()),
    breadthAll=296,
    sellout=float(sellout.total_eur.sum()), selloutDbs=int(sellout.distributor_code.nunique()),
    bvpCy=float(cls[cls.year == 2025].bvp_eur.sum()),
    bvpAll=float(cls[cls.year == 2025].total_eur.sum()),
    bvpShareCy=float(cls[cls.year == 2025].bvp_eur.sum() / cls[cls.year == 2025].total_eur.sum() * 100),
    bvpFactCy=float(cy25[cy25.is_bvp].net_sales_value.sum()),
    bvpFactCyShare=float(cy25[cy25.is_bvp].net_sales_value.sum() / cy25.net_sales_value.sum() * 100),
    bvpFactFy=float(fy26[fy26.is_bvp].net_sales_value.sum()),
    bvpFactFyShare=float(fy26[fy26.is_bvp].net_sales_value.sum() / fy26.net_sales_value.sum() * 100),
    ceiling=float(wfall[wfall.year == 2025].theoretical_wallet_eur.sum()),
    ceilingBvp=float(wfall[wfall.year == 2025].captured_bvp_eur.sum()),
    ceilingCap=float(wfall[wfall.year == 2025].captured_total_eur.sum()),
    ceilingShare=float(wfall[wfall.year == 2025].captured_bvp_eur.sum()
                       / wfall[wfall.year == 2025].captured_total_eur.sum() * 100),
    mixUniv=float(mix[mix.year == 2025].total_eur.sum()),
    mixBvp=float(mix[mix.year == 2025].bvp_eur.sum()),
    mixShare=float(mix[mix.year == 2025].bvp_eur.sum() / mix[mix.year == 2025].total_eur.sum() * 100),
    defEur=float(sum((v or {}).get('silent_eur', 0) for v in DF.values())),
    defN=int(sum((v or {}).get('n_alert', 0) for v in DF.values())),
    defRows=int(len(dl)), custN=int(((defe.level == 'dealer') & (defe.alert == True)).sum()),
    custRows=int((defe.level == 'dealer').sum()),
    premMed=float(prem[prem.year == 2025].price_premium_pct.median() * 100),
    subBvp=float(subst[subst.year == 2025].bvp_eur.sum()),
    subTot=float(subst[subst.year == 2025].total_eur.sum()),
    figcov=FIGCOV,
)
print('NETWORK  billed CY25 %s | FY25/26 %s | GPS base %s | UIO %s (2024 %s)'
      % (f'{N["cyAttr"]:,.0f}', f'{N["fyAttr"]:,.0f}', f'{N["gpsCy"]:,.0f}',
         f'{N["uio"]:,.0f}', f'{N["uio24"]:,.0f}'))
print('  capture %.1f%% | uncaptured %s | warranty %s (%.1f%%) | BVP %s / %s | contested euro %s'
      % (N['capRate'], f'{N["capGap"]:,.0f}', f'{N["warrCy"]:,.0f}', N['warrShare'],
         f'{N["bvpShareCy"]:.2f}%', f'{N["mixShare"]:.2f}%', f'{N["bvpAll"]-N["bvpCy"]:,.0f}'))

payload = dict(snap=SNAP, net=N, dbs=DBS, model18=MODEL18, cis4=CIS4, known=KNOWN,
               b4=B4, suby=SUB_Y, rw=RW, fys=FYS, story=['IUK', 'ITUK', 'GERMANY'])
def _strict(o):
    """Sentinel for values pandas cannot represent: numpy NaN/Inf and a None slope.
    Without this the payload carries bare `NaN`, which is invalid JSON and reads as a
    rendered defect if a chart ever prints it. Charts already skip non-finite slopes."""
    return None


class _NoNaN(json.JSONEncoder):
    """Same output as json.dumps(default=float), but non-finite floats become null."""
    def default(self, o):
        return float(o)

    def iterencode(self, o, _one_shot=False):
        def _fix(v):
            if isinstance(v, float) and not np.isfinite(v):
                return None
            if isinstance(v, dict):
                return {k: _fix(x) for k, x in v.items()}
            if isinstance(v, (list, tuple)):
                return [_fix(x) for x in v]
            return v
        return super().iterencode(_fix(o), _one_shot)


PAY_JSON = _NoNaN(separators=(',', ':'), allow_nan=False).encode(payload).replace('</', '<\\/')
if 'NaN' in PAY_JSON:
    raise SystemExit('builder: NaN leaked into the payload')
print('payload bytes %d' % len(PAY_JSON))
if '--check' in sys.argv:
    sys.exit(0)

# ===================================================================== 6. HTML
CSS = r"""
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:#f4f1ea;color:#222;
 font:13.5px/1.45 -apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
h1,h2,h3,h4,.serif{font-family:Georgia,"Times New Roman",serif}
.wrap{max-width:1560px;margin:0 auto;padding:0 16px 56px}
header.top{background:#15233c;color:#f7f4ee;padding:20px 0 16px;
 border-bottom:4px solid #c0552d}
header.top .inner{max-width:1560px;margin:0 auto;padding:0 16px}
header.top h1{margin:0 0 4px;font-size:25px;letter-spacing:.2px}
header.top .sub{color:#e6dfd0;font-size:12.5px;max-width:1080px}
header.top .flags{margin-top:10px;display:flex;flex-wrap:wrap;gap:6px}
.flag{background:#1e3050;border:1px solid #33507d;border-radius:3px;padding:2px 7px;
 font-size:11px;color:#f7f4ee}
.flag.warn{background:#3d2418;border-color:#c0552d;color:#f7d9c8}
h2.sec{margin:30px 0 4px;font-size:17px;color:#15233c;border-bottom:2px solid #15233c;
 padding-bottom:4px;display:flex;align-items:baseline;gap:10px;flex-wrap:wrap}
h2.sec .n{font:11px/1 inherit;color:#f7f4ee;background:#c0552d;padding:4px 7px;border-radius:2px;
 font-family:-apple-system,"Segoe UI",sans-serif;letter-spacing:.5px}
h2.sec .q{font:12.5px/1.4 -apple-system,"Segoe UI",sans-serif;color:#5a5344;font-weight:400}
h3{font-size:14px;color:#15233c;margin:16px 0 6px}
p.note{color:#5a5344;font-size:12px;margin:6px 0 0;max-width:1100px}
p.tiny{color:#6b6353;font-size:11.5px;margin:5px 0 0;max-width:1100px}
.card{background:#fff;border:1px solid #ddd6c6;border-radius:4px;padding:12px 14px;margin:10px 0}
.grid{display:grid;gap:10px}
.g2{grid-template-columns:repeat(2,minmax(0,1fr))}
.g3{grid-template-columns:repeat(3,minmax(0,1fr))}
.g4{grid-template-columns:repeat(4,minmax(0,1fr))}
.g6{grid-template-columns:repeat(6,minmax(0,1fr))}
@media(max-width:1240px){.g6{grid-template-columns:repeat(3,minmax(0,1fr))}.g4{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:900px){.g2,.g3,.g4,.g6{grid-template-columns:minmax(0,1fr)}}
/* ---- hero ---- */
.hero{display:grid;gap:10px;grid-template-columns:repeat(4,minmax(0,1fr));margin-top:14px}
@media(max-width:1100px){.hero{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:620px){.hero{grid-template-columns:minmax(0,1fr)}}
.kpi{background:#fff;border:1px solid #ddd6c6;border-left:4px solid #15233c;border-radius:3px;
 padding:10px 12px 11px;position:relative}
.kpi .lbl{font-size:11px;text-transform:uppercase;letter-spacing:.6px;color:#5a5344}
.kpi .big{font-family:Georgia,serif;font-size:27px;line-height:1.1;color:#15233c;margin:4px 0 2px}
.kpi .big.t{color:#c0552d}
.kpi .den{font-size:11.5px;color:#5a5344}
.kpi .den b{color:#222}
.kpi .tl,.tl{font-size:11px;color:#5a5344}
/* ---- tooltips ---- */
[data-tip]{position:relative;cursor:help;border-bottom:1px dotted #9a9versions}
.tip{cursor:help;border-bottom:1px dotted #a99f8a}
.tip:hover,.tip:focus{background:#fdf6ec}
[data-tip]:hover::after,.tip:hover::after,[data-tip]:focus::after,.tip:focus::after{
 content:attr(data-tip);position:fixed;z-index:9000;left:50%;top:auto;bottom:24px;transform:translateX(-50%);
 max-width:min(560px,92vw);background:#15233c;color:#f7f4ee;border:1px solid #33507d;
 border-left:4px solid #c0552d;border-radius:3px;padding:9px 12px;font:12px/1.5 -apple-system,
 "Segoe UI",Roboto,sans-serif;white-space:pre-line;box-shadow:0 6px 20px rgba(0,0,0,.35);
 pointer-events:none}
.tipbox[data-tip]:hover::after,.tipbox[data-tip]:focus::after{bottom:auto;top:calc(100% + 6px);
 left:0;transform:none;max-width:min(420px,80vw)}
/* ---- controls ---- */
.bar{position:sticky;top:0;z-index:400;background:#15233c;color:#f7f4ee;
 padding:9px 0;border-bottom:3px solid #c0552d;box-shadow:0 2px 8px rgba(0,0,0,.18)}
.bar .inner{max-width:1560px;margin:0 auto;padding:0 16px;display:flex;flex-wrap:wrap;gap:8px 18px;align-items:center}
.bar .grp{display:flex;align-items:center;gap:6px;flex-wrap:wrap}
.bar .gl{font-size:10.5px;text-transform:uppercase;letter-spacing:.7px;color:#b9c6dc}
.bar button{font:12px/1 inherit;background:#22375c;color:#f7f4ee;border:1px solid #3d5a8c;
 border-radius:3px;padding:5px 9px;cursor:pointer}
.bar button:hover{background:#2c4570}
.bar button[aria-pressed="true"]{background:#c0552d;border-color:#c0552d;color:#fff;font-weight:600}
.bar .state{font-size:11.5px;color:#f7f4ee;background:#1b2c49;border:1px dashed #4a6ba8;
 padding:4px 9px;border-radius:3px;margin-left:auto}
@media(max-width:700px){.bar .state{margin-left:0;width:100%}}
/* ---- tables ---- */
.tbl{width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch;border:1px solid #ddd6c6;
 border-radius:4px;background:#fff}
table{border-collapse:collapse;width:100%;font-size:12px;min-width:1180px}
th,td{padding:5px 7px;text-align:right;white-space:nowrap;border-bottom:1px solid #ece6d8}
th{background:#15233c;color:#f7f4ee;font-weight:600;position:sticky;top:0;z-index:2;
 font-size:11px;text-transform:uppercase;letter-spacing:.35px}
th.l,td.l{text-align:left}
thead tr.grp th{background:#1e3050;color:#e8e2d4;font-size:10.5px;top:0}
tbody tr:nth-child(even){background:#faf8f3}
tbody tr:hover{background:#f1ece0}
tbody tr.story{background:#fdf1e9}
tbody tr.story td:first-child{border-left:4px solid #c0552d}
tbody tr.cis td{color:#6b6353}
tfoot td{background:#eef1f6;color:#15233c;font-weight:600;border-top:2px solid #15233c}
td.na{color:#8b8272;font-style:italic}
td.pos{color:#1f6b45}
td.neg{color:#a33217}
.chip{display:inline-block;padding:1px 5px;border-radius:2px;font-size:10.5px;border:1px solid}
.chip.g{background:#e6f2ea;border-color:#1f6b45;color:#1f6b45}
.chip.a{background:#fdf3e3;border-color:#8a6a20;color:#6b5214}
.chip.r{background:#fbe9e2;border-color:#c0552d;color:#973f1c}
.chip.n{background:#eef1f6;border-color:#5a5344;color:#5a5344}
.warnbar{background:#fbe9e2;border:1px solid #c0552d;border-left:4px solid #c0552d;color:#6b2f16;padding:7px 10px;margin:6px 0 8px;font-size:12px;line-height:1.45;border-radius:2px}
.bar-mini{display:inline-block;height:9px;background:#15233c;vertical-align:middle;border-radius:1px}
.bar-mini.t{background:#c0552d}
.bar-mini.p{background:#8d8574}
/* ---- chart blocks ---- */
.chart{background:#fff;border:1px solid #ddd6c6;border-radius:4px;padding:12px 14px;margin:10px 0}
.chart h3{margin:0 0 2px;font-size:14.5px}
.chart .cap{font-size:11.5px;color:#5a5344;margin:2px 0 8px;max-width:980px}
.legend{display:flex;flex-wrap:wrap;gap:4px 14px;margin:0 0 8px;font-size:11.5px;color:#3d372b}
.legend i{display:inline-block;width:10px;height:10px;margin-right:4px;border-radius:1px;
 vertical-align:-1px}
svg{display:block;max-width:100%;height:auto;overflow:visible}
.svgwrap{overflow-x:auto}
.hm{display:grid;gap:1px;font-size:10.5px}
.hm .cell{height:19px;border-radius:1px;display:flex;align-items:center;justify-content:center;
 color:#fff;font-size:9.5px}
.hm .cell.pale{color:#222}
.hm .rowlbl,.hm .collbl{color:#3d372b;display:flex;align-items:center;font-size:10.5px;
 overflow:hidden;white-space:nowrap}
.mini{display:grid;gap:2px;grid-template-columns:repeat(auto-fill,minmax(158px,1fr))}
.mini .m{border:1px solid #e2dbcb;border-radius:3px;padding:5px 6px;background:#fdfcf9}
.mini .m .h{font-size:10.5px;color:#15233c;display:flex;justify-content:space-between;gap:4px}
.mini .m .v{font-size:11px;color:#5a5344}
.rc{display:flex;flex-wrap:wrap;gap:6px}
.rc .r{background:#1e3050;border:1px solid #33507d;color:#f7f4ee;border-radius:3px;padding:6px 9px;
 font-size:11.5px}
.rc .r b{font-family:Georgia,serif;font-size:15px}
.rc .r.c{background:#3d2418;border-color:#c0552d}
.rc .r.g{background:#1d3a2c;border-color:#2f7a55}
ul.tight{margin:6px 0 0;padding-left:18px;font-size:12.5px;color:#2b2b2b}
ul.tight li{margin:3px 0}
.warnbox{background:#fdf1e9;border:1px solid #c0552d;border-left:4px solid #c0552d;border-radius:3px;
 padding:9px 12px;font-size:12.5px;color:#5c2b13;margin:8px 0}
.warnbox b{color:#973f1c}
.flow{display:flex;flex-wrap:wrap;gap:8px;align-items:stretch}
.flow .f{background:#f7f4ee;border:1px solid #ddd6c6;border-radius:3px;padding:7px 10px;
 font-size:11.5px;min-width:120px}
.flow .f b{display:block;font-family:Georgia,serif;font-size:16px;color:#15233c}
.flow .f.t b{color:#c0552d}
footer.foot{margin-top:26px;border-top:2px solid #15233c;padding-top:10px;font-size:11.5px;
 color:#5a5344;max-width:1200px}
.sticky-note{font-size:11px;color:#5a5344;margin-left:6px}
"""

JS = r"""
const K = window.__KPI__;
const MODE = {period:'cy', dir:'db', warr:'inc'};
const $ = s => document.querySelector(s);
const $$ = s => Array.from(document.querySelectorAll(s));

/* ---------- formatting ---------- */
function eur(v, dp){
  if(v===null||v===undefined||v==='na'||isNaN(v)) return 'unavailable';
  const n = Number(v);
  if(Math.abs(n)>=1e6) return '\u20ac'+(n/1e6).toFixed(2)+'M';
  if(Math.abs(n)>=1e4) return '\u20ac'+Math.round(n/1e3)+'k';
  return '\u20ac'+n.toFixed(dp===undefined?0:dp);
}
function eurL(v){
  if(v===null||v===undefined||v==='na'||isNaN(v)) return 'unavailable';
  return '\u20ac'+Math.round(Number(v)).toLocaleString('en-GB');
}
function pct(v,dp){ if(v===null||v===undefined||v==='na'||isNaN(v)) return 'unavailable';
  return Number(v).toFixed(dp===undefined?1:dp)+'%'; }
function num(v){ if(v===null||v===undefined||v==='na'||isNaN(v)) return 'unavailable';
  return Math.round(Number(v)).toLocaleString('en-GB'); }
function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;'); }

/* ---------- state-derived values ---------- */
const LBL_P = {cy:'Calendar 2025 (Jan\u2013Dec)', fy:'FY25/26 (Apr 2025 \u2013 Mar 2026)'};
const LBL_D = {db:'ISZE \u2192 DB (what we invoice the distributor)',
               dlr:'DB \u2192 dealer (what the distributor invoices its dealers)'};
const LBL_W = {inc:'warranty included', ex:'warranty excluded'};

function monthsFor(){
  const out=[];
  if(MODE.period==='cy'){ for(let m=1;m<=12;m++) out.push('2025-'+String(m).padStart(2,'0')); }
  else { for(let m=4;m<=12;m++) out.push('2025-'+String(m).padStart(2,'0'));
         for(let m=1;m<=3;m++) out.push('2026-'+String(m).padStart(2,'0')); }
  return out;
}
/* Billing-side figures. period + warranty recompute; direction swaps to sales to dealer. */
function view(db){
  const ms = monthsFor();
  let e=0,q=0,b=0, cov = ms.length;
  let used=0;
  ms.forEach(m=>{ const r=db.m[m]; if(r){ used++; e+=r[0]; q+=r[1]; b+=r[2]; } });
  const isCis = K.cis4.indexOf(db.code)>=0;
  let warr=null, warrReason=null;
  if(isCis){ warrReason='no warranty data for this market'; }
  else if(MODE.period==='cy'){ warr = db.warr; if(warr===null) warrReason='not held for this market'; }
  else { warr = db.warrFy ? db.warrFy.fy26 : null;
         if(warr===null) warrReason='no fiscal-tagged warranty file for this market'; }
  if(MODE.warr==='ex' && warr!==null) e = e - warr;
  if(MODE.warr==='ex' && warr===null && !isCis) e = null;   /* cannot strip what we do not hold */
  const dir = MODE.dir;
  const dlr = db.dealer;
  let shown, dirReason=null, warrNoSplit=false;
  if(dir==='db'){ shown = e; }
  else {
    /* The sales-to-dealer file carries no warranty column, so the warranty setting cannot
       be applied in this direction. Say so rather than quietly repeating a warranty-inclusive
       figure when the toggle says warranty excluded. */
    warrNoSplit = (MODE.warr==='ex');
    if(dlr && (MODE.period==='cy')) { shown = dlr.eur; }
    else if(dlr && MODE.period==='fy'){ shown='na'; dirReason='sales-to-dealer file is calendar-2025 only'; }
    else { shown='na'; dirReason='no sales-to-dealer file for this distributor'; }
    if(dlr && MODE.period==='cy' && warrNoSplit){
      dirReason = (dirReason? dirReason+'; ' : '') +
        'the sales-to-dealer file carries no warranty split, so this figure includes warranty parts';
    }
  }
  const uio = db.uio;
  let spu=null, spuWhy=null;
  if(dir==='db'){
    if(shown===null||shown==='na'||isCis||uio===null||!uio){ spuWhy = isCis? 'no fleet denominator for this market'
        : (uio? 'a figure is unavailable' : 'no fleet denominator for this market'); }
    else spu = shown/uio;
  } else spu=null;
  const uioPrev = db.uio24;
  return {eur:shown, qty:q, bvp:b, warr:warr, warrReason:warrReason, dir:dir,
          dirReason:dirReason, warrNoSplit:warrNoSplit, spu:spu, spuWhy:spuWhy, isCis:isCis, uio:uio, uioPrev:uioPrev,
          monthsUsed:used, monthsCov:cov,
          base:e, sub:'', mileage: db.mileage ? db.mileage[0] : 20000,
          mileageMeasured: !!db.mileage};
}

function netView(){
  const ms=monthsFor();
  let e=0,b=0,miss=0;
  K.dbs.forEach(db=>{ if(!db.inModel) return; ms.forEach(m=>{ const r=db.m[m];
    if(r){ e+=r[0]; b+=r[2]; } else miss++; }); });
  const isCis=false;
  let warr = MODE.period==='cy' ? K.net.warrCy : K.net.warrFy;
  const warrAvail = MODE.period==='cy' ? true : (warr>0);
  let ex = e - (warrAvail?warr:0);
  if(MODE.warr==='ex'){ e = ex; }
  const dir = MODE.dir;
  let shown=e, note='';
  if(dir==='dlr'){
    shown = MODE.period==='cy' ? K.net.sellout : 'na';
    note = MODE.period==='cy' ? '' : 'sales-to-dealer file is calendar-2025 only';
  }
  const uio=K.net.uio;
  let spu = (dir==='db' && e>0 && uio>0) ? e/uio : null;
  return {eur:shown, bvp:b, warr:warr, warrAvail:warrAvail, uio:uio, spu:spu, note:note,
          uioPrev:K.net.uio24, monthsMiss:miss};
}
function t(txt, extra){ return (extra? extra+'\n':'') + txt; }
const SNAP = 'Snapshot '+K.snap+'. ';
"""

print('CSS/JS prepared: %d + %d bytes' % (len(CSS), len(JS)))

JS += r"""
/* =================================================================== helpers */
function T(formula, notincl, extra){
  return 'Formula: '+formula+'\nSnapshot: '+K.snap+'.'+ (extra? '\n'+extra : '') +
         (notincl? '\nNot included: '+notincl : '');
}
function tip(txt, inner, cls){
  return '<span class="tip '+(cls||'')+'" tabindex="0" data-tip="'+
    String(txt).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;')+'">'+inner+'</span>';
}
const SET = () => 'Setting: '+LBL_P[MODE.period]+' \u00b7 '+LBL_D[MODE.dir]+' \u00b7 '+LBL_W[MODE.warr]+'.';
const CYNOTE = 'Source is calendar-tagged only: the fiscal view cannot be computed from it.';
function cyOnly(html, why){
  if(MODE.period!=='fy') return html;
  return '<span class="cyonly">'+html+'</span> <span class="chip n" data-tip="'+(
    'Shown for Calendar 2025. The fiscal view is unavailable because: '+(why||CYNOTE)
    )+'\nSnapshot: '+K.snap+'.">CY25</span>';
}
/* A caption-level marker for a whole chart whose source cannot support the fiscal view.
   Without it a reader on FY25/26 would take a calendar figure for a fiscal one. */
function cyChart(why){
  if(MODE.period!=='fy') return '';
  return '<p class="tiny"><span class="chip n" data-tip="Shown for Calendar 2025. The fiscal view is unavailable because: '+
    why+'\nSnapshot: '+K.snap+'.">CY25</span> <b>Calendar figure, not fiscal:</b> '+why+'</p>';
}
function arrow(now, prev){
  if(now===null||prev===null||!prev||now===undefined) return '<span class="na">\u2013</span>';
  const d=(now-prev)/prev*100;
  const s=(d>=0?'\u25b2':' \u25bc')+' '+Math.abs(d).toFixed(1)+'%';
  return '<span class="'+(d>=0?'pos':'neg')+'">'+s+'</span>';
}
function bar(v, max, cls, w){
  const W = w||70;
  if(v===null||v==='na'||isNaN(v)) return '';
  const px = Math.max(1, Math.round(Math.abs(v)/max*W));
  return '<span class="bar-mini '+(cls||'')+'" style="width:'+px+'px"></span>';
}
const CH = [];
function reg(n){ CH.push(n); }

/* =================================================================== hero */
function heroHTML(){
  const n = netView();
  const gap = K.net.capGap, tam = K.net.capTam;
  const rate = K.net.capRate;
  const uio = K.net.uio;
  const cards = [];
  cards.push('<div class="kpi"><div class="lbl">Spend per truck per year</div>'+
    '<div class="big">'+(n.spu? '\u20ac'+n.spu.toFixed(0) : 'unavailable')+'</div>'+
    '<div class="den">on '+tip(T('parts billed \u00f7 vehicles in service (UIO), numerator and denominator both on the 18 modelled distributors.',
      'the four CIS markets, which have no fleet denominator and no warranty data; dealer inventory movements. '+
      'The spend file reconciles to \u20ac'+Math.round(K.net.gpsCy).toLocaleString('en-GB')+' for the modelled book with warranty included.',
      SET()+' Only the billing-fact numerator moves with the period and warranty toggles: the fleet denominator is a 2025 stock count, and on the sales-to-dealer direction this tile is withheld because the six sales-to-dealer files carry a different fleet basis.'),
      num(uio)+' vehicles in service')+'</div>'+
    '<div class="tl">'+(n.spu? 'parts billed to the 18 modelled distributors '+eur(n.eur) : 'needs the ISZE \u2192 DB direction')+'</div></div>');
  cards.push('<div class="kpi"><div class="lbl">Service-part capture</div>'+
    '<div class="big t">'+rate.toFixed(1)+'%</div>'+
    '<div class="den">of the '+num(K.net.capExp)+' service parts the model expects</div>'+
    '<div class="tl">'+tip(T('units billed \u00f7 units the maintenance model expects, across the 14 service families, on the same fleet.',
      'the eight markets whose target spend sits on one flat \u20ac250-per-truck placeholder; parts outside the 14 service families.',
      SET()+' Calendar-2025 source: '+CYNOTE),
      'uncaptured GPS value '+eur(gap))+'</div></div>');
  cards.push('<div class="kpi"><div class="lbl">Uncaptured GPS value</div>'+
    '<div class="big t">'+eur(gap)+'</div>'+
    '<div class="den">addressable on '+eur(tam)+' of modelled demand ('+(tam/gap).toFixed(1)+'&times;)'+'</div>'+
    '<div class="tl">'+tip(T('modelled demand (tam_eur) \u2212 parts billed in those families, summed over the 14 service families and 18 distributors.',
      'the four CIS markets and MIDI (no fleet denominator); the flat-\u20ac250 markets\u2019 ceiling precision.',
      SET()+' A ceiling, not a forecast. '+CYNOTE),
      'service families: air, oil and fuel filters, urea filter, blower filter, brake pad, shoe, rotor, clutch disc, kit, pressure plate, booster, pilot and release bearing')+'</div></div>');
  cards.push('<div class="kpi"><div class="lbl">Vehicles in service (UIO)</div>'+
    '<div class="big">'+num(uio)+'</div>'+
    '<div class="den">'+arrow(uio,K.net.uio24)+' against 2024, '+num(K.net.uio24)+'</div>'+
    '<div class="tl">'+tip(T('sum of vehicles in service across the 18 modelled distributor databases, 2025.',
      'the four CIS markets (no denominator), the 2026\u20132030 forecast (withdrawn).',
      SET()+' Basis: v18 actual for 17 markets, ITUK DVLA for the UK truck fleet.'),
      'no 2026\u20132030 forecast is shown anywhere on this page')+'</div></div>');
  return '<div class="hero">'+cards.join('')+'</div>';
}

/* =================================================================== controls */
function barHTML(){
  const b=(k,v,t,extra)=>'<button type="button" data-k="'+k+'" data-v="'+v+'"'+
    (MODE[k]===v?' aria-pressed="true"':'')+' data-tip="'+t+'\nSnapshot: '+K.snap+'.'+(extra?'\n'+extra:'')+
    '">'+t.split('.')[0]+'</button>';
  return '<div class="bar"><div class="inner">'+
    '<div class="grp"><span class="gl">Period</span>'+
      b('period','cy','Calendar 2025 (Jan\u2013Dec). Recomputed from the billing fact on billing date.','')+
      b('period','fy','FY25/26 (Apr 2025 \u2013 Mar 2026). Recomputed from the billing fact on billing date.')+
    '</div>'+
    '<div class="grp"><span class="gl">Direction</span>'+
      b('dir','db','ISZE \u2192 DB: what we invoice the distributor.')+
      b('dir','dlr','DB \u2192 dealer: what the distributor invoices its dealers. Only six distributors file it (ITUK, UTI, Ireland, IUK, Greece, Portugal).')+
    '</div>'+
    '<div class="grp"><span class="gl">Warranty</span>'+
      b('warr','inc','Warranty included in what we billed.')+
      b('warr','ex','Warranty excluded: warranty parts are stripped to leave the customer-paid book.')+
    '</div>'+
    '<div class="state" id="stateChip"></div>'+
  '</div></div>';
}

/* =================================================================== league */
const COLS = [
 ['Distributor','l'],['Billed',''],['Share',''],['Vehicles in service',''],['Fleet',''],['Spend per truck',''],
 ['Capture',''],['Uncaptured',''],['Largest family gap','l'],['Capture trend','l'],['Defection','l'],
 ['Breadth',''],['Exposure',''],['Warranty',''],['Competitive parts',''],['Stock','']
];
function storyTag(code){ return K.story.indexOf(code)>=0; }
function leagueHTML(){
  /* Counted before the row loop: the share tooltip needs it, so it cannot be a
     let-declaration further down (that threw a ReferenceError in the dealer direction). */
  const nDlr = K.dbs.filter(d=>d.inModel && d.dealer).length;
  let h='<div class="tbl"><table class="league"><thead><tr>'+
    COLS.map((c,i)=>'<th class="'+(c[1]||'')+'">'+c[0]+'</th>').join('')+'</tr></thead><tbody>';
  const maxCy = Math.max.apply(null, K.dbs.map(d=>d.inModel?d.cy:0));
  // Share of the modelled network, on the same billed figure the column shows, so the
  // rows and the footer total always agree whatever the toggles are set to.
  let modTotal=0;
  K.dbs.forEach(d=>{ if(!d.inModel) return; const v=view(d); if(typeof v.eur==='number') modTotal+=v.eur; });
  K.dbs.forEach(d=>{
    const v = view(d);
    const cap = d.cap, tr = d.traj, df = d.defn, br = d.breadth;
    const famGapTop = d.famGap ? d.famGap.slice().sort((a,b)=>b.gap-a.gap)[0] : null;
    h+='<tr class="'+(storyTag(d.code)?'story ':'')+(d.inModel?'':'cis')+'">';
    h+='<td class="l"><b>'+d.label+'</b>'+(storyTag(d.code)?' <span class="chip r">story</span>':'')+
       '<br><span class="tiny">'+d.name+'</span></td>';
    h+='<td>'+tip(T('parts billed to this distributor in the selected period, from the billing fact, attributed through the distributor code map.',
        'MIDI trade and the 2026 rows, which carry customer names instead of distributor codes.'+
        (v.warrNoSplit? ' The sales-to-dealer file has no warranty column, so this figure still contains warranty parts even though warranty excluded is selected.':''),
        SET()), (v.eur==='na'? '<span class="na">no file</span>' : eurL(v.eur)))+'<br>'+bar(d.cy,maxCy,'')+'</td>';
    const share = (d.inModel && typeof v.eur==='number' && modTotal)? pct(v.eur/modTotal*100,1)
                : '<span class="na">outside model</span>';
    h+='<td>'+tip(T('this distributor\u2019s share of the '+(MODE.dir==='dlr'? nDlr+ ' distributors that file sales to dealer' : '18 modelled distributors')+
        ', on the billed figure in this row for the selected period.',
        'the four CIS markets, which sit outside the modelled denominators'+(MODE.dir==='dlr'? '; the twelve distributors with no sales-to-dealer file.' : '.'),
        SET()), share)+'</td>';
    h+='<td>'+tip(T('vehicles in service (UIO) for 2025, the denominator behind spend per truck and capture.',
        'the 2026\u20132030 forecast, which is withdrawn; the four CIS markets have no denominator.',
        'Basis: '+d.uioSrc+'.'),
        num(d.uio))+'</td>';
    h+='<td>'+tip(T('fleet direction: 2025 against 2024 vehicles in service.',
        'new registrations, scrappage or the model\u2019s own survival curve: this is the level change only.'),
        arrow(d.uio,d.uio24))+'</td>';
    h+='<td>'+tip(T('parts billed \u00f7 vehicles in service.',
        'dealer inventory movements; the four CIS markets. '+(v.mileageMeasured? 'Measured distance '+num(v.mileage)+' km/yr is available for this market.':'No measured distance for this market, the model assumes a flat 20,000 km/yr.'),
        SET()+' Direction: '+LBL_D[MODE.dir]+'.'),
        (v.spu? eurL(v.spu) : '<span class="na">unavailable</span>'))+'</td>';
    h+='<td>'+cyOnly(tip(T('units billed \u00f7 units the maintenance model expects, 2025, weighted across 14 service families.',
        'the flat \u20ac250-per-truck markets\u2019 ceiling precision; parts outside the 14 families.',
        SET()+' A rate above 100% means more was billed than the model expects.'),
        (cap? cap.rate.toFixed(1)+'%' : '<span class="na">n/a</span>')))+'</td>';
    h+='<td>'+cyOnly(tip(T('modelled demand \u2212 parts billed, across the 14 service families, in euro.',
        'the four CIS markets; the ceiling\u2019s accuracy in the flat-target markets.',
        SET()+' Ceiling, not forecast.'),
        (famGapTop? eurL(d.famGap.reduce((a,b)=>a+b.gap,0)) : '<span class="na">n/a</span>')))+'</td>';
    h+='<td class="l">'+cyOnly(tip(T('the service family with the largest euro not billed in 2025.',
        'families outside the 14; the flat-target markets.'),
        (famGapTop? famGapTop.fam+' \u00b7 '+eurL(famGapTop.gap)+' <span class="tiny">'+(100-famGapTop.rate).toFixed(0)+'% unbought</span>' : '\u2013')))+'</td>';
    h+='<td class="l">'+cyOnly(tip(T('least-squares slope of the annual capture rate, in percentage points per year, for the worst-fitting family (2023\u20132025).',
        '2026, whose rows are partial; families with fewer than three annual points.',
        SET()), (function(){ const ok=(tr||[]).filter(f=>f && isFinite(f.slope) && isFinite(f.r2));
          if(!ok.length) return '<span class="na">no slope</span>';
          const w=ok.slice().sort((a,b)=>a.slope-b.slope)[0];
          return (w.dec? '<span class="chip r">falling</span> ':'<span class="chip g">rising</span> ')+
            '<span class="tiny">'+w.fam.replace(/_/g,' ')+' '+w.slope.toFixed(2)+' pp/yr, R\u00b2 '+w.r2.toFixed(2)+'</span>'; })()))+'</td>';
    h+='<td class="l">'+cyOnly(tip(T('distributor-and-family combinations silent for longer than their own median reorder gap, as at the March 2026 data horizon. The euro is the trailing twelve months billed on that family.',
        'dealer-level dormancy: the file carries no customer names on this page.',
        SET()), (df? '<span class="chip '+(df.n_alert>1?'r':'a')+'">'+df.n_alert+' quiet</span> <span class="tiny">'+eurL(df.silent_eur)+'</span><br><span class="tiny">'+
          df.tops.slice(0,2).map(t=>t.fam.replace(/_/g,' ')+' silent '+t.silent.toFixed(0)+' mo, '+(t.gap? (t.silent/t.gap).toFixed(1)+'\u00d7 its '+t.gap.toFixed(0)+'-month gap':'no gap')).join('<br>')+'</span>'
          : '<span class="na">none flagged</span>')))+'</td>';
    h+='<td>'+cyOnly(tip(T('number of distinct goods-classification groups (the 3-digit part-class prefix) billed at least once in 2025.',
        'part numbers that carry no goods classification: '+K.net.figcov.toFixed(1)+'% of billed value is classified, so '+ (100-K.net.figcov).toFixed(1)+'% carries none.',
        SET()), (br? br.cy.length : '\u2013')))+'</td>';
    h+='<td>'+cyOnly(tip(T('share of billed value on part numbers the aftersales item master classifies as highly exposed to the independent aftermarket, with the weighted genuine-over-competitive price premium beside it.',
        'the pricing-risk layer, which returned a null on backtest; part numbers with no classification.',
        SET()), ((d.aim? (d.aim.risk).toFixed(2)+'% risk' : '\u2013')+
        (d.prem? ' <span class="tiny">+'+d.prem.prem.toFixed(0)+'% price</span>' : ''))))+'</td>';
    h+='<td>'+tip(T('warranty parts in euro \u00f7 total parts billed, for the selected period.',
        'the four CIS markets, which have no warranty data at all. '+(MODE.period==='fy'?'Fiscal figure comes from the fiscal warranty expense file.':'Calendar figure comes from the spend file.'),
        SET()), (v.warr!==null&&v.warr!==undefined? eurL(v.warr)+' <span class="tiny">'+(d.warrShare? d.warrShare.toFixed(1)+'%':'')+'</span>'
          : '<span class="na">no warranty data</span>'))+'</td>';
    h+='<td>'+tip(T('share of all parts billed that is Competitive (best-value) parts, in euro, and the share of the contested euro that went to Competitive parts.',
        'the four CIS markets in the modelled denominators; the contested classification covers only part numbers with a mapped twin.',
        SET()), (d.bvp? d.bvp.pct.toFixed(2)+'% <span class="tiny">contested capture '+(d.bvp.capr===null?'n/a':d.bvp.capr.toFixed(0)+'%')+'</span>' : '\u2013'))+'</td>';
    h+='<td>'+tip(T('what the distributor sold on to its dealers minus what we invoiced it, for the same calendar year: the indicator of stock the distributor is sitting on.',
        'the twelve distributors with no sales-to-dealer file; the fiscal view, which the file cannot support.',
        SET()), (d.dealer? (function(){ const s=d.dealer.eur-d.cy;
          return '<span class="'+(s>=0?'pos':'neg')+'">'+eurL(s)+'</span><br><span class="tiny">'+d.dealer.ents+' dealers</span>'; })()
        : '<span class="na">no file</span>'))+'</td>';
    h+='</tr>';
  });
  const mod = K.dbs.filter(d=>d.inModel);
  /** @type {any} */
  let tBilled=0, tWarr=0, tBvp=0, tTot=0, nBilled=0, dlrSum=0, nDlrFile=0;
  mod.forEach(d=>{ const v=view(d);
    if(typeof v.eur==='number'){ tBilled+=v.eur; nBilled++; }
    if(typeof v.warr==='number') tWarr+=v.warr;
    if(d.bvp){ tBvp+=d.bvp.bvp; tTot+=d.bvp.rev; }
    if(d.dealer){ dlrSum+=d.dealer.eur; nDlrFile++; } });
  const dlrNote = (MODE.period==='cy')? eurL(dlrSum)+' <span class="tiny">'+nDlrFile+' of 18 file</span>' : '<span class="na">n/a</span>';
  const spuFoot = (MODE.dir==='db' && nBilled)? eurL(tBilled/K.net.uio) : '<span class="na">n/a</span>';
  const bvpFoot = tTot? (tBvp/tTot*100).toFixed(2)+'%' : '\u2013';
  const warrFoot = (MODE.period==='cy')
     ? eurL(K.net.warrCy)
     : (K.net.warrFy? eurL(K.net.warrFy) : '<span class="na">n/a</span>');
  h+='</tbody><tfoot><tr><td class="l">Network, 18 modelled distributors</td>'+
     '<td>'+(nBilled? eurL(tBilled) : '<span class="na">n/a</span>')+'</td><td>'+(nBilled?'100.0%':'<span class="na">n/a</span>')+'</td>'+
     '<td>'+num(K.net.uio)+'</td><td>'+arrow(K.net.uio,K.net.uio24)+'</td>'+
     '<td>'+spuFoot+'</td><td>'+cyOnly(K.net.capRate.toFixed(1)+'%')+'</td><td>'+cyOnly(eurL(K.net.capGap))+'</td>'+
     '<td class="l">clutch disc, the largest family</td><td class="l">see chart</td>'+
     '<td class="l">'+cyOnly(K.net.defN+' quiet rows \u00b7 '+eurL(K.net.defEur))+'</td><td>'+cyOnly(K.net.breadthNet+' of '+K.net.breadthAll)+'</td>'+
     '<td>'+cyOnly('see chart')+'</td><td>'+warrFoot+'</td><td>'+cyOnly(bvpFoot)+'</td>'+
     '<td>'+dlrNote+'</td></tr></tfoot></div>';
  h+='<p class="tiny">Four CIS markets (Ukraine, Armenia, Kazakhstan, Palestine) bill without a fleet denominator and have no warranty data, so they sit outside every modelled figure on this page and are listed with the other 18 rather than inside the league total above. 2026 rows are excluded from every trend: from April 2026 the billing table stores customer names instead of distributor codes, so no calendar or fiscal 2026 view can be attributed. Capture, uncaptured value, trend, breadth, exposure and price premium are calendar-tagged sources and keep their Calendar 2025 value on the fiscal toggle, marked CY25.</p>';
  return h;
}
"""
print('JS part 2 added, total %d bytes' % len(JS))

# ---- league table is re-emitted here by replacement (kept single copy in JS part 2)
JS = JS.replace('__LEAGUE_DUP__', '')

JS += r"""
/* =================================================================== charts */
function svgOpen(w,h){ return '<div class="svgwrap"><svg viewBox="0 0 '+w+' '+h+'" width="'+w+'" height="'+h+
  '" role="img" preserveAspectRatio="xMinYMin meet">'; }

/* G1 -- which markets spend most per truck per year? */
function cSpend(){
  // The same live figure as the league and the hero: the period's parts billed on the
  // selected warranty basis, over the 2025 fleet. The spend file carries a narrower
  // reconciled book, so quoting its spend_per_unit_eur here would contradict the league.
  const rows = K.dbs.filter(d=>d.inModel && d.spu!==null)
    .map(d=>({d:d, v:view(d).spu}))
    .filter(r=>r.v!==null && isFinite(r.v)).sort((a,b)=>b.v-a.v);
  if(!rows.length) return '<div class="chart"><h3>Which markets spend most per truck per year?</h3>'+
    '<p class="note">Unavailable in this setting: spend per truck is only computed on the ISZE \u2192 DB direction, because the six sales-to-dealer files carry a different fleet basis.</p></div>';
  const n=rows.length, bw=34, gap=10, x0=62, H=300, W=x0+ n*(bw+gap)+30;
  const mx=Math.max.apply(null,rows.map(r=>r.v))*1.14, base=H-46;
  const med = median(rows.map(r=>r.v));
  let s=svgOpen(W,H);
  [0,.25,.5,.75,1].forEach(f=>{ const y=base-f*(base-24);
    s+='<line x1="'+x0+'" y1="'+y.toFixed(1)+'" x2="'+(W-24)+'" y2="'+y.toFixed(1)+'" stroke="#e6e0d2"/>'+
       '<text x="'+(x0-6)+'" y="'+(y+3.5).toFixed(1)+'" text-anchor="end" font-size="9.5" fill="#8b8272">\u20ac'+Math.round(mx*f)+'</text>'; });
  s+='<line x1="'+(x0+(rows.findIndex(r=>r.v<med)+(rows.findIndex(r=>r.v<med)<0?n:0))*(bw+gap)-gap/2).toFixed(1)+
     '" y1="24" x2="'+(x0+(rows.findIndex(r=>r.v<med)+(rows.findIndex(r=>r.v<med)<0?n:0))*(bw+gap)-gap/2).toFixed(1)+
     '" y2="'+base+'" stroke="#c0552d" stroke-dasharray="4 3"/>';
  rows.forEach((r,i)=>{
    const x=x0+i*(bw+gap), h=Math.max(2,(r.v/mx)*(base-24));
    const story = K.story.indexOf(r.d.code)>=0;
    s+='<rect x="'+x+'" y="'+(base-h).toFixed(1)+'" width="'+bw+'" height="'+h.toFixed(1)+
       '" fill="'+(story?'#c0552d':'#15233c')+'"><title>'+r.d.label+': \u20ac'+r.v.toFixed(0)+' per truck per year'+
       (r.d.mileage? ' on '+Math.round(r.d.mileage[0]).toLocaleString('en-GB')+' measured km/yr':' on the flat 20,000 km/yr assumption')+'</title></rect>';
    s+='<text x="'+(x+bw/2)+'" y="'+(base-h-4).toFixed(1)+'" text-anchor="middle" font-size="9.5" fill="#15233c">\u20ac'+Math.round(r.v)+'</text>';
    s+='<text x="'+(x+bw/2)+'" y="'+(base+13)+'" text-anchor="middle" font-size="9.5" fill="#3d372b" transform="rotate(0)">'+r.d.label.slice(0,8)+'</text>';
    s+='<text x="'+(x+bw/2)+'" y="'+(base+25)+'" text-anchor="middle" font-size="8.5" fill="#8b8272">'+(r.d.mileage?'meas.':'flat')+'</text>';
  });
  s+='<text x="'+x0+'" y="14" font-size="10" fill="#c0552d">network median \u20ac'+Math.round(med)+'</text>';
  s+='</svg></div>';
  return '<div class="chart"><h3>Which markets spend most per truck per year, and which under-spend their fleet?</h3>'+
   '<p class="cap">Parts billed on the billing fact per vehicle in service, '+LBL_P[MODE.period]+', '+LBL_W[MODE.warr]+
   ', over the 2025 fleet. Bar labels say whether the market\u2019s annual distance is measured or the flat 20,000 km/yr assumption. '+
   'A tall bar is a larger book per truck, not a better-run market.</p>'+s+'</div>';
}
function median(a){ const b=a.slice().sort((x,y)=>x-y); const m=Math.floor(b.length/2);
  return b.length%2? b[m] : (b[m-1]+b[m])/2; }

/* G2 -- how much of last year's growth was more trucks, how much price? */
function cGrowth(){
  const leg = MODE.period==='cy' ? 'splitCy' : 'splitFy';
  const rows = K.dbs.filter(d=>d.inModel).map(d=>({d:d, s:d[leg]==='na'? null : d[leg]}))
    .filter(r=>r.s && (Math.abs(r.s.vol)+Math.abs(r.s.price)+Math.abs(r.s.end-r.s.base))>0);
  if(!rows.length) return '<div class="chart"><h3>Was last year\u2019s parts growth more trucks, or price?</h3>'+
    '<p class="note">Unavailable in this setting. The only source for this split is calendar-tagged (2024 \u2192 2025) and there is no fiscal equivalent here.</p></div>';
  rows.sort((a,b)=>Math.abs(b.s.vol+b.s.price)-Math.abs(a.s.vol+a.s.price));
  const bw=30, gap=26, x0=76, H=280, W=x0+rows.length*(bw*2+gap)+30, base=H-52;
  const mx=Math.max.apply(null,rows.map(r=>Math.max(Math.abs(r.s.vol),Math.abs(r.s.price))))*1.2;
  let s=svgOpen(W,H);
  s+='<line x1="'+x0+'" y1="'+(base/1)+'" x2="'+(W-24)+'" y2="'+(base/1)+'" stroke="#15233c"/>';
  const zy=base/1;
  const sy=v=>zy-(v/mx)*(zy-30)/1;
  [1,.5,-.5,-1].forEach(f=>{ const y=zy-f*(zy-30)*0.9;
    s+='<line x1="'+x0+'" y1="'+y.toFixed(1)+'" x2="'+(W-24)+'" y2="'+y.toFixed(1)+'" stroke="#e6e0d2"/>'+
      '<text x="'+(x0-6)+'" y="'+(y+3.5).toFixed(1)+'" text-anchor="end" font-size="9" fill="#8b8272">'+eur(mx*f*0.9)+'</text>'; });
  rows.forEach((r,i)=>{
    const x=x0+i*(bw*2+gap);
    [['vol','#15233c','volume, trucks'],['price','#c0552d','price']].forEach((p,j)=>{
      const v=r.s[p[0]]; const y=v>=0? sy(v) : zy; const h=Math.abs(sy(v)-zy);
      s+='<rect x="'+(x+j*(bw+3))+'" y="'+y.toFixed(1)+'" width="'+bw+'" height="'+Math.max(1,h).toFixed(1)+
         '" fill="'+p[1]+'"><title>'+r.d.label+' \u00b7 '+p[2]+' '+eur(v)+'</title></rect>';
    });
    s+='<text x="'+(x+bw)+'" y="'+(base/1+14)+'" text-anchor="middle" font-size="9.5" fill="#3d372b">'+r.d.label.slice(0,9)+'</text>';
  });
  s+='<text x="'+x0+'" y="16" font-size="10" fill="#15233c">above the line: growth</text>';
  s+='<text x="'+x0+'" y="'+(zy+12)+'" font-size="10" fill="#8b8272">the line: no change</text>';
  s+='<text x="26" y="'+(zy/2)+'" font-size="10" fill="#3d372b" transform="rotate(-90 26 '+(zy/2)+')" text-anchor="middle">euro of change</text>';
  s+='</svg></div>';
  const noMix = K.dbs.filter(d=>d.inModel).length === rows.length;
  return '<div class="chart"><h3>Was last year\u2019s growth more trucks, or price?</h3>'+
   '<p class="cap">Each distributor decomposed into two measurable legs: volume (more trucks buying) and price (a higher average price on the same part). '+
   'The market-mix leg is <b>not shown</b>: the source\u2019s mix column is a hard zero, which means the two other legs absorb it, not that mix did not move. '+
   (MODE.period==='fy'? 'Fiscal figures are recomputed from the billing fact on the same two-leg formula, FY24/25 \u2192 FY25/26.' : 'Calendar figures come from the 2024 \u2192 2025 waterfall.')+
   '</p>'+s+'</div>';
}
/* G3 -- three-way capture bar */
function cCapture(){
  const rows=K.dbs.filter(d=>d.inModel && d.famGap).slice().sort((a,b)=>(a.cap.rate)-(b.cap.rate));
  if(!rows.length) return '';
  const H=26*rows.length+58, W=940, x0=112, w=W-x0-120;
  let s=svgOpen(W,H);
  rows.forEach((d,i)=>{
    const y=24+i*26, t=d.cap;
    const gq = t.exp? (t.act/Math.max(t.exp,1)) : 0;
    const gs=Math.min(1,Math.max(0,gq));
    s+='<rect x="'+x0+'" y="'+y+'" width="'+w.toFixed(1)+'" height="17" fill="#efe9dc" stroke="#ddd6c6"/>';
    s+='<rect x="'+x0+'" y="'+y+'" width="'+(w*gs).toFixed(1)+'" height="17" fill="'+(gs<0.35?'#c0552d':'#15233c')+
       '"><title>'+d.label+': '+t.act.toFixed(0)+' of '+t.exp.toFixed(0)+' expected service parts billed = '+(gs*100).toFixed(1)+
       '%. The not-bought remainder is '+eur(t.gap)+' across 14 service families on '+num(d.uio)+' vehicles in service.</title></rect>';
    s+='<text x="'+(x0-8)+'" y="'+(y+12.5)+'" text-anchor="end" font-size="10.5" fill="#15233c">'+d.label+'</text>';
    s+='<text x="'+(x0+w+8)+'" y="'+(y+12.5)+'" font-size="10.5" fill="'+(gs<0.35?'#c0552d':'#3d372b')+'">'+
       (gs*100).toFixed(0)+'% \u00b7 '+eur(t.gap)+' unbought</text>';
  });
  s+='<text x="'+x0+'" y="14" font-size="10" fill="#3d372b">billed as a share of the service parts the model expects \u2014 the pale remainder is never bought</text>';
  s+='</svg></div>';
  return '<div class="chart"><h3>Of the service parts the model expects, how much did each distributor bill \u2014 and how much was never bought at all?</h3>'+
   '<p class="cap">Units billed against units the maintenance model expects, on the same fleet, 14 service families, 2025. '+
   'Ireland above 100% is the model\u2019s ceiling under-running on a market with a small truck fleet, not double-counting. '+
   'The euro beside each bar is the value of the pale remainder.</p>'+s+
   cyChart('the capture source is built on calendar years, so there is no fiscal equivalent of the expected units.')+
   '<p class="tiny">Denominator: vehicles in service, shown per row in the league. The expected units rest on an annual distance per market \u2014 measured where a measurement exists, otherwise the flat 20,000 km/yr assumption. IUK\u2019s expected demand falls materially once its measured 14,494 km/yr is applied instead.</p>'+
   '</div>';
}

/* G4 -- capture trend, small multiples of the family slopes */
function cTrend(){
  const dbs=K.dbs.filter(d=>d.inModel && d.traj);
  if(!dbs.length) return '';
  let h='<div class="chart"><h3>Which distributor-and-family captures are rising, and which are falling?</h3>'+
   '<p class="cap">Least-squares slope of the annual capture rate in percentage points per year, 2023\u20132025, one panel per distributor. '+
   'Terracotta means the fit is a fall wide enough to flag; the number is the slope and R\u00b2. A family with fewer than three annual points, or with no slope in the source, is left blank.</p>'+
   '<div class="mini">';
  let plotted=0;
  dbs.forEach(d=>{
    const fams=(d.traj||[]).filter(f=>f && typeof f.slope==='number' && isFinite(f.slope) && typeof f.r2==='number' && isFinite(f.r2));
    if(!fams.length) return;
    h+='<div class="m"><div class="h"><b>'+d.label+'</b><span>'+fams.length+' of '+(d.traj.length)+' families</span></div>';
    fams.slice().sort((a,b)=>a.slope-b.slope).slice(0,7).forEach(f=>{
      const wpx=Math.min(46,Math.max(2,Math.abs(f.slope)*9));
      const col=f.slope<0? (f.dec?'#c0552d':'#a33217') : (f.slope>0.03?'#1f6b45':'#3d6b8c');
      plotted++;
      h+='<div class="v">'+tip(T('slope of the annual capture rate for '+f.fam.replace(/_/g,' ')+', 2023\u20132025: '+
        f.slope.toFixed(2)+' pp/yr, R\u00b2 '+f.r2.toFixed(2)+'.',
        MODE.period==='fy'?'the fiscal view: the trajectory source is calendar-tagged only.':'2026 rows, which are partial (source has no fiscal basis).',
        'Setting: '+LBL_P[MODE.period]+'.'),
        '<span style="float:left;max-width:118px">'+f.fam.replace(/_/g,' ')+
        '</span><span style="float:right;color:'+col+';white-space:nowrap">('+f.slope.toFixed(1)+' pt) </span><span class="bar-mini" style="background:'+col+';width:'+wpx+'px;float:right;margin-left:4px"></span>')+'</div>';
    });
    h+='</div>';
  });
  if(!plotted) return '<div class="chart"><h3>Which distributor-and-family captures are rising, and which are falling?</h3>'+
    '<p class="note">No family carries a usable 2023\u20132025 slope in the source, so nothing is plotted. Families with a flat zero capture across all three years have no slope.</p></div>';
  h+='</div>'+(MODE.period==='fy'? '<p class="tiny"><b>Fiscal view unavailable for this chart:</b> the capture-trajectory source carries calendar years only, so the panels above remain calendar 2023\u20132025 even though the period toggle reads FY25/26.</p>':'')+
   '<p class="tiny">The seven steepest-falling families are shown per distributor, out of the families that carry a slope at all: 226 of the 252 distributor-family rows do, and 26 are flat-zero families with no slope to fit. Five family trends are formally flagged as declining, so this chart is mostly a picture of flat-to-slowly-rising capture rather than collapse.</p></div>';
  return h;
}

/* G5 -- uncaptured GPS value ladder */
function cGap(){
  const rows=K.dbs.filter(d=>d.inModel && d.famGap).map(d=>({d:d,g:d.famGap.reduce((a,b)=>a+b.gap,0)}))
    .sort((a,b)=>b.g-a.g);
  const H=22*rows.length+70, W=1000, x0=112, w=W-x0-190;
  const mx=Math.max.apply(null,rows.map(r=>r.g));
  let s=svgOpen(W,H);
  rows.forEach((r,i)=>{
    const y=26+i*22, bwv=(r.g/mx)*w;
    const top=r.d.famGap.slice().sort((a,b)=>b.gap-a.gap).slice(0,2);
    s+='<rect x="'+x0+'" y="'+y+'" width="'+bwv.toFixed(1)+'" height="15" fill="'+(i<3?'#c0552d':'#15233c')+
       '"><title>'+r.d.label+' \u00b7 '+eur(r.g)+' unbought across 14 service families. Largest: '+
       top.map(t=>t.fam.replace(/_/g,' ')+' '+eur(t.gap)).join('; ')+'. Fleet: '+num(r.d.uio)+' vehicles in service.</title></rect>';
    s+='<text x="'+(x0-8)+'" y="'+(y+11.5)+'" text-anchor="end" font-size="10.5" fill="#15233c">'+r.d.label+'</text>';
    s+='<text x="'+(x0+bwv+8)+'" y="'+(y+11.5)+'" font-size="10.5" fill="#3d372b">'+eur(r.g)+
       ' <tspan fill="#8b8272">\u00b7 '+top.map(t=>t.fam.replace(/_/g,' ')).join(', ')+'</tspan></text>';
    s+='<text x="'+(x0+bwv+8)+'" y="'+(y+11.5)+'" font-size="10.5" fill="#3d372b" opacity="0">.</text>';
  });
  s+='<text x="'+x0+'" y="14" font-size="10" fill="#3d372b">euro of modelled service-part demand never billed, and the family carrying most of it</text>';
  s+='</svg></div>';
  return '<div class="chart"><h3>Where is the unmade parts revenue concentrated?</h3>'+
   '<p class="cap">Modelled demand less parts billed, in euro, 14 service families, 2025, per distributor, on that distributor\u2019s own fleet. '+
   'This is a ceiling, not a forecast: the top bar is also the market with the largest fleet, so the fleet denominator travels with every row in the league table.</p>'+s+
   cyChart('the opportunity and ceiling sources carry calendar years only.')+'</div>';
}

/* G6 -- UIO direction slope */
function cUio(){
  const rows=K.dbs.filter(d=>d.inModel && d.uio && d.uio24);
  if(!rows.length) return '';
  const H=430, W=560, x0=110, x1=420;
  const mx=Math.max.apply(null,rows.map(r=>Math.max(r.uio,r.uio24)))*1.06;
  const sy=v=>H-60-(v/mx)*(H-110);
  let s='<div class="svgwrap"><svg viewBox="0 0 '+W+' '+H+'" width="'+W+'" height="'+H+'" role="img">';
  s+='<text x="'+x0+'" y="26" text-anchor="middle" font-size="11" fill="#15233c">2024</text>';
  s+='<text x="'+x1+'" y="26" text-anchor="middle" font-size="11" fill="#15233c">2025</text>';
  rows.forEach(r=>{
    const up=r.uio>=r.uio24;
    s+='<line x1="'+x0+'" y1="'+sy(r.uio24).toFixed(1)+'" x2="'+x1+'" y2="'+sy(r.uio).toFixed(1)+
       '" stroke="'+(up?'#1f6b45':'#c0552d')+'" stroke-width="'+(r.uio>20000?2.4:1.3)+'" opacity="0.85"/>';
    s+='<circle cx="'+x0+'" cy="'+sy(r.uio24).toFixed(1)+'" r="2.6" fill="#15233c"/>';
    s+='<circle cx="'+x1+'" cy="'+sy(r.uio).toFixed(1)+'" r="2.6" fill="#15233c"/>';
    s+='<text x="'+(x0-7)+'" y="'+(sy(r.uio24)+3.5).toFixed(1)+'" text-anchor="end" font-size="10" fill="#3d372b">'+r.label+
       ' '+num(r.uio24)+'</text>';
    s+='<text x="'+(x1+7)+'" y="'+(sy(r.uio)+3.5).toFixed(1)+'" font-size="10" fill="'+(up?'#1f6b45':'#973f1c')+'">'+
       num(r.uio)+' '+((r.uio-r.uio24)/r.uio24*100).toFixed(1)+'%</text>';
    s+='<title>'+r.label+': '+num(r.uio24)+' \u2192 '+num(r.uio)+' vehicles in service</title>';
  });
  s+='</svg></div>';
  return '<div class="chart g2w"><h3>Is each market\u2019s fleet growing or shrinking?</h3>'+
   '<p class="cap">Vehicles in service, 2024 against 2025. Green rising, terracotta falling. The 2026\u20132030 forecast is deliberately absent: '+
   'it is overstated and awaits correction.</p>'+s+
   cyChart('vehicles in service is an annual stock count, so there is no fiscal split of it.')+'</div>';
}

/* G7 -- dormancy euro */
function cDefect(){
  const rows=K.dbs.filter(d=>d.defn).map(d=>({d:d, g:d.defn.silent_eur})).sort((a,b)=>b.g-a.g);
  if(!rows.length) return '';
  const mx=Math.max.apply(null,rows.map(r=>r.g));
  let h='<div class="chart"><h3>Where have we gone quiet for longer than the normal reorder gap?</h3>'+
   '<p class="cap">Distributor-and-family pairs silent past their own median reorder rhythm, as at the March 2026 data horizon. '+
   'Each euro is the trailing twelve months actually billed on that family, so this is the run-rate at risk, not a lost-order claim.</p>'+
   '<div class="tbl"><table style="min-width:760px"><thead><tr><th class="l">Distributor</th><th class="l">Service family</th>'+
   '<th>Normal gap</th><th>Silent</th><th>Multiple</th><th>Last order</th><th>Trailing 12m billed</th><th class="l">Value at risk</th></tr></thead><tbody>';
  const all=[];
  rows.forEach(r=>r.d.defn.tops.forEach(t=>all.push({d:r.d,t:t})));
  all.sort((a,b)=>b.t.eur-a.t.eur);
  all.slice(0,22).forEach(x=>{
    h+='<tr><td class="l">'+x.d.label+'</td><td class="l">'+x.t.fam.replace(/_/g,' ')+'</td>'+
       '<td>'+x.t.gap.toFixed(0)+' mo</td><td>'+x.t.silent.toFixed(0)+' mo</td>'+
       '<td>'+(x.t.gap? (x.t.silent/x.t.gap).toFixed(1)+'\u00d7' : '\u2013')+'</td>'+
       '<td>'+x.t.last+'</td><td>'+eurL(x.t.eur)+'</td>'+
       '<td class="l">'+tip(T('euro billed on this family in the twelve months to March 2026, allocated from the billing fact; '+
         'the gap is the median months between orders in the family\u2019s active history.',
         'lost revenue: a quiet pair may be ordering elsewhere or may not need the part.',SET()),
         bar(x.t.eur,mx,'t',150))+'</td></tr>';
  });
  h+='</tbody></table></div>'+
   '<p class="tiny">'+K.net.defN+' of '+K.net.defRows+' distributor-and-family combinations across the network carry the flag, on '+eurL(K.net.defEur)+
   ' of trailing twelve-month billing. Customer-level dormancy ('+K.net.custN+' of '+K.net.custRows+
   ' rows) exists in the source but is not shown here: this page carries no customer names.</p>'+
   cyChart('the dormancy flag is read at a March 2026 horizon from calendar-tagged order history.')+'</div>';
  return h;
}

/* G8 -- basket breadth ranking + family presence */
function cBreadth(){
  const rows=K.dbs.filter(d=>d.inModel && d.breadth && (d.breadth.cy.length||d.breadth.fy.length))
    .map(d=>({d:d, n:(MODE.period==='fy'? d.breadth.fy.length : d.breadth.cy.length)})).sort((a,b)=>b.n-a.n);
  if(!rows.length) return '';
  const perLbl = MODE.period==='fy'? 'April 2025 to March 2026' : 'calendar 2025';
  const maxN=296, H=rows.length*22+60, W=760, x0=112, w=W-x0-70;
  let s=svgOpen(W,H);
  rows.forEach((r,i)=>{ const y=22+i*22, bwv=(r.n/maxN)*w;
    s+='<rect x="'+x0+'" y="'+y+'" width="'+bwv.toFixed(1)+'" height="15" fill="'+(r.n<120?'#c0552d':'#15233c')+
       '"><title>'+r.d.label+' billed at least once in '+r.n+' of the 296 goods-classification groups catalogued, '+perLbl+'.</title></rect>';
    s+='<text x="'+(x0-8)+'" y="'+(y+11.5)+'" text-anchor="end" font-size="10.5" fill="#15233c">'+r.d.label+'</text>';
    s+='<text x="'+(x0+bwv+8)+'" y="'+(y+11.5)+'" font-size="10.5" fill="#3d372b">'+r.n+' of 296</text>'; });
  s+='<text x="'+x0+'" y="12" font-size="10" fill="#3d372b">distinct goods-classification groups bought at least once, '+perLbl+'</text>';
  s+='</svg></div>';
  const G7=['brakes','cab','clutch','electrical','engine_cooling','filters','suspension'];
  const GL={brakes:'Brakes',cab:'Cab',clutch:'Clutch & driveline',electrical:'Electrical',
    engine_cooling:'Engine & cooling',filters:'Filters',suspension:'Suspension & chassis'};
  let hm='<div class="tbl"><table style="min-width:760px"><thead><tr><th class="l">Distributor</th>'+
    G7.map(g=>'<th>'+GL[g]+'</th>').join('')+'</tr></thead><tbody>';
  K.dbs.filter(d=>d.inModel).forEach(d=>{
    const have=new Set((d.famBvp||[]).map(f=>f.fam));
    const src={brakes:'Brakes',cab:'Cab',clutch:'Clutch & driveline',electrical:'Electrical',
      engine_cooling:'Engine & cooling',filters:'Filters',suspension:'Suspension & chassis'};
    hm+='<tr><td class="l">'+d.label+'</td>';
    G7.forEach(g=>{
      const f=(d.famBvp||[]).find(x=>src[g]===x.fam);
      hm+='<td>'+(f? tip(T('parts billed in the '+src[g]+' group in 2025: '+eur(f.total)+', of which Competitive parts '+eur(f.bvp)+
        ' ('+(f.total? (f.bvp/f.total*100).toFixed(1):'0')+'%).',
        'groups with no billed line at all: nothing was bought, which the file cannot distinguish from an unmapped part number.',SET()),
        '<span class="chip '+(f.total>1e6?'g':(f.total>1e5?'a':'r'))+'">'+eur(f.total)+'</span>')
        : '<span class="chip n" data-tip="No billed line in this group in 2025 for this distributor. Shown as not bought rather than zero: a part number with no group mapping also lands here.\nSnapshot: '+K.snap+'.">not bought</span>')+'</td>';
    });
    hm+='</tr>';
  });
  hm+='</tbody></table></div>';
  const famLbl = MODE.period==='fy'? 'April 2025 to March 2026' : 'calendar 2025';
  return '<div class="chart"><h3>Which parts groups does each distributor actually buy?</h3>'+
   '<p class="cap">Left: how many of the 296 goods-classification groups each distributor billed at least once, '+famLbl+'. Right: the seven aftersales families and the euro billed in each, '+famLbl+'. '+
   'A market that never buys clutch parts has no clutch conversation to have.</p>'+
   '<div class="grid g2" style="grid-template-columns:minmax(0,1fr) minmax(0,1fr)">'+s+hm+'</div>'+
   '<p class="tiny">'+K.net.figcov.toFixed(1)+'% of billed value carries a goods classification; '+(100-K.net.figcov).toFixed(1)+
   '% does not, and those lines sit in no group.</p>'+
   cyChart('the seven-group family split is computed from a calendar-tagged source, so the group euro stays calendar even on the fiscal toggle.')+'</div>';
}

/* G9 -- exposure vs price position */
function cExpose(){
  const rows=K.dbs.filter(d=>d.inModel && d.aim && d.prem);
  if(!rows.length) return '';
  const W=760,H=440, x0=76, y0=H-64, w=W-x0-40, h=y0-40;
  const mxX=Math.max.apply(null,rows.map(r=>r.aim.risk))*1.25||1;
  const mxY=Math.max.apply(null,rows.map(r=>r.prem.prem))*1.15||1;
  let s=svgOpen(W,H);
  for(let i=1;i<=4;i++){ const x=x0+w*i/4; s+='<line x1="'+x+'" y1="40" x2="'+x+'" y2="'+y0+'" stroke="#e6e0d2"/>'+
    '<text x="'+x+'" y="'+(y0+14)+'" text-anchor="middle" font-size="9.5" fill="#8b8272">'+(mxX*i/4).toFixed(1)+'%</text>'; }
  for(let i=1;i<=4;i++){ const y=y0-h*i/4; s+='<line x1="'+x0+'" y1="'+y+'" x2="'+(x0+w)+'" y2="'+y+'" stroke="#e6e0d2"/>'+
    '<text x="'+(x0-6)+'" y="'+(y+3.5)+'" text-anchor="end" font-size="9.5" fill="#8b8272">+'+(mxY*i/4).toFixed(0)+'%</text>'; }
  const netX=K.net.aimRisk||0, netY=K.net.premMed;
  s+='<line x1="'+(x0+w*netX/mxX)+'" y1="40" x2="'+(x0+w*netX/mxX)+'" y2="'+y0+'" stroke="#c0552d" stroke-dasharray="4 3"/>';
  s+='<line x1="'+x0+'" y1="'+(y0-h*netY/mxY)+'" x2="'+(x0+w)+'" y2="'+(y0-h*netY/mxY)+'" stroke="#c0552d" stroke-dasharray="4 3"/>';
  s+='<text x="'+(x0+w*netX/mxX+4)+'" y="52" font-size="9.5" fill="#c0552d">network exposure</text>';
  s+='<text x="'+(x0+4)+'" y="'+(y0-h*netY/mxY-4)+'" font-size="9.5" fill="#c0552d">network median premium</text>';
  rows.forEach(r=>{
    const cx=x0+w*r.aim.risk/mxX, cy=y0-h*r.prem.prem/mxY, rad=4+Math.sqrt(r.cy)/26;
    s+='<circle cx="'+cx.toFixed(1)+'" cy="'+cy.toFixed(1)+'" r="'+rad.toFixed(1)+'" fill="'+(K.story.indexOf(r.code)>=0?'#c0552d':'#15233c')+'" fill-opacity="0.78"/>';
    s+='<text x="'+(cx+rad+3)+'" y="'+(cy+3.5)+'" font-size="9.5" fill="#3d372b">'+r.label+'</text>';
    s+='<title>'+r.label+': '+r.aim.risk.toFixed(2)+'% of billed value sits on part numbers the item master calls highly exposed, '+
      'and its genuine parts carry a weighted +'+r.prem.prem.toFixed(0)+'% premium over their Competitive twins on '+
      r.prem.units.toLocaleString('en-GB')+' units priced.</title>';
  });
  s+='<text x="'+(x0+w/2)+'" y="'+(y0+34)+'" text-anchor="middle" font-size="10.5" fill="#15233c">share of billed value exposed to the independent aftermarket</text>';
  s+='<text x="24" y="'+(40+h/2)+'" font-size="10.5" fill="#3d372b" transform="rotate(-90 24 '+(40+h/2)+')" text-anchor="middle">genuine premium over the Competitive twin</text>';
  s+='</svg></div>';
  return '<div class="chart"><h3>Where are we priced above the reference dealer price \u2014 and on parts the independent aftermarket can supply?</h3>'+
   '<p class="cap">Each bubble is a distributor: right is more of its book exposed, up is a larger genuine premium over the Competitive twin on the same part. '+
   'Bubble size is the size of the book. Bottom-left is the comfortable corner; top-right is where a customer can buy an alternative cheaply.</p>'+s+
   '<p class="tiny">Premium is unit-weighted across the families where both lines actually sold, so it is a price comparison on a sample, not a win rate. '+
   'The pricing-risk severity layer behind the exposure axis returned a null on backtest and is used here as classification only.</p>'+
   cyChart('both the exposure classification and the price-premium sample are calendar-tagged sources, so this scatter stays calendar 2025 on the fiscal toggle.')+'</div>';
}

/* G10 -- warranty share */
function cWarranty(){
  const rows=K.dbs.filter(d=>d.inModel && d.warrShare!==null).map(d=>({d:d,v:d.warrShare}))
    .sort((a,b)=>b.v-a.v);
  const perLbl = MODE.period==='fy'? 'April 2025 to March 2026' : 'calendar 2025';
  const H=rows.length*22+74, W=760, x0=112, w=W-x0-120;
  const mx=Math.max.apply(null,rows.map(r=>r.v))*1.15;
  let s=svgOpen(W,H);
  rows.forEach((r,i)=>{ const y=24+i*22, bwv=(r.v/mx)*w;
    s+='<rect x="'+x0+'" y="'+y+'" width="'+bwv.toFixed(1)+'" height="15" fill="'+(r.v>25?'#c0552d':'#15233c')+
       '"><title>'+r.d.label+': '+eur(r.d.warr)+' of warranty parts against '+eur(r.d.gpsTotal)+' billed = '+r.v.toFixed(1)+
       '% (calendar 2025). Warranty work is not a customer-paid parts sale.</title></rect>';
    s+='<text x="'+(x0-8)+'" y="'+(y+11.5)+'" text-anchor="end" font-size="10.5" fill="#15233c">'+r.d.label+'</text>';
    s+='<text x="'+(x0+bwv+8)+'" y="'+(y+11.5)+'" font-size="10.5" fill="#3d372b">'+r.v.toFixed(1)+'% \u00b7 '+eur(r.d.warr)+'</text>'; });
  s+='<text x="'+x0+'" y="14" font-size="10" fill="#3d372b">warranty parts as a share of total parts billed, '+perLbl+' \u2014 the depth of grey in the book</text>';
  s+='</svg></div>';
  return '<div class="chart"><h3>How much of what we bill is warranty work rather than customer-paid parts?</h3>'+
   '<p class="cap">Warranty parts in euro over total parts billed, calendar 2025. Network: '+eurL(K.net.warrCy)+' of '+eurL(K.net.gpsCyAll)+
   ' = '+K.net.warrShareAll.toFixed(1)+'% on the full spend file, which is the settled 14.6%; on the 18 modelled distributors alone the same '+
   eurL(K.net.warrCy)+' of '+eurL(K.net.gpsCy)+' reads '+K.net.warrShare.toFixed(1)+
   '%, because the four CIS markets add sales with no warranty beside them. A high share is not growth: it is our own cost of quality passing through the parts account.</p>'+s+
   '<p class="tiny">Unavailable for the four CIS markets (Ukraine, Armenia, Kazakhstan, Palestine): they have no warranty data at all, so they are absent from this chart rather than shown at zero. '+
   'The fiscal view reads '+eurL(K.net.warrFy)+' from the fiscal warranty expense file.</p>'+
   cyChart('the per-distributor warranty share is a calendar-2025 figure from the spend file; only the network total has a fiscal equivalent.')+'</div>';
}
"""
print('JS part 3 added, total %d bytes' % len(JS))

JS += r"""
/* ---- B1 two universes */
function cB1(){
  const bars=[
    {t:'All parts billed, billing fact', d:K.net.cyAttr, n:K.net.bvpFactCy, c:'#15233c',
     why:'Every part number billed to a distributor in the period, competitive parts identified by the catalogue flag. '+K.net.figcov.toFixed(1)+'% of billed value maps to a catalogue record, so the flag is read on almost the whole book.'},
    {t:'All parts billed, modelled book', d:K.net.ceilingCap, n:K.net.ceilingBvp, c:'#3d6b8c',
     why:'The 18 modelled distributors on the ceiling book: what we billed against a modelled target spend. This is the \u20ac30.76M denominator behind the agreed 3.5%.'},
    {t:'Service-part universe (14 families)', d:K.net.capRev, n:K.net.capBvpRev, c:'#1f6b45',
     why:'Only the 14 service families where the maintenance model makes competitive parts directly comparable: what we billed in those families.'},
    {t:'Service-part universe (7 groups)', d:K.net.mixUniv, n:K.net.mixBvp, c:'#c0552d',
     why:'The seven-group service-part cut the agreed 36.7% comes from: filters, brakes, clutch and driveline, suspension and chassis, electrical, engine and cooling, cab.'}
  ];
  const W=900, rowh=76, H=bars.length*rowh+52, x0=250, w=W-x0-150;
  const mx=Math.max.apply(null,bars.map(b=>b.n/b.d));
  let s='<div class="svgwrap"><svg viewBox="0 0 '+W+' '+H+'" width="'+W+'" height="'+H+'" role="img">';
  bars.forEach((b,i)=>{
    const y=30+i*rowh, share=b.n/b.d, bwv=(share/mx)*w;
    s+='<text x="'+(x0-10)+'" y="'+(y+13)+'" text-anchor="end" font-size="11.5" fill="#15233c">'+b.t+'</text>';
    s+='<text x="'+(x0-10)+'" y="'+(y+27)+'" text-anchor="end" font-size="10" fill="#8b8272">denominator '+eur(b.d)+'</text>';
    s+='<rect x="'+x0+'" y="'+(y+2)+'" width="'+w+'" height="20" fill="#efe9dc" stroke="#ddd6c6"/>';
    s+='<rect x="'+x0+'" y="'+(y+2)+'" width="'+bwv.toFixed(1)+'" height="20" fill="'+b.c+'"><title>'+b.t+
       ': competitive parts '+eur(b.n)+' of '+eur(b.d)+' = '+(share*100).toFixed(1)+'%. '+b.why+'</title></rect>';
    s+='<text x="'+(x0+bwv+9)+'" y="'+(y+17)+'" font-size="12" fill="'+b.c+'">'+(share*100).toFixed(1)+'% \u00b7 '+eur(b.n)+'</text>';
    s+='<text x="'+x0+'" y="'+(y+38)+'" font-size="9.5" fill="#5a5344">'+b.why.slice(0,140)+'</text>';
  });
  s+='<text x="'+x0+'" y="16" font-size="10" fill="#3d372b">competitive parts as a share of four different denominators</text>';
  s+='</svg></div>';
  return '<div class="chart"><h3>What share of our billing is Competitive parts \u2014 and which denominator is the real one?</h3>'+
   '<p class="cap">Both agreed universes are here, and they answer different questions. <b>3.5%</b> is the competitive-parts share of <b>everything we bill</b> on the modelled book. '+
   '<b>36.7%</b> is the share of the <b>service-part universe where competitive parts actually compete</b> \u2014 filters, brakes, clutch, suspension, electrical, engine and cooling, cab. '+
   'Neither is the wrong number, and neither is a target. The two middle bars are the same two questions asked of the billing fact, and they read differently because the universe definition differs: that difference is the whole reason the pair has to be published together.</p>'+s+
   '<p class="tiny">Competitive parts are the lower-priced Isuzu line that competes with the independent aftermarket. Genuine is the original-brand line. '+
   'The fiscal view on the billing-fact bars recomputes to '+eurL(K.net.bvpFactFy)+' of '+eurL(K.net.fyAttr)+' = '+K.net.bvpFactFyShare.toFixed(2)+
   '%; the ceiling and seven-group bars are calendar-tagged only.</p></div>';
}

/* ---- B2 addressable range bought */
function cB2(){
  const rows=K.dbs.filter(d=>d.inModel && d.b2).map(d=>({d:d,p:d.b2})).sort((a,b)=>b.p.pct-a.p.pct);
  const H=rows.length*22+74, W=820, x0=112, w=W-x0-190;
  let s=svgOpen(W,H);
  rows.forEach((r,i)=>{ const y=24+i*22, bwv=(r.p.pct/100)*w;
    s+='<rect x="'+x0+'" y="'+y+'" width="'+bwv.toFixed(1)+'" height="15" fill="'+(r.p.pct<40?'#c0552d':'#15233c')+
       '"><title>'+r.d.label+' buys '+r.p.selling+' of the '+r.p.pairs+' genuine-and-competitive part-number pairs mapped to it = '+
       r.p.pct.toFixed(1)+'%. A mapping exercise, not an assortment plan.</title></rect>';
    s+='<text x="'+(x0-8)+'" y="'+(y+11.5)+'" text-anchor="end" font-size="10.5" fill="#15233c">'+r.d.label+'</text>';
    s+='<text x="'+(x0+bwv+8)+'" y="'+(y+11.5)+'" font-size="10.5" fill="#3d372b">'+r.p.pct.toFixed(0)+
       '% <tspan fill="#8b8272">('+r.p.selling+' of '+r.p.pairs+' pairs)</tspan></text>'; });
  s+='<text x="'+x0+'" y="12" font-size="10" fill="#3d372b">share of that distributor\u2019s mapped competitive-parts range that it actually buys</text>';
  s+='</svg></div>';
  return '<div class="chart"><h3>Of the competitive part numbers each distributor could buy, how many does it actually buy?</h3>'+
   '<p class="cap">Each distributor\u2019s mapped genuine-and-competitive pairs, and how many of those pairs it billed at least once in the period. '+
   'The pair list is a part-number mapping, not an approved assortment: a part can be mapped to a market that never orders it for a real reason.</p>'+s+'</div>';
}

/* ---- B3 substitution */
function cB3(){
  const years=['2023','2024','2025'];
  const series=[{n:'Mapped pairs, all distributors', v:years.map(y=>K.suby[y].bvp/K.suby[y].tot*100), c:'#15233c', w:3}];
  const tops=K.dbs.filter(d=>d.inModel && d.suby && d.suby['2025'].tot>50000)
    .map(d=>({l:d.label, v:years.map(y=>d.suby[y].tot? d.suby[y].bvp/d.suby[y].tot*100 : null)}))
    .filter(s=>s.v.every(x=>x!==null)).sort((a,b)=>b.v[2]-a.v[2]).slice(0,6);
  const pal=['#c0552d','#1f6b45','#8a6a20','#3d6b8c','#8d8574','#5c2b13'];
  tops.forEach((t,i)=>series.push({n:t.l, v:t.v, c:pal[i%pal.length], w:1.4}));
  const W=760,H=360, x0=70,y0=H-56,w=W-x0-150,h=y0-34;
  const all=series.reduce((a,s)=>a.concat(s.v),[]);
  const lo=Math.max(0,Math.floor(Math.min.apply(null,all)/5)*5-2), hi=Math.ceil(Math.max.apply(null,all)/5)*5+2;
  let s=svgOpen(W,H);
  for(let i=0;i<=5;i++){ const y=y0-h*i/5;
    s+='<line x1="'+x0+'" y1="'+y.toFixed(1)+'" x2="'+(x0+w)+'" y2="'+y.toFixed(1)+'" stroke="#e6e0d2"/>'+
       '<text x="'+(x0-6)+'" y="'+(y+3.5).toFixed(1)+'" text-anchor="end" font-size="9.5" fill="#8b8272">'+
       (lo+(hi-lo)*i/5).toFixed(0)+'%</text>'; }
  years.forEach((y,i)=>{ const x=x0+w*i/2;
    s+='<line x1="'+x+'" y1="34" x2="'+x+'" y2="'+y0+'" stroke="#f0ebe0"/>';
    s+='<text x="'+x+'" y="'+(y0+16)+'" text-anchor="middle" font-size="10.5" fill="#3d372b">'+y+'</text>'; });
  series.forEach((se,si)=>{
    const pts=se.v.map((v,i)=>{ const x=x0+w*i/2, y=y0-h*(v-lo)/(hi-lo); return [x,y]; });
    s+='<polyline fill="none" stroke="'+se.c+'" stroke-width="'+se.w+'" points="'+
       pts.map(p=>p[0].toFixed(1)+','+p[1].toFixed(1)).join(' ')+'"/>';
    pts.forEach((p,i)=>{ s+='<circle cx="'+p[0].toFixed(1)+'" cy="'+p[1].toFixed(1)+'" r="'+(se.w>2?3.4:2.2)+'" fill="'+se.c+
      '"><title>'+se.n+' in '+years[i]+': '+se.v[i].toFixed(1)+'% of the euro on those pairs went to competitive parts.</title></circle>'; });
    const lp=pts[2];
    s+='<text x="'+(lp[0]+8)+'" y="'+(lp[1]+3.5)+'" font-size="10" fill="'+se.c+'">'+se.n.slice(0,26)+'</text>';
  });
  s+='<text x="26" y="'+(34+h/2)+'" font-size="10.5" fill="#3d372b" transform="rotate(-90 26 '+(34+h/2)+')" text-anchor="middle">competitive share of the euro on mapped pairs</text>';
  s+='</svg></div>';
  return '<div class="chart"><h3>When the same reference part is available as Genuine and as Competitive, which one is moving?</h3>'+
   '<p class="cap">On every mapped pair of part numbers, the share of the euro that went to the competitive line, by year. '+
   'The thick navy line is the whole mapped book: it moved from '+(K.suby['2023'].bvp/K.suby['2023'].tot*100).toFixed(1)+'% in 2023 to '+(K.suby['2025'].bvp/K.suby['2025'].tot*100).toFixed(1)+
   '% in 2025 across '+K.suby['2025'].pairs.toLocaleString('en-GB')+' mapped pair series in 22 distributor databases. '+
   'The thin lines are the six distributors with the largest mapped books.</p>'+s+
   '<p class="tiny">A pair is counted whether it sold as genuine, as competitive, or both, so the line is a mix measure on an unchanged part-number set, not a market-share measure. '+
   'Rising substitution can be a win (we kept the job) or a loss (we sold it cheaper): this chart cannot tell those apart, and the contested-euro chart below can.</p></div>';
}

/* ---- B4 exposure bands */
function cB4(){
  const fam=[];
  Object.keys(K.b4).forEach(db=>K.b4[db].forEach(f=>{
    let x=fam.find(z=>z.fam===f.fam); if(!x){ x={fam:f.fam,risk:0,bvp:0,cat:0,bvpeur:0}; fam.push(x); }
    x.risk+=f.risk*f.cat; x.bvp+=f.bvp*f.cat; x.cat+=f.cat; x.bvpeur+=f.bvpeur;
  }));
  fam.forEach(f=>{ f.risk/=f.cat; f.bvp/=f.cat; });
  const LBL={Belts_Cooling:'Belts & cooling',Brakes:'Brakes',Cab_Misc:'Cab & body',Clutch_Driveline:'Clutch & driveline',
    Electrical:'Electrical',PMS_Filters:'Filters (service)',Suspension_Chassis:'Suspension & chassis'};
  if(!fam.length) return '';
  const W=760,H=400, x0=76,y0=H-66,w=W-x0-40,h=y0-36;
  const mxX=Math.max.apply(null,fam.map(f=>f.risk))*1.4||1, mxY=100;
  let s=svgOpen(W,H);
  for(let i=0;i<=4;i++){ const x=x0+w*i/4;
    s+='<line x1="'+x+'" y1="36" x2="'+x+'" y2="'+y0+'" stroke="#f0ebe0"/>'+
       '<text x="'+x+'" y="'+(y0+15)+'" text-anchor="middle" font-size="9.5" fill="#8b8272">'+(mxX*i/4).toFixed(1)+'%</text>'; }
  for(let i=0;i<=4;i++){ const y=y0-h*i/4;
    s+='<line x1="'+x0+'" y1="'+y+'" x2="'+(x0+w)+'" y2="'+y+'" stroke="#e6e0d2"/>'+
       '<text x="'+(x0-6)+'" y="'+(y+3.5)+'" text-anchor="end" font-size="9.5" fill="#8b8272">'+(mxY*i/4).toFixed(0)+'%</text>'; }
  fam.forEach(f=>{
    const cx=x0+w*f.risk/mxX, cy=y0-h*f.bvp/mxY, rad=5+Math.sqrt(f.cat)/22;
    s+='<circle cx="'+cx.toFixed(1)+'" cy="'+cy.toFixed(1)+'" r="'+rad.toFixed(1)+'" fill="#15233c" fill-opacity="0.8"/>';
    s+='<text x="'+(cx+rad+4)+'" y="'+(cy+3.5)+'" font-size="10" fill="#3d372b">'+LBL[f.fam]+'</text>';
    s+='<title>'+LBL[f.fam]+': '+f.risk.toFixed(1)+'% of the euro in this family sits on part numbers the item master calls highly exposed to the independent aftermarket, '+
      'and '+f.bvp.toFixed(1)+'% of the family euro went to competitive parts ('+eur(f.bvpeur)+' on '+eur(f.cat)+' of catalogue sales).</title>';
  });
  s+='<text x="'+(x0+w/2)+'" y="'+(y0+34)+'" text-anchor="middle" font-size="10.5" fill="#3d372b">family exposure to the independent aftermarket</text>';
  s+='<text x="24" y="'+(36+h/2)+'" font-size="10.5" fill="#3d372b" transform="rotate(-90 24 '+(36+h/2)+')" text-anchor="middle">competitive share of the family euro</text>';
  s+='</svg></div>';
  return '<div class="chart"><h3>Where the genuine part is most exposed, does the competitive line take more of the euro?</h3>'+
   '<p class="cap">The seven aftersales families, 2025. Right is more of the family\u2019s euro sitting on part numbers the item master classifies as highly exposed; '+
   'up is a larger competitive share of that family\u2019s euro. Bubble size is the size of the family. If exposure and competitive share tracked each other, the bubbles would run bottom-left to top-right.</p>'+s+
   '<p class="tiny">Exposure is a classification, not a probability: the severity layer behind it returned a null on backtest and is not used as a KPI. '+
   'A family with a low competitive share and a high exposure figure is where the substitution has not happened yet \u2014 that is the read, not a win.</p></div>';
}

/* ---- B5 contested euro */
function cB5(){
  const rows=K.dbs.filter(d=>d.inModel && d.bvp && d.bvp.cont>0)
    .sort((a,b)=>b.bvp.cont-a.bvp.cont);
  const H=rows.length*26+78, W=980, x0=112, w=W-x0-210;
  let s=svgOpen(W,H);
  rows.forEach((r,i)=>{
    const y=26+i*26, b=r.bvp, tot=b.cont;
    const wBvp=(b.bvp/tot)*w, wGen=((tot-b.bvp)/tot)*w;
    s+='<rect x="'+x0+'" y="'+y+'" width="'+wBvp.toFixed(1)+'" height="17" fill="#c0552d">'+
       '<title>'+r.label+': '+eur(b.bvp)+' of '+eur(tot)+' contested euro won as competitive parts ('+(b.capr===null?'n/a':b.capr.toFixed(0)+'%').replace(/\u2013/,'-')+').</title></rect>';
    s+='<rect x="'+(x0+wBvp).toFixed(1)+'" y="'+y+'" width="'+wGen.toFixed(1)+'" height="17" fill="#15233c">'+
       '<title>'+r.label+': genuine contested euro '+eur(b.gencont)+' on part numbers that have a competitive twin and where the independent aftermarket can supply the job.</title></rect>';
    s+='<text x="'+(x0-8)+'" y="'+(y+12.5)+'" text-anchor="end" font-size="10.5" fill="#15233c">'+r.label+'</text>';
    s+='<text x="'+(x0+w+8)+'" y="'+(y+12.5)+'" font-size="10.5" fill="#3d372b">'+eur(tot)+
       ' <tspan fill="#c0552d">'+(b.capr===null?'n/a':b.capr.toFixed(0)+'% won as competitive')+'</tspan></text>';
  });
  s+='<text x="'+x0+'" y="14" font-size="10" fill="#3d372b">the contested euro only: part numbers where a competitive twin exists and an independent supplier could do the job</text>';
  s+='<rect x="'+(W-198)+'" y="'+(H-30)+'" width="11" height="11" fill="#c0552d"/>'+
     '<text x="'+(W-183)+'" y="'+(H-21)+'" font-size="10" fill="#3d372b">won as competitive</text>'+
     '<rect x="'+(W-92)+'" y="'+(H-30)+'" width="11" height="11" fill="#15233c"/>'+
     '<text x="'+(W-77)+'" y="'+(H-21)+'" font-size="10" fill="#3d372b">won as genuine</text>';
  s+='</svg></div>';
  const lost = K.net.bvpAll - K.net.bvpCy - (K.net.bvpAll*0 - 0);
  return '<div class="chart"><h3>Of the euro where we were actually in a contest, how much did we win \u2014 and how?</h3>'+
   '<p class="cap">Each bar is the contested euro for that distributor: the part numbers where a competitive twin exists, so an independent supplier could have taken the job. '+
   'Terracotta is the euro we kept as competitive parts, navy the euro we kept as genuine. The network contested pool is '+eurL(K.net.bvpAll-K.net.bvpCy)+
   ' within '+eurL(K.net.bvpAll)+' billed, and '+K.net.bvpShareCy.toFixed(2)+'% of everything billed is competitive parts.</p>'+s+
   '<p class="tiny">What is <b>not</b> on this chart is the euro we lost to the independent aftermarket. There is no measured share: the leaked euro would need independent-garage volume, '+
   'which nothing in this workspace measures. The uncaptured GPS value of '+eurL(K.net.capGap)+' is the modelled ceiling on that, not a measurement of it.</p></div>';
}
"""
JS += r"""
/* net figure for the AIM exposure axis: revenue-weighted across the 18 modelled distributors */
function aimRiskNet(){
  const rows=K.dbs.filter(d=>d.inModel && d.aim);
  if(!rows.length) return 0;
  let a=0,b=0; rows.forEach(d=>{ a+=d.aim.risk*d.cy; b+=d.cy; });
  return b? a/b : 0;
}
K.net.aimRisk = aimRiskNet();
"""
JS += r"""
/* =================================================================== narrative */
const STORYTXT = {
 IUK:{tag:'largest book, light commercial only, mileage-corrected',
   head:'The largest book in the network, on a fleet that drives half as far as the model assumes.',
   body:[
    ['billed', d=>'IUK bills '+eurL(d.cy)+' in calendar 2025: the largest distributor book in the network, on '+num(d.uio)+
      ' light commercial vehicles in service.'],
    ['spu', d=>'Spend per truck is '+eurL(d.spu)+' against a network median of \u20ac'+Math.round(K.net.spuFactMed)+
      ' on the billing fact over the 2025 fleet. That gap is not underperformance: measured odometer deltas put the N35 Grafter fleet at 14,494 km/yr against the model\u2019s flat 20,000, '+
      'so the service demand the model expects from an IUK truck is overstated by about a quarter before IUK is judged on it.'],
    ['cap', d=>'Capture reads '+d.cap.rate.toFixed(0)+'%, the lowest of any market above \u20ac5M, and the largest single family gap is '+
      (d.famGap? d.famGap.slice().sort((a,b)=>b.gap-a.gap)[0].fam.replace(/_/g,' ')+' at '+eurL(d.famGap.slice().sort((a,b)=>b.gap-a.gap)[0].gap) : 'unavailable')+
      '. Across all 14 service families the euro never billed is '+eurL(d.cap.gap)+'.'],
    ['bvp', d=>'IUK is a coverage question, not a price question: '+d.bvp.pct.toFixed(2)+
      '% of its billing is competitive parts, the thinnest share of the three large markets, and its genuine parts carry only a moderate premium over their competitive twins.'],
    ['mile', d=>'What makes IUK actionable is that the denominator is now measured rather than assumed. Every IUK figure on this page rests on '+num(d.uio)+
      ' vehicles in service and 14,494 measured km/yr, not on the flat assumption the model uses elsewhere.']
   ]},
 ITUK:{tag:'best capture rate, heavy trucks',
   head:'The best capture rate in the network, on a heavy-truck fleet.',
   body:[
    ['billed', d=>'ITUK bills '+eurL(d.cy)+' on '+num(d.uio)+' vehicles in service, almost all of them N-series and F-series trucks.'],
    ['cap', d=>'Capture is '+d.cap.rate.toFixed(0)+'%, the highest of any market above \u20ac1M, leaving '+eurL(d.cap.gap)+
      ' unbought \u2014 an order of magnitude less than IUK on a comparable book.'],
    ['bvp', d=>'It also carries the strongest competitive-parts mix in the network: '+d.bvp.pct.toFixed(1)+
      '% of all parts billed, and '+(d.bvp.capr===null?'n/a':d.bvp.capr.toFixed(0)+'%')+' of its contested euro won as competitive parts rather than genuine.'],
    ['read', d=>'ITUK is the counter-example that makes the rest of the page readable: when the fleet is heavy, the mileage is right and the service demand in the model is real, '+
      'it gets captured. The gap in the light commercial markets is not a demand problem.']
   ]},
 GERMANY:{tag:'worst capture rate on a large book',
   head:'The worst capture rate on a large book, with a price premium standing where coverage should be.',
   body:[
    ['billed', d=>'Germany bills '+eurL(d.cy)+' on '+num(d.uio)+' vehicles in service.'],
    ['cap', d=>'Capture is '+d.cap.rate.toFixed(0)+'% \u2014 the lowest of any market above \u20ac1M \u2014 leaving '+eurL(d.cap.gap)+
      ' unbought, concentrated in '+(d.famGap? d.famGap.slice().sort((a,b)=>b.gap-a.gap).slice(0,2).map(f=>f.fam.replace(/_/g,' ')).join(' and ') : 'unavailable')+'.'],
    ['price', d=>'At the same time '+d.prem.prem.toFixed(0)+
      '% is the weighted premium its genuine parts carry over their competitive twins across '+d.prem.units.toLocaleString('en-GB')+
      ' priced units: a price answer to what is a coverage problem.'],
    ['mile', d=>'Measured mileage for the German light commercial fleet is 17,819 km/yr, below the flat assumption, so the unbought euro is if anything understated rather than inflated.']
   ]}
};
function storyHTML(){
  return K.story.map(code=>{
    const d=K.dbs.find(x=>x.code===code), s=STORYTXT[code];
    return '<div class="card" data-story="'+code+'"><h4 style="margin:0 0 3px;font-size:15px;color:#15233c">'+
      esc(d.label)+' \u2014 '+s.tag+'</h4><p class="note"><b>'+s.head+'</b></p><ul class="tight">'+
      s.body.map(function(b){ try{ return '<li>'+b[1](d)+'</li>'; }catch(e){ return ''; } }).join('')+'</ul></div>';
  }).join('');
}
"""
print('JS part 5 added, total %d bytes' % len(JS))

JS += r"""
/* =================================================================== honesty */
function honestyHTML(){
  const rows=[
    ['Parts billed, per distributor','measured','the billing fact, attributed by distributor code','Attributed by distributor code. Israel splits at sold-to-SAP level (UMI 1797 / UTI 1799); Portugal sums codes 519 and 92. Calendar 2025 total reconciles to \u20ac33,321,625. 2026 excluded.'],
    ['Vehicles in service (UIO)','measured','the spend file and the model-bucket fleet file','17 markets on the v18 actual basis, the UK truck fleet on DVLA. The weight split is from the model-bucket file, so it is a modelled split of a measured total.'],
    ['Spend per truck','modelled on a measured numerator','the spend file and the billing fact','Billing divided by the fleet denominator. The real weakness is the target spend behind capture, not this ratio. On Calendar 2025 the two sources differ by \u20ac940k (\u20ac31.70M billed against \u20ac30.76M in the spend file) because the spend file is the narrower, reconciled book; the league shows the billing fact and says so.'],
    ['Service-part capture and the uncaptured value','modelled','the capture file and the opportunity matrix','The expected units rest on a maintenance interval and an annual distance. Where the distance is measured it overrides the flat assumption; eight of the 18 modelled markets sit on one flat \u20ac250-per-truck target, which is 40.2% of the total modelled ceiling.'],
    ['Capture trend','measured, weak fit','the capture-trajectory file','Three annual points per distributor-family. Only five of 252 family trends are formally flagged as declining, so most slopes are indistinguishable from flat.'],
    ['Defection and dormancy','measured flag, euro allocated','the defection file plus the billing fact','The silence flag comes from order history to March 2026. The euro beside it is trailing twelve-month billing allocated by distributor and family, not a lost-revenue estimate.'],
    ['Basket breadth','measured, partial','the billing fact goods classification','96.9% of billed value carries a goods classification; the remainder sits in no group and cannot be counted.'],
    ['Exposure and price position','classification and a sample price','the exposure file and the price-premium file','Exposure is a hand classification whose severity layer returned a null on backtest. The premium is unit-weighted only where both lines sold, so it is a sample.'],
    ['Warranty share','measured, with a gap','the spend file and the fiscal warranty file','Calendar share from the spend file; fiscal share from the fiscal warranty file. The four CIS markets have no warranty data at all.'],
    ['Competitive-parts share','measured, two universes','the billing fact, the modelled ceiling file, the service-part mix file','Published twice because the denominator changes the answer. Neither is a target.'],
    ['Substitution on mapped pairs','measured, mapped set','the substitution file','A mapped pair is counted whether it sold as genuine, competitive or both, so the line is a mix measure on an unchanged part-number set.'],
    ['Contested euro','measured within a definition','the parts-mix classification and the six sales-to-dealer files','Contested means a competitive twin exists. The euro lost outright to the independent aftermarket is not measured anywhere.'],
  ];
  const CHIP={measured:'g','modelled':'a','excluded':'r','needs-a-judgement':'n'};
  return '<div class="card"><div class="rc">'+
    '<span class="r g"><b>'+rows.filter(r=>r[1].indexOf('measured')===0).length+'</b> measured</span>'+
    '<span class="r"><b>'+rows.filter(r=>r[1].indexOf('modelled')===0).length+'</b> modelled</span>'+
    '<span class="r c"><b>3</b> figures excluded outright</span>'+
    '<span class="r"><b>'+K.dbs.length+'</b> distributor rows</span>'+
    '<span class="r"><b>'+document.querySelectorAll('.chart').length+'</b> charts on this page</span>'+
    '</div>'+
    '<div class="tbl" style="margin-top:10px"><table style="min-width:1000px"><thead><tr><th class="l">Figure</th>'+
    '<th class="l">How solid</th><th class="l">Behind it</th><th class="l">The honest limit</th></tr></thead><tbody>'+
    rows.map(r=>'<tr><td class="l"><b>'+r[0]+'</b></td><td class="l"><span class="chip '+CHIP[r[1]]+'">'+r[1]+
      '</span></td><td class="l tiny">'+r[2]+'</td><td class="l">'+r[3]+'</td></tr>').join('')+
    '</tbody></table></div></div>';
}
function notshownHTML(){
  const items=[
    '<b>The euro we lost outright to the independent aftermarket.</b> Nothing in this workspace measures independent-garage volume. Every "lost" figure elsewhere is a modelled ceiling, and it is labelled as one here.',
    '<b>Any 2026 calendar or fiscal view.</b> From April 2026 the billing table stores customer names instead of distributor codes, so 2026 rows cannot be attributed to a distributor. Trends therefore end at December 2025.',
    '<b>The 2026\u20132030 fleet forecast.</b> Withdrawn: the forecast scraps vehicles at about 3% a year where the history implies about 10%, and the gap widens with distance. No figure from it appears anywhere on this page.',
    '<b>Sales to dealer for twelve of the eighteen distributors.</b> Only six file it (ITUK, UTI, Ireland, IUK, Greece, Portugal, 69 dealer entities, \u20ac'+ (K.net.sellout/1e6).toFixed(2)+'M). The other twelve show a blank with the reason, never a zero and never a copy of the other direction.',
    '<b>Warranty for the four CIS markets.</b> Ukraine, Armenia, Kazakhstan and Palestine have no warranty data. They are shown as unavailable, not as zero.',
    '<b>The market-mix leg of the growth split.</b> The source\u2019s mix column is a hard zero, so its value has been absorbed into the volume and price legs. It is stated as unavailable rather than drawn as a flat bar.',
    '<b>Customer-level dormancy.</b> The source carries 62 dealer-and-family rows alongside the 203 distributor rows, but this page carries no customer names, so only the distributor level is shown.',
    '<b>The fiscal view of anything the sources tag by calendar year only.</b> The capture, trend, exposure and price-premium sources are calendar-tagged, so on the fiscal toggle those figures stay calendar and say so on the figure.',
    '<b>Part-number-level billing and customer names.</b> Out of scope for this page by rule.',
    '<b>Occupancy, utilisation or any other live operational metric.</b> Not in the sources. Inventing one is the failure this page exists to prevent.'
  ];
  return '<div class="warnbox"><b>Not shown, and why.</b><ul class="tight">'+
    items.map(i=>'<li>'+i+'</li>').join('')+'</ul></div>'+
    '<div class="card"><h3 style="margin-top:0">What the three toggles actually do</h3><ul class="tight">'+
    '<li><b>Period</b> recomputes parts billed, competitive-parts euro and spend per truck from the billing fact on billing date: Calendar 2025 is Jan\u2013Dec 2025, FY25/26 is Apr 2025 \u2013 Mar 2026. Sources that are calendar-tagged only keep their calendar figure and carry a CY25 chip.</li>'+
    '<li><b>Direction</b> swaps what we invoice the distributor for what the distributor invoices its dealers, where a file exists. On the dealer direction, spend per truck is withheld because the six sales-to-dealer files carry a different fleet basis, and the fiscal view is unavailable because those files are calendar 2025.</li>'+
    '<li><b>Warranty</b> strips warranty parts to leave the customer-paid book. Where a market has no warranty data the stripped figure cannot be computed, so it is withheld rather than shown unchanged.</li>'+
    '</ul><p class="tiny">Distributor stock ratio: where a market files sales to dealer, what it sold on to its dealers less what we invoiced it, for the same year. Six markets only: ITUK, IUK, UTI, Ireland, Greece, Portugal. Read it as an indicator of stock the distributor is carrying, not as a sales result.</p></div>';
}

/* =================================================================== render */
function render(){
  const d = MODE.dir==='dlr';
  document.getElementById('hero').innerHTML = d
    ? '<div class="warnbox"><b>Direction: DB \u2192 dealer.</b> Six distributors file what they sell on to their dealers: ITUK, UTI, Ireland, IUK, Greece and Portugal, 69 dealer entities, \u20ac'+
      (K.net.sellout/1e6).toFixed(2)+'M in calendar 2025. The other twelve cannot be shown in this direction at all. The league below keeps its ISZE \u2192 DB figures, since that is the direction every per-distributor source is built on, and marks the dealer comparison in the last column.</div>'
    : heroHTML();
  document.getElementById('league').innerHTML = leagueHTML();
  document.getElementById('growth').innerHTML = cSpend()+cGrowth()+cCapture()+cTrend()+cGap();
  document.getElementById('growth2').innerHTML = cUio()+cDefect()+cBreadth()+cExpose()+cWarranty();
  document.getElementById('bvp').innerHTML = cB1()+cB2()+cB3()+cB4()+cB5();
  document.getElementById('story').innerHTML = storyHTML();
  document.getElementById('honest').innerHTML = honestyHTML();
  document.getElementById('notshown').innerHTML = notshownHTML();
  const n = netView();
  document.getElementById('stateChip').innerHTML = LBL_P[MODE.period]+' \u00b7 '+LBL_D[MODE.dir]+' \u00b7 '+LBL_W[MODE.warr]+
    ' \u2014 night rail: '+(n.monthsMiss? n.monthsMiss+' distributor-months have no billing row (dark distributors)':'complete');
  $$('.chart').forEach((c,i)=>{ c.setAttribute('data-chartidx', i+1); });
  const cov = document.getElementById('coverage');
  if(cov) cov.innerHTML = coverageHTML();
  window.__KPI_META__ = {charts: document.querySelectorAll('.chart').length, mode: JSON.parse(JSON.stringify(MODE)), snap: K.snap};
}
function coverageHTML(){
  const d0 = K.dbs.find(d=>d.dealer && d.inModel);
  const v0 = d0? view(d0) : null;
  const splitWarn = (v0 && v0.warrNoSplit)
    ? '<div class="warnbar">Warranty excluded is selected, but the sales-to-dealer file carries no warranty split. '+
      'Every sales-to-dealer figure below therefore still contains warranty parts. Switch to ISZE \u2192 DB, or back to warranty included, for a clean warranty basis.</div>'
    : '';
  const cells = K.dbs.map(d=>{
    const v=view(d);
    const cls = v.eur==='na'? 'na' : (v.eur===null? 'na' : 'ok');
    return '<span class="chip '+(cls==='ok'?'g':'n')+'" data-tip="'+esc(d.label+': '+(v.monthsUsed)+' of '+v.monthsCov+
      ' months carry a billing row in '+LBL_P[MODE.period]+'. '+(v.eur==='na'? 'No figure in this direction: '+v.dirReason+'.':''))+'">'+
      d.label+' '+(v.monthsUsed)+'/'+v.monthsCov+'</span>';
  }).join(' ');
  return '<h3 style="margin:0 0 4px">Coverage strip \u2014 how many months of the selected period actually carry a billing row, per distributor</h3>'+
    '<p class="cap">A distributor with no rows in a month is dark for that month, not zero: the file simply has nothing. Capture, trend, exposure and price-premium figures are calendar-tagged and keep their calendar value in the fiscal view.</p>'+
    splitWarn+
    '<div class="rc">'+cells+'</div>';
}
document.addEventListener('click', function(ev){
  const b = ev.target.closest && ev.target.closest('.bar button'); if(!b) return;
  MODE[b.getAttribute('data-k')] = b.getAttribute('data-v');
  $$('.bar button').forEach(x=>{ if(x.getAttribute('data-k')===b.getAttribute('data-k'))
      x.setAttribute('aria-pressed', x===b? 'true':'false'); });
  render();
});
document.addEventListener('DOMContentLoaded', render);
if(document.readyState!=='loading') render();
"""
print('JS part 6 added, total %d bytes' % len(JS))

# ===================================================================== 7. page
HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ISZE KPI Dashboard &mdash; per distributor, FY25/26 and Calendar 2025</title>
<style>__CSS__</style></head><body>
<header class="top"><div class="inner">
<h1>KPI dashboard &mdash; measured per distributor</h1>
<div class="sub">The fifteen growth and Competitive-parts KPIs, one row per distributor, on that distributor&rsquo;s own fleet.
Ten growth measures and five Competitive-parts measures, in euro, with the service family and the fleet denominator attached.
Sources snapshot 2026-09-16. Charts are drawn on the page itself: no library, no external request, no connection needed.</div>
<div class="flags">
<span class="flag">FY25/26 = April 2025 &ndash; March 2026</span>
<span class="flag">Calendar 2025 = January &ndash; December 2025</span>
<span class="flag">22 distributors, 18 in the modelled base</span>
<span class="flag warn">2026 is excluded: from April 2026 the billing table carries customer names, not distributor codes</span>
<span class="flag warn">The 2026&ndash;2030 fleet forecast is withdrawn and does not appear here</span>
</div></div></header>
__BAR__
<div class="wrap">
<div id="hero"></div>
<div class="card" style="margin-top:10px"><div id="coverage"></div></div>

<h2 class="sec"><span class="n">1</span>KPI league per distributor
  <span class="q">Every market, the fifteen measures side by side, with the fleet denominator and the weight class attached.</span></h2>
<div id="league"></div>

<h2 class="sec"><span class="n">2</span>The growth panel, first five
  <span class="q">Spend per truck, the growth split, capture, the capture trend and the uncaptured value.</span></h2>
<div id="growth"></div>

<h2 class="sec"><span class="n">3</span>The growth panel, remaining five
  <span class="q">Fleet direction, dormancy, basket breadth, exposure and price, and the quality of the revenue mix.</span></h2>
<div id="growth2"></div>

<h2 class="sec"><span class="n">4</span>Competitive-parts panel
  <span class="q">Both share universes, the addressable range, substitution on the same reference part, exposure bands and the contested euro.</span></h2>
<div id="bvp"></div>

<h2 class="sec"><span class="n">5</span>The three distributors that carry the story
  <span class="q">IUK, ITUK and Germany: the largest book, the best capture rate, and the worst capture rate on a large book.</span></h2>
<div id="story"></div>

<h2 class="sec"><span class="n">6</span>How solid is each figure, and what is not here
  <span class="q">Measured, modelled, excluded or needs a judgement &mdash; stated per figure, with the limits written down.</span></h2>
<div id="notshown"></div>
<div id="honest"></div>

<footer class="foot">
<p><b>Sources.</b> Parts billed and annual distance: the billing fact. Vehicles in service, spend per truck and warranty: the distributor spend file and the model-bucket fleet file.
Capture and the uncaptured value: the capture-by-distributor file and the opportunity matrix. Growth split: the revenue waterfall. Dormancy: the defection alert file.
Basket breadth: the billed-part file plus the goods classification. Exposure and price: the exposure file and the price-premium file.
Competitive parts: the genuine-and-competitive mix file, the mapped-pair substitution file, the addressable-range file, the exposure-by-family file and the parts-mix classification.
Sales to dealer: the six distributor sell-to-dealer files.</p>
<p><b>Definitions.</b> <b>UIO</b>, vehicles in service: the vehicles in operation that parts demand comes from.
<b>GPS</b>: parts spend per vehicle per year, in euro. <b>Capture</b>: units billed divided by units the maintenance model expects, on the same fleet.
<b>Uncaptured GPS value</b>: modelled parts demand never billed, in euro. <b>PMS</b>: the parts model schedule, the maintenance interval behind the expected units.
<b>BVP</b>, Competitive parts: the lower-priced Isuzu line that competes with the independent aftermarket; <b>Genuine</b> is the original-brand line.
<b>DB</b>: distributor, the national importer we bill. <b>Contested euro</b>: euro on part numbers where a Competitive twin exists.</p>
<p>Snapshot 2026-09-16. Calendar years 2023&ndash;2025 complete only.</p>
</footer>
</div>
<script>window.__KPI__=__PAYLOAD__;</script>
<script>__JS__</script>
</body></html>
"""

bar_static = """<div class="bar"><div class="inner">
<div class="grp"><span class="gl">Period</span>
<button type="button" data-k="period" data-v="cy" aria-pressed="true" data-tip="Calendar 2025 (Jan&ndash;Dec). Recomputed from the billing fact on billing date.
Snapshot 2026-09-16.">Calendar 2025</button>
<button type="button" data-k="period" data-v="fy" data-tip="FY25/26 (Apr 2025 &ndash; Mar 2026). Recomputed from the billing fact on billing date.
Snapshot 2026-09-16.">FY25/26</button></div>
<div class="grp"><span class="gl">Direction</span>
<button type="button" data-k="dir" data-v="db" aria-pressed="true" data-tip="ISZE &rarr; DB: what we invoice the distributor.
Snapshot 2026-09-16.">ISZE &rarr; DB</button>
<button type="button" data-k="dir" data-v="dlr" data-tip="DB &rarr; dealer: what the distributor invoices its dealers. Only six distributors file it (ITUK, UTI, Ireland, IUK, Greece, Portugal).
Snapshot 2026-09-16.">DB &rarr; dealer</button></div>
<div class="grp"><span class="gl">Warranty</span>
<button type="button" data-k="warr" data-v="inc" aria-pressed="true" data-tip="Warranty included in what we billed.
Snapshot 2026-09-16.">Included</button>
<button type="button" data-k="warr" data-v="ex" data-tip="Warranty excluded: warranty parts are stripped to leave the customer-paid book.
Snapshot 2026-09-16.">Excluded</button></div>
<div class="state" id="stateChip"></div>
</div></div>"""

page = (HTML.replace('__CSS__', CSS).replace('__BAR__', bar_static)
        .replace('__PAYLOAD__', PAY_JSON).replace('__JS__', JS))

# ---- assertions before writing
import re
bad = re.findall(r'(?:src|href)\s*=\s*["\']https?://', page, re.I)
if bad:
    raise SystemExit('external request found: %s' % bad)
if '@import' in page or 'url(http' in page:
    raise SystemExit('external CSS reference found')
if 'TODO' in page or '__CSS__' in page or '__JS__' in page or '__PAYLOAD__' in page or '__BAR__' in page:
    raise SystemExit('unreplaced template marker found')
with open(OUT_HTML, 'w', encoding='utf-8', newline='\n') as f:
    f.write(page)
print('WROTE %s  (%.1f KB)' % (OUT_HTML, len(page.encode('utf-8')) / 1024))

CMD = os.path.join(SALES, 'OPEN_ISZE_KPI_Dashboard.cmd')
with open(CMD, 'w', encoding='ascii', newline='\r\n') as f:
    f.write('@echo off\r\nstart "" "%~dp0ISZE_KPI_Dashboard.html"\r\n')
print('WROTE %s' % CMD)






