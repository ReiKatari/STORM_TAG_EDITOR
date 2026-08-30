"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                          STORM TAG EDITOR                                      ║
║         Professional Music Tag Editor for MP3, FLAC, M4A, OGG                 ║
╚═══════════════════════════════════════════════════════════════════════════════╝

A modern, fast, and beautiful music tag editor with support for:
- Single and batch tag editing
- Cover art management (embed, extract, preview)
- Auto track numbering
- Genre presets
- Drag and drop support

Author: Storm Development
Version: 0.0.24
"""

import os
import sys
import json
import time
import threading
import subprocess
import urllib.request
from pathlib import Path
from typing import List, Optional
import io
import ctypes

import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import tkinter as tk

# Import tkinterdnd2 for drag and drop
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

from tag_engine import TagEngine, TrackInfo, GENRE_PRESETS, SUPPORTED_EXTENSIONS
from localization import t, set_language, get_language
from converter_dialog import ConverterDialog
from ui_utils import COLORS, ModernButton, show_styled_info, animate_fade_in, FONT_FAMILY

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

APP_NAME = "STORM TAG EDITOR"
APP_VERSION = "0.0.24"
GITHUB_REPO = "ReiKatari/STORM_TAG_EDITOR"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
WINDOW_WIDTH = 1650
WINDOW_HEIGHT = 900
MIN_WIDTH = 1300
MIN_HEIGHT = 750

# Config file path
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

# ═══════════════════════════════════════════════════════════════════════════════
# SETTINGS MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class SettingsManager:
    """Manages application settings persistence."""
    
    DEFAULT_SETTINGS = {
        'window_width': WINDOW_WIDTH,
        'window_height': WINDOW_HEIGHT,
        'window_x': None,
        'window_y': None,
        'left_panel_width': 280,
        'right_panel_width': 300,
        'auto_update': True,
        'language': 'ru',  # 'ru' or 'en'
    }
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.settings = self.DEFAULT_SETTINGS.copy()
        self.load()
    
    def load(self):
        """Load settings from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    self.settings.update(saved)
        except Exception:
            pass
    
    def save(self):
        """Save settings to file."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
        except Exception:
            pass
    
    def get(self, key: str, default=None):
        return self.settings.get(key, default)
    
    def set(self, key: str, value):
        self.settings[key] = value


# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOM WIDGETS
# ═══════════════════════════════════════════════════════════════════════════════

class ModernEntry(ctk.CTkEntry):
    """Styled entry widget with copy/paste support."""
    def __init__(self, master, placeholder="", **kwargs):
        super().__init__(
            master,
            placeholder_text=placeholder,
            fg_color=COLORS['bg_input'],
            border_color=COLORS['border'],
            text_color=COLORS['text'],
            placeholder_text_color=COLORS['text_muted'],
            corner_radius=8,
            height=36,
            **kwargs
        )
        # Bind copy/paste shortcuts
        # Bind copy/paste shortcuts - utilizing KeyPress for layout independence
        self._entry.bind('<Control-KeyPress>', self._on_control_key)
            
    def _on_control_key(self, event):
        """Handle control key events via keycode for layout independence."""
        key = event.keycode
        keysym = event.keysym.lower() if event.keysym else ""
        
        if key == 67: # C
            # If standard binding (c), let it pass to avoid double event
            if keysym == 'c': return None
            self._copy(event)
        elif key == 86: # V
            # If standard binding (v), let it pass
            if keysym == 'v': return None
            self._paste(event)
        elif key == 88: # X
            if keysym == 'x': return None
            self._cut(event)
        elif key == 65: # A
            # Select all logic safe to repeat usually, but lets filter
            if keysym == 'a': return None
            self._select_all(event)
    
    def _copy(self, event=None):
        try:
            self._entry.event_generate("<<Copy>>")
            return 'break'
        except:
            return None
    
    def _paste(self, event=None):
        try:
            self._entry.event_generate("<<Paste>>")
            return 'break'
        except:
            return None
    
    def _cut(self, event=None):
        try:
            self._entry.event_generate("<<Cut>>")
            return 'break'
        except:
            return None
    
    def _select_all(self, event=None):
        self.select_range(0, 'end')
        self.icursor('end')
        return 'break'





class ModernComboBox(ctk.CTkComboBox):
    """Styled combobox widget with autocomplete popup and copy/paste support."""
    def __init__(self, master, values=None, **kwargs):
        self.all_values = [""] + (values or [])
        super().__init__(
            master,
            values=self.all_values,
            fg_color=COLORS['bg_input'],
            border_color=COLORS['border'],
            button_color=COLORS['accent'],
            button_hover_color=COLORS['accent_hover'],
            dropdown_fg_color=COLORS['bg_panel'],
            dropdown_hover_color=COLORS['bg_hover'],
            text_color=COLORS['text'],
            corner_radius=8,
            width=200, # Increased internal width default
            **kwargs
        )
        self.set("")  # Start empty
        self.popup = None # Initialize popup state
        
        # Bind key release for autocomplete filtering
        try:
           self._entry.bind('<KeyRelease>', self._on_key_release)
           self._entry.bind('<FocusOut>', self._hide_popup)
           self._entry.bind('<Escape>', self._hide_popup)
           self._entry.bind('<Return>', self._select_from_popup)
           self._entry.bind('<Down>', self._popup_down)
           self._entry.bind('<Up>', self._popup_up)
        except:
           pass
           
        self.bind('<Control-KeyPress>', self._on_control_key)
        
    def _on_control_key(self, event):
        """Handle control key events via keycode for layout independence."""
        key = event.keycode
        if key == 67: # C
            self._copy(event)
        elif key == 86: # V
            self._paste(event)
        elif key == 88: # X
            self._cut(event)
        elif key == 65: # A
            self._select_all(event)
            
    def _copy(self, event=None):
        try:
            # For Combobox, usually users copy from Entry part
            self._entry.event_generate("<<Copy>>")
        except:
            pass
        return 'break'
    
    def _paste(self, event=None):
        try:
            self._entry.event_generate("<<Paste>>")
        except:
            pass
        return 'break'
    
    def _cut(self, event=None):
        try:
            self._entry.event_generate("<<Cut>>")
        except:
            pass
        return 'break'
    
        return 'break'
        
    def _select_all(self, event=None):
        try:
            self._entry.select_range(0, 'end')
            self._entry.icursor('end')
        except:
            pass
        return 'break'
    
    def _cut(self, event=None):
        try:
            if self._entry.selection_present():
                text = self._entry.selection_get()
                self.clipboard_clear()
                self.clipboard_append(text)
                self._entry.delete('sel.first', 'sel.last')
        except:
            pass
        return "break"
    
    def _select_all(self, event=None):
        try:
            self._entry.select_range(0, 'end')
            self._entry.icursor('end')
        except:
            pass
        return "break"
    
    def _on_key_release(self, event=None):
        """Filter and show autocomplete popup."""
        # Skip special keys
        if event and event.keysym in ('Control_L', 'Control_R', 'Shift_L', 'Shift_R', 
                                        'Alt_L', 'Alt_R', 'Up', 'Down', 'Left', 'Right',
                                        'Return', 'Escape', 'Tab'):
            return
        
        try:
            typed = self.get().strip().lower()
            # Show popup only with 2+ chars
            if len(typed) >= 2:
                filtered = [v for v in self.all_values if v and typed in v.lower()][:8]  # Max 8 items
                if filtered:
                    self._show_popup(filtered)
                else:
                    self._hide_popup()
            else:
                self._hide_popup()
            
            # Also update dropdown values
            if typed:
                filtered_all = [v for v in self.all_values if v and typed in v.lower()]
                if filtered_all:
                    self.configure(values=filtered_all)
            else:
                self.configure(values=self.all_values)
        except:
            pass
    
    def _show_popup(self, items):
        """Show autocomplete popup above the field."""
        if self.popup is None:
            self.popup = tk.Toplevel(self)
            self.popup.wm_overrideredirect(True)
            self.popup.configure(bg=COLORS['bg_panel'])
            
            self.popup_listbox = tk.Listbox(
                self.popup,
                bg=COLORS['bg_panel'],
                fg=COLORS['text'],
                selectbackground=COLORS['accent'],
                selectforeground=COLORS['text'],
                borderwidth=1,
                relief='solid',
                highlightthickness=0,
                font=('Segoe UI', 10),
                activestyle='none'
            )
            self.popup_listbox.pack(fill='both', expand=True)
            self.popup_listbox.bind('<ButtonRelease-1>', self._on_popup_click)
        
        # Update items
        self.popup_listbox.delete(0, tk.END)
        for item in items:
            self.popup_listbox.insert(tk.END, item)
        
        # Position above the entry
        x = self.winfo_rootx()
        y = self.winfo_rooty() - (len(items) * 20 + 4)  # Above the field
        width = self.winfo_width()
        height = len(items) * 20 + 4
        
        if y < 0:  # If not enough space above, show below
            y = self.winfo_rooty() + self.winfo_height()
        
        self.popup.geometry(f"{width}x{height}+{x}+{y}")
        self.popup.deiconify()
        self.popup.lift()
    
    def _hide_popup(self, event=None):
        """Hide autocomplete popup."""
        if self.popup:
            self.popup.withdraw()
    
    def _on_popup_click(self, event=None):
        """Handle click on popup item."""
        try:
            selection = self.popup_listbox.curselection()
            if selection:
                value = self.popup_listbox.get(selection[0])
                self.set(value)
                self._hide_popup()
                self._entry.focus_set()
        except:
            pass
    
    def _select_from_popup(self, event=None):
        """Select highlighted item from popup with Enter."""
        if self.popup and self.popup.winfo_viewable():
            try:
                selection = self.popup_listbox.curselection()
                if selection:
                    value = self.popup_listbox.get(selection[0])
                    self.set(value)
                    self._hide_popup()
                    return "break"
            except:
                pass
    
    def _popup_down(self, event=None):
        """Move selection down in popup."""
        if self.popup and self.popup.winfo_viewable():
            try:
                cur = self.popup_listbox.curselection()
                if cur:
                    next_idx = min(cur[0] + 1, self.popup_listbox.size() - 1)
                else:
                    next_idx = 0
                self.popup_listbox.selection_clear(0, tk.END)
                self.popup_listbox.selection_set(next_idx)
                self.popup_listbox.see(next_idx)
                return "break"
            except:
                pass
    
    def _popup_up(self, event=None):
        """Move selection up in popup."""
        if self.popup and self.popup.winfo_viewable():
            try:
                cur = self.popup_listbox.curselection()
                if cur:
                    prev_idx = max(cur[0] - 1, 0)
                else:
                    prev_idx = 0
                self.popup_listbox.selection_clear(0, tk.END)
                self.popup_listbox.selection_set(prev_idx)
                self.popup_listbox.see(prev_idx)
                return "break"
            except:
                pass


class FileListItem(ctk.CTkFrame):
    """Single file item in the file list."""
    def __init__(self, master, track: TrackInfo, on_select=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.track = track
        self.on_select = on_select
        self.selected = False
        
        self.configure(height=50)
        self.pack_propagate(False)
        
        # Checkbox
        self.checkbox_var = ctk.BooleanVar(value=False)
        self.checkbox = ctk.CTkCheckBox(
            self,
            text="",
            variable=self.checkbox_var,
            width=24,
            checkbox_width=20,
            checkbox_height=20,
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            border_color=COLORS['border'],
            command=self._on_checkbox_change
        )
        self.checkbox.pack(side="left", padx=(10, 5))
        
        # File info
        # Optimization: removed inner frame
        # Just use self and pack (checkbox - left, duration - right, title/sub - top fill x)
        
        # Title/filename
        title_text = track.title if track.title else track.filename
        if track.track_number:
            # Try to zero pad if singular digit?
            # Or just show as is. "1. Title" vs "01. Title"
            # User request: "В файлах показывай, какой номер у трека."
            # Lets just use what is in tag
            title_text = f"{track.track_number}. {title_text}"
            
        self.title_label = ctk.CTkLabel(
            self,
            text=title_text,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=COLORS['text'],
            anchor="w"
        )
        self.title_label.pack(side="top", fill="x", padx=5, pady=(8, 0))
        
        # Artist - Album
        subtitle = f"{track.artist} - {track.album}" if track.artist or track.album else track.format_name
        self.subtitle_label = ctk.CTkLabel(
            self,
            text=subtitle,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=COLORS['text_secondary'],
            anchor="w"
        )
        self.subtitle_label.pack(side="top", fill="x", padx=5)
        
        # Duration
        self.duration_label = ctk.CTkLabel(
            self,
            text=track.duration_str,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=COLORS['text_muted'],
            width=50
        )
        self.duration_label.pack(side="right", padx=10)
        
        # Re-pack checkbox to left (it was packed first so it stays left)
        # Bind click - Checkbox is already packed first
        
        # Bind click
        self.bind("<Button-1>", self._on_click)
        self.title_label.bind("<Button-1>", self._on_click)
        self.subtitle_label.bind("<Button-1>", self._on_click)
    
    def _on_click(self, event=None):
        if self.on_select:
            self.on_select(self, event)
    
    def _on_checkbox_change(self):
        pass
    
    def set_selected(self, selected: bool):
        self.selected = selected
        self.configure(fg_color=COLORS['accent_dark'] if selected else "transparent")
    
    def is_checked(self) -> bool:
        return self.checkbox_var.get()
    
    def set_checked(self, checked: bool):
        self.checkbox_var.set(checked)


class CoverArtPanel(ctk.CTkFrame):
    """Cover art preview and management panel."""
    def __init__(self, master, on_cover_change=None, **kwargs):
        super().__init__(master, fg_color=COLORS['bg_panel'], corner_radius=12, **kwargs)
        
        self.on_cover_change = on_cover_change
        self.current_cover_data = None
        self.photo_image = None
        
        # Grid configuration for Horizontal Layout
        self.columnconfigure(0, weight=0) # Image
        self.columnconfigure(1, weight=1) # Buttons
        self.rowconfigure(0, weight=1)
        
        # Cover preview frame (Left)
        self.preview_frame = ctk.CTkFrame(
            self,
            fg_color=COLORS['bg_input'],
            corner_radius=8,
            width=200,
            height=200
        )
        self.preview_frame.grid(row=0, column=0, rowspan=4, padx=15, pady=15)
        self.preview_frame.pack_propagate(False)
        
        # Cover image label (Standard Tkinter)
        self.cover_label = tk.Label(
            self.preview_frame,
            text=t('no_cover'),
            fg=COLORS['text_muted'],
            bg=COLORS['bg_input'],
            font=(FONT_FAMILY, 10)
        )
        self.cover_label.pack(expand=True, fill="both")
        
        # Buttons Setup (Right, Centered Vertically)
        # We use a container frame for buttons to center them together
        btn_container = ctk.CTkFrame(self, fg_color="transparent")
        btn_container.grid(row=0, column=1, rowspan=4, padx=(0, 15), pady=15, sticky="ew")
        
        self.change_btn = ModernButton(
            btn_container,
            text=t('change_cover'),
            command=self._select_cover
        )
        self.change_btn.pack(fill="x", pady=5)
        
        self.remove_btn = ModernButton(
            btn_container,
            text=t('remove_cover'),
            command=self._remove_cover
        )
        self.remove_btn.pack(fill="x", pady=5)
        
        self.extract_btn = ModernButton(
            btn_container,
            text=t('extract_cover'),
            command=self._extract_cover
        )
        self.extract_btn.pack(fill="x", pady=5)
        
        # Enable DND if available
        if DND_AVAILABLE:
            try:
                self.cover_label.drop_target_register(DND_FILES)
                self.cover_label.dnd_bind('<<Drop>>', self._on_cover_drop)
                self.preview_frame.drop_target_register(DND_FILES)
                self.preview_frame.dnd_bind('<<Drop>>', self._on_cover_drop)
            except:
                pass
                
    def _on_cover_drop(self, event):
        """Handle dropped image file."""
        data = event.data
        path = None
        
        # Robust path parsing
        if '{' in data:
            import re
            paths = re.findall(r'\{([^}]+)\}', data)
            path = paths[0] if paths else None
        else:
            # Maybe it's a single path with spaces without braces (rare but possible on some systems)
            # Or just single path without spaces
            if os.path.exists(data):
                path = data
            else:
                 path = data.split()[0] if data else None

        if not path:
             return
             
        # Normalize path
        path = path.strip()
        if not os.path.isfile(path):
             return
             
        # Check extension
        ext = os.path.splitext(path)[1].lower()
        valid_exts = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']
        
        if ext not in valid_exts:
            show_styled_info(self, t('error'), f"Формат {ext} не поддерживается")
            return
            
        try:
            cover_data, mime = TagEngine.load_cover_from_file(path)
            if cover_data:
                # self.current_cover_data IS SET INSIDE set_cover!
                # Do not set it here, otherwise set_cover optimization will skip update!
                self.set_cover(cover_data)
                if self.on_cover_change:
                    self.on_cover_change(cover_data, mime)
            else:
                show_styled_info(self, t('error'), "Не удалось прочитать файл изображения")
        except Exception as e:
            show_styled_info(self, t('error'), f"Ошибка загрузки: {str(e)}")

    
    def set_cover(self, cover_data: Optional[bytes]):
        """Set and display cover art with transition."""
        
        # Helper to prepare standard image
        def prepare_image(data):
            if not data: return None
            try:
                img = Image.open(io.BytesIO(data))
                
                # Convert to RGBA (handles P, CMYK, etc.)
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                    
                img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                bg = Image.new('RGBA', (200, 200), (0,0,0,0))
                offset = ((200 - img.size[0]) // 2, (200 - img.size[1]) // 2)
                bg.paste(img, offset)
                return bg
            except Exception as e:
                print(f"Error loading image: {e}")
                return None

        # Optimization: Don't update if data is identical (and not forcing)
        if self.current_cover_data == cover_data and cover_data is not None:
             return

        new_pil = prepare_image(cover_data) if cover_data else None
        
        # FIX: Disable animation to prevent 'pyimageX' errors caused by GC
        # Animation creates multiple transient images that Tkinter/GC might Mishandle
        
        try:
            # Cancel anim if any
            if hasattr(self, '_anim_id') and self._anim_id:
                self.after_cancel(self._anim_id)
                self._anim_id = None
            
            if new_pil:
                # Force load
                if hasattr(new_pil, 'load'):
                    new_pil.load()
                    
                # Use standard Tkinter PhotoImage for maximum reliability
                photo = ImageTk.PhotoImage(new_pil)
                self._keep_alive_image = photo # Keep explicit reference!
                
                # Update Tk Label
                self.cover_label.configure(image=photo, text="", bg=COLORS['bg_input'])
            else:
                self.cover_label.configure(image="", text=t('no_cover'), bg=COLORS['bg_input'])
                self._keep_alive_image = None
                    
            self.current_pil = new_pil
            self.current_cover_data = cover_data
            
        except Exception as e:
            # Fallback if image creation fails
            print(f"Error setting cover: {e}")
            try:
                self.cover_label.configure(image="", text=t('error'))
            except:
                pass
    
    def _animate_crossfade(self, start_img, end_img, steps=10, duration=200):
        if hasattr(self, '_anim_id') and self._anim_id:
            self.after_cancel(self._anim_id)
            
        step_time = duration // steps
        
        def step(i):
            if i > steps:
                return
            alpha = i / steps
            blended = Image.blend(start_img, end_img, alpha)
            ctk_img = ctk.CTkImage(light_image=blended, dark_image=blended, size=(200, 200))
            self._keep_alive_anim_image = ctk_img # Keep explicit reference!
            self.cover_label.configure(image=ctk_img, text="")
            self._anim_id = self.after(step_time, lambda: step(i+1))
            
        step(0)
    
    def _select_cover(self):
        """Select a new cover image."""
        file_path = filedialog.askopenfilename(
            title="Выберите изображение обложки",
            filetypes=[
                ("Изображения", "*.jpg *.jpeg *.png *.bmp *.gif"),
                ("Все файлы", "*.*")
            ]
        )
        
        if file_path:
            cover_data, mime = TagEngine.load_cover_from_file(file_path)
            if cover_data:
                # Fix: Don't prevent update logic
                self.set_cover(cover_data)
                if self.on_cover_change:
                    self.on_cover_change(cover_data, mime)
            else:
                messagebox.showerror("Ошибка", "Не удалось загрузить изображение")
    
    def _remove_cover(self):
        """Remove the current cover."""
        self.current_cover_data = None
        self.set_cover(None)
        if self.on_cover_change:
            self.on_cover_change(None, '')
    
    def _extract_cover(self):
        """Extract cover to a file."""
        if not self.current_cover_data:
            show_styled_info(self, t('info'), t('no_cover'), "ℹ️")
            return
        
        file_path = filedialog.asksaveasfilename(
            title=t('extract_cover'),
            defaultextension=".jpg",
            filetypes=[
                ("JPEG", "*.jpg"),
                ("PNG", "*.png")
            ]
        )
        
        if file_path:
            try:
                with open(file_path, 'wb') as f:
                    f.write(self.current_cover_data)
                show_styled_info(self, t('success'), t('cover_extracted'), "✅")
            except Exception as e:
                show_styled_info(self, t('error'), f"{t('error_save')}: {e}", "❌")


class TagEditorPanel(ctk.CTkScrollableFrame):
    """Panel for editing track tags."""
    def __init__(self, master, on_track_number_change=None, **kwargs):
        super().__init__(
            master,
            fg_color=COLORS['bg_panel'],
            corner_radius=12,
            scrollbar_button_color=COLORS['bg_input'],
            scrollbar_button_hover_color=COLORS['bg_hover'],
            **kwargs
        )
        
        self.current_track: Optional[TrackInfo] = None
        self.entries = {}
        self.on_track_number_change = on_track_number_change
        
        self._create_widgets()
    
    def _create_widgets(self):
        # Title
        title = ctk.CTkLabel(
            self,
            text=t('tag_editor'),
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
            text_color=COLORS['text']
        )
        title.pack(pady=(15, 20), padx=15, anchor="w")
        
        # Track info (read-only)
        self.info_label = ctk.CTkLabel(
            self,
            text=t('select_file_hint'),
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=COLORS['text_secondary']
        )
        self.info_label.pack(padx=15, anchor="w")
        
        # Separator
        sep = ctk.CTkFrame(self, height=1, fg_color=COLORS['border'])
        sep.pack(fill="x", padx=15, pady=15)
        
        # Tag fields with localized labels
        fields = [
            ("title", t('title')),
            ("artist", t('artist')),
            ("album", t('album')),
            ("year", t('year')),
            ("genre", t('genre'), "combo"),
            ("track_number", t('track_num'), "small"),
            ("track_total", t('track_total'), "small"),
            ("disc_number", t('disc_num'), "small"),
            ("disc_total", t('disc_total'), "small"),
            ("composer", t('composer')),
            ("comment", t('comment')),
        ]
        
        row_frame = None
        for i, field in enumerate(fields):
            key = field[0]
            label = field[1]
            field_type = field[2] if len(field) > 2 else "normal"
            
            if field_type == "small":
                if row_frame is None:
                    row_frame = ctk.CTkFrame(self, fg_color="transparent")
                    row_frame.pack(fill="x", padx=15, pady=5)
                    # Configure 4 columns uniformly
                    for c in range(4):
                        row_frame.columnconfigure(c, weight=1, uniform="small_fields")
                
                field_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
                # Calculate column index based on field list order
                # Track#, Total, Disc#, Total -> matches 0,1,2,3
                # We need to track index within the row
                col_idx = (i - 5) # 5 is the index of first small field (track_number)
                field_frame.grid(row=0, column=col_idx, sticky="ew", padx=2)
            else:
                row_frame = None
                field_frame = ctk.CTkFrame(self, fg_color="transparent")
                field_frame.pack(fill="x", padx=15, pady=5)
            
            # Label
            lbl = ctk.CTkLabel(
                field_frame,
                text=label,
                font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
                text_color=COLORS['text_secondary']
            )
            lbl.pack(anchor="w")
            
            # Entry or ComboBox
            if field_type == "combo":
                entry = ModernComboBox(field_frame, values=GENRE_PRESETS)
                entry.pack(fill="x", pady=(3, 0))
            else:
                entry = ModernEntry(field_frame)
                if key == "track_number" and self.on_track_number_change:
                     entry.bind('<KeyRelease>', lambda e: self.on_track_number_change(self.entries['track_number'].get()))
                entry.pack(fill="x", pady=(3, 0))
            
            self.entries[key] = entry
    
    def load_track(self, track: TrackInfo):
        """Load a track's data into the editor."""
        self.current_track = track
        
        # Update info label
        self.info_label.configure(
            text=f"{track.filename}  |  {track.format_name}  |  {track.quality_str}"
        )
        
        # Populate fields
        self.entries['title'].delete(0, 'end')
        # Default to filename if title is empty
        display_title = track.title if track.title else (os.path.splitext(track.filename)[0] if track.filename else "")
        self.entries['title'].insert(0, display_title)
        
        self.entries['artist'].delete(0, 'end')
        self.entries['artist'].insert(0, track.artist)
        
        self.entries['album'].delete(0, 'end')
        self.entries['album'].insert(0, track.album)
        
        self.entries['year'].delete(0, 'end')
        self.entries['year'].insert(0, track.year)
        
        self.entries['genre'].set(track.genre)
        
        self.entries['track_number'].delete(0, 'end')
        self.entries['track_number'].insert(0, track.track_number)
        
        self.entries['track_total'].delete(0, 'end')
        self.entries['track_total'].insert(0, track.track_total)
        
        self.entries['disc_number'].delete(0, 'end')
        self.entries['disc_number'].insert(0, track.disc_number)
        
        self.entries['disc_total'].delete(0, 'end')
        self.entries['disc_total'].insert(0, track.disc_total)
        
        self.entries['composer'].delete(0, 'end')
        self.entries['composer'].insert(0, track.composer)
        
        self.entries['comment'].delete(0, 'end')
        self.entries['comment'].insert(0, track.comment)
    
    def get_values(self) -> dict:
        """Get all current field values."""
        return {
            'title': self.entries['title'].get(),
            'artist': self.entries['artist'].get(),
            'album': self.entries['album'].get(),
            'year': self.entries['year'].get(),
            'genre': self.entries['genre'].get(),
            'track_number': self.entries['track_number'].get(),
            'track_total': self.entries['track_total'].get(),
            'disc_number': self.entries['disc_number'].get(),
            'disc_total': self.entries['disc_total'].get(),
            'composer': self.entries['composer'].get(),
            'comment': self.entries['comment'].get(),
        }
    
    def clear(self):
        """Clear all fields."""
        self.current_track = None
        self.info_label.configure(text="Выберите файл для редактирования")
        for entry in self.entries.values():
            if isinstance(entry, ModernComboBox):
                entry.set("")
            else:
                entry.delete(0, 'end')


