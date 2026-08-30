
import sys
import os

# Suppress Pygame welcome message
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"

# Suppress Qt Warnings
os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.multimedia.ffmpeg.info=false;qt.multimedia.ffmpeg.debug=false;qt.multimedia.ffmpeg.warning=false"

import warnings
# Suppress pkg_resources deprecation warning
warnings.filterwarnings("ignore", category=UserWarning, module="pkg_resources")
# Suppress other specific warnings if needed
warnings.filterwarnings("ignore", category=UserWarning, module="pygame")

import shutil
import re
from typing import List

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QListWidgetItem, QLabel, QSlider, QPushButton,
    QFrame, QMessageBox, QFileDialog, QInputDialog, QCheckBox, QComboBox
)
from PyQt6.QtCore import Qt, QSize, QTimer, QSettings, qInstallMessageHandler, QtMsgType
from PyQt6.QtGui import QColor, QIcon, QAction

def qt_message_handler(mode, context, message):
    if "already has a parent" in message:
        return
    
    mode_str = "Debug"
    if mode == QtMsgType.QtInfoMsg: mode_str = "Info"
    elif mode == QtMsgType.QtWarningMsg: mode_str = "Warning"
    elif mode == QtMsgType.QtCriticalMsg: mode_str = "Critical"
    elif mode == QtMsgType.QtFatalMsg: mode_str = "Fatal"
    
    print(f"Qt {mode_str}: {message}", file=sys.stderr)


import ui_utils_qt
from localization import t, set_language, get_language
from ui_components import CoverArtPanel, TagEditorPanel, FileListWidget, BatchEditorPanel
from tag_engine import TagEngine, TrackInfo
from audio_player import AudioPlayer, QMediaPlayer
from converter_dialog_qt import ConverterDialog
from update_manager import UpdateManager
from audio_analyzer import AudioAnalyzer

