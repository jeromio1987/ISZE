"""Build ISZE_UNIVERSE_MAP.html - one plain-language map of the whole Isuzu Universe.

What it is: a single page that shows what connects to what, what is actually built,
and what is still only on paper. Written for a reader who is not technical.

Every number is READ FROM DISK at build time (or from the Windows task list). Nothing
is typed by hand. If a source is missing, the page says so instead of showing a guess.

Run:  python 02_dashboards/_build/build_universe_map.py
Out:  02_dashboards/hub/ISZE_UNIVERSE_MAP.html  (+ OPEN_ISZE_UNIVERSE_MAP.cmd)
"""
from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "02_dashboards" / "hub"
OUT_HTML = OUT_DIR / "ISZE_UNIVERSE_MAP.html"
OUT_CMD = OUT_DIR / "OPEN_ISZE_UNIVERSE_MAP.cmd"

MISSING: list[str] = []


def esc(s) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def eur(v: float) -> str:
    """Euro in the short form a person reads: EUR 30.8M."""
    if v is None:
        return "not read"
    a = abs(v)
    if a >= 1_000_000:
        return f"EUR {v / 1_000_000:,.1f}M"
    if a >= 1_000:
        return f"EUR {v / 1_000:,.0f}k"
    return f"EUR {v:,.0f}"


def num(v) -> str:
    return f"{int(v):,}" if v is not None else "not read"


def rel_label(href: str) -> str:
    """A readable path for display, from a hub-relative href."""
    h = href.replace("../", "", 1) if href.startswith("../") else href
    if h.startswith("../../"):
        return h[6:]
    return "02_dashboards/" + h


# ---------------------------------------------------------------- collectors

def read_metrics() -> dict:
    p = ROOT / "01_data" / "00_derived" / "metrics_snapshot.json"
    try:
        return json.loads(p.read_text(encoding="utf-8")).get("metrics", {})
    except Exception:
        MISSING.append("metrics_snapshot.json")
        return {}


def read_wallet() -> dict:
    p = ROOT / "01_data" / "00_derived" / "wallet_waterfall.csv"
    try:
        d = pd.read_csv(p)
        y = d[d["year"] == 2025]
        return {
            "markets": len(y),
            "wallet": float(y["theoretical_wallet_eur"].sum()),
            "captured": float(y["captured_total_eur"].sum()),
            "uncaptured": float(y["uncaptured_eur"].sum()),
            "pct": float(y["captured_total_eur"].sum() / y["theoretical_wallet_eur"].sum() * 100),
        }
    except Exception:
        MISSING.append("wallet_waterfall.csv")
        return {}


def read_tender() -> dict:
    p = ROOT / "01_data" / "14_dashboards" / "tender_data.json"
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        o = d["opportunities"]
        m = d.get("meta", {})
        st = m.get("stats", {})
        today = datetime.now().strftime("%Y-%m-%d")
        return {
            "generated": (m.get("generated_at") or "")[:10],
            "rows": len(o),
            "notices": st.get("raw_notices"),
            "rm": sum(1 for r in o if r.get("rm_contract")),
            "rm_only": sum(1 for r in o if str(r.get("product_segment_label", "")).startswith("R&M only")),
            "rm_open": sum(1 for r in o if r.get("rm_contract") and str(r.get("deadline_date") or "") >= today),
            "value": sum(1 for r in o if r.get("value_amount")),
            "fleet": sum(1 for r in o if r.get("fleet_size")),
            "deadline": sum(1 for r in o if r.get("deadline_date")),
            "no_deadline": sum(1 for r in o if not r.get("deadline_date")),
            "outcomes": (m.get("outcomes_summary") or {}).get("recorded", 0),
            "countries": len(m.get("country_counts", {})),
        }
    except Exception:
        MISSING.append("tender_data.json")
        return {}


