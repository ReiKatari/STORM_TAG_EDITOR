
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFrame, QFileDialog, QScrollArea, QComboBox,
    QListWidget, QListWidgetItem, QMenu, QSizePolicy, QGridLayout, QCheckBox,
    QSlider, QTextEdit, QStyle, QApplication, QStyleOptionSlider
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QByteArray
from PyQt6.QtGui import QPixmap, QImage, QIcon, QAction, QPainter, QColor, QBrush

from ui_utils_qt import COLORS, FONT_FAMILY
from tag_engine import TagEngine, TrackInfo
from PyQt6.QtWidgets import QCompleter

# Full Genre List
GENRE_PRESETS = [
    "Blues", "Cinematic Modern Gothic", "Classic Rock", "Country", "Dance", "Disco", "Funk", "Grunge", 
    "Hip-Hop", "Jazz", "Metal", "New Age", "Oldies", "Other", "Pop", "R&B", 
    "Rap", "Reggae", "Rock", "Techno", "Industrial", "Alternative", "Ska", 
    "Death Metal", "Pranks", "Soundtrack", "Euro-Techno", "Ambient", 
    "Trip-Hop", "Vocal", "Jazz+Funk", "Fusion", "Trance", "Classical", 
    "Instrumental", "Acid", "House", "Game", "Sound Clip", "Gospel", 
    "Noise", "AlternRock", "Bass", "Soul", "Punk", "Space", "Meditative", 
    "Instrumental Pop", "Instrumental Rock", "Ethnic", "Gothic", 
    "Darkwave", "Techno-Industrial", "Electronic", "Pop-Folk", 
    "Eurodance", "Dream", "Southern Rock", "Comedy", "Cult", "Gangsta", 
    "Top 40", "Christian Rap", "Pop/Funk", "Jungle", "Native American", 
    "Cabaret", "New Wave", "Psychadelic", "Rave", "Showtunes", "Trailer", 
    "Lo-Fi", "Tribal", "Acid Punk", "Acid Jazz", "Polka", "Retro", 
    "Musical", "Rock & Roll", "Hard Rock", "Folk", "Folk-Rock", 
    "National Folk", "Swing", "Fast Fusion", "Bebob", "Latin", "Revival", 
    "Celtic", "Bluegrass", "Avantgarde", "Gothic Rock", "Porgressive Rock", 
    "Psychedelic Rock", "Symphonic Rock", "Slow Rock", "Big Band", 
    "Chorus", "Easy Listening", "Acoustic", "Humour", "Speech", "Chanson", 
    "Opera", "Chamber Music", "Sonata", "Symphony", "Booty Bass", "Primus", 
    "Porn Groove", "Satire", "Slow Jam", "Club", "Tango", "Samba", 
    "Folklore", "Ballad", "Power Ballad", "Rhythmic Soul", "Freestyle", 
    "Duet", "Punk Rock", "Drum Solo", "Acapella", "Euro-House", "Dance Hall"
]
GENRE_PRESETS.sort()
# Translation placeholders (we can wire up real localization later or use defaults)
from localization import t


class ModernEntry(QLineEdit):
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)

