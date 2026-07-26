"""
Hybrid sentiment/priority baseline: VADER (lexicon model) + domain rule-based
cues (banking-specific keyword/pattern lists, extended from audit_sentiment.py)
+ hand-tuned combination weights.

Produces a 0-10 negativity_score (0 = neutral, 10 = severely negative) plus a
separate positive_flag, since positive tone is rare in support tickets and
collapsing it onto the same axis as negativity throws that signal away.

English text is the source of truth for scoring. The Sinhala dataset is a
verbatim-aligned translation (same text_en, same original sentiment/priority
copied over) so the English-derived score is joined onto it by text_en rather
than re-scored with a Sinhala lexicon.
"""
import csv
import os
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

HERE = os.path.dirname(os.path.abspath(__file__))
DATASETS = os.path.dirname(HERE)
EN_TRAIN = os.path.join(DATASETS, "english", "train_labeled.csv")
SI_TRAIN = os.path.join(DATASETS, "sinhala", "train_labeled.csv")
EN_OUT = os.path.join(HERE, "baseline_sentiment_priority_english.csv")
SI_OUT = os.path.join(HERE, "baseline_sentiment_priority_sinhala.csv")

# Same cue families as audit_sentiment.py, reused here as the rule-based
# ensemble member.
NEGATIVE_CUES = [
    r"unacceptable", r"ridiculous", r"terribl", r"horribl", r"\bworst\b",
    r"\bawful\b", r"\bangry\b", r"annoy", r"frustrat", r"disappoint",
    r"not happy", r"unhappy",
    r"rip.?off", r"waste of time", r"still hasn'?t", r"still has not",
    r"still haven'?t", r"still did ?n'?t", r"still don'?t have",
    r"never received", r"no one has", r"nobody has",
    r"keep waiting", r"how much longer",
    r"this is the (?:second|third|fourth)",
    r"again and again", r"over and over",
    r"\bstupid\b", r"can'?t believe", r"not acceptable",
    r"disgusted", r"outrag", r"complain", r"refuse to", r"useless",
    r"nightmare", r"appalling", r"pathetic", r"screwed", r"cheated",
    r"aggravat", r"irritat", r"fed up", r"sick of", r"tired of this",
    r"furious", r"\blivid\b", r"\bmad\b", r"\bupset\b", r"not okay",
    r"not ok\b", r"unimpressed", r"fuming",
]
WEAK_NEGATIVE_CUES = [
    r"why is this taking", r"why hasn'?t", r"why has n'?t",
    r"how long (?:is|will|does)",
]
POSITIVE_CUES = [
    r"thank you", r"\bthanks\b", r"\bgreat\b", r"\bawesome\b", r"\blove\b",
    r"amazing", r"excellent", r"\bperfect\b", r"\bhappy\b",
    r"pleased", r"wonderful", r"fantastic", r"good job", r"well done",
    r"much appreciated", r"you guys are", r"best (?:bank|service|app)",
    r"impressed", r"kudos",
]
URGENT_CUES = [
    r"\burgent\b", r"\basap\b", r"immediately", r"right away",
    r"emergency", r"\bstolen\b", r"\bfraud\b", r"unauthoriz",
    r"locked out", r"can'?t access", r"lost my (?:card|phone)",
]

neg_re = re.compile("|".join(NEGATIVE_CUES), re.IGNORECASE)
weak_neg_re = re.compile("|".join(WEAK_NEGATIVE_CUES), re.IGNORECASE)
pos_re = re.compile("|".join(POSITIVE_CUES), re.IGNORECASE)
urg_re = re.compile("|".join(URGENT_CUES), re.IGNORECASE)

analyzer = SentimentIntensityAnalyzer()


