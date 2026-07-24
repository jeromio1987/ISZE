/* IDS DB Parts posture — app with hover explainers (no Python f-string braces). */
(function () {
  const D = typeof DATA !== "undefined" ? DATA : {};
  const G = D.glossary || {};
  const navy = "#1a2b4a";
  const terra = "#c0552d";
  const muted = "#6b6256";
  const green = "#2e7d54";
  const amber = "#8a6a00";
  const red = "#b23b3b";

  function el(id) {
    return document.getElementById(id);
  }

  function tip(label, key) {
    const t = G[key] || "";
    if (!t) return label;
    return (
      '<span class="tip" tabindex="0" data-tip="' +
      String(t).replace(/"/g, "&quot;") +
      '">' +
      label +
      "</span>"
    );
  }

  function archClass(a) {
    const s = (a || "").toLowerCase();
    if (s.indexOf("floor") >= 0) return "floor";
    if (s.indexOf("ops") >= 0) return "ops";
    if (s.indexOf("ageing") >= 0 || s.indexOf("aging") >= 0) return "uio";
    if (s.indexOf("mix") >= 0) return "mix";
    if (s.indexOf("capture") >= 0) return "capture";
    if (s.indexOf("uio") >= 0 || s.indexOf("€") >= 0) return "uio";
    if (s.indexOf("balanced") >= 0) return "ok";
    return "";
  }

  function metric(labelHtml, val) {
    return (
      '<div><div class="k">' +
      labelHtml +
      '</div><div class="v">' +
      (val == null || val === "" ? "—" : val) +
      "</div></div>"
    );
  }

  function renderHygiene() {
    const h = D.hygiene || {};
    el("hygieneLead").innerHTML =
      "Raw dashboard rows inflate network size (" +
      tip("Benelux rollup", "benelux") +
      " + empty " +
      tip("MIDI 0% shells", "zero_shells") +
      "). Clean averages exclude both before we talk about network D.";
    el("hygieneStats").innerHTML =
      metric(tip("Raw rows", "raw_rows"), h.raw_dealer_rows) +
      metric(tip("Clean rows", "clean_rows"), h.clean_dealer_rows) +
      metric(
        tip("Raw network D", "section_d"),
        h.raw_network_d_pct != null ? h.raw_network_d_pct + "%" : "—"
      ) +
      metric(
        tip("Clean network D", "section_d"),
        h.clean_network_d_pct != null ? h.clean_network_d_pct + "%" : "—"
      ) +
      metric(tip("Dropped Benelux", "benelux"), h.dropped_benelux_rollup) +
      metric(tip("Dropped 0% shells", "zero_shells"), h.dropped_zero_shells);
    el("hygieneNote").textContent = h.note || "";
  }

  function renderCorr() {
    el("corrIntro").innerHTML =
      "Each bar is a " +
      tip("Pearson r", "pearson") +
      " across distributors (not inside one DB). " +
      "<b>PMS</b> and <b>KPI Parts Sales per Unit</b> are removed from this list. " +
      "Intensity = " +
      tip("GPS €/UIO", "gps_spu") +
      "; mix = " +
      tip("genuine share (€ mix)", "genuine_mix") +
      ". Ops companions = " +
      tip("fill", "fill") +
      " &amp; " +
      tip("MOS", "mos") +
      ".";

    el("corrCaption").innerHTML =
      tip("Pearson r", "pearson") +
      " — " +
      tip("IDS Section D %", "section_d") +
      " vs: genuine mix, GPS €/UIO, fill, MOS (PMS &amp; KPI SPU excluded)";

    const corr = D.correlations_chart || D.correlations || {};
    const tipKey = {
      genuine_share_eur: "genuine_mix",
      gps_spu_eur: "gps_spu",
      kpi_fill_rate: "fill",
      kpi_mos_days: "mos",
    };
    const order = ["genuine_share_eur", "gps_spu_eur", "kpi_fill_rate", "kpi_mos_days"];
    const labels = [];
    const vals = [];
    const colors = [];
    const keys = [];
    order.forEach(function (k) {
      const v = corr[k];
      if (!v || v.r == null) return;
      keys.push(k);
      labels.push(v.label || k);
      vals.push(Math.round(v.r * 100) / 100);
      colors.push(v.r >= 0.3 ? green : v.r <= -0.3 ? red : amber);
    });
    const ctx = el("corrBars");
    if (!ctx || !window.Chart) return;
    new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            data: vals,
            backgroundColor: colors,
            borderWidth: 0,
            barThickness: 22,
          },
        ],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              title: function (items) {
                return labels[items[0].dataIndex];
              },
              label: function (c) {
                const i = c.dataIndex;
                const k = keys[i];
                const meta = corr[k] || {};
                const n = meta.n != null ? meta.n : "?";
                const markets = (meta.markets || []).join(", ") || "—";
                return ["r = " + c.raw + "  (n = " + n + " markets)", "Markets: " + markets];
              },
              afterBody: function (items) {
                const k = keys[items[0].dataIndex];
                const gkey = tipKey[k];
                return gkey && G[gkey] ? ["", G[gkey]] : [];
              },
            },
          },
        },
        scales: {
          x: {
            min: -1,
            max: 1,
            ticks: { color: muted, stepSize: 0.5 },
            grid: { color: "#e6e0d6" },
            title: { display: true, text: "Pearson r (−1 … +1)", color: muted },
          },
          y: { ticks: { color: navy, font: { size: 11 } }, grid: { display: false } },
        },
      },
    });

    const mixBox = el("mixVsGpsExplainer");
    if (mixBox) {
      mixBox.innerHTML =
        "<b>Difference between the two metrics in your screenshot</b><br/><br/>" +
        "<b>1) " +
        tip("Genuine parts share (€ mix)", "genuine_mix") +
        "</b> — <i>What kind of parts €?</i><br/>" +
        "Formula: Genuine € ÷ (Genuine € + BVP €).<br/>" +
        "It is a <b>mix / quality split</b>: out of every €100 in that basket, how much is genuine vs BVP.<br/>" +
        "Example: <b>80%</b> = €80 genuine + €20 BVP. High ≠ more total sales; it means the € you do sell lean genuine.<br/>" +
        "Unit: <b>%</b>. Does not use UIO.<br/><br/>" +
        "<b>2) " +
        tip("GPS spend per unit (€/UIO)", "gps_spu") +
        "</b> — <i>How much parts € per vehicle?</i><br/>" +
        "Formula: parts € intensity ÷ Units In Operation (parc).<br/>" +
        "It is an <b>intensity</b> metric: how hard the parc is worked in €/vehicle — closer to what KPI “Parts Sales per Unit” tried to measure, and better filled.<br/>" +
        "Example: <b>€180 / UIO</b> = about €180 of parts activity per vehicle in the parc.<br/>" +
        "Unit: <b>€ per vehicle</b>. Green/amber = PRISM traffic light on that intensity.<br/><br/>" +
        "<b>One-liner:</b> Genuine mix = <i>composition</i> of the basket. GPS €/UIO = <i>how much €</i> per vehicle. You need both; one does not replace the other.";
    }
  }

  function makeScatter(canvasId, captionId, captionHtml, yKey, yLabel, yMax, asPct) {
    const cap = el(captionId);
    if (cap) cap.innerHTML = captionHtml;
    const cards = D.db_cards || [];
    const pts = cards
      .filter(function (c) {
        return c.ids_d_avg != null && c[yKey] != null;
      })
      .map(function (c) {
        var y = Number(c[yKey]);
        if (asPct) y = Math.round(y * 1000) / 10;
        else y = Math.round(y);
        return {
          x: Math.round(c.ids_d_avg * 1000) / 10,
          y: y,
          label: c.ids_country,
        };
      });
    const ctx = el(canvasId);
    if (!ctx || !window.Chart) return;
    new Chart(ctx, {
      type: "scatter",
      data: {
        datasets: [
          {
            data: pts,
            backgroundColor: terra,
            pointRadius: 7,
            pointHoverRadius: 9,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function (c) {
                const p = c.raw;
                const ySuffix = asPct ? "%" : " €/UIO";
                return p.label + ": D " + p.x + "% · " + yLabel + " " + p.y + ySuffix;
              },
            },
          },
        },
        scales: {
          x: {
            title: { display: true, text: "IDS Section D avg %", color: muted },
            min: 60,
            max: 100,
            ticks: { color: muted },
            grid: { color: "#e6e0d6" },
          },
          y: {
            title: { display: true, text: yLabel, color: muted },
            min: 0,
            max: yMax,
            ticks: { color: muted },
            grid: { color: "#e6e0d6" },
          },
        },
      },
    });
  }

  function renderScatters() {
    makeScatter(
      "scatGen",
      "scatGenCaption",
      "Scatter — " +
        tip("IDS Section D %", "section_d") +
        " vs " +
        tip("Genuine parts share (€ mix)", "genuine_mix") +
        " — composition of Genuine vs BVP",
      "genuine_share_eur",
      "Genuine mix",
      100,
      true
    );
    makeScatter(
      "scatGps",
      "scatGpsCaption",
      "Scatter — " +
        tip("IDS Section D %", "section_d") +
        " vs " +
        tip("GPS spend per unit (€/UIO)", "gps_spu") +
        " — intensity (€ per vehicle); replaces KPI Parts Sales per Unit on this chart",
      "gps_spu_eur",
      "GPS €/UIO",
      300,
      false
    );
  }

  function renderCards() {
    const ban = el("gpsWarrantyBanner");
    if (ban) {
      ban.innerHTML =
        "<b>GPS warranty:</b> " +
        (D.gps_warranty_note ||
          "Headline GPS €/UIO includes warranty parts. Cards also show €/UIO ex-warranty.");
    }
    const root = el("cards");
    if (!root) return;
    const cards = D.db_cards || [];
    root.innerHTML = cards
      .map(function (c) {
        const gps =
          c.gps_spu_eur != null ? Math.round(c.gps_spu_eur) + " €" : "—";
        const gpsEx =
          c.gps_spu_ex_warranty_eur != null
            ? Math.round(c.gps_spu_ex_warranty_eur) + " €"
            : "—";
        const park =
          c.park_change_5y_pct_disp != null
            ? (c.park_change_5y_pct_disp > 0 ? "+" : "") +
              c.park_change_5y_pct_disp +
              "%"
            : "—";
        const light = (c.gps_light || "").toLowerCase();
        const lightBadge =
          light === "green"
            ? '<span class="badge green">' + tip("GPS green (incl. warr.)", "gps_light") + "</span>"
            : light === "amber"
              ? '<span class="badge amber">' + tip("GPS amber (incl. warr.)", "gps_light") + "</span>"
              : light
                ? '<span class="badge red">GPS ' + light + "</span>"
                : "";
        const ageBadge =
          c.ageing_risk === "high"
            ? '<span class="badge red">' + (c.ageing_label || "Older park") + "</span> "
            : c.ageing_risk === "elevated"
              ? '<span class="badge amber">' + (c.ageing_label || "Ageing") + "</span> "
              : c.ageing_risk === "low"
                ? '<span class="badge green">' + (c.ageing_label || "Younger") + "</span> "
                : "";
        return (
          '<article class="card">' +
          '<div class="top">' +
          "<div><h3>" +
          (c.ids_country || "") +
          (c.prism_db ? " · " + c.prism_db : "") +
          '</h3><div class="muted" style="font-size:.82rem">Owner TBD · ' +
          (c.dealer_count || "—") +
          " scored dealers</div></div>" +
          '<span class="arch ' +
          archClass(c.archetype) +
          '">' +
          (c.archetype || "") +
          "</span>" +
          "</div>" +
          "<p>" +
          (c.thesis || "") +
          "</p>" +
          '<div class="metrics">' +
          metric(tip("D avg", "section_d"), c.ids_d_avg_pct != null ? c.ids_d_avg_pct + "%" : "—") +
          metric(tip("D min", "d_min"), c.ids_d_min_pct != null ? c.ids_d_min_pct + "%" : "—") +
          metric(
            tip("Genuine", "genuine_mix"),
            c.genuine_share_pct != null ? c.genuine_share_pct + "%" : "—"
          ) +
          metric(tip("Fill", "fill"), c.fill_pct != null ? c.fill_pct + "%" : "—") +
          metric(
            tip("MOS", "mos"),
            c.kpi_mos_days != null ? Math.round(c.kpi_mos_days) + "d" : "—"
          ) +
          metric(tip("€/UIO incl.w", "gps_spu"), gps) +
          metric(tip("€/UIO ex-w", "gps_spu_ex"), gpsEx) +
          metric(tip("Park 5y Δ", "park_age"), park) +
          metric(tip("CAP D-only #", "cap_d_only"), c.cap_d_only) +
          metric(tip("CAP D+C #", "cap_d_plus_c"), c.cap_d_plus_c) +
          "</div>" +
          '<p class="muted" style="font-size:.82rem;margin:.35rem 0 0">' +
          tip("CAP D-only #", "cap_d_only") +
          " / " +
          tip("CAP D+C #", "cap_d_plus_c") +
          " = dealer headcounts in Kaizen buckets (not Excel question D.1 / D.4). " +
          tip("Park 5y Δ", "park_age") +
          " = net UIO change (proxy for ageing).</p>" +
          ageBadge +
          lightBadge +
          '<ol class="asks"><li>' +
          (c.ask_1 || "") +
          "</li><li>" +
          (c.ask_2 || "") +
          "</li></ol>" +
          "</article>"
        );
      })
      .join("");
  }

  function renderParkFill() {
    const pf = D.park_fill || {};
    const lead = el("parkLead");
    if (lead) {
      const r = pf.r_park_change_vs_fill;
      lead.innerHTML =
        "Hypothesis: older / shrinking parks → harder repairs → lower " +
        tip("first fill", "fill") +
        ". " +
        "Across DBs with both values: Pearson r (park 5y Δ vs fill) = <b>" +
        (r == null ? "n/a" : Math.round(r * 100) / 100) +
        "</b> (n=" +
        (pf.n || 0) +
        "). " +
        "Positive r would mean growing/younger parks tend to fill better.";
    }
    const meth = el("parkMethod");
    if (meth) meth.textContent = pf.method_note || "";

    const rows = pf.rows || [];
    el("parkCaption") &&
      (el("parkCaption").innerHTML =
        "Scatter — " +
        tip("Park 5y Δ %", "park_age") +
        " vs " +
        tip("Fill %", "fill") +
        " (each point = one DB)");

    const pts = rows
      .filter(function (r) {
        return r.park_change_5y_pct != null && r.fill_pct != null;
      })
      .map(function (r) {
        return {
          x: Math.round(r.park_change_5y_pct * 1000) / 10,
          y: r.fill_pct,
          label: r.country,
        };
      });
    const ctx = el("scatParkFill");
    if (ctx && window.Chart) {
      new Chart(ctx, {
        type: "scatter",
        data: {
          datasets: [
            {
              data: pts,
              backgroundColor: terra,
              pointRadius: 7,
              pointHoverRadius: 9,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: function (c) {
                  const p = c.raw;
                  return p.label + ": park Δ " + p.x + "% · fill " + p.y + "%";
                },
              },
            },
          },
          scales: {
            x: {
              title: { display: true, text: "Park 5y net change % (− = shrinking/older)", color: muted },
              ticks: { color: muted },
              grid: { color: "#e6e0d6" },
            },
            y: {
              title: { display: true, text: "First fill %", color: muted },
              min: 50,
              max: 100,
              ticks: { color: muted },
              grid: { color: "#e6e0d6" },
            },
          },
        },
      });
    }

    const table = el("parkTable");
    if (!table) return;
    table.querySelector("thead").innerHTML =
      "<tr><th>Country</th><th>UIO name</th><th>UIO</th><th>Park 5y Δ</th><th>Ageing read</th><th>Fill</th><th>D avg</th><th>Note</th></tr>";
    table.querySelector("tbody").innerHTML = rows
      .map(function (r) {
        const dlt =
          r.park_change_5y_pct == null
            ? "—"
            : (r.park_change_5y_pct > 0 ? "+" : "") +
              Math.round(r.park_change_5y_pct * 1000) / 10 +
              "%";
        const risk =
          r.ageing_risk === "high"
            ? '<span class="badge red">' + (r.ageing_label || "") + "</span>"
            : r.ageing_risk === "elevated"
              ? '<span class="badge amber">' + (r.ageing_label || "") + "</span>"
              : r.ageing_risk === "low"
                ? '<span class="badge green">' + (r.ageing_label || "") + "</span>"
                : r.ageing_label || "—";
        return (
          "<tr><td>" +
          (r.country || "") +
          "</td><td>" +
          (r.uio_name || "—") +
          "</td><td>" +
          (r.uio_units != null ? Math.round(r.uio_units).toLocaleString() : "—") +
          "</td><td>" +
          dlt +
          "</td><td>" +
          risk +
          "</td><td>" +
          (r.fill_pct != null ? r.fill_pct + "%" : "—") +
          "</td><td>" +
          (r.ids_d_avg_pct != null ? r.ids_d_avg_pct + "%" : "—") +
          "</td><td>" +
          (r.note || "") +
          "</td></tr>"
        );
      })
      .join("");
  }

  function renderCap() {
    el("capLead").innerHTML =
      "Same country, different CAP: " +
      tip("D-only", "cap_d_only") +
      " = counter / inventory / genuine display process. " +
      tip("D+C", "cap_d_plus_c") +
      " = Parts + Service — workshop pull-through and RO attach. " +
      "Weak = below that country’s median for the section, but never treated as weak if still above 65%.";

    el("capCaption").innerHTML =
      "Dealers per country by CAP type (hover " +
      tip("D-only", "cap_d_only") +
      " / " +
      tip("D+C", "cap_d_plus_c") +
      " / " +
      tip("C-only", "cap_c_only") +
      ")";

    const split = D.cap_split || {};
    const rows = (split.countries || []).slice().sort(function (a, b) {
      const aw = (a.counts["D-only"] || 0) + (a.counts["D+C"] || 0);
      const bw = (b.counts["D-only"] || 0) + (b.counts["D+C"] || 0);
      return bw - aw;
    });
    const labels = rows.map(function (r) {
      return r.country;
    });
    const ctx = el("capStack");
    if (ctx && window.Chart) {
      new Chart(ctx, {
        type: "bar",
        data: {
          labels: labels,
          datasets: [
            {
              label: "D-only (counter/process)",
              data: rows.map(function (r) {
                return r.counts["D-only"] || 0;
              }),
              backgroundColor: terra,
              barThickness: 18,
            },
            {
              label: "D+C (workshop pull-through)",
              data: rows.map(function (r) {
                return r.counts["D+C"] || 0;
              }),
              backgroundColor: navy,
              barThickness: 18,
            },
            {
              label: "C-only",
              data: rows.map(function (r) {
                return r.counts["C-only"] || 0;
              }),
              backgroundColor: "#9aa7b8",
              barThickness: 18,
            },
            {
              label: "OK",
              data: rows.map(function (r) {
                return r.counts.OK || 0;
              }),
              backgroundColor: "#c8d9c8",
              barThickness: 18,
            },
          ],
        },
        options: {
          indexAxis: "y",
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: "bottom", labels: { boxWidth: 12, color: muted } },
            tooltip: {
              callbacks: {
                afterBody: function (items) {
                  const lab = items[0].dataset.label || "";
                  if (lab.indexOf("D+C") === 0) return G.cap_d_plus_c || "";
                  if (lab.indexOf("D-only") === 0) return G.cap_d_only || "";
                  if (lab.indexOf("C-only") === 0) return G.cap_c_only || "";
                  return "";
                },
              },
            },
          },
          scales: {
            x: {
              stacked: true,
              ticks: { color: muted, stepSize: 5 },
              grid: { color: "#e6e0d6" },
              title: { display: true, text: "Dealers", color: muted },
            },
            y: { stacked: true, ticks: { color: navy, font: { size: 11 } }, grid: { display: false } },
          },
        },
      });
    }

    const t = split.totals || {};
    el("capTotals").innerHTML =
      metric(tip("D-only", "cap_d_only"), t["D-only"]) +
      metric(tip("D+C", "cap_d_plus_c"), t["D+C"]) +
      metric(tip("C-only", "cap_c_only"), t["C-only"]) +
      metric("OK", t.OK);

    const ex = el("capExamples");
    if (!ex) return;
    const examples = split.examples || [];
    if (!examples.length) {
      ex.innerHTML = "";
      return;
    }
    ex.innerHTML =
      "<h3 style=\"margin-top:1rem\">Example weak dealers</h3>" +
      examples
        .map(function (e) {
          const badge =
            e.cap_type === "D+C"
              ? '<span class="badge red">' + tip("D+C", "cap_d_plus_c") + "</span>"
              : '<span class="badge amber">' + tip("D-only", "cap_d_only") + "</span>";
          return (
            '<div class="ex">' +
            badge +
            " <b>" +
            e.country +
            "</b> · " +
            e.name +
            " — D " +
            (e.d_pct != null ? Math.round(e.d_pct * 100) + "%" : "—") +
            " · C " +
            (e.c_pct != null ? Math.round(e.c_pct * 100) + "%" : "—") +
            "<br/><span class=\"muted\">" +
            (e.ask || "") +
            "</span></div>"
          );
        })
        .join("");
  }

  function renderSpuExplainer() {
    const root = el("spuExplainer");
    const note = el("spuCoverageNote");
    const cov = D.kpi_spu_coverage || {};
    if (!root) return;

    root.innerHTML =
      "<h3>Why KPI Parts Sales per Unit is off the correlation list</h3>" +
      "<p>That KPI Master row is the same <i>family</i> as " +
      tip("GPS €/UIO", "gps_spu") +
      " (€ parts activity per vehicle), but it is blank for IBX, ITUK, UMI, RSA, etc. " +
      "The old ~0.98 bar used only 3 markets. <b>We dropped it from the chart</b> and use GPS €/UIO for intensity.</p>" +
      "<h3>PMS off conclusions entirely</h3>" +
      "<p>PMS total capture is no longer on DB cards or theses in this pack (per request). " +
      "Focus stays on IDS D, genuine mix, fill/MOS, GPS €/UIO, and park age.</p>" +
      "<h3>GPS and warranty</h3>" +
      "<p>" +
      tip("GPS €/UIO", "gps_spu") +
      " headline <b>includes warranty</b>. Cards also show " +
      tip("€/UIO ex-w", "gps_spu_ex") +
      ".</p>" +
      "<h3>Reminder: genuine mix vs GPS</h3>" +
      "<ul>" +
      "<li><b>Genuine parts share (€ mix)</b> — % composition Genuine vs BVP.</li>" +
      "<li><b>GPS spend per unit (€/UIO)</b> — € intensity per vehicle (incl. warranty in headline).</li>" +
      "</ul>";

    note.innerHTML =
      "<b>KPI SPU coverage (reference only):</b> filled on IDS map = IUK, Romania, Petros. " +
      "Blank = IBX, ITUK, UMI, RSA, Poland, Malta, … → use GPS €/UIO.";

    const table = el("spuCoverage");
    if (!table) return;
    const rows = cov.rows || [];
    table.querySelector("thead").innerHTML =
      "<tr><th>Distributor (KPI name)</th><th>IDS link</th><th>KPI Parts €/unit</th><th>Use for intensity</th><th>Status</th></tr>";
    table.querySelector("tbody").innerHTML = rows
      .map(function (r) {
        const spu =
          r.kpi_spu_eur != null ? "€" + Math.round(r.kpi_spu_eur) : "— blank";
        const st =
          r.kpi_spu_eur != null
            ? '<span class="badge green">SPU filled (optional)</span>'
            : '<span class="badge amber">SPU blank — use GPS</span>';
        return (
          "<tr><td>" +
          (r.kpi_name || "") +
          "</td><td>" +
          (r.ids_countries || "—") +
          "</td><td>" +
          spu +
          "</td><td>GPS €/UIO on DB card</td><td>" +
          st +
          "</td></tr>"
        );
      })
      .join("");
  }

  function renderFoot() {
    const f = el("foot");
    if (!f) return;
    f.innerHTML =
      "Bronnen: IDS 2026 evaluation result reports (hygienic averages); PRISM PMS/GPS CY2025; KPI Master Parts Handling. " +
      "Correlation chart excludes PMS and KPI Parts Sales per Unit. Hover dotted terms for definitions. Israel = UMI only.";
  }

  renderHygiene();
  renderCorr();
  renderScatters();
  renderCards();
  renderParkFill();
  renderCap();
  renderSpuExplainer();
  renderFoot();
})();
