# GPS/PMS V2 — LCV subtype SSOT (Trooper / D-Max RT / D-Max RG)

**Mode B sparring · locked 2026-09-05**  
**Rule:** Opt2 enabled only when subtype counts exist. Unknown → Opt2 disabled (do not invent).

UIO Overview (`1.UIO Overview`) has **one** LCV mtype — no Trooper/RT/RG rows.

## Network map (`lcv_uio > 0`)

| DB | lcv_uio (2025E) | Subtype source | Status | Opt2 |
|----|----------------:|----------------|--------|------|
| IUK | 47,783 | IMIT LCV aggregate; UK pickup SMMT/DVLA **not in repo** — chase sheet [`IUK_SMMT_LCV_DATA_ASK_SPEC.md`](IUK_SMMT_LCV_DATA_ASK_SPEC.md) | need | off |
| UMI | 18,542 | IML/IMIT aggregate; no Israel gov LCV subtype file | need | off |
| GERMANY | 13,048 | Helwig/IMIT LCV total (Helwig file not in repo) | partial B-candidate | off |
| BELGIUM | 9,480 | IMIT LCV (BE/NL/LUX/PL rollup); Poland SAMAR UIO10 count only | partial | off |
| SWEDEN | 8,443 | IMIT LCV | partial | off |
| NORWAY | 7,929 | IMIT LCV | partial | off |
| PORTUGAL | 4,733 | **Matriculas** TFR/TFS chassis prefixes (RT/RG proxy); no Trooper | partial | **skeleton RT/RG only** |
| GREECE | 3,705 | IMIT LCV | partial | off |
| HUNGARY | 3,734 | IMIT LCV | partial | off |
| CYPRUS | 2,105 | IML low-confidence; no national reg | need | off |
| IRELAND | 1,338 | **SIMI** `isuzuregdata.xlsx`: Trooper vs D-Max+TFS aggregate — **RT/RG not separable** (D-Max parked on RT; RG=0) | partial B | **skeleton ON** |
| FINLAND | 1,204 | IMIT LCV | partial | off |
| ROMANIA | 1,071 | IMIT LCV | partial | off |
| DENMARK | 850 | IMIT LCV | partial | off |
| MALTA | 797 | IML low-confidence | need | off |
| ICELAND | 406 | IMIT LCV | partial | off |

## Paths

| Source | Path |
|--------|------|
| IMIT LCV study | `06_uio/_SourceData/LCV UIO (November 2025)_EU_Study_Imit.xlsx` |
| Ireland SIMI | `01_data/07_UIO/isuzuregdata.xlsx` |
| Portugal Matriculas | `01_data/07_UIO/Matriculas Isuzu SAP.xlsx` |
| UIO buckets | `03_analytics/Isuzu/prism/data/uio_by_model_bucket.csv` |

## Generation mapping (working)

| Jerome label | Chassis / name cues | Schedule PDF |
|--------------|---------------------|--------------|
| Trooper | UBS / TROOPER (SIMI) | **Missing** — see Trooper schedule note |
| D-Max RT | RT56 / RT88 / TFS87-class | `RT56_*.pdf`, `RT88_93_*.pdf` |
| D-Max RG | RG / RG21 / TFR86-class | `RG_*.pdf`, `RG21_*.pdf` |

## Ask (human)

1. **IUK (V20 NEED):** SMMT/DVLA (or IUK) pickup extract with Trooper / D-Max RT / D-Max RG counts — filed on [`06_uio/_CURRENT/V20_SPEC.md`](../../06_uio/_CURRENT/V20_SPEC.md) § Still open.  
   - Monday-ready chase/spec (fields, ease, accuracy, Opt2 acceptance): [`IUK_SMMT_LCV_DATA_ASK_SPEC.md`](IUK_SMMT_LCV_DATA_ASK_SPEC.md)  
   - Prefer stock/car park by vintage+model (not only annual new regs)  
   - Medium-easy if IUK already has SMMT (ITUK CV precedent via Duncan); friction = owner + LCV cut + generation mapping  
   - Good enough for Opt2 = subtype counts mappable to Trooper/RT/RG; total LCV only = still Opt1 / rank B  
   - Draft-only — Jerome contacts Aaron/John (or Koen routes); no weekend send  
2. IMIT: Trooper / RT / RG (or chassis cutoffs) per distributor where no national file.  
3. Confirm Portugal Matriculas generation → RT/RG mapping before quoting Opt2 capture externally.
