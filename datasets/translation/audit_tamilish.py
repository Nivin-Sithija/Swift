"""
Tamilish Dataset Audit Script
==============================
Audits tamilish/train_labeled.csv and tamilish/test_labeled.csv for:
1. Register detection (formal literary Tamil vs. colloquial Tanglish)
2. Code-Mixing Index (CMI) per row
3. Anti-pattern detection (formal verb endings, Tamil-only nouns, etc.)
4. Tamil dataset over-formalization flags

Outputs:
- tamilish_audit_train.csv / tamilish_audit_test.csv  (per-row flags)
- tamil_audit_summary.csv                              (per-category summary)
- audit_report.txt                                     (console-readable report)

Based on rules defined in datasets/translation/TAMIL_STYLE.md
"""

import csv
import re
import os
import sys
from collections import Counter, defaultdict

# ---------------------------------------------------------------------------
# Formal Tamil markers — romanized patterns that indicate literary/formal style
# ---------------------------------------------------------------------------

# Literary verb endings (regex patterns)
FORMAL_VERB_ENDINGS = [
    r'\w+kkavillai\b',       # kidaikkavillai (didn't get, formal)
    r'\w+kkiraen\b',         # kaaththukondirukkiraen
    r'\w+kkirathu\b',        # irukkirathu (is, formal)
    r'\w+kkiratha\b',        # irukkiratha (is it?, formal)
    r'\w+kkireerga[l]?\b',   # pannikkireerga (you do, formal)
    r'\w+ppadavillai\b',     # seyyappadavillai (wasn't done, formal)
    r'\w+ppattullathu\b',    # aravidappattullathu (has been charged, formal)
    r'\w+ppatta\b',          # anuppappatta (was sent, formal)
    r'\w+ginrana\b',         # maaruginrana (changes, formal)
    r'\w+girathu\b',         # kaattugirathu (shows, formal)
    r'\w+virunthathu\b',     # irunthirunthathu
    r'\w+vendiyiruppathu\b', # vendiyiruppathu (having to, formal)
    r'\w+kondirukkiren\b',   # kaaththukondirukkiren (I am waiting, formal)
    r'\w+padugireergal\b',   # payanpadugireergal (you use, formal)
]

FORMAL_VERB_RES = [re.compile(p, re.IGNORECASE) for p in FORMAL_VERB_ENDINGS]

# Tamil-only nouns that should be English loanwords in Tanglish
TAMIL_NOUNS_MAP = {
    'attai': 'card',
    'attaiyai': 'card',
    'attaikku': 'card',
    'attaiyin': 'card',
    'attaikkaaga': 'card',
    'attaikkaana': 'card',
    'attaiyil': 'card',
    'attaikaluku': 'cards',
    'attaikalin': 'cards',
    'attayai': 'card',
    'parivarthanai': 'transaction',
    'parivarthanaiyai': 'transaction',
    'parivarthanaiyil': 'transaction',
    'parivarthanaikku': 'transaction',
    'nilaimai': 'status',
    'nilaimaiyai': 'status',
    'kattanam': 'fee/charge',
    'kattanathirkana': 'fee/charge',
    'kattanathirku': 'fee/charge',
    'kattanathai': 'fee/charge',
    'vigitham': 'rate',
    'vigithathai': 'rate',
    'vigithangal': 'rates',
    'vigithangalai': 'rates',
    'vigithangalin': 'rates',
    'naanaya': 'currency (as adj)',
    'naanayangalai': 'currencies',
    'naanayangalil': 'currencies',
    'naanyathil': 'currency',
    'kanakku': 'account',
    'kanakkudan': 'account',
    'kanakkil': 'account',
    'arikkai': 'statement',
    'arikkaiiyil': 'statement',
    'niluvai': 'pending',
    'niluvaiyil': 'pending',
    'viniyogam': 'delivery',
    'viniyogithathu': 'delivery',
}

# Formal pronoun patterns
FORMAL_PRONOUNS = {
    'enathu': 'enoda',      # my (formal → spoken)
    'ungaludaiya': 'ungada/ungaloda',  # your (formal → spoken)
    'ungalathu': 'ungada/ungaloda',
}

# Formal polite forms
FORMAL_POLITE = [
    'thayavuseithu',   # please (literary)
    'thayavu seithu',
    'dhayavuseydhu',
    'dhayavuseithu',
]

