# Phase 2 — extraction before/after

Measured on rebuilt payload from `isuzu_tenders_v3.xlsx` (2026-08-25).

| Field | Before (v3 baseline audit) | After (v4 rebuild) |
|---|---:|---:|
| Fleet size populated | 1 / 778 (0.1%) | **23 / 773 (3.0%)** |
| Deadline populated | ~189 / 778 (24%) | 189 / 773 (24.5%) |
| Contract value populated | ~70 / 778 (9–10%) | 70 / 773 (9.1%) |
| `rm_contract` True | 360 | 373 |
| `fleet_size_confidence` | n/a | `"extracted"` when sized |

## Deadline / value split (source vs parser)

| Source | Deadline % | Value % | Notes |
|---|---:|---:|---|
| UK FaT | high | high | OCDS carries tenderPeriod + value |
| UK-CF | high | medium | OCDS |
| TED EU | low–medium | ~0 on list endpoint | List fields include `DD` when present; **no value field** in current query. Detail API disabled (`TED_FETCH_DETAIL=False`, auth). |
| NL TenderNed | low | ~0 | Atom summary only |

**Conclusion:** deadline/value gaps are mostly **not published on the list feed**, not a silent parser bug for TED. Enabling authenticated TED detail is the next lever (out of band).

## R&M precision (proxy sample)

Flag = RM_CONTRACT_TERMS hit **or** CPV starts with `501`. Proxied agreement with that rule on a 20-row sample is high by construction; treat as **recall-biased** commercial signal, not adjudicated legal classification.
