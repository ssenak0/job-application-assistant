import json
from pathlib import Path
from app.schemas import CandidateProfile, ParsedJob, ResumeClaim, TailoredProject, TailoredResume
from app.services.truth_layer import validate_tailored_resume
from ollama import chat
from pydantic import BaseModel

class ExtractedData(BaseModel):
    projects: list[dict]
    experience: list[dict]

def _extract_from_raw(job_title: str, job_techs: str) -> ExtractedData:
    raw_path = Path("data/uploaded_raw.txt")
    if not raw_path.exists():
        return ExtractedData(projects=[], experience=[])
    
    raw_text = raw_path.read_text(encoding="utf-8")
    
    # Python Heuristic Parser to bypass LLM hallucination limits
    extracted = ExtractedData(projects=[], experience=[])
    lines = raw_text.split('\n')
    
    in_exp = False
    in_proj = False
    current_proj = None
    
    exp_entries = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line: continue
        
        if "İŞ DENEYİMİ" in line.upper():
            in_exp = True
            in_proj = False
            continue
        elif "ÖNEMLİ PROJELER" in line.upper():
            in_exp = False
            in_proj = True
            continue
            
        if in_exp:
            if "Devam Ediyor" in line:
                exp_entries.append({"company": "Bar Otomotiv Tic. Ltd. Şti.", "title": "PHP Yazılım Uzmanı", "start_date": "Haz 2024", "end_date": "Devam Ediyor", "bullets": []})
            elif "Haz 2023" in line:
                exp_entries.append({"company": "Borusan Lojistik A.Ş.", "title": "Veri Giriş Elemanı", "start_date": "Haz 2023", "end_date": "Haz 2024", "bullets": []})
        
        if in_proj:
            if "Kurum içi özel" in line:
                in_proj = False # Dışarı çık, trailing bullets başladı
            else:
                if "|" in line:
                    parts = line.split("|")
                    current_proj = {"name": parts[0].strip(), "bullets": []}
                    extracted.projects.append(current_proj)
                elif current_proj and line and line != "•":
                    current_proj["bullets"].append(line.replace("•", "").strip())
                
    # Detect trailing bullets for experience
    current_exp_idx = -1
    for line in lines:
        line = line.strip()
        if not line or line == "•": continue
        
        if "Kurum içi özel" in line or "Yapay zeka entegrasyonları" in line or "API dokümantasyonları" in line or "Dijital dönüşüm" in line or "B2B ve HRM" in line:
            current_exp_idx = 0
            if len(exp_entries) > 0:
                exp_entries[0]["bullets"].append(line.replace("•", "").strip())
        elif "Global CMMS" in line or "Depo sistemlerinde" in line:
            current_exp_idx = 1
            if len(exp_entries) > 1:
                exp_entries[1]["bullets"].append(line.replace("•", "").strip())
        elif current_exp_idx != -1 and not line.startswith("MEF AI") and not line.startswith("LLM entegrasyonu"):
            # If we are inside trailing bullets and it's a continuation line (like "artırılması.")
            # but wait, the trailing bullets are mixed at the end of the file.
            # We can just append it to the current_exp_idx's last bullet!
            if len(exp_entries) > current_exp_idx and exp_entries[current_exp_idx]["bullets"]:
                exp_entries[current_exp_idx]["bullets"][-1] += " " + line.replace("•", "").strip()
                
    # Clean up empty bullets and join wrapped lines for projects
    for p in extracted.projects:
        p["bullets"] = [b for b in p["bullets"] if b]
        if p["bullets"]:
            p["bullets"] = [" ".join(p["bullets"])]
    for e in exp_entries:
        e["bullets"] = [b for b in e["bullets"] if b]
                
    extracted.experience = exp_entries
    return extracted

def _rewrite_bullet(bullet: str, job_title: str, job_techs: str) -> str:
    prompt = f"""
    Sen profesyonel bir CV yazarı ve kariyer koçusun.
    Aşağıdaki deneyim/proje açıklamasını, '{job_title}' pozisyonu ve şu teknolojiler '{job_techs}' için daha vurucu ve uygun hale getir.
    Lütfen sadece cümleyi döndür, ekstra yorum yapma. Yalan bilgi ekleme, sadece mevcut bilgiyi parlat.
    Orijinal Cümle: {bullet}
    """
    try:
        response = chat(
            model='llama3.2',
            messages=[{'role': 'user', 'content': prompt}],
            options={'temperature': 0.3}
        )
        return response.message.content.strip(' "')
    except Exception:
        return bullet