class CoverArtPanel(QFrame):
    cover_changed = pyqtSignal(bytes, str) # data, mime

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Panel")
        
        self.current_cover_data = None
        self.current_mime = ""
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Image Preview
        self.image_label = QLabel()
        self.image_label.setFixedSize(200, 200)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet(f"background-color: {COLORS['bg_input']}; border-radius: 8px; color: {COLORS['text_muted']};")
        self.image_label.setText(t('no_cover'))
        self.image_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.image_label.mousePressEvent = self.show_full_cover
        layout.addWidget(self.image_label)
        
        # DND
        self.setAcceptDrops(True)
        
        # Buttons
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        from ui_utils_qt import HoverButton
        self.btn_change = HoverButton(t('change_cover'))
        self.btn_change.clicked.connect(self._select_cover)
        
        self.btn_remove = HoverButton(t('remove_cover'))
        self.btn_remove.setObjectName("DangerButton") # Standard styling for danger
        self.btn_remove.clicked.connect(self._remove_cover)
        
        self.btn_extract = HoverButton(t('extract_cover'))
        self.btn_extract.clicked.connect(self._extract_cover)
        
        btn_layout.addWidget(self.btn_change)
        btn_layout.addWidget(self.btn_remove)
        btn_layout.addWidget(self.btn_extract)
        
        layout.addLayout(btn_layout)
        layout.addStretch() # Push everything to left

    def set_cover(self, data: bytes, mime=""):
        self.current_cover_data = data
        self.current_mime = mime
        if data:
            image = QImage.fromData(QByteArray(data))
            if not image.isNull():
                # Scale keeping aspect ratio
                pixmap = QPixmap.fromImage(image).scaled(
                    200, 200, 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
                self.image_label.setPixmap(pixmap)
                self.image_label.setText("")
                return
        
        self.image_label.setPixmap(QPixmap())
        self.image_label.setText(t('no_cover'))

    def _select_cover(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            t('change_cover'), 
            "", 
            "Images (*.jpg *.jpeg *.png *.bmp *.gif)"
        )
        if file_path:
            data, mime = TagEngine.load_cover_from_file(file_path)
            if data:
                self.set_cover(data)
                self.current_mime = mime
                self.cover_changed.emit(data, mime)

    def _remove_cover(self):
        self.set_cover(None)
        self.current_mime = ""
        self.cover_changed.emit(None, "")

    def _extract_cover(self):
        if not self.current_cover_data:
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            t('extract_cover'),
            "cover.jpg",
            "JPEG (*.jpg);;PNG (*.png)"
        )
        if file_path:
            try:
                with open(file_path, 'wb') as f:
                    f.write(self.current_cover_data)
            except Exception as e:
                print(f"Error saving: {e}")

    # drag support
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if not file_path:
                continue
                
            # Check extension
            ext = os.path.splitext(file_path)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']:
                data, mime = TagEngine.load_cover_from_file(file_path)
                if data:
                    self.set_cover(data)
                    self.current_mime = mime
                    self.cover_changed.emit(data, mime)
                break # Only one cover

    def show_full_cover(self, event=None):
        """Show enlarged cover art in a centered overlay dialog."""
        if not self.current_cover_data:
            return
            
        from PyQt6.QtWidgets import QDialog
        
        # Create overlay dialog
        dlg = QDialog(self.window())
        dlg.setWindowTitle(t('cover'))
        dlg.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        dlg.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Create enlarged image label
        img_label = QLabel()
        img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img_label.setStyleSheet(f"background-color: {COLORS['bg_panel']}; border-radius: 12px; padding: 10px;")
        
        # Load full-size image
        image = QImage.fromData(QByteArray(self.current_cover_data))
        if not image.isNull():
            # Scale to max 600x600 keeping aspect ratio (increased slightly)
            pixmap = QPixmap.fromImage(image).scaled(
                600, 600,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            img_label.setPixmap(pixmap)
            
        layout.addWidget(img_label)
        
        # Close on click safe wrapper
        def safe_close(e):
            try:
                dlg.accept() # Use accept instead of close for dialogs
            except Exception as e:
                print(f"Error closing cover: {e}")
        
        img_label.mousePressEvent = safe_close
        
        # Center on parent window
        parent_geo = self.window().geometry()
        dlg.adjustSize()
        dlg.move(
            parent_geo.center().x() - dlg.width() // 2,
            parent_geo.center().y() - dlg.height() // 2
        )
        
        dlg.exec()


class LocalizedTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
    # def contextMenuEvent(self, event):
    #     menu = QMenu(self)
    #     _populate_edit_menu(menu, self)
    #     menu.exec(event.globalPos())

class TagEditorPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Panel")
        
        self.current_track = None
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        content_widget = QWidget()
        self.layout = QVBoxLayout(content_widget)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)
        
        # Title
        title_lbl = QLabel(t('tag_editor'))
        title_lbl.setObjectName("Title")
        self.layout.addWidget(title_lbl)
        
        self.info_lbl = QLabel(t('select_file_hint'))
        self.info_lbl.setObjectName("Subtitle")
        self.layout.addWidget(self.info_lbl)
        
        # Fields
        self.entries = {}
        self._add_field('title', t('title'))
        self._add_field('artist', t('artist'))
        self._add_field('album', t('album'))
        
        # Grid for short fields - Row 1: Year, Track, Track Total
        # Grid for short fields - 3 Columns with Equal Width
        short_fields_grid = QGridLayout()
        short_fields_grid.setSpacing(15)
        
        # Ensure all 3 columns have equal stretch factor
        short_fields_grid.setColumnStretch(0, 1)
        short_fields_grid.setColumnStretch(1, 1)
        short_fields_grid.setColumnStretch(2, 1)
        
        # Row 1: Year | Track Num | Track Total
        self.entries['year'] = self._create_entry(t('year'))
        self.entries['track_number'] = self._create_entry(t('track_num'))
        self.entries['track_total'] = self._create_entry(t('track_total'))
        
        short_fields_grid.addWidget(self._wrap_field(t('year'), self.entries['year']), 0, 0)
        short_fields_grid.addWidget(self._wrap_field(t('track_num'), self.entries['track_number']), 0, 1)
        short_fields_grid.addWidget(self._wrap_field(t('track_total'), self.entries['track_total']), 0, 2)

        # Row 2: Disk Num | Disk Total | Empty
        self.entries['disk_number'] = self._create_entry(t('disc_num'))
        self.entries['disk_total'] = self._create_entry(t('disc_total'))
        
        short_fields_grid.addWidget(self._wrap_field(t('disc_num'), self.entries['disk_number']), 1, 0)
        short_fields_grid.addWidget(self._wrap_field(t('disc_total'), self.entries['disk_total']), 1, 1)
        
        self.layout.addLayout(short_fields_grid)

        # Genre (Separate, Full Width)
        self.genre_combo = QComboBox()
        self.genre_combo.setEditable(True)
        self.genre_combo.addItem("")
        self.genre_combo.addItems(GENRE_PRESETS)
        self.genre_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.genre_combo.completer().setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.genre_combo.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        
        self.layout.addWidget(self._wrap_field(t('genre'), self.genre_combo))
        
        self._add_field('composer', t('composer'))
        self._add_field('comment', t('comment')) # We might want TextEdit for comment? keeping LineEdit for now
        
        # Lyrics (Multi-line text editor)
        from PyQt6.QtWidgets import QTextEdit
        lyrics_layout = QVBoxLayout()
        lyrics_lbl = QLabel(t('lyrics'))
        self.lyrics_edit = LocalizedTextEdit()
        self.lyrics_edit.setPlaceholderText(t('lyrics'))
        self.lyrics_edit.setMinimumHeight(750)
        self.lyrics_edit.setMaximumHeight(1000)
        self.lyrics_edit.setStyleSheet(f"background-color: {COLORS['bg_input']}; border: 1px solid {COLORS['border']}; border-radius: 4px; padding: 4px;")
        lyrics_layout.addWidget(lyrics_lbl)
        lyrics_layout.addWidget(self.lyrics_edit)
        self.layout.addLayout(lyrics_layout)
        
        self.layout.addStretch()
        
        scroll.setWidget(content_widget)
        
        # Main layout for this panel
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _create_entry(self, placeholder):
        return ModernEntry(placeholder)

    def _wrap_field(self, label_text, widget):
        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(5)
        lbl = QLabel(label_text)
        lbl.setStyleSheet("font-weight: bold;")
        lay.addWidget(lbl)
        lay.addWidget(widget)
        return container

    def _add_field(self, key, label_text):
        entry = self._create_entry(label_text)
        self.entries[key] = entry
        self.layout.addWidget(self._wrap_field(label_text, entry))

    def set_track(self, track: TrackInfo):
        self.current_track = track
        if not track:
            self.info_lbl.setText(t('select_file_hint'))
            for key, entry in self.entries.items():
                entry.blockSignals(True)
                entry.clear()
                entry.blockSignals(False)
            self.lyrics_edit.blockSignals(True)
            self.lyrics_edit.clear()
            self.lyrics_edit.blockSignals(False)
            self.genre_combo.blockSignals(True)
            self.genre_combo.setCurrentIndex(0)
            self.genre_combo.blockSignals(False)
            self.setEnabled(False)
            return
            
        self.setEnabled(True)
        self.info_lbl.setText(f"{track.format_name} • {track.bitrate_str} • {track.sample_rate}Hz")
        
        # Block signals to prevent "Changed" events during loading
        for key, entry in self.entries.items():
            entry.blockSignals(True)
        self.lyrics_edit.blockSignals(True)
        self.genre_combo.blockSignals(True)
        
        self.entries['title'].setText(track.title or "")
        self.entries['artist'].setText(track.artist or "")
        self.entries['album'].setText(track.album or "")
        self.entries['year'].setText(track.year or "")
        # Genre
        if track.genre:
            self.genre_combo.setCurrentText(track.genre)
        else:
            self.genre_combo.setCurrentIndex(0)
            
        self.entries['composer'].setText(track.composer or "")
        self.entries['comment'].setText(track.comment or "")
        
        # Track/Disc - separate fields
        self.entries['track_number'].setText(str(track.track_number) if track.track_number else "")
        self.entries['track_total'].setText(str(track.track_total) if track.track_total else "")
        self.entries['disk_number'].setText(str(track.disc_number) if track.disc_number else "")
        self.entries['disk_total'].setText(str(track.disc_total) if track.disc_total else "")
        
        self.lyrics_edit.setText(track.lyrics or "")
        
        # Unblock
        for key, entry in self.entries.items():
            entry.blockSignals(False)
        self.lyrics_edit.blockSignals(False)
        self.genre_combo.blockSignals(False)
        
        # Load lyrics
        if hasattr(self, 'lyrics_edit'):
            self.lyrics_edit.setPlainText(track.lyrics if track.lyrics else "")

    def get_values(self):
        """Returns dict of current values."""
        values = {k: v.text() for k, v in self.entries.items()}
        values['genre'] = self.genre_combo.currentText()
        if hasattr(self, 'lyrics_edit'):
            values['lyrics'] = self.lyrics_edit.toPlainText()
        return values

    def clear_fields(self):
        for entry in self.entries.values():
            entry.clear()
        self.genre_combo.setCurrentText("")
        if hasattr(self, 'lyrics_edit'):
            self.lyrics_edit.clear()

class FileListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlternatingRowColors(False)
        self.setAlternatingRowColors(False)
        self.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.DragDropMode.DropOnly)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
            
    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            event.ignore()
            
    def dropEvent(self, event):
        files = []
        for url in event.mimeData().urls():
            if url.isLocalFile():
                files.append(url.toLocalFile())
        
        if files:
            # Recursive scan for folders
            final_files = []
            for path in files:
                if os.path.isdir(path):
                    final_files.extend(TagEngine.get_supported_files(path))
                else:
                    final_files.append(path)
            
            if final_files:
                self.files_dropped.emit(final_files)
            

    files_dropped = pyqtSignal(list)

    def add_track(self, track: TrackInfo):
        item = QListWidgetItem(self)
        
        widget = FileListItemWidget(track)
        item.setSizeHint(QSize(widget.sizeHint().width(), 65)) # Height 65px
        
        self.setItemWidget(item, widget)
        # Store track in item data for easy retrieval
        item.setData(Qt.ItemDataRole.UserRole, track) 
        
        return item

class FileListItemWidget(QWidget):
    def __init__(self, track: TrackInfo, parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8) # Equal top/bottom
        
        # Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        # Title
        title_txt = track.title if track.title else track.filename
        if track.track_number:
             title_txt = f"{track.track_number}. {title_txt}"
             
        title_lbl = QLabel(title_txt)
        title_lbl.setStyleSheet("font-weight: bold; font-size: 13px;")
        
        # Subtitle
        sub_txt = f"{track.artist} - {track.album}" if track.artist else track.format_name
        sub_lbl = QLabel(sub_txt)
        sub_lbl.setObjectName("Subtitle")
        
        info_layout.addWidget(title_lbl)
        info_layout.addWidget(sub_lbl)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        dur_lbl = QLabel(track.duration_str)
        # dur_lbl.setObjectName("Muted")
        dur_lbl.setStyleSheet("font-size: 13px; color: #E0E0E0; font-weight: 500;")
        layout.addWidget(dur_lbl)

class BatchEditorPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Panel")
        
        self.checkboxes = {}
        self.entries = {}
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Title
        title = QLabel(t('batch_editor')) # Add batch_editor to t() if needed
        title.setObjectName("Title")
        layout.addWidget(title)
        
        layout.addWidget(title)
        
        desc = QLabel(t('batch_hint'))
        desc.setObjectName("Subtitle")
        layout.addWidget(desc)
        
        # Grid
        grid = QGridLayout()
        grid.setVerticalSpacing(10)
        grid.setHorizontalSpacing(15)
        # Equal column widths for 4 columns
        grid.setColumnStretch(0, 0) # Label
        grid.setColumnStretch(1, 1) # Field
        grid.setColumnStretch(2, 0) # Label
        grid.setColumnStretch(3, 1) # Field
        
        fields = [
            ('artist', t('artist')), ('album', t('album')),
            ('year', t('year')), ('genre', t('genre')),
            ('track_total', t('track_total')), ('disc_number', t('disc_num')),
            ('disc_total', t('disc_total')), ('composer', t('composer'))
        ]
        
        for i, (key, label_text) in enumerate(fields):
            row = i // 2
            col = (i % 2) * 2
            
            # Checkbox
            cb = QCheckBox(label_text)
            cb.setStyleSheet("font-weight: bold; background: transparent;")
            self.checkboxes[key] = cb
            
            # Entry
            if key == 'genre':
                entry = QComboBox()
                entry.setEditable(True)
                entry.addItem("") # Empty default
                entry.addItems(GENRE_PRESETS)
                entry.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
                entry.completer().setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
                entry.completer().setFilterMode(Qt.MatchFlag.MatchContains)
            else:
                entry = ModernEntry()
                
            self.entries[key] = entry
            
            # Enable entry only when checked
            entry.setEnabled(False)
            cb.toggled.connect(entry.setEnabled)
            
            grid.addWidget(cb, row, col)
            grid.addWidget(entry, row, col + 1)
            
        layout.addLayout(grid)
        
        layout.addSpacing(10)
        
        # Auto Number
        self.cb_auto_number = QCheckBox(t('auto_numbering'))
        self.cb_auto_number.setStyleSheet("background: transparent;")
        layout.addWidget(self.cb_auto_number)
        
        # Apply Cover
        self.cb_apply_cover = QCheckBox(t('apply_cover_all'))
        self.cb_apply_cover.setStyleSheet("background: transparent;")
        layout.addWidget(self.cb_apply_cover)
        
        layout.addStretch()

    def get_batch_values(self):
        result = {}
        for key, cb in self.checkboxes.items():
            if cb.isChecked():
                if isinstance(self.entries[key], QComboBox):
                    result[key] = self.entries[key].currentText()
                else:
                    result[key] = self.entries[key].text()
        
        result['auto_number'] = self.cb_auto_number.isChecked()
        result['apply_cover'] = self.cb_apply_cover.isChecked()
        return result

    def clear_values(self):
        for cb in self.checkboxes.values():
            cb.setChecked(False)
        for entry in self.entries.values():
            if isinstance(entry, QLineEdit):
                entry.clear()
            elif isinstance(entry, QComboBox):
                entry.setCurrentText("")
        self.cb_auto_number.setChecked(False)
        self.cb_apply_cover.setChecked(False)
        
