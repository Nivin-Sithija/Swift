from __future__ import annotations

from bs4 import BeautifulSoup

# Headings are re-emitted as Markdown '#' prefixes so chunking can recover
# document structure (section_path) from plain text — see chunking/splitter.py.
_HEADING_PREFIXES = {"h1": "#", "h2": "##", "h3": "###", "h4": "####", "h5": "#####", "h6": "######"}
_BLOCK_TAGS = list(_HEADING_PREFIXES) + ["p", "li"]


def parse_html(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    for tag in soup(["script", "style", "meta", "noscript"]):
        tag.decompose()

    lines: list[str] = []
    for el in soup.find_all(_BLOCK_TAGS):
        text = el.get_text(" ", strip=True)
        if not text:
            continue
        prefix = _HEADING_PREFIXES.get(el.name)
        lines.append(f"{prefix} {text}" if prefix else text)

    return "\n\n".join(lines)
