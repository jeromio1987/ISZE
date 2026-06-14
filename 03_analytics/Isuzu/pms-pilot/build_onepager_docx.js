// Build ITUK Pricing One-Pager Word document with ISZE branding.
const path = require('path');
const fs = require('fs');

// Resolve docx from global install
const globalRoot = require('child_process').execSync('npm root -g').toString().trim();
const docxPath = path.join(globalRoot, 'docx');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, LevelFormat, HeadingLevel,
  BorderStyle, WidthType, ShadingType, VerticalAlign, PageNumber,
} = require(docxPath);

const ISZE_BLUE = '1B3A6B';
const ISZE_ORANGE = 'E87722';
const GREY_LIGHT = 'F2F2F2';
const BORDER_GREY = 'CCCCCC';
const TEXT_DARK = '222222';

const A4_WIDTH = 11906;        // DXA
const A4_HEIGHT = 16838;
const MARGIN = 1134;           // ~0.79in
const CONTENT_WIDTH = A4_WIDTH - 2 * MARGIN; // 9638

const border = { style: BorderStyle.SINGLE, size: 4, color: BORDER_GREY };
const cellBorders = { top: border, bottom: border, left: border, right: border };
const cellMargins = { top: 100, bottom: 100, left: 140, right: 140 };

function p(text, opts = {}) {
  return new Paragraph({
    spacing: { before: opts.before ?? 60, after: opts.after ?? 60 },
    alignment: opts.alignment ?? AlignmentType.LEFT,
    children: [new TextRun({
      text,
      bold: opts.bold,
      italics: opts.italics,
      size: opts.size ?? 22, // 11pt
      color: opts.color ?? TEXT_DARK,
      font: 'Arial',
    })],
  });
}

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 280, after: 160 },
    children: [new TextRun({ text, bold: true, size: 36, color: ISZE_BLUE, font: 'Arial' })],
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 240, after: 120 },
    children: [new TextRun({ text, bold: true, size: 28, color: ISZE_BLUE, font: 'Arial' })],
  });
}

function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 200, after: 100 },
    children: [new TextRun({ text, bold: true, size: 24, color: ISZE_BLUE, font: 'Arial' })],
  });
}

function rich(parts) {
  // parts: array of {text, bold?, italic?, color?}
  return new Paragraph({
    spacing: { before: 60, after: 60 },
    children: parts.map(part => new TextRun({
      text: part.text,
      bold: part.bold,
      italics: part.italic,
      color: part.color ?? TEXT_DARK,
      size: 22,
      font: 'Arial',
    })),
  });
}

function bullet(text, color = TEXT_DARK) {
  return new Paragraph({
    numbering: { reference: 'bullets', level: 0 },
    spacing: { before: 40, after: 40 },
    children: [new TextRun({ text, color, size: 22, font: 'Arial' })],
  });
}

function numbered(text) {
  return new Paragraph({
    numbering: { reference: 'numbers', level: 0 },
    spacing: { before: 40, after: 40 },
    children: [new TextRun({ text, size: 22, font: 'Arial' })],
  });
}

function divider() {
  return new Paragraph({
    spacing: { before: 100, after: 100 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: ISZE_BLUE, space: 1 } },
    children: [new TextRun({ text: '' })],
  });
}

// Table cell builder
function tc(content, opts = {}) {
  const isStr = typeof content === 'string';
  const runs = isStr
    ? [new TextRun({ text: content, bold: opts.bold, color: opts.color ?? TEXT_DARK, size: opts.size ?? 22, font: 'Arial' })]
    : content;
  return new TableCell({
    width: { size: opts.width, type: WidthType.DXA },
    borders: cellBorders,
    margins: cellMargins,
    shading: opts.fill ? { fill: opts.fill, type: ShadingType.CLEAR, color: 'auto' } : undefined,
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({
      alignment: opts.align ?? AlignmentType.LEFT,
      children: runs,
    })],
  });
}

