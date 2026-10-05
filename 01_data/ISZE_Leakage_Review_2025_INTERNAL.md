# ISZE - Leakage and opportunity review that respects incomplete coverage

**Conclusion: start the commercial review with IUK fuel filters and brakes, while validating the larger clutch estimates before turning them into targets.** The data supports a ranked opportunity register; it does not establish how much customers spent with competitors, or prove that dealers failed to service vehicles.

**INTERNAL REVIEW. Prepared 20 September 2026.** Rankings use calendar 2025, the latest common full year. Source context is dated 19 September 2026. Billing continues through 30 June 2026, but the 2026 sales-to-dealer periods and published measures do not support an equivalent cross-market comparison. Monetary opportunities are in euro at the source's billing-based valuation, not retail turnover or incremental profit.

This review replaces the earlier empty working pack. It uses the supplied raw billing and dealer-quantity files, the actual available target and service-family extracts, and the context documents. It does not depend on exact filename matches when a usable replacement is supplied.

## Coverage before ranking

| Distributor / market | 2025 billing | 2025 sales to dealer | Target-spend view | Service matrix | Target-model fleet |
| --- | --- | --- | --- | --- | --- |
| ARMENIA | Present | UNKNOWN | Billing only | No | Unknown |
| BELGIUM | Present | UNKNOWN | Yes | Yes | 9,593 |
| CYPRUS | Present | UNKNOWN | Yes | Yes | 2,308 |
| DENMARK | Present | UNKNOWN | Yes | Yes | 851 |
| FINLAND | Present | UNKNOWN | Yes | Yes | 1,204 |
| GERMANY | Present | UNKNOWN | Yes | Yes | 13,780 |
| GREECE | Present | Annual + months | Yes | Yes | 3,742 |
| HUNGARY | Present | UNKNOWN | Yes | Yes | 3,734 |
| ICELAND | Present | UNKNOWN | Yes | Yes | 406 |
| IRELAND | Present | Annual + months | Yes | Yes | 2,161 |
| ITUK | Present | Named + network | Yes | Yes | 23,067 |
| IUK | Present | Annual + months | Yes | Yes | 47,783 |
| KAZAKHSTAN | Present | UNKNOWN | Billing only | No | Unknown |
| MALTA | Present | UNKNOWN | Yes | Yes | 1,040 |
| NORWAY | Present | UNKNOWN | Yes | Yes | 7,929 |
| PALESTINE | Present | UNKNOWN | Billing only | No | Unknown |
| PORTUGAL | Present | Annual + months | Yes | Yes | 7,208 |
| ROMANIA | Present | UNKNOWN | Yes | Yes | 1,071 |
| SWEDEN | Present | UNKNOWN | Yes | Yes | 8,443 |
| UKRAINE | Present | UNKNOWN | Billing only | No | Unknown |
| UMI | Present | UNKNOWN | Yes | Yes | 18,542 |
| UTI | Present | Annual; partial months | Yes | Yes | 10,336 |

### What the coverage map actually establishes

There are 22 markets with dated billing records, 18 with a target-spend and service-family model, and six with a 2025 sales-to-dealer report: Greece, Ireland, ITUK, IUK, Portugal and UTI. Together those six account for 56.96% of the published 2025 parts-billing base. This is a billing-weighted coverage statistic, not a statement that 56.96% of customer repairs are observed. The context shorthand of five reporting distributors does not describe the files supplied for this exercise.

ITUK has both a network part-number report and a named-dealer report covering 64 accounts. These are overlapping presentations, not two sales channels to add together. Greece, Ireland, IUK and Portugal provide annual totals and monthly records. UTI provides an annual 2025 total but an incomplete monthly history. Romania has a 2026 report; this does not create 2025 coverage. UMI has no 2025 dealer report, despite the presence of separate dealer-standards information. Dealer-standards participation is not sales reporting.

**Honesty statement.** Sales to dealers are UNKNOWN for the other 16 billed markets. No file is not zero movement, and it is not evidence that a distributor retains all possible business. A file that is present is also not proof of complete dealer participation: the full dealer-account census and reporting exclusions have not been independently reconciled. The raw dealer file contains quantities, not actual dealer invoice euros. No supplied source provides a complete record of dealers' repairs and sales to end customers. Even in the six reporting markets, end-customer maintenance demand remains inferred rather than directly measured.

