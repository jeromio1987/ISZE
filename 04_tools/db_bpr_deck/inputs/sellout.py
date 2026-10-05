"""Sales to dealer, in whatever shape the distributor sent it.

The distributor's file is never changed. This module reads it as it is, and returns one
fixed frame: part number, month, units.

Two routes, in this order:
  1. the normalized long file the workspace already keeps for that distributor
     (01_data/00_derived/dealer_sellout_long_<DIR>_*.csv, 13 columns, see
     01_data/12_raw/dealer_sales/DEALER_SELL_OUT.md). Preferred, because it is checked.
  2. the distributor's own raw workbook, parsed in memory by shape. Nothing is written.

Shapes we handle, and who sends them:
  line_level     one row per invoice line with a date column     Portugal, Ireland
  month_pivot    one column per month                            IUK, Greece
  network_pivot  year row + month row above the data             ITUK
  month_files    one workbook per calendar month                 Romania, UTI

When a shape does not match, we stop with E202 or E204 and list what we did find. We never
guess which column is the quantity.
"""
from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from ..errors import BprError, BprWarn
from ..paths import DERIVED_DIR, ISZE_ROOT, RAW_DEALER_SALES_DIR
from .catalog import norm_pn

# Column-name keywords, lower case. Used to find the columns in a file we have not seen.
PN_KEYWORDS = ("referencia", "referência", "part number", "part no", "p/n", "item code",
               "item ordered", "item supplied", "item number", "material", "partnumber")
QTY_KEYWORDS = ("quantidade", "qty suppld", "qty ordrd", "orig qty", "qty", "quantidade",
                "quantity", "sum of quantidade", "sum")
DATE_KEYWORDS = ("data da fatura", "invoice date", "invoicedate", "invoice date", "data",
                 "despatchdate", "orderdate", "datum", "date")

MONTH_NAMES = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    "january": 1, "february": 2, "march": 3, "april": 4, "june": 6, "july": 7,
    "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    # German, because the KPI file mixes them and these files come from the same desk
    "mrz": 3, "mai": 5, "okt": 10, "dez": 12,
}


@dataclass
class Sellout:
    db_key: str
    kind: str
    frame: pd.DataFrame          # pn, month (Timestamp, first of month), qty
    sources: list[str]
    months: pd.DatetimeIndex
    note: str = ""
    refreshed: bool = False
    refresh_failed: str | None = None
    read_from: str = ""          # "normalised file" | "raw file, as sent"
    warnings: list[BprWarn] = field(default_factory=list)

    @property
    def pn_count(self) -> int:
        return int(self.frame.pn.nunique())

    @property
    def total_qty(self) -> float:
        return float(self.frame.qty.sum())

    @property
    def first_month(self) -> pd.Timestamp | None:
        return None if self.months.empty else self.months[0]

    @property
    def last_month(self) -> pd.Timestamp | None:
        return None if self.months.empty else self.months[-1]

    @property
    def months_label(self) -> str:
        """The plain months this file actually covers, e.g. 'January 2025 to August 2026'."""
        if self.months.empty:
            return "no months"
        if self.first_month.to_period("M") == self.last_month.to_period("M"):
            return f"{self.first_month:%B %Y}"
        return f"{self.first_month:%B %Y} to {self.last_month:%B %Y}"

    @property
    def months_short(self) -> str:
        """For a source line, e.g. 'Jan 2025 to Aug 2026 (20 months)'."""
        if self.months.empty:
            return "no months"
        return f"{self.first_month:%b %Y} to {self.last_month:%b %Y} ({len(self.months)} months)"

    def source_line(self) -> str:
        """The sentence that goes in a slide footer: which file, which months, how it was read."""
        files = ", ".join(self.sources[:2]) if self.sources else "as sent"
        if len(self.sources) > 2:
            files += f" and {len(self.sources) - 2} more"
        parts = [f"{files}, {self.months_short}"]
        if self.read_from == "normalised file" and self.refreshed:
            parts.append("brought up to date from the raw file for this build")
        elif self.read_from == "normalised file":
            parts.append("read from the checked file")
        else:
            parts.append("read in the format it was sent")
        if self.refresh_failed:
            parts.append("the raw file was newer but could not be processed, so the last good version was used")
        return "; ".join(parts)

    def covers(self, period) -> bool:
        """Does this file reach the end of the period being reported?"""
        if self.last_month is None:
            return False
        return self.last_month.to_period("M") >= pd.Timestamp(period.end).to_period("M")

    def window(self, start, end) -> pd.DataFrame:
        start, end = pd.Timestamp(start), pd.Timestamp(end)
        return self.frame[(self.frame.month >= start) & (self.frame.month <= end)]

    def monthly(self) -> pd.Series:
        if self.frame.empty:
            return pd.Series(dtype="float64")
        return self.frame.groupby("month").qty.sum().sort_index()

    def by_family(self, start=None, end=None) -> pd.DataFrame:
        from .catalog import family_units
        df = self.frame if start is None else self.window(start, end)
        if df.empty:
            return pd.DataFrame(columns=["family", "qty"])
        return family_units(df, "qty")


