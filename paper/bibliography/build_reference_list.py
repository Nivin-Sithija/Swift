"""Generate a human-readable reference list from refs.bib.

    python paper/bibliography/build_reference_list.py

Regenerate after editing refs.bib -- REFERENCES.md is derived, never hand-edited,
so the two cannot drift. Grouping follows the `% ===` section banners in the .bib.
"""
from __future__ import annotations
import re
from pathlib import Path

BIB = Path(__file__).with_name("refs.bib")
OUT = Path(__file__).with_name("REFERENCES.md")


def fields(body: str) -> dict[str, str]:
    """Pull `key = {value}` pairs, tracking brace depth so nested braces survive."""
    out, i = {}, 0
    while i < len(body):
        m = re.compile(r"(\w+)\s*=\s*").match(body, i)
        if not m:
            i += 1
            continue
        key, j = m.group(1).lower(), m.end()
        if body[j] == "{":
            depth, k = 0, j
            while k < len(body):
                if body[k] == "{":
                    depth += 1
                elif body[k] == "}":
                    depth -= 1
                    if depth == 0:
                        break
                k += 1
            val, i = body[j + 1:k], k + 1
        else:
            k = body.find(",", j)
            k = len(body) if k < 0 else k
            val, i = body[j:k].strip(), k
        out[key] = re.sub(r"\s+", " ", val).strip()
    return out


GREEK = {"mu": "\u03bc", "lambda": "\u03bb", "alpha": "\u03b1", "beta": "\u03b2",
         "rho": "\u03c1", "sigma": "\u03c3", "kappa": "\u03ba", "tau": "\u03c4"}


def clean(s: str) -> str:
    """Strip the LaTeX that makes a .bib unreadable as prose."""
    s = re.sub(r"\{\\['\"`^~=.]\{?(\w)\}?\}", r"\1", s)      # accents: {\'e} -> e
    # Math mode: $\mu$ -> the actual letter, before macros are stripped wholesale.
    s = re.sub(r"\$([^$]*)\$", lambda m: m.group(1), s)
    for name, ch in GREEK.items():
        s = s.replace("\\" + name, ch)
    s = s.replace("\\,", "").replace("\\&", "&")            # thin space, escaped ampersand
    s = re.sub(r"\\[a-zA-Z]+\s*", "", s)                      # any remaining macros
    return s.replace("{", "").replace("}", "").replace("\\", "").strip()


def authors(raw: str) -> str:
    names = [clean(a).strip() for a in raw.split(" and ")]
    names = [n.split(",")[0].strip() if "," in n else n.split()[-1] for n in names if n]
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} & {names[1]}"
    return f"{names[0]} et al."


def main() -> int:
    text = BIB.read_text()
    # Section banners: a %=== rule, then % <title>, then another %=== rule.
    banner = re.compile(r"% ={20,}\n% (.+?)\n% ={20,}")
    marks = [(m.start(), clean(m.group(1)).rstrip(".")) for m in banner.finditer(text)]

    def section_of(pos: int) -> str:
        cur = "Uncategorised"
        for start, title in marks:
            if start < pos:
                cur = title
            else:
                break
        return cur

    entries = []
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,]+),", text):
        depth, k = 0, text.index("{", m.start())
        while k < len(text):
            if text[k] == "{":
                depth += 1
            elif text[k] == "}":
                depth -= 1
                if depth == 0:
                    break
            k += 1
        f = fields(text[m.end():k])
        entries.append({"key": m.group(2).strip(), "type": m.group(1),
                        "sec": section_of(m.start()), **f})

    # Several sections carry [VERIFIED] on the banner rather than on every entry.
    # Inherit it, otherwise a dozen checked references render as unknown status.
    for e in entries:
        note, sec = e.get("note", ""), e["sec"]
        e["status"] = ("to-verify" if "[TO VERIFY]" in note
                       else "verified" if "[VERIFIED]" in note or "[VERIFIED]" in sec
                       else "unknown")
    verified = sum(1 for e in entries if e["status"] == "verified")
    toverify = sum(1 for e in entries if e["status"] == "to-verify")
    unknown = sum(1 for e in entries if e["status"] == "unknown")

    L = [f"# Reference list — {len(entries)} entries",
         "",
         "**Generated file — do not edit.** Produced by `build_reference_list.py` from",
         "`refs.bib`; rerun that script after changing the bibliography.",
         "",
         f"- ✅ **{verified}** checked against the publisher record (`[VERIFIED]`)",
         f"- ⚠️ **{toverify}** added from working knowledge, **not yet checked** (`[TO VERIFY]`)"]
    if unknown:
        L.append(f"- ❓ **{unknown}** no verification status recorded")
    L.append("")
    if toverify:
        L += ["> The `[TO VERIFY]` entries must be confirmed against the publisher record",
              "> before submission. Of the entries checked in an earlier pass, three carried",
              "> real errors (a truncated title, an elided author list, missing pages), so",
              "> this is a live risk rather than a formality.", ""]
    L += ["---", ""]

    order, seen = [], set()
    for e in entries:
        if e["sec"] not in seen:
            seen.add(e["sec"])
            order.append(e["sec"])

    for sec in order:
        rows = [e for e in entries if e["sec"] == sec]
        L += [f"## {sec.replace(' -- [VERIFIED]', '')}  ({len(rows)})", ""]
        for e in sorted(rows, key=lambda x: (x.get("year", ""), x["key"])):
            venue = (e.get("journal") or e.get("booktitle") or e.get("institution")
                     or e.get("publisher") or ("arXiv" if e.get("eprint") else ""))
            bits = [clean(venue)]
            if e.get("volume"):
                bits.append(f"vol. {e['volume']}"
                            + (f"({e['number']})" if e.get("number") else ""))
            if e.get("pages"):
                bits.append(f"pp. {e['pages'].replace('--', '–')}")
            if e.get("eprint"):
                bits.append(f"arXiv:{e['eprint']}")
            meta = ", ".join(b for b in bits if b)
            status = {"verified": "✅", "to-verify": "⚠️"}.get(e["status"], "❓")
            L.append(f"### {status} `{e['key']}`")
            L.append("")
            L.append(f"**{authors(e.get('author',''))} ({e.get('year','n.d.')}).** "
                     f"*{clean(e.get('title','—'))}.*")
            if meta:
                L.append(f"{meta}.")
            if e.get("doi"):
                L.append(f"DOI: [{e['doi']}](https://doi.org/{e['doi']})")
            note = clean(re.sub(r"\[(VERIFIED|TO VERIFY)\]\s*", "", e.get("note", "")))
            if note:
                L.append("")
                L.append(f"> **Cited for:** {note}")
            L.append("")
        L.append("---")
        L.append("")

    OUT.write_text("\n".join(L))
    print(f"{len(entries)} entries -> {OUT.relative_to(Path.cwd())}"
          f"   ({verified} verified, {toverify} to verify)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
