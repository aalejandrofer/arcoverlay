from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QPushButton, QComboBox, QStackedWidget, QFrame,
    QGraphicsDropShadowEffect, QMessageBox, QTabWidget, QListWidget, QListWidgetItem,
    QAbstractItemView, QSpinBox, QAbstractSpinBox, QApplication, QFileDialog, QLineEdit, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont, QCursor
import os
import shutil
import zipfile
from datetime import datetime

from .constants import Constants
from .ui_components import ModernToggle, SettingsCard, HotkeyButton
from .base_page import BasePage
from .overlay_ui import OverlayRenderer

class SettingsWindow(BasePage):
    # Signals
    hotkeys_updated = pyqtSignal()
    progress_saved = pyqtSignal() # Add this if missing from original file, based on usage in ProgressHubWindow
    data_restored = pyqtSignal()

    SECTIONS = {
        'storage': ('Stash Count', 'show_storage_info'),
        'trader': ('Trader Info', 'show_trader_info'),
        'notes': ('User Notes', 'show_notes'),
        'crafting': ('Crafting Info', 'show_crafting_info'),
        'hideout': ('Hideout Reqs', 'show_hideout_reqs'),
        'project': ('Project Reqs', 'show_project_reqs'),
        'recycle': ('Recycles Into', 'show_recycles_into'),
        'salvage': ('Salvages Into', 'show_salvages_into')
    }
    DEFAULT_ORDER = ['storage', 'trader', 'notes', 'crafting', 'hideout', 'project', 'recycle', 'salvage']
    DEFAULT_OCR_COLOR = (249, 238, 223)

    def __init__(self, config_manager, data_manager=None, on_save_callback=None):
        super().__init__("Application Settings")
        self.cfg = config_manager
        self.data_manager = data_manager
        self.on_save_callback = on_save_callback

        self.start_hotkey_price = ""
        self.start_hotkey_quest = ""
        self.start_hotkey_hub = ""
        self.preview_widgets = {}

        # Timer for color picker
        self.picker_timer = QTimer()
        self.picker_timer.setSingleShot(True)
        self.picker_timer.timeout.connect(self._perform_color_pick)

        self.init_ui()
        self.load_settings()

    def init_ui(self):
        self.tabs = QTabWidget()
        # Tabs are now compact
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #333; border-radius: 4px; background: transparent; }
            QTabBar::tab { padding: 4px 10px; min-width: 50px; font-size: 13px; }
        """)

        self.content_layout.addWidget(self.tabs)

        self.tabs.addTab(self.setup_general_tab(), "General")
        self.tabs.addTab(self.setup_data_tab(), "Data Management")
        self.tabs.addTab(self.setup_item_overlay_tab(), "Item Overlay")
        self.tabs.addTab(self.setup_quest_overlay_tab(), "Quest Overlay")

        self.footer_layout.addStretch()

        self.btn_revert = QPushButton("Reset")
        self.btn_revert.setObjectName("action_button_red")
        self.btn_revert.setFixedSize(130, 32)
        self.btn_revert.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_revert.clicked.connect(self.reset_current_tab)

        self.btn_save = QPushButton("Save Settings")
        self.btn_save.setObjectName("action_button_green")
        self.btn_save.setFixedSize(130, 32)
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.clicked.connect(self.save_settings)

        self.footer_layout.addWidget(self.btn_revert)
        self.footer_layout.addWidget(self.btn_save)

    # --- TABS ---
    def setup_general_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(10)

        # --- CARD 1: PREFERENCES ---
        layout.addWidget(QLabel("Preferences", objectName="Header"))
        card_pref = SettingsCard()
        l_pref = QVBoxLayout(card_pref)
        l_pref.setContentsMargins(10, 10, 10, 10)

        row_lang = QHBoxLayout()
        lbl_lang = QLabel("Game Language:")
        lbl_lang.setStyleSheet("font-size: 13px; font-weight: bold; color: #E0E6ED; border: none; background: transparent;")
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(sorted(list(Constants.LANGUAGES.keys())))
        self.lang_combo.setFixedWidth(200)

        row_lang.addWidget(lbl_lang)
        row_lang.addStretch()
        row_lang.addWidget(self.lang_combo)
        l_pref.addLayout(row_lang)
        layout.addWidget(card_pref)

        # --- CARD 2: HOTKEYS ---
        layout.addWidget(QLabel("Global Hotkeys", objectName="Header"))
        card_hk = SettingsCard()
        l_hk = QVBoxLayout(card_hk)
        l_hk.setContentsMargins(10, 10, 10, 10)
        l_hk.setSpacing(8)

        def add_hk(txt, btn):
            r = QHBoxLayout()
            r.addWidget(QLabel(txt, styleSheet="font-size: 13px; color: #E0E6ED; border:none; background:transparent;"))
            btn.setFixedWidth(200)
            btn.setFixedHeight(28)
            r.addStretch()
            r.addWidget(btn)
            l_hk.addLayout(r)

        self.hotkey_btn = HotkeyButton()
        add_hk("Item Info Hotkey:", self.hotkey_btn)

        div_hk = QFrame(); div_hk.setFrameShape(QFrame.Shape.HLine); div_hk.setStyleSheet("background: #333;")
        l_hk.addWidget(div_hk)

        self.quest_hotkey_btn = HotkeyButton()
        add_hk("Quest Log Hotkey:", self.quest_hotkey_btn)

        div_hk2 = QFrame(); div_hk2.setFrameShape(QFrame.Shape.HLine); div_hk2.setStyleSheet("background: #333;")
        l_hk.addWidget(div_hk2)

        self.hub_hotkey_btn = HotkeyButton()
        add_hk("Progress Hub Hotkey:", self.hub_hotkey_btn)

        hk_hint = QLabel("Note: Changes to hotkeys require an application restart.")
        hk_hint.setStyleSheet("color: #E5C07B; font-style: italic; font-size: 11px; border:none; background:transparent;")
        l_hk.addWidget(hk_hint)
        layout.addWidget(card_hk)

        # --- CARD 3: SCANNING ---
        layout.addWidget(QLabel("Scanning", objectName="Header"))
        card_scan = SettingsCard()
        l_scan = QVBoxLayout(card_scan)
        l_scan.setContentsMargins(15, 15, 15, 15)
        l_scan.setSpacing(10)

        l_scan.addWidget(QLabel("Tooltip Target Color (RGB Detection):", styleSheet="color: #E0E6ED; font-weight: bold; font-size: 13px; border:none; background:transparent;"))

        # -- Picker Row --
        row_picker = QHBoxLayout()
        self.btn_pick_color = QPushButton("Pick Color (3s)")
        self.btn_pick_color.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pick_color.setFixedSize(110, 30)
        self.btn_pick_color.setStyleSheet("""
            QPushButton { background-color: #61AFEF; color: #1A1F2B; border: none; border-radius: 4px; font-weight: bold; font-size: 12px; }
            QPushButton:hover { background-color: #74bdfa; }
        """)
        self.btn_pick_color.clicked.connect(self._start_color_pick)
        row_picker.addWidget(self.btn_pick_color)

        lbl_picker_hint = QLabel("Click, then hover over tooltip background.")
        lbl_picker_hint.setStyleSheet("color: #888; font-style: italic; font-size: 11px; border:none; background:transparent;")
        row_picker.addWidget(lbl_picker_hint)

        row_picker.addStretch()
        l_scan.addLayout(row_picker)

        # -- RGB Controls Row --
        row_color = QHBoxLayout()
        row_color.setSpacing(15)

        self.spin_r = self._create_color_spinbox()
        self.spin_g = self._create_color_spinbox()
        self.spin_b = self._create_color_spinbox()

        self.spin_r.valueChanged.connect(self._update_color_preview)
        self.spin_g.valueChanged.connect(self._update_color_preview)
        self.spin_b.valueChanged.connect(self._update_color_preview)

        def add_rgb_control(layout, label, color_hex, spinbox):
            container = QWidget()
            h_layout = QHBoxLayout(container)
            h_layout.setContentsMargins(0, 0, 0, 0)
            h_layout.setSpacing(2)
            lbl = QLabel(label); lbl.setStyleSheet(f"color: {color_hex}; font-weight:bold; border:none; background:transparent; margin-right: 5px;")
            btn_style = "QPushButton { background-color: #3E4451; color: white; border: 1px solid #555; border-radius: 3px; font-weight: bold; padding: 0px; } QPushButton:hover { background-color: #4B5363; border-color: #777; }"
            btn_minus = QPushButton("-"); btn_minus.setFixedSize(24, 26); btn_minus.setCursor(Qt.CursorShape.PointingHandCursor); btn_minus.setStyleSheet(btn_style); btn_minus.clicked.connect(spinbox.stepDown)
            btn_plus = QPushButton("+"); btn_plus.setFixedSize(24, 26); btn_plus.setCursor(Qt.CursorShape.PointingHandCursor); btn_plus.setStyleSheet(btn_style); btn_plus.clicked.connect(spinbox.stepUp)
            h_layout.addWidget(lbl); h_layout.addWidget(btn_minus); h_layout.addWidget(spinbox); h_layout.addWidget(btn_plus)
            layout.addWidget(container)

        add_rgb_control(row_color, "R:", "#FF6B6B", self.spin_r)
        add_rgb_control(row_color, "G:", "#51CF66", self.spin_g)
        add_rgb_control(row_color, "B:", "#339AF0", self.spin_b)

        row_color.addSpacing(10)
        row_color.addWidget(QLabel("Preview:", styleSheet="color: #AAA; font-size: 12px; border:none; background:transparent;"))
        self.color_preview = QFrame(); self.color_preview.setFixedSize(32, 24)
        self.color_preview.setStyleSheet("border: 1px solid #555; border-radius: 4px; background-color: rgb(249, 238, 223);")
        row_color.addWidget(self.color_preview)

        row_color.addStretch()
        btn_reset_color = QPushButton("Default"); btn_reset_color.setCursor(Qt.CursorShape.PointingHandCursor); btn_reset_color.setFixedSize(60, 26); btn_reset_color.setStyleSheet("font-size: 11px;")
        btn_reset_color.clicked.connect(self._reset_ocr_color)
        row_color.addWidget(btn_reset_color)
        l_scan.addLayout(row_color)

        # -- Ultra Wide & Debug Toggles --
        l_scan.addSpacing(10)
        self.chk_ultrawide = ModernToggle("Ultra-Wide / 4K Monitor Fix (Full Screen Scan)")
        self.chk_ultrawide.setToolTip("Enable this if the scanner doesn't find items due to monitor scaling.\nIt scans the entire screen.")
        l_scan.addWidget(self.chk_ultrawide)

        self.chk_debug_save = ModernToggle("Save Debug Images (to Pictures/ArcCompanion_Debug)")
        self.chk_debug_save.setToolTip("Saves the raw screenshot and the processed OCR image for troubleshooting.\nDefault: OFF")
        l_scan.addWidget(self.chk_debug_save)

        layout.addWidget(card_scan)
        return page

    # --- DATA MANAGEMENT TAB ---
    def setup_data_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        layout.addWidget(QLabel("Data & Backup", objectName="Header"))

        card = SettingsCard()
        l_card = QVBoxLayout(card)
        l_card.setContentsMargins(15, 15, 15, 15)
        l_card.setSpacing(12)

        info_label = QLabel("Back up your settings and progress data to a zip file.\nYou can restore it easily using the 'Restore Backup' button.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #ABB2BF; font-size: 13px; border: none; background: transparent;")
        l_card.addWidget(info_label)

        l_card.addSpacing(10)

        btn_layout = QHBoxLayout()

        btn_backup = QPushButton("Create Backup")
        btn_backup.setFixedSize(160, 36)
        btn_backup.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_backup.setStyleSheet("""
            QPushButton {
                background-color: #3E4451;
                color: white;
                border: 1px solid #555;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #4B5363;
                border-color: #777;
            }
        """)
        btn_backup.clicked.connect(self._backup_data)

        btn_restore = QPushButton("Restore Backup")
        btn_restore.setFixedSize(160, 36)
        btn_restore.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_restore.setStyleSheet("""
            QPushButton {
                background-color: #3E4451;
                color: #E5C07B;
                border: 1px solid #E5C07B;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #4B5363;
                border-color: #F0D080;
            }
        """)
        btn_restore.clicked.connect(self._restore_data)

        btn_layout.addWidget(btn_backup)
        btn_layout.addSpacing(15)
        btn_layout.addWidget(btn_restore)
        btn_layout.addStretch()

        l_card.addLayout(btn_layout)

        layout.addWidget(card)
        layout.addStretch()

        return page

    def _backup_data(self):
        try:
            dest_dir = QFileDialog.getExistingDirectory(self, "Select Backup Location")
            if not dest_dir: return
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            zip_filename = f"ArcCompanion_Backup_{timestamp}.zip"
            zip_path = os.path.join(dest_dir, zip_filename)
            files_to_backup = [Constants.PROGRESS_FILE, Constants.CONFIG_FILE]
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in files_to_backup:
                    if os.path.exists(file_path):
                        zipf.write(file_path, arcname=os.path.basename(file_path))
            QMessageBox.information(self, "Backup Successful", f"Backup created successfully:\n{zip_path}")
        except Exception as e:
            QMessageBox.warning(self, "Backup Failed", f"An error occurred while creating backup:\n{e}")

    def _restore_data(self):
        try:
            zip_path, _ = QFileDialog.getOpenFileName(self, "Select Backup File", "", "Zip Files (*.zip)")
            if not zip_path: return
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                file_list = zipf.namelist()
                has_progress = os.path.basename(Constants.PROGRESS_FILE) in file_list
                has_config = os.path.basename(Constants.CONFIG_FILE) in file_list
                if not has_progress and not has_config:
                    QMessageBox.warning(self, "Invalid Backup", "The selected zip file does not contain a valid backup.")
                    return
                reply = QMessageBox.question(self, "Confirm Restore", "This will OVERWRITE your current settings and progress.\nAre you sure?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    target_files = [os.path.basename(Constants.PROGRESS_FILE), os.path.basename(Constants.CONFIG_FILE)]
                    for filename in target_files:
                        if filename in file_list:
                             target_path = os.path.join(Constants.DATA_DIR, filename)
                             with zipf.open(filename) as source, open(target_path, "wb") as target:
                                 shutil.copyfileobj(source, target)
                    if self.data_manager: self.data_manager.reload_progress()
                    self.cfg.load(); self.load_settings()
                    if self.on_save_callback: self.on_save_callback()
                    self.data_restored.emit()
                    QMessageBox.information(self, "Restore Successful", "Data restored and reloaded successfully.")
        except Exception as e:
            QMessageBox.warning(self, "Restore Failed", f"An error occurred while restoring backup:\n{e}")

    # --- ITEM OVERLAY TAB ---
    def setup_item_overlay_tab(self):
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(10, 10, 10, 10); layout.setAlignment(Qt.AlignmentFlag.AlignTop); splitter = QHBoxLayout(); splitter.setSpacing(15); left_col = QVBoxLayout()
        card_app = SettingsCard(); l_app = QVBoxLayout(card_app); l_app.setContentsMargins(10, 10, 10, 10)
        self.item_font_size = self._create_slider(l_app, "Font Size:", 8, 24, 12, "pt", lambda: self.update_preview())
        self.item_duration = self._create_slider(l_app, "Duration:", 1, 10, 3, "s", float_scale=True)
        self.item_opacity = self._create_slider(l_app, "Opacity:", 20, 100, 98, "%")
        l_app.addSpacing(5)
        self.slider_offset_x = self._create_slider(l_app, "Offset X:", -1000, 1000, 0, "px", step_scale=50)
        self.slider_offset_y = self._create_slider(l_app, "Offset Y:", -1000, 1000, 0, "px", step_scale=50)
        wrapper = QHBoxLayout(); wrapper.addWidget(QLabel("Position:", styleSheet="color: #E0E6ED; font-size: 13px; min-width: 80px; border:none; background:transparent;"))
        self.cmb_anchor = QComboBox(); self.cmb_anchor.addItems(["Mouse", "Top Left", "Top Center", "Top Right", "Center Left", "Center", "Center Right", "Bottom Left", "Bottom Center", "Bottom Right"]); self.cmb_anchor.setStyleSheet("QComboBox { background: #2C313C; color: #E0E6ED; border: 1px solid #3E4451; padding: 5px; border-radius: 4px; }"); wrapper.addWidget(self.cmb_anchor); l_app.addLayout(wrapper); left_col.addWidget(card_app)
        card_mod = SettingsCard(); l_mod = QVBoxLayout(card_mod); l_mod.setContentsMargins(10, 10, 10, 10); self.chk_future_hideout = ModernToggle("Show All Future Hideout Requirements"); self.chk_future_project = ModernToggle("Show All Future Project Requirements"); l_mod.addWidget(self.chk_future_hideout); l_mod.addWidget(self.chk_future_project); left_col.addWidget(card_mod)
        lbl_list = QLabel("Order & Visibility (Drag to reorder)"); lbl_list.setStyleSheet("font-weight: bold; margin-top: 5px; color: #9DA5B4; border:none; background:transparent;"); left_col.addWidget(lbl_list)
        self.overlay_order_list = QListWidget(); self.overlay_order_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove); self.overlay_order_list.setDefaultDropAction(Qt.DropAction.MoveAction); self.overlay_order_list.setStyleSheet("QListWidget { background-color: #232834; border: 1px solid #333; border-radius: 4px; outline: 0; } QListWidget::item { padding: 4px; background-color: #1A1F2B; border-bottom: 1px solid #333; margin: 2px; color: #E0E6ED; } QListWidget::indicator { width: 20px; height: 20px; border: 1px solid #555; background: #15181E; border-radius: 3px; margin-right: 10px; } QListWidget::indicator:checked { background-color: #4CAF50; border: 1px solid #4CAF50; image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjQiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBvbHlsaW5lIHBvaW50cz0iMjAgNiA5IDE3IDQgMTIiPjwvcG9seWxpbmU+PC9zdmc+); }"); self.overlay_order_list.setFixedHeight(315); self.overlay_order_list.itemChanged.connect(self.update_preview); self.overlay_order_list.model().rowsMoved.connect(self.update_preview); left_col.addWidget(self.overlay_order_list); splitter.addLayout(left_col, stretch=3)
        right_col = QVBoxLayout(); right_col.setAlignment(Qt.AlignmentFlag.AlignTop); right_col.addWidget(QLabel("Live Preview", alignment=Qt.AlignmentFlag.AlignCenter, styleSheet="border:none; background:transparent; font-weight:bold; color: #ABB2BF;")); self.preview_frame = QFrame(); self.preview_frame.setFixedWidth(300); self.preview_frame.setStyleSheet("QFrame { background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 rgba(35, 39, 47, 240), stop:1 rgba(22, 26, 33, 250)); border: 1px solid rgba(255, 255, 255, 0.1); border-top: 3px solid #555; border-radius: 8px; } QLabel { color: #E0E6ED; background: transparent; border: none; }"); shadow = QGraphicsDropShadowEffect(); shadow.setBlurRadius(25); shadow.setXOffset(0); shadow.setYOffset(6); shadow.setColor(QColor(0, 0, 0, 180)); self.preview_frame.setGraphicsEffect(shadow); self.p_layout = QVBoxLayout(self.preview_frame); self.p_layout.setContentsMargins(12, 10, 12, 10); self.p_layout.setSpacing(4); self.p_layout.addStretch(); right_col.addWidget(self.preview_frame); splitter.addLayout(right_col, stretch=2); layout.addLayout(splitter); return page

    # --- QUEST OVERLAY TAB ---
    def setup_quest_overlay_tab(self):
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(10, 10, 10, 10); layout.setAlignment(Qt.AlignmentFlag.AlignTop); card = SettingsCard(); l = QVBoxLayout(card); l.setSpacing(10); l.setContentsMargins(10, 10, 10, 10); self.quest_font_size = self._create_slider(l, "Font Size:", 8, 24, 12, "pt"); self.quest_width = self._create_slider(l, "Width:", 200, 600, 350, "px"); self.quest_opacity = self._create_slider(l, "Opacity:", 30, 100, 95, "%"); self.quest_duration = self._create_slider(l, "Duration:", 1, 20, 5, "s", float_scale=True); layout.addWidget(card); return page

    # --- HELPERS ---
    def _create_slider(self, layout, label, min_v, max_v, default, suffix, callback=None, float_scale=False, step_scale=1):
        row = QHBoxLayout(); row.addWidget(QLabel(label, styleSheet="color: #E0E6ED; font-size: 13px; min-width: 80px; border:none; background:transparent;")); val_lbl = QLabel(f"{default}{suffix}"); val_lbl.setFixedWidth(50); val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); val_lbl.setStyleSheet("color: #4476ED; font-weight: bold; border:none; background:transparent;"); slider = QSlider(Qt.Orientation.Horizontal); slider.setStyleSheet("QSlider::groove:horizontal { height: 4px; background: #3E4451; border-radius: 2px; } QSlider::handle:horizontal { background: #4476ED; width: 16px; margin: -6px 0; border-radius: 8px; }"); real_min = min_v * 10 if float_scale else (min_v // step_scale if step_scale > 1 else min_v); real_max = max_v * 10 if float_scale else (max_v // step_scale if step_scale > 1 else max_v); real_def = int(default * 10) if float_scale else (default // step_scale if step_scale > 1 else default); slider.setRange(real_min, real_max); slider.setValue(real_def)
        def update_lbl(v):
            d = v/10.0 if float_scale else (v * step_scale if step_scale > 1 else v)
            val_lbl.setText(f"{d:.1f}{suffix}" if float_scale else f"{d}{suffix}")
        if callback: slider.valueChanged.connect(lambda: callback())
        slider.valueChanged.connect(update_lbl); row.addWidget(slider); row.addWidget(val_lbl); layout.addLayout(row); return slider

    def _create_color_spinbox(self):
        spin = QSpinBox(); spin.setRange(0, 255); spin.setFixedWidth(45); spin.setAlignment(Qt.AlignmentFlag.AlignCenter); spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons); spin.setStyleSheet("QSpinBox { background-color: #232834; color: #E0E6ED; border: 1px solid #333; padding: 4px; border-radius: 4px; font-weight: bold; } QSpinBox:focus { border: 1px solid #4476ED; }"); return spin

    def _update_color_preview(self): r = self.spin_r.value(); g = self.spin_g.value(); b = self.spin_b.value(); self.color_preview.setStyleSheet(f"border: 1px solid #555; border-radius: 4px; background-color: rgb({r}, {g}, {b});")

    def _reset_ocr_color(self): r, g, b = self.DEFAULT_OCR_COLOR; self.spin_r.setValue(r); self.spin_g.setValue(g); self.spin_b.setValue(b); self._update_color_preview()

    def _start_color_pick(self): self.btn_pick_color.setText("3..."); self.btn_pick_color.setEnabled(False); self.picker_timer.start(1000)

    def _perform_color_pick(self):
        txt = self.btn_pick_color.text()
        if txt == "3...": self.btn_pick_color.setText("2..."); self.picker_timer.start(1000)
        elif txt == "2...": self.btn_pick_color.setText("1..."); self.picker_timer.start(1000)
        elif txt == "1...":
            try:
                screen = QApplication.primaryScreen(); pos = QCursor.pos(); pix = screen.grabWindow(0, pos.x(), pos.y(), 1, 1); img = pix.toImage(); col = img.pixelColor(0, 0); self.spin_r.setValue(col.red()); self.spin_g.setValue(col.green()); self.spin_b.setValue(col.blue())
            except: pass
            self.btn_pick_color.setText("Pick Color (3s)"); self.btn_pick_color.setEnabled(True)

    def update_preview(self):
        if not hasattr(self, 'item_font_size'): return
        while self.p_layout.count():
            item = self.p_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget(): sub.widget().deleteLater()
        
        dummy_data = {
            'item_data': {'id': 'vita_spray', 'name': {'en': 'Vita Spray'}, 'rarity': 'Epic', 'value': 14500, 'imageFilename': 'vita_spray.png', 'recyclesInto': {'circuit_board': 1}, 'salvagesInto': {'scrap_metal': 3}},
            'hideout_reqs': [['Med Bay (Lvl 2): x3', 'next', False]],
            'project_reqs': [['Radio Tower (Ph2): x1', 'future', False]],
            'quest_reqs': [['Collect Samples: x3', True, False]],
            'trade_info': [{'trader': 'Celeste', 'cost': {'itemId': 'assorted_seeds', 'quantity': 1}}],
            'crafting_info': [['Assault Rifle (Lv3): x2', 'next', False]],
            'stash_count': 4,
            'user_note': 'quest item, keep',
            'is_tracked': False,
            'toggle_track_callback': None
        }

        class MockDM:
            def get_localized_name(self, item, lang='en'):
                if isinstance(item, dict): return item.get('name', {}).get('en', 'Unknown')
                return str(item).replace('_', ' ').title()
            def is_item_tracked(self, iid): return False

        class ProxyCfg:
            def __init__(self, p): self.p = p
            def getint(self, s, k, f=0): return self.p.item_font_size.value() if s == 'ItemOverlay' and k == 'font_size' else self.p.cfg.getint(s, k, f)
            def get(self, s, k, f=""):
                if s == 'ItemOverlay' and k == 'section_order':
                    res = []
                    for i in range(self.p.overlay_order_list.count()):
                        it = self.p.overlay_order_list.item(i)
                        if it.checkState() == Qt.CheckState.Checked: res.append(it.data(Qt.ItemDataRole.UserRole))
                    return ",".join(res)
                return self.p.cfg.get(s, k, f)
            def getboolean(self, s, k, f=True): return self.p.chk_future_hideout.isChecked() if k == 'show_all_future_reqs' else (self.p.chk_future_project.isChecked() if k == 'show_all_future_project_reqs' else True)
            def getfloat(self, s, k, f=0.0): return self.p.cfg.getfloat(s,k,f)

        rarity_color = Constants.RARITY_COLORS.get('Epic', "#FFFFFF")
        self.preview_frame.setStyleSheet(self.preview_frame.styleSheet().replace("border-top: 3px solid #555;", f"border-top: 3px solid {rarity_color};"))
        OverlayRenderer.populate(self.p_layout, dummy_data, ProxyCfg(self), MockDM(), "en")
        self.p_layout.addStretch()

    def load_settings(self):
        self.hotkey_btn.set_hotkey(self.cfg.get_item_hotkey()); self.quest_hotkey_btn.set_hotkey(self.cfg.get_quest_hotkey()); self.hub_hotkey_btn.set_hotkey(self.cfg.get_hub_hotkey())
        self.start_hotkey_price = self.hotkey_btn.current_key_string; self.start_hotkey_quest = self.quest_hotkey_btn.current_key_string; self.start_hotkey_hub = self.hub_hotkey_btn.current_key_string
        lang = self.cfg.get_language()
        for n, (j, t) in Constants.LANGUAGES.items():
            if t == lang or j == lang: self.lang_combo.setCurrentText(n); break
        col = self.cfg.get_ocr_color()
        try: parts = [int(x.strip()) for x in col.split(',')]; self.spin_r.setValue(parts[0]); self.spin_g.setValue(parts[1]); self.spin_b.setValue(parts[2])
        except: self._reset_ocr_color()
        self._update_color_preview(); self.item_font_size.setValue(self.cfg.get_item_font_size()); self.item_duration.setValue(int(self.cfg.get_item_duration() * 10)); self.item_opacity.setValue(self.cfg.get_item_opacity())
        idx = self.cmb_anchor.findText(self.cfg.get_item_anchor_mode()); self.cmb_anchor.setCurrentIndex(max(0, idx))
        self.slider_offset_x.setValue(self.cfg.get_item_offset_x() // 50); self.slider_offset_y.setValue(self.cfg.get_item_offset_y() // 50)
        self.chk_future_hideout.setChecked(self.cfg.get_show_future_hideout()); self.chk_future_project.setChecked(self.cfg.get_show_future_project()); self.chk_ultrawide.setChecked(self.cfg.get_full_screen_scan()); self.chk_debug_save.setChecked(self.cfg.get_save_debug_images())
        saved = [x.strip() for x in self.cfg.get_overlay_section_order().split(',') if x.strip() in self.SECTIONS]
        for k in self.DEFAULT_ORDER:
            if k not in saved: saved.append(k)
        self.overlay_order_list.blockSignals(True); self.overlay_order_list.clear()
        for k in saved:
            it = QListWidgetItem(self.SECTIONS[k][0]); it.setData(Qt.ItemDataRole.UserRole, k); it.setCheckState(Qt.CheckState.Checked if self.cfg.get_bool('ItemOverlay', self.SECTIONS[k][1], True) else Qt.CheckState.Unchecked); self.overlay_order_list.addItem(it)
        self.overlay_order_list.blockSignals(False); self.quest_font_size.setValue(self.cfg.get_quest_font_size()); self.quest_width.setValue(self.cfg.get_quest_width()); self.quest_opacity.setValue(self.cfg.get_quest_opacity()); self.quest_duration.setValue(int(self.cfg.get_quest_duration() * 10))
        QTimer.singleShot(100, self.update_preview)

    def save_settings(self):
        self.cfg.set('Hotkeys', 'price_check', self.hotkey_btn.current_key_string); self.cfg.set('Hotkeys', 'quest_log', self.quest_hotkey_btn.current_key_string); self.cfg.set('Hotkeys', 'hub_hotkey', self.hub_hotkey_btn.current_key_string)
        disp = self.lang_combo.currentText()
        if disp in Constants.LANGUAGES: self.cfg.set_language(Constants.LANGUAGES[disp][1])
        self.cfg.set_ocr_color(f"{self.spin_r.value()}, {self.spin_g.value()}, {self.spin_b.value()}"); self.cfg.set_full_screen_scan(self.chk_ultrawide.isChecked()); self.cfg.set_save_debug_images(self.chk_debug_save.isChecked())
        order, states = [], {}
        for i in range(self.overlay_order_list.count()):
            it = self.overlay_order_list.item(i); k = it.data(Qt.ItemDataRole.UserRole); order.append(k); states[self.SECTIONS[k][1]] = (it.checkState() == Qt.CheckState.Checked)
        self.cfg.set_item_overlay_settings(self.item_font_size.value(), self.item_duration.value()/10.0, self.chk_future_hideout.isChecked(), self.chk_future_project.isChecked(), self.slider_offset_x.value() * 50, self.slider_offset_y.value() * 50, self.cmb_anchor.currentText(), self.item_opacity.value(), ",".join(order), states)
        self.cfg.set_quest_overlay_settings(self.quest_font_size.value(), self.quest_width.value(), self.quest_opacity.value(), self.quest_duration.value()/10.0)
        self.cfg.save()
        if self.hotkey_btn.current_key_string != self.start_hotkey_price or self.quest_hotkey_btn.current_key_string != self.start_hotkey_quest or self.hub_hotkey_btn.current_key_string != self.start_hotkey_hub:
             self.start_hotkey_price = self.hotkey_btn.current_key_string; self.start_hotkey_quest = self.quest_hotkey_btn.current_key_string; self.start_hotkey_hub = self.hub_hotkey_btn.current_key_string; self.hotkeys_updated.emit()
        if self.on_save_callback: self.on_save_callback()
        QMessageBox.information(self, "Saved", "Settings saved successfully.")

    def reset_current_tab(self):
        idx = self.tabs.currentIndex(); txt = self.tabs.tabText(idx)
        if QMessageBox.question(self, "Reset", f"Reset '{txt}' to defaults?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            if txt == "General": self._reset_general_tab()
            elif txt == "Item Overlay": self._reset_item_overlay_tab()
            elif txt == "Quest Overlay": self._reset_quest_overlay_tab()

    def _reset_general_tab(self):
        for n, (j, t) in Constants.LANGUAGES.items():
            if t == self.cfg.DEFAULT_LANG: self.lang_combo.setCurrentText(n); break
        self.hotkey_btn.set_hotkey(self.cfg.DEFAULT_HOTKEY_PRICE); self.quest_hotkey_btn.set_hotkey(self.cfg.DEFAULT_HOTKEY_QUEST); self.hub_hotkey_btn.set_hotkey(self.cfg.DEFAULT_HOTKEY_HUB); self._reset_ocr_color(); self.chk_ultrawide.setChecked(self.cfg.DEFAULT_FULL_SCREEN); self.chk_debug_save.setChecked(self.cfg.DEFAULT_DEBUG_SAVE)

    def _reset_item_overlay_tab(self):
        self.item_font_size.setValue(self.cfg.DEFAULT_ITEM_FONT); self.item_duration.setValue(int(self.cfg.DEFAULT_ITEM_DURATION * 10)); self.slider_offset_x.setValue(self.cfg.DEFAULT_ITEM_OFFSET_X); self.slider_offset_y.setValue(self.cfg.DEFAULT_ITEM_OFFSET_Y); self.item_opacity.setValue(self.cfg.DEFAULT_ITEM_OPACITY); self.cmb_anchor.setCurrentText(self.cfg.DEFAULT_ANCHOR_MODE); self.chk_future_hideout.setChecked(self.cfg.DEFAULT_SHOW_FUTURE_HIDEOUT); self.chk_future_project.setChecked(self.cfg.DEFAULT_SHOW_FUTURE_PROJECT); self.overlay_order_list.clear()
        for k in self.cfg.DEFAULT_SECTION_ORDER.split(','):
            if k.strip() in self.SECTIONS:
                it = QListWidgetItem(self.SECTIONS[k.strip()][0]); it.setData(Qt.ItemDataRole.UserRole, k.strip()); it.setCheckState(Qt.CheckState.Checked); self.overlay_order_list.addItem(it)
        self.update_preview()

    def _reset_quest_overlay_tab(self):
        self.quest_font_size.setValue(self.cfg.DEFAULT_QUEST_FONT); self.quest_width.setValue(self.cfg.DEFAULT_QUEST_WIDTH); self.quest_opacity.setValue(self.cfg.DEFAULT_QUEST_OPACITY); self.quest_duration.setValue(int(self.cfg.DEFAULT_QUEST_DURATION * 10))