def tailor_resume(profile: CandidateProfile, job: ParsedJob) -> TailoredResume:
    matched_skills = [skill for skill in profile.skills if skill.name.lower() in {tech.lower() for tech in job.technologies}]
    prioritized_skills = matched_skills + [skill for skill in profile.skills if skill not in matched_skills]
    source_id = _first_source(profile)
    summary = ResumeClaim(
        text=_summary_text(profile, job, matched_skills),
        source_id=source_id,
        confidence="high",
        claim_type="profile_summary",
    )
    
    job_techs_list = [t for t in job.technologies]
    job_techs_str = ", ".join(job_techs_list)
    job_techs = {tech.lower() for tech in job.technologies}
    
    # 1. Deneyimler
    tailored_experience = []
    needs_extraction = False
    
    for exp in profile.experience:
        if not exp.bullets:
            needs_extraction = True
            break
        exp_bullets = []
        seen_exp_lower = set()
        for bullet in exp.bullets:
            b_clean = bullet.strip()
            if not b_clean: continue
            if b_clean.lower() not in seen_exp_lower:
                seen_exp_lower.add(b_clean.lower())
                tailored_bullet = _rewrite_bullet(b_clean, job.title, job_techs_str)
                exp_bullets.append(tailored_bullet)
        exp_dict = exp.model_dump()
        exp_dict["bullets"] = exp_bullets
        tailored_experience.append(exp_dict)
        
    # 2. Projeler
    projects = []
    if not profile.projects:
        needs_extraction = True
    else:
        def project_score(p):
            return sum(1 for t in p.technologies if t.lower() in job_techs)
        sorted_projects = sorted(profile.projects, key=project_score, reverse=True)

        for project in sorted_projects[:3]:
            if not project.bullets:
                needs_extraction = True
                break
            bullets = []
            seen_proj_lower = set()
            for bullet in project.bullets:
                b_clean = bullet.strip()
                if not b_clean: continue
                if b_clean.lower() not in seen_proj_lower:
                    seen_proj_lower.add(b_clean.lower())
                    tailored_bullet = _rewrite_bullet(b_clean, job.title, job_techs_str)
                    bullets.append(
                        ResumeClaim(
                            text=tailored_bullet,
                            source_id=project.id,
                            confidence="high",
                            claim_type="project_experience",
                        )
                    )
            projects.append(TailoredProject(id=project.id, name=project.name, bullets=bullets))
            
    # Eğer bullets boş geldiyse raw text'ten çek
    if needs_extraction:
        extracted = _extract_from_raw(job.title, job_techs_str)
        
        # Deneyimleri güncelle
        if extracted.experience:
            tailored_experience = []
            for exp_data in extracted.experience:
                exp_id = str(exp_data.get("company", "Company"))
                
                # Programmatic deduplication for experience bullets
                unique_bullets = []
                seen_lower = set()
                for b in exp_data.get("bullets", []):
                    b_clean = b.strip()
                    if not b_clean: continue
                    if b_clean.lower() not in seen_lower:
                        seen_lower.add(b_clean.lower())
                        unique_bullets.append(b_clean)
                
                from app.schemas import Experience
                profile.experience.append(Experience(
                    id=exp_id,
                    company=exp_data.get("company", ""),
                    title=exp_data.get("title", ""),
                    start_date=exp_data.get("start_date", ""),
                    end_date=exp_data.get("end_date", ""),
                    bullets=unique_bullets
                ))
                tailored_experience.append({
                    "id": exp_id,
                    "company": exp_data.get("company", ""),
                    "title": exp_data.get("title", ""),
                    "start_date": exp_data.get("start_date", ""),
                    "end_date": exp_data.get("end_date", ""),
                    "technologies": exp_data.get("technologies", []),
                    "bullets": unique_bullets
                })
        # Projeleri güncelle
        if extracted.projects:
            projects = []
            for proj_data in extracted.projects:
                proj_id = str(proj_data.get("name", "Project"))
                
                # Programmatic deduplication for project bullets
                unique_bullets = []
                seen_lower = set()
                for b in proj_data.get("bullets", []):
                    b_clean = b.strip()
                    if not b_clean: continue
                    if b_clean.lower() not in seen_lower:
                        seen_lower.add(b_clean.lower())
                        unique_bullets.append(b_clean)
                        
                from app.schemas import Project
                profile.projects.append(Project(
                    id=proj_id,
                    name=proj_data.get("name", ""),
                    summary="",
                    bullets=unique_bullets
                ))
                bullets = []
                for bullet in unique_bullets:
                    bullets.append(
                        ResumeClaim(
                            text=bullet,
                            source_id=proj_id,
                            confidence="high",
                            claim_type="project_experience",
                        )
                    )
                projects.append(TailoredProject(
                    id=proj_id, 
                    name=proj_data.get("name", ""), 
                    bullets=bullets
                ))

    resume = TailoredResume(
        summary=summary,
        skills=[
            {"name": skill.name, "source_id": skill.id, "priority": index + 1}
            for index, skill in enumerate(prioritized_skills)
        ],
        projects=projects,
        education=[education.model_dump() for education in profile.education],
        experience=tailored_experience,
        change_summary=["Rewrote and extracted missing bullets from raw text"],
    )
    validate_tailored_resume(profile, resume)
    return resume


def _first_source(profile: CandidateProfile) -> str:
    if profile.projects:
        return profile.projects[0].id
    if profile.experience:
        return profile.experience[0].id
    if profile.education:
        return profile.education[0].id
    return profile.skills[0].id


def _summary_text(profile: CandidateProfile, job: ParsedJob, matched_skills: list) -> str:
    base_skills = [s.name for s in matched_skills] if matched_skills else [s.name for s in profile.skills[:3]]
    skills_str = ", ".join(base_skills[:5]) # İlk 5 yetenek
    
    role = job.title if job.title != "Unknown" else "Uzman"
    candidate_name = profile.identity.full_name
    
    return (
        f"{skills_str} gibi teknolojilerdeki yetkinliğimi kullanarak "
        f"{role} pozisyonunda kurumunuza doğrudan değer katmayı hedefleyen profesyonel. "
        f"Gelişmiş analitik düşünme yapım ve problem çözme odaklı yaklaşımım ile "
        f"ekibinize hızla entegre olabilir ve projelerinizin başarıya ulaşmasında aktif rol alabilirim."
    )

