#!/usr/bin/env python3
"""Next-10 GPT-brief HTML fixes → 2026-09-19_next10_fixed.

Applies non-negotiable language / basis / scope fixes to review copies.
Prefer builders when rebuilt separately; this script always produces the
openable fixed map Jerome asked for.
"""
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
GPT = ROOT / "08_gpt" / "html_dashboard_review_next10_2026-09-19"
OUT = ROOT / "02_dashboards" / "sales" / "_gpt_review" / "2026-09-19_next10_fixed"
QA = OUT / "_qa"

BASIS_CSS = """
.basis-strip{display:flex;flex-wrap:wrap;gap:8px 18px;margin:10px 0 14px;padding:10px 14px;
background:#eef3f9;border-left:4px solid #c0552d;font-size:12px;line-height:1.45;color:#222}
.basis-strip b{color:#15233c;letter-spacing:.04em;text-transform:uppercase;font-size:10px;margin-right:4px}
"""

BASIS_DEFAULT = (
    '<div class="basis-strip">'
    "<div><b>Observed</b> Parts billed through 30 June 2026</div>"
    "<div><b>Modelled</b> Target spend / service demand where shown</div>"
    "<div><b>Fleet</b> Historical fleet only — no forward forecast quoted</div>"
    "</div>"
)

BASIS_SALES = (
    '<div class="basis-strip">'
    "<div><b>Observed</b> Parts billed through 30 June 2026</div>"
    "<div><b>Modelled</b> Target spend / service demand where shown</div>"
    "<div><b>Fleet</b> Historical fleet only — no forward forecast quoted</div>"
    "<div><b>Sales to dealer</b> Available for listed distributors only — stocking, not final customer demand</div>"
    "</div>"
)

LOG: list[dict] = []


def note(file: str, wrong: str, fixed: str, left: str = "") -> None:
    LOG.append({"file": file, "wrong": wrong, "fixed": fixed, "left": left})


def write_cmd(folder: Path, name: str, html_name: str) -> None:
    p = folder / name
    p.write_text(f'@echo off\r\nstart "" "%~dp0{html_name}"\r\n', encoding="utf-8", newline="\n")
    # force CRLF
    raw = p.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    p.write_bytes(raw)


def inject_css(html: str) -> str:
    if "basis-strip" in html and ".basis-strip{" in html:
        return html
    if "</style>" in html:
        return html.replace("</style>", BASIS_CSS + "</style>", 1)
    if "<head>" in html:
        return html.replace("<head>", "<head><style>" + BASIS_CSS + "</style>", 1)
    return html


def inject_basis(html: str, strip: str) -> str:
    if 'class="basis-strip"' in html:
        return html
    # Prefer first wrap / sheet / body content
    for marker in (
        '<div class="wrap">',
        '<div class="sheet">',
        '<main',
        '<body>',
    ):
        i = html.find(marker)
        if i >= 0:
            # insert after opening tag line
            end = html.find(">", i)
            if end > 0:
                return html[: end + 1] + "\n" + strip + "\n" + html[end + 1 :]
    return html


