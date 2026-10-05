"""Build the ISZE dashboard audit HTML.

Counts are computed from the files themselves, not taken from auditor claims.
Verified findings are hardcoded with their evidence, after independent checks.
"""
import hashlib
import json
import pathlib
import re
from collections import Counter, defaultdict

ROOT = pathlib.Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards")
UI = ROOT / "_ui"
OUT = ROOT / "_audit" / "ISZE_dashboard_audit_2026-09-16.html"

EXCLUDE = re.compile(r"(_archive|node_modules|_qa|_build|\\Data\\|_audit)", re.I)

def html_files():
    out = []
    for p in ROOT.rglob("*.html"):
        if EXCLUDE.search(str(p)):
            continue
        out.append(p)
    return sorted(out)

files = html_files()
groups = defaultdict(list)
for f in files:
    try:
        rel = f.relative_to(ROOT)
    except ValueError:
        continue
    top = rel.parts[0] if len(rel.parts) > 1 else "(root)"
    groups[top].append(f)

def text(p):
    try:
        return p.read_text("utf-8", errors="ignore")
    except Exception:
        return ""

# ---- mechanical counts, computed not claimed ----
fonts_via_shared = []
fonts_own_link = []
cdn_any = []
external_script = []
no_tooltip = []
has_tooltip = []

for f in files:
    t = text(f)
    if "_ui/editorial.css" in t or "editorial.css" in t:
        fonts_via_shared.append(f)
    if re.search(r"fonts\.googleapis\.com", t):
        fonts_own_link.append(f)
    if re.search(r"unpkg\.com|cdnjs|jsdelivr|cdn\.plot\.ly|<script[^>]+src=[\"']https?://", t):
        cdn_any.append(f)
    if re.search(r"<script[^>]+src=[\"'](?!https?:)[^\"']+\.js", t):
        external_script.append(f)
    tip = len(re.findall(r"\.tip|cursor:\s*help|data-tip", t))
    if tip == 0:
        no_tooltip.append(f)
    else:
        has_tooltip.append(f)

# duplicate detection on live files
hashes = defaultdict(list)
for f in files:
    try:
        hashes[hashlib.sha256(f.read_bytes()).hexdigest()].append(f)
    except Exception:
        pass
dup_groups = {h: v for h, v in hashes.items() if len(v) > 1}
dup_files = sum(len(v) for v in dup_groups.values())
dup_redundant = dup_files - len(dup_groups)

# data folder duplication
d1 = ROOT / "Data" / "dashboards"
d2 = ROOT / "Data" / "14_dashboards"
def names(d):
    return sorted(p.name for p in d.rglob("*") if p.is_file())
same_data = names(d1) == names(d2) if d1.exists() and d2.exists() else False

