# IDS network atlas — concept saved

**Saved:** 2026-09-20 · **Internal / private**
**Source:** a ChatGPT proposal Jerome pasted in full on 2026-09-20 and asked to keep.
**Fidelity:** the ten ideas and the closing recommendation are kept as written. The inline source
markers ChatGPT used to point back at the IDS file it had inspected were stripped, because they mean
nothing outside that chat. Nothing here was checked against our data.

**Status: idea capture only.** No inspection has been done, no source has been confirmed, and this
is not a roadmap entry. Two of the numbers it quotes (564 dealer records, 196 checklist questions)
are ChatGPT's own read of the IDS build and are not verified here. The file it inspected is
`02_dashboards\ids\IDS_2026_dealer_compare.html`.

---

## The shape of the proposal

Distributors become the anchors of the experience, not another set of dots on the map. Four
questions run in one continuous view:

**Where is our network? What can it do? How is the parts business performing? What should ISZE and
the distributor do next?**

The IDS file is a substantial starting point: it contains 564 dealer records, 196 checklist
questions and the five A–E sections, with question-level results, benchmarks and geographic
information. *Records* deliberately: the file includes both Benelux and individual-country views, so
that headline should not automatically become a count of distinct physical dealerships.

The checklist already asks about product categorisation, sales channels, inventory performance and
lost sales. Those are natural connections to the parts and sales dashboards, not connections we
would have to invent.

The exact current sales/AIM dashboard build and its available data joins still need confirmation
from Cursor.

---

## 1. A network atlas that opens from ISZE into distributors and dealers

**The experience:** a full-screen, carefully styled map of the distributor network. Select one
distributor and its dealer network unfolds while the rest of Europe recedes.

Distributor headquarters get a distinct symbol; parts warehouses another; dealer sites stay smaller
points. The distinction matters: the distributor office is not necessarily where parts are supplied
from.

At the widest view, distributor-level information: ISZE billing, performance against target,
relevant UIO, IDS assessment coverage, and the spread of dealer scores. Zoom in and the information
becomes dealer-level capabilities and exceptions. Select a dealer and a side panel opens **without
removing the map or losing the selected distributor**. The panel keeps the distributor's commercial
context above the dealer's own IDS profile, and adds dealer sales data separately where it exists.

The visual highlight: the distributor's network appearing through restrained connecting curves.
Those curves mean **network responsibility**, unless actual shipment data supports a logistics
reading. No permanently animated spaghetti across Europe.

A small overview, breadcrumbs and "Show entire network" keep orientation.

**Why useful:** you go straight from "this distributor needs attention" to "these are the network
weaknesses worth discussing".

**Data needed:** a distributor register, headquarters and warehouse locations, and a verified
distributor–dealer–site relationship. Country alone is not a sufficient join — our file
distinguishes UK CV from UK LCV and UMI from UTI.

## 2. Geography and the AIM parts universe become two views of one selection

The connection to the Parts Atlas concept. The screen splits between geographic network and parts
portfolio. Select **Braking** and the map changes to braking performance. Select a distributor and
the parts universe reshapes to that distributor's family mix. Zoom into brake pads, pick a part
number, open its history — with distributor, period and geography still selected.

It works both ways:

> Start with a weak distributor and find the product families behind its decline.
> Start with a weak family and find the distributors behind its decline.

IDS sits alongside as an **operating-practice lens**: the selected distributor's dealers show their
recorded results on category management, fast-moving-parts ordering and lost-sales tracking. Those
practices are explicitly in the checklist.

The visual moment is not a new chart opening; it is both views reacting as one system — selected
parts stay highlighted, related distributors become prominent, unrelated information fades.

**The boundary:** an IDS stock-management result gives context, not proof it caused a braking-sales
decline.

**Data needed:** PN-to-AIM mapping, ISZE-to-distributor sales, distributor identifiers and — where
available — sales-to-dealer. Without that last source the drill stops at distributor level rather
than inventing dealer allocations.

## 3. Watch the map rearrange itself into a performance chart

Press **"Compare performance"** and the same points lift off their geographic positions and
rearrange onto labelled axes.

