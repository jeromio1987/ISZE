"""Everything one build needs, gathered once and shared by every slide block.

Data is loaded on first use, not up front, so a build that skips the stock slides never opens
the distributor's sales file. Every load is guarded: a failure is recorded against the block
that needed it and turned into an "unavailable, and here is why" answer, not a crash.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from . import blocks as block_defs
from .config import DistConfig, overlay_defaults
from .errors import BprError, BprWarn
from .inputs import billing as billing_mod
from .inputs import fleet as fleet_mod
from .inputs import gps as gps_mod
from .inputs import kpi as kpi_mod
from .inputs import plan as plan_mod
from .inputs import sellout as sellout_mod
from .paths import VERIFICATION_REPORT
from .periods import Period, current_fy, fiscal, fiscal_year_of

# Which data each block needs. Used for the availability table and for lazy loading.
BLOCK_INPUTS: dict[str, tuple[str, ...]] = {    "exec": ("kpi", "billing", "plan"),
    "plan": ("plan", "billing"),
    "s2d": ("kpi",),
    "avail": ("kpi",),
    "s2d_units": ("sellout",),
    "stock": ("sellout", "billing", "catalog"),
    "fleet": ("fleet",),
    "gps": ("gps",),
    "pms": ("pms",),
    "mix": ("mix",),
    "prose": (),
}

# Plan-row name fragments that the automatic rules cannot reach, per distributor.
# The plan workbook's own labels are short: 'IUK', 'ITUK (IC)', 'ISUZU IRELAND', 'BL',
# 'GASANZAMMIT', 'RSA', 'ISUZU SVERIGE'. Only the irregular ones need an entry here.
EXTRA_PLAN_TOKENS: dict[str, list[str]] = {
    "ITUK": ["ITUK"],
    "PETROS": ["PETROS"],
    "NORWAY": ["RSA"],
    "ICELAND": ["BL"],
    "ISD": ["ISD"],
    "IBX": ["IBX"],
    "HUNGARY": ["AW Distribution"],
    "FINLAND": ["Nordic"],
    "DENMARK": ["ISUZU DANMARK"],
    "SWEDEN": ["ISUZU SVERIGE"],
    "CYPRUS": ["LOUTSIOS"],
    "MALTA": ["GASANZAMMIT"],
    "ROMANIA": ["ROM AUTO"],
    "PORTUGAL": ["IMOTORS"],
    "IRELAND": ["IRELAND"],
}


@dataclass
class BuildContext:
    dist: DistConfig
    period: Period
    prior: Period
    theme: str = "charcoal"
    wording: str = "shared"
    prose: dict[str, Any] = field(default_factory=dict)
    options: dict[str, Any] = field(default_factory=dict)
    output_dir: Path | None = None
    logo: Path | None = None

    warnings: list[BprWarn] = field(default_factory=list)
    unavailability: dict[str, str] = field(default_factory=dict)   # block key -> reason
    _loaders: dict[str, Callable[[], Any]] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        self._loaders = {
            "kpi": self._load_kpi,
            "billing": self._load_billing,
            "plan": self._load_plan,
            "sellout": self._load_sellout,
            "fleet": self._load_fleet,
            "gps": self._load_gps,
            "pms": self._load_pms,
            "mix": self._load_mix,
        }

    # ------------------------------------------------------------------ loading
    def get(self, name: str, default=None):
        loader = self._loaders.get(name)
        if loader is None:
            return default
        try:
            return loader()
        except BprError as exc:
            self.warnings.append(BprWarn(f"{name} unavailable: {exc.message}", path=exc.path))
            return default

    def _load_kpi(self):
        if not hasattr(self, "_kpi_cache"):
            self._kpi_cache = kpi_mod.load()
        return self._kpi_cache

    def _load_billing(self):
        if not hasattr(self, "_billing_cache"):
            self._billing_cache = billing_mod.load(self.dist.key, code=self.dist.billing_codes)
        return self._billing_cache

    def _load_plan(self):
        if not hasattr(self, "_plan_cache"):
            codes = self._sold_to()
            from .periods import fiscal_year_of
            fy = fiscal_year_of(self.period.start)
            self._plan_cache = plan_mod.load(self.dist.key, codes, fy_start_year=fy - 1,
                                             name_tokens=self._plan_tokens())
        return self._plan_cache

    def _plan_tokens(self) -> list[str]:
        """Name fragments that identify this row in the plan workbook, longest first.

        The plan workbook's own labels are shorter than ours ('IMOTORS', 'IUK', 'ITUK (IC)',
        'ISUZU IRELAND', 'BL', 'GASANZAMMIT'), so a couple of extra fragments are added by hand
        where the names differ.
        """
        tokens = [self.dist.key, self.dist.display]
        name = self.dist.name or ""
        # the first distinctive word of the legal name, e.g. 'IMOTORS' from 'I-Motors'
        head = re.split(r"[\s,.\-/]+", name)
        if head and len(head[0]) >= 3:
            tokens.append(head[0])
        tokens.extend(EXTRA_PLAN_TOKENS.get(self.dist.key, []))
        return [t for t in tokens if t and t not in ("I-Motors",)]

    def _load_sellout(self):
        if not hasattr(self, "_sellout_cache"):
            self._sellout_cache = sellout_mod.load(self.dist.key, self.dist.sellout_dir,
                                                  self.dist.sellout_kind,
                                                  normalizer=self.dist.sellout_normalizer)
            for note in getattr(self._sellout_cache, "warnings", []):
                self.warnings.append(note)
        return self._sellout_cache

    def _load_fleet(self):
        if not hasattr(self, "_fleet_cache"):
            self._fleet_cache = fleet_mod.load(self.dist.key, self.dist.fleet_source,
                                               self.dist.fleet_file, self.gps_code)
        return self._fleet_cache

    def _load_gps(self):
        if not hasattr(self, "_gps_cache"):
            self._gps_cache = gps_mod.gps(self.gps_code, self.period_year_for_gps)
        return self._gps_cache

    def _load_pms(self):
        if not hasattr(self, "_pms_cache"):
            self._pms_cache = gps_mod.pms(self.gps_code, self.pms_years)
        return self._pms_cache

    def _load_mix(self):
        if not hasattr(self, "_mix_cache"):
            self._mix_cache = gps_mod.mix(self.gps_code, self.calendar_years)
        return self._mix_cache

    # ------------------------------------------------------------------ small helpers
    def _sold_to(self) -> list[float]:
        try:
            return billing_mod.sold_to_codes(self.dist.billing_codes or self.dist.key)
        except BprError:
            return [self.dist.sold_to] if self.dist.sold_to else []

    @property
    def gps_code(self) -> str:
        """The code the parts-billed, service-demand and vehicle-count files use."""
        for candidate in (self.dist.gps_code, self.dist.pms_code, self.dist.gps_key, self.dist.key):
            if candidate:
                return str(candidate).upper()
        return self.dist.key

    @property
    def kpi_labels(self) -> list[str]:
        """Every label this distributor could have in the KPI Master File."""
        out: list[str] = []
        for value in (self.dist.kpi_name, *self.dist.kpi_names):
            if value and value not in out:
                out.append(value)
        return out

    @property
    def period_year_for_gps(self) -> int | None:
        """The GPS files are calendar or fiscal depending on the row; ask for a year, not a window."""
        return self.period.start.year if self.period.basis == "calendar" else None

    @property
    def pms_years(self) -> tuple[int, ...]:
        if self.period.basis == "fiscal":
            fy = fiscal_year_of(self.period.start)
            return (fy, fy - 1)
        return (self.period.start.year, self.period.start.year - 1)

    @property
    def calendar_years(self) -> tuple[int, ...]:
        return (self.period.start.year, self.period.start.year - 1, self.period.start.year - 2)

    def kpi_blocks(self) -> dict:
        return self.get("kpi", {}) or {}

    def kpi_label_for(self, key: str) -> str | None:
        """Which label this distributor has in one KPI block (Israel' is 'UMI', Benelux is IBX)."""
        block = self.kpi_blocks().get(key)
        if block is None:
            return None
        for label in self.kpi_labels:
            if block.has_label(label):
                return label
        return None

    def kpi_series(self, key: str) -> pd.Series:
        """This distributor's monthly series for one KPI block, numeric only."""
        label = self.kpi_label_for(key)
        block = self.kpi_blocks().get(key)
        if block is None or label is None:
            return pd.Series(dtype="float64")
        return block.series(label)

    def kpi_window(self, key: str, period: Period | None = None) -> pd.Series:
        s = self.kpi_series(key)
        if s.empty:
            return s
        p = period or self.period
        return s[(s.index >= p.start) & (s.index <= p.end)]

    def kpi_available(self, key: str) -> bool:
        return self.kpi_label_for(key) is not None

    # ------------------------------------------------------------------ availability
    def check(self, block_key: str) -> tuple[bool, str]:
        """Can this block be built? (available, reason when not)."""
        if block_key in self.dist.blocks_off:
            return False, "Left out for this distributor in the settings file."

        for name in BLOCK_INPUTS.get(block_key, ()):
            if name == "catalog":
                continue
            try:
                data = self.get(name)
            except BprError as exc:
                return False, exc.message
            if data is None:
                return False, f"{name} is not available for this distributor."
            if name in ("sellout", "fleet", "plan", "gps", "pms", "mix") and data is None:
                return False, f"{name} is not available for this distributor."

        if block_key in ("s2d", "avail") and not self.kpi_labels:
            return False, "No KPI reporting name is set for this distributor."
        if block_key in ("s2d", "avail"):
            kpi_key = {"s2d": "sales_to_dealer_eur", "avail": "mos_days"}[block_key]
            if not self.kpi_available(kpi_key):
                block = self.kpi_blocks().get(kpi_key)
                name = block.name if block else kpi_key
                return False, f"This distributor has no row in '{name}' in the KPI Master File."
            # a row can exist with no numbers in this period: check the window, not the row
            if block_key == "s2d":
                if self.kpi_window("sales_to_dealer_eur").empty:
                    return False, ("This distributor has not reported dealer sales in these months; "
                                   "their most recent report is earlier.")
            else:
                if (self.kpi_window("fill_rate").empty and self.kpi_window("mos_days").empty
                        and self.kpi_window("back_orders").empty):
                    return False, ("This distributor has not reported fill rate, stock depth or "
                                   "back orders in these months; their most recent report is earlier.")

        if block_key in ("s2d_units", "stock") and not self.dist.has_sellout:
            return False, "This distributor does not send a sales-to-dealer file."

        return True, ""

    def availability(self) -> list[dict]:
        """One row per block, for the table the tool prints before it asks anything."""
        out = []
        for spec in block_defs.BLOCKS:
            ok, reason = self.check(spec["key"])
            out.append({
                "key": spec["key"],
                "label": spec["label"],
                "needs": spec["needs"],
                "available": ok,
                "reason": reason,
                "default_on": spec["default_on"],
            })
        return out

    def buildable_count(self) -> tuple[int, int]:
        rows = self.availability()
        return sum(1 for r in rows if r["available"]), len(rows)

    # ------------------------------------------------------------------ numbers check
    def verified_numbers_ok(self) -> tuple[bool, str]:
        """Is the shared numbers check green? Refuse to quote parts billed or cover if not."""
        require = overlay_defaults().get("require_verified_numbers", True)
        if not require:
            return True, "numbers check skipped by settings"
        if not VERIFICATION_REPORT.is_file():
            return False, "the numbers check file is missing"
        import json
        try:
            with VERIFICATION_REPORT.open(encoding="utf-8") as fh:
                report = json.load(fh)
        except Exception as exc:
            return False, f"the numbers check file could not be read ({exc})"
        summary = report.get("summary") or {}
        ok = bool(summary.get("ok"))
        if ok:
            return True, f"numbers check green, {summary.get('pass', '?')} checks passed"
        return False, (f"numbers check not green: {summary.get('fail', '?')} failed, "
                       f"{summary.get('warn', '?')} warnings, generated {report.get('generated_at', '?')}")


def make_context(
    *,
    dist: DistConfig,
    theme: str,
    period_basis: str,
    period_year: int,
    through_month: int | None = None,
    wording: str = "shared",
    prose: dict | None = None,
    options: dict | None = None,
    output_dir: Path | None = None,
) -> BuildContext:
    from .periods import build as build_period, prior_year

    period = build_period(period_basis, period_year, through_month)
    return BuildContext(
        dist=dist,
        period=period,
        prior=prior_year(period),
        theme=theme,
        wording=wording,
        prose=prose or {},
        options=options or {},
        output_dir=output_dir,
    )


def default_period_args() -> tuple[str, int, int | None]:
    """Sensible starting point: the fiscal year we are in, through last month that has data."""
    today = pd.Timestamp.today()
    fy = current_fy()
    last_complete = today - pd.offsets.MonthBegin(1)
    through = last_complete.month
    return "fiscal", fy, through
