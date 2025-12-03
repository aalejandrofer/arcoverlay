from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QSlider, QPushButton, QComboBox, QStackedWidget, QFrame, 
    QGraphicsDropShadowEffect, QMessageBox, QTabWidget, QListWidget, QListWidgetItem,
    QAbstractItemView, QSpinBox, QAbstractSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
import os

from .constants import Constants
from .ui_components import ModernToggle, SettingsCard, HotkeyButton
from .base_page import BasePage

class SettingsWindow(BasePage):
    # Signals
    request_data_update = pyqtSignal()
    request_lang_download = pyqtSignal(str)
    request_app_update = pyqtSignal()
    
    SECTIONS = {
        'price': ('Price', 'show_price'),
        'storage': ('Stash Count', 'show_storage_info'),
        'trader': ('Trader Info', 'show_trader_info'),
        'notes': ('User Notes', 'show_notes'),
        'crafting': ('Crafting Info', 'show_crafting_info'),
        'hideout': ('Hideout Reqs', 'show_hideout_reqs'),
        'project': ('Project Reqs', 'show_project_reqs'),
        'recycle': ('Recycles Into', 'show_recycles_into'),
        'salvage': ('Salvages Into', 'show_salvages_into')
    }
    DEFAULT_ORDER = ['price', 'storage', 'trader', 'notes', 'crafting', 'hideout', 'project', 'recycle', 'salvage']
    DEFAULT_OCR_COLOR = (249, 238, 223)

    def __init__(self, config_manager, on_save_callback=None):
        super().__init__("Application Settings") 
        self.cfg = config_manager
        self.on_save_callback = on_save_callback
        
        self.start_hotkey_price = ""
        self.start_hotkey_quest = ""
        self.preview_widgets = {} 

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
        self.tabs.addTab(self.setup_item_overlay_tab(), "Item Overlay")
        self.tabs.addTab(self.setup_quest_overlay_tab(), "Quest Overlay")
        self.tabs.addTab(self.setup_updates_tab(), "Updates")

        self.footer_layout.addStretch()
        
        self.btn_revert = QPushButton("Revert Changes")
        self.btn_revert.setObjectName("action_button_red")
        self.btn_revert.setFixedSize(130, 32)
        self.btn_revert.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_revert.clicked.connect(self.load_settings)
        
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
        
        # Controls Row
        row_color = QHBoxLayout()
        row_color.setSpacing(15)
        
        # Create Spinboxes
        self.spin_r = self._create_color_spinbox()
        self.spin_g = self._create_color_spinbox()
        self.spin_b = self._create_color_spinbox()

        # Connect updates
        self.spin_r.valueChanged.connect(self._update_color_preview)
        self.spin_g.valueChanged.connect(self._update_color_preview)
        self.spin_b.valueChanged.connect(self._update_color_preview)

        # Helper to create the [ - ] [ 123 ] [ + ] layout
        def add_rgb_control(layout, label, color_hex, spinbox):
            container = QWidget()
            h_layout = QHBoxLayout(container)
            h_layout.setContentsMargins(0, 0, 0, 0)
            h_layout.setSpacing(2)

            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {color_hex}; font-weight:bold; border:none; background:transparent; margin-right: 5px;")
            
            # FIXED: Added 'padding: 0px' and increased width to 24 so symbols are visible
            btn_style = """
                QPushButton { 
                    background-color: #3E4451; 
                    color: white; 
                    border: 1px solid #555; 
                    border-radius: 3px; 
                    font-weight: bold; 
                    padding: 0px; 
                } 
                QPushButton:hover { 
                    background-color: #4B5363; 
                    border-color: #777; 
                }
            """
            
            btn_minus = QPushButton("-")
            btn_minus.setFixedSize(24, 26) 
            btn_minus.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_minus.setStyleSheet(btn_style)
            btn_minus.clicked.connect(spinbox.stepDown)

            btn_plus = QPushButton("+")
            btn_plus.setFixedSize(24, 26) 
            btn_plus.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_plus.setStyleSheet(btn_style)
            btn_plus.clicked.connect(spinbox.stepUp)

            h_layout.addWidget(lbl)
            h_layout.addWidget(btn_minus)
            h_layout.addWidget(spinbox)
            h_layout.addWidget(btn_plus)
            
            layout.addWidget(container)

        # Add R, G, B controls
        add_rgb_control(row_color, "R:", "#FF6B6B", self.spin_r)
        add_rgb_control(row_color, "G:", "#51CF66", self.spin_g)
        add_rgb_control(row_color, "B:", "#339AF0", self.spin_b)
        
        # Preview
        row_color.addSpacing(10)
        row_color.addWidget(QLabel("Preview:", styleSheet="color: #AAA; font-size: 12px; border:none; background:transparent;"))
        self.color_preview = QFrame()
        self.color_preview.setFixedSize(32, 24)
        self.color_preview.setStyleSheet("border: 1px solid #555; border-radius: 4px; background-color: rgb(249, 238, 223);")
        row_color.addWidget(self.color_preview)

        # Default Button
        row_color.addStretch()
        btn_reset_color = QPushButton("Default")
        btn_reset_color.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reset_color.setFixedSize(60, 26)
        btn_reset_color.setStyleSheet("font-size: 11px;")
        btn_reset_color.clicked.connect(self._reset_ocr_color)
        row_color.addWidget(btn_reset_color)

        l_scan.addLayout(row_color)
        
        help_txt = QLabel("Adjust these values if the scanner fails to detect the tooltip background color.\nThe default (249, 238, 223) works for standard brightness settings.")
        help_txt.setWordWrap(True)
        help_txt.setStyleSheet("color: #888; font-style: italic; font-size: 11px; margin-top: 5px; border:none; background:transparent;")
        l_scan.addWidget(help_txt)
        
        layout.addWidget(card_scan)

        return page

    def setup_updates_tab(self):
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(10, 10, 10, 10); layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        layout.addWidget(QLabel("Update Management", objectName="Header"))
        card_upd = SettingsCard()
        l_upd = QVBoxLayout(card_upd)
        l_upd.setContentsMargins(15, 15, 15, 15)
        l_upd.setSpacing(12)

        # App Update
        row_app = QHBoxLayout()
        row_app.addWidget(QLabel("Application Version:", styleSheet="color: #ABB2BF; font-weight: bold; border: none; background: transparent; font-size: 14px;"))
        row_app.addStretch()
        app_check_btn = QPushButton("Check for App Updates")
        app_check_btn.setFixedWidth(180)
        app_check_btn.setFixedHeight(30)
        app_check_btn.setStyleSheet("QPushButton { background-color: #3E4451; color: white; border: 1px solid #555; font-weight: bold; border-radius: 4px; font-size: 12px;} QPushButton:hover { background-color: #4B5363; border-color: #777; }")
        app_check_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        app_check_btn.clicked.connect(self.request_app_update.emit)
        row_app.addWidget(app_check_btn)
        l_upd.addLayout(row_app)

        div_upd = QFrame(); div_upd.setFrameShape(QFrame.Shape.HLine); div_upd.setStyleSheet("background: #333;")
        l_upd.addWidget(div_upd)

        # Data Update
        row_data = QHBoxLayout()
        data_lbl_layout = QVBoxLayout()
        data_lbl_layout.setSpacing(2)
        data_lbl_layout.addWidget(QLabel("Data & Language Files:", styleSheet="color: #ABB2BF; font-weight: bold; border: none; background: transparent; font-size: 14px;"))
        self.update_status_label = QLabel("Ready")
        self.update_status_label.setStyleSheet("font-size: 12px; color: #E0E6ED; border: none; background: transparent; font-style: italic;")
        data_lbl_layout.addWidget(self.update_status_label)
        
        row_data.addLayout(data_lbl_layout)
        row_data.addStretch()
        
        data_check_btn = QPushButton("Check for Data Updates")
        data_check_btn.setFixedWidth(180)
        data_check_btn.setFixedHeight(30)
        data_check_btn.setObjectName("action_button_green")
        data_check_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        data_check_btn.setStyleSheet("QPushButton { font-size: 12px; }")
        data_check_btn.clicked.connect(self.request_data_update.emit)
        row_data.addWidget(data_check_btn)
        
        l_upd.addLayout(row_data)
        layout.addWidget(card_upd)
        
        return page

    def setup_item_overlay_tab(self):
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(10, 10, 10, 10); layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        splitter = QHBoxLayout(); splitter.setSpacing(15)
        
        left_col = QVBoxLayout()
        
        # Appearance Card
        card_app = SettingsCard(); l_app = QVBoxLayout(card_app); l_app.setContentsMargins(10, 10, 10, 10)
        self.item_font_size = self._create_slider(l_app, "Font Size:", 8, 24, 12, "pt", lambda: self.update_preview())
        self.item_duration = self._create_slider(l_app, "Duration:", 1, 10, 3, "s", float_scale=True)
        left_col.addWidget(card_app)

        # Modifiers Card
        card_mod = SettingsCard(); l_mod = QVBoxLayout(card_mod); l_mod.setContentsMargins(10, 10, 10, 10)
        self.chk_future_hideout = ModernToggle("Show All Future Hideout Requirements")
        self.chk_future_project = ModernToggle("Show All Future Project Requirements")
        l_mod.addWidget(self.chk_future_hideout); l_mod.addWidget(self.chk_future_project)
        left_col.addWidget(card_mod)

        lbl_list = QLabel("Order & Visibility (Drag to reorder)"); lbl_list.setStyleSheet("font-weight: bold; margin-top: 5px; color: #9DA5B4; border:none; background:transparent;")
        left_col.addWidget(lbl_list)
        
        self.overlay_order_list = QListWidget(); self.overlay_order_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.overlay_order_list.setDefaultDropAction(Qt.DropAction.MoveAction)
        
        # --- FIXED STYLESHEET FOR VISIBILITY ---
        self.overlay_order_list.setStyleSheet("""
            QListWidget { 
                background-color: #232834; 
                border: 1px solid #333; 
                border-radius: 4px; 
                outline: 0;
            }
            QListWidget::item { 
                padding: 4px; 
                background-color: #1A1F2B; 
                border-bottom: 1px solid #333; 
                margin: 2px; 
                color: #E0E6ED;
            }
            QListWidget::item:selected { 
                background-color: #3E4451; 
                border: 1px solid #4476ED; 
            }
            QListWidget::indicator {
                width: 20px; 
                height: 20px; 
                border: 1px solid #555; 
                background: #15181E; 
                border-radius: 3px;
                margin-right: 10px;
            }
            QListWidget::indicator:hover { 
                border: 1px solid #4CAF50; 
            }
            QListWidget::indicator:checked { 
                background-color: #4CAF50; 
                border: 1px solid #4CAF50;
                image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjQiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBvbHlsaW5lIHBvaW50cz0iMjAgNiA5IDE3IDQgMTIiPjwvcG9seWxpbmU+PC9zdmc+);
            }
        """)
        
        self.overlay_order_list.setFixedHeight(315)
        self.overlay_order_list.itemChanged.connect(self.update_preview); self.overlay_order_list.model().rowsMoved.connect(self.update_preview)
        left_col.addWidget(self.overlay_order_list); splitter.addLayout(left_col, stretch=3)

        right_col = QVBoxLayout(); right_col.setAlignment(Qt.AlignmentFlag.AlignTop)
        right_col.addWidget(QLabel("Live Preview", alignment=Qt.AlignmentFlag.AlignCenter, styleSheet="border:none; background:transparent; font-weight:bold; color: #ABB2BF;"))
        self.preview_frame = QFrame(); self.preview_frame.setFixedWidth(300)
        self.preview_frame.setStyleSheet("QFrame { background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #2B303B, stop:1 #1A1F26); border: 1px solid #3E4451; border-top: 3px solid #C678DD; border-radius: 5px; } QLabel { color: #E0E6ED; background: transparent; border: none; }")
        shadow = QGraphicsDropShadowEffect(); shadow.setBlurRadius(15); shadow.setColor(QColor(0,0,0,150)); shadow.setYOffset(4); self.preview_frame.setGraphicsEffect(shadow)
        self.p_layout = QVBoxLayout(self.preview_frame); self.p_layout.setContentsMargins(12, 10, 12, 10); self.p_layout.setSpacing(4)
        
        self.p_title = QLabel("Example Item Name"); self.p_title.setWordWrap(True); self.p_title.setStyleSheet("font-weight: bold; color: #C678DD;")
        self.p_layout.addWidget(self.p_title)
        
        self._build_preview_content()
        self.p_layout.addStretch(); right_col.addWidget(self.preview_frame)
        splitter.addLayout(right_col, stretch=2); layout.addLayout(splitter)
        return page

    def setup_quest_overlay_tab(self):
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(10, 10, 10, 10); layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        card = SettingsCard(); l = QVBoxLayout(card); l.setSpacing(10); l.setContentsMargins(10, 10, 10, 10)
        self.quest_font_size = self._create_slider(l, "Font Size:", 8, 24, 12, "pt")
        self.quest_width = self._create_slider(l, "Width:", 200, 600, 350, "px")
        self.quest_opacity = self._create_slider(l, "Opacity:", 30, 100, 95, "%")
        self.quest_duration = self._create_slider(l, "Duration:", 1, 20, 5, "s", float_scale=True)
        layout.addWidget(card); return page

    # --- HELPERS ---
    def _create_slider(self, layout, label, min_v, max_v, default, suffix, callback=None, float_scale=False):
        row = QHBoxLayout(); row.addWidget(QLabel(label, styleSheet="color: #E0E6ED; font-size: 13px; min-width: 80px; border:none; background:transparent;"))
        val_lbl = QLabel(f"{default}{suffix}"); val_lbl.setFixedWidth(50); val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); val_lbl.setStyleSheet("color: #4476ED; font-weight: bold; border:none; background:transparent;")
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setStyleSheet("QSlider::groove:horizontal { height: 4px; background: #3E4451; border-radius: 2px; } QSlider::handle:horizontal { background: #4476ED; width: 16px; margin: -6px 0; border-radius: 8px; }")
        slider.setRange(min_v*10 if float_scale else min_v, max_v*10 if float_scale else max_v)
        slider.setValue(int(default*10) if float_scale else default)
        
        def update_lbl(v):
            d = v/10.0 if float_scale else v; val_lbl.setText(f"{d:.1f}{suffix}" if float_scale else f"{d}{suffix}")
            if callback: callback()
        slider.valueChanged.connect(update_lbl)
        row.addWidget(slider); row.addWidget(val_lbl); layout.addLayout(row)
        return slider

    def _create_color_spinbox(self):
        spin = QSpinBox()
        spin.setRange(0, 255)
        spin.setFixedWidth(45) 
        spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # CORRECTED LINE:
        spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        
        spin.setStyleSheet("""
            QSpinBox { background-color: #232834; color: #E0E6ED; border: 1px solid #333; padding: 4px; border-radius: 4px; font-weight: bold; }
            QSpinBox:focus { border: 1px solid #4476ED; }
        """)
        return spin

    def _update_color_preview(self):
        r = self.spin_r.value()
        g = self.spin_g.value()
        b = self.spin_b.value()
        self.color_preview.setStyleSheet(f"border: 1px solid #555; border-radius: 4px; background-color: rgb({r}, {g}, {b});")

    def _reset_ocr_color(self):
        r, g, b = self.DEFAULT_OCR_COLOR
        self.spin_r.setValue(r)
        self.spin_g.setValue(g)
        self.spin_b.setValue(b)
        self._update_color_preview()

    def _build_preview_content(self):
        def add(key, html, sub=None, sub_html=None):
            if key in self.SECTIONS: 
                sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
                # --- FIXED SEPARATOR STYLE ---
                sep.setStyleSheet("background-color: rgba(255, 255, 255, 0.1); max-height: 1px; border: none;")
                self.p_layout.addWidget(sep); self.preview_widgets[f"sep_{key}"] = sep
            l = QLabel(html); l.setWordWrap(True); self.p_layout.addWidget(l); self.preview_widgets[key] = l
            if sub: 
                sl = QLabel(sub_html); sl.setStyleSheet("color:#ABB2BF; margin-left:10px;")
                self.p_layout.addWidget(sl); self.preview_widgets[sub] = sl

        add("price", "Price: <span style='color:#E5C07B'>14,500</span>")
        add("storage", "Stash: <span style='color:#ABB2BF'>4</span>")
        add("trader", "<span style='color:#98C379'>Barkley: 2x Gold Watch</span>")
        add("notes", "<span style='color:#FFEB3B'>✎ Save for quest later</span>")
        add("crafting", "<span style='color:#5C6370; font-weight:bold'>Crafting</span>", "crafting_detail", "■ Advanced Bench (45s)")
        add("hideout", "<span style='color:#5C6370; font-weight:bold'>Hideout Upgrade:</span>", "hideout_detail", "■ Med Bay Lv.2: x3")
        add("project", "<span style='color:#5C6370; font-weight:bold'>Project Request:</span>", "project_detail", "■ Radio Tower (Ph2): x1")
        add("recycle", "<span style='color:#5C6370; font-weight:bold'>Recycles Into:</span>", "recycle_detail", "■ 1x Circuit Board")
        add("salvage", "<span style='color:#5C6370; font-weight:bold'>Salvages Into:</span>", "salvage_detail", "■ 2x Metal Scrap")

    def update_preview(self):
        size = self.item_font_size.value()
        
        # 1. Force styles via Stylesheet to override global theme
        # Title Style
        self.p_title.setStyleSheet(f"font-size: {size + 3}pt; font-weight: bold; color: #C678DD; border: none; background: transparent;")
        
        # Main Text Style
        style_main = f"font-size: {size}pt; color: #E0E6ED; border: none; background: transparent;"
        
        # Sub Text Style (Details like "Med Bay Lv.2") - includes indentation
        style_sub = f"font-size: {size}pt; color: #ABB2BF; margin-left: 10px; border: none; background: transparent;"

        # 2. Clear current preview layout (visually)
        for i in reversed(range(1, self.p_layout.count())):
            item = self.p_layout.itemAt(i)
            if item.widget(): 
                item.widget().setParent(None) # Detach from layout to hide
            else: 
                self.p_layout.removeItem(item)

        # 3. Rebuild layout based on enabled items
        first = True
        for i in range(self.overlay_order_list.count()):
            item = self.overlay_order_list.item(i)
            key = item.data(Qt.ItemDataRole.UserRole)
            
            # Check if enabled and exists in our widget cache
            if item.checkState() == Qt.CheckState.Checked and key in self.preview_widgets:
                w = self.preview_widgets[key]
                sep = self.preview_widgets.get(f"sep_{key}")
                
                # Add Separator (if not first item)
                if sep and not first: 
                    self.p_layout.addWidget(sep)
                    sep.show()
                
                # Add Main Label
                self.p_layout.addWidget(w)
                w.setStyleSheet(style_main) # Apply font size
                w.show()
                
                # Add Detail Label (if exists)
                sub = self.preview_widgets.get(f"{key}_detail")
                if sub: 
                    self.p_layout.addWidget(sub)
                    sub.setStyleSheet(style_sub) # Apply font size + margin
                    sub.show()
                
                first = False
                
        self.p_layout.addStretch()
        
        # 4. Adjust box width to fit larger text
        self.preview_frame.setFixedWidth(max(280, int(size * 22)))

    def save_state(self):
        self.save_settings()

    def reset_state(self):
        pass 

    def load_settings(self):
        # Hotkeys
        self.hotkey_btn.set_hotkey(self.cfg.get_str('Hotkeys', 'price_check', "ctrl+f"))
        self.quest_hotkey_btn.set_hotkey(self.cfg.get_str('Hotkeys', 'quest_log', "ctrl+e"))
        self.start_hotkey_price = self.hotkey_btn.current_key_string
        self.start_hotkey_quest = self.quest_hotkey_btn.current_key_string
        
        # General
        lang_code = self.cfg.get_str('General', 'language', 'eng')
        for name, (json_code, tess_code) in Constants.LANGUAGES.items():
            if tess_code == lang_code or json_code == lang_code:
                self.lang_combo.setCurrentText(name); break
        
        # OCR Color
        color_str = self.cfg.get_str('OCR', 'target_color', "249, 238, 223")
        try:
            parts = [int(x.strip()) for x in color_str.split(',')]
            if len(parts) == 3:
                self.spin_r.setValue(parts[0])
                self.spin_g.setValue(parts[1])
                self.spin_b.setValue(parts[2])
            else:
                self._reset_ocr_color()
        except ValueError:
            self._reset_ocr_color()

        self._update_color_preview()

        # Item Overlay
        self.item_font_size.setValue(self.cfg.get_int('ItemOverlay', 'font_size', 12))
        self.item_duration.setValue(int(self.cfg.get_float('ItemOverlay', 'duration_seconds', 3.0) * 10))
        self.chk_future_hideout.setChecked(self.cfg.get_bool('ItemOverlay', 'show_all_future_reqs', False))
        self.chk_future_project.setChecked(self.cfg.get_bool('ItemOverlay', 'show_all_future_project_reqs', False))
        
        # Order List - Check for fresh config
        is_fresh_config = not self.cfg.parser.has_section('ItemOverlay')

        saved_order = [x.strip() for x in self.cfg.get_str('ItemOverlay', 'section_order', "").split(',') if x.strip() in self.SECTIONS]
        for k in self.DEFAULT_ORDER: 
            if k not in saved_order: saved_order.append(k)
        
        self.overlay_order_list.clear()
        for key in saved_order:
            item = QListWidgetItem(self.SECTIONS[key][0])
            item.setData(Qt.ItemDataRole.UserRole, key)
            item.setCheckState(Qt.CheckState.Checked if self.cfg.get_bool('ItemOverlay', self.SECTIONS[key][1], True) else Qt.CheckState.Unchecked)
            self.overlay_order_list.addItem(item)

        # Force save defaults on first run so Overlay can read them
        if is_fresh_config:
            self._force_save_defaults(saved_order)
            
        # Quest Overlay
        self.quest_font_size.setValue(self.cfg.get_int('QuestOverlay', 'font_size', 12))
        self.quest_width.setValue(self.cfg.get_int('QuestOverlay', 'width', 350))
        self.quest_opacity.setValue(self.cfg.get_int('QuestOverlay', 'opacity', 95))
        self.quest_duration.setValue(int(self.cfg.get_float('QuestOverlay', 'duration_seconds', 5.0) * 10))
        
        self.update_preview()

    def _force_save_defaults(self, order_list):
        """Silently saves the defaults to config file for first-time run."""
        self.cfg.set('ItemOverlay', 'section_order', ",".join(order_list))
        for key in order_list:
             # Default to True for all standard sections on first run
             self.cfg.set('ItemOverlay', self.SECTIONS[key][1], True)
        self.cfg.save()

    def save_settings(self):
        self.cfg.set('Hotkeys', 'price_check', self.hotkey_btn.current_key_string)
        self.cfg.set('Hotkeys', 'quest_log', self.quest_hotkey_btn.current_key_string)
        
        display_name = self.lang_combo.currentText()
        if display_name in Constants.LANGUAGES:
            lang_code = Constants.LANGUAGES[display_name][1]
            self.cfg.set('General', 'language', lang_code)
            target = os.path.join(Constants.TESSDATA_DIR, f"{lang_code}.traineddata")
            if lang_code != 'eng' and not os.path.exists(target):
                 QMessageBox.information(self, "Download Required", f"Downloading language data for {display_name}...")
                 self.request_lang_download.emit(lang_code)

        # Save OCR Color
        color_str = f"{self.spin_r.value()}, {self.spin_g.value()}, {self.spin_b.value()}"
        self.cfg.set('OCR', 'target_color', color_str)

        self.cfg.set('ItemOverlay', 'font_size', self.item_font_size.value())
        self.cfg.set('ItemOverlay', 'duration_seconds', self.item_duration.value()/10.0)
        self.cfg.set('ItemOverlay', 'show_all_future_reqs', self.chk_future_hideout.isChecked())
        self.cfg.set('ItemOverlay', 'show_all_future_project_reqs', self.chk_future_project.isChecked())
        
        new_order = []
        for i in range(self.overlay_order_list.count()):
            item = self.overlay_order_list.item(i)
            key = item.data(Qt.ItemDataRole.UserRole)
            new_order.append(key)
            self.cfg.set('ItemOverlay', self.SECTIONS[key][1], item.checkState() == Qt.CheckState.Checked)
        self.cfg.set('ItemOverlay', 'section_order', ",".join(new_order))
        
        self.cfg.set('QuestOverlay', 'font_size', self.quest_font_size.value())
        self.cfg.set('QuestOverlay', 'width', self.quest_width.value())
        self.cfg.set('QuestOverlay', 'opacity', self.quest_opacity.value())
        self.cfg.set('QuestOverlay', 'duration_seconds', self.quest_duration.value()/10.0)
        
        self.cfg.save() 

        if self.hotkey_btn.current_key_string != self.start_hotkey_price or self.quest_hotkey_btn.current_key_string != self.start_hotkey_quest:
            QMessageBox.information(self, "Restart Required", "Hotkeys updated. Please restart the app.")
        
        if self.on_save_callback: self.on_save_callback()
        QMessageBox.information(self, "Saved", "Settings saved successfully.")

    def set_update_status(self, text):
        self.update_status_label.setText(text)