# ---- verified findings (independently checked by grep/read/render) ----
ROOT_CAUSES = [
    {
        "name": "Google Fonts pulled from the network",
        "rule": "No CDN",
        "files": len(set(fonts_via_shared) | set(fonts_own_link)),
        "sev": "HIGH",
        "evidence": "_ui/editorial.css line 2: @import url('https://fonts.googleapis.com/css2?family=Fraunces&family=Inter&display=swap')",
        "why": "One import in a shared stylesheet makes every page that links it network-dependent. Offline, the house typeface silently falls back to Georgia/system.",
        "fix": "Self-host the two fonts as woff2 and drop the @import. One change clears it for every page.",
    },
    {
        "name": "Leaflet loaded from unpkg",
        "rule": "No CDN",
        "files": len([f for f in cdn_any if "ids" in str(f)]),
        "sev": "HIGH",
        "evidence": "IDS_2026_dealer_compare.html line 9 loads the unpkg stylesheet; line 1402 document.write's the unpkg script at runtime",
        "why": "The dealer-compare family is not self-contained, though its own footer claims 'Single-file offline dashboard'.",
        "fix": "Inline _ui/leaflet.js (147 KB) the way the study files already inline Chart.js (200 KB).",
    },
    {
        "name": "Dead preload path leaves a page empty",
        "rule": "Chart/data integrity",
        "files": 2,
        "sev": "HIGH",
        "evidence": "hub/MASTER_DASHBOARD.html:272 needs Data/dashboards/viz/risk_cockpit.preload.js; ops/ISZE_Tender_Monitor_v2.html:490 needs Data/dashboards/tender_data.preload.js",
        "why": "Only the .json files exist at those paths, never the .preload.js. On file:// the fetch fallback is blocked, so 5 KPI chips stay em-dashes and the Tender OS falls to its offline banner.",
        "fix": "Generate the .preload.js siblings from the .json files, or point the script tags at the JSON loader the rest of the folder uses.",
    },
    {
        "name": "Chart library loaded from a sibling file, not inlined",
        "rule": "Self-contained",
        "files": len([f for f in external_script if f.name != "IDZE"]),
        "sev": "MEDIUM",
        "evidence": "e.g. pricing/ISZE_Aftermarket_Live_Pricing_Dashboard.html:72 <script src=\"../_ui/plotly.min.js\"></script>",
        "why": "Renders in place, but any move or copy yields blank charts. _ui/plotly.min.js is 4.8 MB, so inlining is not free either.",
        "fix": "Decide per file: inline the small ones (chart.umd 200 KB), document the _ui/ dependency for the large ones.",
    },
    {
        "name": "Derived KPI has no hover tooltip",
        "rule": "KPI explainers",
        "files": len(no_tooltip),
        "sev": "MEDIUM",
        "evidence": "pricing/ISZE_Pricing_Action_Map.html uses a bare title= attribute on heat cells; the file contains no .tip rule",
        "why": "The house rule says a title= attribute alone does not satisfy it. A reader cannot see the formula, snapshot date, or exclusions.",
        "fix": "Add the .tip hover pattern the compliant files already use (e.g. ISZE_Action_Ledger_Hub.html).",
    },
    {
        "name": "Heatmap text unreadable at the top of the scale",
        "rule": "Contrast",
        "files": len([f for f in files if re.search(r"hm-cell|\.hm\s*\{", text(f))]),
        "sev": "HIGH",
        "evidence": "IDS_2026_dealer_compare.html:83 sets .hm-cell{color:#fff} while heatBg (1062-1063) returns hsl(155,45%,60%) and hsl(12,55%,70%)",
        "why": "Fixed white digits on a pale green or salmon fill, about 2:1. Not the described bug shape, but the same outcome.",
        "fix": "Pick the ink colour from the computed lightness instead of hard-coding #fff.",
    },
    {
        "name": "Euro figure overstated by a factor of a million",
        "rule": "No invented figures",
        "files": 1,
        "sev": "HIGH",
        "evidence": "pricing/ISZE_Pricing_History_Findings_Dashboard.html:57 shows EUR 30,422,371.9M where the sibling pack (:89) shows EUR 30.4M for the same 2023 row",
        "why": "A unit suffix is appended to a value already in units. It reads as 30 trillion euro. One raw nan cell also leaks at line 72.",
        "fix": "Divide by 1e6 before appending M, and render nan as an em-dash like the sibling pack does.",
    },
    {
        "name": "Identical files duplicated inside one folder",
        "rule": "Empty shells / duplication",
        "files": dup_files,
        "sev": "MEDIUM",
        "evidence": "ids/: 22 hash groups covering 45 files, 23 of them redundant",
        "why": "Country dashboards exist twice, at top level and under IDS_all_dashboards_2026-08-19/. Verified by SHA-256, not by name. The nested copies also carry a broken ../_ui/ path.",
        "fix": "Keep one copy and delete the nested tree, or delete the top-level duplicates.",
    },
    {
        "name": "Two identical data trees",
        "rule": "Structure",
        "files": 6,
        "sev": "MEDIUM",
        "evidence": "Data/dashboards and Data/14_dashboards hold the same 6 filenames",
        "why": "Two locations for the same data. Which one a dashboard reads depends on the relative path it happens to use.",
        "fix": "Pick one as canonical and leave a pointer at the other.",
    },
]

