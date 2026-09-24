"""Generate ISZE_OS_Console.html — the operating console of the parts business OS.

The OS is the closed loop data -> decision -> action -> result, with the KPIs as its
instrument panel. The car park (UIO), PRISM and AIM are sensors, not the subject.

Run from anywhere:
  python ISZE/02_dashboards/ops/build_os_console.py

Conventions follow build_os_data_map.py (same house CSS, same OPEN_*.cmd pattern,
same no-CDN assertion). Every figure carries a hover tooltip with formula, snapshot
date and what is not included.
"""
from __future__ import annotations

import html
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT_HTML = HERE / "ISZE_OS_Console.html"
OUT_CMD = HERE / "OPEN_ISZE_OS_Console.cmd"

SNAPSHOT = "2026-09-16"

# ---------------------------------------------------------------------------
# DATA — every value below is re-derived from the file named in its tooltip.
# ---------------------------------------------------------------------------

# CY2025 spend league: billed from gps_spu_by_distributor.csv; fleet from
# wallet_waterfall.csv (worksheet base 163,198 — D08). Five markets differ from the
# July GPS extract (ITUK, Germany, Ireland, Portugal, Belgium). Network average is
# the matched pair EUR 30,756,772 / 163,198 = EUR 188.46. Sorted by spend per vehicle.
SPU_2025 = [
    ("IRELAND", 549.49, 2161, 1187458.6, 1391176.0),
    ("UTI", 322.32, 10336, 3331511.9, 8271300.0),
    ("ITUK", 241.23, 23067, 5564543.9, 11835911.0),
    ("PORTUGAL", 237.21, 7208, 1709794.0, 3494069.0),
    ("FINLAND", 230.83, 1204, 277920.6, 301000.0),
    ("BELGIUM", 219.88, 9593, 2109331.6, 2454394.0),
    ("ICELAND", 210.05, 406, 85281.6, 101500.0),
    ("MALTA", 198.56, 1040, 206502.3, 378827.0),
    ("CYPRUS", 185.63, 2308, 428443.1, 676267.0),
    ("GERMANY", 184.03, 13780, 2535931.8, 3412284.0),
    ("UMI", 179.02, 18542, 3319344.2, 4635500.0),
    ("NORWAY", 178.65, 7929, 1416551.9, 1982250.0),
    ("DENMARK", 174.17, 851, 148220.5, 213239.0),
    ("ROMANIA", 163.60, 1071, 175218.4, 267750.0),
    ("SWEDEN", 151.42, 8443, 1278462.2, 2110750.0),
    ("GREECE", 139.04, 3742, 520303.9, 953593.0),
    ("IUK", 128.33, 47783, 6131920.4, 11945750.0),
    ("HUNGARY", 88.39, 3734, 330030.6, 933500.0),
]
SPU_AVG = 188.46
BILLED_2025 = 30756772.0
UIO_2025 = 163198
# Ceiling / cover / uncaptured: read from wallet_waterfall.csv at build time.
# That file was corrected on 2026-09-22 (the measured 3.5 t share for the six markets whose
# light-truck row was still priced entirely at the heavier band), so the ceiling is now
# EUR 54,375,729 and cover 56.6%. Nothing here is typed in: re-running this builder picks
# up whatever the file holds.
import csv as _csv  # noqa: E402
import os as _os  # noqa: E402

_WW = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                    "..", "..", "01_data", "00_derived", "wallet_waterfall.csv")
_w = [r for r in _csv.DictReader(open(_WW, newline="", encoding="utf-8-sig")) if r["year"] == "2025"]
CEILING_2025 = round(sum(float(r["theoretical_wallet_eur"]) for r in _w), 2)
_cap = sum(float(r["captured_total_eur"]) for r in _w)
CAPTURE_2025 = round(_cap / CEILING_2025 * 100, 1)
UNCAPTURED = round(sum(float(r["addressable_uncaptured_eur"]) for r in _w), 2)
_over = sum(float(r["over_target_eur"]) for r in _w if r.get("over_target_eur"))
OVER_TARGET = round(_over, 2)
_flat = [r for r in _w
         if float(r["uio_units"]) and
         abs(float(r["theoretical_wallet_eur"]) / float(r["uio_units"]) - 250.0) <= 0.01]
FLAT_MARKETS = len(_flat)
FLAT_EURO = round(sum(float(r["theoretical_wallet_eur"]) for r in _flat), 2)
FLAT_SHARE_CEILING = round(FLAT_EURO / CEILING_2025 * 100, 1) if CEILING_2025 else 0.0

# pms_capture_by_db_year.csv, 2025, three-way service-part split on expected units.
SPLIT_EXPECTED = 996890
SPLIT_GENUINE = 197666
SPLIT_BVP = 85130
SPLIT_NOT_BOUGHT = 714094
SPLIT_NOT_BOUGHT_PCT = 71.6
BVP_SHARE_SERVICE = 36.7  # wallet_waterfall.csv captured bvp / captured total, 2025
BVP_SHARE_ALL = 3.5  # mix_genuine_bvp_by_group.csv, 2025 whole book

# pms_summary_by_db.csv, 2025 — weighted total capture across 14 categories.
CAPTURE_BY_DB = [
    ("IRELAND", 102.7), ("ITUK", 65.9), ("CYPRUS", 50.1), ("UTI", 48.4),
    ("GREECE", 40.3), ("ROMANIA", 36.7), ("MALTA", 32.9), ("PORTUGAL", 32.4),
    ("DENMARK", 30.2), ("ICELAND", 30.2), ("FINLAND", 29.0), ("NORWAY", 26.9),
    ("BELGIUM", 25.9), ("SWEDEN", 24.1), ("UMI", 21.3), ("HUNGARY", 19.1),
    ("IUK", 17.3), ("GERMANY", 14.0),
]

# pms_opportunity_matrix.csv, 2025 category revenue gaps.
CATEGORY_GAP = [
    ("clutch_disc", "Clutch disc", 3142767.0),
    ("brake_pad", "Brake pad", 2780016.0),
    ("brake_shoe", "Brake shoe", 2469688.0),
    ("clutch_pressure_plate", "Clutch pressure plate", 1982854.0),
    ("blower_filter", "Blower filter", 1421877.0),
    ("brake_rotor", "Brake rotor", 1394154.0),
    ("fuel_filter", "Fuel filter", 1018496.0),
    ("clutch_kit", "Clutch kit", 957623.0),
    ("urea_filter", "Urea filter", 916329.0),
    ("clutch_booster", "Clutch booster", 700953.0),
    ("air_filter", "Air filter", 655917.0),
    ("release_bearing", "Release bearing", 428962.0),
    ("oil_filter", "Oil filter", 319619.0),
    ("pilot_bearing", "Pilot bearing", 27302.0),
]
CATEGORY_GAP_TOTAL = 18216555.0

# revenue_waterfall.csv — volume / price / mix decomposition.
GROWTH_SPLIT = [
    ("2023 → 2024", 521030.0, -143956.0, 0.0),
    ("2024 → 2025", -272688.0, 19323.0, 0.0),
]

# action_ledger_open.csv, run 20260825T175229Z_48a077.
LEDGER_ROWS = 23236
LEDGER_EUR = 22110563.54
LEDGER_SIGNALS = [
    ("Book B price revision", 500, 9995481.0),
    ("Replenishment exception", 1595, 4168788.0),
    ("Dealer leakage (UK trucks)", 300, 3922774.0),
    ("Defection alert", 204, 2914197.0),
    ("Catalogue gap (no list price)", 31, 591916.0),
    ("Early warning", 18, 293130.0),
    ("Price revision queue", 20572, 224277.0),
    ("Account health", 16, 0.0),
]

# Derived tables backing the sensor-break picture.
VIN_BY_MARKET = [("PT", 2111), ("IE", 647), ("DE", 183), ("MT", 130), ("CY", 114), ("BE", 49), ("GR", 4)]
VIN_TOTAL = 3238
VIN_MARKETS = 7
VIN_MARKETS_TOTAL = 22
UK_VINS = 29935
FLEET_MARKETS = 18
NO_FLEET_MARKETS = ["Ukraine", "Armenia", "Kazakhstan", "Palestine"]
STD_MIX = [("LCV / D-Max", 125168, "no weight class"), ("CV standard", 36793, "no N35 / N75 split"), ("F-series", 1238, "one class")]
WEIGHT_KM = [("N35 (NLR, 3.5 t)", 12165), ("N75 (NPR / NMR / NNR)", 35217), ("F-series (7.5 t+)", 45630), ("Israel, all classes", 51680)]
ASSUMED_KM = 20000

# dealer_sellout_gps_2025.csv + OWNED_NUMBER_SHORTLIST_20260916.md
S2D_EURO_5 = 16735739.0
S2D_PCT_5 = 54.4
S2D_EURO_6 = 18445533.0
S2D_PCT_6 = 60.0
FULL_PARTS_BASE = 112090000.0
FULL_BASE_PCT = 14.9

# ---------------------------------------------------------------------------
# Decision queue — every row is sourced; nothing is invented.
# ---------------------------------------------------------------------------

