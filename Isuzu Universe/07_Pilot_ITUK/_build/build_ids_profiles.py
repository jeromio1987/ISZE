"""Build one Dealer Standards 2026 self-evaluation page per ITUK pilot-side dealer."""
from __future__ import annotations

import hashlib
import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
ISZE = Path(__file__).resolve().parents[3]
PAGES = ROOT / "pages"
BUILD = Path(__file__).resolve().parent

sys.path.insert(0, str(BUILD))
import pilot_dealers as pd_dealers  # noqa: E402

WORKBOOK = ISZE / "01_data" / "08_Distributor" / "IDS_2026" / "ITUK" / "IDS ITUK self evaluations.xlsx"
WORKBOOK_HASH_PREFIX = "6508bc15f1d4afff"
SHEET = "Sales, Parts & Service"
QUESTION_RE = re.compile(r"^[A-E]\.\d+-\d+")
SUBSECTION_RE = re.compile(r"^[A-E]\.\d+$")
TOTAL_QUESTIONS = 219

SECTIONS = {
    "A": "Premises, facility and clothing",
    "B": "Organisation and management",
    "C": "Service",
    "D": "Parts and accessories",
    "E": "Vehicle sales",
}

MEETS = "Meets the standard"
NOT_MEET = "Does not meet"
OWN = "Answered in own words"
NA = "Not applicable"
NONE = "No answer recorded"
CLASSES = [MEETS, NOT_MEET, OWN, NA, NONE]
CLASS_KEY = {
    MEETS: "meets",
    NOT_MEET: "does_not_meet",
    OWN: "own_words",
    NA: "not_applicable",
    NONE: "no_answer",
}
CLASS_CSS = {MEETS: "c-meets", NOT_MEET: "c-not", OWN: "c-own", NA: "c-na", NONE: "c-none"}
CLASS_TIP = {
    MEETS: "The dealer answered yes: the standard is met.",
    NOT_MEET: "The dealer answered no: the standard is not met.",
    OWN: "The dealer wrote something other than yes, no or not applicable. "
         "The words are shown exactly as written in the full questionnaire below.",
    NA: "The dealer marked the question as not applicable to its site.",
    NONE: "The answer cell for this question is empty on the form.",
}


