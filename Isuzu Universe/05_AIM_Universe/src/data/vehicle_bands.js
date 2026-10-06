/* ===========================================================================
   Vehicle bands (JS equivalent of prism/modules/vehicle_bands.py band_for).

   One authored map: 03_analytics/Isuzu/prism/data/series_to_band.csv.
   This module loads that CSV. It does not keep a second dictionary of series
   codes. Wildcard tokens with "*" are never converted into a band.
   =========================================================================== */
(function (root) {
  'use strict';

  var fs = null;
  var pathMod = null;
  try { fs = require('node:fs'); } catch (e) { fs = null; }
  try { pathMod = require('node:path'); } catch (e) { pathMod = null; }

  var UNRESOLVED = 'unresolved';
  var _map = null;
  var _mapPath = null;

  function defaultCsvPath() {
    if (!pathMod) return null;
    return pathMod.resolve(__dirname, '../../../../03_analytics/Isuzu/prism/data/series_to_band.csv');
  }

  function loadMap(csvPath) {
    if (!fs) {
      throw new Error('vehicle_bands.band_for needs Node fs to read series_to_band.csv');
    }
    var p = csvPath || _mapPath || defaultCsvPath();
    var text = fs.readFileSync(p, 'utf8');
    if (text.charCodeAt(0) === 0xFEFF) text = text.slice(1);
    var lines = text.split(/\r?\n/).filter(function (ln) { return ln.length; });
    if (!lines.length) return {};
    var headers = lines[0].split(',');
    var codeIdx = headers.indexOf('code');
    var bandIdx = headers.indexOf('tonnage_band');
    if (codeIdx < 0 || bandIdx < 0) {
      throw new Error('series_to_band.csv missing code or tonnage_band column');
    }
    var map = {};
    for (var i = 1; i < lines.length; i++) {
      var cols = lines[i].split(',');
      var code = (cols[codeIdx] || '').trim().toUpperCase();
      if (!code) continue;
      map[code] = {
        code: code,
        tonnage_band: (cols[bandIdx] || '').trim() || UNRESOLVED
      };
    }
    _map = map;
    _mapPath = p;
    return map;
  }

  function isWildcardToken(code) {
    return String(code || '').indexOf('*') >= 0;
  }

  function bandFor(code, csvPath) {
    if (isWildcardToken(code)) return UNRESOLVED;
    if (!_map || (csvPath && csvPath !== _mapPath)) loadMap(csvPath);
    if (!_map) loadMap(csvPath);
    var row = _map[String(code || '').trim().toUpperCase()];
    if (!row) return UNRESOLVED;
    return row.tonnage_band || UNRESOLVED;
  }

  function resetCache() { _map = null; _mapPath = null; }

  var API = {
    bandFor: bandFor,
    band_for: bandFor,
    isWildcardToken: isWildcardToken,
    loadMap: loadMap,
    resetCache: resetCache,
    UNRESOLVED: UNRESOLVED
  };

  root.AIMVehicleBands = API;
  if (typeof module === 'object' && module.exports) module.exports = API;
})(typeof globalThis !== 'undefined' ? globalThis : this);
