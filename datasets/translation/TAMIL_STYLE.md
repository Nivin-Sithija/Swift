# Colloquial Tamil / Tanglish Translation — Style Guide

The Tamilish dataset (`tamilish/train_labeled.csv`, `tamilish/test_labeled.csv`) is
**colloquial, code-mixed Sri Lankan Tamil** — the way Tamil-speaking Sri Lankans
actually type in a banking support chat — NOT literary/formal Tamil. English
banking terms stay as English words (Latin script), not Tamil script equivalents.

> **Parallel**: this document is the Tamil/Tanglish equivalent of
> [`SINHALA_STYLE.md`](SINHALA_STYLE.md). The same structural decisions apply —
> read that document first for context.

---

## Register rules

- Address the bank as **நீங்க / உங்க** (informal plural), not formal நீங்கள் / உங்களுடைய.
  Tanglish: **neenga / unga**, not neengal / ungaludaiya.
- Use spoken question words:
  - **eppadi** (how) — not evvaaru / evvitham
  - **enna** (what) — not enn / ennaven
  - **eppo** (when) — not eppothu
  - **enga** (where) — not enge / engirunthu
  - **yen** (why) — never literary yaen / yetharkkaaga
- Spoken verb endings:
  - **-la** (negative): `varala` (didn't come), `kidaikkala` (didn't get)
  - **-anum / -anum** (must): `pannanum` (must do), `poga vendum` → `poganum`
  - **-laam** (can): `pannalaam` → `pannalam`
  - **-ttu** (having done): `paattu` → `pannittu`
  - **-rathu** (present continuous): `panrathu` (doing), `varathu` (coming)
