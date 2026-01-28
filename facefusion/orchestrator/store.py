"""
SQLite-based Job Store
----------------------
Persistent storage for jobs with schema versioning and migrations.
"""
import os
import json
import sqlite3
import threading
from typing import Optional, List
from contextlib import contextmanager

from facefusion.orchestrator.models import Job, JobStatus


# Schema version for migrations
SCHEMA_VERSION = 1


class JobStore:
    """Thread-safe SQLite store for jobs."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._local = threading.local()
        self._lock = threading.RLock()
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path) or '.', exist_ok=True)
        
        # Initialize schema
        self._init_schema()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            self._local.conn.row_factory = sqlite3.Row
            # Enable foreign keys and WAL mode for better concurrency
            self._local.conn.execute("PRAGMA foreign_keys = ON")
            self._local.conn.execute("PRAGMA journal_mode = WAL")
        return self._local.conn
    
    @contextmanager
    def _transaction(self):
        """Context manager for database transactions."""
        conn = self._get_connection()
        with self._lock:
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
    
    def _init_schema(self) -> None:
        """Initialize database schema with versioning."""
        with self._transaction() as conn:
            # Check if schema_version table exists
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='schema_version'
            """)
            
            if cursor.fetchone() is None:
                # Fresh database - create all tables
                self._create_tables(conn)
            else:
                # Check version and migrate if needed
                cursor = conn.execute("SELECT version FROM schema_version")
                row = cursor.fetchone()
                current_version = row['version'] if row else 0
                
                if current_version < SCHEMA_VERSION:
                    self._migrate(conn, current_version, SCHEMA_VERSION)
    
    def _create_tables(self, conn: sqlite3.Connection) -> None:
        """Create all database tables."""
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY
            );
            
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'drafted',
                progress REAL DEFAULT 0.0,
                cancel_requested INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                error_code TEXT,
                error_message TEXT,
                config_json TEXT,
                steps_json TEXT,
                metadata_json TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
            CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at);
        """)
        
        conn.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
    
    def _migrate(self, conn: sqlite3.Connection, from_version: int, to_version: int) -> None:
        """Run schema migrations."""
        # Add migration steps here as schema evolves
        # For now, just update version
        conn.execute("UPDATE schema_version SET version = ?", (to_version,))
    
    def create_job(self, job: Job) -> Job:
        """Create a new job in the store."""
        with self._transaction() as conn:
            conn.execute("""
                INSERT INTO jobs (
                    job_id, status, progress, cancel_requested,
                    created_at, started_at, completed_at,
                    error_code, error_message,
                    config_json, steps_json, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.job_id,
                job.status.value,
                job.progress,
                1 if job.cancel_requested else 0,
                job.created_at.isoformat() if job.created_at else None,
                job.started_at.isoformat() if job.started_at else None,
                job.completed_at.isoformat() if job.completed_at else None,
                job.error_code.value if job.error_code else None,
                job.error_message,
                json.dumps(job.config),
                json.dumps([s.to_dict() for s in job.steps]),
                json.dumps(job.metadata),
            ))
        return job
    
    def update_job(self, job: Job) -> Job:
        """Update an existing job."""
        with self._transaction() as conn:
            conn.execute("""
                UPDATE jobs SET
                    status = ?,
                    progress = ?,
                    cancel_requested = ?,
                    started_at = ?,
                    completed_at = ?,
                    error_code = ?,
                    error_message = ?,
                    config_json = ?,
                    steps_json = ?,
                    metadata_json = ?
                WHERE job_id = ?
            """, (
                job.status.value,
                job.progress,
                1 if job.cancel_requested else 0,
                job.started_at.isoformat() if job.started_at else None,
                job.completed_at.isoformat() if job.completed_at else None,
                job.error_code.value if job.error_code else None,
                job.error_message,
                json.dumps(job.config),
                json.dumps([s.to_dict() for s in job.steps]),
                json.dumps(job.metadata),
                job.job_id,
            ))
        return job
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID."""
        conn = self._get_connection()
        cursor = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        return self._row_to_job(row)
    
    def list_jobs(self, status: Optional[JobStatus] = None, limit: int = 100) -> List[Job]:
        """List jobs, optionally filtered by status."""
        conn = self._get_connection()
        
        if status:
            cursor = conn.execute(
                "SELECT * FROM jobs WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                (status.value, limit)
            )
        else:
            cursor = conn.execute(
                "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
        
        return [self._row_to_job(row) for row in cursor.fetchall()]
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job by ID."""
        with self._transaction() as conn:
            cursor = conn.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
            return cursor.rowcount > 0
    
    def set_cancel_requested(self, job_id: str) -> bool:
        """Set cancel_requested flag for a job."""
        with self._transaction() as conn:
            cursor = conn.execute(
                "UPDATE jobs SET cancel_requested = 1 WHERE job_id = ?",
                (job_id,)
            )
            return cursor.rowcount > 0
    
    def is_cancel_requested(self, job_id: str) -> bool:
        """Check if cancelation was requested for a job."""
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT cancel_requested FROM jobs WHERE job_id = ?",
            (job_id,)
        )
        row = cursor.fetchone()
        return bool(row and row['cancel_requested'])
    
    def update_progress(self, job_id: str, progress: float) -> bool:
        """Update job progress (atomic, monotonic)."""
        with self._transaction() as conn:
            # Only update if new progress is greater
            cursor = conn.execute("""
                UPDATE jobs SET progress = ?
                WHERE job_id = ? AND progress < ?
            """, (progress, job_id, progress))
            return cursor.rowcount > 0
    
    def _row_to_job(self, row: sqlite3.Row) -> Job:
        """Convert database row to Job object."""
        from facefusion.orchestrator.models import Step, ErrorCode
        from datetime import datetime
        
        steps_data = json.loads(row['steps_json'] or '[]')
        
        return Job(
            job_id=row['job_id'],
            status=JobStatus(row['status']),
            progress=row['progress'] or 0.0,
            cancel_requested=bool(row['cancel_requested']),
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.utcnow(),
            started_at=datetime.fromisoformat(row['started_at']) if row['started_at'] else None,
            completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
            error_code=ErrorCode(row['error_code']) if row['error_code'] else None,
            error_message=row['error_message'],
            config=json.loads(row['config_json'] or '{}'),
            steps=[Step.from_dict(s) for s in steps_data],
            metadata=json.loads(row['metadata_json'] or '{}'),
        )
    
    def close(self) -> None:
        """Close database connections."""
        if hasattr(self._local, 'conn') and self._local.conn:
            self._local.conn.close()
            self._local.conn = None
