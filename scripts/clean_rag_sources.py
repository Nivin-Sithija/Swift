#!/usr/bin/env python3
"""Clean validated RAG HTML sources into focused Markdown documents."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from bs4 import BeautifulSoup, NavigableString, Tag


ROOT = Path(__file__).resolve().parents[1]
RAG_DIR = ROOT / "docs" / "rag_sources"
DOCUMENTS_DIR = RAG_DIR / "documents"
RAW_DIR = DOCUMENTS_DIR / "raw"
CLEANED_DIR = DOCUMENTS_DIR / "cleaned"
MANIFEST_PATH = RAG_DIR / "rag_source_manifest.csv"
REPORT_PATH = RAG_DIR / "source_validation_report.md"
RETRIEVAL_DATE = "2026-07-29"
VERSION = "1.0"
MIN_WORDS = 100

CONTENT_SELECTORS = {
    "accounts_combank_regular_savings.html": ".editor-content",
    "cards_combank_dispute_policy.html": ".editor-content",
    "fraud_cbsl_online_scams.html": "#article-6952",
    "loans_peoples_bank_pahasu.html": "#Pahasu_Loan",
    "transfers_combank_card_to_card.html": ".editor-content",
}

DROP_TAGS = {
    "script",
    "style",
    "nav",
    "header",
    "footer",
    "form",
    "noscript",
    "template",
    "svg",
    "canvas",
    "iframe",
    "button",
}
NOISE_PATTERN = re.compile(
    r"(?:^|[-_ ])(?:menu|navbar|navigation|breadcrumb|cookie|consent|popup|modal|"
    r"social|share|toolbar|sidebar|pagination|newsletter|search|language-switch|"
    r"related-content|download-app)(?:$|[-_ ])",
    re.IGNORECASE,
)
NAV_TERMS = {
    "home",
    "about us",
    "contact us",
    "personal banking",
    "business banking",
    "corporate banking",
    "login",
    "search",
    "privacy policy",
    "terms and conditions",
}
BLOCK_TAGS = {
    "address",
    "article",
    "aside",
    "blockquote",
    "div",
    "dl",
    "fieldset",
    "figure",
    "figcaption",
    "main",
    "p",
    "section",
    "table",
}


@dataclass
class Result:
    source_id: str
    filename: str
    title: str
    selector: str
    raw_words: int
    main_words: int
    cleaned_words: int
    removed_tags: int
    removed_words: int
    repeated_links_removed: int
    nav_term_hits: int
    checksum: str
    status: str
    reason: str


def words(text: str) -> list[str]:
    return re.findall(r"\b[\w’'-]+\b", text, flags=re.UNICODE)


def normalized_text(node: Tag | BeautifulSoup) -> str:
    return re.sub(r"\s+", " ", node.get_text(" ", strip=True)).strip()


def yaml_string(value: str) -> str:
    # JSON strings are valid quoted YAML scalars and safely handle punctuation.
    return json.dumps(value, ensure_ascii=False)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_raw_file(filename: str) -> Path | None:
    raw_path = RAW_DIR / filename
    if raw_path.exists():
        return raw_path
    legacy_path = DOCUMENTS_DIR / filename
    if legacy_path.exists():
        return legacy_path
    return None


def noise_signature(tag: Tag) -> str:
    classes = " ".join(str(value) for value in tag.get("class", []))
    return f"{tag.get('id', '')} {classes}".strip()


def remove_noise(soup: BeautifulSoup) -> tuple[int, int]:
    removed_tags = 0
    removed_words = 0
    targets: list[Tag] = list(soup.find_all(DROP_TAGS))
    for tag in soup.find_all(True):
        if NOISE_PATTERN.search(noise_signature(tag)):
            targets.append(tag)

    seen: set[int] = set()
    for tag in targets:
        if id(tag) in seen or tag.parent is None:
            continue
        # Do not count descendants again after their parent is removed.
        descendants = {id(item) for item in tag.find_all(True)}
        seen.add(id(tag))
        seen.update(descendants)
        removed_tags += 1 + len(descendants)
        removed_words += len(words(normalized_text(tag)))
        tag.decompose()
    return removed_tags, removed_words


def remove_repeated_links(root: Tag) -> int:
    seen: set[tuple[str, str]] = set()
    removed = 0
    for link in list(root.find_all("a")):
        label = re.sub(r"\s+", " ", link.get_text(" ", strip=True)).casefold()
        href = (link.get("href") or "").strip()
        key = (label, href)
        if key in seen:
            link.decompose()
            removed += 1
        else:
            seen.add(key)
    return removed


def inline_markdown(node: Tag | NavigableString) -> str:
    if isinstance(node, NavigableString):
        return html.unescape(str(node))
    if not isinstance(node, Tag):
        return ""
    inner = "".join(inline_markdown(child) for child in node.children)
    inner = re.sub(r"[ \t\r\f\v]+", " ", inner)
    name = node.name.lower()
    if name in {"strong", "b"} and inner.strip():
        return f"**{inner.strip()}**"
    if name in {"em", "i"} and inner.strip():
        return f"*{inner.strip()}*"
    if name == "code" and inner.strip():
        return f"`{inner.strip()}`"
    if name == "br":
        return "\n"
    if name == "a":
        label = inner.strip()
        href = (node.get("href") or "").strip()
        if label and href.startswith(("http://", "https://")):
            return f"[{label}]({href})"
        return label
    return inner


def table_markdown(table: Tag) -> str:
    rows: list[list[str]] = []
    for row in table.find_all("tr"):
        cells = [
            re.sub(r"\s+", " ", inline_markdown(cell)).strip()
            for cell in row.find_all(["th", "td"], recursive=False)
        ]
        if cells:
            rows.append(cells)
    if not rows:
        return ""
    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]
    header = rows[0]
    output = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in range(width)) + " |",
    ]
    output.extend("| " + " | ".join(row) + " |" for row in rows[1:])
    return "\n".join(output)


def list_markdown(tag: Tag, depth: int = 0) -> str:
    lines: list[str] = []
    ordered = tag.name == "ol"
    number = 1
    for item in tag.find_all("li", recursive=False):
        direct_parts: list[str] = []
        nested: list[Tag] = []
        for child in item.children:
            if isinstance(child, Tag) and child.name in {"ul", "ol"}:
                nested.append(child)
            else:
                direct_parts.append(inline_markdown(child))
        text = re.sub(r"\s+", " ", "".join(direct_parts)).strip()
        marker = f"{number}." if ordered else "-"
        if text:
            lines.append(f"{'  ' * depth}{marker} {text}")
        for child_list in nested:
            lines.append(list_markdown(child_list, depth + 1))
        number += 1
    return "\n".join(line for line in lines if line)


def block_markdown(root: Tag) -> str:
    blocks: list[str] = []

    def visit(node: Tag) -> None:
        for child in node.children:
            if not isinstance(child, Tag):
                continue
            name = child.name.lower()
            if re.fullmatch(r"h[1-6]", name):
                text = re.sub(r"\s+", " ", inline_markdown(child)).strip()
                if text:
                    blocks.append(f"{'#' * int(name[1])} {text}")
            elif name in {"ul", "ol"}:
                rendered = list_markdown(child)
                if rendered:
                    blocks.append(rendered)
            elif name == "table":
                rendered = table_markdown(child)
                if rendered:
                    blocks.append(rendered)
            elif name in {"p", "h7", "blockquote", "address", "figcaption"}:
                text = re.sub(r"[ \t]+", " ", inline_markdown(child)).strip()
                if text:
                    prefix = "> " if name == "blockquote" else ""
                    blocks.append(prefix + text)
            elif name in BLOCK_TAGS:
                visit(child)
            elif not child.find(BLOCK_TAGS | {"ul", "ol"}):
                text = re.sub(r"\s+", " ", inline_markdown(child)).strip()
                if text:
                    blocks.append(text)
            else:
                visit(child)

    visit(root)
    deduplicated: list[str] = []
    seen: set[str] = set()
    for block in blocks:
        key = re.sub(r"\W+", " ", block).strip().casefold()
        if key and key not in seen:
            seen.add(key)
            deduplicated.append(block)
    return "\n\n".join(deduplicated).strip()


def clean_source(row: dict[str, str], raw_path: Path) -> tuple[str, Result]:
    raw_html = raw_path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(raw_html, "html.parser")
    detected_title = (
        soup.title.get_text(" ", strip=True) if soup.title else row["title"]
    )
    raw_word_count = len(words(normalized_text(soup)))
    removed_tags, _ = remove_noise(soup)
    selector = CONTENT_SELECTORS.get(raw_path.name, "main, article")
    main = soup.select_one(selector)
    if main is None:
        result = Result(
            row["source_id"], raw_path.name, detected_title, selector,
            raw_word_count, 0, 0, removed_tags, removed_words, 0, 0,
            sha256(raw_path), "REJECTED", f"main selector not found: {selector}",
        )
        return "", result

    for menu in list(main.select('[role="menu"], .text-bar3, .tabs, .tab-menu')):
        if menu.parent is not None:
            removed_tags += 1 + len(menu.find_all(True))
            menu.decompose()
    main_word_count = len(words(normalized_text(main)))
    # This is the useful corpus statistic: words excluded from the selected main
    # content, rather than a sum over nested removed DOM nodes.
    removed_words = max(raw_word_count - main_word_count, 0)
    repeated_links = remove_repeated_links(main)
    markdown_body = block_markdown(main)
    cleaned_word_count = len(words(markdown_body))
    lowered = markdown_body.casefold()
    nav_hits = sum(lowered.count(term) for term in NAV_TERMS)
    nav_ratio = nav_hits / max(cleaned_word_count, 1)

    reasons: list[str] = []
    if cleaned_word_count < MIN_WORDS:
        reasons.append(f"fewer than {MIN_WORDS} meaningful words")
    if nav_ratio > 0.05:
        reasons.append("content is mostly navigation")
    status = "REJECTED" if reasons else "VALID"
    reason = "; ".join(reasons) if reasons else "passed content validation"

    front_matter = "\n".join(
        [
            "---",
            f"title: {yaml_string(row['title'])}",
            f"organisation: {yaml_string(row['owner'])}",
            f"source_url: {yaml_string(row['source_url'])}",
            f"category: {yaml_string(row['category'])}",
            f"retrieval_date: {yaml_string(RETRIEVAL_DATE)}",
            "---",
            "",
        ]
    )
    body_lines: list[str] = []
    title_key = re.sub(r"\W+", " ", row["title"]).strip().casefold()
    duplicate_title_removed = False
    for line in markdown_body.splitlines():
        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading:
            heading_key = re.sub(r"\W+", " ", heading.group(2)).strip().casefold()
            if heading_key == title_key and not duplicate_title_removed:
                duplicate_title_removed = True
                continue
            if len(heading.group(1)) == 1:
                line = "#" + line
        body_lines.append(line)
    markdown_body = f"# {row['title']}\n\n" + "\n".join(body_lines).lstrip()
    output = front_matter + markdown_body.rstrip() + "\n"
    result = Result(
        row["source_id"], raw_path.name, detected_title, selector,
        raw_word_count, main_word_count, cleaned_word_count, removed_tags,
        removed_words, repeated_links, nav_hits, sha256(raw_path), status, reason,
    )
    return output, result


def read_manifest() -> tuple[list[str], list[dict[str, str]]]:
    with MANIFEST_PATH.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


def manifest_text(rows: list[dict[str, str]], fields: list[str]) -> str:
    from io import StringIO

    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def report_text(results: Iterable[Result]) -> str:
    results = list(results)
    valid = sum(result.status == "VALID" for result in results)
    lines = [
        "# RAG Source Validation Report",
        "",
        f"Processing date: {RETRIEVAL_DATE}",
        "",
        "## Summary",
        "",
        f"- Sources processed: {len(results)}",
        f"- Valid cleaned documents: {valid}",
        f"- Rejected cleaned documents: {len(results) - valid}",
        "- Minimum meaningful-word requirement: 100",
        "- Approval status: all sources remain `pending_internal_review`",
        "",
        "## Validation results",
        "",
        "| Source ID | Detected title | Raw words | Main words | Cleaned words | "
        "Removed tags | Removed words | Repeated links removed | SHA-256 | Result |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for result in results:
        title = result.title.replace("|", "\\|")
        lines.append(
            f"| `{result.source_id}` | {title} | {result.raw_words} | "
            f"{result.main_words} | {result.cleaned_words} | "
            f"{result.removed_tags} | {result.removed_words} | "
            f"{result.repeated_links_removed} | `{result.checksum}` | "
            f"**{result.status}** — {result.reason} |"
        )
    lines.extend(
        [
            "",
            "## Method",
            "",
            "The cleaner removes scripts, styles, navigation, headers, footers, forms, "
            "menus, cookie/consent elements, embedded content, and repeated links. "
            "It then selects the source-specific product or article container and "
            "retains headings, paragraphs, lists, useful links, and tables.",
            "",
            "A cleaned document is rejected when it contains fewer than 100 meaningful "
            "words or when navigation-term density indicates that the output is mostly "
            "navigation. Rejected content is not written to the cleaned directory or "
            "recorded as a cleaned manifest path.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="validate and preview actions without moving or writing files",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    fields, rows = read_manifest()
    checksum_field = "checksum"
    fields = [field for field in fields if field != "checksum_sha256"]
    if "cleaned_path" not in fields:
        local_index = fields.index("local_path") + 1
        fields.insert(local_index, "cleaned_path")
    if checksum_field not in fields:
        cleaned_index = fields.index("cleaned_path") + 1
        fields.insert(cleaned_index, checksum_field)

    results: list[Result] = []
    outputs: dict[Path, str] = {}
    missing: list[str] = []
    for row in rows:
        filename = Path(row["local_path"]).name
        raw_path = find_raw_file(filename)
        if raw_path is None:
            missing.append(filename)
            continue
        output, result = clean_source(row, raw_path)
        results.append(result)
        row["local_path"] = f"documents/raw/{filename}"
        row["cleaned_path"] = (
            f"documents/cleaned/{Path(filename).stem}.md"
            if result.status == "VALID"
            else ""
        )
        row[checksum_field] = result.checksum
        row.pop("checksum_sha256", None)
        row["last_reviewed"] = RETRIEVAL_DATE
        row["version"] = VERSION
        row["approval_status"] = "pending_internal_review"
        if result.status == "VALID":
            outputs[CLEANED_DIR / f"{Path(filename).stem}.md"] = output

    if missing:
        print("Missing input files: " + ", ".join(missing), file=sys.stderr)
        return 1

    for result in results:
        print(
            f"{result.status:8} {result.filename}: "
            f"{result.cleaned_words} cleaned words, {result.checksum}"
        )

    if args.dry_run:
        print(
            f"Dry run: would move/process {len(results)} raw files, write "
            f"{len(outputs)} Markdown files, and update the manifest and report."
        )
        return 0 if all(result.status == "VALID" for result in results) else 2

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)
    for result in results:
        source = DOCUMENTS_DIR / result.filename
        destination = RAW_DIR / result.filename
        if source.exists() and not destination.exists():
            shutil.move(str(source), str(destination))
    for path, content in outputs.items():
        path.write_text(content, encoding="utf-8")
    MANIFEST_PATH.write_text(manifest_text(rows, fields), encoding="utf-8")
    REPORT_PATH.write_text(report_text(results), encoding="utf-8")

    rejected = [result for result in results if result.status != "VALID"]
    print(f"Wrote {len(outputs)} cleaned documents and validation report.")
    return 2 if rejected else 0


if __name__ == "__main__":
    raise SystemExit(main())