# ---------------------------------------------------------------------------- helpers

def _norm(text) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def _find_col(columns: list[str], keywords: tuple[str, ...]) -> int | None:
    """The first column whose name contains one of the keywords. Longest keyword first."""
    lowered = [_norm(c) for c in columns]
    for key in sorted(keywords, key=len, reverse=True):
        for i, name in enumerate(lowered):
            if key in name:
                return i
    return None


def _month_from_label(label) -> pd.Timestamp | None:
    text = _norm(label).replace(",", " ")
    parts = text.split()
    if len(parts) < 2:
        return None
    month = MONTH_NAMES.get(parts[0].rstrip("."))
    year = None
    for token in parts[1:]:
        digits = re.sub(r"\D", "", token)
        if len(digits) == 4:
            year = int(digits)
            break
        if len(digits) == 2:
            year = 2000 + int(digits)
            break
    if month is None or year is None:
        return None
    try:
        return pd.Timestamp(year=year, month=month, day=1)
    except ValueError:
        return None


def _rows(path: Path) -> list[tuple]:
    import openpyxl
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    out: list[tuple] = []
    for ws in wb.worksheets:
        for row in ws.iter_rows(values_only=True):
            out.append(row)
        break          # one sheet is enough; multi-sheet shapes are handled per shape
    wb.close()
    return out


def _sheet_rows(path: Path, sheet: str) -> list[tuple]:
    import openpyxl
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    if sheet not in wb.sheetnames:
        wb.close()
        raise BprError("E201", f"The tab '{sheet}' is not in {path.name}.", path=path,
                       expected=sheet, found=", ".join(wb.sheetnames))
    ws = wb[sheet]
    out = [row for row in ws.iter_rows(values_only=True)]
    wb.close()
    return out


# ---------------------------------------------------------------------------- shapes

def _read_line_level(path: Path, db_key: str) -> pd.DataFrame:
    """One row per invoice line, with a date column. Portugal and Ireland."""
    rows = _rows(path)
    if not rows:
        raise BprError("E202", f"{path.name} opened but has no rows.", path=path, db=db_key)

    header_idx = None
    for i, row in enumerate(rows[:12]):
        names = [_norm(v) for v in row if v is not None]
        if not names:
            continue
        if any(k in " ".join(names) for k in PN_KEYWORDS):
            header_idx = i
            break
    if header_idx is None:
        raise BprError(
            "E202",
            f"Could not find the header row in {path.name}.",
            path=path, db=db_key,
            expected="a row naming the part number and the quantity columns",
            found="first rows: " + " | ".join(
                ", ".join(str(v) for v in r[:4] if v is not None) for r in rows[:4]
            )[:300],
        )

    header = [_norm(v) for v in rows[header_idx]]
    pn_col = _find_col(header, PN_KEYWORDS)
    qty_col = _find_col(header, QTY_KEYWORDS)
    date_col = _find_col(header, DATE_KEYWORDS)
    if pn_col is None or qty_col is None or date_col is None:
        raise BprError(
            "E202",
            f"Could not tell which columns hold the part number, the quantity and the date in {path.name}.",
            path=path, db=db_key,
            expected="one part-number column, one quantity column, one date column",
            found=f"header row {header_idx + 1}: " + ", ".join(str(v) for v in rows[header_idx] if v)[:300],
        )

    records = []
    skipped = 0
    for row in rows[header_idx + 1:]:
        if row is None or len(row) <= max(pn_col, qty_col, date_col):
            continue
        pn, qty, when = row[pn_col], row[qty_col], row[date_col]
        if pn is None or qty is None or when is None:
            skipped += 1
            continue
        try:
            q = float(qty)
        except (TypeError, ValueError):
            skipped += 1
            continue
        stamp = pd.to_datetime(when, errors="coerce")
        if pd.isna(stamp):
            skipped += 1
            continue
        records.append((str(pn), pd.Timestamp(year=stamp.year, month=stamp.month, day=1), q))

    if not records:
        raise BprError("E301", f"Every row in {path.name} was skipped, so there are no units to compare.",
                       path=path, db=db_key, found=f"{skipped} rows unreadable")

    df = pd.DataFrame(records, columns=["pn", "month", "qty"])
    df["pn"] = norm_pn(df["pn"])
    return df.groupby(["pn", "month"], as_index=False).qty.sum()


