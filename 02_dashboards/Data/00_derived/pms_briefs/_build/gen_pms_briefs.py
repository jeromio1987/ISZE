# Generate per-distributor PMS capture briefs + ranked summary.
# Canonical sources only (do NOT recompute from raw billing):
#   pms_summary_by_db.csv        -- per-DB 2025 rollup (PRISM authority)
#   pms_capture_by_db_year.csv   -- per category/line_type detail
#   pms_opportunity_matrix.csv   -- DB -> country/region
# Method (FACTS.md sec.2 / metric_dictionary sec.PMS): expected = UIO x svc/yr x 70% addressable
#   (N75 = 0.5 svc/yr, LCV = 1.0). capture = actual/expected (uncapped).
#   € gap = sum over PMS categories of (expected-actual)*avg_sp, floored at 0 (target = 100% capture).
# Pipeline gate: _verification_report.md must be green (103/0/0, 2026-06-13) -- checked before running.

import csv, os

DERIVED = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\derived"
OUT_BRIEFS = os.path.join(DERIVED, "pms_briefs")
OUT_OKF = r"C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\_OKF_assessment"
YEAR = "2025"  # latest full year (CY2025 complete; FY2025 still partial -- do not use FY)

os.makedirs(OUT_BRIEFS, exist_ok=True)
os.makedirs(OUT_OKF, exist_ok=True)


