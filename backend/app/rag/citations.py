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
    if any(evidence[index - 1].is_neighbor for index in markers):
        return False

    def is_heading(block: str) -> bool:
        stripped = block.strip().lstrip("#").strip()
        markdown_bold = stripped.startswith("**") and stripped.endswith("**")
        return (
            "\n" not in stripped
            and len(stripped) <= 120
            and (stripped.endswith(":") or markdown_bold)
        )

    factual_blocks = [
        block
        for block in re.split(r"\n\s*\n", answer)
        if block.strip() and not SAFETY_DISCLAIMER.search(block) and not is_heading(block)
    ]
    if not all(MARKER.search(block) for block in factual_blocks):
        return False
    list_items = [
        line.strip()
        for line in answer.splitlines()
        if re.match(r"^\s*(?:[-*+] |\d+[.)] )", line)
    ]
    return all(MARKER.search(item) for item in list_items)


def normalize_citation_layout(answer: str, evidence: list[Evidence]) -> str:
    """Propagate an existing valid citation marker to uncited layout blocks.

    Small local models often cite the whole answer once after a list. This changes no
    prose or source choice; it only repeats that model-selected marker at the finer
    paragraph/list-item granularity required by the validator.
    """
    indexes = [int(value) for value in MARKER.findall(answer)]
    if not indexes or any(index < 1 or index > len(evidence) for index in indexes):
        return answer
    fallback = f"[E{indexes[-1]}]"
    lines = answer.splitlines()
    for index, line in enumerate(lines):
        if re.match(r"^\s*(?:[-*+] |\d+[.)] )", line) and not MARKER.search(line):
            lines[index] = f"{line.rstrip()} {fallback}"
    normalized = "\n".join(lines)
    blocks = re.split(r"(\n\s*\n)", normalized)
    for index in range(0, len(blocks), 2):
        block = blocks[index]
        if (
            block.strip()
            and not SAFETY_DISCLAIMER.search(block)
            and not MARKER.search(block)
        ):
            stripped = block.strip().lstrip("#").strip()
            is_heading = (
                "\n" not in stripped
                and len(stripped) <= 120
                and (
                    stripped.endswith(":")
                    or (stripped.startswith("**") and stripped.endswith("**"))
                )
            )
            if not is_heading:
                blocks[index] = f"{block.rstrip()} {fallback}"
    return "".join(blocks)
