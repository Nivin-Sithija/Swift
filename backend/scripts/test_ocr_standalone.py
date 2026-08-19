import asyncio
import os
import sys

import pytesseract
from PIL import Image

# Add backend directory to path so we can import the router
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.inference.services import classify


async def run_ocr_test(image_path: str):
    print("==================================================")
    print(f"Testing OCR on: {image_path}")
    print("==================================================")
    
    if not os.path.exists(image_path):
        print(f"Error: Could not find image at {image_path}")
        return
        
    try:
        # 1. Run OCR
        print("[1/2] Running Tesseract OCR...")
        img = Image.new('RGB', (100, 100)) # Dummy initialization
        img = Image.open(image_path)
        extracted_text = pytesseract.image_to_string(img, lang="eng+tam+sin").strip()
        
        print("\n--- Extracted Text ---")
        if extracted_text:
            print(extracted_text)
        else:
            print("(No text extracted - image might be blank or unreadable)")
        print("----------------------\n")
        
        # 2. Run Classification if text was found
        if extracted_text:
            print("[2/2] Running SVM Classifier (is_ocr=True)...")
            category, priority, sentiment = await classify(
                text=extracted_text,
                is_ocr=True
            )
            
            print(f"Predicted Category: {category.value}")
            print(f"Confidence Score:   {category.confidence:.2f}")
            print(f"Model Version:      {category.model_version}")
        
    except Exception as e:
        print(f"Error during processing: {e}")

if __name__ == "__main__":
    # Get the absolute path to the scripts directory
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Test on the images in the scripts folder
    asyncio.run(run_ocr_test(os.path.join(scripts_dir, "test_ocr.png")))
    
    # If they have another image, we can test it too
    test_ocr1_path = os.path.join(scripts_dir, "test_ocr1.png")
    if os.path.exists(test_ocr1_path):
        asyncio.run(run_ocr_test(test_ocr1_path))
