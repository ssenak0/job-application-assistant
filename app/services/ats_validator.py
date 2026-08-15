from pathlib import Path

from pypdf import PdfReader

from app.config import ATS_POLICY
from app.schemas import ATSValidationResult


def validate_ats_pdf(path: Path) -> ATSValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    headings_found: list[str] = []

    if not path.exists():
        return ATSValidationResult(passed=False, errors=["PDF file does not exist."])
    if path.stat().st_size == 0:
        return ATSValidationResult(passed=False, errors=["PDF file is empty."])

    try:
        reader = PdfReader(str(path))
        page_count = len(reader.pages)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:
        return ATSValidationResult(passed=False, errors=[f"PDF could not be opened: {exc}"])

    if page_count > ATS_POLICY["max_pages"]:
        errors.append(f"PDF has {page_count} pages; max allowed is {ATS_POLICY['max_pages']}.")
    if len(text.strip()) < 300:
        errors.append("Extracted text is too short; PDF may not be ATS-readable.")
    for heading in ATS_POLICY["required_headings"]:
        if heading.lower() in text.lower():
            headings_found.append(heading)
        else:
            errors.append(f"Required heading missing: {heading}")
    if "@" not in text:
        warnings.append("Email address was not detected in extracted text.")
    if any(char == "\ufffd" for char in text):
        errors.append("Broken replacement characters detected in extracted text.")

    return ATSValidationResult(
        passed=not errors,
        errors=errors,
        warnings=warnings,
        page_count=page_count,
        text_length=len(text),
        headings_found=headings_found,
    )

