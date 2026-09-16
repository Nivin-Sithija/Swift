# Collected systems -- exact model + date

## Summary (final state)

| system | exact model | date | collected via | sinhala | tamil |
|---|---|---|---|---|---|
| openai | **TODO: exact model name, e.g. "GPT-5.1"** | **TODO: date pasted** | human, pasted `prompt_openai_{lang}.md` | 150/150 | 150/150 |
| gemini | **TODO: exact model name, e.g. "Gemini 3 Pro"** | **TODO: date pasted** | human, pasted `prompt_gemini_{lang}.md` (identical prompt to openai) | 150/150 | 150/150 |
| gptoss | gpt-oss-20b (Ollama, local, temperature=0) | 2026-09-12 | `fetch_gptoss_translations.py`, mechanically sends the same prompt | 148/150 | 150/150 |

gptoss gaps (both genuine findings about the local model, not tooling failures --
see below):
- **id 2803 (sinhala): blank.** The model never reached a visible answer on this
  row across 5 separate attempts (timeouts up to 600s) -- it appears to enter an
  unrecoverable hidden-reasoning loop on this specific input. Left blank rather
  than re-rolled indefinitely.
- **id 2899 (sinhala): answered mostly in English** (`"withdraw cash charged
  \"why?\""` for "I've notice I was charged for withdrawing cash, can you
  explain why?"), under validate_translations.py's 15% script-fidelity floor.
  Kept as-is -- this is the model's actual output on its one recorded attempt,
  not re-rolled for a better answer, so it stays comparable to how openai/gemini
  were collected (one human paste, no retries for quality).

## Why gptoss needed this much retry machinery, and why that's fair

gpt-oss-20b is a reasoning model: Ollama hides its chain-of-thought and returns
only the final channel, but that hidden reasoning still consumes the token
budget. Two failure modes showed up, both procedural (fixed in
`fetch_gptoss_translations.py`), not translation-quality issues:

1. **Batch size.** Single-shot (150 rows) and even 30-row chunks frequently
   exhausted the token budget in hidden reasoning before ever reaching the
   visible CSV -- 675s, 756s, 724s calls that returned 0 rows. Falling back to
   one row per call (see `fill_missing()`) fixed almost all of it; a single row
   typically finished in 5-20s.
2. **Stated-count mismatch.** `build_prompt()` was slicing the saved prompt
   file but leaving its literal "Here are the **150** rows to translate"
   header intact even when only 1 row followed. That mismatch reproducibly
   stalled the model on a specific subset of rows across repeated identical
   retries (not random -- the same ~9 ids failed every time until the header
   was fixed to state the true count). Once `build_prompt()` rewrites the
   count to match what's actually sent, 7 of those 9 resolved immediately.

None of this touched what was sent for translation -- same instructions, same
rows, same rules -- only how many rows shared one call. OpenAI and Gemini never
needed this because a human pasted the whole 150-row prompt once and the model
did not visibly reason before answering.

## Raw collection log (fetch_gptoss_translations.py --fill-missing history)

## gptoss -- gpt-oss-20b (Ollama, local)
collected: 2026-09-12T16:31:48
- sinhala: chunked:30, 90 missing, saved to systems/gptoss_sinhala.csv
- tamil: chunked:30, 60 missing, saved to systems/gptoss_tamil.csv

## gptoss -- gpt-oss-20b (Ollama, local)
collected: 2026-09-12T18:01:38
- sinhala: per-row retry filled 83, 7 still missing
- tamil: per-row retry filled 57, 3 still missing

## gptoss -- gpt-oss-20b (Ollama, local)
collected: 2026-09-12T18:40:18
- sinhala: per-row retry filled 0, 7 still missing
- tamil: per-row retry filled 1, 2 still missing

## gptoss -- gpt-oss-20b (Ollama, local)
collected: 2026-09-12T19:01:57
- sinhala: per-row retry filled 0, 7 still missing
- tamil: per-row retry filled 0, 2 still missing

## gptoss -- gpt-oss-20b (Ollama, local)
collected: 2026-09-12T19:15:43
- sinhala: per-row retry filled 5, 2 still missing
- tamil: per-row retry filled 2, 0 still missing

## gptoss -- gpt-oss-20b (Ollama, local)
collected: 2026-09-12T19:24:19
- sinhala: per-row retry filled 1, 1 still missing
- tamil: per-row retry filled 0, 0 still missing

## gptoss -- gpt-oss-20b (Ollama, local), build_prompt() row-count fix applied
collected: 2026-09-12T19:30:00
- sinhala: per-row retry filled 7, 2 still missing (2749, 2803)
- tamil: per-row retry filled 2, 0 still missing -- **tamil complete, 150/150**

## gptoss -- gpt-oss-20b (Ollama, local), 600s timeout
collected: 2026-09-12T19:35:00
- sinhala: per-row retry filled 1 (2749), 1 still missing (2803, unrecoverable
  -- see Summary above)
