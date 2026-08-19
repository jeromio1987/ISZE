"""Send FULL pricing analysis pack to Jerome Isuzu mailbox ONLY.

Explicit override: Send allowed ONLY to jerome.van.der.pluym@isuzu-e.com.
Never add CC/BCC or other recipients. Requires audit PASS / PASS_WITH_CAVEATS.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ISZE = Path(__file__).resolve().parents[3]
HTML = ISZE / "02_dashboards" / "pricing" / "ISZE_Pricing_Full_Analysis_Pack.html"
META = ISZE / "01_data" / "00_derived" / "pricing_full_analysis_pack.meta.json"
AUDIT = ISZE / "01_data" / "00_derived" / "_pricing_full_pack_audit.md"
AUDIT_JSON = ISZE / "01_data" / "00_derived" / "_pricing_full_pack_audit.json"
NET = ISZE / "01_data" / "00_derived" / "pr00_realization_network_cy.csv"
MOS = ISZE / "01_data" / "00_derived" / "kpi_mos_response_summary_2025_2026.csv"
ZPR1 = ISZE / "01_data" / "00_derived" / "zpr1_vs_pr00_by_payer_year.csv"
PMS = ISZE / "01_data" / "00_derived" / "pricing_pack_pms_total_by_db_year.csv"
AIMGPS = ISZE / "01_data" / "00_derived" / "pricing_pack_aim_gps_cy2025.csv"
RESULT = ISZE / "02_dashboards" / "pricing" / "_build" / "outlook_send_pricing_full_pack_result.json"

TO = "jerome.van.der.pluym@isuzu-e.com"
OL_MAIL_ITEM = 0


def main() -> int:
    if not HTML.is_file():
        raise SystemExit(f"Missing HTML: {HTML}")
    if not AUDIT_JSON.is_file():
        raise SystemExit("Missing audit JSON — run audit_pricing_full_pack.py first")

    audit = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
    verdict = audit.get("verdict")
    if verdict not in {"PASS", "PASS_WITH_CAVEATS"}:
        raise SystemExit(f"Refusing Send: audit verdict={verdict!r}")

    meta = json.loads(META.read_text(encoding="utf-8")) if META.is_file() else {}
    integ = meta.get("integrity", {})
    score = integ.get("score", audit.get("integrity_score", "?"))
    band = integ.get("band", audit.get("integrity_band", "?"))
    cy25 = next((r for r in meta.get("findings_core", {}).get("network", []) if r.get("year") == 2025), {})
    pms25 = next((r for r in meta.get("pms", {}).get("network_by_year", []) if int(r.get("year", 0)) == 2025), {})
    zf = meta.get("zpr1_flags", {})
    gap = meta.get("findings_core", {}).get("nolist", {})

    subject = (
        f"Pricing FULL analysis pack — integrity {score}/100 ({band}) — audit {verdict} — 2026-08-11"
    )
    body = (
        "Jerome,\n\n"
        "Self-mail: FULL pricing + AIM + PMS/GPS + MOS + VPACC analysis pack.\n"
        f"Audit verdict: {verdict} (mandatory gate before Send).\n\n"
        f"Integrity score: {score}/100 ({band}) — INTERNAL QA / PROVISIONAL.\n"
        "Do not quote list-to-pocket externally.\n\n"
        "Headline findings\n"
        f"1. CY2025 realization (matched): {cy25.get('realization_pct', '—')}%\n"
        f"2. CY2025 list coverage: {cy25.get('coverage_pct', '—')}%\n"
        f"3. NO_LIST gap: EUR {gap.get('gap_eur', 0):,.0f} "
        f"({100 * gap.get('gap_share_of_parts', 0):.1f}% of CY2025 parts)\n"
        f"4. PMS total capture network CY2025: "
        f"{100 * float(pms25.get('capture_rate') or 0):.1f}% (total primary, not genuine-only)\n"
        f"5. GPS SPU UTI {meta.get('gps', {}).get('uti_spu')} vs UMI {meta.get('gps', {}).get('umi_spu')} "
        "(never blend)\n"
        f"6. UMI ZPR1 YoY 2025->2026 median: {zf.get('umi_yoy_2025_2026_median_pct')}% "
        f"(UTI separate: {zf.get('uti_yoy_2025_2026_median_pct')}%) — investigate composition\n"
        f"7. PRISM verification green: {meta.get('verification', {}).get('ok')}\n"
        "8. MOS = KPI Days of Parts in Stock — NOT market elasticity\n"
        f"9. VPACC open actions: {meta.get('findings_core', {}).get('vpacc', {}).get('open_or_in_progress')}\n"
        "10. Open notes: air-filter interval provisional; brake factors pending IML/ITUK\n\n"
        "Attachments: HTML mega-pack + audit note + key CSVs.\n"
        f"Local HTML: {HTML}\n"
        f"Audit: {AUDIT}\n\n"
        "— ISZE build\n"
    )

    import win32com.client  # type: ignore

    outlook = win32com.client.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(OL_MAIL_ITEM)
    mail.To = TO
    mail.CC = ""
    mail.BCC = ""
    mail.Subject = subject
    mail.Body = body
    mail.Attachments.Add(str(HTML.resolve()))
    for att in (AUDIT, META, NET, MOS, ZPR1, PMS, AIMGPS):
        if att.is_file() and att.stat().st_size < 3_000_000:
            mail.Attachments.Add(str(att.resolve()))

    sent = False
    error = None
    try:
        if str(mail.To).strip().lower() != TO.lower():
            raise RuntimeError(f"Refusing Send: To={mail.To!r} (expected {TO})")
        if mail.CC or mail.BCC:
            raise RuntimeError("Refusing Send: CC/BCC must be empty")
        mail.Send()
        sent = True
    except Exception as e:  # noqa: BLE001
        error = str(e)
        try:
            mail.Save()
        except Exception:  # noqa: BLE001
            pass

    result = {
        "to": TO,
        "cc": "",
        "bcc": "",
        "subject": subject,
        "sent": sent,
        "draft_only": not sent,
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "integrity_score": score,
        "integrity_band": band,
        "audit_verdict": verdict,
        "html": str(HTML),
        "error": error,
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if sent else 1


if __name__ == "__main__":
    raise SystemExit(main())
