#!/usr/bin/env python3
"""Patch feedback packs: max-point good/bad per section A–E."""

from __future__ import annotations

from pathlib import Path

P = Path(__file__).resolve().parent / "build_ids_dealer_feedback.py"


HELPER = '''
def max_point_section_highlights(country: str, name: str) -> tuple[list[dict], list[dict]]:
    """Per section A–E: good = full score on a max-point item; bad = zero. Prefer higher max."""
    from build_ids_result_report import (
        COL_FIRST_DEALER,
        COL_MAX,
        COL_TEXT,
        QUESTION_RE,
        ROW_META_START,
        load_matrix_rows_from_sheet,
    )
    from ids_paths import result_report_path
    import xlrd

    path = result_report_path(country)
    if not path.is_file():
        return [], []
    rb = xlrd.open_workbook(str(path))
    sh = rb.sheet_by_index(0)
    col = None
    for c in range(COL_FIRST_DEALER, sh.ncols):
        nm = str(sh.cell_value(ROW_META_START, c) or "").strip()
        if nm.casefold() == name.casefold():
            col = c
            break
    if col is None:
        return [], []
    matrix = load_matrix_rows_from_sheet(sh)
    current_sec = None
    by_sec: dict[str, dict[str, list]] = {}
    for row in matrix:
        ref = (row.ref or "").strip()
        if row.kind == "category":
            m = re.match(r"^([A-E])\\.", ref, re.I)
            current_sec = m.group(1).upper() if m else None
            continue
        if row.kind != "question" or row.sheet_row is None or not current_sec:
            continue
        if not QUESTION_RE.match(ref):
            continue
        max_pts = row.max_points or float(sh.cell_value(row.sheet_row, COL_MAX) or 0) or 0.0
        try:
            score = float(sh.cell_value(row.sheet_row, col))
        except (TypeError, ValueError):
            continue
        if max_pts <= 0:
            continue
        text = (row.text or str(sh.cell_value(row.sheet_row, COL_TEXT) or "")).strip()
        item = {
            "id": ref,
            "section": current_sec,
            "text": text[:120],
            "score": score,
            "max": max_pts,
            "pct": score / max_pts,
            "gap": None,
            "band": "good" if abs(score - max_pts) < 0.05 else ("bad" if score < 0.05 else "medium"),
        }
        bucket = by_sec.setdefault(current_sec, {"good": [], "bad": []})
        if abs(score - max_pts) < 0.05:
            bucket["good"].append(item)
        if score < 0.05:
            bucket["bad"].append(item)
    strengths: list[dict] = []
    weaks: list[dict] = []
    for sec in SECTIONS:
        g = sorted(by_sec.get(sec, {}).get("good", []), key=lambda x: (-x["max"], x["id"]))
        b = sorted(by_sec.get(sec, {}).get("bad", []), key=lambda x: (-x["max"], x["id"]))
        if g:
            strengths.append(g[0])
        if b:
            weaks.append(b[0])
    return strengths, weaks

'''


def main() -> None:
    t = P.read_text(encoding="utf-8")
    if "def max_point_section_highlights" not in t:
        # insert after section_rows
        anchor = "def needs_deep(dealer: dict, rows: list[dict]) -> bool:"
        if anchor not in t:
            raise SystemExit("anchor missing")
        t = t.replace(anchor, HELPER + "\n" + anchor)

    old = """    strengths = sorted([r for r in rows if r["gap"] is not None and r["gap"] > 0], key=lambda r: -r["gap"])[:3]
    weaks = sorted([r for r in rows if r["gap"] is not None and r["gap"] < 0], key=lambda r: r["gap"])[:3]"""
    new = """    strengths, weaks = max_point_section_highlights(country, name)
    if not strengths and not weaks:
        # fallback: section gaps if question extract empty (totals-only packs)
        strengths = sorted([r for r in rows if r["gap"] is not None and r["gap"] > 0], key=lambda r: -r["gap"])[:3]
        weaks = sorted([r for r in rows if r["gap"] is not None and r["gap"] < 0], key=lambda r: r["gap"])[:3]"""
    if old not in t:
        if "max_point_section_highlights(country, name)" in t:
            print("render already patched")
        else:
            raise SystemExit("strengths block missing")
    else:
        t = t.replace(old, new)

    # Callout list formatting for question items
    old_li = """    strength_li = "".join(
        f"<li><strong>{r['id']}</strong> {_pp(r['gap'])} vs country · {band_label(r['band'])}</li>"
        for r in strengths
    ) or "<li>None above country average.</li>"
    weak_li = "".join(
        f"<li><strong>{r['id']}</strong> {_pp(r['gap'])} vs country · {band_label(r['band'])}</li>"
        for r in weaks
    ) or "<li>None below country average.</li>" """
    # Flexible replace of the two join blocks
    t = t.replace(
        "f\"<li><strong>{r['id']}</strong> {_pp(r['gap'])} vs country · {band_label(r['band'])}</li>\"\n"
        "        for r in strengths",
        "f\"<li><strong>{r.get('id') or r.get('ref')}</strong> "
        "{(str(int(r['score']))+'/'+str(int(r['max']))+' (full)') if r.get('max') and r.get('band')=='good' else (_pp(r.get('gap'))+' vs country')} "
        "· {band_label(r.get('band'))}</li>\"\n"
        "        for r in strengths",
    )
    t = t.replace(
        "f\"<li><strong>{r['id']}</strong> {_pp(r['gap'])} vs country · {band_label(r['band'])}</li>\"\n"
        "        for r in weaks",
        "f\"<li><strong>{r.get('id') or r.get('ref')}</strong> "
        "{('0/'+str(int(r['max']))) if r.get('max') and r.get('band')=='bad' else (_pp(r.get('gap'))+' vs country')} "
        "· {band_label(r.get('band'))}</li>\"\n"
        "        for r in weaks",
    )

    # COUNTRY_MAP keys for new labels — alias lookup
    if 'country_display_name' not in t.split('load_db_kpi')[0]:
        pass
    if "country_display_name" not in t:
        t = t.replace(
            "from ids_paths import",
            "from ids_paths import country_display_name,",
            1,
        ) if "from ids_paths import" in t else t

    P.write_text(t, encoding="utf-8")
    print("feedback max-point highlights patched")


if __name__ == "__main__":
    main()
