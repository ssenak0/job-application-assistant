import streamlit as st
from pathlib import Path
import base64

from app.database import init_db
from app.services.tracker import add_job, get_job, update_parsed_job
from app.services.job_parser import parse_job_text
from app.services.match_scorer import score_job
from app.services.profile import validate_profile
from app.services.resume_tailor import tailor_resume
from app.services.pdf_generator import generate_resume_pdf

st.set_page_config(page_title="AI Kariyer Asistanı", layout="wide")

st.title("🚀 AI Destekli Kariyer ve CV Asistanı")
st.markdown("Başvurmak istediğiniz iş ilanının metnini aşağıya yapıştırın. Yapay zeka sizin profilinizle ilanı eşleştirecek ve size özel bir CV üretecektir.")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 İlan Girdisi")
    job_text = st.text_area("İlan Metnini Buraya Yapıştırın", height=400)
    
    if st.button("✨ İlana Özel CV'mi Üret", use_container_width=True, type="primary"):
        if not job_text.strip():
            st.error("Lütfen bir ilan metni girin.")
        else:
            with st.spinner("Yapay zeka ilanı analiz ediyor ve CV'nizi hazırlıyor..."):
                try:
                    init_db()
                    profile_path = Path("data/candidate_profile.json")
                    candidate = validate_profile(profile_path)
                    
                    # 1. Add job
                    job_id = add_job(description=job_text, source="manual")
                    row = get_job(job_id)
                    
                    # 2. Parse job
                    parsed = parse_job_text(row["description"])
                    update_parsed_job(job_id, parsed)
                    
                    # 3. Score
                    score = score_job(candidate, parsed)
                    
                    # 4. Tailor and generate PDF
                    resume = tailor_resume(candidate, parsed)
                    pdf_path = generate_resume_pdf(candidate, resume, parsed.company, parsed.title)
                    
                    st.session_state["score"] = score
                    st.session_state["pdf_path"] = pdf_path
                    st.success("CV Başarıyla Üretildi!")
                except Exception as e:
                    st.error(f"Bir hata oluştu: {str(e)}")

with col2:
    st.subheader("📊 Analiz ve Sonuç")
    if "score" in st.session_state:
        score = st.session_state["score"]
        pdf_path = st.session_state["pdf_path"]
        
        # Display Score
        st.metric(label="Eşleşme Skoru", value=f"{score.total}/100", delta=score.label)
        
        st.markdown(f"**Eşleşen Yetenekler:** {', '.join(score.matched_skills)}")
        st.markdown(f"**Eksik Yetenekler (Risk):** {', '.join(score.missing_skills)}")
        
        # Download button
        with open(pdf_path, "rb") as pdf_file:
            pdf_bytes = pdf_file.read()
        
        st.download_button(
            label="📥 Üretilen CV'yi İndir",
            data=pdf_bytes,
            file_name=pdf_path.name,
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )
        
        # Preview
        base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