def lang_pass(html: str) -> tuple[str, list[str]]:
    """Shared spoken-label replacements on UI text only. Returns (html, change_notes)."""
    notes: list[str] = []
    reps = [
        (r"\bsell-through\b", "sales to dealer"),
        (r"\bSell-through\b", "Sales to dealer"),
        (r"\bsell through\b", "sales to dealer"),
        (r"\bSell through\b", "Sales to dealer"),
        (r"reference dealer sell-out", "reference dealer price"),
        (r"Reference dealer sell-out", "Reference dealer price"),
        (r"dealer sell-out", "sales to dealer"),
        (r"Dealer sell-out", "Sales to dealer"),
        (r"\bsell-out\b", "sales to dealer"),
        (r"\bSell-out\b", "Sales to dealer"),
        (r"\bstreet fills\b", "OEM peer retail prices"),
        (r"\bstreet index\b", "price index"),
        (r"PR00\s*(?:→|->|&rarr;)\s*street", "PR00 → reference dealer price"),
        (r"\bstreet\b", "reference dealer price"),
        (r"\bStreet\b", "Reference dealer price"),
        (r"target parts wallet", "target parts spend"),
        (r"target wallet", "target spend"),
        (r"parts wallet", "parts billed / target spend"),
        (r"(?<![A-Za-z_])wallet(?![A-Za-z_])", "target spend"),
        (r"(?<![A-Za-z_])Wallet(?![A-Za-z_])", "Target spend"),
        (r"Book B \(the price list we might change\)", "the price list we might revise"),
        (r"Book B alloc ambition", "price-list revision ambition"),
        (r"\bBook B\b", "the price list"),
        (r"bucketed parc", "bucketed trucks in service"),
        (r"× parc", "× trucks in service"),
        (r"with parc", "with trucks in service"),
        (r"without parc", "without trucks in service"),
        (r"of the parc", "of the trucks in service"),
        (r"GPS parc", "GPS trucks in service"),
        (r"(?<![A-Za-z_])parc(?![A-Za-z_])", "trucks in service"),
        (r"(?<![A-Za-z_])Parc(?![A-Za-z_])", "Trucks in service"),
        (r"lost sales", "modelled opportunity gap"),
        (r"Lost Sales", "Modelled opportunity gap"),
        (r"never bought", "not currently billed"),
        (r"Never bought", "Not currently billed"),
        (r"Unbought demand", "Unbilled modelled demand"),
        (r"unbought demand", "unbilled modelled demand"),
    ]
    out = html
    for pat, repl in reps:
        new_out, n = re.subn(pat, repl, out)
        if n:
            notes.append(f"{pat} → {repl} (×{n})")
            out = new_out
    out2, n = re.subn(r"\bMode A\b", "shared / external", out)
    if n:
        notes.append(f"Mode A → shared/external ×{n}")
        out = out2
    out2, n = re.subn(r"\bMode B\b", "internal / private", out)
    if n:
        notes.append(f"Mode B → internal/private ×{n}")
        out = out2
    return out, notes


def split_json_payloads(html: str) -> list[tuple[str, bool]]:
    """Split HTML into (chunk, is_json_payload) so lang_pass never touches data keys."""
    parts: list[tuple[str, bool]] = []
    pos = 0
    for m in re.finditer(
        r"<script[^>]*type=[\"']application/json[\"'][^>]*>.*?</script>"
        r"|window\.__\w+__\s*=\s*\{.*?\};\s*"
        r"|<script[^>]*>\s*window\.__\w+__\s*=\s*\{.*?\}\s*;?\s*</script>",
        html,
        flags=re.S | re.I,
    ):
        if m.start() > pos:
            parts.append((html[pos : m.start()], False))
        parts.append((m.group(0), True))
        pos = m.end()
    if pos < len(html):
        parts.append((html[pos:], False))
    if not parts:
        parts = [(html, False)]
    return parts


def lang_pass_shell(html: str) -> tuple[str, list[str]]:
    """Language pass that skips embedded JSON / window payload blobs."""
    notes: list[str] = []
    out_chunks: list[str] = []
    for chunk, is_json in split_json_payloads(html):
        if is_json:
            out_chunks.append(chunk)
            continue
        fixed, n = lang_pass(chunk)
        notes.extend(n)
        out_chunks.append(fixed)
    return "".join(out_chunks), notes


