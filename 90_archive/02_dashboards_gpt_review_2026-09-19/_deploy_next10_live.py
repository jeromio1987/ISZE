#!/usr/bin/env python3
"""Deploy next10 fixed HTML onto live originals + refresh GPT pack + basis on rebuilt exec."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT = ROOT / "02_dashboards" / "sales" / "_gpt_review" / "2026-09-19_next10_fixed"
GPT = ROOT / "08_gpt" / "html_dashboard_review_next10_2026-09-19"

# Import helpers from fix script
import importlib.util

spec = importlib.util.spec_from_file_location(
    "fix_next10", ROOT / "02_dashboards" / "sales" / "_gpt_review" / "_fix_next10.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Mapping: fixed copy name → live original absolute path + preferred OPEN cmd name next to original
MAP = [
    (
        "01_ISZE_Exec_Aftersales_Paper.html",
        ROOT / "02_dashboards" / "sales" / "ISZE_Exec_Aftersales_Paper.html",
        "OPEN_Exec_Aftersales_Paper.cmd",
    ),
    (
        "02_ISZE_Leakage_Cockpit.html",
        ROOT / "02_dashboards" / "sales" / "ISZE_Leakage_Cockpit.html",
        "OPEN_ISZE_Leakage_Cockpit.cmd",
    ),
    (
        "03_Warranty_Commercial_Review.html",
        ROOT / "02_dashboards" / "sales" / "Warranty_Commercial_Review.html",
        "OPEN_Warranty_Commercial_Review.cmd",
    ),
    (
        "04_ISZE_AIM_Classification_Paper.html",
        ROOT / "02_dashboards" / "sales" / "ISZE_AIM_Classification_Paper.html",
        "OPEN_ISZE_AIM_Classification_Paper.cmd",
    ),
    (
        "05_ISZE_AIM_vs_Price_Class_Case.html",
        ROOT / "02_dashboards" / "sales" / "ISZE_AIM_vs_Price_Class_Case.html",
        "OPEN_ISZE_AIM_vs_Price_Class_Case.cmd",
    ),
    (
        "06_ISZE_Pricing_Policy_Paper_REV3.html",
        ROOT / "02_dashboards" / "pricing" / "ISZE_Pricing_Policy_Paper_REV3.html",
        "OPEN_Pricing_Policy_Paper_REV3.cmd",
    ),
    (
        "07_ISZE_Pricing_Revision_AIM_Source.html",
        ROOT / "02_dashboards" / "pricing" / "ISZE_Pricing_Revision_AIM_Source.html",
        "OPEN_Pricing_Revision_AIM_Source.cmd",
    ),
    (
        "08_ISZE_Price_Increase_5pct_Flat_REVIEW_2026-09-17.html",
        ROOT / "02_dashboards" / "pricing" / "ISZE_Price_Increase_5pct_Flat_REVIEW_2026-09-17.html",
        "OPEN_Price_Increase_5pct_Flat_REVIEW.cmd",
    ),
    (
        "09_ISZE_Competitiveness_Dashboard.html",
        ROOT / "02_dashboards" / "sales" / "ISZE_Competitiveness_Dashboard.html",
        "OPEN_ISZE_Competitiveness_Dashboard.cmd",
    ),
    (
        "10_Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html",
        ROOT / "02_dashboards" / "sales" / "Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html",
        "OPEN_Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.cmd",
    ),
]


def write_cmd(path: Path, html_name: str) -> None:
    path.write_bytes(f'@echo off\r\nstart "" "%~dp0{html_name}"\r\n'.encode("ascii"))


def polish_exec_from_builder() -> Path:
    """Take rebuilt live exec HTML, apply basis strip + residual language, write to OUT."""
    src = ROOT / "02_dashboards" / "sales" / "ISZE_Exec_Aftersales_Paper.html"
    dst = OUT / "01_ISZE_Exec_Aftersales_Paper.html"
    html = src.read_text(encoding="utf-8")
    html = html.replace("Parc cohort", "Fleet cohort")
    html = html.replace("parc cohort", "fleet cohort")
    html = mod.inject_css(html)
    strip = (
        '<div class="basis-strip">'
        "<div><b>Observed</b> Parts billed through 30 June 2026 · CY2025 complete</div>"
        "<div><b>Modelled</b> CY2025 target-spend ceiling €55.25M (not a forecast)</div>"
        "<div><b>Fleet</b> Historical trucks in service only — no forward forecast</div>"
        "<div><b>Sales to dealer</b> Six distributors with files (60% of GPS billed €); stocking, not final demand</div>"
        "</div>"
    )
    if 'class="basis-strip"' not in html:
        html = mod.inject_basis(html, strip)
    # Ensure Portugal coverage strings from builder are present
    html, _ = mod.lang_pass_shell(html)
    html = html.replace("theoretical_target spend_eur", "theoretical_wallet_eur")
    dst.write_text(html, encoding="utf-8")
    return dst


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    # Refresh exec fixed copy from builder output
    polish_exec_from_builder()
    write_cmd(OUT / "01_OPEN_Exec_Aftersales_Paper.cmd", "01_ISZE_Exec_Aftersales_Paper.html")

    updated = []
    for fixed_name, live, open_name in MAP:
        fixed = OUT / fixed_name
        if not fixed.exists():
            print("MISSING fixed", fixed_name)
            continue
        shutil.copy2(fixed, live)
        write_cmd(live.parent / open_name, live.name)
        # GPT pack refresh
        gpt_html = GPT / fixed_name
        if gpt_html.parent.exists():
            shutil.copy2(fixed, gpt_html)
        updated.append(str(live))
        print("LIVE", live)

    # GPT OPEN cmds already numbered — refresh from OUT
    for cmd in OUT.glob("0*_OPEN_*.cmd"):
        shutil.copy2(cmd, GPT / cmd.name)

    # Append deploy note to FIX_LOG
    log = OUT / "FIX_LOG.md"
    note = "\n## Live originals overwritten (Jerome ask)\n\n"
    note += "Each fixed file was copied onto its original `02_dashboards/` path:\n\n"
    for p in updated:
        note += f"- `{p}`\n"
    note += "\nGPT pack copies refreshed in parallel.\n"
    if log.exists():
        txt = log.read_text(encoding="utf-8")
        if "Live originals overwritten" not in txt:
            log.write_text(txt.rstrip() + "\n" + note, encoding="utf-8")
            shutil.copy2(log, GPT / "FIX_LOG.md")

    print("UPDATED", len(updated))
    for p in updated:
        print(p)


if __name__ == "__main__":
    main()
