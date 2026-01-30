import os
import json

class DatabaseFixer:
    """
    Applies hardcoded fixes to the database after an update.
    This allows us to correct server-side data errors locally.
    """
    
    # Structure: Filename -> list of fix dictionaries
    # Fix dictionary: { "id": "target_id", "changes": { "key": new_value } }
    OVERRIDES = {
        "projects.json": [
            {
                "id": "expedition_project_s1",
                "changes": {
                    "disabled": True
                }
            }
        ]
    }

    @staticmethod
    def apply_fixes(data_dir):
        """
        Iterates through defined overrides and applies them to the JSON files in data_dir.
        """
        print("[DatabaseFixer] Applying database overrides...")
        applied_count = 0
        
        for filename, fixes in DatabaseFixer.OVERRIDES.items():
            filepath = os.path.join(data_dir, filename)
            if not os.path.exists(filepath):
                print(f"[DatabaseFixer] Warning: File not found {filepath}")
                continue
                
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                modified = False
                
                # Handle List-based JSONs (projects.json, quests.json)
                if isinstance(data, list):
                    for item in data:
                        item_id = item.get('id')
                        # Check if we have fixes for this item
                        for fix in fixes:
                            if fix['id'] == item_id:
                                # Apply changes
                                for key, val in fix['changes'].items():
                                    # Only update if different to avoid meaningless writes
                                    # But always write if we found differences to be safe
                                    if item.get(key) != val:
                                        print(f"[DatabaseFixer] Fixing {filename} : {item_id} -> {key} = {val}")
                                        item[key] = val
                                        modified = True
                                        applied_count += 1
                                        
                # Handle Dict-based JSONs (maps.json sometimes, or others)
                elif isinstance(data, dict):
                    # Logic: if the root dict has keys that match the ID
                    for item_id, item_data in data.items():
                         for fix in fixes:
                            if fix['id'] == item_id:
                                for key, val in fix['changes'].items():
                                    if isinstance(item_data, dict) and item_data.get(key) != val:
                                        print(f"[DatabaseFixer] Fixing {filename} : {item_id} -> {key} = {val}")
                                        item_data[key] = val
                                        modified = True
                                        applied_count += 1

                if modified:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                        
            except Exception as e:
                print(f"[DatabaseFixer] Error fixing {filename}: {e}")
                
        print(f"[DatabaseFixer] Finished. Applied {applied_count} fixes.")
        return applied_count
