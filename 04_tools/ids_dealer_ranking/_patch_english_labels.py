#!/usr/bin/env python3
"""One-shot patch: English country labels + display helpers for IDS builders."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent


def patch_midi() -> None:
    p = ROOT / "midi_fr_ranking.py"
    t = p.read_text(encoding="utf-8")
    old = '''MIDI_COUNTRY_LABELS: dict[str, str] = {
    "FR": "MIDI_FR",
    "IT": "MIDI_IT",
    "CH": "MIDI_CH",
    "ES": "MIDI_ES",
}'''
    new = '''MIDI_COUNTRY_LABELS: dict[str, str] = {
    "FR": "France",
    "IT": "Italy",
    "CH": "Switzerland",
    "ES": "Spain",
}'''
    if old not in t:
        if "Switzerland" in t:
            print("midi: already patched")
            return
        raise SystemExit("midi: block not found")
    p.write_text(t.replace(old, new), encoding="utf-8")
    print("midi: ok")


def patch_result_report() -> None:
    p = ROOT / "build_ids_result_report.py"
    t = p.read_text(encoding="utf-8")
    if "country_display_name" not in t.split("from ids_paths")[1][:400]:
        t = t.replace(
            "from ids_paths import DATA_ROOT, resolve_dk_template, resolve_input_dir, result_report_delta_path, result_report_path",
            "from ids_paths import (\n"
            "    DATA_ROOT,\n"
            "    country_display_name,\n"
            "    resolve_dk_template,\n"
            "    resolve_input_dir,\n"
            "    result_report_delta_path,\n"
            "    result_report_path,\n"
            ")",
        )
    t = t.replace("ws.write(row, 0, country.upper())", "ws.write(row, 0, country_display_name(country))")
    t = t.replace('f"Country  {country.upper()}"', 'f"Country  {country_display_name(country)}"')
    t = t.replace('f"{country}26_Delta"', 'f"{country_display_name(country)}26_Delta"')
    t = t.replace('f"{country}26"', 'f"{country_display_name(country)}26"')
    old_ituk = '    elif country.upper() == "ITUK":'
    new_ituk = '    elif country_display_name(country) == "UK (ITUK)" or country.upper() == "ITUK":'
    t = t.replace(old_ituk, new_ituk)
    p.write_text(t, encoding="utf-8")
    print("result_report: ok", t.count("country_display_name"))


def patch_extract() -> None:
    p = ROOT / "ids_report_extract.py"
    t = p.read_text(encoding="utf-8")
    if "from ids_paths import country_display_name" not in t:
        t = t.replace(
            "from build_ids_result_report import (",
            "from ids_paths import country_display_name\nfrom build_ids_result_report import (",
        )
    old = '''def _country_from_sheet(sh) -> str:
    line = str(sh.cell_value(ROW_COUNTRY, COL_LABEL)).strip()
    if line.lower().startswith("country"):
        return line.split(None, 1)[-1].strip()
    return line


def _country_from_filename(path: Path) -> str:
    stem = path.stem
    if stem.startswith(REPORT_PREFIX):
        return stem[len(REPORT_PREFIX) :]
    return stem'''
    new = '''def _country_from_sheet(sh) -> str:
    line = str(sh.cell_value(ROW_COUNTRY, COL_LABEL)).strip()
    if line.lower().startswith("country"):
        raw = line.split(None, 1)[-1].strip()
        return country_display_name(raw)
    return country_display_name(line)


def _country_from_filename(path: Path) -> str:
    stem = path.stem
    if stem.startswith(REPORT_PREFIX):
        return country_display_name(stem[len(REPORT_PREFIX) :])
    return country_display_name(stem)'''
    if old in t:
        t = t.replace(old, new)
        print("extract: country parsers patched")
    elif "return country_display_name(raw)" in t:
        print("extract: country parsers already patched")
    else:
        print("extract: WARNING country parsers unexpected")

    old_disc = '''def discover_result_reports(reports_dir: Path) -> list[Path]:
    if not reports_dir.is_dir():
        return []
    return sorted(
        p
        for p in reports_dir.glob(f"{REPORT_PREFIX}*{REPORT_SUFFIX}")
        if p.is_file() and "_Delta" not in p.name and " - Copy" not in p.name
    )'''
    new_disc = '''def discover_result_reports(reports_dir: Path) -> list[Path]:
    """List country result .xls files, preferring English-named files over legacy codes."""
    if not reports_dir.is_dir():
        return []
    candidates = [
        p
        for p in reports_dir.glob(f"{REPORT_PREFIX}*{REPORT_SUFFIX}")
        if p.is_file() and "_Delta" not in p.name and " - Copy" not in p.name
    ]
    best: dict[str, Path] = {}
    for path in candidates:
        label = country_display_name(path.stem[len(REPORT_PREFIX) :])
        stem_label = path.stem[len(REPORT_PREFIX) :]
        prev = best.get(label)
        if prev is None:
            best[label] = path
            continue
        prev_stem = prev.stem[len(REPORT_PREFIX) :]
        if stem_label == label and prev_stem != label:
            best[label] = path
        elif stem_label != label and prev_stem != label and path.name < prev.name:
            best[label] = path
    return sorted(best.values(), key=lambda p: p.name.casefold())'''
    if old_disc in t:
        t = t.replace(old_disc, new_disc)
        print("extract: discover patched")
    elif "preferring English-named" in t:
        print("extract: discover already patched")
    else:
        print("extract: WARNING discover unexpected")

    p.write_text(t, encoding="utf-8")
    print("extract: ok")


def patch_feedback() -> None:
    p = ROOT / "build_ids_dealer_feedback.py"
    if not p.is_file():
        print("feedback: missing — skip")
        return
    t = p.read_text(encoding="utf-8")
    t = t.replace('"Goed"', '"Good"').replace('"Slecht"', '"Bad"')
    t = t.replace("Strengths (goed)", "Strengths (good)")
    t = t.replace("Weak points (slecht)", "Weak points (bad)")
    t = t.replace("weak wedges = slecht", "weak wedges = bad")
    t = t.replace("section slecht", "section bad")
    t = t.replace("no slecht section", "no bad section")
    t = t.replace("'slecht'", "'bad'")
    p.write_text(t, encoding="utf-8")
    print("feedback: ok")


def main() -> None:
    patch_midi()
    patch_result_report()
    patch_extract()
    patch_feedback()
    # verify
    from ids_paths import country_display_name
    from midi_fr_ranking import MIDI_COUNTRY_LABELS

    assert MIDI_COUNTRY_LABELS["CH"] == "Switzerland"
    assert country_display_name("MIDI_CH") == "Switzerland"
    print("verify: ok")


if __name__ == "__main__":
    main()
