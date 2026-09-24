ISUZU UNIVERSE - INTERNAL ACTION CENTRE v1
Review edition: 23 September 2026

OPEN THE MOCK
Open ISUZU_UNIVERSE_Action_Centre_v1.html in your browser.
The HTML is self-contained. No installation, external library or internet
connection is needed by the application. A managed browser may restrict local
HTML files or browser storage; follow your organisation's approved method.

The opening state is six cases, zero owners and no recorded outcomes.
Click Review on a card. Each case has three tabs:
- Understand the evidence: scope, figures, limitations and source calculations.
- Assign & act: owner, due date, next action, notes and review checklist.
- Record result: outcome, supporting evidence and comparison scope.

The left navigation follows Act / Understand / Do / Learn. The source register,
action register and results page are working views, not placeholder links.

SAVING YOUR REVIEW
The application attempts to save decisions in browser local storage. When that
is unavailable, a visible notice says that edits last for the current session.
Use Export case file to keep the review as JSON. Restore review imports the
owners, dates, notes and results back into the matching HTML edition. It does
not change source figures. An export from a different source fingerprint is
rejected. Copying the HTML alone does not transfer saved browser decisions.

DATA AND EVIDENCE
case_data.json is the single generated case-data file. The HTML embeds the same
case data, so it opens without fetching any extra files. Values in the first
three cases are read or calculated from explicitly selected attached extracts.
They are not manually entered into the interface.

AC-01: ITUK brake pads - measured 2024/2025 distributor purchasing. No dealer
       year-on-year attribution or dealer service-demand coverage is computed.
AC-02: Germany oil filters - measured units against a modelled expectation.
       The two fleet bases remain distinct. Supply-routing validation is open.
AC-03: IUK air filters - one selected product-mix scope, including BVP entry.
       The missing concession source is not blended into the figures.
AC-04: Front brake pads / blower filters - classification and concession
       validation required. No family concession rates are published.
AC-05: Don't Lose the Deal - amount extracted from page 21 of the white paper,
       explicitly paper-reported, not reconciled to a primary credit ledger.
       The differently labelled 2023 credits remain an open question.
AC-06: Tenders - page 22 of the white paper supplies a historical snapshot
       dated 22 September 2026, not a live feed. Current counts remain unknown.

The five workstation source files named in the conversation are not attached
under their original filenames. This is not a direct connection to the user's
C: drive. The attached presentation extracts are visibly identified as the
selected alternative scope for this mock. Missing primary sources stay listed.
The older tender extract is NOT substituted for the requested newer feed.

No source measurement is promoted from partial to verified when a reviewer
checks a box. No owner, due date, dealer fleet, causal price effect, tender
value or intervention result has been invented. Above-range service coverage
is withheld, not capped at 100%. Portugal clutch is excluded.

INTERNAL ONLY
This file contains multi-market internal information. It has no authentication
or production access control. A market filter is not a permission boundary.
Do not send the multi-market HTML or its JSON export to distributors.
No messages are sent, no external data is refreshed, and no permissions are
managed by the mock. Routine dealer support is outside its scope.

REPRODUCING THE MOCK
build_mock.py + template.html regenerate case_data.json and the self-contained
HTML from the selected attached-extract scope. The build does not automatically
adopt newly supplied primary files without a source-scope review.

Python 3 is required. For secondary PDF text extraction install PyMuPDF:
    python -m pip install pymupdf

Run:
    python build_mock.py --data-dir "PATH_TO_ATTACHED_FILES" --out-dir "OUTPUT"

Required selected extracts in the input folder:
    04_original_vs_value_parts_mix.csv
    03_service_capture_by_market_family.csv
    02_spend_per_truck_by_market.csv
    sales_to_dealer_by_dealer_year.csv
    10_gaps_accounts_tenders.csv

Also retain the supplied context/reference files there:
    01_ISUZU_AND_ISZE_BUSINESS.md
    ISUZU_UNIVERSE_WHITE_PAPER_FINAL_v2_2026-09-23.pdf

The builder records file hashes and selected source rows for reproducibility.
The source files themselves are not redistributed in this package. No raw
line-level billing, full price list or source PDF is included.

VALIDATION
validation_report.json contains calculation and scope checks.
browser_test_report.json contains the browser interaction checks.
Browser automation rendered the supplied HTML directly because this environment
blocks URL navigation. Session fallback, export/restore, desktop/mobile layouts
and form safeguards were tested. Native local-file browser persistence could
not be tested in that restricted environment.

The white paper has not been modified.
