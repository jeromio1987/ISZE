"""Entry point.

Guided:          python build_bpr.py
Straight through: python build_bpr.py --db PORTUGAL --sections exec,plan,s2d --theme charcoal
Replay:          python build_bpr.py --answers answers_PORTUGAL_fiscal2027.yaml
Check only:      python build_bpr.py --db PORTUGAL --check
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    __package__ = "db_bpr_deck"


def _force_utf8_output() -> None:
    """Make the console safe for any character that reaches it.

    Distributor names, caveats and file paths carry characters outside cp1252 (for example the
    Polish 'L' with a stroke in a colleague's name in the Benelux caveats). A plain print would
    then fail with a UnicodeEncodeError and take the whole run down, which is exactly the kind of
    bare crash this tool exists to avoid.
    """
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is None:
            continue
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            try:
                setattr(sys, stream_name, io.TextIOWrapper(
                    stream.buffer, encoding="utf-8", errors="replace"))
            except Exception:                                    # noqa: BLE001
                pass


_force_utf8_output()

from . import blocks as block_defs                       # noqa: E402
from .checks import preflight as preflight_mod            # noqa: E402
from .config import list_keys, load                       # noqa: E402
from .context import make_context                          # noqa: E402
from .errors import (                                      # noqa: E402
    BprError,
    install_traceback_guard,
    write_error_log,
    write_run_log,
)
from .orchestrate import build                             # noqa: E402
from .paths import ISZE_ROOT, log_dir, output_dir, rel     # noqa: E402
from .periods import build as build_period, current_fy     # noqa: E402
from . import wizard                                       # noqa: E402

EXIT_OK = 0
EXIT_CONFIG = 1        # bad distributor, bad settings, bad arguments
EXIT_INPUT = 2         # a source file is missing or changed shape
EXIT_BUILD = 3         # the deck itself failed
EXIT_CHECK = 4         # the deck built but did not pass its checks
EXIT_CANCELLED = 5     # the person stopped


def _parse_args(argv: list[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        prog="build_bpr",
        description="Build a distributor business performance review deck.",
        epilog="Run with no arguments for the guided flow.",
    )
    ap.add_argument("--db", help="distributor key, e.g. PORTUGAL")
    ap.add_argument("--answers", help="answers file from a previous run")
    ap.add_argument("--sections", help="comma-separated slide blocks, e.g. exec,plan,s2d,avail")
    ap.add_argument("--theme", choices=["charcoal", "light"], help="charcoal dark or light")
    ap.add_argument("--wording", choices=["shared", "internal"], help="who will read it")
    ap.add_argument("--basis", choices=["fiscal", "calendar"], help="period basis")
    ap.add_argument("--year", type=int, help="period year, e.g. 2026")
    ap.add_argument("--through", type=int, choices=range(0, 13), metavar="MONTH",
                    help="last month to include, 1-12, or 0 for the whole year")
    ap.add_argument("--out", help="output folder")
    ap.add_argument("--check", action="store_true", help="report what can be built, then stop")
    ap.add_argument("--list", action="store_true", help="list the distributors and stop")
    ap.add_argument("--list-blocks", action="store_true", help="list the slide blocks and stop")
    ap.add_argument("--yes", action="store_true",
                    help="accept every default without asking (for a scripted run)")
    return ap.parse_args(argv)


def _print_banner() -> None:
    print()
    print("  ISZE distributor business review - deck generator")
    print("  Workspace: " + str(ISZE_ROOT))
    print()


def _resolve_answers(args) -> dict:
    """Turn the command line and any answers file into one answer set."""
    answers: dict = {}
    if args.answers:
        answers = wizard.load_answers(Path(args.answers))
    for field, value in (
        ("db", args.db),
        ("theme", args.theme),
        ("wording", args.wording),
        ("period_basis", args.basis),
        ("period_year", args.year),
        ("output_dir", args.out),
    ):
        if value is not None:
            answers[field] = value
    if args.through is not None:
        answers["through_month"] = None if args.through == 0 else args.through
    if args.sections:
        requested = [s.strip().lower() for s in args.sections.replace(";", ",").split(",") if s.strip()]
        unknown = [s for s in requested if s not in block_defs.BLOCK_KEYS]
        if unknown:
            raise BprError("E101", f"Unknown slide block(s): {', '.join(unknown)}.",
                           expected="one or more of: " + ", ".join(block_defs.BLOCK_KEYS))
        answers["sections"] = block_defs.order_for(requested)
    return answers


def _make_context_from_answers(answers: dict):
    key = str(answers.get("db", "")).upper()
    dist = load(key)
    basis = answers.get("period_basis") or "fiscal"
    year = int(answers.get("period_year") or current_fy())
    through = answers.get("through_month")
    if through is None and not answers.get("whole_year"):
        through = last_month_with_data(dist, basis, year)
    theme = answers.get("theme") or "charcoal"
    wording = answers.get("wording") or "shared"

    # default to a folder of its own, so the deck and its logs never litter 09_meetings
    label = build_period(basis, year, through).label.replace(" ", "_")
    out_dir = Path(answers["output_dir"]) if answers.get("output_dir") else output_dir(key, label)

    ctx = make_context(
        dist=dist,
        theme=theme,
        period_basis=basis,
        period_year=year,
        through_month=through,
        wording=wording,
        prose=answers.get("prose") or {},
        output_dir=out_dir,
    )
    ctx.options["period_label"] = ctx.period.label
    return ctx


def last_month_with_data(dist, basis: str, year: int) -> int | None:
    """The last month this distributor actually reported, so a deck never runs past the data.

    Falls back to the previous calendar month when nothing has been reported at all.
    """
    from .inputs import billing as billing_mod

    try:
        billing = billing_mod.load(dist.key)
        last = billing.frame.billing_date.max()
    except BprError:
        return None
    if last is None:
        return None
    # keep the month if it belongs to the period we are building
    if basis == "fiscal":
        fy = last.year + (1 if last.month >= 4 else 0)
        if fy != year:
            return None
    elif last.year != year:
        return None
    return int(last.month)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    args = _parse_args(argv)

    if args.list_blocks:
        print()
        print("  Slide blocks, in deck order:")
        for spec in block_defs.BLOCKS:
            flag = "on " if spec["default_on"] else "off"
            print(f"    {spec['key']:<10} [{flag}]  {spec['label']}")
            print(f"                  {spec['needs']}")
        print()
        return EXIT_OK

    if args.list:
        print()
        print("  Distributors configured:")
        for key in list_keys():
            try:
                dist = load(key)
                ready, total = make_context(dist=dist, theme="charcoal", period_basis="fiscal",
                                            period_year=current_fy()).buildable_count()
                print(f"    {key:<12} {dist.display:<18} {dist.country:<16} {ready} of {total} blocks")
            except BprError as exc:
                print(f"    {key:<12} PROBLEM: {exc.message}")
        print()
        return EXIT_OK

    _print_banner()

    # ---------------------------------------------------------------- check only
    if args.check:
        try:
            answers = _resolve_answers(args)
            if not answers.get("db"):
                raise BprError("E101", "--check needs --db, so we know which distributor to check.")
            ctx = _make_context_from_answers(answers)
        except BprError as exc:
            print(exc.pretty(), file=sys.stderr)
            return EXIT_CONFIG

        pf = preflight_mod.run(ctx)
        preflight_mod.print_report(pf)
        for block_key in ctx.dist.blocks_off:
            print(f"  (left out by settings: {block_key})")
        return EXIT_OK if pf.numbers_ok else EXIT_INPUT

    # ---------------------------------------------------------------- gather answers
    try:
        if args.yes:
            answers = _resolve_answers(args)
            if not answers.get("db"):
                raise BprError("E101", "--yes needs --db.")
        else:
            preset = _resolve_answers(args)
            answers = wizard.run(preset_db=args.db, preset=preset)
    except wizard.Cancelled:
        print()
        print("  Stopped. Nothing was written.")
        return EXIT_CANCELLED
    except BprError as exc:
        log = write_error_log(exc, ISZE_ROOT / "04_tools" / "db_bpr_deck" / "_logs")
        print(exc.pretty(), file=sys.stderr)
        if log:
            print(f"  A copy of this was written to {log}", file=sys.stderr)
        return EXIT_CONFIG

    # ---------------------------------------------------------------- build
    try:
        ctx = _make_context_from_answers(answers)
    except BprError as exc:
        write_error_log(exc, ISZE_ROOT / "04_tools" / "db_bpr_deck" / "_logs")
        print(exc.pretty(), file=sys.stderr)
        return EXIT_CONFIG

    selected = answers.get("sections") or [b["key"] for b in ctx.availability() if b["available"]]

    logs = log_dir(ctx.dist.key, ctx.period.label.replace(" ", "_"))
    install_traceback_guard(logs, db=ctx.dist.key)

    print(f"  Building {ctx.dist.display}, {ctx.period.label}, {len(selected)} slide blocks, "
          f"{ctx.theme} theme...")
    try:
        result = build(ctx, selected)
    except BprError as exc:
        write_error_log(exc, logs)
        write_run_log(logs, argv=argv, answers=answers, warnings=ctx.warnings,
                      result="failed", error=exc)
        print(exc.pretty(), file=sys.stderr)
        return EXIT_BUILD if exc.code.startswith("E5") else EXIT_INPUT

    # ---------------------------------------------------------------- report
    print()
    print("=" * 78)
    print(f"  Deck written: {result.path}")
    print(f"  {result.slides} slides, {len(result.written)} content blocks"
          + (f", {len(result.unavailable)} not available" if result.unavailable else ""))
    print("=" * 78)
    for item in result.written:
        print(f"    page {item['page']:>3}  {item['label']}")
    for item in result.unavailable:
        print(f"    not available  {item['label']}")
        print(f"                   {item['reason']}")
    if result.notes:
        print()
        print("  Worth knowing:")
        for note in result.notes:
            print(note.pretty())

    try:
        answers_path = wizard.save(answers, ctx.output_dir or Path("."))
        print()
        print(f"  Answers saved: {answers_path}")
        print("  Run again with --answers on that file to repeat this build without the questions.")
    except Exception as exc:                                   # noqa: BLE001
        print(f"  (the answers file could not be written: {exc})")

    run_log = write_run_log(logs, argv=argv, answers=answers, warnings=ctx.warnings,
                            result="ok", outputs=[result.path] if result.path else [])
    if run_log:
        print(f"  Run log: {run_log}")

    # ---------------------------------------------------------------- what to look at
    checks = _slide_checks(result)
    if checks["problems"]:
        print()
        print("  Some pages need a look before this deck is presented:")
        for problem in checks["problems"]:
            print(f"    {problem}")
    else:
        print()
        print(f"  Page check: {checks['tables']} tables and {checks['charts']} charts written, "
              "no page came out with headings only.")

    print()
    print(f"  Open it: {rel(result.path)}")
    print()
    return EXIT_OK


def _slide_checks(result) -> dict:
    """A cheap look at the finished deck: did the content actually land on the pages?"""
    from pptx import Presentation

    tables = charts = texts = 0
    problems: list[str] = []
    if not result.path or not Path(result.path).is_file():
        return {"tables": 0, "charts": 0, "texts": 0, "problems": ["the deck file is not on disk"]}

    prs = Presentation(str(result.path))
    for i, slide in enumerate(prs.slides, 1):
        has_table = has_chart = False
        words = 0
        for shape in slide.shapes:
            if getattr(shape, "has_table", False) and shape.has_table:
                if len(shape.table.rows) > 1:
                    has_table = True
            if getattr(shape, "has_chart", False) and shape.has_chart:
                has_chart = True
            if shape.has_text_frame:
                words += len(shape.text_frame.text.split())
        tables += 1 if has_table else 0
        charts += 1 if has_chart else 0
        texts += words
        # only flag a page that is both wordless and has nothing drawn on it
        if words < 25 and not has_table and not has_chart:
            problems.append(f"page {i} is empty: no text, no table and no chart")
    return {"tables": tables, "charts": charts, "texts": texts, "problems": problems}


if __name__ == "__main__":
    raise SystemExit(main())
