"""The guided flow.

Everything has a default, and Enter accepts it, so a colleague can build a deck without
knowing anything about the workspace. Answers are written to a YAML file next to the output,
so the same configuration can be replayed next month with --answers.

Ctrl+C at any prompt cancels cleanly and writes nothing.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import yaml

from . import blocks as block_defs
from .checks import preflight as preflight_mod
from .config import DistConfig, list_keys, load
from .errors import BprError
from .paths import MEETINGS_DIR, output_dir
from .periods import current_fy

ANSWER_VERSION = 1

THEME_CHOICES = [
    ("charcoal", "Charcoal dark - the I Motors / Astara look"),
    ("light", "Light - the house style for shared decks"),
]

WORDING_CHOICES = [
    ("shared", "Shared - safe to show the distributor or management"),
    ("internal", "Internal - our own blunt wording and internal labels"),
]

BASIS_CHOICES = [
    ("fiscal", "Fiscal year, April to March (this is our default)"),
    ("calendar", "Calendar year, January to December"),
]


class Cancelled(Exception):
    """The person pressed Ctrl+C. Nothing is written."""


# ------------------------------------------------------------------ prompt helpers

def _print(text: str = "") -> None:
    print(text)


def _ask(prompt: str, default: str | None = None, allow_blank: bool = False) -> str:
    shown = f" [{default}]" if default not in (None, "") else ""
    while True:
        try:
            raw = input(f"{prompt}{shown}: ").strip()
        except (EOFError, KeyboardInterrupt):
            raise Cancelled()
        if not raw:
            if default not in (None, ""):
                return str(default)
            if allow_blank:
                return ""
            _print("   Please type something, or press Ctrl+C to stop.")
            continue
        return raw


def _ask_int(prompt: str, default: int | None = None, low: int | None = None,
             high: int | None = None) -> int:
    while True:
        raw = _ask(prompt, str(default) if default is not None else None)
        try:
            value = int(raw)
        except ValueError:
            _print("   That needs to be a whole number.")
            continue
        if low is not None and value < low:
            _print(f"   Needs to be {low} or more.")
            continue
        if high is not None and value > high:
            _print(f"   Needs to be {high} or less.")
            continue
        return value


def _ask_yes(prompt: str, default: bool = True) -> bool:
    shown = "Y/n" if default else "y/N"
    while True:
        try:
            raw = input(f"{prompt} [{shown}]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            raise Cancelled()
        if not raw:
            return default
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        _print("   Please answer y or n.")


def _ask_lines(prompt: str, help_text: str = "one per line, blank line when you are done") -> list[str]:
    _print(f"{prompt}  ({help_text})")
    out: list[str] = []
    while True:
        try:
            raw = input("   > ").strip()
        except (EOFError, KeyboardInterrupt):
            raise Cancelled()
        if not raw:
            return out
        out.append(raw)


def _choose(title: str, choices: list[tuple[str, str]], default_key: str | None = None) -> str:
    _print()
    _print(title)
    default_index = 1
    for i, (key, label) in enumerate(choices, 1):
        mark = ""
        if default_key and key == default_key:
            default_index = i
            mark = "   <- default"
        _print(f"  {i:>2}. {label}{mark}")
    while True:
        raw = _ask("  Number", str(default_index))
        try:
            index = int(raw)
        except ValueError:
            _print("   Type the number next to your choice.")
            continue
        if 1 <= index <= len(choices):
            return choices[index - 1][0]
        _print(f"   Between 1 and {len(choices)}.")


# ------------------------------------------------------------------ the flow

def run(
    *,
    preset_db: str | None = None,
    preset: dict | None = None,
    skip_preflight_print: bool = False,
) -> dict:
    """Ask everything and return the answer set. Raises Cancelled if the person stops."""
    preset = preset or {}
    _print()
    _print("=" * 78)
    _print("  ISZE distributor business review - deck generator")
    _print("=" * 78)
    _print()

    # ---------------------------------------------------------- 1. distributor
    keys = list_keys()
    if not keys:
        raise BprError("E101", "No distributors are configured at all.",
                       expected="entries under 'distributors:' in the settings file")

    db_key = preset.get("db") or preset_db
    if db_key:
        db_key = str(db_key).upper()
        if db_key not in keys:
            raise BprError("E101", f"'{db_key}' is not a configured distributor.", db=db_key,
                           expected=", ".join(keys), found=db_key)
        _print(f"  Distributor: {db_key} (from the command line)")
    else:
        _print("  Which distributor is this deck for?")
        counts: dict[str, tuple[int, int]] = {}
        rows = []
        for i, key in enumerate(keys, 1):
            try:
                dist = load(key)
                ctx = _quick_context(dist)
                ready, total = ctx.buildable_count()
            except BprError:
                ready, total = 0, len(block_defs.BLOCKS)
            counts[key] = (ready, total)
            rows.append(f"  {i:>3}. {dist.display:<18} {dist.country:<16} {ready} of {total} slides available")
        for row in rows:
            _print(row)
        while True:
            raw = _ask("  Number", "1")
            try:
                index = int(raw)
            except ValueError:
                _print("   Type the number next to the distributor.")
                continue
            if 1 <= index <= len(keys):
                db_key = keys[index - 1]
                break
            _print(f"   Between 1 and {len(keys)}.")

    dist = load(db_key)

    # ---------------------------------------------------------- 2. preflight
    ctx = _quick_context(dist)
    pf = preflight_mod.run(ctx)
    if not skip_preflight_print:
        preflight_mod.print_report(pf)
    else:
        _print(f"  {pf.summary_line()}")

    if not pf.numbers_ok:
        _print("  The shared numbers are not verified.")
        if not _ask_yes("  Build anyway, for layout only, not for presenting?", default=False):
            raise Cancelled()

    # ---------------------------------------------------------- 3. period
    _print()
    basis = preset.get("period_basis") or _choose(
        "Which period should the deck cover?", BASIS_CHOICES, "fiscal")
    default_year = current_fy() if basis == "fiscal" else date.today().year
    year = int(preset.get("period_year") or _ask_int(
        f"  {'Fiscal' if basis == 'fiscal' else 'Calendar'} year", default_year, 2020, 2035))

    if preset.get("through_month"):
        through = int(preset["through_month"])
    else:
        _print("  Through which month? The deck stops at the last month with data.")
        _print("    1=Jan  2=Feb  3=Mar  4=Apr  5=May  6=Jun  7=Jul  8=Aug  9=Sep  10=Oct  11=Nov  12=Dec")
        _print("    Type 0 for the whole year.")
        through_raw = _ask_int("  Month", 0, 0, 12)
        through = None if through_raw == 0 else through_raw

    # ---------------------------------------------------------- 4. blocks
    _print()
    _print("  Which slide blocks should the deck include?")
    available_rows = [b for b in pf.blocks if b["available"]]
    unavailable_rows = [b for b in pf.blocks if not b["available"]]

    preset_sections = preset.get("sections")
    if preset_sections:
        chosen = [s for s in preset_sections if s in block_defs.BLOCK_KEYS]
        _print("  Using the blocks from the answers file: " + ", ".join(chosen))
    elif _ask_yes("  Include every available block?", default=True):
        chosen = [b["key"] for b in available_rows if b["default_on"]]
    else:
        _print("  Type the numbers to include, separated by commas (for example 1,2,5).")
        for i, row in enumerate(pf.blocks, 1):
            state = "available" if row["available"] else "not possible"
            _print(f"  {i:>2}. [{state:<12}] {row['label']}")
            _print(f"      {row['needs']}")
        raw = _ask("  Numbers", ",".join(str(i) for i, r in enumerate(pf.blocks, 1)
                                         if r["available"] and r["default_on"]))
        chosen = []
        for token in raw.replace(";", ",").split(","):
            token = token.strip()
            if not token.isdigit():
                continue
            index = int(token)
            if 1 <= index <= len(pf.blocks):
                key = pf.blocks[index - 1]["key"]
                if pf.blocks[index - 1]["available"] and key not in chosen:
                    chosen.append(key)
        if not chosen:
            _print("  Nothing was chosen, so the available defaults are used.")
            chosen = [b["key"] for b in available_rows if b["default_on"]]

    if unavailable_rows:
        _print()
        _print("  Left out, because the data is not there:")
        for row in unavailable_rows:
            _print(f"    - {row['label']}: {row['reason']}")
    if not chosen:
        raise BprError("E401", "No slide block can be built for this distributor with the data on disk.",
                       db=db_key, expected="at least one block")

    # ---------------------------------------------------------- 5. look
    _print()
    theme = preset.get("theme") or _choose("How should the deck look?", THEME_CHOICES, "charcoal")
    wording = preset.get("wording") or _choose(
        "Who will read it?", WORDING_CHOICES, "shared")

    # ---------------------------------------------------------- 6. prose
    prose = dict(preset.get("prose") or {})
    # normalise anything that came in as a single string (from an answers file or a form)
    for key, value in list(prose.items()):
        if isinstance(value, str) and key != "skip":
            prose[key] = [v.strip() for v in value.splitlines() if v.strip()]
        elif isinstance(value, list):
            prose[key] = [str(v).strip() for v in value if str(v).strip()]

    if "prose" in chosen and not prose.get("skip"):
        _print()
        _print("  A few words from you make this deck worth reading. All of it is optional.")
        if "observations" not in prose:
            prose["observations"] = _ask_lines("  What are our main observations on this distributor?")
        if "questions" not in prose:
            prose["questions"] = _ask_lines("  What do we want to ask them?")
        if "actions" not in prose:
            _print("  Action points?  (write each as: topic | action | owner, blank line when done)")
            acts = []
            while True:
                try:
                    raw = input("   > ").strip()
                except (EOFError, KeyboardInterrupt):
                    raise Cancelled()
                if not raw:
                    break
                acts.append(raw)
            prose["actions"] = acts
        if "priorities" not in prose:
            _print("  Up to three discussion priorities?  (title | the sentence under it)")
            prio = []
            while True:
                try:
                    raw = input("   > ").strip()
                except (EOFError, KeyboardInterrupt):
                    raise Cancelled()
                if not raw:
                    break
                prio.append(raw)
            prose["priorities"] = prio
        if "programmes" not in prose:
            _print("  Anything to say about programmes (contracts, lubricants, tenders)?")
            probe = _ask_lines("  Programme notes, or leave blank")
            prose["programmes"] = probe

    # ---------------------------------------------------------- 7. output
    fy_label = f"FY{year}" if basis == "fiscal" else f"CY{year}"
    default_dir = output_dir(db_key, fy_label)
    _print()
    _print(f"  The deck will be written to: {default_dir}")
    _print("  A dated file name is used, so an older deck is never overwritten.")
    out_choice = preset.get("output_dir")
    if not out_choice and not _ask_yes("  Use that folder?", default=True):
        out_choice = _ask("  Folder path", str(MEETINGS_DIR))

    answers = {
        "version": ANSWER_VERSION,
        "generated": date.today().isoformat(),
        "db": db_key,
        "period_basis": basis,
        "period_year": year,
        "through_month": through,
        "sections": block_defs.order_for(chosen),
        "theme": theme,
        "wording": wording,
        "prose": prose,
        "output_dir": str(out_choice or default_dir),
    }

    # fill anything the person skipped, so a saved answers file always replays a full build
    answers["version"] = ANSWER_VERSION
    answers["generated"] = date.today().isoformat()
    answers["db"] = db_key
    answers["period_basis"] = basis
    answers["period_year"] = year
    answers["through_month"] = through
    answers["sections"] = block_defs.order_for(chosen)
    answers["theme"] = theme
    answers["wording"] = wording
    answers["prose"] = prose
    answers["output_dir"] = str(out_choice or default_dir)
    if "prose" not in chosen:
        answers["prose"] = answers.get("prose") or {}

    return answers


def _quick_context(dist: DistConfig):
    """A context good enough to answer 'which blocks can be built', with the default period."""
    from .context import make_context
    return make_context(
        dist=dist,
        theme="charcoal",
        period_basis="fiscal",
        period_year=current_fy(),
        through_month=None,
    )


# ------------------------------------------------------------------ answers file

def save(answers: dict, folder: Path) -> Path:
    """Write the answers so the same build can be repeated. Fills any gap with its default."""
    full = {
        "version": ANSWER_VERSION,
        "generated": date.today().isoformat(),
        "period_basis": "fiscal",
        "theme": "charcoal",
        "wording": "shared",
        "prose": {},
        **answers,
    }
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    stem = f"answers_{full.get('db', 'unknown')}_{full['period_basis']}{full.get('period_year', '')}"
    target = folder / f"{stem}.yaml"
    with target.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(full, fh, sort_keys=False, allow_unicode=True, width=100)
    return target


def load_answers(path: Path) -> dict:
    if not path.is_file():
        raise BprError("E102", "That answers file does not exist.", path=path,
                       expected="a YAML file written by a previous run")
    try:
        with path.open(encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
    except Exception as exc:
        raise BprError("E202", f"The answers file could not be read: {exc}", path=path) from exc
    if "db" not in data:
        raise BprError("E202", "The answers file has no distributor in it.", path=path,
                       expected="a 'db:' line")
    return data
