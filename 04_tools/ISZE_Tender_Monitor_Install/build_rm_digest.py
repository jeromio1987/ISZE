"""Weekly R&M tender digest, one page per distributor (work order Block B, 2026-09-24).

Reads 01_data/14_dashboards/tender_data.json -> "opportunities" and writes, per
distributor that has a selected row today:

  - one self-contained HTML page (charcoal + Isuzu red, no CDN, A4 printable)
  - one CSV whose "outcome" column is empty, shaped for tender_outcomes.py

Everything lands under 04_tools/ISZE_Tender_Monitor_Install/rm_digest/<run date>/.
This script never writes into the outcome store (tender_outcomes.json), never
touches run_tender_monitor.bat and never starts a browser.

Selection (changed 2026-10-01 on Jerome's go; before that it also sent undated rows):
    decision in (Attack, Selective, Watch)
    AND (rm_contract == true OR product_segment in (pickup, truck))
    AND deadline_date >= run date

A distributor page carries dated notices only. Rows that pass everything except the
deadline (none published) go to an internal "undated" page, never to a distributor.
Rows with no distributor_code go to an internal "unassigned" page.

The same tender published on TED and on a national portal arrives as two opportunities.
Where both are selected (same country, same buyer, title words overlapping >= 50%), the
page shows one card and the CSV carries both codes with a note to give both one answer.

Run:  C:\\Python314\\python.exe build_rm_digest.py
"""
from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import html as html_lib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent          # 04_tools/ISZE_Tender_Monitor_Install
ROOT = HERE.parents[1]                          # ISZE workspace root
DEFAULT_FEED = ROOT / "01_data" / "14_dashboards" / "tender_data.json"
DIGEST_ROOT = HERE / "rm_digest"

UNASSIGNED = "__unassigned__"

# Step 5 — internal terms that must not appear on a page a distributor could receive.
BANNED_WORDS = ["AIM", "PRISM", "DLOD", "IDS", "GPS", "BVP", "IML", "ITUK", "IUK", "UMI", "UTI", "campaign"]
BANNED_LITERALS = [".csv", ".json", ".py"]
DUTCH_WORDS = ["goed", "slecht"]

DECISIONS = ("Attack", "Selective", "Watch")
VEHICLE_SEGMENTS = ("pickup", "truck")   # Isuzu-shaped vehicle purchases, sent beside R&M
TWIN_TITLE_OVERLAP = 0.5
HIGH_CONFIDENCE = 0.8          # ids_dealer_linkage.py: 0.5 = country fallback, >=0.8 = geo nearest

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


# --------------------------------------------------------------------------- helpers

