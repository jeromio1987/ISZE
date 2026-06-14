"""
Rule-based reclassification of FIG-KEY Parts rows whose L1/L2/L3 is suspect.

For each suspicious row, decide a corrected (L1, L2, L3) from the file's own
Description column. Rows that remain genuinely ambiguous are flagged for EPC
verification.

Output: a list of {row, pn, old, new, evidence} dicts ready to write into the
workbook + a Classification_Fixes sheet.
"""
import openpyxl, json, re
from collections import defaultdict, Counter

SRC = 'ITUK_PMS_Analysis_Apr2026_v5.xlsx'

# (FIG_KEY, L1, L2, L3) -> reason for flagging
SUSPICIOUS = {
    ('050-002', 'Hardware & consumables', 'Consumables', 'Oil / lubricant'): 'lubricant in oil-filter FIG',
    ('050-002', 'Other / review', 'Miscellaneous', 'Review needed'): 'explicit review',
    ('050-002', 'Competitive parts', 'Filters', 'Other filter'): 'non-oil filter in oil-filter FIG',
    ('050-002', 'Competitive parts', 'Air system', 'Other air system'): 'air-system part in oil-filter FIG',
    ('130-006', 'Comfort parts', 'Air conditioning', 'Other A/C'): 'A/C in air-cleaner FIG',
    ('130-006', 'Competitive parts', 'Air system', 'Other air system'): 'misc air in air-cleaner FIG',
    ('130-006', 'Other / review', 'Miscellaneous', 'Review needed'): 'explicit review',
    ('041-002', 'Competitive parts', 'Fuel system', 'Other fuel system'): 'misc fuel in fuel-filter FIG',
    ('041-002', 'Other / review', 'Miscellaneous', 'Review needed'): 'explicit review',
    ('873-042', 'Comfort parts', 'Air conditioning', 'Blower / fan'): 'blower/fan in AC-filter FIG (entire group)',
}

# Target (L1, L2, L3) per part type
OIL_FILTER = ('Competitive parts', 'Filters', 'Oil filter')
AIR_FILTER = ('Competitive parts', 'Filters', 'Air filter')
FUEL_FILTER = ('Competitive parts', 'Filters', 'Fuel filter')
AC_FILTER = ('Comfort parts', 'Air conditioning', 'AC filter')
REPAIR_KIT_OIL = ('Hardware & consumables', 'Consumables', 'Repair kit')
AMBIGUOUS = (None, None, None)  # left as-is, flagged for EPC

# Regex-based decision rules — checked in order. First match wins.
# Each rule: (description_pattern, target_l1_l2_l3, evidence_string)
RULES = [
    # FIG 050-002 oil-filter family
    (r'\bELEMENT\b.*\bOIL\b', OIL_FILTER, 'Description contains ELEMENT + OIL'),
    (r'\bCARTRIDGE\b.*\bOIL\b', OIL_FILTER, 'Description contains CARTRIDGE + OIL'),
    (r'\bOIL\s+(FILTER|ELEMENT|CARTRIDGE)\b', OIL_FILTER, 'Description names OIL filter/element/cartridge'),
    (r'\bELEMENT\s*(?:ASM|;|,)\s*OIL\b', OIL_FILTER, 'Description: ELEMENT ASM/; OIL'),
    (r'\bREPAIR\s*KIT,?\s*OIL\b', REPAIR_KIT_OIL, 'Repair kit, oil-related'),

    # FIG 130-006 air-cleaner family — "ACL" is the abbrev for "AIR CLEANER" in Isuzu nomenclature
    (r'\bFILTER\s*;\s*ACL\b', AIR_FILTER, 'Description: FILTER; ACL (ACL = AIR CLEANER, not AC)'),
    (r'\bELEMENT\b.*\bACL\b', AIR_FILTER, 'Description: ELEMENT + ACL (AIR CLEANER)'),
    (r'\bAIR\s*CLEANER\b', AIR_FILTER, 'Description contains AIR CLEANER'),
    (r'\bELEMENT\b.*\bAIR\b', AIR_FILTER, 'Description: ELEMENT + AIR'),

    # FIG 041-002 fuel-filter family
    (r'\bFUEL\s*(?:ELEMENT|FILTER)\b', FUEL_FILTER, 'Description: FUEL ELEMENT/FILTER'),
    (r'\bELEMENT\s*KIT\s*;\s*F/F\b', FUEL_FILTER, 'F/F = Fuel Filter'),
    (r'\bF/F\b', FUEL_FILTER, 'F/F abbrev for Fuel Filter'),

    # FIG 873-042 AC-filter family — "BLOWER UNIT" is where the cabin/AC filter sits
    (r'\bFILTER\b.*\bBLOWER\s*UNIT\b', AC_FILTER, 'FILTER housed in BLOWER UNIT = AC/cabin filter'),
    (r'\bCABIN\s*(?:AIR\s*)?FILTER\b', AC_FILTER, 'Description names cabin air filter'),
]