def fix_exec(src: Path, dst: Path) -> None:
    html = src.read_text(encoding="utf-8", errors="replace")
    html = inject_css(html)
    # Portugal coverage honesty
    html = html.replace(
        "Sell-out files cover 54.4% of GPS billed euro (five distributors).",
        "Sales-to-dealer files cover 60.0% of GPS billed euro (six distributors, including Portugal).",
    )
    html = html.replace(
        "Sales to dealer files cover 54.4% of GPS billed euro (five distributors).",
        "Sales-to-dealer files cover 60.0% of GPS billed euro (six distributors, including Portugal).",
    )
    html = html.replace(
        "Sell-out files exist for ITUK, IUK, Ireland, UTI and Greece = <b>54.4% of GPS billed euro</b> (€16.74M of €30.76M). Germany + Belgium + Portugal would add €6.36M and lift visibility to <b>75.1%</b>.",
        "Sales-to-dealer files exist for ITUK, IUK, Ireland, UTI, Greece and Portugal = <b>60.0% of GPS billed euro</b> (€18.45M of €30.76M). Germany + Belgium would add €4.65M and lift visibility to <b>75.1%</b>.",
    )
    # after lang_pass these may already be rewritten — also handle post-lang versions
    html = html.replace(
        "five distributors (54.4% of GPS billed euro)",
        "six distributors including Portugal (60.0% of GPS billed euro)",
    )
    html = html.replace(
        "1,595 CY2025 exception rows sit on five distributors only — 54.4% of billed euro, not the whole network",
        "1,595 CY2025 exception rows sit on the observed sales-to-dealer subset — not the whole network",
    )
    html = html.replace(
        "Five DBs = 54.4% of GPS billed euro; DE+BE+PT would reach 75.1%",
        "Six DBs including Portugal = 60.0% of GPS billed euro; DE+BE would reach 75.1%",
    )
    html = html.replace(
        "Sell-out 54.4% of billed euro (to 75.1% with DE/BE/PT)",
        "Sales to dealer 60.0% of billed euro (to 75.1% with DE/BE)",
    )
    html = html.replace(
        "DE+BE+PT sell-out would lift visibility 54.4% → 75.1%",
        "DE+BE sales-to-dealer files would lift visibility 60.0% → 75.1%",
    )
    html = html.replace(
        "DE/BE/PT sell-out",
        "DE/BE sales-to-dealer files",
    )
    html = html.replace(
        "three missing sell-out files",
        "two missing sales-to-dealer files (Germany, Belgium)",
    )
    html = html.replace(
        "three verified sell-out longs",
        "verified sales-to-dealer longs",
    )
    html = html.replace(
        "Germany or Belgium dealer sell-out long",
        "Germany or Belgium sales-to-dealer long",
    )
    html = html.replace(
        "['No sell-out','High ST','No bill','Low ST']",
        "['No sales to dealer','High vs bill','No bill','Low vs bill']",
    )
    html = html.replace(
        "Billed, no matching sell-out",
        "Billed, no matching sales to dealer",
    )
    html = html.replace(
        "High sell-through vs bill",
        "High sales to dealer vs bill",
    )
    html = html.replace(
        "Sell-out with no bill",
        "Sales to dealer with no bill",
    )
    html = html.replace("Low sell-through", "Low sales to dealer")
    html, notes = lang_pass_shell(html)
    strip = (
        '<div class="basis-strip">'
        "<div><b>Observed</b> Parts billed through 30 June 2026 · CY2025 complete</div>"
        "<div><b>Modelled</b> CY2025 target-spend ceiling €55.25M (not a forecast)</div>"
        "<div><b>Fleet</b> Historical trucks in service only — no forward forecast</div>"
        "<div><b>Sales to dealer</b> Six distributors with files (60% of GPS billed €); stocking, not final demand</div>"
        "</div>"
    )
    html = inject_basis(html, strip)
    dst.write_text(html, encoding="utf-8")
    note(
        dst.name,
        "Banned sell-out/sell-through/parc/Book B; five-DB 54.4% ignored Portugal long; no basis strip.",
        "Spoken labels; Portugal included → 60.0% coverage (DE+BE → 75.1%); basis strip; modelled ceiling labelled.",
        "Replenishment exception row count (1,595) still reflects the operational extract vintage — not re-counted in this pass.",
    )


