import sys
import requests
import os
from PIL import Image, ImageDraw

# ==============================================================================
# CONFIGURATION
# ==============================================================================
TICKET_ID = "PASTE_YOUR_TICKET_ID_HERE"
API_URL = "http://localhost:8000" # Change if your server runs on a different port
AUTH_TOKEN = "PASTE_YOUR_BEARER_TOKEN_HERE" # Get this from your browser/Postman
# ==============================================================================

def run_tests():
    if TICKET_ID == "PASTE_YOUR_TICKET_ID_HERE":
        print("Please paste your TICKET_ID in the script first!")
        return

    print("Generating a test image with text...")
    img = Image.new('RGB', (500, 100), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    # This text will map to "cancel_transfer" via SVM because of "cancel"
    text_content = "I lost my credit card yesterday, please help me cancel it"
    d.text((10, 10), text_content, fill=(0, 0, 0))
    img.save('test_ocr.png')
    
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}"
    }

    print(f"\nUploading the test image to ticket {TICKET_ID}...")
    with open('test_ocr.png', 'rb') as f:
        res = requests.post(
            f"{API_URL}/api/v1/tickets/{TICKET_ID}/attachments", 
            headers=headers,
            files={"file": ("test_ocr.png", f, "image/png")}
        )
        
    if res.status_code != 201:
        print(f"Failed to upload! Status: {res.status_code}, Response: {res.text}")
        return
        
    print("Upload successful!")
    
    print("\nFetching the updated ticket...")
    response = requests.get(f"{API_URL}/api/v1/tickets/{TICKET_ID}", headers=headers)
    
    if response.status_code == 200:
        ticket_data = response.json()
        print("\n--- Final Results ---")
        print(f"Original Text:\n{ticket_data.get('original_text')}")
        print(f"Final Category Predicted: {ticket_data.get('category', {}).get('value')}")
        print(f"Final Model Version: {ticket_data.get('category', {}).get('model_version')}")
    else:
        print(f"Failed to fetch ticket! Status: {response.status_code}")
    
    # Clean up
    os.remove('test_ocr.png')
    
if __name__ == "__main__":
    run_tests()
