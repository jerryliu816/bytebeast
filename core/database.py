"""
Database management for ByteBeast virtual pet.
"""

import sqlite3
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import contextmanager

from .models import Beast, EnvFeatures, EmojiFrame, PowerState, SocialEncounter


class ByteBeastDB:
    """SQLite database manager for ByteBeast."""
    
    def __init__(self, db_path: str = "/home/jerry/bytebeast.db"):
        """Initialize database connection."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
        finally:
            conn.close()
    
    def init_database(self):
        """Initialize database tables."""
        with self.get_connection() as conn:
            # State snapshot table - current beast state
            conn.execute('''
                CREATE TABLE IF NOT EXISTS state_snapshot (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    json TEXT NOT NULL,
                    ts INTEGER NOT NULL
                )
            ''')
            
            # History sense data - ring buffer for sensor data
            conn.execute('''
                CREATE TABLE IF NOT EXISTS history_sense (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    json TEXT NOT NULL,
                    ts INTEGER NOT NULL
                )
            ''')
            
            # History events - game events and interactions
            conn.execute('''
                CREATE TABLE IF NOT EXISTS history_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    ts INTEGER NOT NULL
                )
            ''')
            
            # Configuration key-value store
            conn.execute('''
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            ''')
            
            # Daily telemetry aggregation
            conn.execute('''
                CREATE TABLE IF NOT EXISTS telemetry_daily (
                    ts_day INTEGER PRIMARY KEY,
                    stats_json TEXT NOT NULL
                )
            ''')
            
            # Create indexes for performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_sense_ts ON history_sense(ts)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_events_ts ON history_events(ts)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_events_type ON history_events(type)')
            
            conn.commit()
    
    def save_beast_state(self, beast: Beast):
        """Save current beast state snapshot."""
        beast_data = {
            'mood': beast.mood,
            'needs': beast.needs,
            'traits': beast.traits, 
            'evolution_path': beast.evolution_path,
            'evolution_stage': beast.evolution_stage,
            'evolution_prog': beast.evolution_prog,
            'energy': beast.energy,
            'last_updated': beast.last_updated
        }
        
        with self.get_connection() as conn:
            conn.execute(
                'INSERT INTO state_snapshot (json, ts) VALUES (?, ?)',
                (json.dumps(beast_data), int(time.time()))
            )
            conn.commit()
    
    def load_latest_beast_state(self) -> Optional[Beast]:
        """Load the most recent beast state."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                'SELECT json FROM state_snapshot ORDER BY ts DESC LIMIT 1'
            )
            row = cursor.fetchone()
            
            if row:
                data = json.loads(row['json'])
                return Beast(**data)
            return None
    
    def save_sensor_data(self, features: EnvFeatures):
        """Save sensor feature data."""
        features_data = {
            'lux': features.lux,
            'cct_k': features.cct_k,
            'temp_c': features.temp_c,
            'rh': features.rh,
            'pressure_hpa': features.pressure_hpa,
            'pressure_trend': features.pressure_trend,
            'motion_rms_g': features.motion_rms_g,
            'shake_events': features.shake_events,
            'heading_deg': features.heading_deg,
            'roll': features.roll,
            'pitch': features.pitch,
            'yaw': features.yaw,
            'vbat': features.vbat,
            'ibat': features.ibat,
            'pwr_w': features.pwr_w,
            'charging': features.charging,
            'ssid_fingerprint': features.ssid_fingerprint,
            'timestamp': features.timestamp
        }
        
        with self.get_connection() as conn:
            conn.execute(
                'INSERT INTO history_sense (json, ts) VALUES (?, ?)',
                (json.dumps(features_data), int(features.timestamp))
            )
            conn.commit()
    
    def get_recent_sensor_data(self, hours: int = 24) -> List[EnvFeatures]:
        """Get sensor data from recent hours."""
        cutoff = int(time.time() - (hours * 3600))
        
        with self.get_connection() as conn:
            cursor = conn.execute(
                'SELECT json FROM history_sense WHERE ts > ? ORDER BY ts DESC',
                (cutoff,)
            )
            
            features = []
            for row in cursor:
                data = json.loads(row['json'])
                features.append(EnvFeatures(**data))
            
            return features
    
    def log_event(self, event_type: str, payload: Dict[str, Any]):
        """Log a game event."""
        with self.get_connection() as conn:
            conn.execute(
                'INSERT INTO history_events (type, payload_json, ts) VALUES (?, ?, ?)',
                (event_type, json.dumps(payload), int(time.time()))
            )
            conn.commit()
    
    def get_events(self, event_type: Optional[str] = None, hours: int = 24) -> List[Dict]:
        """Get recent events, optionally filtered by type."""
        cutoff = int(time.time() - (hours * 3600))
        
        with self.get_connection() as conn:
            if event_type:
                cursor = conn.execute(
                    'SELECT type, payload_json, ts FROM history_events '
                    'WHERE type = ? AND ts > ? ORDER BY ts DESC',
                    (event_type, cutoff)
                )
            else:
                cursor = conn.execute(
                    'SELECT type, payload_json, ts FROM history_events '
                    'WHERE ts > ? ORDER BY ts DESC',
                    (cutoff,)
                )
            
            events = []
            for row in cursor:
                events.append({
                    'type': row['type'],
                    'payload': json.loads(row['payload_json']),
                    'timestamp': row['ts']
                })
            
            return events
    
    def set_config(self, key: str, value: Any):
        """Set configuration value."""
        with self.get_connection() as conn:
            conn.execute(
                'INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)',
                (key, json.dumps(value))
            )
            conn.commit()
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT value FROM config WHERE key = ?', (key,))
            row = cursor.fetchone()
            
            if row:
                return json.loads(row['value'])
            return default
    
    def cleanup_old_data(self, sensor_days: int = 7, event_days: int = 30):
        """Clean up old data to prevent unbounded growth."""
        sensor_cutoff = int(time.time() - (sensor_days * 24 * 3600))
        event_cutoff = int(time.time() - (event_days * 24 * 3600))
        
        with self.get_connection() as conn:
            # Keep only recent sensor data
            conn.execute('DELETE FROM history_sense WHERE ts < ?', (sensor_cutoff,))
            
            # Keep only recent events
            conn.execute('DELETE FROM history_events WHERE ts < ?', (event_cutoff,))
            
            # Keep only recent state snapshots (last 100)
            conn.execute('''
                DELETE FROM state_snapshot 
                WHERE id NOT IN (
                    SELECT id FROM state_snapshot 
                    ORDER BY ts DESC LIMIT 100
                )
            ''')
            
            conn.commit()
    
    def get_evolution_stats(self, hours: int = 48) -> Dict[str, float]:
        """Calculate evolution path statistics for recent period."""
        recent_data = self.get_recent_sensor_data(hours)
        
        if not recent_data:
            return {}
        
        # Calculate exposure scores
        sun_score = 0.0
        shadow_score = 0.0  
        ember_score = 0.0
        frost_score = 0.0
        social_score = 0.0
        lone_score = 0.0
        
        total_minutes = len(recent_data)
        
        for features in recent_data:
            # Sun path: bright + warm + active
            if features.lux > 1000 and features.temp_c > 20 and features.motion_rms_g > 0.1:
                sun_score += 1
            
            # Shadow path: dark + quiet + low motion
            if features.lux < 100 and features.motion_rms_g < 0.05:
                shadow_score += 1
            
            # Ember path: hot temperatures
            if features.temp_c > 30:
                ember_score += 1
            
            # Frost path: cold temperatures  
            if features.temp_c < 10:
                frost_score += 1
            
            # Social/lone paths would need peer detection data
            # For now, use motion as proxy for social activity
            if features.motion_rms_g > 0.2:
                social_score += 0.5
            else:
                lone_score += 0.5
        
        # Normalize scores
        if total_minutes > 0:
            return {
                'sun': sun_score / total_minutes,
                'shadow': shadow_score / total_minutes,
                'ember': ember_score / total_minutes, 
                'frost': frost_score / total_minutes,
                'social': social_score / total_minutes,
                'lone': lone_score / total_minutes
            }
        
        return {}


# Global database instance
_db_instance = None

def get_database() -> ByteBeastDB:
    """Get singleton database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = ByteBeastDB()
    return _db_instance