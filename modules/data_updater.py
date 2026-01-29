import os
import requests
import zipfile
import shutil
from PyQt6.QtCore import QObject, pyqtSignal

class DataUpdateWorker(QObject):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, download_url, target_dir):
        super().__init__()
        self.download_url = download_url
        self.target_dir = target_dir

    def run(self):
        temp_zip = os.path.join(self.target_dir, "temp_data.zip")
        try:
            self.status.emit("Connecting...")
            response = requests.get(self.download_url, stream=True, timeout=15)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            self.status.emit("Downloading data...")
            with open(temp_zip, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            self.progress.emit(int((downloaded / total_size) * 100))
            
            self.status.emit("Extracting files...")
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                # Extract to a temporary folder first to avoid half-overwrites if something fails
                extract_path = os.path.join(self.target_dir, "temp_extract")
                if os.path.exists(extract_path):
                    shutil.rmtree(extract_path)
                os.makedirs(extract_path)
                
                zip_ref.extractall(extract_path)
                
                # Move files from temp_extract to target_dir
                # Note: The zip usually contains folders like 'items', 'hideout', etc.
                for item in os.listdir(extract_path):
                    s = os.path.join(extract_path, item)
                    d = os.path.join(self.target_dir, item)
                    if os.path.isdir(s):
                        if os.path.exists(d):
                            shutil.rmtree(d)
                        shutil.move(s, d)
                    else:
                        if os.path.exists(d):
                            os.remove(d)
                        shutil.move(s, d)
                
                shutil.rmtree(extract_path)

            if os.path.exists(temp_zip):
                os.remove(temp_zip)
                
            self.finished.emit(True, "Update successful!")
            
        except Exception as e:
            if os.path.exists(temp_zip):
                try: os.remove(temp_zip)
                except: pass
            self.finished.emit(False, str(e))
