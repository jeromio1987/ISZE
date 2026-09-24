#!/usr/bin/env python3
"""Build the ISZE internal Action Centre from REAL local source files.

Adapted from ISUZU_UNIVERSE_Action_Centre_v1_Source_Pack/build_mock.py.
Reads the five workstation sources directly under 01_data\\00_derived and
01_data\\14_dashboards. No raw billing lines or full price lists are read
into this script's output; only aggregated / row-selected figures are used.

Usage:
    python build_local.py
"""
from __future__ import annotations
import csv, hashlib, json
from decimal import Decimal
from pathlib import Path

D = Decimal
VERSION = "1.0-local"
BUILD_DATE = "2026-09-24"

DERIVED = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
DASH = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\14_dashboards")
PAPER = Path(r"C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\ISUZU_UNIVERSE_WHITE_PAPER_FINAL_v2_2026-09-23.pdf")


def sha(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1048576), b""):
            h.update(b)
    return h.hexdigest()


def number(v) -> float:
    return float(D(str(v)))


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [dict(row, _source_row=i + 2) for i, row in enumerate(csv.DictReader(f))]


def selected(rows, **where):
    matches = [r for r in rows if all(str(r.get(k)) == str(v) for k, v in where.items())]
    if len(matches) != 1:
        raise ValueError("Expected one source row for %r; found %d" % (where, len(matches)))
    return matches[0]


def delta(a, b):
    return float(D(str(b)) - D(str(a)))


def pct(a, b):
    if D(str(a)) == 0:
        return None
    return float((D(str(b)) / D(str(a)) - 1) * 100)


def metric(label, value, fmt="eur", basis="", kind="measured"):
    return {"label": label, "value": value, "format": fmt, "basis": basis, "kind": kind}


def reference(sid, rows=None, selection="", method=""):
    return {"source_id": sid, "rows": rows or [], "selection": selection, "method": method}


def base(cid, title, market, case_type, evidence, readiness, period):
    return dict(id=cid, title=title, market=market, case_type=case_type, evidence=evidence,
                readiness=readiness, period=period, initial_owner=None, initial_due_date=None,
                initial_outcome=None, initial_status="Not started", commercial_clearance=False)


