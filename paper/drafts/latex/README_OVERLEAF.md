# Overleaf upload

```bash
cd paper/drafts
zip -r icatc-submission.zip latex
```

Overleaf: **New Project > Upload Project**, drop the zip in. Then Menu (top
left): **Compiler pdfLaTeX**, **Main document main.tex**, **TeX Live 2021 or
later**. Nothing else to configure; BibTeX runs automatically.

## Contents

```
main.tex                        preamble, title, blind toggle, includes
sections/                       one .tex per section, in reading order
figures/encoder_gain_by_script.pdf
refs.bib                        GENERATED -- see below
make_refs.py                    regenerates refs.bib
COMPLIANCE.md                   IEEE + ICATC conformance record, with re-checks
ICATC2026_submission_preview.pdf   6-page clean-mode build
```

| File | Section |
|---|---|
| `00_abstract.tex` | Abstract |
| `01_introduction.tex` | I. Introduction |
| `02_related_work.tex` | II. Related Work |
| `03_corpus.tex` | III. The Corpus |
| `04_methodology.tex` | IV. Methodology |
| `05_results.tex` | V. Roster Results |
| `06_script.tex` | VI. The Transfer Boundary Is Orthographic |
| `07_queue.tex` | VII. From Labels to a Queue |
| `08_discussion.tex` | VIII. Discussion and Limitations |
| `09_conclusion.tex` | IX. Conclusion |
| `10_acknowledgment.tex` | AI disclosure (IEEE policy) |

## Two switches in main.tex

**`\blindtrue`** (line ~41) removes the author block, the personal
acknowledgment, and every repository URL. **Keep it true for the CMT
submission.** Flip to `\blindfalse` only for the camera-ready, and fill in the
real author block, which is currently a placeholder.

**`\draftmodetrue`** (line ~46) shows `\gap` and `\note` markers in colour.
**The page count is only valid with `\draftmodefalse`**, so set it false before
you check length or export the submission PDF.

## Length

6 pages in clean mode, against a 4-6 page limit. There is no slack. Anything you
add has to displace something else. The levers used to get here, in case you
need one back: the tokenizer figure was cut (its numbers are all stated in
Section VI prose), and five marginal citations were dropped.

## Do not hand-edit refs.bib

It is generated. `paper/bibliography/refs.bib` is the record of source and
carries internal `note` fields whose underscores abort the build when
IEEEtran.bst prints them. Regenerate instead:

```bash
python3 make_refs.py
```

BibTeX emits only cited entries, so all 49 stay available while the manuscript
cites 28.

## Fonts

`main.tex` loads `newtxtext,newtxmath` deliberately. Removing them makes the
paper typeset in Latin Modern instead of Times under Unicode engines, with no
error. See COMPLIANCE.md.

## Numbers

Every value traces to a generated file under `paper/results/`. Nothing was
transcribed by hand. If a number here disagrees with `results.md`, the generated
CSV wins.
