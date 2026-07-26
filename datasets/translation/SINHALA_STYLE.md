# Colloquial Sinhala Translation — Style Guide

The Sinhala dataset (`sinhala/sinhala_translation_progress.csv`) is
**colloquial, code-mixed spoken Sinhala** — the way Sri Lankans actually type
in a banking support chat — NOT formal/literary Sinhala. English banking terms
are kept in Sinhala script.

## Register rules
- Address the bank as **ඔයාලා / ඔයාලගේ** ("you all / your"), not formal ඔබ.
- Use spoken question words: **කොහොමද** (how), **මොකක්ද / මොකද** (what/why),
  **කවදද** (when), **කොහෙන්** (where), **ඇයි** (why) — never කෙසේද, කුමක්ද.
- Definite article/classifier **එක**: `කාඩ් එක` (the card), `පේමන්ට් එක`.
- "want/need" → **ඕනේ**; "can?" → **පුළුවන්ද**; polite request → **...කරන්නකෝ**.
- Spoken negatives: **නෑ** (no/not), **හම්බුන්නෑ** (didn't get), **බෑ** (can't).
- Keep it conversational, use commas, allow mild interjections (අනේ, හලෝ).

## Term glossary (keep English loanwords in Sinhala script)
| English | Sinhala (colloquial) |
|---|---|
| card | කාඩ් එක |
| card payment | කාඩ් පේමන්ට් එක |
| payment | පේමන්ට් එක |
| exchange rate | එක්ස්චේන්ජ් රේට් එක |
| transfer | ට්‍රාන්ස්ෆර් එක |
| transaction | ට්‍රාන්සැක්ෂන් එක |
| account | account එක |
| app | ඇප් එක |
| link | ලින්ක් |
| track | ට්‍රැක් |
| delivery | ඩිලිවරි |
| order | ඕඩර් |
| refund | රිෆන්ඩ් එක |
| fee | ෆී එක |
| cash (verb) | කෑෂ් කරගන්නවා |
| money | සල්ලි |
| charged extra / overcharged | වැඩිපුර අයකරලා |
| wrong / incorrect | වැරදියි / හරි නෑ |
| item I bought | මම ගත්ත බඩුව / මම ගත්ත එක |
| purchase | පර්චේස් එක / ගත්ත එක |
| abroad / overseas | පිටරට / පිටරටින් |
| foreign currency | වෙන කරන්සි එකක් / විදේශ මුදල් |
| interbank exchange rate | නිල interbank exchange rate එක |
| still | තාම · but | ඒත් · or/otherwise | නැත්තම් |

- Keep **LKR / USD** as-is (Roman) — don't translate currency codes.
- Localized Rupee amounts (e.g. `Rs 10`, `Rs 100,000`) stay as digits; render
  in words only if natural (`රුපියල් 10ක්`).

## Workflow (how rows get added)
1. Pick the next un-done category (train first-appearance order).
2. Translate every train row of that category in the style above.
3. Put `{train_index: sinhala}` in a JSON file.
4. `python translation/append_sinhala.py <that.json>` — appends aligned rows
   (copies category/sentiment/priority verbatim, refuses misaligned indices).

Done so far: card_arrival, card_linking, exchange_rate, card_payment_wrong_exchange_rate.
