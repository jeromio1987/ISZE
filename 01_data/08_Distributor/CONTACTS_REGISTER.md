# Distributor contacts register

**Canonical daily-contacts workbook (by product line):**
`01_data/08_Distributor/overview_IE30_IE40_IE50_contacts.xlsx`

**Email allow-list master (MAPI collector / domains):**
`01_data/08_Distributor/DB_email_22_DBs.xlsx` → builds `04_tools/interactions/db_domains.yaml`

**Derived flat list:**
`01_data/00_derived/distributor_daily_contacts_ie30_ie40_ie50.csv`

## Source (2026-09-03)

Jerome self-sent from Sent Items (`jerome.van.der.pluym@isuzu-e.com` → himself),
blank subject, attachment `overview IE30-IE40-IE50 contacts.xlsx`.
Intake: `01_data/90_INBOX/contacts_self_sent_20260903/`.

## What is in the workbook

Sheets: `All customers`, `IE30`, `IE40`, `IE50`.
Columns: customer, branch, daily contact name + email per IE30 / IE40 / IE50.

- Customer blocks on All customers: **54**
- Contact rows exported (name or email present): **141**
- Unique emails in overview: **105**
- Unique emails in DB_email_22_DBs: **54**
- Overlap: **21**
- In overview but not in DB_email master: **84**
- In DB_email master but not in overview: **33**

## Practice (do not replace blindly)

- Keep **DB_email_22_DBs.xlsx** as the domain / allow-list source for mail collection.
- Keep **overview_IE30_IE40_IE50_contacts.xlsx** as the operational “who do I call per product line” register.
- Enrich DB_email from overview only after a human pass (shared Astara domains etc.).

### Emails in overview not yet in DB_email_22_DBs

- `a.soezen@sterki.eu`
- `accessories.be@astara.com`
- `andrea.zanetti@midieurope.it`
- `ann.kerkhove@tvh.com`
- `anne.wallussek@hd.com`
- `antoine.debris@external.cnh.com`
- `antonio.pfeifer@isuzu.de`
- `attila.galatz@swedmotor.se`
- `balazs.szonyi@autowallis.com`
- `baldur@vinnuvelarehf.is`
- `bobyk@isuzu.com.ua`
- `cemtufekci@enka.com.tr`
- `cforgham@imgroup.co.uk`
- `cheri.viljoen@hcmaf.com`
- `claus.magelssen@rsa.no`
- `elonga.yolanda@tdmed.es`
- `els.dedeurwaerder@tvh.com`
- `emre.kurdoglu@isuzu.com.tr`
- `eran@uti.co.il`
- `f.thiel@isuzu-sales.de`
- `fahed@motormall.ps`
- `fin.brown@jcb.com`
- `georg.fischer@isuzu.de`
- `gil.fernando@tdmed.es`
- `halil.gulen@isuzu.com.tr`
- `helinonal@enka.com.tr`
- `ilke.bicel@hidromek.com.tr`
- `info@isuzuarmenia.am`
- `info@swedmotor.se`
- `ismo.hiltunen@finmotor.fi`
- `ivan.blanco.g@astara.com`
- `jaun.reitsma@hitachicm.eu`
- `jos.knapen@claesrevisie.be`
- `julian.vazquez@hidromek.es`
- `juliane.laut@hd.com`
- `karl-heinz.jacobs@sanyeurope.com`
- `karoly.soos@autowallis.com`
- `lab@nellemann.dk`
- `lasse.kvam@mtee.no`
- `lee.mcveigh@takeuchi-mfg.co.uk`
- `lewkowicz.a@sanygroup.com`
- `lorenzo.vaccaro@pitteriviolini.com`
- `m.abel@sterki.eu`
- `matti.sallinen@bassadone.fi`
- `melissa.jvrensburg@hcmaf.com`
- `netanelbuc@umi.co.il`
- `nima.shadmandkhasmakhi1@doosan.com`
- `orders@enginesplus.co.uk`
- `osamu.ishikawa@isuzu.de`
- `parts.isuzu.be@astara.com`
- `parts.purchase@hitachicm.eu`
- `parts@isuzuarmenia.am`
- `partsinventory-kcme@kobelco.com`
- `patrick.bruynseels@astara.com`
- `paulo.costa@motolusa.pt`
- `pedro.silva@motolusa.pt`
- `pjohansson@imnordic.com`
- `psa@nellemann.dk`
- `ran@uti.co.il`
- `raniap@petropoulos.com`
- `raul.delvalle@hidromek.es`
- `ricambimotore@pitteriviolini.com`
- `roland.coquilhat@astara.com`
- `s.sasaoka@giken.nl`
- `safwat@motormall.ps`
- `sarah@umi.co.il`
- `shahafr@uti.co.il`
- `shelly@umi.co.il`
- `sigurdur.einar.jonsson@bl.is`
- `siret.akinci@isuzu.com.tr`
- `spare-parts@det-engines.com`
- `stef.coninx@claesrevisie.be`
- `stefano.zermiani@midieurope.it`
- `szentpaly@tdmed.es`
- `tommi.lunde@swedmotor.se`
- `vagi.szabolcs@verbis.hu`
- `varaosat@finmotor.fi`
- `vidulin@motortech.hr`
- `volska@isuzu.com.ua`
- `yaniv@umi.co.il`
- `yps@enka.com.tr`
- `yuji.okimoto@hcmaf.com`
- `zharkymbayev.bakhyt@cbc-group.kz`
- `zsolt.szentpaly@autowallis.com`

