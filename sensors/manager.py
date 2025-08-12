"""
Sensor manager that integrates existing hardware drivers for ByteBeast.
"""

import sys
import time
import logging
import hashlib
import subprocess
from typing import Optional, List, Dict
from pathlib import Path

# Add existing sensor modules to path
sys.path.append('/home/jerry/dev/bytebeast')
sys.path.append('/home/jerry/dev/bytebeast/Sense_HAT_C_Pi/RaspberryPi/IMU/python')
sys.path.append('/home/jerry/dev/bytebeast/Sense_HAT_C_Pi/RaspberryPi/SHTC3/python')
sys.path.append('/home/jerry/dev/bytebeast/Sense_HAT_C_Pi/RaspberryPi/LPS22HBTR/python')
sys.path.append('/home/jerry/dev/bytebeast/Sense_HAT_C_Pi/RaspberryPi/TCS34087/python')

from core.models import EnvFeatures
from core.config import get_config

logger = logging.getLogger(__name__)


class SensorManager:
    """Manages all hardware sensors and feature extraction."""
    
    def __init__(self):
        """Initialize sensor manager."""
        self.config = get_config()
        self._init_sensors()
        self._motion_history = []
        self._pressure_history = []
        
    def _init_sensors(self):
        """Initialize hardware sensors."""
        try:
            # BME280 for temp/humidity/pressure
            from environment.BME280 import BME280
            self.bme280 = BME280()
            self.bme280.get_calib_param()
            logger.info("Initialized BME280 sensor")
        except Exception as e:
            logger.error(f"Failed to initialize BME280: {e}")
            self.bme280 = None
            
        try:
            # INA219 for power monitoring
            from UPS_HAT_C.INA219 import INA219
            self.ina219 = INA219(addr=0x43)
            logger.info("Initialized INA219 power sensor")
        except Exception as e:
            logger.error(f"Failed to initialize INA219: {e}")
            self.ina219 = None
            
        try:
            # IMU sensors
            import IMU
            self.imu = IMU
            logger.info("Initialized IMU sensors")
        except Exception as e:
            logger.error(f"Failed to initialize IMU: {e}")
            self.imu = None
            
        try:
            # SHTC3 temperature/humidity (alternative to BME280)
            import SHTC3
            self.shtc3 = SHTC3
            logger.info("Initialized SHTC3 sensor")
        except Exception as e:
            logger.error(f"Failed to initialize SHTC3: {e}")
            self.shtc3 = None
            
        try:
            # LPS22HB pressure sensor
            import LPS22HB
            self.lps22hb = LPS22HB
            logger.info("Initialized LPS22HB pressure sensor")
        except Exception as e:
            logger.error(f"Failed to initialize LPS22HB: {e}")
            self.lps22hb = None
            
        try:
            # TCS34087 color/light sensor
            import TCS34087
            self.tcs34087 = TCS34087
            logger.info("Initialized TCS34087 light sensor")
        except Exception as e:
            logger.error(f"Failed to initialize TCS34087: {e}")
            self.tcs34087 = None
    
    def read_environmental_data(self) -> Dict:
        """Read temperature, humidity, pressure from available sensors."""
        env_data = {
            'temp_c': 20.0,      # Default values
            'rh': 50.0,
            'pressure_hpa': 1013.25
        }
        
        # Try BME280 first
        if self.bme280:
            try:
                bme_data = self.bme280.readData()
                if bme_data and len(bme_data) >= 3:
                    env_data.update({
                        'pressure_hpa': bme_data[0],
                        'temp_c': bme_data[1],
                        'rh': bme_data[2]
                    })
                    return env_data
            except Exception as e:
                logger.error(f"BME280 read error: {e}")
        
        # Fallback to individual sensors
        if self.shtc3:
            try:
                # SHTC3 would need to be properly initialized and read
                # This is a placeholder for the actual implementation
                pass
            except Exception as e:
                logger.error(f"SHTC3 read error: {e}")
                
        if self.lps22hb:
            try:
                # LPS22HB pressure reading - placeholder
                pass
            except Exception as e:
                logger.error(f"LPS22HB read error: {e}")
        
        return env_data
    
    def read_light_data(self) -> Dict:
        """Read light sensor data and calculate lux, color temperature."""
        light_data = {
            'lux': 500.0,       # Default moderate light
            'cct_k': 5000.0     # Default daylight color temp
        }
        
        if self.tcs34087:
            try:
                # TCS34087 RGB + clear light sensor reading
                # This would need proper implementation based on the sensor API
                # For now, return defaults
                pass
            except Exception as e:
                logger.error(f"TCS34087 read error: {e}")
        
        return light_data
    
    def read_imu_data(self) -> Dict:
        """Read IMU data and calculate motion features."""
        imu_data = {
            'roll': 0.0,
            'pitch': 0.0, 
            'yaw': 0.0,
            'heading_deg': 0.0,
            'motion_rms_g': 0.0,
            'shake_events': 0
        }
        
        if self.imu:
            try:
                # Read accelerometer and gyroscope data
                # This would need proper implementation based on IMU API
                # For now, simulate some basic motion detection
                
                # Calculate motion RMS from acceleration
                # This is a simplified placeholder
                motion_rms = 0.1  # Placeholder value
                self._motion_history.append(motion_rms)
                
                # Keep only recent motion data
                if len(self._motion_history) > 60:  # 1 minute at 1Hz
                    self._motion_history.pop(0)
                
                # Calculate shake events (motion spikes)
                shake_count = sum(1 for m in self._motion_history if m > self.config.get('thresholds.motion_shake_g', 1.0))
                
                imu_data.update({
                    'motion_rms_g': motion_rms,
                    'shake_events': shake_count
                })
                
            except Exception as e:
                logger.error(f"IMU read error: {e}")
        
        return imu_data
    
    def read_power_data(self) -> Dict:
        """Read power/battery data from INA219."""
        power_data = {
            'vbat': 4.2,        # Default full battery voltage
            'ibat': 0.0,        # Default no current draw
            'pwr_w': 0.0,       # Default no power consumption
            'charging': False
        }
        
        if self.ina219:
            try:
                voltage = self.ina219.getBusVoltage_V()
                current = self.ina219.getCurrent_mA()
                power = self.ina219.getPower_W()
                
                power_data.update({
                    'vbat': voltage,
                    'ibat': current,
                    'pwr_w': power,
                    'charging': current < 0  # Negative current indicates charging
                })
                
            except Exception as e:
                logger.error(f"INA219 read error: {e}")
        
        return power_data
    
    def get_wifi_fingerprint(self) -> str:
        """Get WiFi fingerprint for location/peer detection."""
        try:
            # Scan for nearby WiFi networks
            result = subprocess.run(
                ['iwlist', 'wlan0', 'scan'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if result.returncode == 0:
                # Extract SSID and BSSID information
                lines = result.stdout.split('\n')
                networks = []
                
                for line in lines:
                    line = line.strip()
                    if 'ESSID:' in line:
                        ssid = line.split('ESSID:')[1].strip('"')
                        if ssid and ssid != '':
                            networks.append(ssid)
                    elif 'Address:' in line:
                        bssid = line.split('Address: ')[1].strip()
                        networks.append(bssid)
                
                # Create hash of nearby networks for location fingerprinting
                if networks:
                    fingerprint_data = '|'.join(sorted(networks))
                    return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]
                    
        except Exception as e:
            logger.error(f"WiFi scan error: {e}")
        
        return "no_wifi"
    
    def calculate_pressure_trend(self, current_pressure: float) -> float:
        """Calculate pressure trend from history."""
        self._pressure_history.append(current_pressure)
        
        # Keep last hour of data (assuming 1Hz sampling)
        if len(self._pressure_history) > 3600:
            self._pressure_history.pop(0)
        
        if len(self._pressure_history) < 2:
            return 0.0
        
        # Simple linear trend calculation
        recent = self._pressure_history[-300:]  # Last 5 minutes
        if len(recent) < 2:
            return 0.0
            
        trend = (recent[-1] - recent[0]) / (len(recent) / 60.0)  # hPa per hour
        return trend
    
    def read_all_sensors(self) -> EnvFeatures:
        """Read all sensors and return consolidated features."""
        # Read all sensor data
        env_data = self.read_environmental_data()
        light_data = self.read_light_data()
        imu_data = self.read_imu_data()
        power_data = self.read_power_data()
        
        # Calculate derived features
        pressure_trend = self.calculate_pressure_trend(env_data['pressure_hpa'])
        wifi_fingerprint = self.get_wifi_fingerprint()
        
        # Create consolidated feature object
        features = EnvFeatures(
            lux=light_data['lux'],
            cct_k=light_data['cct_k'],
            temp_c=env_data['temp_c'],
            rh=env_data['rh'],
            pressure_hpa=env_data['pressure_hpa'],
            pressure_trend=pressure_trend,
            motion_rms_g=imu_data['motion_rms_g'],
            shake_events=imu_data['shake_events'],
            heading_deg=imu_data['heading_deg'],
            roll=imu_data['roll'],
            pitch=imu_data['pitch'],
            yaw=imu_data['yaw'],
            vbat=power_data['vbat'],
            ibat=power_data['ibat'],
            pwr_w=power_data['pwr_w'],
            charging=power_data['charging'],
            ssid_fingerprint=wifi_fingerprint,
            timestamp=time.time()
        )
        
        return features


class MockSensorManager(SensorManager):
    """Mock sensor manager for testing without hardware."""
    
    def __init__(self):
        """Initialize mock sensor manager."""
        self.config = get_config()
        self._time_offset = 0
        logger.info("Initialized mock sensor manager")
    
    def read_all_sensors(self) -> EnvFeatures:
        """Generate mock sensor data for testing."""
        import random
        import math
        
        # Simulate day/night cycle
        hour_of_day = (time.time() + self._time_offset) % 86400 / 3600
        
        # Light levels based on time of day
        if 6 <= hour_of_day <= 18:  # Daytime
            lux = 2000 + random.uniform(-500, 3000)
            cct_k = 5500 + random.uniform(-500, 500)
        else:  # Nighttime
            lux = 10 + random.uniform(0, 100)
            cct_k = 3000 + random.uniform(-200, 200)
        
        # Temperature with daily variation
        base_temp = 22 + 5 * math.sin((hour_of_day - 12) * math.pi / 12)
        temp_c = base_temp + random.uniform(-2, 2)
        
        return EnvFeatures(
            lux=max(0, lux),
            cct_k=max(2000, cct_k),
            temp_c=temp_c,
            rh=45 + random.uniform(-10, 15),
            pressure_hpa=1013 + random.uniform(-5, 5),
            pressure_trend=random.uniform(-2, 2),
            motion_rms_g=random.uniform(0, 0.5),
            shake_events=random.randint(0, 3),
            heading_deg=random.uniform(0, 360),
            roll=random.uniform(-5, 5),
            pitch=random.uniform(-5, 5),
            yaw=random.uniform(-5, 5),
            vbat=4.2 - random.uniform(0, 1.2),
            ibat=random.uniform(-100, 500),
            pwr_w=random.uniform(0.5, 2.0),
            charging=random.choice([True, False]),
            ssid_fingerprint=f"mock_{random.randint(1000, 9999)}",
            timestamp=time.time()
        )