Ukraine, Palestine, Armenia and Kazakhstan have billed euro but no usable fleet denominator in these measures. Their source zero fleet values are treated as unknown, not as zero vehicles. Their 2025 all-parts billed values are respectively EUR 1,160,672, EUR 27,336, EUR 274,583 and EUR 161,949. They remain visible in coverage, but cannot be ranked by euro per vehicle or service-demand cover. Palestine's last dated 2025 billing record is 2 July; the file alone does not establish why no later transaction appears.

## Primary lens: all-parts billing relative to target spend

The table below retains published 2025 billing and the target-spend model. Actual and target euro per vehicle use the **same target-model fleet**. This avoids comparing a rate based on one fleet with a target based on another. Family scope throughout this table is all in-scope parts; these market-level gaps must not be added to the service-family cells later in the review.

| Market | Model fleet | Parts billed | Billed / vehicle | Target / vehicle | Billed / target | Positive modeled headroom |
| --- | --- | --- | --- | --- | --- | --- |
| ITUK | 23,067 | EUR 5,564,544 | EUR 241.2 | EUR 529.4 | 45.6% | EUR 6,647,507 |
| IUK | 47,783 | EUR 6,131,920 | EUR 128.3 | EUR 250.0 | 51.3% | EUR 5,813,830 |
| UTI | 10,336 | EUR 3,331,512 | EUR 322.3 | EUR 800.2 | 40.3% | EUR 4,939,788 |
| PORTUGAL | 7,208 | EUR 1,709,794 | EUR 237.2 | EUR 423.4 | 56.0% | EUR 1,342,293 |
| UMI | 18,542 | EUR 3,319,344 | EUR 179.0 | EUR 250.0 | 71.6% | EUR 1,316,156 |
| GERMANY | 13,780 | EUR 2,535,932 | EUR 184.0 | EUR 276.4 | 66.6% | EUR 1,272,196 |
| SWEDEN | 8,443 | EUR 1,278,462 | EUR 151.4 | EUR 250.0 | 60.6% | EUR 832,288 |
| HUNGARY | 3,734 | EUR 330,031 | EUR 88.4 | EUR 250.0 | 35.4% | EUR 603,469 |
| NORWAY | 7,929 | EUR 1,416,552 | EUR 178.7 | EUR 250.0 | 71.5% | EUR 565,698 |
| GREECE | 3,742 | EUR 520,304 | EUR 139.0 | EUR 254.8 | 54.6% | EUR 433,289 |
| BELGIUM | 9,593 | EUR 2,109,332 | EUR 219.9 | EUR 255.8 | 86.0% | EUR 344,175 |
| CYPRUS | 2,308 | EUR 428,443 | EUR 185.6 | EUR 293.0 | 63.4% | EUR 247,824 |
| MALTA | 1,040 | EUR 206,502 | EUR 198.6 | EUR 364.3 | 54.5% | EUR 172,325 |
| ROMANIA | 1,071 | EUR 175,218 | EUR 163.6 | EUR 250.0 | 65.4% | EUR 92,532 |
| DENMARK | 851 | EUR 148,221 | EUR 174.2 | EUR 250.6 | 69.5% | EUR 65,018 |
| FINLAND | 1,204 | EUR 277,921 | EUR 230.8 | EUR 250.0 | 92.3% | EUR 23,079 |
| ICELAND | 406 | EUR 85,282 | EUR 210.1 | EUR 250.0 | 84.0% | EUR 16,218 |
| IRELAND | 2,161 | EUR 1,187,459 | EUR 549.5 | EUR 442.5 | 124.2% | EUR 0 |

ITUK, IUK and UTI have the largest modeled all-parts headroom. This makes them important places to investigate, not a forecast of revenue recovery. The target is a ceiling constructed from class-based annual spend assumptions. Several light-commercial markets use a flat EUR 250 per vehicle. The model is not a measured record of customer expenditure, and the supplied extracts do not allow an independent reconstruction of its monetary calibration to ISZE billing. A commercial claim that a certain amount is definitely going to competitors would exceed this evidence.

The fleet denominator also changes some apparent market positions. ITUK's target model uses 23,067 vehicles, while the spend-per-truck extract uses 22,389 and the supplied service-family model uses 23,068. Germany uses 13,780 in the target model versus 12,855 in the spend extract. Ireland uses 2,161 versus 3,056. Portugal uses 7,208 versus 8,176. Belgium differs by one vehicle. These differences are retained explicitly rather than averaged. Ireland's 124.2% of modeled target is therefore not proof that there is no remaining business to win.

