import os
import requests
from dotenv import load_dotenv

# Load the token from backend/.env
load_dotenv("backend/.env")
HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN or HF_TOKEN == "hf_your_actual_token_here" or HF_TOKEN == "PUT_YOUR_HUGGING_FACE_TOKEN_HERE":
    print("[ERROR] You need to put your real Hugging Face token in backend/.env!")
    exit(1)

API_URL = "https://router.huggingface.co/hf-inference/models/Swift-Support/labse-intent-1.0"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}
payload = {"inputs": "I lost my credit card yesterday, please help me cancel it"}

print(f"Sending test ticket to: {API_URL}...")
response = requests.post(API_URL, headers=headers, json=payload)

if response.status_code == 200:
    print("\n[SUCCESS] The Hugging Face Cloud API is working!")
    print("Response from Cloud:")
    print(response.json())
elif "loading" in response.text.lower():
    print("\n[WAIT] The model is currently loading into Hugging Face's server RAM. Wait 20 seconds and run this again.")
else:
    print(f"\n[FAILED] Status Code: {response.status_code}")
    print(response.text)
