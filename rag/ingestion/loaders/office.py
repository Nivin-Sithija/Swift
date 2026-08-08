from __future__ import annotations

from unstructured.partition.auto import partition


def parse_office(file_path: str) -> str:
    """Parse .docx / .pptx via Unstructured — auto-detects format, no per-type branching needed."""
    elements = partition(filename=file_path)
    return "\n\n".join(str(el) for el in elements)