class TrimSlider(QSlider):
    sliderPressed = pyqtSignal()
    sliderReleased = pyqtSignal()
    sliderMoved = pyqtSignal(int)

    def __init__(self, orientation=Qt.Orientation.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self.trim_start = 0
        self.trim_end = 0

    def eventFilter(self, obj, event):
        try:
            if obj == self.lbl_cover and event.type() == Qt.Event.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    self.show_full_cover()
                    return True
            return super().eventFilter(obj, event)
        except Exception as e:
            print(f"Error in CoverArtPanel.eventFilter: {e}")
            import traceback
            traceback.print_exc()
            return False

    def mousePressEvent(self, event):
        try:
            if event.button() == Qt.MouseButton.LeftButton:
                opt = QStyleOptionSlider()
                self.initStyleOption(opt)
                style = self.style()
                groove = style.subControlRect(QStyle.ComplexControl.CC_Slider, opt, QStyle.SubControl.SC_SliderGroove, self)
                handle = style.subControlRect(QStyle.ComplexControl.CC_Slider, opt, QStyle.SubControl.SC_SliderHandle, self)
                
                if self.orientation() == Qt.Orientation.Horizontal:
                    sliderLength = handle.width()
                    sliderMin = groove.x()
                    sliderMax = groove.right() - sliderLength + 1
                    pos = event.pos().x() - sliderLength // 2
                    span = sliderMax - sliderMin
                    if span > 0:
                         val = QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), pos - sliderMin, span)
                    else:
                         val = 0
                else:
                    sliderLength = handle.height()
                    sliderMin = groove.y()
                    sliderMax = groove.bottom() - sliderLength + 1
                    pos = event.pos().y() - sliderLength // 2
                    span = sliderMax - sliderMin
                    if span > 0:
                        val = QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), pos - sliderMin, span, True)
                    else:
                        val = 0
                
                self.setValue(val)
                self.setSliderDown(True)
                self.sliderPressed.emit()
                self.sliderReleased.emit()
                event.accept()
            else:
                super().mousePressEvent(event)
        except Exception as e:
            print(f"Error in mousePressEvent: {e}")
            import traceback
            traceback.print_exc()

    def mouseMoveEvent(self, event):
        try:
            if event.buttons() & Qt.MouseButton.LeftButton:
                opt = QStyleOptionSlider()
                self.initStyleOption(opt)
                style = self.style()
                groove = style.subControlRect(QStyle.ComplexControl.CC_Slider, opt, QStyle.SubControl.SC_SliderGroove, self)
                handle = style.subControlRect(QStyle.ComplexControl.CC_Slider, opt, QStyle.SubControl.SC_SliderHandle, self)
                
                if self.orientation() == Qt.Orientation.Horizontal:
                    sliderLength = handle.width()
                    sliderMin = groove.x()
                    sliderMax = groove.right() - sliderLength + 1
                    pos = event.pos().x() - sliderLength // 2
                    span = sliderMax - sliderMin
                    if span > 0:
                         val = QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), pos - sliderMin, span)
                    else:
                         val = 0
                else:
                    sliderLength = handle.height()
                    sliderMin = groove.y()
                    sliderMax = groove.bottom() - sliderLength + 1
                    pos = event.pos().y() - sliderLength // 2
                    span = sliderMax - sliderMin
                    if span > 0:
                        val = QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), pos - sliderMin, span, True)
                    else:
                        val = 0
                
                self.setValue(val)
                self.sliderMoved.emit(val)
                event.accept()
            else:
                super().mouseMoveEvent(event)
        except Exception as e:
            print(f"Error in mouseMoveEvent: {e}")
            import traceback
            traceback.print_exc()

    def mouseReleaseEvent(self, event):
        try:
            if self.isSliderDown():
                self.setSliderDown(False)
                self.sliderReleased.emit()
                event.accept()
            else:
                super().mouseReleaseEvent(event)
        except Exception as e:
            print(f"Error in mouseReleaseEvent: {e}")
            import traceback
            traceback.print_exc()
        
    def set_trim_mark(self, start, end):
        self.trim_start = start
        self.trim_end = end
        self.update() # Trigger repaint
        
    def paintEvent(self, event):
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        dur = self.maximum()
        if dur <= 0:
            return
            
        width = self.width()
        h = self.height()
        
        # Draw start marker line (green)
        if self.trim_start > 0:
            x1 = int((self.trim_start / dur) * width)
            painter.setPen(QColor('#4CAF50'))  # Green
            painter.drawLine(x1, 4, x1, h - 4)
            
        # Draw end marker line (red)
        if self.trim_end > 0:
            x2 = int((self.trim_end / dur) * width)
            painter.setPen(QColor('#F44336'))  # Red
            painter.drawLine(x2, 4, x2, h - 4)
        
        # Draw range overlay if both are set
        if self.trim_end > self.trim_start:
            x1 = int((self.trim_start / dur) * width)
            x2 = int((self.trim_end / dur) * width)
            w = x2 - x1
            
            # Use semi-transparent accent color
            c = QColor(COLORS['accent'])
            c.setAlpha(80)
            painter.setBrush(QBrush(c))
            painter.setPen(Qt.PenStyle.NoPen)
            
            # Draw over the groove (approx height 6px centered)
            groove_h = 8
            y = (h - groove_h) // 2
            painter.drawRoundedRect(x1, y, w, groove_h, 2, 2)

