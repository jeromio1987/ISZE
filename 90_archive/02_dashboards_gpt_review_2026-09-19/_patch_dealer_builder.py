#!/usr/bin/env python3
from pathlib import Path

p = Path(r"C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\prism\scripts\build_dealer_sellout_aim_gps.py")
t = p.read_text(encoding="utf-8")
reps = [
    ("Second layer (sell-out AIM / GPS)", "Second layer (sales to dealer · AIM / GPS)"),
    ("<h2>Network summary</h2>", "<h2>Observed distributor subset — summary</h2>"),
    ("AIM mix by network", "AIM mix by distributor (observed subset)"),
    ("PMS — BVP qty (sell-out)", "PMS — BVP qty (sales to dealer)"),
    (
        "AIM comparison (sell-out qty vs ISZE-denom. proxy vs billing)",
        "AIM comparison (sales-to-dealer qty vs ISZE-denom. proxy vs billing)",
    ),
    ("Network view.", "Observed subset (not the full ISZE network)."),
    ('["Network","Layer"', '["Distributor","Layer"'),
    ("No sell-out mix rows.", "No sales-to-dealer mix rows."),
    ("on UTI sell-out.", "on UTI sales to dealer."),
    ("on IUK sell-out.", "on IUK sales to dealer."),
    ('f"{dist} sell-out qty"', 'f"{dist} sales-to-dealer qty"'),
]
for a, b in reps:
    c = t.count(a)
    print(("OK" if c else "MISS"), c, a[:70])
    t = t.replace(a, b)

if "basis-strip" not in t:
    t = t.replace(
        ".kpi .tip {{ display:none;",
        ".basis-strip {{ display:flex; flex-wrap:wrap; gap:8px 18px; margin:10px 0 14px; "
        "padding:10px 14px; background:#eef3f9; border-left:4px solid #c0552d; "
        "font-size:12px; line-height:1.45; color:#222; }}\n"
        ".basis-strip b {{ color:#15233c; letter-spacing:.04em; text-transform:uppercase; "
        "font-size:10px; margin-right:4px; }}\n"
        ".kpi .tip {{ display:none;",
    )
    old = (
        '  <div class="callout">{_e(payload.get("scope_note", ""))}<br/><strong>{_e(proxy_note)}</strong></div>\n'
        "  <section><h2>Observed distributor subset — summary</h2>"
    )
    new = (
        '  <div class="basis-strip"><div><b>Observed</b> Sales to dealer CY{YEAR}</div>'
        "<div><b>Scope</b> Listed distributors only — stocking, not final customer demand</div>"
        "<div><b>Entities</b> ITUK ≠ IUK · UTI ≠ UMI</div></div>\n"
        '  <div class="callout"><b>Scope:</b> Sales-to-dealer files for the listed distributors only — '
        "distributor stocking, not final customer demand. ITUK ≠ IUK. UTI ≠ UMI.<br/>"
        '{_e(payload.get("scope_note", ""))}<br/><strong>{_e(proxy_note)}</strong></div>\n'
        "  <section><h2>Observed distributor subset — summary</h2>"
    )
    if old in t:
        t = t.replace(old, new)
        print("basis injected")
    else:
        print("MISS callout block for basis inject")

p.write_text(t, encoding="utf-8")
print("wrote dealer builder")
