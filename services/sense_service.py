#!/usr/bin/env python3
"""
ByteBeast Sensor Service - Sensor polling and feature extraction.

Reads from hardware sensors and publishes environmental features via MQTT.
"""

import time
import logging
import signal
import sys
from pathlib import Path

# Add bytebeast to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sensors.manager import SensorManager, MockSensorManager
from core.database import get_database
from core.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('bytebeast.sense')


class SenseService:
    """Sensor data collection service."""
    
    def __init__(self, mock_mode: bool = False):
        """Initialize sensor service."""
        self.config = get_config()
        self.db = get_database()
        self.running = False
        
        # Initialize sensor manager
        if mock_mode:
            self.sensor_manager = MockSensorManager()
            logger.info("Started in mock mode")
        else:
            self.sensor_manager = SensorManager()
            logger.info("Started with real sensors")
        
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
        logger.info("Sensor service started")
        
        # Get sampling rate from config
        sample_rate = self.config.sensors.get('environmental_rate', 1)  # Hz
        sleep_interval = 1.0 / sample_rate
        
        try:
            while self.running:
                start_time = time.time()
                
                # Read all sensors
                try:
                    features = self.sensor_manager.read_all_sensors()
                    
                    # Save to database
                    self.db.save_sensor_data(features)
                    
                    # Log periodic status
                    if int(start_time) % 60 == 0:  # Every minute
                        logger.info(f"Sensor reading: {features.temp_c:.1f}°C, "
                                  f"{features.rh:.0f}%RH, {features.lux:.0f}lux, "
                                  f"{features.vbat:.2f}V")
                    
                    # TODO: Publish to MQTT when implemented
                    
                except Exception as e:
                    logger.error(f"Error reading sensors: {e}")
                
                # Sleep for remainder of interval
                elapsed = time.time() - start_time
                sleep_time = max(0, sleep_interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
        except Exception as e:
            logger.error(f"Fatal error in sensor service: {e}")
        finally:
            logger.info("Sensor service stopped")


def main():
    """Main entry point."""
    # Check for mock mode argument
    mock_mode = '--mock' in sys.argv or '--test' in sys.argv
    
    service = SenseService(mock_mode=mock_mode)
    service.run()


if __name__ == '__main__':
    main()