# Cross-reference grading (task 2.2)

Built 2026-10-02T07:17:31+00:00 by `grade_crossref_edges.py`.

- rival edges graded: **6,455**
- confirmed: **1,197**
- likely: **855**
- doubtful: **4,240**
- reject: **163**
- usable (confirmed + likely): **2,052** edges, 507 counterpart numbers
- of the usable, carrying a price: **903**

## The boundary that shaped the method

100% of the rival edges are Eucon-sourced. Jerome's standing rule bars Eucon rows from DeepSeek or any outside-EU service, so the plan's original method for this card — DeepSeek pro judging (prompt 6.2) — was **not** used. Grading here is local and deterministic.

## What the tiers mean

| tier | meaning |
|---|---|
| confirmed | corroborated by 2+ independent source files across 2+ vintages, no trap flag |
| likely | 2+ source files, or a single source where our own part carries a category |
| doubtful | a single source file, or one of the two known traps is set |
| reject | the edge contradicts itself, or the number is not shaped like a part number |

A 'confirmed' tier means corroborated by independent files. It is **not** verified against a manufacturer catalogue, and it is not a substitute for that.

## Second source: Spareto (added 2026-10-02)

Spareto `/oe/<isuzu number>` pages, file `spareto_crossref.csv`. An edge moves up ONE tier when Spareto lists the same (our part, rival number) pair under an agreeing brand; never down. The Eucon-only tier is kept in `tier_eucon_only`.

- edges whose pair Spareto lists: 1,600 (brand differs, not moved: 60)
- edges moved: 921 (doubtful -> likely: 771, likely -> confirmed: 41, reject -> doubtful: 109)
- Spareto pairs not in the graph (new, single-source, doubtful): 707 -> `crossref_spareto_new_edges.csv`

Spareto's own upstream source is not stated on its pages: it is independent of Eucon as a pipeline, not proven independent upstream.

## Limit, stated plainly

This separates edges that are safe to act on from edges that need eyes. It cannot confirm a match a human could.
