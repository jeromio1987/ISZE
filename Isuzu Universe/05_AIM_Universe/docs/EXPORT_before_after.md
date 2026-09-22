# AIM Universe — export defect record

Corrective build, 22 September 2026. This is the record for the export layer:
what was wrong, what it does now, and the command that shows it.

The frozen reference `reference/ISZE_AIM_Pricing_Decisions_v03_FROZEN.html`
(sha256 `7494CEA1955BE820D0082EEF15473610945663FBEFC7A06D7969C15822423E14`) was
read, never modified.

## The short version

`tools/build.py` assembles `src/data/export.js` into the artifact and retires
`src/output/recipients.js`. The hardened protections lived almost entirely in the
retired file, so the module the product ships had four gaps: a restricted figure
typed into a sentence went straight into a participant's file, the internal
record's own limits block was written out empty, a restricted word hidden inside
a compound file name was accepted, and the saved brief did not say what it was.

All four are now carried by the shipped module, and the check that distinguishes a
built output from a filtered one still passes.

## How to see it

```
node --test tests\export_shipped.test.mjs
node tests\accept\accept_04_participant.cjs
node tests\accept\accept_05_08_safety.cjs
```

---

## D13 (critical) — a restricted figure typed into free text reached the participant file

**Was.** Putting `"our parts cost is 41.75 and the gross margin is 30%"` into the
request note produced a brief that contained that sentence, and the builder's own
content check returned `{"ok":true,"findings":[]}`. An allowlist stops a
restricted *field*; it cannot see a restricted *figure written into a sentence*,
and nothing in the shipped module looked inside a string.

**Now.** The phrase and pattern lists are ported from the hardened module and
extended to catch a figure written as text. When the check finds something, the
brief is **refused**:

- `ok: false`, `refused: true`, `payload: null`, and no participant payload is
  produced at all;
- `code: "RESTRICTED_WORD_IN_FREE_TEXT"`, with the offending phrase, the rule that
  matched it and the path it was found at named in the error;
- the refusal also lands on `audit.ok`, because the interface reads that key
  before it writes the file. Without it, the guard would see a clean audit and
  download a refused brief.

The sentence is **not** quietly deleted. A silently emptied sentence is the same
fault as the blacklist the allowlist replaced: the output looks clean because
nobody decided what belonged in it. The refusal says what it found and where.

What it now catches, in addition to the hardened module's list: `our cost`,
`supplier cost`, `buying price`, `cost price`, `net cost`, `profit margin`,
`net margin`, `purchase discount`, `supplier rebate`, `what we pay`, `what ISZE
pays`, `costs us`, a cost or margin with `per unit`, a currency pair written as
`USD/EUR 0.92`, and `cost basis` / `verified cost` named in text.

What it does not catch, stated plainly: a restricted figure written with no
restricted word and no currency near it at all ("the number is 41.75"). No
pattern can see that, because nothing in the sentence would tell a reader either.
The check is a safety net under a construction, not a substitute for one, and a
browser-side check is not server-side access control.

**Before / after, on the same input.**

```
note = "Please confirm. Our parts cost of 987654.4321 EUR and the gross margin of 41.7% cannot be shared, and the FX rate of 123456.7891 applies."

before:  payload ok undefined | audit {"ok":true,"findings":[]} | note reached the file: true | 1013 bytes
after:   ok false, refused true, code RESTRICTED_WORD_IN_FREE_TEXT, payload null | note reached the file: false | 4 bytes written ("null")
```

**Command proving it.**

```
node --test tests\export_shipped.test.mjs
```

`X01` to `X09` cover the refusal, the written-figure form, the FX rate, the
margin, the visibility of the refusal as a refusal, the absence of any payload,
and two controls: `X07` shows the allowlist alone carries that sentence (so the
word check is what stops it), and `X08` shows the brief's own limit wording is
not mistaken for a disclosure.

---

## S10c (high) — the internal record's limits block was empty

**Was.** `internalRecord()` declared a `limits` object with `price_approved`,
`current_customer_net_price`, `supplier_cost`, `no_raw_invoices` and
`no_credentials`. None of those five names is declared in `contracts.js`, so
`buildAllowed()` walked into the container and dropped every value in it. The
written record carried `"limits": {}` — a record that claims to state its limits
and states none, which is worse than omitting the section.