### Portugal: the published target is a legacy figure

The instructed light share is **0.6364, or 63.64%, within the LD truck subgroup**. It is not a share of all vehicles including pick-ups. The registration observation date and the original share file are not supplied, so the provenance here is the user's stated official-registration parameter.

The historical 2025 fleet extract contains 4,733 light-commercial vehicles, 2,206 vehicles in the LD truck subgroup and 269 F-series trucks. The published EUR 3,052,087 ceiling is reproduced exactly by 4,733 x EUR 250 + 2,206 x EUR 739 + 269 x EUR 887. This is an arithmetic consistency check: the published value is consistent with all LD vehicles receiving the higher truck rate. It is not proof of how the upstream implementation was written, and it does not demonstrate that the 63.64% light share has been used.

The published all-parts gap of EUR 1,342,293 on 7,208 vehicles therefore remains a **legacy modeled value**, not an approved opportunity commitment. No replacement ceiling is calculated in this review. The fleet difference with the 8,176-vehicle spend extract is an additional issue, not something the light-share correction automatically solves. Portugal does have dealer reporting, which can support a stock and part-number discussion without waiting for a definitive new ceiling.

## Family opportunities: euro size and actionability are different decisions

The family register uses the total line: original plus value parts. All 252 calendar-2025 total rows reconcile to the corresponding original and value-part units and euro in the service extract. The 252 category-ranking records in the opportunity export agree exactly on gap and cover with those service totals. The ranking below follows the supplied monetary cells, not the different monetary examples in the context narrative.

**Ranking rule:** descending positive source euro gap among priced cells. Actionability is shown separately rather than hidden inside an invented probability or a 0-100 score. A large estimate with weak fitment evidence stays a validation task; a smaller consumable opportunity can be the first commercial test. These are 15 market-family cells, not 15 independent projects. No combined Top 15 total is produced.

| Euro rank | Market | Family | Modeled euro gap | Fleet | Gap / vehicle | Total cover | Actionability |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | IUK | Clutch disc | EUR 1,338,473 | 47,783 | EUR 28.01 | 4.5% | Validate repair / fitment |
| 2 | IUK | Brake pad | EUR 806,882 | 47,783 | EUR 16.89 | 24.1% | Commercial review after fitment check |
| 3 | IUK | Brake shoe | EUR 694,105 | 47,783 | EUR 14.53 | 5.6% | Validate fitted fleet |
| 4 | IUK | Clutch pressure plate | EUR 565,154 | 47,783 | EUR 11.83 | 6.5% | Validate repair / fitment |
| 5 | IUK | Fuel filter | EUR 485,078 | 47,783 | EUR 10.15 | 16.0% | Commercial review after fitment check |
| 6 | IUK | Blower filter | EUR 470,253 | 47,783 | EUR 9.84 | 18.4% | Validate fitted fleet |
| 7 | IUK | Brake rotor | EUR 469,224 | 47,783 | EUR 9.82 | 43.5% | Commercial review after fitment check |
| 8 | UTI | Brake pad | EUR 456,181 | 10,336 | EUR 44.14 | 7.0% | Commercial review after fitment check |
| 9 | UTI | Clutch booster | EUR 388,140 | 10,336 | EUR 37.55 | 1.8% | Validate repair / fitment |
| 10 | IUK | Clutch kit | EUR 373,081 | 47,783 | EUR 7.81 | 0.2% | Validate repair / fitment |
| 11 | BELGIUM | Brake shoe | EUR 346,326 | 9,593 | EUR 36.10 | 6.7% | Validate fitted fleet |
| 12 | UMI | Brake pad | EUR 332,399 | 18,542 | EUR 17.93 | 8.7% | Commercial review after fitment check |
| 13 | ITUK | Brake shoe | EUR 325,637 | 23,068 | EUR 14.12 | 8.1% | Internal hold |
| 14 | GERMANY | Clutch disc | EUR 321,800 | 13,780 | EUR 23.35 | 3.1% | Validate repair / fitment |
| 15 | ITUK | Brake pad | EUR 311,991 | 23,068 | EUR 13.52 | 49.2% | Internal hold |

