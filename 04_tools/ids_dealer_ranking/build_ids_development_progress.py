#!/usr/bin/env python3
"""Build the IDS 2026 dealer development progress page (priority + milestones).

Writes 02_dashboards/ids/IDS_2026_Development_Progress.html plus a CRLF
OPEN_IDS_2026_Development_Progress.cmd.

The page carries the assessment half (sections A-E per dealer against the market
average) and the development half that did not exist: one chosen priority and a
milestone record the user fills in. Nothing is saved to a server; the page
downloads a small text file and loads it back through a file picker.

Reads only:
  02_dashboards/ids/IDS_2026_dealer_compare.html — the embedded assessment
  payload of the shipped dealer comparison page. (The same payload exists as
  01_data/91_build/_ids_e/fileA_data.json when a build has staged it there; that
  scratch file is not stable, so the shipped page is the source of record. The
  two were verified byte-equal when this page was first built.)

No CDN, no fetch. English only. UTF-8 without BOM.
"""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import date
from html import escape
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SOURCE_HTML = REPO / "02_dashboards" / "ids" / "IDS_2026_dealer_compare.html"
OUT_HTML = REPO / "02_dashboards" / "ids" / "IDS_2026_Development_Progress.html"
OUT_CMD = REPO / "02_dashboards" / "ids" / "OPEN_IDS_2026_Development_Progress.cmd"

# Durable on-disk milestone store (companion: append_ids_milestone.py in this
# same folder). Read-only here -- this build never writes to it. Starts empty;
# see 00_docs/IDS_MILESTONE_STORE.md for the format and the write-back workflow.
MILESTONE_STORE = REPO / "01_data" / "00_derived" / "ids_milestones" / "ids_milestones_store.json"

# Internal terms that must not appear on anything a distributor could see.
# Whole-word terms first, then literal tokens that are not words.
# A hit is dropped or renamed, never printed; the build fails if one survives.
BANNED_WORDS = [
    "AIM", "PRISM", "DLOD", "IDS", "GPS", "BVP", "IML", "ITUK", "IUK",
    "UMI", "UTI", "campaign", "goed", "slecht",
]
BANNED_LITERALS = [".csv", ".json", ".py"]
_BANNED_RE = re.compile(
    r"(?:\b(?:" + "|".join(re.escape(t) for t in BANNED_WORDS) + r")\b)"
    r"|(?:" + "|".join(re.escape(t) for t in BANNED_LITERALS) + r")",
    re.I,
)

SECTION_LABELS = {
    "A": "Premises, facility and clothing",
    "B": "Organisation and management",
    "C": "Service",
    "D": "Parts and accessories",
    "E": "Vehicle sales",
}

# Market labels in plain English. The two United Kingdom entries keep their real
# split (pickups / light commercial vehicles against trucks) — the label map in
# ids_paths.py is correct and is not flipped here.
MARKET_LABELS = {
    "UK LCV": "United Kingdom, pickups and light commercial vehicles",
    "UK CV": "United Kingdom, trucks",
    "Israel LCV": "Israel",
    "Benelux": "Benelux",
}

NOT_SCORED_TEXT = {
    "totals_only": "Not scored — this market supplied totals only, with no section detail.",
    "not_scored": "Not scored in this assessment.",
    "blank": "Not scored — left blank in this assessment.",
    "none": "Not scored in this assessment.",
}


def market_label(name: str) -> str:
    return MARKET_LABELS.get(name, name)


def clean(text: str) -> bool:
    """True when the string carries no internal term."""
    return not _BANNED_RE.search(text or "")


def strip_network_prefix(name: str) -> str:
    """Drop a leading network code from a dealer name (display only)."""
    parts = name.split(" ", 1)
    if len(parts) == 2 and parts[0].upper() in {"UMI", "UTI"}:
        return parts[1].strip()
    return name


def load_payload() -> dict:
    text = SOURCE_HTML.read_text(encoding="utf-8")
    marker = "const DATA = "
    idx = text.index(marker) + len(marker)
    payload, _ = json.JSONDecoder().raw_decode(text, idx)
    return payload


def assessment_date_text(raw: str) -> tuple[str, bool]:
    """Return (text, supplied). An obvious placeholder is reported as missing."""
    value = (raw or "").strip()
    if not value or value.startswith("1900"):
        return "", False
    return value[:10], True


def build_questions(payload: dict) -> tuple[dict[str, dict], set[str]]:
    """Question catalogue with internal-term wordings left out."""
    kept: dict[str, dict] = {}
    dropped: set[str] = set()
    for q in payload["questions"]:
        qid = q["id"]
        text = (q.get("text") or "").replace("\n", " ").strip()
        text = re.sub(r"\s+", " ", text)
        if not clean(text):
            dropped.add(qid)
            continue
        kept[qid] = {"sec": q.get("section"), "t": text, "m": q.get("max")}
    return kept, dropped


def top_gaps(payload: dict, dealer: dict, questions: dict[str, dict], market: str) -> list[dict]:
    """Up to three checklist items where most points were left on the table."""
    values = dealer.get("q")
    if not values:
        return []
    country_q = (payload["country_profiles"].get(market) or {}).get("q_pct") or []
    order = [q["id"] for q in payload["questions"]]
    gaps: list[dict] = []
    for idx, qid in enumerate(order):
        if idx >= len(values):
            break
        value = values[idx]
        meta = questions.get(qid)
        if meta is None or value is None:
            continue
        if value >= 0.999:
            continue
        mx = meta.get("m") or 0
        weight = (1.0 - value) * mx
        if weight <= 0:
            continue
        country_pct = country_q[idx] if idx < len(country_q) else None
        gaps.append(
            {
                "q": qid,
                "t": meta["t"],
                "s": round(value * mx, 2),
                "m": mx,
                "p": round(value, 4),
                "ca": round(country_pct, 4) if country_pct is not None else None,
                "w": weight,
            }
        )
    gaps.sort(key=lambda g: -g["w"])
    return gaps[:3]


