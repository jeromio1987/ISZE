/* ===========================================================================
   RUN-04 - Separate configuration, secrets and restricted working files.

   Keep real secrets out of code, tests, logs, exports and documentation.
   Use approved environment configuration and least-privilege source access.
   Fail closed on missing production settings. Synthetic development stays
   separate from actual participant data.

   No real secrets are created or read. Synthetic labels only.
   =========================================================================== */
(function (root) {
  'use strict';

  var CREDENTIAL_KEYS = [
    'password', 'api_key', 'apiKey', 'secret', 'token', 'access_token',
    'refresh_token', 'private_key', 'client_secret'
  ];
  var PRIVATE_TABLE_MARKERS = [
    'participant_private', 'dealer_personal', 'restricted_cost_table',
    'private_data_table'
  ];

  function deepClone(v) {
    return JSON.parse(JSON.stringify(v == null ? null : v));
  }

  function name(v) {
    if (v === undefined || v === null) return null;
    var s = String(v).trim();
    return s === '' ? null : s;
  }

  function looksLikeCredentialKey(key) {
    var k = String(key || '').toLowerCase();
    return CREDENTIAL_KEYS.some(function (c) {
      return k === c || k.indexOf(c) >= 0;
    });
  }

  function scanPackage(files) {
    files = Array.isArray(files) ? files : [];
    var findings = [];
    files.forEach(function (f) {
      var path = name(f.path) || 'unknown';
      var content = f.content == null ? '' : String(f.content);
      var lower = content.toLowerCase();

      CREDENTIAL_KEYS.forEach(function (ck) {
        var re = new RegExp('("?' + ck + '"?\\s*[:=]\\s*["\']?[^\\s"\']+)', 'i');
        if (re.test(content)) {
          findings.push({
            path: path,
            kind: 'credential',
            marker: ck,
            statement: 'Credential-shaped value found in package file.'
          });
        }
      });

      PRIVATE_TABLE_MARKERS.forEach(function (mk) {
        if (lower.indexOf(mk) >= 0) {
          findings.push({
            path: path,
            kind: 'private_data_table',
            marker: mk,
            statement: 'Private data table marker found in package file.'
          });
        }
      });
    });

    return {
      ok: findings.length === 0,
      clean: findings.length === 0,
      findings: findings,
      statement: findings.length === 0
        ? 'Clean code package contains no credentials or private data tables.'
        : 'Package scan found ' + findings.length + ' restricted item(s).'
    };
  }

  function scanDiagnosticLog(lines) {
    lines = Array.isArray(lines) ? lines : String(lines || '').split(/\r?\n/);
    var findings = [];
    lines.forEach(function (line, idx) {
      var text = String(line || '');
      var lower = text.toLowerCase();
      CREDENTIAL_KEYS.forEach(function (ck) {
        if (lower.indexOf(ck + '=') >= 0 || lower.indexOf(ck + ':') >= 0) {
          findings.push({
            line: idx + 1,
            kind: 'credential',
            marker: ck,
            statement: 'Credential-shaped value found in diagnostic log.'
          });
        }
      });
      PRIVATE_TABLE_MARKERS.forEach(function (mk) {
        if (lower.indexOf(mk) >= 0) {
          findings.push({
            line: idx + 1,
            kind: 'private_data_table',
            marker: mk,
            statement: 'Private data table marker found in diagnostic log.'
          });
        }
      });
    });
    return {
      ok: findings.length === 0,
      clean: findings.length === 0,
      findings: findings,
      statement: findings.length === 0
        ? 'Diagnostic log contains no credentials or private data tables.'
        : 'Diagnostic log scan found ' + findings.length + ' restricted item(s).'
    };
  }

  /* Fail closed: missing identity/storage config cannot start a live external service. */
  function startExternalService(config) {
    config = config || {};
    var mode = name(config.mode) || 'production';
    var identityConfigured = config.identity_configured === true;
    var storageConfigured = config.storage_configured === true;
    var development = mode === 'development' || config.development_only === true;

    if (mode === 'production' || mode === 'shared' || mode === 'live') {
      if (!identityConfigured || !storageConfigured) {
        return {
          ok: false,
          started: false,
          live_appearance: false,
          permissive_defaults: false,
          code: 'CONFIG_MISSING_FAIL_CLOSED',
          missing: [
            !identityConfigured ? 'identity' : null,
            !storageConfigured ? 'storage' : null
          ].filter(Boolean),
          statement: 'Missing identity/storage configuration cannot start a seemingly live external service. Fail closed.'
        };
      }
    }

    if (development) {
      return {
        ok: true,
        started: true,
        live_appearance: false,
        permissive_defaults: false,
        development_only: true,
        synthetic: true,
        statement: 'Development service started. Explicitly not live; synthetic only.'
      };
    }

    return {
      ok: true,
      started: true,
      live_appearance: true,
      permissive_defaults: false,
      development_only: false,
      statement: 'External service started with approved identity and storage configuration.'
    };
  }

  function loadConfig(env) {
    env = env || {};
    var secrets = {};
    var publicConfig = {};
    Object.keys(env).forEach(function (k) {
      if (looksLikeCredentialKey(k)) {
        /* Never copy secret values into returned public config or logs. */
        secrets[k] = '[redacted]';
      } else {
        publicConfig[k] = env[k];
      }
    });
    return {
      ok: true,
      public_config: publicConfig,
      secret_keys_present: Object.keys(secrets),
      secrets_redacted: true,
      statement: 'Configuration loaded with secrets separated and redacted.'
    };
  }

  var API = {
    CREDENTIAL_KEYS: CREDENTIAL_KEYS.slice(),
    PRIVATE_TABLE_MARKERS: PRIVATE_TABLE_MARKERS.slice(),
    scanPackage: scanPackage,
    scanDiagnosticLog: scanDiagnosticLog,
    startExternalService: startExternalService,
    loadConfig: loadConfig
  };

  root.AIMConfigSecrets = API;
  if (typeof module === 'object' && module.exports) module.exports = API;
}(typeof globalThis !== 'undefined' ? globalThis : (typeof window !== 'undefined' ? window : this)));
