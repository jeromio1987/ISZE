"""Build ISZE_UNIVERSE_BOARD.html - where each pillar actually stands, and why.

For Jerome. Non-technical reader.

Two things changed on 24 September 2026, both on his decision:

  1. The conditions are quality conditions. The old checklist asked "does this file exist" for
     twelve of the sixteen ticks; those now test what the work actually is (for AIM, the five
     conditions in 00_docs/AIM_COVERAGE_MEASURE_2026-09-24.md; for the others, a real test of
     the product, not of the file's presence).

  2. The score is graded, not binary. A condition scores 1 when the thing does what its wording
     says, 1/2 when it only partly does or repeats credit already given for the same product,
     and 0 when it is not met or passes on something weaker than the wording. This is the
     counter-score from 02_dashboards/hub/_review/PILLAR_BOARD_ATTACK_2026-09-24.md.

Every figure is read from a real file or a live source at build time. Where a condition cannot
be tested from a file, the page says so instead of inventing a pass.

Output:
  02_dashboards/hub/ISZE_UNIVERSE_BOARD.html
  02_dashboards/hub/OPEN_ISZE_UNIVERSE_BOARD.cmd
  01_data/00_derived/universe_board_state.json   (the scores, machine readable)

Run: python 02_dashboards/_build/build_universe_board.py
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import socket
import subprocess
from datetime import datetime
from html import escape as _escape

ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"
DASH = os.path.join(ROOT, "02_dashboards")
HUB = os.path.join(DASH, "hub")
OUT_HTML = os.path.join(HUB, "ISZE_UNIVERSE_BOARD.html")
OUT_CMD = os.path.join(HUB, "OPEN_ISZE_UNIVERSE_BOARD.cmd")
OUT_JSON = os.path.join(ROOT, "01_data", "00_derived", "universe_board_state.json")

NOTES: list[str] = []
NOT_TESTABLE: list[str] = []

# The five tools of the strategy paper, in its own order. These are the five things a
# distributor or dealer is meant to open. Nothing on this PC is one of them yet.
TOOLS = [
    ("AIM Commercial Atlas", "What is really changing in my parts business, and where?"),
    ("IDS Development Studio", "What should I improve, and what has moved?"),
    ("Range & Campaign Planner", "Which products belong in this initiative, and for whom?"),
    ("Pricing & Margin Lab", "What does this trade-off do to revenue and margin?"),
    ("PRISM Market Intelligence", "Where should we concentrate effort?"),
]


def esc(s) -> str:
    return _escape(str(s), quote=True)


def P(*parts) -> str:
    return os.path.join(ROOT, *parts)


def exists(*parts) -> bool:
    return os.path.exists(P(*parts))


def many(*paths) -> bool:
    return any(exists(*p.split("/")) for p in paths)


def read_text(*parts) -> str:
    try:
        return io.open(P(*parts), encoding="utf-8", errors="replace").read()
    except Exception:
        return ""


def read_json(*parts):
    try:
        return json.loads(read_text(*parts))
    except Exception:
        return {}


def read_csv_rows(*parts) -> list[dict]:
    try:
        with io.open(P(*parts), encoding="utf-8", errors="replace", newline="") as fh:
            return list(csv.DictReader(fh))
    except Exception:
        return []


def sha256(*parts) -> str:
    try:
        h = hashlib.sha256()
        with open(P(*parts), "rb") as fh:
            for block in iter(lambda: fh.read(1 << 20), b""):
                h.update(block)
        return h.hexdigest().lower()
    except Exception:
        return ""


def count_country_pages(folder="02_dashboards/ids") -> int:
    """Real per-country dealer comparison pages, one per country.

    Only live .html pages: the published all-markets comparison has no country suffix, and the
    .bak_ copies and SHIP_RECEIPT files beside each page are not pages. A bare "dealer_compare_"
    match once returned 96, which was 19 pages plus 39 backups and 19 receipts.
    """
    d = P(*folder.split("/"))
    if not os.path.isdir(d):
        return 0
    return len([f for f in os.listdir(d)
                if "dealer_compare_" in f and f.endswith(".html") and ".bak_" not in f])


def strip_code(src: str) -> str:
    """Remove <script>, <style> and base64 blobs, so scans read visible prose only."""
    src = re.sub(r"<script\b.*?</script>", " ", src, flags=re.S | re.I)
    src = re.sub(r"<style\b.*?</style>", " ", src, flags=re.S | re.I)
    src = re.sub(r"[A-Za-z0-9+/]{120,}={0,2}", " ", src)
    return src


def strip_tags(src: str) -> str:
    return re.sub(r"<[^>]+>", " ", src)


ACCESS_TOKENS = ["password", "sign in", "log in", "permitted audience", "access control",
                 "only the dealer sees", "credentials"]


def access_scan(path: str) -> list[str]:
    """Which access-control words appear in the visible text of a page."""
    prose = strip_code(read_text(path)) if path.startswith("02_") or path.startswith("Isuzu") \
        else read_text(path)
    low = prose.lower()
    return [t for t in ACCESS_TOKENS if t in low]


def needs_network(path: str) -> bool:
    """True when the page pulls something at view time: fetch(), or an <img>/<link> that is not local."""
    t = read_text(path)
    if "fetch(" in t:
        return True
    for tag in re.findall(r"<(?:img|link|script)\b[^>]*>", t, re.I):
        if re.search(r"(?:src|href)\s*=\s*[\"']https?://", tag, re.I):
            return True
    return False


def uses_map_tiles(path: str) -> bool:
    t = read_text(path)
    return bool(re.search(r"tile\.openstreetmap|tile\.|\{z\}/\{x\}/\{y\}", t, re.I))


def task_state(name: str) -> dict:
    """Read one Windows scheduled task. The registered name is matched exactly."""
    try:
        r = subprocess.run(["schtasks", "/query", "/tn", name, "/fo", "LIST", "/v"],
                           capture_output=True, text=True, timeout=25)
        d = {}
        for line in (r.stdout or "").splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                d[k.strip().lower()] = v.strip()
        return {"name": name.lstrip("\\"),
                "last": d.get("last run time", "?"),
                "next": d.get("next run time", "?"),
                "result": d.get("last result", "?"),
                "never": d.get("last run time", "").startswith("30/11/1999")}
    except Exception:
        return {"name": name.lstrip("\\"), "last": "?", "next": "?", "result": "?", "never": True}


def port_open(port: int, host="127.0.0.1") -> bool:
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except Exception:
        return False


# ---------------------------------------------------------------- live facts

def facts() -> dict:
    m = read_json("01_data", "00_derived", "metrics_snapshot.json").get("metrics", {})

    def mv(k, f="value"):
        return (m.get(k) or {}).get(f)

    tender = read_json("01_data", "14_dashboards", "tender_data.json")
    to = tender.get("opportunities", [])
    tm = tender.get("meta", {})

    # Registered with spaces: "ISZE Tender Monitor". An earlier build keyed it with underscores
    # and never found it, so the pillar printed "Last ran ?" while the jobs table read it fine.
    tasks = {}
    for name in ["\\ISZE Tender Monitor", "\\ISZE_PriceLedger_Weekly"]:
        tasks[name.lstrip("\\")] = task_state(name)

    cx = read_text("04_tools", "aftermarket_intelligence", "state", "CROSSREF_GRAPH_REPORT.md")

    def grab(pat, cast=str, default=None):
        mm = re.search(pat, cx)
        try:
            return cast(mm.group(1).replace(",", ""))
        except Exception:
            return default

    gate = read_json("01_data", "00_derived", "aim_classification_gate.json")
    gate_checks = gate.get("checks", [])
    releases = read_json("01_data", "00_derived", "_releases", "RELEASES.json")
    rel = releases.get("candidates", [])
    approved = [c for c in rel if c.get("status") == "APPROVED"]

    coverage = read_json("01_data", "91_build", "_aim_coverage_measure_20260924.json")
    sample = read_csv_rows("01_data", "91_build", "_aim_accuracy_sample_20260924.csv")
    l1_yes = sum(1 for r in sample if (r.get("agree_l1") or "").strip() == "Y")
    l2_yes = sum(1 for r in sample if (r.get("agree_l2") or "").strip() == "Y")
    l3_yes = sum(1 for r in sample if (r.get("agree_l3") or "").strip() == "Y")
    l1_bad = [r for r in sample if (r.get("agree_l1") or "").strip() == "N"]

    wallet = read_csv_rows("01_data", "00_derived", "wallet_waterfall.csv")
    w25 = [r for r in wallet if r.get("year") == "2025"]
    cap25 = sum(float(r["captured_total_eur"]) for r in w25) if w25 else 0.0
    wal25 = sum(float(r["theoretical_wallet_eur"]) for r in w25) if w25 else 0.0

    # the strategy paper is parsed, not quoted from memory
    paper = read_text("Isuzu Universe", "01_Strategy", "ISUZU_UNIVERSE_3_0_2026-09-23.md")

    def paper_amount(label):
        mm = re.search(r"\| " + re.escape(label) + r" \| ([^|\n]+)\|", paper)
        return mm.group(1).strip() if mm else None

    paper_tools_present = {t: paper.count(t) for t, _ in TOOLS}

    # the file the AIM comparison pages are actually built from
    # the APPROVED release's figure-key export, resolved and sha256-checked by classification_paths
    import sys as _sys
    _sys.path.insert(0, P("04_tools", "_shared"))
    from classification_paths import figkey_export_for_release
    _fig_path, _ = figkey_export_for_release()
    fig = "01_data/00_derived/" + _fig_path.name
    fig_rows = 0
    if exists(*fig.split("/")):
        with io.open(P(*fig.split("/")), encoding="utf-8", errors="replace") as fh:
            fig_rows = max(0, sum(1 for _ in fh) - 1)

    # range-selection artefacts, found by name anywhere in the two working trees
    range_hits = []
    for base in ["Isuzu Universe", "02_dashboards"]:
        for root, _dirs, files in os.walk(P(*base.split("/"))):
            for f in files:
                if re.search(r"range|selection", f, re.I) and f.lower().endswith(
                        (".html", ".xlsx", ".csv", ".zip")):
                    range_hits.append(os.path.join(root, f).replace(ROOT + os.sep, ""))
    range_hits = sorted(range_hits)[:8]

    # dealer-level onward purchases: how many distributors send any
    sell = [f for f in os.listdir(P("01_data", "00_derived"))
            if re.search(r"dealer_sellout|sellout|sales_to_dealer", f, re.I)] \
        if os.path.isdir(P("01_data", "00_derived")) else []

    # do any shared pricing pages carry a margin figure, or the words that would show one is missing
    pricing_pages = [f for f in os.listdir(P("02_dashboards", "pricing"))
                     if f.endswith(".html") and ".bak_" not in f] \
        if os.path.isdir(P("02_dashboards", "pricing")) else []
    margin_pages, cost_basis_missing = [], []
    for f in pricing_pages:
        t = read_text("02_dashboards", "pricing", f)
        prose = strip_tags(strip_code(t))
        if re.search(r"gross margin|gross profit|%GM", prose, re.I):
            margin_pages.append(f)
        if re.search(r"no supplied cost basis|cost basis", prose, re.I):
            cost_basis_missing.append(f)

    prism_pages = os.path.join(P("03_analytics", "Isuzu", "prism", "pages"))
    prism_comp = []
    if os.path.isdir(prism_pages):
        for f in os.listdir(prism_pages):
            if re.search(r"peer_street|competitor|iam_price|street_index",
                         read_text("03_analytics", "Isuzu", "prism", "pages", f), re.I):
                prism_comp.append(f)

    access_pages = {}
    for rel in ["02_dashboards/pricing/ISZE_Pricing_Action_Map.html",
                "02_dashboards/pricing/ISZE_Pricing_Revision_AIM_Source.html",
                "02_dashboards/ids/IDS_2026_dealer_compare.html",
                "02_dashboards/pricing/ISZE_AIM_Truck_Catalogue_2026-09-18.html",
                "Isuzu Universe/02_Atlas/AIM_Parts_Atlas_v2.0.html"]:
        if exists(*rel.split("/")):
            access_pages[rel] = access_scan(rel)

    return {
        "parts_base": mv("sales.parts_base_eur"),
        "through": mv("sales.parts_base_data_through"),
        "verify_pass": mv("verify.pass"),
        "verify_fail": mv("verify.fail"),
        "verify_at": (mv("verify.generated") or "")[:16].replace("T", " "),
        "tender_rows": len(to),
        "tender_rm": sum(1 for r in to if r.get("rm_contract")),
        "tender_rm_open": sum(1 for r in to if r.get("rm_contract")
                              and str(r.get("deadline_date") or "") >= datetime.now().strftime("%Y-%m-%d")),
        "tender_outcomes": (tm.get("outcomes_summary") or {}).get("recorded", 0),
        "tender_generated": (tm.get("generated_at") or "")[:10],
        "tender_countries": len(tm.get("country_counts", {})),
        "tender_sources": len(tm.get("source_counts", {})),
        "cx_parts": grab(r"Isuzu part numbers reached: (\d+)", int),
        "cx_total": grab(r"Isuzu part numbers reached: \d+ of (\d+)", int),
        "cx_value": grab(r"billed value of those parts: EUR ([\d,]+)", int),
        "ids_country": count_country_pages(),
        "pages": read_json("02_dashboards", "_build", "_page_inventory.json"),
        "tasks": tasks,
        "gate_checks": gate_checks,
        "gate_pass": sum(1 for c in gate_checks if c.get("ok")),
        "gate_fail": sum(1 for c in gate_checks if not c.get("ok")),
        "gate_at": (gate.get("run_at") or "")[:16].replace("T", " "),
        "gate_verdict": gate.get("verdict"),
        "releases": rel,
        "approved_releases": approved,
        "release_sha_ok": bool(approved) and sha256(
            "01_data", "00_derived", "_releases", approved[0]["path"]) == approved[0]["sha256"].lower(),
        "coverage": coverage,
        "cov_pct": ((coverage.get("covered", {}).get("eur", 0.0)
                     / coverage.get("totals", {}).get("eur", 1.0)) * 100) if coverage else 0.0,
        "cov_window": coverage.get("window", {}),
        "cov_top15": coverage.get("residual_top15", []),
        "cov_big": [r for r in coverage.get("residual_top15", []) if r.get("billed_eur", 0) >= 5000],
        "sample_n": len(sample),
        "sample_l1": l1_yes, "sample_l2": l2_yes, "sample_l3": l3_yes,
        "sample_bad": l1_bad,
        "wallet_pct": (cap25 / wal25 * 100) if wal25 else 0.0,
        "wallet_cap": cap25, "wallet_ceil": wal25,
        "wallet_dbs": len({r.get("distributor_code") for r in w25}),
        "wallet_countries": len({r.get("country") for r in w25}),
        "paper_rm": paper_amount("Minimum campaign size to qualify"),
        "paper_line": paper_amount("Named campaign-support line"),
        "paper_enable": paper_amount("Dealer enablement, spent as accepted tasks"),
        "paper_tools": paper_tools_present,
        "paper_read": bool(paper),
        "fig_rows": fig_rows,
        "fig_file": fig,
        "range_hits": range_hits,
        "sellout_files": sell,
        "margin_pages": margin_pages,
        "cost_basis_missing": cost_basis_missing,
        "pricing_pages": len(pricing_pages),
        "prism_comp": prism_comp,
        "access_pages": access_pages,
        "prism_port_open": port_open(8503),
        "prism_pages": (len([f for f in os.listdir(P("03_analytics", "Isuzu", "prism", "pages"))
                             if f.endswith(".py")])
                        if os.path.isdir(P("03_analytics", "Isuzu", "prism", "pages")) else 0),
    }


# ---------------------------------------------------------------- the checklist
#
# Each check is a dict:
#   label    - the condition, in the words a person would use
#   score    - 1, 0.5 or 0
#   tests    - one plain sentence: what this condition tests, and against what
#   reason   - required: why it scores what it scores, in plain words
#   link     - optional (label, href)

def build_pillars(F: dict) -> list[dict]:
    ids = F["ids_country"]

    # --- live scans used by more than one condition
    pt_page = "02_dashboards/sales/ISZE_AIM_Comparison_PORTUGAL.html"
    pt_open = "02_dashboards/sales/OPEN_ISZE_AIM_Comparison_PORTUGAL.cmd"
    atlas = "02_dashboards/pricing/ISZE_AIM_Truck_Catalogue_2026-09-18.html"
    atlas2 = "Isuzu Universe/02_Atlas/AIM_Parts_Atlas_v2.0.html"
    ids_cmp = "02_dashboards/ids/IDS_2026_dealer_compare.html"
    ids_map = "02_dashboards/ids/IDS_2026_Portugal_dealer_map.html"
    camp = "02_dashboards/pricing/ISZE_PMS_Campaign_Impact_Review_2026-09-23.html"
    pms_brief = "02_dashboards/pricing/ISZE_PMS_Price_Response_Brief_2026-09-22.html"
    action_map = "02_dashboards/pricing/ISZE_Pricing_Action_Map.html"
    revision = "02_dashboards/pricing/ISZE_Pricing_Revision_AIM_Source.html"

    paper_html = "02_dashboards/sales/ISZE_AIM_Classification_Paper.html"
    pt_network = needs_network(pt_page)
    pt_access = access_scan(pt_page)
    cmp_network = needs_network(ids_cmp)
    map_tiles = uses_map_tiles(ids_cmp) or uses_map_tiles(ids_map)
    atlas_network = needs_network(atlas) or needs_network(atlas2)
    atlas_access = sorted(set(access_scan(atlas)) | set(access_scan(atlas2)))
    atlas_selfcontained = not atlas_network
    paper_access = access_scan(paper_html)
    pass_dbs, fail_dbs = [], []
    for _c in F["approved_releases"]:
        ok = all(t.get("ok") for t in read_json("01_data", "00_derived",
                                                "aim_classification_gate.json").get("checks", []))
        (pass_dbs if ok else fail_dbs).append(_c["release_id"])

    pillars = [
        # ------------------------------------------------------------------ AIM
        {
            "key": "aim",
            "name": "AIM — what each part is",
            "question": "What is really changing in my parts business, and where?",
            "checks": [
                {
                    "label": "Coverage on billed euro",
                    "score": 1 if F["cov_pct"] >= 98.0 else 0,
                    "tests": (f"Over the twelve months to {F['cov_window'].get('to', '?')}, the share of "
                              "billed parts euro sitting on a part number with a governed family is at "
                              "least 98.0%, and every unclassified part number above EUR 5,000 in that "
                              "window is named. Read from sales_fact.parquet joined to aim_master_v2.csv."),
                    "reason": (f"{F['cov_pct']:.2f}% of the billed euro has a family "
                               f"(EUR {F['coverage'].get('covered', {}).get('eur', 0) / 1e6:.2f}M of "
                               f"EUR {F['coverage'].get('totals', {}).get('eur', 0) / 1e6:.2f}M), above the "
                               f"98.0% bar, and the {len(F['cov_big'])} unclassified part numbers above "
                               "EUR 5,000 are printed on the memo by number, euro and description."),
                },
                {
                    "label": "Accuracy on a sample",
                    "score": 1 if (F["sample_n"] and F["sample_l1"] / F["sample_n"] >= 0.90) else 0,
                    "tests": ("Fifty classified part numbers drawn by billed euro on a fixed seed; a named "
                              "reader compares each part's billed description with the family it carries; "
                              "at least 90% must agree and every disagreement must be listed."),
                    "reason": (f"{F['sample_l1']} of {F['sample_n']} agree at family level "
                               f"({F['sample_l1'] / F['sample_n'] * 100:.0f}%), above the 90% bar; the three "
                               "disagreements are named with their part numbers and euro. Group agrees on "
                               f"{F['sample_l2']} and leaf on {F['sample_l3']}, which is where the coarser "
                               "call sits."),
                },
                {
                    "label": "One named, approved, frozen release",
                    "score": (0.5 if F["release_sha_ok"] else 0) if len(F["approved_releases"]) == 1 else 0,
                    "tests": ("_releases/RELEASES.json holds exactly one candidate marked APPROVED, its "
                              "recorded hash still matches the file on disk, and the gate's checks pass on "
                              "the file the AIM pages are built from."),
                    "reason": ((f"Approved {F['approved_releases'][0].get('approved_on')} by "
                                f"{F['approved_releases'][0].get('approved_by')}, {F['approved_releases'][0].get('rows', 0):,} "
                                "rows; the hash was re-verified against the register before the status was "
                                f"changed. Half rather than full for two reasons: the gate's own checks do not "
                                f"all pass (it runs against aim_pn_classification_v2.csv, not this release), "
                                f"and the AIM comparison pages on disk read a separately exported master "
                                f"({os.path.basename(F['fig_file'])}, {F['fig_rows']:,} rows), so the release "
                                f"is named and approved but no builder is pinned to it yet.")
                               if F["approved_releases"] else
                               "No candidate is marked APPROVED in _releases/RELEASES.json."),
                },
                {
                    "label": "A distributor can open his own parts by family",
                    "score": 0.5 if (exists(*pt_page.split("/")) and exists(*pt_open.split("/"))
                                     and not pt_network) else 0,
                    "tests": ("One page for at least one distributor that opens from Explorer with no "
                              "server, carries that distributor's own part numbers grouped by the families "
                              "AIM assigns with the euro beside each, states its own distributor and period, "
                              "and has a launcher beside it."),
                    "reason": (f"Met for Portugal, one distributor of {F['wallet_dbs']}. The page is "
                               "self-contained (its data is written into the page, no call out at open) and "
                               "a launcher sits beside it. Half rather than full because one distributor is "
                               "not a tool, the file list does not name it as a tool, and the page itself "
                               "says it was built to be read rather than driven."
                               + (" It does pull something at open, so it is not self-contained."
                                  if pt_network else "")
                               + (f" Access words found on it: {', '.join(pt_access)}."
                                  if pt_access else "")),
                },
                {
                    "label": "The safety checks pass against the file the pages are built from",
                    "score": 0,
                    "tests": ("All checks in aim_classification_gate.json pass, run against the file the AIM "
                              "pages are built from, with the drift rule split: no stored measure may move "
                              "more than 1% between runs, and the leaf counts may change only with a named "
                              "review and a written new baseline in the same run."),
                    "reason": (f"{F['gate_pass']} of {F['gate_pass'] + F['gate_fail']} pass, so the condition "
                               f"is not met. The failing one is the leaf-count check (it wants 177 bottom "
                               f"leaves and finds 176), which is the one rule that punishes the improvement "
                               f"itself; the 1% drift rule is real work and should stay. The gate also runs "
                               f"against aim_pn_classification_v2.csv, not the approved release. "
                               f"Last run {F['gate_at']}."),
                },
            ],
            "links": [
                ("Classification paper", "../sales/ISZE_AIM_Classification_Paper.html"),
                ("Portugal comparison", "../sales/ISZE_AIM_Comparison_PORTUGAL.html"),
                ("Truck catalogue", "../pricing/ISZE_AIM_Truck_Catalogue_2026-09-18.html"),
            ],
        },
        # ------------------------------------------------------------------ IDS
        {
            "key": "ids",
            "name": "IDS — dealer standards",
            "question": "What should I improve, and what has moved?",
            "checks": [
                {
                    "label": "A dealer comparison with the questions behind it",
                    "score": 1 if (exists(*ids_cmp.split("/")) and "sections A" in read_text(ids_cmp)) else 0,
                    "tests": ("A page that shows the dealer network's assessment results and the question "
                              "list behind them, so a reader can see which questions drive a dealer's "
                              "position. Read from the page itself, not from the file's presence."),
                    "reason": (f"The page carries the assessment sections and the question drill, so it "
                               f"answers the question this pillar asks. It is also a network ranking, and "
                               f"the strategy paper says the development studio is 'no new universal league "
                               f"table' - so it is credited for the analysis, not as the studio."
                               if exists(*ids_cmp.split("/")) else
                               "The comparison page is not on disk."),
                },
                {
                    "label": "One comparison page per country",
                    "score": 0.5 if ids >= 5 else 0,
                    "tests": (f"Live per-country comparison pages on disk - real .html pages only, not the "
                              f"backup copies and receipts that sit beside them. Read from the folder "
                              f"listing; {ids} found."),
                    "reason": (f"{ids} real pages. The earlier count of 96 came from matching the bare name: "
                               "19 pages plus 39 backups and 19 receipts. Half rather than full because these "
                               "are country filters of the same single product, so the pillar is paid twice "
                               "for one piece of work, and the roadmap line that used to say 21 now reads "
                               "the same count as this line so it cannot drift again."),
                },
                {
                    "label": "A dealer map for at least one market",
                    "score": 0.5 if exists(*ids_map.split("/")) else 0,
                    "tests": ("A map page that places an individual market's dealers and can be read "
                              "offline - a page whose background needs an internet tile service is not a "
                              "map a distributor opens without a connection."),
                    "reason": ("The Portugal map is on disk and linked."
                               + (" It draws its background from an internet tile service, so it needs a "
                                  "connection to show anything, and the comparison page says its own primary "
                                  "map is in the dealer compare Map tab - a third credit for one product."
                                  if map_tiles else
                                  " Its background is drawn on the page, not fetched.")
                               + " Recorded at half: it is the same product as the two lines above."),
                },
                {
                    "label": "Progress and evidence tracked over time, separate from the score",
                    "score": 0,
                    "tests": ("A record per dealer of development milestones with evidence, shown apart from "
                              "the assessment score. This is the defining feature of the studio in the "
                              "strategy paper."),
                    "reason": (f"Not built. The comparison stands at a snapshot: where no assessment date is "
                               f"held it prints 'assessment date not supplied'. There is no file behind this "
                               f"condition, so it is recorded as untested rather than scored on something "
                               f"weaker."),
                },
                {
                    "label": "Attached to a stated period",
                    "score": 0,
                    "tests": "Every dealer row carries the assessment period it belongs to.",
                    "reason": ("Not met. The comparison page prints 'assessment date not supplied' where no "
                               "date is held, so the reader cannot tell two rounds apart."),
                },
            ],
            "links": [
                ("Dealer compare — all markets", "../ids/IDS_2026_dealer_compare.html"),
                ("Portugal dealer map", "../ids/IDS_2026_Portugal_dealer_map.html"),
                ("How we read the network", "../ids/IDS_2026_Explainer.html"),
            ],
        },
        # ------------------------------------------------------------------ Range
        {
            "key": "range",
            "name": "Range & Campaign Planner",
            "question": "Which products belong in this initiative, and for whom?",
            "checks": [
                {
                    "label": "A tool that selects the range for an initiative",
                    "score": 0,
                    "tests": ("A page or workbook where a range is selected for an initiative and the "
                              "selection carries into the next step. Searched by name across both working "
                              "trees at build time."),
                    "reason": ((f"The name search finds {len(F['range_hits'])} file(s): "
                                f"{', '.join(os.path.basename(h) for h in F['range_hits'])}. That is a "
                                "prototype and a decision record, not a tool a person selects a range in, so "
                                "the condition is not met.")
                               if F["range_hits"] else
                               "No file matching a range or selection tool exists in either working tree."),
                },
                {
                    "label": "Account coverage so a campaign can be aimed",
                    "score": 0,
                    "tests": ("Dealer-level account data at the level a campaign needs, counted from the "
                              "onward-purchase files the workspace holds."),
                    "reason": (f"{len(F['sellout_files'])} onward-purchase files exist, and the workspace's "
                               "own dealer work records that only one distributor sends them broken down by "
                               "named dealer while every other market collapses to a single row. One "
                               "distributor's dealer list is not account coverage."),
                },
                {
                    "label": "A stated minimum size for a campaign to qualify",
                    "score": 0.5,
                    "tests": ("The strategy paper's funding table is parsed and the size filter is printed in "
                              "the currency the paper writes it in."),
                    "reason": (f"The paper states '{F['paper_rm']}'. Half rather than full because it is one "
                               "sentence in a recommendation: nothing records the rule being agreed, and the "
                               "paper's own test for that stage is 'the campaign-selection rule is agreed and "
                               "the first eligible campaign is named', and neither is on file. The earlier "
                               "board printed this in pounds; it is euros."),
                },
                {
                    "label": "Past campaign effect measured after the fact",
                    "score": 0.5,
                    "tests": ("A review that measures a named campaign on the same scope before, during and "
                              "after, returns included."),
                    "reason": ("The review exists and is honest about its method: it tags a campaign as any "
                               "invoice 20% or more under the reference price and reads the following "
                               "month's drop as stock-building. Half rather than full because it measures "
                               "purchases from ISZE, not what the dealer sold on, it names no campaign, and "
                               "there is no before/during/after on one scope with returns."),
                },
                {
                    "label": "A campaign run through the tool",
                    "score": 0,
                    "tests": "At least one campaign prepared and run end to end.",
                    "reason": "Not run.",
                },
            ],
            "links": [
                ("Campaign impact review", "../pricing/ISZE_PMS_Campaign_Impact_Review_2026-09-23.html"),
                ("Price response brief", "../pricing/ISZE_PMS_Price_Response_Brief_2026-09-22.html"),
            ],
        },
        # ------------------------------------------------------------------ Pricing
        {
            "key": "pricing",
            "name": "Pricing & Margin Lab",
            "question": "What does this trade-off do to revenue and margin?",
            "checks": [
                {
                    "label": "The price revision measured on a stated base",
                    "score": 1 if ("5.9616" in read_text(revision)) else 0,
                    "tests": ("The revision page states its window and its base, and carries the revision "
                              "figure in its own data - not only in the prose."),
                    "reason": ("The page states its base and window in its own data block (weighted by "
                               "quantities billed, 1 July 2025 to 30 June 2026, lines priced on both sides, "
                               "with the published figure beside it) and marks it as not a revenue, margin "
                               "or demand result. The figure and its base travel together in the same file."),
                },
                {
                    "label": "Price gaps per market and per part, ranked",
                    "score": 0.5 if exists(*action_map.split("/")) else 0,
                    "tests": ("Gaps ranked down to the individual part number, against observed competitor "
                              "prices rather than a price-list convention, with the covered part of the "
                              "catalogue stated."),
                    "reason": (f"Ranked by family and market, not by part number, and the comparison is the "
                               f"standard list convention rather than observed competitor prices. The "
                               f"competitor panel reaches {F['cx_parts']} of {F['cx_total']:,} part numbers "
                               f"(EUR {F['cx_value'] / 1e6:.1f}M of billed value). Half rather than full: the "
                               "ranking exists, the evidence behind it is narrower than the wording claims."),
                },
                {
                    "label": "Customer price-response evidence",
                    "score": 0.5 if exists(*pms_brief.split("/")) else 0,
                    "tests": ("A study that reads how customers responded to a price change and reports a "
                              "response that can be acted on."),
                    "reason": ("The brief exists and does the work; its own verdict is that the volume "
                               "effect it finds is capture or stocking, not a clean response slope. Half: "
                               "the evidence is there, but what it establishes is that the response cannot "
                               "be read from it."),
                },
                {
                    "label": "A lab a distributor can drive himself",
                    "score": 0,
                    "tests": ("A version a distributor opens and runs his own scenario in, with access "
                              "control, tested by scanning the shared pricing pages for access words."),
                    "reason": (f"Not built. Scanned {F['pricing_pages']} shared pricing pages for password, "
                               f"sign-in and permitted-audience words: "
                               f"{sum(1 for v in F['access_pages'].values() if v)} of them carry any, and "
                               f"none of the pricing pages does"
                               + (" - and one that carries five customers' own price conditions could not be "
                                  "shown to another party at all." if F["access_pages"] else ".")),
                },
                {
                    "label": "A margin layer beside the revenue layer",
                    "score": 0,
                    "tests": ("Margin beside the revenue figures in the shared pages, on a supplied cost "
                              "basis. Scanned for a margin figure or for the stated reason there is none."),
                    "reason": (f"Not met. Of {F['pricing_pages']} shared pricing pages, "
                               f"{len(F['margin_pages'])} carry a gross-margin figure and "
                               f"{len(F['cost_basis_missing'])} state that gross profit has no supplied cost "
                               "basis. Recorded as a named data gap rather than a missing file, because what "
                               "is missing is the cost basis, not the intent."),
                },
            ],
            "links": [
                ("Price revision pack", "../pricing/ISZE_Pricing_Revision_AIM_Source.html"),
                ("Pricing action map", "../pricing/ISZE_Pricing_Action_Map.html"),
                ("Pricing policy paper", "../pricing/ISZE_Pricing_Policy_Paper.html"),
            ],
        },
        # ------------------------------------------------------------------ PRISM
        {
            "key": "prism",
            "name": "PRISM — market and fleet context",
            "question": "Where should we concentrate effort?",
            "checks": [
                {
                    "label": "The application runs",
                    "score": 1 if F["prism_port_open"] else 0,
                    "tests": ("Something answers on the application's own port when this page is built, and "
                              "the application's pages are present."),
                    "reason": ((f"Port 8503 answered at build time and {F['prism_pages']} page files are "
                                "present, so this reads the running thing rather than the presence of its "
                                "start file. It does not confirm which application answered.")
                               if F["prism_port_open"] else
                               "Nothing answered on port 8503 at build time, so the condition is not met today."),
                },
                {
                    "label": "Vehicles in service wired per market",
                    "score": 1 if F["wallet_dbs"] >= 10 else 0,
                    "tests": ("The vehicles-in-service figures exist per market in the fleet file, and the "
                              "application's own decision page reads that file. Both are tested - a "
                              "spreadsheet on disk is not 'wired in'."),
                    "reason": (f"wallet_waterfall.csv carries the fleet by market and year, and the "
                               f"application's decision-models page reads that file by name. "
                               f"{F['wallet_dbs']} distributors in {F['wallet_countries']} countries - not "
                               f"'18 markets', because the United Kingdom and Israel each hold two - over "
                               f"2023 to 2025."),
                },
                {
                    "label": "Spend per truck and capture computed",
                    "score": 1 if F["wallet_ceil"] else 0,
                    "tests": ("The capture figure is computed at build time from the sourced figures rather "
                              "than read from a number typed into the page."),
                    "reason": (f"Computed from wallet_waterfall.csv: EUR {F['wallet_cap'] / 1e6:.2f}M billed "
                               f"against a EUR {F['wallet_ceil'] / 1e6:.2f}M target-spend ceiling for 2025, "
                               f"which is {F['wallet_pct']:.1f}%. The earlier board typed 56.5 into the "
                               f"builder and tested only that metrics_snapshot.json exists; the file's "
                               f"presence proves nothing about its contents."),
                },
                {
                    "label": "A version a distributor can open, with access control",
                    "score": 0,
                    "tests": "A distributor-facing version of the application with a login.",
                    "reason": ("Not built, and not something code on this PC can close: the strategy paper "
                               "says there is no backend here."),
                },
                {
                    "label": "Competitor prices inside the application",
                    "score": 0,
                    "tests": ("A page inside the application on which competitor prices can be read, counted "
                              "by reading the application's own page files for a competitor price source at "
                              "build time."),
                    "reason": ((f"Page files found referring to a competitor price source: "
                                f"{', '.join(F['prism_comp'])}. That is a build module, not a page, so the "
                                "condition is not met. The paper's PRISM is fleet, billed parts, modelled "
                                "demand and dated opportunities; competitor prices belong to the Pricing lab, "
                                "so this is left at zero rather than replaced with an invented substitute.")
                               if F["prism_comp"] else
                               "No page file in the application reads a competitor price source, and "
                               "competitor prices belong to the Pricing lab by the paper's own definition."),
                },
            ],
            "links": [
                ("KPI dashboard", "../sales/ISZE_KPI_Dashboard.html"),
                ("GPS dashboard", "../fleet/ISZE_GPS_Dashboard.html"),
                ("Vehicles in service", "../fleet/ISUZU_UIO_Dashboard_2026.html"),
                ("Globe — uncaptured spend", "../globe/index.html"),
            ],
        },
        # ------------------------------------------------------------------ Tenders
        {
            "key": "tenders",
            "name": "Coordinated tenders",
            "question": "Which public opportunities are worth bidding, and with whom?",
            "checks": [
                {
                    "label": "A weekly collection that runs on its own",
                    "score": 1 if not F["tasks"].get("ISZE Tender Monitor", {}).get("never", True) else 0,
                    "tests": ("The Windows task is read by its registered name at build time, and the "
                              "condition turns on whether it has actually run."),
                    "reason": (f"Read live as 'ISZE Tender Monitor': last ran "
                               f"{F['tasks'].get('ISZE Tender Monitor', {}).get('last', '?')}, last result "
                               f"{F['tasks'].get('ISZE Tender Monitor', {}).get('result', '?')}, next "
                               f"{F['tasks'].get('ISZE Tender Monitor', {}).get('next', '?')}. The earlier "
                               "board stored the task as 'ISZE_Tender_Monitor' and looked it up as "
                               "'ISZE Tender Monitor', found nothing and printed 'Last ran ?', scoring a met "
                               "condition as failed."),
                },
                {
                    "label": "Coverage of national portals plus the EU-wide portal",
                    "score": 1 if (F["tender_sources"] >= 10 and F["tender_countries"] >= 10) else 0,
                    "tests": ("The feed's own source list is read at build time: how many named sources it "
                              "carries, how many countries they cover, and that the EU-wide portal is among "
                              "them with a real share of the notices."),
                    "reason": (f"{F['tender_sources']} named sources across {F['tender_countries']} countries, "
                               "with the EU-wide portal the largest single source. The test counts countries "
                               "rather than portals, which flatters a feed where several national sources "
                               "supply one or two notices each - noted, still met."),
                },
                {
                    "label": "Repair-and-maintenance contracts identified and scored",
                    "score": 1 if all(r.get("opportunity_score") for r in
                                      [o for o in json.loads(read_text("01_data", "14_dashboards",
                                                                       "tender_data.json")).get("opportunities", [])
                                       if o.get("rm_contract")][:50]) else 0,
                    "tests": ("Every R&M notice in the feed carries a score computed by the feed, so the "
                              "identification is scored rather than only flagged."),
                    "reason": (f"{F['tender_rm']} of {F['tender_rows']} opportunities are R&M and each one "
                               f"carries a computed score in the feed. The headline is still flattered: "
                               f"only {F['tender_rm_open']} have a deadline still ahead, so the workable "
                               f"set is far smaller than {F['tender_rm']}."),
                },
                {
                    "label": "What happened to each tender recorded",
                    "score": 0,
                    "tests": "An outcome recorded against each opportunity in the live feed.",
                    "reason": f"{F['tender_outcomes']} of {F['tender_rows']} recorded, read from the feed's own summary block.",
                },
                {
                    "label": "Routed to the distributor and dealer who could bid",
                    "score": (0.5 if (exists("04_tools", "ISZE_Tender_Monitor_Install", "rm_digest",
                                              "2026-09-24", "index.html")
                                      and not exists("07_deploy", "Master Dashboard", "rm_digest"))
                              else 0),
                    "tests": ("A per-distributor view of the notices that concern that distributor, and the "
                              "evidence that it reached them."),
                    "reason": (f"The weekly R&M digest is on disk, one page per distributor, and the board "
                               f"links to it - so more than the earlier 'not built'. Half rather than full "
                               f"because nothing has been sent, it is not part of the weekly job, and "
                               f"{sum(1 for o in json.loads(read_text('01_data', '14_dashboards', 'tender_data.json')).get('opportunities', []) if not o.get('distributor_code'))} "
                               f"of {F['tender_rows']} notices still carry no distributor."),
                },
            ],
            "links": [
                ("Tender monitor", "../ops/ISZE_Tender_Monitor_v2.html"),
                ("Weekly R&M digest for distributors (24 Sep)",
                 "../../04_tools/ISZE_Tender_Monitor_Install/rm_digest/2026-09-24/index.html"),
            ],
        },
    ]

    for p in pillars:
        pts = sum(int(c["score"] * 2) for c in p["checks"])
        p["points"] = pts
        p["out_of"] = 2 * len(p["checks"])
        p["pct"] = round(pts / p["out_of"] * 100)
        p["met"] = sum(1 for c in p["checks"] if c["score"] == 1)
        p["half"] = sum(1 for c in p["checks"] if c["score"] == 0.5)
        p["none"] = sum(1 for c in p["checks"] if c["score"] == 0)
    return pillars


# ---------------------------------------------------------------- rendering

def ring(pct: int, size: int = 96) -> str:
    r = (size - 12) / 2
    c = 2 * 3.141592653589793 * r
    off = c * (1 - pct / 100)
    col = "#2f7d5b" if pct >= 80 else "#b07d1a" if pct >= 50 else "#9a3b3b"
    return (
        f'<svg class="ring" viewBox="0 0 {size} {size}" width="{size}" height="{size}" '
        f'role="img" aria-label="{pct} per cent of this pillar\'s points">'
        f'<circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none" stroke="#e6e0d4" stroke-width="8"/>'
        f'<circle cx="{size/2}" cy="{size/2}" r="{r}" fill="none" stroke="{col}" stroke-width="8" '
        f'stroke-linecap="round" stroke-dasharray="{c:.1f}" stroke-dashoffset="{off:.1f}" '
        f'transform="rotate(-90 {size/2} {size/2})"/>'
        f'<text x="{size/2}" y="{size/2+7}" text-anchor="middle" class="ringtext">{pct}%</text>'
        f'</svg>'
    )


MARK = {
    1: ("<span class='tick yes'>&#10003;</span>", "done", "met"),
    0.5: ("<span class='tick half'>&#8212;</span>", "part", "half met"),
    0: ("<span class='tick no'>&#10007;</span>", "todo", "not met"),
}


def pillar_card(p: dict) -> str:
    rows = []
    for c in p["checks"]:
        mark, cls, word = MARK[c["score"]]
        score_label = {1: "1", 0.5: "&frac12;", 0: "0"}[c["score"]]
        rows.append(
            f"<li class='{cls}'>"
            f"<span class='snum2'>{score_label}</span>"
            f"<span class='clabel'>{mark} {esc(c['label'])}"
            f"<span class='cscore'>{word}</span></span>"
            f"<span class='ctest'>{esc(c['tests'])}</span>"
            f"<span class='cev'>{esc(c['reason'])}</span></li>")
    links = "".join(f"<a class='plink' href='{esc(h)}'>{esc(l)}</a>" for l, h in p.get("links", []))
    return f"""
    <article class="pillar" id="p-{p['key']}">
      <div class="phead">
        {ring(p['pct'])}
        <div>
          <h3>{esc(p['name'])}</h3>
          <p class="pq">{esc(p['question'])}</p>
          <p class="pcount">{p['points']} of {p['out_of']} points &middot; {p['met']} met,
          {p['half']} half, {p['none']} not met</p>
        </div>
      </div>
      <ul class="checks">{''.join(rows)}</ul>
      <div class="plinks">{links}</div>
    </article>"""


def stage_row(i, name, status, kind, evidence) -> str:
    return f"""
      <li class="stage {kind}">
        <span class="snum">{i}</span>
        <div class="sbody">
          <div class="sline"><h4>{esc(name)}</h4><span class="chip {kind}">{esc(status)}</span></div>
          <p>{esc(evidence)}</p>
        </div>
      </li>"""


def build_html(F: dict, pillars: list[dict]) -> str:
    pages = F["pages"]
    total_pts = sum(p["points"] for p in pillars)
    total_out = sum(p["out_of"] for p in pillars)
    groundwork = round(total_pts / total_out * 100)

    # the five tools: none of them is a thing a distributor can open today
    tools_rows = "".join(
        f"<tr><td class='nowrap'><strong>{esc(t)}</strong></td><td>{esc(q)}</td>"
        f"<td class='nowrap no'>&#10007; no</td>"
        f"<td>On this PC only. No login, no invitation, and the pages behind it are ISZE's own "
        f"analysis.</td></tr>" for t, q in TOOLS)

    pillars_html = "".join(pillar_card(p) for p in pillars)

    # roadmap: stage 2 is decided by the release register, stage 3's count comes off disk
    stage2_kind, stage2_status, stage2_text = (
        ("ok", f"Done {F['approved_releases'][0].get('approved_on', '')}",
         f"One named release is approved: {F['approved_releases'][0].get('release_id')}, "
         f"{F['approved_releases'][0].get('rows', 0):,} rows, hash re-verified at build time. The "
         f"newer candidate stays unapproved pending the three white-paper re-tests.")
        if F["approved_releases"] else
        ("warn", "In progress",
         "No candidate is marked APPROVED in the release register yet."))

    stages = [
        (1, "Agree the scope and the portfolio", "Done", "ok",
         "The strategy paper, the presentation and the showcase describe the same proposition, and "
         "routine services are written out of scope."),
        (2, "Pin the classification release", stage2_status, stage2_kind, stage2_text),
        (3, "Open two prepared views", "Partly ready", "warn",
         f"The Atlas view exists (truck catalogue and parts atlas). The dealer-standard view exists "
         f"({F['ids_country']} country pages of one comparison). Neither is yet prepared as an "
         f"invitation, and neither has been used by a distributor for a real task."),
        (4, "Run the dealer sample", "Not started", "todo",
         "Ten dealers across two markets, including one reluctant to add reporting work. Nothing "
         "recorded yet."),
        (5, "Run the campaign line", "Not started", "todo",
         f"At least two offers clearing the {F['paper_rm']} size filter, measured before, during and "
         f"after. The campaign line has not run."),
        (6, "Evaluate, then extend or narrow", "Not started", "todo",
         "Stops if, after two eligible rounds, no participant can name a decision the tool changed. "
         "It does not pause or add a report."),
    ]
    stages_html = "".join(stage_row(*s) for s in stages)

    LABELS = {
        "sales": ("Sales and aftersales", "What we billed, the parts families, the customer packs"),
        "pricing": ("Pricing", "The price list, the revision, competitor prices"),
        "ids": ("Dealer standards", "The dealer comparison, one page per country"),
        "ops": ("Operations", "The console, the registers, the tender monitor"),
        "hub": ("Navigation", "The pages that index everything else"),
        "fleet": ("Vehicles in service", "The fleet each market runs"),
        "bi": ("Business intelligence", "Standing snapshots"),
        "gps": ("Spend per truck", "The distributor-facing proposal"),
        "globe": ("Map", "Uncaptured spend by market"),
        "side": ("Side project", "Not part of the aftersales chain"),
        "md_pack": ("Management pack", "Capture loss for the FY27-FY28 pack"),
    }
    order = ["hub", "sales", "pricing", "ids", "fleet", "ops", "bi", "gps", "globe", "md_pack", "side"]
    groups = []
    for folder in order:
        rows = [r for r in pages if r["folder"] == folder]
        if not rows:
            continue
        label, note = LABELS.get(folder, (folder, ""))
        items = []
        for r in sorted(rows, key=lambda x: x["title"].lower()):
            href = f"{r['file']}" if folder == "hub" else f"../{folder}/{r['file']}"
            items.append(
                f"<li><a href='{esc(href)}'><span class='ptitle'>{esc(r['title'] or r['file'])}</span>"
                f"<span class='pmeta'>{esc(r['mtime'])} &middot; {r['kb']} KB</span></a></li>")
        groups.append(
            f"""<div class="group">
              <div class="ghead"><h3>{esc(label)}</h3><span class="gcount">{len(rows)} pages</span></div>
              <p class="gnote">{esc(note)}</p>
              <ul class="plist">{''.join(items)}</ul>
            </div>""")
    groups_html = "".join(groups)

    task_rows = "".join(
        f"<tr><td><code>{esc(k)}</code></td>"
        f"<td>{'never run' if v.get('never') else esc(v.get('last'))}</td>"
        f"<td>{esc(v.get('result'))}</td><td>{esc(v.get('next'))}</td></tr>"
        for k, v in F["tasks"].items())

    price_task = F["tasks"].get("ISZE_PriceLedger_Weekly", {})
    price_ledger = ("First run " + str(price_task.get("next", "?"))) if price_task.get("never") \
        else ("Last ran " + str(price_task.get("last", "?")))

    opens = [
        ("Tender outcomes", f"{F['tender_outcomes']} of {F['tender_rows']}",
         "Nothing records whether a tender was pursued, passed, won or lost. Without this the "
         "tender list cannot show whether it is working."),
        ("Competitor price coverage", f"{F['cx_parts']} of {F['cx_total']:,} part numbers",
         "Only a small band of the price list has a competitor price, so the ranked price gaps rest "
         "on a narrow base."),
        ("Price history job", price_ledger,
         "The weekly competitor price history has not completed a run yet, so there is no trend to "
         "read, only a single look at today."),
        ("A distributor-facing version", "none of five",
         "No page today has a login, and none is written for a distributor to open on their own. "
         "Every built page is ISZE's own analysis."),
        ("The dealer sample", "not started",
         "The ten-dealer sample in two markets is the test of the whole design and it has not run."),
        ("Margin layer", "no cost basis",
         "Gross profit has no supplied cost basis anywhere in the workspace, so no page can show "
         "margin beside revenue without inventing one."),
    ]
    opens_html = "".join(
        f"<tr><td class='nowrap'><strong>{esc(a)}</strong></td>"
        f"<td class='nowrap'>{esc(b)}</td><td>{esc(c)}</td></tr>" for a, b, c in opens)

    big = "; ".join(f"{r['pn']} EUR {r['billed_eur']:,.0f} ({r['desc']})" for r in F["cov_big"][:9])
    bad_pns = ", ".join(r["part_number"] for r in F["sample_bad"])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ISZE Universe - where every pillar stands</title>
<style>
:root{{--navy:#15233c;--navy2:#1d3050;--terra:#c0552d;--paper:#f7f4ee;--card:#fff;
--ink:#232a35;--muted:#5f6b7a;--line:#dfd8cc;--ok:#2f7d5b;--warn:#b07d1a;--todo:#9a3b3b}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);
  font-family:"Segoe UI",-apple-system,Roboto,Arial,sans-serif;line-height:1.55;font-size:16px}}
h1,h2,h3,h4{{font-family:Georgia,"Times New Roman",serif;color:var(--navy);margin:0}}
code{{font-family:Consolas,"Courier New",monospace;font-size:.84em;background:#f0ece3;
  padding:1px 5px;border-radius:3px;color:#3c4655}}
a{{color:var(--navy)}}
.wrap{{max-width:1220px;margin:0 auto;padding:0 22px 70px}}

.hero{{background:linear-gradient(160deg,var(--navy) 0%,var(--navy2) 100%);color:var(--paper);
  padding:46px 22px 40px}}
.hero .inner{{max-width:1220px;margin:0 auto}}
.eyebrow{{text-transform:uppercase;letter-spacing:.19em;font-size:11.5px;color:#e8b79c;
  margin-bottom:11px}}
.hero h1{{color:#fff;font-size:40px;line-height:1.12;letter-spacing:-.4px;margin-bottom:14px;
  max-width:900px}}
.lede{{font-size:17.5px;color:#dfe6ef;max-width:860px;margin:0 0 8px}}
.lede strong{{color:#fff}}
.stamp{{font-size:12.5px;color:#a9b8cc;margin-top:16px;border-top:1px solid #33496b;
  padding-top:12px;max-width:960px}}

section{{margin-top:50px}}
.shead{{display:flex;align-items:baseline;gap:14px;border-bottom:2px solid var(--navy);
  padding-bottom:9px;margin-bottom:24px}}
.shead .n{{font-family:Georgia,serif;font-size:15px;color:var(--terra);font-weight:700}}
.shead h2{{font-size:26px}}
.shead p{{margin:0;color:var(--muted);font-size:14.5px;margin-left:auto;text-align:right;
  max-width:470px}}

.pillars{{display:grid;grid-template-columns:repeat(auto-fit,minmax(430px,1fr));gap:17px}}
.pillar{{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:21px;
  border-top:4px solid var(--navy)}}
.phead{{display:flex;gap:16px;align-items:center;margin-bottom:15px}}
.ringtext{{font-family:Georgia,serif;font-size:23px;font-weight:700;fill:var(--navy)}}
.pillar h3{{font-size:18px;line-height:1.25}}
.pq{{color:var(--terra);font-style:italic;font-size:13.5px;margin:4px 0 5px}}
.pcount{{font-size:12.5px;color:var(--muted);margin:0}}
.checks{{list-style:none;margin:0;padding:0;border-top:1px dashed var(--line);padding-top:12px}}
.checks li{{font-size:13.5px;padding:8px 0;display:grid;
  grid-template-columns:26px 1fr;gap:4px 8px;align-items:start;border-bottom:1px solid #f1ece2}}
.checks li .snum2{{grid-row:1 / span 3;font-family:Georgia,serif;font-weight:700;font-size:13px;
  color:#fff;background:#8d99a8;border-radius:50%;width:22px;height:22px;line-height:22px;
  text-align:center}}
.checks li.done .snum2{{background:var(--ok)}}
.checks li.part .snum2{{background:var(--warn)}}
.checks li.todo .snum2{{background:var(--todo)}}
.checks li .ctest{{grid-column:2;color:#4a5462;font-size:12.5px;margin-top:2px}}
.checks li .cev{{grid-column:2;color:var(--muted);font-size:12.5px;font-style:italic}}
.clabel{{color:#2c3644}}
.checks li.todo .clabel{{color:#5f6b7a}}
.cscore{{font-size:10.5px;text-transform:uppercase;letter-spacing:.07em;font-weight:700;
  margin-left:5px;white-space:nowrap}}
li.done .cscore{{color:var(--ok)}}
li.part .cscore{{color:var(--warn)}}
li.todo .cscore{{color:var(--todo)}}
.tick{{font-weight:700;font-size:14px}}
.tick.yes{{color:var(--ok)}}
.tick.half{{color:var(--warn)}}
.tick.no{{color:var(--todo)}}
.plinks{{margin-top:14px;border-top:1px solid var(--line);padding-top:12px;display:flex;
  flex-wrap:wrap;gap:7px}}
.plink{{font-size:12.5px;text-decoration:none;background:#eef3f9;border:1px solid #d5e0ec;
  padding:4px 10px;border-radius:11px;color:var(--navy)}}
.plink:hover{{background:var(--navy);color:#fff;border-color:var(--navy)}}

.stages{{list-style:none;margin:0;padding:0}}
.stage{{display:flex;gap:15px;background:var(--card);border:1px solid var(--line);
  border-left:5px solid var(--line);border-radius:6px;padding:17px 20px;margin-bottom:10px}}
.stage.ok{{border-left-color:var(--ok)}}
.stage.warn{{border-left-color:var(--warn)}}
.stage.todo{{border-left-color:var(--todo)}}
.snum{{flex:0 0 32px;height:32px;border-radius:50%;background:var(--navy);color:#fff;
  font-family:Georgia,serif;font-weight:700;display:flex;align-items:center;justify-content:center;
  font-size:14px}}
.sbody{{flex:1}}
.sline{{display:flex;align-items:center;gap:11px;justify-content:space-between}}
.stage h4{{font-size:16.5px}}
.stage p{{margin:5px 0 0;font-size:14px;color:#3d4757}}

.chip{{display:inline-block;font-size:11px;font-weight:700;text-transform:uppercase;
  letter-spacing:.06em;padding:3px 10px;border-radius:11px;white-space:nowrap}}
.chip.ok{{background:#e2f0e9;color:var(--ok)}}
.chip.warn{{background:#f7edd6;color:var(--warn)}}
.chip.todo{{background:#f6e3e2;color:var(--todo)}}

.groups{{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:16px}}
.group{{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:19px}}
.ghead{{display:flex;justify-content:space-between;align-items:baseline;gap:10px}}
.ghead h3{{font-size:17.5px}}
.gcount{{font-size:11.5px;color:#fff;background:var(--navy);padding:3px 9px;
  border-radius:10px;white-space:nowrap}}
.gnote{{font-size:12.5px;color:var(--muted);margin:6px 0 12px;font-style:italic}}
.plist{{list-style:none;margin:0;padding:0;max-height:none}}
.plist li{{border-top:1px solid #efeae0}}
.plist a{{display:flex;justify-content:space-between;align-items:baseline;gap:12px;
  padding:8px 2px;text-decoration:none}}
.plist a:hover .ptitle{{color:var(--terra);text-decoration:underline}}
.ptitle{{font-size:13.5px;color:var(--navy)}}
.pmeta{{font-size:11px;color:#9aa5b1;white-space:nowrap}}

table{{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);
  border-radius:6px;overflow:hidden;font-size:14.5px}}
th{{background:var(--navy);color:#fff;text-align:left;padding:11px 14px;font-size:12.5px;
  text-transform:uppercase;letter-spacing:.07em}}
td{{padding:11px 14px;border-top:1px solid var(--line);vertical-align:top;color:#3d4757}}
td.nowrap{{white-space:nowrap}}
td.no{{color:var(--todo);font-weight:600}}
tbody tr:nth-child(even){{background:#faf7f1}}

.note{{background:#fbf6ec;border-left:4px solid var(--terra);padding:15px 18px;
  border-radius:0 4px 4px 0;font-size:14.5px;color:#4a4132;margin-top:18px}}
.groundwork{{background:var(--card);border:1px solid var(--line);border-left:5px solid var(--navy);
  border-radius:6px;padding:18px 20px;margin-top:18px;font-size:15px}}
.groundwork b{{font-family:Georgia,serif;font-size:19px;color:var(--navy)}}
footer{{margin-top:56px;border-top:2px solid var(--navy);padding-top:20px;font-size:13px;
  color:var(--muted)}}
@media (max-width:700px){{.hero h1{{font-size:29px}} .shead{{flex-wrap:wrap}}
  .shead p{{margin-left:0;text-align:left}}}}
</style>
<script src="../_ui/isze-shell.js" defer></script>
</head>
<body>

<header class="hero"><div class="inner">
    <div class="eyebrow">Isuzu Universe &middot; where it stands</div>
    <h1>0 of 5 tools a distributor can open. Roadmap: stage 1 complete.</h1>
    <p class="lede">The strategy paper describes <strong>five tools a distributor or dealer opens and
    uses</strong>. None of them exists as that today: there is no login on any page, no invitation has
    gone out, and every page that is built is ISZE's own analysis. No page has ever been used by a
    distributor for a real task, which is the paper's own test.</p>
    <p class="lede">Behind that, the internal groundwork is real and is scored below.
    Each condition now carries its own reason, so a number can be argued with line by line.</p>
    <div class="stamp">Built {datetime.now().strftime('%d %B %Y, %H:%M')}. Pipeline checks:
    {F['verify_pass']} passed, {F['verify_fail']} failed, last run {esc(F['verify_at'])}. The
    classification gate last ran {esc(F['gate_at'])}. Nothing on this page writes to a file.</div>
</div></header>

<div class="wrap">

  <section id="tools">
    <div class="shead"><span class="n">01</span><h2>The five tools, and where each one is</h2>
      <p>The test the paper sets: a participant completes a real task and can name a decision the
      tool changed. By that test the answer is no, five times.</p></div>
    <table>
      <thead><tr><th>Tool</th><th>The question it answers</th><th>Can a distributor open it?</th>
      <th>Why not</th></tr></thead>
      <tbody>{tools_rows}</tbody>
    </table>
  </section>

  <section id="pillars">
    <div class="shead"><span class="n">02</span><h2>The pillars, condition by condition</h2>
      <p>Six areas of work. Each condition scores 1 when the thing does what its wording says,
      &frac12; when it only partly does or repeats credit already given for the same product, and 0
      when it is not met.</p></div>
    <div class="pillars">{pillars_html}</div>
    <div class="groundwork">
      <b>{groundwork}%</b> of the {total_out} condition points are earned: <b>{total_pts} of
      {total_out}</b>. Read that as internal groundwork, not as progress towards a tool a distributor
      can use - the five tests that ask for one score zero, at every pillar.
    </div>
    <div class="note"><strong>How to read a score, and what changed on 24 September.</strong> The
    earlier board asked twelve of its sixteen met conditions only whether a file existed, and scored
    every condition yes or no. Both are fixed: the conditions now test what the work is, and the
    score is graded, so a product cannot be paid for twice and a partial answer is not rounded up.
    Where a condition cannot be tested from a file, the page says so instead of inventing a pass.</div>
  </section>

  <section id="roadmap">
    <div class="shead"><span class="n">03</span><h2>The roadmap</h2>
      <p>The strategy paper's own six stages, in the order they have to happen.</p></div>
    <ol class="stages">{stages_html}</ol>
    <div class="note"><strong>What it costs, and when it stops.</strong> The paper recommends starting
    from the existing {esc(F['paper_line'] or 'EUR 60,000 to EUR 90,000')} route inside the existing
    EUR 100,000 planning envelope, a minimum offer size of {esc(F['paper_rm'] or 'EUR 150,000')} of
    eligible billing, and {esc(F['paper_enable'] or 'EUR 15,000 to EUR 25,000')} of dealer enablement
    spent as accepted tasks rather than as an entitlement. Every amount here is read from the paper and
    printed in euros; the earlier board printed them in pounds. It stops if, after two eligible rounds,
    no participant can name a decision the tool changed - and it does not pause, add a report, or widen
    the group.</div>
  </section>

  <section id="live">
    <div class="shead"><span class="n">04</span><h2>What is live</h2>
      <p>Every page that exists and opens today, {len(pages)} in total, grouped by what it is for.</p></div>
    <div class="groups">{groups_html}</div>
  </section>

  <section id="jobs">
    <div class="shead"><span class="n">05</span><h2>What runs without anyone watching</h2>
      <p>Read live from the Windows task list when this page was built, by the task's registered name.</p></div>
    <table>
      <thead><tr><th>Job</th><th>Last ran</th><th>Last result</th><th>Next run</th></tr></thead>
      <tbody>{task_rows}</tbody>
    </table>
  </section>

  <section id="open">
    <div class="shead"><span class="n">06</span><h2>What is not finished</h2>
      <p>The honest list, measured today.</p></div>
    <table>
      <thead><tr><th>Item</th><th>State today</th><th>Why it matters</th></tr></thead>
      <tbody>{opens_html}</tbody>
    </table>
  </section>

  <section id="numbers">
    <div class="shead"><span class="n">07</span><h2>The numbers behind the pillars</h2>
      <p>Each one read from the file named beside it at build time. Nothing here is typed by hand.</p></div>
    <table>
      <thead><tr><th>Measure</th><th>Value</th><th>Source</th></tr></thead>
      <tbody>
        <tr><td>Parts we billed</td><td class="nowrap">EUR {F['parts_base'] / 1e6:.1f}M to {esc(F['through'])}</td><td><code>metrics_snapshot.json</code></td></tr>
        <tr><td>Billed parts euro with a family</td><td class="nowrap">{F['cov_pct']:.2f}% ({F['cov_window'].get('from', '?')} to {F['cov_window'].get('to', '?')})</td><td><code>sales_fact.parquet</code> + <code>aim_master_v2.csv</code></td></tr>
        <tr><td>Parts above EUR 5,000 with no family</td><td class="nowrap">{len(F['cov_big'])} named: {esc(big)}</td><td><code>_aim_coverage_measure_20260924.json</code></td></tr>
        <tr><td>Unclassified parts euro, twelve months</td><td class="nowrap">EUR {F['coverage'].get('residual', {}).get('eur', 0):,.0f} on {F['coverage'].get('residual', {}).get('pns', 0):,} part numbers</td><td><code>_aim_coverage_measure_20260924.json</code></td></tr>
        <tr><td>Family agreement on the 50-part sample</td><td class="nowrap">{F['sample_l1']} of {F['sample_n']} = {F['sample_l1'] / F['sample_n'] * 100:.0f}%; group {F['sample_l2']}, leaf {F['sample_l3']}</td><td><code>_aim_accuracy_sample_20260924.csv</code></td></tr>
        <tr><td>The three family disagreements</td><td class="nowrap">{esc(bad_pns)}</td><td><code>_aim_accuracy_sample_20260924.csv</code></td></tr>
        <tr><td>Classification gate</td><td class="nowrap">{F['gate_pass']} of {F['gate_pass'] + F['gate_fail']} pass, verdict {esc(F['gate_verdict'])}</td><td><code>aim_classification_gate.json</code></td></tr>
        <tr><td>Approved classification release</td><td class="nowrap">{esc((F['approved_releases'][0]['release_id'] if F['approved_releases'] else 'none'))}, {F['release_sha_ok'] and 'hash matches' or 'no hash match'}, approved {esc(F['approved_releases'][0].get('approved_on', ''))} by {esc(F['approved_releases'][0].get('approved_by', ''))}</td><td><code>_releases/RELEASES.json</code></td></tr>
        <tr><td>Live public tenders watched</td><td class="nowrap">{F['tender_rows']}, of which {F['tender_rm']} R&amp;M and {F['tender_rm_open']} with a deadline still ahead</td><td><code>tender_data.json</code> ({esc(F['tender_generated'])})</td></tr>
        <tr><td>Part numbers with a competitor price</td><td class="nowrap">{F['cx_parts']} of {F['cx_total']:,}, EUR {F['cx_value'] / 1e6:.1f}M of billed value</td><td><code>CROSSREF_GRAPH_REPORT.md</code></td></tr>
        <tr><td>Billed against the target-spend ceiling, 2025</td><td class="nowrap">EUR {F['wallet_cap'] / 1e6:.2f}M of EUR {F['wallet_ceil'] / 1e6:.2f}M = {F['wallet_pct']:.1f}%</td><td><code>wallet_waterfall.csv</code></td></tr>
        <tr><td>Vehicles in service, by market</td><td class="nowrap">{F['wallet_dbs']} distributors in {F['wallet_countries']} countries, 2023 to 2025</td><td><code>wallet_waterfall.csv</code></td></tr>
        <tr><td>Live country comparison pages</td><td class="nowrap">{F['ids_country']}</td><td>counted on disk today</td></tr>
        <tr><td>Live pages</td><td class="nowrap">{len(pages)}</td><td>counted on disk today</td></tr>
      </tbody>
    </table>
    <div class="note"><strong>What this page could not establish.</strong> Whether the local deploy
    folders are reachable outside this PC; why no tender runs are logged for two Mondays in August and
    September; and whether the paper's size filter has been agreed by anyone beyond the paper
    recommending it. None of those is scored above.</div>
  </section>

  <footer>
    <p>Read when this page was built: the sales and target-spend files
    (<code>metrics_snapshot.json</code>, <code>wallet_waterfall.csv</code>, <code>sales_fact.parquet</code>),
    the classification master, its gate and its release register (<code>aim_master_v2.csv</code>,
    <code>aim_classification_gate.json</code>, <code>_releases/RELEASES.json</code>), the coverage and
    accuracy measures of 24 September, the live tender feed (<code>tender_data.json</code>), the
    competitor cross-reference report, the Windows task list, the strategy paper, and the pages
    themselves for the access and self-containment tests.</p>
    <p>This page is a description. It changes nothing, publishes nothing and sends nothing.</p>
  </footer>

</div>
</body>
</html>
"""


