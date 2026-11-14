-- ============================================================
-- GeoForge PostgreSQL Schema for Supabase Free Tier
-- Matches the 14-column SQLite jobs table schema
-- ============================================================

CREATE TABLE IF NOT EXISTS jobs (
    job_id UUID PRIMARY KEY,
    filename TEXT NOT NULL,
    status TEXT NOT NULL,
    stage TEXT NOT NULL,
    progress_percent INTEGER NOT NULL DEFAULT 0,
    stage_message TEXT,
    video_path TEXT,
    job_dir TEXT,
    model_path TEXT,
    result_json JSONB,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at);

-- Optional Row-Level Security (RLS) for public read of completed jobs
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read access to completed jobs"
ON jobs FOR SELECT
USING (true);

CREATE POLICY "Allow service role full access"
ON jobs FOR ALL
USING (true);