def fix_leakage(src: Path, dst: Path) -> None:
    html = src.read_text(encoding="utf-8", errors="replace")
    html = inject_css(html)
    # Payload blob starts at const __LEAK__ — never run lang_pass across it.
    marker = "const __LEAK__ = {"
    idx = html.find(marker)
    if idx < 0:
        idx = len(html)
    head, tail = html[:idx], html[idx:]
    head = head.replace(
        "Distributor leakage cockpit",
        "Distributor opportunity cockpit",
    )
    head = head.replace(
        "Where parts revenue is won and lost, by market",
        "Where measured billing and modelled gaps appear, by market — diagnostics are not additive",
    )
    head = head.replace("Unbought demand", "Unbilled modelled demand")
    head = head.replace("unbought demand", "unbilled modelled demand")
    head = head.replace(
        "Where does the fleet need parts that we never billed?",
        "Where does modelled service demand exceed parts billed?",
    )
    head, _ = lang_pass(head)
    # Safe quoted-string swaps inside payload for known UI captions only
    for a, b in [
        ('"Unbought demand"', '"Unbilled modelled demand"'),
        ("'Unbought demand'", "'Unbilled modelled demand'"),
        ("Largest unbought lines", "Largest unbilled modelled lines"),
        ("never billed", "not billed"),
    ]:
        if a in tail:
            tail = tail.replace(a, b)
    banner = (
        '<div class="basis-strip" style="background:#fff4e8">'
        "<div><b>Note</b> Gap types on this page use different bases and are <b>not additive</b>. "
        "Modelled service-demand shortfalls are not observed lost sales. "
        "No network-wide service-demand euro total is shown as a headline.</div>"
        "</div>"
    )
    head = inject_basis(head, BASIS_DEFAULT + banner)
    dst.write_text(head + tail, encoding="utf-8")
    note(
        dst.name,
        "Generic 'leakage / won and lost / unbought' framing; risk of reading gaps as additive observed loss.",
        "Retitled opportunity cockpit; non-additive banner; unbilled modelled demand; basis strip; shell language only.",
        "Full payload rebuild deferred. Source labels.mjs updated for next rebuild.",
    )


def fix_warranty(src: Path, dst: Path) -> None:
    html = src.read_text(encoding="utf-8", errors="replace")
    html = inject_css(html)
    html = html.replace(
        "Warranty parts cost as a share of the part's own target wallet",
        "Warranty parts cost as a share of the part's own target spend",
    )
    html = html.replace("target parts wallet", "target parts spend")
    html = html.replace("target wallet", "target spend")
    html = html.replace("% of wallet", "% of target spend")
    html = html.replace("Target wallet €", "Target spend €")
    html, notes = lang_pass_shell(html)
    html = inject_basis(html, BASIS_DEFAULT)
    dst.write_text(html, encoding="utf-8")
    note(
        dst.name,
        "Used 'wallet' in shared headings.",
        "Target spend wording; basis strip.",
        "Underlying JSON keys still use target_wallet_eur (pipeline).",
    )


def fix_aim_classification(src: Path, dst: Path) -> None:
    html = src.read_text(encoding="utf-8", errors="replace")
    html = inject_css(html)
    html, notes = lang_pass_shell(html)
    html = inject_basis(
        html,
        '<div class="basis-strip">'
        "<div><b>Observed</b> Classification of billed / listed part numbers</div>"
        "<div><b>Purpose</b> Family language for commercial analysis — not a revenue gap model</div>"
        "<div><b>Fleet</b> Historical only where fleet appears</div>"
        "</div>",
    )
    dst.write_text(html, encoding="utf-8")
    note(dst.name, "Missing basis strip; possible spoken-label drift.", "Basis strip + language pass.", "No material gap-hero issues found.")


