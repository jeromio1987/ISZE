"""Full warranty analysis — outputs to console."""
import sys, io, openpyxl, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

WARR = r'C:\Users\jerom\Desktop\claude\ISZE\Data\Final_Complete_Warranty_Pricing_2026.xlsx'
SALES_PATH = r'C:\Users\jerom\Desktop\claude\ISZE\Projects\Isuzu\prism\data\sales_detailed_for_claude_full_fixed.tsv'

wb = openpyxl.load_workbook(WARR, read_only=True, data_only=True)

def norm_pn(v):
    if v is None: return None
    s = str(v).strip()
    if s.endswith(".0"): s = s[:-2]
    if not s or s == "0": return None
    if s.isdigit(): return s.zfill(10)
    return s

prices = {}
descs = {}
abc = {}
ws_p = wb["Pricing_Data"]
hdr_p = list(ws_p.iter_rows(min_row=1, max_row=1, values_only=True))[0]
pn_i = hdr_p.index("P/N")
desc_i = hdr_p.index("Description")
price_i = hdr_p.index("Price")
abc_i = hdr_p.index("ABC Code")
for row in ws_p.iter_rows(min_row=2, max_row=ws_p.max_row, values_only=True):
    pn = norm_pn(row[pn_i])
    if pn:
        if row[price_i] is not None:
            try: prices[pn] = float(row[price_i])
            except: pass
        if row[desc_i]: descs[pn] = str(row[desc_i]).strip()
        if row[abc_i]: abc[pn] = str(row[abc_i]).strip()
print(f"PR00 master: {len(prices):,} parts priced, {sum(1 for a in abc.values() if a):,} with ABC")

CV_MAP = {"ITUK":"ITUK","UTI":"UTI","IRELAND":"IRELAND","ISD":"GERMANY","PORTUGAL":"PORTUGAL",
          "CYPRUS":"CYPRUS","GREECE":"GREECE","MALTA":"MALTA","MIDI":"EXCLUDE","MIDI AIOS Products":"EXCLUDE"}
ws = wb["Raw_CV_Warranty"]
hdr = list(ws.iter_rows(min_row=1, max_row=1, values_only=True))[0]
idx = {h:i for i,h in enumerate(hdr)}
cv_records = []
for row in ws.iter_rows(min_row=2, max_row=ws.max_row, values_only=True):
    bill = str(row[idx["BILLYMD"]]) if row[idx["BILLYMD"]] else ""
    if not bill.startswith("2025"): continue
    dst = str(row[idx["DST_Name"]]).strip() if row[idx["DST_Name"]] else ""
    code = CV_MAP.get(dst)
    if code is None or code == "EXCLUDE": continue
    ope = row[idx["OPE_Name"]]
    mile = row[idx["MILE"]] or 0
    for pn_col, q_col in [("PARTNBR","QTY1"),("PARTNBR2","QTY2")]:
        pn = norm_pn(row[idx[pn_col]])
        if not pn: continue
        try: qty = float(row[idx[q_col]] or 0)
        except: qty = 0
        if qty <= 0: continue
        price = prices.get(pn, 0)
        cv_records.append({"db":code,"pn":pn,"qty":qty,"value":qty*price,
                           "ope":str(ope or "").strip(),"mile":mile})
cv = pd.DataFrame(cv_records)
print(f"CV: {len(cv):,} rows | qty {cv['qty'].sum():,.0f} | val EUR {cv['value'].sum():,.0f}")