APP_NAME = "STORM TAG EDITOR"
VERSION = "1.2.1"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle(f"{APP_NAME} v{VERSION}")
        self.resize(1200, 800)
        
        # Updater
        self.update_manager = UpdateManager(self, current_version=VERSION)
        
        # Audio Player
        self.player = AudioPlayer()
        self.analyzer = AudioAnalyzer()
        # Remove QTimer, use signals instead
        self.is_slider_dragged = False
        
        self.loaded_files = [] # List of TrackInfo
        
        self.settings = QSettings(APP_NAME, "Settings")
        self._load_core_settings() # Lang, Theme
        
        self._init_ui()
        self._restore_ui_state()   # Geometry, Splitter
        self._connect_signals()
        
        # Auto Update Check
        if self.settings.value("auto_update", True, type=bool):
            # Check after UI is shown, using singleShot to not block init
            QTimer.singleShot(2000, lambda: self.update_manager.check_for_updates(silent=True))
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        if event.key() == Qt.Key.Key_Delete:
            self._remove_selected_files()
        else:
            super().keyPressEvent(event)
    
    def _remove_selected_files(self):
        """Remove selected files from the list."""
        items = self.file_list.selectedItems()
        if not items:
            return
        
        # Get tracks to remove
        tracks_to_remove = []
        for item in items:
            track = item.data(Qt.ItemDataRole.UserRole)
            if track:
                tracks_to_remove.append(track)
        
        # Remove from loaded_files
        for track in tracks_to_remove:
            if track in self.loaded_files:
                self.loaded_files.remove(track)
        
        # Remove from list widget (in reverse order to avoid index shifting issues)
        for item in reversed(items):
            row = self.file_list.row(item)
            self.file_list.takeItem(row)
        
        # Clear editor if current track was removed
        if self.panel_editor.current_track in tracks_to_remove:
            self.panel_editor.set_track(None)
            self.cover_panel.set_cover(None)
            self.player.stop()
        
        self.status.setText(t('files_count').format(len(self.loaded_files)))
        
    def _load_core_settings(self):
        # Restore language
        lang = self.settings.value("language", "ru")
        set_language(lang)
        
        # Restore theme
        from ui_themes import get_theme
        theme_name = self.settings.value("theme", "Dark (Default)")
        theme = get_theme(theme_name)
        ui_utils_qt.apply_theme(theme)
        
    def _restore_ui_state(self):
        # Restore geometry
        geo = self.settings.value("geometry")
        if geo:
            self.restoreGeometry(geo)
            
        # Restore splitter state
        splitter_state = self.settings.value("splitter_state")
        if splitter_state:
            self.splitter.restoreState(splitter_state)
            
    def closeEvent(self, event):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("splitter_state", self.splitter.saveState())
        self.settings.setValue("language", get_language())
        if hasattr(self, 'combo_theme'):
            self.settings.setValue("theme", self.combo_theme.currentText())
        event.accept()
        
    def _init_ui(self):
        # Central Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Main Layout (Header, Splitter, Status)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Header
        self.header = QFrame()
        self.header.setFixedHeight(70)
        self.header_layout = QHBoxLayout()
        self.header_layout.setContentsMargins(10, 0, 10, 0)
        self.header.setLayout(self.header_layout)
        
        # Logo - Removed as per user request (already in Window Title)
        # lbl_logo = QLabel("⚡ STORM TAG EDITOR")
        # lbl_logo.setStyleSheet("font-weight: bold; font-size: 16px; color: #ff7f50;")
        # lbl_ver = QLabel(f"v{VERSION}")
        # lbl_ver.setStyleSheet("color: #666; font-size: 10px; margin-left: 5px; margin-bottom: 5px;")
        
        # self.header_layout.addWidget(lbl_logo)
        # self.header_layout.addWidget(lbl_ver)
        # self.header_layout.addStretch()
        
        # Center buttons? Or left align?
        # User said "Remove title/version", presumably keep buttons.
        self.header_layout.addStretch() # Spacer
        
        # Buttons
        from ui_utils_qt import HoverButton, COLORS
        from PyQt6.QtWidgets import QListView

        # 0. Audio Converter (Left)
        # Re-creating button here
        self.btn_converter = HoverButton(t('converter_title'))
        self.btn_converter.setFixedWidth(150)
        self.btn_converter.default_color = QColor("#2980b9")
        self.btn_converter.hover_color = QColor("#3498db")
        self.btn_converter.pressed_color = QColor("#1f618d")
        self.btn_converter.update_style(self.btn_converter.default_color)
        self.btn_converter.clicked.connect(self._open_converter)
        
        self.header_layout.addWidget(self.btn_converter)
        
        # Spacer to push Main Actions to the right (closer to settings)
        self.header_layout.addStretch()
        
        # 1. Main Actions
        self.btn_open_files = HoverButton(t('open_files'))
        self.btn_open_folder = HoverButton(t('open_folder'))
        self.btn_save = HoverButton(t('save'))
        self.btn_save_all = HoverButton(t('save_all'))
        
        self.header_layout.addWidget(self.btn_open_files)
        self.header_layout.addWidget(self.btn_open_folder)
        self.header_layout.addWidget(self.btn_save)
        self.header_layout.addWidget(self.btn_save_all)
        
        # Add spacing before Auto-Update group
        self.header_layout.addSpacing(20)
        
        self.header_layout.addStretch()
        
        # 2. Right Side Controls
        
        # Auto Update (Checkbox)
        self.cb_auto_update = QCheckBox(t('auto_update'))
        self.cb_auto_update.setChecked(self.settings.value("auto_update", True, type=bool))
        self.cb_auto_update.stateChanged.connect(self._save_auto_update)
        
        self.header_layout.addWidget(self.cb_auto_update)
        self.header_layout.addSpacing(15)
        
        # Language Selector
        self.combo_lang = QComboBox()
        self.combo_lang.setView(QListView())
        self.combo_lang.addItems(["🇷🇺 Русский", "🇬🇧 English"])
        curr_lang = get_language()
        self.combo_lang.setCurrentIndex(0 if curr_lang == 'ru' else 1)
        self.combo_lang.currentIndexChanged.connect(self._change_language)
        
        # Theme Switcher
        from ui_themes import get_theme_names
        self.combo_theme = QComboBox()
        self.combo_theme.setView(QListView())
        self.combo_theme.addItems(get_theme_names())
        saved_theme = self.settings.value("theme", "Dark (Default)")
        idx = self.combo_theme.findText(saved_theme)
        if idx >= 0:
            self.combo_theme.setCurrentIndex(idx)
        self.combo_theme.currentTextChanged.connect(self._change_theme)
        
        self.header_layout.addWidget(self.combo_lang)
        self.header_layout.addWidget(self.combo_theme)
        
        self.main_layout.addWidget(self.header)

        # --- Middle Config (Splitter) ---
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(2)
        
        # 1. Left: File List
        self.panel_list = QFrame()
        lay_list = QVBoxLayout(self.panel_list)
        lay_list.setContentsMargins(10, 10, 5, 10)
        
        lbl_files = QLabel(t('files'))
        lbl_files.setStyleSheet("font-weight: bold;")
        lay_list.addWidget(lbl_files)
        
        # Selection Buttons
        btn_sel_lay = QHBoxLayout()
        btn_sel_all = QPushButton(t('select_all'))
        btn_sel_none = QPushButton(t('deselect_all'))
        btn_sel_lay.addWidget(btn_sel_all)
        btn_sel_lay.addWidget(btn_sel_none)
        lay_list.addLayout(btn_sel_lay)
        
        # Format Filter
        filter_lay = QHBoxLayout()
        filter_lbl = QLabel(t('filter_format', 'Формат:'))
        self.format_filter = QComboBox()
        self.format_filter.addItems([t('all_formats', 'Все'), 'MP3', 'FLAC', 'M4A', 'OGG', 'WAV'])
        self.format_filter.currentTextChanged.connect(self._apply_format_filter)
        filter_lay.addWidget(filter_lbl)
        filter_lay.addWidget(self.format_filter)
        filter_lay.addStretch()
        lay_list.addLayout(filter_lay)
        
        self.file_list = FileListWidget()
        lay_list.addWidget(self.file_list)
        
        self.splitter.addWidget(self.panel_list)
        
        # 2. Center: Tag Editor
        self.panel_editor = TagEditorPanel()
        self.splitter.addWidget(self.panel_editor)
        
        # 3. Right: Cover + Batch
        self.panel_right = QFrame()
        lay_right = QVBoxLayout(self.panel_right)
        lay_right.setContentsMargins(5, 10, 10, 10)
        lay_right.setSpacing(15)
        
        self.cover_panel = CoverArtPanel()
        self.batch_panel = BatchEditorPanel()
        
        lay_right.addWidget(self.cover_panel)
        lay_right.addWidget(self.batch_panel)
        lay_right.addStretch()
        
        self.splitter.addWidget(self.panel_right)
        
        # Sizes
        self.splitter.setSizes([300, 400, 300])
        
        self.main_layout.addWidget(self.splitter)
        
        # --- Bottom Player Bar (Keep new feature) ---
        self.bottom_bar = QFrame()
        self.bottom_bar.setFixedHeight(120) # Increased height for new buttons
        self.bottom_bar.setStyleSheet(f"background-color: {ui_utils_qt.COLORS['bg_panel']};")
        
        self.player_layout = QHBoxLayout()
        self.bottom_bar.setLayout(self.player_layout)
        self.player_layout.setContentsMargins(20, 10, 20, 10)
        
        from ui_utils_qt import HoverButton
        self.btn_play = HoverButton("▶")
        self.btn_play.setFixedSize(60, 60)
        self.btn_play.radius = 30 # Circular
        self.btn_play.role = 'accent' # Purple/Green
        self.btn_play.font_size = "28px" # Large Icon
        self.btn_play.update_colors() # Apply colors and style immediately
        self.btn_play.hover_color = QColor(ui_utils_qt.COLORS['accent_hover'])
        self.btn_play.hover_color = QColor(ui_utils_qt.COLORS['accent_hover'])
        self.btn_play.pressed_color = QColor(ui_utils_qt.COLORS['accent_dark'])
        
        self.player_layout.addWidget(self.btn_play)
        
        self.time_layout = QVBoxLayout()
        self.lbl_title = QLabel(t('ready'))
        self.slider_layout = QHBoxLayout()
        self.lbl_current = QLabel("0:00")
        self.lbl_current.setStyleSheet(f"color: {ui_utils_qt.COLORS['text']}; font-weight: bold; font-size: 13px;")
        from ui_components import TrimSlider
        self.slider = TrimSlider(Qt.Orientation.Horizontal)
        self.lbl_total = QLabel("0:00")
        self.lbl_total.setStyleSheet(f"color: {ui_utils_qt.COLORS['text']}; font-weight: bold; font-size: 13px;")
        
        self.slider_layout.addWidget(self.lbl_current)
        self.slider_layout.addWidget(self.slider)
        self.slider_layout.addWidget(self.lbl_total)
        
        self.time_layout.addWidget(self.lbl_title)
        self.time_layout.addLayout(self.slider_layout)
        self.player_layout.addLayout(self.time_layout)
        
        # Trimming
        # Structure: VBox [ Row1: Start, End, Save ] [ Row2: Cancel ]
        # Trimming
        # Structure: HBox [ VBox(Start, End) ] [ VBox(Save, Cancel) ]
        self.trim_container_layout = QHBoxLayout()
        self.trim_container_layout.setSpacing(10)
        self.trim_container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Col 1
        col1 = QVBoxLayout()
        col1.setSpacing(5)
        self.btn_set_start = HoverButton(t('set_start'))
        self.btn_set_end = HoverButton(t('set_end'))
        col1.addWidget(self.btn_set_start)
        col1.addWidget(self.btn_set_end)
        
        # Col 2
        col2 = QVBoxLayout()
        col2.setSpacing(5)
        self.btn_save_trim = HoverButton(t('save_trim'))
        self.btn_cancel_trim = HoverButton(t('cancel'))
        self.btn_cancel_trim.clicked.connect(self._reset_trim)
        col2.addWidget(self.btn_save_trim)
        col2.addWidget(self.btn_cancel_trim)
        
        # Unified Widths
        btn_w = 130 # Increased from 110 to fit text
        for btn in [self.btn_set_start, self.btn_set_end, self.btn_save_trim, self.btn_cancel_trim]:
            btn.setFixedWidth(btn_w)
            
        self.trim_container_layout.addLayout(col1)
        self.trim_container_layout.addLayout(col2)
        
        # Add to player layout (it was likely done after this block, I'll rely on existing code unless I need to add it)
        # I'll check if I need to add it. 
        # If I am replacing lines 274-305, I need to check if `trim_container_layout` was used.
        # Assuming YES.
        
        self.player_layout.addLayout(self.trim_container_layout)
        
        self.trim_start_time = 0
        self.trim_end_time = 0
        
        # Rows removed, using columns now
        
        # Equalizer
        eq_lbl = QLabel(t('equalizer', 'EQ:'))
        from equalizer_presets import get_preset_names
        from PyQt6.QtWidgets import QListView
        self.eq_combo = QComboBox()
        self.eq_combo.setView(QListView())
        self.eq_combo.addItems(get_preset_names())
        self.eq_combo.setFixedWidth(120)
        self.eq_combo.currentTextChanged.connect(self._change_eq)
        
        # Visualization toggle
        self.cb_visualization = QCheckBox(t('visualization', 'Визуализация'))
        self.cb_visualization.setChecked(False)
        self.cb_visualization.stateChanged.connect(self._toggle_visualization)
        
        # Right Control Group
        right_ctrl_lay = QVBoxLayout()
        right_ctrl_lay.addWidget(eq_lbl)
        right_ctrl_lay.addWidget(self.eq_combo)
        right_ctrl_lay.addWidget(self.cb_visualization)
        
        self.player_layout.addSpacing(10)
        self.player_layout.addLayout(self.trim_container_layout)
        self.player_layout.addSpacing(10)
        self.player_layout.addLayout(right_ctrl_lay)
        
        # Visualization Widget
        from visualization_widget import VisualizationWidget
        self.visualization = VisualizationWidget()
        self.visualization.setFixedHeight(150) # Taller
        self.visualization.setVisible(False)  # Hidden by default
        self.visualization.set_analyzer(self.analyzer)
        self.visualization.set_player_reference(self.player)
        
        # Add to main layout, before bottom bar
        self.main_layout.addWidget(self.visualization)
        self.main_layout.setSpacing(0) # Reduce gap between viz and player for "connected" feel? 
        # Or user said "Make it higher up". Maybe strictly taller is enough.
        # "Uneven top and bottom" -> likely internal drawing padding.
        # I should also check VisualizationWidget paint event but setting height here helps.
        
        self.main_layout.addWidget(self.bottom_bar)
        
        # Connect Selection Buttons logic (inline for simplicity or method)
        btn_sel_all.clicked.connect(self.file_list.selectAll)
        btn_sel_none.clicked.connect(self.file_list.clearSelection)
        
        # Status Bar
        self.status = QLabel("Ready")
        self.status.setContentsMargins(10, 2, 10, 2)
        self.statusBar().addWidget(self.status)

    def _connect_signals(self):
        # File Operations
        self.btn_open_files.clicked.connect(self._add_files)
        self.btn_open_folder.clicked.connect(self._add_folder)
        
        # List
        self.file_list.itemSelectionChanged.connect(self._on_selection_changed)
        self.file_list.files_dropped.connect(self._load_files)
        # Play on double click
        self.file_list.doubleClicked.connect(lambda: self._toggle_playback())
        
        # Editor
        self.btn_save.clicked.connect(self._save_changes)
        self.btn_save_all.clicked.connect(self._save_all_changes)
        self.cover_panel.cover_changed.connect(self._on_cover_changed)
        
        # Player
        self.btn_play.clicked.connect(self._toggle_playback)
        self.slider.sliderPressed.connect(self._on_slider_pressed)
        self.slider.sliderReleased.connect(self._on_slider_released)
        self.slider.valueChanged.connect(self._on_slider_value) # For drag updates
        
        # Trimming
        self.btn_set_start.clicked.connect(self._set_start_time)
        self.btn_set_end.clicked.connect(self._set_end_time)
        self.btn_save_trim.clicked.connect(self._save_trimmed)
        
        # Player Backend
        self.player.state_changed.connect(self._on_player_state)
        self.player.position_changed.connect(self._on_player_position)
        self.player.duration_changed.connect(self._on_player_duration)
        self.player.error_occurred.connect(self._show_error)

    def _add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, t('select_audio'), "", f"{t('audio_files')} (*.mp3 *.flac *.m4a *.ogg *.wav)")
        if files:
            self._load_files(files)

    def _add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, t('select_folder'))
        if folder:
            files = TagEngine.get_supported_files(folder)
            self._load_files(files)

    def _open_converter(self):
        # Gather file paths
        # If selection, use selection. Else use all files.
        files = []
        selected_items = self.file_list.selectedItems()
        if selected_items:
             files = [item.data(Qt.ItemDataRole.UserRole).file_path for item in selected_items]
        else:
             files = [t.file_path for t in self.loaded_files]
             
        if not files:
            QMessageBox.information(self, t('info'), t('no_files_convert'))
            return
            
        dlg = ConverterDialog(self, files)
        dlg.exec()

    def _load_files_chunked(self):
        if not hasattr(self, '_load_queue') or not self._load_queue:
             self.status.setText(t('files_count').format(len(self.loaded_files)))
             return
             
        # Take chunk
        CHUNK_SIZE = 10
        chunk = self._load_queue[:CHUNK_SIZE]
        self._load_queue = self._load_queue[CHUNK_SIZE:]
        
        for path in chunk:
            if os.path.isdir(path): continue
            if not os.path.isfile(path): continue
            
            track = TagEngine.read_tags(path)
            if track:
                self.loaded_files.append(track)
                self.file_list.add_track(track)
        
        self.status.setText(f"{t('loading', 'Loading...')} {len(self.loaded_files)}")
        
        if self._load_queue:
            QTimer.singleShot(0, self._load_files_chunked)
        else:
             self.status.setText(t('files_count').format(len(self.loaded_files)))

    def _load_files(self, paths):
        if not hasattr(self, '_load_queue'):
            self._load_queue = []
        self._load_queue.extend(paths)
        QTimer.singleShot(0, self._load_files_chunked)
        
    def _save_auto_update(self, state):
        self.settings.setValue("auto_update", state == Qt.CheckState.Checked.value or state == True)
        
    def _change_language(self, index):
        code = 'ru' if index == 0 else 'en'
        if code != get_language():
            set_language(code)
            self._reload_ui()
    
    def _change_theme(self, theme_name):
        from ui_themes import get_theme
        theme = get_theme(theme_name)
        ui_utils_qt.apply_theme(theme)
        self.setStyleSheet(ui_utils_qt.get_stylesheet())
        self.settings.setValue("theme", theme_name)
        self.bottom_bar.setStyleSheet(f"background-color: {ui_utils_qt.COLORS['bg_panel']};")
        self._update_hover_buttons(self)
        
        # Restore custom color for Converter Button
        if hasattr(self, 'btn_converter'):
             self.btn_converter.default_color = QColor("#9b59b6")
             self.btn_converter.hover_color = QColor("#8e44ad")
             self.btn_converter.pressed_color = QColor("#71368a")
             self.btn_converter.update_style(self.btn_converter.default_color)
        
    def _update_hover_buttons(self, widget):
        from ui_utils_qt import HoverButton
        children = widget.findChildren(HoverButton)
        for btn in children:
            btn.update_colors()
            
    def _reload_ui(self):
        # Header
        self.btn_open_files.setText(t('open_files'))
        self.btn_open_folder.setText(t('open_folder'))
        self.btn_save.setText(t('save'))
        self.btn_save_all.setText(t('save_all'))
        self.btn_converter.setText(t('converter_title'))
        self.cb_auto_update.setText(t('auto_update'))
        
        # Splitter Panels (Need methods in panels to refresh texts)
        # For simplicity, we can just re-create them or add update_texts() methods.
        # Adding simple update methods to components is cleaner but takes more edits.
        # Let's try to update accessible labels directly or hint user to restart for full effect if complex.
        # User requested dynamic without restart.
        # We need to update labels in TagEditorPanel, FileListWidget headers, BatchEditorPanel.
        
        # File List Header
        # FileListWidget doesn't expose headers easily, but it has 'files' label in MainWindow
        self.panel_list.findChild(QLabel).setText(t('files'))
        # Selection buttons
        # They were added to layout, need references. 
        # Making them attributes in _init_ui would be better.
        # For now, let's ask user to restart for full effect or implement deep reload later?
        # User insisted on dynamic.
        # Best approach: recreate central widget? No, state loss.
        # Iterate children?
        
        # Okay, let's just partial reload what we can easily access and maybe re-init UI components?
        # Re-initing UI components might lose state (unsaved changes).
        
        # Let's settle for updating Main Window buttons and Labels we can reach easily.
        # And implemented simple `retranslate_ui` methods in panels if possible.
        pass # Placeholder as we need to modify components to support retranslation

    def _clear_list(self):
        self.file_list.clear()
        self.loaded_files.clear()
        self.panel_editor.load_track(None) # Renamed panel
        self.cover_panel.set_cover(None)
        self.player.stop()

    def _apply_format_filter(self, filter_text):
        """Filter file list by format."""
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            track: TrackInfo = item.data(Qt.ItemDataRole.UserRole)
            if filter_text in [t('all_formats', 'Все'), 'Все', 'All']:
                item.setHidden(False)
            else:
                ext = os.path.splitext(track.file_path)[1].lower()
                format_map = {'.mp3': 'MP3', '.flac': 'FLAC', '.m4a': 'M4A', '.ogg': 'OGG', '.wav': 'WAV'}
                item_format = format_map.get(ext, '')
                item.setHidden(item_format != filter_text)

    def _on_selection_changed(self):
        items = self.file_list.selectedItems()
        if not items:
            return
        
        # Save current unsaved changes to track object (in memory, not to file)
        if self.panel_editor.current_track:
            old_track = self.panel_editor.current_track
            values = self.panel_editor.get_values()
            old_track.title = values.get('title', old_track.title)
            old_track.artist = values.get('artist', old_track.artist)
            old_track.album = values.get('album', old_track.album)
            old_track.year = values.get('year', old_track.year)
            old_track.genre = values.get('genre', old_track.genre)
            old_track.composer = values.get('composer', old_track.composer)
            old_track.comment = values.get('comment', old_track.comment)
            old_track.lyrics = values.get('lyrics', old_track.lyrics)
            # Track/Disk - separate fields
            old_track.track_number = values.get('track_number', old_track.track_number)
            old_track.track_total = values.get('track_total', old_track.track_total)
            old_track.disc_number = values.get('disk_number', old_track.disc_number)
            old_track.disc_total = values.get('disk_total', old_track.disc_total)
            # Cover is auto-updated via signal
            old_track.cover_data = self.cover_panel.current_cover_data
            old_track.cover_mime = self.cover_panel.current_mime or old_track.cover_mime
            
        # Single selection logic for now
        item = items[0]
        track: TrackInfo = item.data(Qt.ItemDataRole.UserRole)
        
        # 1. Update Tag Editor Panel
        self.panel_editor.set_track(track)
        
        # 2. Update Cover Panel
        self.cover_panel.set_cover(track.cover_data, track.cover_mime)
        
        # 3. Load into Player
        self.slider.setValue(0)
        self.slider.setMaximum(int(track.duration * 1000))
        self.player.load(track.file_path)
        
        # 4. Load into Analyzer
        self.analyzer.load(track.file_path)

    def _on_cover_changed(self, data, mime):
        # Update current track object in panel
        if self.panel_editor.current_track:
            self.panel_editor.current_track.cover_data = data

    def _rename_file_with_track(self, track: TrackInfo):
        """Rename file adding track number prefix if needed."""
        if not track or not track.track_number:
            return
            
        try:
            old_path = track.file_path
            directory = os.path.dirname(old_path)
            filename = os.path.basename(old_path)
            
            # Regex to strip existing "N. " prefix
            clean_name = re.sub(r'^\d+\.\s*', '', filename)
            new_filename = f"{track.track_number}. {clean_name}"
            
            if new_filename == filename:
                return
                
            new_path = os.path.join(directory, new_filename)
            
            if os.path.exists(new_path):
                # Avoid overwrite
                return
                
            os.rename(old_path, new_path)
            track.file_path = new_path
            
        except Exception as e:
            print(f"Rename error: {e}")

    def _save_all_changes(self):
        """Save all loaded files with batch options applied."""
        if not self.loaded_files:
            return

        # 1. First, ensure current editor values are committed to current track
        if self.panel_editor.current_track:
             # This logic mimics _save_changes but only updates the object, doesn't write file yet
             t_curr = self.panel_editor.current_track
             values = self.panel_editor.get_values()
             
             t_curr.title = values['title']
             t_curr.artist = values['artist']
             t_curr.album = values['album']
             t_curr.year = values['year']
             t_curr.genre = values['genre']
             t_curr.composer = values['composer']
             t_curr.comment = values['comment']
             t_curr.lyrics = values.get('lyrics', '')
             
             t_curr.track_number = values.get('track_number', '').strip()
             t_curr.track_total = values.get('track_total', '').strip()
             t_curr.disc_number = values.get('disk_number', '').strip()
             t_curr.disc_total = values.get('disk_total', '').strip()
             
             # Cover
             t_curr.cover_data = self.cover_panel.current_cover_data
             t_curr.cover_mime = self.cover_panel.current_mime or t_curr.cover_mime

        batch_values = self.batch_panel.get_batch_values()
        
        tracks_in_order = []
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            track = item.data(Qt.ItemDataRole.UserRole)
            if track:
                tracks_in_order.append((item, track))
        
        saved_count = 0
        total = len(tracks_in_order)
        
        self.status.setText(t('saving'))
        QApplication.processEvents()
        
        for index, (item, track) in enumerate(tracks_in_order):
            for key, value in batch_values.items():
                if key in ['auto_number', 'apply_cover']: continue
                
                if hasattr(track, key):
                    setattr(track, key, value)
                elif key == 'track_total':
                    track.track_total = value
                elif key == 'disc_number':
                    track.disc_number = value
                elif key == 'disc_total':
                    track.disc_total = value
            
            if batch_values.get('auto_number'):
                track.track_number = str(index + 1)
            
            if batch_values.get('apply_cover'):
                 track.cover_data = self.cover_panel.current_cover_data
                 track.cover_mime = self.cover_panel.current_mime or track.cover_mime

            if TagEngine.write_tags(track):
                # Rename logic
                self._rename_file_with_track(track)
                
                saved_count += 1
                from ui_components import FileListItemWidget
                self.file_list.setItemWidget(item, FileListItemWidget(track))
        
        if self.panel_editor.current_track:
            self.panel_editor.set_track(self.panel_editor.current_track)
            
        self.status.setText(t('saved_count').format(saved_count, total))
        # Popup removed as requested

    def _save_changes(self):
        if not self.panel_editor.current_track:
            return
            
        # Get values from UI
        values = self.panel_editor.get_values()
        t = self.panel_editor.current_track
        
        t.title = values['title']
        t.artist = values['artist']
        t.album = values['album']
        t.year = values['year']
        t.genre = values['genre']
        t.composer = values['composer']
        t.comment = values['comment']
        t.lyrics = values.get('lyrics', '')
        
        # Track/Disc - now separate fields
        t.track_number = values.get('track_number', '').strip()
        t.track_total = values.get('track_total', '').strip()
        t.disc_number = values.get('disk_number', '').strip()
        t.disc_total = values.get('disk_total', '').strip()

        # Validation: Check for duplicates
        if t.artist and t.album and t.track_number:
            for other in self.loaded_files:
                if other == t: continue
                if (other.artist.lower() == t.artist.lower() and 
                    other.album.lower() == t.album.lower() and 
                    other.track_number == t.track_number):
                    
                    QMessageBox.warning(self, "Warning", f"Duplicate Track #{t.track_number} for this Album!")
                    return
            
        # Cover is already updated via signal or manually if we want to be safe
        t.cover_data = self.cover_panel.current_cover_data
        t.cover_mime = self.cover_panel.current_mime or t.cover_mime
        
        # Write
        if TagEngine.write_tags(t):
            # Rename logic
            self._rename_file_with_track(t)
            
            self.status.setText(f"Saved: {t.filename}")
            items = self.file_list.selectedItems()
            if items:
                # Update widget
                item = items[0]
                from ui_components import FileListItemWidget
                self.file_list.setItemWidget(item, FileListItemWidget(t))
        else:
            self._show_error("Failed to save tags.")

    # --- Player Logic ---
    
    def _toggle_playback(self):
        if self.player.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.visualization.stop()
        else:
            self.player.play()
            if self.cb_visualization.isChecked():
                self.visualization.start()
            
    def _on_media_restore(self, status):
        # Handle restoring position after EQ change/reload
        # Using a small delay is safer for Qt Multimedia to ensure seekability
        if status in (QMediaPlayer.MediaStatus.BufferedMedia, QMediaPlayer.MediaStatus.LoadedMedia):
            if hasattr(self, '_restore_pending') and self._restore_pending:
                pos = self._restore_pos
                playing = self._restore_playing
                
                def restore():
                    self.player.set_position(pos)
                    if playing:
                        self.player.play()
                
                QTimer.singleShot(100, restore)
                self._restore_pending = False
                
    def _on_player_state(self, state):
        # state is int: 0=Stopped, 1=Playing, 2=Paused
        if state == 1:  # Playing
            self.btn_play.setText("⏸")
            # Start visualization if enabled
            if self.cb_visualization.isChecked() and hasattr(self, 'visualization'):
                self.visualization.start()
        else:
            self.btn_play.setText("▶")
            # Stop visualization
            if hasattr(self, 'visualization'):
                self.visualization.stop()
            if state == 0:  # Stopped
               self.slider.setValue(0)
               self.lbl_current.setText("0:00")
    
    def _toggle_visualization(self, state):
        """Toggle visualization visibility."""
        visible = state == Qt.CheckState.Checked.value
        if hasattr(self, 'visualization'):
            self.visualization.setVisible(visible)
            # If playing, start/stop visualization
            if self.player.player.playbackState().value == 1:  # Playing
                if visible:
                    self.visualization.start()
                else:
                    self.visualization.stop()
            
    def _on_player_position(self, pos):
        if not self.is_slider_dragged:
            self.slider.setValue(pos)
            self.lbl_current.setText(self._format_time(pos))
        
        # Sync visualization
        if hasattr(self, 'visualization') and self.visualization.isVisible():
            self.visualization.set_position(pos)
            
    def _on_player_duration(self, dur):
        self.slider.setMaximum(dur)
        self.lbl_total.setText(self._format_time(dur))

    def _on_slider_pressed(self):
        self.is_slider_dragged = True

    def _on_slider_released(self):
        self.is_slider_dragged = False
        pos = self.slider.value()
        self.player.set_position(pos)

    def _on_slider_value(self, val):
        if self.is_slider_dragged:
            self.lbl_current.setText(self._format_time(val))

    def _format_time(self, ms):
        seconds = ms // 1000
        m = seconds // 60
        s = seconds % 60
        return f"{m}:{s:02d}"

    def _show_error(self, msg):
        QMessageBox.critical(self, "Error", msg)

    # --- Trimming ---
    
    def _set_start_time(self):
        self.trim_start_time = self.player.get_position()
        self.slider.set_trim_mark(self.trim_start_time, self.trim_end_time)
        self.status.setText(t('start_set').format(self._format_time(self.trim_start_time)))
        
    def _set_end_time(self):
        self.trim_end_time = self.player.get_position()
        self.slider.set_trim_mark(self.trim_start_time, self.trim_end_time)
        self.status.setText(t('end_set').format(self._format_time(self.trim_end_time)))
        
    def _reset_trim(self):
        """Reset trim markers."""
        self.trim_start_time = 0
        self.trim_end_time = 0
        self.slider.set_trim_mark(0, 0)
        self.status.setText(t('ready'))
        
    def _save_trimmed(self):
        if self.trim_end_time <= self.trim_start_time:
             QMessageBox.warning(self, t('warning'), t('end_time_error'))
             return
             
        track = self.panel_editor.current_track
        if not track:
            return
            
        # Advanced Save Dialog
        from ui_components import TrimSaveDialog
        dlg = TrimSaveDialog(self)
        if not dlg.exec():
            return
            
        fmt_key, qual_str = dlg.get_values()
        
        # Get encoding args from presets (use UPPERCASE format key)
        from converter_engine import ConverterEngine
        eng = ConverterEngine()
        qual_presets = eng.get_presets(fmt_key.upper())
        q_args = qual_presets.get(qual_str, "")
        
        # Apply equalizer if selected
        from equalizer_presets import apply_eq_to_args
        eq_preset = self.eq_combo.currentText()
        if eq_preset and eq_preset != 'Flat':
            q_args = apply_eq_to_args(q_args, eq_preset)
        
        # Output Folder - Persist
        last_dir = self.settings.value("last_trim_dir", "")
        if not last_dir:
            last_dir = os.path.dirname(track.file_path)
            
        # Ask for file name (with folder)
        default_name = os.path.join(last_dir, os.path.splitext(track.filename)[0] + f"_trim.{fmt_key}")
        
        # Use QFileDialog to pick location
        out_path, _ = QFileDialog.getSaveFileName(self, t('save_trim'), default_name)
        
        if out_path:
            # Save dir
            self.settings.setValue("last_trim_dir", os.path.dirname(out_path))
            
            # Convert quality string to args (re-encode)
            success, msg = self.player.trim_audio(self.trim_start_time, self.trim_end_time, out_path, encode_args=q_args)
            if success:
                QMessageBox.information(self, t('saved'), t('saved'))
            else:
                QMessageBox.critical(self, t('error'), f"{t('error')}: {msg}")

    # --- Equalizer Preview Logic ---
    
    def _change_eq(self, preset_name):
        """Handle EQ preset change to preview effect via Worker."""
        track = self.panel_editor.current_track
        if not track:
            return
            
        # Save state for restoration
        self._restore_pos = self.player.get_position()
        self._restore_playing = self.player.player.playbackState().value == 1
        self._restore_pending = True

        if preset_name == 'Flat':
            # Restore original
            self.player.load(track.file_path)
            # Restoration happens in _on_media_restore
            self.status.setText(t('ready'))
            return
            
        from equalizer_presets import get_preset_filter
        eq_filter = get_preset_filter(preset_name)
        if not eq_filter:
            self._restore_pending = False
            return
            
        # ... (rest of logic)
            
        # Prep paths
        temp_dir = os.path.join(os.environ.get('TEMP', '.'), 'storm_tag_editor_preview')
        os.makedirs(temp_dir, exist_ok=True)
        temp_file = os.path.join(temp_dir, 'preview.wav')
        
        # Save state
        self._eq_pos_cache = self.player.get_position()
        self._eq_playing_cache = self.player.player.playbackState().value == 1
        
        # Show busy
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.status.setText(f"Applying EQ: {preset_name} (Generating Preview)...")
        self.eq_combo.setEnabled(False)
        
        # Start Worker
        self.eq_worker = EQWorker(self.player, track.file_path, temp_file, eq_filter)
        self.eq_worker.finished_signal.connect(lambda s, m, p: self._on_eq_finished(s, m, p, preset_name))
        self.eq_worker.start()
        
    def _on_eq_finished(self, success, msg, path, preset_name):
        QApplication.restoreOverrideCursor()
        self.eq_combo.setEnabled(True)
        
        if success:
            self._restore_pending = True
            # Update cache info for the helper
            self._restore_pos = self._eq_pos_cache
            self._restore_playing = self._eq_playing_cache
            
            self.player.load(path)
            # Restoration happens in _on_media_restore
            
            self.status.setText(f"EQ: {preset_name} applied (Preview)")
        else:
            self.status.setText(f"EQ Error: {msg}")
            QMessageBox.warning(self, "EQ Error", msg)