QUEUE = [
    dict(
        n=1,
        data="<b>Pickup warranty is only read to April 2026.</b> A new network-wide claim export runs to "
             "<b>August 2026</b> and its overlap ties to this file to the euro, but nothing published reads "
             "the last four months: <b>5,048 claim lines, EUR 1,078,462</b> (May 218,099 · Jun 276,570 · "
             "Jul 316,477 · Aug 267,317). The older gap it closes is already settled: the November-2025 end "
             "of the pickup file is no longer the edge.",
        decision="Wire the four new months into the pickup claim data and refresh the pages that show a "
                 "pickup warranty figure, or leave the last four months unread.",
        owner="ISZE",
        blocked="Nothing — the file is on disk. It is a choice about scope.",
        due="2026-10-01",
        state="judgement",
        src="01_data/00_derived/_data_integrity_open_issues.md · LCV-EXT · LCV-DEC",
    ),
    dict(
        n=2,
        data="The 2026 rows of the spend-per-unit file carry a <b>part-year</b> euro column against a <b>full-year</b> ceiling. Read naively they show a 43% collapse that did not happen (first-half 2026 parts are +12% on first-half 2025). Contained 15 Sep: the false capture % and traffic light are blanked.",
        decision="Drop the 2026 year from the file until a dated extract exists, or rebuild the row from a quarter that reconciles to sales_fact.",
        owner="ISZE",
        blocked="A dated 2026 billing extract (Q1 9.99M / Q2 8.72M vs a 9.18M row sum — basis unverified)",
        due="2026-10-15",
        state="excluded",
        src="01_data/00_derived/_data_integrity_open_issues.md · SPU-PARTIAL",
    ),
    dict(
        n=3,
        data="The Japanese VIN register holds <b>3,238 vehicles across seven markets</b> and excludes the two largest aftersales books. Israel has no vehicle age and no model detail in the register.",
        decision="Ask UTI for the Israel VIN pack, or state that Israel age and model mix are not derivable and stop showing them.",
        owner="Jerome — supply UTI VIN pack",
        blocked="Israel VIN pack",
        due="2026-10-01",
        state="excluded",
        src="01_data/07_UIO/vin/VIN_register_summary.json · VIN-IL",
    ),
    dict(
        n=4,
        data="The UK VIN list sits in a mail from the UK parts director: <b>29,935 VINs</b> with registration dates (the earlier 29,926 was wrong). It is extracted but not loaded, and the register still excludes UK.",
        decision="Make the UK extract a second, separately labelled register lane, or leave the UK without a register-based age layer.",
        owner="Jerome / ITUK",
        blocked="Loading the mail extract into the register",
        due="2026-10-01",
        state="measured",
        src="01_data/90_INBOX/_ituk_vins_from_duncan_mail.md · VIN-ITUK",
    ),
    dict(
        n=5,
        data="The 2026–2030 vehicle-in-service forecast scraps 3% a year while the 1990–2025 history implies 10.2% (trucks) and 12.3% (light commercial). Verified 16 Sep: +9% (2026) to +59% (2030) too high; Israel is 25% low in every year.",
        decision="Rebuild to V20 before any 2026–2030 vehicle count is quoted, and keep every forecast column off published pages until then.",
        owner="Vehicle population model owner",
        blocked="V20 rebuild (spec drafted)",
        due="2026-10-31",
        state="excluded",
        src="01_data/00_derived/_data_integrity_open_issues.md · UIO-FCAST · 06_uio/_CURRENT/V20_SPEC.md",
    ),
    dict(
        n=6,
        data="Every 3.5-tonne truck is charged the vehicle weight of a 7.5-tonne truck: the model code is read as tonnage, so the fleet reads 26,689 t against a real 19,687 t (8.24 t a truck instead of 6.08 t).",
        decision="Approve the series-to-weight map (NLR 3.5, NMR 5.5, NNR 6.5, NPR 7.5, FRR 11–12, FSR 13.5) and its effect on the target-spend denominator.",
        owner="ISZE — approve the map",
        blocked="Nothing technical; it changes published spend per unit",
        due="2026-09-23",
        state="judgement",
        src="06_uio/_CURRENT/V20_SPEC.md · problem 6",
    ),
    dict(
        n=7,
        data="Mileage tracks truck class, not market: 3.5 t <b>12,165 km/yr</b>, 7.5 t <b>35,217</b>, F-series <b>45,630</b> — a 3.7× spread against one global assumption of 20,000. Israel measured 51,680 (confirmed at three of three estimators); the UK sample says 16,688 against an assumed 50,000.",
        decision="Switch the model default to per-weight-class mileage, or keep the global number and treat the measured table as a selectable alternative.",
        owner="Jerome / PRISM",
        blocked="One question to the UK distributor: average annual distance of the N-series fleet",
        due="2026-09-23",
        state="judgement",
        src="01_data/00_derived/warranty_cv_km_age_by_market.csv · 01_data/90_INBOX/_cv_warranty_mileage_validation.md · provisional",
    ),
    dict(
        n=8,
        data="Six different vehicle ages are in play for the same fleet: <b>6.86</b> (registration weight), <b>6.07</b> (survivor-weighted model), <b>5.84</b> (model steady state, all trucks), <b>5.06</b> (model steady state, light commercial), <b>3.30</b> (shipment date), <b>1.9</b> (claims-derived).",
        decision="Choose which age basis goes on a published tile, and label it on the tile.",
        owner="Jerome",
        blocked="Nothing",
        due="2026-09-23",
        state="judgement",
        src="01_data/90_INBOX/_assumption_reversibility_spec.md · §5",
    ),
    dict(
        n=9,
        data=(f"{FLAT_MARKETS} markets — <b>€{FLAT_EURO / 1e6:,.2f}M, {FLAT_SHARE_CEILING}%</b> of the "
              f"€{CEILING_2025 / 1e6:.2f}M target ceiling — sit on one flat €250 per vehicle. Denmark "
              f"reads €250.57 and is not flat; the nine-market count was wrong. Re-cut on defensible "
              f"alternatives the same billed book reads 43.6%, 40.6% or 29.4%."),
        decision="Own the ceiling assumption in public (and turn the age-spend curve into a named data ask), or keep the ceiling internal and quote only billed euro.",
        owner="Jerome / VP Sales",
        blocked="A per-market, per-age target-spend basis",
        due="2026-10-15",
        state="modelled",
        src="00_docs/OWNED_NUMBER_SHORTLIST_20260916.md · candidate 2",
    ),
    dict(
        n=10,
        data="Sales to dealer is visible on <b>54.4%</b> of the 2025 billed book in the measured markets (60.0% with Portugal). On the full €112.09M parts base the same six files would read about 14.9%.",
        decision="Fix the denominator for the published number: the €30.76M eighteen-market basis, or the €112.09M full parts base. It has no owner today.",
        owner="Jerome",
        blocked="The denominator choice itself; Germany, Belgium and Portugal are €6.36M of files away",
        due="2026-09-30",
        state="judgement",
        src="00_docs/OWNED_NUMBER_SHORTLIST_20260916.md · candidate 1 · dealer_sellout_gps_2025.csv",
    ),
    dict(
        n=11,
        data="The fleet bucket file carries one <b>cv_std</b> column of 36,793 trucks and no N35 / N75 split, so per-class mileage cannot reach the denominator even though it is measured.",
        decision="Approve splitting cv_std into n35 and n75 (total unchanged) so the weight-class design can actually reach the vehicle count.",
        owner="ISZE",
        blocked="Nothing; changes no published figure until a scenario gives the two halves different mileage",
        due="2026-10-01",
        state="judgement",
        src="03_analytics/Isuzu/prism/data/uio_by_model_bucket.csv · _assumption_reversibility_spec.md §2.5",
    ),
    dict(
        n=12,
        data="The action ledger holds <b>23,236 open opportunities worth €22.1M</b> on mixed bases. <b>Every row is in state NEW</b> and the decisions file is empty (header only) — nothing has been triaged, so no outcome can ever be measured.",
        decision="Triage the top of the ledger into own / defer / drop, or accept that the ledger is an inventory and not a queue.",
        owner="ISZE",
        blocked="An empty decisions file — a 30-minute intentional act, not a data gap",
        due="2026-09-23",
        state="judgement",
        src="01_data/00_derived/action_ledger_open.csv · action_ledger_decisions.csv · ACTION_LEDGER_REVIEW_20260825.md",
    ),
    dict(
        n=13,
        data="Several pages claim to be the aftersales entry point: the command centre, the executive paper, the operating dashboards, this console, the old orientation hub.",
        decision="Name one aftersales front page; the others become references behind it.",
        owner="Jerome",
        blocked="Nothing",
        due="2026-09-23",
        state="judgement",
        src="02_dashboards/hub/ISZE_OS_Hub.html · 02_dashboards/sales/ISZE_After_Sales_Paper.html · this page",
    ),
]

FLAGGED = [
    dict(
        title="AIM classification completeness, 93.5%",
        wrong="Printed in `FACTS.md` (line 109), the master dashboard and the pricing pack as a March 2026 completeness figure. The basis is count-based and superseded; the source itself says it must not be compared with the revenue-weighted figure beside it.",
        here="This console publishes no AIM completeness percentage. The only classification statement on the page is the revenue-weighted residual (1.8% of 2025 revenue unclassified).",
    ),
    dict(
        title="The mixed-lane cell on the master dashboard",
        wrong="One cell puts an IML service-schedule cover figure (35.1%, on 1.25 services a year) beside a PRISM denominator (7,836, on a half-service basis). Two systems in one tile; the row beneath inherits it.",
        here="No service-schedule-lane figure appears on this console at all. Every capture figure here is the network lane, on one denominator, and the lane is named in the tooltip.",
    ),
    dict(
        title="A 43% parts collapse in 2026",
        wrong="The 2026 rows of the spend-per-unit file compare a part-year euro column with a full-year ceiling, so a year-on-year read shows a collapse that did not happen.",
        here="This console shows 2023, 2024 and 2025 only. The 2026 rows are excluded and the reason is stated on the decision row that owns the fix.",
    ),
    dict(
        title="A 2026–2030 vehicle forecast",
        wrong="The published forecast is 9% too high for 2026 and 59% too high for 2030, and 25% low for Israel in every year.",
        here="No forecast vehicle count appears anywhere on this page. Every denominator here is a measured 2025 figure.",
    ),
]

