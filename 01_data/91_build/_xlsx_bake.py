"""Bake openpyxl formulas with Excel, and export selected sheets for visual QA.

openpyxl writes a formula but cannot compute it, so a formula-only workbook shows
blank total cells until someone opens it in Excel. This module drives Excel through
COM to recalculate and re-save the file, which stores the calculated value alongside
the formula. After that the workbook reads correctly in any viewer and the formulas
stay live.

COM is optional: if Excel is not installed, :func:`bake` returns ``ok=False`` with a
reason instead of raising, so a build can still finish and report the limitation.

Usage::

    from _xlsx_bake import bake, export_pdf

    result = bake(path)
    if not result["ok"]:
        print("totals will read blank until Excel opens the file:", result["error"])
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Sequence

__all__ = ["bake", "export_pdf", "excel_available"]

XL_CALC_AUTOMATIC = -4105
XL_TYPE_PDF = 0


def _dispatch():
    import win32com.client  # imported here so the module loads without pywin32

    return win32com.client


def excel_available() -> tuple[bool, str]:
    """(available, reason). Safe to call on a machine without Excel or pywin32."""
    try:
        client = _dispatch()
    except Exception as exc:  # pragma: no cover - environment dependent
        return False, f"pywin32 import failed: {exc}"
    app = None
    try:
        app = client.DispatchEx("Excel.Application")
        version = app.Version
        return True, f"Excel {version}"
    except Exception as exc:  # pragma: no cover - environment dependent
        return False, f"Excel COM unavailable: {exc}"
    finally:
        if app is not None:
            try:
                app.Quit()
            except Exception:
                pass


def bake(path: Path, *, timeout_s: int = 600) -> dict:
    """Recalculate every formula in ``path`` with Excel and re-save in place.

    Returns ``{"ok": bool, "seconds": float, "error": str | None}``. Never raises for
    an Excel-side problem; the caller reports the limitation instead of shipping a
    silent blank.
    """
    path = Path(path)
    if not path.is_file():
        return {"ok": False, "seconds": 0.0, "error": f"not found: {path}"}
    try:
        client = _dispatch()
    except Exception as exc:
        return {"ok": False, "seconds": 0.0, "error": f"pywin32 import failed: {exc}"}

    started = time.time()
    # "Call was rejected by callee" is Excel refusing a call while it is still busy
    # starting or shutting down. Retrying after a pause clears it, so the build does not
    # ship a file whose totals read blank over a transient COM state.
    last_error = None
    for attempt in range(4):
        app = None
        book = None
        try:
            app = client.DispatchEx("Excel.Application")
            app.Visible = False
            app.DisplayAlerts = False
            book = app.Workbooks.Open(str(path), UpdateLinks=0)
            # Calculation mode is set after open: on some installs the property cannot
            # be set on a freshly created instance before a workbook exists.
            try:
                app.Calculation = XL_CALC_AUTOMATIC
            except Exception:
                pass
            app.CalculateFullRebuild()
            book.Save()
            return {"ok": True, "seconds": round(time.time() - started, 1),
                    "error": None, "attempts": attempt + 1}
        except Exception as exc:
            last_error = str(exc)
        finally:
            if book is not None:
                try:
                    book.Close(SaveChanges=False)
                except Exception:
                    pass
            if app is not None:
                try:
                    app.Quit()
                except Exception:
                    pass
        time.sleep(2.0 + 2.0 * attempt)
    return {"ok": False, "seconds": round(time.time() - started, 1),
            "error": last_error, "attempts": 4}


def export_pdf(path: Path, out_pdf: Path, sheets: Sequence[str]) -> dict:
    """Export the named sheets to one PDF, for visual QA only.

    Only the named sheets are selected, so a very long detail sheet is left out and
    the QA file stays a handful of pages.
    """
    path = Path(path)
    out_pdf = Path(out_pdf)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    try:
        client = _dispatch()
    except Exception as exc:
        return {"ok": False, "error": f"pywin32 import failed: {exc}"}

    app = None
    book = None
    try:
        app = client.DispatchEx("Excel.Application")
        app.Visible = False
        app.DisplayAlerts = False
        book = app.Workbooks.Open(str(path), UpdateLinks=0)
        missing = [s for s in sheets if s not in [ws.Name for ws in book.Worksheets]]
        if missing:
            return {"ok": False, "error": f"sheets not in workbook: {missing}"}
        book.Worksheets(list(sheets)).Select()
        app.ActiveSheet.ExportAsFixedFormat(Type=XL_TYPE_PDF, Filename=str(out_pdf),
                                           Quality=0, IncludeDocProperties=True,
                                           IgnorePrintAreas=False, OpenAfterPublish=False)
        return {"ok": True, "error": None, "pdf": str(out_pdf)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
    finally:
        if book is not None:
            try:
                book.Close(SaveChanges=False)
            except Exception:
                pass
        if app is not None:
            try:
                app.Quit()
            except Exception:
                pass