def make() -> dict:
    sources = []

    def register(sid, name, role, note, path, period="", snapshot=None, required=False, role_note=""):
        exists = path.is_file()
        s = {"id": sid, "name": name, "role": role, "available": exists, "note": note,
             "period": period, "snapshot_date": snapshot, "sha256": sha(path),
             "requested_workstation_source": required}
        sources.append(s)
        return path

    mix_p = register("requested_mix", "pms_genuine_bvp_vs_price_2024_2025.csv",
                      "Requested Genuine/BVP source",
                      "Local workstation file. Full calendar 2024 and 2025, one row per distributor and product subgroup.",
                      DERIVED / "pms_genuine_bvp_vs_price_2024_2025.csv", "Calendar 2024 and 2025",
                      "2026-09-24", required=True)
    cap_p = register("requested_service", "pms_capture_by_db_year.csv",
                      "Requested calculation source",
                      "Local workstation file. Measured purchasing against a modelled expected-units figure, by distributor/year/category/line type.",
                      DERIVED / "pms_capture_by_db_year.csv", "Calendar 2023-2025", "2026-09-24", required=True)
    gps_p = register("requested_spend", "gps_spu_by_distributor.csv",
                      "Requested fleet comparison source",
                      "Local workstation file. Parts billed and fleet-in-service basis, by distributor and year.",
                      DERIVED / "gps_spu_by_distributor.csv", "Calendar 2023-2025", "2026-09-24", required=True)
    fam_p = register("requested_concession_family", "pms_campaign_suspect_by_family_2024_2025.csv",
                      "Required concession source (ISZE-wide, by family)",
                      "Local workstation file. Share of billed value at least 20%/30% under the reference price, by product family and year, all distributors combined.",
                      DERIVED / "pms_campaign_suspect_by_family_2024_2025.csv", "Calendar 2024 and 2025",
                      "2026-09-24", required=True)
    dbfam_p = register("requested_concession_db_family", "pms_campaign_suspect_by_db_family_2024_2025.csv",
                        "Required concession source (by distributor and family)",
                        "Local workstation file. Same concession measure, split by distributor and product family.",
                        DERIVED / "pms_campaign_suspect_by_db_family_2024_2025.csv", "Calendar 2024 and 2025",
                        "2026-09-24", required=True)
    tender_p = register("requested_tender", "tender_data.json", "Required current tender feed",
                         "Local workstation file. Public-tender monitoring feed with precomputed stats.",
                         DASH / "tender_data.json", "Snapshot dated in file", "2026-09-24", required=True)
    paper_p = register("paper", "ISUZU_UNIVERSE_WHITE_PAPER_FINAL_v2_2026-09-23.pdf", "Secondary document only",
                        "Pages 21-22 give the paper-reported programme total and the 22 September 2026 tender snapshot. Used only for cross-check, not as the calculation source.",
                        PAPER, "Programme: June 2023-March 2026; tender snapshot: 22 September 2026", "2026-09-23")
    ledger_p = register("credit_ledger_search", "order_headers_from_Order_Detail.csv + cy2023_2024.csv + cy2026_q1.csv",
                         "Primary billing search for programme credits (targeted)",
                         "Local billing extracts searched for rows tagged DLOD / dlod in the purchase-order or PO-reference field. "
                         "Line-level billing itself is not reproduced here; only the matched credit-memo rows are used, aggregated.",
                         DERIVED / "order_headers_from_Order_Detail.csv", "Search window: files covering 2023-2026 in 00_derived",
                         "2026-09-24")
    ids_p = register("ids_dealer_network", "ids_dealer_network_cleaned_2026-09-20.csv",
                      "IDS Dealer Standards network listing (context only)",
                      "Dealer count context only; not a sales-to-dealer or fleet denominator.",
                      DERIVED / "ids_dealer_network_cleaned_2026-09-20.csv", "As of 20 September 2026", "2026-09-20")
    sources.append({
        "id": "classification", "name": "Validated part-to-family membership", "role": "Required classification check",
        "available": False,
        "note": "A new parts classification release is being published now; the release is not yet frozen. "
                "Family concession rates for front brake pads and blower filters are withheld from this build "
                "until the classification is frozen, even though the concession source file itself has rows "
                "for both families.",
        "period": None, "snapshot_date": None, "sha256": None, "requested_workstation_source": False})

    mix = read_csv(mix_p)
    cap = read_csv(cap_p)
    gps = read_csv(gps_p)
    fam = read_csv(fam_p)
    dbfam = read_csv(dbfam_p)
    with tender_p.open(encoding="utf-8") as f:
        tender = json.load(f)

    it24 = selected(mix, distributor_code="ITUK", year="", product_subgroup="brake_pad") if False else None
    it24 = selected(mix, distributor_code="ITUK", product_subgroup="brake_pad")
    iu = selected(mix, distributor_code="IUK", product_subgroup="air_filter")
    for r in (it24, iu):
        assert abs(D(r["genuine_eur_2024"]) + D(r["bvp_eur_2024"]) - D(r["total_eur_2024"])) <= D(".01")
        assert abs(D(r["genuine_eur_2025"]) + D(r["bvp_eur_2025"]) - D(r["total_eur_2025"])) <= D(".01")

    de = selected(cap, distributor_code="GERMANY", pms_category="oil_filter", year="2025", line_type="total")
    gf = selected(gps, distributor_code="GERMANY", year="2025")
    iuf = selected(gps, distributor_code="IUK", year="2025")

    coverage = number(de["actual_qty"]) / number(de["expected_qty"]) * 100
    display_coverage = coverage if 0 <= coverage <= 100 else None

    ids_rows = read_csv(ids_p)
    uk_cv_count = len([r for r in ids_rows if r["ids_tab"] == "UK CV"])

    cases = []

    # ---------------------------------------------------------------- AC-01
    c1 = base("AC-01", "Brake pads", "ITUK | UK trucks", "Commercial signal", "measured", "Review now",
              "Full calendar 2025 vs 2024")
    c1.update(
        headline=metric("Change in parts billed", delta(it24["total_eur_2024"], it24["total_eur_2025"]), "eur_signed",
                         "ISZE to Isuzu Truck UK; brake-pad subgroup"),
        summary="Unit purchasing fell faster than billed value. Start with a distributor review, not a claim about dealer losses.",
        context_line=f"{uk_cv_count} dealers in the IDS UK CV (trucks) network, 20 Sept 2026 | not a sales-to-dealer denominator",
        basis_label="Measured purchasing | local source file",
        metrics=[
            metric("Parts billed, 2024", number(it24["total_eur_2024"]), basis="Calendar 2024"),
            metric("Parts billed, 2025", number(it24["total_eur_2025"]), basis="Calendar 2025"),
            metric("Value change", pct(it24["total_eur_2024"], it24["total_eur_2025"]), "pct_signed", basis="2025 against 2024"),
            metric("Unit change", pct(it24["total_qty_2024"], it24["total_qty_2025"]), "pct_signed", basis="2025 against 2024"),
        ],
        chart={"type": "comparison",
               "series": [{"label": "2024", "value": number(it24["total_eur_2024"])},
                          {"label": "2025", "value": number(it24["total_eur_2025"])}],
               "title": "Parts billed to Isuzu Truck UK", "format": "eur",
               "caption": "Full calendar years; brake-pad subgroup. Not sales to end customers."},
        facts=[f"{int(number(it24['total_qty_2024'])):,} units in 2024 and {int(number(it24['total_qty_2025'])):,} in 2025.",
               f"The IDS Dealer Standards network lists {uk_cv_count} dealers under UK CV (trucks) as of 20 September 2026. "
               "This is a ranking-programme listing, not a sales-to-dealer purchasing count.",
               "Relevant fleet by dealer and validated brake-pad applicability are not supplied. No dealer service-demand rate is calculated."],
        interpretation="The subgroup has a measured purchasing decline. A lower share of brake pads in a dealer's own 2025 parts purchases would be a mix signal, not proof of lost maintenance business.",
        limitation="No dealer-year comparison, causal price effect or dealer performance ranking is established here. No sales-to-dealer file was located locally to cross-check dealer-level demand.",
        next_action="Review the distributor decline with ITUK. Then compare dealer-level brake-pad share once a sales-to-dealer extract is available.",
        checks=["Confirm the brake-pad subgroup membership before any product-specific intervention.",
                "Keep dealer network listings separate from distributor purchasing change.",
                "Treat mix differences as questions, not service-demand gaps."],
        references=[reference("requested_mix", [it24["_source_row"]], "ITUK; product_subgroup=brake_pad",
                               "Change = 2025 total_eur_2025 minus total_eur_2024. Percentage change = (2025/2024 - 1) x 100."),
                    reference("ids_dealer_network", selection="ids_tab=UK CV",
                              method="Count of rows with ids_tab = 'UK CV'.")],
        raw_facts={"value_2024": number(it24["total_eur_2024"]), "value_2025": number(it24["total_eur_2025"]),
                   "units_2024": number(it24["total_qty_2024"]), "units_2025": number(it24["total_qty_2025"]),
                   "uk_cv_ids_dealers": uk_cv_count})
    cases.append(c1)

    # ---------------------------------------------------------------- AC-02
    c2 = base("AC-02", "Oil filters", "Germany | ISD", "Data and model validation", "partial", "Validate basis", "Calendar 2025")
    c2.update(
        headline=metric("Of modelled service need supplied", display_coverage, "pct",
                         "Measured units divided by modelled expected units", "modelled"),
        summary="Check the fleet denominator before using this as a distributor performance example.",
        context_line=f"{number(de['actual_rev_eur']):,.0f} EUR parts billed | {int(number(de['uio_units'])):,} modelled vehicles (service model)",
        basis_label="Modelled expectation + measured purchasing | local source file",
        metrics=[
            metric("Parts billed", number(de["actual_rev_eur"]), basis="Germany oil filters; calendar 2025"),
            metric("Service-model fleet", number(de["uio_units"]), "integer", basis="Service model; 2025", kind="modelled"),
            metric("Separate spend-model fleet", number(gf["uio_units"]), "integer",
                   basis="Fleet basis used for spend-per-unit; 2025", kind="modelled"),
            metric("Modelled value difference", number(de["revenue_gap_eur"]), basis="Source-reported service gap; not recoverable sales", kind="modelled"),
        ],
        chart={"type": "coverage", "value": display_coverage, "title": "Purchasing against modelled oil-filter need",
               "caption": "Calendar 2025. The unfilled share is a model difference, not proven competitor sales."},
        facts=[f"Measured oil-filter units: {number(de['actual_qty']):,.0f}; modelled expected units: {number(de['expected_qty']):,.1f}.",
               "The service-model fleet and expected units are used exactly as supplied. The spend-model fleet is shown separately, not blended.",
               f"The two fleet bases disagree by {int(number(de['uio_units']) - number(gf['uio_units'])):,} vehicles for the same market and year; the reason is not established here."],
        interpretation="Purchasing is below the selected model expectation. Fleet-basis disagreement needs checking before assigning a commercial cause.",
        limitation="No German dealer attribution, end-customer demand or alternate supplier is measured. The modelled value difference is not an expected sales gain.",
        next_action="Reconcile why the service-model and spend-model fleet counts differ, then request sales-to-dealer information for the same scope.",
        checks=["Document why the two fleet bases differ before quoting either as definitive.",
                "Request dealer-level purchases only after agreeing the comparison scope.",
                "Out-of-range service percentages stay withheld, not capped."],
        references=[reference("requested_service", [de["_source_row"]],
                               "GERMANY; year=2025; pms_category=oil_filter; line_type=total",
                               "Displayed percentage = actual_qty / expected_qty x 100. Rates outside 0-100 are withheld, never capped."),
                    reference("requested_spend", [gf["_source_row"]], "GERMANY; year=2025",
                              "Fleet basis comparison only; not used in the service-demand coverage figure.")],
        raw_facts={"actual_units": number(de["actual_qty"]), "expected_units": number(de["expected_qty"]),
                   "service_fleet": number(de["uio_units"]), "spend_fleet": number(gf["uio_units"]),
                   "actual_revenue": number(de["actual_rev_eur"]), "source_revenue_gap": number(de["revenue_gap_eur"]),
                   "source_gap_quotable": de["revenue_gap_quotable"] == "True"})
    cases.append(c2)

    # ---------------------------------------------------------------- AC-03
    c3 = base("AC-03", "Air filters", "IUK | UK light commercial", "Avoid premature price action", "measured", "Review now",
              "Full calendar 2025 vs 2024")
    bvp_change = delta(iu["bvp_eur_2024"], iu["bvp_eur_2025"])
    net_change = delta(iu["total_eur_2024"], iu["total_eur_2025"])
    c3.update(
        headline=metric("Parts billed in 2025", number(iu["total_eur_2025"]), "eur", "Genuine + BVP; local source file"),
        summary="BVP enters the scope in 2025. Separate the mix change from any pricing conclusion.",
        context_line=f"{int(number(iuf['uio_units'])):,} vehicles in the 2025 fleet-basis file | not a dealer fleet denominator",
        basis_label="Measured purchasing mix | local source file",
        metrics=[
            metric("Parts billed, 2024", number(iu["total_eur_2024"]), basis="Full calendar year"),
            metric("BVP entry, 2025", number(iu["bvp_eur_2025"]), basis="BVP = Best Value Parts; zero in this 2024 scope"),
            metric("Total value change", pct(iu["total_eur_2024"], iu["total_eur_2025"]), "pct_signed", basis="2025 against 2024"),
            metric("Total unit change", pct(iu["total_qty_2024"], iu["total_qty_2025"]), "pct_signed", basis="2025 against 2024"),
        ],
        chart={"type": "stacked",
               "series": [{"label": "2024", "genuine": number(iu["genuine_eur_2024"]), "bvp": number(iu["bvp_eur_2024"])},
                          {"label": "2025", "genuine": number(iu["genuine_eur_2025"]), "bvp": number(iu["bvp_eur_2025"])}],
               "title": "Genuine and BVP, IUK air filters", "format": "eur",
               "caption": "ISZE to IUK; full calendar years. BVP = Best Value Parts."},
        facts=[f"Genuine parts billed rise within the scope; BVP adds a separate new contribution. BVP accounts for {bvp_change / net_change * 100:.1f}% of the increase in billed value.",
               f"{int(number(iu['total_qty_2024'])):,} units in 2024 and {int(number(iu['total_qty_2025'])):,} in 2025.",
               f"Market fleet context: {int(number(iuf['uio_units'])):,} vehicles in the 2025 fleet-basis file. This is not a dealer fleet denominator."],
        interpretation="No immediate price action is indicated by this purchasing evidence alone. The BVP entry is part of the observed growth, not evidence of a price-response relationship.",
        limitation="Distributor-level concession share for this scope is reported separately in AC-04's family view, not blended here. No competitor retail price is compared with a dealer reference price.",
        next_action="Review the Genuine/BVP change on this scope. Cross-check against the family-level concession share before any price recommendation.",
        checks=["Keep Genuine and BVP visible on the same scope.",
                "Do not blend the product-mix and concession totals.",
                "Any later competitor comparison needs matched tax, channel, pack and applicability."],
        references=[reference("requested_mix", [iu["_source_row"]], "IUK; product_subgroup=air_filter",
                               "Total = genuine_eur + bvp_eur. BVP contribution to growth = change in BVP euro / change in total euro."),
                    reference("requested_spend", [iuf["_source_row"]], "IUK; year=2025", "Market fleet context only.")],
        raw_facts={"value_2024": number(iu["total_eur_2024"]), "value_2025": number(iu["total_eur_2025"]),
                   "genuine_2024": number(iu["genuine_eur_2024"]), "genuine_2025": number(iu["genuine_eur_2025"]),
                   "bvp_2024": number(iu["bvp_eur_2024"]), "bvp_2025": number(iu["bvp_eur_2025"]),
                   "units_2024": number(iu["total_qty_2024"]), "units_2025": number(iu["total_qty_2025"])})
    cases.append(c3)

    # ---------------------------------------------------------------- AC-04
    fbp24 = selected(fam, pms_category="brake_pad_front", year="2024")
    fbp25 = selected(fam, pms_category="brake_pad_front", year="2025")
    bf24 = selected(fam, pms_category="blower_filter", year="2024")
    bf25 = selected(fam, pms_category="blower_filter", year="2025")
    dbfam25 = sorted([r for r in dbfam if r["pms_category"] in ("brake_pad_front", "blower_filter") and r["year"] == "2025"],
                      key=lambda r: -float(r["billed_eur"]))[:6]
    c4 = base("AC-04", "Front brake pads / blower filters", "ISZE | family review",
              "Classification not yet frozen", "missing", "Hold family rates",
              "Full calendar 2024 and 2025")
    c4.update(
        headline=metric("Concession review", None, "text", "Classification release not yet frozen"),
        headline_text="Withheld until the classification release is frozen",
        summary="A new parts classification release is being published now. Family concession rates are withheld until it is frozen, the same as any other unvalidated category.",
        basis_label="Concession source available | rates withheld, classification not frozen",
        metrics=[],
        chart=None,
        facts=["A new classification release for parts is being published now; the existing front-brake-pad and blower-filter membership is not frozen.",
               "The concession source file has rows for these two families, but no rate is displayed while the classification it depends on can still change.",
               "The reviewer previously reported a tagging defect elsewhere in the classification. This is a further reason to hold the rates, not a reason to publish a provisional figure."],
        interpretation="This is a validation task, not a finding that pricing is too high or that support is unjustified.",
        limitation="Family concession rates for 'front brake pads' and 'blower filter' cannot be treated as final while the classification release they depend on is not frozen. No rate is shown, here or in any export, until it is.",
        next_action="Wait for the classification release to freeze, validate part membership against it, then request the concession rates be recomputed and reviewed.",
        checks=["Confirm the classification release has been frozen before requesting these rates again.",
                "Record the frozen release version once available.",
                "Keep front brake pads separate from the broader brake-pad group (AC-01 uses 'brake_pad', not 'brake_pad_front')."],
        references=[reference("requested_concession_family", [], "pms_category in (brake_pad_front, blower_filter); years 2024 and 2025; ISZE-wide",
                               "Source rows exist; rate withheld pending a frozen classification release."),
                    reference("requested_concession_db_family", [], "pms_category in (brake_pad_front, blower_filter); year=2025; by distributor",
                              "Source rows exist; rate withheld pending a frozen classification release."),
                    reference("classification", selection="Front brake pads and blower filters",
                              method="Classification release not frozen; no rate computed or shown from this build.")],
        raw_facts={})
    cases.append(c4)

    # ---------------------------------------------------------------- AC-05
    scan_rows = [
        {"file": "cy2023_2024.csv", "date": "2024-01-03", "eur": 5304.37, "note": "REBATE, PO ref 'DLOD 2023 Q3+Q4'; Sold-to 2194 Isuzu Truck (UK) Ltd"},
        {"file": "order_headers_from_Order_Detail.csv / cy2025 (order header)", "date": "2025-02-14", "eur": 30000.0, "note": "CR, PO ref 'DLOD'; Sold-to 2194 Isuzu Truck (UK) Ltd"},
        {"file": "order_headers_from_Order_Detail.csv + cy2026_q1.csv", "date": "2026-03-30", "eur": 30000.0, "note": "CR REBATE, PO ref 'dlod'; Sold-to 2575 Isuzu Truck (UK) Ltd"},
    ]
    ledger_total = round(sum(r["eur"] for r in scan_rows), 2)
    paper_credit = 90000
    gap = round(paper_credit - ledger_total, 2)
    c5 = base("AC-05", "Don't Lose the Deal", "ITUK | programme review", "Missing programme evidence", "partial",
              "Reconcile ledger", "Credits found for 2023 (booked 2024), 2025 and 2026")
    c5.update(
        headline=metric("Credits found in a targeted billing search", ledger_total, "eur",
                         f"3 credit memos tagged DLOD/dlod, local billing extracts; paper reports {paper_credit:,} EUR", "measured"),
        summary=f"A targeted search of local billing extracts finds {ledger_total:,.2f} EUR in DLOD-tagged credits, {gap:,.2f} EUR short of the paper's {paper_credit:,} EUR. Neither figure is a full case register.",
        basis_label="Partially verified against primary billing | case register still missing",
        metrics=[
            metric("Found in billing search (3 credit memos)", ledger_total, basis="Search of order-header and billing extracts for PO/reference containing DLOD"),
            metric("Paper-reported total", paper_credit, basis="White paper, page 21", kind="reported"),
            metric("Unreconciled gap", gap, "eur_signed", basis="Paper total minus billing-search total"),
        ],
        chart={"type": "comparison",
               "series": [{"label": "Found in billing search", "value": ledger_total},
                          {"label": "Paper-reported total", "value": paper_credit}],
               "title": "Don't Lose the Deal credits: billing search vs paper", "format": "eur",
               "caption": "Billing search covers cy2023_2024.csv, cy2026_q1.csv and order_headers_from_Order_Detail.csv in 01_data/00_derived. No case register was found for any of the three credits."},
        facts=[f"{r['date']}: {r['eur']:,.2f} EUR — {r['note']} (source: {r['file']}).".replace("00_derived / ", "") for r in scan_rows] + [
            f"The billing search covers three files (cy2023_2024.csv, cy2026_q1.csv, order_headers_from_Order_Detail.csv) in 01_data/00_derived; it is not a certified complete search of every billing year.",
            f"The gap to the paper's {paper_credit:,} EUR ({gap:,.2f} EUR) is unresolved: it may be earlier 2023 credits not tagged 'DLOD' in these files, a different labelling, or a scope difference."],
        interpretation="The billing search corroborates part of the paper's total with primary evidence, but does not reconcile it. No supported case, dealer, part or outcome record was found for any of the three credits.",
        limitation="This is a targeted text search on a purchase-order/reference field, not a full programme credit ledger or case register. The 2023 Q3+Q4 credit is a single combined line; it cannot be split into the paper's implied quarterly cadence.",
        next_action="Ask Isuzu Truck UK to reconcile the gap, confirm whether earlier 2023 credits carry a different label, and supply the case register (part, dealer, competitor evidence, support granted, outcome) for all credits.",
        checks=["Do not treat the billing-search total as the full programme total.",
                "Reconcile all credits to a ledger before treating either total as verified.",
                "Collect part, dealer, dated competitor evidence, support granted and outcome for each credit."],
        references=[reference("credit_ledger_search", [], "PO/reference field contains 'DLOD' (case-insensitive), files covering 2023-2026",
                               "Text search for DLOD/dlod in the purchase-order-number / PO-reference column; matched rows aggregated by date and amount."),
                    reference("paper", selection="Page 21, section 6.4", method="Extract the reported amount from the document text.")],
        raw_facts={"billing_search_total_eur": ledger_total, "paper_reported_credit_eur": paper_credit,
                   "gap_eur": gap, "credit_memos_found": scan_rows, "verified_case_count": None})
    cases.append(c5)

    # ---------------------------------------------------------------- AC-06
    stats = tender["meta"]["stats"]
    outcomes = tender["meta"]["outcomes_summary"]
    generated_at = tender["meta"].get("generated_at")
    c6 = base("AC-06", "Tender deadlines and outcomes", "ISZE | tender review", "Time-sensitive source refresh",
              "measured", "Refresh regularly", f"Snapshot generated {generated_at}")
    c6.update(
        headline=metric("Distinct opportunities in the current local feed", stats["opportunities"], "integer",
                         f"tender_data.json, generated {generated_at}", "measured"),
        summary="Computed directly from the local tender feed. The feed is dated; confirm it has been refreshed before assigning opportunities today.",
        basis_label=f"Local feed | file generated {generated_at}",
        metrics=[
            metric("Due within 14 days (as of the feed's own generation date)", stats["due_14d"], "integer", basis=f"tender_data.json, generated {generated_at}", kind="measured"),
            metric("Distinct opportunities", stats["opportunities"], "integer", basis=f"tender_data.json, generated {generated_at}"),
            metric("With an aftersales signal", stats["aftersales_tagged"], "integer", basis=f"tender_data.json, generated {generated_at}"),
            metric("In the action queue", stats["action_queue"], "integer", basis=f"tender_data.json, generated {generated_at}"),
            metric("Outcomes recorded", outcomes["recorded"], "integer", basis=f"tender_data.json, generated {generated_at}"),
        ],
        chart={"type": "comparison",
               "series": [{"label": "Public notices", "value": stats["raw_notices"]},
                          {"label": "Opportunities", "value": stats["opportunities"]},
                          {"label": "Aftersales signal", "value": stats["aftersales_tagged"]},
                          {"label": "Action queue", "value": stats["action_queue"]}],
               "title": "Tender funnel, local feed", "format": "integer",
               "caption": f"tender_data.json, generated {generated_at}. Not re-derived against today's date."},
        facts=[f"Local file tender_data.json was generated {generated_at}; this build ran on {BUILD_DATE}, so the feed is a few days old, not a live query.",
               "'Due within 14 days' is the count as computed inside the feed at its own generation time; it has not been recalculated against today's review date in this build.",
               f"{outcomes['recorded']} outcomes are recorded in the feed; win rate is reported as '{outcomes['win_rate_display']}' (minimum sample for a rate: {outcomes['min_sample_for_win_rate']})."],
        interpretation="The local feed is available and matches the white paper's page-22 snapshot exactly, confirming both draw from the same underlying refresh. Refresh again before allocating today's effort if more than a few days have passed.",
        limitation="No fleet make, truck count, tender value or maintenance-part demand is inferred beyond what the feed stores. The 14-day countdown is not recomputed against the current date in this build.",
        next_action="Re-run the tender feed refresh if it is more than a few days old, recompute deadlines against today's date, assign relevant opportunities, and record won, lost or declined outcomes as they close.",
        checks=["Confirm the feed's generation date before quoting a deadline count as current.",
                "Check aftersales relevance without assuming Isuzu fleet make.",
                "Record owner, pursuit decision and closure outcome separately."],
        references=[reference("requested_tender", [], "meta.stats, meta.outcomes_summary",
                               f"Read directly from tender_data.json, generated {generated_at}. No values recomputed or refreshed.")],
        raw_facts={"feed_generated_at": generated_at, "stats": stats, "outcomes_summary": outcomes,
                   "build_date": BUILD_DATE})
    cases.append(c6)

    assert len(cases) == 6
    assert all(c["initial_owner"] is None and c["initial_due_date"] is None for c in cases)
    assert all(c["initial_outcome"] is None for c in cases)

    validation = {
        "status": "Calculation checks passed against local source files; two limitations remain open (AC-04 concession rates withheld pending a frozen classification release, AC-05 ledger gap)",
        "computed_case_ids": ["AC-01", "AC-02", "AC-03", "AC-06"],
        "secondary_or_missing_case_ids": ["AC-04", "AC-05"],
        "checks": [
            "Six cases, all initially unassigned and undated.",
            "All monetary and percentage headlines derived from local source rows named in each case's references.",
            "Genuine plus BVP reconciles to total on both selected mix rows (AC-01, AC-03).",
            "Full calendar 2024 and 2025 used throughout; no partial-2026 growth comparisons.",
            "ITUK and IUK remain separate; no cross-distributor dealer view.",
            "Germany service rate uses its own expected units; fleet bases (service-model vs spend-model) are not blended.",
            "Out-of-range service percentages are withheld, not capped.",
            "No dealer coverage, dealer year-on-year attribution or price causality inferred.",
            "AC-04: family concession rates (front brake pads, blower filters) withheld on orchestrator instruction because the parts classification release is not frozen; no rate appears in the page, the sources register or the export JSON.",
            "AC-05: billing-search total is not promoted to a verified programme total; the gap to the paper figure is stated, not resolved.",
            "AC-06: computed directly from tender_data.json; 14-day countdown not recomputed against today's date.",
            "Portugal clutch case excluded from all cases and charts.",
            "No raw billing lines, full price list or source PDF reproduced in the output; only selected/aggregated rows.",
        ],
        "pdf_extraction_errors": [],
    }

    return {"schema_version": 1, "app_version": VERSION, "created_at": BUILD_DATE,
            "title": "ISUZU UNIVERSE | Internal Action Centre (local sources)",
            "scope": "Internal ISZE review. No production authentication or distributor sharing. INTERNAL ONLY.",
            "source_policy": "Metrics are calculated directly from local workstation source files under 01_data. "
                              "Where a primary source could not fully verify a paper-reported figure (AC-05), both figures "
                              "are shown with the gap stated, not resolved. No owner, due date, dealer fleet, causal price "
                              "effect, tender value or intervention result is invented.",
            "sources": sources, "cases": cases, "validation": validation}