STATES = [
    ("measured", "Measured", "Counted in a file, from a named extract, on a stated date."),
    ("modelled", "Modelled", "Built from an assumption that is stated on the figure. A placeholder is a model."),
    ("excluded", "Excluded", "Would be wrong to publish. Named on the page, left out of the arithmetic."),
    ("judgement", "Needs a judgement", "The data is not the blocker. A person has to choose."),
]


def esc(s) -> str:
    return html.escape("" if s is None else str(s), quote=True)


def eur(v: float, dec: int = 0) -> str:
    return ("{:,.%df}" % dec).format(v).replace(",", " ")


def pct(v: float, dec: int = 1) -> str:
    return ("{:,.%df}" % dec).format(v)


def tip(title: str, formula: str, source: str, notincluded: str, state: str = "measured") -> str:
    return (
        '<span class="tip"><b>{t}</b>'
        '<span class="tr"><i>Formula</i>{f}</span>'
        '<span class="tr"><i>Snapshot &amp; source</i>{s}</span>'
        '<span class="tr warn"><i>Not included</i>{n}</span>'
        "</span>"
    ).format(t=title, f=formula, s=source, n=notincluded)


def kpi(value: str, title: str, formula: str, source: str, notincluded: str,
        state: str = "measured", cls: str = "") -> str:
    return (
        '<span class="kpi {state} {cls}" tabindex="0">{v}{tip}</span>'
    ).format(state=state, cls=cls, v=value,
             tip=tip(title, formula, source, notincluded, state))


# ---------------------------------------------------------------------------
# Chart builders — hand-built CSS bars. No chart library, no CDN.
# ---------------------------------------------------------------------------

def bar_rows(rows: list[tuple[str, float]], vmax: float, fmt, *, avg=None,
             avg_label: str = "", tipf=None, track_class: str = "") -> str:
    """rows = (label, value). Bars are CSS-width; every label and value is real text."""
    out = ['<div class="bars %s">' % track_class]
    for label, value in rows:
        w = max(0.4, 100.0 * value / vmax) if vmax else 0.0
        avgline = ('<span class="avg" style="left:{p:.2f}%"></span>'.format(p=100.0 * avg / vmax)
                   if avg is not None else "")
        if tipf:
            t, f, s, ni = tipf(label, value)
            valhtml = kpi(fmt(value), t, f, s, ni)
        else:
            valhtml = esc(fmt(value))
        out.append(
            '<div class="bar-row">'
            '<div class="bl">{label}</div>'
            '<div class="track"><span class="fill" style="width:{w:.2f}%"></span>{avgline}</div>'
            '<div class="bv">{val}</div>'
            "</div>".format(label=esc(label), w=w, avgline=avgline, val=valhtml)
        )
    if avg is not None:
        out.append('<div class="bar-avg"><span class="avg-key"></span>{l}</div>'.format(l=esc(avg_label)))
    out.append("</div>")
    return "".join(out)


def stacked(segments: list[tuple[str, float, str]], total: float, tipf=None) -> str:
    """segments = (label, value, colour-class)."""
    out = ['<div class="stack">']
    for label, value, cls in segments:
        w = 100.0 * value / total if total else 0.0
        out.append(
            '<span class="seg {cls}" style="width:{w:.3f}%"><span class="segl">{l}</span>'
            '<span class="segv">{v}</span></span>'.format(cls=cls, w=w, l=esc(label), v=esc(value))
        )
    out.append("</div>")
    return "".join(out)


