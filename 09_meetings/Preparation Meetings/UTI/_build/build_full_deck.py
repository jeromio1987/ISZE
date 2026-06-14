# -*- coding: utf-8 -*-
"""Full assembled UTI meeting deck. Definitions left out (parked in GPS_PMS_Section)."""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE

RED=RGBColor(0xCC,0x0E,0x1E); LIGHT_RED=RGBColor(0xDC,0x60,0x6E)
WHITE=RGBColor(0xFF,0xFF,0xFF); BLACK=RGBColor(0x1A,0x1A,0x1A); GRAY=RGBColor(0x5A,0x5A,0x5A)
LGRAY=RGBColor(0xF0,0xF0,0xF0); MGRAY=RGBColor(0xD9,0xD9,0xD9)
SW,SH=Inches(13.33),Inches(7.5)
TEMPLATE=r"C:\Users\jerom\Desktop\claude\ISZE\Isuzu\isuzu-ppt-template\assets\template.pptx"

prs=Presentation(TEMPLATE)
while prs.slides:
    rId=prs.slides._sldIdLst[0].rId; prs.part.drop_rel(rId); del prs.slides._sldIdLst[0]

def bg(s): f=s.background.fill; f.solid(); f.fore_color.rgb=WHITE
def txt(s,t,l,top,w,h,size=14,bold=False,color=BLACK,align=PP_ALIGN.LEFT,font="Calibri",italic=False):
    b=s.shapes.add_textbox(l,top,w,h); tf=b.text_frame; tf.word_wrap=True
    for i,ln in enumerate(t.split("\n")):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph(); p.alignment=align
        r=p.add_run(); r.text=ln; r.font.size=Pt(size); r.font.bold=bold; r.font.italic=italic
        r.font.color.rgb=color; r.font.name=font
    return b
def rect(s,l,t,w,h,c,rounded=False):
    sh=s.shapes.add_shape(5 if rounded else 1,l,t,w,h); sh.fill.solid()
    sh.fill.fore_color.rgb=c; sh.line.fill.background(); sh.shadow.inherit=False; return sh
def oval(s,l,t,w,h,c):
    sh=s.shapes.add_shape(9,l,t,w,h); sh.fill.solid(); sh.fill.fore_color.rgb=c
    sh.line.fill.background(); sh.shadow.inherit=False; return sh
def logo(s,l=Inches(0.28),t=Inches(6.80),size=18): txt(s,"ISUZU",l,t,Inches(2),Inches(0.55),size=size,bold=True,color=RED,font="Arial Black")
def footer(s): rect(s,0,SH-Inches(0.13),SW,Inches(0.13),RED)
def wave(s):
    oval(s,Inches(6.2),Inches(3.5),Inches(9.5),Inches(6.0),LIGHT_RED)
    oval(s,Inches(4.2),Inches(4.7),Inches(11.5),Inches(5.0),RED); footer(s)
def cover(title,sub):
    s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s); wave(s)
    txt(s,"ISUZU",Inches(0.38),Inches(0.22),Inches(2),Inches(0.55),size=30,bold=True,color=RED,font="Arial Black")
    txt(s,title,Inches(0.45),Inches(2.45),Inches(7.6),Inches(2.0),size=40,bold=True,color=BLACK)
    txt(s,sub,Inches(0.45),Inches(5.30),Inches(7.0),Inches(0.5),size=15,color=GRAY); return s
def content(title):
    s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s); logo(s); footer(s)
    txt(s,title,Inches(0.28),Inches(0.30),Inches(12.77),Inches(0.72),size=30,bold=True,color=BLACK)
    rect(s,Inches(0.28),Inches(1.02),Inches(12.77),Emu(38100),RED); return s
def closing():
    s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
    txt(s,"Moving the World – for You",Inches(2.5),Inches(2.80),Inches(8.5),Inches(0.65),size=18,color=GRAY,align=PP_ALIGN.CENTER)
    txt(s,"ISUZU",Inches(1.5),Inches(3.20),Inches(10.5),Inches(2.1),size=100,bold=True,color=RED,align=PP_ALIGN.CENTER,font="Arial Black")