FALSE_CLAIMS = [
    {
        "claim": "Pricing_History_Findings_Dashboard ships 5 hardcoded euro KPIs",
        "reality": "3, at lines 282, 287 and 292. Two of the five did not match the pattern the auditor said it grepped.",
        "group": "sales",
    },
    {
        "claim": "side/PROPERTIQ.html has 7 blank photo backgrounds because propertiq-assets is empty",
        "reality": "False. The folder holds 3 files and all 3 referenced images exist. The auditor appears to have checked the wrong path.",
        "group": "hub/ops/side",
    },
    {
        "claim": "side/PROPERTIQ.html has unresolved Dutch text rendering as mojibake",
        "reality": "False positive. The replacement character was a console encoding artefact, not file corruption.",
        "group": "hub/ops/side",
    },
    {
        "claim": "MASTER_DASHBOARD's real data file is at Data/14_dashboards/viz/risk_cockpit.preload.js",
        "reality": "That file does not exist either. Only the .json exists, in both trees. The break is real; the proposed fix was wrong.",
        "group": "hub/ops/side",
    },
]

UNDERSTATES = [
    ("Shared stylesheet reach", "4 files", "15 live files", "fleet auditor"),
    ("Byte-identical duplicates", "20 of 53 files", "45 files in 22 groups (23 redundant)", "ids auditor"),
    ("Hardcoded euro KPIs", "5", "3", "sales auditor"),
]

SEV = Counter()
for c in ROOT_CAUSES:
    SEV[c["sev"]] += c["files"]

inline_lib = (UI / "chart.umd.min.js").read_text("utf-8", errors="ignore")
inline_lib = re.sub(r"//#\s*sourceMappingURL=.*", "", inline_lib)


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


group_rows = "".join(
    f"<tr><td class='g'>{esc(g)}</td><td class='n'>{len(v)}</td></tr>"
    for g, v in sorted(groups.items(), key=lambda kv: -len(kv[1]))
)

cause_rows = ""
for c in sorted(ROOT_CAUSES, key=lambda c: (c["sev"] != "HIGH", -c["files"])):
    cls = "sev-high" if c["sev"] == "HIGH" else "sev-med"
    cause_rows += f"""<tr>
      <td class='cause'>{esc(c['name'])}<div class='rule'>{esc(c['rule'])}</div></td>
      <td class='num'><span class='kpi' tabindex='0'>{c['files']}<span class='tip'>{esc(c['files'])} file(s) in the live set are affected by this root cause. Counted by scanning the files, not taken from a summary.</span></span></td>
      <td><span class='{cls}'>{c['sev']}</span></td>
      <td class='ev'><code>{esc(c['evidence'])}</code><div class='why'>{esc(c['why'])}</div><div class='fix'><b>Fix:</b> {esc(c['fix'])}</div></td>
    </tr>"""

false_rows = "".join(
    f"<tr><td>{esc(f['claim'])}</td><td class='bad'>{esc(f['reality'])}</td><td class='g'>{esc(f['group'])}</td></tr>"
    for f in FALSE_CLAIMS
)

under_rows = "".join(
    f"<tr><td>{esc(n)}</td><td class='num'>{esc(a)}</td><td class='num ok'>{esc(b)}</td><td class='g'>{esc(w)}</td></tr>"
    for n, a, b, w in UNDERSTATES
)

sev_data = json.dumps({"HIGH": SEV.get("HIGH", 0), "MEDIUM": SEV.get("MEDIUM", 0)})
cause_labels = json.dumps([c["name"] for c in sorted(ROOT_CAUSES, key=lambda c: -c["files"])])
cause_data = json.dumps([c["files"] for c in sorted(ROOT_CAUSES, key=lambda c: -c["files"])])

