import os
import sys
from pathlib import Path

import requests

API_URL = "http://localhost:8000"
SAMPLES_DIR = Path(__file__).parent.parent / "data" / "samples"


def seed():
    pdfs = list(SAMPLES_DIR.glob("*.pdf"))

    if not pdfs:
        print("No PDFs found in data/samples/ — add some PDFs first")
        sys.exit(1)

    print(f"Found {len(pdfs)} PDF(s) to upload")

    for pdf_path in pdfs:
        with open(pdf_path, "rb") as f:
            response = requests.post(
                f"{API_URL}/documents/",
                files={"file": (pdf_path.name, f, "application/pdf")},
            )

        if response.status_code == 202:
            data = response.json()
            print(f"Uploaded: {pdf_path.name} → id={data['id']}")
        else:
            print(f"Failed:   {pdf_path.name} → {response.status_code} {response.text}")


if __name__ == "__main__":
    seed()