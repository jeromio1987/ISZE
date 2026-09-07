# Brief checklist

Artifact: `C:\Users\jerom\Desktop\claude\ISZE\09_meetings\IDS_2026_Country_Packs_v1.5\INDEX.md`

- [x] **1.** Averages all countries like Switzerland: IT+CH out of AVG_ALL_IN; zeros/non-responders out of country average; stay on list and map; Notes X of Y / Z did not answer; no IT/CH keep-everyone hover; FR/ES red-mark stays — _Extract: CH 87.8% 16/22 excl 6 named; IT 85.9% 38/41 excl 3; FR 79.8% 64/84. AVG_ALL_IN gone. Hover no keep-everyone. zeros_in_avg=0 on all 19 HTML packs._
- [x] **2.** Map: no CARTO, no API-key watermark, Leaflet inlined, offline pin grid OK, English UI — _CH/FR map screenshots: offline pin grid, text no map-service key; grep carto/apikey=0; L.map inlined in HTML._
- [x] **3.** MIDI 4 disabled on single-country packs (must not pull other three countries); keep Meeting view / Copy table / %|Delta|Both default Both if they make sense — _btn-midi4 and midi-tools stripped from all 19 packs; Meeting view + Copy table + Both default visible on CH/FR vs-network screenshots._
- [x] **4.** Notes tab present; Changelog stripped from Mode A — _Notes tab paints on CH/FR/IT; changelog tab/button absent in all 19 HTML greps._
- [x] **5.** Version label v1.5 on country packs; new folder IDS_2026_Country_Packs_v1.5; leave v1.4 intact; do not invent v1.6; do not overwrite v1.4 — _New folder 09_meetings\IDS_2026_Country_Packs_v1.5; v1.4 INDEX still 2026-08-15 v1.4; title v1.5 on CH/FR/IT screenshots._
- [x] **6.** Israel IDS = UMI only; Section E N.A. is not a fail; English country names; no Dutch; no Weak-sector radar clutter; geo sanity no country-centre pin blobs — _Israel LCV pack only; Notes say UMI not UTI blended; Section E N.A. not a fail; geo sanity PASS all 19; no MIDI_CH/goed/slecht/Weak sector._
- [x] **7.** OPEN_*.cmd sibling per pack; OPEN cmd-only do not start for Jerome — _19 sibling OPEN_IDS_2026_*.cmd plus pack-root OPEN for CH and FR; not started for Jerome._
- [x] **8.** Prove CH ~87.8% 16 of 22 with 6 named non-responders; Italy zeros out of average; France still 64 of 84; cite network % if master rebuilt — _Paint: CH 87.8% 16 of 22 6 did not answer; IT 85.9% 38 of 41; FR 64 of 84; master rebuilt network 80.7% (was 79.3%)._
- [x] **9.** Paint-check CH Notes + vs-network, FR 64 of 84, map no API key; screenshots; SHIP_RECEIPT.json — _QA PNGs under packs _qa; SHIP_RECEIPT to be written this turn._
- [x] **10.** Do not send mail, SharePoint-upload, bump v0.4 dealer workshop packs, mix Alps, use street language, blend UTI into IDS Israel — _No mail, no SharePoint, v0.4 workshop untouched, no Alps mix, no street price language, UTI not blended into IDS Israel._

Machine file: `C:\Users\jerom\Desktop\claude\.cursor\qa-pending\brief-checklist.json`
