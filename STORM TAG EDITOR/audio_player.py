
import os
import subprocess
from PyQt6.QtCore import QObject, pyqtSignal, QUrl, QTimer
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

class AudioPlayer(QObject):
    """
    Manages audio playback and trimming operations.
    Signals:
        position_changed(int): Current position in ms
        duration_changed(int): Total duration in ms
        state_changed(QMediaPlayer.PlaybackState): Play/Pause/Stop
        error_occurred(str): Error message
    """
    position_changed = pyqtSignal(int)
    duration_changed = pyqtSignal(int)
    state_changed = pyqtSignal(int) # QMediaPlayer.PlaybackState
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        
        self.current_file = ""
        
        # Connect signals
        # Connect signals
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.playbackStateChanged.connect(self._on_state_changed)
        self.player.errorOccurred.connect(self._handle_error)

    def _on_position_changed(self, pos):
        self.position_changed.emit(pos)

    def _on_duration_changed(self, dur):
        self.duration_changed.emit(dur)

    def _on_state_changed(self, state):
        self.state_changed.emit(state.value)

    def load(self, file_path):
        if not os.path.exists(file_path):
            self.error_occurred.emit(f"File not found: {file_path}")
            return
            
        self.current_file = file_path
        self.player.setSource(QUrl.fromLocalFile(file_path))
        self.audio_output.setVolume(1.0) # Default full volume

    def play(self):
        self.player.play()

    def pause(self):
        self.player.pause()

    def stop(self):
        self.player.stop()

    def set_position(self, position_ms):
        self.player.setPosition(position_ms)

    def get_duration(self):
        return self.player.duration()

    def get_position(self):
        return self.player.position()

    def _handle_error(self):
        err = self.player.errorString()
        self.error_occurred.emit(f"Playback Error: {err}")

    def trim_audio(self, start_ms, end_ms, output_path, encode_args="-c copy"):
        """
        Trims the current audio file using ffmpeg.
        start_ms, end_ms: Time in milliseconds
        encode_args: list of str or str for ffmpeg encoding (e.g. "-c:a libmp3lame -q:a 2")
        """
        if not self.current_file:
            return False, "No file loaded"
            
        if start_ms >= end_ms:
            return False, "Start time must be before end time"
            
        # Convert ms to seconds
        start_sec = start_ms / 1000.0
        end_sec = end_ms / 1000.0
        duration = end_sec - start_sec
        
        # Prepare encoding args
        if isinstance(encode_args, str):
            enc_list = encode_args.split()
        else:
            enc_list = encode_args
        
        # FFmpeg command
        cmd = [
            'ffmpeg.exe',
            '-y', # Overwrite
            '-ss', f"{start_sec:.3f}",
            '-t', f"{duration:.3f}",
            '-i', self.current_file
        ]
        
        # Add encoding args
        cmd.extend(enc_list)
        
        cmd.append(output_path)
        
        try:
            # Hide console window
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                startupinfo=startupinfo
            )
            
            if process.returncode == 0:
                return True, "Success"
            else:
                return False, f"FFmpeg Error: {process.stderr}"
                
        except FileNotFoundError:
            return False, "ffmpeg.exe not found"
        except Exception as e:
            return False, str(e)

    def apply_filter(self, input_path, output_path, filter_str):
        """Apply ffmpeg filter and save to output."""
        if not input_path or not os.path.exists(input_path):
            return False, "Input not found"
            
        cmd = [
            'ffmpeg.exe', '-y',
            '-i', input_path,
            '-af', filter_str,
            output_path
        ]
        
        try:
            # Hide console window
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                startupinfo=startupinfo
            )
            
            if process.returncode == 0:
                return True, ""
            else:
                return False, f"FFmpeg Error: {process.stderr}"
        except Exception as e:
            return False, str(e)