def sha256_full(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def answer_class(value) -> str:
    if value is None:
        return NONE
    s = str(value).strip()
    if s == "":
        return NONE
    up = s.upper()
    if up == "YES":
        return MEETS
    if up == "NO":
        return NOT_MEET
    if up in ("N/A", "NA"):
        return NA
    return OWN


def read_workbook() -> tuple[list[dict], dict[str, int], list[str]]:
    """Return questions, dealer column index by name, and all dealer names on the sheet."""
    wb = openpyxl.load_workbook(WORKBOOK, read_only=True, data_only=True)
    ws = wb[SHEET]
    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    header = next(r for r in rows if r and r[0] is not None and str(r[0]) == "A.1")
    dealer_cols: dict[str, int] = {}
    for j, cell in enumerate(header):
        if j >= 4 and cell not in (None, ""):
            dealer_cols[str(cell)] = j
    all_names = list(dealer_cols)

    questions: list[dict] = []
    sub_code, sub_title = None, None
    for r in rows:
        if not r or r[0] is None:
            continue
        first = str(r[0]).strip()
        if SUBSECTION_RE.match(first):
            sub_code, sub_title = first, str(r[1]).strip() if r[1] is not None else ""
            continue
        if QUESTION_RE.match(first):
            questions.append(
                {
                    "number": first,
                    "section": first[0],
                    "sub_code": sub_code,
                    "sub_title": sub_title,
                    "wording": "" if r[1] is None else str(r[1]),
                    "compliant": "" if len(r) <= 3 or r[3] is None else str(r[3]),
                    "row": r,
                }
            )
    if len(questions) != TOTAL_QUESTIONS:
        raise SystemExit(f"expected {TOTAL_QUESTIONS} question rows, found {len(questions)}")
    return questions, dealer_cols, all_names


def tip(text: str, tip_text: str) -> str:
    return (
        f'<span class="kpi-tip" tabindex="0">{html.escape(text)}'
        f'<span class="tip">{html.escape(tip_text)}</span></span>'
    )


def stacked_bar(counts: dict[str, int], total: int) -> str:
    parts = [
        '<svg class="stack" viewBox="0 0 1000 18" preserveAspectRatio="none" '
        'role="img" aria-hidden="true">'
    ]
    x = 0.0
    for c in CLASSES:
        n = counts[c]
        if not n:
            continue
        w = 1000.0 * n / total
        parts.append(f'<rect class="{CLASS_CSS[c]}" x="{x:.2f}" y="0" width="{w:.2f}" height="18"/>')
        x += w
    parts.append("</svg>")
    return "".join(parts)


def count_line(counts: dict[str, int]) -> str:
    bits = [
        f'<span class="cl"><i class="sw {CLASS_CSS[c]}"></i>{html.escape(c)} {counts[c]}</span>'
        for c in CLASSES
        if counts[c]
    ]
    return " ".join(bits)


def question_label(n: int) -> str:
    return f"{n} question" if n == 1 else f"{n} questions"


def render_page(dealer: dict, answers: list[dict], counts: dict[str, int]) -> str:
    page_name = str(dealer["page_name"])

    subs: dict[str, dict] = {}
    for a in answers:
        key = a["sub_code"]
        if key not in subs:
            subs[key] = {"title": a["sub_title"], "counts": {c: 0 for c in CLASSES}, "total": 0}
        subs[key]["counts"][a["cls"]] += 1
        subs[key]["total"] += 1

    kpis = "".join(
        f'<div class="kpi {CLASS_CSS[c]}-edge"><p class="label">{html.escape(c)}</p>'
        f'<p class="val">{tip(f"{counts[c]} of {TOTAL_QUESTIONS}", CLASS_TIP[c])}</p></div>'
        for c in CLASSES
    )

    legend = " ".join(
        f'<span class="cl"><i class="sw {CLASS_CSS[c]}"></i>{html.escape(c)}</span>' for c in CLASSES
    )
    overview_rows = []
    for code, s in subs.items():
        overview_rows.append(
            '<div class="ov-row">'
            f'<p class="ov-label"><b>{html.escape(code)}</b> {html.escape(s["title"])} '
            f'<span class="muted">{question_label(s["total"])}</span></p>'
            f'{stacked_bar(s["counts"], s["total"])}'
            f'<p class="ov-counts">{count_line(s["counts"])}</p>'
            "</div>"
        )

    meet_items = "".join(
        f'<li><b>{html.escape(code)}</b> {html.escape(s["title"])}: '
        f'{s["counts"][MEETS]} of {s["total"]}</li>'
        for code, s in subs.items()
        if s["counts"][MEETS]
    )
    gap_list = [a for a in answers if a["cls"] in (NOT_MEET, NONE)]
    gap_items = "".join(
        f'<li><span class="badge {CLASS_CSS[a["cls"]]}">{html.escape(a["cls"])}</span> '
        f'<b>{html.escape(a["number"])}</b> {html.escape(a["wording"])}</li>'
        for a in gap_list
    )
    if not gap_items:
        gap_items = '<li class="muted">None. Every question has an answer other than no.</li>'

    section_blocks = []
    for letter, sec_name in SECTIONS.items():
        sec = [a for a in answers if a["section"] == letter]
        if not sec:
            continue
        sec_counts = {c: sum(1 for a in sec if a["cls"] == c) for c in CLASSES}
        rows = []
        last_sub = None
        for a in sec:
            if a["sub_code"] != last_sub:
                rows.append(
                    f'<tr class="sub"><th colspan="5">{html.escape(a["sub_code"])} '
                    f'{html.escape(a["sub_title"])}</th></tr>'
                )
                last_sub = a["sub_code"]
            rows.append(
                '<tr class="q">'
                f'<td class="qn" data-l="No.">{html.escape(a["number"])}</td>'
                f'<td class="verbatim" data-l="Question">{html.escape(a["wording"])}</td>'
                f'<td class="verbatim" data-l="Compliant when">{html.escape(a["compliant"])}</td>'
                f'<td class="verbatim" data-l="Answer">{html.escape(a["answer_raw"])}</td>'
                f'<td data-l="Reading"><span class="badge {CLASS_CSS[a["cls"]]}">{html.escape(a["cls"])}</span></td>'
                "</tr>"
            )
        section_blocks.append(
            '<details class="sec">'
            f'<summary>{letter}. {html.escape(sec_name)} '
            f'<span class="sum">{question_label(len(sec))}: {count_line(sec_counts)}</span></summary>'
            '<div class="table-wrap"><table><thead><tr>'
            "<th>No.</th><th>Question</th><th>Compliant when</th><th>Answer as written</th><th>Reading</th>"
            "</tr></thead><tbody>"
            + "".join(rows)
            + "</tbody></table></div></details>"
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Isuzu Dealer Standards 2026: your self-evaluation — {html.escape(page_name)}</title>
<style>
:root {{
  --navy:#15233c; --paper:#f7f4ee; --ink:#222; --terra:#c0552d; --line:#d5cfc4;
  --own:#b08a2e; --na:#7d8796; --none:#e7e1d6;
}}
* {{ box-sizing:border-box; }}
html,body {{ margin:0; padding:0; background:var(--paper); color:var(--ink);
  font-family: Georgia, "Times New Roman", serif; }}
body {{ padding:24px 20px 64px; max-width:1100px; margin:0 auto; overflow-x:hidden; }}
h1 {{ font-size:1.65rem; color:var(--navy); margin:0 0 4px; line-height:1.25; }}
h2 {{ font-size:1.15rem; color:var(--navy); margin:0 0 12px; }}
.dealer {{ font-size:1.2rem; color:var(--navy); margin:0 0 8px; }}
.source {{ color:#445; font-size:0.95rem; margin:0 0 22px; max-width:820px; }}
.muted {{ color:#556; font-weight:400; }}
.kpis {{ display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:12px; margin:0 0 28px; }}
.kpi {{ background:#fff; border:1px solid var(--line); border-left:4px solid var(--navy);
  padding:14px 14px 12px; min-width:0; }}
.kpi.c-not-edge {{ border-left-color:var(--terra); }}
.kpi.c-own-edge {{ border-left-color:var(--own); }}
.kpi.c-na-edge {{ border-left-color:var(--na); }}
.kpi.c-none-edge {{ border-left-color:#b9b0a1; }}
.kpi .label {{ font-size:0.78rem; text-transform:uppercase; letter-spacing:0.04em; color:#445; margin:0 0 6px; }}
.kpi .val {{ font-size:1.35rem; color:var(--navy); font-weight:700; margin:0; }}
.kpi-tip {{ position:relative; cursor:help; border-bottom:1px dotted var(--terra); }}
.kpi-tip .tip {{
  display:none; position:absolute; left:0; top:calc(100% + 8px); z-index:20;
  width:min(300px, 80vw); background:var(--navy); color:var(--paper);
  padding:10px 12px; font-size:0.82rem; line-height:1.35; border-top:3px solid var(--terra);
  box-shadow:0 8px 18px rgba(21,35,60,0.25); font-weight:400;
}}
.kpi:nth-child(n+4) .tip {{ left:auto; right:0; }}
.kpi-tip:hover .tip, .kpi-tip:focus .tip {{ display:block; }}
.box {{ background:#fff; border:1px solid var(--line); padding:16px 18px; margin:0 0 28px; }}
.legend {{ margin:0 0 14px; font-size:0.88rem; color:#334; }}
.cl {{ display:inline-block; margin:0 14px 4px 0; white-space:nowrap; }}
.sw {{ display:inline-block; width:12px; height:12px; margin-right:6px; vertical-align:-1px; }}
.c-meets {{ background:var(--navy); fill:var(--navy); }}
.c-not {{ background:var(--terra); fill:var(--terra); }}
.c-own {{ background:var(--own); fill:var(--own); }}
.c-na {{ background:var(--na); fill:var(--na); }}
.c-none {{ background:var(--none); fill:var(--none); }}
i.sw.c-none {{ outline:1px solid #a69d8e; }}
.ov-row {{ margin:0 0 14px; }}
.ov-label {{ margin:0 0 4px; color:var(--navy); font-size:0.95rem; }}
.stack {{ display:block; width:100%; height:18px; background:var(--none); outline:1px solid var(--line); }}
.ov-counts {{ margin:4px 0 0; font-size:0.82rem; color:#334; }}
.lists {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; margin:0 0 28px; }}
.lists .box {{ margin:0; }}
.lists ul {{ margin:0; padding-left:1.1rem; }}
.lists li {{ margin:0 0 6px; line-height:1.4; }}
.badge {{ display:inline-block; padding:1px 7px; font-size:0.74rem; border-radius:2px; white-space:nowrap; }}
.badge.c-meets {{ color:var(--paper); }}
.badge.c-not {{ color:#fff; }}
.badge.c-own {{ color:#fff; }}
.badge.c-na {{ color:#fff; }}
.badge.c-none {{ color:var(--ink); outline:1px solid #a69d8e; }}
details.sec {{ border:1px solid var(--line); background:#fff; margin:0 0 8px; }}
summary {{ cursor:pointer; padding:10px 12px; color:var(--navy); font-weight:700; list-style:none; }}
summary::-webkit-details-marker {{ display:none; }}
summary::before {{ content:"+ "; color:var(--terra); }}
details[open] > summary::before {{ content:"− "; }}
.sum {{ display:block; font-weight:400; color:#445; font-size:0.85rem; margin-top:4px; }}
.table-wrap {{ margin:0 10px 12px; border:1px solid var(--line); }}
table {{ border-collapse:collapse; width:100%; font-size:0.84rem; background:#fff; table-layout:fixed; }}
th, td {{ border-bottom:1px solid var(--line); padding:7px 8px; text-align:left; vertical-align:top;
  color:var(--ink); overflow-wrap:anywhere; }}
thead th {{ background:var(--navy); color:var(--paper); }}
thead th:nth-child(1) {{ width:72px; }} thead th:nth-child(2) {{ width:38%; }}
thead th:nth-child(4) {{ width:15%; }} thead th:nth-child(5) {{ width:150px; }}
tr.sub th {{ background:#eef0f4; color:var(--navy); font-weight:700; }}
td.qn {{ font-family: Consolas, "Courier New", monospace; white-space:nowrap; }}
.limits ul {{ margin:8px 0 0; padding-left:1.2rem; }}
.limits li {{ margin:4px 0; }}
@media (max-width:900px) {{
  .kpis {{ grid-template-columns:1fr 1fr; }}
  .kpi:nth-child(n+4) .tip {{ left:0; right:auto; }}
  .kpi:nth-child(even) .tip {{ left:auto; right:0; }}
  .lists {{ grid-template-columns:1fr; }}
}}
@media (max-width:700px) {{
  body {{ padding:16px 12px 48px; }}
  h1 {{ font-size:1.35rem; }}
  table, thead, tbody, tr, td, th {{ display:block; width:auto !important; }}
  thead {{ display:none; }}
  tr.q {{ border-bottom:2px solid var(--line); padding:6px 0; }}
  tr.q td {{ border:0; padding:3px 8px; }}
  tr.q td::before {{ content:attr(data-l); display:block; font-size:0.72rem; text-transform:uppercase;
    letter-spacing:0.04em; color:#556; }}
}}
@media (max-width:420px) {{
  .kpis {{ grid-template-columns:1fr; }}
  .kpi .tip, .kpi:nth-child(even) .tip {{ left:0; right:auto; }}
}}
</style>
</head>
<body>
<header>
  <h1>Isuzu Dealer Standards 2026: your self-evaluation</h1>
  <p class="dealer">{html.escape(page_name)}</p>
  <p class="source">As recorded by Isuzu Truck UK on the 2026 self-evaluation form for sales, parts and service dealers. The date of the evaluation is not recorded in the source.</p>
</header>

<section class="kpis" aria-label="Answers by type">
{kpis}
</section>

<section class="box" aria-label="Overview by subsection">
  <h2>Your answers by subsection</h2>
  <p class="legend">{legend}</p>
  {''.join(overview_rows)}
</section>

<section class="lists">
  <div class="box">
    <h2>Where you meet the standard</h2>
    <ul>{meet_items}</ul>
  </div>
  <div class="box">
    <h2>Where you do not, or no answer is recorded</h2>
    <ul>{gap_items}</ul>
  </div>
</section>

<section aria-label="Full questionnaire">
  <h2>The full questionnaire</h2>
  {''.join(section_blocks)}
</section>

<section class="box limits">
  <h2>What this page does not show</h2>
  <ul>
    <li>No score or ranking. The page counts your answers; it does not grade them.</li>
    <li>No other dealer's answers.</li>
    <li>No assessment date. The form does not record one.</li>
    <li>Nothing about parts sales.</li>
  </ul>
</section>
</body>
</html>
"""


def main() -> int:
    full_hash = sha256_full(WORKBOOK)
    if not full_hash.startswith(WORKBOOK_HASH_PREFIX):
        raise SystemExit(f"workbook hash {full_hash[:16]} != {WORKBOOK_HASH_PREFIX}")

    questions, dealer_cols, _ = read_workbook()
    for dealer in pd_dealers.DEALERS:
        if str(dealer["ids_name"]) not in dealer_cols:
            raise SystemExit(f"pilot name missing from sheet: {dealer['ids_name']!r}")

    PAGES.mkdir(parents=True, exist_ok=True)
    manifest = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "input_hash": {WORKBOOK.name: full_hash},
        "sheet": SHEET,
        "dealers": [],
    }

    for dealer in pd_dealers.DEALERS:
        col = dealer_cols[str(dealer["ids_name"])]
        answers = []
        for q in questions:
            raw = q["row"][col] if col < len(q["row"]) else None
            answers.append({**q, "answer_raw": "" if raw is None else str(raw), "cls": answer_class(raw)})
        counts = {c: sum(1 for a in answers if a["cls"] == c) for c in CLASSES}

        out_dir = pd_dealers.pages_dir_for(dealer, PAGES)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "Dealer_Standards_2026.html").write_text(
            render_page(dealer, answers, counts), encoding="utf-8"
        )
        (out_dir / "OPEN_Dealer_Standards_2026.cmd").write_bytes(
            b'@echo off\r\nstart "" "%~dp0Dealer_Standards_2026.html"\r\n'
        )
        entry = {"code": dealer["code"], "page_name": dealer["page_name"], "folder": out_dir.name}
        entry.update({CLASS_KEY[c]: counts[c] for c in CLASSES})
        entry["total"] = sum(counts.values())
        manifest["dealers"].append(entry)
        print(
            f"{dealer['code']}: " + " ".join(f"{CLASS_KEY[c]}={counts[c]}" for c in CLASSES)
            + f" total={entry['total']}"
        )

    man_path = PAGES / "ids_manifest.json"
    man_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"wrote {man_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