Distributor view: horizontal axis a defined Parts IDS measure across the assessed network, vertical
axis a commercial measure such as sales against target or a validated GPS measure. Dealer view:
actual dealer-level measures only — for example DB-to-dealer parts purchases per relevant vehicle,
where both numerator and denominator exist.

Geography becomes business comparison. You can see entities with strong recorded practices but weak
commercial performance, entities performing well despite process weaknesses, and entities weak on
both.

Select a point and its original location stays visible in a miniature map. Press "Geography" and
everything returns.

**Why it is more than animation:** it helps the viewer recognise that the entity examined
geographically is the same entity in the comparison.

A benchmark selector compares within a distributor, a vehicle segment or a genuinely comparable peer
group. A national average stays a labelled reference, not an implied compliance threshold.

**Data needed:** reliable joins and compatible measurement periods. Start at DB level where that is
the trustworthy commercial grain. The animation needs stable entity identities; it must never make
one dealer appear to become another.

## 4. A dealer X-ray instead of another radar chart

A **high-quality isometric cutaway of a dealership** — not a decorative truck rotating in space. A
navigable schematic with recognisable areas: premises and reception, workshop, parts warehouse,
vehicle-sales area, and a people/management overlay.

The layout reflects the existing IDS organisation: A premises, facility and clothing; B organisation
and personnel management; C service; D parts and accessories; E vehicle sales.

Click the parts warehouse and it expands into its practices. Click inventory control and the actual
question results appear, alongside supporting operational measures where available. Click staffing
and the organisational requirements become visible.

Switch between **recorded strengths, gaps and missing evidence**. Only relevant areas illuminate,
with precise labels and a conventional comparison table beside the scene.

A selected concern carries through the whole journey:

> Distributor → dealer → parts warehouse → inventory practice → supporting data → proposed Kaizen
> action.

**Why it is interesting:** it turns abstract section letters into an understandable operating
environment while keeping access to the exact checklist.

**Data needed:** the existing IDS questions support a first version. Evidence attachments and
operational KPIs add depth later.

Label the scene a **schematic**, not an accurate model of that particular dealership, unless real
floorplans are supplied.

## 5. A visual investigation workspace for suspected parts losses

The most valuable analytical addition for our work.

When a distributor or parts family underperforms, open an investigation view with the observed change
in the centre. Around it: volume and mix, availability, pricing feedback, recorded lost sales,
relevant UIO, sales-to-dealer coverage and related IDS practices.

The graphic separates three things visibly: **observed facts, possible explanations and missing
evidence.** A braking decline might connect to confirmed backorders through a solid line. A possible
pricing issue gets a different treatment until supported by comparable prices or recorded feedback.
Missing dealer-sales data stays a labelled gap, never a red "zero sales" branch.

**D.2-15** asks whether dealers track lost sales caused by pricing issues or backorders. **D.2-10**
asks about measuring first fill, inventory turnover and standing inventory. Unusually useful hooks
for this workspace.

The action becomes **price investigation, availability follow-up, stock-planning support, a data
request or an SPA review** — depending on the evidence, rather than defaulting to a discount.

**Data needed:** sales, BO, price feedback and lost-sales records with dates and identifiers. IDS
results show whether a tracking practice was recorded; they do not supply the missing lost-sales
transactions.

The connection becomes genuinely intelligent: **the system helps determine what to investigate,
without pretending every sales decline is leakage.**

## 6. A map of service reach — not just dealer presence

A point answers "where is the dealer?". The stronger view answers: **which vehicles can realistically
reach an appropriately equipped service location?**

Select a capability — CV service, a vehicle range, roadside assistance, BEV servicing — and display
travel-time areas around the relevant sites. Overlay geographically available UIO or fleet demand.
Areas outside the selected reach become visible, as do areas relying on a single capable site.

The striking interaction is a before-and-after slider: current recorded capability on one side, a
scenario in which a selected site receives equipment, training or an extra service function on the
other. Newly reachable demand appears immediately.

More meaningful than colouring whole countries by average score.

For BEV, eligibility should use the actual relevant requirements and supporting evidence, not a high
overall IDS score. The checklist includes charging facilities, servicing certificates, protective
equipment, insulated tools and a battery lift.