def build() -> str:
    # ---- hero chips
    hero = [
        ("€" + eur(BILLED_2025), "Parts billed, CY2025", "18 measured markets",
         "Sum of net parts billed on the 2025 rows of gps_spu_by_distributor.csv that carry a vehicle-in-service basis.",
         "gps_spu_by_distributor.csv, 2025 rows, 18 of 22 distributors · snapshot 2026-09-16",
         "Four markets that bill parts but have no vehicle count, and Palestine. Credit-note and return lines excluded."),
        ("€" + eur(SPU_AVG, 2), "Spend per vehicle (GPS)", "Network average, CY2025",
         f"€{BILLED_2025:,.0f} ÷ {UIO_2025:,} vehicles in service (worksheet fleet).",
         "billed: gps_spu 18-market CY2025 · fleet: wallet_waterfall worksheet base · D08 2026-09-22",
         "Matched rate on the target-spend fleet (163,198), not the July GPS extract (163,459). Warranty included."),
        (eur(UIO_2025), "Vehicles in service (UIO)", "18 markets, CY2025",
         "Sum of uio_units on the 2025 target-spend (wallet) rows — worksheet base.",
         "wallet_waterfall.csv, 2025 · D08 rebuild 2026-09-22",
         "Ukraine, Armenia, Kazakhstan and Palestine bill parts with no count and are outside it."),
        (pct(CAPTURE_2025) + "%", "Cover of target spend",
         f"€{BILLED_2025 / 1e6:.2f}M of a €{CEILING_2025 / 1e6:.2f}M ceiling",
         f"Billed parts ÷ modelled target spend. €{BILLED_2025:,.0f} ÷ €{CEILING_2025:,.0f}.",
         "wallet_waterfall.csv, 2025 · ceiling re-derived 2026-09-22",
         f"{FLAT_SHARE_CEILING}% of the ceiling is one flat €250 per vehicle, so this is a direction, not a precision. Warranty is a separate lane."),
        ("€" + eur(UNCAPTURED), "Uncaptured spend value", "€22.28M of it is a flat placeholder",
         f"Ceiling minus billed across 18 markets, floored at zero per market. €{CEILING_2025:,.0f} − €{BILLED_2025:,.0f}.",
         "wallet_waterfall.csv, addressable uncaptured, 2025 · ceiling re-derived 2026-09-22",
         "Not a forecast and not cash. It moves with the ceiling assumption: €22.28M of that ceiling is one flat rate."),
        (pct(SPLIT_NOT_BOUGHT_PCT) + "%", "Service parts not bought", "714,094 of 996,890 expected units",
         "Expected units minus genuine and best-value units actually sold, 14 categories, 18 distributors. 996,890 − (197,666 + 85,130) = 714,094.",
         "pms_capture_by_db_year.csv, 2025, weighted by expected quantity · snapshot 2026-09-16",
         "Filters, brakes, clutch and the other eleven scored categories. It is not all parts, and a unit is not a euro."),
    ]
    hero_html = "".join(
        '<div class="hk" tabindex="0"><div class="v">{v}</div><div class="l">{l}</div>'
        '<div class="n">{n}</div>{t}</div>'.format(v=esc(v), l=esc(l), n=esc(n),
                                                   t=tip(l, f, s, ni))
        for (v, l, n, f, s, ni) in hero
    )

    # ---- sensor cards with breaks
    sensors = [
        ("01", "Car park &amp; vehicle identity", "UIO",
         "163,198 vehicles in service · 18 of 22 markets",
         "Feeds the loop with the denominator: how many vehicles exist to spend money on them at all.",
         [("Break — no vehicle count", "Ukraine, Armenia, Kazakhstan and Palestine bill parts but have no target-spend basis. Any spend-per-vehicle figure for them would be invented."),
          ("Break — no identity", "Israel and the UK are excluded from the VIN register by design. The register holds 3,238 vehicles in 7 markets (PT 2,111 · IE 647 · DE 183 · MT 130 · CY 114 · BE 49 · GR 4). The UK mail extract of 29,935 VINs is not loaded."),
          ("Break — no weight class", "The fleet bucket file carries one combined column of 36,793 trucks with no 3.5 t / 7.5 t split, so a measured per-class distance cannot reach the count.")],
         "vin/VIN_register_summary.json · uio_by_model_bucket.csv · gps_spu_by_distributor.csv"),
        ("02", "Demand &amp; capture", "PRISM",
         "14 service categories · 18 distributors",
         "Feeds the loop with expected demand per category, so billed euro can be read as a share of a plausible total.",
         [("Break — provisional factor", "The air-to-oil replacement ratio of 0.5 is provisional until the engine maker confirms it. Capture is comparable across categories, not locked."),
          ("Break — factor open", "The brake wear factor sits at 0.4 with 0.8 undecided. UK brake capture is not quotable as locked."),
          ("Break — one global distance", "Every category is computed on one global 20,000 km a year, against a measured 12,165 to 51,680 spread by truck class.")],
         "pms_capture_by_db_year.csv · pms_opportunity_matrix.csv · _data_integrity_open_issues.md"),
        ("03", "Part classification", "AIM",
         "Revenue-weighted residual 1.8% unclassified (2025)",
         "Feeds the loop with what a part is, so gaps can be grouped into families a distributor can act on.",
         [("Break — count basis superseded", "The 93.5% completeness figure of March 2026 is count-based, superseded, and is not used anywhere on this page."),
          ("Break — pricing-risk layer", "The pricing-risk score is a null result (a fitted replacement failed its backtest). It is not a key figure and does not appear here.")],
         "AIM gap report 2 Jul 2026 · DECISIONS.md · _archived_kpi_candidates.md"),
    ]
    sensor_cards = []
    for no, title, abbr, headline, role, breaks, src in sensors:
        bl = "".join(
            '<div class="break"><span class="bx">break</span><div><b>{t}</b><p>{p}</p></div></div>'.format(
                t=esc(t), p=p) for t, p in breaks)
        sensor_cards.append(
            '<article class="sensor">'
            '<div class="sh"><span class="sno">{no}</span><h3>{t}</h3><span class="sabbr">{a}</span></div>'
            '<div class="shl">{h}</div><p class="srole">{r}</p>{bl}'
            '<p class="ssrc">{s}</p></article>'.format(
                no=no, t=title, a=abbr, h=esc(headline), r=esc(role), bl=bl, s=esc(src))
        )

    # ---- loop diagram, wide (inline SVG) and narrow (text steps)
    loop_steps = [
        ("DATA", "Signals with a euro value, an owner field and a state.",
         "23,236 open opportunities · €22.1M on mixed bases"),
        ("DECISION", "A person chooses. The choice is written down with a date.",
         "13 rows waiting on this page · 0 decided"),
        ("ACTION", "The choice leaves the building: price, order, visit, file request.",
         "9 signal types in the ledger · 0 actioned"),
        ("RESULT", "Billing comes back and is compared with what the model expected.",
         "Billing horizon 2026-06-30 · outcomes not measurable past it"),
    ]
    loop_wire = [
        ("data→decision", "escalation: euro at stake, owner, state"),
        ("decision→action", "choice + owner + due date"),
        ("action→result", "orders, prices, visits"),
        ("result→data", "actual versus target, back into the loop"),
    ]
    loop_narrow = "".join(
        '<div class="step"><div class="stept">{t}</div><p>{d}</p><div class="stepn">{n}</div></div>'
        + ('<div class="wire"><span>{w}</span></div>'.format(w=esc(loop_wire[i][1])) if i < len(loop_steps) - 1 else
           '<div class="wire back"><span>{w}</span></div>'.format(w=esc(loop_wire[3][1])))
        for i, (t, d, n) in enumerate(loop_steps)
    )

    # ---- chart 1: spend per vehicle by market
    spu_max = 400.0
    c1 = bar_rows(
        [(m, v) for m, v, _, _, _ in SPU_2025], spu_max, lambda v: "€%.2f" % v,
        avg=SPU_AVG, avg_label="Network average €188.46 (dashed line)",
        tipf=lambda m, v: (
            "Spend per vehicle, %s" % m,
            "Parts billed ÷ vehicles in service, %s: €%s ÷ %s vehicles." % (
                m, eur([r[3] for r in SPU_2025 if r[0] == m][0]), eur([r[2] for r in SPU_2025 if r[0] == m][0])),
            "gps_spu_by_distributor.csv, 2025 · snapshot 2026-09-16",
            "Warranty parts are inside this figure. The target-spend ceiling is not: a high bar is spend, not cover."),
    )

    # ---- chart 2: growth split, diverging bars around a centre line
    vmax2 = 521030.0  # largest single move (volume, 2023→2024)
    c2_parts = []
    for label, vol, price, mix in GROWTH_SPLIT:
        total = vol + price + mix
        for sub, val, cls in (("more or fewer trucks (volume)", vol, "vol"),
                              ("price effect", price, "price")):
            w = 50.0 * abs(val) / vmax2
            left = 50.0 if val >= 0 else 50.0 - w
            c2_parts.append(
                '<div class="bar-row diverge"><div class="bl">{l}<span class="sub">{s}</span></div>'
                '<div class="track zero"><span class="fill {c}" style="left:{lf:.3f}%;width:{w:.3f}%"></span></div>'
                '<div class="bv">{v}</div></div>'.format(
                    l=esc(label), s=esc(sub), c=cls, lf=left, w=w,
                    v=("+" if val >= 0 else "\u2212") + "€" + eur(abs(val))))
        c2_parts.append(
            '<div class="bar-row diverge tot"><div class="bl">net change</div>'
            '<div class="track zero"><span class="fill net" style="left:{lf:.3f}%;width:{w:.3f}%"></span></div>'
            '<div class="bv">{v}</div></div>'.format(
                lf=(50.0 if total >= 0 else 50.0 - 50.0 * abs(total) / vmax2),
                w=50.0 * abs(total) / vmax2,
                v=("+" if total >= 0 else "\u2212") + "€" + eur(abs(total))))
    c2 = ('<div class="legendline">'
          '<span class="sw vol"></span>volume · <span class="sw price"></span>price · '
          '<span class="sw mix"></span>mix is not populated in the source file</div>'
          '<div class="centerrule"><span>centre line = no change</span></div>'
          + "".join(c2_parts))

    # ---- chart 3: capture vs uncaptured
    c3 = stacked(
        [("Captured " + pct(CAPTURE_2025) + "% — €" + eur(BILLED_2025), BILLED_2025, "cap"),
         ("Uncaptured €" + eur(UNCAPTURED), UNCAPTURED, "unc")],
        CEILING_2025) + (
        f'<div class="stacknote">One bar is the whole €{CEILING_2025 / 1e6:.2f}M ceiling. The grey end is the '
        f'€{UNCAPTURED / 1e6:.2f}M the network did not sell'
        f' against its own target. €{OVER_TARGET / 1e6:.2f}M of the book sits above target and is not shown as a negative.'
        f' {FLAT_MARKETS} markets holding €{FLAT_EURO / 1e6:.2f}M of that ceiling sit on one flat €250 a vehicle, '
        f'so the split is direction, not precision.</div>')

    # ---- chart 4: three-way service-part split
    c4 = stacked(
        [("Genuine 197,666 units", SPLIT_GENUINE, "gen"),
         ("Competitive parts 85,130", SPLIT_BVP, "bvp"),
         ("Not bought 714,094 — 71.6%", SPLIT_NOT_BOUGHT, "miss")],
        SPLIT_EXPECTED) + (
        '<div class="stacknote">Expected units across 14 scored service categories, 18 distributors, 2025: '
        '<b>996,890</b>. Of those, 282,796 were bought (197,666 genuine + 85,130 competitive) and '
        '<b>714,094 were not bought at all</b> — three units expected for every one sold. Competitive parts are '
        + pct(BVP_SHARE_SERVICE) + "% of what was bought in this universe, and "
        + pct(BVP_SHARE_ALL) + "% of the whole parts book.</div>")

    # ---- chart 5: layer visibility
    c5_rows = [
        ("Vehicle identity, VIN register", 100.0 * VIN_MARKETS / VIN_MARKETS_TOTAL,
         "%d of %d markets" % (VIN_MARKETS, VIN_MARKETS_TOTAL)),
        ("Vehicle count (the denominator)", 100.0 * FLEET_MARKETS / VIN_MARKETS_TOTAL,
         "%d of %d markets" % (FLEET_MARKETS, VIN_MARKETS_TOTAL)),
        ("Sales to dealer, 2025", S2D_PCT_5, pct(S2D_PCT_5) + "% of billed euro"),
        ("Service categories scored", 100.0, "14 of 14"),
        ("Weight class inside the count", 0.0, "none"),
    ]
    c5 = "".join(
        '<div class="bar-row"><div class="bl">{l}</div><div class="track">'
        '<span class="fill {cls}" style="width:{w:.2f}%"></span></div><div class="bv">{v}</div></div>'.format(
            l=esc(l), w=w, v=esc(v), cls="zero" if w == 0 else "")
        for l, w, v in c5_rows)

    # ---- chart 6: capture by market
    c6 = bar_rows(CAPTURE_BY_DB, 110.0, lambda v: pct(v) + "%",
                  tipf=lambda m, v: (
                      "Service-part capture, %s" % m,
                      "Actual units ÷ expected units across the 14 scored categories, weighted by expected units.",
                      "pms_summary_by_db.csv, 2025 · snapshot 2026-09-16",
                      "Network lane only, on one denominator. Ireland reads above 100% because its book includes demand from vehicles outside its own count: it is a signal, not a target. Not the service-schedule lane."))

    # ---- chart 7: category gaps
    c7 = bar_rows([(lab, v) for _, lab, v in CATEGORY_GAP], CATEGORY_GAP[0][2],
                  lambda v: "€" + eur(v),
                  tipf=lambda lab, v: (
                      "Uncaptured service-part value, %s" % lab,
                      "Expected units minus sold units at average selling price, summed over 18 distributors, 2025.",
                      "pms_opportunity_matrix.csv, 2025, 14 scored categories · snapshot 2026-09-16",
                      "The 14 scored categories only; total €18.22M. Not all parts, and the unit prices are averages, so it is not a euro forecast."))

    # ---- chart 8: weight-class distance
    c8 = bar_rows([(lab, v) for lab, v in WEIGHT_KM], 56000.0, lambda v: eur(v) + " km/yr",
                  avg=ASSUMED_KM, avg_label="The one global assumption in the model today: 20,000 km a year",
                  tipf=lambda lab, v: (
                      "%s — median annual distance" % lab,
                      "Median annual distance between the last two warranty odometer readings per vehicle, from claim files.",
                      "warranty_cv_km_age_by_market.csv, _cv_warranty_mileage_validation.md · 2026-09-16 · PROVISIONAL",
                      "A duplicate-sheet check is still pending, so treat as provisional. Claims-derived: only vehicles that claimed a warranty repair enter the sample. Israel's N35 column is empty because there are no 3.5 t trucks in that book."))

    # ---- queue table
    qrows = []
    for r in QUEUE:
        qrows.append(
            '<tr>'
            '<td class="qn" data-label="#">{n}</td>'
            '<td data-label="What the data says">{d}</td>'
            '<td data-label="Decision it implies">{dec}</td>'
            '<td data-label="Owner">{o}</td>'
            '<td data-label="Blocked by">{b}</td>'
            '<td class="qdate" data-label="Date">{due}</td>'
            '<td class="qstate" data-label="State"><span class="chip {st}">{stl}</span>'
            '<span class="qsrc">{src}</span></td>'
            "</tr>".format(n=r["n"], d=r["data"], dec=esc(r["decision"]), o=esc(r["owner"]),
                           b=esc(r["blocked"]), due=esc(r["due"]),
                           st=r["state"],
                           stl=esc(dict((s[0], s[1]) for s in STATES)[r["state"]]),
                           src=esc(r["src"])))

    # ---- ledger strip
    ledger_rows = "".join(
        '<div class="bar-row"><div class="bl">{l}</div>'
        '<div class="track"><span class="fill led" style="width:{w:.2f}%"></span></div>'
        '<div class="bv">{n} · €{v}</div></div>'.format(
            l=esc(l), w=100.0 * v / LEDGER_SIGNALS[0][2], n=eur(n), v=eur(v))
        for l, n, v in LEDGER_SIGNALS)

    # ---- honesty states
    state_html = "".join(
        '<div class="staterow"><span class="chip {k}">{lab}</span><p>{d}</p></div>'.format(
            k=k, lab=esc(lab), d=esc(d)) for k, lab, d in STATES)

    flagged_rows = "".join(
        '<div class="flagrow"><div class="fgt">{t}</div>'
        '<div class="fgw"><span class="fglab">Wrong elsewhere</span><p>{w}</p></div>'
        '<div class="fgh"><span class="fglab">What this page does instead</span><p>{h}</p></div></div>'.format(
            t=esc(f["title"]), w=f["wrong"], h=f["here"]) for f in FLAGGED)

    # ---- narrow loop break list (mobile): sensors stack above
    narrow_breaks = "".join(
        '<li>{s}</li>'.format(s=esc(t + " — " + p)) for _, _, _, _, _, breaks, _ in sensors for t, p in breaks)

    css = """
*{box-sizing:border-box}
html,body{margin:0;padding:0;-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{font-family:"Segoe UI",Helvetica,Arial,sans-serif;color:#222;background:#f7f4ee;font-size:14px;line-height:1.45}
h1,h2,h3,h4{font-family:Georgia,"Times New Roman",serif;color:#1a2b4a;margin:0}
.hero{background:linear-gradient(155deg,#15233c 0%,#203759 55%,#2b4a78 100%);color:#eef1f6;padding:34px 24px 24px}
.hero-inner{max-width:1240px;margin:0 auto}
.brand{font-family:Georgia,serif;font-size:12px;letter-spacing:.18em;text-transform:uppercase;color:#c9d4e6;margin-bottom:12px}
.hero h1{color:#fff;font-size:31px;line-height:1.1;margin:0 0 10px;font-weight:400}
.hero .rule{width:64px;height:3px;background:#c0552d;margin:0 0 14px}
.hero .lead{max-width:900px;font-size:14.5px;color:#d5dce8;margin:0 0 18px}
.hero-kpis{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:10px}
.hk{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.13);padding:11px 12px;position:relative}
.hk .v{font-size:23px;font-weight:700;letter-spacing:-.4px;color:#fff;line-height:1.1}
.hk .l{font-size:10.5px;text-transform:uppercase;letter-spacing:.05em;color:#aeb9cb;margin-top:5px}
.hk .n{font-size:11.5px;color:#9aa8bd;margin-top:5px;line-height:1.3}
.wrap{max-width:1240px;margin:0 auto;padding:24px 24px 70px}
h2{font-size:20px;margin:6px 0 6px;padding-bottom:7px;border-bottom:2px solid #1a2b4a}
h2 .no{color:#c0552d}
h3{font-size:14.5px}
.lead{color:#5d564b;margin:0 0 14px;max-width:980px}
.sub{color:#5d564b;margin:2px 0 12px;font-size:13px}
section{margin-bottom:34px}
.grid2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.grid3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}
.card{background:#fff;border:1px solid #d9d3c8;padding:14px 15px 12px;min-width:0}
.card h3{font-size:14px;margin:0 0 4px}
.card .cap{font-size:12px;color:#6b6256;margin:0 0 10px}
.card.wide{grid-column:1/-1}
/* tooltips */
.kpi{position:relative;display:inline-block;border-bottom:1px dotted #8a7f6d;cursor:help}
.kpi.measured{color:#1d6b4f;border-bottom-color:#1d6b4f}
.kpi.modelled{color:#8a6500;border-bottom-color:#8a6500}
.kpi.excluded{color:#6b6256;border-bottom-color:#6b6256}
.kpi.judgement{color:#a8451f;border-bottom-color:#c0552d}
.tip{display:none;position:absolute;left:0;top:calc(100% + 7px);width:min(330px,72vw);
 background:#15233c;color:#f7f4ee;border-top:3px solid #c0552d;padding:10px 12px;
 font-size:12px;line-height:1.42;z-index:60;box-shadow:0 8px 22px rgba(0,0,0,.28);text-align:left;font-weight:400}
.kpi:hover .tip,.kpi:focus .tip,.kpi:focus-within .tip{display:block}
.tip b{display:block;font-family:Georgia,serif;font-size:12.5px;color:#fff;margin-bottom:5px}
.tr{display:block;margin-top:4px}
.tr i{display:block;font-style:normal;text-transform:uppercase;letter-spacing:.06em;font-size:10px;color:#9aa8bd}
.tr.warn{color:#f2c5b4}
.tip-r .tip{left:auto;right:0}
/* bars */
.bars{display:block}
.bar-row{display:grid;grid-template-columns:132px minmax(0,1fr) 118px;gap:9px;align-items:center;margin:0 0 5px}
.bl{font-size:12px;color:#33302a;line-height:1.25;overflow-wrap:anywhere;min-width:0}
.track{position:relative;background:#efece5;height:16px;min-width:0;overflow:hidden}
.track.zero::before{content:"";position:absolute;left:50%;top:0;bottom:0;width:1px;background:#b9b2a5;z-index:2}
.fill{position:absolute;left:0;top:0;bottom:0;background:#15233c;display:block;max-width:100%}
.fill.vol{background:#15233c}
.fill.price{background:#c0552d}
.fill.mix{background:#888780}
.fill.net{background:#1a2b4a}
.fill.led{background:#2b4a78}
.fill.zero{background:#c0552d}
.bl .sub{display:block;font-size:10.5px;color:#6b6256;line-height:1.2}
.bar-row.tot .bl{font-weight:600;color:#15233c}
.bar-row.tot .bv{font-weight:700;color:#15233c}
.bar-row.tot .fill.net{background:#1a2b4a}
.centerrule{position:relative;height:0;border-top:1px dashed #b9b2a5;margin:6px 0 8px 132px}
.centerrule span{position:absolute;right:0;top:-8px;background:#fff;padding:0 4px;font-size:10px;color:#8a8172}
.avg{position:absolute;top:0;bottom:0;width:2px;background:#c0552d;z-index:3}
.bar-avg{display:grid;grid-template-columns:132px minmax(0,1fr) 118px;gap:9px;margin-top:8px}
.bar-avg span{grid-column:2;font-size:11.5px;color:#6b6256}
.avg-key{display:inline-block;width:12px;height:2px;background:#c0552d;vertical-align:middle;margin-right:6px}
.bv{font-size:12px;text-align:right;color:#222;white-space:nowrap;min-width:0;overflow-wrap:anywhere}
.bv .kpi{white-space:nowrap}
.bar-row .bv .tip{left:auto;right:0}
.bar-row:first-child .bv .tip{max-width:300px}
.legendline{font-size:11.5px;color:#6b6256;margin:0 0 8px}
.sw{display:inline-block;width:10px;height:10px;background:#15233c;margin-right:3px;vertical-align:-1px}
.sw.price{background:#c0552d}
.sw.mix{background:#888780}
/* stacks */
.stack{display:flex;width:100%;height:42px;border:1px solid #d9d3c8;overflow:hidden}
.seg{display:flex;flex-direction:column;justify-content:center;padding:0 8px;min-width:0;overflow:hidden}
.seg .segl{font-size:11.5px;line-height:1.2;white-space:normal;overflow-wrap:anywhere}
.seg .segv{font-size:11px;opacity:.85;line-height:1.2;overflow-wrap:anywhere}
.seg.cap{background:#15233c;color:#f7f4ee}
.seg.unc{background:#dcd7cd;color:#222}
.seg.gen{background:#15233c;color:#f7f4ee}
.seg.bvp{background:#c0552d;color:#fff}
.seg.miss{background:#e8e4dc;color:#222}
.stacknote{font-size:12px;color:#4a453d;margin:8px 0 0;line-height:1.45}
/* sensors */
.sensor{background:#fff;border:1px solid #d9d3c8;border-top:3px solid #1a2b4a;padding:13px 14px;min-width:0}
.sh{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap}
.sno{font-family:Georgia,serif;color:#c0552d;font-size:13px}
.sensor h3{font-size:14px;margin:0}
.sabbr{font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;background:#eef3f9;color:#1a4a7a;padding:2px 6px}
.shl{font-size:12.5px;color:#15233c;font-weight:600;margin:8px 0 4px}
.srole{font-size:12px;color:#5d564b;margin:0 0 10px}
.break{display:grid;grid-template-columns:44px minmax(0,1fr);gap:8px;border-left:3px solid #c0552d;padding:6px 0 6px 8px;margin-bottom:7px;background:#fdf7f4}
.bx{font-size:9.5px;letter-spacing:.09em;text-transform:uppercase;color:#c0552d;font-weight:700;padding-top:2px}
.break b{font-size:12px;display:block;color:#15233c}
.break p{margin:2px 0 0;font-size:12px;color:#33302a}
.ssrc{font-size:10.5px;color:#8a8172;margin:6px 0 0;line-height:1.35;overflow-wrap:anywhere}
/* loop */
.loop-wide{display:block}
.loop-narrow{display:none}
.loopbox{background:#fff;border:1px solid #d9d3c8;padding:10px 12px}
.loopbox .lt{font-family:Georgia,serif;color:#15233c;font-size:14px}
.loopbox .ld{font-size:11.5px;color:#4a453d;margin-top:3px}
.loopbox .ln{font-size:11px;color:#6b6256;margin-top:5px}
.step{background:#fff;border:1px solid #d9d3c8;border-left:4px solid #1a2b4a;padding:10px 12px}
.stept{font-family:Georgia,serif;color:#15233c;font-size:14px}
.step p{margin:3px 0 0;font-size:12.5px}
.stepn{font-size:11px;color:#6b6256;margin-top:5px}
.wire{font-size:11.5px;color:#c0552d;padding:5px 0 5px 14px;border-left:2px dashed #c0552d;margin-left:12px}
.wire.back{border-left:2px solid #c0552d;color:#15233c}
/* queue */
table.queue{width:100%;border-collapse:collapse;font-size:12.5px;background:#fff;table-layout:fixed}
.queue col.c1{width:32px}.queue col.c2{width:25%}.queue col.c3{width:22%}
.queue col.c4{width:12%}.queue col.c5{width:16%}.queue col.c6{width:64px}.queue col.c7{width:15%}
.queue thead th{background:#15233c;color:#f7f4ee;text-align:left;padding:8px 9px;font-size:10.5px;
 text-transform:uppercase;letter-spacing:.05em;font-weight:600}
.queue td{padding:8px 9px;border-bottom:1px solid #e8e4dc;color:#222;vertical-align:top;overflow-wrap:anywhere}
.queue tbody tr:nth-child(odd) td{background:#fff;color:#222}
.queue tbody tr:nth-child(even) td{background:#faf8f4;color:#222}
.qn{font-family:Georgia,serif;color:#c0552d;font-size:14px}
.qdate{white-space:nowrap;color:#33302a}
.qsrc{display:block;font-size:10px;color:#8a8172;margin-top:5px;overflow-wrap:anywhere}
/* chips */
.chip{display:inline-block;font-size:10px;text-transform:uppercase;letter-spacing:.05em;
 padding:2px 7px;font-weight:700;white-space:nowrap}
.chip.measured{background:#e4f5ee;color:#1d6b4f}
.chip.modelled{background:#fff3d6;color:#8a6500}
.chip.excluded{background:#eceae4;color:#444}
.chip.judgement{background:#f8e4dc;color:#8a3030}
/* honesty */
.staterow{display:grid;grid-template-columns:132px minmax(0,1fr);gap:10px;align-items:start;padding:6px 0;border-bottom:1px solid #e8e4dc}
.staterow p{margin:0;font-size:12.5px;color:#33302a}
.flagrow{display:grid;grid-template-columns:220px minmax(0,1fr) minmax(0,1fr);gap:12px;padding:10px 0;border-bottom:1px solid #e8e4dc}
.fgt{font-family:Georgia,serif;color:#15233c;font-size:13.5px}
.fglab{display:block;font-size:9.5px;letter-spacing:.08em;text-transform:uppercase;color:#c0552d;font-weight:700;margin-bottom:3px}
.flagrow p{margin:0;font-size:12px;color:#33302a;min-width:0;overflow-wrap:anywhere}
.foot{margin-top:26px;padding-top:12px;border-top:1px solid #d9d3c8;font-size:11px;color:#6b6256;line-height:1.6}
.small{font-size:11.5px;color:#5d564b}
ul.breaks{margin:6px 0 0;padding-left:18px}
ul.breaks li{font-size:12px;color:#33302a;margin-bottom:4px}
@media(max-width:1100px){
 .hero-kpis{grid-template-columns:repeat(3,minmax(0,1fr))}
 .grid3{grid-template-columns:repeat(2,minmax(0,1fr))}
 .flagrow{grid-template-columns:1fr 1fr}
 .fgt{grid-column:1/-1}
}
@media(max-width:900px){
 .grid2,.grid3{grid-template-columns:1fr}
 .loop-wide{display:none}
 .loop-narrow{display:block}
 .stacknote,.foot,.cap,.srole,.break p,.staterow p,.queue td,.ssrc{overflow-wrap:anywhere}
 table.queue{display:block;table-layout:auto}
 .queue colgroup,.queue thead{display:none}
 .queue tbody,.queue tr,.queue td{display:block;width:auto}
 .queue tr{border:1px solid #d9d3c8;border-left:4px solid #1a2b4a;background:#fff;margin-bottom:10px;padding:4px 2px}
 .queue tbody tr:nth-child(even) td,.queue tbody tr:nth-child(odd) td{background:transparent}
 .queue td{border-bottom:0;padding:4px 11px}
 .queue td[data-label]::before{content:attr(data-label);display:block;font-size:9.5px;
  letter-spacing:.07em;text-transform:uppercase;color:#c0552d;font-weight:700;margin-bottom:1px}
 .queue td.qn{font-size:16px;color:#c0552d;padding-bottom:0}
 .queue td.qn::before{content:"Decision "}
 .flagrow{grid-template-columns:1fr}
 .staterow{grid-template-columns:1fr}
}
@media(max-width:760px){
 .bar-row,.bar-avg{grid-template-columns:104px minmax(0,1fr) 92px;gap:6px}
 .bl,.bv{font-size:11px}
 .loop-wide{display:none}
 .loop-narrow{display:block}
}
@media(max-width:620px){
 .hero h1{font-size:24px}
 .hero-kpis{grid-template-columns:repeat(2,minmax(0,1fr))}
 .wrap,.hero{padding-left:14px;padding-right:14px}
 .bar-row,.bar-avg{grid-template-columns:minmax(0,1fr);gap:2px;margin-bottom:10px}
 .bl{font-size:12px;font-weight:600}
 .bv{text-align:left;font-size:11.5px;padding-left:0;white-space:normal}
 .bar-row .bv .tip,.bar-row:first-child .bv .tip{left:0;right:auto;max-width:min(300px,86vw)}
    .bar-avg span{grid-column:1}
    .avg{display:none}
    .centerrule{margin-left:0;border-top:0;height:0}
    .centerrule span{display:none}
 .stack{height:auto;flex-direction:column}
 .seg{width:100%!important;padding:6px 8px}
 .seg .segl,.seg .segv{font-size:11.5px}
 .tip{width:min(260px,86vw);font-size:11.5px}
 .chip{white-space:normal}
}
@media print{
 .tip{display:none!important}
 .loop-wide{display:block}
 .loop-narrow{display:none}
}
"""

    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Isuzu OS — operating console</title>
