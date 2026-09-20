/* House stylesheet for the distributor leakage tool.
 * Editorial palette: navy #15233c, terracotta #c0552d, paper #f7f4ee, Georgia headings.
 * Contrast rule enforced by construction: every dark surface sets a light text colour
 * and every pale surface sets ink, so a later class cannot wash out a header.
 */

export const CSS = `
:root{
  --navy:#15233c; --navy-2:#1c2f4d; --navy-3:#26406a;
  --paper:#f7f4ee; --surface:#fff; --ink:#22201d; --text:#5f6b80; --muted:#8b97ab;
  --line:#e3dcd1; --terra:#c0552d; --terra-lit:#e0714a; --terra-soft:#f7ece5;
  --green:#2c6e49; --green-soft:#e8f1ea; --amber:#a86412; --amber-soft:#fdf3e0;
  --rose:#9b2c2c; --rose-soft:#fbeaea;
  --shadow:0 1px 2px rgba(21,35,60,.06),0 6px 18px rgba(21,35,60,.05);
  --radius:10px;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);
  font:15px/1.55 "Inter","Segoe UI",Helvetica,Arial,sans-serif;}
h1,h2,h3,h4,.serif{font-family:Georgia,"Times New Roman",serif;font-weight:normal;letter-spacing:.005em}
h1{font-size:30px;margin:0 0 6px;color:var(--navy)}
h2{font-size:22px;margin:0 0 4px;color:var(--navy)}
h3{font-size:16px;margin:0 0 8px;color:var(--navy)}
h4{font-size:13.5px;margin:0 0 6px;color:var(--navy);text-transform:uppercase;letter-spacing:.07em;
   font-family:"Inter","Segoe UI",sans-serif;font-weight:700}

/* ---------- chrome ---------- */
header.top{position:sticky;top:0;z-index:60;background:var(--navy);color:var(--paper);
  padding:12px 26px;display:flex;align-items:center;justify-content:space-between;gap:18px;flex-wrap:wrap}
header.top .wm{font-family:Georgia,serif;font-size:21px;letter-spacing:.02em;color:var(--paper);
  line-height:1.15}
header.top .wm b{color:var(--terra-lit);font-weight:normal}
header.top .wm small{display:block;font:600 9.5px/1.4 "Inter",sans-serif;letter-spacing:.2em;
  text-transform:uppercase;color:var(--muted);margin-top:2px}
header.top .tools{display:flex;align-items:center;gap:9px;flex-wrap:wrap}
.badge{font:700 10px/1 "Inter",sans-serif;letter-spacing:.1em;text-transform:uppercase;
  padding:6px 11px;border-radius:999px;white-space:nowrap}
.badge.int{background:rgba(224,113,74,.2);color:#ffc7ae}
.badge.cust{background:rgba(44,110,73,.28);color:#a7e3bd}
header.top label{font:600 10px/1 "Inter",sans-serif;letter-spacing:.09em;text-transform:uppercase;color:var(--muted)}
header.top select{background:var(--navy-2);color:var(--paper);border:1px solid rgba(139,151,171,.4);
  border-radius:8px;padding:7px 10px;font:13px "Inter",sans-serif;max-width:230px}
nav.mods{display:flex;gap:6px;flex-wrap:wrap;max-width:1280px;margin:0 auto;padding:16px 26px 0}
nav.mods a{font:600 11px/1 "Inter",sans-serif;letter-spacing:.06em;text-transform:uppercase;
  padding:8px 12px;border-radius:8px;text-decoration:none;color:var(--navy);
  border:1px solid var(--line);background:var(--surface);white-space:nowrap}
nav.mods a:hover{border-color:var(--terra);color:var(--terra)}
nav.mods a.on{border-color:var(--terra);background:var(--terra-soft);color:var(--terra)}
main{max-width:1280px;margin:0 auto;padding:18px 26px 70px}
section{margin:0 0 34px;scroll-margin-top:78px}
.panel{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);
  padding:20px 22px;box-shadow:var(--shadow)}
.panel>.q{font:italic 15px/1.5 Georgia,serif;color:var(--terra);margin:0 0 14px}
.sub{font-size:13.5px;color:var(--text);margin:6px 0 16px;max-width:80ch}
.note{font-size:11.5px;color:var(--text);margin-top:14px;line-height:1.55;max-width:95ch}
.foot{max-width:1280px;margin:0 auto;padding:0 26px 60px;color:var(--text);font-size:12px;line-height:1.6}
.foot code{font-size:11px;background:#efe9df;padding:1px 5px;border-radius:4px;color:#4a4436}
.foot a{color:var(--navy)}

/* ---------- KPI cards ---------- */
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));gap:11px;margin:0 0 20px}
.kpi{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);
  padding:13px 15px;position:relative}
.kpi.dark{background:var(--navy);border-color:var(--navy);color:var(--paper)}
.kpi.dark .kpi-l{color:#b6c4d8}
.kpi.dark .kpi-v{color:var(--paper)}
.kpi.dark .kpi-s{color:#a9b9d0}
.kpi-l{display:block;font:600 10.5px/1.35 "Inter",sans-serif;letter-spacing:.07em;
  text-transform:uppercase;color:var(--text)}
.kpi-v{display:block;font-family:Georgia,serif;font-size:25px;line-height:1.15;margin:5px 0 2px;color:var(--navy)}
.kpi-v.sm{font-size:19px}
.kpi-s{display:block;font-size:11.5px;color:var(--text);line-height:1.4}
.kpi-s.pos{color:var(--green);font-weight:600}
.kpi-s.neg{color:var(--terra);font-weight:600}
[data-tip]{cursor:help;position:relative}
[data-tip]:hover::after,[data-tip]:focus::after{
  content:attr(data-tip);position:absolute;left:0;bottom:calc(100% + 8px);z-index:90;
  width:min(330px,72vw);padding:9px 11px;background:var(--navy);color:var(--paper);
  font:12px/1.45 "Inter",sans-serif;border-radius:8px;border-left:3px solid var(--terra);
  white-space:normal;text-align:left;box-shadow:0 8px 24px rgba(21,35,60,.25);pointer-events:none}
[data-tip].tip-r:hover::after{left:auto;right:0}

/* ---------- banners ---------- */
.banner{border-radius:0 8px 8px 0;padding:11px 15px;font-size:13px;margin:0 0 16px;line-height:1.5}
.banner.amber{background:var(--amber-soft);border-left:3px solid var(--amber);color:#5c4517}
.banner.info{background:#eef2f8;border-left:3px solid var(--navy-3);color:#2c3d59}
.banner.rose{background:var(--rose-soft);border-left:3px solid var(--rose);color:#6d2020}
.banner b{font-weight:700}
.empty{color:var(--text);font-style:italic;padding:14px 0;margin:0}

/* ---------- horizontal bars ---------- */
.hb{margin:0}
.hb-row{display:grid;grid-template-columns:minmax(120px,190px) 1fr minmax(96px,auto);
  align-items:center;gap:11px;padding:4px 0}
.hb-row+.hb-row{border-top:1px solid #f2ece3}
.hb-lab{font-size:13px;color:var(--ink);text-align:right;overflow-wrap:anywhere}
.hb-track{background:#f0eae1;border-radius:4px;height:17px;position:relative;overflow:hidden}
.hb-fill{height:100%;background:var(--terra);border-radius:4px;min-width:3px}
.hb-fill.alt{background:var(--navy-3)}
.hb-fill.pos{background:var(--green)}
.hb-fill.neg{background:var(--terra);opacity:.5}
.hb-ref{position:absolute;top:-2px;bottom:-2px;width:2px;background:var(--navy);opacity:.55}
.hb-val{font:600 12.5px/1.3 "Inter",sans-serif;font-variant-numeric:tabular-nums;color:var(--navy);
  white-space:nowrap;text-align:right}
.hb-val .u{display:block;font-weight:400;font-size:10.5px;color:var(--text)}
.hb-sub{font-size:11px;color:var(--text);font-weight:400;display:block;margin-top:1px}
.hb-lg{grid-template-columns:minmax(120px,190px) 1fr minmax(150px,auto)}
.hb-legend{display:flex;gap:14px;flex-wrap:wrap;font-size:11.5px;color:var(--text);margin:2px 0 12px}
.hb-legend i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px;vertical-align:-1px}
.hb-axis{display:flex;justify-content:space-between;font-size:10.5px;color:var(--muted);
  border-top:1px solid var(--line);margin-top:2px;padding-top:4px}

/* ---------- change bars (year on year) ----------
   Fixed headroom above and below the plot so a value label at the extreme is never clipped,
   and the year row plus caption sit in their own flow rows so nothing can overlap. */
.cb2{margin:0 0 6px}
.cb2-plot{display:flex;align-items:stretch;gap:10px;height:200px;position:relative;
  border-bottom:1px solid var(--line)}
.cb2-col{flex:1;min-width:38px;position:relative}
.cb2-zero{position:absolute;left:0;right:0;top:50%;border-top:1px solid #cfc6b8}
.cb2-bar{position:absolute;left:8%;right:8%;border-radius:3px;min-height:3px}
.cb2-bar.up{background:var(--green)}
.cb2-bar.dn{background:var(--terra)}
.cb2-val{position:absolute;left:0;right:0;text-align:center;
  font:700 11.5px/1 "Inter",sans-serif;font-variant-numeric:tabular-nums;color:var(--navy);
  white-space:nowrap}
.cb2-xrow{display:flex;gap:10px;margin-top:6px}
.cb2-xrow span{flex:1;min-width:38px;text-align:center;font:600 11px/1.3 "Inter",sans-serif;
  color:var(--text);overflow-wrap:anywhere}
.cb2-cap{margin-top:8px;font-size:11.5px;color:var(--muted);line-height:1.5}

/* ---------- line chart ---------- */
.lc{margin:2px 0 6px}
.lc svg{display:block;width:100%;height:auto}
.lc circle{cursor:help}

/* ---------- stacked bars ---------- */

/* ---------- in-panel selector ---------- */
.selctl{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:4px 0 14px}
.selctl label{font:700 10.5px/1 "Inter",sans-serif;letter-spacing:.07em;text-transform:uppercase;
  color:var(--text)}
.selctl select{padding:7px 11px;border:1px solid var(--line);border-radius:8px;
  background:var(--surface);color:var(--ink);font:13.5px "Inter",sans-serif;min-width:230px;
  max-width:100%}
.selctl select:hover{border-color:var(--terra)}

/* ---------- KPI cards ---------- */
.stk{display:flex;gap:12px;align-items:flex-end;height:170px;margin:6px 0 4px;
  border-bottom:1px solid var(--line)}
.stk-col{flex:1;min-width:30px;max-width:104px;height:100%;display:flex;flex-direction:column;
  justify-content:flex-end;position:relative}
.stk-seg{width:100%;min-height:2px}
.stk-x{position:absolute;top:100%;left:0;right:0;text-align:center;font:600 11px/1.4 "Inter",sans-serif;
  color:var(--text);padding-top:5px}
.stk-tot{position:absolute;top:-17px;left:0;right:0;text-align:center;font:600 10.5px/1 "Inter",sans-serif;
  color:var(--text);font-variant-numeric:tabular-nums}

/* ---------- donut ---------- */
.donut{display:flex;align-items:center;gap:22px;flex-wrap:wrap}
.donut svg{flex:0 0 auto}
.donut-key{font-size:12.5px;line-height:1.75;color:var(--ink)}
.donut-key i{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:7px;vertical-align:-1px}
.donut-key b{font-variant-numeric:tabular-nums}

/* ---------- trend rows / small multiples ---------- */
.tr{margin:0}
.tr-row{display:grid;grid-template-columns:minmax(130px,196px) 1fr minmax(118px,auto);
  align-items:center;gap:11px;padding:5px 0;border-top:1px solid #f2ece3}
.tr-row:first-child{border-top:none}
.tr-lab{font-size:12.5px;text-align:right;color:var(--ink);overflow-wrap:anywhere}
.tr-lab .u{display:block;font-size:10.5px;color:var(--text)}
.tr-cells{display:grid;grid-auto-flow:column;grid-auto-columns:1fr;gap:4px;height:34px;align-items:end}
.tr-cell{display:flex;flex-direction:column;justify-content:flex-end;height:100%;position:relative}
.tr-bar{width:100%;border-radius:2px 2px 0 0;min-height:2px;background:var(--navy-3)}
.tr-bar.weak{background:var(--terra)}
.tr-bar.good{background:var(--green)}
.tr-yr{font:400 9.5px/1 "Inter",sans-serif;color:var(--muted);text-align:center;padding-top:3px}
.tr-val{font:600 11.5px/1.3 "Inter",sans-serif;font-variant-numeric:tabular-nums;text-align:right;color:var(--navy)}
.tr-val .d{display:block;font-size:10.5px;font-weight:400;color:var(--text)}
.tr-head{display:grid;grid-template-columns:minmax(130px,196px) 1fr minmax(118px,auto);gap:11px;
  font:600 10px/1 "Inter",sans-serif;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);
  padding-bottom:5px;border-bottom:1px solid var(--line)}
.tr-head .c{text-align:right}

/* ---------- tables ---------- */
.tw{overflow-x:auto;margin:0 -2px}
table{border-collapse:collapse;width:100%;font-size:12.5px}
th,td{padding:7px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:var(--navy);color:var(--paper);font:700 10px/1.35 "Inter",sans-serif;
  letter-spacing:.07em;text-transform:uppercase;white-space:nowrap;position:sticky;top:0;z-index:2}
th.s,td.num{text-align:right;font-variant-numeric:tabular-nums}
td.lbl{font-weight:600;color:var(--navy)}
tbody tr:nth-child(odd) td{background:#fdfcfa}
tbody tr:nth-child(even) td{background:var(--surface)}
tbody tr.focus td{background:var(--terra-soft)}
tbody tr:hover td{background:#f6f1e9}
tfoot td{background:#efe9df;font-weight:700;color:var(--navy)}
td .u{display:block;font-size:10.5px;color:var(--text);font-weight:400}
caption{caption-side:top;text-align:left;font-size:11.5px;color:var(--text);padding-bottom:7px}

/* ---------- pills ---------- */
.pill{display:inline-block;font:700 10px/1 "Inter",sans-serif;letter-spacing:.06em;text-transform:uppercase;
  padding:3px 7px;border-radius:999px;white-space:nowrap;vertical-align:1px}
.pill.ok{background:var(--green-soft);color:var(--green)}
.pill.watch{background:var(--amber-soft);color:var(--amber)}
.pill.crit{background:var(--rose-soft);color:var(--rose)}
.pill.info{background:#eef2f8;color:var(--navy-3)}
.pill.mute{background:#f0eae1;color:var(--text)}
.pill+.pill{margin-left:4px}
.dnarrow{font-size:12px;color:var(--green);font-weight:700}
.uparrow{font-size:12px;color:var(--terra);font-weight:700}

/* ---------- heat cells ---------- */
.hm td.cell{text-align:right;font-variant-numeric:tabular-nums;font-weight:600}
.hm td.c1{background:#fbece6;color:#7d2f14}
.hm td.c2{background:#fdf1e9;color:#8a4a20}
.hm td.c3{background:#fbf6ea;color:#7a6420}
.hm td.c4{background:#f0f4ee;color:#3c5c42}
.hm td.c5{background:#e5efe6;color:#245037}
.hm td.cn{background:#f5f2ed;color:var(--muted);font-weight:400}

/* ---------- picker ---------- */
.picker{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);
  padding:16px 18px;box-shadow:var(--shadow)}
.pickbar{display:flex;align-items:center;gap:11px;flex-wrap:wrap;margin-bottom:11px}
.pick-lbl{font:700 10px/1 "Inter",sans-serif;letter-spacing:.08em;text-transform:uppercase;
  color:var(--text);min-width:118px}
.gbtns{display:flex;gap:6px;flex-wrap:wrap}
.gbtn{font:500 12px "Inter",sans-serif;padding:6px 11px;border:1px solid var(--line);border-radius:999px;
  background:var(--surface);color:var(--ink);cursor:pointer}
.gbtn:hover:not(.dis){border-color:var(--terra);color:var(--terra)}
.gbtn.on{border-color:var(--terra);background:var(--terra-soft);color:var(--terra);font-weight:700}
.gbtn .n{color:var(--text);font-size:10.5px;margin-left:3px}
.gbtn.dis{opacity:.42;cursor:not-allowed}
.chips{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:12px}
.chip{display:inline-flex;align-items:center;gap:6px;font-size:12px;padding:5px 10px;
  border:1px solid var(--line);border-radius:7px;background:var(--surface);cursor:pointer}
.chip.on{border-color:var(--terra);background:var(--terra-soft);font-weight:700}
.chip input{margin:0;cursor:pointer}
.chip .sc{font:600 9.5px/1 "Inter",sans-serif;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}
.sel-note{font-size:11.5px;color:var(--text)}

/* ---------- misc ---------- */
.cols2{display:grid;grid-template-columns:1fr 1fr;gap:22px}
.cols3{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}
.stack>*+*{margin-top:20px}
.dl{display:grid;grid-template-columns:minmax(150px,232px) 1fr;gap:4px 16px;font-size:13px}
.dl dt{font-weight:700;color:var(--navy);padding-top:3px}
.dl dd{margin:0;padding-top:3px;color:var(--ink)}
.hr{border:0;border-top:1px solid var(--line);margin:20px 0}
code.k{font:11.5px "SFMono-Regular",Consolas,monospace;background:#efe9df;padding:1px 5px;
  border-radius:4px;color:#4a4436}

@media (max-width:900px){
  .cols2,.cols3{grid-template-columns:1fr}
  .dl{grid-template-columns:1fr;gap:1px 0}
  .dl dd{margin-bottom:9px}
  .hb-row,.hb-lg{grid-template-columns:minmax(96px,1fr) 1.1fr minmax(80px,auto);gap:8px}
  h1{font-size:24px} h2{font-size:19px}
  .hb-val{font-size:11.5px}
}
/* The small-multiples row is a grid with two fixed tracks. At narrow widths the sum of the
   minimum track sizes exceeds the panel and the grid overflows without the container
   reporting it, so the row is restacked rather than shrunk. */
@media (max-width:760px){
  .tr-head{display:none}
  .tr-row{grid-template-columns:1fr;gap:3px;padding:7px 0;
          border-top:1px solid var(--line)}
  .tr-lab{text-align:left;font-weight:600}
  .tr-val{text-align:left;margin-top:3px}
  .tr-val .d{display:inline;margin-left:8px}
  .tr-cells{height:30px}
}
@media (max-width:620px){
  main{padding:12px 13px 60px} header.top{padding:10px 14px} nav.mods{padding:12px 13px 0}
  .hb-row{grid-template-columns:1fr;gap:3px}
  .hb-lab{text-align:left}
  .hb-track{height:14px}
  .hb-val{text-align:left}
}
@media print{
  header.top{position:static;background:var(--navy) !important;-webkit-print-color-adjust:exact;print-color-adjust:exact}
  nav.mods{display:none}
  .panel{box-shadow:none;break-inside:avoid}
  section{break-inside:avoid}
  body{background:#fff}
}
`;
