/* ISZE Editorial chart palette — patches Plotly + Chart.js when body.isze-editorial */
(function () {
  'use strict';

  var SEM = {
    paper: '#F6F3EE',
    plot: '#FFFFFF',
    grid: '#E7E0D8',
    text: '#78716C',
    ink: '#1C1917',
    revenue: 'rgba(204, 14, 30, 0.82)',
    gp: 'rgba(61, 107, 79, 0.75)',
    accent: '#B8956B',
    slate: 'rgba(122, 143, 166, 0.82)',
    warm: '#9A6B4A',
    tan: '#C4A99A',
    warning: 'rgba(196, 165, 116, 0.85)',
    line: '#9A6B4A'
  };

  var PALETTE = [
    '#CC0E1E', '#3D6B4F', '#B8956B', '#7A8FA6', '#9A6B4A',
    '#5C7A6E', '#C4A99A', '#1C1917', '#A84855', '#6B8F7A'
  ];

  var PIE_SEQ = ['#3D6B4F', '#5C7A6E', '#C4A574', '#CC0E1E', '#7A8FA6', '#B8956B'];
  var RISK_SEQ = ['#C4A574', '#CC0E1E', '#3D6B4F'];

  window.ISZE_EDITORIAL_CHARTS = { SEM: SEM, PALETTE: PALETTE };

  function norm(c) {
    return String(c || '').toLowerCase().replace(/\s/g, '');
  }

  function remapColor(c, i) {
    if (!c || c === 'transparent') return c;
    var s = norm(c);
    if (/2e7d32|46,125,50|27ae60|3fb950|0a7a40|558b2f|1b5e20|34a853/.test(s)) return SEM.gp;
    if (/1565c0|21,101,192|2980b9|1a237e|4a148c|006064|0d1a30|30,100,180|4472c4/.test(s)) return SEM.slate;
    if (/cc0e1e|c8102e|9a0b16|200,16,46|204,14,30|e74c3c|c0392b|b71c1c|f85149|9a0b17/.test(s)) return SEM.revenue;
    if (/e65100|f39c12|f57f17|e3b341|c07000|ff9800/.test(s)) return SEM.warning;
    if (/85929e|64748b|5a5a5a|37474f|888|999|aaa|b0b0b0/.test(s)) return SEM.tan;
    if (s === '#ffffff' || s === 'white') return SEM.plot;
    if (typeof i === 'number') return PALETTE[i % PALETTE.length];
    return c;
  }

  function remapColors(arr, pieHint) {
    if (!Array.isArray(arr)) return remapColor(arr);
    if (pieHint && arr.length <= 6) {
      var seq = arr.length === 3 ? RISK_SEQ : PIE_SEQ;
      return arr.map(function (_, idx) { return seq[idx % seq.length]; });
    }
    return arr.map(function (c, idx) { return remapColor(c, idx); });
  }

  function remapTrace(trace, idx) {
    if (!trace || typeof trace !== 'object') return trace;
    var t = Object.assign({}, trace);
    if (t.marker) {
      t.marker = Object.assign({}, t.marker);
      if (t.marker.color !== undefined) {
        t.marker.color = Array.isArray(t.marker.color)
          ? remapColors(t.marker.color, t.type === 'pie')
          : remapColor(t.marker.color, idx);
      }
    }
    if (t.line) {
      t.line = Object.assign({}, t.line);
      if (t.line.color) t.line.color = remapColor(t.line.color, idx);
    }
    if (t.fillcolor) t.fillcolor = remapColor(t.fillcolor, idx);
    if (t.type === 'pie' && t.marker && Array.isArray(t.marker.colors)) {
      t.marker.colors = remapColors(t.marker.colors, true);
    }
    return t;
  }

  function axisDefaults(ax) {
    if (!ax) return { gridcolor: SEM.grid, tickfont: { color: SEM.text, size: 10 }, titlefont: { color: SEM.ink } };
    return Object.assign({
      gridcolor: SEM.grid,
      tickfont: Object.assign({ color: SEM.text, size: 10 }, ax.tickfont || {}),
      titlefont: Object.assign({ color: SEM.ink }, ax.titlefont || {}),
      zerolinecolor: SEM.grid
    }, ax);
  }

  function editorialLayout(layout) {
    var base = {
      paper_bgcolor: SEM.paper,
      plot_bgcolor: SEM.plot,
      font: { family: 'Inter, system-ui, sans-serif', color: SEM.text, size: 11 },
      colorway: PALETTE
    };
    var L = Object.assign({}, base, layout || {});
    ['xaxis', 'yaxis', 'xaxis2', 'yaxis2'].forEach(function (k) {
      if (L[k]) L[k] = axisDefaults(L[k]);
    });
    if (L.legend && L.legend.font) {
      L.legend.font = Object.assign({ color: SEM.text }, L.legend.font);
    } else if (L.legend) {
      L.legend.font = { color: SEM.text };
    }
    return L;
  }

  function patchPlotly() {
    if (!window.Plotly || window.Plotly.__iszeEditorial) return;
    var orig = Plotly.newPlot;
    Plotly.newPlot = function (el, data, layout, config) {
      data = (data || []).map(function (tr, i) { return remapTrace(tr, i); });
      layout = editorialLayout(layout);
      return orig.call(this, el, data, layout, config);
    };
    if (Plotly.react) {
      var origReact = Plotly.react;
      Plotly.react = function (el, data, layout, config) {
        data = (data || []).map(function (tr, i) { return remapTrace(tr, i); });
        layout = editorialLayout(layout);
        return origReact.call(this, el, data, layout, config);
      };
    }
    Plotly.__iszeEditorial = true;
  }

  function remapChartDataset(ds, idx) {
    if (!ds) return ds;
    var d = Object.assign({}, ds);
    if (d.backgroundColor !== undefined) {
      d.backgroundColor = Array.isArray(d.backgroundColor)
        ? remapColors(d.backgroundColor)
        : remapColor(d.backgroundColor, idx);
    }
    if (d.borderColor !== undefined) {
      d.borderColor = Array.isArray(d.borderColor)
        ? remapColors(d.borderColor)
        : remapColor(d.borderColor, idx);
    }
    if (d.pointBackgroundColor !== undefined) {
      d.pointBackgroundColor = Array.isArray(d.pointBackgroundColor)
        ? remapColors(d.pointBackgroundColor)
        : remapColor(d.pointBackgroundColor, idx);
    }
    if (d.borderColor === undefined && d.type === 'line') {
      d.borderColor = remapColor(d.borderColor || SEM.line, idx);
    }
    return d;
  }

  function remapChartOptions(opts) {
    if (!opts) return opts;
    var o = Object.assign({}, opts);
    o.scales = o.scales || {};
    ['x', 'y', 'x2', 'y2'].forEach(function (k) {
      if (o.scales[k]) {
        o.scales[k] = Object.assign({}, o.scales[k]);
        o.scales[k].grid = Object.assign({ color: SEM.grid }, o.scales[k].grid || {});
        o.scales[k].ticks = Object.assign({ color: SEM.text }, o.scales[k].ticks || {});
      }
    });
    if (o.plugins && o.plugins.legend && o.plugins.legend.labels) {
      o.plugins.legend.labels = Object.assign({ color: SEM.text }, o.plugins.legend.labels);
    }
    return o;
  }

  function patchChart() {
    if (!window.Chart || window.Chart.__iszeEditorial) return;
    var Orig = window.Chart;
    var wrapped = function (ctx, config) {
      if (config) {
        config = Object.assign({}, config);
        if (config.data && config.data.datasets) {
          config.data = Object.assign({}, config.data);
          config.data.datasets = config.data.datasets.map(function (ds, i) {
            return remapChartDataset(ds, i);
          });
        }
        if (config.options) config.options = remapChartOptions(config.options);
      }
      return new Orig(ctx, config);
    };
    Object.keys(Orig).forEach(function (k) { wrapped[k] = Orig[k]; });
    wrapped.prototype = Orig.prototype;
    wrapped.__iszeEditorial = true;
    window.Chart = wrapped;

    if (Orig.defaults) {
      Orig.defaults.color = SEM.text;
      Orig.defaults.borderColor = SEM.grid;
      Orig.defaults.font = Object.assign({}, Orig.defaults.font || {}, { family: 'Inter, system-ui, sans-serif' });
      if (Orig.defaults.plugins && Orig.defaults.plugins.legend) {
        Orig.defaults.plugins.legend.labels = Object.assign(
          {}, Orig.defaults.plugins.legend.labels || {}, { color: SEM.text }
        );
      }
    }
  }

  function ensure() {
    patchPlotly();
    patchChart();
  }

  ensure();
  document.addEventListener('DOMContentLoaded', ensure, true);
  var n = 0;
  var poll = setInterval(function () {
    ensure();
    if ((window.Plotly && window.Plotly.__iszeEditorial) && (!window.Chart || window.Chart.__iszeEditorial)) {
      clearInterval(poll);
    }
    if (++n > 400) clearInterval(poll);
  }, 25);
})();