class BatchEditorPanel(ctk.CTkFrame):
    """Panel for batch tag editing."""
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=COLORS['bg_panel'], corner_radius=12, **kwargs)
        
        self.checkboxes = {}
        self.entries = {}
        
        self._create_widgets()
    
    def _create_widgets(self):
        # 4-Column Grid
        # Col 0: Label (Left)
        # Col 1: Input (Left, Weight 1)
        # Col 2: Label (Right)
        # Col 3: Input (Right, Weight 1)
        
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1, uniform="inputs")
        self.columnconfigure(2, weight=0)
        self.columnconfigure(3, weight=1, uniform="inputs")
        
        # Title
        title = ctk.CTkLabel(
            self,
            text=t('batch_editor'),
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            text_color=COLORS['text']
        )
        title.grid(row=0, column=0, columnspan=4, padx=15, pady=(15, 10), sticky="w")
        
        # Description
        desc = ctk.CTkLabel(
            self,
            text=t('batch_hint'),
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=COLORS['text_muted']
        )
        desc.grid(row=1, column=0, columnspan=4, padx=15, pady=(0, 10), sticky="w")
        
        # Fields lists
        fields_col1 = [
            ("artist", t('artist')),
            ("album", t('album')),
            ("year", t('year')),
            ("genre", t('genre')),
        ]
        
        fields_col2 = [
            ("track_total", t('track_total')),
            ("disc_number", t('disc_num')),
            ("disc_total", t('disc_total')),
            ("composer", t('composer')),
        ]
        
        current_row = 2 
        
        # Iterate both columns together
        for i, ((k1, l1), (k2, l2)) in enumerate(zip(fields_col1, fields_col2)):
            row = current_row + i
            
            # --- Left Side (Col 0, 1) ---
            cb_var1 = ctk.BooleanVar(value=False)
            cb1 = ctk.CTkCheckBox(
                self,
                text=l1,
                variable=cb_var1,
                width=24, checkbox_width=18, checkbox_height=18,
                fg_color=COLORS['accent'], hover_color=COLORS['accent_hover'],
                border_color=COLORS['border'],
                font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"), text_color=COLORS['text_secondary']
            )
            cb1.grid(row=row, column=0, sticky="w", padx=(15, 5), pady=3)
            
            if k1 == "genre":
                entry1 = ModernComboBox(self, values=GENRE_PRESETS)
            else:
                entry1 = ModernEntry(self)
            entry1.grid(row=row, column=1, sticky="ew", padx=(0, 10), pady=3)
            
            self.checkboxes[k1] = cb_var1
            self.entries[k1] = entry1
            
            # --- Right Side (Col 2, 3) ---
            cb_var2 = ctk.BooleanVar(value=False)
            cb2 = ctk.CTkCheckBox(
                self,
                text=l2,
                variable=cb_var2,
                width=24, checkbox_width=18, checkbox_height=18,
                fg_color=COLORS['accent'], hover_color=COLORS['accent_hover'],
                border_color=COLORS['border'],
                font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"), text_color=COLORS['text_secondary']
            )
            cb2.grid(row=row, column=2, sticky="w", padx=(10, 5), pady=3)
            
            entry2 = ModernEntry(self)
            entry2.grid(row=row, column=3, sticky="ew", padx=(0, 15), pady=3)
            
            self.checkboxes[k2] = cb_var2
            self.entries[k2] = entry2
            
        current_row += len(fields_col1)
        
        # Auto-numbering
        sep = ctk.CTkFrame(self, height=1, fg_color=COLORS['border'])
        sep.grid(row=current_row, column=0, columnspan=4, sticky="ew", padx=15, pady=10)
        current_row += 1
        
        # Use a container for auto-numbering to align checkbox nicely?
        # Or just grid it.
        # User wants structure. Grid is fine.
        
        self.auto_number_var = ctk.BooleanVar(value=False)
        auto_cb = ctk.CTkCheckBox(
            self,
            text=t('auto_numbering'),
            variable=self.auto_number_var,
            checkbox_width=18, checkbox_height=18,
            fg_color=COLORS['accent'], hover_color=COLORS['accent_hover'],
            border_color=COLORS['border'],
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"), text_color=COLORS['text_secondary']
        )
        auto_cb.grid(row=current_row, column=0, columnspan=4, padx=15, pady=5, sticky="w")
        current_row += 1
        
        # Apply cover to all
        self.apply_cover_var = ctk.BooleanVar(value=False)
        cover_cb = ctk.CTkCheckBox(
            self,
            text=t('apply_cover_all'),
            variable=self.apply_cover_var,
            checkbox_width=18, checkbox_height=18,
            fg_color=COLORS['accent'], hover_color=COLORS['accent_hover'],
            border_color=COLORS['border'],
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"), text_color=COLORS['text_secondary']
        )
        cover_cb.grid(row=current_row, column=0, columnspan=4, padx=15, pady=5, sticky="w")
    
    def get_batch_values(self) -> dict:
        """Get values to apply in batch mode."""
        result = {}
        
        for key, cb_var in self.checkboxes.items():
            if cb_var.get():
                value = self.entries[key].get()
                result[key] = value
        
        result['auto_number'] = self.auto_number_var.get()
        result['apply_cover'] = self.apply_cover_var.get()
        
        return result

    def clear_values(self):
        """Clear all batch input fields."""
        for cb_var in self.checkboxes.values():
            cb_var.set(False)
        
        for entry in self.entries.values():
            if hasattr(entry, 'delete'):
                entry.delete(0, 'end')
            elif hasattr(entry, 'set'):
                entry.set("")
            
        self.auto_number_var.set(False)
        self.apply_cover_var.set(False)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION (with TkinterDnD support)