# Literary long compound verb forms (should be shorter/code-mixed)
FORMAL_COMPOUNDS = [
    'kaaththukondirukkiren',  # I am waiting (should be: wait pannitu irukken)
    'kaaththukondirukkiraen',
    'kaaththirukka',
    'seyyappadavillai',       # wasn't done (should be: aagala)
    'vasulikkappattullathu',  # has been charged
    'payanpaduthugireergal',  # you are using
    'theermanikkireergal',    # you determine
    'kandupidikkirathu',      # finding/locating (formal)
]


def tokenize(text):
    """Simple whitespace + punctuation tokenizer."""
    return re.findall(r"[A-Za-z0-9']+(?:-[A-Za-z0-9']+)*|[^\s]", text.lower())


def is_english_word(word):
    """
    Heuristic: a word is 'English' if it's in a common English word set
    OR if it matches typical English patterns and NOT typical Tamil patterns.
    For CMI purposes, we use a simple approach:
    - Words with common English suffixes/patterns
    - Words that are in our loanword list
    - Short common English words
    """
    # Known English loanwords used in banking Tanglish
    english_words = {
        'card', 'cards', 'payment', 'payments', 'transaction', 'transactions',
        'exchange', 'rate', 'rates', 'account', 'accounts', 'app', 'link',
        'track', 'tracking', 'delivery', 'fee', 'fees', 'refund', 'statement',
        'pending', 'atm', 'pin', 'top', 'up', 'transfer', 'balance', 'order',
        'cancel', 'block', 'activate', 'verify', 'charge', 'charged', 'decline',
        'declined', 'process', 'processed', 'update', 'limit', 'limits',
        'wallet', 'virtual', 'disposable', 'credit', 'debit', 'visa',
        'mastercard', 'status', 'help', 'please', 'ok', 'okay', 'sorry',
        'hi', 'hello', 'hey', 'yes', 'no', 'thank', 'thanks', 'check',
        'online', 'website', 'system', 'service', 'bank', 'banking',
        'mobile', 'phone', 'number', 'email', 'password', 'username',
        'login', 'logout', 'sign', 'currency', 'currencies', 'fiat',
        'eur', 'usd', 'lkr', 'rs', 'euro', 'euros', 'dollar', 'dollars',
        'cash', 'money', 'option', 'options', 'feature', 'features',
        'policy', 'policies', 'guideline', 'guidelines', 'restriction',
        'restrictions', 'limitation', 'limitations', 'available',
        'maximum', 'minimum', 'info', 'information', 'details', 'issue',
        'problem', 'support', 'customer', 'notification', 'alert',
        'receipt', 'hotel', 'gym', 'bag', 'jacket', 'pocket',
        'city', 'centre', 'theatre', 'progress', 'machine',
        'replacement', 'package', 'ship', 'mail', 'mailed', 'post',
        'friend', 'morning', 'today', 'week', 'weeks', 'day', 'days',
        'month', 'months', 'hour', 'hours', 'minute', 'time',
        'the', 'a', 'an', 'is', 'am', 'are', 'was', 'were', 'be',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'can', 'could', 'should', 'shall', 'may', 'might', 'must',
        'i', 'you', 'he', 'she', 'it', 'we', 'they', 'my', 'your',
        'his', 'her', 'its', 'our', 'their', 'me', 'him', 'us', 'them',
        'this', 'that', 'these', 'those', 'what', 'which', 'who', 'whom',
        'how', 'why', 'when', 'where', 'not', 'but', 'and', 'or',
        'if', 'then', 'so', 'because', 'of', 'in', 'on', 'at', 'to',
        'for', 'with', 'from', 'by', 'about', 'into', 'through',
        'after', 'before', 'since', 'until', 'while', 'during',
        'new', 'old', 'extra', 'wrong', 'right', 'correct', 'incorrect',
        'back', 'still', 'already', 'just', 'also', 'too', 'very',
        'more', 'less', 'much', 'many', 'some', 'any', 'all', 'every',
        'confirm', 'confirmed', 'done', 'work', 'working', 'broken',
        'lost', 'stolen', 'found', 'send', 'sent', 'received', 'get',
        'got', 'give', 'take', 'took', 'make', 'made', 'buy', 'bought',
        'use', 'used', 'try', 'tried', 'see', 'saw', 'show', 'showing',
        'foreign', 'international', 'european', 'country', 'countries',
        'temporary', 'temp', 'recent', 'last', 'first', 'next',
        'locker', 'flat', 'type', 'types', 'sort', 'kind',
    }
    word_lower = word.lower().rstrip('.,!?;:')
    return word_lower in english_words


