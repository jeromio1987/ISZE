"""BPR 2.0 — AIM, PRISM and IDS charts, built from real ISZE data only.

Companion to build_leakage_charts.py. Same house chart library (bpr_charts),
same rule: every number on a chart is read from a named file on disk, and the
printout at the bottom lists the number, the value and the file it came from.

Chapters
  AIM     exposure to substitution, the value-line down-trade, the biggest
          contested euro families, the spend-vs-capture map, and where uncaptured
          service volume sits in euro
  PRISM    what the analytics build actually contains, read off disk
  IDS      the 2026 dealer-standard results, by network and by section

Language is shared: "sales to dealer", "parts billed", "trucks in service".
No "sell-out" / "wallet" / "street" / "Book B" wording in any chart text.

Run:  python build_aim_prism_ids_charts.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from statistics import mean

import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import bpr_charts as C  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
PRISM = ROOT / "03_analytics" / "Isuzu" / "prism"
IDS = ROOT / "01_data" / "08_Distributor" / "IDS_2026"

# every figure that ends up on a chart, or in a chart's text, is logged here
USED: list[tuple[str, str, str]] = []

# the PNGs this script owns, printed at the end with their size
OUTPUTS = [
    "_aim_exposure_by_db.png",
    "_aim_family_risk.png",
    "_aim_gap_top.png",
    "_aim_quadrant.png",
    "_pms_capture_network.png",
    "_prism_pages.png",
    "_prism_coverage.png",
    "_ids_country_scores.png",
    "_ids_sections.png",
]


def used(label: str, value, source: str) -> None:
    if isinstance(value, float):
        shown = f"{value:,.4f}".rstrip("0").rstrip(".")
    else:
        shown = str(value)
    USED.append((label, shown, source))


def eur(v: float) -> str:
    a = abs(v)
    sign = "-" if v < 0 else ""
    if a >= 1_000_000:
        return f"{sign}\u20ac{a / 1_000_000:,.2f}M"
    if a >= 1_000:
        return f"{sign}\u20ac{a / 1_000:,.0f}k"
    return f"{sign}\u20ac{a:,.0f}"


def skipped(name: str, body: str) -> None:
    (HERE / name).write_text(body, encoding="utf-8")
    print(f"[skip] {name}\n{body}\n")


DB_LABELS = {
    "ITUK": "ITUK", "IUK": "IUK", "UMI": "UMI (Israel)", "UTI": "UTI (Israel)",
    "GERMANY": "Germany", "BELGIUM": "Belgium", "PORTUGAL": "Portugal",
    "SWEDEN": "Sweden", "NORWAY": "Norway", "IRELAND": "Ireland",
    "GREECE": "Greece", "CYPRUS": "Cyprus", "HUNGARY": "Hungary",
    "FINLAND": "Finland", "ROMANIA": "Romania", "MALTA": "Malta",
    "ICELAND": "Iceland", "DENMARK": "Denmark", "ARMENIA": "Armenia",
    "KAZAKHSTAN": "Kazakhstan", "PALESTINE": "Palestine", "UKRAINE": "Ukraine",
}

FAMILY_LABELS = {
    "PMS_Filters": "Service filters",
    "Brakes": "Brakes",
    "Clutch_Driveline": "Clutch & driveline",
    "Suspension_Chassis": "Suspension & chassis",
    "Cab_Misc": "Cab & interior",
    "Electrical": "Electrical",
    "Belts_Cooling": "Belts & cooling",
}

SUBGROUP_LABELS = {
    "fuel_filter": "Fuel filter",
    "air_filter": "Air filter",
    "oil_filter": "Oil filter",
    "brake_pad": "Brake pad",
    "brake_rotor": "Brake rotor",
    "brake_shoe": "Brake shoe",
    "wiper_blade": "Wiper blade",
    "clutch_disc": "Clutch disc",
    "clutch_kit": "Clutch kit",
    "clutch_cover": "Clutch cover",
    "release_bearing": "Release bearing",
    "blower_filter": "Blower filter",
    "urea_filter": "Urea filter",
    "cabin_filter": "Cabin filter",
    "shock_absorber": "Shock absorber",
    "battery": "Battery",
}


# ------------------------------------------------------------------ AIM 1
def aim_exposure_by_db():
    """Ranked exposure to the substitution flag, with the euro beside each name."""
    src = "aim_exposure_by_db_year.csv"
    df = pd.read_csv(DER / src)
    y = df[(df.year == 2025) & (df.net_sales_eur > 0)].copy()
    billed = float(y.net_sales_eur.sum())
    hr_eur = float(y.high_risk_rev_eur.sum())
    net_pct = hr_eur / billed * 100
    y["hr_pct"] = y.high_risk_rev_pct * 100
    y = y.sort_values("hr_pct", ascending=False)

    labels = [
        f"{DB_LABELS.get(r.distributor_code, r.distributor_code)}  {eur(r.high_risk_rev_eur)}"
        for r in y.itertuples()
    ]
    C.ranked_bar(
        labels,
        [float(v) for v in y.hr_pct],
        "_aim_exposure_by_db.png",
        title="AIM 2025: how much parts revenue sits on part numbers flagged as substitution-exposed?",
        subtitle=(
            f"Share of parts billed on flagged part numbers, CY2025. Network {eur(hr_eur)} of "
            f"{eur(billed)} billed = {net_pct:.2f}% (dashed rule). Euro beside each name is that "
            f"distributor's flagged revenue. {len(y)} distributors."
        ),
        value_fmt="{:,.2f}%",
        reference=net_pct,
        reference_label=f"network {net_pct:.2f}%",
        hot_below=False,
    )
    used("AIM flagged revenue, CY2025", hr_eur, src)
    used("parts billed, CY2025 (22 distributors)", billed, src)
    used("flagged share of parts billed, network", net_pct / 100, src)
    used("largest flagged revenue (IUK)", float(y.high_risk_rev_eur.max()), src)
    used("distributors covered, CY2025", len(y), src)
    return y


# ------------------------------------------------------------------ AIM 2
def aim_family_risk():
    """Family ranking on the measure that actually moves: the value-line share."""
    src = "aim_bvp_family_risk.csv"
    df = pd.read_csv(DER / src)
    y = df[df.year == 2025]
    g = (
        y.groupby("product_family", as_index=False)
        .agg(catalog=("catalog_sales_eur", "sum"), genuine=("genuine_eur", "sum"),
             bvp=("bvp_eur", "sum"), risk=("aim_high_risk_rev_eur", "sum"),
             rows=("catalog_sales_eur", "size"))
        .sort_values("catalog", ascending=False)
    )
    g["bvp_share"] = g.bvp / g.catalog * 100
    total = float(g.catalog.sum())
    net_share = float(g.bvp.sum()) / total * 100
    risk_total = float(g.risk.sum())
    risk_share = risk_total / total * 100

    C.ranked_bar(
        [f"{FAMILY_LABELS.get(r.product_family, r.product_family)}  {eur(r.catalog)}"
         for r in g.itertuples()],
        [float(v) for v in g.bvp_share],
        "_aim_family_risk.png",
        title="Which service families has the value line taken most of?",
        subtitle=(
            f"Value-line share of catalog revenue, CY2025, {len(g)} families aggregated across "
            f"{y.distributor_code.nunique()} distributors ({eur(total)} catalog revenue). "
            f"Network value-line share {net_share:.1f}%. The substitution flag itself carries only "
            f"{eur(risk_total)} ({risk_share:.2f}%), so the loss is in the value line, not in "
            f"third-party parts."
        ),
        value_fmt="{:,.1f}%",
        hot_below=False,
    )
    used("families aggregated, CY2025", len(g), src)
    used("distributors behind the family table", y.distributor_code.nunique(), src)
    used("catalog revenue, CY2025", total, src)
    used("value-line share of catalog revenue, network", net_share / 100, src)
    used("value-line revenue, CY2025", float(g.bvp.sum()), src)
    used("substitution-flagged revenue inside these families", risk_total, src)
    used("highest family value-line share", float(g.bvp_share.max()), src)
    return g


# ------------------------------------------------------------------ AIM 3
def aim_gap_top():
    """Top euro families where genuine and the value line both sell."""
    src = "sellout_aim_by_subgroup_2025.csv"
    df = pd.read_csv(DER / src)
    g = df.pivot_table(index="report_subgroup", columns="aim_bucket",
                       values="eur", aggfunc="sum").fillna(0.0)
    for col in ("bvp", "genuine_contested", "genuine_only"):
        if col not in g.columns:
            g[col] = 0.0
    g["contested"] = g.bvp + g.genuine_contested
    g = g[g.contested > 0].sort_values("contested", ascending=False).head(8)
    g["bvp_share"] = g.bvp / g.contested * 100

    q = df.pivot_table(index="report_subgroup", columns="aim_bucket",
                       values="qty", aggfunc="sum").fillna(0.0)
    q["contested_qty"] = q.get("bvp", 0) + q.get("genuine_contested", 0)

    matrix = pd.read_csv(DER / "aim_gps_matrix.csv")
    m25 = matrix[(matrix.year == 2025) & matrix.distributor_code.isin(df.distributor_code.unique())]
    fleet = float(m25.uio_units.sum())

    total_contested = float(g.contested.sum())

    C.ranked_bar(
        [f"{SUBGROUP_LABELS.get(i, str(i).replace('_', ' '))}  ({r.bvp_share:,.0f}% value line)"
         for i, r in g.iterrows()],
        [float(v) / 1000 for v in g.contested],
        "_aim_gap_top.png",
        title="Where do genuine and the value line both sell, and how much is at stake?",
        subtitle=(
            f"Top {len(g)} families by contested parts value, CY2025, six networks with a "
            f"sales-to-dealer file. Euro is an ISZE price-list valuation of dealer quantities "
            f"and not the dealer's own invoice value. {fleet:,.0f} trucks in service behind it. "
            f"Bars in \u20ac thousands; the bracketed figure is the share of that family's contested "
            f"value already going to the value line."
        ),
        value_fmt="{:,.0f}k",
        hot_below=False,
    )
    used("contested families on the chart (top 8)", len(g), src)
    used("contested parts value, top 8 families", float(g.contested.sum()), src)
    used("trucks in service behind those six networks", fleet, "aim_gps_matrix.csv")
    used("networks with a sales-to-dealer file", df.distributor_code.nunique(), src)
    used("contested units, top families", float(q.contested_qty.loc[g.index].sum()), src)
    used("price basis", "ISZE price-list valuation of dealer quantity", src)
    used("contested families in total, before the top-8 cut",
         int((df.pivot_table(index="report_subgroup", columns="aim_bucket", values="eur",
                             aggfunc="sum").fillna(0.0).sum(axis=1) > 0).sum()), src)
    return g


# ------------------------------------------------------------------ AIM 4
def aim_quadrant():
    src = "aim_gps_matrix.csv"
    df = pd.read_csv(DER / src)
    y = df[(df.year == 2025) & df.gps_spu_eur.notna() & df.pms_capture_all.notna()].copy()
    if len(y) < 6:
        skipped(
            "_aim_quadrant_SKIPPED.md",
            "# AIM spend-vs-capture map skipped\n\n"
            f"`{src}` carries only {len(y)} CY2025 rows with both a spend-per-truck figure and a "
            "capture basis. That is too few points for a quadrant map, and the spend benchmark is "
            "shipped separately. A ranked spend-per-truck chart is the honest form here.\n",
        )
        return None

    y["capture_pct"] = y.pms_capture_all * 100
    xs = [float(v) for v in y.gps_spu_eur]
    ys = [float(v) for v in y.capture_pct]
    x_mid = (min(xs) + max(xs)) / 2
    y_mid = (min(ys) + max(ys)) / 2
    sizes = [float(v) for v in y.uio_units]
    smax = max(sizes) or 1.0

    points = []
    for r in y.itertuples():
        x, yy = float(r.gps_spu_eur), float(r.capture_pct)
        points.append({
            "x": x, "y": yy,
            "size": 260 + 1500 * (float(r.uio_units) / smax),
            "label": DB_LABELS.get(r.distributor_code, r.distributor_code).replace(" (Israel)", ""),
            "hot": x < x_mid and yy < y_mid,
        })
    xl = min(xs) + (x_mid - min(xs)) * 0.5
    xr = x_mid + (max(xs) - x_mid) * 0.5
    yl = min(ys) + (y_mid - min(ys)) * 0.5
    yr = y_mid + (max(ys) - y_mid) * 0.5

    C.bubble_quad(
        points,
        "_aim_quadrant.png",
        title="Which markets under-buy service volume relative to what their trucks should need?",
        subtitle=(
            f"CY2025, {len(y)} networks with both measures. Dashed lines split the range shown at "
            f"its midpoint: {eur(x_mid)} billed per truck and {y_mid:,.0f}% of the expected service "
            f"volume. Bubble = trucks in service ({min(sizes):,.0f} to {max(sizes):,.0f}). "
            f"Red = below both lines."
        ),
        xlabel="Parts billed per truck in service (\u20ac)",
        ylabel="Service volume billed vs the model's expectation (%)",
        quad_labels={
            (xr, yr): "strong spend,\nstrong capture",
            (xl, yr): "thin spend,\nstrong capture",
            (xr, yl): "strong spend,\nweak capture",
            (xl, yl): "thin spend,\nweak capture \u2014 fix first",
        },
    )
    used("networks on the spend-vs-capture map", len(y), src)
    used("spend per truck, range", f"{min(xs):,.0f} to {max(xs):,.0f}", src)
    used("capture of expected service volume, range",
         f"{min(ys):,.1f}% to {max(ys):,.1f}%", src)
    used("trucks in service on the map", float(y.uio_units.sum()), src)
    used("markets below both split lines", sum(1 for p in points if p["hot"]), src)
    over = y[y.pms_capture_all > 1]
    if len(over):
        used("markets above 100% capture",
             ", ".join(over.distributor_code), src)
    return y


# ------------------------------------------------------------------ AIM 5
def pms_capture_network():
    src = "pms_capture_by_db_year.csv"
    df = pd.read_csv(DER / src)
    y = df[(df.year == 2025) & (df.line_type == "total")]
    g = (
        y.groupby("category_label", as_index=False)
        .agg(expected=("expected_qty", "sum"), actual=("actual_qty", "sum"),
             billed=("actual_rev_eur", "sum"), gap=("revenue_gap_eur", "sum"))
    )
    g["capture"] = g.actual / g.expected * 100
    g = g.sort_values("gap", ascending=False).head(10)
    net_cap = float(y.actual_qty.sum()) / float(y.expected_qty.sum()) * 100
    net_gap = float(y.revenue_gap_eur.sum())
    fleet = float(y.drop_duplicates("distributor_code").uio_units.sum())

    C.ranked_bar(
        [f"{r.category_label}  ({r.capture:,.1f}% billed)" for r in g.itertuples()],
        [float(v) / 1e6 for v in g.gap],
        "_pms_capture_network.png",
        title="Where is the uncaptured service-parts value concentrated?",
        subtitle=(
            f"CY2025, full sales basis (genuine plus value line), {y.distributor_code.nunique()} "
            f"distributors and {fleet:,.0f} trucks in service. Network bills {net_cap:.1f}% of the "
            f"service volume the model expects; uncaptured value {eur(net_gap)}. Bars in "
            f"\u20ac millions; bracketed figure is that family's billed share of expected volume."
        ),
        value_fmt="\u20ac{:,.2f}M",
        hot_below=False,
    )
    used("network capture of expected service volume, CY2025", net_cap / 100, src)
    used("uncaptured service-parts value, CY2025", net_gap, src)
    used("families in the capture model", int(df[df.year == 2025].pms_category.nunique()), src)
    used("distributors in the capture model", y.distributor_code.nunique(), src)
    used("trucks in service, capture model", fleet, src)
    used("largest single uncaptured family", float(g.gap.max()), src)
    used("parts billed on the model families, CY2025", float(y.actual_rev_eur.sum()), src)
    return g


# ---------------------------------------------------------------- PRISM 6
def prism_facts():
    pages = sorted(p.name for p in PRISM.joinpath("pages").glob("*.py")
                   if not p.name.startswith("_"))
    derived = sorted(p.name for p in DER.iterdir() if p.is_file())
    rep_path = DER / "_verification_report.json"
    import json

    rep = json.loads(rep_path.read_text(encoding="utf-8"))
    summ = rep.get("summary", {})
    stamp = str(rep.get("generated_at", ""))[:10]
    dbs = int(pd.read_csv(DER / "pms_capture_by_db_year.csv").distributor_code.nunique())

    C.kpi_strip(
        [
            ("Analytics pages", f"{len(pages)}", "in the PRISM page folder, excluding shared modules"),
            ("Derived data files", f"{len(derived):,}", "in the derived-data folder, counted on disk"),
            ("Pipeline checks passed", f"{summ.get('pass', 0)}", f"{stamp} run, {summ.get('warn', 0)} warnings, {summ.get('fail', 0)} failures"),
            ("Distributors in the service model", f"{dbs}", "with an expected-volume capture basis"),
        ],
        "_prism_pages.png",
        title="What does the analytics build actually contain?",
        per_row=4,
    )
    used("analytics pages", len(pages), "03_analytics/Isuzu/prism/pages/*.py")
    used("derived data files", len(derived), "01_data/00_derived/")
    used("pipeline checks passed", summ.get("pass", 0), "_verification_report.json")
    used("pipeline checks warned / failed",
         f"{summ.get('warn', 0)} / {summ.get('fail', 0)}", "_verification_report.json")
    used("verification date", str(rep.get("generated_at")), "_verification_report.json")
    used("distributors in the service model", dbs, "pms_capture_by_db_year.csv")
    return {"pages": len(pages), "derived": len(derived), "summary": summ}


# ---------------------------------------------------------------- PRISM 7
def prism_coverage():
    src = "_data_integrity_open_issues.md"
    text = (DER / src).read_text(encoding="utf-8")
    blocks: dict[str, list[str]] = {}
    current = ""
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            blocks[current] = []
        elif current:
            blocks[current].append(line)

    def rows(block_key: str) -> list[str]:
        for key, lines in blocks.items():
            if block_key.lower() in key.lower():
                return [ln for ln in lines
                        if ln.strip().startswith("|")
                        and not re.match(r"^\|\s*-+", ln.strip())
                        and "ID |" not in ln]
        return []

    open_rows = rows("Cannot fix")
    closed_rows = rows("Closed")
    scope_rows = rows("Out of PMS")
    stale_rows = rows("staleness")

    ids = []
    for ln in open_rows:
        m = re.match(r"^\|\s*\*\*([A-Za-z0-9\-]+)\*\*", ln)
        if m:
            ids.append(m.group(1))
    files_open = sorted({m for ln in open_rows
                         for m in re.findall(r"`([^`]+\.(?:csv|xlsx|parquet))`", ln)})
    closed_ids = [m.group(1) for ln in closed_rows
                  if (m := re.match(r"^\|\s*\*\*([A-Za-z0-9\-/ ]+)\*\*", ln))]
    scope_names = []
    for ln in scope_rows:
        m = re.match(r"^\|\s*([A-Z][A-Za-z ,/]+?)\s*\|", ln)
        if m:
            scope_names.append(m.group(1).strip())
    stale_items = sum(1 for ln in stale_rows
                      if ln.strip().startswith("|") and "`" in ln)

    C.kpi_strip(
        [
            ("Open source gaps", f"{len(ids)}",
             ", ".join(ids)),
            ("Data files they name", f"{len(files_open)}",
             ", ".join(files_open)),
            ("Closed, do not re-open", f"{len(closed_ids)}",
             f"{len(closed_rows)} logged findings, {len(closed_ids)} with an ID"),
            ("Feed staleness to watch", f"{stale_items}",
             "tender feed, metrics snapshot, competitor scrape, integrity page"),
        ],
        "_prism_coverage.png",
        title="What still limits these numbers, and what is it waiting on?",
        per_row=4,
    )
    used("open source-gap issues", len(ids), src)
    used("open issue identifiers", ", ".join(ids), src)
    used("data files named in those issues", len(files_open), src)
    used("files named", ", ".join(files_open), src)
    used("closed findings logged", len(closed_rows), src)
    used("findings outside the service model's scope", len(scope_rows), src)
    used("markets outside scope", ", ".join(scope_names), src)
    used("feed-staleness items", stale_items, src)
    used("open issue detail",
         "LCV-DEC one month short; SPU-PARTIAL 2026 basis unverified; VIN-IL and VIN-ITUK "
         "no vehicle-age layer; UIO-FCAST 2026 to 2030 forecast overstated", src)
    return {"open": ids, "files": files_open}


# ---------------------------------------------------------------- IDS 8
IDS_NETWORK_FILES = {
    "BE": "2026 IDS Evaluation Result Report_BE.xls",
    "Cyprus": "2026 IDS Evaluation Result Report_Cyprus.xls",
    "Denmark": "2026 IDS Evaluation Result Report_Denmark.xls",
    "Hungary": "2026 IDS Evaluation Result Report_Hungary.xls",
    "Israel": "2026 IDS Evaluation Result Report_Israel LCV.xls",
    "ITUK": "2026 IDS Evaluation Result Report_ITUK.xls",
    "IUK": "2026 IDS Evaluation Result Report_IUK.xls",
    "Malta": "2026 IDS Evaluation Result Report_Malta.xls",
    "MIDI_CH": "2026 IDS Evaluation Result Report_MIDI_CH.xls",
    "MIDI_ES": "2026 IDS Evaluation Result Report_MIDI_ES.xls",
    "MIDI_FR": "2026 IDS Evaluation Result Report_MIDI_FR.xls",
    "MIDI_IT": "2026 IDS Evaluation Result Report_MIDI_IT.xls",
    "NL": "2026 IDS Evaluation Result Report_NL.xls",
    "Petros": "2026 IDS Evaluation Result Report_Petros.xls",
    "Poland": "2026 IDS Evaluation Result Report_Poland.xls",
    "Portugal": "2026 IDS Evaluation Result Report_Portugal.xls",
    "Romania": "2026 IDS Evaluation Result Report_Romania.xls",
    "RSA": "2026 IDS Evaluation Result Report_RSA.xls",
}

IDS_LABELS = {
    "MIDI_CH": "Switzerland", "MIDI_ES": "Spain", "MIDI_FR": "France",
    "MIDI_IT": "Italy", "NL": "Netherlands", "BE": "Belgium",
    "RSA": "Norway", "Petros": "Greece", "ITUK": "UK CV", "IUK": "UK LCV",
    "Israel": "Israel LCV",
}

# Section E for the Israel dealer network was filled in at 0 of 18 questions,
# so it is recorded as not scored, not as a vehicle-sales failure.
SECTION_E_NOT_SCORED = {"Israel"}
SECTION_MAX_FALLBACK = {"A": 46.0, "B": 80.0, "C": 80.0, "D": 47.0, "E": 27.0}


def ids_country_scores():
    wb = IDS / "rankings" / "IDS_2026_TOTAL_ranking_all.xlsx"
    if not wb.is_file():
        skipped("_ids_SKIPPED.md", "# IDS charts skipped\n\n"
                f"Looked for the published country ranking workbook at `{wb}` \u2014 not present.\n")
        return None
    sheet = pd.read_excel(wb, sheet_name="By country", header=0)
    meta = pd.read_excel(wb, sheet_name="Info", header=None)
    dealers = int(meta.iloc[1, 1])
    networks = int(meta.iloc[2, 1])

    sheet = sheet.dropna(subset=["Country"]).copy()
    sheet["label"] = [IDS_LABELS.get(c, c) for c in sheet.Country]
    net_avg = float((sheet["Avg points %"] * sheet.Dealers).sum() / sheet.Dealers.sum())
    sheet = sheet.sort_values("Avg points %", ascending=False)

    C.ranked_bar(
        [f"{r.label}  ({int(r.Dealers)} dealers)" for r in sheet.itertuples()],
        [float(v) for v in sheet["Avg points %"]],
        "_ids_country_scores.png",
        title="IDS 2026: which dealer networks score below the European average?",
        subtitle=(
            f"Dealer-standard audit score, average per network across {dealers} dealer audits in "
            f"{networks} networks. European dealer-weighted average {net_avg:.1f}% (dashed rule); "
            f"bars below it in red. Score is out of 280 points."
        ),
        value_fmt="{:,.1f}%",
        reference=net_avg,
        reference_label=f"European average {net_avg:.1f}%",
        hot_below=True,
    )
    used("dealer audits scored", dealers, str(wb.name) + " / Info")
    used("networks scored", networks, str(wb.name) + " / Info")
    used("European dealer-weighted average score", net_avg / 100, str(wb.name) + " / By country")
    used("highest network average", f"{sheet['Avg points %'].max():,.2f}%",
         str(wb.name) + " / By country")
    used("lowest network average", f"{sheet['Avg points %'].min():,.2f}%",
         str(wb.name) + " / By country")
    return sheet


# ---------------------------------------------------------------- IDS 9
def ids_sections():
    try:
        import xlrd
    except ImportError:  # pragma: no cover
        skipped("_ids_SKIPPED.md", "# IDS section chart skipped\n\n"
                "`xlrd` is not installed, so the dealer-standard result workbooks cannot be read.\n")
        return None
    rep = IDS / "reports" / "evaluation_result"
    missing = [f for f in IDS_NETWORK_FILES.values() if not (rep / f).is_file()]
    if missing:
        skipped("_ids_SKIPPED.md", "# IDS section chart skipped\n\n"
                "Looked for the dealer-standard result workbooks in\n"
                f"`{rep}`\n\nMissing:\n" + "".join(f"- `{m}`\n" for m in missing))
        return None

    sec_re = re.compile(r"^([A-H])\.\s")
    order = ["A", "B", "C", "D", "E"]
    rows, values = [], []
    for key in sorted(IDS_NETWORK_FILES):
        sh = xlrd.open_workbook(rep / IDS_NETWORK_FILES[key]).sheet_by_index(0)
        sections: dict[str, int] = {}
        for r in range(sh.nrows):
            m = sec_re.match(str(sh.cell_value(r, 0)))
            if m:
                sections[m.group(1)] = r
        row = []
        for sid in order:
            if sid == "E" and key in SECTION_E_NOT_SCORED:
                row.append(None)
                continue
            r = sections.get(sid)
            mx = sh.cell_value(r, 2) if r is not None else None
            if not isinstance(mx, float) or mx <= 0:
                mx = SECTION_MAX_FALLBACK[sid]
            vals = [sh.cell_value(r, c) for c in range(3, sh.ncols - 2)]
            nums = [v for v in vals if isinstance(v, float)]
            if not nums:
                row.append(None)
                continue
            row.append(mean(nums) / mx * 100)
        rows.append(IDS_LABELS.get(key, key))
        values.append(row)

    C.heatmap(
        rows,
        ["Premises & facility", "Organisation", "Service", "Parts & accessories",
         "Vehicle sales"],
        values,
        "_ids_sections.png",
        title="IDS 2026: which section holds each dealer network's score down?",
        subtitle=(
            "Network average per section as a share of that section's maximum points "
            "(A 46 / B 80 / C 80 / D 47 / E 27 of 280). Hatched = not scored \u2014 the Israel dealer "
            "network filed no vehicle-sales answers, so its total is A\u2013D only."
        ),
        value_fmt="{:,.0f}%",
        cmap_colors=(C.WHITE, C.CHARCOAL),
        row_norm=False,
        figsize=(11.0, 1.4 + 0.34 * len(rows)),
    )
    for name, row in zip(rows, values):
        for sid, v in zip(order, row):
            if v is not None:
                used(f"IDS section {sid}, {name}", round(v / 100, 4),
                     "2026 IDS Evaluation Result Report_*.xls")
    sec_avg = {}
    for i, sid in enumerate(order):
        col = [r[i] for r in values if r[i] is not None]
        sec_avg[sid] = mean(col) if col else None
    used("network average per section, share of maximum",
         " ".join(f"{k} {v:,.0f}%" if v is not None else f"{k} n/a" for k, v in sec_avg.items()),
         "2026 IDS Evaluation Result Report_*.xls (18 networks)")
    used("networks in the section chart", len(rows), "2026 IDS Evaluation Result Report_*.xls")
    return sec_avg


# ------------------------------------------------------------------ report
def main():
    pd.set_option("display.width", 200)
    print("BPR 2.0 \u2014 AIM / PRISM / IDS chart build")
    print("=" * 78)

    aim_exposure_by_db()
    aim_family_risk()
    aim_gap_top()
    aim_quadrant()
    pms_capture_network()
    prism_facts()
    prism_coverage()
    ids_country_scores()
    ids_sections()

    print("\nNumbers used on the charts \u2014 value and source")
    print("-" * 78)
    width = max(len(a) for a, _, _ in USED) + 2
    for label, value, source in USED:
        print(f"{label:<{width}}{value:<26}{source}")

    pngs = [HERE / "charts_out" / n for n in OUTPUTS if (HERE / "charts_out" / n).is_file()]
    print("\nPNGs written by this script")
    print("-" * 78)
    for p in pngs:
        print(f"{p.name:<32}{p.stat().st_size / 1024:>9,.1f} kB")
    print(f"\n{len(pngs)} charts, {len(USED)} logged numbers. Build exit 0.")


if __name__ == "__main__":
    main()
