# Why most tenders have no GPS € figure

Snapshot used below: **186** opportunity families · **3** with a GPS €/year (post product-fit) · **183** without · **13** state a vehicle count in the notice (**7.0%**) · **173** do not (**93.0%**). Of the 13 with a count, most still lack GPS € (no map and/or van/LCV product-fit). Historical note: before product-fit, **6** rows carried GPS € including vans (~€30.4k floor) — that is **not** the live commercial floor (€1,488).

---

### 1. What “sized” vs “unsized” means

**Sized:** the notice states how many vehicles, *and* that country has a GPS wallet rate we can multiply by — so we can show addressable GPS €/year.

**Unsized:** we cannot show that GPS € figure — usually because the notice never says how many vehicles (sometimes the country has no GPS rate on file either).

---

### 2. Why fleet size is missing so often

This is a **source limitation, not a dashboard bug.** Public tender list feeds (especially TED) almost never publish a vehicle count. Our extractor only fills the Fleet column when the title/description literally says something like “20 Transporter” or “83 autovehicule”. On this snapshot that happens for **13 of 186** opportunities (**7.0%**). We **never invent** a fleet size to fill the gap.

---

### 3. What we still do with unsized tenders

They stay in the pipeline as real leads: buyer, title, country, deadline (when published), Fit/decision, R&M flag, and links for a human chase. You can still tender-watch and prioritise them. Missing fleet does **not** mean “fake tender” or “drop it.”

---

### 4. What we cannot claim without fleet

Without a published vehicle count we **cannot** compute GPS addressable €/year. Empty GPS cells are **null**, not €0. We do not invent addressable parts revenue, win rates, or “expected revenue.”

---

### 5. The two legitimate money signals (neither invents the other)

| Signal | When it appears | What it is |
|---|---|---|
| **(a) GPS €/year** | Fleet count known **and** country maps to a GPS SPU row | `fleet × (max wallet € / UIO units)` for that market |
| **(b) Published contract value** | Notice publishes an estimated contract value | The buyer’s stated deal size — **not** GPS parts € |

If (b) exists and (a) does not, show contract value as a separate money signal. Never convert one into the other.

---

### 6. What would raise the sized count for real

Honest options only — no fake fills:

1. **TED (and other) detail fetch** — pull full notice text where vehicle counts often live (needs auth / detail API; list feed is thin).
2. **Better extraction** on text we already have — already multilingual + guarded; on this snapshot description adds **0** new hits (only ~5% of notices even have a description).
3. **Ask the buyer / open the PDF** — human reads the lot and types the count into outcomes when chasing.

Of the **13** with a fleet count today, **6** get a GPS € figure; **7** (France / Poland / Italy) have a count but **no GPS distributor mapping** in `country_distributor_map.yaml` — so still no GPS € until those markets have a wallet row.

---

**Bottom line for managers:** You *can* run a tender pipeline without fleet size. You *cannot* size the GPS parts wallet without it. The empty GPS column means “count not published,” not “worthless lead.”

---

## Engine honesty check (Part C)

**Question:** Can fleet extraction be improved without inventing numbers?

| Lever | Result on this snapshot |
|---|---|
| Re-parse title + description | **0** new hits — only **10 / 202** notices (5%) even have a description; all current fleet hits already come from the title |
| Multilingual patterns already live | Already in `extract_fleet_size` (DE/FR/IT/ES/PL/…); further pattern tweaks risk false positives (years, lot refs) |
| TED detail / full PDF text | Real lever — list feed rarely carries vehicle counts or contract value (value populated: **0 / 186** here) |
| Inventing fleet from CPV or averages | **Forbidden** — null stays null |

**Verdict: WONTFIX for “fill more fleet cells from current list fields.”** Before/after sized counts if we forced description re-extract: **6 → 6** GPS-sized, **13 → 13** with fleet. Raising the count requires richer source text (TED detail) or human entry — not a smarter guess.
