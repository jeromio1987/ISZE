import os, re, json, html, datetime, sys
ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"
DASH = os.path.join(ROOT, "02_dashboards")
HUBDIR = os.path.join(DASH, "hub")
OUT = os.path.join(HUBDIR, "ISZE_Intelligence_Hub.html")

SKIP_PARTS = ("archive", "backsafe", "qa", "propertiq", "ids_all_dashboards", "bak", "composable", "design", "_ui", "audit")
def skip(rel):
    parts = rel.lower().replace("\\", "/").split("/")
    for p in parts[:-1]:
        if p.startswith("_") or any(s in p for s in SKIP_PARTS):
            return True
    f = parts[-1]
    if ".bak" in f or "_qa" in f or f.startswith("_") or f.startswith("OPEN_".lower()):
        return True
    return False

def title_of(path):
    try:
        with open(path, "rb") as fh:
            b = fh.read(120000)
        try:
            raw = b.decode("utf-8")
        except UnicodeDecodeError:
            raw = b.decode("cp1252", "replace")
    except Exception:
        return None
    m = re.search(r"<title[^>]*>(.*?)</title>", raw, re.S | re.I)
    if m:
        t = html.unescape(re.sub(r"\s+", " ", m.group(1))).strip()
        if t:
            return t
    return None

def clean(t):
    t = re.sub(r"(?i)sell[- ]?out", "sales to dealer", t)
    return t

def human(fn):
    b = os.path.splitext(fn)[0]
    b = re.sub(r"^ISZE_", "", b)
    return b.replace("_", " ")

def receipt_ok(path):
    base = os.path.splitext(path)[0]
    for cand in (base + ".SHIP_RECEIPT.json",):
        if os.path.exists(cand):
            try:
                j = json.load(open(cand, encoding="utf-8"))
                if j.get("ok") is True and os.path.getmtime(cand) >= os.path.getmtime(path) - 1:
                    return "checked"
                return "stale"
            except Exception:
                return "stale"
    return "none"

AREAS = [
    ("price", "Price list and revisions", "What happens to margin when the price list moves?", "pricing"),
    ("aim", "AIM, parts tree and sales", "Which parts sit at which AIM level, and how do sales compare by distributor?", "aim"),
    ("capture", "What we capture", "How much of the expected service spend do we actually bill?", "capture"),
    ("comp", "Competitor prices", "Where is our price against the aftermarket?", "comp"),
    ("net", "Network and supply", "Who are the dealers, what is open, what is coming?", "net"),
    ("ctrl", "Control room", "Where does everything stand and how is it connected?", "ctrl"),
]

def classify(rel, title):
    r = rel.lower().replace("\\", "/")
    t = (title or "").lower()
    f = os.path.basename(r)
    s = r + " " + t
    if re.search(r"pbi|power bi", s) and not r.startswith("hub/"):
        return "aim"
    if re.search(r"parc_cohort|universe_opportunity", f):
        return "net"
    if re.search(r"warranty_intelligence", f):
        return "capture"
    if r.startswith("hub/") or r.startswith("ops/") and re.search(r"os_|action_ledger|data_map|model_map|ai_|legal|console|roadmap|board|universe", f):
        return "ctrl"
    if "04_tools/autodoc" in r or re.search(r"aftermarket|\biam\b|competitor|partgroups|eucon|eurocarparts|autodoc", s):
        return "comp"
    if re.search(r"gps|pms|kosha|capture|gap analysis|md_pack", s) and not r.startswith("ids/"):
        return "capture"
    if r.startswith("ids/") or r.startswith("fleet/") or r.startswith("globe/") or "tender" in s or re.search(r"backlog|logistic|replenish|dealer|opex|fill_rate|fill rate|bo_fill|dpd|warehouse", s):
        return "net"
    if re.search(r"\baim\b|aim_|atlas|classification|category_vs|parts_tree|our_tree|tonnage|family_evolution|parts_performance", s):
        return "aim"
    if re.search(r"gps|pms|kosha|capture|uio|md_pack|mainz|wallet|runway|defection", s):
        return "capture"
    if r.startswith("pricing/") or re.search(r"price|pricing|spa_|spa |revision|simulator", s):
        return "price"
    if r.startswith("ops/"):
        return "net"
    if r.startswith("sales/"):
        return "aim"
    return "ctrl"

OUTSCOPE = ("france", "spain", "italy", "switzerland", "poland", "serbia", "midi", "turkey")

