# 20260808T084612Z__audit__20260808T072009Z__alloc__t3pct

- **kind** audit · **scenario** 20260808T072009Z__alloc__t3pct
- **utc** 2026-08-08T08:46:12.718893+00:00
- **config sha** `53fcfdd34ce0a895`
- **headline** audit WARN - 14 pass / 2 warn / 0 fail

## Audit

**Verdict: WARN**

| check                                | status   | detail                                                                                                           |   n |
|:-------------------------------------|:---------|:-----------------------------------------------------------------------------------------------------------------|----:|
| rows present                         | PASS     | 213 rows                                                                                                         | 213 |
| non-positive weight                  | PASS     | 0 rows carry zero or negative revenue weight                                                                     |   0 |
| benchmark coverage                   | PASS     | 54/213 rows have no competitive benchmark                                                                        |  54 |
| thin evidence gated                  | PASS     | 71 rows below min_n=3, correctly held                                                                            |  71 |
| FX rate age                          | PASS     | FX fixed 311 days ago                                                                                            | 311 |
| index reconciles                     | PASS     | delivered 3.000000% vs target 3.000000%                                                                          |   0 |
| caps respected                       | PASS     | 0 lines above their cap                                                                                          |   0 |
| floors respected                     | PASS     | 0 lines below their floor                                                                                        |   0 |
| sign rule respected                  | PASS     | 0 lines move against their own gate                                                                              |   0 |
| no NaN deltas                        | PASS     | 0 NaN                                                                                                            |   0 |
| no movement on unbenchmarked premium | PASS     | 0 lines moved without a benchmarked target                                                                       |   0 |
| every moving line has a reason code  | PASS     | 0 moving lines with no reason                                                                                    |   0 |
| evidence freshness                   | WARN     | no evidence_asof column - benchmark age is untracked, so a stale scrape cannot be distinguished from a fresh one |   0 |
| coherence checks                     | WARN     | no family / kit / supersession columns supplied - these checks did not run                                       |   0 |
| input files unchanged                | PASS     | all inputs byte-identical                                                                                        |   0 |
| diff alloc_detail                    | PASS     | max numeric drift 1.819e-12                                                                                      |   0 |


### Lines carrying most of the impact

| db       | cat         | label        |   delta |   revenue_delta_eur | reason_code      | premium_basis   | evidence_tier   |   cum_share |
|:---------|:------------|:-------------|--------:|--------------------:|:-----------------|:----------------|:----------------|------------:|
| ITUK     | brake_pad   | Brake pads   |   0.033 |             9984.37 | NO_EVIDENCE_HOLD | placeholder     | T5_none         |      0.0577 |
| ITUK     | brake_rotor | Brake rotors |   0.033 |             9379.66 | NO_EVIDENCE_HOLD | placeholder     | T5_none         |      0.1119 |
| ITUK     | fuel_filter | Fuel filter  |   0.033 |             7184.82 | NO_EVIDENCE_HOLD | placeholder     | T5_none         |      0.1534 |
| PORTUGAL | brake_pad   | Brake pads   |   0.063 |             5657.84 | NO_EVIDENCE_HOLD | placeholder     | T5_none         |      0.1861 |
| UTI      | fuel_filter | Fuel filter  |   0.033 |             5366.51 | NO_EVIDENCE_HOLD | placeholder     | T5_none         |      0.2171 |
| ITUK     | air_filter  | Air filter   |   0.033 |             5034.56 | NO_EVIDENCE_HOLD | placeholder     | T5_none         |      0.2462 |
| UTI      | air_filter  | Air filter   |   0.033 |             4840.61 | NO_EVIDENCE_HOLD | placeholder     | T5_none         |      0.2742 |
| IUK      | brake_rotor | Brake rotors |   0.013 |             4691.22 | NO_EVIDENCE_HOLD | placeholder     | T5_none         |      0.3013 |
| GERMANY  | brake_pad   | Brake pads   |   0.033 |             4460.38 | NO_EVIDENCE_HOLD | placeholder     | T5_none         |      0.3271 |
| UTI      | oil_filter  | Oil filter   |   0.033 |             4383.42 | NO_EVIDENCE_HOLD | placeholder     | T5_none         |      0.3524 |
| GERMANY  | brake_rotor | Brake rotors |   0.033 |             4057.31 | NO_EVIDENCE_HOLD | placeholder     | T5_none         |      0.3759 |
| PORTUGAL | brake_rotor | Brake rotors |   0.063 |             3406.7  | NO_EVIDENCE_HOLD | placeholder     | T5_none         |      0.3956 |
| IRELAND  | brake_rotor | Brake rotors |   0.063 |             3336.96 | NO_EVIDENCE_HOLD | placeholder     | T5_none         |      0.4148 |
| IUK      | brake_pad   | Brake pads   |   0.013 |             3324.86 | NO_EVIDENCE_HOLD | placeholder     | T5_none         |      0.4341 |
| ITUK     | oil_filter  | Oil filter   |   0.033 |             3168.86 | NO_EVIDENCE_HOLD | placeholder     | T5_none         |      0.4524 |