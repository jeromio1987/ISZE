-- RUN-01 migration 001: durable case rows for the shared local backend.
-- Synthetic development only. One JSON blob per case (same shape as store.js).

CREATE TABLE IF NOT EXISTS schema_migrations (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cases (
  case_id TEXT PRIMARY KEY NOT NULL,
  record_json TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
