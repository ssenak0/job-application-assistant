from app.schemas import CandidateProfile, MatchScore, ParsedJob


def score_job(profile: CandidateProfile, job: ParsedJob) -> MatchScore:
    profile_skills = profile.skill_names()
    job_skills = {tech.lower() for tech in job.technologies}
    matched = sorted(profile_skills & job_skills)
    missing = sorted(job_skills - profile_skills)

    technical_match = round(45 * (len(matched) / max(1, len(job_skills)))) if job_skills else 20
    seniority_match = _score_seniority(job.seniority)
    location_match = _score_location(profile, job)
    language_match = _score_language(profile, job)
    domain_match = _score_domain(profile, job)
    education_match = 5 if profile.education else 0
    risk_penalty = -min(30, len(job.red_flags) * 10)
    total = technical_match + seniority_match + location_match + language_match + domain_match + education_match + risk_penalty
    label = _label(total)

    reasons = [
        f"Matched skills: {', '.join(matched) if matched else 'none detected'}.",
        f"Missing skills: {', '.join(missing) if missing else 'none detected'}.",
        f"Seniority detected as {job.seniority}.",
    ]
    reasons.extend(job.red_flags)

    return MatchScore(
        total=max(0, min(100, total)),
        label=label,
        technical_match=technical_match,
        seniority_match=seniority_match,
        location_match=location_match,
        language_match=language_match,
        domain_match=domain_match,
        education_match=education_match,
        risk_penalty=risk_penalty,
        reasons=reasons,
        missing_skills=missing,
        matched_skills=matched,
    )


def _score_seniority(seniority: str) -> int:
    return {
        "intern": 20,
        "entry": 20,
        "junior": 18,
        "unknown": 12,
        "mid": 5,
        "senior": 0,
    }.get(seniority, 8)


def _score_location(profile: CandidateProfile, job: ParsedJob) -> int:
    location_text = f"{job.location} {job.workplace_type}".lower()
    if any(preferred.lower() in location_text for preferred in profile.preferred_locations):
        return 10
    if job.workplace_type == "remote":
        return 10
    if job.workplace_type == "unknown":
        return 5
    return 3


def _score_language(profile: CandidateProfile, job: ParsedJob) -> int:
    if not job.language_requirements:
        return 8
    profile_languages = {language.get("name", "").lower() for language in profile.languages}
    required = {language.lower() for language in job.language_requirements}
    return 10 if required <= profile_languages else 4


def _score_domain(profile: CandidateProfile, job: ParsedJob) -> int:
    project_text = " ".join(project.summary + " " + " ".join(project.technologies) for project in profile.projects).lower()
    job_text = " ".join(job.responsibilities + job.requirements + job.technologies).lower()
    hits = sum(1 for token in ["api", "backend", "frontend", "data", "web", "mobile"] if token in project_text and token in job_text)
    return min(10, hits * 2)


def _label(total: int) -> str:
    if total >= 75:
        return "strong"
    if total >= 55:
        return "medium"
    if total >= 35:
        return "weak"
    return "skip"