def load_feed(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def parse_date(value) -> dt.date | None:
    if not value:
        return None
    try:
        return dt.date.fromisoformat(str(value).strip()[:10])
    except ValueError:
        return None


def is_rm(row: dict) -> bool:
    v = row.get("rm_contract")
    return v is True or str(v).strip().lower() == "true"


def clean(value) -> str:
    return re.sub(r"\s+", " ", str(value if value is not None else "")).strip()


# Tender portals prefix the real subject with the classification heading, e.g.
# "Repair and maintenance services of motor vehicles and associated equipment - <subject>"
# or "Germany - <subject>". Strip only headings that the feed itself repeats across
# several notices in more than one country, so a one-off phrasing is left untouched.
SEPARATOR = re.compile(r"\s+[\u2013\u2014]\s+")


def title_segments(title: str) -> list[str]:
    return [s.strip() for s in SEPARATOR.split(title)] if SEPARATOR.search(title) else [title.strip()]


def boilerplate_headings(rows) -> set:
    counts: collections.Counter = collections.Counter()
    countries: dict[str, set] = collections.defaultdict(set)
    for row in rows:
        parts = title_segments(clean(row.get("title_raw")) or clean(row.get("title")))
        if len(parts) > 1:
            counts[parts[0]] += 1
            countries[parts[0]].add(clean(row.get("country")))
    return {head for head, n in counts.items() if n >= 3 and len(countries[head]) >= 2}


def display_title(row: dict, boilerplate: set) -> str:
    raw = clean(row.get("title_raw")) or clean(row.get("title"))
    if not raw:
        return "(no title published in the notice)"
    names = {clean(row.get("country"))} | {clean(c) for c in (row.get("countries") or [])}
    parts = title_segments(raw)
    while len(parts) > 1 and (parts[0] in boilerplate or parts[0] in names):
        parts = parts[1:]
    return " - ".join(parts).strip() or raw


def fmt_amount(amount, currency) -> str:
    if amount is None or amount == "":
        return "not published"
    try:
        num = float(amount)
    except (TypeError, ValueError):
        return clean(amount)
    text = f"{int(num):,}" if float(num).is_integer() else f"{num:,.2f}"
    cur = clean(currency)
    return f"{cur} {text}" if cur else f"{text} (currency not published)"


def fmt_fleet(row: dict) -> str:
    size = row.get("fleet_size")
    if size is None or size == "":
        return "not published"
    try:
        num = float(size)
    except (TypeError, ValueError):
        return clean(size)
    text = f"{int(num):,}" if num.is_integer() else f"{num:,}"
    return f"{text} vehicles"


def fmt_deadline(day: dt.date, days_left: int) -> str:
    stamp = f"{day.day} {MONTHS[day.month - 1]} {day.year}"
    if days_left == 0:
        return f"Deadline {stamp} (closes today)"
    if days_left == 1:
        return f"Deadline {stamp} (1 day left)"
    return f"Deadline {stamp} ({days_left} days left)"


def dealer_line(row: dict) -> str:
    """Nearest Isuzu dealer only where the buyer was matched to a dealer's own area."""
    conf = row.get("ids_match_confidence")
    name = clean(row.get("ids_dealer_name"))
    if not name or conf is None:
        return ""
    try:
        high = float(conf) >= HIGH_CONFIDENCE
    except (TypeError, ValueError):
        high = False
    if not high:
        return ""
    city = clean(row.get("ids_dealer_city"))
    return f"{name} ({city})" if city else name


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return slug or "distributor"


def visible_text(page_html: str) -> str:
    """What a reader would actually see: tags, styles and scripts removed."""
    text = re.sub(r"(?is)<style.*?</style>", " ", page_html)
    text = re.sub(r"(?is)<script.*?</script>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html_lib.unescape(text)).strip()


# --------------------------------------------------------------------------- selection

def in_scope(row: dict) -> bool:
    return is_rm(row) or clean(row.get("product_segment")) in VEHICLE_SEGMENTS


def select_rows(payload: dict, run_date: dt.date):
    rows = payload.get("opportunities") or []
    stats = collections.OrderedDict()
    stats["rows_in_feed"] = len(rows)

    rm = [r for r in rows if is_rm(r)]
    stats["rm_contract_true"] = len(rm)

    scoped = [r for r in rows if in_scope(r)]
    stats["rm_or_pickup_truck"] = len(scoped)
    stats["vehicle_purchase_not_rm"] = len(scoped) - len(rm)

    decided = [r for r in scoped if clean(r.get("decision")) in DECISIONS]
    stats["in_scope_and_actionable_decision"] = len(decided)
    stats["in_scope_ignored"] = len(scoped) - len(decided)

    kept, undated, dropped_past, unparseable = [], [], 0, 0
    for row in decided:
        raw_deadline = row.get("deadline_date")
        if not raw_deadline:
            undated.append(row)
            continue
        day = parse_date(raw_deadline)
        if day is None:
            unparseable += 1
            undated.append(row)
            continue
        if day >= run_date:
            kept.append(row)
        else:
            dropped_past += 1

    stats["dropped_deadline_already_passed"] = dropped_past
    stats["deadline_unreadable"] = unparseable
    stats["selected_dated"] = len(kept)
    stats["undated_internal_only"] = len(undated)
    return kept, undated, stats


def _title_words(row: dict) -> set:
    import unicodedata
    raw = clean(row.get("title_raw")) or clean(row.get("title"))
    text = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode().lower()
    parts = title_segments(text)
    if len(parts) >= 3:              # TED: "Country - heading - subject"
        text = " ".join(parts[2:])
    return set(re.findall(r"[a-z0-9]{4,}", text))


def _is_ted(row: dict) -> bool:
    return any("EU" in str(s) for s in (row.get("sources") or []))


def find_twins(rows: list[dict]) -> dict[str, str]:
    """opportunity_id -> its twin's opportunity_id, for TED/national copies of one tender."""
    twins: dict[str, str] = {}
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            if clean(a.get("country_code")) != clean(b.get("country_code")) or _is_ted(a) == _is_ted(b):
                continue
            ba = set(re.findall(r"\w{3,}", clean(a.get("buyer")).lower()))
            bb = set(re.findall(r"\w{3,}", clean(b.get("buyer")).lower()))
            if not ba or not bb or len(ba & bb) / len(ba | bb) < 0.8:
                continue
            ta, tb = _title_words(a), _title_words(b)
            if ta and tb and len(ta & tb) / len(ta | tb) >= TWIN_TITLE_OVERLAP:
                ida, idb = clean(a.get("opportunity_id")), clean(b.get("opportunity_id"))
                if ida not in twins and idb not in twins:
                    twins[ida], twins[idb] = idb, ida
    return twins


def group_rows(dated, run_date: dt.date, feed_date: dt.date | None):
    groups: dict[str, list[dict]] = collections.defaultdict(list)
    for row in dated:
        code = clean(row.get("distributor_code")) or UNASSIGNED
        key = code if code else UNASSIGNED
        day = parse_date(row.get("deadline_date"))
        entry = dict(row)
        entry["_deadline"] = day
        entry["_days_left"] = (day - run_date).days if day else None
        entry["_stale_days"] = (run_date - feed_date).days if feed_date else None
        groups[key].append(entry)
    for key, items in groups.items():
        items.sort(key=lambda r: (
            0 if r["_deadline"] else 1,
            r["_deadline"] or dt.date.max,
            -(r.get("opportunity_score") or 0),
            clean(r.get("title")),
        ))
    return groups


# --------------------------------------------------------------------------- page build

PAGE_CSS = """
:root{--ink:#1f1f1f;--char:#232323;--red:#e60012;--line:#d8d4cd;--soft:#f6f4f0;--muted:#5f5b56}
*{box-sizing:border-box}
body{margin:0;background:#fff;color:var(--ink);
     font:10.5pt/1.45 "Segoe UI",Arial,Helvetica,sans-serif}
header.bar{background:var(--char);color:#fff;padding:14px 18px 12px;border-bottom:4px solid var(--red)}
header.bar h1{margin:0;font-size:15pt;letter-spacing:.2px}
header.bar .sub{color:#e9e5df;font-size:9.5pt;margin-top:4px}
main{padding:14px 18px 22px}
section h2{font-size:11.5pt;margin:18px 0 8px;padding-bottom:4px;
           border-bottom:2px solid var(--red);color:var(--char)}
section.first h2{margin-top:6px}
.empty{color:var(--muted);font-size:9.5pt;margin:0 0 10px}
article.op{border:1px solid var(--line);border-left:4px solid var(--red);background:var(--soft);
           padding:9px 12px 10px;margin:0 0 9px;page-break-inside:avoid;break-inside:avoid}
article.op h3{margin:0 0 2px;font-size:10.5pt;line-height:1.35}
.opnum{color:var(--red);font-weight:700;margin-right:5px}
.buyer{margin:0 0 6px;color:var(--muted);font-size:9.5pt}
ul.meta{list-style:none;margin:0;padding:0;font-size:9.5pt}
ul.meta li{display:flex;gap:8px;margin:1px 0}
.k{min-width:150px;color:var(--muted)}
.tags{display:inline-block;font-size:8.5pt;padding:1px 6px;border-radius:2px;
      background:var(--red);color:#fff;margin-left:6px;vertical-align:1px}
.tags.wait{background:var(--char)}
a.notice{display:inline-block;margin-top:6px;font-size:9.5pt;color:#a5080f;font-weight:600}
section.ask{border:2px solid var(--char);background:#fff;padding:10px 13px;margin-top:20px}
section.ask h2{margin:0 0 6px;border:none;padding:0;font-size:11.5pt;color:var(--char)}
section.ask p{margin:0 0 4px}
section.ask .words{font-weight:700;letter-spacing:.3px}
footer.note{margin:16px 18px 20px;padding-top:8px;border-top:1px solid var(--line);
            color:var(--muted);font-size:8.5pt}
@page{size:A4;margin:13mm}
@media print{
  body{font-size:10pt}
  header.bar{background:#232323 !important;-webkit-print-color-adjust:exact;print-color-adjust:exact}
  article.op,.tags,.tags.wait{background:var(--soft);-webkit-print-color-adjust:exact;print-color-adjust:exact}
  .tags{background:#e60012 !important;color:#fff !important}
  .tags.wait{background:#232323 !important;color:#fff !important}
}
"""

PAGE_SHELL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>@@PAGETITLE@@</title>
<style>@@CSS@@</style>
</head>
<body>
<header class="bar">
  <h1>@@HEADING@@ &mdash; @@DISTNAME@@</h1>
  <div class="sub">@@RUNLINE@@</div>
</header>
<main>
@@SECTIONS@@
@@CLOSING@@
</main>
<footer class="note">@@FOOTNOTE@@</footer>
</body>
</html>
"""

ASK_BOX = """<section class="ask">
  <h2>Which of these will you pursue? Answer: pursue / pass / not decided yet</h2>
  <p>Please reply with the number of the tender and one of those words.</p>
</section>
"""

INTERNAL_BOX = """<section class="ask">
  <h2>Internal page &mdash; not for a distributor</h2>
  <p>These tenders reached the list but no distributor is identified on them, so there is nobody
  to send them to. They are counted in the run summary and keep an internal number here.</p>
</section>
"""

UNDATED_BOX = """<section class="ask">
  <h2>Internal page &mdash; not for a distributor</h2>
  <p>These tenders pass every rule except one: no deadline is published, so nobody has a moment
  to decide. They no longer go to distributors. Open the notice to find a date; once the feed
  carries one, the tender moves onto the distributor's list by itself.</p>
</section>
"""


def render_card(number: int, row: dict, boilerplate: set, twin: dict | None = None) -> str:
    title = html_lib.escape(display_title(row, boilerplate), quote=True)
    kind = "Repair and maintenance" if is_rm(row) else "Vehicle purchase"
    buyer = html_lib.escape(clean(row.get("buyer")) or "(buyer not published in the notice)", quote=True)
    scope = html_lib.escape(clean(row.get("aftersales_summary")) or "not published", quote=True)
    value = html_lib.escape(fmt_amount(row.get("value_amount"), row.get("currency")), quote=True)
    fleet = html_lib.escape(fmt_fleet(row), quote=True)
    dealer = dealer_line(row)

    days_left = row.get("_days_left")
    if days_left is None:
        stamp = '<span class="tags wait">deadline not published</span>'
    else:
        stamp = f'<span class="tags">{html_lib.escape(fmt_deadline(row["_deadline"], days_left), quote=True)}</span>'

    url = clean(row.get("url"))
    link = (f'<a class="notice" href="{html_lib.escape(url, quote=True)}">Open the notice '
            f'&rarr;</a>') if url else '<span class="empty">No notice link published.</span>'

    dealer_row = (f'<li><span class="k">Nearest Isuzu dealer</span>'
                  f'<span class="v">{html_lib.escape(dealer, quote=True)}</span></li>') if dealer else ""

    twin_row = ""
    if twin:
        tday = parse_date(twin.get("deadline_date"))
        tdate = f"{tday.day} {MONTHS[tday.month - 1]} {tday.year}" if tday else "not published"
        turl = clean(twin.get("url"))
        tlink = (f' &middot; <a href="{html_lib.escape(turl, quote=True)}">open the second notice</a>'
                 if turl else "")
        twin_row = ('    <li><span class="k">Also published</span><span class="v">as a second notice '
                    f'of the same tender, deadline {html_lib.escape(tdate)}. Check which date applies.'
                    f'{tlink}</span></li>\n')

    return (
        '<article class="op">\n'
        f'  <h3><span class="opnum">{number}.</span>{title}{stamp}</h3>\n'
        f'  <p class="buyer">{buyer}</p>\n'
        '  <ul class="meta">\n'
        f'    <li><span class="k">Type</span><span class="v">{kind}</span></li>\n'
        f'    <li><span class="k">Value</span><span class="v">{value}</span></li>\n'
        f'    <li><span class="k">Fleet size</span><span class="v">{fleet}</span></li>\n'
        f'    <li><span class="k">Scope</span><span class="v">{scope}</span></li>\n'
        f'{dealer_row}\n'
        f'{twin_row}'
        '  </ul>\n'
        f'  {link}\n'
        '</article>'
    )


def number_rows(rows: list[dict], twins: dict[str, str]) -> list[tuple[int, dict, dict | None]]:
    """One number per tender. A TED/national pair gets one card: the national copy leads."""
    by_id = {clean(r.get("opportunity_id")): r for r in rows}
    out, done, number = [], set(), 0
    for row in rows:
        oid = clean(row.get("opportunity_id"))
        if oid in done:
            continue
        twin = by_id.get(twins.get(oid, ""))
        lead = row
        if twin is not None and _is_ted(row) and not _is_ted(twin):
            lead, twin = twin, row
        done.add(clean(lead.get("opportunity_id")))
        if twin is not None:
            done.add(clean(twin.get("opportunity_id")))
        number += 1
        lead["_number"] = number
        if twin is not None:
            twin["_number"] = number
        out.append((number, lead, twin))
    return out


def build_page(dist_name: str, rows: list[dict], run_date: dt.date,
               feed_date: dt.date | None, footnote: str, boilerplate: set,
               twins: dict[str, str], closing: str = "", heading: str = "") -> str:
    dated = [r for r in rows if r.get("_deadline")]
    undated = [r for r in rows if not r.get("_deadline")]

    dated.sort(key=lambda r: (r["_deadline"], r.get("_days_left")))
    undated.sort(key=lambda r: (-(r.get("opportunity_score") or 0), clean(r.get("title"))))

    parts: list[str] = []
    cards = number_rows(dated + undated, twins)
    n_dated = sum(1 for _, lead, _ in cards if lead.get("_deadline"))
    n_undated = len(cards) - n_dated

    parts.append('<section class="first">')
    if dated:
        parts.append(f'<h2>Open tenders with a published deadline ({n_dated})</h2>')
        for number, lead, twin in cards:
            if lead.get("_deadline"):
                parts.append(render_card(number, lead, boilerplate, twin))
    if undated:
        parts.append(f'<h2>Deadline not published, check the notice ({n_undated})</h2>')
        for number, lead, twin in cards:
            if not lead.get("_deadline"):
                parts.append(render_card(number, lead, boilerplate, twin))
    if not cards:
        parts.append('<p class="empty">No open tender with a published deadline today.</p>')
    parts.append('</section>')

    run_line = f"Prepared {run_date.day} {MONTHS[run_date.month - 1]} {run_date.year}"
    if feed_date:
        run_line += f" &middot; notices collected from public tender portals on {feed_date.day} {MONTHS[feed_date.month - 1]} {feed_date.year}"
    run_line += f" &middot; {len(cards)} tenders in this list"

    page = (PAGE_SHELL
            .replace("@@CSS@@", PAGE_CSS)
            .replace("@@PAGETITLE@@", html_lib.escape(f"Open fleet tenders - {dist_name}"))
            .replace("@@HEADING@@", heading or "Open fleet tenders")
            .replace("@@DISTNAME@@", html_lib.escape(dist_name))
            .replace("@@RUNLINE@@", run_line)
            .replace("@@SECTIONS@@", "\n".join(parts))
            .replace("@@CLOSING@@", closing or ASK_BOX)
            .replace("@@FOOTNOTE@@", html_lib.escape(footnote)))
    return page


# --------------------------------------------------------------------------- checks

def scan_page(page_html: str, dist_name: str) -> dict:
    text = visible_text(page_html)
    word_hits = {}
    for term in BANNED_WORDS:
        n = len(re.findall(r"(?i)\b" + re.escape(term) + r"\b", text))
        if n:
            word_hits[term] = n
    literal_hits = {}
    for term in BANNED_LITERALS:
        n = len(re.findall(re.escape(term), text, re.I))
        if n:
            literal_hits[term] = n
    dutch_hits = {}
    for term in DUTCH_WORDS:
        n = len(re.findall(r"(?i)\b" + re.escape(term) + r"\b", text))
        if n:
            dutch_hits[term] = n

    # diagnostic only: the same acronyms anywhere inside a longer word (Latin/French text)
    loose = {}
    for term in BANNED_WORDS:
        n = len(re.findall(re.escape(term), text, re.I))
        if n:
            loose[term] = n

    gate = sum(word_hits.values()) + sum(literal_hits.values()) + sum(dutch_hits.values())
    own_name_hits = len(re.findall(re.escape(dist_name), text, re.I)) if dist_name else 0
    return {
        "gate_hits": gate,
        "own_name_hits": own_name_hits,
        "word_hits": word_hits,
        "literal_hits": literal_hits,
        "dutch_hits": dutch_hits,
        "inside_longer_words_diagnostic": loose,
    }


CSV_HEADER = [
    "opportunity_id", "outcome", "status", "decision_date",
    "loss_reason", "competitor_if_known", "actual_parts_revenue_12m", "notes",
]


def write_csv(path: Path, rows: list[dict], twins: dict[str, str] | None = None) -> None:
    """Rows in page order. `notes` says which page number a row is, and names a twin, so the
    reply "3 pursue" can be typed against the right code(s). The loader skips any row whose
    outcome is empty, so these notes are never written into the store on their own."""
    twins = twins or {}
    ordered = sorted(rows, key=lambda r: (r.get("_number") or 0, _is_ted(r)))
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(CSV_HEADER)
        for row in ordered:
            oid = clean(row.get("opportunity_id"))
            note = f"page number {row.get('_number')}" if row.get("_number") else ""
            if oid in twins:
                note += f"; same tender as {twins[oid]} - give both the same answer"
            out = [oid] + [""] * (len(CSV_HEADER) - 1)
            out[CSV_HEADER.index("notes")] = note
            writer.writerow(out)


def write_text(path: Path, body: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)


INDEX_CSS = PAGE_CSS + """
table{width:100%;border-collapse:collapse;font-size:9.5pt}
th,td{border-bottom:1px solid var(--line);padding:5px 6px;text-align:left;vertical-align:top}
th{background:var(--char);color:#fff;font-weight:600}
td.num{text-align:right;white-space:nowrap}
tr.internal td{background:var(--soft)}
.internalnote{color:#a5080f;font-weight:600}
ul.notes{font-size:9.5pt}
"""


def build_index(dist_pages: list[dict], unassigned: dict, undated: dict, stats: dict,
                run_date: dt.date, feed_date: dt.date | None, feed_path: Path) -> str:
    rows_html = []
    for entry in dist_pages:
        mix = entry["decision_mix"]
        mix_text = ", ".join(f"{k} {v}" for k, v in mix.items()) if mix else "&mdash;"
        rows_html.append(
            f'<tr><td><a href="{html_lib.escape(entry["filename"], quote=True)}">'
            f'{html_lib.escape(entry["display_name"])}</a></td>'
            f'<td class="num">{entry["dated"]}</td><td class="num">{entry["undated"]}</td>'
            f'<td class="num">{entry["total"]}</td>'
            f'<td>{html_lib.escape(mix_text)}</td>'
            f'<td>{html_lib.escape(entry["earliest"] or "not published")}</td>'
            f'<td><a href="{html_lib.escape(entry["csv"], quote=True)}">outcome list</a></td></tr>'
        )
    rows_html.append(
        f'<tr class="internal"><td><a href="{html_lib.escape(unassigned["filename"], quote=True)}">'
        f'unassigned &mdash; no distributor identified (internal)</a></td>'
        f'<td class="num">{unassigned["dated"]}</td><td class="num">{unassigned["undated"]}</td>'
        f'<td class="num">{unassigned["total"]}</td>'
        f'<td>{html_lib.escape(unassigned["decision_mix_text"])}</td>'
        f'<td>{html_lib.escape(unassigned["earliest"] or "not published")}</td>'
        f'<td>no outcome list &mdash; no distributor to answer it</td></tr>'
    )
    if undated.get("filename"):
        rows_html.append(
            f'<tr class="internal"><td><a href="{html_lib.escape(undated["filename"], quote=True)}">'
            f'no deadline published &mdash; held back (internal)</a></td>'
            f'<td class="num">0</td><td class="num">{undated["total"]}</td>'
            f'<td class="num">{undated["total"]}</td>'
            f'<td>{html_lib.escape(undated["decision_mix_text"])}</td>'
            f'<td>not published</td>'
            f'<td>not sent &mdash; no moment to decide</td></tr>'
        )

    collected = (f"{feed_date.day} {MONTHS[feed_date.month - 1]} {feed_date.year}"
                 if feed_date else "date not published in the file")
    body = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Fleet tender digest - index (internal)</title>
<style>{INDEX_CSS}</style>
</head>
<body>
<header class="bar">
  <h1>Weekly fleet tender digest &mdash; index</h1>
  <div class="sub">Internal page &mdash; not for distribution to a distributor
  &middot; run {run_date.day} {MONTHS[run_date.month - 1]} {run_date.year}
  &middot; source collected {collected}</div>
</header>
<main>
  <section class="first">
    <h2>One page per distributor</h2>
    <table>
      <thead><tr><th>Distributor</th><th class="num">Dated</th><th class="num">No deadline</th>
      <th class="num">Total</th><th>Our own triage</th><th>Earliest deadline</th><th>Outcome record</th></tr></thead>
      <tbody>
      {chr(10).join(rows_html)}
      </tbody>
    </table>
  </section>
  <section>
    <h2>What this run selected</h2>
    <ul class="notes">
      <li>{stats['rows_in_feed']} opportunities in the feed; {stats['rm_or_pickup_truck']} are repair and maintenance
          ({stats['rm_contract_true']}) or a pickup or truck purchase ({stats['vehicle_purchase_not_rm']}).</li>
      <li>{stats['in_scope_and_actionable_decision']} of those carry an actionable decision; {stats['in_scope_ignored']} are marked Ignore.</li>
      <li>{stats['selected_dated']} have a deadline on or after the run date and are listed
          ({stats['twin_pairs']} of them are the same tender published twice, shown as one card).
          {stats['undated_internal_only']} have no deadline and are held back on an internal page.</li>
      <li>{stats['dropped_deadline_already_passed']} were dropped because the deadline has already passed.</li>
      <li>{unassigned['total']} listed rows have no distributor identified (internal page above).</li>
    </ul>
  </section>
  <section>
    <h2>How the outcome record works</h2>
    <ul class="notes">
      <li>Each distributor has a list beside its page with an empty <code>outcome</code> column.
          Allowed words: pursue / pass / won / lost / no decision / withdrawn.</li>
      <li>Nothing was written into the tender outcome store by this run. As of the source file,
          {stats.get('outcomes_recorded', 0)} of {stats['rows_in_feed']} opportunities carry a recorded outcome.</li>
      <li>The store is keyed on <code>opportunity_id</code>. Load a filled list with one command:
          <code>python tender_outcomes.py rm_digest/{run_date.isoformat()}</code>
          (add <code>--dry-run</code> to see the change first). See <code>README_IMPORT.md</code>.</li>
    </ul>
  </section>
</main>
<footer class="note">Internal index. Source: live tender feed
{html_lib.escape(str(feed_path))}.</footer>
</body>
</html>
"""
    return body


def build_readme(run_date: dt.date, source_name: str) -> str:
    return f"""# Weekly R&M tender digest — how to load a filled outcome list

Run date: {run_date.isoformat()}
Source: {source_name} (read only; nothing in the outcome store was written by this build)

## What each file is

- `<distributor>.html` — the page that can go to that distributor. It shows only its own name.
- `<distributor>.csv` — the outcome record for the same notices.
- `index.html` — internal index. Not for a distributor.
- `unassigned.html` — internal. Selected notices with no distributor identified.

## Filling the outcome list

Put one word in the `outcome` column of a distributor list:

| word | meaning |
|---|---|
| `pursue` | we will bid |
| `pass` | we will not bid |
| `won` | decided, we won |
| `lost` | decided, we lost |
| `no decision` | looked at, nothing decided yet |
| `withdrawn` | the buyer cancelled or never awarded it — neither a win nor a loss |

Leave `decision_date` and `notes` empty if you do not need them. Leave a row's
`outcome` empty if it has not been looked at — do not write anything else in it.

Spelling variations are folded onto the words above when they load, so `bid` counts as
`pursue` and `no-bid` counts as `pass`. A word that is not recognised is still stored and is
listed under `unrecognised_statuses`, so it can never disappear quietly.

## Loading it back — one command

From the folder that holds `tender_outcomes.py`:

```
python tender_outcomes.py rm_digest\\{run_date.isoformat()}
```

That reads every distributor list in the folder and writes the answers into the outcome store.
Add `--dry-run` first to see what would change without writing anything. The store never touches
a row that has no answer, so the command can be run again every week as replies come in.

To read the current position at any time:

```
python tender_outcomes.py --summary
```

## What the summary counts

Two different questions, kept apart on purpose:

- **`engaged`** — `pursue` plus `pass`. This is "did anyone read the list and answer?". It is
  readable after the first week of replies, long before any result exists.
- **`decided`** — `won` plus `lost` only. A tender is decided when there is a result. A pile of
  `pursue` entries is not a decision and must never be counted as one.

The win rate is `won / (won + lost)` and is shown only once that total reaches
`min_sample_for_win_rate` (20). Below that it reads `insufficient data`.
"""


LAUNCHER = '@echo off\r\nstart "" "%~dp0index.html"\r\n'


# --------------------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build the weekly R&M tender digest per distributor.")
    ap.add_argument("--feed", default=str(DEFAULT_FEED), help="tender_data.json to read")
    ap.add_argument("--date", default=None, help="run date, YYYY-MM-DD (default: today)")
    ap.add_argument("--out", default=None, help="output folder (default: rm_digest/<run date>)")
    args = ap.parse_args(argv)

    run_date = parse_date(args.date) or dt.date.today()
    feed_path = Path(args.feed)
    if not feed_path.exists():
        print(f"ERROR: feed not found: {feed_path}", file=sys.stderr)
        return 2

    payload = load_feed(feed_path)
    feed_date = parse_date((payload.get("meta") or {}).get("generated_at"))

    dated, undated, stats = select_rows(payload, run_date)
    stats["outcomes_recorded"] = ((payload.get("meta") or {}).get("outcomes_summary") or {}).get("recorded", 0)
    groups = group_rows(dated, run_date, feed_date)
    boilerplate = boilerplate_headings(dated + undated)
    twins = find_twins(dated)
    stats["twin_pairs"] = len(twins) // 2
    stats["distinct_tenders_listed"] = len(dated) - stats["twin_pairs"]

    out_dir = Path(args.out) if args.out else DIGEST_ROOT / run_date.isoformat()
    out_dir.mkdir(parents=True, exist_ok=True)

    # display names: use the distributor's own name from the file, never the code
    labels: dict[str, str] = {}
    for code, items in groups.items():
        if code == UNASSIGNED:
            continue
        label = next((clean(r.get("ids_distributor_label")) for r in items if clean(r.get("ids_distributor_label"))), "")
        labels[code] = label or code.replace("_", " ").title()

    used_slugs: dict[str, int] = {}
    pages: list[dict] = []
    footnote = ("Dealer named only where the notice buyer could be matched to that dealer's own area. "
                "Value and fleet size are shown as published in the notice; they are not our estimates.")
    if feed_date and (run_date - feed_date).days > 1:
        footnote += (f" The notices were last collected on {feed_date.day} "
                     f"{MONTHS[feed_date.month - 1]} {feed_date.year}, so check the notice before acting on a deadline.")

    ordered = sorted(groups.items(), key=lambda kv: (
        0 if kv[0] != UNASSIGNED else 1,
        -sum(1 for r in kv[1] if r.get("_deadline")),
        -len(kv[1]),
        kv[0],
    ))

    unassigned_info = {"dated": 0, "undated": 0, "total": 0, "filename": "",
                       "decision_mix_text": "", "earliest": ""}
    scan_report: dict[str, dict] = {}

    def mix_text(items: list[dict]) -> str:
        counts = collections.Counter(clean(r.get("decision")) for r in items)
        return ", ".join(f"{name} {counts[name]}" for name in DECISIONS if counts.get(name))

    def earliest_deadline(items: list[dict]) -> str:
        days = sorted(r["_deadline"] for r in items if r.get("_deadline"))
        return days[0].isoformat() if days else ""

    for code, items in ordered:
        is_unassigned = code == UNASSIGNED
        name = "Unassigned notices (internal)" if is_unassigned else labels[code]
        slug = "unassigned" if is_unassigned else slugify(name)
        if slug in used_slugs:
            used_slugs[slug] += 1
            slug = f"{slug}_{used_slugs[slug]}"
        else:
            used_slugs[slug] = 1

        filename = f"{slug}.html"
        page = build_page(name, items, run_date, feed_date, footnote, boilerplate, twins,
                          closing=INTERNAL_BOX if is_unassigned else ASK_BOX)
        write_text(out_dir / filename, page)

        n_dated = len({r.get("_number") for r in items if r.get("_deadline")})
        n_undated = 0

        if is_unassigned:
            unassigned_info = {"dated": n_dated, "undated": n_undated,
                               "total": n_dated, "filename": filename,
                               "decision_mix_text": mix_text(items),
                               "earliest": earliest_deadline(items)}
            continue

        write_csv(out_dir / f"{slug}.csv", items, twins)
        scan = scan_page(page, name)
        scan["other_distributor_names_found"] = sorted(
            other_name for other_code, other_name in labels.items()
            if other_code != code and re.search(re.escape(other_name), visible_text(page), re.I)
        )
        scan_report[filename] = scan
        pages.append({
            "code": code,
            "display_name": name,
            "filename": filename,
            "csv": f"{slug}.csv",
            "dated": n_dated,
            "undated": n_undated,
            "total": n_dated,
            "csv_rows": len(items),
            "decision_mix": {d: sum(1 for r in items if clean(r.get("decision")) == d)
                             for d in DECISIONS if any(clean(r.get("decision")) == d for r in items)},
            "earliest": earliest_deadline(items),
        })

    # ---- undated: internal only, never on a distributor page
    undated_rows = []
    for row in undated:
        entry = dict(row)
        entry["_deadline"], entry["_days_left"] = None, None
        undated_rows.append(entry)
    undated_info = {"total": 0, "filename": "", "decision_mix_text": ""}
    if undated_rows:
        undated_info = {"total": len(undated_rows), "filename": "undated.html",
                        "decision_mix_text": mix_text(undated_rows)}
        page = build_page("No deadline published (internal)", undated_rows, run_date, feed_date,
                          footnote, boilerplate, {}, closing=UNDATED_BOX,
                          heading="Held back, no deadline")
        write_text(out_dir / "undated.html", page)

    write_text(out_dir / "index.html", build_index(pages, unassigned_info, undated_info, stats,
                                                   run_date, feed_date, feed_path))
    write_text(out_dir / "README_IMPORT.md", build_readme(run_date, feed_path.name))

    launcher = out_dir / "OPEN_RM_DIGEST.cmd"
    with launcher.open("wb") as fh:
        fh.write(LAUNCHER.encode("ascii"))

    # ---- the gate a distributor page must pass
    banned_total = sum(s["gate_hits"] for s in scan_report.values())
    bad_pages = {name: s for name, s in scan_report.items() if s["gate_hits"]}
    # Echoes of another distributor's short display name inside a tender title or a buyer
    # name (e.g. the word "Ireland" in "NORTHERN IRELAND WATER LIMITED"). Reported, not
    # gated: the text is the notice's own wording, not an internal reference.
    name_echoes = {name: s["other_distributor_names_found"] for name, s in scan_report.items()
                   if s["other_distributor_names_found"]}

    report = {
        "run_date": run_date.isoformat(),
        "feed": str(feed_path),
        "feed_generated_at": (payload.get("meta") or {}).get("generated_at"),
        "selection": stats,
        "distributors": pages,
        "unassigned": unassigned_info,
        "undated_internal": undated_info,
        "twins": twins,
        "banned_terms": {
            "gate_definition": "word-boundary, case-insensitive for AIM/PRISM/DLOD/IDS/GPS/BVP/IML/ITUK/IUK/UMI/UTI/campaign; "
                               "literal for .csv/.json/.py; word-boundary for goed/slecht. Scanned over visible page text "
                               "(styles and scripts removed).",
            "pages_scanned": sorted(scan_report),
            "total_gate_hits": banned_total,
            "per_page": scan_report,
        },
        "other_distributor_name_echoes": name_echoes,
        "output_folder": str(out_dir),
    }
    write_text(out_dir / "_run_report.json", json.dumps(report, indent=2, ensure_ascii=False) + "\n")

    # ---- console summary
    print(f"Run date: {run_date.isoformat()}   feed: {feed_path.name}   feed dated: {report['feed_generated_at']}")
    print(f"Rows in feed: {stats['rows_in_feed']} | R&M or pickup/truck: {stats['rm_or_pickup_truck']} | "
          f"actionable decision: {stats['in_scope_and_actionable_decision']} (Ignore: {stats['in_scope_ignored']}) | "
          f"listed (dated): {stats['selected_dated']} rows = {stats['distinct_tenders_listed']} tenders "
          f"({stats['twin_pairs']} twin pairs) | held back, no deadline: {stats['undated_internal_only']}")
    print(f"Dropped, deadline already passed: {stats['dropped_deadline_already_passed']} | "
          f"unreadable deadline: {stats['deadline_unreadable']}")
    print("")
    print(f"{'distributor':<34}{'dated':>6}{'undated':>9}{'total':>7}")
    for entry in pages:
        print(f"{entry['display_name'][:33]:<34}{entry['dated']:>6}{entry['undated']:>9}{entry['total']:>7}")
    print(f"{'UNASSIGNED (internal)':<34}{unassigned_info['dated']:>6}{unassigned_info['undated']:>9}{unassigned_info['total']:>7}")
    print("")
    print(f"Banned-term scan, {len(scan_report)} distributor pages: total hits = {banned_total}")
    for name, scan in sorted(scan_report.items()):
        diag = scan["inside_longer_words_diagnostic"]
        echo = scan["other_distributor_names_found"]
        note = ""
        if diag:
            note += f"  (inside longer words, not a hit: {diag})"
        if echo:
            note += f"  (notice text mentions: {echo})"
        print(f"  {name:<38} gate={scan['gate_hits']}{note}")
    if bad_pages:
        print("  FAIL: " + ", ".join(sorted(bad_pages)))
    print("")
    print(f"Output: {out_dir}")
    return 1 if bad_pages else 0


if __name__ == "__main__":
    raise SystemExit(main())
