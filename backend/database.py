"""
database.py — Persistent SQLite Job Management for GeoForge

Stores reconstruction job lifecycle state, stage progression, diagnostics,
and output metadata persistently so completed jobs survive backend restarts.
"""

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("geoforge.database")

DB_PATH = Path(__file__).resolve().parent / "jobs.db"


def get_connection() -> sqlite3.Connection:
    """Create a thread-safe connection to the SQLite database."""
    conn = sqlite3.connect(str(DB_PATH), timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize the jobs table if it does not already exist."""
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    status TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    progress_percent INTEGER NOT NULL DEFAULT 0,
                    stage_message TEXT,
                    video_path TEXT,
                    job_dir TEXT,
                    model_path TEXT,
                    result_json TEXT,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    completed_at TEXT
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at)"
            )
            # Automatic schema migration for existing databases
            try:
                conn.execute("ALTER TABLE jobs ADD COLUMN completed_at TEXT")
            except Exception:
                pass
        logger.info(f"Persistent SQLite job database initialized at {DB_PATH}")
    finally:
        conn.close()


def check_db_connectivity() -> bool:
    """Check whether the persistent SQLite database is accessible and responsive."""
    try:
        conn = get_connection()
        cursor = conn.execute("SELECT 1")
        row = cursor.fetchone()
        conn.close()
        return bool(row and row[0] == 1)
    except Exception as e:
        logger.error(f"Database connectivity check failed: {e}")
        return False


def create_job(
    job_id: str,
    filename: str,
    video_path: Path,
    job_dir: Path
) -> Dict[str, Any]:
    """Register a new job in the persistent database."""
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO jobs (
                    job_id, filename, status, stage, progress_percent,
                    stage_message, video_path, job_dir, model_path,
                    result_json, error_message, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    filename,
                    "queued",
                    "queued",
                    0,
                    "Job queued for reconstruction",
                    str(video_path),
                    str(job_dir),
                    None,
                    None,
                    None,
                    now,
                    now
                )
            )
        return get_job(job_id) or {}
    finally:
        conn.close()


def update_job_progress(
    job_id: str,
    status: Optional[str] = None,
    stage: Optional[str] = None,
    progress_percent: Optional[int] = None,
    stage_message: Optional[str] = None,
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
    model_path: Optional[Path] = None
) -> None:
    """Update progress, stage, or terminal status of an active job."""
    now = datetime.now(timezone.utc).isoformat()
    fields = ["updated_at = ?"]
    params: List[Any] = [now]

    if status is not None:
        fields.append("status = ?")
        params.append(status)
        if str(status).lower() in ("complete", "completed", "failed", "cancelled"):
            fields.append("completed_at = ?")
            params.append(now)
    if stage is not None:
        fields.append("stage = ?")
        params.append(stage)
    if progress_percent is not None:
        fields.append("progress_percent = ?")
        params.append(int(progress_percent))
    if stage_message is not None:
        fields.append("stage_message = ?")
        params.append(stage_message)
    if result is not None:
        fields.append("result_json = ?")
        params.append(json.dumps(result))
    if error is not None:
        fields.append("error_message = ?")
        params.append(error)
    if model_path is not None:
        fields.append("model_path = ?")
        params.append(str(model_path))

    params.append(job_id)
    query = f"UPDATE jobs SET {', '.join(fields)} WHERE job_id = ?"

    conn = get_connection()
    try:
        with conn:
            conn.execute(query, params)
    finally:
        conn.close()


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve full job metadata by job ID."""
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
        row = cursor.fetchone()
        if not row:
            return None
        data = dict(row)
        jid = data.get("job_id") or data.get("id")
        data["id"] = jid
        data["job_id"] = jid
        if data.get("result_json"):
            try:
                data["result"] = json.loads(data["result_json"])
            except Exception:
                data["result"] = None
        else:
            data["result"] = None
        return data
    finally:
        conn.close()


def list_jobs(limit: int = 50) -> List[Dict[str, Any]]:
    """List recent jobs ordered by creation date."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        rows = cursor.fetchall()
        jobs = []
        for r in rows:
            d = dict(r)
            # Ensure both 'id' and 'job_id' are present for frontend compatibility
            jid = d.get("job_id") or d.get("id")
            d["id"] = jid
            d["job_id"] = jid
            if d.get("result_json"):
                try:
                    d["result"] = json.loads(d["result_json"])
                except Exception:
                    d["result"] = None
            jobs.append(d)
        return jobs
    finally:
        conn.close()


def delete_job(job_id: str) -> bool:
    """Delete a job record from the database."""
    conn = get_connection()
    try:
        with conn:
            cursor = conn.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
            return cursor.rowcount > 0
    finally:
        conn.close()


def cancel_job(job_id: str) -> bool:
    """Cancel a queued or active job."""
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    try:
        with conn:
            cursor = conn.execute(
                """
                UPDATE jobs
                SET status = 'cancelled',
                    stage = 'cancelled',
                    stage_message = 'Job was cancelled by user request.',
                    updated_at = ?,
                    completed_at = ?
                WHERE job_id = ? AND status IN ('uploaded', 'queued', 'processing')
                """,
                (now, now, job_id)
            )
            return cursor.rowcount > 0
    finally:
        conn.close()


def recover_interrupted_jobs() -> int:
    """
    Mark any jobs left in 'processing' or 'queued' state at backend startup as failed,
    informing the user that execution was interrupted by a server restart.
    """
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    try:
        with conn:
            cursor = conn.execute(
                """
                UPDATE jobs
                SET status = 'failed',
                    error_message = 'Reconstruction was interrupted by a server restart. Please upload again.',
                    stage_message = 'Interrupted by server restart',
                    updated_at = ?
                WHERE status IN ('processing', 'queued')
                """,
                (now,)
            )
            recovered = cursor.rowcount
            if recovered > 0:
                logger.warning(f"Flagged {recovered} interrupted job(s) as failed on startup.")
            return recovered
    finally:
        conn.close()

