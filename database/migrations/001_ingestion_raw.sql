-- Ingestion landing zone for raw integration payloads
-- Safe to run multiple times (IF NOT EXISTS)

CREATE TABLE IF NOT EXISTS ingestion_raw (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_system TEXT NOT NULL,
  object_type TEXT,
  external_id TEXT,
  payload JSONB NOT NULL,
  checksum TEXT,
  ingested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  sync_run_id UUID
);

-- Uniqueness on (source_system, external_id, checksum) prevents duplicate writes
CREATE UNIQUE INDEX IF NOT EXISTS ux_ingestion_raw_src_ext_ck
  ON ingestion_raw (source_system, external_id, checksum);

-- Sync runs for tracking sync operations
CREATE TABLE IF NOT EXISTS sync_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_system TEXT NOT NULL,
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ,
  status TEXT DEFAULT 'running',
  stats JSONB DEFAULT '{}'::jsonb,
  error TEXT
);

