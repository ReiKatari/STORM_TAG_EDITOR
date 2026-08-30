"""
Storm Tag Editor - Converter Dialog
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import threading
import os
import time
from typing import List

from localization import t
from converter_engine import ConverterEngine, CONVERTER_FORMATS

from ui_utils import COLORS, ModernButton, animate_fade_in, FONT_FAMILY, show_styled_info # Added show_styled_info

try:
    from tkinterdnd2 import DND_FILES
except ImportError:
    DND_FILES = None

class ConverterDialog(ctk.CTkToplevel):
    def __init__(self, parent, files: List[str]):
        super().__init__(parent)
        
        self.files = files
        self.engine = ConverterEngine()
        
        # Window setup
        self.title(t('converter_title'))
        
        # Geometry & Centering
        width = 700
        height = 550
        
        # Calculate center relative to parent
        try:
             x = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
             y = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
        except:
             # Fallback to screen center
             screen_width = self.winfo_screenwidth()
             screen_height = self.winfo_screenheight()
             x = (screen_width - width) // 2
             y = (screen_height - height) // 2
             
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.resizable(False, False)
        
        # Center window behavior
        self.transient(parent)
        self.grab_set()
        
        # Animate
        animate_fade_in(self)
        
        # UI State
        self.format_var = ctk.StringVar(value='MP3')
        self.quality_var = ctk.StringVar()
        self.output_path_var = ctk.StringVar(value=t('same_as_source'))
        self.is_custom_output = False
        self.stop_conversion = False
        
        self._create_widgets()
        self._update_quality_options()
        
        # focus
        self.after(100, self.lift)
        self.after(100, self.focus_force)
        
    def _create_widgets(self):
        # Main container
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        
        # --- Top Section: Files ---
        self.files_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.files_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=(20, 10))
        self.files_frame.columnconfigure(0, weight=1)
        self.files_frame.rowconfigure(1, weight=1)
        
        # Header
        header_lbl = ctk.CTkLabel(
            self.files_frame, 
            text=f"{t('source_files')} ({len(self.files)})", 
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
            text_color=COLORS['text']
        )
        header_lbl.grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        # List
        self.file_list = ctk.CTkTextbox(
            self.files_frame,
            fg_color=COLORS['bg_input'],
            text_color=COLORS['text_secondary'],
            font=ctk.CTkFont(family=FONT_FAMILY, size=13)
        )
        self.file_list.grid(row=1, column=0, sticky="nsew")
        
        # Populate list
        text = "\n".join([os.path.basename(f) for f in self.files])
        self.file_list.insert("0.0", text)
        self.file_list.configure(state="disabled")
        
        # --- Middle Section: Settings ---
        self.settings_frame = ctk.CTkFrame(self, fg_color=COLORS['bg_panel'], corner_radius=10)
        self.settings_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        
        # Format
        ctk.CTkLabel(self.settings_frame, text=t('format'), text_color=COLORS['text'], font=ctk.CTkFont(family=FONT_FAMILY, size=13)).grid(row=0, column=0, padx=15, pady=15, sticky="w")
        self.format_combo = ctk.CTkComboBox(
            self.settings_frame,
            values=list(CONVERTER_FORMATS.keys()),
            variable=self.format_var,
            command=self._update_quality_options,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            dropdown_font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            state="readonly",
            button_color=COLORS['accent'],
            border_color=COLORS['bg_input'],
            dropdown_fg_color=COLORS['bg_input']
        )
        self.format_combo.grid(row=0, column=1, padx=15, pady=15, sticky="ew")
        
        # Quality
        ctk.CTkLabel(self.settings_frame, text=t('quality'), text_color=COLORS['text']).grid(row=0, column=2, padx=15, pady=15, sticky="w")
        self.quality_combo = ctk.CTkComboBox(
            self.settings_frame,
            variable=self.quality_var,
            state="readonly",
            button_color=COLORS['accent'],
            border_color=COLORS['bg_input'],
            dropdown_fg_color=COLORS['bg_input']
        )
        self.quality_combo.grid(row=0, column=3, padx=15, pady=15, sticky="ew")
        
        # Output
        ctk.CTkLabel(self.settings_frame, text=t('output_folder'), text_color=COLORS['text']).grid(row=1, column=0, padx=15, pady=(0,15), sticky="w")
        self.output_entry = ctk.CTkEntry(
            self.settings_frame,
            textvariable=self.output_path_var,
            fg_color=COLORS['bg_input'],
            border_width=0,
            text_color=COLORS['text']
        )
        self.output_entry.grid(row=1, column=1, columnspan=2, padx=15, pady=(0,15), sticky="ew")
        self.output_entry.grid(row=1, column=1, columnspan=2, padx=15, pady=(0,15), sticky="ew")

        # Studio Processing Checkbox
        self.studio_proc_var = ctk.BooleanVar(value=False)
        self.studio_proc_chk = ctk.CTkCheckBox(
            self.settings_frame,
            text=t('studio_processing'),
            variable=self.studio_proc_var,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color='#2CC985', # Green text as requested/implied or just green checkbox
            fg_color='#2CC985',   # Green fill
            hover_color='#25A970',
            border_color=COLORS['text_secondary']
        )
        self.studio_proc_chk.grid(row=2, column=1, columnspan=2, padx=15, pady=(0,15), sticky="w")

        # self.output_entry.configure(state="disabled") # Read-only - NO, enable for DND/Typing if needed
        # But user wants validation. Let's keep it enabled but readonly-ish?
        # Standard Entry supports DND if enabled.
        # If disabled, DND might not work on some platforms.
        # Let's keep it normal but maybe readonly state blocks DND?
        # Usually drop works. Let's try normal state for now.
        
        # Enable DND
        if DND_FILES:
            try:
                self.output_entry.drop_target_register(DND_FILES)
                self.output_entry.dnd_bind('<<Drop>>', self._on_drop)
            except:
                pass
        
        self.browse_btn = ctk.CTkButton(
            self.settings_frame,
            text=t('browse'),
            width=80,
            fg_color=COLORS['bg_input'],
            hover_color=COLORS['bg_hover'],
            command=self._browse_output
        )
        self.browse_btn.grid(row=1, column=3, padx=15, pady=(0,15), sticky="ew")
        
        self.settings_frame.columnconfigure(1, weight=1)
        self.settings_frame.columnconfigure(3, weight=1)
        
        # --- Bottom Section: Progress & Actions ---
        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=20)
        
        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(self.bottom_frame, height=12)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(0, 10))
        self.progress_bar.configure(progress_color=COLORS['accent'])
        
        # Status Label
        self.status_label = ctk.CTkLabel(self.bottom_frame, text="", text_color=COLORS['text_secondary'])
        self.status_label.pack(side="left")
        
        # Buttons
        self.convert_btn = ctk.CTkButton(
            self.bottom_frame,
            text=t('convert'),
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            command=self._start_conversion
        )
        self.convert_btn.pack(side="right", padx=(10, 0))
        
        self.cancel_btn = ctk.CTkButton(
            self.bottom_frame,
            text=t('cancel'),
            fg_color=COLORS['bg_input'],
            hover_color=COLORS['bg_hover'],
            command=self._on_cancel
        )
        self.cancel_btn.pack(side="right")
        
        # Check FFMPEG
        if not self.engine.check_ffmpeg():
            self.status_label.configure(text=t('ffmpeg_not_found'), text_color=COLORS['error'])
            self.convert_btn.configure(state="disabled")
            # Defer showing the warning slightly so the window renders first
            self.after(200, lambda: show_styled_info(self, t('warning'), t('ffmpeg_hint'), "⚠️"))

    def _update_quality_options(self, _=None):
        fmt = self.format_var.get()
        presets = self.engine.get_presets(fmt)
        self.quality_values = presets # Store dict
        options = list(presets.keys())
        self.quality_combo.configure(values=options)
        if options:
            self.quality_combo.set(options[0])
            
    def _browse_output(self):
        path = filedialog.askdirectory(title=t('select_folder'))
        if path:
            self.output_path_var.set(path)
            self.is_custom_output = True
            
    def _on_drop(self, event):
        """Handle dropped folder."""
        if event.data:
            path = event.data
            if path.startswith('{') and path.endswith('}'):
                path = path[1:-1]
            
            if os.path.isdir(path):
                self.output_path_var.set(path)
                self.is_custom_output = True
            else:
                 # If file dropped, take its folder?
                 self.output_path_var.set(os.path.dirname(path))
                 self.is_custom_output = True

    def _toggle_inputs(self, enable: bool):
        state = "normal" if enable else "disabled"
        self.format_combo.configure(state="readonly" if enable else "disabled")
        self.quality_combo.configure(state="readonly" if enable else "disabled")
        self.browse_btn.configure(state=state)
        self.convert_btn.configure(state=state)
        # Cancel button always enabled to stop
        
    def _on_cancel(self):
        if self.engine.is_converting:
            self.stop_conversion = True
            self.status_label.configure(text="Stopping...")
        else:
            self.destroy()
            
    def _start_conversion(self):
        self.stop_conversion = False
        self.engine.is_converting = True
        self._toggle_inputs(False)
        self.progress_bar.set(0)
        
        # Get settings
        fmt = self.format_var.get()
        quality_name = self.quality_var.get()
        quality_args = self.quality_values.get(quality_name, '')
        out_folder = self.output_path_var.get() if self.is_custom_output else None
        
        studio_processing = self.studio_proc_var.get()
        
        # Thread
        threading.Thread(
            target=self._run_conversion,
            args=(fmt, quality_args, out_folder, studio_processing),
            daemon=True
        ).start()
        
    def _run_conversion(self, fmt: str, quality_args: str, out_folder: str, studio_processing: bool):
        total = len(self.files)
        success_count = 0
        ext = CONVERTER_FORMATS.get(fmt, '.mp3')
        
        for i, input_path in enumerate(self.files):
            if self.stop_conversion:
                break
                
            fname = os.path.basename(input_path)
            self.status_label.configure(text=f"{t('converting')} {fname} ({i+1}/{total})")
            
            # Paths
            if out_folder:
                # Create output folder if needed
                if not os.path.exists(out_folder):
                    os.makedirs(out_folder)
                output_path = os.path.join(out_folder, os.path.splitext(fname)[0] + ext)
            else:
                # Same folder
                output_path = os.path.splitext(input_path)[0] + ext
                
            # Check overwrite (simple numeric suffix if needed? No, FFMPEG -y argument handles overwrite in logic)
            # Actually engine has -y to overwrite.
            
            # Convert
            res = self.engine.convert_file(input_path, output_path, quality_args, studio_processing)
            
            if res:
                success_count += 1
            
            # Progress
            progress = (i + 1) / total
            self.progress_bar.set(progress)
            
        self.engine.is_converting = False
        self._toggle_inputs(True)
        
        if self.stop_conversion:
            self.status_label.configure(text="Cancelled", text_color=COLORS['warning'])
        else:
            final_msg = t('conversion_complete') if success_count == total else t('conversion_errors')
            self.status_label.configure(text=f"{final_msg} ({success_count}/{total})", 
                                      text_color=COLORS['success'] if success_count == total else COLORS['warning'])
            
            if success_count == total:
                 self.after(0, lambda: show_styled_info(self, t('info'), t('conversion_complete'), "✅"))
