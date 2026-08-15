from app.schemas import CandidateProfile, ParsedJob, TailoredResume


def generate_cover_letter(profile: CandidateProfile, job: ParsedJob, resume: TailoredResume) -> str:
    strongest_project = resume.projects[0].name if resume.projects else "yazılım projelerim"
    skills = ", ".join(skill["name"] for skill in resume.skills[:4])
    return (
        f"Sayın İlgili,\n\n"
        f"{job.company} bünyesindeki {job.title} pozisyonu ile yakından ilgileniyorum. "
        f"Bir bilgisayar mühendisi olarak {skills} gibi teknolojileri kullanarak çeşitli pratik projeler geliştirdim. "
        f"Özellikle {strongest_project} üzerine yaptığım çalışmalar, pratik yazılım mühendisliği süreçlerini barındırdığı için bu rolle doğrudan örtüşmektedir.\n\n"
        f"Proje deneyimlerimin ve öğrenmeye açık yapımın ekibinize nasıl katkı sağlayabileceğini detaylandırmak üzere sizinle görüşmekten memnuniyet duyarım.\n\n"
        f"Saygılarımla,\n{profile.identity.full_name}\n"
    )


def generate_recruiter_message(profile: CandidateProfile, job: ParsedJob) -> str:
    return (
        f"Merhaba, {job.company} ekibindeki {job.title} rolünü gördüm. "
        f"Bir bilgisayar mühendisi olarak geliştirdiğim projelerin ve kariyer hedeflerimin bu pozisyonla çok uyumlu olduğunu düşünüyorum. "
        f"Değerlendirmeye alınmaktan memnuniyet duyarım. İyi çalışmalar dilerim, {profile.identity.full_name}."
    )[:600]

