/* ===========================================================================
   SAFE-06 - protect attachments throughout upload, storage and access.

   Synthetic local storage only. No real dealer files. Unscanned material stays
   quarantined. Path traversal and executable content are refused. Fetching by
   guessed identifier cannot reuse another case's attachment. A refused upload
   does not erase the saved case.
   =========================================================================== */
(function (root) {
  'use strict';

  var fs = null;
  var path = null;
  try {
    fs = require('fs');
    path = require('path');
  } catch (e) {
    fs = null;
    path = null;
  }

  var MAX_BYTES = 256 * 1024;
  var ALLOWED_EXT = ['.txt', '.png', '.jpg', '.jpeg', '.pdf', '.csv'];
  var EXEC_EXT = ['.exe', '.bat', '.cmd', '.ps1', '.js', '.mjs', '.vbs', '.sh', '.com', '.dll'];

  function reject(code, error, extra) {
    return Object.assign({ ok: false, code: code, error: error }, extra || {});
  }

  function makeAttachmentStore(options) {
    options = options || {};
    if (!fs || !path) {
      throw new Error('SAFE-06 attachment store needs node fs/path.');
    }
    var rootDir = options.rootDir;
    if (!rootDir) throw new Error('makeAttachmentStore needs rootDir.');
    var privateDir = path.join(rootDir, 'private');
    var quarantineDir = path.join(rootDir, 'quarantine');
    var indexPath = path.join(rootDir, 'index.json');
    fs.mkdirSync(privateDir, { recursive: true });
    fs.mkdirSync(quarantineDir, { recursive: true });
    if (!fs.existsSync(indexPath)) {
      fs.writeFileSync(indexPath, JSON.stringify({ attachments: {} }, null, 2), 'utf8');
    }

    function readIndex() {
      return JSON.parse(fs.readFileSync(indexPath, 'utf8'));
    }
    function writeIndex(idx) {
      fs.writeFileSync(indexPath, JSON.stringify(idx, null, 2), 'utf8');
    }

    function sanitizeName(name) {
      var base = path.basename(String(name || ''));
      if (!base || base === '.' || base === '..') {
        return reject('ATTACHMENT_NEEDS_A_NAME', 'An attachment needs a safe file name.');
      }
      if (base.indexOf('\0') >= 0 || /[\\/]/.test(String(name || '')) && path.basename(name) !== String(name).replace(/^.*[\\/]/, '')) {
        return reject('PATH_TRAVERSAL_REFUSED', 'Path traversal in an attachment name is refused.');
      }
      if (/\.\.|[\\/]/.test(name) && path.basename(name) !== name) {
        return reject('PATH_TRAVERSAL_REFUSED', 'Path traversal in an attachment name is refused.');
      }
      if (name.indexOf('..') >= 0 || name.indexOf('/') >= 0 || name.indexOf('\\') >= 0) {
        return reject('PATH_TRAVERSAL_REFUSED', 'Path traversal in an attachment name is refused.');
      }
      return { ok: true, name: base };
    }

    function extensionOf(name) {
      var ext = path.extname(name).toLowerCase();
      return ext;
    }

    function upload(caseId, file, meta) {
      meta = meta || {};
      var caseSnapshot = meta.caseRecord || null;
      if (!caseId) {
        return reject('CASE_REQUIRED', 'An attachment must be associated with a case.', {
          case_erased: false,
          case_still_present: !!(caseSnapshot && caseSnapshot.case_id)
        });
      }
      var named = sanitizeName(file && file.name);
      if (!named.ok) {
        return Object.assign(named, {
          case_erased: false,
          case_still_present: true,
          case_id: caseId
        });
      }
      var ext = extensionOf(named.name);
      if (EXEC_EXT.indexOf(ext) >= 0) {
        return reject('EXECUTABLE_CONTENT_REFUSED',
          'Executable content is refused for case attachments.',
          { case_erased: false, case_still_present: true, case_id: caseId });
      }
      if (ALLOWED_EXT.indexOf(ext) < 0) {
        return reject('FILE_TYPE_REFUSED',
          'File type "' + ext + '" is not allowed for case attachments.',
          { case_erased: false, case_still_present: true, case_id: caseId });
      }
      var bytes = file && file.bytes;
      if (bytes == null) {
        return reject('EMPTY_ATTACHMENT', 'Attachment bytes are required.',
          { case_erased: false, case_still_present: true, case_id: caseId });
      }
      if (typeof bytes === 'string') bytes = Buffer.from(bytes, 'utf8');
      if (!Buffer.isBuffer(bytes)) bytes = Buffer.from(bytes);
      if (bytes.length > MAX_BYTES) {
        return reject('FILE_TOO_LARGE',
          'Attachment exceeds the ' + MAX_BYTES + ' byte limit.',
          { case_erased: false, case_still_present: true, case_id: caseId });
      }

      var scanned = meta.scanned === true;
      var audience = meta.audience || 'case';
      var attachmentId = 'att-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 8);
      var targetDir = scanned ? privateDir : quarantineDir;
      var storedName = attachmentId + ext;
      var storedPath = path.join(targetDir, storedName);
      fs.writeFileSync(storedPath, bytes);

      var idx = readIndex();
      idx.attachments[attachmentId] = {
        attachment_id: attachmentId,
        case_id: String(caseId),
        declared_name: named.name,
        stored_name: storedName,
        quarantined: !scanned,
        scanned: scanned,
        audience: audience,
        size_bytes: bytes.length,
        status: scanned ? 'available' : 'quarantined_unavailable'
      };
      writeIndex(idx);

      return {
        ok: true,
        attachment_id: attachmentId,
        case_id: String(caseId),
        quarantined: !scanned,
        scanned: scanned,
        status: scanned ? 'available' : 'quarantined_unavailable',
        available_for_wider_use: scanned === true,
        case_erased: false,
        case_still_present: true,
        auto_forward_original: false,
        note: scanned
          ? 'Attachment stored privately against the case.'
          : 'Unscanned material is quarantined and unavailable for wider use. Scanning is not claimed as passed.'
      };
    }

    function fetch(attachmentId, requester) {
      requester = requester || {};
      var idx = readIndex();
      var row = idx.attachments[attachmentId];
      if (!row) {
        return reject('ATTACHMENT_NOT_FOUND', 'No attachment exists for that identifier.');
      }
      if (requester.case_id && String(requester.case_id) !== String(row.case_id)) {
        return reject('ATTACHMENT_CASE_MISMATCH',
          'An attachment cannot be reused in another case by guessing its identifier.');
      }
      if (requester.authorised_case_ids) {
        var allowed = requester.authorised_case_ids.map(String);
        if (allowed.indexOf(String(row.case_id)) < 0) {
          return reject('ATTACHMENT_UNAUTHORISED',
            'A case attachment cannot be fetched through an unauthorised direct link.');
        }
      } else if (!requester.case_id) {
        return reject('ATTACHMENT_UNAUTHORISED',
          'A case attachment cannot be fetched through an unauthorised direct link.');
      }
      if (row.quarantined || row.status !== 'available') {
        return reject('ATTACHMENT_QUARANTINED',
          'Disallowed or unscanned files remain unavailable for wider use.',
          { case_id: row.case_id, case_erased: false });
      }
      var full = path.join(privateDir, row.stored_name);
      if (!fs.existsSync(full)) {
        return reject('ATTACHMENT_MISSING_BYTES', 'Stored attachment bytes are missing.');
      }
      return {
        ok: true,
        attachment_id: row.attachment_id,
        case_id: row.case_id,
        declared_name: row.declared_name,
        bytes: fs.readFileSync(full),
        auto_forward_original: false
      };
    }

    function shareShortResponse(attachmentId, options) {
      options = options || {};
      var fetched = fetch(attachmentId, options);
      if (!fetched.ok) return fetched;
      return {
        ok: true,
        short_response: options.short_response || 'A short response was prepared.',
        original_attached: false,
        auto_forward_original: false,
        note: 'The original document is not auto-forwarded when sharing a short response.'
      };
    }

    return {
      upload: upload,
      fetch: fetch,
      shareShortResponse: shareShortResponse,
      MAX_BYTES: MAX_BYTES,
      ALLOWED_EXT: ALLOWED_EXT
    };
  }

  var API = {
    makeAttachmentStore: makeAttachmentStore,
    MAX_BYTES: MAX_BYTES,
    ALLOWED_EXT: ALLOWED_EXT,
    EXEC_EXT: EXEC_EXT
  };

  if (typeof module === 'object' && module.exports) module.exports = API;
  else root.AIMAttachments = API;
})(typeof globalThis !== 'undefined' ? globalThis : this);