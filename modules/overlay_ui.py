from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QFrame, QGraphicsDropShadowEffect, QSizePolicy, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer, QPoint, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QCursor, QColor, QPixmap
import os
import math
from .constants import Constants

# =============================================================================
# SHARED RENDERER (Used by Overlay & Settings Preview)
# =============================================================================
class OverlayRenderer:
    @staticmethod
    def populate(container_layout, data_context, user_settings, data_manager, lang_code="en"):
        """
        Populates a layout with the item overlay UI elements.
        
        Args:
            container_layout (QLayout): The target layout to add widgets to.
            data_context (dict): Contains all display data:
                - item_data (dict)
                - hideout_reqs (list)
                - project_reqs (list)
                - quest_reqs (list)
                - stash_count (int)
                - is_tracked (bool)
            user_settings: The config object.
            data_manager: Reference to DataManager.
            lang_code (str): Language code.
        """
        # Unpack Context
        item_data = data_context.get('item_data', {})
        hideout_reqs = data_context.get('hideout_reqs', [])
        project_reqs = data_context.get('project_reqs', [])
        quest_reqs = data_context.get('quest_reqs', [])
        stash_count = data_context.get('stash_count', 0)
        is_tracked = data_context.get('is_tracked', False)
        toggle_track_callback = data_context.get('toggle_track_callback', None)
        
        # Settings
        font_size = user_settings.getint('ItemOverlay', 'font_size', fallback=12)
        rarity = item_data.get('rarity', 'Common')
        rarity_color = Constants.RARITY_COLORS.get(rarity, "#FFFFFF")

        # 1. Item Info Row (Image + Name + Track Button)
        info_row = QHBoxLayout()
        info_row.setSpacing(12)
        
        # Item Image
        img_filename = item_data.get('imageFilename')
        if img_filename:
            img_path = os.path.join(Constants.DATA_DIR, "images", "items", img_filename)
            if os.path.exists(img_path):
                img_lbl = QLabel()
                pix = QPixmap(img_path).scaled(56, 56, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                img_lbl.setPixmap(pix)
                img_lbl.setStyleSheet("border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px; background: rgba(0,0,0,0.3); padding: 2px;")
                info_row.addWidget(img_lbl)

        # Name & Subtitle
        name_vbox = QVBoxLayout()
        name_vbox.setSpacing(0)
        
        display_name = data_manager.get_localized_name(item_data, lang_code)
        name_lbl = QLabel(display_name.upper())
        if rarity in ["Legendary", "Epic"]:
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(15); shadow.setXOffset(0); shadow.setYOffset(0)
            shadow.setColor(QColor(rarity_color).lighter(120))
            name_lbl.setGraphicsEffect(shadow)
        name_lbl.setStyleSheet(f"color: {rarity_color}; font-size: {font_size+4}pt; font-weight: 900; letter-spacing: 0.5px;")
        name_lbl.setWordWrap(True)
        name_vbox.addWidget(name_lbl)
        
        # Metadata Layout (Rarity | Stash ... Price)
        meta_row = QHBoxLayout()
        meta_row.setSpacing(8)

        meta_str = f"{rarity.upper()}"
        if stash_count > 0: meta_str += f"  |  STASH: {stash_count}"
        meta_lbl = QLabel(meta_str)
        meta_lbl.setStyleSheet(f"color: rgba(255, 255, 255, 0.4); font-size: 8pt; font-weight: bold; letter-spacing: 1px;")
        meta_row.addWidget(meta_lbl)
        
        meta_row.addStretch()

        # FIXED PRICE DISPLAY (Right aligned)
        val = item_data.get('value', 0)
        if val > 0:
            price_cnt = QWidget()
            p_lay = QHBoxLayout(price_cnt); p_lay.setContentsMargins(0,0,0,0); p_lay.setSpacing(4)
            
            p_icon = QLabel()
            if Constants.COIN_ICON_PATH and os.path.exists(Constants.COIN_ICON_PATH):
                 p_icon.setPixmap(QPixmap(Constants.COIN_ICON_PATH).scaled(14, 14, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            
            p_txt = QLabel(f"{int(val):,}")
            p_txt.setStyleSheet(f"color: #E5C07B; font-size: 10pt; font-weight: bold; letter-spacing: 1px;")
            
            p_lay.addWidget(p_icon)
            p_lay.addWidget(p_txt)
            meta_row.addWidget(price_cnt)

        name_vbox.addLayout(meta_row)
        info_row.addLayout(name_vbox, 1)

        # Track Button (Right Aligned in Name Row - Float Top Right)
        # Note: We put track button in a separate vbox on the right of info_row
        btn_track = QPushButton("★" if is_tracked else "☆")
        btn_track.setFixedSize(24, 24)
        btn_track.setCursor(Qt.CursorShape.PointingHandCursor)
        track_color = "#FFD700" if is_tracked else "rgba(255, 255, 255, 0.3)"
        btn_track.setStyleSheet(f"QPushButton {{ background: transparent; color: {track_color}; font-size: 15pt; border: none; }} QPushButton:hover {{ color: #FFD700; }}")
        if toggle_track_callback:
            btn_track.clicked.connect(toggle_track_callback)
        
        right_vbox = QVBoxLayout()
        right_vbox.addWidget(btn_track)
        right_vbox.addStretch()
        info_row.addLayout(right_vbox)

        container_layout.addLayout(info_row)

        OverlayRenderer._add_separator(container_layout)

        # 3. Sections
        section_order = user_settings.get('ItemOverlay', 'section_order', fallback="price,notes,crafting,hideout,project,recycle,salvage,recommendation").split(',')
        has_previous_section = True 

        # Config mapping for visibility
        SECTION_CONFIG_MAP = {
            'storage': 'show_storage_info',
            'trader': 'show_trader_info',
            'notes': 'show_notes',
            'crafting': 'show_crafting_info',
            'hideout': 'show_hideout_reqs',
            'project': 'show_project_reqs',
            'recycle': 'show_recycles_into',
            'salvage': 'show_salvages_into',
            'recommendation': 'show_recommendation'
        }

        for section_id in section_order:
            section_added = False
            
            # Check visibility
            cfg_key = SECTION_CONFIG_MAP.get(section_id)
            if cfg_key and not user_settings.getboolean('ItemOverlay', cfg_key, fallback=True):
                continue
            
            if section_id == "price":
                # Removed (Moved to header)
                pass
            
            elif section_id == "notes":
                item_tags = data_manager.get_item_tags(item_data.get('id', ''))
                if item_tags:
                    tags_str = ", ".join(item_tags)
                    OverlayRenderer._add_glass_section(container_layout, None, tags_str, "#61AFEF", font_size-1, is_italic=True)
                    section_added = True
            
            elif section_id == "hideout" and hideout_reqs:
                OverlayRenderer._add_requirement_section(container_layout, "HIDEOUT REQUIREMENTS", Constants.HIDEOUT_ICON_PATH, hideout_reqs, font_size)
                section_added = True
                
            elif section_id == "project" and project_reqs:
                OverlayRenderer._add_requirement_section(container_layout, "PROJECT REQUESTS", Constants.PROJECT_ICON_PATH, project_reqs, font_size)
                section_added = True
            
            elif section_id == "recycle" and item_data.get('recyclesInto'):
                recycles = item_data['recyclesInto']
                content_widgets = []
                if isinstance(recycles, dict):
                    for iid, qty in recycles.items():
                        iname = data_manager.get_localized_name(iid, lang_code)
                        # BIG CARD LOGIC
                        # Using #4CBF87 (Arc Green-ish) for recycle accent if we want specific, or keep #ABB2BF
                        # User said "keep our current color". Current title color is #ABB2BF.
                        # Let's bump it slightly to #61AFEF (Blue) or #98C379 (Green) for better visibility?
                        # Actually, let's Stick to the requested "current color" but maybe use the item rarity? 
                        # Or just the section color passed in.
                        card_w = OverlayRenderer._create_item_card(iid, iname, qty, font_size, data_manager, "#61AFEF") 
                        content_widgets.append(card_w)
                
                if content_widgets:
                    OverlayRenderer._add_glass_section(container_layout, Constants.RECYCLE_ICON_PATH, "RECYCLES INTO", "#ABB2BF", font_size-1, custom_widgets=content_widgets)
                    section_added = True

            elif section_id == "salvage" and item_data.get('salvagesInto'):
                salvages = item_data['salvagesInto']
                content_widgets = []
                if isinstance(salvages, dict):
                    for iid, qty in salvages.items():
                        iname = data_manager.get_localized_name(iid, lang_code)
                        # Reuse Item Card Logic
                        # accent_color="#E06C75" (Red/Orangeish for salvage?) or "#D19A66" (Orange)
                        # Let's use a distinct color, maybe Orange for Salvage vs Blue for Recycle
                        card_w = OverlayRenderer._create_item_card(iid, iname, qty, font_size, data_manager, "#D19A66") 
                        content_widgets.append(card_w)
                
                if content_widgets:
                    OverlayRenderer._add_glass_section(container_layout, Constants.SALVAGE_ICON_PATH, "SALVAGES INTO", "#D19A66", font_size-1, custom_widgets=content_widgets)
                    section_added = True

            elif section_id == "quest" and quest_reqs:
                OverlayRenderer._add_requirement_section(container_layout, "QUEST REQUIREMENTS", Constants.QUEST_ICON_PATH, quest_reqs, font_size, is_quest=True)
                section_added = True

            elif section_id == "recommendation":
                rec = item_data.get('recommendation', '').upper()
                if rec:
                    color = "#E06C75" if 'SELL' in rec else ("#98C379" if 'KEEP' in rec else "#E5C07B")
                    OverlayRenderer._add_glass_section(container_layout, None, f"DECISION: {rec}", color, font_size, bold_title=True)
                    section_added = True
                    
            if section_added:
                OverlayRenderer._add_separator(container_layout)

    @staticmethod
    def _add_separator(layout):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Plain)
        line.setStyleSheet("background-color: rgba(255, 255, 255, 0.5); max-height: 1px; margin: 2px 0px;")
        layout.addWidget(line)

    @staticmethod
    def _create_item_card(item_id, name, qty, font_size, data_manager, accent_color="#ABB2BF"):
        """Creates a styled card with big icon and left accent bar."""
        container = QFrame()
        container.setStyleSheet(f"background-color: transparent;")
        # Remove border-radius since no background
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 12, 0) # No left margin to let accent bar flush
        layout.setSpacing(10)
        
        # Left Accent Bar
        bar = QFrame()
        bar.setFixedWidth(4)
        bar.setStyleSheet(f"background-color: {accent_color}; border-top-left-radius: 6px; border-bottom-left-radius: 6px;")
        layout.addWidget(bar)
        
        # Icon
        icon_path = os.path.join(Constants.DATA_DIR, "images", "items", f"{item_id}.png")
        if not os.path.exists(icon_path):
             item = data_manager.id_to_item_map.get(item_id)
             if item and item.get('imageFilename'):
                 icon_path = os.path.join(Constants.DATA_DIR, "images", "items", item.get('imageFilename'))

        icon_lbl = QLabel()
        icon_lbl.setFixedSize(32, 32) # Big Icon
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path).scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon_lbl.setPixmap(pix)
        else:
            icon_lbl.setText("?")
            icon_lbl.setStyleSheet("color: #555; font-weight: bold;")
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
        layout.addWidget(icon_lbl)
        
        # Name
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(f"color: #E0E6ED; font-weight: bold; font-size: {font_size}pt;")
        layout.addWidget(name_lbl)
        
        layout.addStretch()
        
        # Quantity
        qty_lbl = QLabel(f"×{qty}")
        qty_lbl.setStyleSheet(f"color: {accent_color}; font-weight: bold; font-size: {font_size}pt;")
        layout.addWidget(qty_lbl)
        
        return container

    @staticmethod
    def _add_glass_section(parent_layout, icon_path, title, title_color, font_size, lines=None, custom_widgets=None, is_italic=False, bold_title=False):
        frame = QFrame()
        frame.setStyleSheet("background: transparent; border: none; margin-top: 2px;")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        
        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        
        if icon_path and os.path.exists(icon_path):
            ic = QLabel()
            ic.setPixmap(QPixmap(icon_path).scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            title_row.addWidget(ic)
            
        title_lbl = QLabel(title)
        bold_style = "font-weight: bold;" if bold_title else ""
        italic_style = "font-style: italic;" if is_italic else ""
        title_lbl.setStyleSheet(f"color: {title_color}; font-size: {font_size}pt; {bold_style} {italic_style}")
        title_row.addWidget(title_lbl)
        title_row.addStretch()
        layout.addLayout(title_row)
        
        if lines:
            for line in lines:
                lbl = QLabel(line)
                lbl.setStyleSheet(f"color: #ABB2BF; font-size: {font_size-1}pt; margin-left: 24px;")
                layout.addWidget(lbl)
        
        if custom_widgets:
            for w in custom_widgets:
                layout.addWidget(w)
                
        parent_layout.addWidget(frame)

    @staticmethod
    def _add_requirement_section(parent_layout, header_text, icon_path, req_list, font_size, is_quest=False):
        frame = QFrame()
        frame.setStyleSheet("background: transparent; border: none; margin-top: 2px;")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        
        h_row = QHBoxLayout()
        if icon_path and os.path.exists(icon_path):
            ic = QLabel(); ic.setPixmap(QPixmap(icon_path).scaled(18, 18))
            h_row.addWidget(ic)
        h_lbl = QLabel(header_text)
        h_lbl.setStyleSheet("color: rgba(255, 255, 255, 0.4); font-weight: bold; font-size: 8pt; letter-spacing: 1px;")
        h_row.addWidget(h_lbl); h_row.addStretch()
        layout.addLayout(h_row)
        
        for req in req_list:
            if is_quest:
                txt, active, done = req[0], req[1], req[2]
                color = "#5C6370" if done else ("#FFD700" if active else "#ABB2BF")
                prefix = "V " if done else ("- " if active else "[ ] ")
            else:
                txt, rtype, done = req[0], req[1], req[2]
                color = "#5C6370" if done else ("#98C379" if rtype == 'next' else "#D19A66")
                prefix = "X " if done else "[ ] "
                
            lbl = QLabel(f"{prefix}{txt}")
            lbl.setStyleSheet(f"color: {color}; font-size: {font_size}pt; margin-left: 24px;")
            if done: lbl.setStyleSheet(lbl.styleSheet() + "text-decoration: line-through;")
            layout.addWidget(lbl)
            
        parent_layout.addWidget(frame)


class BaseOverlay(QWidget):
    def __init__(self, duration_ms, min_width=None, max_width=None, opacity=0.98, enable_distance_close=True, close_threshold=350):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowOpacity(0) # Start at 0 for fade-in

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0) # ZERO MARGIN

        self.container = QFrame()
        self.container.setObjectName("OverlayFrame")

        # PREMIUM GLASSMORPHISM STYLE
        self.container.setStyleSheet(f"""
            #OverlayFrame {{
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, 
                                                  stop:0 rgba(35, 39, 47, 240), 
                                                  stop:1 rgba(22, 26, 33, 250));
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-top: 3px solid #555;
                border-radius: 8px;
            }}
            QLabel {{ color: #E0E6ED; }}
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(6)
        shadow.setColor(QColor(0, 0, 0, 180))
        self.container.setGraphicsEffect(shadow)

        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(15, 4, 15, 12)
        self.container_layout.setSpacing(6)

        self.main_layout.addWidget(self.container)

        if min_width: self.container.setMinimumWidth(min_width)
        if max_width: self.container.setMaximumWidth(max_width)

        self.duration_timer = QTimer(self)
        self.duration_timer.setSingleShot(True)
        self.duration_timer.timeout.connect(self.close)
        self.target_duration = duration_ms

        if enable_distance_close:
            self.mouse_monitor_timer = QTimer(self)
            self.mouse_monitor_timer.timeout.connect(self.check_mouse_distance)
            self.mouse_monitor_timer.start(100)

        self.target_opacity = opacity
        self.close_threshold = close_threshold

    def show_animated(self, start_pos, end_pos):
        self.move(start_pos)
        self.show()
        
        # Opacity Animation
        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(400)
        self.fade_anim.setStartValue(0)
        self.fade_anim.setEndValue(self.target_opacity)
        self.fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Position Animation
        self.pos_anim = QPropertyAnimation(self, b"pos")
        self.pos_anim.setDuration(500)
        self.pos_anim.setStartValue(start_pos)
        self.pos_anim.setEndValue(end_pos)
        self.pos_anim.setEasingCurve(QEasingCurve.Type.OutExpo)
        
        self.fade_anim.start()
        self.pos_anim.start()
        self.duration_timer.start(int(self.target_duration))

    def check_mouse_distance(self):
        mouse_pos = QCursor.pos()
        rect = self.frameGeometry()

        if mouse_pos.x() < rect.left(): dx = rect.left() - mouse_pos.x()
        elif mouse_pos.x() > rect.right(): dx = mouse_pos.x() - rect.right()
        else: dx = 0

        if mouse_pos.y() < rect.top(): dy = rect.top() - mouse_pos.y()
        elif mouse_pos.y() > rect.bottom(): dy = mouse_pos.y() - rect.bottom()
        else: dy = 0

        distance = math.sqrt(dx*dx + dy*dy)
        if distance > self.close_threshold: self.close()

    def set_border_color(self, color_hex):
        self.container.setStyleSheet(f"""
            #OverlayFrame {{
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, 
                                                  stop:0 rgba(35, 39, 47, 240), 
                                                  stop:1 rgba(22, 26, 33, 250));
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-top: 3px solid {color_hex};
                border-radius: 8px;
            }}
            QLabel {{ color: #E0E6ED; }}
        """)

    def show_at_cursor(self):
        cursor_pos = QCursor.pos()
        self.move(cursor_pos.x() + 20, cursor_pos.y() + 20)
        self.show()

    def show_at_position(self, x, y):
        end_pos = QPoint(x, y)
        start_pos = QPoint(x, y + 30)
        self.show_animated(start_pos, end_pos)

class ItemOverlay(BaseOverlay):
    def __init__(self, item_data, user_settings, blueprint_required, hideout_reqs, project_reqs, trade_info, data_manager, user_note="", lang_code="en", stash_count=0, is_collected_blueprint=False, is_active_quest_item=False, quest_reqs=None):
        # Initial config read for constructor args
        duration = user_settings.getfloat('ItemOverlay', 'duration_seconds', fallback=3.0) * 1000
        font_size = user_settings.getint('ItemOverlay', 'font_size', fallback=12)
        min_w = max(340, font_size * 25)
        max_w = max(450, font_size * 35)

        offset_x = user_settings.getint('ItemOverlay', 'offset_x', fallback=0)
        offset_y = user_settings.getint('ItemOverlay', 'offset_y', fallback=0)
        anchor_mode = user_settings.get('ItemOverlay', 'anchor_mode', fallback="Mouse")
        opacity_val = user_settings.getint('ItemOverlay', 'opacity', fallback=98) / 100.0

        # Auto-disable leash if custom offsets are used OR if anchor is not Mouse
        enable_leash = (offset_x == 0 and offset_y == 0 and anchor_mode == "Mouse")

        super().__init__(duration, min_width=min_w, max_width=max_w, opacity=opacity_val, enable_distance_close=enable_leash)

        # Storage
        self.item_data = item_data
        self.user_settings = user_settings
        self.blueprint_required = blueprint_required
        self.hideout_reqs = hideout_reqs
        self.project_reqs = project_reqs
        self.trade_info = trade_info
        self.data_manager = data_manager
        self.user_note = user_note
        self.lang_code = lang_code
        self.stash_count = stash_count
        self.is_collected_blueprint = is_collected_blueprint
        self.is_active_quest_item = is_active_quest_item
        self.quest_reqs = quest_reqs or []

        self.refresh_ui()

    def toggle_track(self):
        item_id = self.item_data.get('id')
        if not item_id: return
        self.data_manager.toggle_item_track(item_id)
        self.refresh_ui()

    def refresh_ui(self):
        # 1. Clear existing layout
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    si = item.layout().takeAt(0)
                    if si.widget(): si.widget().deleteLater()

        # 2. Re-read settings
        font_size = self.user_settings.getint('ItemOverlay', 'font_size', fallback=12)
        min_w = max(340, font_size * 25)
        max_w = max(450, font_size * 35)
        self.container.setMinimumWidth(min_w)
        self.container.setMaximumWidth(max_w)

        # 3. Apply Border Color
        rarity = self.item_data.get('rarity', 'Common')
        rarity_color = Constants.RARITY_COLORS.get(rarity, "#FFFFFF")
        self.set_border_color(rarity_color)
        
        # 4. Build Context
        data_context = {
            'item_data': self.item_data,
            'hideout_reqs': self.hideout_reqs,
            'project_reqs': self.project_reqs,
            'quest_reqs': self.quest_reqs,
            'stash_count': self.stash_count,
            'is_tracked': self.data_manager.is_item_tracked(self.item_data.get('id')),
            'toggle_track_callback': self.toggle_track
        }

        # 5. Delegate to Renderer
        OverlayRenderer.populate(self.container_layout, data_context, self.user_settings, self.data_manager, self.lang_code)

        self.adjustSize()

    def show_smart(self, x=None, y=None):
        from PyQt6.QtGui import QGuiApplication

        cursor_pos = QCursor.pos()
        target_screen = QGuiApplication.screenAt(cursor_pos)
        if not target_screen:
            target_screen = QGuiApplication.primaryScreen()

        screen_geom = target_screen.geometry()

        overlay_height, overlay_width = self.size().height(), self.size().width()

        offset_x = self.user_settings.getint('ItemOverlay', 'offset_x', fallback=0)
        offset_y = self.user_settings.getint('ItemOverlay', 'offset_y', fallback=0)
        anchor_mode = self.user_settings.get('ItemOverlay', 'anchor_mode', fallback="Mouse")

        # Determine Base Position
        if anchor_mode == "Mouse":
             # Original behavior
             pos_x, pos_y = cursor_pos.x() + 20 + offset_x, cursor_pos.y() + 20 + offset_y
        else:
            # Fixed Anchors
            # Coordinates relative to the SCREEN (Top Left is 0,0 of that screen)
            sx, sy, sw, sh = screen_geom.x(), screen_geom.y(), screen_geom.width(), screen_geom.height()

            # Base aligns
            if "Top" in anchor_mode: base_y = sy + 20
            elif "Bottom" in anchor_mode: base_y = sy + sh - overlay_height - 20
            else: base_y = sy + (sh - overlay_height) // 2 # Center

            if "Left" in anchor_mode: base_x = sx + 20
            elif "Right" in anchor_mode: base_x = sx + sw - overlay_width - 20
            else: base_x = sx + (sw - overlay_width) // 2 # Center

            # Apply offsets
            pos_x, pos_y = base_x + offset_x, base_y + offset_y

        # Bounds Checking (Keep fully on screen if possible)
        if pos_x + overlay_width > screen_geom.right():
             pos_x = screen_geom.right() - overlay_width
        if pos_y + overlay_height > screen_geom.bottom():
             pos_y = screen_geom.bottom() - overlay_height
        if pos_x < screen_geom.left():
             pos_x = screen_geom.left()
        if pos_y < screen_geom.top():
             pos_y = screen_geom.top()

        # ANIMATION: Calculate start/end positions
        end_pos = QPoint(int(pos_x), int(pos_y))
        
        # Determine start position based on anchor
        start_pos = QPoint(end_pos.x(), end_pos.y())
        if "Left" in anchor_mode: start_pos.setX(end_pos.x() - 50)
        elif "Right" in anchor_mode: start_pos.setX(end_pos.x() + 50)
        elif "Top" in anchor_mode: start_pos.setY(end_pos.y() - 50)
        elif "Bottom" in anchor_mode: start_pos.setY(end_pos.y() + 50)
        else: start_pos.setY(end_pos.y() + 30) # Default slide up

        self.show_animated(start_pos, end_pos)

class QuestOverlayUI:
    @staticmethod
    def create_window(tracked_quests, user_settings, data_manager=None, lang_code="en"):
        duration = user_settings.getfloat('QuestOverlay', 'duration_seconds', fallback=5.0) * 1000
        width = user_settings.getint('QuestOverlay', 'width', fallback=350)
        opacity = user_settings.getint('QuestOverlay', 'opacity', fallback=95) / 100.0
        font_size = user_settings.getint('QuestOverlay', 'font_size', fallback=12)

        overlay = BaseOverlay(duration, min_width=width, max_width=width, opacity=opacity, enable_distance_close=False)
        overlay.set_border_color(Constants.RARITY_COLORS.get('Rare', '#4A5469'))

        overlay.add_label("Tracked Quests", font_size + 2, True, Constants.RARITY_COLORS['Rare'])
        overlay.add_separator()

        if not tracked_quests:
            overlay.add_label("No quests tracked.", font_size)
        else:
            active_id = data_manager.get_active_quest_id() if data_manager else None
            for i, quest in enumerate(tracked_quests):
                if i > 0: overlay.add_separator()

                q_id = quest.get('id')
                is_active = (q_id == active_id)
                q_name = quest.get('name', 'Unknown')
                if is_active: q_name = f"★ {q_name} (ACTIVE)"
                
                header_color = "#FFD700" if is_active else Constants.QUEST_HEADER_COLOR
                overlay.add_label(q_name, font_size, True, header_color)

                if data_manager:
                    map_names = data_manager.get_quest_map_names(quest, lang_code=lang_code)
                    if map_names:
                        map_str = ", ".join(map_names)
                        overlay.add_label(f"Map: {map_str}", font_size - 1, False, "#61AFEF")

                for objective in quest.get('objectives', []):
                    is_completed = objective in quest.get('objectives_completed', [])
                    color = "#5C6370" if is_completed else ("#FFD700" if is_active else Constants.QUEST_OBJECTIVE_COLOR)
                    txt = f"■ {objective}"
                    lbl = QLabel(txt); lbl.setWordWrap(True); lbl.setFont(QFont("Segoe UI", font_size))
                    if is_completed: lbl.setText(f"<span style='text-decoration: line-through;'>{txt}</span>")
                    lbl.setStyleSheet(f"color: {color}; margin-left: 10px; font-size: {font_size}pt;")
                    if is_active and not is_completed: lbl.setStyleSheet(lbl.styleSheet() + "font-weight: bold;")
                    overlay.container_layout.addWidget(lbl)

        overlay.adjustSize()
        screen = overlay.screen().geometry(); h = overlay.size().height(); y = (screen.height() - h) // 2
        overlay.show_at_position(20, y)
        return overlay