from __future__ import annotations

import re

from app.schemas import ParsedJob


TECH_KEYWORDS = [
    "python",
    "java",
    "javascript",
    "typescript",
    "react",
    "node",
    "fastapi",
    "django",
    "spring",
    "sql",
    "postgresql",
    "mysql",
    "mongodb",
    "docker",
    "kubernetes",
    "aws",
    "azure",
    "git",
    "linux",
    "rest",
    "graphql",
    "html",
    "css",
]


def parse_job_text(text: str) -> ParsedJob:
    lower = text.lower()
    title = _extract_title(text)
    company = _extract_company(text)
    location = _extract_location(text)
    technologies = sorted({tech for tech in TECH_KEYWORDS if re.search(rf"\b{re.escape(tech)}\b", lower)})
    red_flags = _detect_red_flags(lower, title)
    return ParsedJob(
        company=company,
        title=title,
        location=location,
        workplace_type=_workplace_type(lower),
        seniority=_seniority(lower, title.lower()),
        requirements=_extract_lines(text, ["requirements", "qualifications", "what you bring"]),
        nice_to_have=_extract_lines(text, ["nice to have", "preferred"]),
        responsibilities=_extract_lines(text, ["responsibilities", "what you will do", "role"]),
        technologies=technologies,
        language_requirements=_language_requirements(lower),
        red_flags=red_flags,
        application_questions=_extract_questions(text),
    )


def _extract_title(text: str) -> str:
    for line in _clean_lines(text)[:8]:
        if any(word in line.lower() for word in ["engineer", "developer", "intern", "software", "backend", "frontend"]):
            return line[:120]
    return "Unknown"


def _extract_company(text: str) -> str:
    patterns = [r"company[:\s]+(.+)", r"at\s+([A-Z][A-Za-z0-9 .&-]{2,60})"]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip().splitlines()[0][:80]
    return "Unknown"


def _extract_location(text: str) -> str:
    patterns = [r"location[:\s]+(.+)", r"(remote|hybrid|istanbul|ankara|turkey|europe)"]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip().splitlines()[0][:80]
    return "Unknown"


def _workplace_type(lower: str) -> str:
    if "remote" in lower:
        return "remote"
    if "hybrid" in lower:
        return "hybrid"
    if "onsite" in lower or "on-site" in lower:
        return "onsite"
    return "unknown"


def _seniority(lower: str, title: str) -> str:
    if "intern" in lower or "intern" in title or "staj" in lower:
        return "intern"
    if "new grad" in lower or "graduate" in lower or "entry" in lower:
        return "entry"
    if "junior" in lower or "jr." in lower:
        return "junior"
    if "senior" in lower or "lead" in lower:
        return "senior"
    if "mid" in lower:
        return "mid"
    return "unknown"


def _language_requirements(lower: str) -> list[str]:
    languages = []
    if "english" in lower:
        languages.append("English")
    if "turkish" in lower or "türkçe" in lower:
        languages.append("Turkish")
    return languages


def _detect_red_flags(lower: str, title: str) -> list[str]:
    red_flags = []
    years = [int(value) for value in re.findall(r"(\d+)\+?\s*(?:years|yil|yıl)", lower)]
    if ("junior" in lower or "entry" in lower or "graduate" in lower) and any(year >= 3 for year in years):
        red_flags.append("Junior/entry role asks for 3+ years of experience.")
    if "unpaid" in lower or "ücretsiz" in lower:
        red_flags.append("Role appears to be unpaid.")
    if len([tech for tech in TECH_KEYWORDS if tech in lower]) >= 10:
        red_flags.append("Very broad technology list.")
    if "senior" in lower and ("junior" in title or "entry" in title):
        red_flags.append("Entry title contains senior-level expectations.")
    return red_flags


def _extract_questions(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip().endswith("?")]


def _extract_lines(text: str, section_markers: list[str]) -> list[str]:
    lines = _clean_lines(text)
    selected = []
    for line in lines:
        lowered = line.lower()
        if line.startswith(("-", "•", "*")) or any(marker in lowered for marker in section_markers):
            selected.append(line.lstrip("-•* ").strip())
    return selected[:12]


def _clean_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]