LCV_MAP = {"BL ehf.":"ICELAND","ISUZU BENELUX - BELGIUM":"BELGIUM","ISUZU BENELUX - NETHERLANDS":"BELGIUM",
    "Isuzu Benelux NV":"BELGIUM","Isuzu Benelux NV (Poland)":"BELGIUM","ISUZU (UK)":"IUK",
    "Isuzu Ireland":"IRELAND","Isuzu Ireland 2020 Unlimited Company":"IRELAND",
    "ISUZU SALES DEUTSCHLAND - ISD":"GERMANY","ISUZU SALES DEUTSCHLAND - AUSTRIA":"GERMANY",
    "ISUZU SALES DEUTSCHLAND - CZECH":"GERMANY","ISUZU SALES DEUTSCHLAND - SLOVAKIA":"GERMANY",
    "IMOTORS LDA":"PORTUGAL","Isuzu Sverige":"SWEDEN","RSA":"NORWAY","ISUZU Danmark":"DENMARK",
    "Isuzu Motor Finland OY":"FINLAND","GASANZAMMIT MOTORS LIMITED":"MALTA","PETROS PETROPOULOS":"GREECE",
    "A. LOUTSIOS & SONS":"CYPRUS","ISUZU ROM AUTO SRL":"ROMANIA","AW Distribution Kft.":"HUNGARY",
    "MIDI Europe":"EXCLUDE","MIDI Europe S.R.L.":"EXCLUDE","MIDI EUROPE - FRANCE":"EXCLUDE",
    "MIDI EUROPE - ITALY":"EXCLUDE","MIDI EUROPE - MACEDONIA":"EXCLUDE","MIDI EUROPE - SPAIN":"EXCLUDE",
    "MIDI EUROPE - SWITZ":"EXCLUDE","MIDI EUROPE S.R.L.(SLOVENIA)":"EXCLUDE",
    "Midi Europe S.P.L (Ser.mon.)":"EXCLUDE","Midi Europe S.R.L (BOSNIA HERZEGOVINA)":"EXCLUDE",
    "WAE LTD.":"EXCLUDE","ZAMZAM SPRING GENERAL TRADING CO., LTD":"EXCLUDE"}
ws = wb["Raw_LCV_Warranty"]
hdr = list(ws.iter_rows(min_row=1, max_row=1, values_only=True))[0]
idx = {h:i for i,h in enumerate(hdr)}
lcv_records = []
for row in ws.iter_rows(min_row=2, max_row=ws.max_row, values_only=True):
    am = str(row[idx["AssessMonth"]]) if row[idx["AssessMonth"]] else ""
    if not am.startswith("2025"): continue
    dname = str(row[idx["DistributorName"]]).strip() if row[idx["DistributorName"]] else ""
    code = LCV_MAP.get(dname)
    if code is None or code == "EXCLUDE": continue
    pn = norm_pn(row[idx["PartsNo"]])
    if not pn: continue
    try: qty = float(row[idx["Pieces"]] or 0)
    except: qty = 0
    if qty <= 0: continue
    price = prices.get(pn, 0)
    lcv_records.append({"db":code,"pn":pn,"qty":qty,"value":qty*price,
        "ope":str(row[idx["OperationDescription"]] or "").strip(),
        "trouble":str(row[idx["TroubleDesc"]] or "").strip(),
        "system":str(row[idx["System"]] or "").strip(),
        "model":str(row[idx["WarrantyModel"]] or "").strip(),
        "mile":row[idx["Mileage"]] or 0,
        "rdr":row[idx["RDRDate"]],"writedate":row[idx["WrittenDate"]]})
lcv = pd.DataFrame(lcv_records)
print(f"LCV: {len(lcv):,} rows | qty {lcv['qty'].sum():,.0f} | val EUR {lcv['value'].sum():,.0f}")

combined = pd.concat([cv[["db","pn","qty","value"]], lcv[["db","pn","qty","value"]]])

print("\n=== TOP 25 PARTS BY VALUE ===")
tv = combined.groupby("pn").agg(qty=("qty","sum"), value=("value","sum")).sort_values("value", ascending=False).head(25)
for pn,r in tv.iterrows():
    d = (descs.get(pn,"?") or "?")[:38]; a = abc.get(pn,"")
    print(f"  {pn}  qty={r['qty']:>5.0f}  EUR {r['value']:>10,.0f}  ABC={a:1}  {d}")

print("\n=== TOP 25 PARTS BY QUANTITY ===")
tq = combined.groupby("pn").agg(qty=("qty","sum"), value=("value","sum")).sort_values("qty", ascending=False).head(25)
for pn,r in tq.iterrows():
    d = (descs.get(pn,"?") or "?")[:38]; a = abc.get(pn,"")
    print(f"  {pn}  qty={r['qty']:>5.0f}  EUR {r['value']:>10,.0f}  ABC={a:1}  {d}")