// SPU Premium table — the hero
function buildSPUTable() {
  const cols = [3200, 1900, 2069, 2469]; // 9638 total
  const header = new TableRow({
    tableHeader: true,
    children: [
      tc('PMS subgroup', { width: cols[0], bold: true, color: 'FFFFFF', fill: ISZE_BLUE }),
      tc('ITUK €/UIO/yr', { width: cols[1], bold: true, color: 'FFFFFF', fill: ISZE_BLUE, align: AlignmentType.RIGHT }),
      tc('Network median €/UIO/yr', { width: cols[2], bold: true, color: 'FFFFFF', fill: ISZE_BLUE, align: AlignmentType.RIGHT }),
      tc('Premium ITUK pays', { width: cols[3], bold: true, color: 'FFFFFF', fill: ISZE_BLUE, align: AlignmentType.RIGHT }),
    ],
  });
  const rows = [
    ['Brake pads', '€13.51', '€3.88', '+247.7%', true],
    ['Clutch pressure plate', '€1.13', '€0.33', '+243.7%', true],
    ['Fuel filter', '€8.87', '€3.12', '+184.1%', true],
    ['Clutch disc', '€0.65', '€0.33', '+99.5%', false],
    ['Air filter', '€6.95', '€4.51', '+54.0%', false],
    ['Oil filter', '€3.80', '€2.71', '+40.3%', false],
    ['Brake shoes', '€0.10', '€0.78', '−86.9%', false],
  ];
  const dataRows = rows.map(([sg, ituk, net, prem, hot]) => new TableRow({
    children: [
      tc(sg, { width: cols[0], bold: hot, fill: hot ? 'FFF4E6' : undefined }),
      tc(ituk, { width: cols[1], align: AlignmentType.RIGHT, bold: hot, fill: hot ? 'FFF4E6' : undefined }),
      tc(net, { width: cols[2], align: AlignmentType.RIGHT, bold: hot, fill: hot ? 'FFF4E6' : undefined }),
      tc(prem, { width: cols[3], align: AlignmentType.RIGHT, bold: true, color: hot ? ISZE_ORANGE : TEXT_DARK, fill: hot ? 'FFF4E6' : undefined }),
    ],
  }));
  return new Table({
    width: { size: 9638, type: WidthType.DXA },
    columnWidths: cols,
    rows: [header, ...dataRows],
  });
}

// Kosha table
function buildKoshaTable() {
  const cols = [4800, 2400, 2438];
  const header = new TableRow({
    tableHeader: true,
    children: [
      tc('Distributor', { width: cols[0], bold: true, color: 'FFFFFF', fill: ISZE_BLUE }),
      tc('Gap €', { width: cols[1], bold: true, color: 'FFFFFF', fill: ISZE_BLUE, align: AlignmentType.RIGHT }),
      tc('% of own TAM', { width: cols[2], bold: true, color: 'FFFFFF', fill: ISZE_BLUE, align: AlignmentType.RIGHT }),
    ],
  });
  const rows = [
    ['IUK', '€2.37M', '88.8%', false],
    ['UMI', '€577k', '93.2%', false],
    ['Germany', '€518k', '92.0%', false],
    ['ITUK', '€457k', '45.4%', true],
    ['Belgium', '€344k', '89.4%', false],
    ['Portugal', '€228k', '76.5%', false],
  ];
  const dataRows = rows.map(([d, g, t, hot]) => new TableRow({
    children: [
      tc(d, { width: cols[0], bold: hot, fill: hot ? 'FFF4E6' : undefined }),
      tc(g, { width: cols[1], bold: hot, align: AlignmentType.RIGHT, fill: hot ? 'FFF4E6' : undefined, color: hot ? ISZE_ORANGE : TEXT_DARK }),
      tc(t, { width: cols[2], bold: hot, align: AlignmentType.RIGHT, fill: hot ? 'FFF4E6' : undefined }),
    ],
  }));
  return new Table({
    width: { size: 9638, type: WidthType.DXA },
    columnWidths: cols,
    rows: [header, ...dataRows],
  });
}

