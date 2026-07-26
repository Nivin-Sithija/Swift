# Synthetic Banking Support Screenshot Dataset

This project creates 500 deterministic, fictional mobile-banking screenshots and
ground-truth labels for vision-language model testing. It uses **Nova Mobile
Banking**, a made-up identity, and contains no real bank names, logos, accounts,
customers, or personal information.

## Contents

- `generate_dataset.py` — modular generator and validator
- `requirements.txt` — Pillow dependency
- `screenshots/` — 500 PNG mobile screenshots (720 × 1280)
- `labels.json` — one ground-truth object per screenshot
- `preview_grid.png` — a grid of 20 examples

The data covers 15 banking-support categories and English, Sinhala, Tamil,
Singlish, Tanglish, and mixed-language messages. Layout, amount, currency,
date/time, reference, error code, font size, position, background, status, and
light pixel noise vary. Generation uses the fixed seed `20260724`.

## Setup and generation

Python 3.10 or newer is recommended.

```bash
cd synthetic_ticket_dataset
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 generate_dataset.py
```

The command replaces files matching `screenshots/synthetic_bank_*.png`, writes
`labels.json` and `preview_grid.png`, and then validates the complete result.
It prints progress, category/language distributions, and a `Validation: PASS`
message when successful.

To validate an existing dataset without regenerating it:

```bash
python3 generate_dataset.py --validate-only
```

Optional reproducibility arguments:

```bash
python3 generate_dataset.py --count 500 --seed 20260724
```

For the required dataset, keep `--count 500`. A different count is useful only
for development.

## Fonts

The generator searches common Linux locations for Noto Sinhala, Noto Tamil,
DejaVu, and Cantarell fonts. When a script font is missing, it prints a clear
warning and falls back to the best available Latin font or Pillow's default
font. Install the Noto Sinhala and Tamil font packages for correct native-script
glyph shaping on systems that do not already include them.

## Labels

Every object in `labels.json` includes the relative image path, category,
priority, sentiment, language, all intended visible text, error code, expected
image summary, issue clues, and priority clues. Priorities follow the requested
policy: security threats are critical; missing cash and duplicate transactions
are high; disrupted transfers/payments are medium; general informational issues
are low.

## Validation

Validation fails with a non-zero exit status unless:

- exactly the requested number of PNGs and labels exist;
- every label contains all required fields and a unique matching image;
- every category and language is represented;
- all required files are non-empty;
- every screenshot opens as a valid 720 × 1280 PNG; and
- the preview grid exists and is non-empty.

All content is synthetic. Do not treat generated references, dates, error codes,
amounts, or support messages as records of real financial activity.