# ═══════════════════════════════════════════════════════════════════════════════

class StormTagEditor(ctk.CTk if not DND_AVAILABLE else TkinterDnD.Tk):
    """Main application window with drag and drop support."""
    
    def __init__(self):
        super().__init__()
        
        # Hide window during initialization to prevent flash
        self.withdraw()
        
        # Load settings
        self.settings = SettingsManager(CONFIG_FILE)
        
        # Initialize language from settings
        set_language(self.settings.get('language', 'ru'))
        
        # Set dark background immediately (critical for TkinterDnD)
        self['bg'] = COLORS['bg_dark']
        
        # Window setup
        self.title(f"{APP_NAME} v{APP_VERSION}")
        
        # Restore window size from settings
        width = self.settings.get('window_width', WINDOW_WIDTH)
        height = self.settings.get('window_height', WINDOW_HEIGHT)
        self.geometry(f"{width}x{height}")
        self.minsize(MIN_WIDTH, MIN_HEIGHT)
        
        # Configure appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Create main container with dark background (fills entire window)
        self.main_container = ctk.CTkFrame(self, fg_color=COLORS['bg_dark'], corner_radius=0)
        self.main_container.pack(fill="both", expand=True, padx=0, pady=0)
        self.main_container.pack_propagate(True)
        
        # Data
        self.tracks: List[TrackInfo] = []
        self.current_track: Optional[TrackInfo] = None
        self.file_items: List[FileListItem] = []
        self.current_cover_data: Optional[bytes] = None
        self.current_cover_mime: str = "image/jpeg"
        
        # Build UI (now using main_container as parent)
        self._create_header()
        self._create_main_content()
        self._create_status_bar()
        
        # Setup drag and drop
        self._setup_dnd()
        
        # Setup keyboard shortcuts
        self._setup_keyboard_shortcuts()
        
        # Set position BEFORE showing window
        self.update_idletasks()
        saved_x = self.settings.get('window_x')
        saved_y = self.settings.get('window_y')
        if saved_x is not None and saved_y is not None:
            self.geometry(f"+{saved_x}+{saved_y}")
        else:
            x = (self.winfo_screenwidth() - width) // 2
            y = (self.winfo_screenheight() - height) // 2
            self.geometry(f"+{x}+{y}")
        
        # Enable dark title bar on Windows BEFORE showing
        self._set_dark_title_bar()
        
        # Now show the fully configured window
        self.deiconify()
        
        # Bind close event to save settings
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Bind resize event
        self.bind("<Configure>", self._on_configure)
    
        # Show window with animation
        self.deiconify()
        animate_fade_in(self)
        
    def force_taskbar_icon(self):
        """Force icon to taskbar using Windows API."""
        try:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stormtageditor.ico")
            if not os.path.exists(icon_path): return
            
            # Use ctypes to load image and set it to window handle
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            if not hwnd:
                hwnd = self.winfo_id() # Fallback
                
            h_icon = ctypes.windll.user32.LoadImageW(0, icon_path, 1, 0, 0, 0x00000010 | 0x00008000)
            if h_icon:
                # WM_SETICON = 0x80
                # ICON_SMALL = 0
                # ICON_BIG = 1
                ctypes.windll.user32.SendMessageW(hwnd, 0x80, 1, h_icon)
                ctypes.windll.user32.SendMessageW(hwnd, 0x80, 0, h_icon)
        except Exception:
            pass
        
    def _on_configure(self, event=None):
        """Handle window resize/move events."""
        if event and event.widget == self:
            # Debounce - only save occasionally
            pass
    
    def _on_close(self):
        """Handle window close - save settings."""
        # Save window geometry
        self.settings.set('window_width', self.winfo_width())
        self.settings.set('window_height', self.winfo_height())
        self.settings.set('window_x', self.winfo_x())
        self.settings.set('window_y', self.winfo_y())
        self.settings.save()
        self.destroy()
    
    def _setup_keyboard_shortcuts(self):
        """Setup global keyboard shortcuts."""
        # Ctrl+S to save current
        self.bind_all('<Control-s>', lambda e: self._save_current())
        # Ctrl+Shift+S to save all
        self.bind_all('<Control-Shift-s>', lambda e: self._save_all())
        # Ctrl+O to open files
        self.bind_all('<Control-o>', lambda e: self._open_files())
        # Delete to remove selected
        self.bind_all('<Delete>', lambda e: self._remove_selected())
        # Ctrl+A to select all files (with entry protection)
        self.bind_all('<Control-a>', self._on_ctrl_a)
        self.bind_all('<Control-A>', self._on_ctrl_a)
        # Esc to deselect all files
        self.bind_all('<Escape>', lambda e: self._deselect_all())
        
        self.bind_all('<Up>', lambda e: self._on_key_nav(-1, e))
        self.bind_all('<Down>', lambda e: self._on_key_nav(1, e))
        
        # GLobal Control Key handler for layout independence
        self.bind_all('<Control-KeyPress>', self._on_global_control_key)
        
    def _on_global_control_key(self, event):
        """Handle global shortcuts via keycode."""
        key = event.keycode
        if key == 65: # A - Select All
             self._on_ctrl_a(event)
        elif key == 83: # S - Save
             # Shift check?
             if event.state & 0x0001: # Shift
                 self._save_all()
             else:
                 self._save_current()
        elif key == 79: # O - Open
             self._open_files()

    def _on_ctrl_a(self, event):
        """Handle Ctrl+A."""
        # Check if focus is on a text widget
        try:
            widget = event.widget
            # If widget is entry or text, let default behavior happen
            if isinstance(widget, (tk.Entry, tk.Text, ctk.CTkEntry)):
                  return
            # Additional check for internal entry widgets of CTk
            if "entry" in str(widget).lower():
                  return
        except:
            pass
            
        self._select_all()
        return "break"
    
    def _remove_selected(self):
        """Remove selected files from the list."""
        # Find items to remove (checked items)
        to_remove = [item for item in self.file_items if item.is_checked()]
        
        # If no checked items, try to remove the currently active one (if focused)
        # But for now, let's stick to checked items or the one being edited if it's the only one.
        if not to_remove and self.current_track:
            # Find item corresponding to current track
            for item in self.file_items:
                if item.track == self.current_track:
                    to_remove = [item]
                    break
        
        if not to_remove:
            return
            
        # Remove items
        for item in to_remove:
            # Check if this is the current track
            if item.track == self.current_track:
                self.current_track = None
                self.tag_editor.clear()
                self.cover_panel.set_cover(None)
            
            # FIX: Remove from tracks list so it can be added again
            if item.track in self.tracks:
                self.tracks.remove(item.track)

            item.destroy()
            self.file_items.remove(item)
            
        self._update_selection_count()
        self._set_status(f"Удалено из списка: {len(to_remove)}")
    
    def _set_dark_title_bar(self):
        """Enable dark title bar on Windows 10/11."""
        try:
            # Get window handle
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            
            # DWMWA_USE_IMMERSIVE_DARK_MODE = 20 (Windows 10 build 18985+)
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            
            # Set dark mode
            value = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(value),
                ctypes.sizeof(value)
            )
        except Exception:
            pass
    
    def _setup_dnd(self):
        """Setup drag and drop for the main window."""
        if DND_AVAILABLE:
            self.drop_target_register(DND_FILES)
            self.dnd_bind('<<Drop>>', self._on_drop)
            self._set_status("Drag & Drop включен")
        else:
            self._set_status("Готов к работе (без Drag & Drop)")
    
    def _on_drop(self, event):
        """Handle dropped files/folders."""
        data = event.data
        
        # Handle paths with spaces (wrapped in {})
        paths = []
        if '{' in data:
            import re
            paths = re.findall(r'\{([^}]+)\}', data)
            remaining = re.sub(r'\{[^}]+\}', '', data).strip()
            if remaining:
                paths.extend(remaining.split())
        else:
            paths = data.split()
        
        clean_paths = [p.strip() for p in paths if p.strip()]
        
        if clean_paths:
            self._handle_dropped_files(clean_paths)
        
        return event.action
    
    def _handle_dropped_files(self, paths: List[str]):
        """Process dropped files and folders."""
        all_files = []
        
        for path in paths:
            path = path.strip()
            if os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if TagEngine.is_supported(file_path):
                            all_files.append(file_path)
            elif os.path.isfile(path) and TagEngine.is_supported(path):
                all_files.append(path)
        
        if all_files:
            all_files.sort()
            self._add_files(all_files, clear=False)
        else:
            show_styled_info(self, t('info'), f"Не найдено поддерживаемых аудио файлов\n(WAV, MP3, FLAC, M4A, OGG)")
    
    def _create_header(self):
        """Create the header with toolbar."""
        header = ctk.CTkFrame(self.main_container, fg_color=COLORS['bg_main'], height=60)
        header.pack(fill="x", padx=10, pady=(10, 5))
        header.pack_propagate(False)
        
        # Logo/Title
        logo_frame = ctk.CTkFrame(header, fg_color="transparent")
        logo_frame.pack(side="left", padx=15)
        
        logo = ctk.CTkLabel(
            logo_frame,
            text="⚡ STORM TAG EDITOR",
            font=ctk.CTkFont(family=FONT_FAMILY, size=18, weight="bold"),
            text_color=COLORS['accent']
        )
        logo.pack(side="left")
        
        version = ctk.CTkLabel(
            logo_frame,
            text=f"  v{APP_VERSION}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=COLORS['text_muted']
        )
        version.pack(side="left")
        
        # Toolbar buttons
        toolbar = ctk.CTkFrame(header, fg_color="transparent")
        toolbar.pack(side="right", padx=15)
        
        ModernButton(
            toolbar,
            text=t('open_files'),
            command=self._open_files
        ).pack(side="left", padx=3)
        
        ModernButton(
            toolbar,
            text=t('open_folder'),
            command=self._open_folder
        ).pack(side="left", padx=3)
        
        ModernButton(
            toolbar,
            text=t('save'),
            accent=True,
            command=self._save_current
        ).pack(side="left", padx=3)
        
        self.save_all_btn = ModernButton(
            toolbar,
            text=t('save_all'),
            accent=True,
            command=self._save_all
        )
        self.save_all_btn.pack(side="left", padx=5)
        
        # Converter Button
        self.converter_btn = ModernButton(
            toolbar,
            text=t('converter_title'),
            command=self._open_converter,
            width=140,
            fg_color=COLORS['highlight'],
            hover_color=COLORS['highlight_hover']
        )
        self.converter_btn.pack(side="left", padx=5)
        
        # Auto-update checkbox
        self.auto_update_var = ctk.BooleanVar(value=self.settings.get('auto_update', True))
        auto_update_cb = ctk.CTkCheckBox(
            toolbar,
            text=t('auto_update'),
            variable=self.auto_update_var,
            command=self._on_auto_update_change,
            checkbox_width=18,
            checkbox_height=18,
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            border_color=COLORS['border'],
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=COLORS['text']
        )
        auto_update_cb.pack(side="left", padx=(20, 3))
        
        # Language switch button
        current_lang = self.settings.get('language', 'ru')
        lang_text = "EN" if current_lang == 'ru' else "RU"
        self.lang_btn = ModernButton(
            toolbar,
            text=lang_text,
            command=self._toggle_language
        )
        self.lang_btn.pack(side="left", padx=(10, 3))
    
    def _create_main_content(self):
        """Create the main content area."""
        main = ctk.CTkFrame(self.main_container, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Configure grid with resizable columns
        main.grid_columnconfigure(0, weight=1, minsize=280)  # File list
        main.grid_columnconfigure(1, weight=2, minsize=400)  # Tag editor
        main.grid_columnconfigure(2, weight=1, minsize=300)  # Cover + Batch
        main.grid_rowconfigure(0, weight=1)
        
        # === Left panel: File list ===
        left_frame = ctk.CTkFrame(main, fg_color=COLORS['bg_panel'], corner_radius=12)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # File list header
        list_header = ctk.CTkFrame(left_frame, fg_color="transparent")
        list_header.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(
            list_header,
            text=t('files'),
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            text_color=COLORS['text']
        ).pack(side="left")
        
        self.file_count_label = ctk.CTkLabel(
            list_header,
            text=t('files_count', 0),
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=COLORS['text_muted']
        )
        self.file_count_label.pack(side="right")
        
        # Selection buttons
        sel_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        sel_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        ctk.CTkButton(
            sel_frame,
            text=t('select_all'),
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            fg_color=COLORS['bg_input'],
            hover_color=COLORS['bg_hover'],
            height=28,
            corner_radius=6,
            command=self._select_all
        ).pack(side="left", fill="x", expand=True, padx=(0, 2))
        
        ctk.CTkButton(
            sel_frame,
            text=t('deselect_all'),
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            fg_color=COLORS['bg_input'],
            hover_color=COLORS['bg_hover'],
            height=28,
            corner_radius=6,
            command=self._deselect_all
        ).pack(side="left", fill="x", expand=True, padx=(2, 0))
        
        # Drop zone label (shown when no files)
        self.drop_zone_label = ctk.CTkLabel(
            left_frame,
            text=t('drop_hint'),
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=COLORS['text_muted'],
            justify="center"
        )
        self.drop_zone_label.pack(expand=True, pady=50)
        
        # File list scroll area (hidden initially)
        self.file_list = ctk.CTkScrollableFrame(
            left_frame,
            fg_color="transparent",
            scrollbar_button_color=COLORS['bg_input'],
            scrollbar_button_hover_color=COLORS['bg_hover']
        )
        
        self.left_panel = left_frame
        
        # === Center panel: Tag editor ===
        self.tag_editor = TagEditorPanel(main, on_track_number_change=self._on_track_number_live_update)
        self.tag_editor.grid(row=0, column=1, sticky="nsew", padx=5)
        
        # === Right panel: Cover + Batch ===
        right_frame = ctk.CTkFrame(main, fg_color="transparent")
        right_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 0))
        
        # Cover art panel
        self.cover_panel = CoverArtPanel(
            right_frame,
            on_cover_change=self._on_cover_change
        )
        self.cover_panel.pack(fill="x", pady=(0, 10))
        
        # Batch editor panel
        self.batch_editor = BatchEditorPanel(right_frame)
        self.batch_editor.pack(fill="both", expand=True)
    
    def _create_status_bar(self):
        """Create the status bar."""
        status = ctk.CTkFrame(self.main_container, fg_color=COLORS['bg_main'], height=35)
        status.pack(fill="x", padx=10, pady=(5, 10))
        status.pack_propagate(False)
        
        self.status_label = ctk.CTkLabel(
            status,
            text="Готов к работе",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=COLORS['text_secondary']
        )
        self.status_label.pack(side="left", padx=15)
        
        self.selected_label = ctk.CTkLabel(
            status,
            text="Выбрано: 0",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=COLORS['text_muted']
        )
        self.selected_label.pack(side="right", padx=15)
        
        # Progress bar (hidden by default)
        self.progress = ctk.CTkProgressBar(
            status,
            fg_color=COLORS['bg_input'],
            progress_color=COLORS['accent'],
            height=6,
            width=200
        )
        self.progress.set(0)
    
    # === File Operations ===
    
    def _open_files(self):
        """Open audio files."""
        files = filedialog.askopenfilenames(
            title="Выберите аудио файлы",
            filetypes=[
                ("Аудио файлы", "*.mp3 *.flac *.m4a *.ogg *.oga *.wav"),
                ("MP3", "*.mp3"),
                ("FLAC", "*.flac"),
                ("M4A", "*.m4a"),
                ("OGG", "*.ogg *.oga"),
                ("WAV", "*.wav"),
                ("Все файлы", "*.*")
            ]
        )
        
        if files:
            self._add_files(list(files), clear=False)
            
    def _open_converter(self):
        """Open audio converter dialog."""
        # Get checked items
        files_to_convert = [item.track.file_path for item in self.file_items if item.is_checked()]
        
        # If no checked, use ALL files
        if not files_to_convert:
            files_to_convert = [item.track.file_path for item in self.file_items]
            
        if not files_to_convert:
            show_styled_info(self, t('info'), "Нет файлов для конвертации\nОткройте файлы и попробуйте снова.", "ℹ️")
            return
            
        # Open dialog
        dialog = ConverterDialog(self, files_to_convert)
    
    def _open_folder(self):
        """Open a folder with audio files."""
        folder = filedialog.askdirectory(title="Выберите папку с музыкой")
        
        if folder:
            files = TagEngine.get_supported_files(folder)
            if files:
                self._add_files(files, clear=False)
            else:
                messagebox.showinfo("Информация", "В папке не найдено поддерживаемых аудио файлов")
    

    def _load_files_chunked(self):
        """Process loading queue in chunks."""
        CHUNK_SIZE = 50 # Optimized chunk size
        
        if not hasattr(self, '_load_queue') or not self._load_queue:
            # Done
            self.progress.stop()
            self.progress.pack_forget()
            count = len(self.file_items)
            self._set_status(f"Загружено {count} файлов")
            self.file_count_label.configure(text=f"{count} файлов")
            
            # Select first if any
            if self.file_items:
                self._on_file_select(self.file_items[0])
            return
            
        # Process chunk
        paths_chunk = self._load_queue[:CHUNK_SIZE]
        self._load_queue = self._load_queue[CHUNK_SIZE:]
        
        for path in paths_chunk:
            track = TagEngine.read_tags(path)
            if track:
                self.tracks.append(track)
                item = FileListItem(self.file_list, track, on_select=self._on_file_select)
                item.pack(fill="x", pady=2)
                self.file_items.append(item)
                
        # Update status
        self._set_status(f"Загрузка... ({len(self.file_items)})")
        
        # Next chunk
        self.after(5, self._load_files_chunked)

    def _add_files(self, file_paths: List[str], clear: bool = False):
        """Add audio files to the editor (async)."""
        self._set_status("Обработка файлов...")
        
        if clear:
            # Clear
            self.tag_editor.clear()
            self.cover_panel.set_cover(None)
            self.current_track = None
            self.current_cover_data = None
            self.current_cover_mime = "image/jpeg"
            self.last_active_index = None # For Shift-selection
            
            for item in self.file_items:
                item.destroy()
            self.file_items.clear()
            self.tracks.clear()
            self._load_queue = list(file_paths)
        else:
             # Filter duplicates
             existing_paths = {t.file_path for t in self.tracks}
             new_files = [p for p in file_paths if p not in existing_paths]
             
             if not new_files:
                 if not clear and file_paths: 
                     self._set_status("Файлы уже в списке")
                 return
             
             if not hasattr(self, '_load_queue'):
                 self._load_queue = []
             self._load_queue.extend(new_files)
        
        self.drop_zone_label.pack_forget()
        self.file_list.pack(fill="both", expand=True, padx=5, pady=(0, 10))
        
        # Show progress
        self.progress.pack(side="right", padx=15)
        self.progress.start()
        
        self._set_status("Начало загрузки...")
        
        # Start processing
        self.after(50, self._load_files_chunked)

    def _on_ctrl_a(self, event):
        """Handle Ctrl+A."""
        # Removed widget check to force functionality
        self._select_all()
        return "break"

    def _on_key_nav(self, direction, event):
        """Handle arrow key navigation."""
        # Skip if focusing text widgets
        try:
            widget = event.widget
            if isinstance(widget, (tk.Entry, tk.Text, ctk.CTkEntry)):
                  return
            if "entry" in str(widget).lower():
                  return
        except:
            pass
            
        if not self.file_items:
            return "break"
            
        # Get current index
        idx = -1
        if self.current_track:
            for i, item in enumerate(self.file_items):
                if item.track == self.current_track:
                    idx = i
                    break
        
        new_idx = idx + direction
        
        # Clamp
        count = len(self.file_items)
        if new_idx < 0:
            new_idx = 0
        elif new_idx >= count:
            new_idx = count - 1
            
        if 0 <= new_idx < count:
            self._on_file_select(self.file_items[new_idx])
            
            # Ensure visible
            # Note: CTkScrollableFrame doesn't expose easy 'see' method, 
            # but we update selection which handles logic
            pass
            
        return "break"
    
    def _on_file_select(self, item: FileListItem, event=None):
        """Handle file selection with modifiers."""
        
        # PERSISTENCE: Save current UI values to current track before switching
        if self.current_track:
             self._update_track_from_ui(self.current_track)
        
        idx = self.file_items.index(item)
        shift = (event.state & 0x0001) if event else False
        ctrl = (event.state & 0x0004) if event else False
        
        # Deselect all visuals first
        for i in self.file_items:
            i.set_selected(False)
        
        # Logic for selection (Checkboxes)
        if shift and self.last_active_index is not None:
            # Range Select
            start = min(self.last_active_index, idx)
            end = max(self.last_active_index, idx)
            # Uncheck all if not ctrl
            if not ctrl:
                 for i in self.file_items:
                    i.set_checked(False)
            # Check range
            for i in range(start, end + 1):
                self.file_items[i].set_checked(True)
                
        elif ctrl:
            # Toggle Single
            item.set_checked(not item.is_checked())
            
        else:
            # Normal Click
            # Uncheck all
            for i in self.file_items:
                i.set_checked(False)
            # Check this
            item.set_checked(True)
        
        # Always set this as active/focused
        item.set_selected(True)
        self.current_track = item.track
        self.last_active_index = idx
        
        # Load into editor
        self.tag_editor.load_track(item.track)
        
        # Clear batch editor inputs as per user request ("Clear on File Change")
        self.batch_editor.clear_values()
        
        # Update cover
        self.current_cover_data = item.track.cover_data
        self.current_cover_mime = item.track.cover_mime
        self.cover_panel.set_cover(item.track.cover_data)
        
        # Update selection count
        self._update_selection_count()
    
    def _select_all(self):
        """Select all files."""
        for item in self.file_items:
            item.set_checked(True)
        self._update_selection_count()
    
    def _deselect_all(self):
        """Deselect all files."""
        for item in self.file_items:
            item.set_checked(False)
        self._update_selection_count()
    
    
    def _on_track_number_live_update(self, new_value):
        """Update the file list item immediately when track number changes."""
        if not self.current_track:
             return
             
        # Find item
        for item in self.file_items:
            if item.track == self.current_track:
                title = self.current_track.title if self.current_track.title else self.current_track.filename
                if new_value:
                     title = f"{new_value}. {title}"
                # If new_value is empty, just title
                
                item.title_label.configure(text=title)
                break

    def _update_selection_count(self):
        """Update the selection count in status bar."""
        count = sum(1 for item in self.file_items if item.is_checked())
        self.selected_label.configure(text=f"Выбрано: {count}")
    
    # === Cover Operations ===
    
    def _on_cover_change(self, cover_data: Optional[bytes], cover_mime: str):
        """Handle cover art change."""
        self.current_cover_data = cover_data
        self.current_cover_mime = cover_mime if cover_mime else "image/jpeg"
        
    def _update_track_from_ui(self, track: TrackInfo):
        """Update track object with values from UI (Memory Save)."""
        if not track: return
        try:
            values = self.tag_editor.get_values()
            track.title = values['title']
            track.artist = values['artist']
            track.album = values['album']
            track.year = values['year']
            track.genre = values['genre']
            track.track_number = values['track_number']
            track.track_total = values['track_total']
            track.disc_number = values['disc_number']
            track.disc_total = values['disc_total']
            track.composer = values['composer']
            track.comment = values['comment']
            track.cover_data = self.cover_panel.current_cover_data
            track.cover_mime = self.current_cover_mime
        except:
            pass
    
    # === Save Operations ===
    
    def _save_current(self):
        """Save the currently selected file."""
        if not self.current_track:
            show_styled_info(self, t('info'), t('select_file_to_save'))
            return
        
        # Get values from editor
        values = self.tag_editor.get_values()
        
        # Update track
        self.current_track.title = values['title']
        self.current_track.artist = values['artist']
        self.current_track.album = values['album']
        self.current_track.year = values['year']
        self.current_track.genre = values['genre']
        self.current_track.track_number = values['track_number']
        self.current_track.track_total = values['track_total']
        self.current_track.disc_number = values['disc_number']
        self.current_track.disc_total = values['disc_total']
        self.current_track.composer = values['composer']
        self.current_track.comment = values['comment']
        
        # Update cover from panel
        self.current_track.cover_data = self.cover_panel.current_cover_data
        self.current_track.cover_mime = self.current_cover_mime
        
        # Save
        if TagEngine.write_tags(self.current_track):
            self._set_status(f"Сохранено: {self.current_track.filename}")
            
            # Rename file if track# and title exist
            self._try_rename_file(self.current_track)
            
            # Update list item display
            for item in self.file_items:
                if item.track == self.current_track:
                    title = self.current_track.title if self.current_track.title else self.current_track.filename
                    if self.current_track.track_number:
                        title = f"{self.current_track.track_number}. {title}"
                    item.title_label.configure(text=title)
                    subtitle = f"{self.current_track.artist} - {self.current_track.album}"
                    item.subtitle_label.configure(text=subtitle if self.current_track.artist or self.current_track.album else self.current_track.format_name)
                    break
        else:
            self._set_status(f"Ошибка сохранения: {self.current_track.filename}")
            show_styled_info(self, t('error'), t('save_error'))
    
    def _try_rename_file(self, track: TrackInfo):
        """Rename file to 'Track. Title' format if possible."""
        try:
            if not track.track_number or not track.title:
                return
            
            # Sanitize filename
            new_name = f"{track.track_number}. {track.title}"
            clean_name = TagEngine.sanitize_filename(new_name)
            
            # Preserve extension
            ext = os.path.splitext(track.file_path)[1]
            new_filename = clean_name + ext
            
            # Check if name is different
            if new_filename == track.filename:
                return
                
            dir_path = os.path.dirname(track.file_path)
            new_path = os.path.join(dir_path, new_filename)
            
            # Rename
            os.rename(track.file_path, new_path)
            
            # Update track info
            track.file_path = new_path
            # track.filename property is dynamic based on file_path, but TrackInfo is a dataclass?
            # TrackInfo.filename is a property: return os.path.basename(self.file_path)
            # So updating file_path is enough.
            
        except Exception as e:
            print(f"Rename error: {e}")

    def _save_all(self):
        """Save all checked files with batch settings."""
        # Ensure current track is updated from UI values first
        if self.current_track:
            self._update_track_from_ui(self.current_track)
            
        # Save ALL files, regardless of checked status (User Request)
        # However, we should respect "Checked" if user wants batch logic?
        # User said: "Save all should act on ALL FILES, regardless of whether they are selected or not!"
        # This implies checking is ignored for scope.
        checked_items = self.file_items # ALL items
        
        # But for Batch Values application...
        # If user checked items, maybe they expect Batch ONLY to apply to checked?
        # But "Save All" implies one operation.
        # If Batch settings exist, and we save ALL, do we apply Batch to ALL?
        # Yes, standard behavior if scope becomes "All".
        # If user wants to exclude file from batch but save it... they can't in this model easily.
        # But this is what requested.
        
        if not checked_items:
            show_styled_info(self, t('info'), t('select_files_to_save'))
            return
        
        batch_values = self.batch_editor.get_batch_values()
        
        self._set_status("Сохранение...")
        self.progress.pack(side="right", padx=15)
        
        saved = 0
        total = len(checked_items)
        
        for i, item in enumerate(checked_items):
            track = item.track
            
            # Apply batch values
            if 'artist' in batch_values:
                track.artist = batch_values['artist']
            if 'album' in batch_values:
                track.album = batch_values['album']
            if 'year' in batch_values:
                track.year = batch_values['year']
            if 'genre' in batch_values:
                track.genre = batch_values['genre']
            if 'composer' in batch_values:
                track.composer = batch_values['composer']
            if 'disc_number' in batch_values:
                track.disc_number = batch_values['disc_number']
            if 'disc_total' in batch_values:
                track.disc_total = batch_values['disc_total']
            if 'track_total' in batch_values:
                track.track_total = batch_values['track_total']
            
            # Auto-numbering
            if batch_values.get('auto_number'):
                track.track_number = str(i + 1)
                track.track_total = str(total)
            
            # Apply cover
            if batch_values.get('apply_cover') and self.cover_panel.current_cover_data:
                track.cover_data = self.cover_panel.current_cover_data
                track.cover_mime = self.current_cover_mime
            
            # Save
            if TagEngine.write_tags(track):
                saved += 1
                
                # Rename
                self._try_rename_file(track)
                
                # Update list display
                title = track.title if track.title else track.filename
                if track.track_number:
                     title = f"{track.track_number}. {title}"
                item.title_label.configure(text=title)
                subtitle = f"{track.artist} - {track.album}"
                item.subtitle_label.configure(text=subtitle if track.artist or track.album else track.format_name)
            
            # Update progress
            self.progress.set((i + 1) / total)
            self.update_idletasks()
        
        self.progress.pack_forget()
        self._set_status(f"Сохранено {saved} из {total} файлов")
        
        # Refresh current selection
        if self.current_track:
            self.tag_editor.load_track(self.current_track)
    
    def _on_auto_update_change(self):
        """Handle auto-update checkbox change."""
        self.settings.set('auto_update', self.auto_update_var.get())
        self.settings.save()
    
    def _toggle_language(self):
        """Toggle between Russian and English."""
        current = self.settings.get('language', 'ru')
        new_lang = 'en' if current == 'ru' else 'ru'
        self.settings.set('language', new_lang)
        self.settings.save()
        
        # Update button text for immediate feedback
        self.lang_btn.configure(text="🇬🇧 EN" if new_lang == 'ru' else "🇷🇺 RU")
        
        # Show styled restart dialog
        self._show_language_dialog(new_lang)
    
    def _show_language_dialog(self, new_lang: str):
        """Show styled language change dialog with restart button."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("🌐 Language / Язык")
        dialog.geometry("550x180")
        dialog.resizable(False, False)
        dialog.configure(fg_color=COLORS['bg_dark'])
        dialog.transient(self)
        dialog.grab_set()
        
        # Center on parent
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 550) // 2
        y = self.winfo_y() + (self.winfo_height() - 180) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Icon and message
        msg = "Restart the app to apply the new language" if new_lang == 'en' else "Перезапустите программу для применения нового языка"
        
        ctk.CTkLabel(
            dialog,
            text="🌐",
            font=ctk.CTkFont(family=FONT_FAMILY, size=40),
            text_color=COLORS['accent']
        ).pack(pady=(25, 10))
        
        ctk.CTkLabel(
            dialog,
            text=msg,
            font=ctk.CTkFont(family=FONT_FAMILY, size=14),
            text_color=COLORS['text']
        ).pack(pady=(0, 20))
        
        # Buttons
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack()
        
        def restart_app():
            dialog.destroy()
            self._on_close()
            # Restart the application
            os.execl(sys.executable, sys.executable, *sys.argv)
        
        ModernButton(
            btn_frame,
            text="🔄 Restart" if new_lang == 'en' else "🔄 Перезапустить",
            accent=True,
            command=restart_app
        ).pack(side="left", padx=5)
        
        ModernButton(
            btn_frame,
            text="Later" if new_lang == 'en' else "Позже",
            command=dialog.destroy
        ).pack(side="left", padx=5)
    
    def _set_status(self, text: str):
        """Update status bar text."""
        self.status_label.configure(text=text)
        self.update_idletasks()


# ═══════════════════════════════════════════════════════════════════════════════
# AUTO-UPDATE SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class UpdateChecker:
    """Checks for updates from GitHub releases with rate-limit protection."""
    
    # Cache file path
    CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'update_cache.json')
    CACHE_DURATION = 3600  # 1 hour in seconds
    
    @staticmethod
    def check_for_update() -> Optional[dict]:
        """Check if a new version is available. Returns release info or None."""
        
        # Check cache first to avoid rate limiting
        try:
            if os.path.exists(UpdateChecker.CACHE_FILE):
                with open(UpdateChecker.CACHE_FILE, 'r') as f:
                    cache = json.load(f)
                    last_check = cache.get('last_check', 0)
                    cached_result = cache.get('result')
                    
                    # If checked within last hour, use cached result
                    if time.time() - last_check < UpdateChecker.CACHE_DURATION:
                        print(f"[UPDATE] Using cached result (checked {int(time.time() - last_check)}s ago)")
                        return cached_result
        except:
            pass
        
        try:
            req = urllib.request.Request(
                GITHUB_API_URL,
                headers={'User-Agent': 'StormTagEditor/1.0'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                
            latest_version = data.get('tag_name', '').lstrip('v').strip()
            print(f"[UPDATE] Current: {APP_VERSION}, Latest on GitHub: {latest_version}")
            
            result = None
            
            # Compare versions
            if UpdateChecker._is_newer(latest_version, APP_VERSION):
                print(f"[UPDATE] New version available!")
                # Find .exe asset
                assets = data.get('assets', [])
                print(f"[UPDATE] Found {len(assets)} assets")
                
                for asset in assets:
                    name = asset.get('name', '')
                    print(f"[UPDATE] Asset: {name}")
                    if name.endswith('.exe'):
                        print(f"[UPDATE] Found executable asset: {name}")
                        result = {
                            'version': latest_version,
                            'download_url': asset.get('browser_download_url'),
                            'name': name,
                            'body': data.get('body', ''),
                        }
                        break
                if not result:
                    print("[UPDATE] No .exe asset found in release")
            else:
                print(f"[UPDATE] No update needed")
            
            # Save to cache
            try:
                with open(UpdateChecker.CACHE_FILE, 'w') as f:
                    json.dump({'last_check': time.time(), 'result': result}, f)
            except:
                pass
            
            return result
            
        except Exception as e:
            print(f"[UPDATE] Check failed: {e}")
            return None
    
    @staticmethod
    def _is_newer(latest: str, current: str) -> bool:
        """Compare version strings."""
        try:
            latest_parts = [int(x) for x in latest.split('.')]
            current_parts = [int(x) for x in current.split('.')]
            return latest_parts > current_parts
        except:
            return False
    
    @staticmethod
    def download_update(url: str, dest_path: str, progress_callback=None) -> bool:
        """Download update file."""
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'StormTagEditor'})
            with urllib.request.urlopen(req, timeout=60) as response:
                total = int(response.headers.get('Content-Length', 0))
                downloaded = 0
                chunk_size = 8192
                
                with open(dest_path, 'wb') as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total:
                            progress_callback(downloaded / total)
            return True
        except Exception as e:
            print(f"Download failed: {e}")
            return False


class UpdateDialog(ctk.CTkToplevel):
    """Styled update dialog."""
    
    def __init__(self, parent, update_info: dict):
        super().__init__(parent)
        
        self.update_info = update_info
        self.result = False
        
        self.title("Доступно обновление")
        self.geometry("450x300")
        self.resizable(False, False)
        self.configure(fg_color=COLORS['bg_dark'])
        
        # Center on parent
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        
        # Center window
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 450) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 300) // 2
        self.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        # Header
        header = ctk.CTkLabel(
            self,
            text="⚡ Доступна новая версия!",
            font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"),
            text_color=COLORS['accent']
        )
        header.pack(pady=(25, 15))
        
        # Version info
        version_frame = ctk.CTkFrame(self, fg_color=COLORS['bg_panel'], corner_radius=10)
        version_frame.pack(fill="x", padx=30, pady=10)
        
        ctk.CTkLabel(
            version_frame,
            text=f"Текущая версия: {APP_VERSION}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=COLORS['text_muted']
        ).pack(pady=(15, 5))
        
        ctk.CTkLabel(
            version_frame,
            text=f"Новая версия: {self.update_info['version']}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
            text_color=COLORS['success']
        ).pack(pady=(5, 15))
        
        # Progress bar (hidden initially)
        self.progress = ctk.CTkProgressBar(
            self,
            fg_color=COLORS['bg_input'],
            progress_color=COLORS['accent'],
            height=8,
            width=350
        )
        self.progress.set(0)
        
        self.progress_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=COLORS['text_muted']
        )
        
        # Buttons
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(pady=25)
        
        self.update_btn = ModernButton(
            self.btn_frame,
            text="🔄 Обновить",
            accent=True,
            command=self._do_update
        )
        self.update_btn.pack(side="left", padx=10)
        
        self.cancel_btn = ModernButton(
            self.btn_frame,
            text="Позже",
            command=self._cancel
        )
        self.cancel_btn.pack(side="left", padx=10)
    
    def _do_update(self):
        """Start the update process."""
        self.update_btn.configure(state="disabled")
        self.cancel_btn.configure(state="disabled")
        
        self.progress.pack(pady=(0, 5))
        self.progress_label.pack()
        self.progress_label.configure(text="Загрузка...")
        
        # Download in thread
        threading.Thread(target=self._download_thread, daemon=True).start()
    
    def _download_thread(self):
        """Download update in background."""
        url = self.update_info['download_url']
        exe_name = self.update_info['name']
        
        # Download to temp location
        temp_path = os.path.join(os.path.dirname(sys.executable), f"update_{exe_name}")
        
        def progress_cb(p):
            self.after(0, lambda: self.progress.set(p))
            self.after(0, lambda: self.progress_label.configure(text=f"Загрузка: {int(p*100)}%"))
        
        if UpdateChecker.download_update(url, temp_path, progress_cb):
            self.after(0, lambda: self._finish_update(temp_path, exe_name))
        else:
            self.after(0, lambda: self._download_failed())
    
    def _finish_update(self, temp_path: str, exe_name: str):
        """Complete the update process."""
        self.progress_label.configure(text="Применение обновления...")
        
        # Create batch script to replace exe and restart
        current_exe = sys.executable
        # Use current name to preserve specific naming (e.g. spaces vs dots)
        new_exe = current_exe
        
        batch_content = f'''@echo off
timeout /t 3 /nobreak > nul
del "{current_exe}" 2>nul
move "{temp_path}" "{new_exe}"
set PYTHONHOME=
set PYTHONPATH=
set TCL_LIBRARY=
set TK_LIBRARY=
set _MEIPASS2=
start "" "{new_exe}"
del "%~f0"
'''
        batch_path = os.path.join(os.path.dirname(current_exe), "update.bat")
        
        try:
            with open(batch_path, 'w') as f:
                f.write(batch_content)
            
            # Run batch and exit
            subprocess.Popen(['cmd', '/c', batch_path], shell=True)
            self.result = True
            self.master.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось применить обновление: {e}")
            self._cancel()
    
    def _download_failed(self):
        """Handle download failure."""
        self.progress_label.configure(text="Ошибка загрузки!")
        self.update_btn.configure(state="normal")
        self.cancel_btn.configure(state="normal")
    
    def _cancel(self):
        self.result = False
        self.destroy()


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Main entry point."""
    # Initialize language BEFORE creating app (so all UI gets correct language)
    try:
        import json
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                set_language(config.get('language', 'ru'))
    except:
        pass
    
    # Set App ID for Taskbar Icon - Fix syntax error
    try:
        myappid = 'StormDev.StormTagEditor.Pro.v0021'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except:
        pass
    
    app = StormTagEditor()
    
    # Check for updates if enabled
    if app.settings.get('auto_update', True):
        def check_update():
            update_info = UpdateChecker.check_for_update()
            if update_info:
                app.after(0, lambda: UpdateDialog(app, update_info))
        
        threading.Thread(target=check_update, daemon=True).start()
    
    app.mainloop()


if __name__ == "__main__":
    main()