def body(s,items,x=Inches(0.6),y=Inches(1.5),w=Inches(12.1),size=17,gap0=11):
    b=s.shapes.add_textbox(x,y,w,Inches(5.2)); tf=b.text_frame; tf.word_wrap=True
    for i,(lvl,lead,rest) in enumerate(items):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph(); p.space_after=Pt(gap0 if lvl==0 else 5)
        mark="•  " if lvl==0 else "      –  "; sz=size if lvl==0 else size-2
        r0=p.add_run(); r0.text=mark; r0.font.size=Pt(sz); r0.font.color.rgb=(RED if lvl==0 else GRAY); r0.font.bold=(lvl==0); r0.font.name="Calibri"
        if lead:
            r1=p.add_run(); r1.text=lead+(" " if rest else ""); r1.font.size=Pt(sz); r1.font.bold=True; r1.font.color.rgb=BLACK; r1.font.name="Calibri"
        if rest:
            r2=p.add_run(); r2.text=rest; r2.font.size=Pt(sz); r2.font.color.rgb=BLACK; r2.font.name="Calibri"
    return b
def scell(c,t,size=12,bold=False,color=BLACK,fill=WHITE,align=PP_ALIGN.LEFT):
    c.margin_top=Pt(3);c.margin_bottom=Pt(3);c.margin_left=Pt(7);c.margin_right=Pt(7);c.vertical_anchor=MSO_ANCHOR.MIDDLE
    c.fill.solid(); c.fill.fore_color.rgb=fill; tf=c.text_frame; tf.word_wrap=True
    p=tf.paragraphs[0]; p.alignment=align; r=p.add_run(); r.text=t
    r.font.size=Pt(size); r.font.bold=bold; r.font.color.rgb=color; r.font.name="Calibri"
def table(s,rows,x,y,w,col_w,bs=12,hs=12):
    nr,nc=len(rows),len(rows[0]); g=s.shapes.add_table(nr,nc,x,y,w,Inches(0.4*nr)).table
    for j,cw in enumerate(col_w): g.columns[j].width=cw
    g.first_row=False; g.horz_banding=False
    for i,row in enumerate(rows):
        for j,val in enumerate(row):
            c=g.cell(i,j); al=PP_ALIGN.LEFT if j==0 else PP_ALIGN.CENTER
            if i==0: scell(c,val,size=hs,bold=True,color=WHITE,fill=RED,align=al)
            else:
                tot=row[0].lower().startswith(("total","vs "))
                scell(c,val,size=bs,bold=row[0].lower().startswith("total"),color=BLACK,
                      fill=(MGRAY if row[0].lower().startswith("total") else (LGRAY if i%2==0 else WHITE)),align=al)
    return g

# 1 COVER
cover("ISZE – UTI Meeting","Parts programme  ·  UIO  ·  Genuine Parts Share & PMS      |      June 2026")
# 2 AGENDA
s=content("Agenda")
body(s,[(0,"Parts programme (SPA)","– aligning the basket and the flexibility we can offer."),
        (0,"BP FY27","– where the year stands today."),
        (0,"UIO reconciliation","– confirming the active parc together."),
        (0,"Genuine Parts Share (GPS) & PMS","– the capture opportunity and how we run it."),],y=Inches(1.7),size=19,gap0=16)
# 3 BP FY27
s=content("BP FY27 – where the year stands")
table(s,[["FY27 (€K)","Apr","May","YTD"],["Sales","211","191","402"],["Budget","247","235","482"],
        ["vs Budget","−14%","−19%","−17%"],["Prior year","294","286","580"],
        ["vs Prior year","−28%","−33%","−31%"],["Order intake","182","238","420"]],
      Inches(0.6),Inches(1.45),Inches(6.4),[Inches(2.5),Inches(1.3),Inches(1.3),Inches(1.3)],bs=13,hs=13)
body(s,[(0,"Soft start:","YTD sales €402K — −17% vs budget, −31% vs last year."),
        (0,"Both months below plan","(Apr −14%, May −19%)."),
        (0,"Order intake turning up:","May €238K vs €182K in April."),
        (0,"Full-year budget €3.1M","(prior year €2.9M) — recovery builds from here."),],
     x=Inches(7.4),y=Inches(1.55),w=Inches(5.6),size=15,gap0=12)
