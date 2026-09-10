#!/usr/bin/env python3
"""Generate the build's refs.bib from the project's verified bibliography.

`paper/bibliography/refs.bib` is the record of source. It carries internal
`note = {...}` fields documenting how each entry was verified, and those notes
contain underscores that IEEEtran.bst prints straight into the .bbl, where they
land in text mode and abort the build.

This strips the notes and escapes what survives. BibTeX emits only cited
entries, so the full file can stay here even though the 6-page manuscript cites
a subset.

    python3 make_refs.py
"""
from __future__ import annotations

import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent.parent / "bibliography" / "refs.bib"
TARGET = HERE / "refs.bib"
NOTE = re.compile(r"^\s*note\s*=\s*\{", re.IGNORECASE)


def strip_notes(text: str) -> str:
    out, depth = [], 0
    for line in text.splitlines(keepends=True):
        if depth == 0:
            if NOTE.match(line):
                depth = line.count("{") - line.count("}")
                continue
            out.append(line)
        else:
            depth += line.count("{") - line.count("}")
    return "".join(out)


def escape_underscores(text: str) -> str:
    out = []
    for line in text.splitlines(keepends=True):
        if line.lstrip().startswith("%") or "_" not in line or "=" not in line:
            out.append(line)
            continue
        key, _, value = line.partition("=")
        out.append(f"{key}={re.sub(r'(?<!\\)_', r'\\_', value)}")
    return "".join(out)


def main() -> None:
    cleaned = escape_underscores(strip_notes(SOURCE.read_text(encoding="utf-8")))
    header = ("% GENERATED FILE -- do not edit.\n"
              "% Source: paper/bibliography/refs.bib\n"
              "% Regenerate with: python3 make_refs.py\n\n")
    TARGET.write_text(header + cleaned, encoding="utf-8")
    print(f"wrote refs.bib -- {len(re.findall(r'^@', cleaned, re.M))} entries available")


if __name__ == "__main__":
    main()
