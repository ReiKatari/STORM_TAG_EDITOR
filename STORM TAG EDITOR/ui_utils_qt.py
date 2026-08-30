"""
Storm Tag Editor - Qt UI Utilities
Shared UI components and theme for PyQt6.
"""

from PyQt6.QtGui import QColor, QFont, QPalette, QBrush
from PyQt6.QtWidgets import QApplication
import sys
import os

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Colors - Dark Theme (Default - can be updated by apply_theme)
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
    'highlight': '#f97316',
    'highlight_hover': '#fb923c',
}

FONT_FAMILY = "Segoe UI" # Standard modern font for Windows

def apply_theme(theme):
    """Apply a theme dict to COLORS."""
    global COLORS
    COLORS['bg_main'] = theme.get('bg', COLORS['bg_main'])
    COLORS['bg_dark'] = theme.get('bg', COLORS['bg_dark'])
    COLORS['bg_panel'] = theme.get('panel_bg', COLORS['bg_panel'])
    COLORS['bg_input'] = theme.get('input_bg', COLORS['bg_input'])
    COLORS['bg_hover'] = theme.get('btn_bg', COLORS['bg_hover'])
    COLORS['text'] = theme.get('fg', COLORS['text'])
    COLORS['text_secondary'] = theme.get('fg', COLORS['text_secondary'])
    COLORS['text_muted'] = theme.get('input_border', COLORS['text_muted'])
    COLORS['border'] = theme.get('input_border', COLORS['border'])
    COLORS['accent'] = theme.get('accent', COLORS['accent'])
    COLORS['accent_dark'] = theme.get('accent_dark', COLORS['accent_dark'])
    COLORS['highlight'] = theme.get('accent', COLORS['highlight'])

def get_stylesheet():
    """Returns the global QSS stylesheet."""
    return f"""
    QMainWindow, QDialog {{
        background-color: {COLORS['bg_main']};
        color: {COLORS['text']};
    }}
    QWidget {{
        background-color: {COLORS['bg_main']};
        color: {COLORS['text']};
        font-family: "{FONT_FAMILY}";
        font-size: 13px;
    }}
    
    /* Panels */
    QFrame#Panel {{
        background-color: {COLORS['bg_panel']};
        border-radius: 12px;
    }}
    QFrame#InputFrame {{
        background-color: {COLORS['bg_input']};
        border-radius: 8px;
        border: 1px solid {COLORS['border']};
    }}
    
    /* Labels */
    QLabel {{
        background-color: transparent;
        color: {COLORS['text']};
    }}
    QLabel#Title {{
        font-size: 16px;
        font-weight: bold;
    }}
    QLabel#Subtitle {{
        color: {COLORS['text_secondary']};
        font-size: 11px;
    }}
    QLabel#Muted {{
        color: {COLORS['text_muted']};
        font-size: 11px;
    }}
    QLabel#Error {{
        color: {COLORS['error']};
    }}
    QLabel#Success {{
        color: {COLORS['success']};
    }}
    
    /* Inputs */
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {COLORS['bg_input']};
        color: {COLORS['text']};
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        padding: 8px;
        selection-background-color: {COLORS['accent']};
        selection-color: {COLORS['text']};
    }}
    QLineEdit:focus, QTextEdit:focus {{
        border: 1px solid {COLORS['accent']};
    }}
    QLineEdit:disabled, QTextEdit:disabled {{
        color: {COLORS['text_muted']};
        background-color: transparent;
        border: 1px solid {COLORS['border']};
        opacity: 0.5;
    }}
    
    /* Buttons */
    /* Buttons */
    QPushButton {{
        background-color: {COLORS['bg_input']};
        color: {COLORS['text']};
        border: 1px solid {COLORS['border']};
        border-radius: 4px;
        padding: 6px 16px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background-color: #3498db; /* Light Blue */
        color: white;
        border: 1px solid #2980b9;
    }}
    QPushButton:pressed {{
        background-color: {COLORS['accent_dark']};
        border: 1px solid {COLORS['accent']};
    }}
    
    QPushButton#AccentButton {{
        background-color: {COLORS['accent']};
        color: white;
    }}
    QPushButton#AccentButton:hover {{
        background-color: {COLORS['accent_hover']};
        border: 1px solid white;
    }}
    QPushButton#AccentButton:pressed {{
        background-color: {COLORS['accent_dark']};
        border: 1px solid white;
    }}
    
    QPushButton#DangerButton {{
        background-color: transparent;
        border: 1px solid {COLORS['error']};
        color: {COLORS['error']};
    }}
    QPushButton#DangerButton:hover {{
        background-color: {COLORS['error']};
        color: white;
    }}
    
    /* List Widget */
    QListWidget {{
        background-color: {COLORS['bg_input']};
        border: 1px solid {COLORS['border']};
        border-radius: 4px;
    }}
    QListWidget::item {{
        padding: 4px;
        margin-bottom: 4px;
    }}
    QListWidget::item:selected {{
        background-color: {COLORS['accent_dark']};
    }}
    QListWidget::item:hover:!selected {{
        background-color: {COLORS['bg_hover']};
    }}
    
    /* ComboBox */
    QComboBox {{
        background-color: {COLORS['bg_input']};
        color: {COLORS['text']};
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        padding: 6px 12px;
    }}
    QComboBox:disabled {{
        color: {COLORS['text_muted']};
        background-color: transparent;
        border: 1px solid {COLORS['border']};
        opacity: 0.6;
    }}
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 24px;
        border-left-width: 0px;
        border-top-right-radius: 8px;
        border-bottom-right-radius: 8px;
        image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiPjxwb2x5bGluZSBwb2ludHM9IjYgOSAxMiAxNSAxOCA5Ij48L3BvbHlsaW5lPjwvc3ZnPg==);
    }}
    QComboBox QListView {{
        background-color: {COLORS['bg_panel']};
        color: {COLORS['text']};
        selection-background-color: {COLORS['accent']};
        selection-color: {COLORS['text']};
        border: 1px solid {COLORS['border']};
        outline: none;
    }}
    QComboBox QListView::item {{
        padding: 8px 12px;
        min-height: 24px;
    }}
    QComboBox QListView::item:hover {{
        background-color: {COLORS['accent']};
        color: white;
    }}
    QComboBox QListView::item:selected {{
        background-color: {COLORS['accent_dark']};
        color: white;
    }}
    
    /* Scrollbars */
    QScrollBar:vertical {{
        border: none;
        background: {COLORS['bg_panel']};
        width: 10px;
        margin: 0px 0px 0px 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {COLORS['bg_hover']};
        min-height: 20px;
        border-radius: 5px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    
    /* Slider */
    QSlider::groove:horizontal {{
        border: 1px solid {COLORS['bg_hover']};
        height: 6px;
        background: {COLORS['bg_input']};
        margin: 2px 0;
        border-radius: 3px;
    }}
    QSlider::handle:horizontal {{
        background: {COLORS['accent']};
        border: 1px solid {COLORS['accent']};
        width: 16px;
        height: 16px;
        margin: -6px 0;
        border-radius: 8px;
    }}
    
    /* CheckBox */
    QCheckBox {{
        spacing: 8px;
        color: {COLORS['text']};
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 1px solid {COLORS['border']};
        background: transparent;
    }}
    QCheckBox::indicator:hover {{
        border-color: {COLORS['accent']};
    }}
    QCheckBox::indicator:checked {{
        background-color: {COLORS['success']}; /* Green */
        border-color: {COLORS['success']};
        image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIzIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiPjxwb2x5bGluZSBwb2ludHM9IjIwIDYgOSAxNyA0IDEyIj48L3BvbHlsaW5lPjwvc3ZnPg==);
    }}
    """