**Data needed:** verified site coordinates, relevant vehicle geography, service scope and current
capability evidence. Our map explicitly includes approximate city and country-centre locations; those
must not support precise travel-time claims.

Technically, a routing service can supply travel-time polygons — openrouteservice documents time- and
distance-based reachability.

## 7. An IDS fingerprint wall that reveals weaknesses hidden by totals

Two dealers can have similar totals and very different operating weaknesses. Make that visible
across the network.

At the widest view every dealer gets a compact five-section fingerprint. Zoom in and sections resolve
into subsections, then individual checklist items. The screen becomes a dense but ordered matrix.
Select a question and its column is highlighted everywhere. Select a pattern — weaker stock planning
— and the relevant dealers rise to the top while their map positions light up.

The powerful next step is **"Find a useful comparison"**: dealers with similar operating scope but
stronger recorded results on the selected practices, shown side by side with differences marked.

This separates a distributor-wide issue worth a common programme from a few site-specific issues. It
also finds candidates for best-practice sharing — with the caveat that a strong audit result makes a
dealer a **candidate to learn from**, not automatic proof its method is superior.

**Data needed:** most of the first version is already in the file. Peer matching improves with dealer
role, CV/LCV scope, size and operating context.

Totals-only records must stay visibly different. The upload contains **44 UK CV records with totals
only**; their missing detail must never be filled with an invented average.

## 8. A network time machine

A shared timeline. Scrub through periods and watch the network change: commercial performance,
available IDS assessments, unresolved actions, data coverage. A selected dealer keeps its identity
while its recorded profile and results change.

A second mode compares two fixed dates in split view. This shows whether an apparent improvement came
from existing dealers improving, weaker dealers leaving the assessed population, or a change in
scoring scope.

The timeline also shows events: an SPA start, training, a stock-policy change, an audit, a validated
action closure. Clicking an event shows the relevant before-and-after measures.

**The key distinction:** an event followed by better sales is not automatically the cause. Show timing
and comparable evidence, not manufactured attribution.

For IDS, values change when assessments become available — not glide continuously between annual
scores as though measured daily.

**Data needed:** dated assessment history, dated commercial measures, action history and changes in
dealer membership or standard versions. The HTML is a built snapshot; its build timestamp is not a
substitute for each dealer's assessment date.

Strong in distributor reviews: **"What changed since we last met?"** becomes a visual investigation
rather than a search through old presentations.

## 9. A Kaizen investment simulator

Instead of "who scores lowest?", ask: **where would a defined intervention produce the most useful
improvement?**

Show candidate actions with cost, effort, affected sites and expected operational effect. Select an
action and a transparent scenario layer appears over the network. Scenarios: staff training, improved
inventory reporting, equipment availability, a focused parts-stock programme. Where commercial
evidence supports it, an SPA scenario sits beside these — not in place of them.

Compare alternative portfolios: a smaller programme across many dealers versus a deep intervention at
a few important sites. The map shows reach; a separate chart shows cost and the chosen outcome.

Three outputs stay strictly separate: **potential IDS points, modelled operational effects, modelled
commercial effects.** Potential score changes can be calculated from the checklist rules. Revenue or
profit needs separate assumptions and evidence; it must not come from a generic "five IDS points
equals X% growth" formula.

Safety-critical requirements sit outside ordinary commercial trade-offs. Their priority must not
disappear because a cosmetic improvement is cheaper.

**Data needed:** defined interventions, credible costs, owners, capacity constraints and evidence for
any estimated impact. Without those, build a transparent planning tool — not a false ROI engine.

## 10. A meeting mode where questions become views and views become actions

A command bar, but the experience does not depend on a chat window.

Type: *"Show distributors with declining braking sales and their dealer-network Parts IDS gaps."*
The system translates it into visible filters, opens the comparison and shows the data basis. For a
dealer-level request the data cannot support, it says exactly which source or join is missing. The
user can inspect and change the interpretation before relying on the answer.

During a meeting, each useful view saves as a **scene**: selected distributor, period, part family,
map position, benchmark, annotation and data version. A review becomes a sequence of interactive
scenes rather than screenshots that lose their context.

