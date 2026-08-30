"""
Storm Tag Editor - UI Utilities
Shared UI components and theme.
"""

import customtkinter as ctk

# Colors
COLORS = {
    'bg_dark': '#0d0d0d',
    'bg_main': '#141414',
    'bg_panel': '#1a1a1a',
    'bg_input': '#242424',
    'bg_hover': '#2a2a2a',
    'accent': '#6366f1',
    'accent_hover': '#818cf8',
    'accent_dark': '#4f46e5',
    'success': '#22c55e',
    'warning': '#f59e0b',
    'error': '#ef4444',
    'text': '#ffffff',
    'text_secondary': '#a1a1aa',
    'text_muted': '#71717a',
    'border': '#2e2e2e',
    'drop_zone': '#1e3a5f',
    'drop_active': '#2d5a8f',
    'sash': '#3a3a3a',
    'success': '#22c55e',
    'highlight': '#f97316', # Orange for special features
    'highlight_hover': '#fb923c',
}

FONT_FAMILY = "Century Gothic"

class ModernButton(ctk.CTkButton):
    """Styled button widget with auto-emoji font support."""
    def __init__(self, master, text="", accent=False, **kwargs):
        # Check for emojis/symbols to enforce Emoji font
        has_emoji = any(ord(c) > 0x1F000 for c in text) if text else False
        font_family = "Segoe UI Emoji" if has_emoji else FONT_FAMILY
        
        colors = {
            'fg_color': COLORS['accent'] if accent else COLORS['bg_input'],
            'hover_color': COLORS['accent_hover'] if accent else COLORS['bg_hover'],
            'text_color': COLORS['text'],
            'corner_radius': 8,
            'height': 36,
            'font': ctk.CTkFont(family=font_family, size=13, weight="normal"),
        }
        colors.update(kwargs)
        super().__init__(master, text=text, **colors)

def animate_fade_in(window, duration=150):
    """Fade in the window."""
    try:
        window.attributes("-alpha", 0.0)
        
        step = 0.1
        delay = int(duration * step)
        
        def fade(current_alpha):
            if current_alpha < 1.0:
                new_alpha = min(1.0, current_alpha + step)
                window.attributes("-alpha", new_alpha)
                window.after(delay, lambda: fade(new_alpha))
            else:
                window.attributes("-alpha", 1.0)
                
        window.after(10, lambda: fade(0.0))
    except Exception:
        # Fallback if attributes not supported
        pass

def show_styled_info(parent, title: str, message: str, icon: str = ""):
    """Show a styled information dialog matching the dark theme."""
    dialog = ctk.CTkToplevel(parent)
    dialog.title(title)
    dialog.geometry("420x160")
    dialog.resizable(False, False)
    dialog.configure(fg_color=COLORS['bg_dark'])
    
    # Handle transient parent correctly
    try:
        dialog.transient(parent)
        dialog.grab_set()
    except:
        pass
    
    # Center on parent
    dialog.update_idletasks()
    # Center on parent using root coordinates
    dialog.update_idletasks()
    try:
        x = parent.winfo_rootx() + (parent.winfo_width() - 420) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 160) // 2
        dialog.geometry(f"+{x}+{y}")
    except:
        # Fallback to screen center if parent not ready
        sw = dialog.winfo_screenwidth()
        sh = dialog.winfo_screenheight()
        x = (sw - 420) // 2
        y = (sh - 160) // 2
        dialog.geometry(f"+{x}+{y}")
    
    # Animate
    animate_fade_in(dialog)
    
    # Content frame
    content = ctk.CTkFrame(dialog, fg_color="transparent")
    content.pack(fill="both", expand=True, padx=25, pady=20)
    
    # Icon (Optional)
    if icon:
        ctk.CTkLabel(
            content,
            text=icon,
            font=ctk.CTkFont(size=32),
            text_color=COLORS['accent']
        ).pack(side="left", padx=(0, 15))
    
    # Message
    ctk.CTkLabel(
        content,
        text=message,
        font=ctk.CTkFont(family=FONT_FAMILY, size=15),
        text_color=COLORS['text'],
        wraplength=350,  # Slightly wider wrap
        justify="left"
    ).pack(side="left", fill="both", expand=True)
    
    # OK button
    btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
    btn_frame.pack(pady=(0, 20))
    
    ModernButton(
        btn_frame,
        text="OK",
        accent=True,
        width=100,
        command=dialog.destroy
    ).pack()
    
    dialog.wait_window()
