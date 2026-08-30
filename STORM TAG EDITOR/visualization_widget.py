# -*- coding: utf-8 -*-
"""
Storm Tag Editor - Audio Visualization Widget
Advanced animated visualization with 13 modes using Pygame.
"""

import random
import math
import numpy as np
import pygame
from PyQt6.QtWidgets import QWidget, QMenu
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QImage, QPainter

from ui_utils_qt import COLORS

class VisualizationWidget(QWidget):
    """Animated audio visualization widget using Pygame with real-time FFT/Waveform data."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(150)
        self.modes_count = 18 # Increased from 13
        self.mode = 0  # 0 to 17
        
        self.is_playing = False
        
        # Audio Analysis
        self.analyzer = None
        self.player_ref = None # Reference to player to get position
        
        # Data containers
        self.bar_count = 64
        self.fft_data = np.zeros(self.bar_count)
        self.wave_data = np.zeros(self.bar_count) # Fallback handling
        
        # Physics / Smoothing
        self.fft_smooth = np.zeros(self.bar_count)
        self.peak_hold = np.zeros(self.bar_count)
        self.peak_fall = np.ones(self.bar_count) * 2.0
        
        # Beat Detection
        self.beat_sensitivity = 1.2
        self.beat_history = []
        self.is_beat = False
        
        # Pygame Surface
        self.surface = None
        self.time_elapsed = 0.0
        
        # Animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_animation)
        self.timer.setInterval(16)  # ~60 FPS
        
        # Click to switch
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        # Config for visuals (shared state)
        self.config = {
            'bg_color': (5, 5, 8), # Deep dark blue/black
            'hue_shift': 0.0
        }
        
        # Persistent Particles for mode 4 (and others)
        self.particles = []

    def set_analyzer(self, analyzer):
        self.analyzer = analyzer

    def set_player_reference(self, player):
        self.player_ref = player
        
    def set_position(self, pos):
        """Compatibility method for external calls."""
        pass

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.mode = (self.mode + 1) % self.modes_count
            self.update()

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        
        # Apply Theme Style
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
            }}
            QMenu::item {{
                padding: 6px 20px 6px 12px;
                background-color: transparent;
            }}
            QMenu::item:selected {{
                background-color: {COLORS['accent']};
                color: white;
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {COLORS['border']};
                margin: 4px 0px;
            }}
        """)
        
        names = [
            "Modern Spectrum", "Circular Spectrum", "Waveform Tunnel", "Particle Field",
            "Bass Orb", "Digital Rain", "Neon Roads", "Starburst",
            "Fluid Blobs", "Polygons", "Kaleidoscope", "Energy Ring", "DNA Helix",
            "Plasma Wave", "Cyber Grid", "Classic LED", "Vortex Core", "Aurora Borealis"
        ]
        
        for i, name in enumerate(names):
            # Mark current with a bullet or similar?
            prefix = "✔ " if i == self.mode else "    "
            action = menu.addAction(f"{prefix}{i+1}. {name}")
            action.triggered.connect(lambda checked, m=i: self._set_mode(m))
            
        menu.exec(self.mapToGlobal(pos))

    def _set_mode(self, m):
        self.mode = m
        self.particles = [] # Clear particles on switch
        self.update()

    def start(self):
        self.is_playing = True
        self.timer.start()

    def stop(self):
        self.is_playing = False
        self.timer.stop()
        self.fft_data = np.zeros(self.bar_count)
        self.fft_smooth = np.zeros(self.bar_count)
        self.update()

    def _update_animation(self):
        self.time_elapsed += 0.016
        self.config['hue_shift'] = (self.time_elapsed * 20) % 360 # Global color cycle
        
        if self.is_playing and self.analyzer and self.player_ref:
            pos = self.player_ref.get_position()
            fft, wave = self.analyzer.get_data(pos)
            
            if fft is not None:
                if len(fft) != self.bar_count:
                    indices = np.linspace(0, len(fft)-1, self.bar_count, dtype=int)
                    self.fft_data = fft[indices]
                else:
                    self.fft_data = fft
                    
                if wave is not None:
                    indices = np.linspace(0, len(wave)-1, self.bar_count, dtype=int)
                    self.wave_data = wave[indices]
            else:
                 self.fft_data *= 0.9
        else:
             if not self.is_playing:
                 self.fft_data = np.zeros(self.bar_count)

        # Smooth
        self.fft_smooth = self.fft_smooth * 0.7 + self.fft_data * 0.3
        
        # Beat Detection
        bass_energy = np.mean(self.fft_smooth[:4])
        self.beat_history.append(bass_energy)
        if len(self.beat_history) > 30: self.beat_history.pop(0)
        
        avg_energy = np.mean(self.beat_history) if self.beat_history else 0
        self.is_beat = bass_energy > avg_energy * self.beat_sensitivity and bass_energy > 50
        
        # Peak Hold
        for i in range(self.bar_count):
            if self.fft_smooth[i] > self.peak_hold[i]:
                self.peak_hold[i] = self.fft_smooth[i]
            else:
                self.peak_hold[i] -= self.peak_fall[i]
                if self.peak_hold[i] < 0: self.peak_hold[i] = 0

        self.update() 

    def paintEvent(self, event):
        w = self.width()
        h = self.height()
        
        if w <= 0 or h <= 0: return

        if self.surface is None or self.surface.get_width() != w or self.surface.get_height() != h:
            self.surface = pygame.Surface((w, h))

        # Dynamic Fade (trails on beat or always)
        fade_alpha = 40 if self.mode in [3, 4, 5, 8, 12] else 255
        if self.is_beat and self.mode in [5, 12]: fade_alpha = 80 # Flash clear on beat
        
        if fade_alpha < 255:
            fade = pygame.Surface((w, h))
            fade.fill(self.config['bg_color'])
            fade.set_alpha(fade_alpha) 
            self.surface.blit(fade, (0, 0))
        else:
            self.surface.fill(self.config['bg_color'])

        draw_funcs = [
            self.draw_1_spectrum_bars,
            self.draw_2_circular_spectrum,
            self.draw_3_waveform_tunnel,
            self.draw_4_particle_field,
            self.draw_5_bass_orb,
            self.draw_6_digital_rain,
            self.draw_7_neon_roads,
            self.draw_8_starburst,
            self.draw_9_fluid_blobs,
            self.draw_10_polygons,
            self.draw_11_kaleidoscope,
            self.draw_12_energy_ring,
            self.draw_13_dna_helix,
            self.draw_14_plasma_wave,
            self.draw_15_cyber_grid,
            self.draw_16_classic_led,
            self.draw_17_vortex_core,
            self.draw_18_aurora_borealis
        ]
        
        if 0 <= self.mode < len(draw_funcs):
            try:
                draw_funcs[self.mode](self.surface, w, h)
            except Exception as e:
                pass

        data = pygame.image.tostring(self.surface, 'RGB')
        img = QImage(data, w, h, QImage.Format.Format_RGB888)
        
        painter = QPainter(self)
        painter.drawImage(0, 0, img)
        painter.end()


    # ==========================================
    # HELPERS
    # ==========================================

    def _get_color(self, offset=0, sat=100, val=None):
        """Get dynamic color from global hue shift."""
        if val is None: val = 100
        # More vibrant colors
        hue = (self.config['hue_shift'] + offset) % 360
        c = pygame.Color(0)
        c.hsla = (int(hue), int(sat), int(50 if val > 50 else val), 100)
        return c
        
    def _draw_glow_circle(self, surf, color, center, radius, alpha=50):
        """Draw a glowing circle."""
        s = pygame.Surface((int(radius*2), int(radius*2)), pygame.SRCALPHA)
        pygame.draw.circle(s, (color.r, color.g, color.b, alpha), (int(radius), int(radius)), int(radius))
        surf.blit(s, (center[0]-radius, center[1]-radius))

    # ==========================================
    # VISUALIZATIONS
    # ==========================================

    def draw_1_spectrum_bars(self, surf, w, h):
        count = len(self.fft_smooth)
        bar_w = w / count
        
        for i in range(count):
            val = self.fft_smooth[i]
            x = i * bar_w
            
            # Mirror effect: Draw from center
            # Let's keep bottom but add reflection
            
            bar_h = (val / 255.0) * (h * 0.8)
            y = h - bar_h
            
            c = self._get_color(i * 3 + val * 0.5)
            
            # Main Bar with Gradient look (simple fill for perf)
            pygame.draw.rect(surf, c, (x, y, bar_w - 1, bar_h))
            
            # Peak
            peak_y = h - (self.peak_hold[i] / 255.0) * (h * 0.8)
            pygame.draw.line(surf, (255, 255, 255), (x, peak_y), (x + bar_w - 2, peak_y), 2)
            
            # Reflection (dimmer)
            r_h = bar_h * 0.3
            r_c = (c.r//2, c.g//2, c.b//2)
            pygame.draw.rect(surf, r_c, (x, h, bar_w - 1, r_h)) # Draw below? No space.
            # Actually screen is usually full height. Let's just make bars powerful.
            
            # Top glow
            if self.is_beat and i < 5:
                # Flash bars
                rect = pygame.Rect(x, y, bar_w-1, bar_h)
                surf.fill((255, 255, 255), rect, special_flags=pygame.BLEND_ADD)

    def draw_2_circular_spectrum(self, surf, w, h):
        cx, cy = w // 2, h // 2
        radius = min(w, h) * 0.25
        max_bar_h = min(w, h) * 0.3
        count = len(self.fft_smooth)
        
        # Bass throb
        bass = self.fft_smooth[:4].mean()
        throb = (bass / 255.0) * 20
        
        # Center glow
        self._draw_glow_circle(surf, self._get_color(0), (cx, cy), radius + throb, 50)
        
        for i in range(count):
            val = self.fft_smooth[i]
            angle = (i / count) * 360 + self.time_elapsed * 20
            angle_rad = math.radians(angle - 90)
            
            r_inner = radius + throb
            r_outer = r_inner + (val / 255.0) * max_bar_h
            
            x1 = cx + math.cos(angle_rad) * r_inner
            y1 = cy + math.sin(angle_rad) * r_inner
            
            x2 = cx + math.cos(angle_rad) * r_outer
            y2 = cy + math.sin(angle_rad) * r_outer
            
            c = self._get_color(i * 5 + val)
            pygame.draw.line(surf, c, (x1, y1), (x2, y2), 4)

    def draw_3_waveform_tunnel(self, surf, w, h):
        cx, cy = w//2, h//2
        rings = 12 # More rings
        bass = self.fft_smooth[0]
        
        speed = 2 + (bass / 50.0) # Faster
        self.time_elapsed += 0.01 # Add extra speed for this mode
        
        for i in range(rings):
            depth = (self.time_elapsed * speed + i * 0.8) % rings
            scale = math.pow(depth / rings, 3) # Steeper curve
            
            if scale < 0.01: continue
            
            r = min(w, h) * 0.6 * scale
            
            points = []
            steps = 50 # Smoother
            for j in range(steps):
                angle = (j / steps) * math.pi * 2
                
                # Double wave modulation
                wave_idx = int((j / steps) * len(self.wave_data))
                wave_val = self.wave_data[wave_idx] * 80 * scale
                
                angle += self.time_elapsed * 0.5 * (1 if i%2==0 else -1) # Rotating rings in opposite directions
                
                px = cx + math.cos(angle) * (r + wave_val)
                py = cy + math.sin(angle) * (r + wave_val)
                points.append((px, py))
            
            # Neon colors
            c = self._get_color(depth * 40 + bass)
            if len(points) > 2:
                pygame.draw.lines(surf, c, True, points, max(1, int(4 * scale)))

    def draw_4_particle_field(self, surf, w, h):
        # Init particles if needed
        if len(self.particles) < 150:
            self.particles.append({
                'x': w/2, 'y': h/2,
                'vx': random.uniform(-1, 1), 'vy': random.uniform(-1, 1),
                'life': random.randint(50, 100),
                'color_off': random.randint(0, 360)
            })
            
        bass = self.fft_smooth[:4].mean()
        boom = bass / 50.0
        
        # Beat hit? Explode check
        if self.is_beat:
             for p in self.particles:
                 p['vx'] *= 1.5
                 p['vy'] *= 1.5
        
        new_particles = []
        for p in self.particles:
            p['x'] += p['vx'] * (1 + boom)
            p['y'] += p['vy'] * (1 + boom)
            p['life'] -= 1
            
            # Wrap or bounce
            if p['x'] < 0 or p['x'] > w: p['vx'] *= -1
            if p['y'] < 0 or p['y'] > h: p['vy'] *= -1
            
            if p['life'] > 0:
                size = int(3 + (bass / 40.0))
                c = self._get_color(p['color_off'])
                
                # Draw trail
                pygame.draw.circle(surf, c, (int(p['x']), int(p['y'])), size)
                new_particles.append(p)
            else:
                # Reset to center
                 p['x'] = w/2
                 p['y'] = h/2
                 p['vx'] = random.uniform(-2, 2)
                 p['vy'] = random.uniform(-2, 2)
                 p['life'] = random.randint(50, 100)
                 new_particles.append(p)
                 
        self.particles = new_particles

    def draw_5_bass_orb(self, surf, w, h):
        cx, cy = w//2, h//2
        bass = self.fft_smooth[:4].mean()
        
        base_r = min(w, h) * 0.15
        r = base_r + (bass / 255.0) * 120
        
        # Shockwave
        if self.is_beat:
             pygame.draw.circle(surf, (255, 255, 255), (cx, cy), int(r * 1.5), 2)
             
        # Layers of glow
        c1 = self._get_color(bass)
        c2 = self._get_color(bass + 120)
        
        self._draw_glow_circle(surf, c1, (cx, cy), r * 1.2, 30)
        self._draw_glow_circle(surf, c2, (cx, cy), r * 0.8, 100)
        
        # Solid Core
        pygame.draw.circle(surf, (255, 255, 255), (cx, cy), int(r * 0.5))
        
        # Lightning bolts?
        if bass > 150:
             for _ in range(3):
                 angle = random.uniform(0, 6.28)
                 lx = cx + math.cos(angle) * r
                 ly = cy + math.sin(angle) * r
                 lx2 = cx + math.cos(angle) * (r + 50)
                 ly2 = cy + math.sin(angle) * (r + 50)
                 pygame.draw.line(surf, (255, 255, 200), (lx, ly), (lx2, ly2), 2)

    def draw_6_digital_rain(self, surf, w, h):
        cols = int(w / 15)
        if not hasattr(self, 'matrix_drops') or len(self.matrix_drops) != cols:
            self.matrix_drops = [random.randint(-h, 0) for _ in range(cols)]
            
        high_freq = self.fft_smooth[30:].mean()
        
        for i in range(cols):
            x = i * 15
            
            # Speed reactive
            idx = int((i/cols)*len(self.fft_smooth))
            col_energy = self.fft_smooth[idx]
            speed = 8 + (col_energy / 10.0)
            
            self.matrix_drops[i] += speed
            if self.matrix_drops[i] > h:
                self.matrix_drops[i] = random.randint(-200, -50)
            
            head_y = int(self.matrix_drops[i])
            
            # Draw trail
            for j in range(8):
                y = head_y - j * 18
                if 0 <= y < h:
                     # Color shift: Green/Blue/Cyan
                     c_val = 255 - j * 30
                     if j == 0: 
                         col = (200, 255, 200) # Head bright
                     else:
                         col = (0, c_val, c_val if self.is_beat else 0)
                     
                     # Draw "char" (rect for now)
                     rect = (x+2, y, 12, 16)
                     pygame.draw.rect(surf, col, rect)

    def draw_7_neon_roads(self, surf, w, h):
        cx, cy = w//2, h//2
        horizon_y = h * 0.35
        
        # Dynamic sky gradient
        sky_h = int(horizon_y)
        for i in range(10):
            rat = i/10
            c = (int(20*rat), 0, int(60*rat))
            pygame.draw.rect(surf, c, (0, sky_h * (1-rat), w, sky_h/10 + 2))
        
        # Sun
        bass = self.fft_smooth[0]
        sun_r = 60 + bass * 0.3
        # Gradient sun stripes
        pygame.draw.circle(surf, (255, 100, 50), (cx, int(horizon_y - 20)), int(sun_r))
        for k in range(5):
             y_strip = horizon_y - 20 + k * 15
             h_strip = 5
             if y_strip < horizon_y + sun_r:
                 pygame.draw.rect(surf, self.config['bg_color'], (cx - sun_r, y_strip, sun_r*2, h_strip))
        
        # Grid
        speed = (self.time_elapsed * 300) + (bass * 2)
        
        # Perspective Lines
        for i in range(-12, 13):
            x_start = cx + i * 15
            x_end = cx + i * 200 
            c = (200, 0, 255)
            pygame.draw.line(surf, c, (x_start, horizon_y), (x_end, h), 2)
            
        # Horizontal moving lines
        for i in range(12):
             y_base = (i * 40 + speed) % (h - horizon_y)
             y = horizon_y + y_base
             # Exp fog
             alpha = int((y_base / (h - horizon_y)) * 255)
             
             factor = y_base / (h - horizon_y)
             width_at_y = w * factor * 3
             
             x1 = cx - width_at_y / 2
             x2 = cx + width_at_y / 2
             
             c = (0, 255, 255)
             # Draw line with alpha? Pygame line no alpha. Use surface or just modulate color
             c_mod = (0, alpha, alpha)
             pygame.draw.line(surf, c_mod, (x1, y), (x2, y), 2)

    def draw_8_starburst(self, surf, w, h):
        cx, cy = w//2, h//2
        count = 90
        
        # Spin
        spin = self.time_elapsed * 0.5
        
        for i in range(count):
            idx = int((i/count) * len(self.fft_smooth))
            val = self.fft_smooth[idx]
            
            angle = (i/count) * math.pi * 2 + spin
            
            start_r = 30 + (self.fft_smooth[:4].mean() / 5)
            length = (val / 255.0) * (min(w,h) * 0.6)
            
            x1 = cx + math.cos(angle) * start_r
            y1 = cy + math.sin(angle) * start_r
            
            x2 = cx + math.cos(angle) * (start_r + length)
            y2 = cy + math.sin(angle) * (start_r + length)
            
            c = self._get_color(i * 4 + val)
            
            # Thick lines
            pygame.draw.line(surf, c, (x1, y1), (x2, y2), 5)
            
            # Tip glow
            if val > 100:
                pygame.draw.circle(surf, (255, 255, 255), (int(x2), int(y2)), 4)

    def draw_9_fluid_blobs(self, surf, w, h):
        count = 6
        cx, cy = w//2, h//2
        
        for i in range(count):
             idx = i * 3
             val = self.fft_smooth[idx % 64]
             
             offset = (i * math.pi * 2 / count) + self.time_elapsed
             
             # Wobbly orbit
             r_orbit = 60 + math.sin(self.time_elapsed * 2 + i) * 30 + (val * 0.2)
             
             x = cx + math.cos(offset) * r_orbit
             y = cy + math.sin(offset) * r_orbit
             
             radius = 40 + val * 0.6
             
             c = self._get_color(i * 60 + val)
             self._draw_glow_circle(surf, c, (x, y), radius, 150)
             
        # Connect centers
        if self.is_beat:
             pts = []
             for i in range(count):
                 # Recalc pos (inefficient but safe)
                 offset = (i * math.pi * 2 / count) + self.time_elapsed
                 r_orbit = 60 + math.sin(self.time_elapsed * 2 + i) * 30 + (self.fft_smooth[i*3 % 64] * 0.2)
                 pts.append((cx + math.cos(offset)*r_orbit, cy + math.sin(offset)*r_orbit))
             pygame.draw.lines(surf, (255, 255, 255), True, pts, 2)

    def draw_10_polygons(self, surf, w, h):
        cx, cy = w//2, h//2
        shapes = [3, 4, 5, 6, 8] 
        
        bass = self.fft_smooth[0]
        
        for i, sides in enumerate(shapes):
             val = self.fft_smooth[i*5 % 64]
             radius = 60 + (i * 45) + (val * 0.3)
             
             # Rotate alternating
             direction = 1 if i % 2 == 0 else -1
             angle_offset = self.time_elapsed * direction + (bass / 500.0 * direction)
             
             points = []
             for j in range(sides):
                 angle = angle_offset + (j / sides) * math.pi * 2
                 px = cx + math.cos(angle) * radius
                 py = cy + math.sin(angle) * radius
                 points.append((px, py))
                 
             c = self._get_color(i * 50 + val)
             pygame.draw.lines(surf, c, True, points, 4)
             
             # Connect to center if beat
             if self.is_beat and i == 0:
                  pygame.draw.lines(surf, (255, 255, 255), True, points, 1)

    def draw_11_kaleidoscope(self, surf, w, h):
        cx, cy = w//2, h//2
        
        seg_w, seg_h = 250, 250
        seg = pygame.Surface((seg_w, seg_h), pygame.SRCALPHA)
        
        # Draw dynamic art on segment
        for i in range(15):
            val = self.fft_smooth[i*2]
            y = i * 15
            w_rect = (val / 255.0) * seg_w
            c = self._get_color(val + i*10)
            
            pygame.draw.rect(seg, c, (seg_w/2 - w_rect/2, y, w_rect, 10))
            pygame.draw.circle(seg, c, (int(seg_w/2 + math.sin(self.time_elapsed*i)*40), y), int(val/20))

        copies = 8
        base_angle = self.time_elapsed * 10
        
        for i in range(copies):
             angle = base_angle + (i/copies) * 360
             rot = pygame.transform.rotate(seg, angle)
             rect = rot.get_rect(center=(cx, cy))
             surf.blit(rot, rect)

    def draw_12_energy_ring(self, surf, w, h):
        cx, cy = w//2, h//2
        r_base = min(w,h) * 0.35
        
        val = self.fft_smooth.mean()
        
        # Spinning arcs
        count = 4
        for i in range(count):
             r = r_base + i * 15
             width = 8
             
             speed = (i+1) * 2
             angle_start = self.time_elapsed * speed
             
             # Break into segments
             segs = 3
             for j in range(segs):
                 start = angle_start + (j/segs) * 6.28
                 length = 1.0 + (val/255.0) # Length reacts to audio
                 
                 rect = (cx - r, cy - r, r*2, r*2)
                 c = self._get_color(i * 30 + val)
                 pygame.draw.arc(surf, c, rect, start, start + length, width)
        
        # Center Pulse
        c_center = self._get_color(0)
        pygame.draw.circle(surf, c_center, (cx, cy), int(val * 0.5), 2)
        if self.is_beat:
             pygame.draw.circle(surf, (255, 255, 255), (cx, cy), int(val * 0.8), 5)

    def draw_13_dna_helix(self, surf, w, h):
        points_a = []
        points_b = []
        
        count = 50
        spacing = w / count
        amp_base = h * 0.25
        
        freq = 2 # Cycles
        
        # Scroll effect
        shift = self.time_elapsed * 5
        
        for i in range(count):
             x = i * spacing
             
             real_i = i + shift
             
             phase = (real_i / count) * math.pi * 2 * freq
             
             fft_idx = int((i/count) * len(self.fft_smooth))
             amp_mod = 1 + (self.fft_smooth[fft_idx] / 100.0)
             
             y_offset = math.sin(phase) * amp_base * amp_mod
             
             pa = (x, h//2 + y_offset)
             pb = (x, h//2 - y_offset)
             points_a.append(pa)
             points_b.append(pb)
             
             # Rungs
             if i % 2 == 0:
                  c = (100, 100, 100)
                  # If loud, bright rungs
                  if self.fft_smooth[fft_idx] > 150: c = (255, 255, 255)
                  pygame.draw.line(surf, c, pa, pb, 1)
                  
                  # Nodes
                  pygame.draw.circle(surf, self._get_color(i*10), (int(pa[0]), int(pa[1])), 4)
                  pygame.draw.circle(surf, self._get_color(i*10 + 180), (int(pb[0]), int(pb[1])), 4)
                  
        c1 = (0, 255, 100)
        c2 = (0, 100, 255)
        
        if len(points_a) > 2:
            pygame.draw.lines(surf, c1, False, points_a, 3)
    def draw_14_plasma_wave(self, surf, w, h):
        # Plasma Wave: Colorful sine waves
        cx, cy = w//2, h//2
        count = 50
        
        for i in range(count):
            idx = int((i/count) * len(self.fft_smooth))
            val = self.fft_smooth[idx]
            
            x = (i/count) * w
            
            # Multiple sine waves combined
            y_base = h/2 + math.sin(self.time_elapsed * 2 + i * 0.1) * h*0.2
            y_mod = math.sin(self.time_elapsed * 5 + i * 0.5) * (val * 0.5)
            
            y = y_base + y_mod
            
            radius = 10 + val * 0.3
            c = self._get_color(i*10 + val)
            
            # Glow orb
            self._draw_glow_circle(surf, c, (int(x), int(y)), radius, 50)
            
        # Connect lines
        pts = []
        for i in range(count):
             idx = int((i/count) * len(self.fft_smooth))
             val = self.fft_smooth[idx]
             x = (i/count) * w
             y = h/2 + math.sin(self.time_elapsed * 2 + i * 0.1) * h*0.2 + math.sin(self.time_elapsed * 5 + i * 0.5) * (val * 0.5)
             pts.append((x, y))
             
        if len(pts) > 1:
            pygame.draw.lines(surf, (255, 255, 255), False, pts, 2)

    def draw_15_cyber_grid(self, surf, w, h):
        # Retro Grid pulsing
        speed = self.time_elapsed * 50
        bass = self.fft_smooth[0]
        
        # Grid lines
        grid_size = 40
        cols = int(w / grid_size) + 2
        rows = int(h / grid_size) + 2
        
        offset_x = (speed) % grid_size
        offset_y = (speed) % grid_size
        
        c_lines = (0, 100, 200)
        c_beat = (200, 0, 255) if self.is_beat else c_lines
        
        for i in range(cols):
            x = i * grid_size - offset_x
            pygame.draw.line(surf, c_lines, (x, 0), (x, h), 1)
            
        for j in range(rows):
            y = j * grid_size - offset_y
            pygame.draw.line(surf, c_lines, (0, y), (w, y), 1)
            
        # Hexagons or pulse at intersections if loud
        for i in range(cols):
            for j in range(rows):
                if (i+j) % 4 == 0:
                     val = self.fft_smooth[(i*j)%64]
                     if val > 50:
                         x = i * grid_size - offset_x
                         y = j * grid_size - offset_y
                         r = val * 0.1
                         pygame.draw.circle(surf, c_beat, (int(x), int(y)), int(r))

    def draw_16_classic_led(self, surf, w, h):
        # Classic Green-Yellow-Red bars
        count = 32
        bar_w = w / count * 0.8
        gap = w / count * 0.2
        
        for i in range(count):
            idx = int((i/count) * len(self.fft_smooth))
            val = self.fft_smooth[idx]
            
            mh = (val / 255.0) * h
            x = i * (bar_w + gap) + gap/2
            
            # Draw segments
            seg_h = 5
            segs = int(mh / (seg_h + 2))
            
            for j in range(segs):
                y = h - j * (seg_h + 2) - 10
                
                # Color Gradient
                rat = j / (h / (seg_h + 2))
                if rat < 0.5: c = (0, 255, 0) # Green
                elif rat < 0.8: c = (255, 255, 0) # Yellow
                else: c = (255, 0, 0) # Red
                
                pygame.draw.rect(surf, c, (x, y, bar_w, seg_h))

    def draw_17_vortex_core(self, surf, w, h):
        cx, cy = w//2, h//2
        count = 60
        
        spin = self.time_elapsed * 2
        
        for i in range(count):
             idx = i % 64
             val = self.fft_smooth[idx]
             
             angle = (i/count) * math.pi * 4 + spin # Spiral
             r = (i/count) * (min(w,h)*0.8) # Spiral out
             
             # Perturb R
             r += (val / 255.0) * 50
             
             x = cx + math.cos(angle) * r
             y = cy + math.sin(angle) * r
             
             c = self._get_color(val + i*5)
             size = 4 + val * 0.05
             
             pygame.draw.circle(surf, c, (int(x), int(y)), int(size))
             
        # Center black hole
        pygame.draw.circle(surf, (0,0,0), (cx, cy), 20)
        pygame.draw.circle(surf, (255,255,255), (cx, cy), 20, 1)

    def draw_18_aurora_borealis(self, surf, w, h):
        # Soft gradients
        count = 20
        points = []
        points.append((0, h)) # Bottom left
        
        for i in range(count + 1):
             x = (i/count) * w
             
             # Perlin-ish noise via sines
             wave1 = math.sin(self.time_elapsed + i*0.5) * 50
             wave2 = math.cos(self.time_elapsed * 0.5 + i*0.2) * 30
             val = self.fft_smooth[int((i/count)*63)] * 0.5
             
             y = h/2 + wave1 + wave2 - val
             points.append((x, y))
             
        points.append((w, h)) # Bottom right
        
        if len(points) > 3:
             # Transparent overlay
             s = pygame.Surface((w,h), pygame.SRCALPHA)
             c = self._get_color(self.time_elapsed * 20, sat=80, val=200)
             col = (c.r, c.g, c.b, 100)
             pygame.draw.polygon(s, col, points)
             surf.blit(s, (0,0))
             
        # Second layer
        points2 = [(0, h)]
        for i in range(count + 1):
             x = (i/count) * w
             wave1 = math.sin(self.time_elapsed*1.5 + i*0.4 + 2) * 60
             y = h/2 + wave1 + 50
             points2.append((x, y))
        points2.append((w, h))
        
        if len(points2) > 3:
             s = pygame.Surface((w,h), pygame.SRCALPHA)
             c = self._get_color(self.time_elapsed * 20 + 90, sat=80, val=200)
             col = (c.r, c.g, c.b, 80)
             pygame.draw.polygon(s, col, points2)
             surf.blit(s, (0,0))
