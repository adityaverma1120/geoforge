"""
export_sqlite_to_supabase.py — Export local GeoForge SQLite records to Supabase PostgreSQL

Reads records from backend/jobs.db and generates SQL INSERT statements suitable for
pasting into Supabase SQL Editor.
"""

import sqlite3
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "backend" / "jobs.db"
OUTPUT_SQL = ROOT_DIR / "backend" / "supabase_seed_data.sql"

if not DB_PATH.exists():
    print(f"Error: Database not found at {DB_PATH}")
    exit(1)

conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT * FROM jobs ORDER BY created_at ASC")
rows = cur.fetchall()

sql_lines = [
    "-- ============================================================",
    "-- GeoForge Historical Jobs Seed Data for Supabase",
    "-- Generated from backend/jobs.db",
    "-- ============================================================\n"
]

for r in rows:
    job_id = r["job_id"]
    filename = r["filename"].replace("'", "''")
    status = r["status"]
    stage = r["stage"]
    progress = r["progress_percent"]
    stage_msg = (r["stage_message"] or "").replace("'", "''")
    video_path = (r["video_path"] or "").replace("'", "''")
    job_dir = (r["job_dir"] or "").replace("'", "''")
    model_path = (r["model_path"] or "").replace("'", "''")
    result_json = r["result_json"]
    if result_json:
        result_escaped = "'" + result_json.replace("'", "''") + "'::jsonb"
    else:
        result_escaped = "NULL"
    error_msg = ("'" + r["error_message"].replace("'", "''") + "'") if r["error_message"] else "NULL"
    created_at = r["created_at"]
    updated_at = r["updated_at"]
    completed_at = ("'" + r["completed_at"] + "'") if r["completed_at"] else "NULL"

    stmt = f"""INSERT INTO jobs (
    job_id, filename, status, stage, progress_percent, stage_message,
    video_path, job_dir, model_path, result_json, error_message,
    created_at, updated_at, completed_at
) VALUES (
    '{job_id}', '{filename}', '{status}', '{stage}', {progress}, '{stage_msg}',
    '{video_path}', '{job_dir}', '{model_path}', {result_escaped}, {error_msg},
    '{created_at}', '{updated_at}', {completed_at}
) ON CONFLICT (job_id) DO NOTHING;"""
    sql_lines.append(stmt)

with open(OUTPUT_SQL, "w", encoding="utf-8") as f:
    f.write("\n".join(sql_lines) + "\n")

print(f"Successfully exported {len(rows)} job records to: {OUTPUT_SQL}")
