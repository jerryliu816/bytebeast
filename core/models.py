"""
Core data models for ByteBeast virtual pet.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List
import time


@dataclass
class EnvFeatures:
    """Environmental sensor feature data."""
    lux: float              # from clear channel
    cct_k: float           # color temperature
    temp_c: float          # temperature in Celsius
    rh: float              # relative humidity percentage
    pressure_hpa: float    # pressure in hPa
    pressure_trend: float  # dP/dt smoothed
    motion_rms_g: float    # motion RMS in g
    shake_events: int      # shake events per minute
    heading_deg: float     # compass heading
    roll: float            # IMU roll angle
    pitch: float           # IMU pitch angle  
    yaw: float             # IMU yaw angle
    vbat: float            # battery voltage
    ibat: float            # battery current
    pwr_w: float           # power consumption in watts
    charging: bool         # charging status
    ssid_fingerprint: str  # hashed list for place/peer inference
    timestamp: float       # Unix timestamp

    def __post_init__(self):
        """Set timestamp if not provided."""
        if not self.timestamp:
            self.timestamp = time.time()


@dataclass
class Beast:
    """Virtual pet state data."""
    mood: str                           # current mood (happy, calm, sleepy, etc.)
    needs: Dict[str, float] = field(default_factory=lambda: {
        'hunger': 50.0,
        'rest': 50.0, 
        'social': 50.0,
        'hygiene': 50.0
    })                                  # needs 0-100
    traits: Dict[str, float] = field(default_factory=lambda: {
        'playful': 0.5,
        'needy': 0.5,
        'rebellious': 0.5,
        'social': 0.5,
        'explorer': 0.5
    })                                  # traits 0-1
    evolution_path: str = 'sun'         # current evolution path
    evolution_stage: int = 1            # 1-4
    evolution_prog: float = 0.0         # progress to next stage 0-1
    energy: float = 100.0               # energy level 0-100
    last_updated: float = field(default_factory=time.time)

    def __post_init__(self):
        """Validate ranges."""
        # Clamp needs to 0-100
        for need, value in self.needs.items():
            self.needs[need] = max(0.0, min(100.0, value))
        
        # Clamp traits to 0-1
        for trait, value in self.traits.items():
            self.traits[trait] = max(0.0, min(1.0, value))
        
        # Clamp other values
        self.evolution_stage = max(1, min(4, self.evolution_stage))
        self.evolution_prog = max(0.0, min(1.0, self.evolution_prog))
        self.energy = max(0.0, min(100.0, self.energy))


@dataclass  
class EmojiFrame:
    """Display frame with emoji and UI elements."""
    emoji: str                          # main emoji character
    badges: List[str] = field(default_factory=list)  # up to 3 badges
    bars: Dict[str, float] = field(default_factory=dict)  # progress bars
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self):
        """Validate constraints."""
        # Limit badges to 3
        if len(self.badges) > 3:
            self.badges = self.badges[:3]
        
        # Clamp bar values to 0-1
        for bar, value in self.bars.items():
            self.bars[bar] = max(0.0, min(1.0, value))


@dataclass
class PowerState:
    """Power and battery state information."""
    battery_percent: float              # calculated battery percentage
    voltage: float                      # battery voltage
    current_ma: float                   # current draw in mA
    power_w: float                      # power consumption in watts
    charging: bool                      # charging status
    low_battery: bool = False          # low battery warning
    critical_battery: bool = False     # critical battery shutdown
    timestamp: float = field(default_factory=time.time)


@dataclass
class SocialEncounter:
    """Social interaction data."""
    peer_hash: str                      # anonymized peer identifier
    encounter_type: str                 # 'greet' or 'duel'
    result: Dict = field(default_factory=dict)  # encounter result data
    xp_gained: float = 0.0             # experience points gained
    timestamp: float = field(default_factory=time.time)


# Evolution path configurations
EVOLUTION_PATHS = {
    'sun': {
        'name': 'Solar Path',
        'stages': ['🐣', '🐥', '🦅', '🦄'],
        'description': 'Bright, warm, and active environments'
    },
    'shadow': {
        'name': 'Shadow Path', 
        'stages': ['🦇', '🦉', '🐺', '🐉'],
        'description': 'Dark, quiet, low-motion environments'
    },
    'ember': {
        'name': 'Ember Path',
        'stages': ['🦁', '🔥', '🐯', '🐉'], 
        'description': 'Hot temperature environments'
    },
    'frost': {
        'name': 'Frost Path',
        'stages': ['🐧', '❄️', '🐻‍❄️', '🐉'],
        'description': 'Cold temperature environments'
    },
    'social': {
        'name': 'Social Path',
        'stages': ['🐒', '🦁', '🦄', '👑'],
        'description': 'High peer interaction environments'
    },
    'lone': {
        'name': 'Lone Wolf Path',
        'stages': ['🐭', '🦊', '🐺', '🐉'],
        'description': 'Solitary exploration environments'
    }
}

# Mood emoji mappings
MOOD_EMOJIS = {
    'happy': '😃',
    'calm': '😌', 
    'sleepy': '😴',
    'anxious': '😰',
    'sick': '🤒',
    'playful': '🤩',
    'bored': '😐',
    'curious': '🧐',
    'hot': '🥵',
    'cold': '🥶'
}

# Badge emojis for environment/status
BADGE_EMOJIS = {
    # Environment badges
    'sunny': '☀️',
    'dark': '🌙', 
    'hot': '🔥',
    'cold': '❄️',
    'air_quality': '🧪',
    'low_battery': '🔋',
    # Progress badges  
    'evolving': '✨'
}