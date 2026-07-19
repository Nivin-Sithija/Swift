#!/usr/bin/env python3
import csv, re, sys, io

APPLY = "--apply" in sys.argv

BASE = "/Users/sithijaseneviratne/Documents/Github/Swift/datasets"
FILES = [
    f"{BASE}/original dataset/test.csv",
    f"{BASE}/original dataset/train.csv",
    f"{BASE}/llm-zeroshot/english/test_labeled.csv",
    f"{BASE}/llm-zeroshot/english/train_labeled.csv",
]

def sub_all(rules, text):
    for pat, rep in rules:
        text = re.sub(pat, rep, text, flags=re.IGNORECASE)
    return text

# ---- amount helpers ----
def amount_x1000(m):
    n = int(m.group(1))
    return f"Rs {n},000"

def extra_charge(text):
    rules = [
        (r'\$\s?1\.00', 'Rs 10'),
        (r'\$\s?1\b', 'Rs 10'),
        (r'\b1\s?\$', 'Rs 10'),
        (r'£\s?1\b', 'Rs 10'),
        (r'\b1\s?£', 'Rs 10'),
        (r'\b1 euro\b', 'Rs 10'),
        (r'\bpound more\b', 'Rs 10 more'),
        (r'\bdollar more\b', 'Rs 10 more'),
        (r'\bpound charge\b', 'Rs 10 charge'),
        (r'\bone pound\b', 'Rs 10'),
        (r'\bone dollar\b', 'Rs 10'),
        (r'\bextra pound\b', 'extra Rs 10'),
        (r'\bextra dollar\b', 'extra Rs 10'),
        (r'\badditional pound\b', 'additional Rs 10'),
        (r'\badditional dollar\b', 'additional Rs 10'),
        (r'\ba pound\b', 'Rs 10'),
        (r'\ban pound\b', 'Rs 10'),
        (r'\ba dollar\b', 'Rs 10'),
        (r'\bpounds\b', 'Rs 10'),
        (r'\bpound\b', 'Rs 10'),
        (r'\bdollars\b', 'Rs 10'),
        (r'\bdollar\b', 'Rs 10'),
    ]
    return sub_all(rules, text)

def cash_wrong_amount(text):
    # $100 / £30 / 30 pounds / bare 30 (from the known set) -> Rs n,000
    # do NOT consume surrounding whitespace
    text = re.sub(r'(?:\$|£)?\b(100|80|50|40|30|20|10)\b(?: ?pounds?\b| ?dollars?\b)?', amount_x1000, text)
    return text

def cash_not_recognised(text):
    # numeric first (so "five hundred" -> Rs 500,000 below is not re-matched)
    text = re.sub(r'(?:\$|£)?\b(500|200)\b(?: ?pounds?\b| ?dollars?\b| ?£)?', amount_x1000, text)
    text = re.sub(r'\bfive hundred pounds?\b', 'Rs 500,000', text, flags=re.IGNORECASE)
    return text

def receiving_money(text):
    rules = [
        (r'\bUS dollars\b', 'Sri Lankan Rupees'),
        (r'\bGBP\b', 'LKR'),
    ]
    return sub_all(rules, text)

def exchange_via_app(text):
    rules = [
        (r'\bAustralian dollars\b', 'USD'),
        (r'\bAUD\b', 'USD'),
        (r'\bUK currency\b', 'LKR'),
        (r'\bUK pounds\b', 'LKR'),
        (r'\bUK pound\b', 'LKR'),
        (r'\bGBP\b', 'LKR'),
        (r'\bpounds\b', 'LKR'),
        (r'\bpound\b', 'LKR'),
        (r'\bdollars\b', 'USD'),
    ]
    return sub_all(rules, text)

def card_payment_wrong_exchange(text):
    rules = [
        (r'\bRussian Rubles?\b', 'LKR'),
        (r'\bRussian rubles?\b', 'LKR'),
        (r'\brubles?\b', 'LKR'),
        (r'\bUK pound currency\b', 'USD'),
        (r'\bUK pounds\b', 'USD'),
        (r'\bUK pound\b', 'USD'),
        (r'\bBritish pounds\b', 'USD'),
        (r'\bpounds\b', 'USD'),
        (r'\bpound\b', 'USD'),
    ]
    return sub_all(rules, text)

def wrong_rate_cash_withdrawal(text):
    rules = [
        (r'\bBritish pounds\b', 'US dollars'),
        (r'\bBritain\b', 'Sri Lanka'),
    ]
    return sub_all(rules, text)

