#!/usr/bin/env python3
"""
ByteBeast Day Simulation

Simulates a full day of ByteBeast operation for testing.
"""

import time
import sys
import logging
from pathlib import Path

# Add bytebeast to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sensors.manager import MockSensorManager
from state.mood_engine import MoodEngine, create_default_beast
from display.manager import MockDisplayManager
from power.manager import MockPowerManager
from core.database import ByteBeastDB
from core.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('bytebeast.simulation')


class DaySimulation:
    """Simulate a day in the life of ByteBeast."""
    
    def __init__(self):
        """Initialize simulation."""
        self.config = get_config()
        self.db = ByteBeastDB('/tmp/bytebeast_simulation.db')
        
        # Initialize components
        self.sensor_manager = MockSensorManager()
        self.mood_engine = MoodEngine()
        self.display_manager = MockDisplayManager()
        self.power_manager = MockPowerManager()
        
        # Create beast
        self.beast = create_default_beast()
        logger.info(f"Created ByteBeast: {self.beast.mood} mood, {self.beast.evolution_path} path")
        
        # Simulation state
        self.simulation_time = 0
        self.mood_changes = 0
        self.evolution_changes = 0
    
    def simulate_hour(self, hour_of_day: int):
        """Simulate one hour of operation."""
        logger.info(f"=== Hour {hour_of_day}:00 ===")
        
        # Simulate multiple sensor readings per hour
        for minute in range(0, 60, 10):  # Every 10 minutes
            # Read sensors
            features = self.sensor_manager.read_all_sensors()
            
            # Adjust sensor data based on time of day
            features = self._adjust_for_time_of_day(features, hour_of_day, minute)
            
            # Save sensor data
            self.db.save_sensor_data(features)
            
            # Process beast state
            old_mood = self.beast.mood
            old_stage = self.beast.evolution_stage
            old_path = self.beast.evolution_path
            
            # Update beast
            self.beast.mood = self.mood_engine.infer_mood(features, self.beast)
            self.beast = self.mood_engine.update_needs(self.beast, features)
            self.beast = self.mood_engine.tick_traits(features, self.beast)
            self.beast = self.mood_engine.update_evolution(features, self.beast)
            
            # Track changes
            if self.beast.mood != old_mood:
                logger.info(f"  Mood: {old_mood} -> {self.beast.mood}")
                self.mood_changes += 1
            
            if (self.beast.evolution_stage != old_stage or 
                self.beast.evolution_path != old_path):
                logger.info(f"  Evolution: {old_path} stage {old_stage} -> "
                           f"{self.beast.evolution_path} stage {self.beast.evolution_stage}")
                self.evolution_changes += 1
            
            # Save state
            self.db.save_beast_state(self.beast)
            
            # Update display
            emoji_frame = self.display_manager.create_emoji_frame(self.beast, features)
            self.display_manager.update_display(emoji_frame, features)
            
            # Power management
            power_state = self.power_manager.read_power_state()
            policy = self.power_manager.get_power_policy(power_state)
            
            if minute == 0:  # Log once per hour
                logger.info(f"  Status: {self.beast.mood}, "
                           f"needs avg {sum(self.beast.needs.values())/len(self.beast.needs):.0f}%, "
                           f"energy {self.beast.energy:.0f}%, "
                           f"battery {power_state.battery_percent:.0f}%")
        
        # Generate hourly tasks
        tasks = self.mood_engine.generate_tasks(self.beast, features)
        if tasks:
            logger.info(f"  Tasks: {[task['description'] for task in tasks[:2]]}")
    
    def _adjust_for_time_of_day(self, features, hour, minute):
        """Adjust sensor features based on time of day.""" 
        import math
        
        # Light levels - day/night cycle
        if 6 <= hour <= 18:  # Daytime
            base_lux = 5000
            # Peak at noon
            sun_factor = math.sin((hour - 6) * math.pi / 12)
            features.lux = base_lux * sun_factor + 1000
            features.cct_k = 5500
        else:  # Nighttime
            features.lux = 50
            features.cct_k = 3000
        
        # Temperature variation
        temp_cycle = math.sin((hour - 6) * math.pi / 12)
        features.temp_c = 20 + 8 * temp_cycle
        
        # Motion patterns - more active during day
        if 8 <= hour <= 22:
            features.motion_rms_g = 0.1 + 0.2 * (hour % 4) / 4
            features.shake_events = 1 if hour % 3 == 0 else 0
        else:
            features.motion_rms_g = 0.05
            features.shake_events = 0
        
        return features
    
    def run_simulation(self, hours: int = 24):
        """Run full simulation."""
        logger.info(f"Starting {hours}-hour ByteBeast simulation")
        logger.info(f"Initial state: {self.beast.mood} mood, "
                   f"{self.beast.evolution_path} path stage {self.beast.evolution_stage}")
        
        start_time = time.time()
        
        for hour in range(hours):
            try:
                self.simulate_hour(hour)
                
                # Brief pause for realism
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                logger.info("Simulation interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error in hour {hour}: {e}")
        
        # Simulation summary
        elapsed = time.time() - start_time
        logger.info(f"\n=== Simulation Complete ({elapsed:.1f}s) ===")
        logger.info(f"Final state: {self.beast.mood} mood, "
                   f"{self.beast.evolution_path} path stage {self.beast.evolution_stage}")
        logger.info(f"Mood changes: {self.mood_changes}")
        logger.info(f"Evolution changes: {self.evolution_changes}")
        
        # Needs status
        logger.info("Final needs:")
        for need, value in self.beast.needs.items():
            logger.info(f"  {need}: {value:.0f}%")
        
        # Traits status  
        logger.info("Final traits:")
        for trait, value in self.beast.traits.items():
            logger.info(f"  {trait}: {value:.2f}")
        
        # Database stats
        recent_sensors = self.db.get_recent_sensor_data(hours=hours)
        events = self.db.get_events(hours=hours)
        logger.info(f"Database: {len(recent_sensors)} sensor readings, {len(events)} events")
        
        return {
            'final_mood': self.beast.mood,
            'final_path': self.beast.evolution_path,
            'final_stage': self.beast.evolution_stage,
            'mood_changes': self.mood_changes,
            'evolution_changes': self.evolution_changes,
            'sensor_readings': len(recent_sensors),
            'events': len(events)
        }


def main():
    """Main entry point.""" 
    hours = 24
    if len(sys.argv) > 1:
        try:
            hours = int(sys.argv[1])
        except ValueError:
            print("Invalid hours argument, using 24")
    
    simulation = DaySimulation()
    results = simulation.run_simulation(hours)
    
    print(f"\nSimulation Results:")
    print(f"  Duration: {hours} hours")
    print(f"  Final mood: {results['final_mood']}")
    print(f"  Evolution: {results['final_path']} stage {results['final_stage']}")
    print(f"  Mood changes: {results['mood_changes']}")
    print(f"  Evolution changes: {results['evolution_changes']}")
    print(f"  Data points: {results['sensor_readings']} sensors, {results['events']} events")


if __name__ == '__main__':
    main()