"""Build ISZE_AI_MILESTONES.html - what was built here with AI, as a milestone list.

What it is: one page, grouped into new tools and jobs, findings that changed the
picture, and the decks and packs handed over. The words come from a hand-written
register (00_docs/AI_MILESTONES.yaml); the counted figures are READ FROM DISK at
build time so the tally is measured, not typed.

Run:  python 02_dashboards/_build/build_ai_milestones.py
Out:  02_dashboards/hub/ISZE_AI_MILESTONES.html
      (+ OPEN_ISZE_AI_MILESTONES.cmd, CRLF launcher)
"""
from __future__ import annotations

import html
import json
import re
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
YAML_PATH = ROOT / "00_docs" / "AI_MILESTONES.yaml"
OUT_DIR = ROOT / "02_dashboards" / "hub"
OUT_HTML = OUT_DIR / "ISZE_AI_MILESTONES.html"
OUT_CMD = OUT_DIR / "OPEN_ISZE_AI_MILESTONES.cmd"

MISSING: list[str] = []

# state -> (chip class, chip label)
STATE = {
    "live": ("ok", "Live"),
    "done": ("ok", "Done"),
    "pilot": ("warn", "Pilot"),
    "internal": ("warn", "Internal only"),
    "on_paper": ("todo", "On paper"),
}


# ---------------------------------------------------------------- helpers

def esc(s) -> str:
    return html.escape(str(s), quote=True)


def one_line(s) -> str:
    """Fold a YAML block into a single clean sentence."""
    return re.sub(r"\s+", " ", str(s or "")).strip()


def tip(inner: str, text: str) -> str:
    return f'<span class="tip" data-tip="{esc(text)}">{inner}</span>'


# ---------------------------------------------------------------- collectors

def read_part_numbers() -> int | None:
    p = ROOT / "01_data" / "00_derived" / "aim_master_v2.csv"
    try:
        with p.open(encoding="utf-8", errors="replace") as f:
            return max(0, sum(1 for _ in f) - 1)
    except Exception:
        MISSING.append("aim_master_v2.csv")
        return None


def count_pages() -> tuple[int, list[tuple[str, int, str]]]:
    """Real HTML pages per folder, with a plain description."""
    base = ROOT / "02_dashboards"
    where = [
        ("sales", "Sales and aftersales views"),
        ("pricing", "Price lists, price revision, scraped prices"),
        ("ids", "Dealer standards, one page per country"),
        ("ops", "Operating console and registers"),
        ("hub", "The hub pages that index everything"),
        ("fleet", "Vehicles in service"),
        ("bi", "Business intelligence"),
        ("gps", "Spend per truck"),
    ]
    rows = []
    for folder, label in where:
        try:
            n = len(list((base / folder).glob("*.html")))
        except Exception:
            n = 0
        rows.append((folder, n, label))
    return sum(n for _, n, _ in rows), rows


def count_prism_pages() -> int | None:
    p = ROOT / "03_analytics" / "Isuzu" / "prism" / "pages"
    try:
        return len([f for f in p.glob("*.py") if not f.name.startswith("_")])
    except Exception:
        MISSING.append("prism/pages")
        return None


def read_ledger() -> dict:
    p = ROOT / "01_data" / "00_derived" / "action_ledger.meta.json"
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return {
            "open": (d.get("counts") or {}).get("open"),
            "horizon": d.get("billing_horizon"),
            "adapters": len(d.get("adapter_stats") or []),
        }
    except Exception:
        MISSING.append("action_ledger.meta.json")
        return {}


def read_interactions() -> dict:
    """Local, own-mailbox interaction layer. Row counts from the parquet files."""
    base = ROOT / "01_data" / "17_interactions"
    out: dict = {}
    files = {
        "interactions": "interaction_fact.parquet",
        "commitments": "commitment_fact.parquet",
        "stakeholders": "stakeholder_dim.parquet",
    }
    try:
        import pandas as pd
    except Exception:
        MISSING.append("pandas (interaction counts)")
        return out
    for key, name in files.items():
        try:
            out[key] = len(pd.read_parquet(base / name))
        except Exception:
            MISSING.append(name)
    return out


def count_milestones(report: dict) -> int:
    return sum(len(g.get("items") or []) for g in report.get("groups") or [])


# ---------------------------------------------------------------- page pieces

def tile(value_html: str, label: str, tip_text: str, kind: str = "") -> str:
    cls = f"tile {kind}".strip()
    return f"""
      <div class="{cls}">
        <div class="tileval">{tip(value_html, tip_text)}</div>
        <div class="tilelab">{esc(label)}</div>
      </div>"""


