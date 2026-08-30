import sys
import os
import json
import time
import urllib.request
import subprocess
from PyQt6.QtCore import QObject, pyqtSignal, QThread, Qt, QUrl
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QProgressBar, QTextBrowser, QPushButton, QMessageBox, QFrame, QWidget
)
from PyQt6.QtGui import QIcon
from localization import t

# Configuration
GITHUB_REPO = "ReiKatari/STORM_TAG_EDITOR"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
CACHE_FILE = "update_cache.json"
CACHE_DURATION = 3600 # 1 hour

class UpdateWorker(QThread):
    """Worker thread for checking updates."""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, current_version):
        super().__init__()
        self.current_version = current_version

    def run(self):
        try:
            # Check cache first
            if os.path.exists(CACHE_FILE):
                try:
                    with open(CACHE_FILE, 'r') as f:
                        cache = json.load(f)
                        last_check = cache.get('last_check', 0)
                        if time.time() - last_check < CACHE_DURATION:
                            cached_result = cache.get('result')
                            if cached_result:
                                self.finished.emit(cached_result)
                                return
                except:
                    pass

            # API Request
            req = urllib.request.Request(
                GITHUB_API_URL,
                headers={'User-Agent': 'StormTagEditor'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            latest_version = data.get('tag_name', '').lstrip('v').strip()
            
            if self._is_newer(latest_version, self.current_version):
                # Find asset
                assets = data.get('assets', [])
                download_url = None
                asset_name = ""
                
                for asset in assets:
                    name = asset.get('name', '')
                    if name.lower().endswith('.exe'):
                        download_url = asset.get('browser_download_url')
                        asset_name = name
                        break
                
                if download_url:
                    result = {
                        'version': latest_version,
                        'url': download_url,
                        'name': asset_name,
                        'body': data.get('body', '')
                    }
                    
                    # Update cache
                    try:
                        with open(CACHE_FILE, 'w') as f:
                            json.dump({'last_check': time.time(), 'result': result}, f)
                    except:
                        pass
                        
                    self.finished.emit(result)
                    return

            # No update or no asset
            self.finished.emit({})
            
        except Exception as e:
            self.error.emit(str(e))

    def _is_newer(self, latest, current):
        try:
            l_parts = [int(x) for x in latest.split('.')]
            c_parts = [int(x) for x in current.split('.')]
            return l_parts > c_parts
        except:
            return False

class DownloadWorker(QThread):
    """Worker for downloading update."""
    progress = pyqtSignal(int)
    finished = pyqtSignal(str) # path
    error = pyqtSignal(str)
    
    def __init__(self, url, dest_path):
        super().__init__()
        self.url = url
        self.dest_path = dest_path
        self._is_running = True
        
    def run(self):
        try:
            req = urllib.request.Request(self.url, headers={'User-Agent': 'StormTagEditor'})
            with urllib.request.urlopen(req, timeout=60) as response:
                total_size = int(response.headers.get('Content-Length', 0))
                downloaded = 0
                block_size = 8192
                
                with open(self.dest_path, 'wb') as f:
                    while self._is_running:
                        buffer = response.read(block_size)
                        if not buffer:
                            break
                        f.write(buffer)
                        downloaded += len(buffer)
                        if total_size > 0:
                            percent = int((downloaded / total_size) * 100)
                            self.progress.emit(percent)
                            
            if self._is_running:
                self.finished.emit(self.dest_path)
            else:
                os.remove(self.dest_path)
                
        except Exception as e:
            self.error.emit(str(e))
            
    def stop(self):
        self._is_running = False


class UpdateDialog(QDialog):
    """Dialog showing update info and progress."""
    def __init__(self, parent, release_info, current_version):
        super().__init__(parent)
        self.info = release_info
        self.setWindowTitle(t('update_available'))
        self.setFixedSize(500, 400) # Ensure size is appropriate
        
        # Center on parent if available
        if parent:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.Dialog)
            # Center logic:
            geo = self.geometry()
            geo.moveCenter(parent.geometry().center())
            self.setGeometry(geo)
        
        layout = QVBoxLayout(self)
        
        # Header
        lbl_title = QLabel(t('new_version_available'))
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #22c55e;")
        layout.addWidget(lbl_title)
        
        # Versions
        v_layout = QHBoxLayout()
        v_layout.addWidget(QLabel(f"{t('current_version')}: {current_version}"))
        v_layout.addStretch()
        v_layout.addWidget(QLabel(f"{t('new_version')}: {release_info['version']}"))
        layout.addLayout(v_layout)
        
        # Changelog
        self.txt_log = QTextBrowser()
        self.txt_log.setMarkdown(release_info['body'])
        self.txt_log.setStyleSheet("background-color: #242424; border: 1px solid #333; padding: 5px;")
        layout.addWidget(self.txt_log)
        
        # Progress (Hidden initially)
        self.prog_bar = QProgressBar()
        self.prog_bar.setVisible(False)
        layout.addWidget(self.prog_bar)
        
        self.lbl_status = QLabel("")
        layout.addWidget(self.lbl_status)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_later = QPushButton(t('later'))
        self.btn_later.clicked.connect(self.reject)
        
        self.btn_update = QPushButton(t('update_btn'))
        self.btn_update.setStyleSheet("background-color: #6366f1; color: white; padding: 6px 12px; font-weight: bold;")
        self.btn_update.clicked.connect(self.start_update)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_later)
        btn_layout.addWidget(self.btn_update)
        layout.addLayout(btn_layout)
        
        self.download_worker = None
        
    def start_update(self):
        self.btn_update.setEnabled(False)
        self.btn_later.setEnabled(False)
        self.prog_bar.setVisible(True)
        self.prog_bar.setValue(0)
        self.lbl_status.setText(t('downloading').format(0))
        
        # Download to temp
        temp_dir = os.environ.get('TEMP', '.')
        dest = os.path.join(temp_dir, self.info['name'])
        
        self.download_worker = DownloadWorker(self.info['url'], dest)
        self.download_worker.progress.connect(self._on_progress)
        self.download_worker.finished.connect(self._on_download_finished)
        self.download_worker.error.connect(self._on_error)
        self.download_worker.start()
        
    def _on_progress(self, percent):
        self.prog_bar.setValue(percent)
        self.lbl_status.setText(t('downloading').format(percent))
        
    def _on_download_finished(self, path):
        self.lbl_status.setText(t('applying_update'))
        self.accept()
        # Launch updater script
        UpdateManager.apply_update(path)
        
    def _on_error(self, msg):
        self.lbl_status.setText(t('download_error'))
        QMessageBox.critical(self, t('error'), f"{t('download_error')}\n{msg}")
        self.btn_update.setEnabled(True)
        self.btn_later.setEnabled(True)
        
    def closeEvent(self, event):
        if self.download_worker and self.download_worker.isRunning():
            self.download_worker.stop()
            self.download_worker.wait()
        super().closeEvent(event)