def _read_month_pivot(path: Path, db_key: str) -> pd.DataFrame:
    """One column per month. IUK and Greece. Month order is not assumed."""
    rows = _rows(path)
    header_idx, month_cols = None, []
    for i, row in enumerate(rows[:12]):
        found = {j: _month_from_label(v) for j, v in enumerate(row) if v is not None}
        found = {j: m for j, m in found.items() if m is not None}
        if len(found) >= 3:
            header_idx, month_cols = i, found
            break
    if header_idx is None:
        raise BprError(
            "E204",
            f"No month headings were found in {path.name}.",
            path=path, db=db_key,
            expected="a row with month headings such as Jan-25",
            found="first rows: " + " | ".join(
                ", ".join(str(v) for v in r[:6] if v is not None) for r in rows[:3]
            )[:300],
        )

    header = [_norm(v) for v in rows[header_idx]]
    pn_col = _find_col(header, PN_KEYWORDS)
    if pn_col is None:
        raise BprError("E202", f"No part-number column in {path.name}.", path=path, db=db_key,
                       expected="a column such as Part Number",
                       found=", ".join(str(v) for v in rows[header_idx] if v)[:300])

    records = []
    for row in rows[header_idx + 1:]:
        if row is None or len(row) <= pn_col or row[pn_col] is None:
            continue
        pn = str(row[pn_col])
        for col, month in month_cols.items():
            if col >= len(row) or row[col] is None:
                continue
            try:
                qty = float(row[col])
            except (TypeError, ValueError):
                continue
            if qty:
                records.append((pn, month, qty))
    df = pd.DataFrame(records, columns=["pn", "month", "qty"])
    if df.empty:
        raise BprError("E301", f"{path.name} has month columns but no quantities in them.",
                       path=path, db=db_key)
    df["pn"] = norm_pn(df["pn"])
    return df.groupby(["pn", "month"], as_index=False).qty.sum()


def _read_network_pivot(path: Path, db_key: str) -> pd.DataFrame:
    """Year on one header row, months on the next. ITUK."""
    rows = _rows(path)
    year_row_idx = month_row_idx = None
    for i, row in enumerate(rows[:20]):
        months = sum(1 for v in row if v is not None and _month_from_label(v) is not None)
        if months >= 3:
            month_row_idx = i
            year_row_idx = max(i - 1, 0)
            break
    if month_row_idx is None:
        return _read_month_pivot(path, db_key)

    year_row, month_row = rows[year_row_idx], rows[month_row_idx]
    records = []
    for row in rows[month_row_idx + 1:]:
        if not row or row[0] is None:
            continue
        pn = str(row[0])
        for col in range(1, min(len(row), len(month_row))):
            label = month_row[col]
            if label is None or col >= len(year_row):
                continue
            month = _month_from_label(label)
            if month is None:
                continue
            year_token = year_row[col]
            if year_token is not None:
                digits = re.sub(r"\D", "", str(year_token))
                if len(digits) == 4:
                    try:
                        month = month.replace(year=int(digits))
                    except ValueError:
                        pass
            if row[col] is None:
                continue
            try:
                qty = float(row[col])
            except (TypeError, ValueError):
                continue
            if qty:
                records.append((pn, month, qty))
    df = pd.DataFrame(records, columns=["pn", "month", "qty"])
    if df.empty:
        raise BprError("E301", f"{path.name} has a month row but no quantities under it.",
                       path=path, db=db_key)
    # The first column reads "PN - description"; keep only the part number part.
    df["pn"] = norm_pn(df["pn"].str.split(" - ").str[0])
    return df.groupby(["pn", "month"], as_index=False).qty.sum()