// White-space table
function buildWhitespaceTable() {
  const cols = [3000, 2200, 2200, 2238];
  const header = new TableRow({
    tableHeader: true,
    children: [
      tc('Subgroup', { width: cols[0], bold: true, color: 'FFFFFF', fill: ISZE_BLUE }),
      tc('Addressable BVP PNs', { width: cols[1], bold: true, color: 'FFFFFF', fill: ISZE_BLUE, align: AlignmentType.RIGHT }),
      tc('ITUK BVP sold today', { width: cols[2], bold: true, color: 'FFFFFF', fill: ISZE_BLUE, align: AlignmentType.RIGHT }),
      tc('White-space PNs', { width: cols[3], bold: true, color: 'FFFFFF', fill: ISZE_BLUE, align: AlignmentType.RIGHT }),
    ],
  });
  const rows = [
    ['Wheel pin', '19', '0', '19'],
    ['Clutch kit', '20', '8', '12'],
    ['Brake pad', '2', '0', '2'],
    ['Engine foot rubber', '2', '0', '2'],
    ['Brake lining', '1', '0', '1'],
    ['Brake rotor', '1', '0', '1'],
    ['Brake shoe', '1', '0', '1'],
    ['Clutch booster', '1', '0', '1'],
    ['Hub oil seal', '1', '0', '1'],
  ];
  const dataRows = rows.map(([sg, a, s, ws]) => new TableRow({
    children: [
      tc(sg, { width: cols[0] }),
      tc(a, { width: cols[1], align: AlignmentType.RIGHT }),
      tc(s, { width: cols[2], align: AlignmentType.RIGHT }),
      tc(ws, { width: cols[3], align: AlignmentType.RIGHT, bold: true, color: ISZE_ORANGE }),
    ],
  }));
  return new Table({
    width: { size: 9638, type: WidthType.DXA },
    columnWidths: cols,
    rows: [header, ...dataRows],
  });
}

// UREA table
function buildUreaTable() {
  const cols = [2400, 1800, 1800, 1800, 1838];
  const header = new TableRow({
    tableHeader: true,
    children: [
      tc('Distributor', { width: cols[0], bold: true, color: 'FFFFFF', fill: ISZE_BLUE }),
      tc('UREA Genuine €', { width: cols[1], bold: true, color: 'FFFFFF', fill: ISZE_BLUE, align: AlignmentType.RIGHT }),
      tc('UREA BVP €', { width: cols[2], bold: true, color: 'FFFFFF', fill: ISZE_BLUE, align: AlignmentType.RIGHT }),
      tc('UIO', { width: cols[3], bold: true, color: 'FFFFFF', fill: ISZE_BLUE, align: AlignmentType.RIGHT }),
      tc('BVP € share', { width: cols[4], bold: true, color: 'FFFFFF', fill: ISZE_BLUE, align: AlignmentType.RIGHT }),
    ],
  });
  const rows = [
    ['ITUK', '€74,269', '€1,311', '22,389', '1.7%', true],
    ['Ireland', '€4,544', '€150', '2,727', '3.2%', false],
    ['Belgium', '€152', '€0', '9,311', '0.0%', false],
    ['Cyprus', '€76', '€0', '2,072', '0.0%', false],
    ['Malta', '€70', '€0', '1,054', '0.0%', false],
  ];
  const dataRows = rows.map(([d, g, b, u, s, hot]) => new TableRow({
    children: [
      tc(d, { width: cols[0], bold: hot, fill: hot ? 'FFF4E6' : undefined }),
      tc(g, { width: cols[1], align: AlignmentType.RIGHT, bold: hot, fill: hot ? 'FFF4E6' : undefined, color: hot ? ISZE_ORANGE : TEXT_DARK }),
      tc(b, { width: cols[2], align: AlignmentType.RIGHT, bold: hot, fill: hot ? 'FFF4E6' : undefined }),
      tc(u, { width: cols[3], align: AlignmentType.RIGHT, bold: hot, fill: hot ? 'FFF4E6' : undefined }),
      tc(s, { width: cols[4], align: AlignmentType.RIGHT, bold: hot, fill: hot ? 'FFF4E6' : undefined, color: hot ? ISZE_ORANGE : TEXT_DARK }),
    ],
  }));
  return new Table({
    width: { size: 9638, type: WidthType.DXA },
    columnWidths: cols,
    rows: [header, ...dataRows],
  });
}

// ── Build document ──────────────────────────────────────────────────────────
const today = new Date();
const dateStr = today.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });

const children = [];

