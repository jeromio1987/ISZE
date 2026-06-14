"""
Build v7 workbook with:
1. FIG-KEY Parts sheet — L1/L2/L3 corrected in-place
2. Classification_Fixes sheet — full audit trail
"""
import openpyxl, json
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

SRC = 'ITUK_PMS_Analysis_Apr2026_v6_EPC_enriched.xlsx'  # build on top of v6 EPC enrichment
OUT = 'ITUK_PMS_Analysis_Apr2026_v7_reclassified.xlsx'


def main():
    with open('reclassify_changes_v2.json', encoding='utf-8') as f:
        data = json.load(f)
    changes = data['changes']
    by_row = {c['row']: c for c in changes}

    wb = openpyxl.load_workbook(SRC)
    ws = wb['FIG-KEY Parts']
    cols = {c.value: c.column for c in ws[4]}

    # Apply changes in-place, mark cells
    fixed_fill = PatternFill('solid', fgColor='C6EFCE')
    border = Border(bottom=Side(style='thin', color='6FA66F'))
    for row, change in by_row.items():
        for col_name, new_v in [('Level 1 Family', change['new_l1']),
                                 ('Level 2 Group', change['new_l2']),
                                 ('Level 3 Type', change['new_l3'])]:
            c = ws.cell(row=row, column=cols[col_name], value=new_v)
            c.fill = fixed_fill

    # Build Classification_Fixes sheet
    if 'Classification_Fixes' in wb.sheetnames:
        del wb['Classification_Fixes']
    fix_ws = wb.create_sheet('Classification_Fixes')

    title = fix_ws.cell(1, 1, 'CLASSIFICATION FIXES — FIG-KEY Parts L1/L2/L3 corrections')
    title.font = Font(bold=True, size=14)
    fix_ws.merge_cells('A1:K1')

    sub = fix_ws.cell(2, 1, f'Total fixes: {len(changes)}  |  By rule: {sum(1 for c in changes if c["evidence_source"]=="rule")}  |  By EPC: {sum(1 for c in changes if c["evidence_source"]=="epc")}')
    sub.font = Font(italic=True)
    fix_ws.merge_cells('A2:K2')

    headers = ['Row', 'FIG-KEY', 'P/N', 'Newest P/N', 'Description', 'Old L1', 'Old L3', 'New L1', 'New L3', 'Source', 'Evidence']
    for i, h in enumerate(headers, 1):
        c = fix_ws.cell(4, i, h)
        c.font = Font(bold=True, color='FFFFFF')
        c.fill = PatternFill('solid', fgColor='305496')
        c.alignment = Alignment(horizontal='center', wrap_text=True)

    rule_fill = PatternFill('solid', fgColor='E2EFDA')
    epc_fill = PatternFill('solid', fgColor='FFF2CC')
    for i, c in enumerate(changes, start=5):
        fill = rule_fill if c['evidence_source'] == 'rule' else epc_fill
        row_vals = [c['row'], c['fig'], c['pn'], c['newest_pn'], c['description'],
                    c['old_l1'], c['old_l3'], c['new_l1'], c['new_l3'], c['evidence_source'], c['evidence']]
        for j, v in enumerate(row_vals, 1):
            cell = fix_ws.cell(i, j, v)
            cell.fill = fill
            cell.alignment = Alignment(wrap_text=True, vertical='top')

    # Column widths
    widths = [6, 9, 12, 12, 28, 18, 22, 18, 22, 8, 50]
    for i, w in enumerate(widths, 1):
        fix_ws.column_dimensions[get_column_letter(i)].width = w
    fix_ws.row_dimensions[4].height = 30

    # Update Changelog
    if 'Changelog' in wb.sheetnames:
        cw = wb['Changelog']
        # Find next free row
        nr = 4
        while cw.cell(nr, 1).value: nr += 1
        cw.cell(nr, 1, 'v7')
        cw.cell(nr, 2, 'May 2026')
        cw.cell(nr, 3, 'JVDP')
        cw.cell(nr, 4, 'FIG-KEY Parts, Classification_Fixes (new)')
        cw.cell(nr, 5, f'Reclassified 118 suspicious L3 rows. 106 fixed by description-pattern rules (e.g. "FILTER; ACL" => Air filter, "CARTRIDGE OIL" => Oil filter, "BLOWER UNIT FILTER" => AC filter). 12 ambiguous PNs resolved via Snap-on EPC vehicle-family verification. Audit trail in Classification_Fixes sheet.')

    wb.save(OUT)
    print(f'Wrote {OUT}')
    print(f'  {len(changes)} cells updated in FIG-KEY Parts (highlighted green)')
    print(f'  Classification_Fixes sheet: {len(changes)} audit rows')


if __name__ == '__main__':
    main()
