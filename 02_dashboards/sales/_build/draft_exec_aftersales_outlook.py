"""Create ONE Outlook draft for the ISZE exec aftersales paper. Save — do NOT Send.

Attaches ISZE_Exec_Aftersales_Paper.html (+ optional OPEN_*.cmd launcher).
Default: draft to Jerome (self) so he can set To/CC before sending.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import win32com.client
except ImportError:
    print("win32com not available — run this script on Jerome's Windows PC with Outlook open.", flush=True)
    sys.exit(1)

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
SALES = ISZE / "02_dashboards" / "sales"
HTML = SALES / "ISZE_Exec_Aftersales_Paper.html"
LAUNCHER = SALES / "OPEN_ISZE_Exec_Aftersales_Paper.cmd"
OUT = SALES / "_build" / "outlook_draft_exec_aftersales_result.json"

TO_DEFAULT = "jerome.van.der.pluym@isuzu-e.com"
SUBJECT = "ISZE aftersales — opportunity and commercialisation (16-page paper)"

BODY = """Hi Bart,

Please find attached the aftersales commercialisation paper (16 pages, printable HTML).

The short read:
- CY2025 we billed €30.8M against a €60.2M target-spend ceiling (51.1%). About 37% of that ceiling is a flat €250/UIO placeholder, so the cover headline moves to 29–44% under realistic alternatives.
- The largest quotable component gaps are clutch disc €3.14M, brake pad €2.78M and brake shoe €2.47M (€8.39M of an €18.22M basket gap). The UK-truck oil-filter story is a method illustration only.
- Eucon gross margin at risk on the scraped set is €2.21M (44 part numbers). Book B alloc ambition and no-list ownership are the ready levers already on the table.
- Independent workshop unit volume remains unknown. The paper states that explicitly rather than inferring it from PMS residual.

Open the HTML attachment directly in your browser. It paints offline; no server needed. If you have the full sales folder, the OPEN_ISZE_Exec_Aftersales_Paper.cmd launcher sits next to the HTML.

Happy to walk through pages 1, 4 and 14 if useful.

Thx,
Jerome
"""


def log(msg: str) -> None:
    print(msg, flush=True)


def main() -> None:
    if not HTML.exists():
        raise SystemExit(f"missing {HTML}")

    outlook = win32com.client.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(0)
    mail.To = TO_DEFAULT
    mail.Subject = SUBJECT
    mail.Body = BODY
    mail.BodyFormat = 1  # olFormatPlain

    mail.Attachments.Add(str(HTML))
    log(f"ATTACH {HTML.name}")
    if LAUNCHER.exists():
        mail.Attachments.Add(str(LAUNCHER))
        log(f"ATTACH {LAUNCHER.name}")

    mail.Save()
    try:
        mail.Display(False)
    except Exception as exc:  # noqa: BLE001
        log(f"DISPLAY warn {exc}")

    result = {
        "status": "draft_saved_not_sent",
        "saved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "to": str(getattr(mail, "To", "") or ""),
        "cc": str(getattr(mail, "CC", "") or ""),
        "subject": str(getattr(mail, "Subject", "") or ""),
        "attachments": [HTML.name] + ([LAUNCHER.name] if LAUNCHER.exists() else []),
        "html_path": str(HTML),
        "draft_only": True,
        "sent": False,
        "note": "Save only. Jerome sends. Edit To/CC before sending.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    log("DRAFT SAVED (not sent)")
    log(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