def _read_month_files(folder: Path, db_key: str, pattern: str = "*.xlsx") -> pd.DataFrame:
    """One workbook per calendar month. Romania and UTI. Period comes from the file name."""
    files = sorted(p for p in folder.glob(pattern) if not p.name.startswith("~$"))
    if not files:
        raise BprError("E102", f"No monthly sales files in {folder.name}.", path=folder, db=db_key,
                       expected=f"{pattern} files, one per month")

    records, sources = [], []
    for path in files:
        match = re.search(r"(\d{4})-(\d{2})", path.stem)
        if not match:
            continue
        month = pd.Timestamp(year=int(match.group(1)), month=int(match.group(2)), day=1)
        rows = _rows(path)
        header_idx = None
        for i, row in enumerate(rows[:12]):
            if row and row[0] is not None and _norm(row[0]) in ("part number", "item code", "p/no", "part no"):
                header_idx = i
                break
        if header_idx is None:
            for i, row in enumerate(rows[:12]):
                names = " ".join(_norm(v) for v in row if v is not None)
                if any(k in names for k in PN_KEYWORDS):
                    header_idx = i
                    break
        if header_idx is None:
            raise BprError(
                "E202",
                f"No header row found in {path.name}.",
                path=path, db=db_key,
                expected="a row naming the part number column",
                found="first rows: " + " | ".join(
                    ", ".join(str(v) for v in r[:4] if v is not None) for r in rows[:4])[:300],
            )
        header = [_norm(v) for v in rows[header_idx]]
        pn_col = _find_col(header, PN_KEYWORDS)
        qty_col = _find_col(header, QTY_KEYWORDS)
        if pn_col is None or qty_col is None:
            raise BprError(
                "E202",
                f"Could not find the part number and quantity columns in {path.name}.",
                path=path, db=db_key,
                found="header: " + ", ".join(str(v) for v in rows[header_idx] if v)[:300],
            )
        for row in rows[header_idx + 1:]:
            if not row or len(row) <= max(pn_col, qty_col) or row[pn_col] is None:
                continue
            try:
                qty = float(row[qty_col])
            except (TypeError, ValueError):
                continue
            if qty:
                records.append((str(row[pn_col]), month, qty))
        sources.append(path.name)

    df = pd.DataFrame(records, columns=["pn", "month", "qty"])
    if df.empty:
        raise BprError("E301", f"No quantities were read from the monthly files in {folder.name}.",
                       path=folder, db=db_key, found=", ".join(sources[:6]))
    df["pn"] = norm_pn(df["pn"])
    return df.groupby(["pn", "month"], as_index=False).qty.sum()


# ---------------------------------------------------------------------------- long file

def _long_file_candidates(db_key: str, sellout_dir: str) -> list[Path]:
    """Every normalised file for this distributor, dealer-grain first.

    Nothing is dropped here. Which grain to use is decided per year in _read_long_files, because
    for ITUK the dealer file and the network companion cover different years and both are needed.
    """
    found = sorted(DERIVED_DIR.glob(f"dealer_sellout_long_{sellout_dir}_*.csv"))
    return sorted(found, key=lambda p: (is_companion_file(p), p.name))


def _newest_mtime(paths: list[Path]) -> float:
    stamps = [p.stat().st_mtime for p in paths if p.is_file()]
    return max(stamps) if stamps else 0.0


def _raw_files(sellout_dir: str) -> list[Path]:
    """The files the distributor sent: workbooks and csv, never a temporary lock file."""
    raw_dir = RAW_DEALER_SALES_DIR / sellout_dir
    if not raw_dir.is_dir():
        return []
    out: list[Path] = []
    for pattern in ("*.xlsx", "*.xlsm", "*.xls", "*.csv"):
        out.extend(p for p in raw_dir.glob(pattern) if not p.name.startswith("~$"))
    return sorted(out)