The first five cells all belong to IUK because its fleet and the source's euro estimates place them there. The list is not artificially diversified to make different markets appear. Clutch disc, pressure plate and clutch kit can relate to the same repair; their modeled values cannot be added until part contents and applications are separated. Pads, shoes and rotors also need unit and axle checks before being converted into a repair-event estimate. The stated fleet is the fleet behind the source model, not a verified count of vehicles fitted with that particular component.

The currently supplied Belgium brake-shoe cell is EUR 346,326, not the EUR 344,450 example in the context narrative. Germany's clutch-disc cell is EUR 321,800, not its EUR 319,817 context example. The source opportunity export corroborates the supplied service cells, so the CSV versions are used here. The exact reason for the version difference is not established. The CSV concordance is the working basis here, not a claim that the context has been formally superseded.

### The peer comparison changes the order of action

The requested official percentile file is not supplied. The following is a **new descriptive calculation**, not a recovered official measure: within eight markets whose supplied 2025 fleet is light-commercial only, rank each market's total service-family cover, using average ranks for ties. Percentile = (ascending rank - 1) / (number of markets - 1). A higher percentile means higher cover. The cohort is Finland, Hungary, Iceland, IUK, Norway, Romania, Sweden and UMI. UTI is not in it, and this is not a dealer-standards score.

| IUK family | Modeled gap | Fleet | Total cover | New peer percentile |
| --- | --- | --- | --- | --- |
| Fuel filter | EUR 485,078 | 47,783 | 16.0% | 0.0th |
| Brake pad | EUR 806,882 | 47,783 | 24.1% | 57.1th |
| Brake shoe | EUR 694,105 | 47,783 | 5.6% | 57.1th |
| Clutch disc | EUR 1,338,473 | 47,783 | 4.5% | 85.7th |
| Clutch pressure plate | EUR 565,154 | 47,783 | 6.5% | 100.0th |
| Blower filter | EUR 470,253 | 47,783 | 18.4% | 14.3th |

IUK is lowest in this group for fuel-filter cover, despite an expected recurring maintenance role. That makes the EUR 485,078 modeled gap on 47,783 vehicles a strong starting point for investigation. It does not establish price as the cause: applicability, stock availability, order timing and alternative sourcing must be tested.

By contrast, IUK is second-highest for clutch-disc cover and highest for clutch-pressure-plate cover in this same cohort, even though their absolute modeled cover is very low. The common low cover may reflect a common commercial problem, an overly broad expected-replacement assumption, component/kit classification, transmission mix, or a combination. The data cannot choose between those explanations. The large clutch euro estimates justify a careful repair-level review, not an accusation that IUK performs uniquely badly.

### Unpriced does not mean no opportunity

Thirty-nine of the 252 service-family cells are flagged as not monetarily quotable. Typically actual sales are zero, so there is no observed unit price from which to value the model's expected units. The source books a zero euro gap, but the analytical register replaces that with a blank monetary value and an explicit UNKNOWN label. No price is borrowed from another market or another family.

Examples include IUK urea filters and clutch boosters on its 47,783-vehicle modeled fleet, and UTI blower filters, pilot bearings and release bearings on its 10,336-vehicle fleet. These are unpriced diagnostic questions, not zero-leakage findings. Equipment applicability can be especially important for a family with no observed sales. Summing only the priced rows still would not produce a valid complete network opportunity; no network service-gap total is reproduced here.

## What the next customer meeting should ask for: the five largest cells

### IUK clutch discs - EUR 1,338,473 modeled gap; 47,783 vehicles

The purpose is to establish the count of applicable clutch-repair events, not to negotiate against the full modeled euro gap. The disc expectation is equivalent to 20% of the entire 47,783-vehicle model fleet in one year, before a verified manual-transmission and kit-contents adjustment is available. That assumption is a major part of why the modeled value is large. Ask for the fleet split by model, registration year and manual/automatic transmission; the clutch disc part numbers and supersessions; the contents of all relevant kits; and distributor sales-to-dealer quantities by part number and month on the same 2025 basis. Ask a representative set of dealers for actual clutch jobs and their procurement routes, separately identifying full-kit and component repairs. Warranty claims are not a substitute for this job information.

The commercial move, after the fitment and repair-unit checks, is a complete-repair offer with confirmed availability of the disc, pressure plate, release bearing and applicable ancillary components. Price support should be tested against matched quotations and delivery/service terms, not assumed necessary. Agree the eligible repair population and the baseline first. The evidence does not support an incremental sales or margin forecast yet.

