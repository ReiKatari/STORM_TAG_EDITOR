"""
Storm Tag Editor - Converter Engine
Handles audio conversion using FFMPEG.
"""

import os
import subprocess
import threading
import json
from typing import Optional, List, Dict, Callable
from pathlib import Path

# Supported formats and their extensions
CONVERTER_FORMATS = {
    'MP3': '.mp3',
    'FLAC': '.flac',
    'WAV': '.wav',
    'OGG': '.ogg',
    'M4A': '.m4a',
    'ALAC': '.m4a',
    'AIFF': '.aiff',
    'APE': '.ape',
    'WV': '.wv',
    'TTA': '.tta'
}

class ConverterEngine:
    """Engine for converting audio files using FFMPEG."""
    
    def __init__(self):
        self.ffmpeg_path = self._find_ffmpeg()
        self.is_converting = False
        self.stop_flag = False
    
    def _find_ffmpeg(self) -> Optional[str]:
        """Find FFMPEG executable in path or local folder."""
        # Check local folder first
        local_ffmpeg = os.path.join(os.path.dirname(__file__), 'ffmpeg.exe')
        if os.path.exists(local_ffmpeg):
            return local_ffmpeg
            
        # Check system path
        try:
            subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return 'ffmpeg'
        except FileNotFoundError:
            return None

    def get_presets(self, format_name: str) -> Dict[str, str]:
        """Get quality presets for a format."""
        presets = {}
        if format_name == 'MP3':
            presets = {
                'Best (320kbps)': '-b:a 320k',
                'High (256kbps)': '-b:a 256k',
                'Medium (192kbps)': '-b:a 192k',
                'VBR High (V0)': '-q:a 0',
                'VBR Standard (V2)': '-q:a 2'
            }
        elif format_name == 'FLAC':
            presets = {
                'Maximum Compression (8)': '-compression_level 8',
                'Standard Compression (5)': '-compression_level 5',
                'Fast Compression (1)': '-compression_level 1'
            }
        elif format_name == 'OGG':
            presets = {
                'Best (Q10)': '-q:a 10',
                'High (Q7)': '-q:a 7',
                'Standard (Q5)': '-q:a 5',
                'Low (Q3)': '-q:a 3'
            }
        elif format_name == 'M4A': # AAC
            presets = {
                'Best (320kbps)': '-c:a aac -b:a 320k',
                'High (256kbps)': '-c:a aac -b:a 256k',
                'Standard (192kbps)': '-c:a aac -b:a 192k'
            }
        elif format_name == 'ALAC':
            presets = {
                'Lossless': '-c:a alac'
            }
        elif format_name == 'WAV' or format_name == 'AIFF':
            presets = {
                'CD Quality (16-bit)': '-sample_fmt s16',
                'High Res (24-bit)': '-sample_fmt s24',
                'Studio (32-bit float)': '-sample_fmt f32'
            }
        elif format_name == 'APE':
            presets = {
                'High Compression': '-c:a ape -compression_level 3000',
                'Standard': '-c:a ape -compression_level 2000',
                'Fast': '-c:a ape -compression_level 1000'
            }
        elif format_name == 'WV':
            presets = {
                'Best Compression': '-c:a wavpack -compression_level 3',
                'Standard': '-c:a wavpack -compression_level 1',
                'Fast': '-c:a wavpack -compression_level 0'
            }
        elif format_name == 'TTA':
            presets = {
                'Lossless': '-c:a tta'
            }
            
        return presets

    def convert_file(self, input_path: str, output_path: str, format_args: str, 
                    studio_processing: bool = False,
                    on_progress: Callable[[float], None] = None) -> bool:
        """Convert a single file."""
        if not self.ffmpeg_path:
            return False
            
        try:
            cmd = [
                self.ffmpeg_path,
                '-y',  # Overwrite output
                '-i', input_path,
                '-map_metadata', '0',  # Copy global metadata
                '-id3v2_version', '3', # Ensure ID3v2.3 for MP3 compatibility
            ]
            
            # Add format arguments
            cmd.extend(format_args.split())

            # Studio Processing Filters
            if studio_processing:
                # Filters explanation:
                # 1. highpass=f=50: Remove sub-bass muck.
                # 2. bass=g=3, treble=g=4: EQ for color.
                # 3. acompressor: Adds density and saturation ("Studio Sound") - fixes pumping by leveling fast.
                # 4. alimiter: Prevents clipping.
                # No dynamic normalization (dynaudnorm/loudnorm) to avoid "floating" volume.
                filters = "highpass=f=50,bass=g=3,treble=g=4,acompressor=threshold=-12dB:ratio=2:attack=5:release=50,alimiter=limit=0.98"
                cmd.extend(['-af', filters])
            
            cmd.append(output_path)
            
            # Run conversion
            # Using startupinfo to hide console window on Windows
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=startupinfo
            )
            
            # Wait for completion (TODO: parse progress from stderr for detailed bar)
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                print(f"Conversion error: {stderr.decode('utf-8', errors='ignore')}")
                return False
                
            return True
            
        except Exception as e:
            print(f"Conversion exception: {e}")
            return False

    def check_ffmpeg(self) -> bool:
        return self.ffmpeg_path is not None
