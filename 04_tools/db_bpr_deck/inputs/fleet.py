"""How many vehicles are in service, and where the number came from.

Three sources, in falling order of quality. The slide must always say which one it used,
because a vehicle-level registration file and a band-level count are not the same evidence
and a shipment count is weaker still.

  registration    a vehicle-level file with chassis and first-registration date (Portugal)
  band_counts     vehicles grouped by weight band, 01_data/00_derived/uio_by_market_type_year.csv
  shipment_proxy  shipments standing in for the fleet (weakest; labelled on the slide)

Fleet years are ISZE fiscal years: April to March. FY2026 means April 2025 to March 2026.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from ..errors import BprError, BprWarn
from ..paths import DERIVED_DIR, ISZE_ROOT

BAND_FILE = DERIVED_DIR / "uio_by_market_type_year.csv"

BAND_LABEL = {
    "LD": "light truck",
    "MD": "medium truck",
    "CV": "truck",
    "F-Series": "F-Series",
    "F_Series": "F-Series",
    "LCV": "pickup (D-Max)",
    "LCV_Unidentified": "pickup (unidentified)",
}


@dataclass
class Fleet:
    db_key: str
    source: str                       # registration | band_counts | shipment_proxy
    source_note: str
    by_fy: dict[int, float] = field(default_factory=dict)
    by_fy_band: dict[int, dict[str, float]] = field(default_factory=dict)
    coverage: tuple[pd.Timestamp, pd.Timestamp] | None = None

    def units(self, fy: int) -> float | None:
        value = self.by_fy.get(fy)
        return None if value is None else float(value)

    def source_sentence(self) -> str:
        return self.source_note


def _fy_of(stamp: pd.Timestamp) -> int:
    return stamp.year + (1 if stamp.month >= 4 else 0)


def _fy_window(fy: int) -> tuple[pd.Timestamp, pd.Timestamp]:
    return pd.Timestamp(year=fy - 1, month=4, day=1), pd.Timestamp(year=fy, month=3, day=31)


# --------------------------------------------------------------------- band counts

def _from_band_counts(db_key: str, code: str | None = None) -> Fleet:
    if not BAND_FILE.is_file():
        raise BprError("E102", "The vehicle count file is missing.",
                       path=BAND_FILE, db=db_key,
                       expected="01_data/00_derived/uio_by_market_type_year.csv")
    wanted = (code or db_key).upper()
    df = pd.read_csv(BAND_FILE)
    df = df[df.distributor_code.astype(str).str.upper() == wanted]
    if df.empty:
        raise BprError("E401", f"There is no vehicle count for {db_key} in the fleet file.",
                       db=db_key, path=BAND_FILE,
                       expected=f"rows for {wanted}",
                       found="distributors present: " + ", ".join(
                           sorted(pd.read_csv(BAND_FILE).distributor_code.unique())[:30]))

    # Calendar-year rows from the market's fleet table. A fiscal year straddles two calendar
    # years; this source is a calendar snapshot, so FY(n) is read as CY(n-1) and labelled that
    # way on the slide. No interpolation between snapshots is invented.
    out: dict[int, float] = {}
    bands: dict[int, dict[str, float]] = {}
    for year, group in df.groupby("year"):
        total = float(group.uio_units.sum())
        if total <= 0:
            continue
        fy = int(year) + 1
        previous = out.get(fy)
        # actual beats estimate beats forecast when two rows carry the same year
        if previous is None or total > previous:
            out[fy] = total
            bands[fy] = group.groupby("vehicle_class").uio_units.sum().to_dict()
    note = ("Vehicle count by weight band, from the market's own fleet table. It is a count of "
            "vehicles in service, kept by calendar year, so the fiscal-year label shows the "
            "snapshot it comes from. This is not a chassis-level count.")
    return Fleet(db_key=db_key, source="band_counts", source_note=note, by_fy=out, by_fy_band=bands)


# --------------------------------------------------------------------- registration

def _from_registration(db_key: str, path: Path) -> Fleet:
    """Portugal only: one row per vehicle with a first-registration date.

    Two counts are produced, both named on the slide, because they answer different questions:
      ten  the 10-year car park: vehicles first registered in the last ten fiscal years
      all  every vehicle ever registered in the file
    The scrap-rate model (each year reduced by a survival curve) is a third method used by the
    PRISM engine; it is not reproduced here, so the slide does not claim it.
    """
    if not path.is_file():
        raise BprError("E102", f"The registration file for {db_key} is missing.", path=path,
                       db=db_key, expected="the vehicle-level registration workbook")

    import openpyxl
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    sheet_names = list(wb.sheetnames)
    sheets = {s.strip(): s for s in sheet_names}

    rows: list[tuple] = []
    used: list[str] = []
    for name, sheet in sheets.items():
        if "sum" in name.lower():
            continue
        ws = wb[sheet]
        block = [r for r in ws.iter_rows(values_only=True)]
        head = None
        for i, row in enumerate(block[:8]):
            flat = " ".join(str(v).lower() for v in row if v is not None)
            if "vin" in flat or "chassis" in flat:
                head = i
                break
        if head is None:
            continue
        header = [str(v or "").strip().lower() for v in block[head]]
        vin_col = next((j for j, h in enumerate(header) if "vin" in h or "chassis" in h), None)
        date_col = next((j for j, h in enumerate(header)
                         if "reg" in h or "matric" in h or "data" in h), None)
        if vin_col is None or date_col is None:
            continue
        for row in block[head + 1:]:
            if row is None or len(row) <= max(vin_col, date_col):
                continue
            if row[vin_col] in (None, "") or row[date_col] in (None, ""):
                continue
            rows.append((str(row[vin_col]), row[date_col]))
        used.append(sheet)
    wb.close()

    if not rows:
        raise BprError(
            "E202",
            f"The registration file for {db_key} opened but no chassis column was recognised.",
            path=path, db=db_key,
            expected="a column named VIN or chassis, plus a first-registration date column",
            found="tabs: " + ", ".join(sheet_names)[:200],
        )

    frame = pd.DataFrame(rows, columns=["vin", "reg"])
    frame["reg"] = pd.to_datetime(frame.reg, errors="coerce")
    frame = frame[frame.reg.notna()].drop_duplicates("vin")
    frame["fy"] = frame.reg.dt.year + (frame.reg.dt.month >= 4).astype(int)

    ten: dict[int, float] = {}
    allv: dict[int, float] = {}
    bands: dict[int, dict[str, float]] = {}
    last_fy = _fy_of(pd.Timestamp.today())
    for fy in range(int(frame.fy.min()), last_fy + 1):
        allv[fy] = float((frame.fy <= fy).sum())
        window = frame[(frame.fy <= fy) & (frame.fy > fy - 10)]
        ten[fy] = float(len(window))
        if fy == last_fy:
            bands[fy] = {"10-year car park": ten[fy], "all registrations": allv[fy]}

    note = (f"Vehicle-level count from the registration file: {len(frame):,} chassis, "
            f"counted on the 10-year car park basis (first registered in the last ten fiscal years). "
            f"Counting every registration ever would give {allv[last_fy]:,.0f}.")
    fleet = Fleet(db_key=db_key, source="registration", source_note=note, by_fy=ten, by_fy_band=bands)
    fleet.coverage = (frame.reg.min(), frame.reg.max())
    return fleet


def _from_shipment_proxy(db_key: str, code: str | None = None) -> Fleet:
    """Weakest source: shipments standing in for the fleet.

    Read from the JP shipment register, which carries a distributor code per vehicle. The slide
    says plainly that these are vehicles shipped, not vehicles in service.
    """
    path = DERIVED_DIR / "uio" / "vin" / "VIN_register.parquet"
    if not path.is_file():
        path = DERIVED_DIR / "uio_vin_register.parquet"
    if not path.is_file():
        candidates = list(DERIVED_DIR.glob("**/VIN_register.parquet"))
        path = candidates[0] if candidates else None

    if path is None or not Path(path).is_file():
        raise BprError(
            "E102",
            "No shipment register is on disk, so this market cannot show a vehicle count.",
            db=db_key,
            expected="a VIN shipment register with a distributor column",
        )

    df = pd.read_parquet(path)
    code_col = next((c for c in ("db_code", "distributor_code", "db") if c in df.columns), None)
    date_col = next((c for c in ("shipment_date", "cohort_date", "invoice_month", "prod_month")
                     if c in df.columns), None)
    if code_col is None or date_col is None:
        raise BprError(
            "E202",
            "The shipment register does not carry the columns needed to count vehicles per market.",
            db=db_key, path=path,
            expected="a distributor column and a shipment date column",
            found=", ".join(map(str, df.columns))[:200],
        )

    key = (code or db_key).upper()
    part = df[df[code_col].astype(str).str.upper() == key]
    if part.empty:
        raise BprError("E401", f"No shipments for {db_key} in the shipment register.", db=db_key,
                       path=path,
                       found="codes present: " + ", ".join(
                           sorted(df[code_col].astype(str).unique())[:30]))
    stamps = pd.to_datetime(part[date_col], errors="coerce").dropna()
    stamps = stamps[stamps <= pd.Timestamp.today()]          # ignore future schedulings
    if stamps.empty:
        raise BprError("E301", f"Shipments for {db_key} carry no usable dates.", db=db_key, path=path)

    # vehicles shipped in a rolling twelve months, which is the closest stand-in for a fleet
    by_fy: dict[int, float] = {}
    for fy in range(fiscal_year_of(stamps.min()), fiscal_year_of(stamps.max()) + 1):
        start, end = _fy_window(fy)
        by_fy[fy] = float(((stamps >= start) & (stamps <= end)).sum())

    note = (f"Vehicles shipped in the twelve months to March, standing in for vehicles in service: "
            f"this market has no registration or band-level vehicle count. "
            f"{len(part):,} shipment records from the JP shipment register.")
    return Fleet(db_key=db_key, source="shipment_proxy", source_note=note, by_fy=by_fy)


# --------------------------------------------------------------------- entry

def load(db_key: str, source: str, fleet_file: str | None = None, code: str | None = None) -> Fleet:
    """The best vehicle count available for this market.

    The configured source is tried first. If it has nothing, the band-level count is tried
    before giving up, because a lower-quality count that is labelled honestly beats a missing
    page. The slide always states which source it used.
    """
    attempts: list[str] = []
    if source == "registration":
        path = Path(fleet_file) if fleet_file else None
        if path is None or not path.is_absolute():
            path = (ISZE_ROOT / fleet_file) if fleet_file else None
        if path is not None:
            try:
                return _from_registration(db_key, path)
            except BprError as exc:
                attempts.append(f"registration file: {exc.message}")
        else:
            attempts.append("registration file: no path given in the settings file")

    if source in ("registration", "shipment_proxy"):
        try:
            return _from_shipment_proxy(db_key, code)
        except BprError as exc:
            attempts.append(f"shipment register: {exc.message}")

    try:
        return _from_band_counts(db_key, code)
    except BprError as exc:
        attempts.append(f"vehicle count by band: {exc.message}")

    raise BprError(
        "E401",
        f"No vehicle count could be found for {db_key} from any source.",
        db=db_key,
        expected="a registration file, a shipment register row, or a row in the fleet table",
        detail=" | ".join(attempts),
    )


def probe(db_key: str, fleet: Fleet) -> list[BprWarn]:
    out = [BprWarn(f"fleet for {db_key} from {fleet.source}; available FY: "
                   + ", ".join(f"FY{fy}:{n:,.0f}" for fy, n in sorted(fleet.by_fy.items())[-4:]))]
    return out