<style>{css}</style>
</head>
<body>
<div class="hero">
  <div class="hero-inner">
    <div class="brand">Isuzu Europe · aftersales OS</div>
    <h1>The operating console</h1>
    <div class="rule"></div>
    <p class="lead">The OS is the loop: data to decision to action to result, with the key figures as its instrument
    panel. The car park, PRISM and the classification layer are its sensors. This page is the loop, the instruments
    and the decisions waiting on a person. Figures are 2025 unless the label says otherwise.</p>
    <div class="hero-kpis">{hero_html}</div>
  </div>
</div>

<div class="wrap">

<section>
  <h2><span class="no">01</span> · The loop, and where the sensors are blind</h2>
  <p class="lead">Three sensors feed one loop. A blind sensor is drawn as a break in the line, not as a footnote:
  the loop runs on what is measured and the break stays visible in the picture.</p>

  <div class="loop-wide">
  <svg viewBox="0 0 1200 520" role="img" aria-label="The operating loop: three sensors feed data, decision, action and result, with the instrument panel attached">
    <defs>
      <marker id="ah" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto">
        <path d="M0,0 L9,4.5 L0,9 z" fill="#15233c"/>
      </marker>
      <marker id="ahr" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto">
        <path d="M0,0 L9,4.5 L0,9 z" fill="#c0552d"/>
      </marker>
    </defs>
    <text x="16" y="24" font-family="Georgia,serif" font-size="15" fill="#15233c">Sensors — what the loop can see</text>
    <text x="470" y="24" font-family="Georgia,serif" font-size="15" fill="#15233c">The loop — what the business does</text>
    <text x="985" y="24" font-family="Georgia,serif" font-size="15" fill="#15233c">Instruments</text>

    <rect x="16" y="40" width="330" height="140" fill="#fff" stroke="#d9d3c8"/>
    <rect x="16" y="40" width="4" height="140" fill="#1a2b4a"/>
    <text x="32" y="64" font-size="13" fill="#15233c" font-weight="700">Car park &amp; vehicle identity</text>
    <text x="32" y="84" font-size="12" fill="#33302a">163,198 vehicles in service</text>
    <text x="32" y="102" font-size="12" fill="#33302a">18 of 22 markets have a count</text>
    <text x="32" y="126" font-size="11" fill="#c0552d">Break 1 — no count: 4 markets bill, no denominator</text>
    <text x="32" y="144" font-size="11" fill="#c0552d">Break 2 — no identity: Israel + UK out of the register</text>
    <text x="32" y="162" font-size="11" fill="#c0552d">Break 3 — no weight class: one combined truck column</text>

    <rect x="16" y="196" width="330" height="140" fill="#fff" stroke="#d9d3c8"/>
    <rect x="16" y="196" width="4" height="140" fill="#1a2b4a"/>
    <text x="32" y="220" font-size="13" fill="#15233c" font-weight="700">Demand &amp; capture (PRISM)</text>
    <text x="32" y="240" font-size="12" fill="#33302a">14 service categories · 18 distributors</text>
    <text x="32" y="258" font-size="12" fill="#33302a">996,890 expected units in 2025</text>
    <text x="32" y="282" font-size="11" fill="#c0552d">Break 4 — air-to-oil factor 0.5 provisional</text>
    <text x="32" y="300" font-size="11" fill="#c0552d">Break 5 — brake wear factor 0.4 vs 0.8 undecided</text>
    <text x="32" y="318" font-size="11" fill="#c0552d">Break 6 — one global 20,000 km against a 3.7× spread</text>

    <rect x="16" y="352" width="330" height="104" fill="#fff" stroke="#d9d3c8"/>
    <rect x="16" y="352" width="4" height="104" fill="#1a2b4a"/>
    <text x="32" y="376" font-size="13" fill="#15233c" font-weight="700">Part classification (AIM)</text>
    <text x="32" y="396" font-size="12" fill="#33302a">1.8% of 2025 revenue unclassified</text>
    <text x="32" y="420" font-size="11" fill="#c0552d">Break 7 — the 93.5% count figure is superseded</text>
    <text x="32" y="438" font-size="11" fill="#c0552d">Break 8 — pricing-risk score is a null result</text>

    <line x1="346" y1="110" x2="404" y2="150" stroke="#15233c" stroke-width="1.6" marker-end="url(#ah)"/>
    <line x1="346" y1="266" x2="404" y2="216" stroke="#15233c" stroke-width="1.6" marker-end="url(#ah)"/>
    <line x1="346" y1="404" x2="404" y2="256" stroke="#15233c" stroke-width="1.6" marker-end="url(#ah)"/>
    <text x="352" y="536" font-size="0" fill="none">.</text>

    <rect x="410" y="96" width="240" height="96" fill="#fff" stroke="#d9d3c8"/>
    <text x="424" y="120" font-size="13.5" fill="#15233c" font-weight="700">1 · DATA</text>
    <text x="424" y="140" font-size="11.5" fill="#33302a">Billed euro, expected demand, vehicle count</text>
    <text x="424" y="158" font-size="11.5" fill="#33302a">and state. 23,236 open opportunities, €22.1M</text>
    <text x="424" y="176" font-size="11.5" fill="#33302a">on mixed bases — an inventory, not yet a queue.</text>

    <rect x="700" y="96" width="240" height="96" fill="#fff" stroke="#d9d3c8"/>
    <text x="714" y="120" font-size="13.5" fill="#15233c" font-weight="700">2 · DECISION</text>
    <text x="714" y="140" font-size="11.5" fill="#33302a">A person chooses and writes it down with an</text>
    <text x="714" y="158" font-size="11.5" fill="#33302a">owner and a date. 13 decisions wait on this</text>
    <text x="714" y="176" font-size="11.5" fill="#33302a">page. None decided. The decisions file is empty.</text>

    <rect x="700" y="252" width="240" height="96" fill="#fff" stroke="#d9d3c8"/>
    <text x="714" y="276" font-size="13.5" fill="#15233c" font-weight="700">3 · ACTION</text>
    <text x="714" y="296" font-size="11.5" fill="#33302a">Price, order, dealer visit, file request. The</text>
    <text x="714" y="314" font-size="11.5" fill="#33302a">choice leaves the building here. 0 of 23,236</text>
    <text x="714" y="332" font-size="11.5" fill="#33302a">ledger rows carry an action.</text>

    <rect x="410" y="252" width="240" height="96" fill="#fff" stroke="#d9d3c8"/>
    <text x="424" y="276" font-size="13.5" fill="#15233c" font-weight="700">4 · RESULT</text>
    <text x="424" y="296" font-size="11.5" fill="#33302a">Billing returns as actual against target spend</text>
    <text x="424" y="314" font-size="11.5" fill="#33302a">per vehicle. Billing horizon 2026-06-30;</text>
    <text x="424" y="332" font-size="11.5" fill="#33302a">nothing past it is measurable and is left null.</text>

    <line x1="650" y1="144" x2="694" y2="144" stroke="#15233c" stroke-width="1.6" marker-end="url(#ah)"/>
    <text x="652" y="132" font-size="10.5" fill="#6b6256">euro at stake, owner, state</text>
    <line x1="820" y1="192" x2="820" y2="246" stroke="#15233c" stroke-width="1.6" marker-end="url(#ah)"/>
    <text x="826" y="222" font-size="10.5" fill="#6b6256">choice + owner + date</text>
    <line x1="694" y1="300" x2="656" y2="300" stroke="#15233c" stroke-width="1.6" marker-end="url(#ah)"/>
    <text x="600" y="292" font-size="10.5" fill="#6b6256">orders, prices, visits</text>
    <path d="M400 350 L400 430 L530 430 L530 196" fill="none" stroke="#c0552d" stroke-width="1.6"
          stroke-dasharray="5 4" marker-end="url(#ahr)"/>
    <text x="404" y="422" font-size="10.5" fill="#c0552d">feedback — actual vs target, back into the data</text>

    <rect x="966" y="40" width="218" height="252" fill="#fff" stroke="#d9d3c8" stroke-top="3"/>
    <rect x="966" y="40" width="218" height="4" fill="#c0552d"/>
    <text x="982" y="66" font-size="13" fill="#15233c" font-weight="700">Instrument panel</text>
    <text x="982" y="86" font-size="11" fill="#33302a">8 charts on this page:</text>
    <text x="982" y="104" font-size="11" fill="#33302a">spend per vehicle by market (18)</text>
    <text x="982" y="120" font-size="11" fill="#33302a">capture rate by market (18)</text>
    <text x="982" y="136" font-size="11" fill="#33302a">category gap (14 categories)</text>
    <text x="982" y="152" font-size="11" fill="#33302a">growth split three ways</text>
    <text x="982" y="168" font-size="11" fill="#33302a">cover vs uncaptured value</text>
    <text x="982" y="184" font-size="11" fill="#33302a">three-way service-part split</text>
    <text x="982" y="200" font-size="11" fill="#33302a">layer visibility (4 sensors)</text>
    <text x="982" y="216" font-size="11" fill="#33302a">distance by weight class</text>
    <text x="982" y="240" font-size="11" fill="#c0552d">The instruments read the loop.</text>
    <text x="982" y="256" font-size="11" fill="#c0552d">They are not the loop.</text>
    <text x="982" y="278" font-size="11" fill="#33302a">Panel state: 6 key figures,</text>
    <text x="982" y="292" font-size="11" fill="#33302a">4 of them modelled or needing</text>

    <rect x="966" y="308" width="218" height="148" fill="#fdf7f4" stroke="#c0552d"/>
    <text x="982" y="332" font-size="13" fill="#15233c" font-weight="700">Decision queue</text>
    <text x="982" y="352" font-size="11" fill="#33302a">13 rows · 1 due this week</text>
    <text x="982" y="368" font-size="11" fill="#33302a">5 are open data gaps</text>
    <text x="982" y="384" font-size="11" fill="#33302a">6 need a person to choose</text>
    <text x="982" y="400" font-size="11" fill="#33302a">2 are publication choices</text>
    <text x="982" y="424" font-size="11" fill="#c0552d">A break in a sensor line</text>
    <text x="982" y="438" font-size="11" fill="#c0552d">becomes a row here.</text>
  </svg>
  </div>

  <div class="loop-narrow">
    <div class="grid3" style="margin-bottom:14px">{narrow_sensors}</div>
    <div class="step"><div class="stept">1 · DATA</div><p>Billed euro, expected demand, vehicle count and state. 23,236 open opportunities, €22.1M on mixed bases.</p></div>
    <div class="wire">euro at stake, owner, state</div>
    <div class="step"><div class="stept">2 · DECISION</div><p>A person chooses and writes it down with an owner and a date. 13 decisions wait on this page; the decisions file is empty.</p></div>
    <div class="wire">choice + owner + date</div>
    <div class="step"><div class="stept">3 · ACTION</div><p>Price, order, dealer visit, file request. 0 of 23,236 ledger rows carry an action.</p></div>
    <div class="wire">orders, prices, visits</div>
    <div class="step"><div class="stept">4 · RESULT</div><p>Billing returns as actual against target spend per vehicle. Billing horizon 2026-06-30; nothing past it is measurable.</p></div>
    <div class="wire back">feedback — actual vs target, back into the data</div>
    <div class="card" style="margin-top:14px"><h3>Sensors and their breaks</h3>
      <ul class="breaks">{narrow_breaks}</ul></div>
  </div>