def decide(description: str):
    """Return (new_l1, new_l2, new_l3, evidence) or AMBIGUOUS + reason."""
    if not description:
        return AMBIGUOUS + ('empty description',)
    desc = description.upper()
    for pattern, target, evidence in RULES:
        if re.search(pattern, desc):
            return (*target, evidence)
    return AMBIGUOUS + (f'no rule matched: "{description}"',)


def main():
    wb = openpyxl.load_workbook(SRC, data_only=True)
    ws = wb['FIG-KEY Parts']
    cols = {c.value: c.column for c in ws[4]}

    group = None
    changes = []
    ambiguous = []

    for r in range(1, ws.max_row + 1):
        a = ws.cell(r, 1).value
        if a and isinstance(a, str) and a.startswith('FIG-KEY'):
            group = a.split('  ')[0].replace('FIG-KEY ', '').strip()
            continue
        if not a or a == 'P/N':
            continue
        l1 = ws.cell(r, cols['Level 1 Family']).value
        l2 = ws.cell(r, cols['Level 2 Group']).value
        l3 = ws.cell(r, cols['Level 3 Type']).value
        key = (group, l1, l2, l3)
        if key not in SUSPICIOUS:
            continue
        pn = ws.cell(r, cols['P/N']).value
        newest = ws.cell(r, cols['Newest P/N']).value
        desc = ws.cell(r, cols['Description']).value
        new_l1, new_l2, new_l3, evidence = decide(desc)
        if new_l1 is None:
            ambiguous.append({
                'row': r, 'fig': group, 'pn': pn, 'newest_pn': newest,
                'description': desc, 'old': (l1, l2, l3), 'reason': evidence,
            })
        else:
            changes.append({
                'row': r, 'fig': group, 'pn': pn, 'newest_pn': newest,
                'description': desc,
                'old_l1': l1, 'old_l2': l2, 'old_l3': l3,
                'new_l1': new_l1, 'new_l2': new_l2, 'new_l3': new_l3,
                'evidence': evidence,
            })

    print(f'Suspicious rows in source: {len(changes) + len(ambiguous)}')
    print(f'Rule-based fixes proposed: {len(changes)}')
    print(f'Ambiguous (need EPC): {len(ambiguous)}')

    by_change = Counter()
    for c in changes:
        by_change[(c['old_l3'], '->', c['new_l3'])] += 1
    print('\nFix distribution by L3 change:')
    for k, v in by_change.most_common():
        print(f'  {v:>3}  {k[0]} {k[1]} {k[2]}')

    print('\n=== Ambiguous PNs needing EPC lookup ===')
    seen = set()
    for a in ambiguous:
        pn = a['newest_pn'] or a['pn']
        if pn in seen: continue
        seen.add(pn)
        print(f'  {pn}  FIG {a["fig"]}  desc="{a["description"]}"  old=({a["old"][2]})')
    print(f'  Unique ambiguous PNs: {len(seen)}')

    with open('reclassify_changes.json', 'w', encoding='utf-8') as f:
        json.dump({'changes': changes, 'ambiguous': ambiguous}, f, indent=1, ensure_ascii=False, default=str)
    with open('reclassify_ambiguous_pns.json', 'w', encoding='utf-8') as f:
        json.dump(sorted(seen), f, indent=1)
    print('\nWritten: reclassify_changes.json, reclassify_ambiguous_pns.json')


if __name__ == '__main__':
    main()