def compute_cmi(text):
    """
    Compute Code-Mixing Index using Das & Gambäck (2014) formula:
    CMI = (N - max_lang) / N * 100
    where N = total tokens (excluding punctuation/numbers),
    max_lang = count of the dominant language tokens.
    
    Returns (cmi_value, n_english, n_tamil, n_total)
    """
    words = [w for w in tokenize(text) if re.match(r'[a-zA-Z]', w) and len(w) > 1]
    if not words:
        return 0.0, 0, 0, 0
    
    n_english = sum(1 for w in words if is_english_word(w))
    n_tamil = len(words) - n_english
    n_total = len(words)
    max_lang = max(n_english, n_tamil)
    
    if n_total == 0:
        return 0.0, 0, 0, 0
    
    cmi = ((n_total - max_lang) / n_total) * 100
    return round(cmi, 2), n_english, n_tamil, n_total


def detect_formal_verbs(text):
    """Count formal verb ending matches."""
    count = 0
    matches = []
    for regex in FORMAL_VERB_RES:
        found = regex.findall(text.lower())
        if found:
            count += len(found)
            matches.extend(found)
    return count, matches


def detect_tamil_nouns(text):
    """Find Tamil-only nouns that should be English loanwords."""
    words = tokenize(text)
    found = {}
    for w in words:
        w_clean = w.lower().rstrip('.,!?;:')
        if w_clean in TAMIL_NOUNS_MAP:
            found[w_clean] = TAMIL_NOUNS_MAP[w_clean]
    return found


def detect_formal_pronouns(text):
    """Find formal pronoun usage."""
    found = {}
    words = tokenize(text)
    for w in words:
        w_clean = w.lower().rstrip('.,!?;:')
        if w_clean in FORMAL_PRONOUNS:
            found[w_clean] = FORMAL_PRONOUNS[w_clean]
    return found


def detect_formal_polite(text):
    """Find formal politeness markers."""
    text_lower = text.lower()
    return [fp for fp in FORMAL_POLITE if fp in text_lower]


def detect_formal_compounds(text):
    """Find literary compound verb forms."""
    text_lower = text.lower()
    return [fc for fc in FORMAL_COMPOUNDS if fc in text_lower]


def classify_register(formal_verb_count, tamil_nouns, formal_pronouns, 
                       formal_polite, formal_compounds, cmi):
    """
    Classify a row's register as FORMAL, COLLOQUIAL, or MIXED.
    """
    formal_score = 0
    formal_score += formal_verb_count * 2  # verb endings are strong signals
    formal_score += len(tamil_nouns) * 2   # Tamil-only nouns are strong signals
    formal_score += len(formal_pronouns) * 1
    formal_score += len(formal_polite) * 1
    formal_score += len(formal_compounds) * 3  # compounds are very strong signals
    
    if cmi < 5:
        formal_score += 2  # very low code-mixing suggests formal
    
    if formal_score >= 4:
        return 'FORMAL'
    elif formal_score >= 2:
        return 'MIXED'
    else:
        return 'COLLOQUIAL'


def audit_row(row_id, text, text_en, category):
    """Audit a single row and return a dict of findings."""
    cmi, n_eng, n_tam, n_total = compute_cmi(text)
    formal_verb_count, formal_verb_matches = detect_formal_verbs(text)
    tamil_nouns = detect_tamil_nouns(text)
    formal_pronouns = detect_formal_pronouns(text)
    formal_polite = detect_formal_polite(text)
    formal_compounds = detect_formal_compounds(text)
    
    register = classify_register(
        formal_verb_count, tamil_nouns, formal_pronouns,
        formal_polite, formal_compounds, cmi
    )
    
    issues = []
    if formal_verb_count > 0:
        issues.append(f"formal_verbs:{','.join(formal_verb_matches[:3])}")
    if tamil_nouns:
        for tn, should_be in tamil_nouns.items():
            issues.append(f"tamil_noun:{tn}→{should_be}")
    if formal_pronouns:
        for fp, should_be in formal_pronouns.items():
            issues.append(f"formal_pronoun:{fp}→{should_be}")
    if formal_polite:
        issues.append(f"formal_polite:{','.join(formal_polite)}")
    if formal_compounds:
        issues.append(f"formal_compound:{','.join(formal_compounds[:2])}")
    
    return {
        'id': row_id,
        'category': category,
        'register': register,
        'cmi': cmi,
        'n_english_tokens': n_eng,
        'n_tamil_tokens': n_tam,
        'n_total_tokens': n_total,
        'formal_verb_count': formal_verb_count,
        'tamil_noun_count': len(tamil_nouns),
        'formal_pronoun_count': len(formal_pronouns),
        'formal_polite_count': len(formal_polite),
        'formal_compound_count': len(formal_compounds),
        'issues': ' | '.join(issues) if issues else '',
        'needs_fix': register != 'COLLOQUIAL',
    }


