"""_c_receipt_notes.py - append the evidence notes to the candidate c ship receipt."""
import io, sys, json, os, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

CUR = r'C:\Users\jerom\Desktop\claude\ISZE\06_uio\_CURRENT'
ART = os.path.join(CUR, 'ISUZU_UIO_Overview_2026_V20_CANDIDATE_2026-09-22c.xlsx')
REC = ART + '.SHIP_RECEIPT.json'
MIRROR = r'C:\Users\jerom\Desktop\claude\.cursor\qa-receipts\1f90ad41e4aead75.json'

notes = (
    "UIO V20 candidate 2026-09-22c (retention-safety pass). Base = candidate 2026-09-22b. "
    "NOT PROMOTED; V19 remains canonical. "
    "CELLS CHANGED THIS PASS (4 rows, AQ:AU): "
    "r54 PORTUGL LCV [5022,5438,5976,6384,6691] -> [5109,5425,5709,5967,6251] (reverted to candidate a); "
    "r90 CYPRUS LCV [3252,3506,3708,3811,3868] -> [2238,2339,2445,2521,2614] (reverted to candidate a); "
    "r69 POLAND LCV [61,49,37,26,16] -> [23,19,15,11,8]; "
    "r88 CYPRUS LD [261,256,249,245,244] -> [205,208,210,214,220]. "
    "Grand Total 2026-2030: 253145.15/246392.50/239403.81/232583.44/225964.19 -> "
    "252124.15/245134.50/237812.81/230830.44/224238.19. "
    "NEW HARNESS CHECK: verify_uio_v20.py v1.1.0 check10_retention_sanity. "
    "On candidate b it CONVICTS (FAIL): r90 CYPRUS LCV k2026=1.3738, r88 CYPRUS LD k2026=1.1375, "
    "r69 POLAND LCV k2026=2.1843. On candidate c it PASSES (81 rows evaluated, 0 violations). "
    "HARNESS VERDICT ON c: CONVICTED, 3 fails - check1 (r54 ratio 0.969 + r90 ratio 0.997), "
    "check5 (r54), check7 (measured 6.8/14.0/21.7/29.7/37.9 vs spec 7.8/15.6/23.2/30.6/37.7; 2027,2028 out of "
    "band; residual reported, not forced). No check10 failure. "
    "INVARIANTS: r79 unchanged from b; r25 CY2026F = 44926 locked; rows 22/24 AQ:AU remain live sheet-4 "
    "formulas; r54 and r90 equal candidate a exactly; Grand Total reconciles to the sum of rows in all 41 years. "
    "V19 mtime/size unchanged (1789744616.396761 / 789276); candidate a sha 7c4f5521685508fb and candidate b "
    "sha 5ec1ae2af7784743 unchanged. "
    "VERIFICATION METHOD (xlsx, no screenshots applicable): reopened with openpyxl and read every touched cell, "
    "the retention audit sheet and the Grand Total formula; recalculated with Excel COM (CalculateFullRebuild) and "
    "read back the cached Grand Total."
)

for p in (REC, MIRROR):
    if not os.path.exists(p):
        print('missing:', p)
        continue
    d = json.load(open(p, encoding='utf-8'))
    d['notes'] = notes
    d.setdefault('checks', [])
    d['checks'] += [
        {"id": "harness_convicts_b_on_check10", "ok": True,
         "detail": "verify_uio_v20.py v1.1.0 check10_retention_sanity FAIL on 2026-09-22b: r90 k=1.3738, r88 k=1.1375, r69 k=2.1843"},
        {"id": "harness_passes_c_on_check10", "ok": True,
         "detail": "check10 PASS on 2026-09-22c: 81 rows evaluated, 0 violations"},
        {"id": "retention_audit_sheet_written", "ok": True,
         "detail": "sheet 'V20 RETENTION AUDIT': 31 rows, 0 violations, 0 red cells"},
        {"id": "grand_total_reconciles", "ok": True,
         "detail": "sum of rows 7:90 == row 2 SUMPRODUCT for 2026-2030 after Excel CalculateFullRebuild"},
        {"id": "locked_and_links_intact", "ok": True,
         "detail": "r25 CY2026F=44926; rows 22/24 AQ:AU are live '4. ITUK UIO Projection' formulas"},
        {"id": "prior_artifacts_intact", "ok": True,
         "detail": "candidate a sha16 7c4f5521685508fb, candidate b sha16 5ec1ae2af7784743, V19 sha16 cdf070750674e71b"},
        {"id": "candidate_not_promoted", "ok": True,
         "detail": "candidate c is a candidate only; V19 is still canonical"},
    ]
    json.dump(d, open(p, 'w', encoding='utf-8'), indent=2)
    print('updated:', p, os.path.getsize(p), 'bytes')
print('artifact latest mtime_ms:', int(os.stat(ART).st_mtime * 1000))
