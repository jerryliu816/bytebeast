#!/usr/bin/env python3
"""
ByteBeast Visualization Service - Emoji rendering to LCD displays.

Renders emoji UI to the triple LCD display system based on beast state.
"""

import time
import logging
import signal
import sys
from pathlib import Path

# Add bytebeast to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from display.manager import DisplayManager, MockDisplayManager
from core.database import get_database
from core.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('bytebeast.viz')


class VizService:
    """Display visualization service."""
    
    def __init__(self, mock_mode: bool = False):
        """Initialize visualization service."""
        self.config = get_config()
        self.db = get_database()
        self.running = False
        self.start_time = time.time()
        
        # Initialize display manager
        if mock_mode:
            self.display_manager = MockDisplayManager()
            logger.info("Started in mock mode")
        else:
            self.display_manager = DisplayManager()
            logger.info("Started with real displays")
        
        # Frame rate control
        self.current_fps = self.config.display['fps_active']
        self.static_mode = False
        self.brightness = 1.0
        
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
        logger.info("Visualization service started")
        
        frame_count = 0
        last_fps_log = time.time()
        
        try:
            while self.running:
                start_time = time.time()
                
                try:
                    # Get current beast state
                    beast = self.db.load_latest_beast_state()
                    if not beast:
                        logger.warning("No beast state available")
                        time.sleep(1.0)
                        continue
                    
                    # Get recent sensor data
                    recent_data = self.db.get_recent_sensor_data(hours=1)
                    if not recent_data:
                        logger.warning("No recent sensor data available")
                        time.sleep(1.0)
                        continue
                    
                    latest_env = recent_data[0]
                    
                    # Check if we should adjust display settings based on power
                    # This would normally come from power service via MQTT
                    # For now, simulate power-aware display
                    battery_pct = self.display_manager._calculate_battery_percent(latest_env.vbat)
                    
                    if battery_pct <= self.config.display['battery_shutdown_pct']:
                        # Critical battery - show shutdown warning
                        self._show_shutdown_warning()
                        time.sleep(5.0)
                        continue
                    elif battery_pct <= self.config.display['battery_static_pct']:
                        # Static mode
                        if not self.static_mode:
                            logger.info("Entering static display mode")
                            self.static_mode = True
                            self.current_fps = 1
                    elif battery_pct <= self.config.display['battery_dim_pct']:
                        # Dim mode
                        if self.current_fps != self.config.display['fps_idle']:
                            logger.info("Entering dim display mode")
                            self.static_mode = False
                            self.current_fps = self.config.display['fps_idle']
                            self.brightness = 0.5
                    else:
                        # Normal mode
                        if self.current_fps != self.config.display['fps_active']:
                            logger.info("Entering normal display mode")
                            self.static_mode = False
                            self.current_fps = self.config.display['fps_active']
                            self.brightness = 1.0
                    
                    # Create emoji frame from beast state
                    emoji_frame = self.display_manager.create_emoji_frame(beast, latest_env)
                    
                    # Update display (skip animation frames in static mode)
                    if self.static_mode or frame_count % 10 == 0:  # Update every 10th frame when not static
                        uptime = time.time() - self.start_time
                        self.display_manager.update_display(emoji_frame, latest_env, uptime)
                        
                        # Set brightness if supported
                        self.display_manager.set_brightness(self.brightness)
                    
                    frame_count += 1
                    
                    # Log FPS periodically
                    if time.time() - last_fps_log > 60:  # Every minute
                        actual_fps = frame_count / (time.time() - last_fps_log)
                        logger.info(f"Display: {actual_fps:.1f} FPS, "
                                   f"mode: {'static' if self.static_mode else 'active'}, "
                                   f"battery: {battery_pct:.0f}%")
                        frame_count = 0
                        last_fps_log = time.time()
                    
                    # TODO: Listen for display commands from MQTT
                    
                except Exception as e:
                    logger.error(f"Error updating display: {e}")
                
                # Frame rate control
                frame_interval = 1.0 / self.current_fps
                elapsed = time.time() - start_time
                sleep_time = max(0, frame_interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
        except Exception as e:
            logger.error(f"Fatal error in visualization service: {e}")
        finally:
            # Clear displays on shutdown
            self.display_manager.clear_all_displays()
            logger.info("Visualization service stopped")
    
    def _show_shutdown_warning(self):
        """Show critical battery shutdown warning."""
        try:
            # Create shutdown warning image
            from PIL import Image, ImageDraw
            
            # Main display warning
            if hasattr(self.display_manager, 'main_display') and self.display_manager.main_display:
                image = Image.new('RGB', (240, 240), (100, 0, 0))  # Dark red background
                draw = ImageDraw.Draw(image)
                
                # Warning text
                draw.text((120, 100), "LOW BATTERY", anchor="mm", 
                         fill=(255, 255, 255), font=self.display_manager.font_large)
                draw.text((120, 130), "SHUTTING DOWN", anchor="mm",
                         fill=(255, 255, 255), font=self.display_manager.font_medium)
                
                # Battery icon (simple rectangle)
                draw.rectangle([100, 160, 140, 180], outline=(255, 255, 255), width=2)
                draw.rectangle([102, 162, 110, 178], fill=(255, 100, 100))  # Red empty battery
                
                if not self.display_manager.mock_mode:
                    self.display_manager.main_display.ShowImage(image)
                else:
                    logger.info("Mock shutdown warning displayed")
            
        except Exception as e:
            logger.error(f"Error showing shutdown warning: {e}")


def main():
    """Main entry point."""
    # Check for mock mode argument
    mock_mode = '--mock' in sys.argv or '--test' in sys.argv
    
    service = VizService(mock_mode=mock_mode)
    service.run()


if __name__ == '__main__':
    main()