**Now.** The block is carried in the form the contract already declares: an array
of statements under the permitted `limits` key, which the allowlist does not
filter. All five limitations are written out in plain words. The array satisfies
`SAFE-05 S01c` too, because `Array.isArray(limits) && limits.length > 0`.

**A second instance of the same fault, found while verifying this one.** The
`review` section had the same problem. `review` is a case section, not a scenario
or result field, so `declaredFields()` does not cover its keys; the written record
came out as `"review": {"owner_role":"case_owner","state":"ready_for_review"}`,
with the case owner's own explanation and note dropped. The revision `history` had
it twice over: `export.js` read `caseObject.history`, a key the case object does
not carry (the interface passes it in `extra`), so the log was written as `[]`
even when revisions existed — and the revision keys were not declared either, so
it would have been written as an array of empty objects even once the source was
fixed.

**Before / after, on the same input.**

```
before:  limits key present: true | limits value: {} | review: {"owner_role":"case_owner","state":"ready_for_review"}
after:   limits: 5 statements incl. "No price in this record is approved." and "No credentials are carried in this record."
         review: owner_role, state, next_action, next_update_due, explanation, note
         history: revisions written out with revision, state, note (was [])
```

**Command proving it.**

```
node --test tests\export_shipped.test.mjs
```

`X10` and `X11` read the block in memory and in the written bytes. `X09b` asks the
same question of every internal section, so a rule that "states its limits" cannot
be satisfied by an empty shell.

**The route taken, and the contract change requested.** The clean fix is for the
contract to declare the five leaf names. `contracts.js` is frozen and this build
did not edit it, so the statements were carried as an array under the key the
contract already permits. See "Contract change requested" below.

---

## S09b (high) — a restricted word inside a compound file name was not caught

**Was.** The name check matched a whole word between word boundaries, so
`supplier_cost_list_2026.xlsx`, `gross_margin_report.xlsx`, `my_cost_file.xlsx`,
`parts_purchase_price.xlsx` and `invoices_2026.xlsx` were all accepted: the
underscores join the words into one token and no boundary falls inside it.

**Now.** `checkAttachmentName()` flattens the separators, then matches:

- a restricted *stem* at the start of a token — `cost`, `invoice`, `margin`,
  `markup`, `profit`, `discount`, `rebate`, `billing`, `purchase`, `landed`,
  `supplier`, `price`, `kickback`. This catches `invoices_2026`, `costing_2026`,
  `my_cost_file` and `supplier_cost_list`;
- a short token *exactly* — `gp`, `fx`, `fob`, `jpy`. So `gpx_export_2026.csv` is
  not mistaken for `gp`;
- a known two-word measure written with no separator at all —
  `grossmarginreport.xlsx`, `pricelist.xlsx`, `partscost.xlsx`. A token rule
  cannot see these because the whole name is one token and it is not a substring
  of a restricted word in a way that a reader would call a match, so they are
  listed explicitly rather than pretended away.

**Before / after, on the same inputs.**

```
before:  no such check existed in the shipped module (checkAttachmentName: undefined)
after:   refused 11 compound names and 5 one-word names;
         "grossing_up.xlsx" and "gpx_export_2026.csv" are not refused
```

**Command proving it.**

```
node --test tests\export_shipped.test.mjs
```

`X12` covers the reviewer's five names plus hyphens and stems, `X12b` the
one-word form, and `X13` is the opposite control: a check that refuses everything
is not a check, so six ordinary names — including `gpx_export_2026.csv` — have to
pass.

The name check is a convenience. The control is the recipient allowlist and, in a
deployed system, the permission decision, which needs a server this component does
not have. `src\data\export.js` is a browser module and this is a browser-side
check; it is not access control.

---

## S01c (medium) — the saved brief did not say what it was

**Was.** The written brief's top-level keys were the six containers
(`reference`, `offer`, `price`, `quantity`, `customers`, `limits`), so a reader of
the file — or a checker — saw `schema` as `undefined`. The schema marker was
declared in the module and never reached the file.

**Now.** `schema`, `contract_version`, `recipient` and `audience` are written at
the top level, beside the containers. The container structure is unchanged, so
this is an addition and not a rearrangement of the offer the recipient reads.

