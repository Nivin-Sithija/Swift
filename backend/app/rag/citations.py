import re
from collections import defaultdict

from app.rag.types import Citation, Evidence

MARKER = re.compile(r"\[E(\d+)\]")


def build_citations(answer: str, evidence: list[Evidence]) -> list[Citation]:
    indexes = sorted({int(value) for value in MARKER.findall(answer)})
    grouped: dict[str, list[tuple[int, Evidence]]] = defaultdict(list)
    for index in indexes:
        if 1 <= index <= len(evidence):
            grouped[evidence[index - 1].source_id].append((index, evidence[index - 1]))
    citations = []
    for source_items in grouped.values():
        first_index, first = source_items[0]
        citations.append(Citation(
            marker=f"E{first_index}", source_id=first.source_id, title=first.title,
            institution=first.institution, url=first.source_url, version=first.version,
            review_date=first.review_date, chunk_ids=tuple(item.chunk_id for _, item in source_items),
        ))
    return citations


def citations_are_valid(answer: str, evidence: list[Evidence]) -> bool:
    markers = [int(value) for value in MARKER.findall(answer)]
    if not markers or any(index < 1 or index > len(evidence) for index in markers):
        return False
    factual_lines = [line for line in answer.splitlines() if line.strip()]
    return all(MARKER.search(line) for line in factual_lines)
