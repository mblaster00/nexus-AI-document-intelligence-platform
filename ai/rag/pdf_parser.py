from dataclasses import dataclass
from pathlib import Path

import pdfplumber
import structlog

logger = structlog.get_logger()


@dataclass
class ParsedPage:
    page_number: int
    text: str


@dataclass
class ParsedDocument:
    document_id: str
    pages: list[ParsedPage]
    total_pages: int

    @property
    def full_text(self) -> str:
        return "\n\n".join(page.text for page in self.pages if page.text.strip())


def parse_pdf(file_path: str, document_id: str) -> ParsedDocument:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    pages = []

    with pdfplumber.open(path) as pdf:
        total_pages = len(pdf.pages)

        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""

            pages.append(ParsedPage(
                page_number=i + 1,
                text=text,
            ))

    logger.info(
        "pdf_parsed",
        document_id=document_id,
        total_pages=total_pages,
        non_empty_pages=sum(1 for p in pages if p.text.strip()),
    )

    return ParsedDocument(
        document_id=document_id,
        pages=pages,
        total_pages=total_pages,
    )