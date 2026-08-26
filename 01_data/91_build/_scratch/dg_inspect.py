import openpyxl, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

P = r'c:\Users\jerom\Downloads\UMIUTI_Logistics_Study_v2.xlsx'
wb = openpyxl.load_workbook(P, read_only=True, data_only=True)

def dump(sheet, header_row, maxrows=8):
    ws = wb[sheet]
    print(f"\n===== SHEET {sheet!r} (header row {header_row}) =====")
    rows = []
    for i, r in enumerate(ws.iter_rows(values_only=True)):
        rows.append(r)
        if i >= header_row + maxrows - 1:
            break
    # print header
    print("HEADER:", [str(c) for c in rows[header_row-1]])
    for r in rows[header_row:header_row+maxrows]:
        print("  ", [str(c)[:28] if c is not None else '' for c in r])

dump('DG list (deduped)', 4, 12)
dump('Dangerous goods', 1, 8)
dump('Data (joined)', 4, 5)
dump('DG x MoT Summary', 1, 25)
dump('DG Material Pareto', 1, 15)
