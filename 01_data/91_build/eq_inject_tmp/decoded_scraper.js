// EQ-Hit overnight scraper 20260919 — Part Number placeholder (Glass browser safe)
window.__EQ_DOUBT_OPEN_PNS = window.__EQ_DOUBT_OPEN_PNS || [];
window.__eqDoubtResults = window.__eqDoubtResults || [];

window.__eqDoubtLookup = async function (pn) {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const pnInput = () => {
    const byPh = document.querySelector('input[placeholder="Part Number"]');
    if (byPh) return byPh;
    const btn = [...document.querySelectorAll("button")].find(
      (b) => (b.title || "") === "Perform search"
    );
    if (!btn) return null;
    const grp = btn.closest(".p-toolbar-group-right") || btn.parentElement;
    const texts = [...(grp ? grp.querySelectorAll('input[type="text"]') : [])];
    return (
      texts.find((i) => !/inputMask/.test(i.className || "")) ||
      texts[texts.length - 1] ||
      null
    );
  };
  const searchBtn = () =>
    [...document.querySelectorAll("button")].find(
      (b) => (b.title || "") === "Perform search"
    );
  const getTotal = () => {
    let t = null;
    document.querySelectorAll("div.right").forEach((e) => {
      const m = (e.textContent || "")
        .trim()
        .match(/^Total Results:?\s*(\d+)/);
      if (m) t = +m[1];
    });
    return t;
  };

  const inp = pnInput();
  const btn = searchBtn();
  if (!inp || !btn)
    return { pn, error: "no controls", eq_status: "ERROR" };

  const nativeSet = Object.getOwnPropertyDescriptor(
    window.HTMLInputElement.prototype,
    "value"
  ).set;
  inp.focus();
  nativeSet.call(inp, pn);
  inp.dispatchEvent(
    new InputEvent("input", {
      bubbles: true,
      data: pn,
      inputType: "insertText",
    })
  );
  inp.dispatchEvent(new Event("change", { bubbles: true }));
  await sleep(80);
  btn.click();

  const t0 = Date.now();
  let total = null,
    headerOk = false;
  while (Date.now() - t0 < 12000) {
    const h =
      (document.querySelector(".part-search-header") || {}).textContent || "";
    if (h.includes(pn)) {
      headerOk = true;
      total = getTotal();
      if (total !== null) break;
    }
    await sleep(180);
  }
  if (!headerOk)
    return { pn, error: "header timeout", eq_status: "ERROR" };
  if (total === 0) {
    return {
      pn,
      eq_status: "NOT_FOUND",
      eq_total: 0,
      found: false,
      eq_fig_name: "",
      eq_part_name: "",
      eq_catalog: "",
      method: "ui",
    };
  }

  await sleep(250);
  const rows = [...document.querySelectorAll(".ag-row")].filter((rr) =>
    /\d{4,6}\s*-\s*/.test(rr.textContent || "")
  );
  let catalog = "";
  if (rows.length) {
    catalog = (rows[0].textContent || "")
      .trim()
      .replace(/\s+/g, " ")
      .slice(0, 160);
    rows[0].click();
    await sleep(800);
  }

  let fig_name = "",
    part_name = "";
  for (let i = 0; i < 20; i++) {
    const txt = document.body.innerText || "";
    const m = txt.match(
      /FIG Name\s*[\r\n]+Part Name\s*[\r\n]+([^\r\n]+)[\r\n]+([^\r\n]+)/
    );
    if (m && m[1].trim() && !/^FIG Name/i.test(m[1])) {
      fig_name = m[1].trim();
      part_name = m[2].trim();
      break;
    }
    await sleep(180);
  }

  return {
    pn,
    eq_status: "FOUND",
    eq_total: total,
    found: true,
    eq_fig_name: fig_name,
    eq_part_name: part_name,
    eq_catalog: catalog,
    method: "ui",
    applied: "N",
  };
};

window.__eqDoubtRun = async function (pns, gapMs) {
  if (!pns || !pns.length) return "no pns";
  if (window.__eqDoubtState && window.__eqDoubtState.running)
    return "already running";
  gapMs = gapMs || 2200;
  window.__eqDoubtState = {
    total: pns.length,
    done: 0,
    running: true,
    started: Date.now(),
  };
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  for (let i = 0; i < pns.length; i++) {
    if (window.__eqDoubtState.cancelRequested) break;
    let hit;
    try {
      hit = await window.__eqDoubtLookup(pns[i]);
    } catch (e) {
      hit = {
        pn: pns[i],
        error: String((e && e.message) || e),
        eq_status: "ERROR",
      };
    }
    window.__eqDoubtResults.push(hit);
    window.__eqDoubtState.done = i + 1;
    window.__eqDoubtState.last = hit;
    if (i < pns.length - 1) await sleep(gapMs);
  }
  window.__eqDoubtState.running = false;
  window.__eqDoubtState.elapsedMs =
    Date.now() - window.__eqDoubtState.started;
  return window.__eqDoubtState;
};

"scraper_v2_ok";
