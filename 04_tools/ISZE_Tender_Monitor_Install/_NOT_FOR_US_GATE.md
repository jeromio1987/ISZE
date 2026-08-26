# Not for us — postal / courier panel vans leave the desk

**Rule:** If it is not an Isuzu play, it must **not appear** as an opportunity. GPS-null alone is not enough — that still clutters the desk “just in case.”

---

## Why postal / courier vans are out

Buyers of **postal / courier panel vans** (Poșta Română “utilitare”, post-purchase van fleets, Transporter / Kastenwagen / bestelwagen leasing) buy **Ford / Fiat / Stellantis / VW** panel vans.

Isuzu’s exclusive play here is **D-Max (pickup)** and **N-Series-shaped truck / chassis cab** — not a postal panel van. Keeping those rows as leads with GPS € stripped still wastes operator time.

| Buyer example | What they buy | Isuzu chance as exclusive play |
|---|---|---|
| C.N. POSTA ROMANA S.A. | 83 autovehicule utilitare / leasing | Near **zero** |
| Stuttgart / DE “Transporter” | Panel vans | Near **zero** |
| Bestelwagen / furgon / Kastenwagen fleets | Panel vans | Near **zero** |

---

## What stays

| Keep | Why |
|---|---|
| **Pickup** / D-Max-shaped | Core product |
| **Chassis cab / tipper / truck** (N-Series-shaped) | Core commercial vehicle |
| **Real fleet R&M / parts** on commercial vehicles | Aftersales desk — when not a postal org and not a panel-van purchase |

---

## What is hard-dropped (not merely GPS-null)

| Drop | Examples |
|---|---|
| Postal / courier buyers & postal van fleets | Poșta Română, Hrvatska pošta, “postal van” titles |
| Panel-van / utilitar / transporter / bestelwagen **buys & leasing** | “20 Transporter”, “83 utilitare leasing”, Kastenwagen |
| `lcv_van` vehicle buys without a real CV aftersales-only keep | TED “Vans” pure panel fleets |
| Pure passenger van fleets with no LCV-truck signal | Already cut by Isuzu noise gate |

---

## Desk default

Dashboard product filter defaults to **CV (pickup + truck)**.  
“All product segments” still exists for audit; postal panel vans should already be gone from the snapshot.

---

## Code

| Piece | Role |
|---|---|
| `passes_not_for_us_gate` / `row_passes_not_for_us_gate` | Hard drop |
| `row_passes_isuzu_selection_gate` | Isuzu noise/CPV **then** not-for-us |
| `classify_product_segment` | Still labels `lcv_van` — gate removes them from opps |
| `build_dashboard_v4.py` | Re-applies gate on rebuild; default filter = CV |
| `_PRODUCT_FIT_GATE.md` | GPS € honesty (pickup/truck only) — complementary |

CPV `34136` (vans) alone is **no longer** Isuzu-core. Truck-shape regex upgraded so ciężarowe / DMC / N-Series mislabeled TED “Vans” can classify as **truck** and stay.

---

## Snapshot — before / after hard drop

Same pre-gate JSON rebuild (2026-08-25), then parallel coverage agents may add CV later — vans stay out.

| Metric | Before not-for-us | After hard drop (same feed) |
|---|---:|---:|
| Opportunities | **230** | **188** (−42) |
| Notices | 256 | 208 (−48) |
| `lcv_van` on desk | 50 | ~0–3 (parts-only survivors) |
| C.N. POSTA ROMANA S.A. | present (`lcv_van`, GPS null) | **gone** |

Dashboard default product filter: **CV (pickup + truck)**.