### IUK brake pads - EUR 806,882 modeled gap; 47,783 vehicles

Ask for part-number coverage by model and axle, whether reported quantities are pieces or axle sets, monthly sales to dealer, opening and closing distributor stock, backorders and lost quotations. Request matched competitor quotations with application, brand, tax treatment, quotation date and delivery terms. A missing sale may reflect availability or range coverage rather than price.

The next commercial action is a limited test on the relevant fast-moving applications, with dealer commitments, an agreed availability standard and a clear original/value-parts offer. Evaluate the change in total in-scope sales to dealers on a comparable period, stock days and contribution, not simply a shift from original parts to the value line. The value line is already inside the ISZE business and must not be counted as competitor leakage.

### IUK brake shoes - EUR 694,105 modeled gap; 47,783 vehicles

The first question is how many of those vehicles actually use the drum-brake applications covered by the listed parts. Ask for rear-brake configuration by model and year, shoe-versus-lining coverage, set contents and the unit convention used in the source. Obtain replacement-job evidence from customer work orders, not warranty incidence. This is important because the model fleet is not yet a verified brake-shoe-fitted fleet.

After the denominator is agreed, build a specific brake-shoe range and stocking proposal for the relevant applications. Avoid a fleet-wide promotion based on the full modeled count. No general price reduction is justified by this extract alone.

### IUK clutch pressure plates - EUR 565,154 modeled gap; 47,783 vehicles

Run this as part of the same clutch review as discs, not as a second unrelated revenue programme. Ask which plates are supplied inside a complete kit and which are bought separately, whether the kit and component part numbers share the same application, and how repair jobs are counted. IUK's highest cover in the comparable peer group makes a common model or classification issue a live alternative explanation.

The required meeting outcome is one non-overlapping clutch opportunity per applicable repair, with component availability and complete-kit alternatives. Do not add the pressure-plate estimate to the disc or kit estimate before that reconciliation. No combined euro ambition is given here.

### IUK fuel filters - EUR 485,078 modeled gap; 47,783 vehicles

Although fifth by euro size, this is the first category I would discuss commercially. Its total model cover is 16.0%, lowest in the eight-market light-commercial cohort. Ask for the service schedule by generation, the filter/element/assembly part-number relationships, current and year-end stock, dealer backorders, supersession coverage, and monthly sales-to-dealer quantities. Then use a small representative set of actual customer service jobs to establish what was fitted and where it was sourced.

The commercial response depends on that evidence: fill missing range, correct stocking, resolve availability, or test a matched competitive offer. A short, agreed pilot should track total original-plus-value dealer movement and completed applicable services. No uplift percentage is assumed. The EUR 485,078 is the model's full gap, not the expected proceeds of the pilot.

## Dealer bridge: separate inventory questions from competitive leakage

A direct subtraction of native ISZE billing euro from a source-valued dealer total is not a valid leakage calculation. The raw dealer file has no euro field. The existing dealer euro summaries are valuations, and their selected part universe and valuation assumptions differ from native billing. We therefore retain them only as separate commercial-class context and construct a new, explicit common-value diagnostic.

For each of the six reporting markets, the bridge uses one annual 2025 network presentation. Part numbers are matched exactly to that market's 2025 billing quantities. A matched dealer quantity is valued at the same market's weighted 2025 ISZE billing unit value. No guessed supersession or physical-family mapping is applied. Billed-only part numbers stay separate; dealer-only quantities stay unvalued. The signed difference is matched billing value minus the same-value dealer equivalent. It is not dealer turnover, gross profit, confirmed inventory change or competitor leakage.

| Market | Fleet basis | Matched billing | Dealer equivalent | Signed difference | Billed-only scope | Unvalued dealer quantity |
| --- | --- | --- | --- | --- | --- | --- |
| GREECE | 3,742 | EUR 438,530 | EUR 437,602 | EUR 929 | EUR 84,828 | 1.5% |
| IRELAND | 2,161 | EUR 1,172,296 | EUR 1,025,314 | EUR 146,982 | EUR 20,466 | 26.1% |
| ITUK | 23,067 | EUR 5,516,077 | EUR 5,533,387 | EUR -17,310 | EUR 59,681 | 5.1% |
| IUK | 47,783 | EUR 5,924,933 | EUR 5,712,946 | EUR 211,987 | EUR 206,076 | 0.9% |
| PORTUGAL | 7,208 | EUR 1,682,198 | EUR 1,421,068 | EUR 261,130 | EUR 30,027 | 8.2% |
| UTI | 10,336 | EUR 2,457,653 | EUR 2,140,034 | EUR 317,619 | EUR 879,464 | 1.4% |

