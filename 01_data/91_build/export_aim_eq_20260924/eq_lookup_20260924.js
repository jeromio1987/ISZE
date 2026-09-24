// EQ-Hit lookup for the EXPORT.XLSX price extract — 2026-09-24
// Injected into the signed-in Snap-on EQ tab via CDP Runtime.evaluate.
// Results land in window.__eaim.results; harvested per batch over CDP.
//
// Exposes:
//   await window.__eaim.lookup(pn)        one part number -> a result row
//   window.__eaim.results                 accumulated rows
//   await window.__eaim.run(pns, gapMs)   sequential batch

(() => {
  if (window.__eaim && window.__eaim.__ready) return "already installed";

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  const pnInput = () => {
    const byPh = document.querySelector('input[placeholder="Part Number"]');
    if (byPh) return byPh;
    // On the results page the field carries no placeholder; it is the only
    // visible text input that is not the VIN box and not a masked VIN field.
    return (
      [...document.querySelectorAll("input")].find((i) => {
        const r = i.getBoundingClientRect();
        const isMasked = (i.className || "").includes("inputMask");
        const isVin = (i.placeholder || "") === "Enter VIN";
        return (
          i.type === "text" &&
          r.width > 0 &&
          r.height > 0 &&
          !isMasked &&
          !isVin &&
          !(i.className || "").includes("ag-input-field")
        );
      }) || null
    );
  };

  const searchBtn = () =>
    [...document.querySelectorAll("button")].find(
      (b) => (b.title || "").trim() === "Perform search"
    ) || null;

  const totalResults = () => {
    let t = null;
    document.querySelectorAll("div.right").forEach((e) => {
      const m = (e.textContent || "").trim().match(/^Total Results:?\s*(\d+)/);
      if (m) t = +m[1];
    });
    return t;
  };

  const nativeSet = Object.getOwnPropertyDescriptor(
    window.HTMLInputElement.prototype,
    "value"
  ).set;

  window.__eaim = window.__eaim || {};
  window.__eaim.results = window.__eaim.results || [];
  window.__eaim.__ready = true;

  window.__eaim.lookup = async function (pn) {
    const inp = pnInput();
    const btn = searchBtn();
    if (!inp || !btn) return { pn, eq_status: "ERROR", error: "no controls" };

    inp.focus();
    nativeSet.call(inp, pn);
    inp.dispatchEvent(new InputEvent("input", { bubbles: true, data: pn, inputType: "insertText" }));
    inp.dispatchEvent(new Event("change", { bubbles: true }));
    await sleep(90);

    const r = btn.getBoundingClientRect();
    const cx = r.left + r.width / 2;
    const cy = r.top + r.height / 2;
    ["pointerdown", "mousedown", "pointerup", "mouseup", "click"].forEach((t) =>
      btn.dispatchEvent(
        new MouseEvent(t, {
          bubbles: true,
          cancelable: true,
          view: window,
          clientX: cx,
          clientY: cy,
          button: 0,
        })
      )
    );

    const t0 = Date.now();
    let total = null;
    let headerOk = false;
    while (Date.now() - t0 < 15000) {
      const h = (document.querySelector(".part-search-header") || {}).textContent || "";
      if (h.includes(pn)) {
        headerOk = true;
        total = totalResults();
        if (total !== null) break;
      }
      await sleep(180);
    }
    if (!headerOk) return { pn, eq_status: "ERROR", error: "header timeout" };

    if (total === 0) {
      return { pn, eq_status: "NOT_FOUND", eq_total: 0, found: false };
    }

    await sleep(300);
    const rows = [...document.querySelectorAll(".ag-row")].filter((rr) =>
      /\d{3,6}\s*-\s*[A-Z0-9]{2,4}/.test(rr.textContent || "")
    );

    const out = {
      pn,
      eq_status: "FOUND",
      eq_total: total,
      found: true,
      row_count: rows.length,
      eq_catalog: "",
      eq_fig_key: "",
      eq_fig_name: "",
      eq_part_name: "",
    };

    if (rows.length) {
      const cells = [...rows[0].querySelectorAll(".ag-cell")].map((c) =>
        (c.textContent || "").trim()
      );
      out.eq_catalog = cells.join(" | ").slice(0, 300);
      const fk = cells.find((c) => /^\d{3,6}\s*-\s*[A-Z0-9]{2,4}$/.test(c));
      if (fk) out.eq_fig_key = fk.replace(/\s+/g, "");
      rows[0].click();
      await sleep(900);
    }

    for (let i = 0; i < 25; i++) {
      const txt = document.body.innerText || "";
      const m = txt.match(/FIG Name\s*[\r\n]+Part Name\s*[\r\n]+([^\r\n]+)[\r\n]+([^\r\n]+)/);
      if (m && m[1].trim() && !/^FIG Name/i.test(m[1])) {
        out.eq_fig_name = m[1].trim();
        out.eq_part_name = m[2].trim();
        break;
      }
      await sleep(180);
    }

    return out;
  };

  window.__eaim.run = async function (pns, gapMs) {
    if (!Array.isArray(pns) || !pns.length) return "no pns";
    if (window.__eaim.running) return "already running";
    gapMs = gapMs || 1800;
    const start = window.__eaim.results.length;
    window.__eaim.running = true;
    window.__eaim.started = Date.now();
    for (let i = 0; i < pns.length; i++) {
      if (window.__eaim.cancelRequested) break;
      let hit;
      try {
        hit = await window.__eaim.lookup(pns[i]);
      } catch (e) {
        hit = { pn: pns[i], eq_status: "ERROR", error: String((e && e.message) || e) };
      }
      window.__eaim.results.push(hit);
      window.__eaim.last = hit;
      if (i < pns.length - 1) await sleep(gapMs);
    }
    window.__eaim.running = false;
    window.__eaim.elapsedMs = Date.now() - window.__eaim.started;
    return {
      added: window.__eaim.results.length - start,
      total: window.__eaim.results.length,
      elapsedMs: window.__eaim.elapsedMs,
    };
  };

  return "installed";
})();
