import sqlite3
import json
import os
from .constants import Constants

class DatabaseManager:
    def __init__(self, db_path=None):
        self.db_path = db_path or os.path.join(Constants.DATA_DIR, 'progress.db')
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=10)
        # Enable WAL mode for better concurrency (allows multiple readers + 1 writer)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Items Tracking (Stash, Tracked Status, Notes, Tags)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS items_tracking (
                    item_id TEXT PRIMARY KEY,
                    stash_count INTEGER DEFAULT 0,
                    is_tracked BOOLEAN DEFAULT 0,
                    note TEXT DEFAULT '',
                    tags TEXT DEFAULT ''
                )
            ''')

            # 2. Quests Progress
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS quests_progress (
                    quest_id TEXT PRIMARY KEY,
                    is_tracked BOOLEAN DEFAULT 0,
                    is_completed BOOLEAN DEFAULT 0,
                    objectives_completed TEXT DEFAULT '[]'
                )
            ''')

            # 3. Projects Progress
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS projects_progress (
                    project_id TEXT PRIMARY KEY,
                    completed_phase INTEGER DEFAULT 0,
                    inventory TEXT DEFAULT '{}'
                )
            ''')

            # 4. Hideout Progress
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS hideout_progress (
                    station_id TEXT PRIMARY KEY,
                    level INTEGER DEFAULT 0,
                    inventory TEXT DEFAULT '{}'
                )
            ''')

            # 5. App State (Key-Value)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS app_state (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            
            conn.commit()

    # --- ITEM METHODS ---
    def get_item_data(self, item_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT stash_count, is_tracked, note, tags FROM items_tracking WHERE item_id = ?", (item_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'stash_count': row[0],
                    'is_tracked': bool(row[1]),
                    'note': row[2],
                    'tags': row[3].split(',') if row[3] else []
                }
            return {'stash_count': 0, 'is_tracked': False, 'note': '', 'tags': []}

    def set_item_stash(self, item_id, count):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO items_tracking (item_id, stash_count) 
                VALUES (?, ?) 
                ON CONFLICT(item_id) DO UPDATE SET stash_count = EXCLUDED.stash_count
            ''', (item_id, count))
            conn.commit()

    def set_item_tracked(self, item_id, tracked):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO items_tracking (item_id, is_tracked) 
                VALUES (?, ?) 
                ON CONFLICT(item_id) DO UPDATE SET is_tracked = EXCLUDED.is_tracked
            ''', (item_id, 1 if tracked else 0))
            conn.commit()

    def set_item_note(self, item_id, note):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO items_tracking (item_id, note) 
                VALUES (?, ?) 
                ON CONFLICT(item_id) DO UPDATE SET note = EXCLUDED.note
            ''', (item_id, note))
            conn.commit()

    def set_item_tags(self, item_id, tags):
        tags_str = ",".join(tags)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO items_tracking (item_id, tags) 
                VALUES (?, ?) 
                ON CONFLICT(item_id) DO UPDATE SET tags = EXCLUDED.tags
            ''', (item_id, tags_str))
            conn.commit()

    def get_all_tracked_items(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT item_id, tags FROM items_tracking WHERE is_tracked = 1")
            return {row[0]: {'tags': row[1].split(',') if row[1] else []} for row in cursor.fetchall()}

    def get_all_stash(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT item_id, stash_count FROM items_tracking WHERE stash_count > 0")
            return {row[0]: row[1] for row in cursor.fetchall()}

    def get_all_notes(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT item_id, note FROM items_tracking WHERE note != ''")
            return {row[0]: row[1] for row in cursor.fetchall()}

    # --- QUEST METHODS ---
    def get_quest_progress(self, quest_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT is_tracked, is_completed, objectives_completed FROM quests_progress WHERE quest_id = ?", (quest_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'is_tracked': bool(row[0]),
                    'quest_completed': bool(row[1]),
                    'objectives_completed': json.loads(row[2])
                }
            return {'is_tracked': False, 'quest_completed': False, 'objectives_completed': []}

    def set_quest_progress(self, quest_id, is_tracked, is_completed, objectives):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO quests_progress (quest_id, is_tracked, is_completed, objectives_completed) 
                VALUES (?, ?, ?, ?) 
                ON CONFLICT(quest_id) DO UPDATE SET 
                    is_tracked = EXCLUDED.is_tracked,
                    is_completed = EXCLUDED.is_completed,
                    objectives_completed = EXCLUDED.objectives_completed
            ''', (quest_id, 1 if is_tracked else 0, 1 if is_completed else 0, json.dumps(objectives)))
            conn.commit()

    def get_all_quest_progress(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT quest_id, is_tracked, is_completed, objectives_completed FROM quests_progress")
            return {row[0]: {
                'is_tracked': bool(row[1]),
                'quest_completed': bool(row[2]),
                'objectives_completed': json.loads(row[3])
            } for row in cursor.fetchall()}

    # --- PROJECT METHODS ---
    def get_project_progress(self, project_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT completed_phase, inventory FROM projects_progress WHERE project_id = ?", (project_id,))
            row = cursor.fetchone()
            if row: return {'completed_phase': row[0], 'inventory': json.loads(row[1])}
            return {'completed_phase': 0, 'inventory': {}}

    def set_project_progress(self, project_id, phase, inventory):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO projects_progress (project_id, completed_phase, inventory) 
                VALUES (?, ?, ?) 
                ON CONFLICT(project_id) DO UPDATE SET 
                    completed_phase = EXCLUDED.completed_phase,
                    inventory = EXCLUDED.inventory
            ''', (project_id, phase, json.dumps(inventory)))
            conn.commit()

    def get_all_project_progress(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT project_id, completed_phase, inventory FROM projects_progress")
            return {row[0]: {'completed_phase': row[1], 'inventory': json.loads(row[2])} for row in cursor.fetchall()}

    # --- HIDEOUT METHODS ---
    def get_hideout_progress(self, station_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT level, inventory FROM hideout_progress WHERE station_id = ?", (station_id,))
            row = cursor.fetchone()
            if row: return {'level': row[0], 'inventory': json.loads(row[1])}
            return {'level': 0, 'inventory': {}}

    def set_hideout_progress(self, station_id, level, inventory=None):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # If inventory is not provided, we might want to keep existing one or set empty
            if inventory is None:
                cursor.execute("SELECT inventory FROM hideout_progress WHERE station_id = ?", (station_id,))
                row = cursor.fetchone()
                inventory = json.loads(row[0]) if row else {}
            
            cursor.execute('''
                INSERT INTO hideout_progress (station_id, level, inventory) 
                VALUES (?, ?, ?) 
                ON CONFLICT(station_id) DO UPDATE SET 
                    level = EXCLUDED.level,
                    inventory = EXCLUDED.inventory
            ''', (station_id, level, json.dumps(inventory)))
            conn.commit()

    def get_all_hideout_levels(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT station_id, level FROM hideout_progress")
            return {row[0]: row[1] for row in cursor.fetchall()}

    def get_all_hideout_inventories(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT station_id, inventory FROM hideout_progress")
            return {row[0]: json.loads(row[1]) for row in cursor.fetchall()}

    # --- STATE METHODS ---
    def get_state(self, key, default=None):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM app_state WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row: return json.loads(row[0])
            return default

    def set_state(self, key, value):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO app_state (key, value) VALUES (?, ?) 
                ON CONFLICT(key) DO UPDATE SET value = EXCLUDED.value
            ''', (key, json.dumps(value)))
            conn.commit()
