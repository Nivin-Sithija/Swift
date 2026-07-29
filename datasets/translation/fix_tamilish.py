#!/usr/bin/env python3
"""
Fix and standardize Tamilish (Tanglish) datasets per TAMIL_STYLE.md rules.

Converts formal/literary Tamil transliteration into natural spoken Sri Lankan
Tanglish with appropriate English code-mixing (loanwords) and colloquial verbs/pronouns.

Usage:
    python datasets/translation/fix_tamilish.py
"""
import csv
import os
import re

# -----------------------------------------------------------------------------
# Rules from TAMIL_STYLE.md
# -----------------------------------------------------------------------------

PRONOUN_RULES = [
    (r"\benathu\b", "enoda"),
    (r"\benadhu\b", "enoda"),
    (r"\bennudaiya\b", "enoda"),
    (r"\bungaludaiya\b", "unga"),
    (r"\bungalathu\b", "unga"),
    (r"\bungaladhu\b", "unga"),
    (r"\bungal\b", "unga"),
    (r"\bneengal\b", "neenga"),
    (r"\bnaangal\b", "naanga"),
    (r"\bthayavuseithu\b", "please"),
    (r"\bthayavu seithu\b", "please"),
    (r"\bdhayavuseydhu\b", "please"),
    (r"\bdhayavuseithu\b", "please"),
    (r"\bthayavuseythu\b", "please"),
    (r"\bthayavu seythu\b", "please"),
]

LOANWORD_RULES = [
    # Card
    (r"\battaiyai\b", "card-ai"),
    (r"\battaikku\b", "card-ku"),
    (r"\battaiyin\b", "card-oda"),
    (r"\battaikkaaga\b", "card-kaaga"),
    (r"\battaikkaana\b", "card-kaana"),
    (r"\battaiyil\b", "card-la"),
    (r"\battaikalai\b", "cards-ai"),
    (r"\battaikaluku\b", "cards-ku"),
    (r"\battaikalukku\b", "cards-ku"),
    (r"\battaikalin\b", "cards-in"),
    (r"\battaikal\b", "cards"),
    (r"\battai\b", "card"),
    (r"\battayai\b", "card-ai"),
    # Transaction
    (r"\bparivarthanaiyai\b", "transaction-ai"),
    (r"\bparivarthanaiyil\b", "transaction-la"),
    (r"\bparivarthanaikku\b", "transaction-ku"),
    (r"\bparivarthanaigalai\b", "transactions-ai"),
    (r"\bparivarthanaikalai\b", "transactions-ai"),
    (r"\bparivarthanaigal\b", "transactions"),
    (r"\bparivarthanaikal\b", "transactions"),
    (r"\bparivarthanai\b", "transaction"),
    # App
    (r"\bseyaliyil\b", "app-la"),
    (r"\bseyaliyai\b", "app-ai"),
    (r"\bseyalikku\b", "app-ku"),
    (r"\bseyali\b", "app"),
    # Account
    (r"\bkanakkil\b", "account-la"),
    (r"\bkanakkudan\b", "account-oda"),
    (r"\bkanakkai\b", "account-ai"),
    (r"\bkanakkukku\b", "account-ku"),
    (r"\bkanakkuku\b", "account-ku"),
    (r"\bkanakku\b", "account"),
    # Other Banking Vocabulary
    (r"\barikkaiiyil\b", "statement-la"),
    (r"\barikkaiyil\b", "statement-la"),
    (r"\barikkai\b", "statement"),
    (r"\bniluvaiyil\b", "pending-la"),
    (r"\bniluvai\b", "pending"),
    (r"\bkattanathirkana\b", "fee-kaana"),
    (r"\bkattanathirku\b", "fee-ku"),
    (r"\bkattanathai\b", "fee-ai"),
    (r"\bkattanam\b", "fee"),
    (r"\bvigithangalai\b", "rates-ai"),
    (r"\bvigithangalin\b", "rates-in"),
    (r"\bvigithangal\b", "rates"),
    (r"\bvigithathai\b", "rate-ai"),
    (r"\bvigitham\b", "rate"),
    (r"\bnaanayangalai\b", "currencies-ai"),
    (r"\bnaanayangalil\b", "currencies-la"),
    (r"\bnaanyathil\b", "currency-la"),
    (r"\bnaanaya\b", "currency"),
    (r"\bnilaimaiyai\b", "status-ai"),
    (r"\bnilaimai\b", "status"),
    (r"\bviniyogappattathu\b", "deliver aachu"),
    (r"\bviniyogithathu\b", "delivery"),
    (r"\bviniyogam\b", "delivery"),
    (r"\bpanam\b", "cash"),
    (r"\bthogaiyai\b", "amount-ai"),
    (r"\bthogai\b", "amount"),
]

