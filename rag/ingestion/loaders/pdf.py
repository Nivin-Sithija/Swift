from __future__ import annotations

from pypdf import PdfReader


def parse_pdf(file_path: str) -> str:
    """Extract text locally with pypdf; fall back to pdfplumber for pages pypdf returns blank."""
    reader = PdfReader(file_path)

    text_parts: list[str] = []
    blank_pages: list[int] = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            text_parts.append(text)
        else:
            blank_pages.append(i)

    if blank_pages:
        import pdfplumber

        with pdfplumber.open(file_path) as pdf:
            for page_num in blank_pages:
                fallback_text = pdf.pages[page_num].extract_text() or ""
                if fallback_text.strip():
                    text_parts.append(fallback_text)

    return "\n\n".join(text_parts)