def fix_aim_price_class(src: Path, dst: Path) -> None:
    html = src.read_text(encoding="utf-8", errors="replace")
    html = inject_css(html)
    html, notes = lang_pass_shell(html)
    # Prefer margin language callout if factors dominate
    if "class_factor" in html.lower() or "factor 0." in html.lower():
        tip = (
            '<div class="basis-strip"><div><b>Read as margin</b> Class factors are divisors; '
            "decision language is margin (e.g. factor 0.47 = 53% margin). "
            "Reference dealer price = list × 1.40 × 1.275.</div></div>"
        )
        html = inject_basis(html, tip)
    else:
        html = inject_basis(html, BASIS_DEFAULT)
    dst.write_text(html, encoding="utf-8")
    note(dst.name, "Risk of factor-first language; missing basis.", "Margin tip + basis + language pass.", "")


def fix_pricing_policy(src: Path, dst: Path) -> None:
    html = src.read_text(encoding="utf-8", errors="replace")
    html = inject_css(html)
    html, notes = lang_pass_shell(html)
    html = inject_basis(
        html,
        '<div class="basis-strip">'
        "<div><b>Observed</b> Current priced book / competing quotes where cited</div>"
        "<div><b>Modelled</b> Policy rules and revision scenarios — not committed list changes</div>"
        "<div><b>Fleet</b> Historical only; no forward forecast as a price basis</div>"
        "</div>",
    )
    dst.write_text(html, encoding="utf-8")
    note(dst.name, "Book B / spoken-label risk; missing basis strip.", "Language pass + policy basis strip.", "REV3 label retained.")


def fix_pricing_revision(src: Path, dst: Path) -> None:
    text = src.read_text(encoding="utf-8", errors="replace")
    text = inject_css(text)
    text, _ = lang_pass_shell(text)
    text = inject_basis(
        text,
        '<div class="basis-strip">'
        "<div><b>Observed</b> AIM / list / billed windows labelled on the page</div>"
        "<div><b>Modelled</b> Proposed revision — not yet a committed price move</div>"
        "<div><b>Entities</b> ITUK ≠ IUK · UMI ≠ UTI</div>"
        "</div>",
    )
    dst.write_text(text, encoding="utf-8")
    note(
        dst.name,
        "Shell wording risk; no basis strip.",
        "Shell language + basis; embedded JSON payload left intact (field names).",
        "Full rebuild of AIM source dashboard not run in this pass (6MB payload).",
    )


def fix_price_5pct(src: Path, dst: Path) -> None:
    html = src.read_text(encoding="utf-8", errors="replace")
    html = inject_css(html)
    html, _ = lang_pass_shell(html)
    banner = (
        '<div class="basis-strip" style="background:#fff4e8">'
        "<div><b>Scenario</b> Flat ~5% list increase is a <b>modelled impact reading</b>, not committed policy "
        "and not observed uplift. CY2026 billing is January–June only — do not compare to a full prior year as growth.</div>"
        "</div>"
    )
    html = inject_basis(html, banner + BASIS_DEFAULT)
    dst.write_text(html, encoding="utf-8")
    note(dst.name, "Scenario could be read as committed policy.", "Scenario banner + basis strip + language.", "")


def fix_competitiveness(src: Path, dst: Path) -> None:
    html = src.read_text(encoding="utf-8", errors="replace")
    html = inject_css(html)
    html = html.replace("PR00 → street", "PR00 → reference dealer price")
    html = html.replace("PR00 &rarr; street", "PR00 &rarr; reference dealer price")
    html = html.replace("Full chain PR00 → street", "Full chain PR00 → reference dealer price")
    html, _ = lang_pass_shell(html)
    html = inject_basis(
        html,
        '<div class="basis-strip">'
        "<div><b>Observed</b> Shop / peer quotes where scraped</div>"
        "<div><b>Reference</b> Reference dealer price = list × 1.40 × 1.275 (price index = shop ÷ reference)</div>"
        "<div><b>Coverage</b> Peer coverage is incomplete — do not read as full-network</div>"
        "</div>",
    )
    dst.write_text(html, encoding="utf-8")
    note(dst.name, "Street wording in channel chain footnotes.", "Reference dealer price; basis strip; language pass.", "Cross-nav links outside pack unchanged.")


