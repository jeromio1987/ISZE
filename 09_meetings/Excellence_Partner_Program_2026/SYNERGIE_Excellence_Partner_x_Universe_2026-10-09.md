# Excellence Partner Program en Isuzu Universe — hoe ze samen werken

**Status:** interne analyse, draft · **Datum:** 9 oktober 2026 · **Hoort bij:** `ANALYSE_Excellence_Partner_Program_2026-10-09.md`
**Vraag van Jerome:** het programma overlapt met Universe. Waar zitten de synergieën? Moeten we alles naar Excellence verschuiven en Universe ("tools maken en zo de data afdwingen") als plan B houden voor als management de korting niet goedkeurt? En welke data is het belangrijkst?

---

> **Correctie, 9 oktober 2026 (later).** Eerder stond hier dat er voor Duitsland, Benelux, Zweden, Noorwegen en UMI geen sales-to-dealer-bestand bestaat. Dat klopt alleen voor het **register in de workspace**. In de notulen van de sales reviews van augustus 2026 staat dat Duitsland (ISD) sinds mei 2025 maandelijks onderdeelnummer, aantal en datum doorstuurt, en dat Griekenland, Isuzu UK pickup, Ierland en Portugal maandelijkse bestanden zonder prijzen hebben toegezegd. Voor Benelux, Zweden, Noorwegen en UMI weten we het niet. Het register loopt dus achter op de praktijk. Zie hoofdstuk 3 van het white paper.

## 0. Mijn advies in het kort

**Niet kiezen tussen de twee, maar ze in elkaar schuiven.** Excellence wordt de voordeur, en Universe de machinekamer erachter.

- **Excellence Partner** is wat management en distributeurs te zien krijgen. Het is een herkenbaar partnerprogramma met een status en een korting. Het geeft de distributeur een **reden om mee te doen**. Dat is precies wat Universe mist: Universe scoort zichzelf op 55 van de 100 voor de kans dat een distributeur meedoet zoals ontworpen, en op 35 voor de kans dat hij meer deelt dan het huidige rapport.
- **Universe** levert drie dingen die Excellence mist: **de datastandaard** (die is al volledig uitgeschreven), **de analyses en wat we teruggeven** (de distributeur-one-pagers bestaan al voor 19 markten), en **de spelregels** die voorkomen dat het programma als controle van ISZE aanvoelt. Zonder dat koopt Excellence met de korting alleen het minimale bestand. Dat waarschuwt Universe zelf: "a file sent to satisfy a condition is the minimum that satisfies the condition".

**Wat je wel kan parkeren: het platformdeel van Universe** — een gedeelde app met login, een backend en de €300k-route. Dat bestaat vandaag niet. Er is geen server, geen echte login (geparkeerd tot IT erbij komt), en de laatste acceptatietesten (ACCEPT-04 tot 08) wachten op echte deelnemers. De analyses en documenten werken nu al zonder platform, als bestanden die we per distributeur maken en doorsturen.

**Over plan B: tools kunnen geen data afdwingen.** Een tool trekt aan, maar dwingt niets af. Als management de korting niet goedkeurt, is het realistische plan B daarom: de bestaande kickback-voorwaarde aanscherpen tot dezelfde datastandaard, plus de Universe-terugkoppeling als reden om goed aan te leveren. Dat kost niets extra, maar levert ook minder deelname op (§7).

**Over de belangrijkste data: sales to dealer per dealer, per onderdeel, per maand, zonder prijzen.** Daarnaast eenmalig een dealerlijst gekoppeld aan het klantnummer, en maandelijks fill rate en openstaande backorders. In §4 leg ik uit welke analyse dat mogelijk maakt en hoe die tot meer omzet leidt.

---

## 1. Wat ik heb doorgenomen