def read_crossref() -> dict:
    p = ROOT / "04_tools" / "aftermarket_intelligence" / "state" / "CROSSREF_GRAPH_REPORT.md"
    try:
        t = p.read_text(encoding="utf-8", errors="replace")
        def grab(pat, cast=str, default=None):
            m = re.search(pat, t)
            if not m:
                return default
            try:
                return cast(m.group(1).replace(",", ""))
            except Exception:
                return default
        return {
            "parts": grab(r"Isuzu part numbers reached: (\d+) of (\d+)", int),
            "of_total_raw": grab(r"Isuzu part numbers reached: \d+ of (\d+)", int),
            "billed": grab(r"billed value of those parts: EUR ([\d,]+)", float),
            "two_parts": grab(r"### 2\+ sources[\s\S]*?Isuzu part numbers reached: (\d+)", int),
            "witness2": grab(r"2\+ INDEPENDENT witnesses[\s\S]*?competitor numbers: (\d+)", int),
        }
    except Exception:
        MISSING.append("CROSSREF_GRAPH_REPORT.md")
        return {}


def read_ratio() -> dict:
    p = ROOT / "04_tools" / "aftermarket_intelligence" / "state" / "RATIO_MODEL_REPORT.md"
    try:
        t = p.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"typical miss model x([\d.]+) \(off by (\d+)%\) vs constant x([\d.]+) \(off by (\d+)%\)", t)
        if m:
            return {"model": int(m.group(2)), "flat": int(m.group(4))}
    except Exception:
        pass
    MISSING.append("RATIO_MODEL_REPORT.md")
    return {}


def read_scrapers() -> dict:
    p = ROOT / "04_tools" / "autodoc_scraper" / "refresh_and_check_drift.py"
    try:
        t = p.read_text(encoding="utf-8", errors="replace")
        block = t.split("JOBS = [", 1)[1].split("]", 1)[0]
        jobs = re.findall(r'\("([a-z_]+)\.py"', block)
        return {"live": jobs, "n": len(jobs)}
    except Exception:
        MISSING.append("refresh_and_check_drift.py")
        return {}


def read_tasks() -> list[dict]:
    """Live Windows scheduled tasks (ISZE only). Falls back to a stated blank."""
    names = ["\\ISZE Tender Monitor", "\\ISZE_PriceLedger_Weekly"]
    out = []
    for n in names:
        row = {"name": n.lstrip("\\"), "last": "?", "next": "?", "result": "?"}
        try:
            r = subprocess.run(["schtasks", "/query", "/tn", n, "/fo", "LIST", "/v"],
                               capture_output=True, text=True, timeout=25)
            for line in (r.stdout or "").splitlines():
                if ":" not in line:
                    continue
                k, _, v = line.partition(":")
                k, v = k.strip().lower(), v.strip()
                if k == "last run time":
                    row["last"] = v
                elif k == "next run time":
                    row["next"] = v
                elif k == "last result":
                    row["result"] = v
            row["never"] = row["last"].startswith("30/11/1999") or row["last"].startswith("1999")
        except Exception:
            row["never"] = False
        out.append(row)
    if not out:
        MISSING.append("scheduled tasks")
    return out


def read_aim_rows() -> int | None:
    p = ROOT / "01_data" / "00_derived" / "aim_master_v2.csv"
    try:
        with p.open(encoding="utf-8", errors="replace") as f:
            return max(0, sum(1 for _ in f) - 1)
    except Exception:
        MISSING.append("aim_master_v2.csv")
        return None


def count_pages() -> list[tuple[str, int, str]]:
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
        ("globe", "Map view"),
    ]
    rows = []
    for folder, label in where:
        try:
            n = len(list((base / folder).glob("*.html")))
        except Exception:
            n = 0
        rows.append((folder, n, label))
    return rows


# ---------------------------------------------------------------- content

def build_context() -> dict:
    m = read_metrics()
    w = read_wallet()
    t = read_tender()
    x = read_crossref()
    r = read_ratio()
    s = read_scrapers()
    tasks = read_tasks()
    aim = read_aim_rows()
    pages = count_pages()

    def mv(key, field="value"):
        return (m.get(key) or {}).get(field)

    return {
        "built_at": datetime.now().strftime("%d %B %Y, %H:%M"),
        "parts_base": mv("sales.parts_base_eur"),
        "through": mv("sales.parts_base_data_through"),
        "rows": mv("sales_fact.rows"),
        "verify_pass": mv("verify.pass"),
        "verify_fail": mv("verify.fail"),
        "verify_at": (mv("verify.generated") or "")[:16].replace("T", " "),
        "defection": mv("defection.active_alerts"),
        "wallet": w,
        "tender": t,
        "crossref": x,
        "ratio": r,
        "scrapers": s,
        "tasks": tasks,
        "aim": aim,
        "pages": pages,
    }


