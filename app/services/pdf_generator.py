from __future__ import annotations

from pathlib import Path
import re
import subprocess

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.config import get_settings
from app.schemas import CandidateProfile, TailoredResume


def render_resume_html(profile: CandidateProfile, resume: TailoredResume, output_path: Path) -> Path:
    template_dir = Path(__file__).resolve().parents[1] / "templates"
    env = Environment(loader=FileSystemLoader(template_dir), autoescape=select_autoescape())
    template = env.get_template("ats_resume.html")
    identity = profile.identity
    links = " | ".join(filter(None, [identity.linkedin, identity.github, identity.portfolio]))
    
    # Check for extracted profile picture
    pic_path = Path("outputs/uploads/profile_pic.png").resolve()
    profile_pic = f"file://{pic_path}" if pic_path.exists() else None

    html = template.render(
        full_name=identity.full_name,
        email=identity.email,
        phone=identity.phone,
        location=identity.location,
        links=links,
        identity=identity,
        summary=resume.summary.text,
        skills=resume.skills,
        projects=resume.projects,
        education=resume.education,
        experience=resume.experience,
        profile_pic=profile_pic
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path


def generate_resume_pdf(profile: CandidateProfile, resume: TailoredResume, company: str, title: str) -> Path:
    settings = get_settings()
    resume_dir = settings.output_dir / "resumes"
    resume_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{_slug(company)}_{_slug(title)}_resume.pdf"
    pdf_path = resume_dir / filename
    html_path = pdf_path.with_suffix(".html")
    
    # 1. HTML'i oluştur
    render_resume_html(profile, resume, html_path)
    
    # 2. Chrome Headless ile PDF'e çevir (Sena'nın özel tasarımı için)
    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    subprocess.run([
        chrome_path, 
        "--headless", 
        f"--print-to-pdf={pdf_path}", 
        "--no-pdf-header-footer", 
        f"file://{html_path.resolve()}"
    ], check=True, capture_output=True)
    
    return pdf_path


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.lower()).strip("_")
    return slug or "unknown"
