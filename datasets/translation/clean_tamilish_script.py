"""
datasets/translation/clean_tamilish_script.py

Cleans and transliterates any stray Tamil-script characters (\u0B80-\u0BFF)
inside the Latin-script Tanglish (tamilish) dataset files:
  - datasets/tamilish/train_labeled.csv
  - datasets/tamilish/test_labeled.csv

Ensures 100% Roman-script Tanglish consistency.
"""
import os
import re
import pandas as pd

# Comprehensive word/substring replacement map for known Tanglish code-mixed tokens
SUBSTRING_MAP = {
    # Known mixed tokens
    "kandupடிக்க": "kandupudikka",
    "kanduபிடிக்க": "kandupudikka",
    "kanduபிடிக்க": "kandupudikka",
    "iணைக்க": "inaikka",
    "iணைப்பது": "inaippathu",
    "maாற்ற": "maattra",
    "maாற்றுவது": "maattruvathu",
    "seyalபடுத்துகிறீர்கள்": "seyalpaduthugireergal",
    "seyalபடுத்துவது": "seyalpaduthuvathu",
    "seyalபடுத்து": "seyalpaduthu",
    "paார்க்": "paarkka",
    "paக்கலாம்": "paakkalam",
    "paathaப்போ": "paathappo",
    "pannaப்போ": "pannappo",
    "pannும்போது": "pannumbothu",
    "thappானது": "thappanathu",
    "என்று": "endru",
    "ஏna": "yena",
    "ஏன்னா": "yeenna",
    "ஏற்கப்படுகிறதா": "yerkkapadukiratha",
    "ஏற்கின்றன": "yerkkindrana",
    "ஏற்கிறது": "yerkkirathu",
    "ஏற்க்குமா": "yerkkuma",
    "ஏர்க்குமா": "yerkkuma",
    "ஏற்க்கும்": "yerkkum",
    "ஏர்க்கும்": "yerkkum",
    "நடந்து": "nadanthu",
    "பண்ணனும்": "pannanum",
    "பண்ணலாம்": "pannalam",
    "பண்ண": "panna",
    "மேற்கொள்ளப்பட்டதா": "merkkollappattatha",
    "வேணும்": "venum",
    "வே": "ve",
    "டிக்க": "udikka",
    "பிடிக்க": "pudikka",
    "படுத்துவது": "paduthuvathu",
    "படுத்து": "paduthu",
    "ாற்ற": "aattra",
    "ாற்றுவது": "aattruvathu",
    "ார்க்": "aarkka",
}

# General Tamil character-to-Latin transliteration fallback
CHAR_MAP = {
    "அ": "a", "ஆ": "aa", "இ": "i", "ஈ": "ee", "உ": "u", "ஊ": "oo",
    "எ": "e", "ஏ": "ae", "ஐ": "ai", "ஒ": "o", "ஓ": "oo", "ஔ": "au",
    "க்": "k", "க": "ka", "கா": "kaa", "கி": "ki", "கீ": "kee", "கு": "ku", "கூ": "koo",
    "ங்": "ng", "ங": "nga",
    "ச்": "ch", "ச": "sa", "சா": "saa", "சி": "si", "சீ": "see", "சு": "su", "சூ": "soo",
    "ஞ்": "nj", "ஞ": "nja",
    "ட்": "t", "ட": "ta", "டா": "taa", "டி": "ti", "டீ": "tee", "டு": "tu", "டூ": "too",
    "ண்": "n", "ண": "na", "ணா": "naa", "ணி": "ni", "ணீ": "nee", "ணு": "nu", "ணூ": "noo",
    "த்": "th", "த": "tha", "தா": "thaa", "தி": "thi", "தீ": "thee", "து": "thu", "தூ": "thoo",
    "ந்": "nth", "ந": "na", "நா": "naa", "நி": "ni", "நீ": "nee", "நு": "nu", "நூ": "noo",
    "ப்": "p", "ப": "pa", "பா": "paa", "பி": "pi", "பீ": "pee", "பு": "pu", "பூ": "poo",
    "ம்": "m", "ம": "ma", "மா": "maa", "மி": "mi", "மீ": "mee", "மு": "mu", "மூ": "moo",
    "ய்": "y", "ய": "ya", "யா": "yaa", "யி": "yi", "யீ": "yee", "யு": "yu", "யூ": "yoo",
    "ர்": "r", "ர": "ra", "ரா": "raa", "ரி": "ri", "ரீ": "ree", "ரு": "ru", "ரூ": "roo",
    "ல்": "l", "ல": "la", "லா": "laa", "லி": "li", "லீ": "lee", "லு": "lu", "லூ": "loo",
    "வ்": "v", "வ": "va", "வா": "vaa", "வி": "vi", "வீ": "vee", "வு": "vu", "வூ": "voo",
    "ழ்": "zh", "ழ": "zha", "ழா": "zhaa", "ழி": "zhi", "ழீ": "zhee", "ழு": "zhu", "ழூ": "zhoo",
    "ள்": "l", "ள": "la", "ளா": "laa", "ளி": "li", "ளீ": "lee", "ளு": "lu", "ளூ": "loo",
    "ற்": "r", "ற": "ra", "றா": "raa", "றி": "ri", "றீ": "ree", "று": "ru", "றூ": "roo",
    "ன்": "n", "ன": "na", "னா": "naa", "னி": "ni", "னீ": "nee", "னு": "nu", "னூ": "noo",
    "ா": "aa", "ி": "i", "ீ": "ee", "ு": "u", "ூ": "oo", "ெ": "e", "ே": "ae", "ை": "ai",
    "ொ": "o", "ோ": "oo", "ௌ": "au", "்": "",
}

def clean_text(text: str) -> str:
    s = str(text)
    # 1. First replace known multi-char substrings
    for tamil_sub, latin_sub in SUBSTRING_MAP.items():
        if tamil_sub in s:
            s = s.replace(tamil_sub, latin_sub)
            
    # 2. Fallback: replace any remaining Tamil characters using CHAR_MAP
    if re.search(r'[\u0B80-\u0BFF]', s):
        for t_char, l_char in CHAR_MAP.items():
            if t_char in s:
                s = s.replace(t_char, l_char)
        # Remove any lingering Tamil Unicode code points if unmapped
        s = re.sub(r'[\u0B80-\u0BFF]', '', s)
        
    # Clean up double spaces or awkward spacing
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def process_file(filepath: str):
    df = pd.read_csv(filepath)
    orig_count = sum(1 for t in df["text"] if re.search(r'[\u0B80-\u0BFF]', str(t)))
    print(f"[{os.path.basename(filepath)}] Found {orig_count} rows with Tamil script characters.")
    
    df["text"] = df["text"].apply(clean_text)
    new_count = sum(1 for t in df["text"] if re.search(r'[\u0B80-\u0BFF]', str(t)))
    
    df.to_csv(filepath, index=False, encoding="utf-8")
    print(f"[{os.path.basename(filepath)}] Saved cleaned file. Remaining Tamil script rows: {new_count}")

def main():
    # datasets/translation/clean_tamilish_script.py -> datasets/translation -> datasets -> repo root.
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    train_file = os.path.join(base_dir, "datasets", "tamilish", "train_labeled.csv")
    test_file = os.path.join(base_dir, "datasets", "tamilish", "test_labeled.csv")
    
    print("=== Cleaning Tamil-Script Characters in Tamilish Dataset ===")
    process_file(train_file)
    process_file(test_file)
    print("=== Complete! ===")

if __name__ == "__main__":
    main()