| Bron | Wat ik eruit haal |
|---|---|
| Universe 3.0 (23 sep), white paper, Yellow Paper v0.5, mapindex | Vijf tools, scope-afbakening, budgetroutes €0 / €100k / €300k, deelnamescores, spelregels ("do not") |
| Value-exchange model (21 sep) | Deelname per niveau 0–4, de regel "als je X geeft, krijg je Y, waarmee je Z beslist", wat we niet moeten vragen |
| Commercial participation model | **Minimale datastandaard voor sales to dealer**, kickback als startmotor, "20% van de incentive hangt eraan" |
| Pilot evidence pack (21 sep) | Datamatrix per distributeur, het uitgewerkte luchtfiltervoorbeeld bij ITUK, de lijst met ontbrekende gegevens |
| €300k term sheet, DLOD-uitrol (23 sep) | Geen bewezen rendement; DLOD Route A €90k; de prijsherziening als vergelijkingspunt |
| Universe-software (05_AIM_Universe) + roadmap | Interne component, geen backend, 90 van 96 taken geverifieerd, niets uitgerold |
| Atlas: distributeur-one-pagers (sep 2026) | Bestaand terugkoppelformaat per distributeur |
| Sales-to-dealer-register, de aangeleverde bestanden, de regel voor sales to dealer | Wie levert wat, op welk detailniveau |
| Data-map Isuzu OS, BI-bouwlijst | Wat we hebben, wat ontbreekt, wat geblokkeerd is |
| IDS 2026, KPI-master, actieplan FY2027, kickbackvoorstel FY27 | Zie de eerste analyse |

---

## 2. Twee projecten, elk met de zwakte die het andere oplost

| | Excellence Partner Program | Isuzu Universe |
|---|---|---|
| Waar het om draait | Distributeurs aan boord krijgen met status en korting | Distributeurs en dealers tools geven die ze willen gebruiken, en in ruil betere data verdienen |
| Hefboom | Geld (−2,5% / −5% op stockorders) en erkenning | Wat de deelnemer terugkrijgt (analyse, uitleg, verdediging) |
| Sterk | Eenvoudig te begrijpen voor management en distributeurs; een echte prikkel; vanaf april 2027 haalbaar zonder IT | Datastandaard, analysemethode, spelregels en terugkoppeling zijn uitgewerkt en op echte cijfers getest |
| Zwak | Betaalt voor naleving, niet voor kwaliteit; er komt niets terug, dus de distributeur levert het minimum; IDS is een zelfscore | Geen echte reden voor de tweede stap (deelnamescore 45–55); geen platform; budget tot €100–300k; niets bij een echte deelnemer getest |
| Wat het andere project levert | Universe levert de standaard, de terugkoppeling en de spelregels | Excellence levert de reden om mee te doen en een kader dat management kent |

Universe zegt het zelf, in het participation model: **"The kickback is the ignition mechanism, not the end-state."** Excellence is een sterkere versie van die startmotor. Het einddoel van Universe blijft wel geldig: een distributeur die ook zonder korting zou blijven aanleveren, omdat hij er zelf iets aan heeft.

---

## 3. Waar we vandaag staan met de data

### 3.1 Sales to dealer

| Distributeur | Kickback? | Sales to dealer in de workspace | Per dealer? |
|---|---|---|---|
| Isuzu Truck UK | nee | 2023–2026 | **Alleen 2025 (64 dealers)**; 2023, 2024 en 2026 alleen als netwerktotaal |
| Isuzu UK pickup | ja | 2025 + 2026 tot juli | nee, netwerktotaal |
| Ierland | ja | 2025 + 2026 tot juli | nee |
| UTI | ja | 2025 (feb–jul ontbreekt) + 2026 | nee |
| Portugal | ja | 2025 + 2026 | nee |
| Griekenland | nee | 2025 | nee |
| Roemenië | nee | 2026 jan–aug (na formele vraag van 15 sep 2026) | nee |
| Duitsland, Benelux, Zweden, Noorwegen, UMI | **ja** | **geen** | — |
| Cyprus, Hongarije, Finland, Malta, Denemarken, IJsland, Palestina | nee | geen | — |

Wat dit zegt:

- **Per dealer hebben we één jaar van één distributeur.** Zonder dealerniveau kunnen we per onderdeel alleen zeggen wat het hele netwerk van een distributeur verkocht. Daarmee zie je niet welke dealer een probleem heeft.
- **Zelfs ITUK viel in 2026 terug naar een netwerktotaal.** Het bestand met dealerdetail was eenmalig. Zonder een vaste afspraak blijft het niet komen.
- **Van de 9 kickback-distributeurs staat er voor 5 geen enkel bestand in de workspace** (Duitsland, Benelux, Zweden, Noorwegen, UMI), terwijl 20% van hun kickback volgens de Universe-papers aan die aanlevering hangt. Ofwel komt het bestand niet, ofwel komt het wel maar bereikt het deze workspace niet. Dat moet je eerst nagaan: als de huidige voorwaarde niet wordt opgevolgd, zal een nieuwe voorwaarde dat ook niet worden.
- **Vragen werkt soms.** Roemenië leverde binnen twee dagen na je formele vraag acht maanden aan.

### 3.2 Andere data

- **Maandelijkse KPI's** (fill rate, MOS): rijen voor 10 distributeurs in de KPI-master; Portugal, Hongarije en Cyprus ontbreken.
- **Backorders**: alleen Ierland (40 wekelijkse overzichten, oktober 2025 – augustus 2026).
- **Dealerlijst gekoppeld aan klantnummer**: bestaat nergens. Bij ITUK komen maar 16 van de 44 IDS-namen exact overeen met de 64 namen in het sales-to-dealer-bestand.
- **Wagenpark per dealer**: bestaat nergens. Het wagenpark stopt overal op landniveau.

---

## 4. Welke data het belangrijkst is — en hoe ze tot meer omzet leidt

Je zegt het zelf: data moet zorgen voor betere analyses, en die moeten de omzet doen stijgen. Daarom heb ik de data gerangschikt op twee dingen: wat de analyse ermee oplevert voor de verkoop, en hoeveel werk het de distributeur kost.

### 1. Sales to dealer per dealer, per onderdeel, per maand — zonder prijzen

Dit is de belangrijkste. Het maakt vijf dingen mogelijk die we vandaag niet of slecht kunnen:

| Analyse | Wat het oplevert voor de verkoop | Voorbeeld uit de workspace |
|---|---|---|
| Echte vraag scheiden van stockbewegingen | Weten of een daling verloren verkoop is of afbouw van voorraad, voor we een actie starten | Isuzu UK pickup: wat we factureerden ≈ sales to dealer (€6,0M); het gat in GPS was €1,34M garantie, geen verloren verkoop |
| Per dealer zien waar genuine of BVP niet gekocht wordt | Gerichte campagnes en SPA's per dealer in plaats van per land | ITUK luchtfilters: 17 van de 64 dealers kochten een ander onderdeelnummer; met prijsvergelijking (onze dealerprijs €49,98 tegenover €35,10 voor niet-genuine) wordt dat een gesprek over het argument, niet over de prijs |
| Prijsreactie meten van distributeur naar dealer | **Rechtstreeks voor jouw prijsherzieningen**: sinds 11 augustus 2026 is beslist dat de prijsreactie alleen op het niveau distributeur → dealer gemeten mag worden, en daarvoor zijn twee opeenvolgende jaren nodig | Vandaag geblokkeerd: nergens twee jaar data |
| Voorspellen dichter bij de echte vraag | Betere stockorders naar Japan en Thailand (35–65 dagen levertijd) | De huidige basisvoorspelling heeft een mediane fout (WAPE) van 49%; dat sales to dealer dit verbetert is te verwachten, maar nog niet gemeten |
| Koppeling met IDS per dealer | Verbeteracties per dealer met commerciële onderbouwing | Wacht op de dealerlijst (punt 2) |

**Waarom zonder prijzen:** dat haalt het grootste bezwaar van de distributeur weg (zijn marge), en we hebben de prijzen niet nodig. Waarde berekenen we zelf met onze eigen gefactureerde prijs. Universe heeft dit al zo vastgelegd.

### 2. Eenmalig een dealerlijst: dealer-ID, vestiging, locatie en klantnummer, en die bijhouden