def audit_file(filepath, output_path):
    """Audit an entire CSV file and write results."""
    results = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_id = row.get('id', '')
            text = row.get('text', '')
            text_en = row.get('text_en', '')
            category = row.get('category', '')
            
            result = audit_row(row_id, text, text_en, category)
            results.append(result)
    
    # Write per-row audit
    if results:
        fieldnames = list(results[0].keys())
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
    
    return results


def generate_report(train_results, test_results, report_path):
    """Generate a human-readable audit report."""
    lines = []
    lines.append("=" * 70)
    lines.append("TAMILISH DATASET AUDIT REPORT")
    lines.append("=" * 70)
    lines.append("")
    
    for name, results in [("TRAIN", train_results), ("TEST", test_results)]:
        total = len(results)
        formal = sum(1 for r in results if r['register'] == 'FORMAL')
        mixed = sum(1 for r in results if r['register'] == 'MIXED')
        colloquial = sum(1 for r in results if r['register'] == 'COLLOQUIAL')
        needs_fix = sum(1 for r in results if r['needs_fix'])
        
        cmis = [r['cmi'] for r in results]
        avg_cmi = sum(cmis) / len(cmis) if cmis else 0
        
        lines.append(f"--- {name} SET ({total} rows) ---")
        lines.append(f"  Register distribution:")
        lines.append(f"    COLLOQUIAL:  {colloquial:5d} ({colloquial/total*100:.1f}%)")
        lines.append(f"    MIXED:       {mixed:5d} ({mixed/total*100:.1f}%)")
        lines.append(f"    FORMAL:      {formal:5d} ({formal/total*100:.1f}%)")
        lines.append(f"  Needs fix:     {needs_fix:5d} ({needs_fix/total*100:.1f}%)")
        lines.append(f"")
        lines.append(f"  Code-Mixing Index (CMI):")
        lines.append(f"    Mean:    {avg_cmi:.1f}")
        lines.append(f"    Min:     {min(cmis):.1f}")
        lines.append(f"    Max:     {max(cmis):.1f}")
        
        # CMI distribution
        cmi_0 = sum(1 for c in cmis if c == 0)
        cmi_low = sum(1 for c in cmis if 0 < c <= 10)
        cmi_mid = sum(1 for c in cmis if 10 < c <= 25)
        cmi_high = sum(1 for c in cmis if c > 25)
        lines.append(f"    CMI = 0:     {cmi_0:5d} ({cmi_0/total*100:.1f}%) — pure single-language")
        lines.append(f"    CMI 1-10:    {cmi_low:5d} ({cmi_low/total*100:.1f}%) — light mixing")
        lines.append(f"    CMI 11-25:   {cmi_mid:5d} ({cmi_mid/total*100:.1f}%) — moderate mixing")
        lines.append(f"    CMI > 25:    {cmi_high:5d} ({cmi_high/total*100:.1f}%) — heavy mixing")
        lines.append(f"")
        
        # Issue breakdown
        issue_types = Counter()
        for r in results:
            if r['formal_verb_count'] > 0:
                issue_types['formal_verbs'] += 1
            if r['tamil_noun_count'] > 0:
                issue_types['tamil_nouns_as_loanwords'] += 1
            if r['formal_pronoun_count'] > 0:
                issue_types['formal_pronouns'] += 1
            if r['formal_polite_count'] > 0:
                issue_types['formal_polite_forms'] += 1
            if r['formal_compound_count'] > 0:
                issue_types['formal_compounds'] += 1
        
        lines.append(f"  Issue breakdown (rows affected):")
        for issue, count in issue_types.most_common():
            lines.append(f"    {issue:30s}  {count:5d} ({count/total*100:.1f}%)")
        lines.append("")
        
        # Per-category breakdown
        cat_stats = defaultdict(lambda: {'total': 0, 'formal': 0, 'mixed': 0, 'cmi_sum': 0})
        for r in results:
            cat = r['category']
            cat_stats[cat]['total'] += 1
            if r['register'] == 'FORMAL':
                cat_stats[cat]['formal'] += 1
            elif r['register'] == 'MIXED':
                cat_stats[cat]['mixed'] += 1
            cat_stats[cat]['cmi_sum'] += r['cmi']
        
        lines.append(f"  Per-category register breakdown (top 15 worst):")
        lines.append(f"  {'Category':<40s} {'Total':>5s} {'Formal':>6s} {'Mixed':>6s} {'AvgCMI':>7s}")
        lines.append(f"  {'-'*40} {'-'*5} {'-'*6} {'-'*6} {'-'*7}")
        
        sorted_cats = sorted(cat_stats.items(), 
                           key=lambda x: (x[1]['formal'] + x[1]['mixed']) / x[1]['total'],
                           reverse=True)
        for cat, stats in sorted_cats[:15]:
            avg = stats['cmi_sum'] / stats['total'] if stats['total'] else 0
            lines.append(f"  {cat:<40s} {stats['total']:5d} {stats['formal']:6d} {stats['mixed']:6d} {avg:7.1f}")
        lines.append("")
    
    # Specific test-set register-split analysis
    lines.append("--- TEST SET REGISTER SPLIT ANALYSIS ---")
    if test_results:
        # Check if there's a clear boundary
        first_formal = None
        last_formal = None
        first_colloquial = None
        for i, r in enumerate(test_results):
            if r['register'] == 'FORMAL':
                if first_formal is None:
                    first_formal = i
                last_formal = i
            elif r['register'] == 'COLLOQUIAL' and first_colloquial is None:
                first_colloquial = i
        
        if first_formal is not None:
            lines.append(f"  First FORMAL row: index {first_formal} (id={test_results[first_formal]['id']})")
            lines.append(f"  Last FORMAL row:  index {last_formal} (id={test_results[last_formal]['id']})")
        if first_colloquial is not None:
            lines.append(f"  First COLLOQUIAL row: index {first_colloquial} (id={test_results[first_colloquial]['id']})")
        
        # Count formal rows in first 30 vs rest
        first30_formal = sum(1 for r in test_results[:30] if r['register'] != 'COLLOQUIAL')
        rest_formal = sum(1 for r in test_results[30:] if r['register'] != 'COLLOQUIAL')
        lines.append(f"")
        lines.append(f"  Rows 0-29: {first30_formal}/30 non-colloquial ({first30_formal/30*100:.0f}%)")
        rest_total = len(test_results) - 30
        lines.append(f"  Rows 30+:  {rest_formal}/{rest_total} non-colloquial ({rest_formal/rest_total*100:.1f}%)")
    lines.append("")
    
    report = '\n'.join(lines)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(report)
    return report


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    datasets_dir = os.path.join(base_dir, '..')
    
    train_path = os.path.join(datasets_dir, 'tamilish', 'train_labeled.csv')
    test_path = os.path.join(datasets_dir, 'tamilish', 'test_labeled.csv')
    
    out_dir = os.path.join(datasets_dir, 'tamilish', 'audit')
    os.makedirs(out_dir, exist_ok=True)
    
    print("Auditing train set...")
    train_results = audit_file(
        train_path,
        os.path.join(out_dir, 'tamilish_audit_train.csv')
    )
    print(f"  → {len(train_results)} rows audited")
    
    print("Auditing test set...")
    test_results = audit_file(
        test_path,
        os.path.join(out_dir, 'tamilish_audit_test.csv')
    )
    print(f"  → {len(test_results)} rows audited")
    
    print("\nGenerating report...")
    generate_report(
        train_results, test_results,
        os.path.join(out_dir, 'audit_report.txt')
    )
    
    print(f"\nAudit files written to: {out_dir}")
    print(f"  - tamilish_audit_train.csv")
    print(f"  - tamilish_audit_test.csv")
    print(f"  - audit_report.txt")


if __name__ == '__main__':
    main()