def _read_one_long_file(path: Path) -> pd.DataFrame:
    """One normalised file: month rows only, with the calendar year and whether it is a companion.

    The grain is taken from the file name and from the file's own flags column. ITUK marks three
    of its four year files as companions only in the flags column, so trusting the name alone
    would treat network totals as dealer sales.
    """
    df = pd.read_csv(path, dtype={"part_number": str})
    if "period_grain" in df.columns:
        # Year-to-date rows sit beside month rows and would double count if summed together.
        df = df[df.period_grain == "month"]
    if df.empty:
        return pd.DataFrame(columns=["pn", "month", "qty", "year", "companion"])

    companion = is_companion_file(path)
    if not companion and "flags" in df.columns:
        marked = df["flags"].fillna("").astype(str).str.contains("companion", case=False)
        companion = bool(marked.any())

    df = df[["part_number", "period", "qty"]].copy()
    df["month"] = pd.PeriodIndex(df.period.astype(str), freq="M").to_timestamp()
    df = df.rename(columns={"part_number": "pn"})
    df["qty"] = pd.to_numeric(df.qty, errors="coerce").fillna(0)
    df["year"] = df.month.dt.year
    df["companion"] = companion
    return df[["pn", "month", "qty", "year", "companion"]]


def _read_long_files(paths: list[Path]) -> pd.DataFrame:
    """Combine the normalised files without ever counting the same vehicles twice.

    Some distributors ship both grains. For ITUK the per-year files are all network companions and
    the dealer-grain file carries 2025, so neither grain can simply be dropped: dropping the
    companion loses 2023, 2024 and 2026, and dropping the dealer file loses the dealer grain. The
    rule is therefore per calendar year:
        use the dealer-grain file when one covers that year;
        otherwise use the companion, because it is the only record of that year.
    A single year is never taken from both, so the market is never counted twice.
    """
    frames = [f for f in (_read_one_long_file(p) for p in paths) if not f.empty]
    if not frames:
        return pd.DataFrame(columns=["pn", "month", "qty"])

    kept: list[pd.DataFrame] = []
    for _year, group in pd.concat(frames, ignore_index=True).groupby("year"):
        dealer_rows = group[~group.companion]
        kept.append(dealer_rows if not dealer_rows.empty else group)

    out = pd.concat(kept, ignore_index=True)
    if out.empty:
        return pd.DataFrame(columns=["pn", "month", "qty"])
    out["pn"] = norm_pn(out["pn"])
    # Summing is safe here: the year rows are gone and each year comes from exactly one grain.
    return out.groupby(["pn", "month"], as_index=False).qty.sum()


# ---------------------------------------------------------------------------- refresh

def is_companion_file(path: Path) -> bool:
    """Is this the network-grain companion rather than the dealer-grain file, judged by name?

    ITUK ships the same vehicles twice: once per dealer and once as a network total. Summing both
    would count the market twice. The name carries the marker for the 2025 file; the other years
    are only marked inside the file, so _read_one_long_file checks the flags column as well. The
    other tools in the workspace exclude the 2025 file by name
    (01_data/91_build/build_sales_to_dealer_colleague_pack_20260924.py).
    """
    return "network" in path.name.lower() or "companion" in path.name.lower()


def _run_normalizer(script_name: str) -> tuple[bool, str]:
    """Run one of the workspace normalisers. Returns (ok, one-line result).

    The scripts sit in 01_data/91_build and take their source path as an argument with a default
    pointing at the current raw file. They are run with the same interpreter as this tool, so a
    virtual environment is honoured.
    """
    script = ISZE_ROOT / "01_data" / "91_build" / script_name
    if not script.is_file():
        return False, f"the normaliser {script_name} is not in 01_data/91_build"

    try:
        proc = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(ISZE_ROOT),
            capture_output=True,
            text=True,
            timeout=600,
        )
    except subprocess.TimeoutExpired:
        return False, f"{script_name} did not finish within ten minutes"
    except Exception as exc:                                     # noqa: BLE001
        return False, f"{script_name} could not be started ({type(exc).__name__}: {exc})"

    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()
        detail = tail[-1] if tail else "no output"
        return False, f"{script_name} exited {proc.returncode} ({detail[:160]})"
    return True, f"{script_name} ran"