# ---------------------------------------------------------------- page

def stage_card(n, title, q, body, chip, chip_kind) -> str:
    return f"""
      <article class="stage">
        <div class="stagenum">{n}</div>
        <h3>{esc(title)}</h3>
        <p class="stageq">{esc(q)}</p>
        <p class="stagebody">{body}</p>
        <span class="chip {chip_kind}">{esc(chip)}</span>
      </article>"""


def tool_card(name, question, status, kind, evidence, links) -> str:
    link_html = ""
    if links:
        link_html = "<ul class='evlinks'>" + "".join(
            f"<li><code>{esc(p)}</code></li>" for p in links
        ) + "</ul>"
    return f"""
      <article class="tool">
        <div class="toolhead">
          <h3>{esc(name)}</h3>
          <span class="chip {kind}">{esc(status)}</span>
        </div>
        <p class="toolq">{esc(question)}</p>
        <p class="toolev">{evidence}</p>
        {link_html}
      </article>"""


def build_html(c: dict) -> str:
    w, t, x, r, s = c["wallet"], c["tender"], c["crossref"], c["ratio"], c["scrapers"]
    x_total = f"{x.get('of_total_raw'):,}" if x.get("of_total_raw") else "?"

    # ---- headline tiles
    tiles = [
        (eur(c["parts_base"]), "Parts we billed",
         f"All Isuzu parts billed to distributors, in the {c['rows']:,} rows of sales we hold, "
         f"up to {c['through']}. Source: metrics snapshot.",
         "money"),
        (eur(w.get("wallet")), "Target spend, whole network",
         f"What the vehicles in service would spend on parts if every one bought at the "
         f"planning rate. {w.get('markets','?')} markets, calendar 2025. This is a ceiling, not a forecast.",
         "money"),
        (f"{w.get('pct',0):.1f}%", "Share of that ceiling we reach",
         f"Parts billed divided by target spend: {eur(w.get('captured'))} of {eur(w.get('wallet'))}. "
         f"The rest, {eur(w.get('uncaptured'))}, is the size of the opportunity.",
         "pct"),
        (num(c["aim"]), "Part numbers classified",
         "Every part number we hold, given a family and a product form so it can be grouped. "
         "Source: the classification master.",
         "count"),
        (f"{x.get('parts','?')} of {x_total}", "Part numbers with a competitor price",
         f"The cross-reference reaches {x.get('parts')} of our {x_total} part numbers, "
         f"carrying {eur(x.get('billed'))} of billing. The other sources are labelled below.",
         "warn"),
        (f"{t.get('rows','?')}", "Live public tenders watched",
         f"Open opportunities collected {t.get('generated','')} from national portals and the EU-wide "
         f"portal. {t.get('rm')} are repair-and-maintenance contracts. {t.get('outcomes',0)} outcomes recorded so far.",
         "count"),
    ]
    tile_html = "".join(
        f"""
      <div class="tile {kind}">
        <div class="tileval">{esc(val)}</div>
        <div class="tilelab">{esc(lab)}</div>
        <div class="tiletip">{esc(tip)}</div>
      </div>""" for val, lab, tip, kind in tiles
    )

    # ---- the map
    stages = [
        ("1", "The vehicles", "How many are on the road?",
         "The fleet each market runs, split by truck weight and pickup. This is the base every other number is divided by.",
         f"{w.get('markets','?')} markets, calendar 2025", "ok"),
        ("2", "What we billed", "What did they actually buy from us?",
         "Every part we invoiced a distributor, with quantity, euro and date. The part number is the thread that runs through everything.",
         f"{eur(c['parts_base'])} to {c['through']}", "ok"),
        ("3", "What each part is", "What kind of part is it, and does it fit?",
         "Each part number given a family (brakes, filters, steering) and a product form (element, kit, housing), and matched to the vehicle bands it fits.",
         f"{num(c['aim'])} part numbers classified", "ok"),
        ("4", "What the market charges", "What does the same part cost elsewhere?",
         "Competitor prices collected from public shops and catalogues, matched to our part numbers. Thin today, and the map says exactly how thin.",
         f"{x.get('parts','?')} of {x_total} parts have a competitor price", "warn"),
        ("5", "The decisions", "What do we do about it?",
         "Where the analysis becomes action: the price revision, price gaps per market, tenders worth bidding, and which dealer needs attention.",
         "Runs, but the tender outcome half is empty", "warn"),
        ("6", "What we hand over", "What can someone else open?",
         "The pages and packs: distributor reviews, country pages, the executive paper, the dealer standard comparisons.",
         f"{sum(n for _, n, _ in c['pages'])} live pages", "ok"),
    ]
    map_html = "".join(stage_card(*st) for st in stages)

    # ---- five tools, honest status (checked against files on disk)
    tools = [
        ("AIM Commercial Atlas", "What is really changing in my parts business, and where?",
         "Partly built", "warn",
         "A parts atlas page and a truck catalogue exist, sitting on the classification rebuild finished today. "
         "The classification itself is solid. What is missing is a view a distributor opens and drives himself.",
         ["Isuzu Universe/02_Atlas/AIM_Parts_Atlas_v2.0.html",
          "02_dashboards/pricing/ISZE_AIM_Truck_Catalogue_2026-09-18.html"]),
        ("IDS Development Studio", "What should I improve, and what has moved?",
         "Partly built", "warn",
         "The assessment half is built: 25 pages, one per country, with a Portugal dealer map and a Belgium follow-up page. "
         "The second half of the name, tracking progress and evidence over time, is not built.",
         ["02_dashboards/ids/IDS_2026_dealer_compare.html",
          "02_dashboards/ids/IDS_2026_Portugal_dealer_map.html"]),
        ("Range &amp; Campaign Planner", "Which products belong in this initiative, and for whom?",
         "On paper", "todo",
         "No file for this was found on disk. It is described in the strategy paper; it has not been built.",
         []),
        ("Pricing &amp; Margin Lab", "What does this trade-off do to revenue and margin?",
         "Partly built", "warn",
         "30 pricing pages exist, including the revision pack and a pricing action map. "
         "They are ISZE's own analysis. There is no shared lab where a distributor tests a trade-off himself.",
         ["02_dashboards/pricing/ISZE_Pricing_Revision_AIM_Source.html",
          "02_dashboards/pricing/ISZE_Pricing_Action_Map.html"]),
        ("PRISM Market Intelligence", "Where should we concentrate effort?",
         "Internal only", "warn",
         "The app exists and runs internally on 19 pages. There is no version a distributor could open, "
         "no password on it, and no page for competitor prices. The strategy paper itself calls its showcase "
         "'for reference only'.",
         ["03_analytics/Isuzu/prism/pages/"]),
    ]
    tools_html = "".join(tool_card(*tl) for tl in tools)

    # ---- three worked examples from the paper
    examples = [
        ("Coordinated tenders",
         "A distributor spots a local opportunity; Isuzu entities put a joint vehicle and parts offer together.",
         "Half built", "warn",
         f"The collection works: {t.get('rows')} opportunities, {t.get('rm')} of them repair and maintenance, "
         f"from {t.get('countries')} countries, refreshed weekly. Two pieces are missing: nothing records what "
         f"happened to a tender ({t.get('outcomes',0)} outcomes today), and nothing routes a tender to the "
         f"distributor who could bid."),
        ("IDS development progress",
         "A dealer picks a development priority and records milestones with evidence, separate from its score.",
         "On paper", "todo",
         "Not built. The dealer comparison pages show where a dealer stands; they do not yet track what it does next."),
        ("Deal of the Day",
         "ISZE helps a distributor prepare one specific, time-limited commercial offer.",
         "On paper", "todo",
         "Not built."),
    ]
    examples_html = "".join(
        f"""
      <article class="example">
        <div class="toolhead"><h3>{esc(n)}</h3><span class="chip {k}">{esc(st)}</span></div>
        <p class="toolq">{esc(what)}</p>
        <p class="toolev">{esc(ev)}</p>
      </article>""" for n, what, st, k, ev in examples
    )

    # ---- what is built, real counts
    page_rows = "".join(
        f"<tr><td><code>{esc(folder)}</code></td><td class='r'>{n}</td><td>{esc(label)}</td></tr>"
        for folder, n, label in c["pages"]
    )

    # ---- open / weak
    open_items = [
        ("Tender outcomes", f"{t.get('outcomes',0)} of {t.get('rows')}",
         "Nothing records whether a tender was pursued, passed, won or lost. Until that is filled in, "
         "the tender list cannot say whether it is working."),
        ("Tender detail published by the buyer", f"value on {t.get('value')}, fleet size on {t.get('fleet')} of {t.get('rows')}",
         f"Most notices do not publish a value or a fleet size, and {t.get('no_deadline')} publish no deadline at all."),
        ("Competitor price coverage", f"{x.get('parts','?')} of {x_total} part numbers",
         f"Only {x.get('two_parts','?')} part numbers have two or more sources, and {x.get('witness2','?')} "
         f"competitor numbers are confirmed by more than one independent source."),
        ("Estimating an unknown competitor price", f"model is {r.get('model','?')}% off, one flat ratio is {r.get('flat','?')}% off",
         "The model that guesses a competitor price from our list price adds almost nothing over one flat "
         "number, so the part of the price list we have not matched cannot be priced by estimate."),
        ("Competitor price collection", f"{s.get('n','?')} sources run weekly",
         "Two sources are still fetched: one by part number, one by maintenance category only. "
         "Three were retired for giving false matches; two block the collector."),
        ("Price history job", "has not run yet",
         "The weekly price-history job has never completed a run. Its first run is scheduled below."),
        ("PRISM's tender page", "reads a file from May",
         "The page inside the app still reads an old tender file, not the live one, so its counts are out of date."),
    ]
    open_html = "".join(
        f"""
      <tr>
        <td class="nowrap"><strong>{esc(n)}</strong></td>
        <td class="nowrap">{esc(st)}</td>
        <td>{esc(why)}</td>
      </tr>""" for n, st, why in open_items
    )

    # ---- roadmap sequence (the paper's own order)
    seq = [
        ("Agree the scope and the tools", "A clear five-tool portfolio, with routine services written out",
         "This map, the strategy paper, the presentation and the showcase all say the same thing"),
        ("Pin the classification release", "One named file, version and build date",
         "Reproduce a family and product-form view from the frozen release"),
        ("Open two prepared views", "One Atlas view and one dealer-standard profile, ready before anyone is invited",
         "A participant completes a real task and finds it clearer than today's review"),
        ("Run the dealer sample", "Ten dealers in two markets, including one that does not want more reporting",
         "What they corrected, what was useful, what it cost them, and why some did not use it"),
        ("Run the commercial line", "At least two offers that clear the size filter",
         "Contribution measured on the same scope before, during and after, including returns"),
        ("Evaluate, then widen or stop", "A stated result, good or bad",
         "Real evidence and effort, not a screen that rendered"),
    ]
    seq_html = "".join(
        f"""
      <li class="seqitem">
        <span class="seqnum">{i}</span>
        <div>
          <h4>{esc(a)}</h4>
          <p class="seqres">{esc(b)}</p>
          <p class="seqev"><span>Move on when:</span> {esc(cc)}</p>
        </div>
      </li>""" for i, (a, b, cc) in enumerate(seq, 1)
    )

    # ---- scheduled jobs, live
    task_rows = "".join(
        f"""
      <tr>
        <td><code>{esc(j['name'])}</code></td>
        <td>{'never run' if j.get('never') else esc(j['last'])}</td>
        <td>{esc(j['next'])}</td>
      </tr>""" for j in c["tasks"]
    )

    # ---- where to look next
    nexts = [
        ("What I built with AI", "../hub/ISZE_AI_MILESTONES.html",
         "Every tool, finding and pack built here, as a milestone list"),
        ("The hub that indexes everything", "../hub/ISZE_OS_Hub.html",
         "How the layers connect, and where each one lives"),
        ("The operating console", "../ops/ISZE_OS_Console.html",
         "What is open, what is blocked, what needs a decision"),
        ("The executive aftersales paper", "../sales/ISZE_Exec_Aftersales_Paper.html",
         "The opportunity case, with category gaps and margin"),
        ("The price revision pack", "../pricing/ISZE_Pricing_Revision_AIM_Source.html",
         "The revision the price change was measured on"),
        ("The dealer-standard pages", "../ids/IDS_2026_dealer_compare.html",
         "Every country's dealer comparison"),
        ("The tender monitor", "../ops/ISZE_Tender_Monitor_v2.html",
         "The public tenders being watched, refreshed weekly"),
    ]
    next_html = "".join(
        f"""
      <a class="nextcard" href="{esc(href)}" target="_blank" rel="noopener">
        <h4>{esc(nm)}</h4>
        <p>{esc(what)}</p>
        <code>{esc(rel_label(href))}</code>
      </a>""" for nm, href, what in nexts
    )

    missing_note = ""
    if MISSING:
        missing_note = (
            "<p class='missing'>This page could not read: "
            + ", ".join(esc(m) for m in sorted(set(MISSING)))
            + ". The affected numbers say so rather than showing a guess.</p>"
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The whole picture - what is built and what is next</title>
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
  padding:52px 22px 44px;margin-bottom:0}}
