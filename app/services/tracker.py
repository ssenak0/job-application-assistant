from __future__ import annotations

from datetime import datetime
from pathlib import Path
import hashlib
import json
import sqlite3

from app.database import connect, dump_json, now_iso
from app.schemas import JobRecord, JobStatus, MatchScore, ParsedJob


def stable_job_id(description: str, url: str | None = None) -> str:
    material = (url or "") + "::" + description[:1000]
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


def add_job(description: str, source: str = "manual", source_risk: str = "low", url: str | None = None) -> str:
    job_id = stable_job_id(description, url)
    timestamp = now_iso()
    with connect() as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO jobs
            (id, source, source_risk, url, company, title, location, description, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (job_id, source, source_risk, url, "Unknown", "Unknown", "Unknown", description, JobStatus.new.value, timestamp, timestamp),
        )
    return job_id


def get_job(job_id: str) -> sqlite3.Row:
    with connect() as connection:
        row = connection.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if row is None:
        raise ValueError(f"Job not found: {job_id}")
    return row


def update_parsed_job(job_id: str, parsed: ParsedJob) -> None:
    with connect() as connection:
        connection.execute(
            """
            UPDATE jobs
            SET company = ?, title = ?, location = ?, parsed_json = ?, status = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                parsed.company,
                parsed.title,
                parsed.location,
                parsed.model_dump_json(),
                JobStatus.parsed.value,
                now_iso(),
                job_id,
            ),
        )


def load_parsed_job(job_id: str) -> ParsedJob:
    row = get_job(job_id)
    if not row["parsed_json"]:
        raise ValueError("Job has not been parsed yet.")
    return ParsedJob.model_validate(json.loads(row["parsed_json"]))


def save_application_review(job_id: str, score: MatchScore) -> str:
    application_id = hashlib.sha256(f"{job_id}:application".encode("utf-8")).hexdigest()[:16]
    timestamp = now_iso()
    with connect() as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO applications
            (id, job_id, status, match_score, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (application_id, job_id, JobStatus.review.value, score.total, timestamp, timestamp),
        )
        for skill in score.missing_skills:
            connection.execute(
                "INSERT INTO skill_gap_events (id, job_id, skill, created_at) VALUES (?, ?, ?, ?)",
                (hashlib.sha256(f"{job_id}:{skill}".encode("utf-8")).hexdigest()[:16], job_id, skill, timestamp),
            )
    return application_id


def save_resume_version(job_id: str, pdf_path: Path, metadata: dict, ats_passed: bool) -> str:
    version_id = hashlib.sha256(f"{job_id}:{pdf_path}".encode("utf-8")).hexdigest()[:16]
    with connect() as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO resume_versions
            (id, job_id, template_version, pdf_path, html_path, metadata_json, ats_passed, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                version_id,
                job_id,
                "ats_v1",
                str(pdf_path),
                str(pdf_path.with_suffix(".html")),
                dump_json(metadata),
                int(ats_passed),
                now_iso(),
            ),
        )
        connection.execute(
            "UPDATE applications SET resume_version_id = ?, status = ?, updated_at = ? WHERE job_id = ?",
            (version_id, JobStatus.tailored.value, now_iso(), job_id),
        )
    return version_id


def save_generated_document(job_id: str, kind: str, path: Path, metadata: dict | None = None) -> str:
    document_id = hashlib.sha256(f"{job_id}:{kind}:{path}".encode("utf-8")).hexdigest()[:16]
    with connect() as connection:
        connection.execute(
            "INSERT OR REPLACE INTO generated_documents (id, job_id, kind, path, metadata_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (document_id, job_id, kind, str(path), dump_json(metadata or {}), now_iso()),
        )
    return document_id


def mark_applied(job_id: str) -> None:
    with connect() as connection:
        connection.execute(
            "UPDATE applications SET status = ?, applied_at = ?, updated_at = ? WHERE job_id = ?",
            (JobStatus.applied.value, datetime.utcnow().isoformat(), now_iso(), job_id),
        )


def list_jobs(status: str | None = None) -> list[sqlite3.Row]:
    query = "SELECT * FROM jobs"
    params: tuple[str, ...] = ()
    if status:
        query += " WHERE status = ?"
        params = (status,)
    query += " ORDER BY created_at DESC"
    with connect() as connection:
        return list(connection.execute(query, params).fetchall())