def balance_not_updated(text):
    rules = [
        (r'\bUK bank account\b', 'local bank account'),
        (r'\bUK banking account\b', 'local bank account'),
        (r'\bUK Account\b', 'local bank account'),
        (r'\bUK account\b', 'local bank account'),
        (r'\bUK bank\b', 'local bank'),
        (r'\bwithin the UK\b', 'within Sri Lanka'),
        (r'\bfrom the UK\b', 'from a local bank'),
        (r'\bUK transfers\b', 'local bank transfers'),
        (r'\bUK transfer\b', 'local bank transfer'),
        (r'\bthe UK\b', 'Sri Lanka'),
        (r'\bUK\b', 'local'),
    ]
    return sub_all(rules, text)

def transfer_not_received(text):
    rules = [
        (r'\bwithin the UK\b', 'within Sri Lanka'),
        (r'\bthe UK\b', 'Sri Lanka'),
    ]
    return sub_all(rules, text)

def country_support(text):
    rules = [
        (r'\bthe UK area\b', 'Sri Lanka'),
        (r'\bthe UK\b', 'Sri Lanka'),
        (r'\bUK\b', 'Sri Lanka'),
        (r'\bin the European Union\b', 'in Sri Lanka'),
        (r'\bthe European Union\b', 'Sri Lanka'),
        (r'\bEuropean Union\b', 'Sri Lanka'),
        (r'\bof Europe\b', 'of Sri Lanka'),
        (r'\bto Europe\b', 'to Sri Lanka'),
        (r'\bin Europe\b', 'in Sri Lanka'),
        (r'\bEurope\b', 'Sri Lanka'),
    ]
    return sub_all(rules, text)

def transfer_timing(text):
    rules = [
        (r'\bfrom Europe\b', 'from overseas'),
        (r'\bin Europe\b', 'overseas'),
        (r'\bEuropean\b', 'overseas'),
        (r'\bEurope\b', 'overseas'),
    ]
    return sub_all(rules, text)

def top_up_card_charge(text):
    rules = [
        (r'\bEuropean\b', 'foreign'),
    ]
    return sub_all(rules, text)

HANDLERS = {
    'extra_charge_on_statement': extra_charge,
    'wrong_amount_of_cash_received': cash_wrong_amount,
    'cash_withdrawal_not_recognised': cash_not_recognised,
    'receiving_money': receiving_money,
    'exchange_via_app': exchange_via_app,
    'card_payment_wrong_exchange_rate': card_payment_wrong_exchange,
    'wrong_exchange_rate_for_cash_withdrawal': wrong_rate_cash_withdrawal,
    'balance_not_updated_after_bank_transfer': balance_not_updated,
    'transfer_not_received_by_recipient': transfer_not_received,
    'country_support': country_support,
    'transfer_timing': transfer_timing,
    'top_up_by_card_charge': top_up_card_charge,
}

review = []  # (file, line, category, old, new)

for path in FILES:
    with open(path, newline='', encoding='utf-8') as f:
        rows = list(csv.reader(f))
    header = rows[0]
    out = [header]
    for i, row in enumerate(rows[1:], start=2):  # line numbers match file (header=line1)
        if not row:
            out.append(row); continue
        text = row[0]
        category = row[1] if len(row) > 1 else ''
        h = HANDLERS.get(category)
        if h:
            new = h(text)
            if new != text:
                review.append((path.split('/datasets/')[1], i, category, text, new))
                row = [new] + row[1:]
        out.append(row)
    if APPLY:
        with open(path, 'w', newline='', encoding='utf-8') as f:
            csv.writer(f).writerows(out)

# write review file
rev_path = "/private/tmp/claude-501/-Users-sithijaseneviratne-Documents-Github-Swift/a7045249-9d97-44c0-b269-f3fe95891cc0/scratchpad/changes_review.csv"
with open(rev_path, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['file', 'line', 'category', 'old_text', 'new_text'])
    w.writerows(review)

# summary
from collections import Counter
by_file = Counter(r[0] for r in review)
by_cat = Counter(r[2] for r in review)
print("APPLIED" if APPLY else "DRY RUN")
print("Total changed rows:", len(review))
print("\nBy file:")
for k, v in by_file.items():
    print(f"  {v:4d}  {k}")
print("\nBy category:")
for k, v in sorted(by_cat.items(), key=lambda x: -x[1]):
    print(f"  {v:4d}  {k}")
