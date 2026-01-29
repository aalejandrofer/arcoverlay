from __future__ import annotations
import argparse, os, sys, traceback
import ctypes
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

from pynput import keyboard as pynput_keyboard, mouse as pynput_mouse
from PyQt6.QtWidgets import (QApplication, QSystemTrayIcon, QMenu,
                             QMessageBox, QProgressDialog)
from PyQt6.QtGui import QIcon, QAction, QDesktopServices
from PyQt6.QtCore import QObject, pyqtSignal, QThread, Qt, QUrl, QSharedMemory

from modules.constants import Constants
from modules.overlay_ui import ItemOverlay, QuestOverlayUI
from modules.progress_hub_window import ProgressHubWindow
from modules.data_manager import ItemDatabase, DataManager
from modules.scanner import ItemScanner
from modules.config_manager import ConfigManager

APP_VERSION = "1.4.0"

@dataclass
class Config:
    tesseract_path: Optional[str] = None; once: bool = False; debug: bool = False
    @classmethod
    def from_args(cls, args: argparse.Namespace) -> Config:
        return cls(tesseract_path=args.tesseract, once=args.once, debug=args.debug)

class HotkeyListener(QObject):
    item_check_triggered = pyqtSignal()
    quest_log_triggered = pyqtSignal()
    hub_triggered = pyqtSignal()

    def __init__(self, item_hotkey, quest_hotkey, hub_hotkey):
        super().__init__()
        self.raw_hotkeys = {
            'item': item_hotkey,
            'quest': quest_hotkey,
            'hub': hub_hotkey
        }
        self.kb_hotkey_map = {}
        self.m_hotkey_map = {}
        
        for action, hk in self.raw_hotkeys.items():
            if not hk: continue
            if hk.startswith("mouse:"):
                try:
                    btn_num = int(hk.split(":")[-1])
                    self.m_hotkey_map[btn_num] = action
                except: pass
            else:
                pynput_hk = self._convert_to_pynput_format(hk)
                if action == 'item': self.kb_hotkey_map[pynput_hk] = self._on_item_check
                elif action == 'quest': self.kb_hotkey_map[pynput_hk] = self._on_quest_log
                elif action == 'hub': self.kb_hotkey_map[pynput_hk] = self._on_hub

        self.kb_listener = None
        self.m_listener = None

    def _convert_to_pynput_format(self, hotkey_str):
        parts = hotkey_str.lower().replace(" ", "").split('+')
        formatted_parts = []
        modifiers = {'ctrl', 'shift', 'alt', 'cmd', 'enter', 'tab', 'esc', 'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12', 'insert', 'delete', 'home', 'end', 'pageup', 'pagedown'}
        for part in parts:
            if part in modifiers: formatted_parts.append(f"<{part}>")
            else: formatted_parts.append(part)
        return '+'.join(formatted_parts)

    def run(self):
        print(f"Hotkey listener started. KB: {list(self.kb_hotkey_map.keys())}, Mouse: {list(self.m_hotkey_map.keys())}")
        
        try:
            self.kb_listener = pynput_keyboard.GlobalHotKeys(self.kb_hotkey_map)
            self.kb_listener.start()
            
            if self.m_hotkey_map:
                self.m_listener = pynput_mouse.Listener(on_click=self._on_mouse_click)
                self.m_listener.start()
            
            self.kb_listener.join()
        except Exception as e: 
            print(f"Error in Hotkey Listener: {e}")

    def stop(self):
        if self.kb_listener: self.kb_listener.stop()
        if self.m_listener: self.m_listener.stop()

    def _on_mouse_click(self, x, y, button, pressed):
        if pressed:
            btn_val = None
            if button == pynput_mouse.Button.middle: btn_val = 3
            elif button == pynput_mouse.Button.x1: btn_val = 4
            elif button == pynput_mouse.Button.x2: btn_val = 5
            
            if btn_val in self.m_hotkey_map:
                action = self.m_hotkey_map[btn_val]
                if action == 'item': self._on_item_check()
                elif action == 'quest': self._on_quest_log()
                elif action == 'hub': self._on_hub()

    def _on_item_check(self): self.item_check_triggered.emit()
    def _on_quest_log(self): self.quest_log_triggered.emit()
    def _on_hub(self): self.hub_triggered.emit()

