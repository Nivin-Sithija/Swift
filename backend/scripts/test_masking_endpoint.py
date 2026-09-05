import asyncio
import os
import sys
import httpx

async def test_masking_endpoint(image_path: str, engine: str = "tesseract"):
    print(f"\n--- Testing Endpoint with Engine: {engine} ---")
    print(f"Using Image: {image_path}")

    if not os.path.exists(image_path):
        print(f"[ERROR] File not found at '{image_path}'")
        sys.exit(1)

    try:
        async with httpx.AsyncClient() as client:
            with open(image_path, 'rb') as f:
                print("Sending image to /api/v1/ocr/test-masking...")
                response = await client.post(
                    f"http://localhost:8000/api/v1/ocr/test-masking?engine={engine}",
                    files={"file": (os.path.basename(image_path), f, "image/png")}, # Assuming PNG or JPEG
                    timeout=30.0
                )
                
            if response.status_code == 200:
                data = response.json()
                print("\n[SUCCESS]")
                print("Engine Used:", data.get("engine_used"))
                print("-" * 30)
                print("RAW TEXT FROM OCR:\n", data.get("raw_text"))
                print("-" * 30)
                print("MASKED TEXT (PII Redacted):\n", data.get("masked_text"))
            else:
                print("[FAILED]", response.status_code, response.text)
    except Exception as e:
        print(f"[ERROR] during request: {repr(e)}")

if __name__ == "__main__":
    # Hardcoded path to the test image located in the same scripts/ directory
    image_path = os.path.join(os.path.dirname(__file__), "test_ocr.png")
    
    # Change to "google_vision" if you want to test the Google API
    engine_choice = "tesseract"
    
    asyncio.run(test_masking_endpoint(image_path, engine=engine_choice))