</section>

<section>
  <h2><span class="no">02</span> · The instrument panel</h2>
  <p class="lead">Eight instruments. Every bar carries its value; every figure carries its formula, its source and
  what it leaves out.</p>

  <div class="grid2">
    <div class="card wide">
      <h3>Chart 1 — What does a vehicle in each market actually spend on parts?</h3>
      <p class="cap">Parts billed per vehicle in service, 2025, 18 markets, sorted. Dashed line = network average.</p>
      {c1}
    </div>

    <div class="card">
      <h3>Chart 2 — How much of the change was more trucks, price, or real volume?</h3>
      <p class="cap">Year-on-year parts revenue split, whole network, € per year.</p>
      {c2}
    </div>

    <div class="card">
      <h3>Chart 3 — How much of the target spend did the network capture?</h3>
      <p class="cap">Billed parts against the modelled target-spend ceiling, 2025, 18 markets.</p>
      {c3}
    </div>

    <div class="card wide">
      <h3>Chart 4 — Of the service parts that were expected to be sold, how many were not bought at all?</h3>
      <p class="cap">Expected units against genuine and competitive units actually sold, 14 scored categories, 18 distributors, 2025.</p>
      {c4}
    </div>

    <div class="card">
      <h3>Chart 5 — How much of the book does each sensor actually see?</h3>
      <p class="cap">Coverage of the four sensors, as a share of the thing each one is supposed to cover.</p>
      {c5}
      <p class="small" style="margin-top:8px">Vehicle identity: 3,238 vehicles across 7 markets, plus a UK mail extract of
      29,935 VINs that is not loaded. A zero bar means the split does not exist in the file, not that it is small.</p>
    </div>

    <div class="card">
      <h3>Chart 6 — Which markets capture the least of their own service demand?</h3>
      <p class="cap">Weighted capture across 14 service categories, 2025, 18 distributors, sorted.</p>
      {c6}
    </div>

    <div class="card">
      <h3>Chart 7 — Where is the uncaptured service-part value concentrated?</h3>
      <p class="cap">Uncaptured value by service category, 2025, 14 scored categories, €18.22M in total.</p>
      {c7}
    </div>

    <div class="card wide">
      <h3>Chart 8 — Is one global distance assumption defensible across a mixed fleet?</h3>
      <p class="cap">Median annual distance by truck class, measured from warranty odometer readings. PROVISIONAL — a duplicate-sheet check is pending. Dashed line = the single global assumption the model uses today.</p>
      {c8}
    </div>
  </div>