class UpdateManager(QObject):
    """Manages update check and application."""
    
    def __init__(self, parent=None, current_version="1.0.0"):
        super().__init__(parent)
        self.current_version = current_version
        self.worker = None
        
    def check_for_updates(self, silent=True):
        """Start check."""
        if self.worker and self.worker.isRunning():
            return
            
        self.silent = silent
        self.worker = UpdateWorker(self.current_version)
        self.worker.finished.connect(self._on_check_finished)
        self.worker.error.connect(self._on_check_error)
        self.worker.start()
        
    def _on_check_finished(self, result):
        if not result:
            if not self.silent:
                QMessageBox.information(None, t('info'), t('no_update_found', "No updates available.")) # localized string might need fallback
            return
            
        # Show dialog
        dlg = UpdateDialog(self.parent(), result, self.current_version)
        dlg.exec()
        
    def _on_check_error(self, msg):
        if not self.silent:
            QMessageBox.warning(None, t('error'), f"Update check failed: {msg}")

    @staticmethod
    def apply_update(new_file_path):
        """Generate batch script and restart."""
        exe_path = sys.executable
        cwd = os.path.dirname(exe_path)
        pid = os.getpid()
        
        # Batch script
        bat_content = f"""
@echo off
timeout /t 2 /nobreak >nul
taskkill /PID {pid} /F >nul 2>&1
:loop
del "{exe_path}" >nul 2>&1
if exist "{exe_path}" goto loop
move /y "{new_file_path}" "{exe_path}"
set _MEIPASS2=
set PYTHONHOME=
set PYTHONPATH=
start "" "{exe_path}"
del "%~f0"
"""
        bat_path = os.path.join(cwd, "updater.bat")
        with open(bat_path, "w") as f:
            f.write(bat_content)
            
        # Run batch
        subprocess.Popen([bat_path], shell=True)
        sys.exit(0)
