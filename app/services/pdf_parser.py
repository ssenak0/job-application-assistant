import json
from pathlib import Path
from pypdf import PdfReader
from ollama import chat
from pydantic import BaseModel

from app.schemas import CandidateProfile

def parse_cv_pdf(pdf_path: Path) -> CandidateProfile:
    # 1. Metni ve Fotoğrafı PDF'den çıkart
    reader = PdfReader(str(pdf_path))
    text = ""
    image_extracted = False
    
    upload_dir = Path("outputs/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    pic_path = upload_dir / "profile_pic.png"
    
    # Eski fotoğrafı sil
    if pic_path.exists():
        pic_path.unlink()

    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
            
        # Fotoğraf çıkartma (ilk bulunanı al)
        if not image_extracted and page.images:
            for image_file_object in page.images:
                with open(pic_path, "wb") as fp:
                    fp.write(image_file_object.data)
                image_extracted = True
                break
                
    # Raw metni yedekleme amacıyla kaydet
    Path("data/uploaded_raw.txt").write_text(text, encoding="utf-8")

    # 2. Ollama ile Llama3.2 modeline metni verip JSON çek
    schema = CandidateProfile.model_json_schema()
    
    prompt = f"""
    Sen uzman bir İnsan Kaynakları asistanısın. Görevin aşağıda verilen CV metnini analiz edip, İSTENEN JSON formatında eksiksiz ve doğru bir şekilde dönüştürmektir.
    Lütfen adayın kimlik bilgilerini, yeteneklerini, projelerini, eğitimini ve deneyimlerini doldur.
    ÖNEMLİ: İş deneyimi ve Projeler (bullets) kısmını çok kısa tutma! CV'deki bilgileri kullanarak her bir projeyi ve deneyimi, adayın neler başardığını gösterecek şekilde detaylı, etkileyici ve profesyonel cümleler (bullet points) halinde yaz.
    Fakat CV'de OLMAYAN hiçbir bilgiyi de uydurma.
    
    CV Metni:
    {text}
    """
    
    try:
        response = chat(
            model='llama3.2',
            messages=[{'role': 'user', 'content': prompt}],
            format=schema,
            options={'temperature': 0}
        )
        
        parsed_json = json.loads(response.message.content)
        return CandidateProfile(**parsed_json)
    except Exception as e:
        print(f"Ollama Parse Hatası: {e}")
        raise Exception(f"PDF Analiz Hatası: {str(e)}")
