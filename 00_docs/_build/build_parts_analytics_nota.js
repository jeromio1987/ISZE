const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  LevelFormat, convertInchesToTwip,
} = require('docx');
const fs = require('fs');

const W = 9000; // usable width in DXA
const NAVY = '1F3864';
const GREY = '595959';
const LIGHT = 'F2F2F2';

const p = (text, opts = {}) => new Paragraph({
  spacing: { after: opts.after ?? 120, line: 276 },
  alignment: opts.align,
  children: [new TextRun({ text, bold: opts.bold, italics: opts.italics, size: opts.size ?? 21, color: opts.color, font: 'Calibri' })],
});

const h1 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_1,
  spacing: { before: 280, after: 140 },
  children: [new TextRun({ text, bold: true, size: 26, color: NAVY, font: 'Calibri' })],
});

const cell = (text, opts = {}) => new TableCell({
  width: { size: opts.w, type: WidthType.DXA },
  shading: opts.head ? { type: ShadingType.CLEAR, fill: LIGHT, color: 'auto' } : undefined,
  margins: { top: 80, bottom: 80, left: 120, right: 120 },
  children: [new Paragraph({
    spacing: { after: 0, line: 260 },
    children: [new TextRun({ text, bold: opts.head || opts.bold, size: 20, font: 'Calibri' })],
  })],
});

const table = (rows, widths) => new Table({
  columnWidths: widths,
  width: { size: W, type: WidthType.DXA },
  borders: {
    top: { style: BorderStyle.SINGLE, size: 2, color: 'BFBFBF' },
    bottom: { style: BorderStyle.SINGLE, size: 2, color: 'BFBFBF' },
    left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE },
    insideHorizontal: { style: BorderStyle.SINGLE, size: 2, color: 'D9D9D9' },
    insideVertical: { style: BorderStyle.NONE },
  },
  rows: rows.map((r, i) => new TableRow({
    tableHeader: i === 0,
    children: r.map((c, j) => cell(c, { w: widths[j], head: i === 0 })),
  })),
});

const bullet = (text) => new Paragraph({
  numbering: { reference: 'dash', level: 0 },
  spacing: { after: 60, line: 276 },
  children: [new TextRun({ text, size: 21, font: 'Calibri' })],
});

const numbered = (text) => new Paragraph({
  numbering: { reference: 'steps', level: 0 },
  spacing: { after: 60, line: 276 },
  children: [new TextRun({ text, size: 21, font: 'Calibri' })],
});

const rule = () => new Paragraph({
  spacing: { before: 60, after: 200 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: NAVY } },
  children: [new TextRun({ text: '', size: 2 })],
});

