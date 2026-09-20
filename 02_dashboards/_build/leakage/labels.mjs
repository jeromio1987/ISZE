/* Approved label dictionary - ISZE Distributor Leakage Cockpit.
 *
 * Single place where every user-facing string for this tool is defined. The build
 * refuses to compile if any of these values contains banned vocabulary, so Mode A
 * copy cannot drift into internal or banned language by accident.
 *
 * See .cursor/rules/isze-spoken-labels.mdc and isze-pricing-no-street-ui.mdc.
 */

export const BANNED = [
  // spoken-label bans
  "sell-out", "sell out", "sellout",
  "street", "street fills", "street index", "street eur", "street price",
  "wallet", "wallet eur", "parts wallet",
  "book b",
  // internal nicknames that must never reach a distributor
  "iml v7", "model b", "prism lane", "interval model",
  "tier a", "mode a", "mode b", "ship gate", "ship-gate",
  "harness", "loss function", "grain", "spar", "cartoon", "brain",
  // dealer-cost-plus shorthand
  "x1.785", "×1.785",
  // pipeline jargon
  "parquet", "payload", "csv", "yaml", "dashboard json", "sold-to", "sold_to",
  "pr00", "prism", "pbi", "sap",
];

/* Words that are legitimate business English in this context and must not trip the
 * scanner. Kept explicit so a future reviewer can see the exemptions rather than
 * guessing why a check passed. */
export const ALLOWED_CONTEXTS = [
  // "reference dealer price" is the approved substitute, so "reference" is fine.
  "reference dealer price",
];

export const L = {
  tool: {
    cockpitTitle: "Distributor opportunity cockpit",
    cockpitSub: "Where measured billing and modelled gaps appear, by market — diagnostics are not additive",
    packTitle: "Sales performance review",
    packSub: "Parts revenue, service demand and fleet spend",
    internalBadge: "Internal",
    customerBadge: "Prepared for distribution",
  },

  nav: {
    evolution: "Sales evolution",
    dynamics: "Monthly dynamics",
    gps: "Target spend vs billed",
    pms: "Service families",
    mix: "Brand mix",
    aim: "Part-group risk",
    subgroup: "Subcategories",
    unbilled: "Unbilled modelled demand",
    actions: "What to act on",
    league: "Partner league",
    honesty: "What this does not claim",
  },

  q: {
    evolution: "How has our parts business moved, on the same months of each year?",
    dynamics: "What does the monthly movement look like inside the year?",
    gps: "How much of the target spend per truck are we actually billing?",
    pms: "Which service families are we capturing, and which are slipping?",
    mix: "Is the brand mix drifting, and in which part families?",
    aim: "How much of our revenue sits in part groups we are least likely to keep?",
    subgroup: "Where in the part hierarchy is the other-brand share highest?",
    unbilled: "Where does modelled service demand exceed parts billed?",
    actions: "Which part numbers should we be talking about, and why?",
    league: "Which partners are critical, and on what evidence?",
    honesty: "What are the limits of this analysis?",
  },

  term: {
    partsRevenue: "Parts revenue",
    gpsEligible: "Parts eligible for target-spend reporting",
    warranty: "Warranty parts, excluded from target spend",
    ceiling: "Target spend ceiling",
    captured: "Billed against the ceiling",
    gap: "Addressable gap",
    structural: "Structurally unaddressable",
    beyondCeiling: "Billed above the ceiling",
    captureRate: "Share of expected service demand captured",
    expectedDemand: "Expected service demand",
    actualDemand: "Parts billed",
    fleet: "Vehicles in service",
    spendPerTruck: "Parts billed per vehicle in service",
    highRisk: "Revenue in part groups most at risk of being replaced",
    competingBrand: "Another brand",
    ownBrand: "Own brand",
    peerMedian: "Same-type market median",
    modelled: "Modelled, not observed",
    gapTypeSubstitution: "Bought another brand instead",
    gapTypeUnderService: "Fewer service visits than the fleet needs",
    gapTypeCatalog: "No part of ours fits this application",
    dealerDetail: "Dealer outlet detail",
    partsFamily: "Part family",
    serviceFamily: "Service family",
    sameMonths: "Same months of each year",
    averageMonth: "Average month",
  },

  basis: {
    likeForLike: "Like for like",
    windowNote: "The current year is only part complete, so every comparison here uses the same months of each year. Nothing is annualised.",
    partYear: "Part year, not comparable with a full year",
    averageMonthNote: "An average month is shown so periods of different length can be compared without annualising anything.",
  },

  status: {
    ok: "Within range",
    watch: "Watch",
    critical: "Critical",
    unknown: "Not measured",
    unavailable: "Not available for this market",
  },

  msg: {
    thinPeer: (n) => `Only ${n} comparable market${n === 1 ? "" : "s"} available, so no median is shown. A median over fewer than three markets would read as a benchmark when it is not one.`,
    noPeer: "No comparable market group for this selection, so nothing is benchmarked on this page.",
    noDealerDetail: "This market's detail stops at the national total. No dealer outlet file exists, so no network view is shown rather than an implied one.",
    notScored: "This market has no service records in the model, so it is not scored. It is listed so the gap is visible rather than silently dropped.",
    vintage: (s) => `Vintage: ${s}.`,
    unitsNeedContext: "Units are shown beside euro and the fleet base. A unit count on its own cannot be judged.",
  },

  peer: {
    label: "Compare against",
    scope: "Same customer type",
    region: "Same region",
    fleet: "Similar fleet size",
    all: "All markets",
    anonymous: "Benchmarks are an unlabelled median across comparable markets. No other distributor is named.",
  },

  honesty: {
    title: "What this page does not claim",
    mileage: "Distance travelled",
    capture: "Capture above 100%",
    dealer: "Dealer-level detail",
    vintage: "Model vintage",
    mix: "Volume and price split",
    scope: "Market coverage",
    fleet: "Fleet base",
    peer: "Peer comparison",
  },
};

/* Fails the build rather than shipping banned language. */
export function assertLabelsClean(extraStrings = []) {
  const flat = [];
  const walk = (node, path) => {
    if (typeof node === "function") return;              // dynamic copy checked at render time
    if (typeof node === "string") { flat.push([path, node]); return; }
    if (node && typeof node === "object") {
      for (const [k, v] of Object.entries(node)) walk(v, path ? `${path}.${k}` : k);
    }
  };
  walk(L, "L");
  for (const [n, s] of extraStrings.entries()) flat.push([`extra[${n}]`, s]);

  const hits = [];
  for (const [path, s] of flat) {
    const low = String(s).toLowerCase();
    for (const bad of BANNED) {
      if (!low.includes(bad)) continue;
      const exempt = ALLOWED_CONTEXTS.some((ok) => low.includes(ok));
      if (!exempt) hits.push(`${path}: "${bad}" in "${s}"`);
    }
  }
  if (hits.length) {
    throw new Error("Banned vocabulary in label dictionary:\n  " + hits.join("\n  "));
  }
  return flat.length;
}