In UTI, the broad all-parts comparison of EUR 3,331,512 published billing with EUR 2,143,892 in the existing source-valued dealer summary could create a false EUR 1.19 million leakage story for 10,336 trucks. On the new exact-part common-value basis, the signed matched-flow difference is EUR 317,619, while EUR 879,464 of candidate billing relates to part numbers absent from the dealer report's matched set. Neither amount proves where the parts ultimately went. The sensible request is opening and closing stock, transfers, returns and report-scope reconciliation, not an accusation of missing customers.

ITUK's matched dealer equivalent is EUR 17,310 above matched billing across its 23,067-vehicle target-model fleet. That near alignment can coexist with a large modeled all-parts target gap: wholesale stock movement and total customer spend are different questions. Greece shows the same distinction. Its EUR 929 signed matched difference on 3,742 vehicles does not erase the EUR 433,289 all-parts target gap.

Ireland has 26.1% of reported dealer quantity unvalued in this exact-match bridge. That is a quantity-weighted limitation, not a revenue coverage estimate: unmatched items could carry very different prices. Its apparent euro-flow result should not be read as complete. Similar unmatched portions remain visible for every market.

### The bridge itself has an accounting limit

The reproducible candidate raw billing scope does not fully reproduce the published net-parts extract. The 2025 difference across the 22 billed markets is EUR 43,471.90. It includes market-level differences in both directions. It is not a commercial opportunity. Published net-parts billing is therefore retained as the primary target-spend numerator, and the raw-derived bridge remains an internal diagnostic. The complete source exclusion/normalisation logic is needed before a signed-off stock reconciliation could be claimed.

Even exact equality between billing and dealer movements would not prove zero leakage: without a complete eligible customer-demand measure, both could be low together. Conversely, a positive signed difference could be inventory, timing, transfers, unreported transactions or transformation scope. No opening/closing stock data is supplied to distinguish these mechanisms.

### Classification evidence is partial

The supplied dealer classification summaries distinguish value parts, original parts in a contested class and other original parts. They do not replace the missing complete part-number-to-physical-family file. This review cannot independently reconstruct a dealer brake/filter/clutch bridge or verify kit contents from those summaries. Existing broad commercial-class valued totals are shown in the workbook on their own basis, not forced into the new matched bridge.

The selected original/value-parts mix file also differs from the service-family universe. For example, its 2025 IUK brake-pad selection totals EUR 129,463, while the service total line is EUR 255,744 on the 47,783-vehicle fleet. Those are different scopes, not evidence that half of the sales disappeared. The service export's own original-plus-value total is used for demand cover. High value-parts share within a selected family is not a failure of total business retention.

## ITUK: preserve the externally agreed basis

The uploaded service export has ITUK oil-filter total cover of 78.67%, based on 23,068 vehicles and its own expected units. The context describes a different internal-network result of 116% uncapped, while the approved external standard is 35.1% on 22,389 trucks. The export-versus-context difference cannot be explained away merely by saying there are two intentionally different audiences; the exact internal export version also needs reconciliation.

The internally ranked brake-shoe and brake-pad cells therefore stay out of the ITUK customer note. The note uses the separately stated external standard: calendar-2025 parts actuals, 22,389 trucks from the March-2026 DVLA register, 1.25 annual filter services and a 0.5 wear factor. Its individual family estimates are air filters EUR 736,037 at 13.2% cover, brakes EUR 641,833 at 35.3%, clutch EUR 392,559 at 7.8%, oil filters EUR 140,602 at 35.1%, and fuel filters EUR 127,440 at 65.1%. These five external cells are not inserted into the internal cross-market ranking or added to it.

The external air interval remains provisional and brake-wear calibration is not locked. Those limitations stay in the customer note. Separate methods must never be averaged or substituted without explaining the fleet and expected service frequency.

## Original plus value parts: the UTI example

