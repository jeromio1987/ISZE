"""The check that runs before anything is asked or built.

It answers three questions for one distributor:
  1. is the shared numbers check green, so we may quote parts billed and service cover at all;
  2. which slide blocks can be filled, and for the ones that cannot, why not, in one sentence;
  3. is any input stale, and which of the distributor's own reporting habits need reading first.

Nothing here changes a file.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from ..config import DistConfig
from ..context import BuildContext
from ..errors import BprError, BprWarn
from ..inputs import billing as billing_mod
from ..inputs import kpi as kpi_mod
from ..inputs import plan as plan_mod
from ..inputs import sellout as sellout_mod
from ..paths import KPI_MASTER, SALES_FACT, VERIFICATION_REPORT, rel

STALE_MONTHS = 3


@dataclass
class Preflight:
    dist: DistConfig
    ok: bool = True
    numbers_ok: bool = False
    numbers_note: str = ""
    blocks: list[dict] = field(default_factory=list)
    notes: list[BprWarn] = field(default_factory=list)
    freshness: list[tuple[str, str, str]] = field(default_factory=list)   # (what, when, verdict)

    @property
    def buildable(self) -> list[str]:
        return [b["key"] for b in self.blocks if b["available"]]

    @property
    def blocked(self) -> list[dict]:
        return [b for b in self.blocks if not b["available"]]

    def summary_line(self) -> str:
        return f"{len(self.buildable)} of {len(self.blocks)} slide blocks can be built for {self.dist.display}"


def _file_note(path, what: str, stale_days: int | None = None) -> tuple[str, str, str]:
    if path is None or not path.exists():
        return (what, "-", "MISSING")
    stamp = pd.Timestamp(path.stat().st_mtime, unit="s")
    verdict = "ok"
    if stale_days is not None:
        age = (pd.Timestamp.today().normalize() - stamp.normalize()).days
        if age > stale_days:
            verdict = f"STALE ({age} days old)"
    return (what, f"{stamp:%Y-%m-%d %H:%M}", verdict)


def run(ctx: BuildContext) -> Preflight:
    """Build the availability table and the notes. Never raises for a missing input."""
    pf = Preflight(dist=ctx.dist)

    # ---- 1. may we quote the shared numbers at all
    pf.numbers_ok, pf.numbers_note = ctx.verified_numbers_ok()

    # ---- 2. freshness of the shared inputs
    pf.freshness = [
        _file_note(SALES_FACT, "Billing (sales_fact.parquet)"),
        _file_note(KPI_MASTER, "KPI Master File", stale_days=45),
        _file_note(VERIFICATION_REPORT, "Numbers check"),
    ]

    # ---- 3. notes about this distributor's own inputs, gathered quietly
    if ctx.kpi_labels:
        try:
            blocks = ctx.get("kpi") or {}
            for key, block in blocks.items():
                label = ctx.kpi_label_for(key)
                if label is None:
                    pf.notes.append(BprWarn(
                        f"no row in '{block.name}' (KPI Master File) - months there are treated as not reported"))
                    continue
                latest = block.latest(label)
                if latest is None:
                    pf.notes.append(BprWarn(f"'{block.name}': no numeric values for {ctx.dist.display}"))
                    continue
                month, value = latest
                gap = kpi_mod.stale_by(block, label, STALE_MONTHS)
                tail = f"  (reported through {month:%b %Y})"
                if gap:
                    tail += f"  NOTE: {gap} months behind other distributors' latest report"
                pf.notes.append(BprWarn(f"'{block.name}': latest {value:,.2f}{tail}"))
        except BprError as exc:
            pf.notes.append(BprWarn(f"KPI Master File unreadable: {exc.message}", path=exc.path))
    else:
        pf.notes.append(BprWarn("no KPI reporting name set, so the KPI slides are skipped"))

    # billing
    pf.notes.extend(billing_mod.probe(ctx.dist.key, ctx.dist.billing_codes))

    # plan
    try:
        pf.notes.extend(plan_mod.probe(ctx.dist.key, billing_mod.sold_to_codes(ctx.dist.key),
                                       name_tokens=ctx._plan_tokens()))
    except Exception as exc:                                   # noqa: BLE001
        pf.notes.append(BprWarn(f"plan unavailable: {exc}"))

    # sales to dealer
    if ctx.dist.has_sellout:
        try:
            so = ctx.get("sellout")
            if so is not None:
                pf.notes.append(BprWarn(
                    f"sales to dealer: {so.total_qty:,.0f} units from {so.pn_count:,} part numbers, "
                    f"{so.months[0]:%b %Y} to {so.months[-1]:%b %Y} ({so.note})"))
                pf.notes.append(BprWarn(
                    f"sales to dealer source: {so.source_line()}"))
                if so.refreshed:
                    pf.notes.append(BprWarn(
                        "the raw file was newer than the checked file, so it was brought up to "
                        "date before this build - the deck uses the newer data"))
                elif so.refresh_failed:
                    pf.notes.append(BprWarn(
                        f"STALE READ: the raw file is newer but it could not be processed "
                        f"({so.refresh_failed}). The deck uses the last good checked version. "
                        "Ask a colleague to check the source file before presenting."))
                elif so.read_from == "raw file, as sent":
                    pf.notes.append(BprWarn(
                        "read straight from the files as sent: this distributor has no checked "
                        "file to go stale, so every build reads the raw months"))
                last_month = so.months[-1].to_period("M")
                end_month = ctx.period.end.to_period("M")
                if last_month < end_month:
                    pf.notes.append(BprWarn(
                        f"their file ends {so.months[-1]:%b %Y}, before {ctx.period.end:%b %Y}: "
                        "the stock comparison will be labelled with the months it actually covers"))
                else:
                    pf.notes.append(BprWarn(
                        f"their file covers the whole window, through {so.months[-1]:%b %Y}"))
        except BprError as exc:
            pf.notes.append(BprWarn(f"sales to dealer unreadable: {exc.message}", path=exc.path))
    else:
        pf.notes.append(BprWarn("no sales-to-dealer file for this distributor; those slides are left out"))

    # ---- 4. the availability table itself
    pf.blocks = ctx.availability()

    # ---- 5. the distributor's own caveats, from the settings file
    for line in ctx.dist.watch:
        pf.notes.append(BprWarn(f"settings caveat: {line}"))

    pf.ok = pf.numbers_ok
    return pf


def print_report(pf: Preflight, *, stream=None) -> None:
    import sys
    out = stream or sys.stdout
    d = pf.dist

    print(file=out)
    print("=" * 78, file=out)
    print(f"  Before we build: {d.display} ({d.key}) - {d.name}, {d.country}", file=out)
    print("=" * 78, file=out)

    status = "GREEN" if pf.numbers_ok else "NOT GREEN"
    print(f"  Shared numbers check : {status} - {pf.numbers_note}", file=out)
    print(file=out)
    print("  Input                    Modified              State", file=out)
    for what, when, verdict in pf.freshness:
        print(f"  {what:<24} {when:<21} {verdict}", file=out)

    print(file=out)
    print("  Slide blocks available:", file=out)
    print("  " + "-" * 74, file=out)
    for row in pf.blocks:
        mark = "yes" if row["available"] else " no"
        line = f"  [{mark}]  {row['label']}"
        print(line, file=out)
        if not row["available"]:
            print(f"            why not: {row['reason']}", file=out)

    if pf.notes:
        print(file=out)
        print("  Worth knowing before you choose:", file=out)
        for note in pf.notes:
            print(note.pretty(), file=out)

    print(file=out)
    print(f"  {pf.summary_line()}", file=out)
    if not pf.numbers_ok:
        print(file=out)
        print("  STOP: the shared numbers are not verified, so a deck built now must not be presented.",
              file=out)
        print(f"        {VERIFICATION_REPORT}", file=out)
    print("=" * 78, file=out)
    print(file=out)


def short_block_table(pf: Preflight) -> str:
    """One-line-per-block text used by the wizard."""
    lines = []
    for i, row in enumerate(pf.blocks, 1):
        state = "yes" if row["available"] else "no "
        lines.append(f"  {i:>2}. [{state}] {row['label']}")
    return "\n".join(lines)
