# GPT pack — sales / warranty / sales-to-dealer

**Built:** 2026-09-20 05:40 UTC
**Folder:** `C:\Users\jerom\Desktop\claude\ISZE\01_data\15_gpt_safe\gpt_pack_2026-09-20`

## Why three cores (do not blend them)

| Layer | File | What it is | Why it matters |
|---|---|---|---|
| **1. ISZE → distributor billing** | `01_all_sales_isze_to_distributor.csv` | What we invoiced distributors (line grain from `sales_fact`) | The euro we actually booked. GPS capture %, mix, and “what we billed” start here. Israel: split on `sold_to_sap` **1797 = UMI**, **1799 = UTI** — never blend. |
| **2. Warranty claims** | `02_all_warranty.csv` | Claim lines (`dataset=warranty_raw_grain`) plus commercial summary tables (other `dataset=` tags) | Quality / loyalty / who-pays. Not a substitute for scheduled service demand (consumables barely appear). |
| **3. Distributor → dealer sales** | `03_all_sales_to_dealer.csv` | What distributors sold into their dealer networks | The only view of sell-through. Needed for leakage vs billing, dealer packs, and “share with customers”. Coverage is partial by market. |

## Extra layers (advantages for analysis / customer share)

| File | Role |
|---|---|
| `04_gps_spu_by_distributor.csv` | Target spend per truck vs billed — the GPS denominator |
| `05_pms_opportunity_matrix.csv` | Category gaps in euro (clutch, pads, …) — customer opportunity ranking |
| `06_pms_capture_by_db_year.csv` | PMS total capture by market / year |
| `07_uio_ld_n35_share.csv` | Light vs heavy truck mix inside LD (Portugal **0.6364** from official registrations) |
| `08_wallet_waterfall.csv` | Ceiling build-up (do not silently rebuild; read-only for GPT) |
| `09_aim_pn_classification_v2.csv` | Parts family spine for mix / leakage by family |
| `10_dealer_sellout_aim_gps_vs_billing_2025.csv` | Billing vs sales-to-dealer bridge where coverage exists |
| `11_mix_genuine_bvp_pms.csv` | Genuine vs total mix (total capture stays primary) |
| `12_network_percentile.csv` | Peer ranking context for customer conversations |

## Hard rules for GPT

1. Lead findings with **euro + parts family + vehicles in service** — never piece counts alone.
2. Primary PMS lens = **total** sales / capture; genuine is an extra lens.
3. UTI ≠ UMI; IUK ≠ ITUK.
4. Do not invent a price increase narrative; pricing increase figures are out of scope for this pack.
5. Warranty cannot prove maintenance intervals.

## Build receipt

```json
{
  "core": [
    {
      "file": "01_all_sales_isze_to_distributor.csv",
      "rows": 514037,
      "cols": 12,
      "mb": 51.19
    },
    {
      "file": "02_all_warranty.csv",
      "rows": 62059,
      "cols": 61,
      "mb": 9.11
    },
    {
      "file": "03_all_sales_to_dealer.csv",
      "rows": 334182,
      "cols": 14,
      "mb": 61.45
    }
  ],
  "extras": [
    {
      "file": "04_gps_spu_by_distributor.csv",
      "rows": 89,
      "cols": 21,
      "mb": 0.02,
      "source": "01_data/00_derived/gps_spu_by_distributor.csv",
      "status": "OK"
    },
    {
      "file": "05_pms_opportunity_matrix.csv",
      "rows": 1008,
      "cols": 13,
      "mb": 0.11,
      "source": "01_data/00_derived/pms_opportunity_matrix.csv",
      "status": "OK"
    },
    {
      "file": "06_pms_capture_by_db_year.csv",
      "rows": 3024,
      "cols": 16,
      "mb": 0.4,
      "source": "01_data/00_derived/pms_capture_by_db_year.csv",
      "status": "OK"
    },
    {
      "file": "07_uio_ld_n35_share.csv",
      "rows": 9,
      "cols": 6,
      "mb": 0.0,
      "source": "03_analytics/Isuzu/prism/data/uio_ld_n35_share.csv",
      "status": "OK"
    },
    {
      "file": "08_wallet_waterfall.csv",
      "rows": 54,
      "cols": 16,
      "mb": 0.01,
      "source": "01_data/00_derived/wallet_waterfall.csv",
      "status": "OK"
    },
    {
      "file": "09_aim_pn_classification_v2.csv",
      "rows": 164667,
      "cols": 16,
      "mb": 24.58,
      "source": "01_data/00_derived/aim_pn_classification_v2.csv",
      "status": "OK"
    },
    {
      "file": "10_dealer_sellout_aim_gps_vs_billing_2025.csv",
      "rows": 4,
      "cols": 14,
      "mb": 0.0,
      "source": "01_data/00_derived/dealer_sellout_aim_gps_vs_billing_2025.csv",
      "status": "OK"
    },
    {
      "file": "11_mix_genuine_bvp_pms.csv",
      "rows": 1504,
      "cols": 24,
      "mb": 0.28,
      "source": "01_data/00_derived/mix_genuine_bvp_pms.csv",
      "status": "OK"
    },
    {
      "file": "12_network_percentile.csv",
      "rows": 409,
      "cols": 8,
      "mb": 0.04,
      "source": "01_data/00_derived/network_percentile.csv",
      "status": "OK"
    }
  ]
}
```