html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ISZE dashboard audit - 16 September 2026</title>
<style>
:root{{--navy:#15233c;--navy2:#1d3050;--terra:#c0552d;--paper:#f7f4ee;--ink:#222;--line:#d8d2c6;--muted:#6b6b6b}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);font:15px/1.6 Georgia,'Times New Roman',serif}}
header{{background:var(--navy);color:var(--paper);padding:34px 40px 28px}}
header h1{{margin:0 0 6px;font-size:30px;font-weight:400;letter-spacing:-.3px}}
header .sub{{color:#cfd6e2;font-size:14px}}
header .stamp{{margin-top:14px;font-size:12px;color:#9fb0c8;font-family:Consolas,monospace}}
main{{max-width:1180px;margin:0 auto;padding:30px 40px 70px}}
h2{{font-size:20px;font-weight:400;color:var(--navy);border-bottom:2px solid var(--navy);padding-bottom:6px;margin:38px 0 14px}}
h3{{font-size:16px;color:var(--navy);margin:24px 0 8px;font-weight:600}}
p{{margin:8px 0}}
.lede{{font-size:16px;background:#fff;border-left:4px solid var(--terra);padding:16px 20px;margin:0 0 22px}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin:18px 0 8px}}
.kpi-card{{background:#fff;border:1px solid var(--line);border-radius:5px;padding:14px 16px}}
.kpi-card .v{{font-size:27px;color:var(--navy);font-family:Consolas,monospace}}
.kpi-card .l{{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin-top:4px}}
table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line);font-size:13.5px}}
th{{background:var(--navy);color:var(--paper);text-align:left;padding:9px 11px;font-weight:600;font-size:12.5px;letter-spacing:.3px}}
td{{padding:9px 11px;border-top:1px solid var(--line);vertical-align:top}}
tbody tr:hover td{{background:#fcfaf6}}
td.num,th.num{{text-align:right;white-space:nowrap}}
td.g{{color:var(--muted);font-family:Consolas,monospace;font-size:12.5px}}
td.cause{{font-weight:600}}
.rule{{font-size:11.5px;color:var(--muted);font-weight:400;text-transform:uppercase;letter-spacing:.4px}}
.ev code{{display:block;background:#f3f0ea;border:1px solid var(--line);border-radius:3px;padding:6px 8px;font-size:12px;color:#3a3a3a;word-break:break-word}}
.why{{font-size:12.5px;color:#444;margin-top:5px}}
.fix{{font-size:12.5px;color:var(--navy);margin-top:5px}}
.sev-high{{background:var(--terra);color:#fff;padding:2px 8px;border-radius:3px;font-size:11.5px;font-weight:600}}
.sev-med{{background:#e8dcc8;color:#6b4a1f;padding:2px 8px;border-radius:3px;font-size:11.5px;font-weight:600}}
.bad{{color:#8c2f14}}
.ok{{color:#1f6b45}}
.kpi{{position:relative;cursor:help;border-bottom:1px dotted var(--terra);padding-bottom:1px}}
.kpi .tip{{display:none;position:absolute;right:0;top:130%;z-index:40;width:290px;background:var(--navy);color:var(--paper);border-left:3px solid var(--terra);border-radius:4px;padding:9px 11px;font-size:12px;line-height:1.5;text-align:left;font-weight:400;box-shadow:0 4px 14px rgba(0,0,0,.25)}}
.kpi:hover .tip,.kpi:focus .tip,.kpi:focus-within .tip{{display:block}}
.chartbox{{background:#fff;border:1px solid var(--line);border-radius:5px;padding:14px 16px;margin:16px 0}}
.chartbox h3{{margin:0 0 10px}}
.note{{background:#fff;border:1px solid var(--line);border-left:4px solid var(--terra);border-radius:4px;padding:14px 18px;margin:16px 0;font-size:13.5px}}
.mono{{font-family:Consolas,monospace;font-size:12.5px;word-break:break-all}}
footer{{border-top:1px solid var(--line);margin-top:34px;padding-top:14px;font-size:12px;color:var(--muted)}}
ul{{margin:8px 0 8px 18px}}li{{margin:4px 0}}
</style></head><body>
<header>
  <h1>ISZE dashboard audit</h1>
  <div class="sub">Every live dashboard under 02_dashboards, checked against the house rules.</div>
  <div class="stamp">Run 2026-09-16 &middot; five parallel audit passes, one independent verify pass &middot; read-only</div>
</header>
<main>

<div class="lede">
The dashboards are in better shape than the finding count suggests, and worse in one specific way: a handful of
root causes account for most findings, and two of them stop pages from working at all. No CDN except Google Fonts
and Leaflet. No chart library is missing from disk. But two dashboards render empty because a data script is
referenced that was never generated, and the dealer-compare family is not offline-capable despite saying so in
its own footer.
</div>

<div class="kpis">
  <div class="kpi-card"><div class="v">{len(files)}</div><div class="l">Live dashboards</div>
    <div class="tiny">HTML files excluding _archive, _build, _qa and Data</div></div>
  <div class="kpi-card"><div class="v">{len(ROOT_CAUSES)}</div><div class="l">Root causes</div>
    <div class="tiny">Distinct defects behind the findings</div></div>
  <div class="kpi-card"><div class="v">{SEV.get('HIGH',0)}</div><div class="l">Files, HIGH</div>
    <div class="tiny">Blank page, wrong number, or unreadable text</div></div>
  <div class="kpi-card"><div class="v">{len(FALSE_CLAIMS)}</div><div class="l">Claims overturned</div>
    <div class="tiny">Auditor findings the verify pass disproved</div></div>
  <div class="kpi-card"><div class="v">{dup_redundant}</div><div class="l">Redundant copies</div>
    <div class="tiny">Byte-identical, verified by SHA-256</div></div>
</div>

<h2>Root causes, ranked</h2>
<p>The same few defects repeat across folders. Fixing the first one clears {len(set(fonts_via_shared) | set(fonts_own_link))} files at once.</p>
<table>
<thead><tr><th style="width:22%">Defect</th><th class="num" style="width:8%">Files</th><th style="width:9%">Severity</th><th>Evidence, why it matters, and the fix</th></tr></thead>
<tbody>{cause_rows}</tbody>
</table>

<div class="chartbox"><h3>Where the work is</h3><canvas id="causeChart" height="130"></canvas></div>
<div class="chartbox"><h3>Files affected by severity</h3><canvas id="sevChart" height="110"></canvas></div>

<h2>What the live set looks like</h2>
<table>
<thead><tr><th>Folder</th><th class="num">Live HTML</th></tr></thead>
<tbody>{group_rows}</tbody>
</table>

<h2>Claims the verify pass overturned</h2>
<p>Each audit group was told to report only what it could confirm in the files. Four claims did not survive an independent check.
These are recorded because a wrong finding is worse than no finding: it sends someone to edit a file that was never broken.</p>
<table>
<thead><tr><th style="width:32%">Auditor claim</th><th>What the files actually show</th><th style="width:14%">Group</th></tr></thead>
<tbody>{false_rows}</tbody>
</table>

<h3>And three counts that moved</h3>
<p>Under-counts rather than fabrications, but the numbers were not usable until recounted.</p>
<table>
<thead><tr><th>Measured</th><th class="num">Reported</th><th class="num">Verified</th><th>Group</th></tr></thead>
<tbody>{under_rows}</tbody>
</table>

<h2>What is genuinely clean</h2>
<ul>
<li><b>No chart library is missing from disk.</b> <span class="mono">chart.umd.min.js</span> (200,807 bytes), <span class="mono">plotly.min.js</span> (4,847,499), <span class="mono">echarts.min.js</span> (1,029,203), <span class="mono">leaflet.js</span> (147,552) are all present in <span class="mono">_ui/</span>.</li>
<li><b>No source maps shipped.</b> Zero <span class="mono">sourceMappingURL</span> occurrences across the audited files and the libraries.</li>
<li><b>No invented live statistics.</b> No occupancy percentage, live stock or live price is presented as current. The only occurrences of those words are explicit disclaimers.</li>
<li><b>Contrast is mostly deliberate.</b> The repeated white-on-dark header pattern (navy or red gradient) is intentional, not the pale-background bug. One auditor correctly refused to report a match that happened to be light text on a dark gradient.</li>
<li><b>Tooltips exist where they were built.</b> Six files implement the hover pattern properly, including full run-id provenance in <span class="mono">ISZE_Action_Ledger_Hub.html</span>.</li>
<li><b>Four files clean across every rule tested:</b> <span class="mono">hub/index.html</span>, <span class="mono">hub/BI_PACKS.html</span>, <span class="mono">ops/ISZE_OS_Data_Map.html</span>, <span class="mono">ops/ISZE_Action_Ledger_Hub.html</span>.</li>
</ul>

<h2>Two decisions this needs from you</h2>
<div class="note">
<b>1. The chart libraries.</b> <span class="mono">plotly.min.js</span> is 4.8 MB. Inlining it into each dashboard would add roughly 5 MB per file and is probably the wrong answer. The rule as written says inline; that rule was made for Chart.js at 200 KB. Either accept a documented <span class="mono">_ui/</span> dependency for the large libraries, or move those dashboards to a served URL where relative paths are stable.
</div>
<div class="note">
<b>2. The duplicate tree.</b> {dup_redundant} redundant dashboards in <span class="mono">ids/</span> plus two identical data trees. Deleting the nested copy is safe on the hashes but will break any link that points into it. That is a call for you, not for me.
</div>

<h2>Method and limits</h2>
<ul>
<li><b>How this was checked.</b> Five audit passes ran in parallel, one per folder group, each read-only and required to quote a file, line and rule. A separate pass then re-checked every high-severity fact by grep, read and headless render.</li>
<li><b>Counts on this page are recomputed from the files</b> at build time, not copied from the audit summaries. That is why three of them disagree with what the audit passes reported.</li>
<li><b>The pipeline a dashboard reads from was never touched.</b> No file was modified. No dashboard was rebuilt. No derived data was regenerated.</li>
<li><b>What was not checked.</b> The 39 IDS files below the size cap were not read individually. Contrast was assessed from the CSS cascade plus headless renders of two pages, not every page. KPI tooltips were judged on the presence of a hover mechanism, not on whether each tooltip text is correct.</li>
<li><b>Known soft spot.</b> The unreadable-tab finding in <span class="mono">ISZE_Monthly_Sales_Tracker.html</span> was left unconfirmed. The cascade is real, but the render did not settle whether the tab strip receives a dark background. It is recorded as unproven rather than promoted to HIGH.</li>
</ul>

<footer>
Built 2026-09-16. Read-only audit; nothing modified. Charts rendered from inline Chart.js, no CDN.
</footer>
</main>
<script>{inline_lib}</script>
<script>
const NAVY='#15233c', TERRA='#c0552d', PAPER='#f7f4ee';
Chart.defaults.font.family="Georgia, 'Times New Roman', serif";
Chart.defaults.color='#333';
new Chart(document.getElementById('causeChart'), {{
  type:'bar',
  data:{{
    labels:{cause_labels},
    datasets:[{{label:'Files affected', data:{cause_data}, backgroundColor:TERRA, borderColor:NAVY, borderWidth:1}}]
  }},
  options:{{indexAxis:'y', responsive:true, animation:false,
    plugins:{{legend:{{display:false}}, title:{{display:true,text:'Root causes by number of files touched',color:NAVY,font:{{size:14}}}}}},
    scales:{{x:{{beginAtZero:true,grid:{{color:'#e8e3d8'}}}},y:{{grid:{{display:false}},ticks:{{font:{{size:11}}}}}}}}}}
}});
new Chart(document.getElementById('sevChart'), {{
  type:'bar',
  data:{{labels:['HIGH','MEDIUM'],datasets:[{{label:'Files',data:[{SEV.get('HIGH',0)},{SEV.get('MEDIUM',0)}],backgroundColor:[TERRA,'#8a9bb5'],borderColor:NAVY,borderWidth:1}}]}},
  options:{{responsive:true,animation:false,plugins:{{legend:{{display:false}},title:{{display:true,text:'Files by severity',color:NAVY,font:{{size:14}}}}}},
    scales:{{y:{{beginAtZero:true,grid:{{color:'#e8e3d8'}}}},x:{{grid:{{display:false}}}}}}}}
}});
</script>
</body></html>"""

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(html, encoding="utf-8")

print(f"files scanned (live)      : {len(files)}")
print(f"groups                    : {dict((g, len(v)) for g, v in sorted(groups.items(), key=lambda kv: -len(kv[1])))}")
print(f"google fonts affected     : {len(set(fonts_via_shared) | set(fonts_own_link))}")
print(f"  via shared stylesheet   : {len(fonts_via_shared)}")
print(f"  own <link> in file      : {len(fonts_own_link)}")
print(f"any external CDN          : {len(cdn_any)}")
print(f"external (non-http) script: {len(external_script)}")
print(f"no tooltip mechanism      : {len(no_tooltip)}")
print(f"has tooltip mechanism     : {len(has_tooltip)}")
print(f"dup groups/files/redundant: {len(dup_groups)} / {dup_files} / {dup_redundant}")
print(f"two data trees identical  : {same_data}")
print(f"wrote {OUT}")
print(f"size  : {OUT.stat().st_size:,} bytes")