from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout

class TrimSaveDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t('save_trim'))
        self.resize(300, 150)
        
        layout = QVBoxLayout(self)
        
        from converter_engine import CONVERTER_FORMATS, ConverterEngine
        self.engine = ConverterEngine()
        
        # Form
        form = QFormLayout()
        
        # Format
        self.combo_format = QComboBox()
        self.formats = sorted([f.upper() for f in CONVERTER_FORMATS.keys()])
        self.combo_format.addItems(self.formats)
        self.combo_format.currentTextChanged.connect(self._update_quality)
        form.addRow(t('format'), self.combo_format)
        
        # Quality
        self.combo_quality = QComboBox()
        form.addRow(t('quality'), self.combo_quality)
        
        layout.addLayout(form)
        
        # Buttons
        btns_layout = QHBoxLayout()
        btns_layout.addStretch()
        
        from ui_utils_qt import HoverButton, animate_dialog
        self.btn_ok = HoverButton(t('ok', 'OK'))
        self.btn_cancel = HoverButton(t('cancel', 'Cancel'))
        
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        
        btns_layout.addWidget(self.btn_ok)
        btns_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(btns_layout)
        
        # Init quality
        self._update_quality(self.combo_format.currentText())
        
        # Center on parent
        if parent:
            geo = self.geometry()
            geo.moveCenter(parent.geometry().center())
            self.setGeometry(geo)
            
    def showEvent(self, event):
        from ui_utils_qt import animate_dialog
        animate_dialog(self)
        super().showEvent(event)
            
    def _update_quality(self, fmt_text):
        self.combo_quality.clear()
        # Use UPPERCASE key for get_presets
        fmt_key = fmt_text.upper()
        presets = self.engine.get_presets(fmt_key)
        self.combo_quality.addItems(list(presets.keys()))
        
    def get_values(self):
        return self.combo_format.currentText().lower(), self.combo_quality.currentText()
