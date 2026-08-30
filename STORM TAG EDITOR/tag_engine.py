"""
Storm Tag Editor - Tag Engine Module
Handles reading and writing audio file metadata using mutagen library.
Supports MP3 (ID3), FLAC, M4A, and OGG formats.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, List, Tuple
from pathlib import Path
import io

from mutagen import File as MutagenFile
from mutagen.mp3 import MP3
from mutagen.flac import FLAC, Picture
from mutagen.mp4 import MP4, MP4Cover
from mutagen.oggvorbis import OggVorbis
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, TDRC, TCON, TRCK, TPOS, TCOM, COMM, USLT
from PIL import Image

SUPPORTED_EXTENSIONS = {'.mp3', '.flac', '.m4a', '.ogg', '.oga', '.wav'}

GENRE_PRESETS = [
    "Acoustic", "Acoustic Gothic Ballad", "Alternative", "Alternative Rock", "Ambient",
    "Black Metal", "Blues", "Breakbeat", "Brit Pop", "Chillout", "Chiptune",
    "Cinematic Modern Gothic", "Classical", "Country", "Dance", "Darkwave", 
    "Death Metal", "Deathcore", "Deep House", "Disco", "Doom Metal", "Dream Pop",
    "Drum & Bass", "Dubstep", "Electro", "Electronic", "Emo", "Ethno", 
    "Experimental", "Folk", "Folk Metal", "Funk", "Garage", "Glitch", "Gothic", 
    "Gothic Rap", "Gothic Rock", "Grindcore", "Grunge", "Hardcore", "Hard Rock",
    "Heavy Metal", "Hip-Hop", "House", "IDM", "Indie", "Indie Pop", "Indie Rock",
    "Industrial", "J-Pop", "J-Rock", "Jazz", "Jungle", "K-Pop", "Latin", "Lo-Fi",
    "Math Rock", "Melodic Death Metal", "Metal", "Metalcore", "Minimal", "New Age",
    "New Wave", "Noise", "Nu-Metal", "Opera", "Orchestral", "Pop", "Pop Rock",
    "Post-Hardcore", "Post-Metal", "Post-Punk", "Post-Rock", "Power Metal",
    "Progressive Metal", "Progressive Rock", "Psychedelic", "Punk", "Punk Rock",
    "R&B", "Rap", "Reggae", "Reggaeton", "Rock", "Shoegaze", "Ska", "Slowcore",
    "Soul", "Soundtrack", "Space Rock", "Speed Metal", "Stoner Rock",
    "Symphonic Gothic Metal", "Symphonic Metal", "Synth Pop", "Synthwave",
    "Tech House", "Techno", "Thrash Metal", "Trance", "Trip-Hop", "Vapor Wave",
    "Visual Kei", "Witch House", "World"
]


@dataclass
class TrackInfo:
    """Data model for a single audio track."""
    file_path: str
    title: str = ""
    artist: str = ""
    album: str = ""
    year: str = ""
    genre: str = ""
    track_number: str = ""
    track_total: str = ""
    disc_number: str = ""
    disc_total: str = ""
    composer: str = ""
    comment: str = ""
    lyrics: str = ""  # Lyrics (USLT for MP3, LYRICS for FLAC)
    cover_data: Optional[bytes] = field(default=None, repr=False)
    cover_mime: str = "image/jpeg"
    
    # Read-only info
    duration: float = 0.0
    bitrate: int = 0
    sample_rate: int = 0
    channels: int = 0
    format_name: str = ""
    
    @property
    def filename(self) -> str:
        return os.path.basename(self.file_path)
    
    @property
    def duration_str(self) -> str:
        mins, secs = divmod(int(self.duration), 60)
        return f"{mins}:{secs:02d}"
    
    @property
    def bitrate_str(self) -> str:
        return f"{self.bitrate} kbps" if self.bitrate else "N/A"
    
    @property
    def quality_str(self) -> str:
        return f"{self.bitrate_str} • {self.sample_rate}Hz • {'Stereo' if self.channels == 2 else 'Mono'}"


class TagEngine:
    """Engine for reading and writing audio file tags."""
    
    @staticmethod
    def is_supported(file_path: str) -> bool:
        """Check if the file format is supported."""
        ext = Path(file_path).suffix.lower()
        return ext in SUPPORTED_EXTENSIONS
    
    @staticmethod
    def get_supported_files(folder_path: str) -> List[str]:
        """Get all supported audio files from a folder recursively."""
        files = []
        for root, dirs, filenames in os.walk(folder_path):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                if TagEngine.is_supported(file_path):
                    files.append(file_path)
        return sorted(files)
    
    @staticmethod
    def read_tags(file_path: str) -> Optional[TrackInfo]:
        """Read tags from an audio file."""
        if not os.path.exists(file_path):
            return None
        
        try:
            audio = MutagenFile(file_path)
            if audio is None:
                return None
            
            ext = Path(file_path).suffix.lower()
            
            track = None
            if ext == '.mp3':
                track = TagEngine._read_mp3(file_path, audio)
            elif ext == '.flac':
                track = TagEngine._read_flac(file_path, audio)
            elif ext == '.m4a':
                track = TagEngine._read_m4a(file_path, audio)
            elif ext in {'.ogg', '.oga'}:
                track = TagEngine._read_ogg(file_path, audio)
            elif ext == '.wav':
                track = TagEngine._read_wav(file_path)
            
            # Default title from filename if empty
            if track and not track.title:
                track.title = os.path.splitext(track.filename)[0]
                
            return track
            
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return None
    
    @staticmethod
    def _read_mp3(file_path: str, audio) -> TrackInfo:
        """Read MP3 tags."""
        track = TrackInfo(file_path=file_path)
        track.format_name = "MP3"
        
        # Audio info
        if hasattr(audio.info, 'length'):
            track.duration = audio.info.length
        if hasattr(audio.info, 'bitrate'):
            track.bitrate = audio.info.bitrate // 1000
        if hasattr(audio.info, 'sample_rate'):
            track.sample_rate = audio.info.sample_rate
        if hasattr(audio.info, 'channels'):
            track.channels = audio.info.channels
        
        # ID3 tags
        try:
            id3 = ID3(file_path)
        except:
            return track
        
        track.title = str(id3.get('TIT2', ''))
        track.artist = str(id3.get('TPE1', ''))
        track.album = str(id3.get('TALB', ''))
        track.year = str(id3.get('TDRC', ''))
        track.genre = str(id3.get('TCON', ''))
        track.composer = str(id3.get('TCOM', ''))
        
        # Track number
        trck = id3.get('TRCK')
        if trck:
            parts = str(trck).split('/')
            track.track_number = parts[0]
            track.track_total = parts[1] if len(parts) > 1 else ""
        
        # Disc number
        tpos = id3.get('TPOS')
        if tpos:
            parts = str(tpos).split('/')
            track.disc_number = parts[0]
            track.disc_total = parts[1] if len(parts) > 1 else ""
        
        # Comment
        for key in id3.keys():
            if key.startswith('COMM'):
                track.comment = str(id3[key])
                break
        
        # Lyrics (USLT)
        for key in id3.keys():
            if key.startswith('USLT'):
                track.lyrics = str(id3[key])
                break
        
        # Cover art
        front_cover = None
        other_cover = None
        
        # Robustly get all APIC frames using Mutagen's getall
        frames = id3.getall('APIC') + id3.getall('PIC')
        
        for frame in frames:
             # print(f"DEBUG: Found Frame {frame.HashKey}, Type: {frame.type}, Len: {len(frame.data)}")
             if frame.type == 3: # Front Cover
                 front_cover = frame
             else:
                 other_cover = frame
        
        final_cover = front_cover if front_cover else other_cover
        if final_cover:
            track.cover_data = final_cover.data
            track.cover_mime = final_cover.mime
        
        return track
    
    @staticmethod
    def sanitize_filename(name: str) -> str:
        """Remove illegal characters from filename."""
        illegal = '<>:"/\\|?*'
        for char in illegal:
            name = name.replace(char, '')
        return name.strip()
    
    @staticmethod
    def _read_flac(file_path: str, audio) -> TrackInfo:
        """Read FLAC tags."""
        track = TrackInfo(file_path=file_path)
        track.format_name = "FLAC"
        
        # Audio info
        if hasattr(audio.info, 'length'):
            track.duration = audio.info.length
        if hasattr(audio.info, 'bitrate'):
            track.bitrate = audio.info.bitrate // 1000
        if hasattr(audio.info, 'sample_rate'):
            track.sample_rate = audio.info.sample_rate
        if hasattr(audio.info, 'channels'):
            track.channels = audio.info.channels
        
        # Vorbis comments
        track.title = audio.get('title', [''])[0]
        track.artist = audio.get('artist', [''])[0]
        track.album = audio.get('album', [''])[0]
        track.year = audio.get('date', [''])[0]
        track.genre = audio.get('genre', [''])[0]
        track.composer = audio.get('composer', [''])[0]
        track.comment = audio.get('comment', [''])[0]
        
        # Track/disc numbers
        tracknumber = audio.get('tracknumber', [''])[0]
        if '/' in tracknumber:
            track.track_number, track.track_total = tracknumber.split('/', 1)
        else:
            track.track_number = tracknumber
            track.track_total = audio.get('tracktotal', [''])[0]
        
        discnumber = audio.get('discnumber', [''])[0]
        if '/' in discnumber:
            track.disc_number, track.disc_total = discnumber.split('/', 1)
        else:
            track.disc_number = discnumber
            track.disc_total = audio.get('disctotal', [''])[0]
        
        # Lyrics
        track.lyrics = audio.get('lyrics', [''])[0]
        
        # Cover art
        if audio.pictures:
            pic = audio.pictures[0]
            track.cover_data = pic.data
            track.cover_mime = pic.mime
        
        return track
    
    @staticmethod
    def _read_m4a(file_path: str, audio) -> TrackInfo:
        """Read M4A tags."""
        track = TrackInfo(file_path=file_path)
        track.format_name = "M4A"
        
        # Audio info
        if hasattr(audio.info, 'length'):
            track.duration = audio.info.length
        if hasattr(audio.info, 'bitrate'):
            track.bitrate = audio.info.bitrate // 1000
        if hasattr(audio.info, 'sample_rate'):
            track.sample_rate = audio.info.sample_rate
        if hasattr(audio.info, 'channels'):
            track.channels = audio.info.channels
        
        # MP4 tags
        track.title = audio.get('\xa9nam', [''])[0]
        track.artist = audio.get('\xa9ART', [''])[0]
        track.album = audio.get('\xa9alb', [''])[0]
        track.year = str(audio.get('\xa9day', [''])[0])
        track.genre = audio.get('\xa9gen', [''])[0]
        track.composer = audio.get('\xa9wrt', [''])[0]
        track.comment = audio.get('\xa9cmt', [''])[0]
        
        # Track number
        trkn = audio.get('trkn', [(0, 0)])[0]
        if isinstance(trkn, tuple):
            track.track_number = str(trkn[0]) if trkn[0] else ""
            track.track_total = str(trkn[1]) if trkn[1] else ""
        
        # Disc number
        disk = audio.get('disk', [(0, 0)])[0]
        if isinstance(disk, tuple):
            track.disc_number = str(disk[0]) if disk[0] else ""
            track.disc_total = str(disk[1]) if disk[1] else ""
        
        # Cover art
        covers = audio.get('covr', [])
        if covers:
            track.cover_data = bytes(covers[0])
            track.cover_mime = "image/jpeg"
        
        return track
    
    @staticmethod
    def _read_ogg(file_path: str, audio) -> TrackInfo:
        """Read OGG tags."""
        track = TrackInfo(file_path=file_path)
        track.format_name = "OGG"
        
        # Audio info
        if hasattr(audio.info, 'length'):
            track.duration = audio.info.length
        if hasattr(audio.info, 'bitrate'):
            track.bitrate = audio.info.bitrate // 1000
        if hasattr(audio.info, 'sample_rate'):
            track.sample_rate = audio.info.sample_rate
        if hasattr(audio.info, 'channels'):
            track.channels = audio.info.channels
        
        # Vorbis comments (same as FLAC)
        track.title = audio.get('title', [''])[0]
        track.artist = audio.get('artist', [''])[0]
        track.album = audio.get('album', [''])[0]
        track.year = audio.get('date', [''])[0]
        track.genre = audio.get('genre', [''])[0]
        track.composer = audio.get('composer', [''])[0]
        track.comment = audio.get('comment', [''])[0]
        
        # Track/disc numbers
        track.track_number = audio.get('tracknumber', [''])[0]
        track.track_total = audio.get('tracktotal', [''])[0]
        track.disc_number = audio.get('discnumber', [''])[0]
        track.disc_total = audio.get('disctotal', [''])[0]
        
        return track
    
    @staticmethod
    def write_tags(track: TrackInfo) -> bool:
        """Write tags to an audio file."""
        if not os.path.exists(track.file_path):
            return False
        
        try:
            ext = Path(track.file_path).suffix.lower()
            
            if ext == '.mp3':
                return TagEngine._write_mp3(track)
            elif ext == '.flac':
                return TagEngine._write_flac(track)
            elif ext == '.m4a':
                return TagEngine._write_m4a(track)
            elif ext in {'.ogg', '.oga'}:
                return TagEngine._write_ogg(track)
            elif ext == '.wav':
                return TagEngine._write_wav(track)
            
        except Exception as e:
            error_msg = f"Error writing {track.file_path}: {e}"
            print(error_msg)
            try:
                with open("storm_error.log", "a", encoding="utf-8") as f:
                    f.write(error_msg + "\n")
            except:
                pass
            return False
        
        return False
    
    @staticmethod
    def _write_mp3(track: TrackInfo) -> bool:
        """Write MP3 tags."""
        try:
            try:
                id3 = ID3(track.file_path)
            except:
                # Create new ID3 tag
                from mutagen.id3 import ID3NoHeaderError
                id3 = ID3()
            
            # Text tags
            if track.title:
                id3['TIT2'] = TIT2(encoding=1, text=track.title)
            if track.artist:
                id3['TPE1'] = TPE1(encoding=1, text=track.artist)
            if track.album:
                id3['TALB'] = TALB(encoding=1, text=track.album)
            if track.year:
                id3['TDRC'] = TDRC(encoding=1, text=track.year)
            if track.genre:
                id3['TCON'] = TCON(encoding=1, text=track.genre)
            if track.composer:
                id3['TCOM'] = TCOM(encoding=1, text=track.composer)
            
            # Track number
            if track.track_number:
                trck = track.track_number
                if track.track_total:
                    trck += f"/{track.track_total}"
                id3['TRCK'] = TRCK(encoding=1, text=trck)
            
            # Disc number
            if track.disc_number:
                tpos = track.disc_number
                if track.disc_total:
                    tpos += f"/{track.disc_total}"
                id3['TPOS'] = TPOS(encoding=1, text=tpos)
            
            # Comment
            if track.comment:
                id3['COMM::eng'] = COMM(encoding=1, lang='eng', desc='', text=track.comment)
            
            # Lyrics (USLT)
            if track.lyrics:
                id3.delall('USLT')
                id3['USLT::eng'] = USLT(encoding=3, lang='eng', desc='', text=track.lyrics)
            
            # Cover art
            if track.cover_data and len(track.cover_data) > 0:
                # Remove existing covers safely
                id3.delall('APIC')
                
                # Ensure valid mime type
                mime = track.cover_mime if track.cover_mime else 'image/jpeg'
                if not mime.startswith('image/'):
                    mime = 'image/jpeg'
                
                # Use empty description for maximum compatibility (Windows Explorer preference)
                id3.add(APIC(
                    encoding=1, # UTF-16
                    mime=mime,
                    type=3,  # Front cover
                    desc='', # Empty description
                    data=track.cover_data
                ))
            
            id3.save(track.file_path, v2_version=3)
            return True
            
        except Exception:
            raise
    
    @staticmethod
    def _write_flac(track: TrackInfo) -> bool:
        """Write FLAC tags."""
        try:
            audio = FLAC(track.file_path)
            
            audio['title'] = track.title
            audio['artist'] = track.artist
            audio['album'] = track.album
            audio['date'] = track.year
            audio['genre'] = track.genre
            audio['composer'] = track.composer
            audio['comment'] = track.comment
            
            if track.track_number:
                audio['tracknumber'] = track.track_number
            if track.track_total:
                audio['tracktotal'] = track.track_total
            if track.disc_number:
                audio['discnumber'] = track.disc_number
            if track.disc_total:
                audio['disctotal'] = track.disc_total
            
            # Lyrics
            if track.lyrics:
                audio['lyrics'] = track.lyrics
            
            # Cover art
            if track.cover_data:
                audio.clear_pictures()
                pic = Picture()
                pic.type = 3  # Front cover
                pic.mime = track.cover_mime
                pic.data = track.cover_data
                
                # Get image dimensions
                try:
                    img = Image.open(io.BytesIO(track.cover_data))
                    pic.width, pic.height = img.size
                    pic.depth = 24
                except:
                    pass
                
                audio.add_picture(pic)
            
            audio.save()
            return True
            
        except Exception:
            raise
    
    @staticmethod
    def _write_m4a(track: TrackInfo) -> bool:
        """Write M4A tags."""
        try:
            audio = MP4(track.file_path)
            
            audio['\xa9nam'] = track.title
            audio['\xa9ART'] = track.artist
            audio['\xa9alb'] = track.album
            audio['\xa9day'] = track.year
            audio['\xa9gen'] = track.genre
            audio['\xa9wrt'] = track.composer
            audio['\xa9cmt'] = track.comment
            
            # Track number
            trk_num = int(track.track_number) if track.track_number.isdigit() else 0
            trk_total = int(track.track_total) if track.track_total.isdigit() else 0
            if trk_num or trk_total:
                audio['trkn'] = [(trk_num, trk_total)]
            
            # Disc number
            disc_num = int(track.disc_number) if track.disc_number.isdigit() else 0
            disc_total = int(track.disc_total) if track.disc_total.isdigit() else 0
            if disc_num or disc_total:
                audio['disk'] = [(disc_num, disc_total)]
            
            # Cover art
            if track.cover_data:
                if 'png' in track.cover_mime.lower():
                    cover_format = MP4Cover.FORMAT_PNG
                else:
                    cover_format = MP4Cover.FORMAT_JPEG
                audio['covr'] = [MP4Cover(track.cover_data, imageformat=cover_format)]
            
            audio.save()
            return True
            
        except Exception:
            raise
    
    @staticmethod
    def _write_ogg(track: TrackInfo) -> bool:
        """Write OGG tags."""
        try:
            audio = OggVorbis(track.file_path)
            
            audio['title'] = track.title
            audio['artist'] = track.artist
            audio['album'] = track.album
            audio['date'] = track.year
            audio['genre'] = track.genre
            audio['composer'] = track.composer
            audio['comment'] = track.comment
            
            if track.track_number:
                audio['tracknumber'] = track.track_number
            if track.track_total:
                audio['tracktotal'] = track.track_total
            if track.disc_number:
                audio['discnumber'] = track.disc_number
            if track.disc_total:
                audio['disctotal'] = track.disc_total
            
            audio.save()
            return True
            
        except Exception:
            raise
    
    @staticmethod
    def _read_wav(file_path: str) -> Optional[TrackInfo]:
        """Read WAV tags using ID3 tags embedded in WAV."""
        try:
            from mutagen.wave import WAVE
            from mutagen.id3 import ID3
            
            track = TrackInfo(file_path=file_path)
            
            # Get audio info
            audio = WAVE(file_path)
            if audio.info:
                track.duration = int(audio.info.length)
                track.bitrate = audio.info.bitrate // 1000 if hasattr(audio.info, 'bitrate') and audio.info.bitrate else 0
                track.sample_rate = audio.info.sample_rate if hasattr(audio.info, 'sample_rate') else 0
            
            # WAV files can have ID3 tags
            try:
                tags = audio.tags
                if tags is None:
                    # Try to load ID3 directly
                    try:
                        tags = ID3(file_path)
                    except:
                        pass
                
                if tags:
                    track.title = str(tags.get('TIT2', [''])[0]) if 'TIT2' in tags else ''
                    track.artist = str(tags.get('TPE1', [''])[0]) if 'TPE1' in tags else ''
                    track.album = str(tags.get('TALB', [''])[0]) if 'TALB' in tags else ''
                    track.year = str(tags.get('TDRC', [''])[0]) if 'TDRC' in tags else ''
                    track.genre = str(tags.get('TCON', [''])[0]) if 'TCON' in tags else ''
                    track.composer = str(tags.get('TCOM', [''])[0]) if 'TCOM' in tags else ''
                    
                    # Comments
                    for key in tags:
                        if key.startswith('COMM'):
                            track.comment = str(tags[key].text[0]) if tags[key].text else ''
                            break
                    
                    # Track number
                    if 'TRCK' in tags:
                        trck = str(tags['TRCK'][0])
                        if '/' in trck:
                            parts = trck.split('/')
                            track.track_number = parts[0]
                            track.track_total = parts[1] if len(parts) > 1 else ''
                        else:
                            track.track_number = trck
                    
                    # Disc number
                    if 'TPOS' in tags:
                        tpos = str(tags['TPOS'][0])
                        if '/' in tpos:
                            parts = tpos.split('/')
                            track.disc_number = parts[0]
                            track.disc_total = parts[1] if len(parts) > 1 else ''
                        else:
                            track.disc_number = tpos
                    
                    # Cover art
                    for key in tags:
                        if key.startswith('APIC'):
                            apic = tags[key]
                            track.cover_data = apic.data
                            track.cover_mime = apic.mime
                            break
            except Exception as e:
                print(f"Error reading WAV tags: {e}")
            
            return track
            
        except Exception as e:
            print(f"Error reading WAV: {e}")
            return None
    
    @staticmethod
    def _write_wav(track: TrackInfo) -> bool:
        """Write tags to WAV file using ID3."""
        try:
            from mutagen.wave import WAVE
            from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TCON, TCOM, TRCK, TPOS, COMM, APIC, ID3NoHeaderError
            
            audio = WAVE(track.file_path)
            
            # Get or create ID3 tags
            try:
                if audio.tags is None:
                    audio.add_tags()
                tags = audio.tags
            except:
                audio.add_tags()
                tags = audio.tags
            
            # Set text frames
            tags['TIT2'] = TIT2(encoding=3, text=track.title)
            tags['TPE1'] = TPE1(encoding=3, text=track.artist)
            tags['TALB'] = TALB(encoding=3, text=track.album)
            tags['TDRC'] = TDRC(encoding=3, text=track.year)
            tags['TCON'] = TCON(encoding=3, text=track.genre)
            tags['TCOM'] = TCOM(encoding=3, text=track.composer)
            
            # Track number
            if track.track_number:
                trck = track.track_number
                if track.track_total:
                    trck += f"/{track.track_total}"
                tags['TRCK'] = TRCK(encoding=3, text=trck)
            
            # Disc number
            if track.disc_number:
                tpos = track.disc_number
                if track.disc_total:
                    tpos += f"/{track.disc_total}"
                tags['TPOS'] = TPOS(encoding=3, text=tpos)
            
            # Comment
            if track.comment:
                tags['COMM::eng'] = COMM(encoding=3, lang='eng', desc='', text=track.comment)
            
            # Cover art
            if track.cover_data:
                mime = track.cover_mime or 'image/jpeg'
                tags['APIC:'] = APIC(
                    encoding=3,
                    mime=mime,
                    type=3,  # Front cover
                    desc='Cover',
                    data=track.cover_data
                )
            
            audio.save()
            return True
            
        except Exception:
            raise
    
    @staticmethod
    def extract_cover(track: TrackInfo, output_path: str) -> bool:
        """Extract cover art to a file."""
        if not track.cover_data:
            return False
        
        try:
            ext = '.png' if 'png' in track.cover_mime.lower() else '.jpg'
            if not output_path.lower().endswith(('.jpg', '.jpeg', '.png')):
                output_path += ext
            
            with open(output_path, 'wb') as f:
                f.write(track.cover_data)
            return True
        except Exception as e:
            print(f"Error extracting cover: {e}")
            return False
    
    @staticmethod
    def load_cover_from_file(image_path: str, max_size: int = 800) -> Tuple[Optional[bytes], str]:
        """Load and optionally resize an image for use as cover art."""
        try:
            img = Image.open(image_path)
            
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P', 'LA', 'L'):
                # Create white background for transparency
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                else:
                    img = img.convert('RGB')
            
            # Resize if too large
            if max(img.size) > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Save to bytes
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=90)
            data = buffer.getvalue()
            
            if data and len(data) > 0:
                return data, 'image/jpeg'
            else:
                return None, ''
            
        except Exception as e:
            print(f"Error loading cover: {e}")
            return None, ''

