import os
import subprocess
import wave
import numpy as np
import tempfile
import math

class AudioAnalyzer:
    """
    Analyzes audio files to provide frequency (FFT) and waveform data
    synchronized with playback position.
    """
    def __init__(self):
        self.current_file = None
        self.wave_data = None
        self.sample_rate = 22050
        self.n_fft = 1024
        self.hop_length = 512
        self.duration = 0
        self.channels = 1
        
        # Temp file for converted WAV
        self.temp_wav = os.path.join(tempfile.gettempdir(), "storm_viz_temp.wav")

    def load(self, file_path):
        """Converts input file to a temporary mono WAV for analysis."""
        if not os.path.exists(file_path):
            return False
            
        self.current_file = file_path
        
        # Convert to specific WAV format: 22050Hz, Mono, 16-bit PCM
        # This standardizes analysis regardless of input format.
        cmd = [
            'ffmpeg.exe', '-y',
            '-i', file_path,
            '-ac', '1',          # Mono
            '-ar', str(self.sample_rate), # 22050 Hz
            '-f', 'wav',
            self.temp_wav
        ]
        
        try:
            # Hide console
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            subprocess.run(cmd, capture_output=True, startupinfo=startupinfo)
            
            # Read WAV data
            with wave.open(self.temp_wav, 'rb') as wf:
                self.channels = wf.getnchannels()
                self.sample_width = wf.getsampwidth()
                self.frames = wf.getnframes()
                self.duration = self.frames / self.sample_rate
                
                raw_data = wf.readframes(self.frames)
                
                # Convert to numpy array (int16)
                self.wave_data = np.frombuffer(raw_data, dtype=np.int16)
                
                # Normalize to -1.0 to 1.0 (optional, but keep as int16 for now and normalize on fly)
                # self.wave_data = self.wave_data.astype(np.float32) / 32768.0
                
            return True
            
        except Exception as e:
            print(f"Audio Analysis Error: {e}")
            self.wave_data = None
            return False

    def get_data(self, position_ms):
        """
        Returns (fft_data, waveform_data) for the current position.
        position_ms: Current playback position in milliseconds
        """
        if self.wave_data is None:
            return None, None
            
        # Calculate sample index
        # position_ms / 1000 = seconds
        # seconds * sample_rate = sample_index
        center_idx = int((position_ms / 1000.0) * self.sample_rate)
        
        # Define window size
        window_size = self.n_fft
        start_idx = center_idx - window_size // 2
        end_idx = center_idx + window_size // 2
        
        # Handle boundary conditions
        if start_idx < 0:
            # Pad beginning with zeros
            chunk = np.concatenate((np.zeros(-start_idx, dtype=np.int16), self.wave_data[:end_idx]))
        elif end_idx > len(self.wave_data):
            # Pad end with zeros
            chunk = np.concatenate((self.wave_data[start_idx:], np.zeros(end_idx - len(self.wave_data), dtype=np.int16)))
        else:
            chunk = self.wave_data[start_idx:end_idx]
            
        # Ensure chunk is correct size (might be off if file is tiny)
        if len(chunk) != window_size:
            chunk = np.zeros(window_size, dtype=np.int16)

        # Apply Hanning window to smooth edges
        window = np.hanning(window_size)
        windowed_chunk = chunk * window
        
        # FFT
        fft_complex = np.fft.rfft(windowed_chunk)
        fft_mag = np.abs(fft_complex)
        
        # Normalize FFT (logarithmic scale usually looks better for audio)
        # Log scale: 20 * log10(amplitude)
        with np.errstate(divide='ignore'):
             fft_db = 20 * np.log10(fft_mag + 1e-9)
        
        # Clip to a range (e.g., -80dB to 0dB, then scale to 0-255)
        # Assuming int16 input, max val is ~32768. log10(32768) ~ 4.5. 20*4.5 = 90dB.
        # So range is roughly 0 to 90.
        
        fft_normalized = np.clip((fft_db - 10) / 80.0, 0, 1) * 255.0
        
        # Waveform for visualization (raw chunk)
        # Normalize int16 (-32768 to 32767) to -1.0 to 1.0, then scale to height in widget
        waveform_normalized = chunk / 32768.0
        
        return fft_normalized.astype(np.uint8), waveform_normalized

    def cleanup(self):
        if os.path.exists(self.temp_wav):
            try:
                os.remove(self.temp_wav)
            except:
                pass