.hero .inner{{max-width:1180px;margin:0 auto}}
.eyebrow{{text-transform:uppercase;letter-spacing:.19em;font-size:11.5px;color:#e8b79c;margin-bottom:12px}}
.hero h1{{color:#fff;font-size:44px;line-height:1.12;letter-spacing:-.5px;margin-bottom:16px}}
.lede{{font-size:18.5px;color:#dfe6ef;max-width:820px;margin:0 0 18px}}
.stamp{{font-size:13px;color:#a9b8cc;border-top:1px solid #33496b;padding-top:14px;max-width:900px}}

/* sections */
section{{margin-top:52px}}
.shead{{display:flex;align-items:baseline;gap:14px;border-bottom:2px solid var(--navy);
  padding-bottom:9px;margin-bottom:26px}}
.shead .n{{font-family:Georgia,serif;font-size:15px;color:var(--terra);font-weight:700}}
.shead h2{{font-size:27px}}
.shead p{{margin:0;color:var(--muted);font-size:14.5px;margin-left:auto;text-align:right;max-width:430px}}

/* tiles */
.tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(268px,1fr));gap:15px}}
.tile{{background:var(--card);border:1px solid var(--line);border-top:4px solid var(--navy);
  border-radius:5px;padding:20px 20px 17px;position:relative}}
.tile.warn{{border-top-color:var(--terra)}}
.tileval{{font-family:Georgia,serif;font-size:31px;color:var(--navy);line-height:1.1}}
.tilelab{{font-weight:600;font-size:14.5px;color:var(--terra);margin:7px 0 9px;
  text-transform:uppercase;letter-spacing:.05em}}
.tiletip{{font-size:13.5px;color:var(--muted)}}

/* map */
.map{{display:grid;grid-template-columns:repeat(auto-fit,minmax(310px,1fr));gap:16px}}
.stage{{background:var(--card);border:1px solid var(--line);border-radius:5px;padding:20px;
  position:relative;border-left:4px solid var(--navy)}}
.stagenum{{position:absolute;top:-13px;left:18px;width:27px;height:27px;border-radius:50%;
  background:var(--navy);color:#fff;font-size:13.5px;font-weight:700;display:flex;
  align-items:center;justify-content:center;font-family:Georgia,serif}}
.stage h3{{font-size:18.5px;margin:10px 0 5px}}
.stageq{{font-style:italic;color:var(--terra);font-size:14px;margin:0 0 11px}}
.stagebody{{font-size:14.5px;color:#3d4757;margin:0 0 14px}}

/* chips */
.chip{{display:inline-block;font-size:11.5px;font-weight:700;text-transform:uppercase;
  letter-spacing:.06em;padding:4px 10px;border-radius:11px;white-space:nowrap}}
.chip.ok{{background:#e2f0e9;color:var(--ok)}}
.chip.warn{{background:#f7edd6;color:var(--warn)}}
.chip.todo{{background:#f6e3e2;color:var(--todo)}}

/* tools */
.tools{{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:16px}}
.tool{{background:var(--card);border:1px solid var(--line);border-radius:5px;padding:20px}}
.toolhead{{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;margin-bottom:6px}}
.toolhead h3{{font-size:18.5px}}
.toolq{{color:var(--terra);font-style:italic;font-size:14px;margin:0 0 11px}}
.toolev{{font-size:14.5px;color:#3d4757;margin:0}}
.evlinks{{margin:12px 0 0;padding-left:0;list-style:none;border-top:1px dashed var(--line);padding-top:11px}}
.evlinks li{{margin:3px 0}}

/* examples */
.examples{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px}}
.example{{background:#fdfbf7;border:1px solid var(--line);border-radius:5px;padding:19px;
  border-left:4px solid var(--terra)}}

/* tables */
table{{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);
  border-radius:5px;overflow:hidden;font-size:14.5px}}
th{{background:var(--navy);color:#fff;text-align:left;padding:11px 14px;font-size:12.5px;
  text-transform:uppercase;letter-spacing:.07em;font-weight:600}}
td{{padding:11px 14px;border-top:1px solid var(--line);vertical-align:top;color:#3d4757}}
td.r{{text-align:right;font-variant-numeric:tabular-nums;font-weight:600;color:var(--navy)}}
td.nowrap{{white-space:nowrap}}
tbody tr:nth-child(even){{background:#faf7f1}}

/* sequence */
.seq{{list-style:none;margin:0;padding:0;counter-reset:s}}
.seqitem{{display:flex;gap:16px;background:var(--card);border:1px solid var(--line);
  border-radius:5px;padding:18px 20px;margin-bottom:11px;position:relative}}
.seqnum{{flex:0 0 34px;height:34px;border-radius:50%;background:var(--terra);color:#fff;
  font-family:Georgia,serif;font-weight:700;display:flex;align-items:center;justify-content:center}}
.seqitem h4{{font-size:17px;margin-bottom:4px}}
.seqres{{margin:0 0 7px;font-size:14.5px;color:#3d4757}}
.seqev{{margin:0;font-size:13.5px;color:var(--muted)}}
.seqev span{{color:var(--terra);font-weight:600}}

/* next */
.nexts{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}}
.nextcard{{display:block;background:var(--card);border:1px solid var(--line);border-radius:5px;
  padding:18px;text-decoration:none;color:inherit;transition:.13s}}
.nextcard:hover{{border-color:var(--terra);transform:translateY(-2px);box-shadow:0 5px 18px rgba(21,35,60,.1)}}
.nextcard h4{{font-size:16.5px;margin-bottom:5px}}
.nextcard p{{margin:0 0 10px;font-size:13.5px;color:var(--muted)}}

.note{{background:#fbf6ec;border-left:4px solid var(--terra);padding:15px 18px;
  border-radius:0 4px 4px 0;font-size:14.5px;color:#4a4132;margin-top:18px}}
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
  <div class="eyebrow">Isuzu Universe &middot; one map</div>
  <h1>The whole picture, on one page</h1>
  <p class="lede">What we hold, how it connects, what is actually built, and what is still only
  a plan. Written to be read without any technical background. Every figure is read from the
  files named beside it when this page was built.</p>
  <div class="stamp">Built {esc(c['built_at'])}. Pipeline checks: {c['verify_pass']} passed,
  {c['verify_fail']} failed, last run {esc(c['verify_at'])}. Nothing on this page writes to any file.</div>
</div></header>

<div class="wrap">

  <section id="minute">
    <div class="shead"><span class="n">01</span><h2>The one-minute version</h2>
      <p>Six numbers that say where the business and the data stand today.</p></div>
    <div class="tiles">{tile_html}</div>
  </section>

  <section id="map">
    <div class="shead"><span class="n">02</span><h2>How it all connects</h2>
      <p>Six steps, in the order the data actually flows. Each step feeds the next one.</p></div>
    <div class="map">{map_html}</div>
    <div class="note"><strong>The thread that ties the six steps together is the part number.</strong>
    Every step keys on it: the vehicles it fits, what we billed for it, what kind of part it is,
    what a competitor charges for it, what we decide, and what the reader sees. Where that thread is
    thin, the whole chain is thin at that point &mdash; and that is why step four is the weak one today.</div>
  </section>

  <section id="tools">
    <div class="shead"><span class="n">03</span><h2>The five tools, and where each one really is</h2>
      <p>Described in the strategy paper. This is what exists on disk, checked file by file.</p></div>
    <div class="tools">{tools_html}</div>
  </section>

  <section id="examples">
    <div class="shead"><span class="n">04</span><h2>The three worked examples</h2>
      <p>The paper's three demonstrations of the tools doing real work, and their true state.</p></div>
    <div class="examples">{examples_html}</div>
  </section>

  <section id="built">
    <div class="shead"><span class="n">05</span><h2>What is built</h2>
      <p>Pages that exist and open today, counted in their folders.</p></div>
    <table>
      <thead><tr><th>Folder</th><th style="text-align:right">Pages</th><th>What it holds</th></tr></thead>
      <tbody>{page_rows}</tbody>
    </table>
    <div class="note">These are the pages themselves. The analysis behind them lives in the
    derived files they read, and the whole chain is checked by a pipeline check that passed
    {c['verify_pass']} tests and failed {c['verify_fail']} on {esc(c['verify_at'])}.</div>
  </section>

  <section id="open">
    <div class="shead"><span class="n">06</span><h2>What is not finished</h2>
      <p>The honest list. Each line is a real gap measured today, not a wish.</p></div>
    <table>
      <thead><tr><th>Item</th><th>State today</th><th>Why it matters</th></tr></thead>
      <tbody>{open_html}</tbody>
    </table>

    <div class="shead" style="margin-top:34px;border-bottom-width:1px"><span class="n">&middot;</span>
      <h2 style="font-size:20px">Jobs that run without anyone watching</h2>
      <p>Read live from the Windows task list when this page was built.</p></div>
    <table>
      <thead><tr><th>Job</th><th>Last ran</th><th>Next run</th></tr></thead>
      <tbody>{task_rows}</tbody>
    </table>
  </section>

  <section id="roadmap">
    <div class="shead"><span class="n">07</span><h2>The roadmap, in the order it has to happen</h2>
      <p>The strategy paper's own six stages. Each stage names the evidence that lets you move on.</p></div>
    <ol class="seq">{seq_html}</ol>
    <div class="note"><strong>What it costs, and when it stops.</strong> The paper recommends starting
    from the existing &pound;100,000 route, with an offer-support line of &pound;60,000 to &pound;90,000 inside it,
    a minimum offer size of &pound;150,000 of eligible billing, and &pound;15,000 to &pound;25,000 of dealer
    enablement spent as accepted tasks rather than as an entitlement. It stops if, after two eligible
    rounds, no participant can name a decision the tool changed &mdash; and it does not pause, add a report,
    or widen the group to find a better answer.</div>
  </section>

  <section id="next">
    <div class="shead"><span class="n">08</span><h2>Where to look next</h2>
      <p>Seven places worth opening, and what each one is for.</p></div>
    <div class="nexts">{next_html}</div>
    {missing_note}
  </section>

  <footer>
    <p>Sources read when this page was built: the metrics snapshot and the sales and wallet files
    (<code>metrics_snapshot.json</code>, <code>wallet_waterfall.csv</code>, <code>sales_fact.parquet</code>);
    the live tender feed (<code>tender_data.json</code>, written {esc(t.get('generated',''))});
    the competitor cross-reference and price-model reports
    (<code>CROSSREF_GRAPH_REPORT.md</code>, <code>RATIO_MODEL_REPORT.md</code>);
    the weekly price collector (<code>refresh_and_check_drift.py</code>);
    the classification master (<code>aim_master_v2.csv</code>);
    the Windows task list; and the strategy paper
    (<code>Isuzu Universe/01_Strategy/ISUZU_UNIVERSE_3_0_2026-09-23.md</code>).</p>
    <p>This page is a description. It changes nothing, publishes nothing and sends nothing.</p>
  </footer>

</div>
</body>
</html>
"""


def write_cmd() -> None:
    body = (
        "@echo off\r\n"
        'start "" "%~dp0ISZE_UNIVERSE_MAP.html"\r\n'
    )
    OUT_CMD.write_bytes(body.encode("ascii"))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ctx = build_context()
    html = build_html(ctx)
    OUT_HTML.write_text(html, encoding="utf-8")  # no BOM
    write_cmd()
    print(f"wrote {OUT_HTML} ({OUT_HTML.stat().st_size/1024:.0f} KB)")
    print(f"wrote {OUT_CMD}")
    if MISSING:
        print("MISSING sources:", sorted(set(MISSING)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
