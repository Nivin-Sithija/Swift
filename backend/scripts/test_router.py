import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

async def run_tests():
    print("Testing ML Router directly...")
    from app.inference.services import classify
    
    text = "I lost my credit card yesterday, please help me cancel it"
    
    # 1. Test Digital Text (Should route to LaBSE)
    print("\n--- Test 1: Digital Text (is_ocr = False) ---")
    intent, _, _ = await classify(text, is_ocr=False)
    print(f"Predicted Category: {intent.value}")
    print(f"Model Version: {intent.model_version}")
    if intent.model_version == "Swift-Support/labse-intent-1.0":
        print("Correctly routed to the Hugging Face Space.")
    else:
        print("Failed to route to LaBSE!")
        
    # 2. Test OCR Text (Should route to SVM)
    print("\n--- Test 2: OCR Text (is_ocr = True) ---")
    intent, _, _ = await classify(text, is_ocr=True)
    print(f"Predicted Category: {intent.value}")
    print(f"Model Version: {intent.model_version}")
    if intent.model_version == "svm-intent-1.0":
        print("Correctly routed to SVM.")
    else:
        print("Failed to route to SVM!")

if __name__ == "__main__":
    asyncio.run(run_tests())
