import re
import os
import pytesseract
from PIL import ImageEnhance
from typing import Optional, Dict, Any

# RapidFuzz / Difflib check
try:
    from rapidfuzz import process, fuzz; _HAS_RAPIDFUZZ = True
except ImportError:
    import difflib; _HAS_RAPIDFUZZ = False

from .constants import Constants
from .image_processor import ImageProcessor

class ItemScanner:
    def __init__(self, config, data_manager):
        """
        :param config: The app config object (contains tesseract path, debug flags).
        :param data_manager: The DataManager instance for looking up item details.
        """
        self.cmd_config = config
        self.data_manager = data_manager
        
        # Default Settings
        self.target_color = (249, 238, 223)
        self.ocr_lang_code = 'eng'
        self.json_lang_code = 'en'
        
        # Configure Tesseract Path if provided
        if self.cmd_config.tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = self.cmd_config.tesseract_path

    def update_settings(self, target_color, ocr_lang_code, json_lang_code):
        """Updates scanner settings when the user changes preferences."""
        self.target_color = target_color
        self.ocr_lang_code = ocr_lang_code
        self.json_lang_code = json_lang_code

    def scan_screen(self, full_screen: bool = False) -> Optional[Dict[str, Any]]:
        """
        Captures screen, processes image, runs OCR, finds item, and gathers all data.
        Returns a dictionary of item data or None if nothing found.
        """
        # 1. Capture Image
        img = ImageProcessor.capture_and_process(self.target_color, full_screen=full_screen)
        if img is None:
            return None
        
        # 2. Debug: Check color region
        if self.cmd_config.debug:
            if ImageProcessor.find_color_region(img, self.target_color):
                print("[DEBUG] Tooltip color region found! Cropping to tooltip.")
        
        # 3. Enhance Image for OCR
        img = img.convert('L')
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        
        # 4. Setup Language / Tesseract Config
        custom_lang_file = os.path.join(Constants.TESSDATA_DIR, f"{self.ocr_lang_code}.traineddata")
        
        if os.path.exists(custom_lang_file):
            os.environ["TESSDATA_PREFIX"] = Constants.TESSDATA_DIR
            tess_config = "--psm 6"
            lang = self.ocr_lang_code
        else:
            if "TESSDATA_PREFIX" in os.environ: del os.environ["TESSDATA_PREFIX"]
            if self.ocr_lang_code != 'eng':
                print(f"[WARN] Language file for '{self.ocr_lang_code}' not found. Falling back to 'eng'.")
            tess_config = "--psm 6"
            lang = 'eng'
        
        # 5. Run OCR
        try:
            raw_text = pytesseract.image_to_string(img, lang=lang, config=tess_config)
            lines = raw_text.splitlines()
        except Exception as e:
            print(f"[Error] OCR Failed: {e}")
            return None

        if not lines: 
            return None
            
        # 6. Clean Text
        cleaned = [re.sub(r'[^a-zA-Z0-9\s-]', '', l).strip() for l in lines if len(l.strip()) >= 3]
        
        # 7. Fuzzy Match against Database
        item_names_lower = [name.lower() for name in self.data_manager.items.keys()]
        lower_to_actual_name = {name.lower(): name for name in self.data_manager.items.keys()}

        best_name, best_score = None, 0
        
        # Create candidates (single lines + combined adjacent lines for multi-line names)
        search_candidates = cleaned + [f"{cleaned[i]} {cleaned[i+1]}" for i in range(len(cleaned) - 1)] if len(cleaned) > 1 else cleaned
        
        for candidate in [c for c in search_candidates if len(c) >= 3]:
            if _HAS_RAPIDFUZZ:
                result = process.extractOne(candidate.lower(), item_names_lower, scorer=fuzz.token_sort_ratio)
                if result and result[1] > best_score:
                    best_score, best_name = result[1], lower_to_actual_name[result[0]]
            else:
                # Fallback for difflib (slower/less accurate)
                import difflib
                matches = difflib.get_close_matches(candidate.lower(), item_names_lower, n=1, cutoff=0.6)
                if matches:
                    score = difflib.SequenceMatcher(None, candidate.lower(), matches[0]).ratio() * 100
                    if score > best_score:
                        best_score, best_name = score, lower_to_actual_name[matches[0]]

        if best_score < 70: 
            best_name = None

        if self.cmd_config.debug: 
            print(f"[DEBUG] Best Match: '{best_name}' with score {best_score}")

        if not best_name:
            return None

        # 8. Aggregate Data
        print(f"Item Found: {best_name}. gathering data...")
        item_details = self.data_manager.get_item_by_name(best_name)
        item_id = item_details.get('id') if item_details else None
        
        user_note = self.data_manager.get_item_note(item_id) if item_id else ""
        stash_count = self.data_manager.get_stash_count(item_id) if item_id else 0
        
        # Blueprint Logic
        is_bp = False
        is_collected_bp = False
        if item_details:
            is_bp = (item_details.get('type') == "Blueprint") or ("Blueprint" in item_details.get('name', ''))
            if is_bp:
                is_collected_bp = stash_count > 0

        # Construct final data packet
        return {
            "item": item_details, 
            "trade": self.data_manager.find_trades_for_item(best_name),
            "hideout": self.data_manager.find_hideout_requirements(best_name, lang_code=self.json_lang_code), 
            "project": self.data_manager.find_project_requirements(best_name, lang_code=self.json_lang_code),
            "blueprint": is_bp,
            "note": user_note,
            "stash_count": stash_count,
            "is_collected_bp": is_collected_bp
        }