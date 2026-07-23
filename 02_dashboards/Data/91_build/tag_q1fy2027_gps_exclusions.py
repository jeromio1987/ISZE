"""
Tag Q1FY2027.XLSX (raw SAP billing extract, 12_raw/sales/) with GPS exclusion
flags per isze-gps-auditor rules. Does NOT drop rows -- adds flag columns so
warranty (separate dataset, joined later) and Shell/Rimula lube lines can be
filtered out downstream without rebuilding.

Source: 01_data/12_raw/sales/Q1FY2027.XLSX
Output: 01_data/00_derived/q1fy2027_billing_tagged.csv
        01_data/00_derived/q1fy2027_billing_tagged.parquet

Known issue: 2 SAP-export footer/total rows (no billing date/payer) are
stripped before tagging -- see _data_integrity_open_issues.md (Q1FY27-FOOTER).
Known issue: clean net-value total (EUR 6.57M) does not reconcile to the
Jun-2026 monthly report's stated Q1 FY27 Sales amount (EUR 8.611M) -- see
_data_integrity_open_issues.md (Q1FY27-GAP). Unresolved as of build date.
"""
import openpyxl, re, csv
from pathlib import Path

SRC = Path("12_raw/sales/Q1FY2027.XLSX")
OUT_CSV = Path("00_derived/q1fy2027_billing_tagged.csv")

SHELL_CODES = {"550047337", "550047252", "550070445", "550070643"}
SATY_INCLUDE = {"SOR", "VOR", "RUSH", "PRD", "SVOR"}
SATY_REVIEW = {"DR", "ZDR"}
SATY_EXCLUDE = {"CR", "RE"}

def is_shell_lube(matnr: str) -> bool:
    if matnr in SHELL_CODES:
        return True
    return bool(re.match(r"^55004", matnr) or re.match(r"^55007", matnr))

def main():
    wb = openpyxl.load_workbook(SRC, read_only=True, data_only=True)
    ws = wb["Sheet1"]
    header = next(ws.iter_rows(min_row=1, max_row=1, values_only=True))
    out_header = list(header) + [
        "is_footer_row", "flag_transport", "flag_shell_lube", "flag_rebate",
        "flag_late_payment_interest", "flag_service_fee", "flag_demurrage",
        "saty_treatment", "is_credit_note_g2", "net_value_gps_signed",
        "gps_excluded_any",
    ]

    n_footer = 0
    n_rows = 0
    n_excluded = 0

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(out_header)

        for r in ws.iter_rows(min_row=2, values_only=True):
            billing_date, billdoc, billt, sorg, payer_code, soldto, payer_name, \
                desc, matnr, bqty, su1, oqty, su2, net_value, curr, net_price, \
                curr2, po, saty, doc_date, salesdoc = (list(r) + [None]*21)[:21]

            is_footer = billing_date is None and (billdoc is None or billdoc == "")
            if is_footer:
                n_footer += 1
                writer.writerow(list(r[:21]) + [True] + [""]*9)
                continue

            n_rows += 1
            d = str(desc).upper() if desc else ""
            m = str(matnr) if matnr else ""
            nv = float(net_value) if net_value is not None else 0.0

            flag_transport = "TRANSPORT" in d
            flag_shell = is_shell_lube(m)
            flag_rebate = "REBATE" in d
            flag_late_pay = "LATE PAYMENT INTEREST" in d
            flag_service = "SERVICE" in d
            flag_demurrage = "DEMURRAGE" in d

            saty_key = str(saty) if saty else ""
            if saty_key in SATY_INCLUDE:
                saty_treatment = "INCLUDE"
            elif saty_key in SATY_REVIEW:
                saty_treatment = "REVIEW"
            elif saty_key in SATY_EXCLUDE:
                saty_treatment = "EXCLUDE"
            else:
                saty_treatment = "UNKNOWN"

            is_g2 = (billt == "G2")
            # G2/CR/RE appear as positive in SAP export but are revenue reductions
            sign_corrected = -abs(nv) if (is_g2 or saty_key in SATY_EXCLUDE) else nv

            excluded_any = any([flag_transport, flag_shell, flag_rebate,
                                 flag_late_pay, flag_service, flag_demurrage,
                                 is_g2, saty_key in SATY_EXCLUDE])
            if excluded_any:
                n_excluded += 1

            writer.writerow(list(r[:21]) + [
                False, flag_transport, flag_shell, flag_rebate, flag_late_pay,
                flag_service, flag_demurrage, saty_treatment, is_g2,
                round(sign_corrected, 2), excluded_any,
            ])

    print(f"Footer rows stripped: {n_footer}")
    print(f"Transaction rows tagged: {n_rows}")
    print(f"Rows flagged for any exclusion: {n_excluded}")
    print(f"Wrote: {OUT_CSV}")

if __name__ == "__main__":
    main()
