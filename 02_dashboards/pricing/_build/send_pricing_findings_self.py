"""Send pricing findings pack to Jerome Isuzu mailbox ONLY (explicit override).

NEVER add other recipients. COM Send allowed for jerome.van.der.pluym@isuzu-e.com only.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ISZE = Path(__file__).resolve().parents[3]
HTML = ISZE / "02_dashboards" / "pricing" / "ISZE_Pricing_History_Findings_Dashboard.html"
META = ISZE / "01_data" / "00_derived" / "pricing_history_findings.meta.json"
NET = ISZE / "01_data" / "00_derived" / "pr00_realization_network_cy.csv"
MOS = ISZE / "01_data" / "00_derived" / "kpi_mos_response_summary_2025_2026.csv"
ZPR1 = ISZE / "01_data" / "00_derived" / "zpr1_vs_pr00_by_payer_year.csv"
RESULT = ISZE / "02_dashboards" / "pricing" / "_build" / "outlook_send_pricing_findings_result.json"

TO = "jerome.van.der.pluym@isuzu-e.com"
OL_MAIL_ITEM = 0


def main() -> int:
    if not HTML.is_file():
        raise SystemExit(f"Missing HTML: {HTML}")
    meta = json.loads(META.read_text(encoding="utf-8")) if META.is_file() else {}
    integ = meta.get("integrity", {})
    score = integ.get("score", "?")
    band = integ.get("band", "?")
    cy25 = next((r for r in meta.get("network", []) if r.get("year") == 2025), {})

    subject = (
        f"Pricing history findings — integrity {score}/100 (provisional QA) — 2026-08-11"
    )
    body = (
        "Jerome,\n\n"
        "Self-mail pack: year-matched PR00 realization + ZPR1 / MOS / NO_LIST / VPACC findings.\n\n"
        f"Integrity score: {score}/100 ({band}) — INTERNAL QA / PROVISIONAL.\n"
        "Do not quote list-to-pocket externally until QA closes.\n\n"
        "Headline (CY2025, matched lines only)\n"
        f"• Realization: {cy25.get('realization_pct', '—')}%\n"
        f"• List coverage: {cy25.get('coverage_pct', '—')}%\n"
        f"• NO_LIST gap: €{meta.get('nolist', {}).get('gap_eur', 0):,.0f} "
        f"({100 * meta.get('nolist', {}).get('gap_share_of_parts', 0):.1f}% of parts)\n\n"
        "Notes\n"
        "• UTI (1799) and UMI (1797) kept separate — never blended.\n"
        "• KPI MOS = Days of Parts in Stock — not market elasticity.\n"
        "• ISZE→DB volume elasticity remains non-quotable.\n\n"
        "Attachments: HTML dashboard + key CSVs.\n"
        f"Local HTML: {HTML}\n\n"
        "— ISZE build\n"
    )

    import win32com.client  # type: ignore

    outlook = win32com.client.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(OL_MAIL_ITEM)
    mail.To = TO
    # Explicit: no CC/BCC
    mail.CC = ""
    mail.BCC = ""
    mail.Subject = subject
    mail.Body = body
    mail.Attachments.Add(str(HTML.resolve()))
    for att in (NET, MOS, ZPR1, META):
        if att.is_file() and att.stat().st_size < 2_000_000:
            mail.Attachments.Add(str(att.resolve()))

    sent = False
    error = None
    try:
        # Explicit self-send override for this task only
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
        "html": str(HTML),
        "error": error,
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if sent else 1


if __name__ == "__main__":
    raise SystemExit(main())
