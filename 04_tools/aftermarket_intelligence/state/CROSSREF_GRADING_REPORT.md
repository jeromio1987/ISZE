# Cross-reference grading (task 2.2)

Built 2026-10-01T16:34:48+00:00 by `grade_crossref_edges.py`.

- rival edges graded: **6,455**
- confirmed: **1,156**
- likely: **125**
- doubtful: **4,902**
- reject: **272**
- usable (confirmed + likely): **1,281** edges, 286 counterpart numbers
- of the usable, carrying a price: **592**

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

## Limit, stated plainly

This separates edges that are safe to act on from edges that need eyes. It cannot confirm a match a human could.
