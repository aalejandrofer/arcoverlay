from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, 
    QScrollArea, QGridLayout, QLabel, QComboBox, QFrame, QSplitter, 
    QTextEdit, QSizePolicy, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer, QObject
from PyQt6.QtGui import QPixmap, QColor
import os
import requests
from .constants import Constants
from .ui_components import InventoryControl, StashProgressBar
from .base_page import BasePage

try:
    from rapidfuzz import fuzz; _HAS_RAPIDFUZZ = True
except ImportError:
    import difflib; _HAS_RAPIDFUZZ = False

# HELPER CLASSES
class ImageDownloadWorker(QThread):
    download_complete = pyqtSignal(bool, str) 
    def __init__(self, url, save_path, parent=None):
        super().__init__(parent); self.url = url; self.save_path = save_path
    def run(self):
        try:
            os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
            response = requests.get(self.url, timeout=10, stream=True)
            if response.status_code == 200:
                with open(self.save_path, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        if self.isInterruptionRequested(): f.close(); return
                        f.write(chunk)
                self.download_complete.emit(True, self.save_path)
            else: self.download_complete.emit(False, self.save_path)
        except Exception: self.download_complete.emit(False, self.save_path)

class ItemImageLoader(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_cache = {}
        self.active_downloads = {}
        self.pending_labels = {} 
    def load_image(self, item, label, size=64):
        item_id = item.get('id'); img_url = item.get('imageFilename')
        filename = img_url.split('/')[-1] if img_url else f"{item_id}.png"
        path = os.path.join(Constants.DATA_DIR, "images", "items", filename)
        if path in self.image_cache: self._set_pixmap(label, self.image_cache[path], size)
        elif os.path.exists(path):
            pix = QPixmap(path); self.image_cache[path] = pix; self._set_pixmap(label, pix, size)
        elif img_url and img_url.startswith("http"):
            label.setText("..."); self._start_download(img_url, path, label, size)
        else: label.setText("?")
    def _set_pixmap(self, label, pixmap, size):
        label.setPixmap(pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
    def _start_download(self, url, path, label, size):
        if path not in self.pending_labels: self.pending_labels[path] = []
        self.pending_labels[path].append((label, size))
        if path in self.active_downloads: return
        worker = ImageDownloadWorker(url, path, self)
        worker.download_complete.connect(self._on_download_complete)
        self.active_downloads[path] = worker; worker.start()
    def _on_download_complete(self, success, path):
        if path in self.active_downloads: del self.active_downloads[path]
        waiting = self.pending_labels.pop(path, [])
        if success and os.path.exists(path):
            pix = QPixmap(path); self.image_cache[path] = pix
            for label, size in waiting:
                try: self._set_pixmap(label, pix, size)
                except RuntimeError: pass 
        else:
            for label, _ in waiting:
                try: label.setText("x")
                except RuntimeError: pass
    def cleanup(self):
        for w in self.active_downloads.values(): w.requestInterruption(); w.quit(); w.wait(50)
        self.active_downloads.clear()

class ItemGridCard(QFrame):
    clicked = pyqtSignal(dict) 
    def __init__(self, item, localized_name, image_loader, stash_count=0, stack_size=1, is_collected=False, is_selected=False):
        super().__init__()
        self.item = item; self.is_selected = is_selected
        self.setFixedSize(100, 130); self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.rarity = item.get('rarity', 'Common'); self.rarity_color = Constants.RARITY_COLORS.get(self.rarity, "#777")
        self.is_bp = (item.get('type') == "Blueprint") or ("Blueprint" in item.get('name', ''))
        self._update_style()
        layout = QVBoxLayout(self); layout.setContentsMargins(5, 5, 5, 5); layout.setSpacing(4)
        img_lbl = QLabel(); img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter); img_lbl.setFixedSize(40, 40); img_lbl.setStyleSheet("border: none; background: transparent;")
        image_loader.load_image(item, img_lbl, size=40)
        layout.addWidget(img_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        name_lbl = QLabel(localized_name); name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter); name_lbl.setWordWrap(True)
        name_lbl.setStyleSheet("color: #E0E0E0; font-size: 11px; font-weight: bold; border: none; background: transparent;")
        layout.addWidget(name_lbl)
        if not self.is_bp:
            self.bar = StashProgressBar(font_size=8); self.bar.setFixedHeight(16); self.bar.update_status(stash_count, stack_size); layout.addWidget(self.bar)
        else: layout.addStretch()
        if is_collected and self.is_bp:
            self.check_lbl = QLabel("✓", self); self.check_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter); self.check_lbl.setFixedSize(24, 24)
            self.check_lbl.setStyleSheet("background-color: #4CAF50; color: #FFFFFF; border-radius: 12px; font-weight: bold; font-size: 14px; border: 2px solid #1a1f2b;"); self.check_lbl.move(100, 6); self.check_lbl.show()
    def set_selected(self, selected):
        if self.is_selected != selected: self.is_selected = selected; self._update_style()
    def _update_style(self):
        if self.is_bp: 
            bg = "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 rgba(13, 27, 42, 0.8), stop:1 rgba(27, 38, 59, 0.9))"
            bg_hover = "rgba(22, 34, 53, 1.0)"
            base_border = "rgba(65, 90, 119, 0.3)"
        else: 
            bg = "rgba(19, 21, 25, 0.6)"
            bg_hover = "rgba(35, 40, 52, 0.8)"
            base_border = "rgba(255, 255, 255, 0.05)"
            
        if self.is_selected: 
            border = "2px solid #4476ED"
            bg_style = bg_hover
            hover_border = "#4476ED"
        else: 
            border = f"1px solid {base_border}"
            bg_style = bg
            hover_border = self.rarity_color
            
        self.setStyleSheet(f"""
            QFrame {{ 
                background: {bg_style}; 
                border: {border}; 
                border-top: 3px solid {self.rarity_color}; 
                border-radius: 8px; 
            }} 
            QFrame:hover {{ 
                background: {bg_hover}; 
                border-color: {hover_border}; 
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton: self.clicked.emit(self.item)

class ItemInspectorPanel(QFrame):
    data_changed = pyqtSignal()
    def __init__(self, data_manager, image_loader, lang_code):
        super().__init__()
        self.data_manager = data_manager; self.image_loader = image_loader; self.lang_code = lang_code; self.current_item = None
        self.setFixedWidth(320)
        self.setStyleSheet("QFrame { background-color: rgba(26, 31, 43, 0.4); border-left: 1px solid rgba(255, 255, 255, 0.05); }")
        
        self.main_layout = QVBoxLayout(self); self.main_layout.setContentsMargins(15, 20, 15, 10); self.main_layout.setSpacing(12)
        
        self.placeholder = QLabel("SELECT AN ITEM\\nTO VIEW DETAILS"); 
        self.placeholder.setStyleSheet("color: rgba(255, 255, 255, 0.3); font-size: 13px; font-weight: bold; letter-spacing: 1px; border: none;")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter); self.main_layout.addWidget(self.placeholder)
        self.content_container = QWidget(); self.content_container.setVisible(False); self.content_container.setStyleSheet("border: none;")
        self.c_layout = QVBoxLayout(self.content_container); self.c_layout.setContentsMargins(0,0,0,0)
        self.header_lbl = QLabel(); self.header_lbl.setWordWrap(True); self.header_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter); self.c_layout.addWidget(self.header_lbl)
        controls_wrapper = QHBoxLayout(); controls_wrapper.setAlignment(Qt.AlignmentFlag.AlignCenter); controls_wrapper.setSpacing(10)
        self.left_btns_container = QWidget(); left_btns = QVBoxLayout(self.left_btns_container); left_btns.setSpacing(5); left_btns.setContentsMargins(0,0,0,0)
        self.btn_sub_1 = self._create_adj_btn("-1", "#d32f2f"); self.btn_sub_10 = self._create_adj_btn("-10", "#d32f2f")
        left_btns.addWidget(self.btn_sub_1); left_btns.addWidget(self.btn_sub_10); controls_wrapper.addWidget(self.left_btns_container)
        center_display = QVBoxLayout(); center_display.setSpacing(8); center_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_lbl = QLabel(); self.img_lbl.setFixedSize(90, 90); self.img_lbl.setStyleSheet("border: 1px solid #333; background-color: #000; border-radius: 5px;")
        self.storage_bar = StashProgressBar(); self.storage_bar.setFixedSize(90, 24)
        self.bp_toggle_btn = QPushButton("NOT COLLECTED"); self.bp_toggle_btn.setFixedSize(110, 24); self.bp_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor); self.bp_toggle_btn.setVisible(False)
        self.bp_toggle_btn.clicked.connect(self._toggle_blueprint)
        center_display.addWidget(self.img_lbl, alignment=Qt.AlignmentFlag.AlignCenter); center_display.addWidget(self.storage_bar, alignment=Qt.AlignmentFlag.AlignCenter); center_display.addWidget(self.bp_toggle_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        controls_wrapper.addLayout(center_display)
        self.right_btns_container = QWidget(); right_btns = QVBoxLayout(self.right_btns_container); right_btns.setSpacing(5); right_btns.setContentsMargins(0,0,0,0)
        self.btn_add_1 = self._create_adj_btn("+1", "#388E3C"); self.btn_add_10 = self._create_adj_btn("+10", "#388E3C")
        right_btns.addWidget(self.btn_add_1); right_btns.addWidget(self.btn_add_10); controls_wrapper.addWidget(self.right_btns_container); self.c_layout.addLayout(controls_wrapper)
        self.btn_sub_1.clicked.connect(lambda: self._modify_storage(-1)); self.btn_sub_10.clicked.connect(lambda: self._modify_storage(-10))
        self.btn_add_1.clicked.connect(lambda: self._modify_storage(1)); self.btn_add_10.clicked.connect(lambda: self._modify_storage(10))
        btn_layout = QHBoxLayout(); btn_layout.setSpacing(10)
        self.track_btn = QPushButton("TRACK"); self.track_btn.setCursor(Qt.CursorShape.PointingHandCursor); self.track_btn.setFixedHeight(32); self.track_btn.clicked.connect(self._toggle_track)
        self.notes_btn = QPushButton("NOTES"); self.notes_btn.setCursor(Qt.CursorShape.PointingHandCursor); self.notes_btn.setFixedHeight(32); self.notes_btn.setStyleSheet("QPushButton { background-color: #3E4451; color: #E0E6ED; border: 1px solid #555; border-radius: 4px; font-weight: bold; } QPushButton:hover { background-color: #4B5363; border-color: #777; }"); self.notes_btn.clicked.connect(self._scroll_to_notes)
        btn_layout.addWidget(self.track_btn); btn_layout.addWidget(self.notes_btn); self.c_layout.addLayout(btn_layout)
        stats_w = QWidget(); self.stats_grid = QGridLayout(stats_w); self.stats_grid.setContentsMargins(0,0,0,0); self.stats_grid.setSpacing(5); self.stat_labels = {}; self._init_stat_labels(); self.c_layout.addWidget(stats_w)
        self.details_scroll = QScrollArea(); self.details_scroll.setWidgetResizable(True); self.details_scroll.setStyleSheet("background: transparent; border: none;")
        scroll_c = QWidget(); self.scroll_layout = QVBoxLayout(scroll_c)
        self.req_label = QLabel("REQUIRED FOR:"); self.req_label.setStyleSheet("font-weight: bold; color: #DDD; margin-top: 10px; border-bottom: 1px solid #444;"); self.scroll_layout.addWidget(self.req_label)
        self.req_container = QWidget(); self.req_layout = QVBoxLayout(self.req_container); self.req_layout.setContentsMargins(0,0,0,0); self.scroll_layout.addWidget(self.req_container)
        n_lbl = QLabel("USER NOTES:"); n_lbl.setStyleSheet("font-weight: bold; color: #DDD; margin-top: 15px; border-bottom: 1px solid #444;"); self.scroll_layout.addWidget(n_lbl)
        self.note_edit = QTextEdit(); self.note_edit.setPlaceholderText("Write personal notes here..."); self.note_edit.setStyleSheet("background-color: #111; color: #E5C07B; border: 1px solid #444; border-radius: 4px; padding: 5px;"); self.note_edit.setFixedHeight(80); self.note_edit.textChanged.connect(self._on_note_change); self.scroll_layout.addWidget(self.note_edit)
        
        self.scroll_layout.addStretch()

        self.details_scroll.setWidget(scroll_c); self.c_layout.addWidget(self.details_scroll); self.main_layout.addWidget(self.content_container)
    def _create_adj_btn(self, text, bg_color):
        btn = QPushButton(text); btn.setFixedSize(55, 30); btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"QPushButton {{ background-color: {bg_color}40; color: #FFF; border: 1px solid {bg_color}; border-radius: 4px; font-weight: bold; }} QPushButton:hover {{ background-color: {bg_color}80; }} QPushButton:pressed {{ background-color: {bg_color}; }}")
        return btn
    def _init_stat_labels(self):
        def add(row, col, key, label, color):
            self.stats_grid.addWidget(QLabel(f"<span style='color:#888'>{label}:</span>"), row, col)
            container = QWidget(); layout = QHBoxLayout(container); layout.setContentsMargins(0,0,0,0); layout.setSpacing(4); layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            icon_lbl = QLabel(); icon_lbl.setFixedSize(16, 16); icon_lbl.setVisible(False); layout.addWidget(icon_lbl)
            val_lbl = QLabel("-"); val_lbl.setStyleSheet(f"color: {color}; font-weight: bold;"); layout.addWidget(val_lbl)
            self.stats_grid.addWidget(container, row, col+1); self.stat_labels[key] = (val_lbl, icon_lbl)
        add(0, 0, "val", "Price", "#E5C07B"); add(0, 2, "w", "Weight", "#61AFEF"); add(1, 0, "stack", "Stack", "#ABB2BF"); add(1, 2, "type", "Type", "#98C379")
    def set_item(self, item, req_details):
        self.current_item = item; self.placeholder.setVisible(False); self.content_container.setVisible(True)
        rarity_color = Constants.RARITY_COLORS.get(item.get('rarity', 'Common'), "#777"); self.header_lbl.setText(self.data_manager.get_localized_name(item, self.lang_code)); self.header_lbl.setStyleSheet(f"color: {rarity_color}; font-size: 20px; font-weight: bold; margin-bottom: 5px;")
        self.image_loader.load_image(item, self.img_lbl, size=90)
        item_type = item.get('type', 'Item'); is_bp = (item_type == "Blueprint") or ("Blueprint" in item.get('name', ''))
        current_stash = self.data_manager.get_stash_count(item.get('id'))
        try: stack_size = int(item.get('stackSize', 1))
        except: stack_size = 1
        if stack_size < 1: stack_size = 1
        if is_bp:
            self.left_btns_container.setVisible(False); self.right_btns_container.setVisible(False); self.storage_bar.setVisible(False)
            self.bp_toggle_btn.setVisible(True); self._update_bp_style(current_stash > 0)
        else:
            self.left_btns_container.setVisible(True); self.right_btns_container.setVisible(True); self.storage_bar.setVisible(True)
            self.bp_toggle_btn.setVisible(False); self.storage_bar.update_status(current_stash, stack_size)
        self._update_track_btn_style()
        price_val = item.get('value', 0); val_lbl, icon_lbl = self.stat_labels["val"]; val_lbl.setText(f"{price_val:,}")
        if Constants.COIN_ICON_PATH and os.path.exists(Constants.COIN_ICON_PATH):
            pix = QPixmap(Constants.COIN_ICON_PATH); icon_lbl.setPixmap(pix.scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)); icon_lbl.setVisible(True)
        else: icon_lbl.setVisible(False); val_lbl.setText(f"£{price_val:,}")
        self.stat_labels["w"][0].setText(f"{item.get('weightKg', 0)}kg"); self.stat_labels["stack"][0].setText(str(stack_size)); self.stat_labels["type"][0].setText(item_type)
        self.note_edit.blockSignals(True); self.note_edit.setPlainText(self.data_manager.get_item_note(item.get('id'))); self.note_edit.blockSignals(False)
        while self.req_layout.count(): child = self.req_layout.takeAt(0); (child.widget().deleteLater() if child.widget() else None)
        if any(req_details.values()):
            self.req_label.setVisible(True); self._add_reqs("QUESTS", req_details.get('quest'), "#4CAF50"); self._add_reqs("HIDEOUT", req_details.get('hideout'), "#2196F3"); self._add_reqs("PROJECTS", req_details.get('project'), "#FF9800")
        else: self.req_label.setVisible(False)
    def _add_reqs(self, title, items, color):
        if items:
            l = QLabel(title); l.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 11px; margin-top: 5px;"); self.req_layout.addWidget(l)
            for i in items: il = QLabel(f"• {i}"); il.setWordWrap(True); il.setStyleSheet("color: #BBB; margin-left: 10px;"); self.req_layout.addWidget(il)
    def _modify_storage(self, amount):
        if not self.current_item: return
        iid = self.current_item.get('id'); current = self.data_manager.get_stash_count(iid); new_val = max(0, current + amount)
        self.data_manager.set_stash_count(iid, new_val)
        try: stack_size = int(self.current_item.get('stackSize', 1))
        except: stack_size = 1
        if stack_size < 1: stack_size = 1
        self.storage_bar.update_status(new_val, stack_size); self.data_changed.emit()
    def _toggle_blueprint(self):
        if not self.current_item: return
        iid = self.current_item.get('id'); current = self.data_manager.get_stash_count(iid); new_val = 1 if current == 0 else 0
        if new_val > 0:
            if self.data_manager.is_item_tracked(iid): self.data_manager.toggle_item_track(iid)
        else:
            if not self.data_manager.is_item_tracked(iid): self.data_manager.toggle_item_track(iid)
        self.data_manager.set_stash_count(iid, new_val)
        self._update_bp_style(new_val > 0); self._update_track_btn_style(); self.data_changed.emit()
    def _update_bp_style(self, collected):
        if collected: self.bp_toggle_btn.setText("COLLECTED"); self.bp_toggle_btn.setStyleSheet("QPushButton { background-color: #2E5C32; color: #4CAF50; border: 1px solid #4CAF50; font-weight: bold; font-size: 11px; border-radius: 3px; }")
        else: self.bp_toggle_btn.setText("NOT COLLECTED"); self.bp_toggle_btn.setStyleSheet("QPushButton { background-color: #3E4451; color: #AAA; border: 1px solid #555; font-weight: bold; font-size: 11px; border-radius: 3px; }")
    def _scroll_to_notes(self): self.note_edit.setFocus(); bar = self.details_scroll.verticalScrollBar(); bar.setValue(bar.maximum())
    def _on_note_change(self):
        if self.current_item: self.data_manager.set_item_note(self.current_item.get('id'), self.note_edit.toPlainText())
    def _toggle_track(self):
        if not self.current_item: return
        iid = self.current_item.get('id')
        self.data_manager.toggle_item_track(iid)
        self._update_track_btn_style(); self.data_changed.emit()
    def _update_track_btn_style(self):
        if not self.current_item: return
        is_tracked = self.data_manager.is_item_tracked(self.current_item.get('id'))
        if is_tracked: self.track_btn.setText("TRACKED"); self.track_btn.setStyleSheet("QPushButton { background-color: rgba(76, 175, 80, 0.2); color: #4CAF50; border: 1px solid #4CAF50; border-radius: 4px; font-weight: bold; } QPushButton:hover { background-color: rgba(76, 175, 80, 0.4); }")
        else: self.track_btn.setText("TRACK"); self.track_btn.setStyleSheet("QPushButton { background-color: #3E4451; color: #AAA; border: 1px solid #555; border-radius: 4px; font-weight: bold; } QPushButton:hover { background-color: #4B5363; border-color: #777; color: #DDD; }")

# MAIN CONTROLLER
class ItemDatabaseWindow(BasePage):
    def __init__(self, data_manager, lang_code="en"):
        super().__init__("Item Database") 
        self.data_manager = data_manager; self.lang_code = lang_code; self.image_loader = ItemImageLoader(self)
        if self.data_manager.id_to_item_map: self.unique_items = list(self.data_manager.id_to_item_map.values())
        else:
            seen = set(); self.unique_items = []
            for i in self.data_manager.items.values():
                if i.get('id') and i['id'] not in seen: seen.add(i['id']); self.unique_items.append(i)
        
        self.selected_item_id = None
        self._enforce_blueprint_defaults()
        self.filtered_items = []; self.current_display_limit = 50; self.req_cache = {}
        self._build_requirements_cache()
        self.all_types = sorted(list(set(item.get('type', 'Unknown') for item in self.unique_items)))
        self.all_rarities = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
        
        self.search_timer = QTimer(); self.search_timer.setSingleShot(True); self.search_timer.setInterval(300); self.search_timer.timeout.connect(self.filter_items)
        self.resize_timer = QTimer(); self.resize_timer.setSingleShot(True); self.resize_timer.setInterval(200); self.resize_timer.timeout.connect(self.update_display)
        
        self.init_ui()
        self.filter_items(); self.update_blueprint_stats()

    def init_ui(self):
        # 1. Top Filter Layout (Global Filters)
        filter_layout = QHBoxLayout()
        self.search_bar = QLineEdit(); self.search_bar.setPlaceholderText("Search items..."); self.search_bar.setStyleSheet("QLineEdit { background-color: #1A1F2B; border: 1px solid #333; border-radius: 4px; padding: 8px; color: white; font-size: 14px; }")
        self.search_bar.textChanged.connect(self.search_timer.start); filter_layout.addWidget(self.search_bar, 1)
        
        self.reset_btn = QPushButton("✖")
        self.reset_btn.setFixedSize(40, 32)
        self.reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_btn.setToolTip("Reset Search and Filters")
        self.reset_btn.setStyleSheet("""
            QPushButton { background-color: rgba(211, 47, 47, 0.2); color: #ef5350; border: 1px solid #ef5350; border-radius: 4px; font-weight: bold; font-size: 14px; } 
            QPushButton:hover { background-color: rgba(211, 47, 47, 0.4); }
        """)
        self.reset_btn.clicked.connect(self.reset_filters); filter_layout.addWidget(self.reset_btn)

        self.view_filter = self._create_combo("All Items", ["Tracked Only", "Stash", "Quests", "Hideout", "Projects"])
        self.type_filter = self._create_combo("All Types", self.all_types); self.rarity_filter = self._create_combo("All Rarities", self.all_rarities)
        for w in [self.view_filter, self.type_filter, self.rarity_filter]: filter_layout.addWidget(w)
        
        self.content_layout.addLayout(filter_layout)
        
        # 2. Blueprint / Stash Buttons Layout
        bp_layout = QHBoxLayout(); bp_layout.setContentsMargins(5, 0, 0, 0);bp_layout.setSpacing(10)
        self.bp_filter_btn = QPushButton("Blueprints (0/0)"); self.bp_filter_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.bp_filter_btn.setStyleSheet("QPushButton { background-color: #1E3A5F; color: #FFF; border: 1px solid #4476ED; border-radius: 4px; padding: 6px 12px; font-weight: bold; min-width: 140px; } QPushButton:hover { background-color: #2b4c75; }")
        self.bp_filter_btn.clicked.connect(self._filter_to_blueprints)
        
        self.storage_filter_btn = QPushButton("Stash"); self.storage_filter_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.storage_filter_btn.setStyleSheet("QPushButton { background-color: #2E5C32; color: #FFF; border: 1px solid #4CAF50; border-radius: 4px; padding: 6px 12px; font-weight: bold; min-width: 100px; } QPushButton:hover { background-color: #3d7a42; }")
        self.storage_filter_btn.clicked.connect(self._filter_to_storage)
        bp_layout.addWidget(self.bp_filter_btn); bp_layout.addWidget(self.storage_filter_btn); bp_layout.addStretch()
        
        # 3. Main Splitter Setup
        splitter = QSplitter(Qt.Orientation.Horizontal); splitter.setStyleSheet("QSplitter::handle { background-color: #3E4451; width: 2px; }")
        
        # --- List Area (Scroll) ---
        self.scroll_content = QWidget(); self.grid_layout = QGridLayout(self.scroll_content); self.grid_layout.setContentsMargins(5, 5, 5, 5); self.grid_layout.setSpacing(10); self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.inner_scroll = QScrollArea(); self.inner_scroll.setWidgetResizable(True); self.inner_scroll.setWidget(self.scroll_content)
        self.inner_scroll.setStyleSheet("background: transparent; border: none;")
        
        # --- Inspector Panel ---
        self.inspector = ItemInspectorPanel(self.data_manager, self.image_loader, self.lang_code)
        self.inspector.data_changed.connect(self.update_blueprint_stats); self.inspector.data_changed.connect(self.filter_items)
        
        # --- NEW: Left Container (Groups Buttons + List) ---
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 5, 0) # Zero margins align it with top filters, 5px right margin for splitter handle
        left_layout.setSpacing(10)
        
        left_layout.addLayout(bp_layout)      # Add Buttons here
        left_layout.addWidget(self.inner_scroll) # Add List here

        # Add to Splitter
        splitter.addWidget(left_container)
        splitter.addWidget(self.inspector)
        splitter.setStretchFactor(0, 1); splitter.setStretchFactor(1, 0)
        
        self.content_layout.addWidget(splitter)

    # ... [Helper methods identical to previous logic] ...
    
    def _enforce_blueprint_defaults(self):
        tracked = self.data_manager.get_tracked_items_data()
        stash = self.data_manager.user_progress.get('stash_inventory', {})
        changed = False
        for item in self.unique_items:
            # Blueprint check
            if (item.get('type') == "Blueprint") or ("Blueprint" in item.get('name', '')):
                iid = item.get('id')
                if iid and stash.get(iid, 0) == 0 and iid not in tracked:
                    tracked[iid] = {"tags": []}
                    changed = True
        if changed:
            self.data_manager.user_progress['tracked_items'] = tracked
            self.data_manager.save_user_progress()

    def _build_requirements_cache(self):
        self.req_cache = {}
        def get_name(obj, fallback): n = obj.get('name', {}); return n.get(self.lang_code, n.get('en', fallback)) if isinstance(n, dict) else n
        for quest in self.data_manager.quest_data:
            q_name = get_name(quest, 'Quest')
            for req in quest.get('requiredItemIds', []): self._add_to_cache(req.get('itemId'), 'quest', f"{q_name} ({req.get('quantity', 1)}x)")
        for station in self.data_manager.hideout_data:
            s_name = get_name(station, 'Station')
            for level in station.get('levels', []):
                for req in level.get('requirementItemIds', []): self._add_to_cache(req.get('itemId'), 'hideout', f"{s_name} Lv.{level.get('level')} ({req.get('quantity', 1)}x)")
        for proj in self.data_manager.project_data:
            p_name = get_name(proj, 'Project').replace("Project", "").strip()
            for phase in proj.get('phases', []):
                for req in phase.get('requirementItemIds', []): self._add_to_cache(req.get('itemId'), 'project', f"{p_name} ({req.get('quantity', 1)}x)")

    def _add_to_cache(self, item_id, type_key, text):
        if not item_id: return
        if item_id not in self.req_cache: self.req_cache[item_id] = {'types': set(), 'details': {'quest': [], 'hideout': [], 'project': []}}
        self.req_cache[item_id]['types'].add(type_key); self.req_cache[item_id]['details'][type_key].append(text)

    def _create_combo(self, default, items):
        c = QComboBox(); c.addItem(default); c.addItems(items)
        c.setStyleSheet("QComboBox { background-color: #1A1F2B; border: 1px solid #333; border-radius: 4px; padding: 5px; color: #ddd; min-width: 80px; font-size: 12px; }")
        c.currentTextChanged.connect(self.filter_items); return c

    def _filter_to_blueprints(self): self.view_filter.setCurrentText("All Items"); self.type_filter.setCurrentText("Blueprint"); self.filter_items()
    def _filter_to_storage(self): self.view_filter.setCurrentText("Stash"); self.filter_items()

    def reset_filters(self):
        self.search_bar.blockSignals(True); self.view_filter.blockSignals(True); self.type_filter.blockSignals(True); self.rarity_filter.blockSignals(True)
        self.search_bar.clear(); self.view_filter.setCurrentIndex(0); self.type_filter.setCurrentIndex(0); self.rarity_filter.setCurrentIndex(0)
        self.search_bar.blockSignals(False); self.view_filter.blockSignals(False); self.type_filter.blockSignals(False); self.rarity_filter.blockSignals(False)
        self.filter_items()

    def update_blueprint_stats(self):
        total = 0; collected = 0; stash = self.data_manager.user_progress.get('stash_inventory', {})
        for item in self.unique_items:
            if (item.get('type') == "Blueprint") or ("Blueprint" in item.get('name', '')):
                total += 1
                if stash.get(item.get('id'), 0) > 0: collected += 1
        self.bp_filter_btn.setText(f"Blueprints ({collected}/{total})")

    def filter_items(self):
        self.current_display_limit = 50; search = self.search_bar.text().lower().strip(); view, f_type, f_rarity = self.view_filter.currentText(), self.type_filter.currentText(), self.rarity_filter.currentText()
        tracked = self.data_manager.user_progress.get('tracked_items', []); stash = self.data_manager.user_progress.get('stash_inventory', {})
        self.filtered_items = []
        for item in self.unique_items:
            name = item.get('name', '').lower(); iid = item.get('id')
            if search:
                found = search in name
                if not found and 'names' in item:
                    for val in item['names'].values():
                        if val and search in val.lower(): found = True; break
                if not found: continue
            if view == "Tracked Only" and iid not in tracked: continue
            if view == "Stash" and stash.get(iid, 0) <= 0: continue
            
            reqs = self.req_cache.get(iid, {'types': set()})['types']
            if view == "Quests" and 'quest' not in reqs: continue
            if view == "Hideout" and 'hideout' not in reqs: continue
            if view == "Projects" and 'project' not in reqs: continue
            if f_type != "All Types" and item.get('type') != f_type: continue
            if f_rarity != "All Rarities" and item.get('rarity') != f_rarity: continue
            self.filtered_items.append(item)
        if search: self.filtered_items.sort(key=lambda x: (search not in x.get('name', '').lower(), x.get('name', '')))
        else: self.filtered_items.sort(key=lambda x: x.get('name', ''))
        self.update_display()

    def resizeEvent(self, event): self.resize_timer.start(); super().resizeEvent(event)
    
    def update_display(self):
        while self.grid_layout.count(): item = self.grid_layout.takeAt(0); (item.widget().deleteLater() if item.widget() else None)
        # --- FIXED: Use inner_scroll ---
        viewport_width = self.inner_scroll.viewport().width(); card_width = 110; max_cols = max(1, viewport_width // card_width)
        row, col, count, limit = 0, 0, 0, self.current_display_limit
        stash = self.data_manager.user_progress.get('stash_inventory', {})
        for item in self.filtered_items:
            if count >= limit:
                btn = QPushButton(f"Show More ({len(self.filtered_items)-count} remaining)"); btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setStyleSheet("QPushButton { background-color: #3E4451; color: #E0E6ED; border: 1px solid #5C6370; padding: 10px; font-weight: bold; }")
                btn.clicked.connect(lambda: [setattr(self, 'current_display_limit', self.current_display_limit + 50), self.update_display()])
                self.grid_layout.addWidget(btn, row + 1, 0, 1, max_cols); break
            
            loc_name = self.data_manager.get_localized_name(item, self.lang_code)
            is_bp = (item.get('type') == "Blueprint") or ("Blueprint" in item.get('name', ''))
            is_collected = False; is_selected = (item.get('id') == self.selected_item_id)
            if is_bp: is_collected = stash.get(item.get('id'), 0) > 0
            
            try: stack_size = int(item.get('stackSize', 1))
            except: stack_size = 1
            if stack_size < 1: stack_size = 1
            stash_count = stash.get(item.get('id'), 0)

            card = ItemGridCard(item, loc_name, self.image_loader, stash_count=stash_count, stack_size=stack_size, is_collected=is_collected, is_selected=is_selected)
            card.clicked.connect(self.on_item_clicked); self.grid_layout.addWidget(card, row, col)
            col += 1; count += 1
            if col >= max_cols: col = 0; row += 1

    def on_item_clicked(self, item): 
        self.selected_item_id = item.get('id')
        for i in range(self.grid_layout.count()):
            w = self.grid_layout.itemAt(i).widget()
            if isinstance(w, ItemGridCard): w.set_selected(w.item.get('id') == self.selected_item_id)
        reqs = self.req_cache.get(item.get('id'), {'details': {}})['details']
        self.inspector.set_item(item, reqs)

    def confirm_reset(self):
        from PyQt6.QtWidgets import QMessageBox
        # Main reset confirmation
        msg = QMessageBox(self)
        msg.setWindowTitle("Confirm Reset")
        msg.setText("Are you sure you want to completely reset ALL Stash, Blueprints, and Tracked Items?")
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        
        if msg.exec() == QMessageBox.StandardButton.Yes:
            # Secondary confirmation for notes
            msg_notes = QMessageBox(self)
            msg_notes.setWindowTitle("Clear Notes?")
            msg_notes.setText("Do you also want to clear all Item Notes?")
            msg_notes.setInformativeText("Select 'No' to keep your personal notes.")
            msg_notes.setIcon(QMessageBox.Icon.Question)
            msg_notes.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg_notes.setDefaultButton(QMessageBox.StandardButton.No)
            
            clear_notes = (msg_notes.exec() == QMessageBox.StandardButton.Yes)
            self.reset_state(clear_notes=clear_notes)

    def reset_state(self, clear_notes=False):
        self.data_manager.user_progress['stash_inventory'] = {}
        self.data_manager.user_progress['tracked_items'] = []
        
        if clear_notes:
            self.data_manager.user_progress['item_notes'] = {}
            
        self.data_manager.save_user_progress()
        
        # Reset UI filters
        self.reset_filters()
        
        # Re-apply defaults (e.g. tracking default blueprints if needed)
        self._enforce_blueprint_defaults()
        
        # Refresh UI
        self.filter_items()
        self.update_blueprint_stats()
        
        # If inspector is open, refresh it too
        if self.inspector.isVisible() and self.selected_item_id:
            item = self.data_manager.id_to_item_map.get(self.selected_item_id)
            if item:
                reqs = self.req_cache.get(item.get('id'), {'details': {}})['details']
                self.inspector.set_item(item, reqs)

    # --- NEW: Explicit Cleanup Method ---
    def cleanup(self):
        """Called by parent when closing to stop image download threads."""
        if hasattr(self, 'image_loader'):
            self.image_loader.cleanup()

    def closeEvent(self, event): 
        self.cleanup()
        super().closeEvent(event)