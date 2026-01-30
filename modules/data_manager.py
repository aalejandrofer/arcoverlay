import json
import os
import shutil
from typing import Optional
from .constants import Constants
from .database_manager import DatabaseManager

class ItemDatabase:
    """Loads and holds all item data from the /data/items/ directory."""
    def __init__(self): 
        self.items = self._load_items_from_dir(Constants.ITEMS_DIR)
        
    def _load_items_from_dir(self, directory: str):
        choices = {}
        if not os.path.exists(directory): 
            print(f"Warning: Items directory not found: {directory}. Using empty database.")
            return choices
            
        for filename in os.listdir(directory):
            if filename.endswith('.json'):
                filepath = os.path.join(directory, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        item_object = json.load(f)
                        name_obj = item_object.get('name')
                        
                        if isinstance(name_obj, dict):
                            if 'en' in name_obj: item_object['name'] = str(name_obj['en']).strip()
                            item_object['names'] = name_obj
                            for lang_code, name_val in name_obj.items():
                                if name_val: choices[str(name_val).strip()] = item_object
                                    
                        elif isinstance(name_obj, str): 
                             item_name = str(name_obj).strip()
                             item_object['name'] = item_name
                             item_object['names'] = {'en': item_name}
                             choices[item_name] = item_object

                except Exception as e:
                    print(f"Error loading item file {filename}: {e}")
        return choices

class DataManager:
    def __init__(self, items):
        self.items = items
        self.item_names_lower = [name.lower() for name in self.items.keys()]
        
        self.hideout_data = self._load_json_dir(Constants.HIDEOUT_DIR)
        self.project_data = self._load_json(Constants.PROJECTS_FILE, [])
        self.trade_data = self._load_json(Constants.TRADES_FILE, [])
        self.item_to_trades_map = {}
        for trade in self.trade_data:
            item_id = trade.get('itemId')
            if item_id: self.item_to_trades_map.setdefault(item_id, []).append(trade)
        
        self.maps_data = self._load_json(Constants.MAPS_FILE, [])
        self.id_to_map = {m.get('id'): m for m in self.maps_data if m.get('id')}
            
        self.quest_data = self._load_json_dir(Constants.QUESTS_DIR)
        
        # --- NEW: SQL Database ---
        self.db = DatabaseManager()
        self.user_progress = {}
        self._load_user_progress()
        
        # --- NEW: Stash Data ---
        # Stash is saved in the user_progress dictionary under 'stash_inventory'
        if 'stash_inventory' not in self.user_progress:
            self.user_progress['stash_inventory'] = {}
        
        self.id_to_item_map = {}
        for item in self.items.values():
            if item.get('id'): self.id_to_item_map[item['id']] = item
        
        self.id_to_name_map = {i_id: item.get('name', 'Unknown') for i_id, item in self.id_to_item_map.items()}
        self._backup_progress()

    def _load_user_progress(self):
        # 1. Check if we need to migrate
        is_migrated = self.db.get_state('is_migrated', False)
        if not is_migrated and os.path.exists(Constants.PROGRESS_FILE):
            self._migrate_from_json()
        
        # 2. Load from DB
        self.user_progress = {
            'stash_inventory': self.db.get_all_stash(),
            'item_notes': self.db.get_all_notes(),
            'tracked_items': self.db.get_all_tracked_items(),
            'quests': self.db.get_all_quest_progress(),
            'projects': self.db.get_all_project_progress(),
            'active_quest_id': self.db.get_state('active_quest_id'),
            'quest_order': self.db.get_state('quest_order', []),
            'hideout_station_order': self.db.get_state('hideout_station_order', []),
            'hideout_inventory': self.db.get_all_hideout_inventories()
        }
        
        # Load station levels
        levels = self.db.get_all_hideout_levels()
        self.user_progress.update(levels)

    def _migrate_from_json(self):
        print("[INFO] Migrating progress from JSON to SQL...")
        json_data = self._load_json(Constants.PROGRESS_FILE, {})
        if not json_data: return

        # Items
        stash = json_data.get('stash_inventory', {})
        for iid, qty in stash.items(): self.db.set_item_stash(iid, qty)
        
        notes = json_data.get('item_notes', {})
        for iid, note in notes.items(): self.db.set_item_note(iid, note)
        
        tracked = json_data.get('tracked_items', {})
        if isinstance(tracked, list):  # Handle old list format
            for iid in tracked: self.db.set_item_tracked(iid, True)
        elif isinstance(tracked, dict):
            for iid in tracked: self.db.set_item_tracked(iid, True)

        # Quests
        quests = json_data.get('quests', {})
        for qid, qdata in quests.items():
            self.db.set_quest_progress(qid, qdata.get('is_tracked', False), qdata.get('quest_completed', False), qdata.get('objectives_completed', []))

        # Projects
        projects = json_data.get('projects', {})
        for pid, pdata in projects.items():
            self.db.set_project_progress(pid, pdata.get('completed_phase', 0), pdata.get('inventory', {}))

        # Hideout
        h_inv = json_data.get('hideout_inventory', {})
        for sid, sinv in h_inv.items():
            # Get level from main dict
            lvl = json_data.get(sid, 0)
            self.db.set_hideout_progress(sid, lvl, sinv)

        # App State
        self.db.set_state('active_quest_id', json_data.get('active_quest_id'))
        self.db.set_state('quest_order', json_data.get('quest_order', []))
        self.db.set_state('hideout_station_order', json_data.get('hideout_station_order', []))
        
        # Mark as migrated
        self.db.set_state('is_migrated', True)
        
        # Backup JSON
        try: shutil.move(Constants.PROGRESS_FILE, Constants.PROGRESS_FILE + ".migrated")
        except: pass
        print("[INFO] Migration complete.")

    def _load_json(self, filepath: str, default=None):
        if not os.path.exists(filepath): return default or {}
        try: 
            with open(filepath, 'r', encoding='utf-8') as f: return json.load(f)
        except: return default or {}

    def _load_json_dir(self, directory: str):
        data_list = []
        if not os.path.exists(directory): return data_list
        for filename in os.listdir(directory):
            if filename.endswith('.json'):
                filepath = os.path.join(directory, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f: data_list.append(json.load(f))
                except Exception as e: print(f"Error loading data file {filename} from {directory}: {e}")
        return data_list

    def _backup_progress(self):
        # We can still backup the DB file
        if os.path.exists(Constants.PROGRESS_DB):
            try: shutil.copy2(Constants.PROGRESS_DB, Constants.PROGRESS_DB + ".bak")
            except Exception: pass

    def save_user_progress(self):
        """Syncs current self.user_progress to the SQLite database."""
        try:
            # Sync Items
            stash = self.user_progress.get('stash_inventory', {})
            # We don't want to wipe the DB and re-insert everything every time 
            # if we can help it, but for a simple app it might be easiest 
            # to just use the specific setters already called by the UI.
            # However, some UI parts might modify self.user_progress directly then call save.
            
            # To be safe, we sync the core parts
            for iid, qty in stash.items(): self.db.set_item_stash(iid, qty)
            # Remove items that were deleted from stash
            # (In a real DB manager we'd do this more efficiently)
            
            notes = self.user_progress.get('item_notes', {})
            for iid, note in notes.items(): self.db.set_item_note(iid, note)
            
            tracked = self.user_progress.get('tracked_items', {})
            # This is tricky because tracked_items is a dict of metadata now
            for iid, meta in tracked.items():
                self.db.set_item_tracked(iid, True)

            quests = self.user_progress.get('quests', {})
            for qid, qdata in quests.items():
                self.db.set_quest_progress(qid, qdata.get('is_tracked', False), qdata.get('quest_completed', False), qdata.get('objectives_completed', []))

            projects = self.user_progress.get('projects', {})
            for pid, pdata in projects.items():
                self.db.set_project_progress(pid, pdata.get('completed_phase', 0), pdata.get('inventory', {}))

            hideout_inv = self.user_progress.get('hideout_inventory', {})
            for station in self.hideout_data:
                sid = station.get('id')
                if not sid: continue
                lvl = self.user_progress.get(sid, 0)
                sinv = hideout_inv.get(sid, {})
                self.db.set_hideout_progress(sid, lvl, sinv)

            # State
            self.db.set_state('active_quest_id', self.user_progress.get('active_quest_id'))
            self.db.set_state('quest_order', self.user_progress.get('quest_order', []))
            self.db.set_state('hideout_station_order', self.user_progress.get('hideout_station_order', []))
            
            self._backup_progress()
        except Exception as e: print(f"Error saving progress to DB: {e}")

    def reload_progress(self): 
        self._load_user_progress()
        self._backup_progress()
    
    # --- STASH MANAGEMENT ---
    def get_stash_count(self, item_id: str) -> int:
        return self.user_progress.get('stash_inventory', {}).get(item_id, 0)

    def set_stash_count(self, item_id: str, count: int):
        if count > 0:
            self.user_progress['stash_inventory'][item_id] = count
        else:
            if item_id in self.user_progress['stash_inventory']:
                del self.user_progress['stash_inventory'][item_id]
        self.save_user_progress()

    def get_item_note(self, item_id: str) -> str:
        return self.user_progress.get('item_notes', {}).get(item_id, "")

    def set_item_note(self, item_id: str, note: str):
        if 'item_notes' not in self.user_progress: self.user_progress['item_notes'] = {}
        if note and note.strip(): self.user_progress['item_notes'][item_id] = note.strip()
        elif item_id in self.user_progress['item_notes']: del self.user_progress['item_notes'][item_id]
        self.save_user_progress()

    def get_active_quest_id(self) -> Optional[str]:
        return self.user_progress.get('active_quest_id')

    def set_active_quest_id(self, quest_id: Optional[str]):
        self.user_progress['active_quest_id'] = quest_id
        self.save_user_progress()

    def get_localized_name(self, item_identifier, lang_code='en'):
        item = None
        if isinstance(item_identifier, dict): item = item_identifier
        elif isinstance(item_identifier, str): item = self.id_to_item_map.get(item_identifier) or self.id_to_map.get(item_identifier)
        if not item: return item_identifier.replace('_', ' ').title() if isinstance(item_identifier, str) else "Unknown"
        names = item.get('names', {})
        if isinstance(names, dict) and lang_code in names: return names[lang_code]
        name_field = item.get('name')
        if isinstance(name_field, dict): return name_field.get(lang_code, name_field.get('en', 'Unknown'))
        elif isinstance(name_field, str): return name_field
        return "Unknown"

    def get_tracked_items_data(self) -> dict:
        """Returns a dict of tracked item IDs and their metadata (tags, etc)."""
        tracked = self.user_progress.get('tracked_items', {})
        if isinstance(tracked, list):
            # Migration: convert old list format to new dict format
            new_tracked = {iid: {} for iid in tracked if isinstance(iid, str)}
            self.user_progress['tracked_items'] = new_tracked
            self.save_user_progress()
            return new_tracked
        return tracked

    def is_item_tracked(self, item_id: str) -> bool:
        tracked = self.get_tracked_items_data()
        return item_id in tracked

    def toggle_item_track(self, item_id: str):
        tracked = self.get_tracked_items_data()
        if item_id in tracked:
            del tracked[item_id]
        else:
            tracked[item_id] = {}
        self.user_progress['tracked_items'] = tracked
        self.save_user_progress()



    def get_quest_map_names(self, quest_data, lang_code='en'):
        map_ids = quest_data.get('map')
        if not map_ids: return []
        if isinstance(map_ids, str): map_ids = [map_ids]
        names = []
        for mid in map_ids:
            map_obj = self.id_to_map.get(mid)
            names.append(self.get_localized_name(map_obj, lang_code) if map_obj else mid.replace('_', ' ').title())
        return names

    def get_filtered_quests(self, tracked_only: bool = False, lang_code='en'):
        if 'quests' not in self.user_progress: self.user_progress['quests'] = {}
        all_quest_info = []
        for quest in self.quest_data:
            q_id = quest.get('id')
            if not q_id: continue
            info = quest.copy()
            if isinstance(info.get('name'), dict): info['name'] = info['name'].get(lang_code, info['name'].get('en', 'Unknown'))
            original_objs, flat_objs = info.get('objectives', []), []
            for obj in original_objs:
                if isinstance(obj, dict): flat_objs.append(obj.get(lang_code, obj.get('en', 'Unknown')))
                elif isinstance(obj, str): flat_objs.append(obj)
            info['objectives'] = flat_objs
            progress = self.user_progress['quests'].get(q_id, {})
            info.update(is_completed=progress.get('quest_completed', False), is_tracked=progress.get('is_tracked', False), objectives_completed=progress.get('objectives_completed', []))
            all_quest_info.append(info)
        custom_order = self.user_progress.get('quest_order', [])
        def sort_key(q):
            q_id = q['id']
            order_index = custom_order.index(q_id) if q_id in custom_order else len(custom_order)
            return (not q['is_tracked'], order_index, q['is_completed'])
        sorted_quests = sorted(all_quest_info, key=sort_key)
        if tracked_only: return sorted([q for q in all_quest_info if q['is_tracked'] and not q['is_completed']], key=lambda q: custom_order.index(q['id']) if q['id'] in custom_order else 999)
        else: return sorted_quests



    def find_trades_for_item(self, item_name: str):
        item = self.get_item_by_name(item_name)
        if not item or 'id' not in item: return []
        
        raw_trades = self.item_to_trades_map.get(item['id'], [])
        results = []
        for trade in raw_trades:
             trader = trade.get('trader', 'Unknown')
             cost_data = trade.get('cost', {})
             cost_id = cost_data.get('itemId')
             cost_qty = cost_data.get('quantity', 0)
             
             cost_name = self.get_localized_name(cost_id)
             
             limit = trade.get('dailyLimit')
             limit_str = f" (Limit {limit})" if limit is not None else ""
             
             # Format: Trader: CostItem xQty (Limit)
             display_str = f"{trader}: {cost_name} x{cost_qty}{limit_str}"
             results.append((display_str, 'trade', False))
             
        return results
    
    def find_hideout_requirements(self, item_name: str, lang_code='en'):
        """
        Find hideout upgrade requirements for an item.
        Returns list of tuples: (display_string, req_type, is_complete, needed_qty)
        - display_string: formatted requirement text
        - req_type: 'next' or 'future' 
        - is_complete: True if user has enough items for this requirement
        - needed_qty: quantity needed for the requirement
        """
        results, target_item = [], self.get_item_by_name(item_name)
        if not target_item or 'id' not in target_item: return []
        tid = target_item['id']
        h_inv = self.user_progress.get('hideout_inventory', {})
        for station in self.hideout_data:
            sid = station.get('id')
            sname = self.get_localized_name(station, lang_code)
            cur_lvl = self.user_progress.get(station.get('id'), 0)
            for lvl_info in station.get('levels', []):
                lvl = lvl_info.get('level', 0)
                if lvl <= cur_lvl: continue
                req_type = 'next' if lvl == cur_lvl + 1 else 'future'
                for req in lvl_info.get('requirementItemIds', []):
                    if req.get('itemId') == tid:
                        needed = req.get('quantity', 0)
                        owned = h_inv.get(sid, {}).get(str(lvl), {}).get(req.get('itemId'), 0)
                        is_complete = owned >= needed
                        # Show remaining if not complete, otherwise show total needed with tick
                        if is_complete:
                            display_str = f"{sname} (Lvl {lvl}): x{needed}"
                        else:
                            remaining = needed - owned
                            display_str = f"{sname} (Lvl {lvl}): x{remaining}"
                        results.append((display_str, req_type, is_complete, needed))
        return results

    def find_project_requirements(self, item_name: str, lang_code='en'):
        """Find project/expedition requirements for an item. Returns list of (display_string, req_type) tuples."""
        results, target_item = [], self.get_item_by_name(item_name)
        if not target_item or 'id' not in target_item: return []
        tid = target_item['id']
        p_prog = self.user_progress.get('projects', {})
        
        # DEBUG PRINT
        print(f"[DEBUG] Searching project reqs for {tid} ({item_name})")

        for proj in self.project_data:
            pid = proj.get('id')
            pname = self.get_localized_name(proj, lang_code)
            if 'Project' in pname: pname = pname.replace('Project', '').strip()
            # Filter inactive projects
            if proj.get('disabled', False): continue
            
            prog = p_prog.get(pid, {'completed_phase': 0, 'inventory': {}})
            comp_phase, inv = prog.get('completed_phase', 0), prog.get('inventory', {})
            
            # DEBUG PRINT
            if pid == 'trophy_display_project':
                print(f"[DEBUG] Checking Trophy Display. Comp Phase: {comp_phase}")

            for phase in proj.get('phases', []):
                pnum = phase.get('phase', 0)
                
                # DEBUG PRINT
                if pid == 'trophy_display_project':
                    print(f"[DEBUG]   Phase {pnum}. Skip? {pnum <= comp_phase}")

                if pnum <= comp_phase: continue
                req_type = 'next' if pnum == comp_phase + 1 else 'future'
                for req in phase.get('requirementItemIds', []):
                    if pid == 'trophy_display_project' and req.get('itemId') == tid:
                        print(f"[DEBUG]     FOUND MATCH! Needed: {req.get('quantity')}")

                    if req.get('itemId') == tid:
                        needed = req.get('quantity', 0)
                        owned = inv.get(str(pnum), {}).get(req.get('itemId'), 0)
                        is_complete = owned >= needed
                        # Show remaining if not complete, otherwise show total needed with tick
                        if is_complete:
                            display_str = f"{pname} (Ph{pnum}): x{needed}"
                        else:
                            remaining = needed - owned
                            display_str = f"{pname} (Ph{pnum}): x{remaining}"
                        results.append((display_str, req_type, is_complete, needed))
        return results

    def find_quest_requirements(self, item_name: str, lang_code='en'):
        """Find quest requirements for an item. Returns list of (display_string, is_active, is_complete) tuples."""
        results, target_item = [], self.get_item_by_name(item_name)
        if not target_item or 'id' not in target_item: return []
        tid = target_item['id']
        active_id = self.get_active_quest_id()
        
        for quest in self.quest_data:
            qid = quest.get('id')
            qname = self.get_localized_name(quest, lang_code)
            
            # Check requirements
            reqs = quest.get('requiredItemIds', [])
            for req in reqs:
                if req.get('itemId') == tid:
                    needed = req.get('quantity', 0)
                    prog = self.user_progress.get('quests', {}).get(qid, {})
                    is_complete = prog.get('quest_completed', False)
                    is_active = (qid == active_id)
                    results.append((f"{qname}: x{needed}", is_active, is_complete))
        return results

    def get_item_by_name(self, name: str): return self.items.get(name)