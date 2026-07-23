(function () {
  const ink = "#52514e",
    grid = "#e1e0d9",
    navy = "#2a78d6",
    terra = "#c0552d",
    grey = "#888780",
    red = "#e24b4a",
    green = "#1d9e75";
  const corr = DATA.correlations || {};
  const rows = DATA.join_rows || [];
  const focus = DATA.focus_dealers || [];

  function rTxt(v) {
    return v == null ? "—" : Number(v).toFixed(2);
  }

  const rFill = corr.kpi_fill_rate && corr.kpi_fill_rate.r;
  const rGen = corr.genuine_share_eur && corr.genuine_share_eur.r;
  const rPms = corr.pms_capture_genuine && corr.pms_capture_genuine.r;
  const rPmsTot = corr.pms_capture_total && corr.pms_capture_total.r;
  const rGps = corr.gps_spu_eur && corr.gps_spu_eur.r;

  function tip(label, text) {
    return (
      '<span class="tip" tabindex="0" data-tip="' +
      String(text)
        .replace(/&/g, "&amp;")
        .replace(/"/g, "&quot;")
        .replace(/\n/g, "&#10;") +
      '">' +
      label +
      "</span>"
    );
  }

  const TIP_R =
    "Pearson r (correlation) measures how two series move together across markets, from −1 to +1.\n+1 = perfect lockstep\n0 = no linear link\n−1 = perfect opposite\n\nExample: r = +0.5 on fill means countries with higher Section D tend to have higher first fill. Weak or negative r is still a finding — do not drop the metric.";
  const TIP_WAVE1 =
    "Wave-1 = the first 90-day Kaizen batch: a short call list of priority dealers (not a permanent blacklist). Fix Excel gaps + one commercial check, then expand to Wave-2.";

  let verdict =
    "<b>Thesis half-confirmed.</b> Markets with higher IDS Section D tend to show <b>higher genuine parts share</b> (" +
    tip("r", TIP_R) +
    "=" +
    rTxt(rGen) +
    ") and <b>higher KPI first fill</b> (" +
    tip("r", TIP_R) +
    "=" +
    rTxt(rFill) +
    "). ";
  verdict +=
    "But <b>PMS capture does not rise with Section D</b> (genuine capture " +
    tip("r", TIP_R) +
    "=" +
    rTxt(rPms) +
    ", total capture " +
    tip("r", TIP_R) +
    "=" +
    rTxt(rPmsTot) +
    "); GPS EUR/UIO is also weak (" +
    tip("r", TIP_R) +
    "=" +
    rTxt(rGps) +
    "). ";
  verdict +=
    "Meaning for Parts: a clean Section D score is a <b>process / stock / promo hygiene</b> signal — it does <b>not</b> replace attach and capture work. " +
    tip("Wave-1", TIP_WAVE1) +
    " therefore pairs Excel D-gaps (esp. D.2-10 fill/turnover &amp; D.1-8 Genuine/BVP promo) with RO/PMS Kaizen on <b>" +
    focus.length +
    " dealers</b>.";
  document.getElementById("verdict").innerHTML = verdict;
  document.getElementById("naming").innerHTML =
    "<b>Naming:</b> <i>Genuine parts share</i> = Genuine EUR / (Genuine+BVP) on the PMS mix (your GPS share). <i>GPS EUR/UIO</i> = PRISM spend per unit — different metric. <i>PMS capture</i> = sold vs expected service parts. KPI fill/MOS = distributor Parts Handling averages. n≈11 paired markets (ITUK excluded from D heatmap).";

  const corrList = Object.entries(corr).filter(function (e) {
    return e[1].r != null;
  });
  const bestAbs = corrList.length
    ? Math.max
        .apply(
          null,
          corrList.map(function (e) {
            return Math.abs(e[1].r);
          })
        )
        .toFixed(2)
    : "—";
  const stats = [
    ["Markets paired", rows.length],
    [tip("Wave-1 dealers", TIP_WAVE1), focus.length],
    [tip("Best |r|", TIP_R), bestAbs],
    ["Scored dealers", DATA.scored_dealers || "—"],
  ];
  document.getElementById("stats").innerHTML = stats
    .map(function (s) {
      return (
        '<div class="stat"><div class="n">' +
        s[1] +
        '</div><div class="l">' +
        s[0] +
        "</div></div>"
      );
    })
    .join("");

  function scatter(canvasId, yKey, yLabel, yIsPct) {
    const pts = rows
      .filter(function (r) {
        return (
          r.ids_d_avg != null &&
          r[yKey] != null &&
          !(typeof r[yKey] === "number" && isNaN(r[yKey]))
        );
      })
      .map(function (r) {
        return {
          x: +(r.ids_d_avg * 100).toFixed(1),
          y: yIsPct
            ? +(r[yKey] * 100).toFixed(1)
            : +(+r[yKey]).toFixed(1),
          n: r.ids_country,
        };
      });
    const labelsPlugin = {
      id: "lbl" + canvasId,
      afterDatasetsDraw: function (ch) {
        const c = ch.ctx,
          m = ch.getDatasetMeta(0);
        c.save();
        c.font = "11px sans-serif";
        c.fillStyle = ink;
        m.data.forEach(function (p, i) {
          const d = pts[i];
          c.textAlign = "left";
          c.fillText(d.n, p.x + 8, p.y + 3);
        });
        c.restore();
      },
    };
    new Chart(document.getElementById(canvasId), {
      type: "scatter",
      data: {
        datasets: [
          {
            data: pts,
            backgroundColor: terra,
            pointRadius: 7,
            borderColor: "#fff",
            borderWidth: 1.5,
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
                const d = pts[c.dataIndex];
                return d.n + ": D " + d.x + "% / " + yLabel + " " + d.y;
              },
            },
          },
        },
        scales: {
          x: {
            title: { display: true, text: "IDS Section D avg %", color: ink },
            min: 50,
            max: 100,
            grid: { color: grid },
            ticks: { color: ink },
          },
          y: {
            title: { display: true, text: yLabel, color: ink },
            grid: { color: grid },
            ticks: { color: ink },
          },
        },
      },
      plugins: [labelsPlugin],
    });
  }

  // Primary PMS view = TOTAL capture (sales is sales). Genuine share is an extra lens.
  scatter("scatPms", "pms_capture_total", "PMS total capture %", true);
  scatter("scatGen", "genuine_share_eur", "Genuine share %", true);
  scatter("scatGps", "gps_spu_eur", "GPS EUR / UIO", false);

  const corrKeys = [
    "pms_capture_genuine",
    "genuine_share_eur",
    "gps_spu_eur",
    "pms_capture_total",
    "kpi_fill_rate",
    "kpi_mos_days",
    "kpi_spu_eur",
  ];
  const corrLabs = corrKeys.map(function (k) {
    return corr[k] && corr[k].label
      ? corr[k].label.replace(" (CY2025)", "")
      : k;
  });
  const corrVals = corrKeys.map(function (k) {
    return corr[k] && corr[k].r != null ? +corr[k].r.toFixed(2) : null;
  });
  new Chart(document.getElementById("corrBars"), {
    type: "bar",
    data: {
      labels: corrLabs,
      datasets: [
        {
          data: corrVals,
          backgroundColor: corrVals.map(function (v) {
            return v == null
              ? grey
              : v >= 0.4
                ? green
                : v <= -0.2
                  ? red
                  : navy;
          }),
          borderRadius: 4,
          barThickness: 18,
        },
      ],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: {
          min: -1,
          max: 1,
          grid: { color: grid },
          ticks: { color: ink },
          title: { display: true, text: "Pearson r (hover label in page for explainer)", color: ink },
        },
        y: {
          grid: { display: false },
          ticks: { color: ink, font: { size: 11 } },
        },
      },
    },
  });

  const th = [
    "Country",
    "DB",
    "IDS D%",
    "PMS gen%",
    "Genuine share%",
    "GPS EUR/UIO",
    "KPI fill%",
    "n dealers",
  ];
  document.querySelector("#joinTable thead").innerHTML =
    "<tr>" +
    th
      .map(function (t) {
        return "<th>" + t + "</th>";
      })
      .join("") +
    "</tr>";
  const sorted = rows.slice().sort(function (a, b) {
    return (a.ids_d_avg || 0) - (b.ids_d_avg || 0);
  });
  document.querySelector("#joinTable tbody").innerHTML = sorted
    .map(function (r) {
      function d(x, pct) {
        if (x == null || (typeof x === "number" && isNaN(x))) return "—";
        return pct ? (x * 100).toFixed(1) + "%" : (+x).toFixed(0);
      }
      return (
        "<tr><td><b>" +
        r.ids_country +
        "</b></td><td>" +
        r.prism_db +
        "</td><td>" +
        d(r.ids_d_avg, true) +
        "</td><td>" +
        d(r.pms_capture_genuine, true) +
        "</td><td>" +
        d(r.genuine_share_eur, true) +
        "</td><td>" +
        d(r.gps_spu_eur, false) +
        "</td><td>" +
        d(r.kpi_fill_rate, true) +
        "</td><td>" +
        (r.dealer_count || "—") +
        "</td></tr>"
      );
    })
    .join("");

  document.getElementById("dealers").innerHTML = focus
    .map(function (f, i) {
      const badge =
        f.ids_d_pct < 0.6 ? "red" : f.ids_d_pct < 0.75 ? "amber" : "green";
      const gaps = (f.gaps || []).filter(function (g) {
        return g.ref;
      });
      const lis = gaps
        .slice(0, 8)
        .map(function (g) {
          return (
            "<li><b>" +
            g.ref +
            "</b> — " +
            g.score +
            "/" +
            g.max +
            " (" +
            (g.pct * 100).toFixed(0) +
            "%) · " +
            g.text +
            "</li>"
          );
        })
        .join("");
      const ctx = f.db_context || {};
      return (
        '<div class="dealer-card"><h3>' +
        (i + 1) +
        ". " +
        f.name +
        ' <span class="muted">(' +
        f.country +
        ')</span> <span class="badge ' +
        badge +
        '">D ' +
        (f.ids_d_pct * 100).toFixed(0) +
        '%</span> <span class="badge amber">Total ' +
        (f.ids_total_pct * 100).toFixed(0) +
        "%</span></h3>" +
        '<p class="muted">DB context: PMS genuine ' +
        (ctx.pms_gen || "—") +
        " · Genuine share " +
        (ctx.gen_share || "—") +
        " · GPS EUR/UIO " +
        (ctx.gps || "—") +
        " · Fill " +
        (ctx.fill || "—") +
        "</p>" +
        "<p><b>Why (from Excel Section D):</b></p>" +
        '<ul class="gap-list">' +
        (lis || "<li>No question detail (check report)</li>") +
        "</ul>" +
        "<p><b>Suggested Kaizen:</b> " +
        (f.suggested_actions || "K1 / K2 / K3") +
        "</p></div>"
      );
    })
    .join("");
})();