```
before:  top-level keys: reference, offer, price, quantity, customers, limits | parsed.schema: undefined
after:   top-level keys: schema, contract_version, recipient, audience, exported_at,
                          reference, offer, price, quantity, customers, limits
         parsed.schema: "isze-pricing-member-brief"
```

**Command proving it.**

```
node --test tests\export_shipped.test.mjs
```

`X14` reads the written bytes, checks the four identity fields, and then checks
that all six containers and the part number and both prices are still there, so it
cannot pass by rearranging the brief.

---

## The check that distinguishes a construction from a filter

Kept, because it is the one that matters. `X16` moves the internal parts cost from
60 to 41.75 — and the margin and the gross-profit figures with it — and requires
the member brief to come out **byte-identical**. A filter would let the change
reach the brief; a construction cannot, because none of those values is ever
copied across.

```
before:  brief bytes identical before and after the internal cost moved from 60 to 41.75
after:   brief bytes identical before and after the internal cost moved from 60 to 41.75 (1276 bytes)
```

`X17` keeps it honest by requiring the internal record to still carry the cost, so
the mutation proof cannot pass by an internal record that carries nothing.

---

## What was not done, and what is not claimed

- `src\output\recipients.js` was **not** edited. It is the reference this build
  ported from, and it is still the module the two remaining acceptance failures
  are pointed at.
- `src\data\contracts.js` was **not** edited. It is frozen.
- Nothing under `src\engine\`, `src\ui\`, `src\case\`, `tools\build.py`,
  `tests\accept\` or `dist\` was edited by this build.
- A browser-side check is not server-side access control. Nothing here is evidence
  that a hosted page would be safe: there is no server, so there is no
  server-side permission to test. Production sign-in, organisation membership and
  revocation remain unimplemented.
- `dist\ISZE_AIM_Pricing_Decisions_v04_INTERNAL.html` has **not** been rebuilt
  since these fixes. The file on disk contains an earlier revision of
  `src\data\export.js`. The disk-byte checks (`SAFE-05 S01c`) pass against it
  already; the in-memory checks (`ACCEPT-04 D13`, `SAFE-05 S09b` and `S10c`) read
  the current source and pass now. A rebuild by the integration owner would put
  the same code in the artifact.

## Contract change requested

For the integration owner, not made here:

1. **Declare the five limits leaf names** so the internal record can carry its
   limits as a structured block instead of the statements array it uses now:
   `price_approved`, `current_customer_net_price`, `supplier_cost`,
   `no_raw_invoices`, `no_credentials`.
2. **Declare the review section's keys** (`review` is a case section, so
   `declaredFields()` does not reach inside it): `explanation`, `owner`, `status`,
   `note`, `outcome`.
3. **Declare the revision log's keys**: `revision`, `recorded_at`, `supersedes`,
   `recorded_by`, `note`.

Until (1) is declared, the internal record states its limits as an array of five
sentences. That is readable and complete, but it is a workaround: a structured
block is what the record was designed to carry, and the statements array is only
safe because the allowlist happens to leave string arrays alone.

## Acceptance counts

Run before and after, on the same machine, with no edits to `tests\accept\`.

| Suite | Before | After |
|---|---|---|
| `node --test tests\export_shipped.test.mjs` | did not exist | **25 pass / 0 fail** |
| `node tests\accept\accept_04_participant.cjs` | 11 pass / 2 fail | **13 pass / 0 fail** |
| `node tests\accept\accept_05_08_safety.cjs` | 13 pass / 3 fail | **14 pass / 2 fail** |
| `node tests\export_bytes.test.mjs` (retired module) | 11 pass / 0 fail | 11 pass / 0 fail |
| `node tests\run_tests.cjs` (developer suite) | 60 pass / 0 fail | 60 pass / 0 fail |

`ACCEPT-04` went from 2 failures to 0. `SAFE-05/08` went from 3 to 2.

The two remaining `SAFE-05` failures are `S09b` and `S10c`, and both are asserted
against `src/output/recipients.js` — the **retired** module that
`tools/build.py` does not assemble. The same two questions now pass against the
shipped module; `X21` in `tests\export_shipped.test.mjs` puts that on the record
using the reviewer's own inputs. They will keep failing until the reviewer
re-points them at `src/data/export.js`, which this build cannot do because
`tests\accept\` is reviewer-owned.
