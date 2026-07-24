import csv
import re

# Strong cues: fairly confident the row reads as Negative regardless of
# genre (explicit emotion words, or an unfulfilled expectation + fatigue
# phrasing like "still hasn't ... keep waiting").
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

# Weak cues: plausible but noisy on their own (plain informational
# "how long does it take" questions trip these) - only escalate to a
# suggestion when paired with a strong cue.
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

rows = []
with open("datasets/llm-zeroshot/english/train_labeled.csv") as f:
    r = csv.DictReader(f)
    for i, row in enumerate(r):
        row["row_index"] = i
        rows.append(row)

flags = []
for row in rows:
    text = row["text"]
    sentiment = row["sentiment"]
    priority = row["priority"]
    neg_hits = neg_re.findall(text)
    weak_neg_hits = weak_neg_re.findall(text)
    pos_hits = pos_re.findall(text)
    urg_hits = urg_re.findall(text)
    excl = text.count("!")
    qmarks = text.count("?")

    reasons = []
    suggested_sentiment = None

    if sentiment == "Neutral" and neg_hits:
        suggested_sentiment = "Negative"
        reasons.append(f"neg cues: {neg_hits}")
    elif sentiment == "Neutral" and weak_neg_hits and len(weak_neg_hits) >= 2:
        # two independent "weary/impatient" markers stacked is a decent signal
        # even without a strong lexical cue
        suggested_sentiment = "Negative?"
        reasons.append(f"stacked weak cues: {weak_neg_hits}")
    if sentiment == "Neutral" and pos_hits and not neg_hits:
        suggested_sentiment = "Positive"
        reasons.append(f"pos cues: {pos_hits}")
    if sentiment == "Positive" and neg_hits and not pos_hits:
        suggested_sentiment = "Negative?"
        reasons.append(f"neg cues in Positive-labeled: {neg_hits}")
    if sentiment == "Negative" and pos_hits and not neg_hits:
        suggested_sentiment = "Positive?"
        reasons.append(f"pos cues in Negative-labeled: {pos_hits}")
    if excl >= 2 and sentiment == "Neutral":
        reasons.append(f"{excl} exclamation marks")
        suggested_sentiment = suggested_sentiment or "Negative"

    suggested_priority = None
    if priority == "Low" and urg_hits:
        suggested_priority = "Medium/High?"
        reasons.append(f"urgent cues in Low priority: {urg_hits}")

    if reasons:
        flags.append({
            "row_index": row["row_index"],
            "text": text,
            "category": row["category"],
            "sentiment": sentiment,
            "suggested_sentiment": suggested_sentiment or "",
            "priority": priority,
            "suggested_priority": suggested_priority or "",
            "reasons": "; ".join(reasons),
        })

print(f"Total rows: {len(rows)}")
print(f"Flagged rows: {len(flags)}")

with open("datasets/translation/sentiment_audit_candidates.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["row_index", "text", "category", "sentiment", "suggested_sentiment", "priority", "suggested_priority", "reasons"])
    w.writeheader()
    for row in flags:
        w.writerow(row)