def rows(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


summary = rows(os.path.join(DERIVED, "pms_summary_by_db.csv"))
capture = rows(os.path.join(DERIVED, "pms_capture_by_db_year.csv"))
oppm = rows(os.path.join(DERIVED, "pms_opportunity_matrix.csv"))

# DB -> (country, region)
geo = {}
for r in oppm:
    geo.setdefault(r["distributor_code"], (r.get("country", ""), r.get("region", "")))

# DB -> list of 2025 total-line category rows
det = {}
for r in capture:
    if r["year"] == YEAR and r["line_type"] == "total":
        det.setdefault(r["distributor_code"], []).append(r)

CAT_LABEL = {
    "oil_filter": "Oil filter", "fuel_filter": "Fuel filter", "air_filter": "Air filter",
    "urea_filter": "Urea/AdBlue filter", "blower_filter": "Blower filter",
    "brake_pad": "Brake pad", "brake_shoe": "Brake shoe", "clutch_disc": "Clutch disc",
    "clutch_pressure_plate": "Clutch pressure plate", "clutch_kit": "Clutch kit",
    "release_bearing": "Release bearing", "pilot_bearing": "Pilot bearing",
    "clutch_booster": "Clutch booster",
}

ACTION_BY_CAT = {
    "urea_filter": "Range & stock genuine AdBlue/urea filters (capture near zero)",
    "brake_shoe": "Validate brake-shoe fitment first (~0% capture network-wide) before sizing",
    "brake_pad": "Genuine brake retention pilot (pads)",
    "clutch_disc": "Genuine clutch range push (disc capture very low)",
    "clutch_pressure_plate": "Genuine clutch range push (pressure plate / kit)",
    "clutch_kit": "Promote genuine clutch kits vs BVP",
    "clutch_booster": "Stock clutch boosters (near-zero capture)",
    "air_filter": "Low priority - air-filter gap inflated by flat service interval (flag C)",
    "oil_filter": "Defend genuine oil-filter mix vs BVP (capture already saturated)",
    "fuel_filter": "Defend genuine fuel-filter mix vs BVP",
    "release_bearing": "Bundle release bearing into clutch-kit sales",
    "pilot_bearing": "Minor - bundle with clutch",
    "blower_filter": "Minor cabin/blower filter line",
}

# Bespoke top actions for headline / distorted distributors
ACTION_OVERRIDE = {
    "ITUK": "Filters saturated (oil 162%, fuel 206%) - drive genuine MIX + a brake-shoe/clutch wear-parts retention pilot (ISZJ). Not a capture-deficit story.",
    "IUK": "Largest € ceiling but LCV-scope & assumption-sensitive - validate LCV service rate with IML before treating as winnable; focus genuine clutch/brake.",
    "UMI": "Fix the genuine/warranty DATA gap first (genuine 1.1%); € gap is directional only. BVP/aftermarket-dominant channel.",
    "UTI": "BVP-only channel (genuine 2.2%, total 112%) - capture saturated on BVP; genuine upsell limited. Treat genuine gap as low-confidence.",
}

SRC_LABEL = {"ituk_dvla_2026": "own DVLA registration (Mar 2026)", "v18_actual": "central v18 parc model"}


def confidence(db, gen, src):
    if src.startswith("ituk_dvla"):
        return "HIGH", "own DVLA registration UIO (Mar 2026)"
    if db == "UMI":
        return "LOW", "genuine capture 1.1% - genuine/warranty data gap; € gap directional only"
    if db == "UTI":
        return "LOW", "~100% BVP channel (genuine 2.2%) - genuine capture not meaningful"
    if db == "IUK":
        return "MED", "central v18 parc-model UIO; LCV scope (1.0 svc/yr) - € gap assumption-sensitive"
    return "MED", "central v18 parc-model UIO (not own-registration)"


def f_eur(x):
    return "€{:,.0f}".format(x)


def f_pct(x):
    return "{:.1f}%".format(x * 100)


recs = []
for s in summary:
    db = s["distributor_code"]
    uio = int(float(s["uio_units"]))
    tot = float(s["capture_rate_total_wtd"])
    gen = float(s["capture_rate_genuine_wtd"])
    oilc = float(s["oil_filter_capture"])
    gap = float(s["revenue_gap_eur_sum"])
    country, region = geo.get(db, ("", ""))

    drows = det.get(db, [])
    scope = drows[0]["scope"] if drows else "N75_only"
    src = drows[0]["uio_source"] if drows else "v18_actual"
    svc = "1.0" if scope == "LCV_only" else "0.5"
    scope_lbl = "LCV (1.0 svc/yr)" if scope == "LCV_only" else "N75 (0.5 svc/yr)"

    # top €-gap categories (total line)
    cats = sorted(drows, key=lambda r: float(r["revenue_gap_eur"]), reverse=True)
    top = [r for r in cats if float(r["revenue_gap_eur"]) > 0][:5]
    top_cat = top[0]["pms_category"] if top else "oil_filter"

    conf, conf_reason = confidence(db, gen, src)
    action = ACTION_OVERRIDE.get(db, ACTION_BY_CAT.get(top_cat, "Review weak categories"))

    # narrative read
    if gen < 0.05:
        read = "Channel is BVP/aftermarket: genuine capture is effectively nil, so the € gap is **directional, not winnable as genuine**. Total/BVP saturation, not a genuine-capture deficit."
    elif tot >= 1.0:
        read = "Blended N75 demand is **saturated** (total capture >=100%). The residual € gap is a handful of weak wear/urea categories plus genuine-vs-BVP mix - not a headline capture deficit."
    elif oilc >= 1.0:
        read = "Consumable filters are saturated; the gap sits in **wear parts** (brake/clutch) and urea. Real headroom, but validate fitment and net off BVP retention before sizing."
    else:
        read = "Genuine capture sits below expected demand across filters and wear parts - genuine headroom exists, but a large share is already retained in-tent via BVP (not a loss)."

    genbvp_pp = (tot - gen) * 100

    # ---- per-DB brief ----
    lines = []
    lines.append("# PMS Capture - {} ({}{})".format(db, country, ", " + region if region else ""))
    lines.append("")
    lines.append("**Year:** CY{} (latest full year) | **Source:** `pms_capture_by_db_year.csv` (PRISM, verify 103/0 2026-06-13) | **Cust id:** {}".format(
        YEAR, {"IUK": "2574", "ITUK": "2575"}.get(db, "-")))
    lines.append("")
    lines.append("## Headline")
    lines.append("- **UIO (denominator):** {:,} - {} | scope **{}** x 70% addressable".format(uio, SRC_LABEL.get(src, src), scope_lbl))
    lines.append("- **Total capture:** {} | **Genuine capture:** {} | genuine->total gap: {:.0f} pp".format(f_pct(tot), f_pct(gen), genbvp_pp))
    lines.append("- **Oil-filter capture:** {}".format(f_pct(oilc)))
    lines.append("- **€ addressable gap to 100% capture** (PMS categories, gross SP): **{}**".format(f_eur(gap)))
    lines.append("- **Data confidence:** {} - {}".format(conf, conf_reason))
    lines.append("")
    lines.append("## Where the € gap sits (CY{}, total line)".format(YEAR))
    lines.append("")
    lines.append("| Category | Capture | € gap |")
    lines.append("|---|---:|---:|")
    for r in top:
        lines.append("| {} | {} | {} |".format(
            CAT_LABEL.get(r["pms_category"], r["pms_category"]),
            f_pct(float(r["capture_rate"])), f_eur(float(r["revenue_gap_eur"]))))
    if not top:
        lines.append("| _(no category below 100% capture)_ | - | € 0 |")
    lines.append("")
    lines.append("## Read")
    lines.append(read)
    lines.append("")
    lines.append("## Top action")
    lines.append(action)
    lines.append("")
    caveats = []
    if any(r["pms_category"] == "air_filter" for r in top):
        caveats.append("air-filter gap inflated by flat service interval (integrity flag C) - not cross-category comparable")
    if any(r["pms_category"] == "brake_shoe" for r in top):
        caveats.append("brake-shoe capture ~0% across the whole network - likely fitment/availability, not a real winnable gap")
    if scope == "LCV_only":
        caveats.append("LCV scope (1.0 svc/yr) - € ceiling sensitive to the service-rate assumption")
    caveats.append("€ gap is gross SP to 100% capture (theoretical ceiling), before any realistic pilot target (+1% filters / +3% wear) and before netting BVP in-tent retention")
    lines.append("_Caveats: " + "; ".join(caveats) + "._")
    lines.append("")

    with open(os.path.join(OUT_BRIEFS, "{}_pms_capture.md".format(db)), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    recs.append(dict(db=db, country=country, uio=uio, tot=tot, gen=gen, gap=gap,
                     conf=conf, action=action, scope=scope))

# ---- ranked summary ----
recs.sort(key=lambda r: r["gap"], reverse=True)
total_gap = sum(r["gap"] for r in recs)

S = []
S.append("# PMS Capture - All Distributors (CY{})".format(YEAR))
S.append("")
S.append("**Generated from PRISM canonical derived data** (`01_data/derived/`), pipeline green **103 pass / 0 fail (2026-06-13)**. "
         "Expected demand = UIO x svc/yr x 70% addressable (N75 0.5 / LCV 1.0; FACTS.md sec.2). "
         "€ gap = sum over PMS categories of (expected-actual) x avg SP, floored at 0 = the cost of closing to **100% capture** "
         "(a theoretical ceiling, not a forecast). Capture is uncapped. Reconciles to FACTS.md sec.1 for ITUK.")
S.append("")
S.append("**Confidence key:** HIGH = own external-registration UIO (ITUK/DVLA). MED = central v18 parc-model UIO (real, network-standard, "
         "but not own-registration). LOW = v18 UIO **and** a structural distortion making capture unreliable (BVP-only channel / genuine-data gap). "
         "No distributor uses a *proxied or missing* UIO - the split is own-registration (ITUK) vs the v18 model (all others).")
S.append("")
S.append("| # | DB | Country | UIO | Total cap | Genuine cap | € gap (to 100%) | Conf | Top action |")
S.append("|---:|---|---|---:|---:|---:|---:|:--:|---|")
for i, r in enumerate(recs, 1):
    S.append("| {} | **{}** | {} | {:,} | {} | {} | **{}** | {} | {} |".format(
        i, r["db"], r["country"], r["uio"], f_pct(r["tot"]), f_pct(r["gen"]), f_eur(r["gap"]), r["conf"], r["action"]))
S.append("| | **NETWORK** | | | | | **{}** | | |".format(f_eur(total_gap)))
S.append("")
S.append("## Read-out")
S.append("")
S.append("- **Newly sized vs ITUK:** ITUK was the only distributor with a standing capture write-up (the oil-filter dispute anchor). "
         "The other **17 distributors are newly given a per-DB € brief here**, off the existing green pipeline - same method, same source, "
         "now distributor-by-distributor.")
S.append("- **Total addressable (to 100% capture, CY{}):** **{}** across 18 distributors, PMS categories only. "
         "This is a gross-SP ceiling, **not** the GPS wallet (€75.1M) and **not** a forecast.".format(YEAR, f_eur(total_gap)))
S.append("- **Concentration:** the top 3 (IUK, ITUK, UMI) carry {:.0f}% of the € ceiling. "
         "IUK alone is {:.0f}% and rests on the LCV 1.0 svc/yr assumption.".format(
             100 * sum(r["gap"] for r in recs[:3]) / total_gap, 100 * recs[0]["gap"] / total_gap))
S.append("")
S.append("## Honesty line - where the data is too thin to trust")
S.append("")
S.append("- **UMI (LOW):** genuine capture 1.1% is a genuine/warranty **data gap**, not a real sell-out read. The €1.1M is directional.")
S.append("- **UTI (LOW):** ~100% BVP channel; genuine capture (2.2%) is structurally meaningless. Total capture already >100%.")
S.append("- **IUK (MED, but caveat):** the single biggest number (€3.9M) is LCV-scope and assumption-sensitive; treat as a ceiling pending IML LCV service-rate sign-off.")
S.append("- **Air-filter gaps everywhere (flag C):** expected demand uses a flat service interval, so air-filter capture is artificially deflated and its € gap overstated. Not cross-category comparable.")
S.append("- **Brake-shoe ~0% capture network-wide:** almost certainly a fitment/availability reality, not a winnable genuine gap - it inflates several DBs' totals (ITUK alone €535K).")
S.append("- **BVP is not leakage:** genuine->BVP is in-tent retention. The winnable genuine slice is materially **smaller** than the €{:.1f}M ceiling; sizing it needs IML interval data + PN->schedule (EQ-HIT) fitment validation (both open in pms-coverage.md).".format(total_gap / 1e6))
S.append("")
S.append("_Source: `01_data/derived/pms_summary_by_db.csv`, `pms_capture_by_db_year.csv`, `pms_opportunity_matrix.csv`. Regenerate: `python 01_data/derived/pms_briefs/_build/gen_pms_briefs.py`._")

with open(os.path.join(OUT_OKF, "PMS_capture_all_distributors.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(S))

print("briefs written:", len(recs))
print("total_gap_eur: {:,.0f}".format(total_gap))
for r in recs:
    print("  {:<9} gap={:>12,.0f}  tot={:.3f} gen={:.3f} conf={}".format(r["db"], r["gap"], r["tot"], r["gen"], r["conf"]))