### Customers (All customers)

- AIOS ve Tcaret AS
- AutoWallis Distribution
- BL
- CBC - Trans
- CNH INDUSTRIAL FRANCE SA
- DIESEL EQUIPMENT TRADING B.V.
- DOOSAN BOBCAT EMEA S.R.O.
- ENGINES PLUS LTD
- ENKA PAZARLAMA IHRACAT ITHALAT
- FINMOTOR OY
- GIKEN EUROPE N.V.
- GasanZammit Motors
- Grand Avto
- HD Hyundai Infracore Europe s.r.o
- HIDROMEK A.S.
- HIDROMEK MAQUINARIA DE
- HITACHI CONSTR MACHINERY AFRICA
- HITACHI CONSTRUCTION MACH EUROPE NV
- Imotors
- Isuzu Benelux (IBX)
- Isuzu Denmark
- Isuzu Ireland
- Isuzu Motor Finland (Nordic Automotive Trading)
- Isuzu Motors Germany  (IMG)
- Isuzu Rom Auto
- Isuzu Sales Deutschland (Lang)
- Isuzu Sales deutschland GMBH ( ISD )
- Isuzu Sverige (IM Nordic)
- Isuzu Truck UK (TVS)
- Isuzu UK (IM Parts & Service)
- JCB SERVICE
- KIMA Latejaret
- KOBELCO CONSTR MACHINERY EUROPE BV
- Komtranskomplekt
- Loutsios & Sons
- MIDI Europe
- MITSUBISHI TURBOCHARGER AND ENGINE
- MOTOLUSA LDA
- MOTORTECH CONSULTING D.O.O.
- PITTERI VIOLINI SPA (MI)
- Petros Petropoulos
- REVISIEBEDRIJF CLAES EN ZONEN NV
- Rutebileiernes Standardiserings AS (RSA)
- SANY EUROPE GMBH
- SANY POLAND
- STERKI-HTP GMBH & CO KG
- SwedMotor AB
- TAKEUCHI MFG. CO., LTD
- TDMED Power Systems S.L.
- TVH FORKLIFT PARTS NV
- Universal Motors Israel (UMI)
- Universal Trucks Israel (UTI)
- VERBIS Kft.
- VINNEVULAR OG ASAFL EHF