From a scene, create a draft action with owner, due date, evidence required and review measure.
ISZE's action normally sits with the distributor; dealer-level execution stays linked to the relevant
DB responsibility.

The demonstration:

> Ask a question → the network reorganises → inspect a dealer → open the underlying evidence → agree
> an action → save the exact view for the next review.

**Data needed:** a shared filter model, defined metrics and an action register. Natural-language
interpretation comes after reliable search and filtering, and must use the same calculations as the
rest of the application.

---

## How it would be connected technically

Connect the data and selection state — not merely place two dashboards next to each other.

The IDS file already has an embedded data object separate from most of its rendering functions; that
gives a practical starting point for an adapter into a shared model.

The foundation is stable identifiers for distributor, dealer business, physical site, assessment,
question and part number. A separate relationship table describes which distributor supports which
site, for which vehicle scope, during which dates. Names are display labels, not the joining
mechanism.

Every view shares the same selected distributor, dealer, period and part family. Changing one
selection updates the relevant views while retaining the others. Benchmarks are explicitly labelled
as fixed references or recalculated selected-group comparisons.

Visual engine: prototype **MapLibre GL JS with deck.gl** for the atlas and transitions. MapLibre
gives WebGL mapping in the browser; deck.gl gives geographic layers and animated attribute
transitions. The map-to-chart transformations still need custom work.

For larger sales datasets: start with compact aggregates, load detail on request. DuckDB-Wasm is an
option for browser-side querying through a worker, but add it only where the measured workload
justifies the deployment complexity.

Two delivery modes: a richer hosted application, and a lightweight distributor-specific snapshot for
meetings and offline use.

### The rules that must survive the redesign

- The three commercial levels stay distinct: **ISZE-to-distributor billing, distributor-to-dealer
  sales, and dealer-to-end-customer sales.** Missing downstream data stays unknown. A DB's revenue
  must not be assigned to its dealers to make a map look complete.
- Recorded IDS results, absolute targets and relative peer performance stay separate. The current map
  colour is the dealer's position against its national average, which is not the same as satisfying
  an agreed standard.
- The missing-data rules deserve equal care. The existing treatment of UMI's unscored Section E must
  survive every new chart, filter and scenario — not merely the headline total.
- Distributor permissions must control the data delivered, not just what the interface displays. In a
  hosted system access checks belong outside the browser; in a portable snapshot the file contains
  only the recipient's permitted detail and approved benchmarks. Hiding another distributor behind a
  filter is not access control.

---

## What would be built first

For the strongest first demonstration: **Network Atlas + linked AIM view + the map-to-performance
transformation.** Together they show one connected analytical environment rather than a collection of
separate HTML pages.

The IDS fingerprint and dealer detail work from existing data immediately, while the commercial joins
are being confirmed — no waiting for a perfect dataset before improving the experience.

Then the investigation workspace and the meeting-to-action flow, because they turn visuals into
something useful for distributor support. Travel-time coverage and investment simulation follow once
the location and operational data can support them.

Graphic direction: **cinematic during transitions, calm during analysis.** A restrained neutral base,
Isuzu red for selection and navigation, diagnostic colours with consistent meanings, high-resolution
imagery where it helps, fully readable labels. The drama comes from relationships becoming clear, not
from constant motion.

## The one inventory asked for from Cursor

> Inspect the latest IDS, sales, GPS/PMS and AIM dashboard sources without modifying them. Identify
> the current dashboard entry points and builders, then inventory the distributor register,
> headquarters/warehouse locations, dealer/site master and ID crosswalks; sales-to-dealer data
> including wholesale and its coverage; PN-to-AIM mappings; UIO at its actual geographic level;
> inventory, BO and lost-sales records; and dated IDS assessments, evidence and action history. For
> each source, return its path, fields, date range, row grain, join keys and coverage. Flag uncertain
> matches, duplicate records and missing data rather than estimating them. Also confirm whether the
> target must remain a single offline HTML file or can be hosted with authentication.

## Closing recommendation

Make one selection travel through the whole system: **distributor → territory → parts family → dealer
practices → evidence → action.** That continuity is what would make it both visually exceptional and
genuinely valuable for ISZE.