def score_text(text, category, category_mode_priority):
    vader = analyzer.polarity_scores(text)
    strong_hits = neg_re.findall(text)
    weak_hits = weak_neg_re.findall(text)
    pos_hits = pos_re.findall(text)
    urgent_hits = urg_re.findall(text)
    excl = text.count("!")

    rule_points = 0.0
    rule_points += 3.0 * min(len(strong_hits), 2)
    rule_points += 1.5 * (len(weak_hits) if len(weak_hits) >= 2 else 0)
    rule_points += 1.0 * min(excl, 2)
    rule_points += 1.0 * (1 if urgent_hits else 0)
    rule_points = min(rule_points, 10.0)

    vader_points = max(0.0, -vader["compound"]) * 10.0

    negativity = round(0.5 * vader_points + 0.5 * rule_points, 1)

    positive_flag = bool(pos_hits) and not strong_hits and vader["compound"] > 0.2
    if positive_flag:
        negativity = 0.0

    if positive_flag:
        bucket = "Positive"
    elif negativity < 2:
        bucket = "Neutral"
    elif negativity < 6:
        bucket = "Mildly Negative"
    else:
        bucket = "Severely Negative"

    # Priority in this dataset turns out to be ~97.6% determined by category
    # alone (mean per-category purity 0.976; only 280/10003 rows deviate from
    # their category's majority label) - it was assigned per-topic, not
    # per-ticket. So the baseline is the category's majority priority, and
    # content signal (urgency cues / negativity) is only used to judge
    # whether a deviation from that baseline looks like a genuine exception
    # or a likely mislabel.
    suggested_priority = category_mode_priority[category]
    has_content_support = bool(urgent_hits) or negativity >= 6

    return {
        "vader_compound": round(vader["compound"], 3),
        "negativity_score": negativity,
        "positive_flag": positive_flag,
        "suggested_sentiment": bucket,
        "suggested_priority": suggested_priority,
        "priority_content_support": has_content_support,
        "has_urgent_cue": bool(urgent_hits),
        "strong_neg_hits": "; ".join(strong_hits),
        "urgent_hits": "; ".join(urgent_hits),
    }


def compute_category_mode_priority(rows):
    counts = {}
    for row in rows:
        c = counts.setdefault(row["category"], {})
        c[row["priority"]] = c.get(row["priority"], 0) + 1
    return {cat: max(c, key=c.get) for cat, c in counts.items()}


