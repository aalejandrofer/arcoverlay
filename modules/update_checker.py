from PyQt6.QtCore import QObject, pyqtSignal
import requests
import json
import os
from .constants import Constants

class UpdateChecker(QObject):
    """
    Runs on a background thread to check for and download data updates
    from the GitHub repository without freezing the UI.
    """
    checking_for_updates = pyqtSignal()
    update_check_finished = pyqtSignal(list, str)
    download_progress = pyqtSignal(int, int, str)
    update_complete = pyqtSignal(bool, str)

    def __init__(self):
        super().__init__()
        self.local_versions = self._load_local_versions()

    def _load_local_versions(self):
        """Loads the local versions.json file, or returns an empty dict if not found."""
        versions_path = os.path.join(Constants.DATA_DIR, 'versions.json')
        if os.path.exists(versions_path):
            try:
                with open(versions_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def get_remote_commit_date(self):
        """Fetches the latest commit date from the GitHub repository."""
        try:
            repo_api_url = "https://api.github.com/repos/RaidTheory/arcraiders-data/commits/main"
            response = requests.get(repo_api_url, timeout=10)
            response.raise_for_status()
            commit_data = response.json()
            # ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ
            date_str = commit_data['commit']['committer']['date']
            return date_str
        except Exception as e:
            print(f"Error fetching remote date: {e}")
            return None

    def get_local_data_date(self):
        """Reads the locally saved last-update timestamp."""
        version_path = os.path.join(Constants.DATA_DIR, 'data_version.json')
        if os.path.exists(version_path):
            try:
                with open(version_path, 'r') as f:
                    data = json.load(f)
                    return data.get('last_updated')
            except: pass
        return None

    def save_local_data_date(self, date_str):
        """Saves the current timestamp as the last update time."""
        version_path = os.path.join(Constants.DATA_DIR, 'data_version.json')
        try:
            with open(version_path, 'w') as f:
                json.dump({'last_updated': date_str}, f)
        except Exception as e:
            print(f"Error saving local date: {e}")

    def run_check(self):
        """Checks if we can reach GitHub, then offers a full refresh since versions.json is deprecated."""
        self.checking_for_updates.emit()
        # Just check connection for the manual button
        try:
            repo_api_url = "https://api.github.com/repos/RaidTheory/arcraiders-data"
            requests.get(repo_api_url, timeout=10).raise_for_status()
            self.update_check_finished.emit([{'path': 'FULL_SYNC', 'sha': 'zip'}], "Connection established. A full data refresh is available.")
        except requests.exceptions.RequestException as e:
            self.update_check_finished.emit([], f"Error: Could not connect to GitHub. ({e})")

    def check_for_updates_startup(self):
        """
        Signals update_available(True/False, msg) based on date comparison.
        Intended for automatic startup check.
        """
        remote_date = self.get_remote_commit_date()
        if not remote_date:
            return # Silent fail on startup

        local_date = self.get_local_data_date()
        
        # Simple string comparison works for ISO 8601
        if local_date is None or remote_date > local_date:
            self.update_check_finished.emit([{'path': 'FULL_SYNC', 'sha': 'zip'}], f"New data available ({remote_date})")
        else:
            # Up to date
            pass

    def download_updates(self, files_to_download):
        """Downloads the entire database as a ZIP and extracts it, replacing the old incremental logic."""
        import zipfile
        import io
        import shutil
        from pathlib import Path

        self.download_progress.emit(0, 100, "Downloading latest game data ZIP...")
        
        repo_url = "https://github.com/RaidTheory/arcraiders-data/archive/refs/heads/main.zip"
        data_dir = Path(Constants.DATA_DIR)

        try:
            resp = requests.get(repo_url, timeout=60)
            resp.raise_for_status()
            
            self.download_progress.emit(50, 100, "Extracting updates...")
            
            with zipfile.ZipFile(io.BytesIO(resp.content)) as zip_ref:
                root_folder = zip_ref.namelist()[0].split('/')[0]
                
                # Managed paths mapping (ZIP folder -> Local subfolder)
                sync_map = {
                    "items/": "items",
                    "projects.json": "projects.json",
                    "quests/": "quests",
                    "hideout/": "hideout",
                    "trades.json": "trades.json",
                    "maps.json": "maps.json",
                    "bots.json": "bots.json",
                    "images/": "images"
                }
                
                updated_count = 0
                for zip_info in zip_ref.infolist():
                    if not zip_info.filename.startswith(root_folder + "/"):
                        continue
                        
                    rel_path = zip_info.filename[len(root_folder)+1:]
                    if not rel_path: continue
                    
                    target_rel_path = None
                    for key, local_subpath in sync_map.items():
                        if rel_path == key or rel_path.startswith(key):
                            target_rel_path = local_subpath + rel_path[len(key)-1:] if key.endswith('/') else local_subpath
                            break
                    
                    if target_rel_path:
                        dest_path = data_dir / target_rel_path
                        if zip_info.is_dir():
                            dest_path.mkdir(parents=True, exist_ok=True)
                        else:
                            dest_path.parent.mkdir(parents=True, exist_ok=True)
                            with zip_ref.open(zip_info) as source, open(dest_path, "wb") as target:
                                shutil.copyfileobj(source, target)
                            updated_count += 1

            self.update_complete.emit(True, f"Successfully synced {updated_count} files from GitHub. Please restart.")
            
            # Save the remote timestamp as local version
            remote_date = self.get_remote_commit_date()
            if remote_date:
                self.save_local_data_date(remote_date)

        except Exception as e:
            self.update_complete.emit(False, f"Update failed: {str(e)}")

    def download_language(self, lang_code):
        """Downloads a specific Tesseract language file."""
        filename = f"{lang_code}.traineddata"
        # Using tessdata_fast for better performance/size ratio
        url = f"https://github.com/tesseract-ocr/tessdata_fast/raw/main/{filename}"
        target_path = os.path.join(Constants.TESSDATA_DIR, filename)
        
        if os.path.exists(target_path):
            self.update_complete.emit(True, f"Language data for {lang_code} is already installed.")
            return

        self.download_progress.emit(0, 100, f"Downloading {filename}...")
        
        try:
            os.makedirs(Constants.TESSDATA_DIR, exist_ok=True)
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            block_size = 8192
            downloaded = 0
            
            with open(target_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=block_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        # Emit progress as percentage if we know total size
                        if total_size > 0:
                            percent = int((downloaded / total_size) * 100)
                            self.download_progress.emit(percent, 100, f"Downloading {filename}")
            
            self.update_complete.emit(True, f"Successfully downloaded {filename}")
            
        except Exception as e:
            if os.path.exists(target_path): os.remove(target_path)
            self.update_complete.emit(False, f"Failed to download language data: {e}")