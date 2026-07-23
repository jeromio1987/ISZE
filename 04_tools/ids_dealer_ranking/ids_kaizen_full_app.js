(function () {
  const ink = "#52514e",
    grid = "#e1e0d9",
    navy = "#2a78d6",
    terra = "#c0552d",
    grey = "#888780",
    red = "#e24b4a",
    green = "#1d9e75",
    amber = "#eda100";

  const focus = DATA.focus_dealers || [];
  const matrix = DATA.country_matrix || [];
  const flags = DATA.country_flags || [];
  const labels = DATA.section_labels || {};
  const network = DATA.network_sections || {};
  const sections = ["A", "B", "C", "D", "E"];

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
  const TIP_WAVE =
    "Wave / selection = who enters Kaizen now. In this full IDS pack: the 3 lowest total scores per country (fewer if the market is smaller). It is a call list for 90-day CAP work — not a permanent blacklist. Wave-1 in the Parts study was a smaller pilot (4 dealers); this pack is the country-wide roll-out list.";

  document.getElementById("howto").innerHTML =
    "<b>" +
    tip("Wave / selection", TIP_WAVE) +
    ":</b> for each IDS country we take the <b>3 lowest total scores</b> (fewer if the market is smaller). " +
    "That is the Kaizen call list — not a punishment league. " +
    "Excel gaps tell you <i>what</i> to fix (question refs). " +
    "The country×section matrix is the side quest: where a whole market is soft on A–E vs the network, ask the distributor why.";

  document.getElementById("stats").innerHTML = [
    ["Countries", (DATA.countries || []).length],
    ["Kaizen dealers", focus.length],
    ["Per country", DATA.dealers_per_country || 3],
    ["Section flags", flags.length],
  ]
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

  function pct(v) {
    if (v == null || (typeof v === "number" && isNaN(v))) return "—";
    return (v * 100).toFixed(0) + "%";
  }
  function hmColor(v) {
    if (v == null) return grey;
    if (v >= 0.85) return green;
    if (v >= 0.75) return navy;
    if (v >= 0.65) return amber;
    return red;
  }

  // Country ranking bars
  const ranked = matrix.slice().sort(function (a, b) {
    return (a.total_pct || 0) - (b.total_pct || 0);
  });
  new Chart(document.getElementById("countryRank"), {
    type: "bar",
    data: {
      labels: ranked.map(function (r) {
        return r.country;
      }),
      datasets: [
        {
          data: ranked.map(function (r) {
            return r.total_pct == null ? null : +(r.total_pct * 100).toFixed(1);
          }),
          backgroundColor: ranked.map(function (r, i) {
            return i < 4 ? terra : navy;
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
          min: 50,
          max: 100,
          grid: { color: grid },
          ticks: { color: ink },
          title: { display: true, text: "IDS total %", color: ink },
        },
        y: { grid: { display: false }, ticks: { color: ink } },
      },
    },
  });

  // Grouped section bars: network + 3 weakest countries by total
  const weakCountries = ranked.slice(0, 3).map(function (r) {
    return r.country;
  });
  const datasets = [
    {
      label: "Network",
      data: sections.map(function (s) {
        return network[s] == null ? null : +(network[s] * 100).toFixed(1);
      }),
      backgroundColor: grey,
      borderRadius: 3,
      barThickness: 14,
    },
  ];
  const colors = [terra, navy, amber];
  weakCountries.forEach(function (c, i) {
    const row = matrix.find(function (r) {
      return r.country === c;
    });
    datasets.push({
      label: c,
      data: sections.map(function (s) {
        const v = row && row.sections ? row.sections[s] : null;
        return v == null ? null : +(v * 100).toFixed(1);
      }),
      backgroundColor: colors[i],
      borderRadius: 3,
      barThickness: 14,
    });
  });
  new Chart(document.getElementById("sectionRadar"), {
    type: "bar",
    data: {
      labels: sections.map(function (s) {
        return labels[s] || s;
      }),
      datasets: datasets,
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "bottom", labels: { color: ink } } },
      scales: {
        y: {
          min: 40,
          max: 100,
          grid: { color: grid },
          ticks: { color: ink },
          title: { display: true, text: "%", color: ink },
        },
        x: { grid: { display: false }, ticks: { color: ink } },
      },
    },
  });

  // Matrix table
  document.querySelector("#matrixTable thead").innerHTML =
    "<tr><th>Country</th><th>n</th><th>Total</th>" +
    sections
      .map(function (s) {
        return "<th>" + s + "</th>";
      })
      .join("") +
    "<th>Weakest</th></tr>";
  document.querySelector("#matrixTable tbody").innerHTML = ranked
    .map(function (r) {
      const cells = sections
        .map(function (s) {
          const v = r.sections[s];
          return (
            '<td><span class="hm" style="background:' +
            hmColor(v) +
            '">' +
            pct(v) +
            "</span></td>"
          );
        })
        .join("");
      return (
        "<tr><td><b>" +
        r.country +
        "</b></td><td>" +
        (r.dealer_count || "—") +
        "</td><td>" +
        pct(r.total_pct) +
        "</td>" +
        cells +
        "<td>" +
        (r.weakest_section || "—") +
        "</td></tr>"
      );
    })
    .join("");

  document.getElementById("askList").innerHTML = flags.length
    ? flags
        .map(function (f) {
          return (
            "<li><b>" +
            f.country +
            "</b> · " +
            f.section_label +
            " (" +
            pct(f.country_pct) +
            ", " +
            f.vs_network_pp.toFixed(1) +
            " pp vs network) — <i>" +
            f.ask +
            "</i></li>"
          );
        })
        .join("")
    : "<li class='muted'>No section more than 8 pp below network.</li>";

  // Dealers grouped by country
  const byC = {};
  focus.forEach(function (f) {
    (byC[f.country] = byC[f.country] || []).push(f);
  });
  document.getElementById("dealers").innerHTML = Object.keys(byC)
    .sort()
    .map(function (country) {
      const cards = byC[country]
        .map(function (f) {
          const gaps = (f.gaps || []).filter(function (g) {
            return g.ref;
          });
          const lis = gaps
            .slice(0, 6)
            .map(function (g) {
              return (
                "<li><b>" +
                g.ref +
                "</b> (" +
                g.score +
                "/" +
                g.max +
                ") — " +
                g.text +
                "</li>"
              );
            })
            .join("");
          const qlis = (f.db_questions || [])
            .map(function (q) {
              return (
                "<li><span class='badge'>" +
                (q.theme || "") +
                "</span> " +
                q.question +
                "</li>"
              );
            })
            .join("");
          const note = f.totals_only
            ? "<p class='muted'>Totals only — no Excel question breakdown.</p>"
            : "";
          const rankBits = [];
          if (f.ids_country_rank_total != null)
            rankBits.push("IDS country rank " + f.ids_country_rank_total);
          if (f.ids_global_rank != null)
            rankBits.push("global " + f.ids_global_rank);
          if (f.b1_country_rank != null)
            rankBits.push(
              "B.1 rank " +
                f.b1_country_rank +
                (f.b1_pct != null ? " (" + pct(f.b1_pct) + ")" : "")
            );
          return (
            '<div class="dealer-card"><h3>#' +
            f.rank_in_country +
            " " +
            f.name +
            ' <span class="badge">Total ' +
            pct(f.ids_total_pct) +
            "</span> " +
            (f.weakest_section
              ? '<span class="badge">Weak ' +
                f.weakest_section +
                " " +
                pct(f.weakest_section_pct) +
                "</span>"
              : "") +
            "</h3>" +
            "<p class='muted'>vs country avg " +
            (f.vs_country_pp == null
              ? "—"
              : f.vs_country_pp.toFixed(1) + " pp") +
            (rankBits.length ? " · " + rankBits.join(" · ") : "") +
            "</p>" +
            note +
            (lis
              ? "<p><b>Excel gaps:</b></p><ul class='gap-list'>" +
                lis +
                "</ul>"
              : "") +
            "<p><b>Kaizen focus:</b> " +
            (f.suggested || "—") +
            "</p>" +
            (qlis
              ? "<p><b>Ask the DB:</b></p><ul class='gap-list'>" +
                qlis +
                "</ul>"
              : "") +
            "</div>"
          );
        })
        .join("");
      return (
        '<div class="country-block"><h3>' +
        country +
        "</h3>" +
        cards +
        "</div>"
      );
    })
    .join("");
})();