</section>

<section>
  <h2><span class="no">03</span> · What the action ledger holds</h2>
  <p class="lead">The loop's action end already has an inventory. It has no triage: every row sits in state NEW and the
  decisions file is empty, so no outcome can be measured.</p>
  <div class="grid2">
    <div class="card">
      <h3>Open opportunities by signal, and the euro attached</h3>
      <p class="cap">23,236 open rows, €22.1M at stake on mixed bases — the euro total is not one comparable sum.</p>
      {ledger_rows}
      <p class="small" style="margin-top:8px">Run 20260825T175229Z_48a077 · billing horizon 2026-06-30 · 0 rejects ·
      all 23,236 rows in state NEW · 0 outcomes.</p>
    </div>
    <div class="card">
      <h3>Why nothing can close yet</h3>
      <div class="staterow"><span class="chip measured">Measured</span><p>Billing spine complete through 2026-06-30, nine
      source surfaces green, 23,236 rows built and backfilled.</p></div>
      <div class="staterow"><span class="chip excluded">Excluded</span><p>Any outcome past the billing horizon. Those rows
      stay not-measurable with a null result and are never estimated.</p></div>
      <div class="staterow"><span class="chip judgement">Needs a judgement</span><p>Triage. Own, defer or drop the top of
      the ledger. That is a decision, not a data gap — and it is the reason the action half of the loop is still empty.</p></div>
    </div>
  </div>
