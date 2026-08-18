import urllib.request
import zipfile
import os
from pathlib import Path

# Provide the public URL to your zipped models here (e.g. AWS S3, Google Drive direct link, or GitHub Release Asset)
# The zip should contain the contents of the `Swift/ml/models` directory.
MODEL_URL = "https://example.com/path/to/models.zip"
DOWNLOAD_PATH = "models.zip"
TARGET_DIR = Path(__file__).parent.parent.parent / "ml" / "models"

def main():
    if MODEL_URL == "https://example.com/path/to/models.zip":
        print("Please update MODEL_URL in scripts/download_weights.py with your actual upload link.")
        return

    print(f"Downloading ML model weights from {MODEL_URL}...")
    urllib.request.urlretrieve(MODEL_URL, DOWNLOAD_PATH)
    
    print(f"Extracting weights to {TARGET_DIR.absolute()}...")
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(DOWNLOAD_PATH, 'r') as zip_ref:
        zip_ref.extractall(TARGET_DIR)
        
    print("Cleaning up...")
    os.remove(DOWNLOAD_PATH)
    
    print("Done! The server is now ready to run inference.")

if __name__ == "__main__":
    main()