def _raw_signature(raw_files: list[Path]) -> list[list]:
    """A fingerprint of the raw files: name, size and timestamp of each one."""
    out = []
    for p in sorted(raw_files):
        st = p.stat()
        out.append([p.name, st.st_size, st.st_mtime_ns])
    return out


def _state_path() -> Path:
    return DERIVED_DIR / "_sellout_refresh_state.json"


def _read_state() -> dict:
    path = _state_path()
    if not path.is_file():
        return {}
    try:
        import json
        with path.open(encoding="utf-8") as fh:
            return json.load(fh) or {}
    except Exception:                                            # noqa: BLE001
        return {}


def _write_state(db_key: str, signature: list[list], outputs: list[Path]) -> None:
    """Remember that these raw files have already been turned into these output files.

    Without this, a raw file whose clock runs ahead of this machine would be treated as newer on
    every build and the normaliser would run forever. Never allowed to break a build.
    """
    try:
        import json
        state = _read_state()
        state[db_key] = {
            "raw_signature": signature,
            "outputs": [p.name for p in outputs],
            "refreshed_at": pd.Timestamp.now().isoformat(timespec="seconds"),
        }
        path = _state_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2)
    except Exception:                                            # noqa: BLE001
        pass


def _already_refreshed(db_key: str, raw_files: list[Path], long_paths: list[Path]) -> bool:
    """Have these exact raw files already been turned into the checked files we have?"""
    if not long_paths:
        return False
    stored = (_read_state().get(db_key) or {})
    if stored.get("raw_signature") != _raw_signature(raw_files):
        return False
    # the outputs must still be there, or the record is meaningless
    names = set(stored.get("outputs") or [])
    return bool(names) and all((DERIVED_DIR / n).is_file() for n in names)


def _refresh_normalised_file(
    *,
    db_key: str,
    sellout_dir: str,
    normalizer: str,
    raw_files: list[Path],
    long_paths: list[Path],
) -> tuple[bool, str]:
    """Bring the normalised file up to date when the raw file is newer.

    Returns (refreshed, message). Never raises: a failure here must not stop a build, because a
    stale file that is labelled is better than no deck at all.

    Success is judged by whether a file was actually rewritten, not by comparing timestamps against
    the raw file. A raw file copied from another machine can carry a clock that runs ahead, so the
    freshly written output can legitimately look older than its own input.
    """
    before = {p: p.stat().st_mtime for p in long_paths}
    ok, message = _run_normalizer(normalizer)
    if not ok:
        return False, message

    # The normaliser may create a file that did not exist before, so re-glob the folder.
    after_paths = _long_file_candidates(db_key, sellout_dir)
    if not after_paths:
        return False, f"{normalizer} ran but wrote no file matching its expected name"

    touched = [p.name for p in after_paths if before.get(p) != p.stat().st_mtime]
    if not touched:
        return False, f"{normalizer} ran but nothing was rewritten"

    _write_state(db_key, _raw_signature(raw_files), after_paths)
    return True, f"{normalizer} refreshed {', '.join(sorted(touched)[:3])}"


# ---------------------------------------------------------------------------- entry