print("\n=== TOP 15 LCV FAILURE OPERATIONS ===")
ol = lcv.groupby("ope").agg(count=("pn","count"), value=("value","sum")).sort_values("value", ascending=False).head(15)
for op,r in ol.iterrows():
    print(f"  {r['count']:>4.0f} cases  EUR {r['value']:>10,.0f}  {op[:60]}")

print("\n=== TOP 15 CV FAILURE OPERATIONS ===")
oc = cv.groupby("ope").agg(count=("pn","count"), value=("value","sum")).sort_values("value", ascending=False).head(15)
for op,r in oc.iterrows():
    print(f"  {r['count']:>4.0f} cases  EUR {r['value']:>10,.0f}  {op[:60]}")

print("\n=== LCV BY TROUBLE CODE ===")
tr = lcv.groupby("trouble").agg(count=("pn","count"), value=("value","sum")).sort_values("value", ascending=False).head(12)
for t,r in tr.iterrows():
    print(f"  {r['count']:>4.0f} cases  EUR {r['value']:>10,.0f}  {t}")

print("\n=== LCV BY SYSTEM CODE ===")
sd = lcv.groupby("system").agg(count=("pn","count"), value=("value","sum")).sort_values("value", ascending=False)
for s,r in sd.iterrows():
    print(f"  System '{s}'  {r['count']:>5.0f} cases  EUR {r['value']:>10,.0f}")

print("\n=== LCV BY MILEAGE BAND ===")
def mb(m):
    try: m=float(m)
    except: return "unknown"
    if m==0: return "0 PDI"
    if m<5000: return "0-5k"
    if m<20000: return "5-20k"
    if m<50000: return "20-50k"
    if m<100000: return "50-100k"
    if m<200000: return "100-200k"
    return ">200k"
lcv["mb"] = lcv["mile"].apply(mb)
mbd = lcv.groupby("mb").agg(count=("pn","count"), value=("value","sum"))
for b in ["0 PDI","0-5k","5-20k","20-50k","50-100k","100-200k",">200k","unknown"]:
    if b in mbd.index:
        r = mbd.loc[b]
        print(f"  {b:<12}  {r['count']:>5.0f} cases  EUR {r['value']:>10,.0f}")

print("\n=== LCV BY WARRANTY MODEL ===")
mod = lcv[lcv["model"]!=""].groupby("model").agg(count=("pn","count"), value=("value","sum")).sort_values("value", ascending=False).head(10)
for m,r in mod.iterrows():
    print(f"  {m:<10}  {r['count']:>5.0f} cases  EUR {r['value']:>10,.0f}")

print("\n=== PER-DB WARRANTY INTENSITY ===")
uio_total = {"ITUK":22389,"IUK":47783,"UTI":11253,"UMI":18542,"IRELAND":3056,
    "BELGIUM":9594,"GERMANY":12855,"PORTUGAL":8176,"SWEDEN":8443,"NORWAY":7929,
    "DENMARK":851,"FINLAND":1204,"ICELAND":406,"GREECE":3742,"CYPRUS":2308,
    "MALTA":1040,"ROMANIA":1071,"HUNGARY":3734}
per_db = combined.groupby("db").agg(qty=("qty","sum"), value=("value","sum")).reset_index()
per_db["uio"] = per_db["db"].map(uio_total)
per_db["eur_per_uio"] = per_db["value"] / per_db["uio"]
per_db["parts_per_uio"] = per_db["qty"] / per_db["uio"]
per_db = per_db.sort_values("eur_per_uio", ascending=False)
print(f"{'DB':<10}{'UIO 2025':>10}{'Warr qty':>10}{'Warr EUR':>14}{'EUR/UIO':>10}{'parts/UIO':>12}")
for _,r in per_db.iterrows():
    print(f"  {r['db']:<8}{r['uio']:>10,}{r['qty']:>10.0f}{r['value']:>14,.0f}{r['eur_per_uio']:>10.2f}{r['parts_per_uio']:>12.3f}")

