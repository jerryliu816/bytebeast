#!/usr/bin/env python3
"""
Integration tests for ByteBeast system.
"""

import unittest
import tempfile
import sys
from pathlib import Path

# Add bytebeast to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sensors.manager import MockSensorManager
from state.mood_engine import MoodEngine, create_default_beast
from display.manager import MockDisplayManager
from power.manager import MockPowerManager
from core.database import ByteBeastDB
from core.config import Config


class TestIntegration(unittest.TestCase):
    """Integration tests for ByteBeast components."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Use temporary database
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db = ByteBeastDB(self.temp_db.name)
        
        # Initialize components in mock mode
        self.sensor_manager = MockSensorManager()
        self.mood_engine = MoodEngine()
        self.display_manager = MockDisplayManager()
        self.power_manager = MockPowerManager()
        
        # Create test beast
        self.beast = create_default_beast()
    
    def test_sensor_to_database_flow(self):
        """Test sensor data flows to database correctly."""
        # Read sensor data
        features = self.sensor_manager.read_all_sensors()
        
        # Save to database
        self.db.save_sensor_data(features)
        
        # Retrieve recent data
        recent_data = self.db.get_recent_sensor_data(hours=1)
        
        self.assertTrue(len(recent_data) > 0, "Should have sensor data in database")
        self.assertEqual(recent_data[0].temp_c, features.temp_c, 
                        "Temperature should match")
    
    def test_state_engine_processing(self):
        """Test state engine processes sensor data correctly.""" 
        # Generate sensor data
        features = self.sensor_manager.read_all_sensors()
        
        # Process through state engine
        original_mood = self.beast.mood
        new_mood = self.mood_engine.infer_mood(features, self.beast)
        
        # Update beast state
        self.beast.mood = new_mood
        updated_beast = self.mood_engine.update_needs(self.beast, features)
        updated_beast = self.mood_engine.tick_traits(features, updated_beast)
        updated_beast = self.mood_engine.update_evolution(features, updated_beast)
        
        # Verify state was updated
        self.assertIsNotNone(updated_beast.mood, "Beast should have a mood")
        self.assertTrue(all(0 <= need <= 100 for need in updated_beast.needs.values()),
                       "Needs should be in valid range")
        self.assertTrue(all(0 <= trait <= 1 for trait in updated_beast.traits.values()),
                       "Traits should be in valid range")
    
    def test_display_rendering(self):
        """Test display system renders correctly."""
        # Generate test data
        features = self.sensor_manager.read_all_sensors()
        
        # Create emoji frame
        emoji_frame = self.display_manager.create_emoji_frame(self.beast, features)
        
        # Verify frame has required elements
        self.assertIsNotNone(emoji_frame.emoji, "Frame should have main emoji")
        self.assertIsInstance(emoji_frame.badges, list, "Badges should be a list")
        self.assertLessEqual(len(emoji_frame.badges), 3, "Should have max 3 badges")
        
        # Test display update (mock mode)
        try:
            self.display_manager.update_display(emoji_frame, features, uptime=100.0)
        except Exception as e:
            self.fail(f"Display update failed: {e}")
    
    def test_power_management(self):
        """Test power management system."""
        # Read power state
        power_state = self.power_manager.read_power_state()
        
        # Verify power state is valid
        self.assertGreaterEqual(power_state.battery_percent, 0.0)
        self.assertLessEqual(power_state.battery_percent, 100.0)
        self.assertGreater(power_state.voltage, 0.0)
        
        # Test power policy
        policy = self.power_manager.get_power_policy(power_state)
        
        self.assertIsNotNone(policy.fps, "Policy should have FPS setting")
        self.assertIsInstance(policy.dim, bool, "Policy dim should be boolean")
        self.assertIsInstance(policy.static_mode, bool, "Policy static_mode should be boolean")
    
    def test_full_system_cycle(self):
        """Test a full system processing cycle."""
        # 1. Sensor reading
        features = self.sensor_manager.read_all_sensors()
        self.db.save_sensor_data(features)
        
        # 2. State processing
        self.beast.mood = self.mood_engine.infer_mood(features, self.beast)
        self.beast = self.mood_engine.update_needs(self.beast, features)
        self.beast = self.mood_engine.tick_traits(features, self.beast)
        self.beast = self.mood_engine.update_evolution(features, self.beast)
        self.db.save_beast_state(self.beast)
        
        # 3. Power management
        power_state = self.power_manager.read_power_state()
        policy = self.power_manager.get_power_policy(power_state)
        
        # 4. Display update
        emoji_frame = self.display_manager.create_emoji_frame(self.beast, features)
        self.display_manager.update_display(emoji_frame, features)
        
        # 5. Verify system state is consistent
        saved_beast = self.db.load_latest_beast_state()
        self.assertEqual(saved_beast.mood, self.beast.mood, 
                        "Saved beast mood should match current")
        
        recent_data = self.db.get_recent_sensor_data(hours=1)
        self.assertTrue(len(recent_data) > 0, "Should have recent sensor data")
    
    def test_database_persistence(self):
        """Test database persistence and retrieval."""
        # Save test data
        features = self.sensor_manager.read_all_sensors()
        self.db.save_sensor_data(features)
        self.db.save_beast_state(self.beast)
        
        # Log test event
        self.db.log_event('test_event', {'value': 42})
        
        # Retrieve and verify
        recent_sensors = self.db.get_recent_sensor_data(hours=1)
        self.assertTrue(len(recent_sensors) > 0)
        
        saved_beast = self.db.load_latest_beast_state()
        self.assertEqual(saved_beast.mood, self.beast.mood)
        
        events = self.db.get_events(event_type='test_event', hours=1)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['payload']['value'], 42)
    
    def test_configuration_system(self):
        """Test configuration system.""" 
        config = Config()
        
        # Test default values
        fps = config.get('display.fps_active')
        self.assertIsNotNone(fps, "Should have default FPS setting")
        
        temp_hot = config.get('thresholds.temp_hot')
        self.assertEqual(temp_hot, 30.0, "Should have correct hot temperature threshold")
        
        # Test section access
        display_config = config.display
        self.assertIn('fps_active', display_config, "Display config should have fps_active")
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Close and remove temporary database
        import os
        self.temp_db.close()
        os.unlink(self.temp_db.name)


class TestSystemBehavior(unittest.TestCase):
    """Test system behavior scenarios."""
    
    def setUp(self):
        """Set up test scenario."""
        self.sensor_manager = MockSensorManager()
        self.mood_engine = MoodEngine()
        self.beast = create_default_beast()
    
    def test_hot_environment_scenario(self):
        """Test system behavior in hot environment."""
        # Override mock to return hot conditions
        def mock_hot_sensors():
            features = self.sensor_manager.read_all_sensors()
            features.temp_c = 35.0  # Hot temperature
            features.lux = 8000.0   # Bright light
            return features
        
        features = mock_hot_sensors()
        mood = self.mood_engine.infer_mood(features, self.beast)
        
        self.assertEqual(mood, 'hot', "Should be hot mood in hot environment")
    
    def test_low_battery_scenario(self):
        """Test system behavior with low battery."""
        # Create low battery power state
        from core.models import PowerState
        
        power_state = PowerState(
            battery_percent=15.0,
            voltage=3.3,
            current_ma=200.0,
            power_w=0.66,
            charging=False,
            low_battery=True,
            critical_battery=False
        )
        
        power_manager = MockPowerManager()
        policy = power_manager.get_power_policy(power_state)
        
        # Should trigger power-saving measures
        self.assertTrue(policy.dim, "Should dim display on low battery")
        self.assertLess(policy.fps, 10, "Should reduce FPS on low battery")
    
    def test_evolution_progression_scenario(self):
        """Test evolution progression over time.""" 
        # Simulate sun path conditions repeatedly
        for _ in range(10):
            features = self.sensor_manager.read_all_sensors()
            features.temp_c = 25.0    # Warm
            features.lux = 8000.0     # Bright
            features.motion_rms_g = 0.3  # Active
            
            self.beast = self.mood_engine.update_evolution(features, self.beast)
        
        # Evolution progress should have increased
        self.assertGreater(self.beast.evolution_prog, 0.0,
                          "Evolution should progress with consistent conditions")


if __name__ == '__main__':
    unittest.main()