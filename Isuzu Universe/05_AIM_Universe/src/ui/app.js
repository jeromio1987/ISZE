<script>/* ISZE AIM pricing decisions - internal, self-contained review component.
   One scenario record is used by every view, the save and every export.
   No server writes, no approvals, no price changes. */
'use strict';
(function(root){
const D=JSON.parse(document.getElementById('case-data').textContent);
const E=AIMEngine, X=AIMExport, C=AIMCandidates, K=AIMCases, CT=AIMContracts, M=AIMComparable;
const store=AIMScenario.makeScenarioStore(D,E);
const repo=K.makeRepository({
  forceMemory: !(function(){try{root.localStorage.setItem('__t','1');root.localStorage.removeItem('__t');return true;}catch(e){return false;}})()
});
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const num=(v,d=0)=>v===null||v===undefined||!Number.isFinite(Number(v))?'Not supplied':Number(v).toLocaleString('en-GB',{minimumFractionDigits:d,maximumFractionDigits:d});
const eur=(v,d=0)=>v===null||v===undefined||!Number.isFinite(Number(v))?'Not calculated':new Intl.NumberFormat('en-IE',{style:'currency',currency:'EUR',minimumFractionDigits:d,maximumFractionDigits:d}).format(v);
const pct=v=>v===null||v===undefined||!Number.isFinite(Number(v))?'Not comparable':`${v>0?'+':''}${num(v,1)}%`;
const signedEUR=v=>`${v>0?'+':''}${eur(v)}`;
const color=v=>v===null||v===undefined?'':v<0?'neg':v>0?'pos':'';
const views=['decision','position','objectives','economics','candidates','case','action'];
/* Every view key needs a label here. `views` above is the set of keys the router
   accepts; TAB_LABELS is what a reader sees. The `case` key - the exact-part
   review reached from a candidate row - was in the first list and missing from
   the second, so its tab rendered the raw word "case". Found during the MARKET
   panel work; pre-existing at HEAD, not introduced then. */
const TAB_LABELS=[['decision','Sales evidence'],['position','Price position'],['objectives','Two objectives'],['economics','Price & profit test'],['candidates','Candidates'],['case','Part review'],['action','Internal action']];
const ordered=['IMOTORS-CABIN','ITUK-TURBO','ITUK-PADS','ITUK-DISCS','IMOTORS-OIL'];
let state={unsavedReview:{},caseId:'IMOTORS-CABIN',compare:'half',view:'objectives',objective:'revenue',market:'all',billingMetric:'billingEUR',
           candidateQuery:'',candidatePage:1,candidatePageSize:50,candidateCriteria:{},
           candidateSortKey:'observed_billing_eur',candidateSortDirection:'desc',
           partRoute:null,offerDate:null,viewError:null,dealer:null};

/* ---------------------------------------------------------------- helpers */
function current(){return D.cases.find(c=>c.id===state.caseId)||D.cases[0];}
/* The working record, with no side effect. The caller decides whether naming a
   case should also materialise its default: painting does, restoring does not. */
function scenario(){return state.caseId?store.get(state.caseId):null;}
function offerDate(){const s=scenario();if(s.offer_effective_date)return s.offer_effective_date;
  const b=D.meta.costBases.find(x=>x.status==='forward');return b?(b.offer_effective_from||null):null;}
function basisOptions(){return (D.meta.costBases||[]).filter(b=>b.status==='forward');}
function caseResult(){return store.calculate(state.caseId);}
function coin(){const s=scenario();return {name:(D.meta.costBases||[]).find(b=>b.basis_id===s.cost_basis_id)||null};}
function sourceButton(){return '<button class="sourcesbutton" data-sources>Source and calculation basis</button>';}
function firstError(){return null;}
/* UX-01. The one working context, read from the open case and the address. A
   dealer selection is private working state: it is never written into the
   address, and it is honoured only on a dealer-scope case that lists the dealer. */
function context(){return AIMScenario.contextFor(D,current(),{compare:state.compare,dealer:state.dealer});}
function contextStrip(x){
  const scope=x.scope==='dealer'?'dealer scope':'national scope';
  return `<div class="context-strip" aria-label="Working context" data-context="${esc(AIMScenario.contextKey(x))}"><span><b>Distributor</b> ${esc(x.distributor||'not stated')}</span> &middot; <span><b>Account</b> ${esc(x.purchasing_account||'not stated')}, ${scope}</span> &middot; <span><b>Original part</b> ${esc(x.original_part||'not stated')}</span> &middot; <span><b>Family</b> ${esc(x.family||'not stated')}</span> &middot; <span><b>Source version</b> ${esc(x.source_version||'not declared')}</span> &middot; <span><b>Period</b> ${esc(x.period||'not stated')}</span></div>`;
}

/* UX-03. The assumptions the visible numbers rest on, and the two questions a
   reader is entitled to ask of them: which exact inputs produced this result,
   and what is wrong with the field I just typed into.

   Both are computed from the ONE working record and written onto the same page
   as data-trace and as per-field data-state attributes, so the reader, the
   export and the test all read one record rather than three copies that can
   drift apart. */

/* The inputs the visible results rest on. Every key is a declared scenario
   field; no view state and no derived figure is in here. */
const TRACE_INPUTS=['price_before','price_after','quantity_before','quantity_after','scope',
  'pack_size','support_eur','cost_eur','cost_basis_id','cost_basis_source','quantity_label',
  'evidence_period','offer_effective_date','selected_alternative_id'];
const TRACE_LABELS={price_before:'scenario base price',price_after:'proposed net price',
  quantity_before:'eligible base quantity',quantity_after:'proposed total quantity',scope:'volume scope',
  pack_size:'pack size',support_eur:'one-off support',cost_eur:'unit parts purchase cost',
  cost_basis_id:'supplier-cost basis',cost_basis_source:'cost source',quantity_label:'volume basis label',
  evidence_period:'evidence period',offer_effective_date:'offer effective date',
  selected_alternative_id:'selected option'};

/* A small deterministic fingerprint over the traced inputs and the two results.
   Plain arithmetic, no dependency, so it behaves the same everywhere. */
function traceFingerprint(obj){
  const text=JSON.stringify(obj);
  let h1=0x811c9dc5,h2=0x1000193;
  for(let i=0;i<text.length;i++){
    const ch=text.charCodeAt(i);
    h1=((h1^ch)*16777619)>>>0;
    h2=((h2+ch*2654435761)>>>0);
  }
  return 'a03-'+h1.toString(16).padStart(8,'0')+h2.toString(16).padStart(8,'0');
}

function assumptionTrace(){
  const s=scenario(),r=caseResult();
  const inputs={};
  TRACE_INPUTS.forEach(k=>{inputs[k]=(s&&s[k]!==undefined)?s[k]:null;});
  const results={ok:r.ok,revenue_change:r.revenue_change,gp_change:r.gp_change,
    margin_after_pct:r.margin_after_pct,quantity_after:r.quantity_after};
  const fingerprint=traceFingerprint({inputs,results});
  const label=String(s.quantity_label||'').toLowerCase();
  const isCommitment=label.indexOf('commitment')>=0||label.indexOf('observed')>=0;
  return {
    case_id:state.caseId,
    scenario_version:s.version,
    inputs:inputs, results:results, fingerprint:fingerprint,
    labels:TRACE_LABELS,
    commitment:{label:s.quantity_label||null,is_commitment:isCommitment,
      statement:isCommitment
        ? 'The volume basis is recorded: "'+s.quantity_label+'". The result rests on that recorded basis, not on a modelled response.'
        : 'A manual scenario on a stated assumption ("'+(s.quantity_label||'manual')+'"): the result is what the entered inputs produce, and it is not a commitment or a forecast.'},
    statement:'Every visible result is produced by these inputs and by no other. The same fingerprint is written onto the view as data-trace, so the numbers on screen are tied to the exact record they came from.'
  };
}

/* The per-field verdict, drawn from the engine's own validation so there is no
   second set of rules. A blank is unknown, a zero is a stated value, and neither
   is an error; only a real entry problem is an error. */
function fieldIssues(){
  const s=scenario(),v=E.validateScenario(s),st=v.states||{};
  const field=(id,state,text)=>({field:id,state:state||'unknown',text:text});
  const fields=[];
  const priceText=(id,label)=>{
    const state=st[id==='s-newP'?'price_after':id==='s-baseP'?'price_before':null]||'value';
    if(state==='invalid')return field(id,'invalid','The '+label+' must be a number above zero. It is not, so nothing is calculated from this field.');
    if(state==='unknown')return field(id,'unknown','The '+label+' is empty. An empty price is an unknown, not a price of zero, so the result is not calculated.');
    return field(id,'value','A stated '+label+'. The result uses this exact value.');
  };
  fields.push(priceText('s-baseP','scenario base price'));
  fields.push(priceText('s-newP','proposed net price'));
  const qb=st.quantity_before||'value';
  fields.push(field('s-baseQ',qb,qb==='invalid'?'The starting quantity must be a number above zero.':qb==='unknown'?'No starting quantity is stated, so there is nothing to price.':'The recorded eligible quantity this scenario rests on.'));
  const qa=s.quantity_after===null||s.quantity_after===undefined?'unknown':(st.quantity_after||'value');
  fields.push(field('s-qty',qa,qa==='zero'?'Zero is a full withdrawal, not a price scenario. Record it as a decision to stop supplying this part.':qa==='invalid'?'The proposed quantity is not a number. Leave it blank to keep the starting quantity.':qa==='unknown'?'Blank means the quantity does not change. That is an unknown volume, not a volume of zero.':'A stated proposed quantity; the result uses it.'));
  const cst=st.cost||'unknown';
  fields.push(field('s-cost',cst,cst==='zero'?'A parts cost of zero is a stated value and makes gross margin equal the price, so it is reported rather than assumed.':cst==='invalid'?'The parts cost is not a number. Leave it blank if no verified cost exists.':cst==='unknown'?'No cost is entered, so gross profit and gross margin are not calculated. A missing cost is not a cost of zero, and revenue is unaffected.':'A stated parts purchase cost; gross profit is calculated from it.'));
  const sup=st.support||'unknown';
  fields.push(field('s-support',sup,sup==='zero'?'Support of zero is a stated assumption, not proof that no support exists.':sup==='invalid'?'Support cannot be a negative amount.':sup==='unknown'?'No support is entered. It is treated as none for this scenario and shown as such.':'The one-off support, deducted once from gross profit.'));
  fields.push(field('s-pack','value','Whole order increments: a required quantity rounds up to a real pack.'));
  const bad=v.errors||[];
  return {
    ok:v.ok,
    fields:fields,
    errors:bad,
    statement:v.ok?'Every field holds a value, a stated zero or a stated unknown. No field is in error.'
      :bad.length+' field(s) are in error. Each is named below; the scenario is not calculated until they are corrected.'
  };
}

/* UX-04. A sensitivity view over the SAME one engine. Each row is one engine
   call with its own stated inputs; a point whose profit is suppressed by a
   missing cost prints the reason in place of a figure rather than a zero. The
   numeric table is always rendered, so the chart is never the only carrier. */
function sensitivityView(){
  const sens=store.sensitivity(state.caseId);
  const row=p=>`<tr data-sens="${esc(p.label)}" data-profit-state="${esc(p.profit_state)}"><td>${esc(p.label)}</td>`
    +`<td class="n">${p.price_after===null?'-':eur(p.price_after,2)}</td>`
    +`<td class="n">${p.quantity_after===null?'unchanged':num(p.quantity_after,0)}</td>`
    +`<td class="n ${p.revenue_change===null?'':color(p.revenue_change)}">${p.ok&&p.revenue_change!==null?signedEUR(p.revenue_change):'-'}</td>`
    +`<td class="n ${p.gp_change===null?'':color(p.gp_change)}">${p.gp_change!==null?signedEUR(p.gp_change):(p.profit_state==='suppressed'?'Not calculated':'<span class="small">'+esc(p.error||'not calculated')+'</span>')}</td></tr>`;
  const table=(title,rows,note)=>`<div class="panel"><h3>${esc(title)}</h3><p class="small">${esc(note)}</p><div class="tablewrap" tabindex="0" aria-label="Scrollable table"><table><thead><tr><th>Point</th><th class="n">Proposed price</th><th class="n">Total quantity</th><th class="n">Revenue change</th><th class="n">Gross-profit change</th></tr></thead><tbody>${rows.map(row).join('')}</tbody></table></div></div>`;
  const base=sens.baseline;
  return `<div class="inputsnote"><b>${esc(sens.no_forecast)}</b> Engine entry point: ${esc(sens.engine_entry_point)}.</div>
  ${sens.profit_suppressed?unavailableBlock({title:'Gross profit is not plotted for these points',reason:esc(sens.statement),required:'the parts purchase cost for '+esc(current().pn)+' per the declared supplier purchase-cost calculation, or a manually entered cost labelled as an assumption',scope:'sensitivity view'}):''}
  <div class="panel"><h3>Unchanged offer</h3><div class="evidence-line"><span>Revenue change at the unchanged offer</span><b>${signedEUR(base.revenue_change)}</b></div><div class="evidence-line"><span>Gross-profit change at the unchanged offer</span><b>${base.gp_change!==null?signedEUR(base.gp_change):'Not calculated (no cost applied)'}</b></div></div>
  ${table('Sensitivity to the proposed price',sens.price_points,'The proposed price moves in stated steps and the volume basis is unchanged. Each row is the engine\'s own result for that price, not a trend line.')}
  ${table('Sensitivity to the assumed quantity',sens.volume_points,'The quantity moves in stated steps and the price is unchanged. The model does not predict volume; these are stated test assumptions.')}`;
}


/* ===========================================================================
   Ported from the retired second view layer (src/ui/views.js and render.js).

   Two view layers existed for this one component. The retired one held features
   this shipped layer did not, so the features are moved here rather than the
   layer. Each block below says which view raised it and what it prevents.

   Nothing here reformats an existing block, and nothing here changes a figure.
   =========================================================================== */

/* UX-06.

   An absent quantity must be an explicit amber state that names the reason and
   what would supply it. Before this, a missing cost was rendered as the words
   "Cost required" in an ordinary warn panel, which a reader can mistake for a
   step still to come rather than a figure that does not exist. A blank or an
   ordinary panel is a FAIL here, not a pass.

   The colours are carried inline rather than left to a stylesheet, because the
   artifact's shell stylesheet is the frozen v03 one and declares no rule for
   this class: any rule for it lives in a QA harness builder that is not
   assembled. Without the inline declaration the block would render as a plain
   white panel with the word "Unavailable", which is exactly the reading this
   state exists to prevent. The house colours are used: amber 96620d on fffaf1
   with an ead7b9 border, so the state is distinguishable from an ordinary warn
   panel, which carries the same pale background and no amber border. */
const UNAVAILABLE_STYLE='background:#fffaf1;border:1px solid #ead7b9;border-left:4px solid #96620d;border-radius:10px;padding:18px;margin-bottom:15px';
function unavailableBlock(u){
  if(!u)return '';
  return `<div class="panel unavailable" role="status" aria-live="polite" data-unavailable="${esc(u.scope||'')}" style="${UNAVAILABLE_STYLE}">
  <div class="eyebrow" style="color:#96620d;font-size:10px;font-weight:750;letter-spacing:1.5px;text-transform:uppercase;margin:0 0 6px">Unavailable</div>
  <h3 style="color:#7d5209;font-size:16px;margin:0 0 9px;line-height:1.3">${esc(u.title)}</h3>
  <p class="small" style="color:#5f7183;margin:0 0 12px">${esc(u.reason)}</p>
  ${u.required?`<div class="evidence-line" style="display:flex;align-items:baseline;justify-content:space-between;gap:15px;margin:7px 0;font-size:12px"><span>What is required</span><b style="font-size:15px;color:#102b43">${esc(u.required)}</b></div>`:''}
  ${u.scope?`<div class="evidence-line" style="display:flex;align-items:baseline;justify-content:space-between;gap:15px;margin:7px 0;font-size:12px"><span>Scope</span><b style="font-size:15px;color:#102b43">${esc(u.scope)}</b></div>`:''}</div>`;
}

/* REVIEW-04, ported. The retired layer prefixed every view with the exact
   original part reference so it could not be lost behind a tab. In this layer it
   was only present where the case text happened to mention it: measured on the
   five cases, the internal action view carried it on 0 of 5 and the objectives
   view on 1 of 5. It is a navigation aid, not a calculation, and it is printed as
   the reference itself, never rewritten into a derived number. */
function partStrip(c){
  if(!c)return '';
  const related=(c.related||[]).slice();
  return `<div class="part-strip" aria-label="Exact part references" data-part-strip>
  <span class="part-strip-label">Exact part references</span>
  <span class="pn pn-strong">${esc(c.pn)}</span>
  <span class="small">${esc(c.name)} &middot; ${esc(c.tier||'class not stated')} &middot; unit: ${esc(c.unit||'not stated')}</span>
  ${related.length?`<span class="part-strip-related">Related numbers recorded: ${related.map(p=>`<span class="pn">${esc(p)}</span>`).join(' ')}</span>`:''}</div>`;
}

/* The strip on the selected-part review must describe the part being reviewed,
   not the case that happens to be open beside it. Showing case A's part
   reference above a review of part B tells the reader two different things at
   once, and the screened row does not carry a class or a unit, so the strip says
   that rather than inventing one. */
function partRouteSummary(partNumber){
  const rows=C.search(D.candidateScreen||[],partNumber).filter(r=>r.part_number===partNumber);
  return {pn:partNumber,
    name:(rows[0]&&rows[0].description)||'description not held on the screened row',
    tier:'screened candidate row, not a worked case',
    unit:'not held on the screened row',
    related:[]};
}

/* The guard the retired layer ran before paint. A banned label must not reach a
   reader through a retained template string, and a literal typed months ago
   cannot notice that it has become wrong. */
const BANNED_WORDS=[
  {re:/\bMode\s*[AB]\b/i,why:'audience label; say shared/external or internal/private'},
  {re:/\bwallet\b/i,why:'use parts billed or target spend per truck'},
  {re:/\bstreet\b/i,why:'use reference dealer price'},
  {re:/sell-?out/i,why:'say sales to dealer'},
  {re:/\bBook\s*B\b/i,why:'say the price list'},
  {re:/\bclass\s*factor\b/i,why:'work in margins, not factors'}];
function bannedWords(html){
  const findings=[];
  BANNED_WORDS.forEach(b=>{const m=String(html).match(b.re);if(m)findings.push({word:m[0],why:b.why});});
  return findings;
}

/* The framework's own turbo resolution. In this layer the reader was still shown
   "Conflicting recorded list prices" on a case whose conflict the payload had
   already settled, so the screen asked a question the file had answered. The
   resolution is read from the payload and the ambiguity is named as settled. */
function turboResolution(){
  const t=D.turboPriceResolution;
  if(!t||t.resolved_billable_list===undefined||t.resolved_billable_list===null)return null;
  const records=t.records||[],sensitivity=t.sensitivity_range||[];
  return {part_number:t.part_number,
    resolved_billable_list:t.resolved_billable_list,
    resolved_by:t.resolved_by,resolved_on:t.resolved_on,
    sensitivity_range:sensitivity,
    records_examined:records.length,
    usable_records:records.filter(r=>r.usable).length,
    open_statement:t.still_open,
    statement:'The competing list records are resolved. '+eur(t.resolved_billable_list,2)
      +' is the carried list price and is the amount that bills; '
      +eur(sensitivity[0],2)+' is retained as a separate observation. '
      +records.length+' records were examined and only '
      +records.filter(r=>r.usable).length+' is usable as a billed list price.'};
}
function turboFor(c){const t=turboResolution();return t&&c&&c.pn===t.part_number?t:null;}

/* UX-05. One reading of the current metadata, derived from the payload and the
   working scenario. The header, the cost results, the scenario panel, the
   decision summary and the export all paint this block, so none of them keeps
   its own older wording. */
function currentMetadata(c){
  const s=scenario(),t=turboFor(c),pe=c.packEvidence||{};
  const applied=s.cost_eur!==null&&s.cost_eur!==undefined;
  return {payload_version:String((D.meta&&D.meta.version)||'not declared'),
    build_date:(D.meta&&D.meta.buildDate)||'not declared',
    list_price_status:t?'list conflict resolved from the payload'+(t.resolved_on?' on '+t.resolved_on:'')
      :pe.listConflict?'two recorded list amounts are held; neither is a confirmed customer net price'
      :'list snapshots available; current customer net price not held',
    cost_status:applied?(s.cost_basis_id?'parts purchase cost applied on basis '+s.cost_basis_id:'parts purchase cost entered by hand')
      :pe.costRecordPresent?'parts purchase cost held, not applied to this scenario':'no parts purchase cost held',
    cost_basis_id:s.cost_basis_id||null,
    offer_effective_date:s.offer_effective_date||null};
}
function metadataLine(m){return `<p class="small meta-line" data-metadata="${esc(JSON.stringify(m))}">${esc(m.payload_version)} &middot; built ${esc(m.build_date)} &middot; list price: ${esc(m.list_price_status)} &middot; ${esc(m.cost_status)}${m.offer_effective_date?' &middot; offer from '+esc(m.offer_effective_date):''}</p>`;}
/* UX-05. Three different questions, kept apart: is the evidence complete, has
   a figure been technically checked, and has anyone commercially approved the
   price. A technically checked cost does not make the evidence complete, and
   neither of them is an approval. */
function decisionStatus(c){
  const pe=c.packEvidence||{},t=turboFor(c);
  const missing=[];
  if(!pe.costRecordPresent)missing.push('parts purchase cost');
  if(!onwardHeld(c))missing.push('sales to dealer');
  if(!t&&pe.listConflict)missing.push('one confirmed list price');
  missing.push('current customer net price');
  const acceptance=(D.packAudit||{}).acceptedStatus;
  const rec=repo.load(c.id),st=rec&&rec.state;
  return {
    completeness:'Incomplete. Not held: '+missing.join(', ')+'.',
    technical:(pe.costRecordPresent
      ?'The parts purchase cost for '+c.pn+' is a technically checked record on the declared supplier purchase-cost basis, and the results are calculated by the checked engine.'
      :'No technically checked parts purchase cost is held for '+c.pn+'. Revenue results are calculated by the checked engine.')
      +' These are developer checks. '+(acceptance?'Pack acceptance: '+acceptance+'.':'No business or source acceptance is recorded.'),
    commercial:st==='approved'
      ?'A recorded case move puts this case at "approved". Check the move before relying on it.'
      :'Not approved. No commercial approval is recorded for this case, and a saved revision is not an approval.'};
}
function decisionSummary(c){
  const cmp=c.comparisons[state.compare],d=decisionStatus(c);
  return `<div class="panel callout decision-summary" data-decision-summary><div class="eyebrow">Decision summary</div><h3>${esc(c.action||c.name)}</h3>
  <div class="evidence-line"><span>Recorded change</span><b>${signedEUR(cmp.revenueDelta)} in recorded billing &middot; ${esc(cmp.label)}</b></div>
  <div class="evidence-line" data-status="evidence-completeness"><span>Evidence completeness</span><b class="small">${esc(d.completeness)}</b></div>
  <div class="evidence-line" data-status="technical-authority"><span>Technical authority</span><b class="small">${esc(d.technical)}</b></div>
  <div class="evidence-line" data-status="commercial-approval"><span>Commercial approval</span><b class="small">${esc(d.commercial)}</b></div>
  <div class="evidence-line"><span>Next action</span><b class="small">${esc(c.next)}</b></div>
  ${metadataLine(currentMetadata(c))}</div>`;
}

/* UX-02, ported. The retired layer stated on screen that changing the objective
   re-orders the alternatives and moves nothing else. This layer showed two
   panels and let the reader infer it. Both orders are built here from two engine
   rankings on the same scenario inputs, so the claim cannot drift from the
   numbers printed underneath it. */
function objectiveTwin(c){
  const opts={payload:D,pack_size:scenario().pack_size,offer_effective_date:offerDate()};
  const rev=E.rankAlternatives(c,'revenue',opts),gp=E.rankAlternatives(c,'grossProfit',opts);
  const id=x=>x.alternative.alternative_id;
  const revOrder=rev.ranked.map(id),gpOrder=gp.ranked.map(id);
  /* Compare matched alternatives, never matched positions: the two lists are
     sorted by different measures, so index-to-index would compare an alternative
     with a different one and report an assumption difference that does not
     exist. */
  const gpById={};
  gp.ranked.forEach(x=>{gpById[id(x)]=x.result;});
  const sameBaseline=rev.baseline.price===gp.baseline.price&&rev.baseline.quantity===gp.baseline.quantity;
  const sameRows=rev.ranked.every(x=>{
    const y=gpById[id(x)];
    return !!y&&x.result.quantity_after===y.quantity_after&&x.result.revenue_change===y.revenue_change;
  });
  const sameDate=(rev.offer_effective_date||null)===(gp.offer_effective_date||null);
  const orderingOnly=sameBaseline&&sameRows&&sameDate;
  return {ordering_only:orderingOnly,
    orders_differ:revOrder.join(',')!==gpOrder.join(','),
    assumptions:{same_baseline:sameBaseline,same_quantities:sameRows,same_offer_effective_date:sameDate,ordering_only:orderingOnly},
    statement:orderingOnly
      ? 'Ordering only. Both objectives are ranked from the same unchanged offer, the same eligible quantity and the same offer effective date. Changing the objective re-orders the alternatives; it does not move a quantity, a price or a date.'
      : 'Assumptions differ. The two objectives are not ranking from one identical unchanged offer here, so their orders are not comparable without resolving the difference first.'};
}

/* ------------------------------------------------------- retained evidence */
/* UX-06. Sales to dealer is an optional source. When no row carries it the
   review is narrower and says so, instead of drawing an empty chart that reads
   as zero sales to dealers. */
function onwardHeld(c){return (c.series||[]).some(r=>r&&r.onwardQuantity!==null&&r.onwardQuantity!==undefined);}
function onwardMissing(){return unavailableBlock({title:'No sales-to-dealer record is held for this case',
  reason:'The distributor\'s sales to its dealers are not in the evidence for this case. That is a missing source, not zero sales to dealers.',
  required:'monthly sales-to-dealer rows from the distributor for both periods',scope:'sales to dealer'});}
function reviewScopeNote(c){return onwardHeld(c)?'':'<p class="small" data-review-scope="narrower">This review is narrower: it covers what ISZE billed only. Sales to dealer is not held for this case, so no comparison with the dealer flow is made.</p>';}
function stats(c){
 const x=c.comparisons[state.compare],a=x.prior,z=x.current;
 return `<div class="stats">
 <div class="stat"><div class="label">ISZE billing change</div><strong class="${color(x.revenueDelta)}">${signedEUR(x.revenueDelta)}</strong><div class="detail">${eur(a.eur)} &rarr; ${eur(z.eur)}<br>Measured billing; not price-caused loss.</div></div>
 <div class="stat"><div class="label">Observed net unit price</div><strong>${eur(z.price,2)}</strong><div class="detail">${eur(a.price,2)} before &middot; ${pct(x.priceChangePct)}<br>Includes order and commercial-term mix.</div></div>
 <div class="stat"><div class="label">ISZE quantity change</div><strong class="${color(x.quantityChangePct)}">${pct(x.quantityChangePct)}</strong><div class="detail">${num(a.quantity)} &rarr; ${num(z.quantity)} ${esc(c.unit)}s<br>Purchases from ISZE.</div></div>
 ${onwardHeld(c)?`<div class="stat"><div class="label">Sales-to-dealer change</div><strong class="${color(x.onwardChangePct)}">${x.onwardChangePct===null?'Not comparable':pct(x.onwardChangePct)}</strong><div class="detail">${num(a.salesToDealer)} &rarr; ${num(z.salesToDealer)} ${esc(c.unit)}s<br>Separate national wholesale flow.</div></div>`:`<div class="stat" data-source-missing="sales to dealer"><div class="label">Sales-to-dealer change</div><strong>Not held</strong><div class="detail">No sales-to-dealer record for this case.<br>A missing source, not a zero.</div></div>`}</div>`;
}
function chart(c,key,title,line=false){
 const cmp=c.comparisons[state.compare],years=[cmp.prior.year,cmp.current.year],months=cmp.current.months;
 const a=Array.from({length:months},(_,i)=>c.series.find(r=>r.year===years[0]&&r.month===i+1));
 const b=Array.from({length:months},(_,i)=>c.series.find(r=>r.year===years[1]&&r.month===i+1));
 const vals=[...a,...b].map(r=>r?.[key]).filter(v=>v!==null&&v!==undefined);
 const width=500,height=215,left=42,top=17,bottom=36,right=14,plotH=height-top-bottom,plotW=width-left-right;
 let max=Math.max(1,...vals),min=Math.min(0,...vals);max*=1.13;if(min<0)min*=1.13;
 const yy=v=>top+(max-v)/(max-min)*plotH,slot=plotW/months,xx=i=>left+slot*(i+.5),barw=Math.min(16,slot*.31);
 let svg=`<svg class="chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(title)}; ${years.join(' compared with ')}">`;
 for(let i=0;i<=3;i++){const v=min+(max-min)*i/3,y=yy(v);svg+=`<line x1="${left}" x2="${width-right}" y1="${y}" y2="${y}" stroke="#e4ebf0"/><text x="${left-6}" y="${y+4}" text-anchor="end" font-size="10" fill="#6b7c8c">${key==='billingEUR'&&Math.abs(v)>=1000?num(v/1000,1)+'k':num(v,0)}</text>`;}
 const names=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
 [a,b].forEach((series,si)=>{
  const fill=si===0?'#193d58':'#008374';let segment=[];
  function endSeg(){if(segment.length>1)svg+=`<polyline points="${segment.join(' ')}" fill="none" stroke="${fill}" stroke-width="2.5"/>`;segment=[];}
  series.forEach((r,i)=>{const v=r?.[key];if(v===null||v===undefined){endSeg();return;}
   if(line){segment.push(`${xx(i)},${yy(v)}`);svg+=`<circle cx="${xx(i)}" cy="${yy(v)}" r="3.8" fill="${fill}"><title>${names[i]} ${years[si]}: ${eur(v,2)}</title></circle>`;}
   else{const x=xx(i)+(si===0?-barw-1:1),y=yy(v),zero=yy(0);svg+=`<rect x="${x}" y="${Math.min(y,zero)}" width="${barw}" height="${Math.max(1.3,Math.abs(zero-y))}" rx="2" fill="${fill}" ${v===0?'opacity=".24"':''}><title>${names[i]} ${years[si]}: ${num(v)}${v===0?' (no recorded line)':''}</title></rect>`;}
  });endSeg();
 });
 a.forEach((r,i)=>{const vals2=[a[i]?.[key],b[i]?.[key]],description=`${names[i]}: ${years[0]} ${['price','billingEUR'].includes(key)?eur(vals2[0],2):num(vals2[0])}; ${years[1]} ${['price','billingEUR'].includes(key)?eur(vals2[1],2):num(vals2[1])}`;
  svg+=`<g class="month-hit" tabindex="0" role="button" aria-label="${esc(description)}" data-readout="${esc(description)}" data-chart="${key}"><rect class="hit" x="${left+slot*i}" y="${top}" width="${slot}" height="${plotH+27}" fill="transparent"/><text x="${xx(i)}" y="${height-12}" text-anchor="middle" fill="#6b7c8c" font-size="10">${names[i]}</text></g>`;
 });svg+='</svg>';
 const note=key==='price'?'Price = positive billed EUR / positive billed quantity. Gaps mean no observed price, not a zero price.':key==='onwardQuantity'?'National monthly rows only, signed quantities. No dealer attribution or end-customer consumption is inferred.':'Positive ISZE billing; a zero-height bar means no recorded line, not proven zero demand.';
 return `<div class="panel"><div class="chart-title"><h3>${esc(title)}</h3><span class="small">${key==='price'?'EUR per unit':key==='billingEUR'?'Recorded EUR':'Recorded units'}${key.startsWith('billing')?' &middot; <button class="linkbutton" id="toggle-billing-metric">'+(key==='billingEUR'?'Show units':'Show EUR')+'</button>':''}</span></div><div class="legend"><span><i></i>${years[0]}</span><span><i class="new"></i>${years[1]}</span></div>${svg}<div class="chart-note">${note}</div><div class="month-readout" id="readout-${key}">Select a month to inspect its values.</div></div>`;
}
function listSummary(c){return c.packEvidence.listChanges.map(r=>`${eur(r.amount,2)} (${pct(r.changePct)} vs the 2025 snapshot)`).join(' or ');}
function targetBox(c){
 const e=c.packEvidence;
 return `<div class="panel ${e.listConflict?'warn':'callout'} imported-callout"><div class="eyebrow">New evidence loaded &middot; accepted subset</div><h3>${e.listConflict?'Conflicting recorded list prices':'Recorded list: '+listSummary(c)}</h3>${e.listConflict?`<p><b>${listSummary(c)}</b></p>`:''}<p>${esc(c.verdict)}</p><div class="readiness-chips"><span class="badge fact">List history connected</span><span class="badge review">Current customer net unconfirmed</span><span class="badge review">Cost basis dated, not approved</span></div><div class="rowactions"><button class="linkbutton" data-view="position">Read the price history and offers &rarr;</button><button class="linkbutton" data-sources>What passed the source review?</button></div></div>`;
}
function termsTable(c){
 let rows='';
 for(const [label,obj] of [['2024 full year',c.annual['2024']],['2025 full year',c.annual['2025']],['2026 Jan-Jun',c.half['2026']]])for(const r of (obj?obj.orderTypes:[])||[])rows+=`<tr><td>${label}</td><td>${esc(r.type)}</td><td class="n">${num(r.quantity)}</td><td class="n">${eur(r.price,2)}</td></tr>`;
 return `<details><summary>Separate order terms from a price-list change</summary><p>All prices below are measured effective billing averages within the recorded order type. PRD is the source order-type code; its contractual conditions are not reconstructed. A blank 2026 type is not assumed to be SOR.</p><div class="tablewrap" tabindex="0" aria-label="Scrollable table"><table><thead><tr><th>Period</th><th>Recorded type</th><th class="n">Units</th><th class="n">EUR / unit</th></tr></thead><tbody>${rows}</tbody></table></div></details>`;
}
function relatedTable(c){
 const e=c.packEvidence,p=c.parts||{};
 const rows=(e.relationships||[]).map(r=>`<tr><td class="pn">${esc(r.part_number_a)}</td><td class="pn">${esc(r.part_number_b)}</td><td>${esc(r.relationship_type)}</td><td>${esc(r.validation_status)}<br><span class="small">${esc(r.source_document)} &middot; ${esc(r.pointer)}</span></td></tr>`).join('');
 return `<details><summary>Documented Genuine / BVP, replacements and application</summary><p>${esc(c.bvp)}</p>${rows?`<div class="tablewrap" tabindex="0" aria-label="Scrollable table"><table><thead><tr><th>From number</th><th>To number</th><th>Recorded relationship</th><th>What is established</th></tr></thead><tbody>${rows}</tbody></table></div>`:'<p class="small">No non-self relationship for this exact part is included in the exported table. This does not prove that no alternative exists elsewhere.</p>'}<p><b>Part classification:</b> ${esc(p.aim_l1||'')} / ${esc(p.aim_l2||'')} / ${esc(p.aim_l3||'')}.<br><span class="small">${esc(p.aim_release||'')}; ${esc(p.classification_approved||'')}.</span></p><p><b>Part relationships are records, not approval to fit a part to a vehicle.</b></p><p>${esc(c.application)}</p><p class="small">Relationship records and the source description remain distinct from approval to fit a part to a vehicle. No market fleet is split between parts or dealers.</p></details>`;
}
function safeLink(url,label){return /^https?:\/\//i.test(url||'')?`<a class="sourcelink" target="_blank" rel="noopener noreferrer" href="${esc(url)}">${esc(label||'Source page')} &nearr;</a>`:`<span class="small">${esc(url||'No direct product URL in export')}</span>`;}
function snapshotPanel(c){
 const e=c.packEvidence;
 const points=(e.snapshots||[]).map(r=>({label:r.list_version.replace('snapshot ','') ,price:eur(r.amount,2)}));
 points.push({label:'2026 recorded list',price:(e.recordedListCandidates||[]).map(v=>eur(v,2)).join(' / ')});
 return `<div class="panel"><div class="eyebrow">Price levels kept separate</div><h3>List snapshots are not the prices invoiced to this customer.</h3><div class="snapshot-grid">${points.map((p,i)=>`<div class="snapshot ${i===3&&e.listConflict?'snapshot-conflict':''}"><span>${esc(p.label)}</span><strong>${p.price}</strong><small>EUR per supplied price unit; tax excluded</small></div>`).join('')}</div><p><b>${listSummary(c)}.</b> The last column is a source record, not confirmation of the net price available today.</p><p class="small">H1 2026 observed billing average: <b>${eur(c.half['2026'].price,2)}</b> per ${esc(c.unit)}. A dated list movement and a weighted billing movement are not interchangeable. No list snapshot is applied backwards to reprice historic sales.</p><details><summary>Every recorded price source and validity field</summary><div class="tablewrap" tabindex="0" aria-label="Scrollable table"><table><thead><tr><th>Observation</th><th>EUR / price unit</th><th>Recorded validity</th><th>Source and trace</th></tr></thead><tbody>${(e.prices||[]).map(r=>`<tr><td>${esc(r.list_version)}<br><span class="small">${esc(r.observation_type)}</span></td><td class="n">${eur(r.amount,2)}</td><td>${esc(r.valid_from)} &rarr; ${esc(r.valid_to)}</td><td>${esc(r.source_reference)}<br><span class="small">${esc(r.pointer)}</span></td></tr>`).join('')}</tbody></table></div><p class="small">Open-ended and overlapping fields are carried as source values, not interpreted as an authoritative continuous price history. Duplicate sources do not become independent prices.</p></details></div>`;
}
function archiveOfferTable(offers){
 if(!offers.length)return '<p>No priced exact-number competitor records are included in this export. Earlier web evidence is retained separately below.</p>';
 return `<div class="tablewrap" tabindex="0" aria-label="Scrollable table"><table class="offers-table"><thead><tr><th>Seller / manufacturer part</th><th>Advertised amount</th><th>Tax / contents</th><th>Use and provenance</th></tr></thead><tbody>${offers.map(o=>`<tr><td><b>${esc(o.brand||'Not supplied')}</b><br><span class="pn">${esc(o.manufacturer_part_number||'Not supplied')}</span><br>${esc(o.seller)}</td><td class="n">${o.price_original?`${esc(o.currency_original)} ${num(Number(o.price_original),2)}`:'No usable price'}<br><span class="small">${esc(o.observation_date)}</span>${o.currency_original==='GBP'&&o.normalised_price_eur&&o.vat_included_excluded==='VAT included (UK 20%)'?`<br><span class="small">Recorded conversion: EUR ${num(Number(o.normalised_price_eur),2)} ex VAT<br>Historical 1.17 EUR/GBP; not current FX</span>`:''}</td><td>${esc(o.vat_included_excluded)}<br><span class="small">${esc(o.pack_quantity)}; ${esc(o.kit_contents)}<br>Delivery charges: ${esc(o.mandatory_delivery_or_other_charges)}</span></td><td><b>${esc(o.use)}</b><br><span class="small">${esc(o.match_reason)}<br>${esc(o.historical_label)}<br>${esc(o.pointer)}</span><br>${safeLink(o.source_url,'Recorded source')}</td></tr>`).join('')}</tbody></table></div>`;
}
/* ===========================================================================
   MARKET-07 / MARKET-08 on a screen (view developer).

   src/data/comparable.js computes the comparable-price panel and declares its
   own contract; it draws nothing. This block is what a reader sees of it, and it
   recomputes nothing: every figure, every reason code and every explanatory
   sentence below is read from the panel's return value. Where the panel refuses
   to state a figure, the screen states the refusal.

   Three things this view exists to keep apart, because the artifact's earlier
   revisions ran them together:

     1. A date. Three list snapshots, four archive offers, an earlier web pass
        and ten competitor observations sat on one screen, so a retired figure
        read as a current price range.
     2. A commercial price level. An advertised retail price by another seller is
        not an ISZE net distributor price, and it is not proof our net terms are
        too high.
     3. Two kinds of evidence. What we bought and sold ourselves says nothing
        about where our price sits against another seller. The panel returns them
        as two separately named outputs with a different declared kind each, and
        they are drawn as two panels that say so.

   What a reader most often gets here, on the authorised payload, is the
   unavailable state: NOTHING REACHES AN AGREED BASIS. That is the honest answer
   for this file, not a broken view, and it renders as an amber state naming the
   reason on every row and the smallest thing that would change it.
   =========================================================================== */

/* What each declared price level is, in the words a reader needs before seeing
   any figure on it. The commercial rule the panel enforces is unreadable without
   this, so the table is on the screen and not in a footnote. */
const MARKET_LEVEL_TRAITS={
  isze_net_distributor:'our own terms, a price that actually changed hands',
  isze_net_list:'our own terms, a carried list figure rather than a transaction',
  distributor_dealer_transaction:'a price that changed hands between a distributor and a dealer',
  public_advertised_retail:'an advertised price by a different seller; the pack, tax and delivery basis may not be stated',
  oem_peer_retail:'a reference dealer price published by a peer manufacturer, used as a comparison convention only',
  list:'our own terms, a carried list figure',
  observed_billing_average:'our own recorded billing average',
  competitor_advertised:'an advertised price by another seller',
  reference_dealer:'a derived reference figure, not a transaction',
  supplier_cost:'a purchase cost, which is not a selling price at any level'};
function marketLevelNote(level){
  if(!level)return 'no price level is declared on this row, so it may not be compared with any other figure';
  return MARKET_LEVEL_TRAITS[level]||'the meaning of this price level is not declared here, so nothing is stated about it';
}

/* Every derived figure on this screen carries its own explanation on hover, in
   the house colours. The frozen shell stylesheet declares no rule for it, so the
   rule travels with the view rather than waiting for a stylesheet nobody
   assembles. Nothing here is a title attribute: a title is not a tooltip a
   reviewer can read beside the number. */
const MARKET_TIP_STYLE=`<style>.mk-tip{position:relative;border-bottom:1px dotted #6b7c8c;cursor:help}`
 +'.mk-tip:hover::after{content:attr(data-tip);position:absolute;left:0;bottom:135%;z-index:60;width:330px;'
 +'background:#15233c;color:#f7f4ee;border-left:4px solid #c0552d;border-radius:6px;padding:9px 11px;'
 +'font-size:11px;line-height:1.45;font-weight:400;text-align:left;white-space:normal;'
 +'box-shadow:0 6px 18px rgba(0,0,0,.28)}</style>';
const tip=(v,t)=>`<span class="mk-tip" data-tip="${esc(t)}">${v}</span>`;

/* The declarations a reader makes about one held offer, and the two this screen
   states by default.

   A declaration is a fact about an observation that the record has to carry: which
   commercial price level it is, what unit it counts in, whether its quote covers
   a piece or a pack, what its product match rests on, and how its money is to be
   adjusted. `comparable.js` refuses to invent any of them, and this screen will
   not invent them either. So the record's own `observation_declarations` block is
   forwarded key by key, and where the record declares nothing the declaration
   stays missing and the observation is reported as unresolved rather than
   admitted on a guess.

   The two defaults below are readings of the file, stated on the screen and
   overridable by the record:

     the price level   the offers this component holds are public indexed
                       listings by other sellers, which is an advertised retail
                       observation and not our own net terms;
     the match basis   the file's own match notes describe seller cross-references
                       and similar listings, not approved equivalence.

   Neither default can make an observation comparable on its own. Both are printed
   under "Admissibility rule applied" so a reader can disagree with them. */
const MARKET_OFFER_DECLARATION_KEYS=['level','unit','match_basis','role','amount_scope','pack',
  'equivalence','vat_rate_unit','delivery_included','delivery_cost_eur','fx_rates'];
function marketDeclarations(c,offer){
  const declared=(offer&&offer.observation_declarations)||{};
  const out={unit:c.unit,level:'public_advertised_retail',match_basis:'cross_reference'};
  MARKET_OFFER_DECLARATION_KEYS.forEach(k=>{
    if(Object.prototype.hasOwnProperty.call(declared,k)&&declared[k]!==null&&declared[k]!==undefined){
      out[k]=declared[k];
    }
  });
  return out;
}
function marketPanel(c){
  const offers=(c.offers||[]).map(id=>(D.offers||{})[id]).filter(Boolean);
  const observations=offers.map(o=>M.observationFromOffer(o,marketDeclarations(c,o)));
  const result=M.panel({case_id:c.id,part_number:c.pn,market:c.market,unit:c.unit},observations,{
    basis_level:'public_advertised_retail',basis_unit:c.unit,
    basis_named_by:'the admissibility rule stated on this screen',
    as_of:(D.meta&&D.meta.buildDate)||null,
    own_movement:M.movementFromComparison((c.comparisons||{}).half)});
  return {result,offers,observations};
}

/* The kind of evidence one observation is, in the two words a reader needs
   before the figures. A dated advertised price and a recorded transaction are
   different things; the table says which one each row is rather than leaving it
   to the price level's name. */
function marketEvidenceKind(r){
  const info=M.levelInfo(r&&r.level);
  if(info.is_our_terms)return {short:'our own recorded terms',
    what:'our own price on this part, not an observation by another seller'};
  if(info.is_actual_transaction)return {short:'a recorded transaction',
    what:'a price that actually changed hands between a distributor and a dealer'};
  if(info.is_advertised_observation)return {short:'a dated advertised price',
    what:'a price another seller published on the date shown; it is not a quotation and it does not state what that seller paid'};
  if(info.is_derived_reference)return {short:'a derived reference figure',
    what:'a comparison convention, not a transaction and not revenue that was earned'};
  if(info.restricted)return {short:'a purchase cost',
    what:'what a buyer paid; it is not a selling price at any level'};
  return {short:'kind not declared',
    what:'the kind of evidence on this row is not declared here, so nothing is read from it'};
}

/* Every reason a row was left out, grouped and counted. A code is never printed
   alone: it is looked up in the module's own declared list, and a code that list
   does not know is reported as unknown rather than as a reviewed reason. */
function marketReasonGroups(rows){
  const order=[],byCode={};
  (rows||[]).forEach(r=>{
    (r.reason_codes||[]).forEach(code=>{
      if(!byCode[code]){
        const explained=M.explainExclusion(code);
        byCode[code]={code,kind:explained.known?explained.kind:'unknown',known:explained.known,rows:[]};
        order.push(code);
      }
      byCode[code].rows.push(r);
    });
  });
  return order.map(code=>byCode[code]).sort((a,b)=>b.rows.length-a.rows.length);
}

/* One observation exactly as the panel returned it: the quote, every recorded
   adjustment step, the match status, the date, the declared kind of evidence it
   is, and the reason it stands where it does. Nothing here is recalculated and
   no figure is derived in the view.

   The adjusted figure and the rate handed to the shared rule are the two derived
   numbers in the row, so each carries its own explanation on hover. */
function marketOfferTable(rows,kindLabel){
  if(!rows||!rows.length)return '';
  return `<div class="tablewrap" tabindex="0" aria-label="Scrollable table"><table><thead><tr><th>Observation</th><th>Price level and seller</th><th class="n">Quoted</th><th>Kind of evidence</th><th>Adjustment, step by step</th><th>Match</th><th>Date and recorded basis</th><th>Where this row stands</th></tr></thead><tbody>
  ${rows.map(r=>{
    const a=r.adjustment||{};
    const steps=(a.steps||[]).length
      ?a.steps.map(s=>`<div class="small">${esc(s.step||'adjustment')}: ${num(s.from,2)} &rarr; ${num(s.to,2)} <span class="small">(${esc(s.rule||'')})</span></div>`).join('')
      :'<div class="small">No adjustment step is recorded for this row.</div>';
    const vatUse=a.vat_rate_used
      ?`<div class="small">Rate handed to the shared rule: ${tip('<b>'+num(a.vat_rate_used.passed_to_the_rule,2)+'</b>','The rate as the shared adjustment rule receives it, which is a percentage. The row declares its own unit as '+(a.vat_rate_used.declared_by_the_row_as||'not stated')+', and the file stores the number '+num(a.vat_rate_used.original_value,3)+'. A rate whose unit is not declared is left unresolved in the comparison module rather than guessed, because 0.20 as a fraction and 20 as a percentage differ by a factor of one hundred.')} declared by the row as ${esc(a.vat_rate_used.declared_by_the_row_as||'not stated')} (the file stores ${num(a.vat_rate_used.original_value,3)}).</div>`
      :'';
    const unresolved=(a.unresolved||[]).length
      ?`<div class="small danger-line">Not adjusted: ${a.unresolved.map(u=>esc(u)).join(' ')}</div>`:'';
    const codes=(r.reason_codes||[]).map(code=>`<span class="badge ${M.explainExclusion(code).kind==='unresolved'?'assumption':'review'}">${esc(code)}</span>`).join(' ');
    const kind=marketEvidenceKind(r);
    return `<tr><td class="pn">${esc(r.observation_id||'no identifier')}<div class="small">${esc(r.role||'role not stated')}</div></td>
    <td>${esc(r.level_label||'level not declared')}<div class="small">${esc(r.seller||'seller not stated')} &middot; ${esc(r.market||'market not stated')}</div></td>
    <td class="n">${r.quoted&&r.quoted.amount!==null?esc(String(r.quoted.currency||''))+' '+num(r.quoted.amount,2):'<span class="danger-line">no amount</span>'}<div class="small">${esc((r.quoted&&r.quoted.tax)||'tax basis not stated')}<br>${r.quoted&&r.quoted.amount_scope?esc(r.quoted.amount_scope):'piece or pack not stated'}</div></td>
    <td class="small"><b>${esc(kind.short)}</b><div class="small">${esc(kind.what)}</div></td>
    <td>${steps}${vatUse}${unresolved}<div class="small">${a.ok?tip('Adjusted figure '+num(a.value,2),'The quoted amount after every recorded nominal adjustment &mdash; tax removed at the stated rate, currency converted at the stated dated rate, and stated delivery added. It is derived only from the retained original and the recorded inputs on this row, and it is not a comparison with our own price.'):'<span class="danger-line">no adjusted figure is stated</span>'}</div></td>
    <td class="small">${esc((r.match&&r.match.status)||'not stated')} on ${esc((r.match&&r.match.basis)||'a basis not stated')}</td>
    <td class="small">${esc(r.retrieved||'no date recorded')}${r.age_days===null||r.age_days===undefined?'':'<br>'+num(r.age_days,0)+' day(s) before this build'}<br>${esc(kindLabel)}</td>
    <td class="small">${r.selected===false?'Not selected: ':''}${esc(r.selection||'')}${codes?('<div style="margin-top:6px">'+codes+'</div>'):''}${r.reason?`<div class="small">${esc(r.reason)}</div>`:''}</td></tr>`;}).join('')}
  </tbody></table></div>`;
}

/* What this part was billed and what the row itself says is unresolved. The
   admissibility columns are shown, not hidden: a row left out by an evidence
   ceiling or a screen is still a row, and hiding it is how a screener gets read
   as an approved decision. */
function marketRecordedRows(c){
  const rows=(D.candidateScreen||[]).filter(r=>r.part_number===c.pn);
  if(!rows.length)return unavailableBlock({
    title:'No screened row carries this part number',
    reason:'The candidate screen holds no row for this exact reference, so the billed quantity, billing and unit price behind its own screening rules are not shown here. A missing row is not a billed quantity of zero.',
    required:'a screened row for '+c.pn+', which is how the billing below is verified',
    scope:'candidate screen, this exact reference'});
  const shown=rows.slice(0,50);
  const withoutBilling=rows.filter(r=>!Number.isFinite(Number(r.observed_billing_eur))).length;
  return `<div class="tablewrap" tabindex="0" aria-label="Scrollable table"><table><thead><tr><th>Account</th><th class="n">Billed qty</th><th class="n">Billed</th><th class="n">Unit price</th><th class="n">List</th><th class="n">Parts purchase cost</th><th>Selection reason</th><th>Unresolved on the row</th></tr></thead><tbody>
  ${shown.map(r=>`<tr><td>${esc(r.distributor)}</td><td class="n">${num(r.billed_qty,0)}</td><td class="n">${eur(r.observed_billing_eur)}</td><td class="n">${r.observed_unit_price===null?'-':eur(r.observed_unit_price,2)}</td><td class="n">${r.list_eur===null?'-':eur(r.list_eur,2)}</td><td class="n">${r.verified_cost_eur_oct26===null?'<span class="danger-line">not held</span>':eur(r.verified_cost_eur_oct26,4)}</td><td class="small">${esc(r.selection_reasons)}</td><td class="small">${esc(r.unresolved_inputs||'-')}</td></tr>`).join('')}
  </tbody></table></div>
  <p class="small">${num(rows.length,0)} screened row(s) carry this exact reference; ${num(shown.length,0)} shown.${withoutBilling?' '+num(withoutBilling,0)+' of them carry no billing value and are excluded from any total rather than counted as zero.':''} A row is a customer-part record, not a part: the same reference can appear on several. These counts and the unresolved notes are copied from the screen that owns that rule; they are not re-derived here.</p>`;
}

/* The unavailable state. An empty comparable set on this payload is the correct
   output, so this names what is empty, what the panel said about each row, and
   what evidence would fill it. A blank panel, a zero and a section that quietly
   vanishes are all FAIL here. */
function marketUnavailable(c,panelResult,groups,counts){
  const request=M.missingEvidenceRequest(panelResult,{case_id:c.id,part_number:c.pn,market:c.market});
  const asked=request&&request.ok?request:null;
  const reasonList=groups.length
    ?groups.map(g=>`<div class="evidence-line"><span>${esc(g.code)} <span class="small">(${esc(g.kind)})</span></span><b>${tip(num(g.rows.length,0)+' of '+num(counts.observations,0)+' observation(s)','How many of the observations read for this case carry this reason. One observation can carry several reasons at once, so these numbers do not add up to the number of rows: each row is counted once per reason it actually carries.')}</b></div>`).join('')
    :'<div class="small">No observation was supplied for this case, so there is no reason code to list.</div>';
  const decl=(D.meta&&D.meta.marketComparisonDeclarations)||{};
  return unavailableBlock({
    title:panelResult.observations_in?'Nothing reaches the agreed comparison basis':'No competitor observation is held for this case',
    reason:(panelResult.statement||'')+' '+(counts.observations
      ?counts.observations+' observation(s) were read and '+num(counts.excluded,0)+' of them were left out, each with a reason recorded below. The comparable set is empty because of what the rows and the file state, not because this view failed.'
      :'The panel was given no observation at all, so it states no comparison. That is not a price of zero and it is not a statement that no competing offer exists.'),
    required:asked?asked.smallest_missing_detail:'an observation that declares a price level, a unit, a tax basis and a product match basis',
    scope:counts.observations?('every competitor observation this case holds ('+num(counts.all,0)+' in the file for it)'):
      (decl.ceiling_never_price_action?'the competitor observations on this case':'the competitor observation set for this case')
  })+`<div class="panel" style="margin-top:12px"><div class="eyebrow">Why each observation was left out</div>
  <h3>Named reasons, counted on this case</h3>
  ${reasonList}
  <p class="small">A reason code is one of ${num(Object.keys(M.EXCLUSION_CODES).length,0)} this comparison module declares. It is looked up and never printed alone, and a code the module does not know is reported as unknown rather than as a reviewed reason. Every row it applies to is in the adjustment table below, with its own words and its own date.</p>
  ${asked?`<div class="panel callout" style="margin-top:12px"><div class="eyebrow">Draft only &middot; nothing is sent from here</div>
    <h3>The smallest thing missing: ${esc(String(asked.topic).replace(/_/g,' '))}</h3>
    <p class="small">${esc(asked.smallest_missing_detail)}</p>
    <div class="evidence-line"><span>What it is used for</span><b class="small">${esc(asked.use)}</b></div>
    <div class="evidence-line"><span>Who is asked</span><b class="small">${esc(asked.audience)}</b></div>
    <div class="evidence-line"><span>What comes back</span><b class="small">${esc(asked.response_offered)}</b></div>
    <div class="evidence-line"><span>Observations affected</span><b>${num(asked.observations_affected,0)}</b></div>
    <p class="small">This request does not ask for ${esc(asked.does_not_ask_for.join(', '))}. ${asked.other_gaps_not_asked_for.length?num(asked.other_gaps_not_asked_for.length,0)+' further gap(s) are recorded and deliberately not asked for in this request. ':''}It is composed as a draft; nothing here sends it, and the case keeps its own state.</p></div>`
   :`<p class="small">Nothing this panel can ask for is missing: every observation is either in the comparable set or was left out for a reason it cannot resolve by asking anyone.</p>`}</div>`;
}

function marketView(c){
 const built=marketPanel(c);
 const p=built.result;
 const observations=p.observations_in;
 const excluded=(p.ineligible_offers||[]).length;
 const eligible=(p.eligible_offers||[]).length;
 const groups=marketReasonGroups(p.ineligible_offers||[]);
 const counts={all:built.offers.length,observations,excluded,eligible};
 const levels=[...new Set((p.candidate_bases&&p.candidate_bases.candidates||[]).map(b=>b.level))];
 const movement=p.purchasing_movement||{};
 const positioning=p.price_positioning||{};
 const decl=(D.meta&&D.meta.marketComparisonDeclarations)||null;
 const retained=(p.raw_records_retained||0)===observations;
 return MARKET_TIP_STYLE+`<div class="inputsnote"><b>Comparable-price panel.</b> ${num(observations,0)} dated observation(s) are read for this case on a named commercial price level and a named unit. Nothing is summarised unless an approved aggregation rule says so, and the cheapest observation is not treated as the right one.</div>

 <div class="panel warn"><span class="badge review">Advertised retail is not our net terms</span>
 <p style="margin-top:12px">${esc(decl?decl.levels_kept_apart:'ISZE net distributor price, the reference dealer price, distributor and dealer transaction prices, and public advertised retail, are separate commercial levels and are kept apart.')}</p>
 <p class="small">${esc(decl?decl.advertised_retail:'An advertised retail price is a dated observation by another seller. It is shown beside our own terms and is never presented as proof that our own net terms are too high, and it is never put into one figure with our own price.')} <b>${esc(decl?decl.price_action:'No price action is certified from this view.')}</b></p></div>

 <div class="grid2">
  <div class="panel"><span class="eyebrow">The comparison being built</span><h3>${esc((p.selected_basis&&p.selected_basis.level_label)||'No comparison basis is named')}</h3>
   <div class="evidence-line"><span>Base price level</span><b>${esc(p.selected_basis&&p.selected_basis.level_label||'not named')}</b></div>
   <div class="evidence-line"><span>Base unit</span><b>${esc(p.selected_basis&&p.selected_basis.unit||'not named')}</b></div>
   <div class="evidence-line"><span>Named by</span><b class="small">${esc(p.selected_basis&&p.selected_basis.named_by||'not stated')}</b></div>
   <div class="evidence-line"><span>Admissibility rule applied</span><b>${esc(decl&&decl.basis_admissibility||'as declared by the comparison module')}</b></div>
   <p class="small">${esc(p.selected_basis?p.selected_basis.statement:'No two observations have been put beside each other and no index is stated, because no basis is named.')} ${esc(decl&&decl.view_honesty||'')}</p></div>
  <div class="panel"><span class="eyebrow">What the panel counted</span><h3>${num(counts.all,0)} price offer(s) in the file; ${num(observations,0)} read by the panel; ${num(eligible,0)} comparable</h3>
   <div class="evidence-line"><span>Price offers held for this case</span><b>${tip(num(counts.all,0),'The number of entry keys in the offers block that this case names, whether or not each one carries a usable price. An entry with a null price is held as a record and is not a price of zero.')}</b></div>
   <div class="evidence-line"><span>Read by the panel</span><b>${tip(num(observations,0),'The offers that reached the comparison module as observations. An entry with no identifier, or with no price at all, is not silently dropped: it is counted separately below and on the case record.')}</b></div>
   <div class="evidence-line"><span>Left out, with a named reason</span><b>${tip(num(excluded,0),'Observations the module refused on the named basis. Every one of them carries at least one reason code, all of them are listed below, and none of them is discarded: each keeps its own record and its own date on this screen.')}</b></div>
   <div class="evidence-line"><span>Every row the panel read was retained</span><b>${tip(retained?'yes':'no &mdash; a row was not retained','Checked by the module itself: it serialises the caller\'s array before it works and compares it afterwards, so this is its own verdict on whether it modified the input, not a figure this screen calculated.')}</b></div>
   <div class="evidence-line"><span>Offer(s) that reached no panel row</span><b>${num(counts.all-observations,0)}${counts.all-observations?' <span class="small">(no identifier or no price; never counted as zero)</span>':''}</b></div>
   <p class="small">${num(p.raw_records_retained||0,0)} of ${num(observations,0)} observation(s) came back with their raw record intact. ${esc(p.all_exclusion_codes_named?'Every reason code on this case resolves in the declared list.':'A reason code on this case does not resolve in the declared list, so it is reported as unknown.')} A missing value is never counted as a zero, and a row is never dropped quietly.</p></div>
 </div>

 ${eligible?`<div class="panel good"><span class="eyebrow">Comparable observations</span><h3>${num(eligible,0)} observation(s) reached the named basis</h3>
  <p class="small">${esc(p.eligible_offers[0].selection)}</p>
  ${marketOfferTable(p.eligible_offers,'comparable on the named basis')}
  <p class="small">${esc(p.aggregation?p.aggregation.statement:'No aggregation rule is declared, so no summary figure is stated.')}</p></div>`
  :marketUnavailable(c,p,groups,counts)}

 <div class="panel"><h3>Every price level present, and the base level each one is refused against</h3>
  <p class="small">${esc((p.candidate_bases&&p.candidate_bases.statement)||'')} A comparison has to name a like-for-like level or a supported bridge. A level that is not on the basis is shown and is not put into one figure with it.</p>
  <div class="tablewrap" tabindex="0" aria-label="Scrollable table"><table><thead><tr><th>Price level</th><th>What it is, and what may not be read from it</th><th>Declared</th></tr></thead><tbody>
  ${(levels.length?levels:['']).map(l=>{
    const info=M.levelInfo(l);
    return `<tr><td><b>${esc(info.label)}</b><div class="small">${esc(info.what_it_is||'the meaning of this level is not declared')}</div></td>
    <td class="small">${esc(marketLevelNote(l))}</td>
    <td class="small">${info.named?'declared':'<span class="danger-line">not declared</span>'}</td></tr>`;}).join('')}
  </tbody></table></div>
  <p class="small">${esc(decl&&decl.basis_admissibility||'')}${decl&&decl.bridge?' '+esc(decl.bridge):''}</p></div>

 <div class="panel"><h3>Currency, tax and delivery, adjustment by adjustment</h3>
  <p class="small">Each observation below carries the quote exactly as the file records it and every step recorded between that quote and a comparable figure. A tax rate whose unit the file does not declare is left unresolved rather than guessed, because a declared 0.20 fraction and a declared 20 percent rate are the same digits and a hundred-fold different amount.</p>
  <p class="small">${esc(decl&&decl.vat_unit_defect||'')}</p>
  ${marketOfferTable(p.ineligible_offers||[],'not comparable on the named basis')}
  <p class="small">An adjusted figure appears only where every step could be completed from stated inputs. The original quote is kept beside it and is never overwritten.</p></div>

 <div class="grid2">
  <div class="panel"><span class="eyebrow">Evidence kind one &middot; our own records</span><h3>What we bought and sold on this part</h3>
   <div class="evidence-line"><span>Declared evidence kind</span><b class="small">${esc(movement.evidence_kind||'')}</b></div>
   ${movement.available?`<div class="tablewrap" tabindex="0" aria-label="Scrollable table"><table><thead><tr><th>Recorded period</th><th class="n">Quantity</th><th class="n">Realised unit price</th></tr></thead><tbody>
   ${(movement.periods||[]).map(x=>`<tr><td>${esc(x.label||'not stated')}</td><td class="n">${num(x.quantity,0)}</td><td class="n">${x.unit_price===null?'<span class="small">not stated</span>':tip(eur(x.unit_price,2),'Recorded billing divided by recorded quantity for that period and that part, copied from the movement the case already carries. It is a realised average on our own terms, not a list price and not a price observed from another seller.')}</td></tr>`).join('')}
   </tbody></table></div>`
   :unavailableBlock({title:'No recorded movement of our own volumes and realised prices for this case',
     reason:'The case does not carry a recorded prior-and-later movement on this part, so what we bought and sold is not stated. Its absence is not a zero and it says nothing about another seller.',
     required:'the case comparison the movement would be read from, or the recorded billing periods for this exact part',
     scope:'our own records, this part'})}
   <p class="small">${esc(movement.statement||'')}</p>
   <p class="small"><b>Not proof of:</b> ${esc((movement.must_not_be_read_as||[]).join('; '))}. This panel is about us. On its own it positions nothing.</p></div>
  <div class="panel ${positioning.available?'':'warn'}"><span class="eyebrow">Evidence kind two &middot; other sellers</span><h3>Where our price sits against another seller</h3>
   <div class="evidence-line"><span>Declared evidence kind</span><b class="small">${esc(positioning.evidence_kind||'')}</b></div>
   <div class="evidence-line"><span>Comparable offer(s) by other sellers</span><b>${num(positioning.comparable_offers_by_other_sellers||0,0)}</b></div>
   <div class="evidence-line"><span>Index stated</span><b>${positioning.index_stated?'stated':'<span class="danger-line">not stated</span>'}</b></div>
   <div class="evidence-line"><span>Basis the index would be stated on</span><b class="small">${esc(positioning.basis?positioning.basis.level_label+' in '+positioning.basis.unit:'no basis named')}</b></div>
   <p class="small">${esc(positioning.statement||'')}</p>
   <p class="small"><b>Not proof of:</b> ${esc((positioning.must_not_be_read_as||[]).join('; '))}. This panel is about somebody else's published price. It never states what we paid or earned.</p></div>
 </div>
 <div class="panel"><div class="eyebrow">These two panels are not interchangeable, and neither is derived from the other</div>
  <p class="small">The left panel is our own recorded movement: what we bought and sold, from our own billing. The right panel is a dated price published by another seller. The comparison module returns them as two differently named outputs with a different declared kind of evidence each, so neither can be read as proof of the other. Purchasing movement is not proof of where our price sits against another seller. A price position is not proof of what we paid or what we earned, and it is not an approved price action.</p>
  <p class="small">Nothing above is combined into one number. No index is computed from our own terms alone, and the price position is refused unless at least one comparable observation is somebody else's.</p></div>

 <div class="panel"><h3>Saved comparisons, kept as they were saved</h3>
  ${(p.saved_comparisons||[]).length?p.saved_comparisons.map(s=>`<div class="source-row"><b>${esc(s.comparison_id||'saved comparison')}</b><p class="small">Saved ${esc(s.saved_at||'with no recorded date')} on ${esc(s.basis||'a basis not stated')} at ${s.value===null?'no stated figure':eur(s.value,2)}. Rewritten by a newer price: <b>${s.rewritten?'yes':'no'}</b>.</p><p class="small">${esc(s.statement)}${s.superseded_by_observation_ids.length?' Superseding observations: '+esc(s.superseded_by_observation_ids.join(', '))+'.':''}</p></div>`).join(''):'<p class="small">No saved comparison is recorded for this case.</p>'}
  <p class="small">Nothing on this screen rewrites one. A newer observation does not silently replace a figure that was saved from an earlier one, and no summary is invented to stand in for either. A saved figure stands as the figure that was saved, with the newer price shown beside it.</p></div>

 <div class="panel"><h3>Other recorded observations for this part, under their own clock</h3>
  <p class="small">Dates, recorded validity, provenance and every conflicting cached value on those screens are left exactly as they were recorded. Nothing below is a current customer quotation, and the earlier pass was not refreshed for this revision.</p>
  <details><summary>Price levels and dated snapshots recorded for this case, as recorded</summary>${snapshotPanel(c)}</details>
  <details><summary>Dated advertised records in the archive (${num(((c.packEvidence||{}).offers||[]).filter(o=>o.independent_offer).length,0)} independent record(s))</summary><p class="small">These records carry their own tax, contents and delivery basis as recorded. They are not adjusted onto a common basis on this screen and none of them is a quotation.</p>${archiveOfferTable(((c.packEvidence||{}).offers||[]).filter(o=>o.independent_offer))}</details>
  <details><summary>Earlier web pass, kept separate</summary><p class="small">Retrieved for the earlier version and not refreshed in this revision. A missing record in the archive above does not erase these.</p>${(c.offers||[]).map(id=>(D.offers||{})[id]).filter(Boolean).map(o=>`<div class="source-row"><b>${esc(o.seller)} &middot; ${esc(o.part)} &middot; ${esc(o.market)}</b><p>${o.price===null?'Reference only':`${esc(o.currency)} ${num(o.price,2)}`} &middot; VAT ${esc(o.tax)}.<br>${esc(o.match)} ${esc(o.note)}</p><p class="small">${esc(o.freshness)} ${esc(o.verification)}</p>${safeLink(o.url,'Recorded source')}</div>`).join('')}</details>
  <details><summary>What this part was billed, and what each row says is unresolved</summary>${marketRecordedRows(c)}</details></div>

 <div class="panel warn"><h3>What this view does not say</h3>
  <p class="small">No price optimum, no elasticity, no acceptable profit sacrifice and no minimum margin are stated here, and none is computed. ${esc(decl&&decl.ceiling_never_price_action||'')} A view that cannot make a like-for-like comparison says so; it does not fill the gap with a number.</p>
  <div class="evidence-line"><span>Price action certified by this view</span><b>${p.price_action_certified?'<span class="danger-line">certified</span>':'not certified'}</b></div>
  <div class="evidence-line"><span>Aggregation rule</span><b class="small">${esc(p.aggregation?p.aggregation.statement:'no rule declared')}</b></div>
  <div class="evidence-line"><span>Scenario link from this comparison</span><b class="small">${esc(p.scenario_link&&p.scenario_link.statement||'')}</b></div></div>

 <div class="panel"><h3>Where these records come from, and what may leave this file</h3>
  <p class="small">The ${num(counts.all,0)} price offer(s) on this screen are copied field by field out of the authorised payload named in the source panel, with the dates and the conversion basis the payload itself records. No live price, no live exchange rate and no supplier cost is read. No address, no clickable page and no seller contact is printed. The screen carries no customer name beyond the account that was billed, no negotiation history, and no raw invoice line.</p>
  <div class="rowactions"><button class="linkbutton" data-sources>Source and calculation basis</button><button class="linkbutton" data-sources>What passed the source review?</button></div></div>

 ${relatedTable(c)}`;
}

function decision(c){
 const cmp=c.comparisons[state.compare];
 return `<div class="compare-row"><div><span class="eyebrow">Measured record</span><div class="small">${sourceButton()} &middot; no forecast or lost-sales attribution</div></div><select id="comparison" aria-label="Comparison period"><option value="half" ${state.compare==='half'?'selected':''}>January-June 2026 vs 2025</option><option value="annual" ${state.compare==='annual'?'selected':''}>Calendar 2025 vs 2024</option></select></div>
 ${decisionSummary(c)}${reviewScopeNote(c)}${stats(c)}${targetBox(c)}
 <div class="grid2">${chart(c,state.billingMetric,state.billingMetric==='billingEUR'?'What ISZE billed':'What ISZE supplied')}${onwardHeld(c)?chart(c,'onwardQuantity','What the distributor supplied to dealers'):onwardMissing()}</div>
 <div class="grid2"><div class="panel"><span class="badge fact">Evidence supporting review</span><p style="margin-top:12px">${esc(c.reason)}</p></div><div class="panel warn"><span class="badge review">Evidence against a simple price story</span><p style="margin-top:12px">${esc(c.counter)}</p></div></div>
 <div class="grid2">${chart(c,'price','Observed ISZE unit price',true)}<div class="panel"><div class="eyebrow">Reconcile the euro change</div><h3>${signedEUR(cmp.revenueDelta)} in recorded billing</h3><div class="evidence-line"><span>Quantity effect, at prior price</span><b class="${color(cmp.volumeEffect)}">${signedEUR(cmp.volumeEffect)}</b></div><div class="evidence-line"><span>Effective price / terms effect</span><b class="${color(cmp.effectivePriceEffect)}">${signedEUR(cmp.effectivePriceEffect)}</b></div><div class="ruleline small">Exact identity: (new quantity &minus; old quantity) &times; old price + new quantity &times; (new price &minus; old price). The second term includes mix of order conditions. It is not causal price elasticity or a measured price-list effect.</div><div class="scopebox"><b>${num(c.fleet)} ${c.market==='ITUK'?'trucks':'vehicles'} &middot; 2025 market reference</b><br>${esc(c.application)} No part-level demand gap or dealer rate is computed.</div></div></div>
 ${termsTable(c)}${relatedTable(c)}<div class="panel callout"><h3>The next commercial action</h3><p>${esc(c.next)}</p><div class="rowactions"><button class="button primary" data-view="economics">Test price and gross profit</button><button class="button" data-view="action">Prepare the internal review</button></div></div>`;
}
/* Price position.

   This view used to be where every dated record landed at once: three list
   snapshots, the offer archive, an earlier web pass and a readiness list side by
   side, with nothing saying which clock or which commercial price level each one
   stood on. The comparable-price panel now computes what a reader is allowed to
   place beside our own terms, and this view draws that panel and keeps the
   remaining dated evidence in sections that state their own clock.

   The archive and the earlier web pass are deliberately NOT adjusted onto the
   panel's basis here. Doing that by hand in a view is how two commercial price
   levels got mixed before; the shared rule that would do it properly belongs to
   src/data/evidence.js, and a view that guessed it would be a second definition
   of the same thing. */
function position(c){
 const e=c.packEvidence||{};
 const leads=(e.offers||[]).filter(o=>o.independent_offer),other=(e.offers||[]).filter(o=>!o.independent_offer);
 const sellers=[...new Set(leads.map(o=>o.seller))];
 const prior=(c.offers||[]).map(id=>D.offers[id]).filter(Boolean);
  const turboHere=turboFor(c);
  const leadsBlock=leads.length
    ?`<div class="panel"><div class="compare-row"><div><div class="eyebrow">Archive &middot; exact part ${c.pn}</div><h3>${leads.length} advertised records from ${sellers.length} sellers</h3></div><span class="badge review">No approved comparable quotation</span></div><p class="small">These are dated advertised observations, not current customer quotations. An accepted seller cross-reference is not approval of fitment, kit contents, a delivered price or a tax-normalised comparison with ISZE. No fresh web validation was performed for this revision.</p>${archiveOfferTable(leads)}${other.length?`<details><summary>${other.length} unresolved, rejected or derived records kept out of the price decision</summary>${archiveOfferTable(other)}</details>`:''}</div>`
    :`${unavailableBlock({title:'No priced exact-number competitor record is held',reason:'No dated advertised record for this exact part number is in the held evidence. That is a gap in the file, not a statement that no competing offer exists.',required:'a dated quotation naming the part number, its contents, its tax basis and its delivery charge',scope:'held competitor observations'})}${other.length?`<details><summary>${other.length} unresolved, rejected or derived records kept out of the price decision</summary>${archiveOfferTable(other)}</details>`:''}`;
  return `${marketView(c)}
 <div class="panel"><div class="eyebrow">Other recorded evidence, each under its own clock</div><h3>List snapshots, the archive and the earlier web pass</h3>
  <p class="small">Each block below is kept under the clock and the commercial price level its own source recorded. None of it is placed beside the comparable set above and none of it is put into one figure with it.</p></div>
 ${turboHere?`<div class="panel callout"><div class="eyebrow">Resolved before this screen</div><h3>The turbo list-price conflict is already settled. It is not a question for the reader.</h3><p>${esc(turboHere.statement)}</p>${metadataLine(currentMetadata(c))}<div class="evidence-line"><span>Applicable list price for billing</span><b>${eur(turboHere.resolved_billable_list,2)}</b></div><div class="evidence-line"><span>Second observation, kept as a sensitivity</span><b>${turboHere.sensitivity_range.map(v=>eur(v,2)).join(' / ')}</b></div><div class="evidence-line"><span>Resolved by</span><b class="small">${esc(turboHere.resolved_by||'not stated')}</b></div><p class="small"><b>Still open:</b> ${esc(turboHere.open_statement||'not stated')}</p></div>`:''}${snapshotPanel(c)}${leadsBlock}<details class="prior-web"><summary>Earlier web evidence, kept separate (${prior.length} records)</summary><p class="small">Retrieved for version 0.1, with the cache-age limits below. These records were not part of the accepted archive and have not been refreshed in this revision. A missing record in that archive does not erase them.</p>${prior.map(o=>`<div class="source-row"><b>${esc(o.seller)} &middot; ${esc(o.part)} &middot; ${esc(o.market)}</b><p>${o.price===null?'Reference only':`${esc(o.currency)} ${num(o.price,2)}`} &middot; VAT ${esc(o.tax)}.<br>${esc(o.match)} ${esc(o.note)}</p><p class="small">${esc(o.freshness)} ${esc(o.verification)}</p>${safeLink(o.url,'Earlier source listing')}</div>`).join('')}</details>${relatedTable(c)}<div class="panel warn"><h3>What remains unresolved for this case</h3><div class="acceptance-grid">${(e.readiness||[]).map(r=>`<div><b>${esc(r.name)}</b><p class="small">${esc(r.status)}</p></div>`).join('')}</div><p class="small">Restricted model-cost records and the source invoice line were not copied into this browser file. The former generic reference-price multiplier and automatic price ceilings have been removed. ${esc(D.meta.confirmedRules.costTypeRequired||'')}</p><button class="button primary" data-view="economics">Test a stated price, not an inferred optimum</button></div>`;
}

/* ------------------------------------------------------- corrected views */
function flagChips(r){
  if(!r.ok||!r.flags||!r.flags.length)return '<span class="badge hold">No trade-off flagged</span>';
  return r.flags.map(f=>`<span class="badge ${f.severity==='high'?'review':'assumption'}">${esc(f.text)}</span>`).join(' ');
}
function resultStateTable(r,c){
  if(!r.ok)return `<div class="panel warn error-msg"><b>This scenario was not calculated.</b><br>${esc(r.error)}</div>`;
  const gp=(r.gp_change===null);
  return `<div class="tablewrap" tabindex="0" aria-label="Scrollable table"><table>
  <thead><tr><th>Measure</th><th class="n">Unchanged offer</th><th class="n">Proposed offer</th><th class="n">Change</th></tr></thead>
  <tbody>
  <tr><td>Applicable net price, EUR/${esc(c.unit)}</td><td class="n">${eur(r.price_before,2)}</td><td class="n">${eur(r.price_after,2)}</td><td class="n ${color(r.price_after-r.price_before)}">${pct(100*(r.price_after/r.price_before-1))}</td></tr>
  <tr><td>Eligible quantity</td><td class="n">${num(r.quantity_before,0)}</td><td class="n">${num(r.quantity_after,0)}</td><td class="n">${num(r.quantity_after-r.quantity_before,0)}</td></tr>
  <tr><td>ISZE revenue</td><td class="n">${eur(r.revenue_before)}</td><td class="n">${eur(r.revenue_after)}</td><td class="n ${color(r.revenue_change)}">${signedEUR(r.revenue_change)}</td></tr>
  <tr><td>Parts purchase cost applied</td><td class="n" colspan="2">${r.cost===null?'<span class="danger-line">No verified cost</span>':eur(r.cost,4)+' / '+esc(c.unit)+' &middot; '+esc(r.cost_basis_id||'unnamed basis')}</td><td class="n">${r.cost===null?'gross profit not calculated':'parts purchase cost only'}</td></tr>
  <tr><td>Gross profit</td><td class="n">${gp?'Cost required':eur(r.gp_before)}</td><td class="n">${gp?'Cost required':eur(r.gp_after)}</td><td class="n ${gp?'':color(r.gp_change)}">${gp?'Cost required':signedEUR(r.gp_change)}</td></tr>
  <tr><td>Offer gross margin (profit &divide; revenue)</td><td class="n">${gp?'Cost required':num(r.margin_before_pct,1)+'%'}</td><td class="n">${gp?'Cost required':num(r.margin_after_pct,1)+'%'}</td><td class="n ${gp?'':color(r.margin_pp_change)}">${gp?'Cost required':pct(r.margin_pp_change)+' pp'}</td></tr>
  <tr><td>Unit margin on the proposed price</td><td class="n" colspan="2">${gp?'-':num(r.margin_unit_after_pct,1)+'%'}</td><td class="n small">a different measure from the offer margin</td></tr>
  <tr><td>Discount given away on existing volume</td><td class="n" colspan="2">${esc(r.scope==='all'?'applies to all eligible volume':'incremental units only')}</td><td class="n ${r.discount_on_existing_volume_eur>0?'danger-line':''}">${eur(r.discount_on_existing_volume_eur)}</td></tr>
  ${gp?'':`<tr><td>Profit bridge: revenue &minus; cost &minus; support</td><td class="n" colspan="3">${signedEUR(r.bridge_revenue_change)} &minus; ${eur(r.bridge_cost_change)} &minus; ${eur(r.bridge_support_eur)} ${r.bridge_reconciles?'<span class="badge fact">reconciles</span>':'<span class="badge review">does not reconcile</span>'}</td></tr>`}
  </tbody></table></div>
  <p class="small ruleline">Quantity basis: <b>${esc(r.quantity_label)}</b>. Evidence period: <b>${esc(r.evidence_period||'not stated')}</b>. Offer effective date: <b>${esc(r.offer_effective_date||'not set')}</b>. No volume response to a price change is assumed.</p>
  ${r.conditional.length?`<div class="panel warn" style="margin-top:12px"><h3>What remains conditional</h3>${r.conditional.map(t=>`<p class="small">${esc(t)}</p>`).join('')}</div>`:''}`;
}
function breakEvens(r){
  if(!r.ok)return '';
  const gp=(r.gp_change===null);
  const inc=(r.scope==='incremental');
  /* The price direction decides what the two break-even figures mean. On a cut
     the proposed price is lower, so the figures are quantities that have to be
     reached. On a rise the same contribution arrives on fewer units, so the
     figures are volume floors - the lowest totals volume may fall to before
     each measure drops below the unchanged offer. Showing both under one
     heading called "required" invites the rise case to be read backwards. */
  const rising=r.price_after>r.price_before;
  const cut=r.price_after<r.price_before;
  const chg=v=>(v===null||v===undefined||!Number.isFinite(v))?'-':pct(100*(v/Math.max(r.quantity_before,1)-1));
  return `<div class="panel"><h3>${rising?'The volume floor each measure allows':(cut?'The quantity each measure requires':'The volume each measure needs')}</h3>
  <p class="small"><b>${inc?'Incremental-only pricing.':'All-volume pricing.'}</b> ${inc?'Existing units keep the current price, so they already hold their revenue and their gross profit. Only additional units are tested against the support.':'The proposed price applies to every eligible unit, so the existing volume is repriced as well.'}${rising?' <b>Because this is a price rise, the two figures below are floors, not targets: volume may fall as far as the lower of them before a measure drops below the unchanged offer.</b>':''}</p>
  <div class="tablewrap" tabindex="0" aria-label="Scrollable table"><table>
  <thead><tr><th>Test</th><th class="n">${rising?'Lowest total quantity that still holds':'Required total quantity'}</th><th class="n">Change from the unchanged offer</th></tr></thead>
  <tbody>
  <tr><td>Hold revenue</td><td class="n">${num(r.qty_preserve_revenue,0)}</td><td class="n">${chg(r.qty_preserve_revenue)}</td></tr>
  <tr><td>Hold gross profit</td><td class="n">${r.qty_preserve_gp===null?(gp?'Cost required':'<span class="danger-line">Not attainable at this price</span>'):num(r.qty_preserve_gp,0)}</td><td class="n">${r.qty_preserve_gp===null?'Not calculated':chg(r.qty_preserve_gp)}</td></tr>
  <tr><td>Exceed revenue (smallest orderable quantity)</td><td class="n">${r.extra_qty_to_exceed_revenue===null?'-':num(r.quantity_before+r.extra_qty_to_exceed_revenue,0)}</td><td class="n">${r.extra_qty_to_exceed_revenue===null?'-':num(r.extra_qty_to_exceed_revenue,0)+' more units'}</td></tr>
  <tr><td>Exceed gross profit (smallest orderable quantity)</td><td class="n">${r.extra_qty_to_exceed_gp===null?'Not attainable':num(r.quantity_before+r.extra_qty_to_exceed_gp,0)}</td><td class="n">${r.extra_qty_to_exceed_gp===null?'-':num(r.extra_qty_to_exceed_gp,0)+' more units'}</td></tr>
  <tr><td class="small" colspan="3">Pack size applied: ${num(r.pack_size,0)} unit(s). A quantity above a threshold is the smallest orderable multiple above it, not the threshold plus a fraction.</td></tr>
  ${r.price_after>r.price_before?`<tr><td><b>Tolerable volume loss</b></td><td class="n" colspan="2">Before revenue falls: <b>${E.fmtPct(r.tolerable_loss_revenue_pct)}</b> &middot; before gross profit falls: <b>${r.tolerable_loss_gp_pct===null?'-':E.fmtPct(r.tolerable_loss_gp_pct)}</b> &middot; binding limit <b>${E.fmtPct(r.tolerable_volume_loss_pct)}</b></td></tr>`:''}
  </tbody></table></div>
  <p class="small ruleline">Where the evidence cannot predict volume, this states ${rising?'the lowest quantity the price rise still allows (a floor, not a target) and the test':'the quantity required and the test'}. It is not a false optimal price.</p>
  ${E.conditionalTest(r).map(t=>`<p class="small"><b>The test:</b> ${esc(t)}</p>`).join('')}</div>`;
}
function objectives(c){
  const objective=state.objective||'revenue';
  const rk=E.rankAlternatives(c,objective,{payload:D,pack_size:scenario().pack_size,offer_effective_date:offerDate()});
  const rev=E.rankAlternatives(c,'revenue',{payload:D,offer_effective_date:offerDate()});
  const gp=E.rankAlternatives(c,'grossProfit',{payload:D,offer_effective_date:offerDate()});
  const b=rk.baseline;
  const s=scenario();
  const baselineCost=s.cost_basis_id?E.costRecord(D,c.pn,s.cost_basis_id):null;
  const anyTradeOff=rk.ranked.some(x=>x.result.ok&&x.result.flags.some(f=>f.code==='REV_UP_GP_DOWN'||f.code==='GP_UP_REV_DOWN'));
  const spread=rk.baseline_consistency;
  const migUnresolved=rk.ranked.filter(x=>x.alternative.kind==='migration');
  const rows=rk.ranked.map((x,i)=>({x,r:x.result,i}));
  return `<div class="inputsnote"><b>Two objectives, one engine, one baseline.</b> Revenue growth is the default view. Changing the objective re-ranks the alternatives; it does not change the baseline, the eligible quantity or the volume assumption. Every row shows both measures.</div>
  ${(()=>{const tw=objectiveTwin(c);return `<div class="panel ${tw.ordering_only?'good':'warn'}"><span class="badge ${tw.ordering_only?'hold':'review'}">${tw.ordering_only?'Ordering only':'Assumptions differ'}</span><p style="margin-top:12px">${esc(tw.statement)}</p><p class="small">${tw.orders_differ?'The two objectives put the alternatives in a different order for this case.':'Both objectives put the alternatives in the same order for this case; the two measures still differ per row.'}</p></div>`;})()}
  <div class="compare-row"><div><span class="eyebrow">Ranking objective</span><div class="small">${esc(rk.objective_label)} &middot; compared with the unchanged offer over ${esc(b.period)}</div></div>
  <select id="objective" aria-label="Ranking objective">
    <option value="revenue" ${objective==='revenue'?'selected':''}>Revenue growth - additional ISZE revenue (default)</option>
    <option value="grossProfit" ${objective==='grossProfit'?'selected':''}>Gross-profit growth - additional gross profit in EUR</option>
  </select></div>
  ${!spread.consistent?`<div class="panel warn"><span class="badge review">More than one profit baseline is present</span><p style="margin-top:12px">These alternatives do not all declare the same supplier-cost basis, so their gross-profit figures are <b>not</b> directly comparable. The screen reports the ${spread.distinct_gross_profit_baselines} distinct unchanged-offer gross profits it found instead of presenting them as one baseline. Set one offer effective date across the alternatives you intend to compare, or treat a supplier-cost change as a separate documented assumption.</p></div>`:''}
  ${anyTradeOff?`<div class="panel warn"><span class="badge review">Trade-off present</span><p style="margin-top:12px">At least one alternative moves revenue and gross profit in opposite directions. A revenue increase with a gross-profit reduction, or a gross-profit increase with a revenue reduction, is flagged and is not automatically approved.</p></div>`:''}
  <div class="grid3">
    <div class="panel"><span class="eyebrow">Baseline</span><h3>Unchanged offer</h3>
      <div class="evidence-line"><span>Applicable net price</span><b>${eur(b.price,2)}</b></div>
      <div class="evidence-line"><span>Eligible quantity</span><b>${num(b.quantity,0)}</b></div>
      <div class="evidence-line"><span>Revenue</span><b>${eur(b.revenue)}</b></div>
      <div class="evidence-line"><span>Recorded billing</span><b>${eur(b.recorded_billing_eur)}</b></div>
      <div class="evidence-line"><span>Gross profit</span><b>${baselineCost&&b.quantity!==null?eur(b.quantity*(b.price-baselineCost.cost_eur)):'Cost required'}</b></div>
      <p class="small">${esc(b.basis_statement)}</p>
      ${b.is_rounded_scenario?'<p class="small danger-line">The rounded price does not reproduce the recorded billing, so this is a rounded scenario and is labelled as one.</p>':''}
      <div class="evidence-line"><span>Offer effective date</span><b>${esc(offerDate()||'not set')}</b></div>
      <div class="evidence-line"><span>Evidence period</span><b>${esc(b.period)}</b></div>
      </div>
    <div class="panel ${objective==='revenue'?'callout':''}">
      <span class="eyebrow">Objective 1${objective==='revenue'?' &middot; default':''}</span>
      <h3>Revenue-growth option</h3>
      ${rev.ranked.length&&rev.ranked[0].result.ok?`<div class="resultbig ${color(rev.ranked[0].result.revenue_change)}">${signedEUR(rev.ranked[0].result.revenue_change)}</div>
      <div class="small">${esc(rev.ranked[0].alternative.name)}</div>
      <div class="evidence-line"><span>Gross-profit change</span><b class="${color(rev.ranked[0].result.gp_change)}">${rev.ranked[0].result.gp_change===null?'Cost required':signedEUR(rev.ranked[0].result.gp_change)}</b></div>
      <div class="evidence-line"><span>Offer gross margin after</span><b>${rev.ranked[0].result.margin_after_pct===null?'Cost required':num(rev.ranked[0].result.margin_after_pct,1)+'%'}</b></div>
      <button class="button" data-select="${esc(rev.ranked[0].alternative.alternative_id)}">Use this option in the price test</button>`:unavailableBlock({title:'No revenue-producing alternative is held for this case',reason:'No recorded alternative produces an ISZE revenue change here, so none is ranked. The panel is not empty because the view failed; the payload holds no such alternative.',required:'a stated alternative with a recorded price movement for this exact part',scope:'case alternatives'})}
      </div>
    <div class="panel ${objective==='grossProfit'?'callout':''}">
      <span class="eyebrow">Objective 2</span>
      <h3>Gross-profit-growth option</h3>
      ${gp.ranked.length&&gp.ranked[0].result.gp_change!==null?`<div class="resultbig ${color(gp.ranked[0].result.gp_change)}">${signedEUR(gp.ranked[0].result.gp_change)}</div>
      <div class="small">${esc(gp.ranked[0].alternative.name)}</div>
      <div class="evidence-line"><span>Revenue change</span><b class="${color(gp.ranked[0].result.revenue_change)}">${signedEUR(gp.ranked[0].result.revenue_change)}</b></div>
      <div class="evidence-line"><span>Offer gross margin after</span><b>${num(gp.ranked[0].result.margin_after_pct,1)}%</b></div>
      <button class="button" data-select="${esc(gp.ranked[0].alternative.alternative_id)}">Use this option in the price test</button>`:unavailableBlock({title:'Gross-profit growth is not available for this case',reason:'No parts purchase cost is held or entered for this exact part, so gross profit and gross margin are not calculated. Revenue still is. No figure is estimated and no cost is defaulted.',required:'the parts purchase cost for '+c.pn+' per the declared supplier purchase-cost calculation, or a manually entered cost labelled as an assumption',scope:'case alternatives'})}
      </div>
  </div>
  ${migUnresolved.length?`<div class="panel warn"><span class="badge review">Product migration is not priced here</span>${migUnresolved.map(m=>`<p class="small"><b>${esc(m.alternative.name)}</b> - ${esc(m.result.error)}</p>`).join('')}</div>`:''}
  <div class="panel"><h3>Ranked under ${esc(rk.objective_label)}</h3>
    <p class="small">Same customer, same period, same eligible quantity and same product population for every row. Volume assumptions and evidence limitations stay visible.</p>
    <div class="tablewrap" tabindex="0" aria-label="Scrollable table"><table><thead><tr><th>Rank</th><th>Alternative</th><th class="n">Price</th><th class="n">Revenue change</th><th class="n">Gross-profit change</th><th class="n">Offer margin</th><th>Volume basis</th><th>Flags</th></tr></thead><tbody>
    ${rows.map(row=>`<tr${row.x.alternative.alternative_id===s.selected_alternative_id?' class="selected-row"':''}>
      <td class="n">${row.i+1}</td>
      <td><b>${esc(row.x.alternative.name)}</b><div class="small">${esc(row.x.alternative.eligibility)}</div>${row.x.alternative.evidence?`<div class="small">${esc(row.x.alternative.evidence)}</div>`:''}<div style="margin-top:6px"><button class="linkbutton" data-select="${esc(row.x.alternative.alternative_id)}">Select &rarr;</button></div></td>
      <td class="n">${row.r.ok?eur(row.r.price_after,2):'-'}</td>
      <td class="n ${row.r.ok?color(row.r.revenue_change):''}">${row.r.ok?signedEUR(row.r.revenue_change):'<span class="small">unresolved</span>'}</td>
      <td class="n ${row.r.ok?color(row.r.gp_change):''}">${!row.r.ok?'-':row.r.gp_change===null?'Cost required':signedEUR(row.r.gp_change)}</td>
      <td class="n">${row.r.ok&&row.r.margin_after_pct!==null?num(row.r.margin_after_pct,1)+'%':'-'}</td>
      <td class="small">${esc(row.x.alternative.volume_label)}</td>
      <td>${row.r.ok?flagChips(row.r):`<span class="badge hold">not priced</span>`}</td></tr>`).join('')}
    </tbody></table></div>
    <p class="small ruleline">This ranks by the selected objective and does not use an invented composite score. A mathematically profitable scenario is not an approved offer and is not a forecast.</p></div>
  ${(()=>{
    /* Ported from the retired layer. It used to hold up the selected part's own
       worked detail and its break-even table. This layer's economics tab is the
       one place a scenario is entered and calculated, so repeating it here would
       put two editable copies of one price on screen. What was missing on the
       ranking is the volume the top-ranked alternative actually needs, so the
       volume test is stated here and the one point of entry stays on the tab
       that owns it. */
    const topRev=rev.ranked.length&&rev.ranked[0].result.ok?rev.ranked[0]:null;
    const topGp=gp.ranked.length&&gp.ranked[0].result.ok&&gp.ranked[0].result.gp_change!==null?gp.ranked[0]:null;
    const top=objective==='grossProfit'&&topGp?topGp:topRev;
    if(!top)return '';
    const r=top.result;
    const chg=v=>(v===null||v===undefined||!Number.isFinite(v))?'-':pct(100*(v/Math.max(r.quantity_before,1)-1));
    const inc=(r.scope==='incremental');
    const rising=r.price_after>r.price_before;
    const cut=r.price_after<r.price_before;
    return `<div class="panel"><h3>${rising?'The volume floor the top-ranked option allows':(cut?'The quantity the top-ranked option requires':'The volume the top-ranked option needs')}</h3>
    <p class="small"><b>${esc(top.alternative.name)}</b> &middot; <b>${inc?'Incremental-only pricing.':'All-volume pricing.'}</b> ${inc?'Existing units keep the current price, so they already hold their revenue and their gross profit. Only additional units are tested against the support.':'The proposed price applies to every eligible unit, so the existing volume is repriced as well.'}${rising?' <b>Because this is a price rise, the two figures below are floors, not targets: volume may fall as far as the lower of them before a measure drops below the unchanged offer.</b>':''}</p>
    <div class="tablewrap" tabindex="0" aria-label="Scrollable table"><table><thead><tr><th>Test</th><th class="n">${rising?'Lowest total quantity that still holds':'Required total quantity'}</th><th class="n">Change from the unchanged offer</th></tr></thead><tbody>
    <tr><td>Hold revenue</td><td class="n">${num(r.qty_preserve_revenue,0)}</td><td class="n">${chg(r.qty_preserve_revenue)}</td></tr>
    <tr><td>Hold gross profit</td><td class="n">${r.qty_preserve_gp===null?(r.gp_change===null?'Cost required':'<span class="danger-line">Not attainable at this price</span>'):num(r.qty_preserve_gp,0)}</td><td class="n">${r.qty_preserve_gp===null?'Not calculated':chg(r.qty_preserve_gp)}</td></tr>
    <tr><td>Exceed revenue (smallest orderable quantity)</td><td class="n">${r.extra_qty_to_exceed_revenue===null?'-':num(r.quantity_before+r.extra_qty_to_exceed_revenue,0)}</td><td class="n">${r.extra_qty_to_exceed_revenue===null?'-':num(r.extra_qty_to_exceed_revenue,0)+' more units'}</td></tr>
    <tr><td>Exceed gross profit (smallest orderable quantity)</td><td class="n">${r.extra_qty_to_exceed_gp===null?'Not attainable':num(r.quantity_before+r.extra_qty_to_exceed_gp,0)}</td><td class="n">${r.extra_qty_to_exceed_gp===null?'-':num(r.extra_qty_to_exceed_gp,0)+' more units'}</td></tr>
    <tr><td class="small" colspan="3">Pack size applied: ${num(r.pack_size,0)} unit(s). A quantity above a threshold is the smallest orderable multiple above it, not the threshold plus a fraction.</td></tr>
    ${r.price_after>r.price_before?`<tr><td><b>Tolerable volume loss</b></td><td class="n" colspan="2">Before revenue falls: <b>${pct(r.tolerable_loss_revenue_pct)}</b> &middot; before gross profit falls: <b>${r.tolerable_loss_gp_pct===null?'-':pct(r.tolerable_loss_gp_pct)}</b> &middot; binding limit <b>${pct(r.tolerable_volume_loss_pct)}</b></td></tr>`:''}
    </tbody></table></div>
    <p class="small ruleline">Where the evidence cannot predict volume, this states ${rising?'the lowest quantity the price rise still allows (a floor, not a target) and the test':'the quantity required and the test'}. It is not a false optimal price.</p>
    ${E.conditionalTest(r).map(t=>`<p class="small"><b>The test:</b> ${esc(t)}</p>`).join('')}</div>`;
  })()}
  ${s.selected_alternative_id?`<div class="panel callout"><h3>Selected for the decision</h3><p class="small">${esc((c.alternatives.find(a=>a.alternative_id===s.selected_alternative_id)||{}).name||'')} is now the record used by the price test, the internal action, the save and every export.</p><div class="rowactions"><button class="button primary" data-view="economics">Open it in the price &amp; profit test</button><button class="button" data-view="action">Prepare the internal review</button></div></div>`:''}
  <div class="panel dark"><h3>What this does not say</h3>
    <p>No minimum gross margin and no acceptable profit sacrifice are confirmed, so both approval controls are deliberately unset. That absence does not block these calculations; it blocks approval.</p>
    <div class="evidence-line"><span>Minimum gross margin control</span><b>${esc(D.meta.confirmedRules.minMarginStatus)}</b></div>
    <div class="evidence-line"><span>Acceptable profit sacrifice control</span><b>${esc(D.meta.confirmedRules.maxProfitSacrificeStatus)}</b></div>
    <p class="small">No invented threshold is populated into either control, and neither control was needed to produce the numbers above.</p>
    <p class="small">${esc(c.counter||'')}</p></div>`;
}
function economicsResults(){
  const c=current(),r=caseResult(),s=scenario();  const gp=(r.gp_change===null);
  const stress=[r.scope==='all'?[-10,0,10,25,50]:[0,10,25,50,100]].flat();
  const stressRows=stress.map(v=>{
    const rr=E.calculate({price_before:s.price_before,price_after:s.price_after,
      quantity_before:s.quantity_before,quantity_after:s.quantity_after===null?null:s.quantity_after*(1+v/100),
      scope:s.scope,support_eur:s.support_eur,cost_eur:s.cost_eur,pack_size:s.pack_size,
      quantity_label:'stated test assumption'});
    return `<tr><td>${pct(v)}</td><td class="n ${color(rr.revenue_change)}">${rr.ok?signedEUR(rr.revenue_change):'-'}</td><td class="n ${color(rr.gp_change)}">${rr.ok&&!gp?(rr.gp_change===null?'Cost required':signedEUR(rr.gp_change)):'Cost required'}</td></tr>`;}).join('');
  return `${metadataLine(currentMetadata(c))}${!r.ok?`<div class="panel warn error-msg"><b>This scenario was not calculated.</b><br>${esc(r.error)}</div>`:`<div class="grid2"><div class="panel"><div class="result-label">Revenue change in this scenario</div><div class="resultbig ${color(r.revenue_change)}">${signedEUR(r.revenue_change)}</div><div class="small">${num(r.quantity_after,1)} ${esc(c.unit)}s &middot; ${eur(r.price_after,2)} proposed net price<br>Against ${eur(r.revenue_before)} at the accepted base price of ${eur(r.price_before,2)}.</div></div><div class="panel ${gp?'warn':r.gp_change<0?'warn':'good'}"><div class="result-label">Scenario gross-profit change</div><div class="resultbig ${gp?'':color(r.gp_change)}">${gp?'Cost required':signedEUR(r.gp_change)}</div><div class="small">${gp?'No verified parts purchase cost is held for this part on the selected basis.':'Parts purchase cost only, less '+eur(r.support_eur)+' of one-off support counted once. Freight, duty, overheads and kickbacks are excluded.'}</div></div></div>`}
  ${resultStateTable(r,current())}
  ${gp?unavailableBlock({title:'Gross profit and gross margin are not calculated for this case',reason:(c.packEvidence.costRecordPresent?'A parts purchase cost is held for this part, but no cost is applied to this scenario yet, so gross profit and gross margin are not stated. Apply the basis or enter the cost and the figures follow. A missing cost is not zero.':'No parts purchase cost is held or entered for this exact part, so gross profit and gross margin cannot be stated. A missing cost is not zero.')+' Revenue and the revenue break-even still are. The figures are not estimated and no cost is defaulted.',required:'the parts purchase cost for '+c.pn+' per the declared supplier purchase-cost calculation, or a manually entered cost labelled as an assumption',scope:'this scenario'}):''}
  ${breakEvens(r)}
  ${!gp?`<div class="panel"><div class="evidence-line"><span>Offer gross margin before</span><b>${num(r.margin_before_pct,1)}%</b></div><div class="evidence-line"><span>Offer gross margin after</span><b>${num(r.margin_after_pct,1)}%</b></div><div class="evidence-line"><span>Unit margin on the proposed price</span><b>${num(r.margin_unit_after_pct,1)}%</b></div>${r.margin_unit_after_pct<=0?'<p class="error-msg">Proposed net price does not exceed the entered unit cost. Do not release this price.</p>':''}</div>`:''}
  <div class="panel"><h3>Stress the volume assumption</h3><div class="tablewrap" tabindex="0" aria-label="Scrollable table"><table><thead><tr><th>Assumed volume change</th><th class="n">Revenue change</th><th class="n">Gross-profit change</th></tr></thead><tbody>${stressRows}</tbody></table></div><p class="small ruleline">The model does not predict volume. The change must come from a commitment or a stated test assumption. It does not multiply a modelled market gap by an invented recovery rate.</p></div>
  <div class="panel dark"><h3>Read this before a pricing decision</h3><p>${esc(c.recommendation)}</p><p class="small">Effective rounded price change: ${pct(r.ok?100*(r.price_after/r.price_before-1):null)}. The base covers the recorded period; it is not annualised. The default cohort is all historical units. Change the eligibility scope before treating a targeted offer as a blanket discount.</p></div>`;
}
/* UX-02. The price test names the ranked option it started from and the values
   edited by hand since, so a selected option and a manual edit are one record. */
const EDIT_LABELS={price_before:'scenario base price',price_after:'proposed net price',quantity_before:'base quantity',
  quantity_after:'proposed quantity',quantity_label:'volume basis label',scope:'volume scope',support_eur:'one-off support cost',
  cost_eur:'unit parts purchase cost',cost_basis_id:'supplier-cost basis',pack_size:'pack size'};
function chosenOption(){
  const a=store.alternativeEdits(state.caseId);
  if(!a.selected)return '<p class="small" data-chosen-option="">No ranked option is selected. The values below are the unchanged offer or your own entries.</p>';
  const edits=a.edited_fields===null?'Whether a value was edited after selection is not known for a reopened record.'
    :a.edited_fields.length?'Edited by hand since selection: '+a.edited_fields.map(k=>esc(EDIT_LABELS[k]||k)).join(', ')+'.'
    :'No value has been edited since selection.';
  return `<div class="panel callout" data-chosen-option="${esc(a.selected)}"><span class="eyebrow">Selected option</span><p><b>${esc(a.label)}</b></p><p class="small" data-edited-fields="${esc((a.edited_fields||[]).join(','))}">${edits}</p></div>`;
}
function economics(c){
  const r=caseResult(),s=scenario(),e=c.packEvidence;
  const bases=basisOptions();
  const rec=s.cost_basis_id?E.costRecord(D,c.pn,s.cost_basis_id):null;
  const trace=assumptionTrace(),fi=fieldIssues();
  return `<div class="inputsnote"><b>Scenario only; no automatic price move.</b> Default price and volume response are unchanged. A manual price or cost does not approve a customer quotation, cost basis or margin floor.</div>
  <div class="split"><div class="panel scenario-controls"><h3>Define the offer being tested</h3>${chosenOption()}
  <div class="field"><label for="s-pn">Exact part</label><input id="s-pn" value="${esc(s.part_number)}" readonly><small>The original part reference is carried, never rewritten.</small></div>
  <div class="field"><label for="s-basis">Supplier-cost basis</label><select id="s-basis">${bases.map(b=>`<option value="${esc(b.basis_id)}" ${s.cost_basis_id===b.basis_id?'selected':''}>${esc(b.basis_id)} - ${esc(b.name)}</option>`).join('')}</select><small>${rec?`Verified parts purchase cost ${eur(rec.cost_eur,4)} per ${esc(c.unit)} on ${esc(rec.basis_id)} (${esc(rec.rate_window||'')}).`:'No verified cost is held for this part on the selected basis.'} ${esc(D.meta.confirmedRules.costTypeRequired||'')}</small></div>
  <div class="field"><label for="s-date">Offer effective date</label><input id="s-date" type="date" value="${esc(s.offer_effective_date||'')}"><small>Required. It selects the supplier-cost basis. It is kept separate from the evidence period below.</small></div>
  <div class="field"><label for="s-period">Evidence period (recorded history)</label><input id="s-period" value="${esc(s.evidence_period||'')}"><small>A separate clock. Recorded history is never relabelled as a forward offer.</small></div>
  <div class="field"><label for="s-baseP">Scenario base price, EUR / ${esc(c.unit)}</label><input id="s-baseP" type="number" min=".01" step=".01" value="${s.price_before}"><small>Changing this changes the scenario base, not historical recorded billing.</small></div>
  <div class="field"><label for="s-newP">Proposed ISZE net price, EUR / ${esc(c.unit)}</label><input id="s-newP" type="number" step=".01" min=".01" value="${s.price_after}"><small>Starts unchanged. Choosing a list value is a sensitivity, not an approved net offer.</small></div>
  <div class="field"><label for="s-scope">Which volume receives the new price?</label><select id="s-scope"><option value="all" ${s.scope==='all'?'selected':''}>All eligible volume</option><option value="incremental" ${s.scope==='incremental'?'selected':''}>Additional units only</option></select><small>Additional-units-only keeps existing units at the current price.</small></div>
  <div class="field"><label for="s-baseQ">Eligible historical base quantity</label><input id="s-baseQ" type="number" min="1" step="1" value="${s.quantity_before}"><small>Recorded for this period. No annualisation. A zero or negative quantity is refused.</small></div>
  <div class="field"><label for="s-qty">Proposed total quantity (leave blank for unchanged)</label><input id="s-qty" type="number" min="0" step="1" value="${s.quantity_after===null?'':s.quantity_after}"><small>Blank means the quantity does not change. Zero is refused as a full withdrawal, not a price scenario.</small></div>
  <div class="field"><label for="s-pack">Pack size (units per order increment)</label><input id="s-pack" type="number" min="1" step="1" value="${s.pack_size}"><small>Required quantities round up to a whole pack.</small></div>
  <div class="field"><label for="s-cost">Unit parts purchase cost, EUR</label><input id="s-cost" type="number" min="0" step=".0001" placeholder="No verified cost held" value="${s.cost_eur===null?'':s.cost_eur}"><small>${e.costRecordPresent?'A verified cost record exists for this part. Selecting a basis fills the value. A manual entry overrides it and is your assumption.':'No cost-basis record is present for this exact part.'} A missing cost is not zero: leaving this empty means gross profit is not calculated, not that profit is nil.</small></div>
  <div class="field"><label for="s-support">One-off support cost, EUR</label><input id="s-support" type="number" min="0" step="1" value="${s.support_eur}"><small>Deducted once from gross profit. Zero is a stated assumption, not proof that no support exists.</small></div>
  <div class="field"><label for="s-label">Volume basis label</label><input id="s-label" value="${esc(s.quantity_label)}"><small>A movement is labelled, never predicted. Only 'observed history' and 'stated commitment' are treated as evidenced.</small></div>
  <div class="rowactions"><button class="button" id="reset-scenario">Reset to the unchanged offer</button><button class="button primary" data-view="action">Carry this scenario into the review</button></div>
  <p class="small" id="scenario-version">Scenario version ${s.version}. Every change updates this one record, which is what the ranking, the save and the exports read.</p>
  <div class="panel" data-trace="${esc(trace.fingerprint)}"><div class="eyebrow">What this result rests on</div><p class="small">${esc(trace.statement)}</p>${TRACE_INPUTS.map(k=>`<div class="evidence-line"><span>${esc(TRACE_LABELS[k]||k)}</span><b class="small" data-input="${esc(k)}">${esc(trace.inputs[k]===null||trace.inputs[k]===undefined?'not stated':String(trace.inputs[k]))}</b></div>`).join('')}<p class="small" data-commitment="${trace.commitment.is_commitment?'commitment':'manual'}">${esc(trace.commitment.statement)}</p></div>
  <div class="panel ${fi.ok?'':'warn'}" data-field-issues="${esc(JSON.stringify(fi.fields.map(f=>({field:f.field,state:f.state}))))}"><div class="eyebrow">What is wrong with a field, if anything</div><p class="small">${esc(fi.statement)}</p>${fi.fields.map(f=>`<div class="evidence-line"><span>${esc(f.field)}</span><b class="small" data-state="${esc(f.state)}" data-field="${esc(f.field)}">${esc(f.text)}</b></div>`).join('')}</div>
  </div><div id="economic-results">${economicsResults()}${sensitivityView()}</div></div>`;
}
function candidateState(){
  const all=D.candidateScreen||[];
  const s=state;
  const wb=C.workbench(all,{query:s.candidateQuery,criteria:s.candidateCriteria,
    page:s.candidatePage,page_size:s.candidatePageSize,
    sort_key:s.candidateSortKey,sort_direction:s.candidateSortDirection});
  return wb;
}
function candidatesView(){
  const wb=candidateState(),pg=wb.page,cov=wb.coverage,basis=wb.basis;
  const districts=[...new Set((D.candidateScreen||[]).map(r=>r.distributor))];
  /* The empty result is an explicit amber state. "Rows 1 to 0 of 0" reads as
     nonsense, and an unexplained empty table reads as a missing file rather than
     a filter that excluded the rows. */
  const emptyState=pg.total===0?unavailableBlock({
    title:'No candidate row matches this search',
    reason:'The search ran over all '+num(cov.rows_total,0)+' screened rows and none matched. The rows are not missing; the filter excluded them.',
    required:'a different search term, or clearing the cost and competitor filters',
    scope:'candidate screen, both pilot accounts'}):'';
  const arrow=k=>pg.page&&state.candidateSortKey===k?(state.candidateSortDirection==='desc'?' &darr;':' &uarr;'):'';
  const th=(k,label)=>`<button class="linkbutton sort-button" data-sort="${esc(k)}">${label}${arrow(k)}</button>`;
  return `<div class="inputsnote"><b>Derived candidate screen.</b> ${esc(D.screenRule.what)}. ${esc(D.screenRule.notA)}.</div>
  <div class="panel ${basis.declared?'':'warn'}"><h3>Reporting basis</h3><p class="small">${esc(basis.statement)}</p></div>
  <div class="stats">
    <div class="stat"><div class="label">Rows screened in total</div><strong>${num((D.candidateScreen||[]).length,0)}</strong><div class="detail">${num(cov.unique_parts,0)} distinct part numbers in the whole screened set &middot; a row is not a part &middot; both pilot accounts</div></div>
    <div class="stat"><div class="label">Rows matching this search</div><strong>${num(pg.total,0)}</strong><div class="detail">${num(pg.page_count,0)} page(s) at ${num(pg.page_size,0)} rows</div></div>
    <div class="stat"><div class="label">Rows with a price and a cost record</div><strong>${num(cov.rows_with_cost_and_list,0)}</strong><div class="detail">${num(cov.unique_parts_with_cost_and_list,0)} distinct part numbers &middot; coverage, not approval</div></div>
    <div class="stat"><div class="label">Rows with competitor evidence</div><strong>${num(cov.rows_with_competitor_evidence,0)}</strong><div class="detail">${num(cov.unique_parts_with_competitor_evidence,0)} distinct part numbers &middot; the rest state it is not located</div></div>
  </div>
  <div class="panel warn"><h3>Read the coverage before the ranking</h3>
    <p class="small">${esc(cov.cost_and_list_coverage)}</p>
    <p class="small">${esc(cov.not_approval)}</p>
    <p class="small">${esc(D.screenRule.competitorGap)}</p></div>
  ${emptyState}
  <div class="panel"><h3>Search and filter the whole permitted set</h3>
    <div class="filter-row">
      <div class="field"><label for="candidate-search">Search part number, description, distributor or reason</label><input id="candidate-search" value="${esc(state.candidateQuery)}" placeholder="e.g. PAD KIT, filter, 12345"><small>Every term must match. The search runs over all ${num(cov.rows_total,0)} rows, not the page you are looking at.</small></div>
      <div class="field"><label for="c-dist">Distributor</label><select id="c-dist"><option value="">All</option>${districts.map(d=>`<option value="${esc(d)}" ${state.candidateCriteria.distributor===d?'selected':''}>${esc(d)}</option>`).join('')}</select></div>
      <div class="field"><label for="c-ev">Evidence</label><select id="c-ev"><option value="">Any</option><option value="with_cost" ${state.candidateCriteria.with_cost?'selected':''}>Has a verified cost</option><option value="without_cost" ${state.candidateCriteria.without_cost?'selected':''}>No verified cost</option><option value="with_competitor" ${state.candidateCriteria.with_competitor?'selected':''}>Has competitor evidence</option><option value="base_price_moved" ${state.candidateCriteria.base_price_moved?'selected':''}>Base price moved</option></select></div>
      <div class="field"><label for="c-size">Rows per page</label><select id="c-size">${[10,25,50,100,250].map(n=>`<option value="${n}" ${state.candidatePageSize===n?'selected':''}>${n}</option>`).join('')}</select></div>
      <div class="rowactions"><button class="button" id="c-clear">Clear search and filters</button></div>
    </div>
    <p class="small">${num(pg.total,0)} of ${num(cov.rows_total,0)} rows match. ${pg.total===0?'No rows match the current search.':'Showing rows '+num(pg.first_row,0)+' to '+num(pg.last_row,0)+' of '+num(pg.total,0)+'.'} Every permitted row is reachable by search and paging, not only the first page.</p>
    <div class="tablewrap" tabindex="0" aria-label="Scrollable table"><table><thead><tr><th>Customer</th><th>${th('part_number','Part')}</th><th>Description</th><th class="n">${th('billed_qty','Billed qty')}</th><th class="n">${th('observed_billing_eur','Observed billing')}</th><th class="n">Observed unit price</th><th class="n">${th('list_eur','List')}</th><th class="n">${th('verified_cost_eur_oct26','Verified cost')}</th><th>Selection reason</th><th>Unresolved</th><th>Competitor</th><th>Review</th></tr></thead><tbody>
    ${pg.rows.length?pg.rows.map(r=>`<tr><td>${esc(r.distributor)}</td><td class="pn">${esc(r.part_number)}</td><td class="small">${esc(r.description||'')}</td>
      <td class="n">${num(r.billed_qty,0)}</td><td class="n">${eur(r.observed_billing_eur)}</td>
      <td class="n">${r.observed_unit_price===null?'-':eur(r.observed_unit_price,2)}</td>
      <td class="n">${r.list_eur===null?'-':eur(r.list_eur,2)}</td>
      <td class="n">${r.verified_cost_eur_oct26===null?'<span class="danger-line">not held</span>':eur(r.verified_cost_eur_oct26,4)}</td>
      <td class="small">${esc(r.selection_reasons)}</td><td class="small">${esc(r.unresolved_inputs||'-')}</td>
      <td class="small">${esc(r.competitor_evidence)}</td>
      <td><button class="linkbutton" data-open-part="${esc(r.part_number)}">Review ${esc(r.part_number)}</button></td></tr>`).join(''):'<tr><td colspan="12">No row matches the current search and filters. Clear the search or widen a filter; this is not an empty source.</td></tr>'}
    </tbody></table></div>
    <div class="pager">
      <button class="button" id="c-first" data-page="1" ${pg.page<=1?'disabled':''}>First</button>
      <button class="button" id="c-prev" data-page="${Math.max(1,pg.page-1)}" ${pg.page<=1?'disabled':''}>Previous</button>
      <span class="small">${pg.total===0?'No rows match the current search.':'Rows <b>'+num(pg.first_row,0)+'</b> to <b>'+num(pg.last_row,0)+'</b> of <b>'+num(pg.total,0)+'</b> matching &middot; page <b>'+num(pg.page,0)+'</b> of <b>'+num(pg.page_count,0)+'</b>'}</span>
      <button class="button" id="c-next" data-page="${Math.min(pg.page_count,pg.page+1)}" ${pg.page>=pg.page_count||pg.total===0?'disabled':''}>Next</button>
      <button class="button" id="c-last" data-last-page="1" ${pg.total===0?'disabled':''}>Last page</button>
    </div>
    <p class="small ruleline">Observed unit price is recorded billing divided by recorded quantity. It is not a list price, and a movement in it is not automatically a list-price change. A row with a cost and a list is a candidate for review, not a cleared price decision.</p></div>
  <div class="panel"><h3>The confirmed measure</h3>
    <p class="small"><b>Revenue</b> = applicable ISZE net parts selling price &times; quantity. <b>Gross profit</b> = revenue minus parts purchase cost of the quantities sold. <b>Gross margin</b> = gross profit &divide; revenue.</p>
    <p class="small">Excluded from the measure: ${(D.meta.confirmedRules.excludedFromMeasure||[]).join(', ')}. ${esc(D.meta.confirmedRules.doubleDeduction)}.</p>
    <p class="small">${esc(D.meta.confirmedRules.classMarginWarning)}</p>
    <p class="small">Minimum gross margin: <b>${esc(D.meta.confirmedRules.minMarginStatus)}</b>. Acceptable profit sacrifice: <b>${esc(D.meta.confirmedRules.maxProfitSacrificeStatus)}</b>. ${esc(D.meta.confirmedRules.effectOfAbsence)}</p></div>`;
}

/* F10 / UX-05. The route from a candidate row to that exact part.

   A row is a customer-part record, not a part: the same original reference can
   appear on several rows, and two rows can share a reference and still not be
   the same thing. So this view names the exact original reference and what would
   have to exist before it could become a case, and it never creates a case. */
function caseView(){
  const route=state.partRoute;
  if(!route){
    return unavailableBlock({
      title:'No part is selected',
      reason:'Open a row from the Candidates tab to review that exact part. Nothing is shown here because nothing was selected.',
      required:'a part number selected from the candidate workbench',
      scope:'selected part review'});
  }
  const rows=C.search(D.candidateScreen||[],route.partNumber).filter(r=>r.part_number===route.partNumber);
  const worked=(D.cases||[]).find(x=>x.pn===route.partNumber);
  const accounts={};rows.forEach(r=>{accounts[r.distributor]=(accounts[r.distributor]||0)+1;});
  const billing=rows.reduce((s,r)=>s+(Number.isFinite(Number(r.observed_billing_eur))?Number(r.observed_billing_eur):0),0);
  const withoutBilling=rows.filter(r=>!Number.isFinite(Number(r.observed_billing_eur))).length;
  const blockers=(typeof C.promotionBlockers==='function')?C.promotionBlockers(rows[0]||{}):null;
  return `<div class="panel callout"><div class="eyebrow">Selected part review</div>
  <h3>${esc(route.partNumber)} &mdash; ${esc(rows.length?(rows[0].description||'description not held'):'description not held')}</h3>
  <div class="evidence-line"><span>Exact original part reference</span><b class="pn">${esc(route.partNumber)}</b></div>
  <div class="evidence-line"><span>Screened rows covering it</span><b>${num(rows.length,0)}</b></div>
  <div class="evidence-line"><span>Accounts it was billed to</span><b class="small">${esc(Object.keys(accounts).map(k=>k+' ('+accounts[k]+' row(s))').join(', '))}</b></div>
  <div class="evidence-line"><span>Recorded billing across those rows</span><b>${eur(billing)}</b></div>
  ${withoutBilling?`<p class="small">${withoutBilling} of these rows carry no billing value. They are excluded from that total rather than counted as zero.</p>`:''}</div>
  ${worked?`<div class="panel good"><h3>This part is one of the worked cases</h3><p class="small">Open case ${esc(worked.id)} to test price and gross profit against its recorded evidence. The case carries the same exact part reference ${esc(worked.pn)}.</p><button class="button primary" data-open-case="${esc(worked.id)}">Open case ${esc(worked.id)}</button></div>`
   :`<div class="panel warn"><h3>No case record exists for this exact part yet</h3><p class="small">A screened row is a candidate for review. It is not a case, and nothing on this screen creates one. The row carries recorded billing and a list value and, where held, a parts purchase cost.</p>${blockers&&blockers.length?`<div class="ruleline"><b>What would have to exist before this could become a case</b>${blockers.map(b=>`<div class="evidence-line"><span>${esc(b.code||'Required')}</span><b class="small">${esc(b.text||'')}</b></div>`).join('')}</div>`:'<p class="small">The row does not state the current customer net price, the applicable cost basis and effective date, or a stated alternative to test. None of those three is inferred from the screened row, because the row shows what was billed, not what was offered.</p>'}</div>`}
  <div class="panel"><h3>The screened rows for this exact part</h3>
  <div class="tablewrap" tabindex="0" aria-label="Scrollable table"><table><thead><tr><th>Account</th><th class="n">Billed qty</th><th class="n">Observed billing</th><th class="n">Observed unit price</th><th class="n">List</th><th class="n">Parts purchase cost</th><th>Selection reason</th><th>Unresolved</th></tr></thead><tbody>
  ${rows.slice(0,50).map(r=>`<tr><td>${esc(r.distributor)}</td><td class="n">${num(r.billed_qty,0)}</td><td class="n">${eur(r.observed_billing_eur)}</td><td class="n">${r.observed_unit_price===null?'-':eur(r.observed_unit_price,2)}</td><td class="n">${r.list_eur===null?'-':eur(r.list_eur,2)}</td><td class="n">${r.verified_cost_eur_oct26===null?'<span class="danger-line">not held</span>':eur(r.verified_cost_eur_oct26,4)}</td><td class="small">${esc(r.selection_reasons)}</td><td class="small">${esc(r.unresolved_inputs||'-')}</td></tr>`).join('')}
  </tbody></table></div>
  ${rows.length>50?`<p class="small">Showing the first 50 rows held for this part of ${num(rows.length,0)}.</p>`:''}</div>
  <div class="rowactions"><button class="button" data-view="candidates">Back to the candidate screen</button></div>`;
}
function actionView(){
  const c=current(),r=caseResult(),s=scenario();
  const existing=repo.load(c.id);
  const summary=existing?repo.summarize(existing):null;
  const latest=existing?existing.revisions[existing.revisions.length-1]:null;
  const unsaved=state.unsavedReview[c.id]||null;
  const v=unsaved||(latest&&latest.record&&latest.record.review)||{};
  const consistency=store.consistency(c.id);
  const hist=existing?repo.history(c.id):[];
  return `<div class="inputsnote"><b>A durable record, not a scratch pad.</b> A save writes a new revision. Nothing is overwritten, and a correction names the revision it replaces.</div>
  <div class="grid2">
  <div class="panel"><div class="eyebrow">Prospective internal record</div><h3>One decision, with its evidence already attached</h3><p>${esc(c.next)}</p>
  <div class="field"><label for="a-owner">Owner role</label><input id="a-owner" value="${esc(v.owner_role||c.owner||'')}"><small>A suggested role is not a person's acceptance of ownership.</small></div>
  <div class="formrow"><div class="field"><label for="a-due">Next update due</label><input id="a-due" type="date" value="${esc(v.next_update_due||'')}"></div>
  <div class="field"><label for="a-status">State</label><select id="a-status">${CT.CASE_STATES.map(a=>`<option value="${a}" ${a===(v.state||summary&&summary.state||'draft')?'selected':''}>${esc(a)}</option>`).join('')}</select></div></div>
  <div class="field"><label for="a-next">Next action owed</label><input id="a-next" value="${esc(v.next_action||'Request the comparable quotation and the supplier support position')}"><small>Who owes what, by when. This is what the queue reads.</small></div>
  <div class="field"><label for="a-explanation">Customer / supply explanation (leave unknown if not received)</label><textarea id="a-explanation" placeholder="Unknown. Record who said what, when, and which parts it covers.">${esc(v.explanation||'')}</textarea></div>
  <div class="field"><label for="a-note">Proposed action and test conditions</label><textarea id="a-note">${esc(v.note||c.recommendation)}</textarea></div>
  <div class="field"><label for="a-outcome">Delivered support and outcome (recorded separately from the proposal)</label><textarea id="a-outcome" placeholder="Not yet delivered or measured. An agreed action is not a result.">${esc(v.outcome||'')}</textarea></div>
  <div class="rowactions"><button class="button primary" id="save-case">Save a new revision</button><button class="button" id="export-json">Export the internal record (JSON)</button><button class="button" id="export-member">Build a participant brief</button><button class="button" id="export-review-body">Export a readable case review</button><button class="button" id="export-bundle">Export all cases (recovery bundle)</button></div>
  <div class="status-msg" id="save-status">${unsaved?`Not saved. The form holds your unsaved entries; ${summary?`the last saved revision is ${summary.version}`:'no revision is saved for this case'}. Correct the cause and save again.`:summary?`Case at revision ${summary.version}, state ${esc(summary.state)}, last saved ${esc(summary.updated_at)}.`:'No revision saved yet for this case.'}</div>
  ${repo.store.isDurable()?'':'<p class="small danger-line">This browser will not keep the record after it closes. Use the recovery bundle before closing.</p>'}</div>
  <div>
  <div class="panel ${consistency.ok?'good':'warn'}"><h3>One scenario, checked</h3><p class="small">${esc(consistency.statement)}</p>${metadataLine(currentMetadata(c))}
    <div class="evidence-line"><span>Selected option</span><b>${esc(s.selected_alternative_id||'none - manual scenario')}</b></div>
    <div class="evidence-line"><span>Scenario version</span><b>${num(s.version,0)}</b></div>
    <div class="evidence-line"><span>Offer effective date</span><b>${esc(s.offer_effective_date||'not set')}</b></div>
    <div class="evidence-line"><span>Evidence period</span><b>${esc(s.evidence_period||'not stated')}</b></div>
    <div class="evidence-line"><span>Proposed net price</span><b>${eur(s.price_after,2)}</b></div>
    <div class="evidence-line"><span>Revenue change</span><b class="${color(r.revenue_change)}">${r.ok?signedEUR(r.revenue_change):'not calculated'}</b></div>
    <div class="evidence-line"><span>Gross-profit change</span><b class="${color(r.gp_change)}">${r.ok&&r.gp_change!==null?signedEUR(r.gp_change):'Cost required'}</b></div>
  </div>
  <div class="panel warn"><h3>Approval checks are still outstanding</h3><p class="small">The accepted records do not clear these approval checks. A saved revision does not approve a price, apply a discount or submit a case to another system.</p><div class="checks">${E.assess?E.assess(c).blockers.map(b=>`<div class="small">&square; ${esc(b)}</div>`).join(''):''}</div></div>
  <div class="panel"><h3>Revision history</h3>${hist.length?`<div class="tablewrap" tabindex="0" aria-label="Scrollable table"><table><thead><tr><th>Rev</th><th>Recorded</th><th>State</th><th>Supersedes</th><th>Note</th></tr></thead><tbody>${hist.map(h=>`<tr><td class="n">${h.revision}</td><td class="small">${esc(h.recorded_at)}</td><td>${esc(h.state)}</td><td class="n">${h.supersedes===null?'-':h.supersedes}</td><td class="small">${esc(h.note||'')}</td></tr>`).join('')}</tbody></table></div><button class="button" id="reopen-prev">Reopen the previous revision into the scenario</button>`:'<p class="small">No revision yet. Save one to start the history.</p>'}</div>
  </div></div>`;
}
function render(){
  const c=current();
  const ctx=context();
  $('#market').value=state.market;
  $('#case-list').innerHTML=ordered.map(id=>D.cases.find(x=>x.id===id)).filter(Boolean).filter(x=>state.market==='all'||x.market===state.market).map(x=>{const m=x.comparisons[x.defaultCompare];return `<button class="case-card ${c.id===x.id?'active':''}" data-case="${x.id}" aria-pressed="${c.id===x.id}"><div class="card-meta"><span>${esc(x.customer)}</span><span>${x.defaultCompare==='annual'?'Full year':'Matched H1'}</span></div><div class="case-name">${esc(x.name)}</div><div class="pn">${x.pn}</div><div class="case-amount ${color(m.revenueDelta)}">${signedEUR(m.revenueDelta)}</div><div class="case-period">ISZE billing &middot; ${esc(m.label)}</div><div class="case-direction">${x.id==='IMOTORS-OIL'?'&nearr;':'&rarr;'} ${esc(x.actionType)}</div></button>`;}).join('');
  $('#case-header').innerHTML=`<div class="head-line"><div><div class="eyebrow">${esc(c.customer)} &middot; ${esc(c.category)} &middot; ${c.pn}</div><span class="badge ${c.id==='IMOTORS-OIL'?'hold':'review'}">${esc(c.actionType)}</span></div><div class="head-right"><button class="button secondary" id="export-review">Export case review</button></div></div><h2>${esc(c.action)}</h2><p>${esc(c.verdict)}</p>`;
  $('#scope-strip').innerHTML=`<div><span>Customer / scope</span>${esc(c.customer)} &middot; ${ctx.scope==='dealer'?`dealer scope, ${(ctx.dealer_selector||[]).length} dealer(s) listed${ctx.selected_dealer?' &middot; selected '+esc(ctx.selected_dealer):''}`:'distributor, not dealer'}</div><div><span>Selected comparison</span>${esc(c.comparisons[state.compare].label)}</div><div><span>Basis / reporting clocks</span>ISZE net EUR; separate onward quantities</div><div><span>Historical fleet context</span>${ctx.fleet_denominator?`${num(ctx.fleet_denominator.value)} market ${ctx.fleet_denominator.market==='ITUK'?'trucks':'vehicles'}, 2025 &middot; part fleet unknown`:'No fleet stated for this market'}</div>`;
  /* The status words in this strip are read from the payload and from the count
     of review findings the payload actually carries. They used to be literals,
     including a fixed "10 review findings" that no longer described the file. */
  const packAudit=D.packAudit||{};
  const findings=(packAudit.issues||[]).length;
  const turboHere=turboFor(c),meta=currentMetadata(c);
  const listStatus=meta.list_price_status,listClass=turboHere?'fact':'review';
  $('#pack-status').innerHTML=`<span><b>${esc((D.meta&&D.meta.version)||'Version not declared')}</b> &middot; ${esc(packAudit.acceptedStatus||'acceptance state not declared')}</span>`
    +`<span class="badge ${listClass}">List: ${esc(listStatus)}</span>`
    +`<span>Cost: ${esc(meta.cost_status)} &middot; not approved</span>`
    +`<button class="sourcesbutton" data-sources>${findings} review finding${findings===1?'':'s'} in the payload</button>`;
  /* The payload version, exposed on a chrome element so a check can assert that
     the page and the payload agree without scraping a styled span. */
  $('#pack-status').setAttribute('data-payload-version',String((D.meta&&D.meta.version)||'not declared'));
  $('#pack-status').setAttribute('data-metadata',JSON.stringify(meta));
  $('#tabs').innerHTML=views.map(k=>`<button class="tab ${state.view===k?'active':''}" role="tab" aria-selected="${state.view===k}" data-view="${k}">${(TAB_LABELS.find(t=>t[0]===k)||[k,k])[1]}</button>`).join('');
  /* A view that fails must never leave the previous view's content underneath a
     newly selected tab (F05). */
  /* F05. The old content is cleared and the region marked before the view is
     built, so a view that fails can never leave the previous tab's content on
     screen under a newly active tab. The failure card names the failing view. */
  let html=null,failed=false;
  const content=$('#content');
  if(content){content.setAttribute('data-render-state','building');content.innerHTML='';}
  try{
    html=state.view==='decision'?decision(c):state.view==='position'?position(c):state.view==='objectives'?objectives(c):state.view==='economics'?economics(c):state.view==='candidates'?candidatesView():state.view==='case'?caseView():actionView();
    if(typeof html!=='string'||!html.trim()){
      html=viewErrorPanel(state.view,new Error('The view returned no content.'));failed=true;
    }else{
      /* REVIEW-04: the exact part reference is carried at the head of every view,
         so the gate below cannot pass a view that has lost it. The selected-part
         review is described by the part being reviewed, not by the open case, so
         its anchor is the routed reference. A review with nothing selected has no
         reference to carry and states that in an amber block. */
      const reviewing=state.view==='case'&&state.partRoute;
      /* Only the selected-part review can be showing a different part. On that
         view, and only there, the button that would open one part inside the
         review of another is removed: a view of a different part is reachable by
         pressing the first business action on that view, never by the browser's
         own history or a reload. */
      if(state.view==='case'&&!reviewing)html=html.replace(/(<button[^>]*data-open-part="[^"]*"[^>]*>[\s\S]*?<\/button>)/g,'');
      const anchor=(reviewing?state.partRoute.partNumber:c.pn)||null;
      html=partStrip(reviewing?partRouteSummary(state.partRoute.partNumber):c)+html;
      if(!reviewing)html=contextStrip(ctx)+html;
      if(anchor&&!html.includes(anchor)){
        html=viewErrorPanel(state.view,new Error('The built view does not carry the exact part reference '+anchor+', so it is not shown.'));failed=true;
      }else{
        const banned=bannedWords(html);
        if(banned.length){
          html=viewErrorPanel(state.view,new Error('The built view contains wording a reader must not see: '+banned.map(b=>'"'+b.word+'" ('+b.why+')').join(', ')+'.'));failed=true;
        }
      }
    }
  }catch(err){
    html=viewErrorPanel(state.view,err);failed=true;
  }
  if(content){
    content.innerHTML=html;
    content.setAttribute('data-render-state',failed?'failed':'built');
  }
  const rs=$('#render-status');
  if(rs){
    rs.textContent=failed
      ? 'The '+(TAB_LABELS.find(t=>t[0]===state.view)||[state.view,state.view])[1]+' view failed to build. Nothing from another view is shown.'
      : (TAB_LABELS.find(t=>t[0]===state.view)||[state.view,state.view])[1]+' built for '+state.caseId+'.';
    rs.setAttribute('data-failed',failed?'true':'false');
  }
  $('#error-detail')?.addEventListener('click',()=>{const d=$('#error-detail-body');if(d)d.style.display=d.style.display==='none'?'block':'none';});
  $('#reload-view')?.addEventListener('click',()=>render());
  /* UX-07. A table wider than its column scrolls sideways inside its own
     wrapper. That wrapper is reachable by tab and named, so a keyboard reader
     can move it; a scroll box the keyboard cannot reach is a hidden control
     under another name. Where the view provides a heading or a summary that owns
     the table, the label says which table it is, not only that it scrolls. */
  $$('.tablewrap').forEach(w=>{
    if(w.scrollWidth<=w.clientWidth)return;
    if((w.getAttribute('aria-label')||'')!=='Scrollable table'){
      /* closest() and parentElement are read defensively: the module suites run
         this file in a stub document whose elements have neither, and a helper
         that throws there would take every view down with it. */
      const owner=(typeof w.closest==='function'?w.closest('.panel,.grid2,.grid3,.split,details'):null)||w.parentElement||null;
      const head=owner&&(owner.querySelector('h3,summary,h2,h4')||owner.querySelector('.eyebrow'));
      const text=head&&String(head.textContent||'').replace(/\s+/g,' ').trim();
      if(text)w.setAttribute('aria-label','Scrollable table: '+text.slice(0,90));
    }
  });
  bind();
}
function viewErrorPanel(view,err){
  const label=(TAB_LABELS.find(t=>t[0]===view)||[view,view])[1];
  const currentCaseId=state.caseId,currentCaseName=(current()||{}).name||null;
  const name=(err&&(err.name||(err.constructor&&err.constructor.name)))||'Error';
  const message=(err&&err.message)||String(err||'The view produced no content.');
  const kind=/ReferenceError/.test(name)?'a name the view referenced does not exist in scope'
    :/TypeError/.test(name)?'a value the view used was not the shape it expected'
    :/SyntaxError/.test(name)?'the view source could not be parsed'
    :/is not a function/.test(message)?'a helper the view called is not available in this build'
    :'the view stopped with an error';
  const stack=(err&&err.stack)?String(err.stack).split('\n').slice(0,6).join('\n'):null;
  return `<div class="panel warn error-msg render-failure" role="alert" data-failed-view="${esc(view)}">
  <div class="eyebrow">This view failed to build</div>
  <h3>${esc(label)} did not render</h3>
  <p><b>${esc(name)}:</b> ${esc(message)}</p>
  <p class="small">The page has not shown the previous tab's content in its place, because that would leave evidence on screen that does not belong to the tab you selected. Nothing from another view is being shown.</p>
  <div class="evidence-line"><span>Failing view</span><b>${esc(view)}</b></div>
  <div class="evidence-line"><span>Case</span><b>${esc(currentCaseId||'none')}${currentCaseName?' &mdash; '+esc(currentCaseName):''}</b></div>
  <div class="evidence-line"><span>What kind of failure</span><b class="small">${esc(kind)}</b></div>
  <div class="ruleline"><b>This is what you can do</b><p class="small">Build this view again &middot; open a different view for the same case &middot; open a different case</p></div>
  <div class="rowactions"><button class="button" id="reload-view">Build this view again</button><button class="button" data-view="decision">Go to Sales evidence</button></div>
  ${stack?`<p class="small"><button class="linkbutton" id="error-detail">Technical detail for a developer</button></p><pre class="small" id="error-detail-body" style="display:none;white-space:pre-wrap">${esc(stack)}</pre>`:''}</div>`;
}
function collectReview(c){
  /* A blank next-update date is `null`, not the empty string. `''` fails the
     record's own check ("next_update_due must be YYYY-MM-DD or null") on the
     second save of a case with no due date, so the field is normalised here. */
  const due=($('#a-due')?$('#a-due').value:'').trim();
  return {owner_role:$('#a-owner')?$('#a-owner').value:null,
    next_update_due:due===''?null:due,
    state:$('#a-status')?$('#a-status').value:'draft',
    next_action:$('#a-next')?$('#a-next').value:null,
    explanation:$('#a-explanation')?$('#a-explanation').value:'',
    note:$('#a-note')?$('#a-note').value:(c?c.recommendation:''),
    outcome:$('#a-outcome')?$('#a-outcome').value:''};
}
/* UX-06. A refused save keeps what was typed, so a later repaint shows the
   unsaved entries rather than the last saved revision. */
function keepUnsaved(c,review){state.unsavedReview[c.id]=review;}
function saveCase(){
  const c=current(),r=caseResult(),s=scenario();
  const review=collectReview(c);
  const consistency=store.consistency(c.id);
  if(!consistency.ok){
    keepUnsaved(c,review);
    toast('Not saved: the ranked option and the working record disagree.');
    return;
  }
  const existing=repo.load(c.id);
  if(!r.ok){
    keepUnsaved(c,review);
    toast('Not saved: the scenario is not calculated. '+r.error);
    return;
  }
  const res=repo.save(c.id,{scenario:s,result:r,part_number:c.pn,review:review,consistency:consistency},
    {expected_version:existing?existing.version:0,state:review.state,owner_role:review.owner_role,
     next_action:review.next_action,next_update_due:review.next_update_due,recorded_by:'internal user'});
  if(res.ok){
    delete state.unsavedReview[c.id];
    $('#save-status').textContent=res.durable
      ? `Saved as revision ${res.version}. Nothing was overwritten.`
      : `Saved as revision ${res.version} for this session only. Use the recovery bundle before closing.`;
    toast(res.durable?`Revision ${res.version} saved.`:'Saved for this session only.');
    render();
  }else{
    keepUnsaved(c,review);
    $('#save-status').textContent=res.conflict?`Not saved. ${res.error}`:`Not saved. ${res.error}`;
    toast(res.conflict?'Someone else changed this case. Reload first.':'Not saved.');
  }
}

/* ----------------------------------------------------------------- exports */
function download(name,content,mime){const blob=new Blob([content],{type:mime}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function caseObjectForExport(c){return {case_id:c.id,customer:c.customer,market:c.market,
  part_number:c.pn,unit:c.unit,description:(c.packEvidence.parts||{}).aim_l3||c.name,
  title:c.name,version:1,state:(repo.load(c.id)||{}).state||'draft',
  owner_role:(repo.load(c.id)||{}).owner_role||c.owner};}
function exportInternal(){
  const c=current(),r=caseResult(),s=scenario();
  const existing=repo.load(c.id);
  const review=existing?existing.revisions[existing.revisions.length-1].record.review:collectReview(c);
  const exported=X.internalRecord(caseObjectForExport(c),s,r,{exported_at:new Date().toISOString(),
    review:review,sources:s.sources,history:existing?repo.history(c.id):[],metadata:currentMetadata(c)});
  download(`${c.customer.replaceAll(' ','_')}_${c.pn}_Internal_Record.json`,JSON.stringify(exported.payload,null,2),'application/json');
  toast('Internal record exported. Audience: ISZE internal only.');
}
function exportMember(){
  const c=current(),r=caseResult(),s=scenario();
  if(!r.ok){toast('Not exported: the scenario is not calculated.');return;}
  const exported=X.memberBrief(caseObjectForExport(c),s,r,{exported_at:new Date().toISOString(),
    request_note:$('#a-next')?$('#a-next').value:null});
  const bytes=X.toBytes(exported,true);
  if(!exported.audit.ok){
    toast('Not exported: the brief failed its own content check ('+exported.audit.findings.join(', ')+').');
    return;
  }
  download(`${c.customer.replaceAll(' ','_')}_${c.pn}_Participant_Brief.json`,bytes.text,'application/json');
  toast('Participant brief built from permitted fields only; content check clean.');
}
function exportBundle(){
  const bundle=repo.exportAll();
  download(`ISZE_AIM_Cases_Recovery_${new Date().toISOString().slice(0,10)}.json`,
    JSON.stringify(bundle,null,2),'application/json');
  toast('Recovery bundle written: '+Object.keys(bundle.cases).length+' case record(s).');
}
function exportReview(){
  const c=current(),r=caseResult(),s=scenario();
  const evidence=Object.values(c.comparisons).map(m=>`<tr><td>${esc(m.label)}</td><td>${eur(m.prior.eur,2)}</td><td>${eur(m.current.eur,2)}</td><td>${signedEUR(m.revenueDelta)}</td><td>${pct(m.onwardChangePct)}</td></tr>`).join('');
  const rows=c.series.filter(x=>x.billingEUR!==null||x.onwardQuantity!==null).map(x=>`<tr><td>${esc(x.period)}</td><td>${num(x.billingQuantity)}</td><td>${eur(x.billingEUR,2)}</td><td>${eur(x.price,2)}</td><td>${num(x.onwardQuantity)}</td><td>${esc(x.billingState)} / ${esc(x.onwardState)}</td></tr>`).join('');
  const text=`<!doctype html><html lang="en"><meta charset="utf-8"><title>${esc(c.customer)} - ${c.pn} - internal pricing review</title><style>body{font:14px/1.5 Segoe UI,Arial,sans-serif;color:#15344b;max-width:1100px;margin:35px auto;padding:0 25px}h1{font-size:28px}h2{font-size:20px;margin-top:28px}table{border-collapse:collapse;width:100%;font-size:12px}th,td{padding:8px;border-bottom:1px solid #d8e1e8;text-align:left;vertical-align:top}th{background:#eff4f8}aside{background:#fff5e3;padding:15px}a{color:#226c98}footer,.small{font-size:11px;color:#53697a}pre{white-space:pre-wrap;font:inherit}.n{text-align:right}</style><body><p>ISZE INTERNAL ONLY | ${esc(D.meta.version)}</p><h1>${esc(c.customer)} - ${esc(c.name)}</h1><p><b>${c.pn} | ${esc(c.category)}</b></p><h2>${esc(c.action)}</h2><p>${esc(c.verdict)}</p><aside>No confirmed price-caused lost-sales amount and no current net-price approval. No supplier purchase cost and no ISZE margin are stated in a participant-facing brief. Manual inputs remain assumptions.</aside><h2>Measured commercial evidence</h2><table><tr><th>Comparison</th><th>Prior ISZE EUR</th><th>Later ISZE EUR</th><th>Change</th><th>Onward quantity change</th></tr>${evidence}</table><p>${esc(c.reason)}</p><h2>Counter-evidence</h2><p>${esc(c.counter)}</p><p>${esc(c.application)}</p>${snapshotPanel(c)}<h2>Scenario (not a forecast or approval)</h2>${r.ok?`<p>Eligible quantity ${num(r.quantity_before,0)} units at EUR ${num(r.price_before,2)}. Proposed net price ${eur(r.price_after,2)}; scope ${esc(r.scope)}; volume basis ${esc(r.quantity_label)}. Evidence period ${esc(r.evidence_period||'not stated')}; offer effective date ${esc(r.offer_effective_date||'not set')} on cost basis ${esc(r.cost_basis_id||'not set')}. Revenue change ${signedEUR(r.revenue_change)}. Gross-profit change: ${r.gp_change===null?'not calculated; no verified parts purchase cost':signedEUR(r.gp_change)}. Support ${eur(r.support_eur)}, counted once. Offer gross margin after ${r.margin_after_pct===null?'not calculated':num(r.margin_after_pct,1)+'%'}; unit margin on the proposed price ${r.margin_unit_after_pct===null?'-':num(r.margin_unit_after_pct,1)+'%'}.</p><p class="small">Profit bridge: ${signedEUR(r.bridge_revenue_change)} revenue &minus; ${eur(r.bridge_cost_change)} cost &minus; ${eur(r.bridge_support_eur)} support = ${signedEUR(r.gp_change)} ${r.bridge_reconciles?'(reconciles)':'(DOES NOT RECONCILE)'}.</p>`:`<p>${esc(r.error)}</p>`}<h2>Exact-part monthly aggregates</h2><p>Flows remain separate. An absent recorded line is not proof of zero customer demand.</p><table><tr><th>Month</th><th>ISZE units</th><th>ISZE EUR</th><th>Observed EUR/unit</th><th>Onward units</th><th>Recorded states</th></tr>${rows}</table><footer>Remains internal. Contains no participant-facing brief, no raw invoices and no full price list.</footer></body></html>`;
  download(`${c.customer.replaceAll(' ','_')}_${c.pn}_Pricing_Review.html`,text,'text/html');
  toast('Internal case review exported.');
}
function sourcesModal(){
  const a=D.packAudit,node=document.createElement('div');node.className='screen-overlay';
  node.innerHTML=`<section class="modal" role="dialog" aria-modal="true" aria-label="Source and engine basis"><div class="modal-head"><div><div class="eyebrow">Accepted subset, not blanket approval</div><h2>What this component's evidence does and does not establish</h2></div><button class="button" id="close-modal">Close</button></div><div class="panel good"><b>Price history, selected competitor observations and catalogue relationships are connected.</b><p class="small">The same five cases and their measured baseline remain. The parts purchase cost is dated and named by basis; it is not promoted to an accounting cost. An archive cross-reference is not promoted to a comparable quotation.</p></div><p><b>${num(a.offerScope.rows)}</b> archive records were inspected; <b>${num(a.offerScope.exactCaseRows)}</b> directly reference the five selected part numbers. Related or unrelated archive rows are not silently attached to a case.</p><p class="small">Source: ${esc(a.inputFile)}. SHA-256: ${esc(a.inputSHA256)}.</p>${(a.issues||[]).map(i=>`<div class="source-row"><span class="badge review">${esc(i.id)} &middot; ${esc(i.severity)}</span><h3>${esc(i.title)}</h3><p>${esc(i.finding)}</p><p><b>Handling:</b> ${esc(i.handling)}</p><code>${esc(i.source)}</code></div>`).join('')}<h3>Source inventory</h3>${D.sources.map(s=>`<div class="source-row"><b>${esc(s.title)} <span class="badge fact">${esc(s.kind)}</span></b><span class="small">${esc(s.date)}</span><p style="margin:6px 0">${esc(s.basis)}</p><code>${esc(s.file)}</code></div>`).join('')}<h3>Boundaries</h3><p>A billing fall is not proof of price-caused lost sales. National purchasing does not identify a dealer. No approved margin floor or cost is assumed. This internal file contains both pilot accounts; filtering is not access control.</p></section>`;
  document.body.append(node);$('#close-modal').onclick=()=>node.remove();
  node.onclick=e=>{if(e.target===node)node.remove();};
  node.onkeydown=e=>{if(e.key==='Escape')node.remove();};$('#close-modal').focus();
}

/* -------------------------------------------------------------------- bind */
function bind(){
  $$('[data-case]').forEach(el=>el.onclick=()=>route({caseId:el.dataset.case,viewError:null}));
  $$('[data-view]').forEach(el=>el.onclick=()=>route({view:el.dataset.view,viewError:null}));
  $$('[data-select]').forEach(el=>el.onclick=()=>{
    const res=store.selectAlternative(current().id,el.dataset.select);
    if(!res.ok){toast(res.error);return;}
    if(res.migration_unresolved){toast('Selected. The product migration stays financially unresolved.');}
    else{toast('Selected: '+(res.alternative.name||res.alternative.alternative_id));}
    route({view:'objectives',viewError:null});
  });
  $$('[data-sources]').forEach(el=>el.onclick=sourcesModal);
  $('#toggle-billing-metric')?.addEventListener('click',()=>{state.billingMetric=state.billingMetric==='billingEUR'?'billingQuantity':'billingEUR';render();});
  $('#comparison')?.addEventListener('change',e=>route({compare:e.target.value}));
  $$('.month-hit').forEach(el=>{const fn=()=>{const t=$('#readout-'+el.dataset.chart);if(t)t.textContent=el.dataset.readout;};
    el.onclick=fn;el.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();fn();}};});
  const osel=document.getElementById('objective');
  if(osel)osel.onchange=e=>{state.objective=e.target.value;render();};
  $('#reload-view')?.addEventListener('click',()=>render());
  if(state.view==='economics'){
    const fieldMap=[['s-baseP','price_before'],['s-newP','price_after'],['s-baseQ','quantity_before'],
      ['s-support','support_eur'],['s-pack','pack_size']];
    fieldMap.forEach(([id,key])=>{
      const el=$('#'+id); if(!el)return;
      el.addEventListener('input',()=>{
        try{
          const raw=el.value;
          store.set(state.caseId,{[key]:raw===''?null:Number(raw)});
          $('#economic-results').innerHTML=economicsResults();
          const v=$('#scenario-version'); if(v)v.textContent='Scenario version '+scenario().version+'. Every change updates this one record, which is what the ranking, the save and the exports read.';
        }catch(err){toast(err.message);}
      });
    });
    const qty=$('#s-qty');
    if(qty)qty.addEventListener('input',()=>{try{
      store.set(state.caseId,{quantity_after:qty.value===''?null:Number(qty.value)});
      $('#economic-results').innerHTML=economicsResults();}catch(err){toast(err.message);}});
    const cost=$('#s-cost');
    if(cost)cost.addEventListener('input',()=>{try{
      store.set(state.caseId,{cost_eur:cost.value===''?null:Number(cost.value),cost_basis_source:'stated assumption'});
      $('#economic-results').innerHTML=economicsResults();}catch(err){toast(err.message);}});
    const scope=$('#s-scope');
    if(scope)scope.addEventListener('change',()=>{try{
      store.set(state.caseId,{scope:scope.value});
      $('#economic-results').innerHTML=economicsResults();}catch(err){toast(err.message);}});
    const basis=$('#s-basis');
    if(basis)basis.onchange=()=>{try{
      const rec=E.costRecord(D,current().pn,basis.value);
      store.set(state.caseId,{cost_basis_id:basis.value,cost_eur:rec?rec.cost_eur:null,
        cost_basis_source:rec?'verified record':'no verified cost held'});
      render();}catch(err){toast(err.message);}};
    const dateEl=$('#s-date');
    if(dateEl)dateEl.addEventListener('change',()=>{try{
      const val=dateEl.value;
      if(val){
        const check=E.costForDate(D,current().pn,val);
        if(!check.resolved){toast(check.error);}
      }
      store.set(state.caseId,{offer_effective_date:val||null});
      render();}catch(err){toast(err.message);}});
    const period=$('#s-period');
    if(period)period.addEventListener('input',()=>{try{
      store.set(state.caseId,{evidence_period:period.value});}catch(err){toast(err.message);}});
    const label=$('#s-label');
    if(label)label.addEventListener('input',()=>{try{
      store.set(state.caseId,{quantity_label:label.value,volume_is_observed:label.value==='observed history'});
      $('#economic-results').innerHTML=economicsResults();}catch(err){toast(err.message);}});
    const reset=$('#reset-scenario');
    if(reset)reset.onclick=()=>{store.set(state.caseId,store.defaults(state.caseId));render();toast('Reset to the unchanged offer.');};
  }
  if(state.view==='candidates'){
    const q=$('#candidate-search'),dist=$('#c-dist'),ev=$('#c-ev'),size=$('#c-size');
    let debounce=null;
    if(q)q.addEventListener('input',()=>{clearTimeout(debounce);debounce=setTimeout(()=>{
      state.candidateQuery=q.value;state.candidatePage=1;render();
      const nq=$('#candidate-search');if(nq){nq.focus();nq.setSelectionRange(nq.value.length,nq.value.length);}},350);});
    if(dist)dist.onchange=()=>{state.candidateCriteria.distributor=dist.value||undefined;state.candidatePage=1;render();};
    if(ev)ev.onchange=()=>{
      state.candidateCriteria={};if(dist&&dist.value)state.candidateCriteria.distributor=dist.value;
      if(ev.value)state.candidateCriteria[ev.value]=true;state.candidatePage=1;render();};
    if(size)size.onchange=()=>{state.candidatePageSize=Number(size.value);state.candidatePage=1;render();};
    $('#c-clear')?.addEventListener('click',()=>{
      state.candidateQuery='';state.candidateCriteria={};state.candidatePage=1;render();});
    /* Every pager control carries the page it goes to, so the counter can never
       print a reversed range such as "Rows 1 to 0 of 0". */
    $$('[data-page]').forEach(el=>el.addEventListener('click',()=>{
      state.candidatePage=Number(el.dataset.page)||1;render();}));
    $('#c-last')?.addEventListener('click',()=>{
      state.candidatePage=candidateState().page.page_count;render();});
    $$('[data-sort]').forEach(el=>el.addEventListener('click',()=>{
      const key=el.dataset.sort;
      const dir=(state.candidateSortKey===key&&state.candidateSortDirection==='desc')?'asc':'desc';
      state.candidateSortKey=key;state.candidateSortDirection=dir;state.candidatePage=1;render();}));
  }
  /* F10: a candidate row routes to that exact part, and a part with no worked
     case opens its own review rather than borrowing a case's numbers. */
  $$('[data-open-part]').forEach(el=>el.addEventListener('click',()=>{
    const pn=el.dataset.openPart;
    const worked=(D.cases||[]).find(x=>x.pn===pn);
    if(worked){route({caseId:worked.id,view:'decision',partRoute:null});return;}
    const found=C.search(D.candidateScreen||[],pn).filter(r=>r.part_number===pn);
    if(!found.length){toast('No screened row carries part number '+pn+'.');return;}
    route({partRoute:{partNumber:pn},view:'case'});}));
  $$('[data-open-case]').forEach(el=>el.addEventListener('click',()=>{
    route({caseId:el.dataset.openCase,view:'decision',partRoute:null});}));
  if(state.view==='action'){
    $('#save-case')?.addEventListener('click',saveCase);
    $('#export-json')?.addEventListener('click',exportInternal);
    $('#export-member')?.addEventListener('click',exportMember);
    $('#export-bundle')?.addEventListener('click',exportBundle);
    $('#export-review-body')?.addEventListener('click',exportReview);
    $('#reopen-prev')?.addEventListener('click',()=>{
      const existing=repo.load(current().id);
      if(!existing||existing.revisions.length<2){toast('There is no earlier revision to reopen.');return;}
      const prev=existing.revisions[existing.revisions.length-2];
      const patch={};
      Object.keys(prev.record.scenario||{}).forEach(k=>{if(CT.SCENARIO_FIELDS.indexOf(k)>=0)patch[k]=prev.record.scenario[k];});
      try{store.set(state.caseId,patch);toast('Revision '+prev.revision+' reopened into the scenario.');render();}
      catch(err){toast(err.message);}
    });
  }
  const ex=$('#export-review');
  if(ex)ex.addEventListener('click',exportReview);
}

/* ------------------------------------------------------------------ routes */
function readHash(){
 const h=new URLSearchParams(location.hash.replace(/^#/,''));
 if(D.cases.some(c=>c.id===h.get('case')))state.caseId=h.get('case');
 state.view=views.includes(h.get('view'))?h.get('view'):'decision';
 state.compare=['half','annual'].includes(h.get('compare'))?h.get('compare'):current().defaultCompare;
  /* The address carries the case, the tab and the comparison period. It does not
     carry a selected part, so a part selection must be cleared as soon as the
     reader leaves the selected-part review - otherwise the previous part's rows
     could be shown under a different tab. It is deliberately NOT cleared while
     the review itself is on screen: opening a part writes the address, and the
     address change re-enters here. */
  if(state.view!=='case')state.partRoute=null;
}
function route(p){state={...state,...p};const hash=new URLSearchParams({case:state.caseId,view:state.view,compare:state.compare}).toString();if(location.hash.slice(1)!==hash)location.hash=hash;else render();}
function toast(t){const n=document.createElement('div');n.className='toast';n.textContent=t;document.body.append(n);setTimeout(()=>n.remove(),3500);}
$('#market').onchange=e=>{state.market=e.target.value;const list=D.cases.filter(c=>state.market==='all'||c.market===state.market);if(!list.some(c=>c.id===state.caseId)){route({caseId:list[0].id});}else render();};
$('#sources-top').onclick=sourcesModal;
/* Reopen: the working scenario is the last saved revision, not a fresh default.

   Two faults stopped that, and both are fixed here.

   1. Ordering. This block used to run before readHash(), so it read the case id
      from the hardcoded initial state rather than from the address, looked in the
      wrong case, found nothing and silently showed a fresh default.

   2. The restore was expressed as an edit. It collected the saved values into a
      patch and handed them to store.set(). set() is an edit path: it diffs the
      patch, and for any difference it bumps the version and re-derives the record
      id ("<case>:v<n+1>"). A restore is not an edit. The page therefore ended up
      in a third state - not the saved revision, not a default - and the reopened
      action tab reported scenario ITUK-PADS:v2 while the revision on disk, and
      the one both results had been calculated from, was v3. Measured on all five
      cases: matches_saved_revision false, matches_a_fresh_default false.

   restoreSavedScenario() writes the saved revision onto the working record with
   its own version and record id intact, carrying only fields the scenario
   contract declares. Reopening is the only thing that calls it: a case switch
   inside a live session deliberately leaves any unsaved edit alone.

   It runs AFTER readHash(), because the case id comes from the address. */
function restoreSavedScenario(caseId){
  const existing=repo.load(caseId);
  if(!existing||!existing.revisions||!existing.revisions.length)return false;
  const saved=(existing.revisions[existing.revisions.length-1].record||{}).scenario;
  if(!saved||typeof saved!=='object')return false;
  const target=store.get(caseId);
  let carried=0;
  Object.keys(saved).forEach(k=>{
    if(CT.SCENARIO_FIELDS.indexOf(k)<0)return;
    target[k]=saved[k];carried++;
  });
  return carried>0;
}
readHash();
restoreSavedScenario(state.caseId);
window.addEventListener('hashchange',()=>{readHash();state.viewError=null;render();});
render();
window.AIMPricing={data:D,engine:E,export:X,candidates:C,cases:repo,contracts:CT,scenario:store,
  render:()=>render(),
  /* The QA sweep and the ux_flow checks drive the shipped layer through these.
     openPart is the one candidate-route entry point the retired shell had; it is
     ported rather than re-implemented beside the click handler. */
  openPart:(partNumber)=>{
    const worked=(D.cases||[]).find(x=>x.pn===partNumber);
    if(worked){route({caseId:worked.id,view:'decision',partRoute:null});
      return {ok:true,view:'decision',case_id:worked.id};}
    const found=C.search(D.candidateScreen||[],partNumber).filter(r=>r.part_number===partNumber);
    if(!found.length)return {ok:false,error:'No screened record carries part number '+partNumber+'.'};
    route({partRoute:{partNumber},view:'case'});
    return {ok:true,view:'case',part_number:partNumber,rows:found.length};
  },
  openCase:caseId=>route({caseId,view:'decision',partRoute:null}),
  go:patch=>route(patch),
  /* The candidate screen's search is state, not an action, and the QA probe has
     no live input element to type into. This writes the same field the input
     handler writes; it is not a second search path. */
  setCandidateQuery:(q)=>{state.candidateQuery=String(q||'');state.candidatePage=1;render();},
  getState:()=>({...state}),getScenario:()=>store.get(state.caseId),getContext:()=>context(),
  getResult:()=>store.calculate(state.caseId),
  /* UX-03. The assumptions behind the visible results, and the per-field
     verdict, both read from the one working record. */
  assumptions:()=>assumptionTrace(),
  fieldIssues:()=>fieldIssues(),
  sensitivity:()=>store.sensitivity(state.caseId),
  /* UX-08. Older local notes migrate onto an explicit legacy basis. */
  migrateLegacyCases:()=>repo.migrateLegacyCases(),
  /* Test-only: make the tabs reachable when the shell's own tab bar is not
     rendered by the harness. It sets the one state field the router reads. */
  setView:v=>{state.view=v;},
  selectAlternative:id=>store.selectAlternative(state.caseId,id),
  consistency:()=>store.consistency(state.caseId),
  setScenario:patch=>store.set(state.caseId,patch)};
})(typeof globalThis!=='undefined'?globalThis:this);
</script>
