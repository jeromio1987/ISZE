# Product-fit gate (GPS € honesty)

**Problem:** The engine treated every `fleet × GPS SPU` as “Isuzu can win this.” Poșta Română (83 utilitare / vans via leasing) showed **€20,750/yr** GPS addressable — as if a D-Max win. It is not.

**Rule:** Classify product reality first. GPS € only for segments that match the GPS product mix. Fleet stays visible when extracted. Null ≠ 0. No invented N-Series SPU. No “expected revenue.”

**Desk rule (stricter, 2026-08-25):** Postal/courier panel vans are **hard-dropped** from opportunities — not kept as GPS-null clutter. See `_NOT_FOR_US_GATE.md`.

---

## Segments

| Code | Operator label | GPS €? | On desk? |
|---|---|---|---|
| `pickup` | Pickup / D-Max-shaped | Yes (if fleet + distributor SPU) | **Keep** |
| `truck` | Truck / chassis | Yes (if fleet + distributor SPU) | **Keep** |
| `lcv_van` | Postal van / LCV | **No** | **Hard-drop** vehicle buys (not-for-us) |
| `rm_only` | R&M only — no vehicle buy | **No** | **Keep** (real fleet R&M) |
| `weak` | Generic vehicle — weak fit | **No** | In data; default UI = CV |

Priority: pickup > truck > lcv_van > rm_only > weak.  
`gps_spu_by_distributor.csv` has **one** SPU per distributor (pickup/network UIO). There is **no** N-Series line — do not invent a smaller van wallet.

Hebrew ISR keep-signals / EU noise exclusions (SEND, CPV 600, etc.) are unchanged. This gate changes **GPS/segment** logic; `_NOT_FOR_US_GATE.md` removes postal/panel-van rows from the opportunity list.

---

## Poșta Română — before / after (evolution)

| Field | GPS-null era | Not-for-us era (now) |
|---|---|---|
| Buyer | C.N.POSTA ROMANA S.A. | **Gone from opportunities** |
| Product segment | `lcv_van` | classified then **hard-dropped** |
| GPS addressable / yr | null (was €20,750 fantasy) | n/a — row not on desk |
| Why | Van ≠ pickup GPS | Postal panel van ≠ Isuzu play |

---

## Code touchpoints

- `isze_core_v3.py` — `classify_product_segment` / `attach_product_segment` / `GPS_ELIGIBLE_SEGMENTS` / `passes_not_for_us_gate`
- `gps_pms_linkage.py` — product-fit gate before computing GPS €
- `build_dashboard_v4.py` — default product filter **CV**; gate re-applied on rebuild

Unsized clarity (`_WHY_UNSIZED_GPS.md`, “No fleet count in notice” KPI) stays — product-fit is an *additional* reason GPS can be null when fleet *is* known on remaining rows.