def build_dealers(payload: dict, questions: dict[str, dict]) -> list[dict]:
    out: list[dict] = []
    for dealer in payload["dealers"]:
        market = dealer["country"]
        sections: dict[str, dict] = {}
        totals_only = bool(dealer.get("totals_only"))
        for sid, sec in (dealer.get("sections") or {}).items():
            pct = sec.get("pct")
            fill = sec.get("fill")
            sections[sid] = {
                "s": sec.get("score"),
                "m": sec.get("max"),
                "p": round(pct, 4) if pct is not None else None,
                "ca": round(sec["country_avg_pct"], 4) if sec.get("country_avg_pct") is not None else None,
                "na": None if pct is not None else NOT_SCORED_TEXT.get(fill or ("totals_only" if totals_only else "none"), NOT_SCORED_TEXT["none"]),
            }
        adate, supplied = assessment_date_text(dealer.get("assessment_date") or "")
        out.append(
            {
                "c": market,
                "n": strip_network_prefix(dealer["name"]),
                "a": (dealer.get("address") or "").replace("\n", " ").strip(),
                "ad": adate,
                "ads": supplied,
                "tot": round(dealer["total_pct"], 4) if dealer.get("total_pct") is not None else None,
                "pts": dealer.get("total"),
                "max": dealer.get("total_max"),
                "ex": bool(dealer.get("excluded_from_average")),
                "to": totals_only,
                "sec": sections,
                "gaps": top_gaps(payload, dealer, questions, market),
            }
        )
    return out


def build_countries(payload: dict) -> dict:
    out: dict[str, dict] = {}
    for name, prof in payload["country_profiles"].items():
        secs = {}
        for sid, pct in (prof.get("sections_pct") or {}).items():
            secs[sid] = round(pct, 4) if pct is not None else None
        out[name] = {
            "n": prof.get("dealer_count"),
            "inavg": prof.get("avg_basis_count"),
            "excl": prof.get("excluded_from_average_count"),
            "tot": round(prof["total_pct"], 4) if prof.get("total_pct") is not None else None,
            "sec": secs,
        }
    return out


def build_network(payload: dict) -> dict:
    net = payload.get("network") or {}
    return {
        "n": net.get("dealer_count"),
        "inavg": net.get("avg_basis_count"),
        "tot": round(net["total_pct"], 4) if net.get("total_pct") is not None else None,
        "sec": {k: (round(v, 4) if v is not None else None) for k, v in (net.get("sections_pct") or {}).items()},
    }


