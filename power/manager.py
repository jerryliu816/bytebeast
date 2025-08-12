"""
Power management system for ByteBeast.

Handles battery monitoring, power policies, and safe shutdown procedures.
"""

import sys
import time
import logging
import subprocess
from typing import Dict, Optional, List
from dataclasses import dataclass

# Add existing power module to path
sys.path.append('/home/jerry/dev/bytebeast')

from core.models import PowerState, EnvFeatures
from core.config import get_config

logger = logging.getLogger(__name__)


@dataclass
class PowerPolicy:
    """Power policy configuration."""
    fps: int
    dim: bool
    static_mode: bool
    shutdown: bool
    brightness: float = 1.0


class PowerManager:
    """Manages power consumption and battery monitoring."""
    
    def __init__(self, mock_mode: bool = False):
        """Initialize power manager."""
        self.config = get_config()
        self.mock_mode = mock_mode
        self._init_power_sensor()
        self._shutdown_initiated = False
        self._last_power_state = None
        
    def _init_power_sensor(self):
        """Initialize INA219 power sensor."""
        if self.mock_mode:
            self.ina219 = None
            logger.info("Initialized power manager in mock mode")
            return
            
        try:
            from UPS_HAT_C.INA219 import INA219
            self.ina219 = INA219(addr=0x43)
            logger.info("Initialized INA219 power sensor")
        except Exception as e:
            logger.error(f"Failed to initialize INA219: {e}")
            self.ina219 = None
    
    def read_power_state(self) -> PowerState:
        """Read current power state from sensor."""
        if self.mock_mode:
            # Mock power data for testing
            import random
            voltage = 4.2 - random.uniform(0, 1.5)  # 2.7V to 4.2V range
            current = random.uniform(-100, 500)  # -100mA (charging) to 500mA (load)
            power = abs(voltage * current / 1000.0)
            
            return PowerState(
                battery_percent=self._calculate_battery_percent(voltage),
                voltage=voltage,
                current_ma=current,
                power_w=power,
                charging=current < 0
            )
        
        if not self.ina219:
            # Return default values if sensor not available
            return PowerState(
                battery_percent=50.0,
                voltage=3.7,
                current_ma=100.0,
                power_w=0.37,
                charging=False
            )
        
        try:
            voltage = self.ina219.getBusVoltage_V()
            current_ma = self.ina219.getCurrent_mA()
            power_w = self.ina219.getPower_W()
            
            # Determine charging status (negative current = charging)
            charging = current_ma < -10  # Allow some noise tolerance
            
            battery_pct = self._calculate_battery_percent(voltage)
            
            # Determine warning states
            low_battery = voltage < self.config.power['low_voltage']
            critical_battery = voltage < self.config.power['critical_voltage']
            
            power_state = PowerState(
                battery_percent=battery_pct,
                voltage=voltage,
                current_ma=current_ma,
                power_w=power_w,
                charging=charging,
                low_battery=low_battery,
                critical_battery=critical_battery
            )
            
            self._last_power_state = power_state
            return power_state
            
        except Exception as e:
            logger.error(f"Error reading power state: {e}")
            # Return last known state or defaults
            return self._last_power_state or PowerState(
                battery_percent=0.0,
                voltage=0.0,
                current_ma=0.0,
                power_w=0.0,
                charging=False,
                low_battery=True,
                critical_battery=True
            )
    
    def _calculate_battery_percent(self, voltage: float) -> float:
        """Calculate battery percentage from voltage using Li-ion curve."""
        # Li-ion voltage curve approximation
        if voltage >= 4.1:
            return 100.0
        elif voltage >= 3.9:
            return 75.0 + (voltage - 3.9) * 125.0  # 75-100%
        elif voltage >= 3.7:
            return 25.0 + (voltage - 3.7) * 250.0  # 25-75%
        elif voltage >= 3.4:
            return 5.0 + (voltage - 3.4) * 66.7   # 5-25%
        elif voltage >= 3.0:
            return (voltage - 3.0) * 12.5         # 0-5%
        else:
            return 0.0
    
    def get_power_policy(self, power_state: PowerState) -> PowerPolicy:
        """Determine power policy based on battery state."""
        display_config = self.config.display
        
        # Critical battery - prepare for shutdown
        if (power_state.battery_percent <= display_config['battery_shutdown_pct'] or 
            power_state.critical_battery):
            return PowerPolicy(
                fps=1,
                dim=True,
                static_mode=True,
                shutdown=True,
                brightness=0.1
            )
        
        # Very low battery - static mode
        if power_state.battery_percent <= display_config['battery_static_pct']:
            return PowerPolicy(
                fps=1,
                dim=True,
                static_mode=True,
                shutdown=False,
                brightness=0.2
            )
        
        # Low battery - dim and reduce frame rate
        if (power_state.battery_percent <= display_config['battery_dim_pct'] or
            power_state.low_battery):
            return PowerPolicy(
                fps=display_config['fps_idle'],
                dim=True,
                static_mode=False,
                shutdown=False,
                brightness=0.5
            )
        
        # Normal operation
        return PowerPolicy(
            fps=display_config['fps_active'],
            dim=False,
            static_mode=False,
            shutdown=False,
            brightness=1.0
        )
    
    def initiate_shutdown(self, delay_seconds: int = 60):
        """Initiate safe shutdown procedure."""
        if self._shutdown_initiated:
            return
        
        self._shutdown_initiated = True
        logger.critical(f"Critical battery level - initiating shutdown in {delay_seconds} seconds")
        
        try:
            # Show shutdown warning (this would be handled by display manager)
            logger.warning("Displaying shutdown warning to user")
            
            # Wait for the delay period
            time.sleep(delay_seconds)
            
            # Attempt graceful shutdown
            if not self.mock_mode:
                subprocess.run(['sudo', 'shutdown', '-h', 'now'], check=True)
            else:
                logger.info("Mock shutdown - system would halt now")
                
        except Exception as e:
            logger.error(f"Failed to initiate shutdown: {e}")
    
    def estimate_remaining_time(self, power_state: PowerState) -> float:
        """Estimate remaining battery time in hours."""
        if power_state.charging or power_state.current_ma <= 0:
            return float('inf')  # Charging or no load
        
        # Estimate based on current draw and battery capacity
        # Assuming ~2000mAh battery capacity (typical for Pi Zero setup)
        battery_capacity_mah = 2000
        remaining_capacity = battery_capacity_mah * (power_state.battery_percent / 100.0)
        
        if power_state.current_ma > 0:
            hours_remaining = remaining_capacity / power_state.current_ma
            return max(0.0, hours_remaining)
        
        return 0.0
    
    def optimize_power_consumption(self, power_state: PowerState) -> Dict[str, any]:
        """Suggest power optimization actions."""
        suggestions = {}
        
        if power_state.battery_percent < 30:
            suggestions.update({
                'reduce_brightness': True,
                'lower_fps': True,
                'disable_wifi_scan': True,
                'reduce_sensor_rate': True
            })
        
        if power_state.battery_percent < 15:
            suggestions.update({
                'minimal_display': True,
                'disable_social': True,
                'emergency_mode': True
            })
        
        return suggestions
    
    def get_charging_status(self, power_state: PowerState) -> Dict[str, any]:
        """Get detailed charging status information."""
        status = {
            'charging': power_state.charging,
            'battery_percent': power_state.battery_percent,
            'voltage': power_state.voltage,
            'current_ma': power_state.current_ma,
            'power_w': power_state.power_w,
            'estimated_time_remaining': self.estimate_remaining_time(power_state)
        }
        
        if power_state.charging:
            # Estimate time to full charge
            if power_state.current_ma < -10:  # Actually charging
                remaining_capacity = 2000 * (1.0 - power_state.battery_percent / 100.0)
                charge_rate = abs(power_state.current_ma)
                if charge_rate > 0:
                    status['time_to_full'] = remaining_capacity / charge_rate
                else:
                    status['time_to_full'] = float('inf')
            else:
                status['time_to_full'] = float('inf')
        
        return status
    
    def monitor_power_events(self, power_state: PowerState) -> List[Dict]:
        """Monitor and log power-related events."""
        events = []
        
        # Check for significant power state changes
        if self._last_power_state:
            # Battery level changes
            pct_change = power_state.battery_percent - self._last_power_state.battery_percent
            if abs(pct_change) > 5.0:  # 5% change
                events.append({
                    'type': 'battery_level_change',
                    'old_percent': self._last_power_state.battery_percent,
                    'new_percent': power_state.battery_percent,
                    'change': pct_change
                })
            
            # Charging status changes
            if power_state.charging != self._last_power_state.charging:
                events.append({
                    'type': 'charging_status_change',
                    'charging': power_state.charging,
                    'voltage': power_state.voltage
                })
            
            # Low battery warnings
            if (not self._last_power_state.low_battery and power_state.low_battery):
                events.append({
                    'type': 'low_battery_warning',
                    'battery_percent': power_state.battery_percent,
                    'voltage': power_state.voltage
                })
            
            # Critical battery warnings
            if (not self._last_power_state.critical_battery and power_state.critical_battery):
                events.append({
                    'type': 'critical_battery_warning',
                    'battery_percent': power_state.battery_percent,
                    'voltage': power_state.voltage
                })
        
        return events