Dit kost het minste werk en levert het meeste op. Zonder deze lijst kan niet per dealer berekend worden hoeveel van wat ISZE factureert doorverkocht wordt (bij ITUK geven alle 65.619 regels "niet berekenbaar"), en kan IDS niet aan de verkoopcijfers gekoppeld worden.

### 3. Maandelijks: fill rate, MOS en openstaande backorders per onderdeel

Dit maakt het verschil tussen "de dealer kocht niet" en "de distributeur kon niet leveren". Zonder die info lees je een leveringsprobleem als een verkoopprobleem, en dat wil de distributeur zelf ook niet. Ierland toont dat het formaat al bestaat.

### 4. Optioneel, alleen als het een concrete vraag beantwoordt

Redenen bij verloren verkoop, gemiddelde kilometers per modelgroep (bij ITUK al voorbereid, maar nooit verstuurd), en stock per onderdeel. Volgens de Universe-regel vraag je dit pas wanneer je kan zeggen: "als je ons X geeft, krijg je Y, en daarmee beslis je Z."

### Niet vragen

Verkoopprijzen, marges, klantnamen, chassisnummers en werkplaatsorders. Het kost vertrouwen, we hebben het niet nodig, en bij prijzen is er een mededingingsrisico.

---

## 5. Het programma als één geheel

### 5.1 Niveau 1 — Partner (−2,5% op stockorders), getoetst per kwartaal

| Wat de distributeur doet | Standaard (overgenomen uit Universe) |
|---|---|
| Sales to dealer, maandelijks | Distributeur-ID · dealer-ID · vestigings-ID · Isuzu-onderdeelnummer · aantal (ook negatief bij retours) · datum of maand · soort transactie · regel-ID · rapportageperiode · versie · **verklaring van wat erin zit** (aantal dealers, wat uitgesloten is). Binnen 10 werkdagen na het einde van de maand. Zonder prijzen. Het Excel-formaat is vrij, de inhoud niet. |
| Dealerlijst | Eén keer, daarna bijhouden. Gesloten of hernoemde dealers houden hun ID. |
| Maandelijkse KPI's | Fill rate, MOS, stockwaarde en openstaande backorders per onderdeel |
| IDS | De ronde uitgevoerd waar ISZE en IMG die plannen, met minstens 70% van de dealers |
| Training | Verplichte trainingen gevolgd (vanaf april 2027) |

**Wat de distributeur terugkrijgt, elke maand:** een overzicht van zijn eigen netwerk in het formaat van de bestaande one-pagers (wat we factureerden en wat doorverkocht werd, genuine/BVP, dekking van onderhoudsonderdelen, IDS). Zodra het dealerdetail binnenkomt, ook per dealer. Het overzicht toont alleen de cijfers van de distributeur zelf, naast een anoniem netwerkgemiddelde.

**Waarin dit verschilt van de kickback:** de kickback vraagt vandaag een bestand. Niveau 1 vraagt een **bruikbaar** bestand: per dealer, maandelijks, op tijd, met een verklaring van wat erin zit, plus de dealerlijst. Zo betaalt ISZE niet twee keer voor hetzelfde.

### 5.2 Niveau 2 — Excellence Partner (−5% op stockorders), getoetst per jaar

Alles van niveau 1, plus minstens 85 op 100 op resultaat:

- parts-omzet tegenover het businessplan;
- genuine-aandeel in euro niet gedaald;
- verbeteracties afgesloten (IDS-opvolging, zoals de IDS Development Studio van Universe het beschrijft);
- **elke maand één afgesproken actie met eigenaar en datum**, en de opvolging ervan (het derde punt uit de "minimum viable exchange" van Universe);
- een stap vooruit in R&M of extended warranty.

### 5.3 Wat partners extra krijgen, zonder dat de gewone service afhankelijk wordt

Universe heeft extra programma's die geen gewone service zijn. Daarin kunnen partners voorrang krijgen:

- campagnesteun op extra volume boven een basislijn (Universe stelt €60–90k voor, met een minimum van €150k aan in aanmerking komende facturatie);
- DLOD-steun bij concurrerende offertes (Route A: drie markten, €90k);
- het tenderkader;
- analyses op aanvraag (bv. een studie naar beschikbaarheid, als de distributeur zijn stock deelt).

De gewone service (levertermijnen, BVP-alternatieven, offertes, gewone ondersteuning) blijft voor iedereen gelijk. Dat is een harde regel uit Universe en ze moet ook in het reglement van Excellence staan.

---

## 6. Waar de twee botsen, en hoe je dat oplost

| Universe zegt | Excellence doet | Oplossing |
|---|---|---|
| Betaal niet per record of per veld; tel geen uploads als deelname | Betaalt voor aanleveren | Betalen voor het halen van een **kwaliteitsstandaard per kwartaal** (volledig, per dealer, op tijd, met verklaring), niet voor het aantal regels. Op niveau 2 telt wat er met de data gebeurt (acties), niet de upload. |
| Geen publieke rangschikking van dealers, geen nalevingsscore op IDS | Jaarstatus, award, IDS in de score | Geen rangschikking van distributeurs: wie het niveau haalt, krijgt het, zonder 1-2-3. IDS telt als opvolging, niet als absolute zelfscore. Dealers worden nooit gerangschikt. |
| De gewone service hangt nooit af van wat iemand aanlevert | Development Partners krijgen geen korting | Korting en extra programma's zijn geen gewone service. De gewone service staat expliciet in het reglement als gelijk voor iedereen. |
| Benader nooit rechtstreeks een dealer | — | Alles loopt via de distributeur; ISZE stuurt de terugkoppeling naar de distributeur. |
| Budget van €100k tot €300k, zonder bewezen rendement | Tot €560k (niveau 1) of €1,12M (niveau 2), zonder plafond | Zie §7: realistisch jaar 1 ligt lager, maar management zal het naast de prijsherziening leggen. |
| Stoptest: als de prikkel wegvalt, blijft men dan aanleveren? | — | Overnemen als succesmaatstaf van Excellence: komen er verbeteringen of extra gegevens die niet verplicht waren? |

---

## 7. Kosten naast elkaar

| Wat | Bedrag per jaar | Status |
|---|---:|---|
| Excellence niveau 1, iedereen zonder CIS | tot €560k | voorstel |
| Excellence niveau 2, iedereen zonder CIS | tot €1,12M | voorstel |
| **Excellence niveau 1, realistisch jaar 1** (de 7 distributeurs die vandaag al sales to dealer leveren: ITUK, Isuzu UK pickup, UTI, Ierland, Portugal, Griekenland, Roemenië — als ze er dealerdetail aan toevoegen) | **€335k** | schatting op stockorders FY2026 |
| Universe, budgetroute | €100k (aanbevolen), plafond €300k | voorstel, niet goedgekeurd |
| DLOD Route A | ±€90k | voorstel |
| Ter vergelijking: prijsherziening +5% | +€638k tot +€726k aan opbrengst | lopende beslissing |

**Eerlijk gezegd:** als iedereen niveau 1 haalt, geeft Excellence ongeveer 80% terug van wat de prijsherziening van +5% opbrengt. Management zal die twee naast elkaar leggen. Twee argumenten helpen. Ten eerste komt niet iedereen meteen aan boord: in jaar 1 is ±€335k realistischer. Ten tweede is de korting gekoppeld aan data die de prijsherziening zelf beter maakt (de prijsreactie meten, §4).

### Plan B — als management de korting niet goedkeurt

1. **De bestaande kickback-voorwaarde aanscherpen** tot de standaard van niveau 1, voor de 9 kickback-distributeurs, te beginnen bij de 5 waarvoor geen bestand in de workspace staat. Kost €0 extra. Het vraagt wel dat je de voorwaarden van de kickback kan aanpassen.
2. **Een formele vraag met iets terug** voor ITUK, Griekenland en Roemenië (en daarna de anderen): de maandelijkse terugkoppeling als tegenprestatie. Roemenië bewijst dat dit kan werken.
3. **Status en award zonder korting.** Erkenning op de Europese aftersales-meeting, met IMG ter ondersteuning. Dat is zwakker, maar niet niets.
4. **Universe-tools als aantrekking**, niet als afdwinging. Universe schat zelf in dat dit zonder extra prikkel maar matig werkt (55 voor meedoen, 35 voor meer delen dan nu).