def load_milestones() -> dict:
    """Dealer-keyed milestone rows from the durable store, or {} if absent/unreadable.

    Never fails the build: a missing or malformed store degrades to "no
    milestones on file" rather than blocking the page. Keys are
    "<market>::<dealer display name>", matching how the page itself identifies
    the selected dealer (see current() in the page script below).
    """
    if not MILESTONE_STORE.is_file():
        return {}
    try:
        raw = json.loads(MILESTONE_STORE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    out: dict[str, dict] = {}
    for key, rec in (raw.get("dealers") or {}).items():
        if not isinstance(rec, dict):
            continue
        rows = [
            {
                "d": str(m.get("date") or ""),
                "note": str(m.get("note") or ""),
                "ev": str(m.get("evidence") or ""),
                "done": bool(m.get("done")),
            }
            for m in (rec.get("milestones") or [])
            if isinstance(m, dict)
        ]
        out[str(key)] = {"priority": rec.get("priority"), "rows": rows}
    return out


def build_payload() -> dict:
    payload = load_payload()
    questions, dropped = build_questions(payload)
    dealers = build_dealers(payload, questions)
    countries = build_countries(payload)
    network = build_network(payload)
    milestones = load_milestones()
    return {
        "built": date.today().isoformat(),
        "extract": {
            "version": payload.get("version") or "v1.4",
            "dealers": payload.get("dealer_count"),
            "markets": payload.get("country_count"),
            "held_on": date.today().isoformat(),
            "questions_shown": len(questions),
            "questions_withheld": len(dropped),
        },
        "sections": [{"id": s["id"], "label": SECTION_LABELS.get(s["id"], s["label"])} for s in payload["sections"]],
        "markets": {k: market_label(k) for k in sorted(countries)},
        "countries": countries,
        "network": network,
        "dealers": dealers,
        "milestones": milestones,
    }


def main() -> None:
    data = build_payload()

    html = TEMPLATE.replace("/*__DATA__*/", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    html = html.replace("__BUILT__", date.today().isoformat())

    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(html, encoding="utf-8", newline="\n")
    OUT_CMD.write_bytes(
        f'@echo off\r\nstart "" "%~dp0{OUT_HTML.name}"\r\n'.encode("utf-8")
    )

    # The page itself must be free of internal terms.
    body = OUT_HTML.read_text(encoding="utf-8")
    hits = _BANNED_RE.findall(body)
    print(f"wrote {OUT_HTML} ({OUT_HTML.stat().st_size} bytes)")
    print(f"dealers {len(data['dealers'])} markets {len(data['countries'])} "
          f"questions shown {data['extract']['questions_shown']} withheld {data['extract']['questions_withheld']}")
    print(f"milestone store: {len(data.get('milestones') or {})} dealer(s) with saved milestones "
          f"({MILESTONE_STORE if MILESTONE_STORE.is_file() else 'not found -- treated as empty'})")
    print(f"internal-term hits in page: {len(hits)} {' '.join(sorted(set(hits)))}")
    if hits:
        raise SystemExit("internal terms present in the built page")


def main_probe() -> None:
    """Print the payload summary without writing (used by the QA script)."""
    data = build_payload()
    print(json.dumps({k: v for k, v in data.items() if k != "dealers"}, ensure_ascii=False, indent=1)[:4000])
    print("dealers", len(data["dealers"]))
    for d in data["dealers"][:3]:
        print(json.dumps(d, ensure_ascii=False)[:600])


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dealer development progress</title>
<style>
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:#e8e4dc;color:#222;font-family:"Segoe UI",Helvetica,Arial,sans-serif;font-size:15px;line-height:1.5}
h1,h2,h3{font-family:Georgia,"Times New Roman",serif;font-weight:400;color:#15233c;margin:0}
.banner{background:#15233c;color:#f7f4ee;padding:28px 32px 30px}
.banner .k{font-size:11px;letter-spacing:.08em;text-transform:uppercase;opacity:.8}
.banner h1{color:#f7f4ee;font-size:29px;margin:8px 0 10px;max-width:30ch}
.banner .rule{width:56px;height:3px;background:#c0552d;margin:0 0 12px}
.banner p{margin:0;max-width:88ch;color:#f7f4ee}
.wrap{max-width:1120px;margin:0 auto;padding:18px 20px 56px}
.page{background:#fff;padding:24px 26px 28px;margin:0 0 16px;box-shadow:0 1px 6px rgba(0,0,0,.08)}
h2.sec{font-size:20px;margin:0 0 10px;padding-bottom:8px;border-bottom:2px solid #15233c}
h2.sec .no{color:#c0552d}
.lead{color:#6b6256;font-size:13.5px;margin:0 0 14px;max-width:98ch}
label.f{display:block;font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:#6b6256;margin:0 0 5px}
select,input[type=text],input[type=date],textarea{font:inherit;font-size:14px;padding:7px 9px;border:1px solid #c9c2b6;background:#fff;color:#222;border-radius:2px}
select{min-width:290px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:12px 0 6px}
.kpi{background:#f7f4ee;border-top:3px solid #15233c;padding:11px 13px;position:relative;cursor:help}
.kpi .l{font-size:10px;text-transform:uppercase;letter-spacing:.04em;color:#6b6256}
.kpi .v{font-family:Georgia,serif;font-size:23px;color:#15233c;margin-top:3px}
.kpi.gap .v{color:#c0552d}
.kpi.ok{border-top-color:#1d9e75}
.kpi.amber{border-top-color:#eda100}
.kpi .s{font-size:11.5px;color:#6b6256;margin-top:3px}
.tip{display:none;position:absolute;left:10px;right:10px;top:100%;z-index:40;margin-top:8px;background:#15233c;color:#f7f4ee;padding:10px 12px;font-size:12px;line-height:1.45;border-top:3px solid #c0552d}
.kpi:hover .tip,.kpi:focus .tip{display:block}
table{width:100%;border-collapse:collapse;margin:8px 0 4px;font-size:13px}
th{background:#15233c;color:#f7f4ee;text-align:left;padding:7px 9px;font-size:11px;text-transform:uppercase;letter-spacing:.03em}
td{padding:6px 9px;border-bottom:1px solid #d9d3c8;color:#222;vertical-align:top}
tbody tr:nth-child(even){background:#f7f4ee}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
.barrow{display:flex;align-items:center;gap:10px;margin:7px 0}
.barrow .n{width:190px;font-size:12.5px;color:#15233c}
.barrow .track{flex:1;height:20px;background:#eeeae3;position:relative}
.barrow .fill{height:20px;position:relative;z-index:1}
.barrow .fill.avg{background:#15233c;opacity:.32;position:absolute;top:0;z-index:0}
.barrow .fill.above{background:#1d9e75}
.barrow .fill.below{background:#c0552d}
.barrow .na{height:20px;border:1px dashed #b9b1a4;display:flex;align-items:center;justify-content:center;font-size:11px;color:#6b6256;flex:1}
.barrow .v{width:120px;text-align:right;font-variant-numeric:tabular-nums;font-size:12px}
.pill{display:inline-block;font-size:10px;font-weight:700;letter-spacing:.03em;text-transform:uppercase;padding:2px 7px}
.pill.good{background:#d7efe4;color:#1d6b4a}
.pill.medium{background:#f8e6c0;color:#8a5a00}
.pill.weak{background:#f3d4d0;color:#8a2a22}
.pill.ns{background:#e8ecf2;color:#15233c}
.pill.sugg{background:#f7e2d8;color:#8a3a1c}
.callout{border-left:3px solid #c0552d;background:#f7f4ee;padding:12px 14px;margin:0 0 14px}
.callout.navy{border-left-color:#15233c;background:#f3f5f8}
.callout.ok{border-left-color:#1d9e75;background:#eef7f3}
.callout b{color:#15233c}
.callout p{margin:6px 0 0}
ul.tight{margin:6px 0 0;padding-left:18px}
ul.tight li{margin:5px 0}
.prio{display:block;border:1px solid #d9d3c8;background:#fff;padding:10px 12px;margin:0 0 8px;cursor:pointer}
.prio:hover{background:#f7f4ee}
.prio.sel{border-color:#15233c;border-left:4px solid #c0552d;background:#f7f4ee}
.prio.off{opacity:.62;cursor:not-allowed;background:#f2f0ec}
.prio .t{font-size:14px;color:#15233c;font-weight:600}
.prio .d{font-size:12px;color:#6b6256;margin-top:2px}
.mile-actions{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0 4px}
button{font:inherit;font-size:13px;padding:7px 12px;border:1px solid #15233c;background:#fff;color:#15233c;cursor:pointer;border-radius:2px}
button:hover{background:#15233c;color:#f7f4ee}
button.primary{background:#15233c;color:#f7f4ee}
button.primary:hover{background:#c0552d;border-color:#c0552d}
button:disabled{opacity:.45;cursor:not-allowed}
.mil td{padding:4px 6px}
.mil input[type=text],.mil input[type=date]{width:100%;font-size:13px;padding:5px 6px}
.mil input[type=checkbox]{width:17px;height:17px}
.prog{background:#f7f4ee;padding:12px 14px;margin:10px 0 0}
.prog .track{height:16px;background:#e2ddd3;margin:8px 0 6px}
.prog .fill{height:16px;background:#1d9e75}
.prog .stat{font-size:12.5px;color:#6b6256}
.empty{border:1px dashed #b9b1a4;background:#faf8f4;padding:14px 16px;color:#3f3a33}
.empty b{color:#15233c}
.muted{color:#6b6256;font-size:12px}
.foot{margin-top:18px;padding-top:10px;border-top:1px solid #d9d3c8;font-size:11.5px;color:#6b6256}
.sum{border:2px solid #15233c;padding:18px 20px;background:#fff}
.sum h3{font-size:19px;margin:0 0 2px}
.sum .sub{font-size:12px;color:#6b6256;margin:0 0 12px}
.sum table{font-size:12px}
.sum th{padding:5px 8px;font-size:10.5px}
.sum td{padding:5px 8px}
.sig{display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-top:18px;font-size:12px;color:#6b6256}
.sig div{border-top:1px solid #222;padding-top:5px}
.tl{width:100%;height:66px;display:block}
@media(max-width:900px){.kpis,.grid2,.grid3{grid-template-columns:1fr}.barrow .n{width:130px}}
@media print{
  html,body{background:#fff}
  body{font-size:10px;line-height:1.35}
  .banner,.noprint{display:none !important}
  .wrap{max-width:none;padding:0}
  .page{box-shadow:none;margin:0;padding:0}
  h2.sec{font-size:14px;margin:0 0 6px;padding-bottom:4px;border-bottom:1px solid #15233c}
  .sum{border:1px solid #15233c;page-break-inside:avoid;padding:12px 14px}
  .sum h3{font-size:15px}
  .sum .sub{font-size:9.5px;margin:0 0 8px}
  .sum table{font-size:9.5px;margin:4px 0 2px}
  .sum th{padding:3px 6px;font-size:9px}
  .sum td{padding:3px 6px}
  .sum .sig{margin-top:12px;font-size:9.5px}
  .foot{font-size:9px;margin-top:8px;padding-top:6px}
}
</style>
</head>
<body>
<div class="banner">
  <div class="k">Isuzu Dealer Standards 2026 · development progress · built __BUILT__</div>
  <h1>What the dealer will do next, and whether it moved</h1>
  <div class="rule"></div>
  <p>The assessment says where a dealer stands today. This page holds the other half: one development priority the dealer chooses with its distributor, the milestones agreed for it, the evidence that they happened, and a printable summary for the meeting. Progress here is separate from the assessment score and never changes it.</p>
</div>
<div class="wrap">

<div class="page noprint">
  <h2 class="sec"><span class="no">1.</span> Pick the dealer</h2>
  <p class="lead">Every dealer that sits in the assessment we hold is reachable. The starting point comes straight from that assessment — nothing on this page re-scores anybody.</p>
  <div class="grid2">
    <div><label class="f" for="f-market">Market</label><select id="f-market"></select></div>
    <div><label class="f" for="f-dealer">Dealer</label><select id="f-dealer"></select></div>
  </div>
  <p class="muted" id="pick-note"></p>
</div>

<div class="page noprint">
  <h2 class="sec"><span class="no">2.</span> Where the dealer stands</h2>
  <p class="lead" id="where-lead"></p>
  <div class="kpis" id="where-kpis"></div>
  <div id="where-bars"></div>
  <p class="muted" id="where-note"></p>
  <div id="where-empty"></div>
  <div id="where-gaps"></div>
</div>

<div class="page noprint">
  <h2 class="sec"><span class="no">3.</span> One development priority</h2>
  <div class="callout navy">
    <b>One priority, agreed with the distributor</b>
    <p>Choose a single area to work on. The list is the five assessed areas, ordered so this dealer's weakest scored area comes first. Two are marked suggested. An area that was not scored in this assessment is not offered as a priority, because nothing was measured there.</p>
  </div>
  <div id="prio-list"></div>
  <div id="prio-empty"></div>
</div>

<div class="page noprint">
  <h2 class="sec"><span class="no">4.</span> Milestones, evidence, progress</h2>
  <div class="callout">
    <b>A finished milestone is not a higher score</b>
    <p>The assessment score moves only when a later assessment is recorded and scored. Completing the work agreed here does not raise it, and this page never adds one to the other. What you see below is progress on the agreed work: how many milestones were done, and when.</p>
  </div>
  <p class="lead">Type the milestones the dealer and its distributor agree. A date, a line on what will be done, and the evidence slot for what was actually sent or seen. Leave a row blank rather than filling it with a guess. If this dealer already has milestones on file from an earlier session, they are loaded below automatically — nothing here is invented.</p>
  <div class="mile-actions noprint">
    <button type="button" class="primary" id="btn-add">Add milestone</button>
    <button type="button" id="btn-save">Save my plan to a file</button>
    <button type="button" id="btn-load">Load a saved plan</button>
    <button type="button" id="btn-print">Print the one-page summary</button>
    <input type="file" id="file-load" accept="text/plain,text/csv" style="display:none">
  </div>
  <p class="muted" id="save-note"></p>
  <table class="mil">
    <thead>
      <tr>
        <th style="width:34px">#</th>
        <th style="width:150px">Date</th>
        <th>Milestone — what will be done</th>
        <th>Evidence — what was sent, what happened</th>
        <th style="width:74px">Done</th>
        <th style="width:60px" class="noprint"></th>
      </tr>
    </thead>
    <tbody id="mil-body"></tbody>
  </table>
  <div class="prog">
    <div class="stat"><b>Development progress</b> — milestones completed on the chosen priority. This is not the assessment score and does not change it.</div>
    <div class="track"><div class="fill" id="prog-fill" style="width:0%"></div></div>
    <div class="stat" id="prog-text"></div>
  </div>
  <h3 style="margin:18px 0 6px;font-size:15px">Progress over time</h3>
  <div id="tl-wrap"></div>
</div>

<div class="page">
  <h2 class="sec noprint"><span class="no">5.</span> One-page summary for the meeting</h2>
  <p class="lead noprint">This is what prints — one page the distributor can take into the dealer meeting. Use the print button above; what you see here is what comes out.</p>
  <div class="sum" id="sum"></div>
  <p class="foot" id="sum-foot"></p>
</div>

<div class="page noprint">
  <h2 class="sec"><span class="no">6.</span> What this page knows and does not know</h2>
  <div class="grid2">
    <div class="callout ok">
      <b>What it holds</b>
      <ul class="tight" id="knows"></ul>
    </div>
    <div class="callout">
      <b>What it does not hold</b>
      <ul class="tight">
        <li>No invented milestone history. Where nothing was ever saved for a dealer, its table starts empty; nothing is guessed or backfilled to fill it.</li>
        <li>No actions, owners or dates. Where the workspace holds no minutes, the row stays blank.</li>
        <li>No second assessment round. Section scores shown are the ones on file; a change in recorded answers appears only when a new assessment exists.</li>
        <li>No live saving from this page. It cannot write to a server or a shared drive by itself while it is open.</li>
      </ul>
    </div>
  </div>
  <div class="callout navy">
    <b>How your entries survive</b>
    <p>While you work, entries live in this open browser tab. Press <b>Save my plan to a file</b> to download them as a small text file — keep it, or pass it back to whoever maintains this page's shared record, so it can be folded in. Once that happens, this dealer's milestones will already be loaded the next time this page is prepared, without anyone retyping them. Until then, <b>Load a saved plan</b> brings a file back into this tab yourself. Printing works whether or not you save.</p>
  </div>
  <p class="foot" id="data-notes"></p>
</div>

</div>
<script type="application/json" id="devdata">/*__DATA__*/</script>
<script>
(function () {
  "use strict";
  var DATA = JSON.parse(document.getElementById("devdata").textContent);

  var state = { market: null, dealer: null, priority: null, miles: [] };

  var BANDS = { good: 0.80, medium: 0.60 };
  var SECTION_IDS = ["A", "B", "C", "D", "E"];

  function $(id) { return document.getElementById(id); }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function pct(v) { return v == null ? "—" : (v * 100).toFixed(1) + "%"; }
  function pp(v) { return v == null ? "—" : (v >= 0 ? "+" : "") + (v * 100).toFixed(1) + " pp"; }
  function sectLabel(id) { return SECTION_LABELS[id] || id; }
  function band(p) {
    if (p == null) return ["Not scored", "ns"];
    if (p >= BANDS.good) return ["Good", "good"];
    if (p >= BANDS.medium) return ["Medium", "medium"];
    return ["Needs improvement", "weak"];
  }

  var SECTION_LABELS = {};
  DATA.sections.forEach(function (s) { SECTION_LABELS[s.id] = s.label; });

  function marketName(key) { return DATA.markets[key] || key; }

  function dealersFor(market) {
    return DATA.dealers.filter(function (d) { return d.c === market; })
      .sort(function (a, b) { return a.n.toLowerCase() < b.n.toLowerCase() ? -1 : 1; });
  }

  function current() {
    if (!state.market || !state.dealer) return null;
    return DATA.dealers.filter(function (d) {
      return d.c === state.market && d.n === state.dealer;
    })[0] || null;
  }

  function prioCandidates(dealer) {
    var scored = SECTION_IDS.filter(function (id) {
      return dealer.sec[id] && dealer.sec[id].p != null;
    }).sort(function (a, b) { return dealer.sec[a].p - dealer.sec[b].p; });
    return scored;
  }

  /* ---------- milestones already on file for this dealer ---------- */
  function storedMilestones(market, dealer) {
    if (!market || !dealer || !DATA.milestones) { return null; }
    return DATA.milestones[market + "::" + dealer] || null;
  }

  function applyStoredMilestones(resetPriorityWhenNone) {
    var rec = storedMilestones(state.market, state.dealer);
    if (rec && rec.rows && rec.rows.length) {
      state.miles = rec.rows.map(function (r) {
        return { d: r.d || "", note: r.note || "", ev: r.ev || "", done: !!r.done };
      });
      if (rec.priority) { state.priority = rec.priority; }
      else if (resetPriorityWhenNone) { state.priority = null; }
    } else {
      state.miles = [];
      if (resetPriorityWhenNone) { state.priority = null; }
    }
  }

  /* ---------- 1. pickers ---------- */
  function initPickers() {
    var mk = $("f-market");
    Object.keys(DATA.markets).sort(function (a, b) {
      return marketName(a).localeCompare(marketName(b));
    }).forEach(function (key) {
      var o = document.createElement("option");
      o.value = key; o.textContent = marketName(key) + " (" + DATA.countries[key].n + " dealers)";
      mk.appendChild(o);
    });
    var withData = Object.keys(DATA.countries).sort(function (a, b) {
      var x = DATA.countries[a].sec, y = DATA.countries[b].sec;
      var nx = SECTION_IDS.filter(function (s) { return x[s] != null; }).length;
      var ny = SECTION_IDS.filter(function (s) { return y[s] != null; }).length;
      return ny - nx;
    })[0];
    state.market = withData;
    mk.value = withData;
    fillDealers();

    mk.addEventListener("change", function () {
      state.market = mk.value;
      fillDealers();
      applyStoredMilestones(false);
      renderAll();
    });
    $("f-dealer").addEventListener("change", function () {
      state.dealer = $("f-dealer").value;
      applyStoredMilestones(true);
      renderAll();
    });
  }

  function fillDealers() {
    var ds = dealersFor(state.market);
    var sel = $("f-dealer");
    sel.innerHTML = "";
    ds.forEach(function (d) {
      var o = document.createElement("option");
      o.value = d.n;
      o.textContent = d.n + (d.to ? "  (totals only)" : "");
      sel.appendChild(o);
    });
    state.dealer = ds.length ? ds[0].n : null;
    sel.value = state.dealer;
    $("pick-note").textContent = ds.length
      ? ds.length + " dealers in this market on the assessment extract. Market average " + pct(DATA.countries[state.market].tot) + "."
      : "No dealer shown for this market.";
  }

  /* ---------- 2. where the dealer stands ---------- */
  function renderWhere() {
    var d = current();
    if (!d) { return; }
    var country = DATA.countries[d.c];
    var diff = (d.tot != null && country.tot != null) ? d.tot - country.tot : null;
    var b = band(d.tot);

    $("where-lead").innerHTML =
      "<b>" + esc(d.n) + "</b> · " + esc(marketName(d.c)) +
      (d.ad ? " · assessment " + esc(d.ad) : " · assessment date not supplied") +
      (d.ex ? " · this dealer sits outside the market average on the extract" : "") + ".";

    var kpis = [];
    kpis.push(kpi("Total on file", pct(d.tot), d.pts != null ? (Math.round(d.pts * 10) / 10) + " of " + (d.max || 280) + " points" : "", "The dealer's own recorded total on the assessment extract. Not re-scored here."));
    kpis.push(kpi("Market average", pct(country.tot), country.inavg + " dealers in the average", "Average of the " + country.inavg + " dealers counted in this market's average on the same extract." + (country.excl ? " " + country.excl + " dealer(s) in this market sit outside it, marked by the market's own review." : " No dealer is excluded from this market's average."), "ok"));
    kpis.push(kpi("Difference", pp(diff), "against the market average", "Dealer total minus market average, in percentage points. A negative number is behind the market average, not a failure.", diff != null && diff < 0 ? "gap" : "ok"));
    kpis.push(kpi("Band", b[0], "Good 80% · Medium 60%", "Bands come from the assessment extract: Good from 80%, Medium from 60%, below that Needs improvement. Section scores move close together across the network, so a band is a reading aid, not a judgement of commercial performance."));
    $("where-kpis").innerHTML = kpis.join("");

    var rows = "";
    SECTION_IDS.forEach(function (id) {
      var s = d.sec[id];
      if (!s) { return; }
      if (s.p == null) {
        rows += '<div class="barrow"><div class="n">' + esc(id + ". " + sectLabel(id)) + '</div>' +
          '<div class="na">Not scored</div><div class="v">Not scored</div></div>';
        return;
      }
      var cls = (s.ca != null && s.p >= s.ca) ? "above" : "below";
      var avgBar = s.ca != null ? '<div class="fill avg" style="width:' + (s.ca * 100).toFixed(1) + '%"></div>' : "";
      rows += '<div class="barrow"><div class="n">' + esc(id + ". " + sectLabel(id)) + '</div>' +
        '<div class="track">' + avgBar + '<div class="fill ' + cls + '" style="width:' + (s.p * 100).toFixed(1) + '%"></div></div>' +
        '<div class="v">' + pct(s.p) + " · " + pp(s.p - (s.ca == null ? s.p : s.ca)) + "</div></div>";
    });
    $("where-bars").innerHTML = rows;

    var missing = SECTION_IDS.filter(function (id) {
      return d.sec[id] && d.sec[id].p == null;
    });
    $("where-note").textContent =
      "Solid bar = this dealer. Pale bar = the market average on that same area. " +
      (missing.length
        ? "Areas not assessed are labelled Not scored and are never drawn as zero: " +
          missing.map(function (id) { return id + " (" + d.sec[id].na + ")"; }).join(" ")
        : "All five areas were scored for this dealer on the extract.");

    $("where-empty").innerHTML = d.to
      ? '<div class="empty"><b>This market supplied totals only.</b> The assessment for ' + esc(marketName(d.c)) +
        " carries a total per dealer but no section detail, so no area can be shown and no area-based priority can be suggested. " +
        "The dealer-level checklist behind this total is in the dealer comparison page held with this file.</div>"
      : "";

    if (d.gaps && d.gaps.length) {
      var g = '<h3 style="margin:18px 0 6px;font-size:15px">Largest unfinished checklist items</h3>' +
        '<p class="lead">Where this dealer left the most points on the table, against the market average on the same item. Useful as the starting conversation before a priority is chosen.</p>' +
        '<table><thead><tr><th style="width:74px">Item</th><th>Checklist item</th><th class="num" style="width:96px">This dealer</th><th class="num" style="width:130px">Market average</th></tr></thead><tbody>';
      d.gaps.forEach(function (x) {
        g += "<tr><td>" + esc(x.q) + "</td><td>" + esc(x.t) + '</td><td class="num">' +
          (Math.round(x.s * 10) / 10) + " / " + x.m + " points</td><td class=\"num\">" + pct(x.ca) + "</td></tr>";
      });
      g += "</tbody></table>";
      if (DATA.extract.questions_withheld) {
        g += '<p class="muted">' + DATA.extract.questions_withheld +
          " checklist items are not reproduced on this page. Their wording names an internal programme, so they are left to the dealer comparison page.</p>";
      }
      $("where-gaps").innerHTML = g;
    } else {
      $("where-gaps").innerHTML = d.to ? "" :
        '<p class="muted">No individual checklist item is shown for this dealer on the extract.</p>';
    }
  }

  function kpi(label, value, sub, tip, cls) {
    return '<div class="kpi ' + (cls || "") + '" tabindex="0"><div class="l">' + esc(label) +
      '</div><div class="v">' + esc(value) + '</div><div class="s">' + esc(sub) +
      '</div><div class="tip">' + esc(tip) + "</div></div>";
  }

  /* ---------- 3. priority ---------- */
  function renderPriority() {
    var d = current();
    if (!d) { return; }
    var cands = prioCandidates(d);
    if (!cands.length) {
      $("prio-list").innerHTML = "";
      $("prio-empty").innerHTML = '<div class="empty"><b>No priority can be derived for this dealer.</b> ' +
        esc(marketName(d.c)) + " holds a total only, with no scored area, so there is nothing to rank. " +
        "Agree the priority with the distributor from the checklist in the dealer comparison page, then write the milestones below.</div>";
      return;
    }
    $("prio-empty").innerHTML = "";
    var html = "";
    var weakest = cands[0];
    cands.forEach(function (id, idx) {
      var s = d.sec[id];
      var sel = state.priority === id ? " sel" : "";
      var suggested = idx < 2;
      html += '<div class="prio' + sel + '" data-sec="' + id + '">' +
        '<div class="t">' + esc(id + ". " + sectLabel(id)) +
        ' <span class="pill ' + band(s.p)[1] + '">' + band(s.p)[0] + "</span>" +
        (suggested ? ' <span class="pill sugg">suggested</span>' : "") + "</div>" +
        '<div class="d">' + pct(s.p) + " on this area · market average " + pct(s.ca) + " · " + pp(s.p - (s.ca == null ? s.p : s.ca)) +
        (id === weakest ? " · weakest scored area for this dealer" : "") + "</div></div>";
    });
    SECTION_IDS.forEach(function (id) {
      if (cands.indexOf(id) !== -1) { return; }
      var s = d.sec[id];
      html += '<div class="prio off"><div class="t">' + esc(id + ". " + sectLabel(id)) +
        ' <span class="pill ns">Not scored</span></div><div class="d">' + esc(s ? s.na : NOT_SCORED_INLINE) + "</div></div>";
    });
    $("prio-list").innerHTML = html;

    Array.prototype.forEach.call($("prio-list").querySelectorAll(".prio[data-sec]"), function (el) {
      el.addEventListener("click", function () {
        state.priority = el.getAttribute("data-sec");
        renderPriority();
        renderProgress();
        renderSummary();
      });
    });
  }

  var NOT_SCORED_INLINE = "Not scored in this assessment — not offered as a priority.";

  /* ---------- 4. milestones ---------- */
  function blankRow() { return { d: "", note: "", ev: "", done: false }; }

  function renderMiles() {
    var body = $("mil-body");
    if (!state.miles.length) { state.miles = [blankRow(), blankRow(), blankRow()]; }
    body.innerHTML = state.miles.map(function (m, i) {
      return "<tr>" +
        '<td>' + (i + 1) + "</td>" +
        '<td><input type="date" data-i="' + i + '" data-k="d" value="' + esc(m.d) + '"></td>' +
        '<td><input type="text" data-i="' + i + '" data-k="note" value="' + esc(m.note) + '" placeholder="What will be done"></td>' +
        '<td><input type="text" data-i="' + i + '" data-k="ev" value="' + esc(m.ev) + '" placeholder="What was sent, what happened"></td>' +
        '<td style="text-align:center"><input type="checkbox" data-i="' + i + '" data-k="done"' + (m.done ? " checked" : "") + "></td>" +
        '<td class="noprint"><button type="button" data-del="' + i + '">Remove</button></td>' +
        "</tr>";
    }).join("");
    Array.prototype.forEach.call(body.querySelectorAll("input"), function (el) {
      el.addEventListener("input", onEdit);
      el.addEventListener("change", onEdit);
    });
    Array.prototype.forEach.call(body.querySelectorAll("button[data-del]"), function (el) {
      el.addEventListener("click", function () {
        state.miles.splice(parseInt(el.getAttribute("data-del"), 10), 1);
        renderMiles(); renderProgress(); renderSummary();
      });
    });
  }

  function onEdit(ev) {
    var el = ev.target;
    var i = parseInt(el.getAttribute("data-i"), 10);
    var k = el.getAttribute("data-k");
    if (!state.miles[i]) { return; }
    state.miles[i][k] = (k === "done") ? el.checked : el.value;
    if (k === "done" || k === "d") { renderProgress(); renderSummary(); }
  }

  function usedRows() {
    return state.miles.filter(function (m) {
      return (m.d || "").trim() || (m.note || "").trim() || (m.ev || "").trim() || m.done;
    });
  }

  function renderProgress() {
    var rows = usedRows();
    var done = rows.filter(function (m) { return m.done; }).length;
    var p = rows.length ? (done / rows.length) : 0;
    $("prog-fill").style.width = (p * 100).toFixed(0) + "%";
    $("prog-text").innerHTML = rows.length
      ? "<b>" + done + " of " + rows.length + "</b> milestones recorded for this priority are marked done. " +
        (state.priority ? "Priority: " + esc(state.priority + ". " + sectLabel(state.priority)) + ". " : "No priority chosen yet. ") +
        "The assessment score on the extract is " + (current() && current().tot != null ? pct(current().tot) : "—") + " and is unchanged by this."
      : "No milestone recorded yet" + (state.priority ? " for " + esc(state.priority + ". " + sectLabel(state.priority)) : "") +
        ". Until one is typed there is nothing to show, and nothing is invented to fill the gap. The assessment score on the extract is " +
        (current() && current().tot != null ? pct(current().tot) : "—") + " and is unchanged by anything on this page.";

    var dated = rows.filter(function (m) { return /^\d{4}-\d{2}-\d{2}$/.test(m.d); })
      .sort(function (a, b) { return a.d < b.d ? -1 : 1; });
    if (!dated.length) {
      $("tl-wrap").innerHTML = '<div class="empty"><b>No dated milestones yet.</b> The line appears as soon as at least one milestone has a date. ' +
        "This workspace holds no development history for any dealer, so the page starts empty on purpose rather than showing a made-up past.</div>";
      return;
    }
    var first = new Date(dated[0].d + "T00:00:00").getTime();
    var last = new Date(dated[dated.length - 1].d + "T00:00:00").getTime();
    var span = Math.max(last - first, 1);
    var w = 1000, h = 66, pad = 30;
    var svg = '<svg class="tl" viewBox="0 0 ' + w + " " + h + '" preserveAspectRatio="none" role="img" aria-label="Milestone dates">';
    svg += '<line x1="' + pad + '" y1="34" x2="' + (w - pad) + '" y2="34" stroke="#d9d3c8" stroke-width="2"></line>';
    dated.forEach(function (m, idx) {
      var t = new Date(m.d + "T00:00:00").getTime();
      var x = pad + ((w - 2 * pad) * (t - first) / span);
      var colour = m.done ? "#1d9e75" : "#c0552d";
      svg += '<circle cx="' + x.toFixed(1) + '" cy="34" r="7" fill="' + (m.done ? colour : "#fff") + '" stroke="' + colour + '" stroke-width="2"></circle>';
      svg += '<text x="' + x.toFixed(1) + '" y="' + (idx % 2 ? 58 : 18) + '" font-size="11" fill="#15233c" text-anchor="middle">' + esc(m.d.slice(5)) + "</text>";
    });
    svg += "</svg>";
    var list = '<table><thead><tr><th style="width:110px">Date</th><th>Milestone</th><th>Evidence</th><th style="width:88px">Status</th></tr></thead><tbody>';
    dated.forEach(function (m) {
      list += "<tr><td>" + esc(m.d) + "</td><td>" + esc(m.note || "—") + "</td><td>" + esc(m.ev || "—") +
        '</td><td><span class="pill ' + (m.done ? "good" : "medium") + '">' + (m.done ? "Done" : "Planned") + "</span></td></tr>";
    });
    list += "</tbody></table>";
    $("tl-wrap").innerHTML = svg + list +
      '<p class="muted">Filled dots are milestones marked done, open dots are planned. Dates are the ones you typed; they are not assessment dates.</p>';
  }

  /* ---------- 5. printable summary ---------- */
  function renderSummary() {
    var d = current();
    if (!d) { $("sum").innerHTML = ""; return; }
    var country = DATA.countries[d.c];
    var rowsCand = prioCandidates(d);
    var rows = "";
    SECTION_IDS.forEach(function (id) {
      var s = d.sec[id];
      if (!s) { return; }
      if (s.p == null) {
        rows += "<tr><td>" + esc(id + ". " + sectLabel(id)) + '</td><td class="num">Not scored</td><td class="num">—</td><td class="num">Not scored</td><td class="num">—</td></tr>';
        return;
      }
      rows += "<tr><td>" + esc(id + ". " + sectLabel(id)) + '</td><td class="num">' + (Math.round(s.s * 10) / 10) + " / " + s.m +
        '</td><td class="num">' + pct(s.p) + '</td><td class="num">' + pct(s.ca) + '</td><td class="num">' +
        pp(s.p - (s.ca == null ? s.p : s.ca)) + "</td></tr>";
    });
    var used = usedRows();
    var done = used.filter(function (m) { return m.done; }).length;
    var ms = "";
    used.slice(0, 6).forEach(function (m, i) {
      ms += "<tr><td>" + (i + 1) + '</td><td>' + esc(m.d || "—") + "</td><td>" + esc(m.note || "—") +
        "</td><td>" + esc(m.ev || "—") + "</td><td>" + (m.done ? "Done" : "Planned") + "</td></tr>";
    });
    if (!ms) {
      ms = '<tr><td colspan="5" style="color:#6b6256">No milestone recorded yet. This is blank on purpose: the workspace holds no development history for this dealer.</td></tr>';
    }
    $("sum").innerHTML =
      "<h3>" + esc(d.n) + "</h3>" +
      '<p class="sub">' + esc(marketName(d.c)) + " · assessment " +
      (d.ad ? esc(d.ad) : "date not supplied") + " · development summary prepared " + esc(DATA.built) + "</p>" +
      '<table><thead><tr><th>Area</th><th class="num">Points</th><th class="num">Score</th><th class="num">Market average</th><th class="num">Difference</th></tr></thead><tbody>' +
      rows + "</tbody></table>" +
      '<p class="sub" style="margin-top:8px">Total on file <b>' + pct(d.tot) + "</b> · market average <b>" + pct(country.tot) +
      "</b> · difference <b>" + pp(d.tot != null ? d.tot - country.tot : null) + "</b>. Areas marked Not scored were not assessed and are not drawn as zero.</p>" +
      "<h3 style='font-size:15px;margin:14px 0 4px'>Development priority</h3>" +
      '<p class="sub" style="margin:0 0 8px">' +
      (state.priority
        ? "<b>" + esc(state.priority + ". " + sectLabel(state.priority)) + "</b>" +
          (d.sec[state.priority] ? " — starting from " + pct(d.sec[state.priority].p) + " against a market average of " + pct(d.sec[state.priority].ca) + "." : "")
        : "<b>Not chosen yet.</b> " + (rowsCand.length ? "The weakest scored area for this dealer is " + esc(rowsCand[0] + ". " + sectLabel(rowsCand[0])) + "." : "No scored area is available to rank in this market.")) +
      "</p>" +
      "<h3 style='font-size:15px;margin:14px 0 4px'>Milestones and evidence</h3>" +
      '<table><thead><tr><th style="width:26px">#</th><th style="width:96px">Date</th><th>Milestone</th><th>Evidence</th><th style="width:66px">Status</th></tr></thead><tbody>' +
      ms + "</tbody></table>" +
      '<p class="sub" style="margin-top:8px"><b>Development progress: ' + done + " of " + used.length +
      " milestones marked done.</b> This is progress on the agreed work. It is not the assessment score, and completing a milestone does not raise the score — only a later assessment that is recorded and scored changes it.</p>" +
      '<div class="sig"><div>Dealer</div><div>Distributor</div></div>';

    $("sum-foot").textContent =
      "Starting point from the dealer assessment extract held in this workspace (version " + DATA.extract.version +
      ", " + DATA.extract.dealers + " dealers across " + DATA.extract.markets + " markets, read on " + DATA.extract.held_on +
      "). Development rows are the dealer's and its distributor's own record. Internal working paper — not a score report.";
  }

  function renderAll() {
    renderWhere(); renderPriority(); renderMiles(); renderProgress(); renderSummary();
  }

  /* ---------- save / load ---------- */
  var HEAD = "dealer-development-plan|1";
  function planText() {
    var d = current();
    var lines = [HEAD, "market|" + (state.market || ""), "dealer|" + (state.dealer || ""),
      "priority|" + (state.priority || ""), "date|note|evidence|done"];
    usedRows().forEach(function (m) {
      lines.push([m.d, m.note, m.ev, m.done ? "done" : "planned"]
        .map(function (s) { return String(s == null ? "" : s).replace(/\|/g, " ").replace(/[\r\n]+/g, " "); }).join("|"));
    });
    return lines.join("\n");
  }

  function saveFile() {
    var blob = new Blob([planText()], { type: "text/plain;charset=utf-8" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "dealer-development-plan.txt";
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 2000);
    $("save-note").textContent = "Saved as dealer-development-plan.txt in your downloads folder. Keep it with the dealer's file and load it back here next time.";
  }

  function loadText(text) {
    var lines = String(text).split(/\r?\n/).filter(function (l) { return l.trim(); });
    if (!lines.length || lines[0].indexOf("dealer-development-plan") !== 0) {
      $("save-note").textContent = "That file is not a plan file saved from this page. Nothing was changed.";
      return;
    }
    var rec = { market: "", dealer: "", priority: "" }, rows = [], headerSeen = false;
    lines.slice(1).forEach(function (line) {
      var parts = line.split("|");
      if (parts[0].toLowerCase() === "market") { rec.market = parts[1] || ""; return; }
      if (parts[0].toLowerCase() === "dealer") { rec.dealer = parts[1] || ""; return; }
      if (parts[0].toLowerCase() === "priority") { rec.priority = parts[1] || ""; return; }
      if (!headerSeen && parts[0].toLowerCase() === "date") { headerSeen = true; return; }
      rows.push({ d: parts[0] || "", note: parts[1] || "", ev: parts[2] || "", done: (parts[3] || "").toLowerCase() === "done" });
    });
    if (rec.market && DATA.markets[rec.market]) {
      state.market = rec.market;
      $("f-market").value = rec.market;
      fillDealers();
    }
    if (rec.dealer) {
      var ok = dealersFor(state.market).some(function (x) { return x.n === rec.dealer; });
      if (ok) { state.dealer = rec.dealer; $("f-dealer").value = rec.dealer; }
    }
    state.miles = rows.length ? rows : [blankRow(), blankRow(), blankRow()];
    state.priority = null;
    renderAll();
    if (rec.priority) { state.priority = rec.priority; renderPriority(); renderProgress(); renderSummary(); }
    $("save-note").textContent = "Plan loaded: " + usedRows().length + " milestone row(s) for " + state.dealer + ".";
  }

  /* ---------- start ---------- */
  initPickers();
  applyStoredMilestones(true);
  renderAll();

  $("btn-add").addEventListener("click", function () {
    state.miles.push(blankRow()); renderMiles(); renderProgress(); renderSummary();
  });
  $("btn-save").addEventListener("click", saveFile);
  $("btn-load").addEventListener("click", function () { $("file-load").click(); });
  $("btn-print").addEventListener("click", function () { window.print(); });
  $("file-load").addEventListener("change", function (ev) {
    var f = ev.target.files && ev.target.files[0];
    if (!f) { return; }
    var fr = new FileReader();
    fr.onload = function () { loadText(fr.result); };
    fr.readAsText(f);
    ev.target.value = "";
  });

  $("save-note").textContent = "Entries stay in this browser tab, plus whatever was already on file for this dealer when the page was prepared. Save them to a file to add to that record, and load a file back any time.";

  var milestoneDealerCount = DATA.milestones ? Object.keys(DATA.milestones).length : 0;

  $("knows").innerHTML =
    "<li>Sections A to E for all " + DATA.extract.dealers + " dealers in the assessment extract, with each market's average beside them.</li>" +
    "<li>The market average and the share of dealers counted in it, market by market.</li>" +
    "<li>The largest unfinished checklist items per dealer, with the market average on the same item.</li>" +
    "<li>Assessment dates where the extract carries one; " +
    DATA.dealers.filter(function (d) { return !d.ads; }).length + " of " + DATA.extract.dealers + " entries carry none and are shown as not supplied.</li>" +
    "<li>Previously saved milestones, for the " + milestoneDealerCount + " dealer(s) that have any on file as of this page's build.</li>";

  $("data-notes").textContent =
    "Sources: the dealer assessment extract held in this workspace (version " + DATA.extract.version + ", " + DATA.extract.dealers +
    " dealers, " + DATA.extract.markets + " markets, read " + DATA.extract.held_on + "). Sections not assessed are labelled Not scored and never drawn as zero. " +
    DATA.extract.questions_withheld + " checklist items are not reproduced because their wording names a supplier programme. " +
    "Milestone history is never invented: each entry shown was either typed in this session or was already saved to this dealer's record (" +
    milestoneDealerCount + " dealer(s) network-wide as of this build) before this page was prepared. No figure is sent anywhere.";
})();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
