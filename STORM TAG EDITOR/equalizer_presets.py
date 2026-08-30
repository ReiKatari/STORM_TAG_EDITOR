# -*- coding: utf-8 -*-
"""
Storm Tag Editor - Equalizer Presets
FFmpeg audio filter presets for different music styles.
"""

# Equalizer presets as FFmpeg equalizer filter strings
# Format: superequalizer=f1h:f2h:f3h:...f18h (18 bands from 65Hz to 16kHz)
# Each band value is in dB, 0 = neutral, positive = boost, negative = cut

EQ_PRESETS = {
    'Flat': '',  # No EQ applied
    'Rock': 'equalizer=f=60:t=q:w=1:g=4,equalizer=f=170:t=q:w=1:g=2,equalizer=f=1000:t=q:w=1:g=-1,equalizer=f=4000:t=q:w=1:g=3,equalizer=f=12000:t=q:w=1:g=4',
    'Pop': 'equalizer=f=60:t=q:w=1:g=-1,equalizer=f=250:t=q:w=1:g=2,equalizer=f=1000:t=q:w=1:g=4,equalizer=f=4000:t=q:w=1:g=3,equalizer=f=8000:t=q:w=1:g=2',
    'Classical': 'equalizer=f=60:t=q:w=1:g=-2,equalizer=f=250:t=q:w=1:g=-1,equalizer=f=1000:t=q:w=1:g=0,equalizer=f=4000:t=q:w=1:g=2,equalizer=f=8000:t=q:w=1:g=3',
    'Jazz': 'equalizer=f=60:t=q:w=1:g=2,equalizer=f=250:t=q:w=1:g=0,equalizer=f=1000:t=q:w=1:g=2,equalizer=f=4000:t=q:w=1:g=3,equalizer=f=8000:t=q:w=1:g=1',
    'Electronic': 'equalizer=f=60:t=q:w=1:g=5,equalizer=f=250:t=q:w=1:g=3,equalizer=f=1000:t=q:w=1:g=0,equalizer=f=4000:t=q:w=1:g=2,equalizer=f=12000:t=q:w=1:g=4',
    'Hip-Hop': 'equalizer=f=60:t=q:w=1:g=6,equalizer=f=250:t=q:w=1:g=4,equalizer=f=1000:t=q:w=1:g=0,equalizer=f=4000:t=q:w=1:g=2,equalizer=f=8000:t=q:w=1:g=1',
    'Metal': 'equalizer=f=60:t=q:w=1:g=5,equalizer=f=250:t=q:w=1:g=3,equalizer=f=1000:t=q:w=1:g=-2,equalizer=f=4000:t=q:w=1:g=4,equalizer=f=12000:t=q:w=1:g=5',
    'Vocal': 'equalizer=f=60:t=q:w=1:g=-3,equalizer=f=250:t=q:w=1:g=0,equalizer=f=1000:t=q:w=1:g=3,equalizer=f=4000:t=q:w=1:g=4,equalizer=f=8000:t=q:w=1:g=2',
    'Bass Boost': 'equalizer=f=60:t=q:w=1:g=8,equalizer=f=150:t=q:w=1:g=6,equalizer=f=400:t=q:w=1:g=3,equalizer=f=1000:t=q:w=1:g=0,equalizer=f=4000:t=q:w=1:g=0',
    'Treble Boost': 'equalizer=f=60:t=q:w=1:g=0,equalizer=f=250:t=q:w=1:g=0,equalizer=f=1000:t=q:w=1:g=1,equalizer=f=4000:t=q:w=1:g=4,equalizer=f=12000:t=q:w=1:g=6',
}

def get_preset_names():
    """Return list of preset names."""
    return list(EQ_PRESETS.keys())

def get_preset_filter(name):
    """Get FFmpeg filter string for preset."""
    return EQ_PRESETS.get(name, '')

def apply_eq_to_args(args_str, eq_preset):
    """Add equalizer filter to FFmpeg args string."""
    eq_filter = EQ_PRESETS.get(eq_preset, '')
    if not eq_filter:
        return args_str
    
    # Insert -af filter before output format options
    if '-af' in args_str:
        # Append to existing -af
        parts = args_str.split('-af')
        return f"{parts[0]}-af {eq_filter},{parts[1].strip()}"
    else:
        return f"-af {eq_filter} {args_str}"