def load(db_key: str, sellout_dir: str | None, kind: str | None,
         normalizer: str | None = None) -> Sellout:
    """Read this distributor's sales-to-dealer data, refreshing it first if the raw file is newer.

    Order of reading:
      1. if a raw file dropped in is newer than the normalised file, run the normaliser, then read
         the normalised file;
      2. if there is no normaliser (UTI), read the raw monthly files directly;
      3. if the normalised file is the newest, read it;
      4. if only the raw file exists, read the raw file;
      5. if the refresh fails, fall back to the normalised file and label the read as stale.
    """
    if not sellout_dir or not kind:
        raise BprError(
            "E402",
            f"{db_key} does not send a sales-to-dealer file, so this block cannot be built.",
            db=db_key,
            expected="a sales-to-dealer file",
            found="no folder configured",
        )

    raw_files = _raw_files(sellout_dir)
    long_paths = _long_file_candidates(db_key, sellout_dir)
    warnings: list[BprWarn] = []
    refreshed = False
    refresh_failed: str | None = None

    # ---- 2: no normaliser configured. This distributor's raw files are already the shape we need
    # (UTI sends one workbook per month), so they are read directly on every build. There is no
    # normalised copy of this data, and therefore nothing that can go stale.
    if not normalizer and raw_files:
        frame = _read_raw(sellout_dir, kind, db_key)
        frame = frame.groupby(["pn", "month"], as_index=False).qty.sum()
        sellout = _finish(db_key, kind, frame, [p.name for p in raw_files],
                          note="read from the file as sent; no normaliser is needed for this "
                               "distributor, so there is no copy that can go stale")
        sellout.read_from = "raw file, as sent"
        return sellout

    # ---- 1: is the raw file newer than what we already have?
    # A raw file whose clock runs ahead would look newer forever, so a signature of the raw files
    # already processed is kept. The signature only ever suppresses a re-run; it never triggers one.
    raw_newer = bool(raw_files) and (
        not long_paths or _newest_mtime(raw_files) > _newest_mtime(long_paths)
    )
    if raw_newer and not _already_refreshed(db_key, raw_files, long_paths):
        refreshed, message = _refresh_normalised_file(
            db_key=db_key, sellout_dir=sellout_dir, normalizer=normalizer,
            raw_files=raw_files, long_paths=long_paths,
        )
        long_paths = _long_file_candidates(db_key, sellout_dir)
        if refreshed:
            warnings.append(BprWarn(f"sales to dealer for {db_key}: {message}, "
                                    "so this build uses the newer data"))
        else:
            refresh_failed = message
            warnings.append(BprWarn(
                f"sales to dealer for {db_key}: the raw file is newer but it could not be "
                f"processed ({message}); the last good version is used instead and the slide "
                "says so"))

    # ---- 3 and 5: the normalised file, now current or knowingly stale
    if long_paths:
        frame = _read_long_files(long_paths)
        if not frame.empty:
            sellout = _finish(db_key, kind, frame, [p.name for p in long_paths],
                              note="read from the checked long file")
            sellout.refreshed = refreshed
            sellout.refresh_failed = refresh_failed
            sellout.read_from = "normalised file"
            sellout.warnings.extend(warnings)
            return sellout

    # ---- 4: no normalised file at all, so read what they sent
    if not raw_files:
        raise BprError(
            "E102",
            f"No sales-to-dealer file for {db_key}, in either the raw folders or the checked files.",
            path=(RAW_DEALER_SALES_DIR / sellout_dir), db=db_key,
            expected="the workbook the distributor sent",
        )
    frame = _read_raw(sellout_dir, kind, db_key)
    frame = frame.groupby(["pn", "month"], as_index=False).qty.sum()
    sellout = _finish(db_key, kind, frame, [p.name for p in raw_files],
                      note="read from the file as sent")
    sellout.read_from = "raw file, as sent"
    sellout.warnings.extend(warnings)
    return sellout


def _read_raw(sellout_dir: str, kind: str, db_key: str) -> pd.DataFrame:
    """Read the file as the distributor sent it, by whichever shape they use."""
    raw_dir = RAW_DEALER_SALES_DIR / sellout_dir
    files = _raw_files(sellout_dir)
    if kind == "line_level":
        return pd.concat([_read_line_level(p, db_key) for p in files], ignore_index=True)
    if kind == "month_pivot":
        return pd.concat([_read_month_pivot(p, db_key) for p in files], ignore_index=True)
    if kind == "network_pivot":
        return pd.concat([_read_network_pivot(p, db_key) for p in files], ignore_index=True)
    if kind == "month_files":
        return _read_month_files(raw_dir, db_key)
    raise BprError("E202", f"Unknown sales-to-dealer shape '{kind}' for {db_key}.",
                   db=db_key, expected="one of line_level, month_pivot, network_pivot, month_files",
                   found=kind)


def _finish(db_key: str, kind: str, frame: pd.DataFrame, sources: list[str], note: str) -> Sellout:
    months = pd.DatetimeIndex(sorted(frame.month.unique()))
    return Sellout(db_key=db_key, kind=kind, frame=frame, sources=sources, months=months, note=note)
