from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
import shutil

from app.database import init_db
from app.services.tracker import add_job, get_job, update_parsed_job
from app.services.job_parser import parse_job_text
from app.services.match_scorer import score_job
from app.services.profile import validate_profile
from app.services.resume_tailor import tailor_resume
from app.services.pdf_generator import generate_resume_pdf
from app.services.cover_letter import generate_cover_letter

app = FastAPI(title="Job Application Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup() -> None:
    init_db()

from app.services.pdf_parser import parse_cv_pdf
import json

@app.post("/api/upload-cv")
async def upload_cv(file: UploadFile = File(...)):
    upload_dir = Path("outputs/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # PDF'yi Ollama (Llama 3.2) ile analiz et ve JSON'a çevir
        candidate_profile = parse_cv_pdf(file_path)
        
        # Sonucu özel bir JSON dosyasına kaydet
        profile_path = Path("data/uploaded_profile.json")
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        with open(profile_path, "w", encoding="utf-8") as f:
            f.write(candidate_profile.model_dump_json(indent=2))
            
        return {"message": "CV başarıyla analiz edildi ve kaydedildi!", "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class JobRequest(BaseModel):
    description: str
    generate_cover_letter: bool = False

@app.post("/api/tailor")
def tailor_cv(req: JobRequest):
    if not req.description.strip():
        raise HTTPException(status_code=400, detail="Description is empty")
    
    try:
        uploaded_profile_path = Path("data/uploaded_profile.json")
        if uploaded_profile_path.exists():
            profile_path = uploaded_profile_path
        else:
            profile_path = Path("data/candidate_profile.json")
            
        candidate = validate_profile(profile_path)
        
        job_id = add_job(description=req.description, source="web")
        row = get_job(job_id)
        
        parsed = parse_job_text(row["description"])
        update_parsed_job(job_id, parsed)
        
        score = score_job(candidate, parsed)
        resume = tailor_resume(candidate, parsed)
        pdf_path = generate_resume_pdf(candidate, resume, parsed.company, parsed.title)
        
        cover_letter_url = None
        if req.generate_cover_letter:
            cl_text = generate_cover_letter(candidate, parsed, resume)
            cl_path = Path("outputs/cover_letters") / f"{job_id}.txt"
            cl_path.parent.mkdir(parents=True, exist_ok=True)
            cl_path.write_text(cl_text, encoding="utf-8")
            cover_letter_url = f"/api/download_cl/{cl_path.name}"
            
        return {
            "score": score.total,
            "matched_skills": score.matched_skills,
            "missing_skills": score.missing_skills,
            "pdf_url": f"/api/download/{pdf_path.name}",
            "cover_letter_url": cover_letter_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download/{filename}")
def download_pdf(filename: str):
    pdf_path = Path("outputs/resumes") / filename
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    # Inline rendering for iframe
    return FileResponse(
        pdf_path, 
        media_type="application/pdf", 
        content_disposition_type="inline"
    )

@app.get("/api/download_cl/{filename}")
def download_cl(filename: str):
    cl_path = Path("outputs/cover_letters") / filename
    if not cl_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        cl_path, 
        media_type="text/plain", 
        filename=filename
    )

