"""Verify Universe pilot parts pages against the U1 brief table."""
from __future__ import annotations

import html as html_lib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "pages"
ISZE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pilot_dealers as pd_dealers  # noqa: E402

EXPECTED = {
    "P1": dict(part_numbers=1243, bought=12217, returned=3, net_units=12214, value_eur=541917.74, units_without_list_price=1, best_value_units=168, not_yet_classified_units=254),
    "P2": dict(part_numbers=1112, bought=6354, returned=58, net_units=6296, value_eur=334783.16, units_without_list_price=6, best_value_units=135, not_yet_classified_units=176),
    "P3": dict(part_numbers=442, bought=2191, returned=3, net_units=2188, value_eur=107252.01, units_without_list_price=0, best_value_units=124, not_yet_classified_units=21),
    "P4": dict(part_numbers=936, bought=6638, returned=6, net_units=6632, value_eur=395134.85, units_without_list_price=0, best_value_units=207, not_yet_classified_units=115),
    "P5": dict(part_numbers=401, bought=1457, returned=5, net_units=1452, value_eur=93265.41, units_without_list_price=0, best_value_units=52, not_yet_classified_units=28),
    "R6": dict(part_numbers=643, bought=3495, returned=15, net_units=3480, value_eur=211096.30, units_without_list_price=2, best_value_units=229, not_yet_classified_units=133),
    "R7": dict(part_numbers=640, bought=3880, returned=0, net_units=3880, value_eur=185049.00, units_without_list_price=1, best_value_units=144, not_yet_classified_units=99),
    "R8": dict(part_numbers=450, bought=1800, returned=0, net_units=1800, value_eur=126063.86, units_without_list_price=0, best_value_units=66, not_yet_classified_units=65),
}

BANNED = [
    "AIM", "PRISM", "DLOD", "IDS", "GPS", "BVP", "IML", "ITUK", "IUK", "UMI", "UTI",
    "campaign", "sell-out", "sellout", "wallet", "street",
    ".csv", ".json", ".py", "1.785", "1.40", "1.275",
]

# file-name fragments that must not appear
BANNED_FILES = [
    "dealer_sellout", "aim_pn", "pricing_pr00", "bvp_pn", "pilot_pairs",
    "parts_manifest", "build_parts", "check_parts", "pilot_dealers",
]


def visible_text(raw: str) -> str:
    no_script = re.sub(r"<script\b[^>]*>.*?</script>", " ", raw, flags=re.I | re.S)
    no_style = re.sub(r"<style\b[^>]*>.*?</style>", " ", no_script, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", no_style)
    text = html_lib.unescape(text)
    return re.sub(r"\s+", " ", text)


def other_ituk_dealer_names(own: dict) -> list[str]:
    import pandas as pd

    sales = pd.read_csv(
        ISZE / "01_data" / "00_derived" / "dealer_sellout_long_ITUK_CY2025.csv",
        usecols=["dealer_name"],
    )
    names = sorted({str(n) for n in sales["dealer_name"].dropna().unique()})
    own_names = {
        str(own["sales_name"]),
        str(own["ids_name"]),
        str(own["page_name"]),
    }
    # also skip if contained in own names
    out = []
    for n in names:
        if n in own_names:
            continue
        if any(n in o for o in own_names):
            continue
        if any(o in n for o in own_names if len(o) >= 8):
            # skip supersets carefully - brief: skip names contained in the page's own names
            pass
        # skip if this other name is contained in an own name, or an own name is contained in it?
        # "skip names contained in the page's own names"
        if any(n in o for o in own_names):
            continue
        out.append(n)
    return out


def main() -> int:
    man_path = PAGES / "parts_manifest.json"
    if not man_path.exists():
        print("FAIL missing manifest")
        return 1
    man = json.loads(man_path.read_text(encoding="utf-8"))
    by_code = {d["code"]: d for d in man["dealers"]}
    errors: list[str] = []

    for code, exp in EXPECTED.items():
        got = by_code.get(code)
        if not got:
            errors.append(f"{code}: missing from manifest")
            continue
        for k, v in exp.items():
            g = got[k]
            if k == "value_eur":
                if abs(float(g) - float(v)) > 0.01:
                    errors.append(f"{code}.{k}: {g} != {v}")
            else:
                if int(g) != int(v):
                    errors.append(f"{code}.{k}: {g} != {v}")

    ok = 0
    for dealer in pd_dealers.DEALERS:
        code = str(dealer["code"])
        folder = pd_dealers.pages_dir_for(dealer, PAGES)
        html_path = folder / "Parts_2025.html"
        cmd_path = folder / "OPEN_Parts_2025.cmd"
        if not html_path.exists():
            errors.append(f"{code}: missing html")
            continue
        if not cmd_path.exists():
            errors.append(f"{code}: missing open cmd")
            continue
        raw = html_path.read_text(encoding="utf-8")
        pn_rows = len(re.findall(r'<tr\s+class="pn"', raw))
        exp_pn = EXPECTED[code]["part_numbers"]
        if pn_rows != exp_pn:
            errors.append(f"{code}: pn rows {pn_rows} != {exp_pn}")

        vis = visible_text(raw)
        for term in BANNED:
            if term in ("IUK", "UMI", "UTI", "IDS", "GPS", "BVP", "IML", "AIM", "DLOD", "PRISM", "ITUK"):
                # whole-word-ish for short acronyms
                if re.search(rf"(?<![A-Za-z0-9]){re.escape(term)}(?![A-Za-z0-9])", vis):
                    errors.append(f"{code}: banned term {term!r} in visible text")
            else:
                if term.lower() in vis.lower() if term.islower() or term.startswith(".") or term[0].isdigit() else term in vis:
                    # case handling
                    if term.startswith(".") or term[0].isdigit() or term.islower():
                        if term.lower() in vis.lower():
                            errors.append(f"{code}: banned term {term!r} in visible text")
                    elif term in vis:
                        errors.append(f"{code}: banned term {term!r} in visible text")

        for frag in BANNED_FILES:
            if frag in vis:
                errors.append(f"{code}: file fragment {frag!r} in visible text")

        for name in other_ituk_dealer_names(dealer):
            if name in vis or html_lib.escape(name) in raw:
                # skip if name is substring of own page/ids/sales
                own = [str(dealer["sales_name"]), str(dealer["ids_name"]), str(dealer["page_name"])]
                if any(name in o for o in own):
                    continue
                errors.append(f"{code}: other dealer name present: {name}")
                break

        for m in re.finditer(r"""\b(?:src|href)\s*=\s*["']([^"']+)["']""", raw, flags=re.I):
            if "http" in m.group(1).lower():
                errors.append(f"{code}: http in {m.group(0)}")

        for bad in ("NaN", "undefined", "null"):
            if re.search(rf"(?<![A-Za-z0-9]){bad}(?![A-Za-z0-9])", vis):
                errors.append(f"{code}: {bad} in visible text")

        cmd_bytes = cmd_path.read_bytes()
        if b"\r\n" not in cmd_bytes:
            errors.append(f"{code}: OPEN not CRLF")
        if b"Parts_2025.html" not in cmd_bytes:
            errors.append(f"{code}: OPEN does not name Parts_2025.html")

        if not any(e.startswith(f"{code}:") for e in errors):
            ok += 1

    if errors:
        print("FAIL")
        for e in errors[:50]:
            print(" -", e)
        if len(errors) > 50:
            print(f" ... +{len(errors)-50} more")
        return 1

    print(f"PARTS_PAGES_OK {ok}/8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())