</section>

<section>
  <h2><span class="no">04</span> · The decision queue</h2>
  <p class="lead">13 decisions the OS is waiting on. Five come from the open data-gap register, the rest from the
  assumption and ownership work of 16 September. Nothing here is invented: the source file is on every row.</p>
  <table class="queue">
    <colgroup><col class="c1"><col class="c2"><col class="c3"><col class="c4"><col class="c5"><col class="c6"><col class="c7"></colgroup>
    <thead><tr><th>#</th><th>What the data says</th><th>Decision it implies</th><th>Owner</th><th>Blocked by</th><th>Date</th><th>State · source</th></tr></thead>
    <tbody>{qrows}</tbody>
  </table>
</section>

<section>
  <h2><span class="no">05</span> · Honesty layer</h2>
  <p class="lead">Four states on every figure on this page, then the figures that are wrong elsewhere in the estate
  and what this page does instead.</p>
  <div class="grid2">
    <div class="card">
      <h3>The four states</h3>
      {state_html}
    </div>
    <div class="card">
      <h3>Where this page's figures sit</h3>
      <div class="staterow"><span class="chip measured">Measured</span><p>Parts billed €30.76M · vehicles 163,198 · spend
      per vehicle €188.46 · the 18-market spend league · 54.4% sales-to-dealer visibility · 23,236 ledger rows.</p></div>
      <div class="staterow"><span class="chip modelled">Modelled</span><p>The {CEILING} target-spend ceiling and everything
      derived from it ({COVER} cover, {UNCAP} uncaptured) · the 996,890 expected service units · category gaps at average
      selling price.</p></div>
      <div class="staterow"><span class="chip excluded">Excluded</span><p>2026 rows of the spend-per-unit file · every
      2026–2030 vehicle forecast · the AIM completeness percentage · the pricing-risk score · the service-schedule
      capture lane.</p></div>
      <div class="staterow"><span class="chip judgement">Needs a judgement</span><p>Which age basis goes on a tile · the
      sales-to-dealer denominator · the flat-target ceiling · the mileage default · which page is the aftersales front
      page · ledger triage.</p></div>
    </div>
  </div>

  <div class="card" style="margin-top:14px">
    <h3>Figures that are wrong elsewhere in the estate</h3>
    <p class="cap">Four known defects that a reader of other pages will meet. Each one is stated, not repeated.</p>
    {flagged_rows}
  </div>
</section>

<p class="foot">
Built {snapshot} by <code>build_os_console.py</code> — rebuild rather than edit the HTML.
Sources, all re-derived on {snapshot}: <code>gps_spu_by_distributor.csv</code> ·
<code>wallet_waterfall.csv</code> · <code>pms_capture_by_db_year.csv</code> ·
<code>pms_summary_by_db.csv</code> · <code>pms_opportunity_matrix.csv</code> ·
<code>mix_genuine_bvp_by_group.csv</code> · <code>revenue_waterfall.csv</code> ·
<code>dealer_sellout_gps_2025.csv</code> · <code>warranty_cv_km_age_by_market.csv</code> ·
<code>uio_by_model_bucket.csv</code> · <code>VIN_register_summary.json</code> ·
<code>action_ledger_open.csv</code> · <code>action_ledger.meta.json</code> ·
<code>_data_integrity_open_issues.md</code> · <code>OWNED_NUMBER_SHORTLIST_20260916.md</code> ·
<code>_cv_warranty_mileage_validation.md</code> · <code>_assumption_reversibility_spec.md</code> ·
<code>V20_SPEC.md</code>.
No customer names, no dealer names, no line-level billing, no personal data. The 2026–2030 vehicle forecast is
deliberately absent: the direction of its error is confirmed and its endpoint is not.
</p>
</div>
</body>
</html>
""".format(css=css, hero_html=hero_html, narrow_sensors="".join(sensor_cards),
           narrow_breaks=narrow_breaks, c1=c1, c2=c2, c3=c3, c4=c4, c5=c5, c6=c6, c7=c7, c8=c8,
           qrows="".join(qrows), ledger_rows=ledger_rows, state_html=state_html,
           flagged_rows=flagged_rows, snapshot=SNAPSHOT,
           # Derived from wallet_waterfall.csv at build time, so a pipeline change cannot leave
           # this page quoting a superseded ceiling.
           CEILING="€%.2fM" % (CEILING_2025 / 1e6),
           COVER="%.1f%%" % CAPTURE_2025,
           UNCAP="€%.2fM" % (UNCAPTURED / 1e6))


def main() -> None:
    html_out = build()
    # No CDN, no external request anywhere in the file.
    for bad in ('src="http', "src='http", 'href="http', "href='http", "url(http", "<script src"):
        if bad in html_out:
            raise SystemExit("External reference leaked into the HTML: %s" % bad)
    if "<canvas" in html_out:
        raise SystemExit("Canvas found — this page must use hand-built bars only")
    OUT_HTML.write_text(html_out, encoding="utf-8")
    OUT_CMD.write_text(
        '@echo off\r\nstart "" "%~dp0' + OUT_HTML.name + '"\r\n',
        encoding="utf-8",
        newline="",
    )
    n_charts = 8
    print("Wrote %s" % OUT_HTML)
    print("Wrote %s" % OUT_CMD)
    print("charts=%d queue_rows=%d sensors=%d bytes=%d" % (
        n_charts, len(QUEUE), 3, len(html_out)))


if __name__ == "__main__":
    main()
