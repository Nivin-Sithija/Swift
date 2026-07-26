import os
import time
import pandas as pd
from tqdm.auto import tqdm
from dotenv import load_dotenv

from pydantic import BaseModel
from google import genai
from google.genai import types

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SCRIPT_DIR, ".env"), override=True)

class Translation(BaseModel):
    tamil: str
    tanglish: str

class BatchTranslation(BaseModel):
    translations: list[Translation]

MODEL = "gemini-3.5-flash"

SYSTEM_PROMPT = """
You are an expert English → Tamil translator.

Translate every sentence into:
1. Natural Sri Lankan Tamil (accurate, preserving context exactly without omitting meaning)
2. Tanglish (Tamil written using English letters, natural typing style)

Rules:
• Preserve the exact meaning and context of the original sentence.
• Do not omit words or change the intent.
• Banking/technical terminology should sound natural in context.
• Do NOT explain anything.
• Return only the JSON schema.
"""

class KeyManager:
    def __init__(self):
        self.keys = []
        
        # 1. Check GEMINI_API_KEYS (comma separated)
        keys_str = os.getenv("GEMINI_API_KEYS", "")
        if keys_str:
            for k in keys_str.split(","):
                k_clean = k.strip()
                if k_clean and k_clean != "your_first_api_key_here" and k_clean not in self.keys:
                    self.keys.append(k_clean)
                    
        # 2. Check individual GEMINI_API_KEY* variables
        for var, val in os.environ.items():
            if var.startswith("GEMINI_API_KEY") and val:
                val_clean = val.strip()
                if val_clean and not val_clean.startswith("your_") and val_clean not in self.keys:
                    self.keys.append(val_clean)
                    
        if not self.keys:
            raise ValueError("No valid API keys found in .env! Please add at least one API key to GEMINI_API_KEYS in .env.")
            
        self.current_idx = 0
        self.client = genai.Client(api_key=self.keys[self.current_idx])
        print(f"Loaded {len(self.keys)} API key(s) from .env. Starting with API Key #1.")

    def get_client(self):
        return self.client

    def rotate_key(self):
        if len(self.keys) == 1:
            print("Only 1 API key available. Waiting 60 seconds before retrying...")
            time.sleep(60)
            return
            
        self.current_idx = (self.current_idx + 1) % len(self.keys)
        print(f"--> Quota reached! Switching to API Key #{self.current_idx + 1} of {len(self.keys)}...")
        self.client = genai.Client(api_key=self.keys[self.current_idx])
        
        # If we cycled all the way back to key #1, pause briefly so quotas can refresh
        if self.current_idx == 0:
            print("Cycled through all API keys! Waiting 45 seconds for quota reset before continuing...")
            time.sleep(45)

    def remove_current_key(self):
        if len(self.keys) <= 1:
            print("Warning: Only 1 API key remaining and it returned an error! Waiting 60s before retrying...")
            time.sleep(60)
            return
        bad_key = self.keys.pop(self.current_idx)
        print(f"--> [Warning] Removed invalid/unauthenticated API key from rotation ({len(self.keys)} keys remaining).")
        self.current_idx = self.current_idx % len(self.keys)
        self.client = genai.Client(api_key=self.keys[self.current_idx])


def translate_batch(client, sentences):
    numbered = "\n".join(
        f"{i+1}. {s}"
        for i, s in enumerate(sentences)
    )

    response = client.models.generate_content(
        model=MODEL,
        contents=f"""
{SYSTEM_PROMPT}

Translate these sentences:

{numbered}
""",
        config=types.GenerateContentConfig(
            temperature=0.2,
            response_mime_type="application/json",
            response_schema=BatchTranslation,
        ),
    )

    return response.parsed

def load_csv(path):
    for enc in ["utf-8-sig", "utf-8", "latin1"]:
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            continue
    return pd.read_csv(path)

def main():
    INPUT_FILE = os.path.join(SCRIPT_DIR, "test.csv")
    OUTPUT_FILE = os.path.join(SCRIPT_DIR, "translated_test.csv")
    
    # Load or resume dataset
    if os.path.exists(OUTPUT_FILE):
        print(f"Resuming from existing '{OUTPUT_FILE}'...")
        df = load_csv(OUTPUT_FILE)
    else:
        print(f"Loading original '{INPUT_FILE}'...")
        df = load_csv(INPUT_FILE)
        
    for col in ["tamil", "tanglish", "translation_status", "model"]:
        if col not in df.columns:
            df[col] = ""
            
    df["translation_status"] = df["translation_status"].fillna("")
    
    remaining = df[df["translation_status"] != "completed"].index.tolist()
    print(f"Total rows remaining to translate: {len(remaining)} / {len(df)}")
    
    if len(remaining) == 0:
        print("All rows are already translated!")
        return

    key_manager = KeyManager()
    
    BATCH_SIZE = 40
    
    for start in tqdm(range(0, len(remaining), BATCH_SIZE), desc="Translating batches"):
        batch_idx = remaining[start:start+BATCH_SIZE]
        sentences = df.loc[batch_idx, "text"].tolist()
        
        success = False
        retry_count = 0
        while not success:
            try:
                client = key_manager.get_client()
                result = translate_batch(client, sentences)
                
                if len(result.translations) != len(batch_idx):
                    print(f"Warning: Expected {len(batch_idx)} translations, got {len(result.translations)}. Retrying...")
                    time.sleep(2)
                    continue
                    
                for idx, translation in zip(batch_idx, result.translations):
                    df.at[idx, "tamil"] = translation.tamil
                    df.at[idx, "tanglish"] = translation.tanglish
                    df.at[idx, "translation_status"] = "completed"
                    df.at[idx, "model"] = MODEL
                    
                success = True
                
            except Exception as e:
                err_str = str(e)
                print(f"\n[Error encountered]: {err_str[:120]}...")
                err_lower = err_str.lower()
                if any(x in err_lower for x in ["401", "unauthenticated", "403", "permission_denied", "invalid"]):
                    key_manager.remove_current_key()
                    retry_count = 0
                elif any(x in err_lower for x in ["429", "resource_exhausted", "quota"]):
                    key_manager.rotate_key()
                    retry_count = 0
                else:
                    retry_count += 1
                    if retry_count >= 3:
                        print("Persistent error on current key after 3 attempts. Rotating API key...")
                        key_manager.rotate_key()
                        retry_count = 0
                    else:
                        print(f"Temporary network/API issue. Waiting 5 seconds before retry ({retry_count}/3)...")
                        time.sleep(5)
                    
        # Save after every batch using utf-8-sig (with BOM) so Excel opens it without mojibake
        df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
        time.sleep(1)
        
    print(f"\nAll done! Translated dataset saved as '{OUTPUT_FILE}' (with Excel-readable UTF-8 BOM encoding).")

if __name__ == "__main__":
    main()
