# Portugal (I Motors) — annual km mileage

**Filed:** 2026-07-26  
**Home:** `01_data/08_Distributor/` (DATA_MANIFEST §08)

## Figure

| Field | Value |
|-------|------:|
| Country | PORTUGL (Portugal) |
| Distributor | IMOTORS LDA |
| VIN count in sample | **1,596** |
| **Average mileage per year** | **22,742 km/yr** |

Rounded for discussion: **~22,700 km/yr**.

## Source (mail + attachment)

- **Thread:** `RE: LCV Oil filters data` (IMIT Kawin ↔ ISZE, Jul 2026)
- **Attachment:** `EU Mileage.xlsx` (saved as `EU_Mileage_by_country_IMG_2020-11_to_2026-06.xlsx`)
- **Sheet:** `Europe Mileage (20'Nov- 26'Jun)` — columns: CountryName, DistributorName, Count of VIN, Average of Mileage per year
- **Framing in mail:** Kawin — average mileage “same data as from IMG… same for all European markets” (file itself is **per-country**, not a single Europe flat rate). Jerome had asked for D-Max annual km.

## Scope note (important)

This is an **LCV / D-Max style VIN-mileage sample** shared on the LCV oil-filter PMS ask — **not** a measured N75 CV R&M mileage for Portugal.

| Scope | Portugal km/yr | Status |
|-------|---------------:|--------|
| LCV (this file) | **~22,742** | Confirmed from IMG EU Mileage xlsx |
| N75 / CV truck | — | **Not in this file** — still open for I Motors / R&M ask |

Peers in same file (same definition): UMI Israel **34,443**; UK **24,481**; Europe grand total **25,600** (n=76,208 VINs).

## Related artefacts

- Workbook: `01_data/08_Distributor/EU_Mileage_by_country_IMG_2020-11_to_2026-06.xlsx`
- Blower network note: `01_data/08_Distributor/Blower_filter_network_capture_CY2025.md`
- Pipeline default (N75): `annual_km_yr: 20000` in `pms_capture_assumptions.yaml` — do **not** silently overwrite with this LCV figure
