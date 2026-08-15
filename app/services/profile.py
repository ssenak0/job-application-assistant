from pathlib import Path
import json

from app.schemas import CandidateProfile


def load_profile(path: Path) -> CandidateProfile:
    return CandidateProfile.model_validate(json.loads(path.read_text(encoding="utf-8")))


def validate_profile(path: Path) -> CandidateProfile:
    profile = load_profile(path)
    if not profile.projects and not profile.experience:
        raise ValueError("Profile must include at least one project or experience item.")
    if not profile.skills:
        raise ValueError("Profile must include at least one skill.")
    return profile