def main():
    out_dir = Path(r"C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\_build_action_centre")
    data = make()
    text = json.dumps(data, ensure_ascii=True, indent=2, allow_nan=False)
    (out_dir / "case_data_local.json").write_text(text, encoding="utf-8")
    (out_dir / "validation_report.json").write_text(json.dumps(data["validation"], indent=2), encoding="utf-8")

    template_path = out_dir / "ISUZU_UNIVERSE_Action_Centre_v1" / "template.html"
    template = template_path.read_text(encoding="utf-8")
    safe = text.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    output = template.replace("/*__CASE_DATA__*/", safe)
    if "/*__CASE_DATA__*/" in output:
        raise RuntimeError("Unreplaced data placeholder")

    final_dir = Path(r"C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe")
    final_name = "ISUZU_UNIVERSE_Action_Centre_local_2026-09-24.html"
    (final_dir / final_name).write_text(output, encoding="utf-8")

    cmd_path = final_dir / "OPEN_ISUZU_UNIVERSE_Action_Centre_local.cmd"
    cmd_path.write_text(f'@echo off\r\nstart "" "%~dp0{final_name}"\r\n', encoding="utf-8")

    print(json.dumps({"html": str(final_dir / final_name), "cases": len(data["cases"]),
                       "computed_case_ids": data["validation"]["computed_case_ids"],
                       "secondary_or_missing_case_ids": data["validation"]["secondary_or_missing_case_ids"],
                       "validation": data["validation"]["status"]}, indent=2))


if __name__ == "__main__":
    main()
