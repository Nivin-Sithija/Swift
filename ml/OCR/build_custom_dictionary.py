import os
import re
from collections import Counter
import pandas as pd

LANGUAGES = ["english", "sinhala", "singlish", "tamil", "tamilish"]
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATASETS_DIR = os.path.join(REPO_ROOT, "datasets")
RESULTS_DIR = os.path.join(REPO_ROOT, "ml", "OCR", "results")

def build_dictionary():
    word_counts = Counter()
    print("Building custom SymSpell dictionary from training data...")
    
    for lang in LANGUAGES:
        train_path = os.path.join(DATASETS_DIR, lang, "train_labeled.csv")
        if not os.path.exists(train_path):
            print(f"Skipping missing dataset: {train_path}")
            continue
            
        df = pd.read_csv(train_path)
        print(f"Processing {lang}: {len(df)} rows")
        
        for text in df["text"].dropna():
            # Extract alphabetic words only (supports Unicode letters for Sinhala/Tamil)
            words = re.findall(r'[^\W\d_]+', str(text).lower())
            word_counts.update(words)
            
    print(f"Total unique words extracted: {len(word_counts)}")
    
    # Ensure results directory exists
    os.makedirs(RESULTS_DIR, exist_ok=True)
    dict_path = os.path.join(RESULTS_DIR, "custom_symspell_dict.txt")
    
    # Save to SymSpell dictionary format: "word count"
    with open(dict_path, "w", encoding="utf-8") as f:
        # Sort by frequency descending
        for word, count in word_counts.most_common():
            f.write(f"{word} {count}\n")
            
    print(f"Dictionary saved to {dict_path}")

if __name__ == "__main__":
    build_dictionary()
