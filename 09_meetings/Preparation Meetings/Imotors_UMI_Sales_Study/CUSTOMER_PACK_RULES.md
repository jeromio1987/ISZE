# Customer deep-study pack rules (persist across Vn)

**Agent sync:** 2026-07-26 · Applies to `Imotors_UMI_Sales_Study` **V4+** (and legacy V3.1).

Internal agent rules for building packs. **Customer-facing HTML/PDF/Excel = Mode A** — no agent slang, no “UTI≠UMI”, no “never blend”, no “IML v7” / “Model B”.

## Hard rules (do not regress)

1. **One pack per customer** — no dual I Motors↔UMI compare decks for customer meetings.
2. **At most one light benchmark graph** — this customer vs **network / LCV average** only. Never name-compare peer countries on GPS.
3. **GPS:** show **now vs past** capture **%** only (e.g. CY2024→CY2025→YTD run-rate). **Do not** chart other countries / peer DBs. Absolute €/SPU footnote only if needed.
4. **PMS:** display capture **% hit only** (no € gaps). **Never silent-cap at 100%** — if capture > 100%, diagnose (UIO/scope, interval, expected qty, category mismatch, blower overcount, line_type) and either fix the cut or **exclude with an explicit reason** / footnote the artefact. Put **IML service schedule** assumption text above every PMS graph. Never “IML v7” / “Model B” on external packs. Primary = **total** capture.
5. **Source mix:** JP/TH/LOCAL share charts from Power BI when available (I Motors / UMI). Skip silently if no PBI sidecar.
6. **Product family:** share **%** now vs past — never € bars. Customer text: “ISZE parts classification” — **never say PR00**.
7. **PN:** FY vs FY (Apr–Mar), exclude REBATE / non-part / credit (SaTy CR·RE) lines.
8. **PN depth (V4+):** for each customer, quantity-based vanished / new / continuing droppers, plus a **channel-shift test** on the largest qty crashes (customer Δ vs rest-of-network Δ). Mode A verdict labels only: customer-local decline / network-wide decline / volume shifted elsewhere.
9. **UMI ≠ UTI (build rule)** — never emit the string `UTI` in the UMI external pack. Customer agenda Mode A: “IDS Israel covers the UMI network only.” Blunt UTI≠UMI only in `SPEAKER_NOTES_Jerome.md` (Mode B).
10. **Reconcile** Power BI SALES vs ISZE billing when overlapping figures exist; always state fiscal definition + billing max.
11. **Scope:** V4 builds **all** in-scope distributors (see `DB_Sales_Order_Study/study_state.json`), not only meeting customers.

## Fiscal years

Latest **two complete** FYs only. With billing through 2026-03-31 that is **FY2024 vs FY2025**. Do not present a partial FY2026 as a complete year.

## Rebuild

```powershell
python "$env:ISZE_ROOT\09_meetings\Preparation Meetings\Imotors_UMI_Sales_Study\_build_v4_customer_packs.py"
```

Outputs: `V4/` + copies of I Motors/UMI to this folder + all packs to `../DB_Sales_Order_Study/deep_v4/`.