For UTI's 10,336-vehicle modeled 2025 fleet, the air-filter family has EUR 161,519 of actual total billed parts and 131.46% total cover, versus only 2.43% if original parts alone are counted. Fuel filters carry EUR 162,618 of actual total billed parts and 144.91% total cover, versus 56.57% original-only. A genuine-only headline would wrongly describe substantial existing value-parts business as lost to outside competitors.

Total cover above 100% is retained, not silently capped. It may reflect stocking, cross-fleet sales or an imperfect expectation; it is not proof that every customer service was captured. UTI still has a separately priced EUR 456,181 brake-pad gap at 7.04% total cover, and a EUR 388,140 clutch-booster estimate on the same fleet. The booster estimate needs especially careful applicability and replacement-incidence validation. A strong filter total does not cancel a weak wear-family signal.

The historical 2025 opportunity also precedes the first 2026 order under UTI's special-price agreement described in the context. The next discussion should review the relevant existing agreement and obtain a comparable current follow-through period, not present a new agreement as though none exists or claim an improvement from mismatched partial-year figures.

## External material versus internal material

The separate distributor notes contain only that distributor's family estimates, the stated fleet and model basis, clear requests, and the limitations that affect interpretation. The IUK note includes anonymous comparable-peer positions with the new method explained. It does not reveal another distributor's cash values. UMI and UTI each receive a distinct note; no combined Israel figure is generated. The ITUK note uses only its explicitly approved external standard. Portugal's note does not carry the unsettled overall ceiling as a commercial target.

The full coverage matrix, cross-market ranking, accounting reconciliation, source filenames, duplicate presentations, model-version conflicts, and the detailed identity controls remain internal. Material uncertainty is not hidden from the distributor merely because its internal technical explanation is recorded elsewhere. There is no network service-gap total, no Top 15 aggregate and no promised revenue uplift.

## Anti-patterns: false rankings this method avoids

| Tempting but false conclusion | Why it would fail here | What this review does instead |
| --- | --- | --- |
| Low warranty euro means no aftermarket problem. | Claims omit routine maintenance and differ by quality, settlement and reporting. | Warranty is not used as a ranking input. |
| UMI has no dealer file, so it has no downstream leakage. | Missing reporting says nothing about sell-through. | UMI sales to dealer is UNKNOWN; its service family estimates remain model comparisons. |
| UTI air filters have 2.43% cover. | That is original-only and discards value-parts business. | Use 131.46% total cover with EUR 161,519 actual family billing and a 10,336-vehicle model fleet. |
| Add monthly and annual quantities to capture all dealer activity. | These are repeated presentations of the same period. | Use one annual network presentation; monthly data is a separate time-series option. |
| Add ITUK named-dealer and network files. | Their reports overlap; their totals also differ. | Keep the network bridge and named-dealer classification views separate. |
| UTI has about EUR 1.19 million of dealer leakage. | Native billing and source-valued dealer euro have different scope and basis. | Use a separate exact-part common-value bridge, unmatched scope and a stock-data request. |
| No sales and zero source gap mean a clean result. | Thirty-nine cells lack a usable selling price. | Mark euro UNKNOWN; do not infer a price or a healthy market. |
| Clutch disc + plate + kit are three independent prizes. | One repair may consume a kit containing both components. | Use an overlap group and no summed target. |
| The largest clutch euro means IUK is the worst peer. | Absolute fleet-sized gap and relative cover are different. | Show IUK second-highest disc and highest plate cover in the comparable cohort. |
| Portugal current ceiling already reflects 63.64% light trucks. | Its published arithmetic is consistent with all LD vehicles at the heavier rate. | Retain a legacy label; do not invent a replacement ceiling. |
| Ireland is above target, so no opportunity remains. | Fleet counts and modeled expectations differ across measures. | Retain the denominator caveat and inspect families separately. |
| Dealer flows match billing, so the full market is served. | Both wholesale layers can be aligned while both miss customer spend. | Separate flow reconciliation from target-spend and service-demand lenses. |
| Compare 2026 dealer totals with 2025 and call it growth. | Dealer reports extend to different months and billing is partial. | Rank on the common full year; do not infer 2026 improvement. |
| A current list price explains historical price leakage. | A single price snapshot does not establish period-matched transaction prices. | No price-increase or historical price-leakage narrative is fabricated. |

**Warranty reminder.** Warranty data measures claims, defects and settlements, with incomplete coverage and potentially different currency and payer conventions. It does not normally record scheduled filters or routine brake work. Neither low nor high warranty cost establishes dealer maintenance effort, service intervals, total parts retention or competitor purchases. It has no analytical role in this register.