VERB_AND_QUESTION_RULES = [
    (r"\bkidaikkavillai\b", "kidaikkala"),
    (r"\bvaravillai\b", "varala"),
    (r"\bseravillai\b", "serala"),
    (r"\bseyyappadavillai\b", "seiyappadala"),
    (r"\bmudiyavillai\b", "mudiyala"),
    (r"\bseiyavillai\b", "seiyala"),
    (r"\billavillai\b", "illai"),
    (r"\birukkirathu\b", "irukku"),
    (r"\birukkiratha\b", "irukka"),
    (r"\birukkirathaa\b", "irukkaa"),
    (r"\bkaattugirathu\b", "kaattuthu"),
    (r"\bkaattukirathu\b", "kaattuthu"),
    (r"\bedukkirathu\b", "edukkuthu"),
    (r"\bedukkiratha\b", "edukkutha"),
    (r"\bnadakkirathu\b", "nadakkuthu"),
    (r"\bvarugirathu\b", "varuthu"),
    (r"\btherigirathu\b", "theriyuthu"),
    (r"\btheriyavillai\b", "theriyala"),
    (r"\bpuriyavillai\b", "puriyala"),
    (r"\bevvaaru\b", "eppadi"),
    (r"\bevvaru\b", "eppadi"),
    (r"\benge\b", "enga"),
    (r"\bkaaththukondirukkiren\b", "wait pannitu irukken"),
    (r"\bkaaththukondirukkiraen\b", "wait pannitu irukken"),
    # General regex endings for literary verbs
    (r"\b([a-z]+)kkavillai\b", r"\1kkala"),
    (r"\b([a-z]+)kkirathu\b", r"\1kkuthu"),
    (r"\b([a-z]+)kkiratha\b", r"\1kkutha"),
    (r"\b([a-z]+)kkiraen\b", r"\1kkren"),
    (r"\b([a-z]+)kkireergal\b", r"\1kkireenga"),
    (r"\b([a-z]+)kkireerga\b", r"\1kkireenga"),
    (r"\b([a-z]+)ppadavillai\b", r"\1ppadala"),
    (r"\b([a-z]+)ppattullathu\b", r"\1ppattirukku"),
    (r"\b([a-z]+)ginrana\b", r"\1guthu"),
    (r"\b([a-z]+)girathu\b", r"\1guthu"),
    (r"\b([a-z]+)kondirukkiren\b", r"\1tu irukken"),
    (r"\b([a-z]+)padugireergal\b", r"\1padureenga"),
]

ALL_RULES = PRONOUN_RULES + LOANWORD_RULES + VERB_AND_QUESTION_RULES


def standardize_text(text: str) -> str:
    if not text:
        return text
    
    out = text
    for pat, rep in ALL_RULES:
        out = re.sub(pat, rep, out, flags=re.IGNORECASE)
    
    # Capitalize first letter of sentence if needed
    if out and len(out) > 0:
        out = out[0].upper() + out[1:]
        
    return out


def fix_file(input_path: str, output_path: str) -> tuple[int, int]:
    with open(input_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    
    changed_count = 0
    for r in rows:
        old_text = r["text"]
        new_text = standardize_text(old_text)
        if new_text != old_text:
            r["text"] = new_text
            changed_count += 1

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "text_en", "text", "category", "sentiment", "priority"])
        w.writeheader()
        w.writerows(rows)
    
    return len(rows), changed_count


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    datasets_dir = os.path.join(base_dir, "..")
    
    train_path = os.path.join(datasets_dir, "tamilish", "train_labeled.csv")
    test_path = os.path.join(datasets_dir, "tamilish", "test_labeled.csv")
    
    print("Standardizing train set...")
    total_tr, changed_tr = fix_file(train_path, train_path)
    print(f"  -> {changed_tr}/{total_tr} rows updated in train_labeled.csv ({changed_tr/total_tr*100:.1f}%)")
    
    print("Standardizing test set...")
    total_te, changed_te = fix_file(test_path, test_path)
    print(f"  -> {changed_te}/{total_te} rows updated in test_labeled.csv ({changed_te/total_te*100:.1f}%)")


if __name__ == "__main__":
    main()