def fix_dealer(src: Path, dst: Path) -> None:
    html = src.read_text(encoding="utf-8", errors="replace")
    html = inject_css(html)
    html = html.replace(
        "Second layer (sell-out AIM / GPS)",
        "Second layer (sales to dealer · AIM / GPS)",
    )
    html = html.replace("<h2>Network summary</h2>", "<h2>Observed distributor subset — summary</h2>")
    html = html.replace("AIM mix by network", "AIM mix by distributor (observed subset)")
    html = html.replace("PMS — BVP qty (sell-out)", "PMS — BVP qty (sales to dealer)")
    html = html.replace(
        "AIM comparison (sell-out qty vs ISZE-denom. proxy vs billing)",
        "AIM comparison (sales-to-dealer qty vs ISZE-denom. proxy vs billing)",
    )
    html = html.replace(
        "Network view.",
        "Observed subset (not the full ISZE network).",
    )
    html = html.replace("<th>Network</th>", "<th>Distributor</th>")
    # scope callout
    if "stocking decisions" not in html.lower():
        html = html.replace(
            '<div class="callout">',
            '<div class="callout"><b>Scope:</b> Sales-to-dealer files for the listed distributors only — '
            "distributor stocking, not final customer demand. ITUK ≠ IUK. UTI ≠ UMI. "
            "Portugal is included where the long file exists.<br/>",
            1,
        )
    html, _ = lang_pass_shell(html)
    html = inject_basis(html, BASIS_SALES)
    dst.write_text(html, encoding="utf-8")
    note(
        dst.name,
        "Headline 'Network' / sell-out UI; overclaim risk.",
        "Sales to dealer wording; observed-subset labels; basis strip; UTI≠UMI / ITUK≠IUK restated.",
        "Filename still contains Sellout (lineage only).",
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    QA.mkdir(parents=True, exist_ok=True)

    jobs = [
        ("01_ISZE_Exec_Aftersales_Paper.html", fix_exec, "01_OPEN_Exec_Aftersales_Paper.cmd"),
        ("02_ISZE_Leakage_Cockpit.html", fix_leakage, "02_OPEN_Leakage_Cockpit.cmd"),
        ("03_Warranty_Commercial_Review.html", fix_warranty, "03_OPEN_Warranty_Commercial_Review.cmd"),
        ("04_ISZE_AIM_Classification_Paper.html", fix_aim_classification, "04_OPEN_AIM_Classification_Paper.cmd"),
        ("05_ISZE_AIM_vs_Price_Class_Case.html", fix_aim_price_class, "05_OPEN_AIM_vs_Price_Class_Case.cmd"),
        ("06_ISZE_Pricing_Policy_Paper_REV3.html", fix_pricing_policy, "06_OPEN_Pricing_Policy_Paper_REV3.cmd"),
        ("07_ISZE_Pricing_Revision_AIM_Source.html", fix_pricing_revision, "07_OPEN_Pricing_Revision_AIM_Source.cmd"),
        ("08_ISZE_Price_Increase_5pct_Flat_REVIEW_2026-09-17.html", fix_price_5pct, "08_OPEN_Price_Increase_5pct_Flat_REVIEW.cmd"),
        ("09_ISZE_Competitiveness_Dashboard.html", fix_competitiveness, "09_OPEN_Competitiveness_Dashboard.cmd"),
        ("10_Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html", fix_dealer, "10_OPEN_Dealer_Sales_to_Dealer_AIM_GPS_ITUK_UTI_2025.cmd"),
    ]

    for html_name, fn, cmd_name in jobs:
        src = GPT / html_name
        if not src.exists():
            note(html_name, "MISSING in GPT folder", "", "Skipped")
            continue
        print("fixing", html_name, flush=True)
        fn(src, OUT / html_name)
        write_cmd(OUT, cmd_name, html_name)

    # Competitiveness assets
    for sub in ("_ui", "Data"):
        s = GPT / sub
        if s.exists():
            d = OUT / sub
            if d.exists():
                shutil.rmtree(d)
            shutil.copytree(s, d)

    # Also sync fixed copies back into GPT folder (Jerome wants openable files)
    for html_name, _, cmd_name in jobs:
        if (OUT / html_name).exists():
            shutil.copy2(OUT / html_name, GPT / html_name)
            if (OUT / cmd_name).exists():
                shutil.copy2(OUT / cmd_name, GPT / cmd_name)

    # INDEX + FIX_LOG
    lines = [
        "# Next 10 fixed — 2026-09-19",
        "",
        f"Built: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "Open from this folder (double-click `0N_OPEN_*.cmd`).",
        "",
        f"`{OUT}`",
        "",
        "| # | HTML | OPEN |",
        "|---|---|---|",
    ]
    for i, (html_name, _, cmd_name) in enumerate(jobs, 1):
        lines.append(f"| {i} | `{html_name}` | `{cmd_name}` |")
    lines += [
        "",
        "## Also updated",
        "",
        f"Copies synced into `{GPT}` so MAP paths still open fixed files.",
        "",
        "See `FIX_LOG.md` for per-file detail.",
        "",
    ]
    (OUT / "INDEX.md").write_text("\n".join(lines), encoding="utf-8")

    fl = ["# FIX_LOG — next 10 HTML (2026-09-19)", "", "Against `ISZE_HTML_DASHBOARD_FIX_BRIEF.md` non-negotiables.", ""]
    for row in LOG:
        fl.append(f"## {row['file']}")
        fl.append(f"- **Was wrong:** {row['wrong']}")
        fl.append(f"- **Fixed:** {row['fixed']}")
        if row.get("left"):
            fl.append(f"- **Left / disagreed:** {row['left']}")
        fl.append("")
    fl += [
        "## Cross-page disagreements / notes",
        "",
        "- **Portugal coverage:** Portugal `dealer_sellout_long_PORTUGAL_CY2025.csv` exists. "
        "Exec paper coverage updated from five-DB 54.4% → six-DB **60.0%** of the controlled €30.76M GPS billed book; "
        "DE+BE still lifts to **75.1%**. Controlled CY2025 ceiling figures unchanged (€55.253M / 55.7% / €24.497M gap).",
        "- **Leakage Cockpit:** Full node rebuild not required for this review deliverable; UI strings patched on the snapshot. "
        "`labels.mjs` source updated so the next extract/build keeps the new wording.",
        "- **Pricing Revision AIM Source:** Embedded JSON payload not rewritten (avoids breaking field names); shell only.",
        "- **Filename `Dealer_Sellout_*`:** Kept for lineage; UI says sales to dealer.",
        "",
    ]
    (OUT / "FIX_LOG.md").write_text("\n".join(fl), encoding="utf-8")
    shutil.copy2(OUT / "FIX_LOG.md", GPT / "FIX_LOG.md")
    shutil.copy2(OUT / "INDEX.md", GPT / "FIXED_INDEX.md")

    # Point MAP at fixed folder
    map_path = GPT / "MAP.md"
    if map_path.exists():
        m = map_path.read_text(encoding="utf-8", errors="replace")
        banner = (
            "\n\n---\n\n## Fixed deliverable (2026-09-19 pass)\n\n"
            "Openable fixed copies live in:\n\n"
            f"`{OUT}`\n\n"
            "Also synced into this GPT folder. See `FIX_LOG.md` / `FIXED_INDEX.md`.\n"
        )
        if "Fixed deliverable (2026-09-19 pass)" not in m:
            map_path.write_text(m.rstrip() + banner, encoding="utf-8")

    print("DONE", OUT)
    print("files", len(list(OUT.glob("*.html"))))


if __name__ == "__main__":
    main()
