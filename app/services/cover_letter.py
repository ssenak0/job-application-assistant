from app.schemas import CandidateProfile, ParsedJob, TailoredResume


def generate_cover_letter(profile: CandidateProfile, job: ParsedJob, resume: TailoredResume) -> str:
    strongest_project = resume.projects[0].name if resume.projects else "my software projects"
    skills = ", ".join(skill["name"] for skill in resume.skills[:4])
    return (
        f"Dear Hiring Team,\n\n"
        f"I am interested in the {job.title} role at {job.company}. "
        f"As a new graduate computer engineer, I have built practical projects using {skills}. "
        f"My work on {strongest_project} is especially relevant to this role because it reflects hands-on software engineering practice.\n\n"
        f"I would appreciate the opportunity to discuss how my project experience and learning mindset can contribute to your team.\n\n"
        f"Best regards,\n{profile.identity.full_name}\n"
    )


def generate_recruiter_message(profile: CandidateProfile, job: ParsedJob) -> str:
    return (
        f"Hi, I saw the {job.title} role at {job.company}. "
        f"I am a new graduate computer engineer and the role looks aligned with my software projects and target roles. "
        f"I would appreciate the chance to be considered. Thank you, {profile.identity.full_name}."
    )[:600]