Wat ik **niet** zou doen: plan B bouwen rond "tools die data afdwingen". Een tool dwingt niets af, en het platform waarop zo'n tool moet draaien, bestaat niet.

---

## 8. Wat ik nu zou doen

| Stap | Wie | Waarom eerst |
|---|---|---|
| Nagaan waarom er voor Duitsland, Benelux, Zweden, Noorwegen en UMI geen sales-to-dealer-bestand is, terwijl het in hun kickback zit | Jerome | Als de huidige voorwaarde niet opgevolgd wordt, moet dat eerst opgelost of verklaard zijn |
| De voorwaarden van de kickback (en de jaarlijkse incentive-MOU) naast niveau 1 leggen | Jerome levert ze aan, ik vergelijk | Om niet twee keer te betalen |
| De vraag aan ITUK versturen (kilometers per modelgroep, dealerlijst met klantnummer) | Jerome | Al voorbereid en nooit verstuurd; het is de goedkoopste stap met het meeste effect |
| De datastandaard op één pagina zetten voor distributeurs (Engels, gedeeld) | Ik | Zelfde tekst voor Excellence én Universe |
| Een controle per distributeur: wie haalt niveau 1 vandaag al, en wat ontbreekt er | Ik, uit het register | Toont management de realistische kost van jaar 1 |
| Het deck aanvullen met de dia's "wat we vragen / wat je terugkrijgt", de kosten en plan B | Ik, na jouw akkoord | Voor de managementbeslissing |

---

## Bronnen

| Wat | Waar |
|---|---|
| Universe 3.0, deelnamescores, spelregels, budget | `Isuzu Universe/01_Strategy/ISUZU_UNIVERSE_3_0_2026-09-23.md` §4, §8, §9 |
| Value-exchange model, niveaus 0–4, wat niet vragen | `Isuzu Universe/01_Strategy/UNIVERSE_VALUE_EXCHANGE_MODEL_2026-09-21.md` |
| Minimale datastandaard, kickback = 20% | `Isuzu Universe/01_Strategy/Universe_Commercial_Participation_Model.md` |
| Datamatrix, luchtfiltervoorbeeld, vraag aan ITUK niet verstuurd | `Isuzu Universe/01_Strategy/UNIVERSE_PILOT_EVIDENCE_PACK_2026-09-21.md` §3, §5, §8 |
| €300k, prijsherziening +5% | `Isuzu Universe/01_Strategy/UNIVERSE_300K_GUARANTEE_TERM_SHEET_2026-09-21.md` §2 |
| DLOD Route A | `Isuzu Universe/01_Strategy/DLOD_NETWORK_ROLLOUT_2026-09-23.md` §7 |
| Stand van de Universe-software | `00_docs/ISZE_ROADMAP.md` (Universe engineering programme), `Isuzu Universe/05_AIM_Universe/README.md` |
| Distributeur-one-pagers | `Isuzu Universe/02_Atlas/DISTRIBUTOR_ONE_PAGERS_2026-09/` |
| Sales-to-dealer-bestanden en standaardregel | `01_data/00_derived/dealer_sellout_long_*.csv`, `03_analytics/Isuzu/prism/data/dealer_sales/DEALER_SELL_OUT.md`, `01_data/DATA_MANIFEST.md` §05 |
| Wat we hebben en wat ontbreekt | `00_docs/ISZE_OS_DATA_MAP.yaml`, `00_docs/AFTERMARKET_BI_BUILD_MENU_20260819.md` |
| Prijsreactie alleen distributeur → dealer | `DECISIONS.md`, 11 augustus 2026 |
| Kosten per distributeur | `_build/order_mix_fy2026.csv` |
