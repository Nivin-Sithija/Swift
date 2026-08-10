import json
import os
import pandas as pd
from PIL import Image, ImageFilter
from pathlib import Path

def main():
    root_dir = Path(__file__).parent.resolve()
    labels_path = root_dir / "labels.json"
    metadata_csv_path = root_dir / "metadata.csv"
    aug_dir = root_dir / "screenshots" / "augmented"
    aug_dir.mkdir(parents=True, exist_ok=True)
    
    with open(labels_path, "r", encoding="utf-8") as f:
        labels = json.load(f)
        
    records = []
    
    def get_script(lang):
        lang_lower = lang.lower()
        if "sinhala" in lang_lower: return "Sinhala"
        if "tamilish" in lang_lower: return "Latin"
        if "tamil" in lang_lower: return "Tamil"
        return "Latin"
        
    for item in labels:
        img_path_rel = item["image_path"]
        orig_img_path = root_dir / img_path_rel
        if not orig_img_path.exists():
            continue
            
        base_name = orig_img_path.stem # e.g. synthetic_bank_0001
        
        # ID is usually the digits at the end
        img_id = base_name.split("_")[-1]
        primary_lang = item.get("language", "English")
        scripts = get_script(primary_lang)
        ground_truth = item.get("visible_text", "")
        
        # Original (clean)
        records.append({
            "id": img_id,
            "image_path": img_path_rel,
            "primary_language": primary_lang,
            "scripts": scripts,
            "condition": "clean",
            "ground_truth": ground_truth
        })
        
        # Load image for augmentations
        try:
            img = Image.open(orig_img_path).convert("RGB")
        except Exception as e:
            print(f"Failed to open {orig_img_path}: {e}")
            continue
            
        # 1. Blur
        blur_path = f"screenshots/augmented/{base_name}_blur.png"
        img_blur = img.filter(ImageFilter.GaussianBlur(radius=1.5))
        img_blur.save(root_dir / blur_path)
        records.append({
            "id": img_id,
            "image_path": blur_path,
            "primary_language": primary_lang,
            "scripts": scripts,
            "condition": "blur",
            "ground_truth": ground_truth
        })
        
        # 2. Rotation (5 degrees)
        rot_path = f"screenshots/augmented/{base_name}_rot.png"
        # Rotate expands bounding box and fills with white
        img_rot = img.rotate(5, expand=True, fillcolor=(255, 255, 255))
        img_rot.save(root_dir / rot_path)
        records.append({
            "id": img_id,
            "image_path": rot_path,
            "primary_language": primary_lang,
            "scripts": scripts,
            "condition": "rotation",
            "ground_truth": ground_truth
        })
        
        # 3. Low Resolution (scale down to 30%, then scale back up)
        lowres_path = f"screenshots/augmented/{base_name}_lowres.png"
        orig_size = img.size
        img_small = img.resize((int(orig_size[0]*0.3), int(orig_size[1]*0.3)), Image.Resampling.BILINEAR)
        img_lowres = img_small.resize(orig_size, Image.Resampling.NEAREST)
        img_lowres.save(root_dir / lowres_path)
        records.append({
            "id": img_id,
            "image_path": lowres_path,
            "primary_language": primary_lang,
            "scripts": scripts,
            "condition": "low-resolution",
            "ground_truth": ground_truth
        })
        
    df = pd.DataFrame(records)
    df.to_csv(metadata_csv_path, index=False)
    print(f"Generated {len(records)} metadata records (with augmentations) in metadata.csv")

if __name__ == "__main__":
    main()
