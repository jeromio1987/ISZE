import openpyxl
from collections import Counter

p = r'01_data\Final_Complete_Warranty_Pricing_2026.xlsx'
wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
ws = wb['Raw_LCV_Warranty']
it = ws.iter_rows(values_only=True)
hdr = [str(h).strip() if h is not None else '' for h in next(it)]
print('LCV header:', hdr)
print()
# scan every cell of every row for the part number, then show the whole row
hits = 0
c = Counter()
for row in it:
    cells = [str(x).strip() if x is not None else '' for x in row]
    if any('7552026060' in x for x in cells):
        hits += 1
        # operation description is the likely label column
        c[cells[10][:70] if len(cells) > 10 else ''] += 1
        if hits <= 3:
            print('ROW:', [x[:40] for x in cells])
print()
print('rows containing 7552026060:', hits)
for k, v in c.most_common(10):
    print(f'   x{v:>4}  {k}')
wb.close()