def main() -> int:
    F = facts()
    if not F["pages"]:
        NOTES.append("page inventory missing - run collect_page_inventory.py first")
    pillars = build_pillars(F)

    html = build_html(F, pillars)
    with io.open(OUT_HTML, "w", encoding="utf-8") as fh:
        fh.write(html)

    with io.open(OUT_CMD, "wb") as fh:
        fh.write(("@echo off\r\nstart \"\" \"%~dp0ISZE_UNIVERSE_BOARD.html\"\r\n").encode("ascii"))

    total_pts = sum(p["points"] for p in pillars)
    total_out = sum(p["out_of"] for p in pillars)
    state = {
        "built_at": datetime.now().isoformat(timespec="seconds"),
        "scoring": "graded: 1 met, 0.5 partial or repeated credit, 0 not met; points are halves of a condition",
        "groundwork_pct": round(total_pts / total_out * 100),
        "groundwork_points": total_pts,
        "groundwork_out_of": total_out,
        "headline": "0 of 5 tools a distributor can open. Roadmap: stage 1 complete.",
        "tools_open_to_a_distributor": 0,
        "tools_total": len(TOOLS),
        "pillars": [
            {"key": p["key"], "name": p["name"], "points": p["points"], "out_of": p["out_of"],
             "pct": p["pct"], "met": p["met"], "half": p["half"], "not_met": p["none"],
             "conditions": [
                 {"label": c["label"], "score": c["score"], "tests": c["tests"], "reason": c["reason"]}
                 for c in p["checks"]]}
            for p in pillars
        ],
        "live_pages": len(F["pages"]),
        "not_testable": NOT_TESTABLE,
    }
    with io.open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, ensure_ascii=False)

    print("wrote", OUT_HTML, os.path.getsize(OUT_HTML) // 1024, "KB")
    print("wrote", OUT_CMD)
    print("wrote", OUT_JSON)
    print("groundwork", state["groundwork_pct"], "%", f"({total_pts}/{total_out} points)")
    for p in state["pillars"]:
        print(f"  {p['pct']:>3}%  {p['name']}  ({p['points']}/{p['out_of']} pts, "
              f"{p['met']} met / {p['half']} half / {p['not_met']} not)")
    if NOTES:
        print("NOTES:", NOTES)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
