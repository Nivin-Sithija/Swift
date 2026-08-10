from __future__ import annotations

from dataclasses import dataclass

DEFAULT_MAX_CHARS = 1500


@dataclass
class Chunk:
    source_id: str
    chunk_index: int
    content: str
    section_path: str
    char_start: int
    char_end: int


def _heading(line: str) -> tuple[int, str] | None:
    """('## Fees' -> (2, 'Fees')) if line is a Markdown heading, else None."""
    stripped = line.lstrip("#")
    level = len(line) - len(stripped)
    if 1 <= level <= 6 and stripped.startswith(" "):
        return level, stripped.strip()
    return None


def chunk_document(text: str, source_id: str, max_chars: int = DEFAULT_MAX_CHARS) -> list[Chunk]:
    """Split on structure (headings, paragraphs) — never fixed character counts.

    Loaders emit Markdown-style '#' headings (see loaders/html.py); this walks
    blank-line-separated blocks, tracks a heading stack for section_path, and
    only splits a section into multiple chunks when it exceeds max_chars.
    """
    heading_stack: list[tuple[int, str]] = []
    chunks: list[Chunk] = []
    buffer_parts: list[str] = []
    buffer_start: int | None = None
    cursor = 0

    def section_path() -> str:
        return " > ".join(title for _, title in heading_stack)

    def flush(end: int) -> None:
        nonlocal buffer_parts, buffer_start
        content = "\n\n".join(buffer_parts).strip()
        if content:
            chunks.append(
                Chunk(
                    source_id=source_id,
                    chunk_index=len(chunks),
                    content=content,
                    section_path=section_path(),
                    char_start=buffer_start if buffer_start is not None else end,
                    char_end=end,
                )
            )
        buffer_parts = []
        buffer_start = None

    for block in text.split("\n\n"):
        block_start = cursor
        cursor += len(block) + 2

        stripped = block.strip()
        if not stripped:
            continue

        heading = _heading(stripped)
        if heading is not None:
            flush(block_start)
            level, title = heading
            heading_stack = [h for h in heading_stack if h[0] < level]
            heading_stack.append((level, title))
            continue

        projected_len = sum(len(p) for p in buffer_parts) + len(stripped)
        if buffer_parts and projected_len > max_chars:
            flush(block_start)

        if buffer_start is None:
            buffer_start = block_start
        buffer_parts.append(stripped)

    flush(len(text))
    return chunks