def main():
    rows = list(csv.DictReader(open(EN_TRAIN, encoding="utf-8")))
    category_mode_priority = compute_category_mode_priority(rows)

    scored = {}
    en_out_rows = []
    for i, row in enumerate(rows):
        s = score_text(row["text"], row["category"], category_mode_priority)
        scored[row["text"]] = s
        en_out_rows.append({
            "row_index": i,
            "text": row["text"],
            "category": row["category"],
            "sentiment_existing": row["sentiment"],
            "priority_existing": row["priority"],
            **s,
        })

    fieldnames = ["row_index", "text", "category", "sentiment_existing", "priority_existing",
                  "vader_compound", "negativity_score", "positive_flag", "suggested_sentiment",
                  "suggested_priority", "priority_content_support", "has_urgent_cue",
                  "strong_neg_hits", "urgent_hits"]
    with open(EN_OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(en_out_rows)

    # "Mildly/Severely Negative" both collapse to "Negative" for comparison to the old 3-class labels
    def collapse(b):
        return "Negative" if "Negative" in b else b
    sent_disagree = [r for r in en_out_rows if collapse(r["suggested_sentiment"]) != r["sentiment_existing"]]
    # Positive -> Neutral is the dominant, high-confidence pattern (rule/VADER
    # found zero positive-tone support for the existing "Positive" label) -
    # safe to bulk-fix. Everything else genuinely needs a human read.
    sent_bulk_fix = [r for r in sent_disagree
                      if r["sentiment_existing"] == "Positive" and collapse(r["suggested_sentiment"]) == "Neutral"]
    sent_needs_review = [r for r in sent_disagree if r not in sent_bulk_fix]

    prio_deviant = [r for r in en_out_rows if r["priority_existing"] != r["suggested_priority"]]
    prio_deviant_unsupported = [r for r in prio_deviant if not r["priority_content_support"]]

    # Category-majority deviance misses tickets that are individually urgent
    # but sit in an otherwise-routine category and got the category's usual
    # (non-High) priority anyway - e.g. "I need my card ASAP!" filed under
    # card_delivery_estimate, which is Low the vast majority of the time. So
    # flag urgent-cue rows separately, regardless of category consistency.
    prio_urgent_but_not_high = [r for r in en_out_rows
                                 if r["has_urgent_cue"] and r["priority_existing"] != "High"]

    print(f"English: {len(en_out_rows)} rows scored -> {EN_OUT}")
    print(f"  sentiment disagreement vs existing 3-class label: {len(sent_disagree)} ({len(sent_disagree)/len(en_out_rows)*100:.1f}%)")
    print(f"    high-confidence Positive->Neutral bulk-fix candidates: {len(sent_bulk_fix)}")
    print(f"    needs human review: {len(sent_needs_review)}")
    print(f"  priority deviates from category majority: {len(prio_deviant)} ({len(prio_deviant)/len(en_out_rows)*100:.1f}%)")
    print(f"    of those, with no content signal to justify it (likely mislabel): {len(prio_deviant_unsupported)}")
    print(f"  priority has urgent cue but existing label isn't High: {len(prio_urgent_but_not_high)}")

    sent_fieldnames = ["row_index", "text", "category", "sentiment_existing", "suggested_sentiment",
                        "vader_compound", "negativity_score", "strong_neg_hits"]
    with open(os.path.join(HERE, "sentiment_bulk_fix_candidates.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=sent_fieldnames)
        w.writeheader()
        w.writerows({k: r[k] for k in sent_fieldnames} for r in sent_bulk_fix)
    with open(os.path.join(HERE, "sentiment_review_candidates.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=sent_fieldnames)
        w.writeheader()
        w.writerows({k: r[k] for k in sent_fieldnames} for r in sent_needs_review)

    review_fieldnames = ["row_index", "text", "category", "sentiment_existing", "priority_existing",
                          "suggested_priority", "priority_content_support", "urgent_hits", "reason"]
    review_path = os.path.join(HERE, "priority_review_candidates.csv")
    review_rows = {}
    for r in prio_deviant:
        reason = ("deviates from category majority, no urgency/negativity support - likely mislabel"
                  if not r["priority_content_support"]
                  else "deviates from category majority, but has urgency/negativity support - plausible exception")
        review_rows[r["row_index"]] = {k: r[k] for k in ["row_index", "text", "category", "sentiment_existing",
                                       "priority_existing", "suggested_priority",
                                       "priority_content_support", "urgent_hits"]} | {"reason": reason}
    for r in prio_urgent_but_not_high:
        reason = f"text has urgent cue ({r['urgent_hits']}) but priority is only {r['priority_existing']}"
        if r["row_index"] in review_rows:
            review_rows[r["row_index"]]["reason"] += f"; also: {reason}"
        else:
            review_rows[r["row_index"]] = {"row_index": r["row_index"], "text": r["text"],
                                            "category": r["category"], "sentiment_existing": r["sentiment_existing"],
                                            "priority_existing": r["priority_existing"],
                                            "suggested_priority": "High", "priority_content_support": True,
                                            "urgent_hits": r["urgent_hits"], "reason": reason}
    review_out = sorted(review_rows.values(), key=lambda r: r["row_index"])
    with open(review_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=review_fieldnames)
        w.writeheader()
        w.writerows(review_out)
    print(f"  -> {len(review_out)} priority review candidates written to {review_path}")

    # join onto Sinhala via text_en (verbatim-aligned translation)
    si_rows = list(csv.DictReader(open(SI_TRAIN, encoding="utf-8")))
    si_out_rows = []
    unmatched = 0
    for row in si_rows:
        s = scored.get(row["text_en"])
        if s is None:
            unmatched += 1
            continue
        si_out_rows.append({
            "text_en": row["text_en"],
            "text_si": row["text"],
            "category": row["category"],
            "sentiment_existing": row["sentiment"],
            "priority_existing": row["priority"],
            **s,
        })

    si_fieldnames = ["text_en", "text_si", "category", "sentiment_existing", "priority_existing",
                      "vader_compound", "negativity_score", "positive_flag", "suggested_sentiment",
                      "suggested_priority", "priority_content_support", "has_urgent_cue",
                      "strong_neg_hits", "urgent_hits"]
    with open(SI_OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=si_fieldnames)
        w.writeheader()
        w.writerows(si_out_rows)

    si_sent_disagree = sum(1 for r in si_out_rows if collapse(r["suggested_sentiment"]) != r["sentiment_existing"])
    si_prio_deviant = sum(1 for r in si_out_rows if r["priority_existing"] != r["suggested_priority"])
    print(f"Sinhala: {len(si_out_rows)} rows joined ({unmatched} unmatched) -> {SI_OUT}")
    print(f"  sentiment disagreement vs existing label: {si_sent_disagree} ({si_sent_disagree/len(si_out_rows)*100:.1f}%)")
    print(f"  priority deviates from category majority: {si_prio_deviant} ({si_prio_deviant/len(si_out_rows)*100:.1f}%)")


if __name__ == "__main__":
    main()
