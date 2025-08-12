#!/usr/bin/env python3
"""
ByteBeast Power Service - Battery monitoring and power management.

Monitors battery state and implements power policies for safe operation.
"""

import time
import logging
import signal
import sys
from pathlib import Path

# Add bytebeast to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from power.manager import PowerManager, MockPowerManager
from core.database import get_database
from core.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('bytebeast.power')


class PowerService:
    """Power monitoring and management service."""
    
    def __init__(self, mock_mode: bool = False):
        """Initialize power service."""
        self.config = get_config()
        self.db = get_database()
        self.running = False
        
        # Initialize power manager
        if mock_mode:
            self.power_manager = MockPowerManager()
            logger.info("Started in mock mode")
        else:
            self.power_manager = PowerManager()
            logger.info("Started with real power monitoring")
        
        # Power state tracking
        self.last_policy = None
        self.shutdown_warning_sent = False
        
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
        logger.info("Power service started")
        
        # Monitoring frequency
        sample_rate = self.config.sensors.get('power_rate', 2)  # Hz
        sleep_interval = 1.0 / sample_rate
        last_status_log = 0
        
        try:
            while self.running:
                start_time = time.time()
                
                try:
                    # Read power state
                    power_state = self.power_manager.read_power_state()
                    
                    # Check for power events
                    events = self.power_manager.monitor_power_events(power_state)
                    for event in events:
                        logger.info(f"Power event: {event['type']}")
                        self.db.log_event(f"power_{event['type']}", event)
                    
                    # Determine power policy
                    policy = self.power_manager.get_power_policy(power_state)
                    
                    # Log policy changes
                    if self.last_policy != policy:
                        logger.info(f"Power policy change: FPS={policy.fps}, "
                                   f"dim={policy.dim}, static={policy.static_mode}, "
                                   f"shutdown={policy.shutdown}")
                        
                        self.db.log_event('power_policy_change', {
                            'fps': policy.fps,
                            'dim': policy.dim,
                            'static_mode': policy.static_mode,
                            'shutdown': policy.shutdown,
                            'brightness': policy.brightness,
                            'battery_percent': power_state.battery_percent,
                            'voltage': power_state.voltage
                        })
                        
                        self.last_policy = policy
                    
                    # Handle critical battery shutdown
                    if policy.shutdown and not self.shutdown_warning_sent:
                        logger.critical("Critical battery level - initiating shutdown sequence")
                        self.db.log_event('shutdown_initiated', {
                            'reason': 'critical_battery',
                            'battery_percent': power_state.battery_percent,
                            'voltage': power_state.voltage
                        })
                        
                        # Initiate shutdown (non-blocking)
                        self.power_manager.initiate_shutdown(delay_seconds=60)
                        self.shutdown_warning_sent = True
                    
                    # Log status periodically
                    if start_time - last_status_log > 300:  # Every 5 minutes
                        remaining_time = self.power_manager.estimate_remaining_time(power_state)
                        charging_status = self.power_manager.get_charging_status(power_state)
                        
                        logger.info(f"Power: {power_state.battery_percent:.1f}% "
                                   f"({power_state.voltage:.2f}V), "
                                   f"{power_state.current_ma:.0f}mA, "
                                   f"{power_state.power_w:.2f}W, "
                                   f"{'charging' if power_state.charging else 'discharging'}")
                        
                        if remaining_time < float('inf'):
                            logger.info(f"Estimated time remaining: {remaining_time:.1f} hours")
                        
                        last_status_log = start_time
                    
                    # Save power telemetry
                    self.db.log_event('power_telemetry', {
                        'battery_percent': power_state.battery_percent,
                        'voltage': power_state.voltage,
                        'current_ma': power_state.current_ma,
                        'power_w': power_state.power_w,
                        'charging': power_state.charging,
                        'low_battery': power_state.low_battery,
                        'critical_battery': power_state.critical_battery
                    })
                    
                    # Power optimization suggestions
                    if power_state.battery_percent < 30:
                        optimizations = self.power_manager.optimize_power_consumption(power_state)
                        if optimizations:
                            logger.debug(f"Power optimizations suggested: {optimizations}")
                            # TODO: Send optimization commands via MQTT
                    
                    # TODO: Publish power state to MQTT for other services
                    
                except Exception as e:
                    logger.error(f"Error in power monitoring: {e}")
                
                # Sleep for remainder of interval
                elapsed = time.time() - start_time
                sleep_time = max(0, sleep_interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
        except Exception as e:
            logger.error(f"Fatal error in power service: {e}")
        finally:
            logger.info("Power service stopped")


def main():
    """Main entry point."""
    # Check for mock mode argument
    mock_mode = '--mock' in sys.argv or '--test' in sys.argv
    
    service = PowerService(mock_mode=mock_mode)
    service.run()


if __name__ == '__main__':
    main()