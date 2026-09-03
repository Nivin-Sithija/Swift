import re
from collections import defaultdict

from app.rag.types import Citation, Evidence

MARKER = re.compile(r"\[E(\d+)\]")
SAFETY_DISCLAIMER = re.compile(
    r"general policy guidance.*(?:does not|not).*confirm.*(?:account|transaction)",
    re.IGNORECASE | re.DOTALL,
)


def build_citations(answer: str, evidence: list[Evidence]) -> list[Citation]:
    indexes = sorted({int(value) for value in MARKER.findall(answer)})
    grouped: dict[str, list[tuple[int, Evidence]]] = defaultdict(list)
    for index in indexes:
        if 1 <= index <= len(evidence):
            grouped[evidence[index - 1].source_id].append((index, evidence[index - 1]))
    citations = []
    for source_items in grouped.values():
        first_index, first = source_items[0]
        citations.append(
            Citation(
                marker=f"E{first_index}",
                source_id=first.source_id,
                title=first.title,
                institution=first.institution,
                url=first.source_url,
                version=first.version,
                review_date=first.review_date,
                chunk_ids=tuple(item.chunk_id for _, item in source_items),
            )
        )
    return citations


def citations_are_valid(answer: str, evidence: list[Evidence]) -> bool:
    markers = [int(value) for value in MARKER.findall(answer)]
    if not markers or any(index < 1 or index > len(evidence) for index in markers):
        return False

    def is_heading(block: str) -> bool:
        stripped = block.strip().lstrip("#").strip()
        return "\n" not in stripped and len(stripped) <= 120 and stripped.endswith(":")

    factual_blocks = [
        block
        for block in re.split(r"\n\s*\n", answer)
        if block.strip() and not SAFETY_DISCLAIMER.search(block) and not is_heading(block)
    ]
    return all(MARKER.search(block) for block in factual_blocks)
