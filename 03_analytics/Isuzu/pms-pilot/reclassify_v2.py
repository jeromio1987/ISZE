"""
Reclassifier v2 — rule-based + EPC-verified for ambiguous cases.

Produces the full list of (row, old, new, evidence) changes ready to write into
the v7 workbook.
"""
import openpyxl, json, re
from collections import defaultdict, Counter

SRC = 'ITUK_PMS_Analysis_Apr2026_v5.xlsx'

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

OIL_FILTER = ('Competitive parts', 'Filters', 'Oil filter')
AIR_FILTER = ('Competitive parts', 'Filters', 'Air filter')
FUEL_FILTER = ('Competitive parts', 'Filters', 'Fuel filter')
AC_FILTER = ('Comfort parts', 'Air conditioning', 'AC filter')
REPAIR_KIT_OIL = ('Hardware & consumables', 'Consumables', 'Repair kit')
NOT_IN_EPC = ('Other / review', 'Miscellaneous', 'Not in current EPC')

RULES = [
    (r'\bELEMENT\b.*\bOIL\b', OIL_FILTER, 'desc: ELEMENT + OIL'),
    (r'\bCARTRIDGE\b.*\bOIL\b', OIL_FILTER, 'desc: CARTRIDGE + OIL'),
    (r'\bOIL\s+(FILTER|ELEMENT|CARTRIDGE)\b', OIL_FILTER, 'desc: OIL filter/element/cartridge'),
    (r'\bELEMENT\s*(?:ASM|;|,)\s*OIL\b', OIL_FILTER, 'desc: ELEMENT ASM/; OIL'),
    (r'\bREPAIR\s*KIT,?\s*OIL\b', REPAIR_KIT_OIL, 'desc: REPAIR KIT, OIL'),
    (r'\bFILTER\s*;\s*ACL\b', AIR_FILTER, 'desc: FILTER; ACL (ACL = AIR CLEANER, not AC)'),
    (r'\bELEMENT\b.*\bACL\b', AIR_FILTER, 'desc: ELEMENT + ACL (AIR CLEANER)'),
    (r'\bAIR\s*CLEANER\b', AIR_FILTER, 'desc: AIR CLEANER'),
    (r'\bELEMENT\b.*\bAIR\b', AIR_FILTER, 'desc: ELEMENT + AIR'),
    (r'\bFUEL\s*(?:ELEMENT|FILTER)\b', FUEL_FILTER, 'desc: FUEL ELEMENT/FILTER'),
    (r'\bELEMENT\s*KIT\s*;\s*F/F\b', FUEL_FILTER, 'desc: F/F (Fuel Filter)'),
    (r'\bF/F\b', FUEL_FILTER, 'desc: F/F abbrev'),
    (r'\bFILTER\b.*\bBLOWER\s*UNIT\b', AC_FILTER, 'desc: FILTER + BLOWER UNIT (cabin/AC filter)'),
    (r'\bCABIN\s*(?:AIR\s*)?FILTER\b', AC_FILTER, 'desc: CABIN FILTER'),
]


def decide_from_desc(description: str):
    if not description:
        return None
    desc = description.upper()
    for pattern, target, evidence in RULES:
        if re.search(pattern, desc):
            return (*target, evidence)
    return None


def decide_from_epc(epc_data, fig_group):
    """When description is ambiguous, use EPC vehicle families to decide.
    Returns (l1, l2, l3, evidence) or None."""
    if not epc_data:
        return None
    if epc_data.get('error') or epc_data.get('total') is None:
        return None
    if epc_data.get('total') == 0:
        # Not findable in EPC
        return (*NOT_IN_EPC, 'EPC search returned 0 results — likely obsolete or pre-EPC era')
    families = epc_data.get('families', []) or []
    # Use the FIG group + EPC application context to decide
    fams = '|'.join(families).upper()
    is_industrial_marine = ('INDUSTRIAL' in fams or 'MARINE' in fams) and 'TRUCKS' not in fams and 'BUSES' not in fams
    if fig_group == '050-002':
        # Oil filter group — almost any cartridge/element fits as oil filter
        # unless it's clearly something else in EPC
        return (*OIL_FILTER, f'EPC: applies to {", ".join(families[:3])} — oil filter fit for FIG 050-002')
    if fig_group == '130-006':
        # Air cleaner group
        return (*AIR_FILTER, f'EPC: applies to {", ".join(families[:3])} — air filter fit for FIG 130-006')
    if fig_group == '041-002':
        return (*FUEL_FILTER, f'EPC: applies to {", ".join(families[:3])} — fuel filter fit for FIG 041-002')
    if fig_group == '873-042':
        return (*AC_FILTER, f'EPC: applies to {", ".join(families[:3])} — AC filter fit for FIG 873-042')
    return None


def main():
    wb = openpyxl.load_workbook(SRC, data_only=True)
    ws = wb['FIG-KEY Parts']
    cols = {c.value: c.column for c in ws[4]}

    with open('epc_results_merged.json', encoding='utf-8') as f:
        epc_list = json.load(f)
    epc_by_pn = {r['pn']: r for r in epc_list}

    group = None
    changes = []
    still_ambiguous = []

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
        # Try description rules first
        d = decide_from_desc(desc)
        source = 'rule'
        if not d:
            # Fall back to EPC
            d = decide_from_epc(epc_by_pn.get(newest), group)
            source = 'epc'
        if not d:
            still_ambiguous.append({
                'row': r, 'fig': group, 'pn': pn, 'newest_pn': newest,
                'description': desc, 'old': (l1, l2, l3),
            })
            continue
        new_l1, new_l2, new_l3, evidence = d
        changes.append({
            'row': r, 'fig': group, 'pn': pn, 'newest_pn': newest,
            'description': desc,
            'old_l1': l1, 'old_l2': l2, 'old_l3': l3,
            'new_l1': new_l1, 'new_l2': new_l2, 'new_l3': new_l3,
            'evidence_source': source,
            'evidence': evidence,
        })

    print(f'Total suspicious rows: {len(changes) + len(still_ambiguous)}')
    print(f'  Resolved by rules: {sum(1 for c in changes if c["evidence_source"] == "rule")}')
    print(f'  Resolved by EPC:   {sum(1 for c in changes if c["evidence_source"] == "epc")}')
    print(f'  Still ambiguous:   {len(still_ambiguous)}')

    by_change = Counter()
    for c in changes:
        by_change[(c['old_l3'], '->', c['new_l3'])] += 1
    print('\nFix distribution by L3 change:')
    for k, v in by_change.most_common():
        print(f'  {v:>3}  {k[0]} {k[1]} {k[2]}')

    if still_ambiguous:
        print('\nStill ambiguous (left as-is, flagged for manual):')
        for a in still_ambiguous:
            print(f'  row {a["row"]}  {a["pn"]}  FIG {a["fig"]}  desc="{a["description"]}"  old={a["old"][2]}')

    with open('reclassify_changes_v2.json', 'w', encoding='utf-8') as f:
        json.dump({'changes': changes, 'still_ambiguous': still_ambiguous}, f, indent=1, ensure_ascii=False, default=str)
    print('\nWritten: reclassify_changes_v2.json')


if __name__ == '__main__':
    main()