items = []
for dp, dn, fn in os.walk(DASH):
    rel_dir = os.path.relpath(dp, DASH)
    if rel_dir == ".":
        rel_dir = ""
    for f in fn:
        if not f.lower().endswith(".html"):
            continue
        rel = os.path.join(rel_dir, f) if rel_dir else f
        if skip(rel):
            continue
        full = os.path.join(dp, f)
        if os.path.abspath(full) == os.path.abspath(OUT):
            continue
        if os.path.getsize(full) < 3000:
            continue
        items.append((rel.replace("\\", "/"), full, "dash"))

EXTRA = [
    "autodoc_scraper/_html_previews/isze_executive_dashboard.html",
    "autodoc_scraper/_html_previews/isze_executive_iam.html",
    "autodoc_scraper/_html_previews/isze_executive_pms.html",
    "autodoc_scraper/_html_previews/isze_iam_drift_trend.html",
    "autodoc_scraper/_html_previews/isze_pms_iam_bridge.html",
    "autodoc_scraper/_html_previews/iam_matrix_broadsheet.html",
    "autodoc_scraper/_html_previews/iam_matrix_plex.html",
    "ISZE_Tender_Monitor_Install/00_EXEC_ONE_PAGER.html",
    "ISZE_Tender_Monitor_Install/isze_dashboard_v2.html",
    "ISZE_Tender_Monitor_Install/isze_dashboard_v4_opportunity.html",
    "ISZE_Tender_Monitor_Install/review/ISZE_Tender_Review.html",
]
for e in EXTRA:
    full = os.path.join(ROOT, "04_tools", e.replace("/", os.sep))
    if os.path.exists(full):
        items.append(("04_tools/" + e, full, "tool"))

rows = []
for rel, full, kind in items:
    if any(m in os.path.basename(full).lower() for m in OUTSCOPE) or rel.startswith("side/"):
        continue
    t = title_of(full)
    fn = os.path.basename(full)
    area = classify(rel if kind == "dash" else rel, t)
    if kind == "tool" and "tender" in rel.lower():
        area = "net"
    if kind == "tool" and "autodoc" in rel.lower():
        area = "comp"
    href = ("../" + rel) if kind == "dash" else ("../../" + rel)
    st = os.stat(full)
    rows.append(dict(
        rel=rel, full=full, href=href, title=clean(t or human(fn)), fn=fn, area=area, kind=kind,
        size=st.st_size, mtime=datetime.date.fromtimestamp(st.st_mtime).isoformat(),
        rc=receipt_ok(full), midi=False,
        folder=os.path.dirname(rel) or "root"))

# group IDS country pages
def is_ids_country(r):
    return r["rel"].startswith("ids/") and re.search(r"dealer_compare_[A-Za-z_]+\.html$", r["fn"]) and r["fn"] != "IDS_2026_dealer_compare.html"

ids_country = [r for r in rows if is_ids_country(r)]
rows_main = [r for r in rows if not is_ids_country(r)]

# collapse older versions: keep pages but flag
def esc(x):
    return html.escape(x, quote=True)