class ScanWorker(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, scanner: ItemScanner, from_tray: bool):
        super().__init__()
        self.scanner = scanner
        self.from_tray = from_tray

    def run(self):
        try:
            result = self.scanner.scan_screen(full_screen=self.from_tray)
            self.finished.emit(result)
        except Exception as e:
            traceback.print_exc()
            self.error.emit(str(e))
            self.finished.emit(None)

class ArcOverlayApp(QObject):

    def __init__(self, config: Config):
        super().__init__()
        self.app = QApplication.instance()
        self.app.setQuitOnLastWindowClosed(False)
        self.app.aboutToQuit.connect(self.cleanup_threads)
        self.cmd_config = config

        self.config_manager = ConfigManager()

        self.db = ItemDatabase()
        self.data_manager = DataManager(self.db.items)
        self.overlays = []
        self.scan_thread = None

        self.scanner = ItemScanner(self.cmd_config, self.data_manager)

        self.reload_settings(is_initial_load=True)

        self.progress_hub = ProgressHubWindow(
            self.data_manager,
            self.config_manager,
            self.reload_settings,
            APP_VERSION,
            lang_code=self.json_lang_code
        )

        self.progress_hub.settings_tab.hotkeys_updated.connect(self.restart_hotkeys)
        self.progress_hub.show()

        self.tray = QSystemTrayIcon()
        self.tray.setIcon(QIcon(Constants.ICON_FILE if os.path.exists(Constants.ICON_FILE) else self.app.style().standardIcon(self.app.style().StandardPixmap.SP_ComputerIcon)))
        self._build_tray_menu()
        self.tray.activated.connect(self.on_tray_icon_activated)
        self.tray.show()

        self.hotkey_thread = QThread()
        self.start_background_services()

    def start_background_services(self):
        """Starts background services."""
        self._start_hotkey_service()

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.restore_app()

    def _build_tray_menu(self):
        menu = QMenu()
        settings_action = QAction("Settings", self); settings_action.triggered.connect(self.show_settings_tab)
        hub_action = QAction("Progress Hub", self); hub_action.triggered.connect(self.restore_app)
        exit_action = QAction("Exit", self); exit_action.triggered.connect(self.quit_app)
        menu.addAction(settings_action); menu.addAction(hub_action)
        if self.cmd_config.debug:
            menu.addSeparator()
            test_ocr_action = QAction("Test Item Check (No Hotkey)", self)
            test_ocr_action.triggered.connect(lambda: self.process_item_check(from_tray=True))
            menu.addAction(test_ocr_action)
        menu.addSeparator(); menu.addAction(exit_action)
        self.tray.setContextMenu(menu)

    def _start_hotkey_service(self):
        hotkey_item = self.config_manager.get_item_hotkey()
        hotkey_quest = self.config_manager.get_quest_hotkey()
        hotkey_hub = self.config_manager.get_hub_hotkey()
        self.hotkey_worker = HotkeyListener(hotkey_item, hotkey_quest, hotkey_hub)
        self.hotkey_worker.moveToThread(self.hotkey_thread)
        self.hotkey_worker.item_check_triggered.connect(self.process_item_check)
        self.hotkey_worker.quest_log_triggered.connect(self.process_quest_log)
        self.hotkey_worker.hub_triggered.connect(self.restore_app)
        self.hotkey_thread.started.connect(self.hotkey_worker.run)
        self.hotkey_thread.start()

    def restart_hotkeys(self):
        print("Restarting hotkey service...")
        if hasattr(self, 'hotkey_worker') and self.hotkey_worker:
            try:
                self.hotkey_worker.stop()
            except: pass

        if hasattr(self, 'hotkey_thread') and self.hotkey_thread:
            if self.hotkey_thread.isRunning():
                self.hotkey_thread.quit()
                if not self.hotkey_thread.wait(2000): 
                    print("[WARNING] Hotkey thread took too long to stop, terminating...")
                    self.hotkey_thread.terminate()
                    self.hotkey_thread.wait()

        self.hotkey_thread = QThread()
        self._start_hotkey_service()
        print("Hotkey service restarted.")

    def show_settings_tab(self):
        self.progress_hub.show()
        self.progress_hub.tabs.setCurrentIndex(4)

    def reload_settings(self, is_initial_load=False):
        self.config_manager.load()
        try:
            color_str = self.config_manager.get_ocr_color()
            self.target_color = tuple(map(int, color_str.split(',')))
        except ValueError: self.target_color = (249, 238, 223)

        self.ocr_lang_code = self.config_manager.get_language()
        self.json_lang_code = 'en'
        for _, (json_c, tess_c) in Constants.LANGUAGES.items():
            if tess_c == self.ocr_lang_code:
                self.json_lang_code = json_c; break

        full_screen = self.config_manager.get_full_screen_scan()
        save_debug = self.config_manager.get_save_debug_images()

        self.scanner.update_settings(self.target_color, self.ocr_lang_code, self.json_lang_code, full_screen_mode=full_screen, save_debug_images=save_debug)

        for overlay in self.overlays:
            if hasattr(overlay, 'refresh_ui'):
                overlay.refresh_ui()

        if is_initial_load: print(f"[INFO] Settings Loaded. Lang: {self.ocr_lang_code}")
        else: print("Settings reloaded.")

    def process_item_check(self, from_tray=False):
        for overlay in self.overlays:
            overlay.close()
        self.overlays.clear()

        if self.scan_thread:
            try:
                if self.scan_thread.isRunning():
                    print("[INFO] Scan already in progress.")
                    return
            except RuntimeError:
                self.scan_thread = None

        self.scan_thread = QThread()
        self.scan_worker = ScanWorker(self.scanner, from_tray)
        self.scan_worker.moveToThread(self.scan_thread)

        self.scan_thread.started.connect(self.scan_worker.run)
        self.scan_worker.finished.connect(self.handle_scan_result)
        self.scan_worker.finished.connect(self.scan_thread.quit)
        self.scan_worker.finished.connect(self.scan_worker.deleteLater)
        self.scan_thread.finished.connect(self.scan_thread.deleteLater)

        self.scan_thread.start()

    def handle_scan_result(self, scan_result):
        if scan_result:
            self.display_item_overlay(scan_result)

    def process_quest_log(self):
        try:
            tracked = self.data_manager.get_filtered_quests(tracked_only=True, lang_code=self.json_lang_code)
            self.display_quest_overlay(tracked)
        except Exception as e: print(f"Error: {e}")

    def display_item_overlay(self, data):
        from modules.overlay_ui import ItemOverlay
        ov = ItemOverlay(
            data['item'], 
            self.config_manager.parser, 
            data['blueprint'], 
            data['hideout'], 
            data['project'], 
            data['trade'], 
            self.data_manager, 
            data['note'], 
            lang_code=self.json_lang_code, 
            stash_count=data['stash_count'], 
            is_collected_blueprint=data['is_collected_bp'],
            is_active_quest_item=data.get('is_active_quest_item', False),
            quest_reqs=data.get('quests', [])
        )
        ov.show_smart()
        self.overlays.append(ov)

    def display_quest_overlay(self, tracked):
        ov = QuestOverlayUI.create_window(tracked, self.config_manager.parser, self.data_manager, lang_code=self.json_lang_code)
        self.overlays.append(ov)

    def ensure_data_exists(self):
        # We assume data exists now as update logic is removed
        return True

    def cleanup_threads(self):
            if hasattr(self, 'hotkey_worker') and self.hotkey_worker:
                try:
                    self.hotkey_worker.stop()
                except RuntimeError: pass

            if hasattr(self, 'hotkey_thread') and self.hotkey_thread:
                try:
                    self.hotkey_thread.quit()
                    self.hotkey_thread.wait()
                except RuntimeError: pass

            if hasattr(self, 'scan_thread') and self.scan_thread:
                try:
                    if self.scan_thread.isRunning():
                        self.scan_thread.quit()
                        self.scan_thread.wait()
                except RuntimeError:
                    pass

            if hasattr(self, 'progress_hub'):
                try:
                    self.progress_hub.cleanup()
                except RuntimeError: pass

    def quit_app(self): self.app.quit()
    def run(self): sys.exit(self.app.exec())

    def restore_app(self):
        self.progress_hub.show()
        if self.progress_hub.windowState() & Qt.WindowState.WindowMinimized:
            self.progress_hub.setWindowState(self.progress_hub.windowState() & ~Qt.WindowState.WindowMinimized)
        self.progress_hub.setWindowFlags(self.progress_hub.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.progress_hub.show()
        self.progress_hub.setWindowFlags(self.progress_hub.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
        self.progress_hub.show()
        self.progress_hub.activateWindow()
        self.progress_hub.raise_()

from modules.ui_components import set_dark_title_bar, DarkTitleBarProxy

def main():
    def get_tesseract_path():
        if getattr(sys, 'frozen', False):
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
            qt_plugins_path = os.path.join(base_path, 'PyQt6', 'Qt6', 'plugins')
            if not os.path.exists(qt_plugins_path):
                 qt_plugins_path = os.path.join(base_path, 'PyQt6', 'plugins')
            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(qt_plugins_path, 'platforms')
            return os.path.join(base_path, 'Tesseract-OCR', 'tesseract.exe')
        local = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Tesseract-OCR', 'tesseract.exe')
        return local if os.path.exists(local) else None

    parser = argparse.ArgumentParser(); parser.add_argument('--tesseract', default=get_tesseract_path()); parser.add_argument('--once', action='store_true'); parser.add_argument('--debug', action='store_true')
    config = Config.from_args(parser.parse_args())

    if sys.platform == 'win32':
        try:
            myappid = f'joopzor.arcoverlay.client.{APP_VERSION}'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except (AttributeError, ImportError): pass

    try:
        app_instance = QApplication(sys.argv)
        app_instance.setStyleSheet(Constants.DARK_THEME_QSS)

        dark_proxy = DarkTitleBarProxy()
        app_instance.installEventFilter(dark_proxy)
        app_instance._dark_proxy = dark_proxy

        if os.path.exists(Constants.ICON_FILE): app_instance.setWindowIcon(QIcon(Constants.ICON_FILE))
        app = ArcOverlayApp(config); app.run()
    except Exception as e:
        try:
            log_dir = Constants.DATA_DIR if 'Constants' in globals() else os.getcwd()
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, "arcoverlay_crash.log")
            with open(log_path, "w") as f:
                f.write(f"Crash: {datetime.now()}\n")
                f.write(f"Version: {APP_VERSION}\n")
                f.write(f"OS: {sys.platform}\n")
                f.write("-" * 20 + "\n")
                f.write(traceback.format_exc())
            print(f"CRITICAL: Application crashed. Log saved to: {log_path}")
        except Exception as log_error:
            print(f"CRITICAL: Application crashed and could not even write log: {log_error}")
            print(traceback.format_exc())

        if not QApplication.instance():
            _ = QApplication(sys.argv)
        QMessageBox.critical(None, "Fatal Error", f"Arc Overlay has encountered a fatal error and must close.\n\nError: {e}\n\nA crash log has been saved."); 
        sys.exit(1)

if __name__ == '__main__': main()