from functools import lru_cache
from pathlib import Path
import os


class Settings:
    database_path: Path
    output_dir: Path
    max_resume_pages: int
    company_cooldown_days: int
    max_applications_per_company_per_month: int
    llm_provider: str

    def __init__(self) -> None:
        self.database_path = Path(os.getenv("DATABASE_PATH", "data/jobs.db"))
        self.output_dir = Path(os.getenv("OUTPUT_DIR", "outputs"))
        self.max_resume_pages = int(os.getenv("MAX_RESUME_PAGES", "1"))
        self.company_cooldown_days = int(os.getenv("COMPANY_COOLDOWN_DAYS", "14"))
        self.max_applications_per_company_per_month = int(
            os.getenv("MAX_APPLICATIONS_PER_COMPANY_PER_MONTH", "2")
        )
        self.llm_provider = os.getenv("LLM_PROVIDER", "offline")


@lru_cache
def get_settings() -> Settings:
    return Settings()


ATS_POLICY = {
    "layout": "single_column",
    "forbidden_elements": [
        "tables",
        "icons",
        "charts",
        "graphics",
        "progress_bars",
        "text_as_image",
    ],
    "required_headings": ["Summary", "Skills", "Projects", "Education"],
    "max_pages": 1,
    "llm_can_modify_template": False,
    "llm_output_format": "json_only",
}

