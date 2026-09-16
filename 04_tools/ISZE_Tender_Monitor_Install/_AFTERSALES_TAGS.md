# Aftersales tags — Jerome cheat sheet

**What:** Each opportunity can show **aftersales hooks** when the notice text (or CPV) mentions service / parts / warranty language. Vehicles-only notices stay empty — we never invent a service contract.

**Where:** v4 opportunity table **Aftersales** column · detail panel · KPI “Aftersales hooks” · sheet `isze_dashboard_v4_opportunities.xlsx` (Aftersales column).

**Not the same as:** GPS € (parts wallet if won) or PMS demand rows. Those stay separate.

---

## Tags (chip colours)

| Tag id | Chip label | Means (only if matched in notice) |
|--------|------------|-----------------------------------|
| `service_contract` | Service contract | Maintenance / service *contract* language (EN/FR/DE/Nordic/HE/…) |
| `repair_maintenance` | R&M | Repair & maintenance outsourcing — also when CPV `501xx` or existing `rm_contract` |
| `parts` | Parts | Spare parts / parts supply / Ersatzteile / pièces / … |
| `extended_warranty` | Ext. warranty | Extended warranty / garantie étendue / … |
| `full_service_lease` | Full-service lease | Wet lease / full-service lease *with* maintenance language |

Empty → chip **vehicles only** (tooltip: no service/parts/warranty language found).

---

## Fields on each opportunity

| Field | Content |
|-------|---------|
| `aftersales_tags` | List of tag ids above (stable order) |
| `aftersales_summary` | Short human string, e.g. `Service contract · Parts` — or `null` if none |
| `aftersales_match_tip` | One-sentence hover: what was matched |
| `aftersales_evidence` | Tag → matched phrases / CPV (debug) |
| `rm_contract` | **Unchanged** legacy boolean (R&M outsourcing / CPV 501) |

---

## Rules

1. **Evidence only** — title, description, CPV desc, or CPV `501*`. No guesswork.
2. **Null when nothing matched** — “vehicles only”, not a fake service deal.
3. **Multilingual** — keywords cover EN + FR/DE/NL/ES/IT/PL/Nordic/HE (and cousins). Extend lists in `isze_core_v3.py` if a market keeps slipping through.

Rebuild: `python build_dashboard_v4.py` (or weekly bat). Open: `OPEN_isze_dashboard_v4_opportunity.cmd`.
