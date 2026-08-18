import re
from dataclasses import dataclass
from pathlib import Path
import joblib
import torch
from transformers import pipeline

from app.domain.enums import LanguageForm, Priority, Sentiment

_labse_pipeline = None
_svm_pipeline = None


@dataclass(frozen=True)
class Result:
    value: str
    confidence: float
    model_version: str


SINHALA = re.compile(r"[\u0D80-\u0DFF]")
TAMIL = re.compile(r"[\u0B80-\u0BFF]")
LATIN = re.compile(r"[A-Za-z]")


def detect_language(text: str) -> Result:
    si, ta, en = len(SINHALA.findall(text)), len(TAMIL.findall(text)), len(LATIN.findall(text))
    if si and en:
        value = LanguageForm.code_mixed
    elif ta and en:
        value = LanguageForm.code_mixed
    elif si:
        value = LanguageForm.sinhala
    elif ta:
        value = LanguageForm.tamil
    elif en:
        lowered = text.lower()
        if any(x in lowered for x in ("eka", "naha", "mage", "karanna", "wela")):
            value = LanguageForm.singlish
        elif any(x in lowered for x in ("enna", "panna", "varala", "mudiyala", "aayiduchu")):
            value = LanguageForm.tanglish
        else:
            value = LanguageForm.english
    else:
        value = LanguageForm.unknown
    return Result(value.value, 0.90 if value != LanguageForm.unknown else 0.30, "unicode-rules-1.0")


def classify(text: str, is_ocr: bool = False) -> tuple[Result, Result, Result]:
    global _labse_pipeline, _svm_pipeline
    
    ml_dir = Path("/app/ml")
    if not ml_dir.exists():
        ml_dir = Path(__file__).resolve().parents[3] / "ml"
    
    # 1. Intent Classification Router
    if is_ocr:
        # Route OCR text to SVM
        if _svm_pipeline is None:
            svm_path = ml_dir / "models" / "tfidf_linear_svm_all.joblib"
            _svm_pipeline = joblib.load(svm_path)
            
        pred = _svm_pipeline.predict([text])[0]
        intent_result = Result(pred, 0.85, "svm-intent-1.0")
    else:
        # Route digital text to LaBSE Transformer
        labse_path = ml_dir / "models" / "encoders" / "intent_labse" / "best_model"
        
        # 1. Local Fallback
        if labse_path.exists():
            if _labse_pipeline is None:
                device = 0 if torch.cuda.is_available() else -1
                _labse_pipeline = pipeline(
                    "text-classification", 
                    model=str(labse_path), 
                    tokenizer=str(labse_path), 
                    device=device,
                    truncation=True,
                    max_length=128
                )
            res = _labse_pipeline(text)[0]
            intent_result = Result(res["label"], res["score"], "labse-intent-1.0")
            
        # 2. Serverless Cloud Fallback 
        else:
            import requests
            import os
            API_URL = "https://router.huggingface.co/hf-inference/models/Swift-Support/labse-intent-1.0"
            HF_TOKEN = os.getenv("HF_TOKEN", "PUT_YOUR_HUGGING_FACE_TOKEN_HERE")
            
            headers = {"Authorization": f"Bearer {HF_TOKEN}"}
            
            try:
                # Send the text directly to Hugging Face's servers
                response = requests.post(API_URL, headers=headers, json={"inputs": text})
                
                if response.status_code == 200:
                    # The API returns a list of lists, we grab the top prediction
                    res = response.json()[0][0]
                    intent_result = Result(res["label"], res["score"], "labse-intent-1.0-cloud-api")
                else:
                    print(f"Hugging Face API Error: {response.text}")
                    intent_result = Result("unknown_intent", 0.0, "api_error")
            except Exception as e:
                print(f"Failed to connect to Hugging Face: {e}")
                intent_result = Result("unknown_intent", 0.0, "connection_error")

    # 2. Priority & Sentiment (Keeping mocked for now)
    lowered = text.lower()
    critical = any(
        x in lowered for x in ("fraud", "stolen", "not recognise", "unauthorised", "unauthorized")
    )
    negative = any(
        x in lowered for x in ("failed", "deduct", "missing", "blocked", "නැහැ", "தோல்வி")
    )
    return (
        intent_result,
        Result(
            (
                Priority.critical if critical else Priority.high if negative else Priority.medium
            ).value,
            0.68,
            "development-rules-priority-1.0",
        ),
        Result(
            (Sentiment.negative if negative else Sentiment.neutral).value,
            0.66,
            "development-rules-sentiment-1.0",
        ),
    )


def response_template(language: str) -> str:
    templates = {
        "sinhala": "අප හා සම්බන්ධ වීම ගැන ස්තුතියි. ඔබ ලබා දුන් තොරතුරු සහාය නිලධාරියෙකු විසින් සමාලෝචනය කරනු ඇත. මෙම පණිවිඩය කිසිදු බැංකු ක්‍රියාවක් සම්පූර්ණ වූ බව තහවුරු නොකරයි.",
        "tamil": "எங்களைத் தொடர்புகொண்டதற்கு நன்றி. நீங்கள் வழங்கிய தகவலை ஆதரவு அலுவலர் சரிபார்ப்பார். இந்தச் செய்தி எந்த வங்கிச் செயலும் நிறைவடைந்ததை உறுதிப்படுத்தவில்லை.",
        "english": "Thank you for contacting Swift Support. A support agent will review the information you provided. This message does not confirm that any banking action has been completed.",
    }
    return templates.get(language, templates["english"])