class MockPowerManager(PowerManager):
    """Mock power manager for testing without hardware."""
    
    def __init__(self):
        """Initialize mock power manager."""
        super().__init__(mock_mode=True)
        self._mock_battery = 75.0  # Start with 75% battery
        self._mock_charging = False
        
    def read_power_state(self) -> PowerState:
        """Generate mock power state for testing."""
        import random
        
        # Simulate battery drain or charging
        if self._mock_charging:
            self._mock_battery += random.uniform(0.1, 0.5)  # Charge
            if self._mock_battery >= 95:
                self._mock_charging = False
        else:
            self._mock_battery -= random.uniform(0.05, 0.2)  # Drain
            if self._mock_battery <= 10:
                self._mock_charging = True
        
        self._mock_battery = max(0.0, min(100.0, self._mock_battery))
        
        # Convert to voltage
        if self._mock_battery > 75:
            voltage = 3.9 + (self._mock_battery - 75) * 0.008
        else:
            voltage = 3.4 + (self._mock_battery / 75) * 0.5
        
        current = -200 if self._mock_charging else random.uniform(100, 400)
        power = abs(voltage * current / 1000.0)
        
        return PowerState(
            battery_percent=self._mock_battery,
            voltage=voltage,
            current_ma=current,
            power_w=power,
            charging=self._mock_charging,
            low_battery=self._mock_battery < 20,
            critical_battery=self._mock_battery < 5
        )