const doc = new Document({
  numbering: {
    config: [
      { reference: 'dash', levels: [{ level: 0, format: LevelFormat.BULLET, text: '–', alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: convertInchesToTwip(0.25), hanging: convertInchesToTwip(0.17) } } } }] },
      { reference: 'steps', levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: convertInchesToTwip(0.3), hanging: convertInchesToTwip(0.22) } } } }] },
    ],
  },
  sections: [{
    properties: { page: { margin: { top: 1100, bottom: 1000, left: 1100, right: 1100 } } },
    children: [

      new Paragraph({
        spacing: { after: 40 },
        children: [new TextRun({ text: 'ISZE Parts Analytics op de bedrijfsomgeving', bold: true, size: 34, color: NAVY, font: 'Calibri' })],
      }),
      new Paragraph({
        spacing: { after: 60 },
        children: [new TextRun({ text: 'Benodigdheden — notitie voor IT en Parts management', size: 24, color: GREY, font: 'Calibri' })],
      }),
      new Paragraph({
        spacing: { after: 0 },
        children: [new TextRun({ text: 'Jérôme Van der Pluym  ·  14 augustus 2026  ·  versie 1.0', size: 18, color: GREY, font: 'Calibri' })],
      }),
      rule(),

      h1('1.  Aanleiding en doel'),
      p('Voor de Parts-organisatie is een analyselaag ontwikkeld die de bestaande SAP-uittreksels omzet naar afgeleide tabellen en vaste rapportagepagina’s. De laag dekt onder meer GPS, PMS-capture, AIM-classificatie, prijspositionering en dealer sell-out.'),
      p('Deze laag vult de bestaande Power BI-rapportage aan, en vervangt die niet. Power BI geeft de periodieke stand van zaken; deze analyselaag geeft de diepte per onderdeelnummer en per distributeur die nodig is voor prijszetting, PMS-opvolging en distributeurgesprekken.'),
      p('Doel van deze notitie: vastleggen wat nodig is om de analyselaag structureel op de bedrijfsomgeving te laten draaien, onder beheer en overdraagbaar aan een tweede persoon.'),

      h1('2.  Wat de analyselaag doet'),
      table([
        ['Onderdeel', 'Omvang'],
        ['Verwerkingsscripts (Python)', 'circa 108, in een vaste uitvoeringsvolgorde'],
        ['Rapportagepagina’s', '74 statische HTML-pagina’s — geen server nodig'],
        ['Invoer', 'SAP-uittreksels die reeds op de gedeelde netwerkschijf staan'],
        ['Uitvoer', 'Afgeleide tabellen (CSV / Parquet / JSON) en de rapportagepagina’s'],
        ['Richting', 'Uitsluitend lezen — geen enkele terugschrijfactie naar SAP'],
      ], [3000, 6000]),
      p(''),
      p('De afgeleide laag wordt bij elke uitvoering opnieuw opgebouwd en hoeft niet bewaard of verplaatst te worden. Er wordt uitsluitend gelezen uit de bronbestanden; die blijven ongewijzigd.', { italics: true, color: GREY, size: 20 }),

      h1('3.  Wat er nodig is'),
      table([
        ['Nodig', 'Toelichting'],
        ['1.  Windows-werkplek met Python 3.11 of hoger', 'De cloudwerkplek volstaat. Circa 20 GB vrije schijfruimte. Python mag reeds geïnstalleerd worden.'],
        ['2.  Python-pakketten', 'pandas, numpy, pyarrow, openpyxl, plotly, scipy, matplotlib, reportlab, pyyaml. Via pip vanaf PyPI, een interne pakketspiegel, of een eenmalige offline bundel.'],
        ['3.  Leesrecht op de gedeelde netwerkschijf', 'Read & Execute, geen schrijfrechten. Betreft de map waar de SAP-uittreksels reeds worden geplaatst.'],
        ['4.  Schrijfrecht op één afzonderlijke map', 'Buiten de bronstructuur, uitsluitend voor de uitvoer. Bijvoorbeeld een eigen map op dezelfde schijf of een documentbibliotheek op de Parts-teamsite.'],
        ['5.  Windows Taakplanner', 'Reeds aanwezig op elke werkplek, geen aanvraag. Alleen nodig zodra de uitvoering automatisch moet lopen; niet vereist bij aanvang.'],
        ['6.  Aanwijzing van een tweede beheerder', 'Voorstel: in overleg met de beheerder van de bestaande Power BI-omgeving, zodat kennis en toegang bij twee personen liggen.'],
      ], [3200, 5800]),

      h1('4.  Wat er niet nodig is'),
      p('De aanvraag blijft bewust klein. Er is geen behoefte aan:'),
      bullet('een nieuwe server, virtuele machine of database;'),
      bullet('Azure-, Synapse- of Fabric-capaciteit;'),
      bullet('een rechtstreekse koppeling naar SAP — de uittreksels bestaan al;'),
      bullet('beheerdersrechten buiten het installeren van Python;'),
      bullet('bijkomende netwerkschijven of gedeelde mappen;'),
      bullet('een investeringsbudget of een IT-project.'),

      h1('5.  Buiten scope'),
      p('Twee onderdelen worden bewust niet meegenomen, om de aanvraag beperkt en beoordeelbaar te houden:'),
      bullet('Toepassingen die externe websites raadplegen. Die vragen uitgaand netwerkverkeer en een afzonderlijke juridische afweging, en worden los behandeld.'),
      bullet('Interactieve toepassingen die een server en een netwerkpoort vereisen. De rapportage gebeurt via statische pagina’s, waarvoor geen infrastructuur nodig is.'),

      h1('6.  Beheer en continuïteit'),
      table([
        ['Aspect', 'Invulling'],
        ['Versiebeheer', 'De volledige scriptset staat onder versiebeheer; wijzigingen zijn herleidbaar.'],
        ['Documentatie', 'Kolomdefinities en rekenregels zijn vastgelegd in een data dictionary en een metric dictionary.'],
        ['Controle op de cijfers', 'Elke uitvoering levert een verificatierapport. Uitkomsten worden getoetst voordat ze gedeeld worden.'],
        ['Overdraagbaarheid', 'Twee beheerders; de uitvoering is beschreven in een draaiboek.'],
        ['Gegevensbescherming', 'Uitsluitend lezen. Geen wijziging aan bronbestanden, geen terugschrijven naar SAP, geen gegevens buiten het bedrijfsnetwerk.'],
      ], [2600, 6400]),

      h1('7.  Voorgestelde volgende stappen'),
      numbered('Bevestigen van leesrecht op de map met de bestaande SAP-uittreksels.'),
      numbered('Aanmaken van één uitvoermap met schrijfrecht, buiten de bronstructuur.'),
      numbered('Nagaan of pip de pakketspiegel kan bereiken; zo niet, eenmalig een offline bundel voorzien.'),
      numbered('Proefuitvoering op de bedrijfsomgeving en vergelijking van de uitkomsten met de huidige.'),
      numbered('Formeel aanwijzen van de tweede beheerder.'),
      p(''),
      p('Stap 1 tot en met 3 zijn kleine, afzonderlijk uitvoerbare handelingen. Stap 4 vraagt geen bijkomende toegang. Na stap 5 is de analyselaag volledig binnen de bedrijfsomgeving belegd en niet meer afhankelijk van één persoon.', { italics: true, color: GREY, size: 20 }),
    ],
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(process.argv[2], buf);
  console.log('written:', process.argv[2]);
});
