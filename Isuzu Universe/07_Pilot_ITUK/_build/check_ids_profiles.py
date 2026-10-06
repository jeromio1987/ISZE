"""Verify the Dealer Standards 2026 profile pages against the U2 brief."""
from __future__ import annotations

import html as html_lib
import json
import re
import sys
from pathlib import Path

BUILD = Path(__file__).resolve().parent
ROOT = BUILD.parent
PAGES = ROOT / "pages"
sys.path.insert(0, str(BUILD))
import pilot_dealers as pd_dealers  # noqa: E402
from build_ids_profiles import read_workbook  # noqa: E402

PAGE = "Dealer_Standards_2026.html"
OPEN = "OPEN_Dealer_Standards_2026.cmd"

EXPECTED = {
    "P1": (195, 18, 5, 0, 1, 219),
    "P2": (198, 11, 0, 0, 10, 219),
    "P3": (213, 5, 1, 0, 0, 219),
    "P4": (218, 1, 0, 0, 0, 219),
    "P5": (196, 10, 12, 0, 1, 219),
    "R6": (201, 5, 10, 2, 1, 219),
    "R7": (210, 7, 0, 0, 2, 219),
    "R8": (214, 5, 0, 0, 0, 219),
}
KEYS = ("meets", "does_not_meet", "own_words", "not_applicable", "no_answer", "total")

ACRONYMS = ["AIM", "PRISM", "DLOD", "IDS", "GPS", "BVP", "IML", "ITUK", "IUK", "UMI", "UTI"]
WORDS = ["campaign", "sell-out", "sellout", "wallet", ".csv", ".json", ".py", ".xlsx"]
FILE_FRAGMENTS = [
    "self evaluations", "pilot_dealers", "build_ids", "check_ids", "ids_manifest",
    "Dealer_Standards_2026", "parts_manifest",
]


def strip_blocks(raw: str) -> str:
    raw = re.sub(r"<script\b[^>]*>.*?</script>", " ", raw, flags=re.I | re.S)
    return re.sub(r"<style\b[^>]*>.*?</style>", " ", raw, flags=re.I | re.S)


def to_text(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", " ", fragment)
    return re.sub(r"\s+", " ", html_lib.unescape(text))


def visible_text(raw: str) -> str:
    return to_text(strip_blocks(raw))


def visible_outside_verbatim(raw: str) -> str:
    body = strip_blocks(raw)
    body = re.sub(r'<td class="verbatim"[^>]*>.*?</td>', " ", body, flags=re.S)
    return to_text(body)


def main() -> int:
    errors: list[str] = []
    questions, dealer_cols, all_names = read_workbook()

    man_path = PAGES / "ids_manifest.json"
    if not man_path.exists():
        print("FAIL missing ids_manifest.json")
        return 1
    man = json.loads(man_path.read_text(encoding="utf-8"))
    by_code = {d["code"]: d for d in man["dealers"]}
    if set(by_code) != set(EXPECTED):
        errors.append(f"manifest codes {sorted(by_code)} != {sorted(EXPECTED)}")
    for code, exp in EXPECTED.items():
        got = by_code.get(code, {})
        for k, v in zip(KEYS, exp):
            if got.get(k) != v:
                errors.append(f"{code}.{k}: {got.get(k)} != {v}")

    ok = 0
    for dealer in pd_dealers.DEALERS:
        code = str(dealer["code"])
        before = len(errors)
        folder = pd_dealers.pages_dir_for(dealer, PAGES)
        page, cmd = folder / PAGE, folder / OPEN
        if not page.exists() or not cmd.exists():
            errors.append(f"{code}: missing page or OPEN file")
            continue
        raw = page.read_text(encoding="utf-8")

        q_rows = re.findall(r'<tr class="q">(.*?)</tr>', raw, flags=re.S)
        if len(q_rows) != 219:
            errors.append(f"{code}: {len(q_rows)} question rows, expected 219")
        # Question numbers repeat on the sheet (D.1-2, D.2-11), so rows are paired in order.
        for q, row in zip(questions, q_rows):
            cells = re.findall(r"<td[^>]*>(.*?)</td>", row, flags=re.S)
            if len(cells) < 2 or cells[0] != html_lib.escape(q["number"]):
                errors.append(f"{code}: row order differs at {q['number']}")
            elif cells[1] != html_lib.escape(q["wording"]):
                errors.append(f"{code}: wording differs for {q['number']}")

        vis = visible_text(raw)
        outside = visible_outside_verbatim(raw)
        # Banned commercial words and acronyms are allowed inside class="verbatim"
        # cells (question wording and answers), the same way "%" already is.
        # C.3-12 on the sheet contains the word "campaigns".
        for term in ACRONYMS:
            if re.search(rf"(?<![A-Za-z0-9]){term}(?![A-Za-z0-9])", outside):
                errors.append(f"{code}: banned term {term!r}")
        for term in WORDS:
            if term in outside.lower():
                errors.append(f"{code}: banned term {term!r}")
        for frag in FILE_FRAGMENTS:
            if frag.lower() in vis.lower():
                errors.append(f"{code}: file name fragment {frag!r}")

        if "%" in outside:
            errors.append(f"{code}: % outside verbatim cells")

        own = str(dealer["page_name"])
        for name in all_names:
            if name == str(dealer["ids_name"]) or name in own or name in str(dealer["ids_name"]):
                continue
            if name in raw or html_lib.escape(name) in raw:
                errors.append(f"{code}: other dealer name present: {name}")

        for m in re.finditer(r"""\b(?:src|href)\s*=\s*["']([^"']*)["']""", raw, flags=re.I):
            if "http" in m.group(1).lower():
                errors.append(f"{code}: http in {m.group(0)}")

        for bad in ("NaN", "undefined", "null"):
            if re.search(rf"(?<![A-Za-z0-9]){bad}(?![A-Za-z0-9])", vis):
                errors.append(f"{code}: {bad!r} in visible text")

        cmd_bytes = cmd.read_bytes()
        if b"\r\n" not in cmd_bytes or re.search(rb"(?<!\r)\n", cmd_bytes):
            errors.append(f"{code}: OPEN file is not CRLF")
        if PAGE.encode() not in cmd_bytes:
            errors.append(f"{code}: OPEN file does not name {PAGE}")

        if len(errors) == before:
            ok += 1

    if errors:
        print("FAIL")
        for e in errors[:60]:
            print(" -", e)
        if len(errors) > 60:
            print(f" ... +{len(errors) - 60} more")
        return 1
    print(f"IDS_PROFILES_OK {ok}/8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