# 4 SPA
s=content("Parts programme (SPA)")
body(s,[(0,"","We modelled 53 part numbers together to build a sustainable, competitive programme."),
        (0,"","Current total volumes are lower than before, which makes the agreed targets harder to reach for both sides."),
        (0,"Flexibility from our side:","we can run the programme over a 6-month period rather than a full year."),
        (0,"Two ways to work it:","line by line, or on the total basket – whichever fits UTI's purchasing best."),
        (0,"","The aim is a programme that stays competitive for UTI and viable for ISZE."),],y=Inches(1.55),size=17,gap0=12)
# 5 LINES
s=content("Two lines to review together")
body(s,[(0,"NOx sensor (8983528481):","the largest single line in the basket."),
        (1,"","A high share of this line moves through warranty rather than retail sales."),
        (1,"","We propose reviewing the warranty volume together before fixing a programme price."),
        (0,"EGR cooler / valve:","included specifically to help address parallel-import competition."),
        (1,"","These are genuine-only parts, so the programme price is about defending against grey imports, not the aftermarket."),],y=Inches(1.55),size=17,gap0=12)
# 6 THREAD
s=content("How the topics connect")
steps=[("1","Sales down","YTD −31% vs last year"),("2","SPA flexibility","defend price on contested lines"),
       ("3","Filter mix vs ITUK","fuel+air BVP today · ~€65K revenue if genuine"),("4","Needs accurate UIO","to size capture on the real parc")]
bx,by,bw,bh,gap=Inches(0.45),Inches(2.45),Inches(2.85),Inches(2.3),Inches(0.32)
for i,(num,t,sub) in enumerate(steps):
    x=Emu(int(bx)+i*(int(bw)+int(gap)))
    rect(s,x,by,bw,bh,LGRAY,rounded=True); rect(s,x,by,bw,Inches(0.18),RED)
    oval(s,Emu(int(x)+int(Inches(0.2))),Emu(int(by)+int(Inches(0.35))),Inches(0.62),Inches(0.62),RED)
    txt(s,num,Emu(int(x)+int(Inches(0.2))),Emu(int(by)+int(Inches(0.43))),Inches(0.62),Inches(0.5),size=22,bold=True,color=WHITE,align=PP_ALIGN.CENTER)
    txt(s,t,Emu(int(x)+int(Inches(0.18))),Emu(int(by)+int(Inches(1.15))),Emu(int(bw)-int(Inches(0.36))),Inches(0.7),size=15,bold=True,color=BLACK)
    txt(s,sub,Emu(int(x)+int(Inches(0.18))),Emu(int(by)+int(Inches(1.65))),Emu(int(bw)-int(Inches(0.36))),Inches(0.6),size=12,color=GRAY)
    if i<3: txt(s,"›",Emu(int(x)+int(bw)+int(Inches(0.02))),Emu(int(by)+int(Inches(0.85))),Inches(0.3),Inches(0.6),size=30,bold=True,color=RED,align=PP_ALIGN.CENTER)
txt(s,"One logic: a softer market makes price flexibility and capturing more of the existing parc's demand the two ways to protect the business — both depend on knowing the real UIO.",Inches(0.5),Inches(5.1),Inches(12.3),Inches(0.9),size=15,color=BLACK)
# 7 INVISIBLE MARKET
s=content("The invisible market")
body(s,[(0,"Every Isuzu in operation generates predictable parts demand.",""),
        (0,"","Today, neither ISZE nor our distributors can see how much of that demand we actually capture."),
        (0,"","This is our first attempt to make it visible — and an invitation to refine it together."),],y=Inches(1.7),size=19,gap0=22)
# 8 MIX
s=content("Filters: UTI buys BVP where ITUK buys genuine")
table(s,[["Filter","UTI genuine","ITUK genuine"],
        ["Fuel filter","~0%","80%"],["Air filter","~0%","85%"],
        ["Oil filter","~0%","71%"],["Brake pad","97%","100%"]],
      Inches(0.6),Inches(1.6),Inches(6.2),[Inches(2.4),Inches(1.9),Inches(1.9)],bs=13,hs=12)
body(s,[(0,"UTI is 89% genuine overall","– BVP is ~11% of spend. But within parts that HAVE a BVP option, UTI takes BVP 82% of the time; ITUK only 21%."),
        (0,"Filters are the gap:","UTI buys air/fuel/oil ~100% as BVP; ITUK runs them 71–85% genuine – proof the genuine sale holds."),
        (0,"The prize is the fuel filter:","~11,400 BVP units/yr; at genuine pricing ≈ +€54K revenue. Air filter ≈ +€11K."),
        (0,"Leave oil filter on BVP:","the genuine oil element is a cheaper commodity – converting loses money."),],
     x=Inches(7.0),y=Inches(1.55),w=Inches(6.0),size=13,gap0=10)
