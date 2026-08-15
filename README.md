# Job Application Assistant

Local-first, human-approved job application assistant for reviewing many jobs, ranking fit, generating truthful ATS-safe resumes, and tracking applications.

This project is not a LinkedIn automation bot. It does not scrape LinkedIn, auto-click Easy Apply, auto-fill forms, send messages, bypass bot detection, or submit applications.

## Core Guarantees

- Human approval is required before marking a job as applied.
- Resume content must pass the Truth Layer.
- PDF resumes must pass ATS validation before use.
- LLM output is limited to structured content, not layout or PDF rules.
- Generated personal files stay local and are gitignored.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp data/candidate_profile.example.json data/candidate_profile.json
```

Edit `data/candidate_profile.json` with your real information.

## First Run

```bash
job-assistant init-db
job-assistant profile validate --profile data/candidate_profile.json
job-assistant add-job --input data/sample_job.txt --source manual
```

Copy the printed job id, then run:

```bash
job-assistant parse-job --job-id JOB_ID
job-assistant score-job --job-id JOB_ID
job-assistant tailor-resume --job-id JOB_ID
job-assistant generate-cover-letter --job-id JOB_ID
job-assistant generate-message --job-id JOB_ID
job-assistant mark-applied --job-id JOB_ID
```

`mark-applied` requires typing `APPLY` to confirm that you manually submitted the application.

## Batch Links

Create `data/job_links.txt`:

```text
https://boards.greenhouse.io/company/jobs/123
https://jobs.lever.co/company/job
https://www.linkedin.com/jobs/view/123
```

Import:

```bash
job-assistant import-links --input data/job_links.txt
```

LinkedIn links are stored as high-risk and require manual job text. They are not scraped.

## ATS Validation

```bash
job-assistant validate-resume --resume outputs/resumes/example.pdf
python scripts/validate_ats_pdf.py outputs/resumes/example.pdf
```

The validator checks that the PDF opens, text can be extracted, required headings exist, and the page count respects the configured limit.

## Tests

```bash
pytest
```

