# -*- coding: utf-8 -*-
from pathlib import Path

p = Path(
    r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\ISZE_Full_Project_Audit_20260825\ISZE_Full_Project_Audit_20260825.html"
)
html = p.read_text(encoding="utf-8")

old_verdict = (
    "    (€103.57M parts base, PMS/GPS/BVP, green-gated facts). It is not yet world-class, because the decision loop is unfinished\n"
    "    (23,236 ledger opportunities, 0 outcomes), dealer sell-out covers only 5 distributors, billing truth stops at 31 Mar 2026,\n"
    "    and 1,677 files sit unsorted in INBOX. Best-in-class is not more dashboards — it is network sell-out/fill, locked interval\n"
    "    assumptions, validated pocket price, and a weekly ledger→realised-€ cadence."
)

new_verdict = (
    "    (€112.09M parts base after Apr–Jun 2026 billing wired, PMS/GPS/BVP, <strong>verify gate green 116/0/0</strong>).\n"
    "    It is not yet world-class: the decision loop is still unfinished (23,236 ledger opportunities, 0 outcomes) and dealer sell-out\n"
    "    still covers only 5 distributors (long CSVs now re-emitted). Billing truth now runs through <strong>30 Jun 2026</strong>;\n"
    "    INBOX cut <strong>1,677 → 545</strong> after Week-1 execute. Best-in-class remains network sell-out/fill, locked intervals,\n"
    "    validated pocket price, and a weekly ledger→realised-€ cadence — not more dashboards."
)

if old_verdict not in html:
    raise SystemExit("cover verdict block not found")
html = html.replace(old_verdict, new_verdict)

replacements = [
    (
        '<div class="kpi ok"><div class="lbl">Parts base</div><div class="val">€103.57M</div><div class="note">GPS-facing parts only · snapshot</div></div>',
        '<div class="kpi ok"><div class="lbl">Parts base</div><div class="val">€112.09M</div><div class="note">GPS-facing parts · as-of 25 Aug 2026</div></div>',
    ),
    (
        '<div class="kpi"><div class="lbl">sales_fact rows</div><div class="val">477,505</div><div class="note">2023-01-03 → 2026-03-31</div></div>',
        '<div class="kpi"><div class="lbl">sales_fact rows</div><div class="val">514,037</div><div class="note">2023-01-03 → 2026-06-30</div></div>',
    ),
    (
        '<div class="kpi warn"><div class="lbl">Verify gate</div><div class="val">114 / 1 / 1</div><div class="note">pass / warn / fail · not green</div></div>',
        '<div class="kpi ok"><div class="lbl">Verify gate</div><div class="val">116 / 0 / 0</div><div class="note">pass / warn / fail · green</div></div>',
    ),
    (
        '<div class="kpi warn"><div class="lbl">INBOX backlog</div><div class="val">1,677</div><div class="note">files · ~477 MB unsorted</div></div>',
        '<div class="kpi"><div class="lbl">INBOX backlog</div><div class="val">545</div><div class="note">was 1,677 · Week-1 sort</div></div>',
    ),
    (
        "<li><strong>Time is stale at the core.</strong> <code>sales_fact</code> ends 31 Mar 2026 while newer raw (incl. Q1FY2027) already sits on disk — Apr–Aug 2026 is invisible to every derived KPI.</li>",
        "<li><strong>Billing freshness closed through Jun 2026.</strong> <code>Q1FY2027.XLSX</code> is now in <code>sales_fact</code> (514,037 rows). Jul–Aug 2026 still need the next SAP extract; Q1FY2027 lacks SaTy.</li>",
    ),
    (
        "every euro of the €103.57M parts base explained by",
        "every euro of the €112.09M parts base explained by",
    ),
    (
        "data:[1677,285,181,43,55,40,32,28,22,186]",
        "data:[545,285,181,43,55,40,32,28,22,186]",
    ),
    (
        "sales_fact.parquet (477,505) · CY23–25 raw · sales_2026tillApril · Israel GPS extract",
        "sales_fact.parquet (514,037) · CY23–25 raw · sales_2026tillApril · Q1FY2027 · Israel GPS extract",
    ),
    (
        "<td>Rows</td><td>477,505</td><td>Stable vs verify expectation (Δ 0%)</td>",
        "<td>Rows</td><td>514,037</td><td>Post Q1FY2027 wire · verify green</td>",
    ),
    (
        "<td>Date span</td><td>2023-01-03 → 2026-03-31</td><td>Five months of 2026 calendar missing from KPIs</td>",
        "<td>Date span</td><td>2023-01-03 → 2026-06-30</td><td>Jul–Aug 2026 still missing</td>",
    ),
    (
        "<td>Billing</td><td>sales_fact.parquet (477,505)</td><td>Active · horizon stale</td>",
        "<td>Billing</td><td>sales_fact.parquet (514,037)</td><td>Active · through Jun 2026</td>",
    ),
    (
        "<td>Staging</td><td>90_INBOX 1,677 files</td><td>Sorting owed</td>",
        "<td>Staging</td><td>90_INBOX 545 files</td><td>Reduced; more sorting owed</td>",
    ),
    (
        "<tr><td>10</td><td>INBOX 1,677 / ~477 MB unsorted</td><td>Landed sources not wired</td><td>90_INBOX</td></tr>",
        "<tr><td>10</td><td>INBOX was 1,677 → now 545</td><td>Partially sorted Week-1; more owed</td><td>90_INBOX</td></tr>",
    ),
    (
        "<li><strong>INBOX rule violated at scale</strong> — 1,677 files means “sorting owed” is not a footnote; it is the operating model failure.</li>",
        "<li><strong>INBOX discipline improved but not done</strong> — 1,677→545 after Week-1; target remains empty.</li>",
    ),
]

for old, new in replacements:
    if old not in html:
        print("MISSING:", old[:80])
    else:
        html = html.replace(old, new)

banner = """
<div class="callout green">
  <strong>Week-1 execute update (25 Aug 2026, same evening):</strong> verify green; sales_fact → 30 Jun 2026;
  parts base €112.09M; sell-out long CSVs re-emitted for 5 DBs + second layer rebuilt; INBOX 1,677→545;
  UIO_v17 quarantined; UMI ask drafted; leakage € stays internal until list-to-pocket signed.
  Cover KPIs above are post-execute. Body sections below still describe the audit-time baseline where noted.
</div>
"""
needle = '<div class="callout">\n  <strong>How this audit was built.</strong>'
if needle not in html:
    raise SystemExit("how-built callout not found")
if "Week-1 execute update" not in html:
    html = html.replace(needle, banner + needle, 1)

p.write_text(html, encoding="utf-8")
print("OK", p.stat().st_size)
