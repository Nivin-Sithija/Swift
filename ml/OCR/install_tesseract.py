import urllib.request
import os
import subprocess
from pathlib import Path

def install_tesseract():
    installer_url = "https://github.com/UB-Mannheim/tesseract/releases/download/v5.4.0.20240606/tesseract-ocr-w64-setup-5.4.0.20240606.exe"
    installer_path = "tesseract_installer.exe"
    
    tess_dir = r"C:\Program Files\Tesseract-OCR"
    tess_exe = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    tessdata_dir = r"C:\Program Files\Tesseract-OCR\tessdata"
    
    if not os.path.exists(tess_exe):
        print("Downloading Tesseract installer...")
        urllib.request.urlretrieve(installer_url, installer_path)
        print("Installing Tesseract silently...")
        subprocess.run([installer_path, "/S"], check=True)
        print("Tesseract installed.")
    else:
        print("Tesseract already installed.")
        
    print("Downloading language packs...")
    langs = {
        "sin.traineddata": "https://github.com/tesseract-ocr/tessdata_best/raw/main/sin.traineddata",
        "tam.traineddata": "https://github.com/tesseract-ocr/tessdata_best/raw/main/tam.traineddata"
    }
    
    for lang, url in langs.items():
        dest = os.path.join(tessdata_dir, lang)
        if not os.path.exists(dest):
            print(f"Downloading {lang}...")
            urllib.request.urlretrieve(url, dest)
            print(f"Saved to {dest}")
        else:
            print(f"{lang} already exists.")
            
    print("Done! Tesseract setup complete.")

if __name__ == "__main__":
    install_tesseract()
