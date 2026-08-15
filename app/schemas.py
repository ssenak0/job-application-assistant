from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator


class SourceRisk(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class JobStatus(str, Enum):
    new = "new"
    parsed = "parsed"
    review = "review"
    tailored = "tailored"
    applied = "applied"
    skipped = "skipped"
    rejected = "rejected"
    interview = "interview"
    offer = "offer"


class Skill(BaseModel):
    id: str
    name: str
    level: str = "beginner"
    evidence_ids: list[str] = Field(default_factory=list)


class Project(BaseModel):
    id: str
    name: str
    technologies: list[str] = Field(default_factory=list)
    summary: str
    bullets: list[str] = Field(default_factory=list)
    links: dict[str, str] = Field(default_factory=dict)


class Education(BaseModel):
    id: str
    school: str
    degree: str
    start_date: str | None = None
    end_date: str | None = None
    details: list[str] = Field(default_factory=list)


class Experience(BaseModel):
    id: str
    company: str
    title: str
    start_date: str | None = None
    end_date: str | None = None
    technologies: list[str] = Field(default_factory=list)
    bullets: list[str] = Field(default_factory=list)


class Identity(BaseModel):
    full_name: str
    email: str
    phone: str
    location: str
    linkedin: str | None = None
    github: str | None = None
    portfolio: str | None = None


class CandidateProfile(BaseModel):
    identity: Identity
    target_roles: list[str] = Field(default_factory=list)
    preferred_locations: list[str] = Field(default_factory=list)
    languages: list[dict[str, str]] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    skills: list[Skill] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    certifications: list[dict[str, Any]] = Field(default_factory=list)
    never_claim: list[str] = Field(default_factory=list)
    constraints: dict[str, Any] = Field(default_factory=dict)

    def source_ids(self) -> set[str]:
        ids = {item.id for item in self.education}
        ids.update(item.id for item in self.skills)
        ids.update(item.id for item in self.projects)
        ids.update(item.id for item in self.experience)
        for cert in self.certifications:
            cert_id = cert.get("id")
            if cert_id:
                ids.add(str(cert_id))
        return ids

    def skill_names(self) -> set[str]:
        return {skill.name.lower() for skill in self.skills}


class ParsedJob(BaseModel):
    company: str = "Unknown"
    title: str = "Unknown"
    location: str = "Unknown"
    workplace_type: Literal["remote", "hybrid", "onsite", "unknown"] = "unknown"
    seniority: Literal["intern", "entry", "junior", "mid", "senior", "unknown"] = "unknown"
    requirements: list[str] = Field(default_factory=list)
    nice_to_have: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    language_requirements: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    application_questions: list[str] = Field(default_factory=list)


class JobRecord(BaseModel):
    id: str
    source: str = "manual"
    source_risk: SourceRisk = SourceRisk.low
    url: str | None = None
    company: str = "Unknown"
    title: str = "Unknown"
    location: str = "Unknown"
    description: str
    parsed: ParsedJob | None = None
    status: JobStatus = JobStatus.new
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class MatchScore(BaseModel):
    total: int
    label: Literal["strong", "medium", "weak", "skip"]
    technical_match: int
    seniority_match: int
    location_match: int
    language_match: int
    domain_match: int
    education_match: int
    risk_penalty: int
    reasons: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    matched_skills: list[str] = Field(default_factory=list)

    @field_validator("total")
    @classmethod
    def total_range(cls, value: int) -> int:
        return max(0, min(100, value))


class ResumeClaim(BaseModel):
    text: str
    source_id: str
    confidence: Literal["high", "medium", "needs_user_review"]
    claim_type: str


class TailoredProject(BaseModel):
    id: str
    name: str
    bullets: list[ResumeClaim]


class TailoredResume(BaseModel):
    summary: ResumeClaim
    skills: list[dict[str, Any]]
    projects: list[TailoredProject]
    education: list[dict[str, Any]] = Field(default_factory=list)
    experience: list[dict[str, Any]] = Field(default_factory=list)
    needs_user_review: list[str] = Field(default_factory=list)
    change_summary: list[str] = Field(default_factory=list)


class ATSValidationResult(BaseModel):
    passed: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    page_count: int = 0
    text_length: int = 0
    headings_found: list[str] = Field(default_factory=list)

