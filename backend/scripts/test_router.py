import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

async def run_tests():
    print("Testing ML Router directly...")
    from app.inference.services import classify, classify_ocr_intent, fuse_intent
    
    text = "I lost my credit card yesterday, please help me cancel it"
    
    # 1. Customer text always goes to LaBSE
    print("
--- Test 1: Customer text (LaBSE) ---")
    text_intent, _, _ = await classify(text)
    print(f"Predicted Category: {text_intent.value}")
    print(f"Confidence:         {text_intent.confidence:.2f}")
    print(f"Model Version:      {text_intent.model_version}")
    if text_intent.model_version == "Swift-Support/labse-intent-1.0":
        print("Correctly routed to the Hugging Face Space.")
    else:
        print("Failed to route to LaBSE!")
        
    # 2. Attachment (OCR) text goes to the local SVM with a calibrated confidence
    print("
--- Test 2: Attachment text (SVM) ---")
    ocr_intent = classify_ocr_intent(text)
    print(f"Predicted Category: {ocr_intent.value}")
    print(f"Confidence:         {ocr_intent.confidence:.2f}")
    print(f"Model Version:      {ocr_intent.model_version}")

    # 3. Fusion keeps the customer text unless its prediction is weak
    fused = fuse_intent(text_intent, ocr_intent)
    print("
--- Test 3: Fused intent ---")
    print(f"Predicted Category: {fused.value} ({fused.model_version}, {fused.confidence:.2f})")

if __name__ == "__main__":
    asyncio.run(run_tests())