FACETS = [
    ("ITUK", r"ituk"), ("IUK", r"\biuk\b|_iuk"), ("UTI", r"\buti\b|_uti"), ("UMI", r"\bumi\b|_umi"),
    ("Ireland", r"ireland"), ("Greece", r"greece"), ("Portugal", r"portugal"), ("Nordics", r"nordic|sweden|norway|denmark|finland"),
    ("Brakes", r"brake|pad|disc|shoe"), ("Filters", r"filter"), ("Clutch", r"clutch"), ("Oil", r"\boil\b|lubric"),
    ("Water pump", r"water.?pump"), ("Steering", r"steering"),
]
DIST = {"ITUK","IUK","UTI","UMI","Ireland","Greece","Portugal","Nordics"}
_vis_cache = {}
def visible_text(path):
    try:
        raw = open(path, "rb").read().decode("utf-8", "ignore")
    except Exception:
        return ""
    raw = re.sub(r"(?is)<(script|style).*?</>", " ", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    return html.unescape(raw).lower()
def facets_of(r):
    s = (r["title"] + " " + r["fn"]).lower()
    vis = visible_text(r["full"])
    out = []
    for n, p in FACETS:
        if re.search(p, s):
            out.append(n); continue
        c = len(re.findall(p, vis))
        if c >= (8 if n in DIST else 40):
            out.append(n)
    return out

AREA_INDEX = {a[0]: a for a in AREAS}
counts = {a[0]: 0 for a in AREAS}
for r in rows_main:
    counts[r["area"]] += 1
counts["net"] += len(ids_country)

# headline numbers: verified snapshot only
snap = json.load(open(os.path.join(ROOT, "01_data", "00_derived", "metrics_snapshot.json"), encoding="utf-8"))["metrics"]
ver = json.load(open(os.path.join(ROOT, "01_data", "00_derived", "_verification_report.json"), encoding="utf-8"))["summary"]
def g(k): return snap[k]["value"]
heads = dict(
    base=g("sales.parts_base_eur"), through=g("sales.parts_base_data_through"),
    gps=g("waterfall.network.gps_pct_2025"), billed=g("waterfall.network.captured_eur_2025"),
    target=g("waterfall.network.wallet_eur_2025"), runway=g("runway.network.wallet_eur_2030"),
    alerts=g("defection.active_alerts"), asof=snap["sales.parts_base_eur"] and json.load(open(os.path.join(ROOT,"01_data","00_derived","metrics_snapshot.json"),encoding="utf-8"))["as_of"][:10],
    vpass=ver["pass"], vfail=ver["fail"], vok=ver["ok"])
M = lambda v: "EUR %.1fM" % (v / 1e6)

def card(r):
    fc = facets_of(r)
    badge = {"checked": '<span class="b ok" data-tip="A ship receipt exists and covers this file version.">checked</span>',
             "stale": '<span class="b warn" data-tip="A receipt exists but is older than the file.">receipt old</span>',
             "none": '<span class="b none" data-tip="No render receipt on disk for this page. It may be fine, nobody has recorded it.">not receipt-checked</span>'}[r["rc"]]
    mid = '<span class="b midi" data-tip="MIDI network page. Not in your own book.">MIDI</span>' if r["midi"] else ""
    sz = "%.1f MB" % (r["size"] / 1e6) if r["size"] > 1e6 else "%d KB" % (r["size"] // 1024)
    return ('<a class="card" href="%s" data-area="%s" data-f="%s" data-q="%s">'
            '<div class="ct">%s</div><div class="cm">%s &middot; %s &middot; %s<br>%s</div><div class="cb">%s%s</div></a>') % (
        esc(r["href"]), r["area"], esc("|".join(fc)), esc((r["title"] + " " + r["fn"] + " " + r["folder"]).lower()),
        esc(r["title"]), esc(r["folder"]), r["mtime"], sz, esc(r["fn"]), badge, mid)

sections = []
for key, name, q, _ in AREAS:
    rs = sorted([r for r in rows_main if r["area"] == key], key=lambda r: (r["folder"], r["title"]))
    groups = {}
    for r in rs:
        m = re.match(r"^(.*?)\s+v(\d+)$", r["title"])
        base = m.group(1) if m else r["title"]
        groups.setdefault(base, []).append((int(m.group(2)) if m else 1, r))
    shown, old = [], []
    for base, lst in groups.items():
        lst.sort(key=lambda x: x[0], reverse=True)
        shown.append(lst[0][1])
        old += [x[1] for x in lst[1:]]
    shown.sort(key=lambda r: (r["folder"], r["title"]))
    cards = "\n".join(card(r) for r in shown)
    if old:
        cards += '<details class="old"><summary>%d older versions</summary><div class="grid">%s</div></details>' % (len(old), "\n".join(card(r) for r in old))
    extra = ""
    if key == "net" and ids_country:
        links = "".join('<a class="chip%s" href="%s" data-q="%s">%s</a>' % (
            " midi" if r["midi"] else "", esc(r["href"]),
            esc(r["fn"].lower()), esc(re.sub(r"IDS_2026_dealer_compare_", "", os.path.splitext(r["fn"])[0]).replace("_", " ")))
            for r in sorted(ids_country, key=lambda r: r["fn"]))
        extra = ('<div class="ids"><h4>IDS dealer compare, one page per country (%d)</h4>'
                 '<div class="chips">%s</div></div>') % (len(ids_country), links)
    sections.append(
        '<section id="%s" class="area"><header><h2>%s</h2><p>%s</p><span class="n">%d pages</span></header>'
        '<div class="grid">%s</div>%s</section>' % (key, esc(name), esc(q), counts[key], cards, extra))

def tile(key, big, small, tip):
    a = AREA_INDEX[key]
    return ('<a class="tile" href="#%s"><div class="tn">%s</div><div class="tq">%s</div>'
            '<div class="tk" data-tip="%s">%s</div><div class="ts">%s</div><div class="tc">%d pages</div></a>') % (
        key, esc(a[1]), esc(a[2]), esc(tip), esc(big), esc(small), counts[key])

_sims = sorted([r for r in rows_main if re.match(r"^Price Revision Simulator v\d+$", r["title"])], key=lambda r: int(re.search(r"v(\d+)$", r["title"]).group(1)))
_sim = _sims[-1] if _sims else None
tiles = [
    tile("price", (_sim["title"].replace("Price Revision ", "") if _sim else "Price pages"), "Latest price revision tool, file dated %s. No headline figure here: the result depends on the move you enter." % (_sim["mtime"] if _sim else "n/a"),
         "Opens the pricing pages. No number is shown because none is fixed until a move is chosen."),
    tile("aim", "AIM Parts Atlas v2.0", "Parts tree by AIM level, plus distributor comparison. Figures live inside each page.",
         "No single headline figure on this tile. Each page carries its own."),
    tile("capture", "%.1f%% GPS" % heads["gps"], "2025 network: we billed %s of %s target spend." % (M(heads["billed"]), M(heads["target"])),
         "GPS = what we billed divided by the GPS target spend. Source: wallet_waterfall.csv via metrics_snapshot.json, snapshot %s." % heads["asof"]),
    tile("comp", "IAM price pages", "Aftermarket price tracking and the service-schedule link. Figures live inside each page.",
         "Tracking comes from the aftermarket price scraper. No headline figure is fixed on this tile."),
    tile("net", "%d active alerts" % heads["alerts"], "Accounts flagged as slipping, data through Aug 2026.",
         "Defection alerts. Source: defection_alerts.csv via metrics_snapshot.json. Counts accounts whose billing pattern has turned, not lost euros."),
    tile("ctrl", "%d checks, %d failed" % (heads["vpass"] + 1, heads["vfail"]), "Data checks behind every number on these pages.",
         "Pass %d, warning 1, fail %d, from _verification_report.json. The one warning: older years of one workbook have unfilled Denmark rows." % (heads["vpass"], heads["vfail"])),
]

CHAIN = [("price", "Price list"), ("aim", "AIM level"), ("capture", "Capture"), ("comp", "Competitors"), ("net", "Network"), ("ctrl", "Control room")]

facet_names = [n for n, p in FACETS]
fchips = "".join('<button class="fc" data-f="%s">%s</button>' % (esc(n), esc(n)) for n in facet_names)

CSS = """
:root{--navy:#15233c;--terra:#c0552d;--paper:#f7f4ee;--ink:#222;--pale:#eef3f9;--line:#d9d3c7;--mut:#5b6575;--bg:#f7f4ee;--card:#fff}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#0f1829;--card:#18253d;--ink:#eee8dc;--pale:#1c2b46;--line:#2c3b58;--mut:#9aa7bd}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,Segoe UI,Arial,sans-serif}
h1,h2,h3,h4{font-family:Georgia,serif;margin:0}
.top{background:var(--navy);color:var(--paper);padding:28px 16px 22px}
.wrap{max-width:1240px;margin:0 auto;padding:0 16px}
.top h1{font-size:30px;color:var(--paper)}.top p{margin:6px 0 0;color:#d9d4c8;max-width:760px}
.top .asof{margin-top:10px;font-size:12.5px;color:#b8c0cf}
nav.chain{position:sticky;top:0;z-index:20;background:var(--navy);border-top:1px solid #2a3b5c;border-bottom:3px solid var(--terra)}
nav.chain .wrap{display:flex;gap:0;overflow-x:auto;align-items:center}
nav.chain a{color:var(--paper);text-decoration:none;padding:11px 14px;font-size:13.5px;white-space:nowrap;border-right:1px solid #2a3b5c}
nav.chain a:hover{background:var(--terra);color:#fff}
nav.chain .arrow{color:#8091ad;padding:0 2px}
.tools{margin:18px auto 6px}
.tools input{width:100%;padding:11px 14px;font-size:15px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--ink)}
.fcs{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px;align-items:center}.fcs span{font-size:12.5px;color:var(--mut);margin-right:4px}
.fc{border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:14px;padding:4px 11px;font-size:12.5px;cursor:pointer}
.fc.on{background:var(--navy);color:var(--paper);border-color:var(--navy)}
.tiles{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:18px auto}@media (max-width:900px){.tiles{grid-template-columns:repeat(2,minmax(0,1fr))}}@media (max-width:560px){.tiles{grid-template-columns:minmax(0,1fr)}}
.tile{display:block;text-decoration:none;color:var(--ink);background:var(--card);border:1px solid var(--line);border-top:4px solid var(--terra);border-radius:6px;padding:14px}
.tile:hover{border-top-color:var(--navy);box-shadow:0 2px 10px rgba(0,0,0,.12)}
.tn{font-family:Georgia,serif;font-size:16px;color:var(--navy)}@media (prefers-color-scheme: dark){:root:not([data-theme="light"]) .tn{color:var(--paper)}}
.tq{font-size:12.5px;color:var(--mut);margin:3px 0 10px;min-height:34px}
.tk{font-family:Georgia,serif;font-size:21px;color:var(--terra);cursor:help;position:relative;display:inline-block}
.ts{font-size:12.5px;margin-top:4px}.tc{font-size:11.5px;color:var(--mut);margin-top:8px}
[data-tip]{position:relative}
[data-tip]:hover::after{content:attr(data-tip);position:absolute;left:0;top:calc(100% + 6px);z-index:50;background:var(--navy);color:var(--paper);border-left:3px solid var(--terra);padding:8px 10px;font:12px/1.4 system-ui,sans-serif;width:270px;border-radius:4px;box-shadow:0 4px 14px rgba(0,0,0,.3);white-space:normal;font-style:normal}
.area{margin:30px 0}
.area header{border-bottom:2px solid var(--navy);padding-bottom:8px;margin-bottom:12px;display:flex;flex-wrap:wrap;gap:4px 14px;align-items:baseline}
.area header h2{font-size:22px;color:var(--navy)}@media (prefers-color-scheme: dark){:root:not([data-theme="light"]) .area header h2{color:var(--paper)}}
.area header p{margin:0;color:var(--mut);flex:1 1 300px}.area header .n{font-size:12.5px;background:var(--navy);color:var(--paper);padding:2px 9px;border-radius:10px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(285px,100%),1fr));gap:10px}
.card{display:block;text-decoration:none;color:var(--ink);background:var(--card);border:1px solid var(--line);border-left:4px solid var(--navy);border-radius:5px;padding:10px 12px}
.card:hover{border-left-color:var(--terra);box-shadow:0 2px 8px rgba(0,0,0,.12)}
.ct{font-weight:600;font-size:14px;line-height:1.3}.cm{font-size:11.5px;color:var(--mut);margin:3px 0 6px;word-break:break-all}
.b{font-size:11px;padding:1px 7px;border-radius:9px;margin-right:5px;cursor:help;display:inline-block}
.b.ok{background:#dbeedd;color:#1d4a28}.b.warn{background:#f6e6c7;color:#6b4a0a}.b.none{background:var(--pale);color:var(--mut);border:1px solid var(--line)}.b.midi{background:#e8e3f3;color:#3b2a66}
.ids{margin-top:14px;background:var(--pale);border:1px solid var(--line);border-radius:6px;padding:12px}
.ids h4{font-size:15px;margin-bottom:8px;color:var(--navy)}@media (prefers-color-scheme: dark){:root:not([data-theme="light"]) .ids h4{color:var(--paper)}}
.chips{display:flex;flex-wrap:wrap;gap:6px}.chip{font-size:12.5px;text-decoration:none;background:var(--card);color:var(--ink);border:1px solid var(--line);padding:3px 10px;border-radius:12px}
.chip:hover{background:var(--terra);color:#fff;border-color:var(--terra)}.chip.midi{border-style:dashed}
.link{margin:34px 0;background:var(--card);border:1px solid var(--line);border-radius:6px;padding:16px}
.link h3{font-size:18px;color:var(--navy);margin-bottom:6px}@media (prefers-color-scheme: dark){:root:not([data-theme="light"]) .link h3{color:var(--paper)}}
.flow{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:8px 0}.flow a{background:var(--navy);color:var(--paper);text-decoration:none;padding:6px 12px;border-radius:4px;font-size:13px}
.flow a:hover{background:var(--terra)}.flow i{color:var(--mut);font-style:normal}
footer{background:var(--navy);color:#cfd5e0;padding:18px 16px;font-size:12.5px;margin-top:30px}footer a{color:#f1c4b1}
.hide{display:none!important}.old{grid-column:1/-1;margin-top:6px}.old summary{cursor:pointer;color:var(--mut);font-size:13px}.old .grid{margin-top:8px}
.empty{display:none;padding:16px;color:var(--mut)}
@media (max-width:600px){.top h1{font-size:24px}}
"""

JS = """
(function(){
var q=document.getElementById('q'),on={};
function run(){var s=(q.value||'').toLowerCase().trim(),any=Object.keys(on).length>0,shown=0;
 document.querySelectorAll('.card').forEach(function(c){
  var ok=(!s||c.dataset.q.indexOf(s)>-1);
  if(ok&&any){var f=(c.dataset.f||'').split('|');ok=Object.keys(on).every(function(k){return f.indexOf(k)>-1})}
  c.classList.toggle('hide',!ok);if(ok)shown++});
 document.querySelectorAll('.chip').forEach(function(c){c.classList.toggle('hide',!!s&&c.dataset.q.indexOf(s)<0||any)});
 document.querySelectorAll('.area').forEach(function(a){
  var v=a.querySelectorAll('.card:not(.hide)').length+a.querySelectorAll('.chip:not(.hide)').length;
  a.classList.toggle('hide',(s||any)&&v===0)});
 document.getElementById('cnt').textContent=(s||any)?shown+' matching dashboards (country pages count in the chips)':'';}
q.addEventListener('input',run);
document.querySelectorAll('.fc').forEach(function(b){b.addEventListener('click',function(){
 var k=b.dataset.f;if(on[k]){delete on[k];b.classList.remove('on')}else{on[k]=1;b.classList.add('on')}run()})});
})();
"""

total = len(rows)
page = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ISZE Intelligence Hub</title><style>%s</style></head><body>
<div class="top"><div class="wrap"><h1>ISZE Intelligence Hub</h1>
<p>Every live dashboard in one place, grouped by the question it answers. Start with the six tiles, open an area, then open the page. Search or pick a distributor or part family to see every page that mentions it, across all areas.</p>
<div class="asof">%d pages listed. Headline figures come from the checked data snapshot of %s (parts billed through %s). Built %s.</div></div></div>
<nav class="chain"><div class="wrap">%s</div></nav>
<div class="wrap">
<div class="tiles">%s</div>
<div class="tools"><input id="q" type="search" placeholder="Search all pages: a distributor, a part family, a topic (for example UTI, brake, replenishment)" aria-label="Search dashboards">
<div class="fcs"><span>Show only pages about:</span>%s</div><div id="cnt" class="empty" style="display:block;font-size:12.5px;padding:6px 0"></div></div>
%s
<div class="link"><h3>How the areas connect</h3>
<div class="flow">%s</div>
<p style="margin:6px 0 0;color:var(--mut);font-size:13.5px">The price list sets what a distributor pays. AIM says which parts the move touches. Capture says how much of the expected service spend we bill today. Competitor prices show how far the aftermarket sits from us. The network shows who buys and what is open. Use the filter chips above to follow one distributor or one part family through every area.</p></div>
</div>
<footer><div class="wrap">Pages marked "not receipt-checked" have no render check on disk. They may be fine; nobody has recorded it. The filter chips match the page title, or words shown on the page (8 or more mentions for a distributor, 40 for a part family). They do not look inside hidden data. Figures on the tiles are from <code>01_data/00_derived/metrics_snapshot.json</code> (%s).</div></footer>
<script>%s</script></body></html>""" % (
    CSS, total, heads["asof"], heads["through"], datetime.date.today().isoformat(),
    "".join('<a href="#%s">%s</a>%s' % (k, esc(n), '<span class="arrow">&rsaquo;</span>' if i < len(CHAIN) - 1 else "") for i, (k, n) in enumerate(CHAIN)),
    "\n".join(tiles), fchips, "\n".join(sections),
    "".join('<a href="#%s">%s</a>%s' % (k, esc(n), "<i>&rarr;</i>" if i < len(CHAIN) - 1 else "") for i, (k, n) in enumerate(CHAIN)),
    heads["asof"], JS)

open(OUT, "w", encoding="utf-8").write(page)
open(os.path.join(HUBDIR, "OPEN_ISZE_Intelligence_Hub.cmd"), "w", newline="\r\n").write('@echo off\nstart "" "%~dp0ISZE_Intelligence_Hub.html"\n')
print("pages", total, "ids_country", len(ids_country), counts)
print("receipts", {k: sum(1 for r in rows if r["rc"] == k) for k in ("checked", "stale", "none")})
print("bytes", os.path.getsize(OUT))