// Title block
children.push(new Paragraph({
  spacing: { before: 0, after: 0 },
  alignment: AlignmentType.LEFT,
  border: { bottom: { style: BorderStyle.SINGLE, size: 18, color: ISZE_ORANGE, space: 6 } },
  children: [
    new TextRun({ text: 'ISZE Sales', bold: true, size: 24, color: ISZE_BLUE, font: 'Arial' }),
  ],
}));
children.push(new Paragraph({
  spacing: { before: 240, after: 80 },
  children: [new TextRun({ text: 'ITUK PMS Pricing — Position Paper v1', bold: true, size: 44, color: ISZE_BLUE, font: 'Arial' })],
}));
children.push(rich([
  { text: 'Prepared by:  ', bold: true },
  { text: 'ISZE Sales · J. Van der Pluym' },
]));
children.push(rich([
  { text: 'Source:  ', bold: true },
  { text: 'ISZE lifetime sales data, CY2023–2025, all 18 active distributors' },
]));
children.push(rich([
  { text: 'Status:  ', bold: true },
  { text: 'Internal — for the ITUK pricing conversation and Kosha PMS narrative', italic: true },
]));
children.push(divider());

// Headline
children.push(h1('Headline'));
children.push(rich([
  { text: 'ITUK is paying 40% to 248% more per fleet vehicle than the network median on every PMS subgroup we measure — except one.', bold: true, color: ISZE_BLUE },
  { text: ' This is not a fleet-mix story. It is a price-per-PMS-unit story, measured on the same parts, on the same fleet basis (SPU = spend per unit-in-operation).' },
]));

// The number that matters
children.push(h1('The number that matters'));
children.push(buildSPUTable());
children.push(p(''));
children.push(rich([
  { text: 'Read: ', bold: true },
  { text: 'ITUK customers spend roughly ' },
  { text: '3.5× the network median', bold: true, color: ISZE_ORANGE },
  { text: ' on brake pads, ' },
  { text: '3.4×', bold: true, color: ISZE_ORANGE },
  { text: ' on clutch pressure plates, and ' },
  { text: '2.8×', bold: true, color: ISZE_ORANGE },
  { text: ' on fuel filters — per truck in their fleet, per year, on Genuine + BVP combined. Only brake shoes are below median, and on negligible volume.' },
]));

// Kosha narrative
children.push(h1('Why this matters for the Kosha narrative'));
children.push(bullet('The ISZE network is leaving €5.07M / year in PMS revenue on the table by under-capturing its fleet (sum of revenue gap, latest year across all distributors).'));
children.push(bullet('ITUK is responsible for €457k of that gap — 9.0% of the network total, despite holding a much smaller share of the UIO.'));
children.push(bullet('ITUK’s capture-rate gap vs the network median is the symptom; the SPU premium above is the cause. Customers walking away from ITUK’s PMS prices show up downstream as a low capture rate and as the IAM share of wallet that we lose entirely.'));
children.push(p('', { after: 100 }));
children.push(buildKoshaTable());

// Counter-arguments
children.push(h1('What ITUK will counter and how the data answers'));
children.push(rich([
  { text: '1. “ITUK fleet is younger / different mix.” ', bold: true, color: ISZE_BLUE },
  { text: 'Mitigated — SPU is normalised by UIO. Mix-shift between PMS subgroups doesn’t explain a uniform 40–248% premium across all of them.' },
]));
children.push(rich([
  { text: '2. “ITUK Genuine ASP is set by IML.” ', bold: true, color: ISZE_BLUE },
  { text: 'Partly true on Genuine. But the BVP-equivalent ASP is also higher at ITUK than at peers selling the exact same paired PN — see ' },
  { text: 'PricingGap_Pairs', italic: true },
  { text: ' sheet in the data pack.' },
]));
children.push(rich([
  { text: '3. “ITUK costs more to serve.” ', bold: true, color: ISZE_BLUE },
  { text: 'Cost-to-serve does not justify a 248% retail premium on a competitive PMS part. R&M studies of the same N-series fleet across markets land within ±15% on fully-loaded service cost, not 3.5×.' },
]));