## Source mapping and reproducibility

| Required source | Actual source used | What it supports | Limit |
| --- | --- | --- | --- |
| 01_all_sales_isze_to_distributor.csv | Exact file supplied | Measured ISZE billing; customer split preserved | Candidate 2025 scope does not fully reproduce supplied net-parts figures; reconciliation retained. |
| 03_all_sales_to_dealer.csv | Exact file supplied | Six 2025 markets; quantities, periods and reporting levels | Annual and monthly presentations are alternatives, not additions; no native dealer euro field. |
| 04_gps_spu_by_distributor.csv | 02_spend_per_truck_by_market.csv + 01_parts_billed_vs_target_by_market.csv | Published billing and model target; 18 target markets plus four billed markets without fleet | Use target-model fleet for both sides of per-vehicle comparison; show separate published spend fleet. |
| 05_pms_opportunity_matrix.csv | 10_gaps_accounts_tenders.csv: category_gap_ranking | 2025 category opportunity records | All 252 gap and cover cells reconcile exactly to the supplied service total rows; other datasets excluded. |
| 06_pms_capture_by_db_year.csv | 03_service_capture_by_market_family.csv | Total-line service demand and 39 unpriced cells | Original plus value parts reconciles to total; unknown-priced cells are not zero opportunity. |
| 09_aim_pn_classification_v2.csv | Full part-number classification NOT supplied | Only existing aggregated classifications can be used | No physical-family rebuild of dealer quantities or verified kit / component exclusions. |
| 10_dealer_sellout_aim_gps_vs_billing_2025.csv | dealer_sellout_gps_2025.csv; dealer_sellout_aim_mix_2025.csv; dealer_sellout_compare.json; dealer_sellout_pms_compare.csv | Existing broad commercial-class aggregates and comparison context | Euro amounts in these aggregates are valuations, not native dealer invoice revenue. New exact-part bridge shown separately. |
| 11_mix_genuine_bvp_pms.csv | 04_original_vs_value_parts_mix.csv | Original / value-parts mix in the source selection | Scope differs from service total rows; mix is not a demand-cover numerator or a market share. |
| 12_network_percentile.csv | Not supplied; new peer calculation explicitly labelled | Eight LCV-only market cohort; same service-family total cover | Descriptive rank, not the missing official percentile file and not dealer-standards scoring. |
| 07_uio_ld_n35_share.csv | Not supplied; user instructed share 0.6364; 07_fleet_trucks_in_service.csv provides class counts | Portugal LD subgroup light share 63.64% | Registration observation date unavailable. Current target is retained as legacy; no replacement ceiling calculated. |

The workbook preserves source monetary estimates rather than recalculating them from rounded displayed expected quantities. A check using those printed quantities differs by at most EUR 5.79, within the effect of their rounding and source unit-value precision. The original and value-part components reconcile to the service total, and the separate category ranking corroborates all 252 monetary and cover cells. The source manifest records exact input filenames, byte counts and hashes so another reviewer can identify the snapshots used.

The workbook contains the coverage map, all 18 target-market contexts, the 15 ranked family cells, all 252 service rows, the eight-market peer calculations, the six-market matched dealer bridge, published-versus-candidate billing reconciliation, separately scoped mix tables, ITUK's external reference, and the explicit limitations. It contains no raw billing lines and no full price list. Local arithmetic checks do not constitute a rerun of the upstream verification report, which was not supplied.

The missing complete part-number classification, official percentile file, dated Portugal share extract, stock balances, dealer-account coverage reconciliation, and year-matched native dealer invoice values are specific limits on specific claims. They are not reasons to discard the analysis already supported by the supplied files.

## Decision

Convene the IUK discussion with fuel filters first, brake pads next, and fitted-fleet checks for shoes; run clutch disc, plate and kit as one validation exercise rather than three revenue programmes. Maintain separate UTI and UMI brake discussions, with total original-plus-value performance as the primary measure. Keep ITUK on its agreed external method. Treat Portugal's aggregate target as unsettled while using its existing dealer reporting for stock and range diagnosis.

No discount recommendation, recoverable-revenue forecast or claim of dealer service failure follows automatically from this register. Those decisions require the next layer of applicable-fleet, repair-job, stock, availability and matched commercial evidence.
