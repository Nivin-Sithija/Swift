import os
import zipfile

root_dir = r"c:\Users\ASUS\Desktop\Swif Shazan\Swift"
zip_path = os.path.join(root_dir, "swift_kaggle_package.zip")

def should_include(path):
    # Exclude unnecessary heavy directories
    excludes = ['node_modules', 'venv', '.venv', '.git', '__pycache__', 'models', 'swift_kaggle_package.zip']
    for ex in excludes:
        if f"\\{ex}\\" in path or path.endswith(f"\\{ex}"):
            return False
            
    # Include only ml and datasets
    if path.startswith(os.path.join(root_dir, "ml")) or path.startswith(os.path.join(root_dir, "datasets")):
        return True
        
    return False

print(f"Creating zip file at {zip_path}...")
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for foldername, subfolders, filenames in os.walk(root_dir):
        for filename in filenames:
            file_path = os.path.join(foldername, filename)
            if should_include(file_path):
                # Add file to zip with relative path
                arcname = os.path.relpath(file_path, root_dir)
                zf.write(file_path, arcname)

print(f"Zip created successfully! Size: {os.path.getsize(zip_path) / (1024*1024):.2f} MB")
