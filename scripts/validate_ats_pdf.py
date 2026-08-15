from pathlib import Path
import json
import sys

from app.services.ats_validator import validate_ats_pdf


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/validate_ats_pdf.py path/to/resume.pdf")
        return 1
    result = validate_ats_pdf(Path(sys.argv[1]))
    print(json.dumps(result.model_dump(), indent=2))
    return 0 if result.passed else 2


if __name__ == "__main__":
    raise SystemExit(main())

