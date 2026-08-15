from __future__ import annotations

from pathlib import Path
import json

import typer

from app.database import init_db
from app.schemas import ParsedJob
from app.services.ats_validator import validate_ats_pdf
from app.services.cover_letter import generate_cover_letter, generate_recruiter_message
from app.services.job_parser import parse_job_text
from app.services.match_scorer import score_job
from app.services.pdf_generator import generate_resume_pdf
from app.services.profile import validate_profile
from app.services.resume_tailor import tailor_resume
from app.services.tracker import (
    add_job as add_job_record,
    get_job,
    list_jobs as list_job_records,
    load_parsed_job,
    mark_applied as mark_applied_record,
    save_application_review,
    save_generated_document,
    save_resume_version,
    update_parsed_job,
)

app = typer.Typer(help="Local-first job application assistant.")
profile_app = typer.Typer(help="Candidate profile commands.")
app.add_typer(profile_app, name="profile")


@app.command("init-db")
def init_database() -> None:
    init_db()
    typer.echo("Database initialized.")


@profile_app.command("validate")
def validate_candidate_profile(profile: Path = typer.Option(..., "--profile")) -> None:
    validate_profile(profile)
    typer.echo(f"Profile is valid: {profile}")


@app.command("add-job")
def add_job(input: Path = typer.Option(..., "--input"), source: str = "manual", url: str | None = None) -> None:
    init_db()
    description = input.read_text(encoding="utf-8")
    job_id = add_job_record(description=description, source=source, url=url)
    typer.echo(job_id)


@app.command("parse-job")
def parse_job(job_id: str = typer.Option(..., "--job-id")) -> None:
    row = get_job(job_id)
    parsed = parse_job_text(row["description"])
    update_parsed_job(job_id, parsed)
    typer.echo(parsed.model_dump_json(indent=2))


@app.command("score-job")
def score_job_command(job_id: str = typer.Option(..., "--job-id"), profile: Path = typer.Option("data/candidate_profile.json", "--profile")) -> None:
    candidate = validate_profile(profile)
    parsed = load_parsed_job(job_id)
    score = score_job(candidate, parsed)
    save_application_review(job_id, score)
    typer.echo(score.model_dump_json(indent=2))


@app.command("tailor-resume")
def tailor_resume_command(job_id: str = typer.Option(..., "--job-id"), profile: Path = typer.Option("data/candidate_profile.json", "--profile")) -> None:
    candidate = validate_profile(profile)
    parsed = load_parsed_job(job_id)
    resume = tailor_resume(candidate, parsed)
    pdf_path = generate_resume_pdf(candidate, resume, parsed.company, parsed.title)
    validation = validate_ats_pdf(pdf_path)
    save_resume_version(
        job_id,
        pdf_path,
        {"tailored_resume": resume.model_dump(), "ats_validation": validation.model_dump()},
        validation.passed,
    )
    typer.echo(f"Resume: {pdf_path}")
    typer.echo(validation.model_dump_json(indent=2))
    if not validation.passed:
        raise typer.Exit(code=2)


@app.command("validate-resume")
def validate_resume(resume: Path = typer.Option(..., "--resume")) -> None:
    result = validate_ats_pdf(resume)
    typer.echo(result.model_dump_json(indent=2))
    if not result.passed:
        raise typer.Exit(code=2)


@app.command("generate-cover-letter")
def cover_letter_command(job_id: str = typer.Option(..., "--job-id"), profile: Path = typer.Option("data/candidate_profile.json", "--profile")) -> None:
    candidate = validate_profile(profile)
    parsed = load_parsed_job(job_id)
    resume = tailor_resume(candidate, parsed)
    text = generate_cover_letter(candidate, parsed, resume)
    path = Path("outputs/cover_letters") / f"{job_id}.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    save_generated_document(job_id, "cover_letter", path)
    typer.echo(path)


@app.command("generate-message")
def message_command(job_id: str = typer.Option(..., "--job-id"), profile: Path = typer.Option("data/candidate_profile.json", "--profile")) -> None:
    candidate = validate_profile(profile)
    parsed = load_parsed_job(job_id)
    text = generate_recruiter_message(candidate, parsed)
    path = Path("outputs/messages") / f"{job_id}.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    save_generated_document(job_id, "recruiter_message", path)
    typer.echo(path)


@app.command("list-jobs")
def list_jobs(status: str | None = typer.Option(None, "--status")) -> None:
    for row in list_job_records(status):
        typer.echo(f"{row['id']} | {row['status']} | {row['company']} | {row['title']}")


@app.command("mark-applied")
def mark_applied(job_id: str = typer.Option(..., "--job-id")) -> None:
    confirmation = typer.prompt("Have you manually applied to this job? Type APPLY to confirm")
    if confirmation != "APPLY":
        typer.echo("Not marked as applied.")
        raise typer.Exit(code=1)
    mark_applied_record(job_id)
    typer.echo("Marked as applied.")


@app.command("import-links")
def import_links(input: Path = typer.Option(..., "--input")) -> None:
    init_db()
    links = [line.strip() for line in input.read_text(encoding="utf-8").splitlines() if line.strip()]
    imported = []
    for link in links:
        risk = "high" if "linkedin.com" in link.lower() else "medium"
        text = f"URL: {link}\nManual job text required." if risk == "high" else f"URL: {link}\nPending fetch or manual text."
        imported.append(add_job_record(text, source="link_import", source_risk=risk, url=link))
    typer.echo(json.dumps({"imported": len(imported), "job_ids": imported}, indent=2))


@app.command("daily-report")
def daily_report() -> None:
    rows = list_job_records()
    status_counts: dict[str, int] = {}
    for row in rows:
        status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1
    typer.echo(json.dumps({"jobs_total": len(rows), "by_status": status_counts}, indent=2))


@app.command("weekly-report")
def weekly_report() -> None:
    typer.echo(json.dumps({"message": "Weekly analytics scaffold is ready; update statuses to build signal."}, indent=2))


@app.command("discover-jobs")
def discover_jobs(query: str = typer.Option(..., "--query"), daily_target: int = typer.Option(50, "--daily-target")) -> None:
    typer.echo(
        json.dumps(
            {
                "query": query,
                "daily_target": daily_target,
                "status": "Discovery scaffold ready. Configure Google Custom Search or public board adapters next.",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    app()

