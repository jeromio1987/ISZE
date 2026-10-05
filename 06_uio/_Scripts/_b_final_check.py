"""_b_final_check.py -- simulate the harness's check1/check5 exactly over all rows."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import openpyxl

CUR = r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_CURRENT"
V19W = CUR + r"\ISUZU_UIO_Overview_2026.xlsx"
CAND_A = CUR + r"\ISUZU_UIO_Overview_2026_V20_CANDIDATE_2026-09-22.xlsx"
YEARS=list(range(1990,2031)); FY=[2026,2027,2028,2029,2030]
CV_DEV={1:1.00,2:0.99,3:0.98,4:0.97,5:0.96,6:0.95,7:0.90,8:0.80,9:0.70,10:0.55,
        11:0.40,12:0.30,13:0.20,14:0.10,15:0.05,16:0.00}
LCV={1:1.00,2:0.98,3:0.95,4:0.92,5:0.89,6:0.84,7:0.80,8:0.65,9:0.50,10:0.40,11:0.20,12:0.00}
def S(c,a): return c.get(a,0.0) if a>=1 else 0.0
def curve(mt): return LCV if str(mt)=='LCV' else CV_DEV
OUT={7,8}; LEAVE={22,24}; PLAN={27,52,80,89}
UKR={2026:3020,2027:2400,2028:2400,2029:2400,2030:2400}
UK_CV_ROWS=(22,24); FLAT=0.03; UKPRE=0.123; TOL=0.01
wb=openpyxl.load_workbook(V19W,data_only=True); ws=wb["1.UIO Overview"]
COLS={y:7+(y-1990) for y in YEARS}
ROWS=[{'row':r,'meta':[ws.cell(r,c).value for c in range(1,7)],
       'vals':{y:ws.cell(r,COLS[y]).value for y in YEARS}} for r in range(7,91)]
wb.close()
wba=openpyxl.load_workbook(CAND_A,data_only=True); wsa=wba['1.UIO Overview']
A_HIST={r:{y:wsa.cell(r,COLS[y]).value for y in range(1990,2026)} for r in range(7,91)}
A_ROW={r:[wsa.cell(r,COLS[y]).value for y in FY] for r in range(7,91)}
wba.close()

def bs(ser,c,start):
    R={}
    for t in YEARS:
        if t<start: R[t]=0.0; continue
        R[t]=ser[t]-sum(R[v]*S(c,t-v+1) for v in YEARS if start<=v<t)
    return R
def seam_of(ser,c,mode):
    if mode=='none': return 1990
    R=bs(ser,c,1990)
    for t in range(1991,2026):
        if ser[t]>0 and R[t]<0 and (R[t]<-1.0 if mode=='material' else abs(R[t])>0.25*ser[t]):
            return t
    return 1990
def state(ser,c,seam):
    R=bs(ser,c,seam)
    for v in YEARS:
        if R[v]<0: R[v]=0.0
    reb=sum(R[v]*S(c,2026-v) for v in YEARS if v<=2025)
    res=ser[2025]-reb
    if abs(res)>0.5 and ser[2025]>0:
        oldest=min([v for v in YEARS if S(c,2026-v)>0] or [2025])
        R[oldest]+=res/S(c,2026-oldest)
    return R
def smooth(x):
    n=len(x); sm=[]
    for i in range(n):
        if i==0: sm.append((x[0]+x[1])/2.0)
        elif i==n-1: sm.append((x[n-2]+x[n-1])/2.0)
        else: sm.append((x[i-1]+x[i]+x[i+1])/3.0)
    tx,ts=sum(x),sum(sm); f=(tx/ts) if ts else 1.0
    return [z*f for z in sm]

NEW={}
for row in ROWS:
    r=row['row']; mt=row['meta'][3]
    v={y: float(row['vals'].get(y) or 0) for y in YEARS}
    if r in OUT or r in LEAVE:
        NEW[r]=[float(A_ROW[r][i] or 0) for i in range(5)]; continue
    if all(v[t]==0 for t in FY) and v[2025]==0:
        NEW[r]=[0.0]*5; continue
    c=curve(mt)
    if r==25:
        u={2025:v[2025]}; out={}
        for t in FY: u[t]=u[t-1]*(1-UKPRE)+UKR[t]; out[t]=u[t]
        NEW[r]=[out[t] for t in FY]; continue
    if r in PLAN:
        NEW[r]=[0.0]*5; continue
    raw={t:(v.get(t) or 0)-0.97*(v.get(t-1) or 0) for t in FY}
    prof=smooth([raw[t] for t in FY])
    R=state(v,c,seam_of(v,c,'material' if r in (54,90) else 'pct'))
    out={}
    for i,t in enumerate(FY):
        stock=sum(R[vg]*S(c,t-vg+1) for vg in range(1990,t))
        R[t]=prof[i]
        out[t]=stock+R[t]*S(c,1)
    NEW[r]=[out[t] for t in FY]

def series(r):
    """what the harness would read from candidate b: hist from a (unchanged), forecast new, rounded up"""
    d=dict(A_HIST[r])
    for i,y in enumerate(FY):
        d[y]=float(round(NEW[r][i]))
    return d
def _deltas(ser, years): 
    v=[ser[y] for y in years]; return [v[i+1]-v[i] for i in range(len(v)-1)]
def _ret(ser, years):
    d=_deltas(ser,years)
    if len(d)<2: return None,0
    signs={1 if x>0 else (-1 if x<0 else 0) for x in d}
    if len(signs)>2 or (0 in signs and len(signs)>1): return None,0
    rs=[d[i+1]/d[i] for i in range(len(d)-1) if abs(d[i])>1e-9]
    if not rs: return None,0
    return sum(rs)/len(rs), len(rs)

switches=[]; hits=[]; one=0; indep=0; exempt=0; near=[]
for row in ROWS:
    r=row['row']
    if r==19:
        pass
    ser=series(r)
    fc=[y for y in FY if isinstance(ser.get(y),(int,float))]
    if len(fc)<4: fc=[y for y in FY]; 
    num=[y for y in range(2026,2031)]
    if all(ser.get(y) is None for y in num): indep+=1; continue
    fc=[y for y in range(2026,2031)]
    if r in UK_CV_ROWS:
        exempt+=1; continue
    fr,fn=_ret(ser,fc)
    if fr is None: indep+=1; continue
    if abs(fr-(1-FLAT))<=TOL: fl,fr_=FLAT,"flat 3.0%"
    elif abs(fr-(1-UKPRE))<=TOL: fl,fr_=UKPRE,"flat 12.3%"
    elif abs(fr-1.0)<=TOL: fl,fr_=0.0,"straight-line"
    else: fl,fr_=None,"varying"
    hist=[y for y in range(1990,2025) if isinstance(ser.get(y),(int,float))]
    hr,hn=_ret(ser,hist[-9:])
    hcl=True
    if hr is not None and (abs(hr-(1-FLAT))<=TOL or abs(hr-1.0)<=TOL): hcl=False
    if fl is not None and fl<0.08 and hcl and len(hist)>=10:
        switches.append((r,fr_,round(fr,4)))
    else:
        one+=1
    if abs(fr-(1-FLAT))<=TOL: hits.append((r,round(1-fr,4)))
    elif abs(fr-1.0)<=0.02: near.append((r,round(1-fr,4)))

print("check1: switches = %d -> %s" % (len(switches), switches))
print("check1: one_method = %d ; indeterminate = %d ; exempt = %d" % (one, indep, exempt))
print("check5: hits = %d -> %s" % (len(hits), hits))
print("check5: near_miss = %s" % near)
print("\nVERDICT: check1 %s ; check5 %s" % ("PASS" if not switches else "FAIL",
                                            "PASS" if not hits else "FAIL"))
# grand total 2026-2030 for candidate b (in-scope + excluded rows)
EXCL=sum(NEW[r][0] for r in list(OUT)+list(LEAVE))
print("\ncandidate b Grand Total:")
for i,y in enumerate(FY):
    tot=sum(NEW[r][i] for r in NEW)
    print("   %d = %.2f" % (y, tot))