print("\n=== WARRANTY AS % OF COMMERCIAL SALES 2025 ===")
sales_2025 = {"ITUK":5769868,"IUK":6221920,"UTI":3402117,"UMI":3388801,"IRELAND":1213660,
    "BELGIUM":2143952,"GERMANY":2577766,"PORTUGAL":1712791,"SWEDEN":1289481,"NORWAY":1438473,
    "DENMARK":150218,"FINLAND":285913,"ICELAND":87260,"GREECE":528391,"CYPRUS":429512,
    "MALTA":206502,"ROMANIA":177276,"HUNGARY":330031}
per_db["sales"] = per_db["db"].map(sales_2025)
per_db["pct"] = per_db["value"] / per_db["sales"]
s = per_db.sort_values("pct", ascending=False)
print(f"{'DB':<10}{'Sales EUR':>14}{'Warr EUR':>14}{'Warr/Sales':>14}")
for _,r in s.iterrows():
    print(f"  {r['db']:<8}{r['sales']:>14,.0f}{r['value']:>14,.0f}{r['pct']*100:>13.1f}%")
print(f"  {'NETWORK':<8}{sum(sales_2025.values()):>14,.0f}{per_db['value'].sum():>14,.0f}{per_db['value'].sum()/sum(sales_2025.values())*100:>13.1f}%")

print("\n=== TOP 25 WARRANTY PARTS — ALSO IN COMMERCIAL SALES 2025? ===")
sdf = pd.read_csv(SALES_PATH, sep='\t', low_memory=False)
sdf["year"] = pd.to_numeric(sdf["year"], errors='coerce')
sdf["net_sales_value"] = pd.to_numeric(sdf["net_sales_value"], errors='coerce')
sdf["pn_norm"] = sdf["part_number"].apply(norm_pn)
s25 = sdf[sdf["year"]==2025].groupby("pn_norm").agg(sq=("billed_qty","sum"), sv=("net_sales_value","sum"))
top = combined.groupby("pn").agg(wq=("qty","sum"), wv=("value","sum")).sort_values("wv", ascending=False).head(25)
print(f"{'PN':<12}{'Description':<30}{'Warr Q':>7}{'Warr EUR':>10}{'Sale Q':>8}{'Sale EUR':>11}{'W/(W+S)%':>10}")
for pn,r in top.iterrows():
    d = (descs.get(pn,"?") or "?")[:28]
    sq = s25.loc[pn]["sq"] if pn in s25.index else 0
    sv = s25.loc[pn]["sv"] if pn in s25.index else 0
    ratio = r["wv"] / (r["wv"]+sv) * 100 if (r["wv"]+sv) > 0 else 0
    print(f"  {pn:<10}{d:<30}{r['wq']:>7.0f}{r['wv']:>10,.0f}{sq:>8.0f}{sv:>11,.0f}{ratio:>9.1f}%")

print("\n=== ABC CLASSIFICATION OF WARRANTY VALUE ===")
combined["abc"] = combined["pn"].map(abc).fillna("?")
abcd = combined.groupby("abc").agg(qty=("qty","sum"), value=("value","sum"))
tv2 = abcd["value"].sum()
for a,r in abcd.iterrows():
    print(f"  ABC '{a}'  qty {r['qty']:>6.0f}  EUR {r['value']:>11,.0f}  ({r['value']/tv2*100:.1f}%)")

print("\n=== LCV FAILURE AGE PROFILE ===")
def age_band(rdr,wd):
    try:
        if rdr is None or wd is None: return "unknown"
        if isinstance(rdr,str) or isinstance(wd,str): return "unknown"
        d = (wd - rdr).days
        if d < 0: return "neg"
        if d < 90: return "<3mo"
        if d < 365: return "3-12mo"
        if d < 730: return "1-2yr"
        if d < 1095: return "2-3yr"
        return ">3yr"
    except: return "unknown"
lcv["age"] = lcv.apply(lambda r: age_band(r["rdr"], r["writedate"]), axis=1)
ag = lcv.groupby("age").agg(count=("pn","count"), value=("value","sum"))
tot_lcv = lcv["value"].sum()
for b in ["<3mo","3-12mo","1-2yr","2-3yr",">3yr","neg","unknown"]:
    if b in ag.index:
        r = ag.loc[b]
        print(f"  {b:<10}  {r['count']:>5.0f} cases  EUR {r['value']:>10,.0f}  ({r['value']/tot_lcv*100:.1f}%)")

print("\nDONE")