- Contractions and spoken forms:
  - **Enoda** (my) — not enathu / enathu  
  - **ungaloda / ungada** (your) — not ungaludaiya
  - **adhu** (that) — not athu in flowing speech
  - **ithula** (in this) — not ithil
  - **enakku** (to me) — stays as-is (already spoken form)
  - **kidaikkala** (didn't get) — not kidaikkavillai
  - **mudiyala** (can't) — not mudiyavillai
  - **seiyala** (didn't do) — not seiyavillai
  - **iruku** (is/exists) — not irukkirathu
  - **aagala** (didn't happen) — not aagavillai
- Mild interjections are fine: **da**, **ya**, **please**, **sorry**
- Sentence-ending particles: **nu** (quotative), **thaan** (emphasis), **la** (locative/question)

---

## Term glossary — English loanwords kept AS ENGLISH

**Key difference from Sinhala**: In Singlish, English loanwords appear in Sinhala
script in the native-script source (කාඩ් → overridden to `card`). In Tanglish,
the English word appears **directly as the English word** — no Tamil-script
intermediate. This mirrors how Sri Lankan Tamil speakers actually type.

| English | Tanglish form | Do NOT use (formal Tamil romanization) |
|---|---|---|
| card | card | ~~attai~~ / ~~attaiyin~~ / ~~kartu~~ |
| payment | payment | ~~kattanam~~ / ~~seluththal~~ |
| transaction | transaction | ~~parivarthanai~~ |
| exchange rate | exchange rate | ~~maatru vigitham~~ / ~~naanaya maatru vighitham~~ |
| account | account | ~~kanakku~~ |
| app | app | ~~seyali~~ / ~~payanpaatu~~ |
| link (v.) | link panna | ~~inaikka~~ / ~~inaippathu~~ |
| track (v.) | track panna | ~~kandupidikka~~ (when meaning parcel tracking) |
| delivery | delivery | ~~viniyogam~~ / ~~thabaalil anupputhal~~ |
| fee | fee | ~~kattanam~~ (use kattanam only for formal context) |
| refund | refund | ~~thirumba koduppathu~~ |
| statement | statement | ~~arikkai~~ / ~~vibaraththai~~ |
| pending | pending | ~~niluvai~~ / ~~niluvaiyil~~ |
| ATM | ATM | Keep as-is |
| PIN | PIN | Keep as-is |
| top up | top up | ~~nirappuval~~ |
| transfer | transfer | ~~maatrudhal~~ |
| balance | balance | ~~iruppu~~ (unless specifically meaning bank balance in Tamil) |
| order (v.) | order panna | ~~kettaarppittal~~ |
| cancel | cancel panna | ~~rathu seivathu~~ |
| block (v.) | block panna | ~~thadupathu~~ |
| activate | activate panna | ~~seiyalpadutha~~ |
| verify | verify panna | ~~uruthi seivathu~~ |
| charge (v.) | charge panna | ~~aravidu~~ / ~~vasool~~ |
| decline (v.) | decline aaguthu | ~~niraagarikka~~ |
| process (v.) | process aaguthu | ~~seyalpadutha~~ |
| update | update | ~~pudhuppu~~ / ~~maatrram~~ |
| limit | limit | ~~varambu~~ / ~~ellay~~ |
| wallet | wallet | ~~panappaiy~~ |
| virtual | virtual | ~~meynikara~~ |
| disposable | disposable | ~~oru murai payanpaduthum~~ |

- Keep **LKR / USD / EUR / Rs** as-is (Roman script) — don't translate currency codes.
- Localized Rupee amounts (e.g. `Rs 10`, `Rs 100,000`) stay as digits.

---

## Tanglish romanization conventions

For Tamil words that DO appear romanized (as opposed to being replaced by English
loanwords), use these conventions:

| Tamil character/sound | Tanglish spelling | Notes |
|---|---|---|
| ழ | zh | Uniquely Tamil retroflex approximant |
| ற | r (word-medial), tr (word-initial or after consonant) | Context-dependent |
| ண | n (default) or N (if disambiguation needed) | Retroflex n |
| ஞ | nj | Palatal nasal |
| ங | ng | Velar nasal |
| Long vowels (ா ீ ூ ே ோ) | aa, ee/ii, oo, ee, oo | Doubled vowel |
| Short vowels (அ இ உ எ ஒ) | a, i, u, e, o | Single letter |
| ஐ | ai | Diphthong |
| ஔ | au | Diphthong |
| Aspirates (in loanwords) | th, dh, bh, ph | Only for loanwords from Sanskrit/Hindi |

### Capitalization

- Sentence-initial capitalization: **Yes** (first letter uppercase) — matches
  natural Tanglish typing behavior
- English loanwords: **match natural typing** — usually lowercase in mid-sentence
  (`card`, `app`), uppercase only for proper nouns/acronyms (`ATM`, `PIN`, `Visa`, `Mastercard`)

---

## Hyphen convention for code-mixing

When an English word takes a Tamil suffix, use a **hyphen** to join them:

| Pattern | Example | Notes |
|---|---|---|
| English noun + Tamil case suffix | `card-ai` (card-accusative), `account-la` (in the account) | Hyphen before Tamil suffix |
| English noun + possessive | `card-oda` (card's) | |
| English verb + Tamil auxiliary | `track panna` (to track), `cancel pannunga` (please cancel) | Space, not hyphen — `panna` is a separate Tamil word |
| English adjective + Tamil particle | `pending-la` (in pending state) | Hyphen |
| English noun + plural | `cards` (use English plural) or `card-gal` (Tamil plural) | Either is acceptable |

---

## Anti-patterns — what the dataset should NOT contain

These are markers of **machine-translated formal Tamil** that slipped into
Tanglish via literal romanization. Every row exhibiting these patterns needs
correction:

| Anti-pattern | Example | Should be |
|---|---|---|
| Literary verb endings: -kirrathu, -villai, -padugirrathu | `kidaikkavillai` | `kidaikkala` |
| Full Tamil nouns for English loanwords | `attai` (card), `parivarthanai` (transaction) | `card`, `transaction` |
| Formal pronouns | `enathu` (my, formal) | `enoda` (my, spoken) |
| Long polite forms | `thayavuseithu` (please, literary) | `please` or `dayavu seidhu` |
| Literary question endings | `-irukkiratha?`, `-seyyappadavillai?` | `-irukka?`, `-aagala?` |
| Zero code-mixing (entire sentence in romanized Tamil) | `enathu attai innum vanthu seravillai` | `Enoda card innum varala` |
| Sandhi-heavy long compounds | `kaaththukondirukkiren` (I am waiting) | `wait pannitu irukken` / `kaathitu irukken` |

---

## Workflow (how rows get added/fixed)

1. Start from the English source text in `text_en`.
2. Translate to colloquial spoken Tamil, code-mixed with English banking terms per
   the glossary above.
3. Romanize to Tanglish using the conventions above.
4. Verify: does it sound like something a young Sri Lankan Tamil speaker would
   actually type in a chat? If it sounds like a textbook or Google Translate
   output, rewrite it.

### Quality self-check for each row

- [ ] Uses English for banking terms, not Tamil equivalents?
- [ ] Uses colloquial verb endings (-la, -anum, -laam), not literary ones (-villai, -vendum)?
- [ ] Uses spoken pronouns (enoda, unga), not formal ones (enathu, ungaludaiya)?
- [ ] Sentence-initial capitalized?
- [ ] Hyphens used correctly for English-Tamil suffix joining?
- [ ] Reads naturally aloud as spoken Tamil-English chat?

---

## Status

This style guide is newly created. It needs review by a native Sri Lankan Tamil
speaker before it can be considered authoritative. Currently applies to:
- `tamilish/train_labeled.csv` (10,006 rows) — mostly colloquial ✅ (but has
  pockets of formal romanization, see audit)
- `tamilish/test_labeled.csv` (3,083 rows) — rows 0–29 are formal/literary ❌,
  rows 30+ are colloquial ✅ (register split)
