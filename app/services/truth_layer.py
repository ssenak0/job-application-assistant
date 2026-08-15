from app.schemas import CandidateProfile, ResumeClaim, TailoredResume


class TruthLayerError(ValueError):
    pass


def validate_claim(profile: CandidateProfile, claim: ResumeClaim) -> None:
    if claim.source_id not in profile.source_ids():
        raise TruthLayerError(f"Unsupported claim source: {claim.source_id}")

    lowered_claim = claim.text.lower()
    for forbidden in profile.never_claim:
        if forbidden.lower() in lowered_claim:
            raise TruthLayerError(f"Forbidden claim detected: {forbidden}")


def validate_tailored_resume(profile: CandidateProfile, resume: TailoredResume) -> None:
    validate_claim(profile, resume.summary)
    for project in resume.projects:
        for bullet in project.bullets:
            validate_claim(profile, bullet)

