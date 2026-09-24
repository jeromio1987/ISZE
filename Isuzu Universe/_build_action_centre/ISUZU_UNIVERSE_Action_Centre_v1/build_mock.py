#!/usr/bin/env python3
"""Build the internal ISZE mock from attached extracts. No raw data is exported.

Usage: python build_mock.py --data-dir PATH --out-dir PATH
PDF snapshot extraction requires PyMuPDF: python -m pip install pymupdf
The requested workstation files are NOT silently substituted. Attached extracts
are explicitly registered as an alternative scope. Missing primary sources remain
validation tasks. Monetary and percentage values are calculated from source rows.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, re
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

VERSION = '1.0-review'
BUILD_DATE = '2026-09-23'
D = Decimal

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''): h.update(b)
    return h.hexdigest()

def number(v: Any) -> float:
    return float(D(str(v)))

def read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding='utf-8-sig', newline='') as f:
        return [dict(row, _source_row=i+2) for i, row in enumerate(csv.DictReader(f))]

def selected(rows, **where):
    matches = [r for r in rows if all(str(r.get(k)) == str(v) for k,v in where.items())]
    if len(matches) != 1:
        raise ValueError('Expected one source row for %r; found %d' % (where, len(matches)))
    return matches[0]

def delta(a,b): return float(D(b)-D(a))
def pct(a,b):
    if D(a) == 0: return None
    return float((D(b)/D(a)-1)*100)

def make(data_dir: Path) -> dict:
    sources=[]
    def register(sid, name, role, note, period='', snapshot=None, required=False):
        p=data_dir/name
        exists=p.is_file()
        s={'id':sid,'name':name,'role':role,'available':exists,'note':note,
           'period':period,'snapshot_date':snapshot,'sha256':sha(p) if exists else None,
           'requested_workstation_source':required}
        sources.append(s)
        return p

    register('requested_service','pms_capture_by_db_year.csv','Requested calculation source',
             'Not directly available from the Windows path. The attached presentation extract is explicitly identified below.',required=True)
    register('requested_spend','gps_spu_by_distributor.csv','Requested fleet comparison source',
             'Not directly available from the Windows path. The attached spend-per-truck extract is used only for the separate fleet-basis check.',required=True)
    register('requested_mix','pms_genuine_bvp_vs_price_2024_2025.csv','Requested Genuine/BVP source',
             'Not supplied here. The attached product-mix extract is the selected scope; it is not blended with a concession scope.',required=True)
    register('requested_concession','pms_campaign_suspect_by_db_family_2024_2025.csv','Required concession source',
             'Not supplied. No concession rate or family-level price conclusion is published.',required=True)
    register('requested_tender','tender_data.json','Required current tender feed',
             'Not supplied. The paper snapshot cannot be refreshed or treated as a current opportunity list.',required=True)
    register('business_context','01_ISUZU_AND_ISZE_BUSINESS.md','Account mapping reference',
             'Germany sold-to mapping is the basis for the account-routing validation task; it is not evidence that both accounts are covered in a selected extract.',
             'Business structure as of 19 September 2026','2026-09-19')
    mp=register('mix_extract','04_original_vs_value_parts_mix.csv','Selected attached extract',
                'ISZE-to-distributor purchasing by product subgroup. Full calendar 2024 and 2025 only are selected. BVP means Best Value Parts.',
                'Calendar 2024 and 2025', '2026-09-19')
    sp=register('service_extract','03_service_capture_by_market_family.csv','Selected attached extract',
                'Germany oil filters: total line, calendar 2025. Measured purchasing is compared with modelled expected units; no percentage above 100 is displayed.',
                'Calendar 2025', '2026-09-19')
    gp=register('spend_extract','02_spend_per_truck_by_market.csv','Fleet-basis check only',
                'A separate fleet basis is retained as a separate fact. It does not replace the service-demand denominator.',
                'Calendar 2025', '2026-09-19')
    dp=register('dealer_summary','sales_to_dealer_by_dealer_year.csv','Dealer coverage check only',
                'Counts named dealers and available years; no dealer fleet denominator or dealer year-on-year change is inferred.',
                'Calendar 2025', None)
    pp=register('paper','ISUZU_UNIVERSE_WHITE_PAPER_FINAL_v2_2026-09-23.pdf','Secondary document only',
                'Pages 21-22 are used only for paper-reported programme and tender snapshots. They are not a substitute for a credit ledger or live tender feed.',
                'Programme: June 2023-March 2026; tender snapshot: 22 September 2026','2026-09-23')
    op=register('older_tenders','10_gaps_accounts_tenders.csv','Older extract, NOT selected for the tender card',
                'A different, older opportunity population. It is not substituted for the requested 22 September feed.',
                'Older snapshot in the 19 September pack','2026-09-19')
    sources.extend([
        {'id':'credit_ledger','name':'Programme credit ledger and case register','role':'Required primary evidence','available':False,
         'note':'No identifiable programme credit/case ledger was supplied. Missing records are not counted as zero.',
         'period':'June 2023-March 2026','snapshot_date':None,'sha256':None,'requested_workstation_source':False},
        {'id':'classification','name':'Validated part-to-family membership','role':'Required classification check','available':False,
         'note':'The reviewed release and membership for front brake pads and blower filters are not attached. Family rates remain withheld.',
         'period':None,'snapshot_date':None,'sha256':None,'requested_workstation_source':False}
    ])
    mix=read_csv(mp); service=read_csv(sp); fleet=read_csv(gp); dealer=read_csv(dp)
    it24=selected(mix,distributor_code='ITUK',year=2024,product_subgroup='brake_pad')
    it25=selected(mix,distributor_code='ITUK',year=2025,product_subgroup='brake_pad')
    iu24=selected(mix,distributor_code='IUK',year=2024,product_subgroup='air_filter')
    iu25=selected(mix,distributor_code='IUK',year=2025,product_subgroup='air_filter')
    de=selected(service,distributor_code='GERMANY',year=2025,service_family='oil_filter',line_type='total')
    gf=selected(fleet,distributor_code='GERMANY',year=2025)
    iuf=selected(fleet,distributor_code='IUK',year=2025)
    for r in [it24,it25,iu24,iu25]:
        assert abs(D(r['original_eur'])+D(r['value_parts_eur'])-D(r['total_eur'])) <= D('.01')
        assert D(r['original_units'])+D(r['value_parts_units']) == D(r['total_units'])
    dr=[r for r in dealer if r['distributor_code']=='ITUK']
    years=sorted({int(r['year']) for r in dr})
    assert years == [2025], 'Dealer comparison scope changed; review the case wording.'
    dealer_count=len({r['dealer_name'] for r in dr})
    coverage=number(de['actual_units'])/number(de['expected_units'])*100
    display_coverage=coverage if 0 <= coverage <= 100 else None
    net_change=delta(iu24['total_eur'],iu25['total_eur'])
    bvp_change=delta(iu24['value_parts_eur'],iu25['value_parts_eur'])
    assert D(iu24['value_parts_eur']) == 0, 'The first BVP entry assumption needs review.'
    paper_credit=None; tender={}; extraction_errors=[]
    if pp.exists():
        try:
            import fitz
            with fitz.open(pp) as doc:
                t21=re.sub(r'\s+',' ',doc[20].get_text())
                t22=re.sub(r'\s+',' ',doc[21].get_text())
                cr=re.search(r'\u20ac([\d,]+) across 2023, 2025 and 2026',t21)
                if cr: paper_credit=int(cr.group(1).replace(',',''))
                for key,label in [('notices','Public notices collected'),('opportunities','Distinct opportunities'),
                    ('aftersales','With an aftersales signal'),('queue','In the action queue'),
                    ('due_14_days','Due within 14 days'),('outcomes','Outcomes recorded')]:
                    m=re.search(re.escape(label)+r'\s+(\d+)',t22)
                    if not m: raise ValueError('Cannot extract '+label+' from PDF page 22')
                    tender[key]=int(m.group(1))
        except (ImportError,ValueError,IndexError) as e:
            extraction_errors.append(str(e)); paper_credit=None; tender={}
    older=read_csv(op)
    old=[r for r in older if r['dataset']=='tender']
    older_count=len({r['opportunity_id'] for r in old})
    def metric(label,value,fmt='eur',basis='',kind='measured'):
        return {'label':label,'value':value,'format':fmt,'basis':basis,'kind':kind}
    def reference(sid,rows=None,selection='',method=''):
        return {'source_id':sid,'rows':rows or [],'selection':selection,'method':method}
    def base(cid,title,market,case_type,evidence,readiness,period):
        return dict(id=cid,title=title,market=market,case_type=case_type,evidence=evidence,
             readiness=readiness,period=period,initial_owner=None,initial_due_date=None,
             initial_outcome=None,initial_status='Not started',commercial_clearance=False)
    c1=base('AC-01','Brake pads','ITUK | UK trucks','Commercial signal','measured','Review now','Full calendar 2025 vs 2024')
    c1.update(headline=metric('Change in parts billed',delta(it24['total_eur'],it25['total_eur']),'eur_signed',
                 'ISZE to Isuzu Truck UK; selected brake-pad subgroup'),
        summary='Unit purchasing fell faster than billed value. Start with a distributor review, not a claim about dealer losses.',
        context_line='Relevant dealer fleet: not supplied',
        basis_label='Measured purchasing | selected attached extract',
        metrics=[metric('Parts billed, 2024',number(it24['total_eur']),basis='Calendar 2024; selected subgroup'),
                 metric('Parts billed, 2025',number(it25['total_eur']),basis='Calendar 2025; selected subgroup'),
                 metric('Value change',pct(it24['total_eur'],it25['total_eur']),'pct_signed',basis='2025 against 2024'),
                 metric('Unit change',pct(it24['total_units'],it25['total_units']),'pct_signed',basis='2025 against 2024')],
        chart={'type':'comparison','series':[{'label':'2024','value':number(it24['total_eur'])},{'label':'2025','value':number(it25['total_eur'])}],
               'title':'Parts billed to Isuzu Truck UK','format':'eur','caption':'Full calendar years; same selected subgroup. Not sales to end customers.'},
        facts=[f"{int(number(it24['total_units'])):,} units in 2024 and {int(number(it25['total_units'])):,} in 2025, on the selected product-mix scope.",
               f"The attached dealer summary has {dealer_count} named dealers, in {years[0]} only. It cannot explain a dealer year-on-year decline.",
               'Relevant fleet by dealer and validated brake-pad applicability are not supplied. No dealer service-demand rate is calculated.'],
        interpretation='The selected subgroup has a measured purchasing decline. A lower share of brake pads in a dealer\'s own 2025 parts purchases would be a mix signal, not proof of lost maintenance business.',
        limitation='No dealer-year comparison, causal price effect or unusually low dealer performance is established. A validated part mapping is still needed before a dealer-mix signal is scored.',
        next_action='Review the distributor decline. Then compare each dealer\'s brake-pad share of its own 2025 purchases with the ITUK network share, using one validated part set and one valuation basis.',
        checks=['Confirm the selected brake-pad membership before any product-specific intervention.',
                'Keep 2025 dealer snapshots separate from distributor 2024-2025 change.',
                'Treat mix differences as questions, not service-demand gaps.'],
        references=[reference('mix_extract',[it24['_source_row'],it25['_source_row']],
                     'ITUK; product_subgroup=brake_pad; years 2024 and 2025',
                     'Change = 2025 total_eur minus 2024 total_eur. Percentage change = (2025 / 2024 - 1) x 100.'),
                    reference('dealer_summary',selection='ITUK; distinct dealer_name and year',method='Count unique dealer names; inspect available calendar years.')],
        raw_facts={'value_2024':number(it24['total_eur']),'value_2025':number(it25['total_eur']),
                   'units_2024':number(it24['total_units']),'units_2025':number(it25['total_units']),'named_dealers':dealer_count,'dealer_years':years})
    c2=base('AC-02','Oil filters','Germany | ISD','Data and model validation','partial','Validate basis','Calendar 2025')
    c2.update(headline=metric('Of modelled service need supplied',display_coverage,'pct',
                        'Measured units divided by modelled expected units','modelled'),
        summary='Check the fleet denominator and supply accounts before using this as a distributor performance example.',
        context_line=f"{number(de['actual_revenue_eur']):,.0f} EUR parts billed | {int(number(de['trucks_in_service'])):,} modelled vehicles",
        basis_label='Modelled expectation + measured purchasing | basis unresolved',
        metrics=[metric('Parts billed',number(de['actual_revenue_eur']),basis='Germany oil filters; calendar 2025'),
                 metric('Service-model fleet',number(de['trucks_in_service']),'integer',basis='Service model, split by vehicle group; 2025',kind='modelled'),
                 metric('Separate spend-model fleet',number(gf['trucks_in_service']),'integer',basis='Historical fleet used for spend per truck; 2025',kind='modelled'),
                 metric('Modelled value difference',number(de['revenue_gap_eur']),basis='Source-reported service gap; not recoverable sales',kind='modelled')],
        chart={'type':'coverage','value':display_coverage,'title':'Purchasing against modelled oil-filter need',
               'caption':'Calendar 2025. The unfilled share is a model difference, not proven competitor sales.'},
        facts=[f"Measured oil-filter units: {number(de['actual_units']):,.0f}; modelled expected units: {number(de['expected_units']):,.1f}.",
               'The card uses the service-model fleet and expected units exactly as supplied. The spend-model fleet is shown separately, not substituted or averaged.',
               'The business-context account mapping names German sold-to accounts 93 and 2516. Their coverage and any indirect supply require a separate check.'],
        interpretation='Purchasing is below the selected model expectation. Both fleet-basis disagreement and possible account routing need checking before assigning a commercial cause.',
        limitation='No German dealer attribution, end-customer demand or alternate supplier is measured. The modelled value difference is not an expected sales gain.',
        next_action='Confirm German supply routing and both sold-to accounts, reconcile the fleet basis, then request sales-to-dealer information for the same scope.',
        checks=['Confirm both German sold-to accounts and any indirect supply routes.','Document why the two fleet bases differ.',
                'Request dealer-level purchases only after agreeing the comparison scope.'],
        references=[reference('service_extract',[de['_source_row']],
                     'GERMANY; year=2025; service_family=oil_filter; line_type=total',
                     'Displayed percentage = actual_units / expected_units x 100. The stored rounded rate is not the calculation input. Rates outside 0-100 are withheld, never capped.'),
                    reference('spend_extract',[gf['_source_row']],'GERMANY; year=2025','Fleet basis comparison only; not used in service-demand coverage.'),
                    reference('business_context',selection='Market mapping: ISD / Germany',method='Sold-to 93 and 2516 are mapping references, not a verification of supply coverage.')],
        raw_facts={'actual_units':number(de['actual_units']),'expected_units':number(de['expected_units']),
                   'service_fleet':number(de['trucks_in_service']),'spend_fleet':number(gf['trucks_in_service']),
                   'actual_revenue':number(de['actual_revenue_eur']),'source_revenue_gap':number(de['revenue_gap_eur']),
                   'source_gap_quotable':de['revenue_gap_quotable']=='True'})
    c3=base('AC-03','Air filters','IUK | UK light commercial','Avoid premature price action','measured','Review now','Full calendar 2025 vs 2024')
    c3.update(headline=metric('Parts billed in the selected 2025 scope',number(iu25['total_eur']),'eur',
                             'Genuine + BVP; attached product-mix extract'),
        summary='BVP enters the selected scope in 2025. Separate the mix change from any pricing conclusion.',
        basis_label='Measured purchasing mix | concession source missing',
        metrics=[metric('Parts billed, 2024',number(iu24['total_eur']),basis='Same selected subgroup; full calendar year'),
                 metric('BVP entry, 2025',number(iu25['value_parts_eur']),basis='BVP = Best Value Parts; zero in this 2024 scope'),
                 metric('Total value change',pct(iu24['total_eur'],iu25['total_eur']),'pct_signed',basis='2025 against 2024'),
                 metric('Total unit change',pct(iu24['total_units'],iu25['total_units']),'pct_signed',basis='2025 against 2024')],
        chart={'type':'stacked','series':[{'label':'2024','genuine':number(iu24['original_eur']),'bvp':number(iu24['value_parts_eur'])},
                                       {'label':'2025','genuine':number(iu25['original_eur']),'bvp':number(iu25['value_parts_eur'])}],
               'title':'Genuine and BVP, one source scope','format':'eur',
               'caption':'ISZE to IUK; full calendar years. BVP = Best Value Parts. No concession-scope values are mixed into these bars.'},
        facts=[f"Genuine parts billed rise within the selected scope; BVP adds a separate new contribution. BVP accounts for {bvp_change/net_change*100:.1f}% of the increase in billed value.",
               f"The selected extract contains {int(number(iu24['total_units'])):,} units in 2024 and {int(number(iu25['total_units'])):,} in 2025.",
               f"Market fleet context: {int(number(iuf['trucks_in_service'])):,} vehicles in the 2025 spend-per-truck extract. This is not a dealer fleet denominator."],
        interpretation='No immediate price action is indicated by this purchasing evidence alone. The BVP entry is part of the observed growth; it is not evidence of a price-response relationship.',
        limitation='The requested concession file is absent. The separate concession-scope total and the falling-concession claim are not used here. No competitor retail price is compared with a dealer reference price.',
        next_action='Review the Genuine/BVP change on this one scope. Obtain the concession source and reconcile its membership before adding any concession trend or price recommendation.',
        checks=['Keep Genuine and BVP visible on the same scope.','Do not blend the product-mix and concession totals.',
                'Any later competitor comparison needs matched tax, channel, pack and applicability.'],
        references=[reference('mix_extract',[iu24['_source_row'],iu25['_source_row']],
                    'IUK; product_subgroup=air_filter; years 2024 and 2025',
                    'Total = original_eur + value_parts_eur. BVP contribution to growth = change in BVP euro / change in total euro. Full-year comparison only.'),
                    reference('spend_extract',[iuf['_source_row']],'IUK; year=2025','Market fleet context only.'),
                    reference('requested_concession',selection='Not available',method='No concession percentage is computed.')],
        raw_facts={'value_2024':number(iu24['total_eur']),'value_2025':number(iu25['total_eur']),
                   'genuine_2024':number(iu24['original_eur']),'genuine_2025':number(iu25['original_eur']),
                   'bvp_2024':number(iu24['value_parts_eur']),'bvp_2025':number(iu25['value_parts_eur']),
                   'units_2024':number(iu24['total_units']),'units_2025':number(iu25['total_units'])})
    c4=base('AC-04','Front brake pads / blower filters','ISZE | family review','Classification before concession review','missing','Hold family rates','Intended comparison: calendar 2024-2025')
    c4.update(headline=metric('Concession review',None,'text','Classification and concession source required'),
        headline_text='Validation required',summary='Confirm what these families contain before interpreting discounts. Rates remain withheld.',
        basis_label='Missing primary source + unvalidated family membership',metrics=[],chart=None,
        facts=['The requested concession extract is not attached.',
               'The reviewer reported a tagging defect elsewhere in the classification. This is a reason to check membership, not proof that these two families are wrong.',
               'No euro opportunity, concession share or dealer performance score is published for these unvalidated categories.'],
        interpretation='This is a validation task, not a finding that pricing is too high or that support is unjustified.',
        limitation='Neither category contents nor concession concentration can be recomputed from the files supplied here.',
        next_action='Validate the part membership for each family, obtain the concession extract, then review whether discounted billing is concentrated in justified cases or repeated across ordinary business.',
        checks=['Record the reviewed classification release and family membership.','Check the dated reference-price basis before interpreting concessions.',
                'Keep front brake pads separate from the broader brake-pad group.'],
        references=[reference('classification',selection='Front brake pads and blower filters',method='Membership check outstanding.'),
                    reference('requested_concession',selection='Calendar 2024 and 2025',method='No rate displayed before primary evidence is available.')],raw_facts={})
    c5=base('AC-05',"Don't Lose the Deal",'ITUK | programme review','Missing programme evidence','partial','Reconcile ledger','Credits reported for 2023, 2025 and 2026')
    c5.update(headline=metric('Credits reported in the white paper',paper_credit,'eur',
                             'Secondary document only; not independently reconciled','reported'),
        summary='Reconcile the programme credits and their case records. The earlier credit labels remain an open question.',
        basis_label='Paper-reported amount | ledger and case register missing',metrics=[],chart=None,
        facts=['The white paper reports the programme amount on page 21. The credit ledger and case register needed to verify it are absent.',
               'The reviewer notes that the 2023 credits carry a different label. Confirm with Isuzu Truck UK whether they belong to this programme.',
               'The paper reports no structured cases. This mock does not convert an absent case register into a verified zero.'],
        interpretation='The next task is to reconcile the payment basis and document what the support funded. No return on the programme is established.',
        limitation='The amount is extracted from a secondary document, not calculated from credit lines. Annual allocation, the 2023 label and outcome coverage remain unresolved.',
        next_action='Ask Isuzu Truck UK to reconcile the differently labelled 2023 credits, identify the related parts/dealers, and provide support decisions, order references and outcomes.',
        checks=['Confirm whether the 2023-labelled credits belong to this programme.','Reconcile all credits to the ledger before treating the reported total as verified.',
                'Collect part, dealer, dated competitor evidence, support granted and the outcome.'],
        references=[reference('paper',selection='Page 21, section 6.4',method='Extract the reported amount from the document text. Status remains paper-reported, not ledger-verified.'),
                    reference('credit_ledger',selection='Programme credits and corresponding supported cases',method='Not supplied; no zero-case calculation is made.')],
        raw_facts={'paper_reported_credit_eur':paper_credit,'ledger_verified_credit_eur':None,'verified_case_count':None})
    c6=base('AC-06','Tender deadlines and outcomes','ISZE | tender review','Time-sensitive source refresh','partial','Refresh source','Historical snapshot: 22 September 2026')
    c6.update(headline=metric('Current time-critical opportunities',None,'text','Current feed is not attached'),headline_text='Refresh required',
        summary='The paper snapshot is dated. Refresh the feed before assigning opportunities or quoting a current deadline count.',
        basis_label='Historical paper snapshot | current feed missing',
        metrics=[metric('Due within 14 days in the snapshot',tender.get('due_14_days'),'integer',basis='22 September 2026; paper page 22',kind='reported'),
                 metric('Distinct opportunities in the snapshot',tender.get('opportunities'),'integer',basis='22 September 2026; paper page 22',kind='reported')],
        chart=None,
        facts=['The snapshot is not a live queue. Its deadline count does not automatically remain valid on later review dates.',
               'A different, older attached tender extract is registered in Sources but is not substituted for the requested population.',
               'No fleet make, truck count, tender value or maintenance-part demand is inferred. Missing tender value is not zero value.'],
        interpretation='Refresh and qualify the dated opportunities before allocating effort. Record a pursuit decision and a closure outcome for each supported opportunity.',
        limitation='The primary tender_data.json feed is absent. The paper\'s reported outcome count cannot establish the current state of the tender register.',
        next_action='Obtain a fresh tender feed, recalculate deadlines against the review date, assign relevant opportunities, and record won, lost or declined when each closes.',
        checks=['Load a dated current feed; do not treat the old countdown as current.','Check aftersales relevance without assuming Isuzu fleet make.',
                'Record owner, pursuit decision and closure outcome separately.'],
        references=[reference('paper',selection='Page 22, section 6.5; snapshot 22 September 2026',method='Extract reported snapshot counts; do not refresh them by changing the display date.'),
                    reference('requested_tender',selection='Current feed',method='Missing; live deadline and outcome counts remain unavailable.'),
                    reference('older_tenders',selection='dataset=tender',method='Different older population; excluded from the case headline.')],
        raw_facts={'paper_snapshot_date':'2026-09-22','paper_snapshot':tender,'older_attached_population':older_count,
                   'current_due_count':None,'current_outcome_count':None})
    cases=[c1,c2,c3,c4,c5,c6]
    assert len(cases)==6
    assert all(c['initial_owner'] is None and c['initial_due_date'] is None for c in cases)
    assert all(c['initial_outcome'] is None for c in cases)
    assert c2['headline']['value'] is None or c2['headline']['value'] <= 100
    assert c5['raw_facts']['verified_case_count'] is None
    assert c6['raw_facts']['current_due_count'] is None
    validation={
        'status':'Calculation checks passed; source limitations remain open',
        'computed_case_ids':['AC-01','AC-02','AC-03'],
        'secondary_or_missing_case_ids':['AC-04','AC-05','AC-06'],
        'checks':[
            'Six cases, all initially unassigned and undated.',
            'All monetary headlines in computed cases derived from selected source rows.',
            'Genuine plus BVP reconciles to total on all selected mix rows.',
            'Full calendar 2024 and 2025 used; no partial-2026 growth comparisons.',
            'ITUK and IUK remain separate; no cross-distributor dealer view.',
            'Germany service rate uses its own expected units; fleet bases are not blended.',
            'Out-of-range service percentages are withheld, not capped.',
            'No dealer coverage, dealer year-on-year attribution or price causality inferred.',
            'No primary-ledger zero or current tender count inferred from missing files.',
            'Portugal clutch case excluded; no unvalidated family concession rates published.',
            'No raw billing lines, full price list or source PDFs included in the output.'
        ],'pdf_extraction_errors':extraction_errors}
    return {'schema_version':1,'app_version':VERSION,'created_at':BUILD_DATE,
            'title':'ISUZU UNIVERSE | Internal Action Centre',
            'scope':'Internal ISZE review mock. No production authentication or distributor sharing.',
            'source_policy':'Metrics are calculated from explicitly selected attached extracts. Unavailable workstation sources stay listed as missing. Secondary document values are labelled, not promoted to verified measurements.',
            'sources':sources,'cases':cases,'validation':validation}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--data-dir',type=Path,required=True)
    ap.add_argument('--out-dir',type=Path,default=Path.cwd())
    args=ap.parse_args(); args.out_dir.mkdir(parents=True,exist_ok=True)
    data=make(args.data_dir)
    text=json.dumps(data,ensure_ascii=True,indent=2,allow_nan=False)
    (args.out_dir/'case_data.json').write_text(text,encoding='utf-8')
    (args.out_dir/'validation_report.json').write_text(json.dumps(data['validation'],indent=2),encoding='utf-8')
    template=Path(__file__).with_name('template.html').read_text(encoding='utf-8')
    safe=text.replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    output=template.replace('/*__CASE_DATA__*/',safe)
    if '/*__CASE_DATA__*/' in output: raise RuntimeError('Unreplaced data placeholder')
    name='ISUZU_UNIVERSE_Action_Centre_v1.html'
    (args.out_dir/name).write_text(output,encoding='utf-8')
    print(json.dumps({'html':str(args.out_dir/name),'cases':len(data['cases']),
                      'calculated_cases':data['validation']['computed_case_ids'],
                      'validation':data['validation']['status']},indent=2))

if __name__=='__main__': main()