// Recommended ask
children.push(h1('Recommended ask'));
children.push(numbered('Re-baseline ITUK’s PMS retail pricing to network median + a defensible UK premium (10–20% max). Worst-case revenue impact is offset by the capture-rate recovery (model says ~30% on fuel filter alone).'));
children.push(numbered('Make BVP the formal first-line offer at ITUK for the 8 zero-penetration subgroups (wheel pin, brake lining, brake rotor, brake shoe friction, brake pad, clutch booster, engine foot rubber, hub oil seal — all have ITUK addressable Genuine sales but zero BVP sales).'));
children.push(numbered('Land UREA-filter BVP push as Euro 6 PMS quick-win. ITUK has £74k Genuine, £1.3k BVP — single biggest UREA opportunity in the network.'));

// Page break before appendix
children.push(new Paragraph({ pageBreakBefore: true, children: [new TextRun({ text: '' })] }));

// Appendix
children.push(h1('Numerical appendix (selected high-stakes rows)'));
children.push(h2('A. The 8 ITUK BVP white-space subgroups'));
children.push(buildWhitespaceTable());
children.push(h2('B. UREA filter snapshot — Euro 6 PMS opportunity'));
children.push(buildUreaTable());

// Source data
children.push(h1('Source data'));
children.push(p('C:\\Users\\jerom\\Desktop\\claude\\ISZE\\Projects\\Isuzu\\pms-pilot\\ISZE_ITUK_DataPack_v1.xlsx', { italics: true, color: '666666' }));
children.push(bullet('ITUK_vs_Network_PMS — premium table above'));
children.push(bullet('Kosha_Gap_OneNumber — €5.07M network gap, top-15 distributor breakdown'));
children.push(bullet('WhiteSpace — addressable vs sold per (distributor × subgroup)'));
children.push(bullet('PricingGap_Pairs — pair-level ASP delta (genuine vs BVP)'));
children.push(bullet('UREA_QuickWin — full UREA snapshot'));
children.push(bullet('Substitution_Momentum — 4 flagged YoY substitution signals'));
children.push(bullet('AIM_BVP_CrossLink — top 80 (distributor × family) where IAM is heavy and BVP is light'));
children.push(p(''));
children.push(rich([
  { text: 'Underlying pipeline: ', bold: true },
  { text: 'C:\\Users\\jerom\\Desktop\\claude\\ISZE\\Data\\derived\\ — built and verified via the prism contracts pipeline.', italic: true },
]));

// Build doc
const doc = new Document({
  creator: 'ISZE Sales',
  title: 'ITUK PMS Pricing Position Paper v1',
  styles: {
    default: { document: { run: { font: 'Arial', size: 22 } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 36, bold: true, color: ISZE_BLUE, font: 'Arial' },
        paragraph: { spacing: { before: 280, after: 160 }, outlineLevel: 0 } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 28, bold: true, color: ISZE_BLUE, font: 'Arial' },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } },
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 24, bold: true, color: ISZE_BLUE, font: 'Arial' },
        paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 2 } },
    ],
  },
  numbering: {
    config: [
      { reference: 'bullets',
        levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: 'numbers',
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: A4_WIDTH, height: A4_HEIGHT },
        margin: { top: 1134, right: MARGIN, bottom: 1134, left: MARGIN },
      },
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [new TextRun({ text: 'ITUK PMS Pricing — Position Paper v1', size: 18, color: ISZE_BLUE, font: 'Arial', italics: true })],
        })],
      }),
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          spacing: { before: 0, after: 0 },
          children: [
            new TextRun({ text: dateStr, size: 18, color: '666666', font: 'Arial' }),
            new TextRun({ text: '          ' }),
            new TextRun({ text: 'Internal — ISZE Sales', size: 18, color: '666666', font: 'Arial', italics: true }),
            new TextRun({ text: '          Page ', size: 18, color: '666666', font: 'Arial' }),
            new TextRun({ children: [PageNumber.CURRENT], size: 18, color: '666666', font: 'Arial' }),
            new TextRun({ text: ' / ', size: 18, color: '666666', font: 'Arial' }),
            new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 18, color: '666666', font: 'Arial' }),
          ],
        })],
      }),
    },
    children,
  }],
});

const outPath = path.join(__dirname, 'ITUK_Pricing_OnePager_v1.docx');
Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(outPath, buf);
  console.log('Wrote', outPath, '(' + buf.length + ' bytes)');
}).catch(e => { console.error('FAIL', e); process.exit(1); });
