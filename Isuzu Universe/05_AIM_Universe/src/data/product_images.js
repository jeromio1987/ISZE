/* ===========================================================================
   RANGE-07 - Use authentic, permitted product images with a clear fallback.

   Small image reference index: approved existing assets, part associations and
   usage/source information. Reuse genuine product imagery only when permission
   is already recorded. Otherwise show a neutral no-image state. Do not invent
   a product image or infer fitment from a picture. Do not download images.

   Synthetic permission records only. No image files are fetched.
   =========================================================================== */
(function (root) {
  'use strict';

  function deepClone(v) {
    return JSON.parse(JSON.stringify(v == null ? null : v));
  }
  function name(v) {
    if (v === undefined || v === null) return null;
    var s = String(v).trim();
    return s === '' ? null : s;
  }

  function makeImageIndex(entries) {
    entries = Array.isArray(entries) ? entries : [];
    var byId = Object.create(null);
    var byPart = Object.create(null);

    entries.forEach(function (raw) {
      var e = deepClone(raw || {});
      var id = name(e.image_id);
      var part = name(e.part_number);
      var permission = name(e.permission_record);
      if (!id || !part || !permission) return;
      e.image_id = id;
      e.part_number = part;
      e.permission_record = permission;
      e.source = name(e.source) || name(e.reference) || null;
      e.permitted = true;
      byId[id] = e;
      if (!byPart[part]) byPart[part] = [];
      byPart[part].push(id);
    });

    function fallback(partNumber, reason) {
      return {
        ok: true,
        has_image: false,
        fallback: true,
        part_number: name(partNumber),
        image_id: null,
        source: null,
        permission_record: null,
        identification_intact: true,
        case_workflow_intact: true,
        reason: name(reason) || 'No permitted product image is recorded for this part.',
        statement: 'Neutral no-image state. Identification and the case workflow continue.'
      };
    }

    function resolveForPart(partNumber) {
      var part = name(partNumber);
      if (!part) {
        return {
          ok: false,
          code: 'PART_REQUIRED',
          has_image: false,
          fallback: true,
          identification_intact: true,
          case_workflow_intact: true,
          error: 'A part number is required to resolve an image.'
        };
      }
      var ids = byPart[part] || [];
      if (!ids.length) return fallback(part, 'No permitted product image is recorded for this part.');
      var img = byId[ids[0]];
      return {
        ok: true,
        has_image: true,
        fallback: false,
        part_number: part,
        image_id: img.image_id,
        source: img.source,
        permission_record: img.permission_record,
        identification_intact: true,
        case_workflow_intact: true,
        statement: 'Permitted product image resolved from recorded permission.'
      };
    }

    /* An image cannot silently be copied to a different part. */
    function associateImage(imageId, targetPart) {
      var id = name(imageId);
      var part = name(targetPart);
      var img = id ? byId[id] : null;
      if (!img) {
        return { ok: false, code: 'IMAGE_UNKNOWN', error: 'Unknown image_id.' };
      }
      if (!part) {
        return { ok: false, code: 'PART_REQUIRED', error: 'Target part required.' };
      }
      if (img.part_number !== part) {
        return {
          ok: false,
          code: 'CROSS_PART_COPY_REFUSED',
          image_id: id,
          recorded_part: img.part_number,
          requested_part: part,
          source: img.source,
          statement: 'An image points to its known source/reference and cannot silently be copied to a different part.'
        };
      }
      return {
        ok: true,
        image_id: id,
        part_number: part,
        source: img.source,
        permission_record: img.permission_record
      };
    }

    function caseIdentification(partNumber) {
      var resolved = resolveForPart(partNumber);
      return {
        ok: true,
        part_number: name(partNumber),
        image: resolved,
        identification_broken: false,
        case_workflow_broken: false,
        statement: resolved.has_image
          ? 'Part identified with permitted image.'
          : 'Part identified with no-image fallback; workflow continues.'
      };
    }

    return {
      resolveForPart: resolveForPart,
      associateImage: associateImage,
      caseIdentification: caseIdentification,
      fallback: fallback,
      permittedCount: function () { return Object.keys(byId).length; },
      list: function () { return deepClone(Object.keys(byId).map(function (k) { return byId[k]; })); }
    };
  }

  var API = { makeImageIndex: makeImageIndex };
  root.AIMProductImages = API;
  if (typeof module === 'object' && module.exports) module.exports = API;
}(typeof globalThis !== 'undefined' ? globalThis : (typeof window !== 'undefined' ? window : this)));
