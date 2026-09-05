import asyncio
import os
import httpx
from PIL import Image, ImageDraw, ImageFont

async def create_test_image(filename: str):
    """Creates a temporary image with fake PII for testing."""
    img = Image.new('RGB', (400, 200), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    # Adding fake PII
    text = (
        "Name: John Doe\n"
        "Credit Card: 1234-5678-9012-3456\n"
        "Email: john.doe@example.com\n"
        "Phone: +1-555-123-4567\n"
        "Please update my account."
    )
    d.text((10, 10), text, fill=(0, 0, 0))
    img.save(filename)

async def test_masking_endpoint(engine: str = "tesseract"):
    print(f"\n--- Testing Endpoint with Engine: {engine} ---")
    image_filename = 'temp_pii_test.png'
    await create_test_image(image_filename)

    try:
        async with httpx.AsyncClient() as client:
            with open(image_filename, 'rb') as f:
                print("Sending image to /api/v1/ocr/test-masking...")
                response = await client.post(
                    f"http://localhost:8000/api/v1/ocr/test-masking?engine={engine}",
                    files={"file": (image_filename, f, "image/png")},
                    timeout=30.0
                )
                
            if response.status_code == 200:
                data = response.json()
                print("\n✅ Success!")
                print("Engine Used:", data.get("engine_used"))
                print("-" * 30)
                print("RAW TEXT FROM OCR:\n", data.get("raw_text"))
                print("-" * 30)
                print("MASKED TEXT (PII Redacted):\n", data.get("masked_text"))
            else:
                print("❌ Failed:", response.status_code, response.text)
    finally:
        if os.path.exists(image_filename):
            os.remove(image_filename)

if __name__ == "__main__":
    # Test with default Tesseract
    asyncio.run(test_masking_endpoint(engine="tesseract"))
    
    # You can also test with Google Vision if your API key is configured
    # asyncio.run(test_masking_endpoint(engine="google_vision"))