def milestone(item: dict) -> str:
    state = str(item.get("state") or "").strip().lower()
    chip_cls, chip_label = STATE.get(state, ("todo", state.title() or "Note"))
    when = one_line(item.get("when"))
    plain = one_line(item.get("plain"))
    why = one_line(item.get("why"))
    ev = item.get("evidence") or []
    ev_html = ""
    if ev:
        ev_html = "<ul class='evlinks'>" + "".join(
            f"<li><code>{esc(one_line(p))}</code></li>" for p in ev
        ) + "</ul>"
    when_html = f"<span class='when'>{esc(when)}</span>" if when else ""
    return f"""
      <article class="ms">
        <div class="mshead">
          <h3>{esc(one_line(item.get('title')))}</h3>
          <span class="chip {chip_cls}">{esc(chip_label)}</span>
        </div>
        <p class="msplain">{esc(plain)}</p>
        <p class="mswhy"><span class="whyflag">Why it mattered:</span> {esc(why)}</p>
        <div class="msfoot">{when_html}{ev_html}</div>
      </article>"""


def build_html(report: dict, counts: dict) -> str:
    groups = report.get("groups") or []
    title = one_line(report.get("title")) or "What I built with AI"
    subtitle = one_line(report.get("subtitle"))
    intro = one_line(report.get("intro"))
    internal_note = one_line(report.get("internal_note"))

    # ---- headline tiles, every number read from disk
    n_pages, page_rows = counts["pages"]
    ms_total = counts["milestones"]
    n_prism = counts["prism"]
    n_parts = counts["parts"]
    led = counts["ledger"]
    inter = counts["interactions"]

    tiles = [
        tile(f"{ms_total}", "Milestones on this page",
             "Every tool, finding and pack listed below. The list is written by hand in "
             "00_docs/AI_MILESTONES.yaml; this page only counts and lays it out.", "money"),
        tile(f"{n_pages}" if n_pages else "not read",
             "Pages that open today",
             "HTML pages counted in their folders under 02_dashboards at build time. "
             "It includes this page and the hub itself.", "count"),
        tile(f"{n_prism}" if n_prism is not None else "not read",
             "Pages in the analytical app",
             "Working pages in the local PRISM app (fleet, spend per truck, capture, mix, "
             "warranty, forecast, dealers, tenders) at build time.", "count"),
        tile(f"{n_parts:,}" if n_parts else "not read",
             "Part numbers classified",
             "Every part number given a family and a product form, from the classification "
             "master. This is the foundation the aftermarket pages sit on.", "count"),
        tile(f"{led.get('open'):,}" if led.get("open") else "not read",
             "Open opportunities in the ledger",
             f"Rows joined from {led.get('adapters', 'several')} separate findings into one queue, "
             f"each carrying where its number came from. Billing read through {led.get('horizon', '?')}.",
             "count"),
        tile(f"{inter.get('interactions'):,}" if inter.get("interactions") else "not read",
             "Mail interactions read locally",
             "Own mailbox only, kept on this machine, bodies not stored. Counts what was "
             "promised and who was involved — it never stores the message text.", "count"),
    ]
    tiles_html = "".join(tiles)

    # ---- one section per group
    sections = []
    for i, g in enumerate(groups, start=2):
        label = one_line(g.get("label"))
        blurb = one_line(g.get("blurb"))
        items = g.get("items") or []
        cards = "".join(milestone(it) for it in items)
        sections.append(f"""
  <section id="{esc(g.get('id') or f'g{i}')}">
    <div class="shead"><span class="n">{i:02d}</span><h2>{esc(label)}</h2>
      <p>{esc(blurb)}</p></div>
    <div class="mslist">{cards}</div>
  </section>""")
    sections_html = "".join(sections)

    # ---- folder tally (measured)
    tally_rows = "".join(
        f"<tr><td><code>{esc(folder)}</code></td>"
        f"<td class='r'>{n}</td><td>{esc(lab)}</td></tr>"
        for folder, n, lab in page_rows
    )

    internal_banner = ""
    if internal_note:
        internal_banner = (
            f'<div class="note"><strong>Internal only.</strong> {esc(internal_note)}</div>'
        )

    missing_note = ""
    if MISSING:
        missing_note = (
            "<p class='missing'>This page could not read: "
            + ", ".join(esc(m) for m in sorted(set(MISSING)))
            + ". The affected numbers say so instead of showing a guess.</p>"
        )

    built_at = datetime.now().strftime("%d %B %Y, %H:%M")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<style>
