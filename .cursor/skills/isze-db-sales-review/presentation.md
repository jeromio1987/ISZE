# Presentation — shared Sales Review (audience first)

Companion to `SKILL.md`. Every slide and takeaway is for the **distributor in the room** — not for agents, not for Jerome’s pipeline notes.

**Craft reference (Sep 2026):** `01_data/Presentaion style/ISZE_UMI_Customer_Executive_Redesign.pptx` — decision-led meeting core, not a topic checklist. HQ/strategy packs may follow the McKinsey prototype in the same folder; that voice stays out of distributor rooms.

## Audience test (fail closed)

Read each bullet out loud. If a parts manager who never opened SAP would ask “what does that mean?”, rewrite it.

| Say (audience) | Never say on the slide |
|----------------|------------------------|
| Stock orders vs urgent orders (share of coded €) | SaTy, sold-to, export file, blank %, tagged extract |
| Official sales (Power BI) | PBI≠SAP, loader, window_label, `_summary.json` |
| Shell lubricants (on hold) | `5500*`, UNCLASSIFIED, PN mask |
| Dealer network score vs country average | IDS bucket code, ranking workbook path |
| Capture vs potential for the trucks in service | GPS denom archaeology, Model B, PRISM lane |
| Parts billed / target spend per truck | wallet / wallet € |
| Sales to dealer | sell-out / sellout / Sales-to-Dealer as a title |
| Shared pack / internal notes | Mode A / Mode B |

Internal nicknames (IML v7, Model B, PRISM, UTI blend, etc.) stay in chat / speaker notes internal only — see `isze-external-iml-language.mdc`.

## Four questions before any shared claim

1. **Mirror** — Does the opening sales slide match their Power BI within rounding?
2. **Audience** — Would a non-ISZE person understand every word without a glossary?
3. **No false zeros** — Any chart implying no business when € clearly exists?
4. **Re-derive** — After a data fix, were conclusions rewritten — not just charts refreshed?

## Meeting design (decision-led core)

Two artefacts, one build:

| Layer | Role | Typical length |
|-------|------|----------------|
| **Meeting core** | What you speak in the room | ≈ 10–12 slides |
| **Appendix** | PN tables, SPA process, R&M questions, analytical deep dive | After the first closing slide |

### Meeting-core sequence

1. Cover  
2. **Executive storyline** — 3–4 facts the customer must accept + **3 joint decisions** the meeting must leave with (not a topic agenda)  
3. Performance — official cut / YTD; headline is a **finding sentence**  
4. Mix — commercial H1: growth is real somewhere; leakage sits elsewhere  
5. **Leakage** — top 2–3 categories as cards (from→to €, one question, **recommended first action**). Not one slide per family with PN lists  
6. **Opportunities** — short growth list + **Repeatable / Protectable / Actionable** decision lens  
7. GPS — capture vs uncaptured € (or amount view) + one meeting question  
8. Service-parts pilot — pick the first category vs network  
9. IDS (if data) — spread vs network, not a ranking dump  
10. FY2027 target — bridge in plain English  
11. **Joint plan** — 3–4 workstreams with owners (lubricants / pilot category / SPA / part-level sales-to-dealer data)  
12. Closing  

### Appendix (not spoken by default)

- Per-category PN decline / growth deep dives  
- New Business validation queue  
- SPA process cards, R&M discussion questions, detailed data-request cards  
- Analytical deep dive from `build_full_deck.py` (FY GPS excl. warranty, mix, AIM, warranty lenses)

## Slide craft

- **Headline = finding sentence.** “FY2027 YTD is budget-positive, but last year is still negative” — not “Parts Performance — Exhaust.”
- One story per slide. Boom and decline cannot both be the headline.
- Lead with their official cut when we have it; our detail supports it.
- Plain verbs: up / down / on hold / not driving price — not “definition gap” or “reconcile”.
- Call out only material outliers the customer already feels (e.g. Shell oils quiet after a spike).
- Order urgency: say whether it is / isn’t lifting billed price — with SOR/VOR shares only if those labels are already used with that customer; otherwise “stock vs urgent”.
- IDS: the network that sat the assessment (Israel = UMI dealers).
- PN detail belongs in the appendix unless the customer already named that part number.

## Anti-patterns (banned on shared)

- Topic-list **agenda** as the second slide (use storyline + decisions).
- One decline slide per category with long PN lists in the spoken path.
- Pipeline excuses (“export lag”, “payer name”, “sold-to filter”).
- Copying another DB’s excludes / notes without Jerome asking for this DB.
- “Best market” bars when best > 100%.
- Hand-written % that don’t match live coded mix.
- Agent slang, file names, or “we fixed the loader” on a customer slide.
- Mode A / Mode B / wallet / sell-out on any slide the customer sees.