txt(s,"2025 · classified from the BVP catalog crossref (authoritative). Revenue uplift = UTI BVP filter volume × (network genuine price − UTI BVP price).",
    Inches(0.6),Inches(6.55),Inches(12.2),Inches(0.4),size=9,color=MGRAY)
# 9 SPEND PER UNIT
s=content("GPS – parts spend per vehicle (history)")
cd=CategoryChartData(); cd.categories=["2023","2024","2025"]; cd.add_series("Spend per unit (€)",(331,249,313))
gf=s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED,Inches(0.6),Inches(1.5),Inches(7.2),Inches(4.6),cd)
ch=gf.chart; ch.has_legend=False; pl=ch.plots[0]; pl.has_data_labels=True
pl.data_labels.number_format='€0'; pl.data_labels.number_format_is_linked=False
pl.data_labels.font.size=Pt(13); pl.data_labels.font.bold=True
for sr in pl.series: sr.format.fill.solid(); sr.format.fill.fore_color.rgb=RED
body(s,[(0,"","Parts spend per vehicle dipped in 2024, recovered in 2025."),
        (0,"2025 ≈ €313/unit,","still below the 2023 level of €331."),
        (0,"On a parc of ≈ 10,700 units","— so small per-unit moves scale quickly."),
        (0,"","The PMS gap shows where the next per-unit gains sit."),],x=Inches(8.1),y=Inches(1.7),w=Inches(4.9),size=15,gap0=12)
# 10 HOW WE RUN IT
s=content("How we run it with UTI")
body(s,[(0,"","We run the genuine-parts capture exercise for every ISZE market in FY27, starting at ISZE → distributor level."),
        (0,"","At a later stage it can extend to lower (dealer) levels; UTI is welcome to run the same view at their own level."),
        (0,"Two lenses, per market:",""),
        (1,"Items comparison","– within your market, which categories you capture best and where the gap is."),
        (1,"Anonymised peer view","– similar parc, different coverage – what moves the needle."),
        (0,"Phased:","Q1 data & method · Q2 coverage · Q3 action plans · Q4 implementation – and it depends on confirmed UIO."),],y=Inches(1.55),size=16,gap0=10)
# 11 UIO start
s=content("UIO reconciliation – our starting point")
body(s,[(0,"","We are locking our units-in-operation (active parc) figures market by market, and would like to confirm UTI's directly before we close the numbers."),
        (0,"Our current model estimate for Israel, end-2025:",""),
        (1,"N-Series:","6,444 units"),(1,"F-Series:","4,809 units"),
        (0,"","These are derived from IML cumulative shipment data applied to a survival curve – not registration totals – so your local view may differ."),],y=Inches(1.55),size=17,gap0=12)
# 12 UIO ask
s=content("UIO reconciliation – what would help us")
body(s,[(0,"Active parc as of 31/12/2025","– operating vehicles only, not cumulative registrations."),
        (0,"CV N- and F-series","– split by tonnage level, if possible."),
        (0,"Source of the data","– registration authority, your own records, or an estimate."),
        (0,"Any local scrap or de-registration rate","you use internally."),
        (0,"Anything that makes your market diverge from our curve","– used imports, exports, road conditions, registration practices."),
        (0,"Timing:","information would be welcome by the beginning of next week."),],y=Inches(1.5),size=16,gap0=10)
# 13 NEXT STEPS
s=content("Next steps")
body(s,[(0,"UIO:","UTI to share active parc as of 31/12/2025, by the beginning of next week."),
        (0,"SPA:","confirm the straightforward lines; review NOx warranty volume together; agree 6-month or full term, line-by-line or total."),
        (0,"GPS / PMS:","confirm participation and level; share category sales and the real brake / clutch replacement intervals so we can size the gap together."),],y=Inches(1.7),size=18,gap0=14)
# 14 CLOSING
closing()

out=r"C:\Users\jerom\Desktop\claude\ISZE\Preparation Meetings\UTI\UTI_Meeting_June2026.pptx"
try: prs.save(out); print("saved",out)
except PermissionError:
    alt=out.replace(".pptx","_NEW.pptx"); prs.save(alt); print("LOCKED - saved",alt)
