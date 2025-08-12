#!/usr/bin/env python3
"""
ByteBeast State Service - Mood, needs, traits, and evolution engine.

Processes sensor data to update beast state and publish mood changes.
"""

import time
import logging
import signal
import sys
from pathlib import Path

# Add bytebeast to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from state.mood_engine import MoodEngine, create_default_beast
from core.database import get_database
from core.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('bytebeast.state')


class StateService:
    """Beast state management service."""
    
    def __init__(self):
        """Initialize state service."""
        self.config = get_config()
        self.db = get_database()
        self.mood_engine = MoodEngine()
        self.running = False
        
        # Load or create beast
        self.beast = self.db.load_latest_beast_state()
        if not self.beast:
            self.beast = create_default_beast()
            logger.info("Created new ByteBeast")
        else:
            logger.info(f"Loaded existing ByteBeast: {self.beast.mood} mood, "
                       f"stage {self.beast.evolution_stage} {self.beast.evolution_path}")
        
        # Set up signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def run(self):
        """Main service loop."""
        self.running = True
        logger.info("State service started")
        
        # Update frequency - every 10 seconds
        update_interval = 10.0
        last_mood_log = 0
        
        try:
            while self.running:
                start_time = time.time()
                
                try:
                    # Get recent sensor data
                    recent_data = self.db.get_recent_sensor_data(hours=1)
                    
                    if recent_data:
                        # Use most recent sensor reading
                        latest_env = recent_data[0]
                        
                        # Update beast state
                        old_mood = self.beast.mood
                        old_stage = self.beast.evolution_stage
                        old_path = self.beast.evolution_path
                        
                        # Infer new mood
                        self.beast.mood = self.mood_engine.infer_mood(latest_env, self.beast)
                        
                        # Update needs and traits
                        self.beast = self.mood_engine.update_needs(self.beast, latest_env)
                        self.beast = self.mood_engine.tick_traits(self.beast, latest_env)
                        
                        # Update evolution
                        self.beast = self.mood_engine.update_evolution(latest_env, self.beast)
                        
                        # Log significant changes
                        if self.beast.mood != old_mood:
                            logger.info(f"Mood changed: {old_mood} -> {self.beast.mood}")
                            self.db.log_event('mood_change', {
                                'old_mood': old_mood,
                                'new_mood': self.beast.mood,
                                'temp_c': latest_env.temp_c,
                                'lux': latest_env.lux,
                                'motion': latest_env.motion_rms_g
                            })
                        
                        if (self.beast.evolution_stage != old_stage or 
                            self.beast.evolution_path != old_path):
                            logger.info(f"Evolution: {old_path} stage {old_stage} -> "
                                       f"{self.beast.evolution_path} stage {self.beast.evolution_stage}")
                            self.db.log_event('evolution_change', {
                                'old_path': old_path,
                                'new_path': self.beast.evolution_path,
                                'old_stage': old_stage,
                                'new_stage': self.beast.evolution_stage,
                                'progression': self.beast.evolution_prog
                            })
                        
                        # Periodic status logging
                        if start_time - last_mood_log > 300:  # Every 5 minutes
                            avg_needs = sum(self.beast.needs.values()) / len(self.beast.needs)
                            logger.info(f"Status: {self.beast.mood} mood, "
                                       f"avg needs {avg_needs:.0f}%, "
                                       f"energy {self.beast.energy:.0f}%, "
                                       f"{self.beast.evolution_path} stage {self.beast.evolution_stage}")
                            last_mood_log = start_time
                        
                        # Save state snapshot
                        self.db.save_beast_state(self.beast)
                        
                        # Generate daily tasks (simplified)
                        if int(start_time) % 3600 == 0:  # Every hour
                            tasks = self.mood_engine.generate_tasks(self.beast, latest_env)
                            if tasks:
                                self.db.log_event('tasks_generated', {'tasks': tasks})
                        
                        # TODO: Publish state changes to MQTT
                        
                    else:
                        logger.warning("No recent sensor data available")
                    
                except Exception as e:
                    logger.error(f"Error updating beast state: {e}")
                
                # Sleep for remainder of interval
                elapsed = time.time() - start_time
                sleep_time = max(0, update_interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
        except Exception as e:
            logger.error(f"Fatal error in state service: {e}")
        finally:
            # Save final state
            if self.beast:
                self.db.save_beast_state(self.beast)
            logger.info("State service stopped")


def main():
    """Main entry point."""
    service = StateService()
    service.run()


if __name__ == '__main__':
    main()