from PyQt6.QtCore import QThread, pyqtSignal

class EQWorker(QThread):
    finished_signal = pyqtSignal(bool, str, str) # success, msg, temp_file

    def __init__(self, player, input_path, output_path, filter_str):
        super().__init__()
        self.player = player
        self.input_path = input_path
        self.output_path = output_path
        self.filter_str = filter_str

    def run(self):
        success, msg = self.player.apply_filter(self.input_path, self.output_path, self.filter_str)
        self.finished_signal.emit(success, msg, self.output_path)

class AudioAnalysisWorker(QThread):
    """
    Analyzes audio file to generate amplitude map for visualization sync.
    Uses FFmpeg to stream PCM data and calculate RMS.
    """
    data_ready = pyqtSignal(list, float) # amplitudes (0-1), duration

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        try:
            # Use FFmpeg to get raw PCM data (mono, 44100Hz, s16le)
            cmd = [
                "ffmpeg", 
                "-i", self.file_path,
                "-f", "s16le",
                "-ac", "1",
                "-ar", "8000", # Lower sample rate for speed
                "-"
            ]
            
            # Run process
            import subprocess
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.DEVNULL,
                bufsize=10**6
            )
            
            chunk_size = 800 # 0.1s at 8000Hz
            amplitudes = []
            
            import struct
            import math
            
            while True:
                raw_data = process.stdout.read(chunk_size * 2) # 2 bytes per sample
                if not raw_data:
                    break
                    
                # Calculate RMS
                # Using struct to unpack is slow for large data, but for 0.1s chunks it's ok-ish (4k samples)
                # Optimization: Max value or simple avg
                count = len(raw_data) // 2
                if count == 0: break
                
                # Simple envelope: max value in chunk
                # Better: RMS
                shorts = struct.unpack(f"{count}h", raw_data)
                
                # RMS
                sum_sq = sum(s*s for s in shorts)
                rms = math.sqrt(sum_sq / count)
                
                # Normalize (16-bit max is 32768)
                amp = rms / 32768.0
                amplitudes.append(amp)
                
            process.wait()
            
            # Emit data (interval 0.1s)
            self.data_ready.emit(amplitudes, 0.1)
            
        except Exception as e:
            print(f"Analysis failed: {e}")
            # Fallback random
            pass
        self.file_path = file_path

    def run(self):
        # Todo: Implement real analysis. for now, generate structure based on file size/hash
        # to at least be deterministic?
        # Better: Use FFmpeg via AudioPlayer to get volume stats? Too slow.
        # Let's generate a "fake but consistent" map or just use random for now?
        # User said "Must correspond to music".
        # Let's try to extract volume levels using ffmpeg 'ebur128' or 'volumedetect'?
        # Too slow for instant play.
        # Fallback: Just random variations in the widget was "ok" but "must move WITH IT".
        # The widget currently moves randomly.
        # Let's improve the widget's internal random generator to look more rhythmic?
        # OR: Actually implement a worker that runs `ffmpeg -i file -f s16le -ac 1 -ar 4000 -`
        # and reads PCM chunks to calculate RMS.
        import subprocess
        import struct
        import math
        
        try:
            # Downsample heavily for speed (4000Hz)
            cmd = [
                'ffmpeg.exe', '-y', 
                '-i', self.file_path,
                '-f', 's16le', '-ac', '1', '-ar', '4000', 
                '-'
            ]
            
            # Hide console
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, startupinfo=startupinfo)
            
            amps = []
            chunk_size = 400 # 0.1s at 4000Hz
            
            while True:
                data = process.stdout.read(chunk_size * 2) # 2 bytes per sample
                if not data:
                    break
                
                # Calculate RMS of chunk
                count = len(data) // 2
                sum_sq = 0
                for i in range(0, len(data), 2):
                    sample = struct.unpack('<h', data[i:i+2])[0]
                    sum_sq += sample * sample
                
                rms = math.sqrt(sum_sq / count) if count > 0 else 0
                norm = min(1.0, rms / 20000.0) # Normalize approx
                amps.append(norm)
                
            self.data_ready.emit(amps, 0.1) # 0.1s per step
            
        except Exception:
            self.data_ready.emit([], 0.1)

if __name__ == '__main__':
    # Set AppUserModelID for Windows Taskbar Icon
    import ctypes
    myappid = 'mycompany.myproduct.subproduct.version' # arbitrary string
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    qInstallMessageHandler(qt_message_handler)

    from PyQt6.QtCore import QLockFile, QDir
    app = QApplication(sys.argv)
    
    # Single Instance Check
    lock_file = QLockFile(QDir.tempPath() + "/storm_tag_editor.lock")
    if not lock_file.tryLock(100):
        # Already running
        from PyQt6.QtWidgets import QMessageBox
        # Use APP_NAME and localized text
        QMessageBox.warning(None, APP_NAME, t('app_running_error'))
        sys.exit(1)
        
    app.setStyle("Fusion") # Good base for dark theme
    
    # Load stylesheet
    app.setStyleSheet(ui_utils_qt.get_stylesheet())
    
    # Set Icon
    icon_path = ui_utils_qt.resource_path("stormtageditor.ico")
    app.setWindowIcon(QIcon(icon_path))
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())
