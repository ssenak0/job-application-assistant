from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import sqlite3

from app.config import get_settings


def connect() -> sqlite3.Connection:
    settings = get_settings()
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(settings.database_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS jobs (
              id TEXT PRIMARY KEY,
              source TEXT NOT NULL,
              source_risk TEXT NOT NULL,
              url TEXT,
              company TEXT NOT NULL,
              title TEXT NOT NULL,
              location TEXT NOT NULL,
              description TEXT NOT NULL,
              parsed_json TEXT,
              status TEXT NOT NULL,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS applications (
              id TEXT PRIMARY KEY,
              job_id TEXT NOT NULL,
              status TEXT NOT NULL,
              match_score INTEGER DEFAULT 0,
              quality_score INTEGER DEFAULT 0,
              resume_version_id TEXT,
              cover_letter_path TEXT,
              recruiter_message_path TEXT,
              applied_at TEXT,
              notes TEXT DEFAULT '',
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              FOREIGN KEY(job_id) REFERENCES jobs(id)
            );

            CREATE TABLE IF NOT EXISTS resume_versions (
              id TEXT PRIMARY KEY,
              job_id TEXT NOT NULL,
              template_version TEXT NOT NULL,
              pdf_path TEXT NOT NULL,
              html_path TEXT,
              metadata_json TEXT NOT NULL,
              ats_passed INTEGER NOT NULL,
              created_at TEXT NOT NULL,
              FOREIGN KEY(job_id) REFERENCES jobs(id)
            );

            CREATE TABLE IF NOT EXISTS generated_documents (
              id TEXT PRIMARY KEY,
              job_id TEXT NOT NULL,
              kind TEXT NOT NULL,
              path TEXT NOT NULL,
              metadata_json TEXT NOT NULL,
              created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS skill_gap_events (
              id TEXT PRIMARY KEY,
              job_id TEXT NOT NULL,
              skill TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            """
        )


def now_iso() -> str:
    return datetime.utcnow().isoformat()


def dump_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