:root{{
  --navy:#15233c; --navy2:#1d3050; --terra:#c0552d; --paper:#f7f4ee; --card:#fff;
  --ink:#232a35; --muted:#5f6b7a; --line:#dfd8cc;
  --ok:#2f7d5b; --warn:#b07d1a; --todo:#9a3b3b;
}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);
  font-family:"Segoe UI",-apple-system,Roboto,Arial,sans-serif;line-height:1.55;font-size:16px}}
h1,h2,h3,h4{{font-family:Georgia,"Times New Roman",serif;color:var(--navy);margin:0}}
code{{font-family:Consolas,"Courier New",monospace;font-size:.83em;background:#f0ece3;
  padding:1px 5px;border-radius:3px;color:#3c4655;word-break:break-all}}
.wrap{{max-width:1180px;margin:0 auto;padding:0 22px 70px}}

/* hero */
.hero{{background:linear-gradient(160deg,var(--navy) 0%,var(--navy2) 100%);color:var(--paper);
  padding:52px 22px 44px}}
.hero .inner{{max-width:1180px;margin:0 auto}}
.eyebrow{{text-transform:uppercase;letter-spacing:.19em;font-size:11.5px;color:#e8b79c;margin-bottom:12px}}
.hero h1{{color:#fff;font-size:44px;line-height:1.12;letter-spacing:-.5px;margin-bottom:16px}}
.lede{{font-size:18.5px;color:#dfe6ef;max-width:840px;margin:0 0 18px}}
.stamp{{font-size:13px;color:#a9b8cc;border-top:1px solid #33496b;padding-top:14px;max-width:900px}}

/* sections */
section{{margin-top:52px}}
.shead{{display:flex;align-items:baseline;gap:14px;border-bottom:2px solid var(--navy);
  padding-bottom:9px;margin-bottom:26px}}
.shead .n{{font-family:Georgia,serif;font-size:15px;color:var(--terra);font-weight:700}}
.shead h2{{font-size:27px}}
.shead p{{margin:0;color:var(--muted);font-size:14.5px;margin-left:auto;text-align:right;max-width:440px}}

/* tiles */
.tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(268px,1fr));gap:15px}}
.tile{{background:var(--card);border:1px solid var(--line);border-top:4px solid var(--navy);
  border-radius:5px;padding:20px 20px 17px}}
.tileval{{font-family:Georgia,serif;font-size:31px;color:var(--navy);line-height:1.1}}
.tilelab{{font-weight:600;font-size:14.5px;color:var(--terra);margin:7px 0 0;
  text-transform:uppercase;letter-spacing:.05em}}

/* tooltip on a counted number */
.tip{{position:relative;cursor:help;border-bottom:1px dotted #c0552d}}
.tip::after{{content:attr(data-tip);position:absolute;left:0;top:1.7em;z-index:40;
  width:270px;background:var(--navy);color:var(--paper);padding:9px 11px;border-radius:4px;
  font-family:"Segoe UI",sans-serif;font-size:12.5px;font-weight:400;line-height:1.4;
  text-transform:none;letter-spacing:0;opacity:0;pointer-events:none;transition:.12s;
  border-top:3px solid var(--terra);box-shadow:0 6px 18px rgba(21,35,60,.28)}}
.tip:hover::after{{opacity:1}}

/* milestone cards */
.mslist{{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:16px}}
.ms{{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--navy);
  border-radius:5px;padding:20px}}
.mshead{{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;margin-bottom:9px}}
.mshead h3{{font-size:18px;line-height:1.25}}
.msplain{{margin:0 0 11px;font-size:14.5px;color:#3d4757}}
.mswhy{{margin:0;font-size:14px;color:#4a4132;background:#fbf6ec;border-left:3px solid var(--terra);
  padding:9px 12px;border-radius:0 4px 4px 0}}
.whyflag{{color:var(--terra);font-weight:700}}
.msfoot{{margin-top:12px;border-top:1px dashed var(--line);padding-top:11px}}
.when{{display:inline-block;font-size:12px;font-weight:700;text-transform:uppercase;
  letter-spacing:.06em;color:var(--muted)}}
.evlinks{{margin:9px 0 0;padding-left:0;list-style:none}}
.evlinks li{{margin:3px 0}}

/* chips */
.chip{{display:inline-block;font-size:11.5px;font-weight:700;text-transform:uppercase;
  letter-spacing:.06em;padding:4px 10px;border-radius:11px;white-space:nowrap}}
.chip.ok{{background:#e2f0e9;color:var(--ok)}}
.chip.warn{{background:#f7edd6;color:var(--warn)}}
.chip.todo{{background:#f6e3e2;color:var(--todo)}}

/* tables */
table{{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);
  border-radius:5px;overflow:hidden;font-size:14.5px}}
th{{background:var(--navy);color:#fff;text-align:left;padding:11px 14px;font-size:12.5px;
  text-transform:uppercase;letter-spacing:.07em;font-weight:600}}
td{{padding:11px 14px;border-top:1px solid var(--line);vertical-align:top;color:#3d4757}}
td.r{{text-align:right;font-variant-numeric:tabular-nums;font-weight:600;color:var(--navy)}}
tbody tr:nth-child(even){{background:#faf7f1}}

.note{{background:#fbf6ec;border-left:4px solid var(--terra);padding:15px 18px;
  border-radius:0 4px 4px 0;font-size:14.5px;color:#4a4132;margin-top:20px}}
.missing{{font-size:13.5px;color:var(--todo)}}
footer{{margin-top:60px;border-top:2px solid var(--navy);padding-top:20px;font-size:13px;color:var(--muted)}}
footer code{{font-size:.85em}}
@media (max-width:640px){{
  .hero h1{{font-size:31px}} .shead{{flex-wrap:wrap}} .shead p{{margin-left:0;text-align:left}}
}}
</style>
<script src="../_ui/isze-shell.js" defer></script>
</head>
<body>

<header class="hero"><div class="inner">
  <div class="eyebrow">Isuzu Universe &middot; built with AI</div>
  <h1>{esc(title)}</h1>
  <p class="lede">{esc(intro)}</p>
  <div class="stamp">Built {esc(built_at)}. Every counted figure on this page was read from
  the files named beside it at build time. Nothing here changes, publishes or sends anything.</div>
</div></header>

<div class="wrap">

  {internal_banner}

  <section id="minute">
    <div class="shead"><span class="n">01</span><h2>The one-minute version</h2>
      <p>Six numbers behind the list below. Hover any number for what it counts.</p></div>
    <div class="tiles">{tiles_html}</div>
  </section>

  {sections_html}

  <section id="tally">
    <div class="shead"><span class="n">&middot;</span><h2 style="font-size:21px">Where the pages live</h2>
      <p>Counted in the folders at build time, so the tally moves on its own.</p></div>
    <table>
      <thead><tr><th>Folder</th><th style="text-align:right">Pages</th><th>What it holds</th></tr></thead>
      <tbody>{tally_rows}</tbody>
    </table>
    <div class="note"><strong>How to read this page.</strong> The words are hand-written in
    <code>00_docs/AI_MILESTONES.yaml</code>; the numbers are read from disk when the page is built.
    A line added to the register shows up here on the next build. Say the change, rebuild, and it
    is current. One evidence folder is named for the dealer-sales data it holds
    (<code>01_data/05_Dealer_sellout/</code>); it is quoted once, in this footnote,
    because it is the real folder name.
    {esc(missing_note)}</div>
  </section>

  <footer>
    <p>Counted at build time from: the classification master (<code>aim_master_v2.csv</code>);
    the HTML pages under <code>02_dashboards/</code>; the working pages under
    <code>03_analytics/Isuzu/prism/pages/</code>; the action ledger
    (<code>action_ledger.meta.json</code>); and the local interaction layer
    (<code>01_data/17_interactions/</code>). Written source: <code>00_docs/AI_MILESTONES.yaml</code>.</p>
    <p>This page is a description. It changes nothing, publishes nothing and sends nothing.</p>
  </footer>

</div>
</body>
</html>
"""


def write_cmd() -> None:
    body = (
        "@echo off\r\n"
        'start "" "%~dp0ISZE_AI_MILESTONES.html"\r\n'
    )
    OUT_CMD.write_bytes(body.encode("ascii"))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report = yaml.safe_load(YAML_PATH.read_text(encoding="utf-8")) or {}
    counts = {
        "pages": count_pages(),
        "prism": count_prism_pages(),
        "parts": read_part_numbers(),
        "ledger": read_ledger(),
        "interactions": read_interactions(),
        "milestones": count_milestones(report),
    }
    html_out = build_html(report, counts)
    OUT_HTML.write_text(html_out, encoding="utf-8")  # no BOM
    write_cmd()
    print(f"wrote {OUT_HTML} ({OUT_HTML.stat().st_size / 1024:.0f} KB)")
    print(f"wrote {OUT_CMD}")
    print(f"milestones={counts['milestones']} pages={counts['pages'][0]} "
          f"prism={counts['prism']} parts={counts['parts']} "
          f"ledger_open={(counts['ledger'] or {}).get('open')} "
          f"interactions={(counts['interactions'] or {}).get('interactions')}")
    if MISSING:
        print("MISSING sources:", sorted(set(MISSING)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