from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QTimer, pyqtProperty, QParallelAnimationGroup, QRect, QVariantAnimation, QAbstractAnimation
from PyQt6.QtWidgets import QPushButton, QGraphicsOpacityEffect, QWidget, QDialog
from PyQt6.QtGui import QColor

class HoverButton(QPushButton):
    """Button with animated hover and click color transition."""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.role = 'default' # default, accent, danger
        self.update_colors()
        
        self.anim = QVariantAnimation()
        self.anim.valueChanged.connect(self.update_style)
        self.anim.setDuration(150)
        self.anim.setEasingCurve(QEasingCurve.Type.OutQuad)

    def setObjectName(self, name):
        super().setObjectName(name)
        if "Accent" in name: self.role = 'accent'
        elif "Danger" in name: self.role = 'danger'
        self.update_colors()

    def update_colors(self):
        if self.role == 'accent':
            self.default_color = QColor(COLORS['accent'])
            self.hover_color = QColor(COLORS['accent_hover'])
            self.pressed_color = QColor(COLORS['accent_dark'])
        elif self.role == 'danger':
            self.default_color = QColor(COLORS['bg_input'])
            self.hover_color = QColor(COLORS['error'])
            self.pressed_color = QColor(COLORS['error'])
        else:
            self.default_color = QColor(COLORS['bg_input'])
            # User requested Light Blue (#3498db) hover for all
            self.hover_color = QColor("#3498db") 
            self.pressed_color = QColor(COLORS['accent_dark'])
            
        self.update_style(self.default_color)

    def update_style(self, color):
        if isinstance(color, QColor):
            c = color.name()
        else:
            c = str(color)
        # We need to preserve border/padding
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {c};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 6px 16px;
                font-weight: 500;
            }}
        """)
        
    def enterEvent(self, event):
        self.anim.stop()
        self.anim.setStartValue(self.default_color)
        self.anim.setEndValue(self.hover_color)
        self.anim.start()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self.anim.stop()
        self.anim.setStartValue(self.hover_color)
        self.anim.setEndValue(self.default_color)
        self.anim.start()
        super().leaveEvent(event)
        
    def mousePressEvent(self, e):
        self.anim.stop()
        self.anim.setStartValue(self.hover_color)
        self.anim.setEndValue(self.pressed_color)
        self.anim.start()
        super().mousePressEvent(e)
        
    def mouseReleaseEvent(self, e):
        self.anim.stop()
        self.anim.setStartValue(self.pressed_color)
        self.anim.setEndValue(self.hover_color)
        self.anim.start()
        super().mouseReleaseEvent(e)

# Animation Helper for Dialogs
def animate_dialog(dialog: QDialog):
    """Fade in and scale up dialog."""
    opacity = QGraphicsOpacityEffect(dialog)
    dialog.setGraphicsEffect(opacity)
    
    anim = QPropertyAnimation(opacity, b"opacity")
    anim.setDuration(300)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.OutQuad)
    anim.start()
    
    dialog.window_anim = anim
