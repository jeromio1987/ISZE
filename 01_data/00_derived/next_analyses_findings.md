# Next analyses — sales-to-dealer deep layers (six DBs)

Framework: `00_docs/sales-to-dealer-analytics-framework_deeplayers.md`
Default focus: **core** · default view: **gps** · gap metric: **eur**

## Consumables gate
- AIM: `aim_l1 == Hardware & consumables` OR L2/L3 gasket|seal|bolt|fastener
- Core ranking excludes consumables; share shown for transparency

## Core BVP capture ranking
- **#1 UTI (CV)**: capture 92.5%, mix 13.7%, consumables share 1.9%.
- **#2 PORTUGAL (CV+LCV)**: capture 74.4%, mix 6.4%, consumables share 2.5%.
- **#3 GREECE (CV+LCV)**: capture 48.7%, mix 9.5%, consumables share 3.5%.
- **#4 IRELAND (CV+LCV)**: capture 26.8%, mix 5.4%, consumables share 2.7%.
- **#5 ITUK (CV)**: capture 19.0%, mix 2.7%, consumables share 2.0%.
- **#6 IUK (LCV)**: capture 8.5%, mix 0.8%, consumables share 2.0%.

## GPS gated (Core) €/UIO
- Channels: ITUK=CV · UTI=CV · IRELAND=CV+LCV · IUK=LCV · GREECE=CV+LCV · PORTUGAL=CV+LCV. **IUK = LCV only**.
- **ITUK (CV)**: StD €241/vehicle vs billing €244/vehicle (UIO 22,389).
- **UTI (CV)**: StD €204/vehicle vs billing €316/vehicle (UIO 10,336).
- **IRELAND (CV+LCV)**: StD €329/vehicle vs billing €381/vehicle (UIO 3,056).
- **IUK (LCV)**: StD €119/vehicle vs billing €126/vehicle (UIO 47,783).
- **GREECE (CV+LCV)**: StD €114/vehicle vs billing €135/vehicle (UIO 3,742).
- **PORTUGAL (CV+LCV)**: StD €172/vehicle vs billing €204/vehicle (UIO 8,176).

## PMS expected vs actual (headline filters / brakes / clutch, €)
- **Oil filter**: ITUK exp €82,462 / bill €96,024 / StD €104,276 · UTI exp €145,479 / bill €132,828 / StD €107,996 · IRELAND exp €13,818 / bill €26,316 / StD €22,667 · IUK exp €225,058 / bill €84,858 / StD €91,912 · GREECE exp €19,102 / bill €18,556 / StD €16,138 · PORTUGAL exp €29,896 / bill €15,568 / StD €17,429
- **Fuel filter**: ITUK exp €138,644 / bill €217,717 / StD €241,830 · UTI exp €112,275 / bill €162,618 / StD €141,010 · IRELAND exp €20,225 / bill €42,969 / StD €47,877 · IUK exp €577,219 / bill €92,334 / StD €100,532 · GREECE exp €32,394 / bill €21,549 / StD €17,213 · PORTUGAL exp €49,927 / bill €22,390 / StD €27,164
- **Air filter**: ITUK exp €166,501 / bill €152,559 / StD €147,946 · UTI exp €126,293 / bill €146,682 / StD €131,806 · IRELAND exp €19,704 / bill €40,260 / StD €38,936 · IUK exp €404,483 / bill €116,316 / StD €108,175 · GREECE exp €29,323 / bill €26,990 / StD €23,108 · PORTUGAL exp €62,049 / bill €38,901 / StD €24,348
- **Brake pad**: ITUK exp €415,256 / bill €302,550 / StD €316,572 · UTI exp €490,766 / bill €34,565 / StD €44,869 · IRELAND exp €54,446 / bill €47,564 / StD €41,951 · IUK exp €1,062,694 / bill €255,744 / StD €268,078 · GREECE exp €99,657 / bill €30,943 / StD €26,965 · PORTUGAL exp €141,293 / bill €89,806 / StD €61,816
- **Brake shoe**: ITUK exp €239,398 / bill €28,643 / StD €38,347 · UTI exp €111,823 / bill €34,555 / StD €22,346 · IRELAND exp €29,534 / bill €8,903 / StD €7,597 · IUK exp €735,141 / bill €41,015 / StD €39,953 · GREECE exp €75,012 / bill €6,527 / StD €6,186 · PORTUGAL exp €140,039 / bill €16,529 / StD €10,698
- **Brake rotor**: ITUK exp €143,781 / bill €284,226 / StD €277,907 · UTI exp €238,019 / bill €22,107 / StD €17,421 · IRELAND exp €23,441 / bill €52,967 / StD €53,714 · IUK exp €830,114 / bill €360,843 / StD €380,470 · GREECE exp €66,662 / bill €24,274 / StD €23,270 · PORTUGAL exp €105,055 / bill €54,074 / StD €26,677
- **Clutch kit**: ITUK exp €145,609 / bill €46,626 / StD €61,176 · UTI exp €246,068 / bill €80,247 / StD €59,966 · IRELAND exp €12,454 / bill €14,116 / StD €34,000 · IUK exp €373,852 / bill €782 / StD €943 · GREECE exp €26,674 / bill €3,868 / StD €2,394 · PORTUGAL exp €61,582 / bill €21,088 / StD €25,365
- **Clutch disc**: ITUK exp €212,483 / bill €29,198 / StD €28,660 · UTI exp €169,019 / bill €2,158 / StD €27,375 · IRELAND exp €28,342 / bill €15,416 / StD €9,232 · IUK exp €1,401,380 / bill €62,909 / StD €69,131 · GREECE exp €77,516 / bill €3,851 / StD €4,237 · PORTUGAL exp €119,035 / bill €21,074 / StD €19,355
- **Clutch pressure plate**: ITUK exp €188,375 / bill €25,481 / StD €12,330 · UTI exp €254,627 / bill €3,548 / StD €2,710 · IRELAND exp €28,717 / bill €16,758 / StD €8,440 · IUK exp €604,264 / bill €39,074 / StD €33,768 · GREECE exp €65,228 / bill €3,153 / StD €2,082 · PORTUGAL exp €106,089 / bill €18,078 / StD €10,245

## Pointed findings
- Core gate (ex-consumables) keeps the same BVP capture order as Overall — consumables were not the ranking driver.
- Consumables share of StD proxy € — ITUK: 2.0% (excluded from Core ranking).
- UTI billing/StD disconnect (Core gate, €): StD proxy €2,103,414 vs billing €3,269,831 (-35.7%).
- Core BVP capture: UTI 92.5% (mix 13.7%); floor IUK 8.5%.
- IUK GPS (Core): StD proxy €119/vehicle vs billing €126/vehicle — park = LCV only (UIO 47,783), not CV/trucks.
- PMS oil filter total capture (billing ÷ PRISM expected): ITUK bill 116.4% · UTI bill 91.3% · IRELAND bill 190.6% · IUK bill 37.7%.
- PORTUGAL 2026 StD run-rate ~ €1,889,938 through 2026-08.
- ITUK dealer spread: ANDY POWELL COMMERCIALS LTD 73.0% vs WALDRON COMMERCIALS LTD 0.4% (≥€20k).
- IUK top-25 StD qty consumables share 50.9% (why Core gate exists — ranking uses € on Core, not gasket/bolt qty).
- Stock/loading: parked. Default landing = Core · GPS €/UIO · gap in € · PMS filters/brakes/clutch on the same page.

## Parked
- Stock / loading — not analysed.
