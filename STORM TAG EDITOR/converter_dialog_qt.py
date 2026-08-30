
import os
import threading
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QLineEdit, QPushButton, QProgressBar, QTextEdit, 
    QFileDialog, QMessageBox, QFrame, QSizePolicy, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

from ui_utils_qt import COLORS
from converter_engine import ConverterEngine, CONVERTER_FORMATS

from localization import t

class DropLineEdit(QLineEdit):
    """QLineEdit that accepts folder drops."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)
            
    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                path = urls[0].toLocalFile()
                if os.path.isdir(path):
                    self.setText(path)
                    event.acceptProposedAction()
                    # Trigger editingFinished or similar if needed, 
                    # but mostly just setting text is checked by parent via text()
                else:
                    # If file, get dirname?
                    self.setText(os.path.dirname(path))
                    event.acceptProposedAction()
        else:
            super().dropEvent(event)


class ConverterDialog(QDialog):
    sig_progress = pyqtSignal(int)
    sig_status = pyqtSignal(str)
    sig_finished = pyqtSignal(int, int)

    def __init__(self, parent, files):
        super().__init__(parent)
        self.files = files
        self.engine = ConverterEngine()
        
        self.setWindowTitle(t('converter_title'))
        self.resize(700, 550)
        
        self.is_custom_output = False
        self.stop_conversion = False
        
        self._init_ui()
        self._update_quality_options()
        
        # Connect signals
        self.sig_progress.connect(self._update_progress_ui)
        self.sig_status.connect(self._update_status_ui)
        self.sig_finished.connect(self._finish_conversion_ui)
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Files Section
        layout.addWidget(QLabel(f"{t('source_files')} ({len(self.files)})"))
        
        self.file_list = QTextEdit()
        self.file_list.setReadOnly(True)
        self.file_list.setPlainText("\n".join([os.path.basename(f) for f in self.files]))
        layout.addWidget(self.file_list)
        
        # Settings Frame
        settings_frame = QFrame()
        settings_frame.setObjectName("Panel")
        s_layout = QVBoxLayout(settings_frame)
        
        # Format/Quality Row
        row1 = QHBoxLayout()
        
        self.format_combo = QComboBox()
        self.format_combo.setMinimumWidth(250)
        self.format_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.format_combo.addItems(sorted(CONVERTER_FORMATS.keys()))
        self.format_combo.currentTextChanged.connect(self._update_quality_options)
        
        self.quality_combo = QComboBox()
        self.quality_combo.setMinimumWidth(400)
        self.quality_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        row1.addWidget(QLabel(t('format') + ":"))
        row1.addWidget(self.format_combo)
        row1.addWidget(QLabel(t('quality') + ":"))
        row1.addWidget(self.quality_combo)
        
        s_layout.addLayout(row1)
        
        # Output Row
        row2 = QHBoxLayout()
        self.output_entry = DropLineEdit(t('same_as_source'))
        # Connect textChanged to detect if user dropped or typed
        self.output_entry.textChanged.connect(self._on_output_changed)
        
        # self.output_entry.setReadOnly(True) # Allow typing if they really want
        self.btn_browse = QPushButton(t('browse'))
        self.btn_browse.clicked.connect(self._browse_output)
        
        row2.addWidget(QLabel(t('output_folder') + ":"))
        row2.addWidget(self.output_entry)
        row2.addWidget(self.btn_browse)
        
        s_layout.addLayout(row2)
        
        # Studio Processing Checkbox
        row3 = QHBoxLayout()
        self.cb_studio = QCheckBox(t('studio_processing'))
        # Style: Green text and green indicator
        self.cb_studio.setStyleSheet("""
            QCheckBox { color: #2CC985; font-weight: bold; font-size: 13px; }
            QCheckBox::indicator:checked { background-color: #2CC985; border: 1px solid #2CC985; }
        """)
        self.cb_studio.setToolTip(t('studio_processing_desc'))
        row3.addWidget(self.cb_studio)
        row3.addStretch()
        
        s_layout.addLayout(row3)
        
        layout.addWidget(settings_frame)
        
        # Progress
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel(t('ready'))
        self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(self.status_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_convert = QPushButton(t('convert'))
        self.btn_convert.setObjectName("AccentButton")
        self.btn_convert.clicked.connect(self._start_conversion)
        
        self.btn_cancel = QPushButton(t('close'))
        self.btn_cancel.clicked.connect(self._on_cancel)
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_convert)
        
        layout.addLayout(btn_layout)
        
        # Check FFMPEG
        if not self.engine.check_ffmpeg():
             self.status_label.setText("FFmpeg not found! Conversion disabled.")
             self.status_label.setStyleSheet(f"color: {COLORS['error']};")
             self.btn_convert.setEnabled(False)

    def _update_quality_options(self):
        fmt = self.format_combo.currentText()
        presets = self.engine.get_presets(fmt)
        self.quality_values = presets
        self.quality_combo.clear()
        self.quality_combo.addItems(list(presets.keys()))

    def _browse_output(self):
        path = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if path:
            self.output_entry.setText(path)
            self.is_custom_output = True

    def _on_output_changed(self, text):
        if text != t('same_as_source'):
            self.is_custom_output = True
        else:
            self.is_custom_output = False

    def _toggle_inputs(self, enable):
        self.format_combo.setEnabled(enable)
        self.quality_combo.setEnabled(enable)
        self.output_entry.setEnabled(enable)
        self.btn_browse.setEnabled(enable)
        self.cb_studio.setEnabled(enable)
        self.btn_convert.setEnabled(enable)
        self.btn_cancel.setText(t('stop') if not enable else t('close'))

    def _on_cancel(self):
        if self.engine.is_converting:
            self.stop_conversion = True
            self.status_label.setText("Stopping...")
        else:
            self.reject()

    def _start_conversion(self):
        self.stop_conversion = False
        self.engine.is_converting = True
        self._toggle_inputs(False)
        self.progress_bar.setValue(0)
        
        fmt = self.format_combo.currentText()
        quality = self.quality_combo.currentText()
        quality_args = self.quality_values.get(quality, '')
        out_folder = self.output_entry.text() if self.is_custom_output else None
        
        studio_processing = self.cb_studio.isChecked()
        
        threading.Thread(
            target=self._run_conversion,
            args=(fmt, quality_args, out_folder, studio_processing),
            daemon=True
        ).start()

    def _run_conversion(self, fmt, quality_args, out_folder, studio_processing):
        total = len(self.files)
        success_count = 0
        ext = CONVERTER_FORMATS.get(fmt, '.mp3')
        
        for i, input_path in enumerate(self.files):
            if self.stop_conversion:
                break
                
            fname = os.path.basename(input_path)
            
            # Use signals for UI updates
            self.sig_status.emit(f"Converting {fname} ({i+1}/{total})")
            
            if out_folder:
                if not os.path.exists(out_folder):
                    os.makedirs(out_folder)
                output_path = os.path.join(out_folder, os.path.splitext(fname)[0] + ext)
            else:
                output_path = os.path.splitext(input_path)[0] + ext
                
            res = self.engine.convert_file(input_path, output_path, quality_args, studio_processing)
            
            if res:
                success_count += 1
            
            # Progress
            prog = int(((i + 1) / total) * 100)
            self.sig_progress.emit(prog)
            
        self.engine.is_converting = False
        self.sig_finished.emit(success_count, total)

    # Slots for signals
    def _update_status_ui(self, text):
        self.status_label.setText(text)

    def _update_progress_ui(self, val):
        self.progress_bar.setValue(val)

    def _finish_conversion_ui(self, success, total):
        self._toggle_inputs(True)
        if self.stop_conversion:
            self.status_label.setText("Cancelled")
        else:
            if success == total:
                self.status_label.setText("Conversion Complete!")
                QMessageBox.information(self, t('success'), t('converted_files').format(success))
            else:
                self.status_label.setText(f"Completed with errors ({success}/{total})")
