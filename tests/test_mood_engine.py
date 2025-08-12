#!/usr/bin/env python3
"""
Test suite for ByteBeast mood inference engine.
"""

import unittest
import sys
from pathlib import Path

# Add bytebeast to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.models import EnvFeatures, Beast
from state.mood_engine import MoodEngine, create_default_beast


class TestMoodEngine(unittest.TestCase):
    """Test mood inference engine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = MoodEngine()
        self.beast = create_default_beast()
    
    def test_hot_mood_rule(self):
        """Test hot temperature rule has priority."""
        env = EnvFeatures(
            temp_c=35.0,  # Above hot threshold (30°C)
            lux=5000.0,   # Bright light  
            rh=50.0,
            pressure_hpa=1013.0,
            pressure_trend=0.0,
            motion_rms_g=0.1,
            shake_events=0,
            heading_deg=180.0,
            roll=0.0, pitch=0.0, yaw=0.0,
            vbat=4.0, ibat=100.0, pwr_w=0.4,
            charging=False,
            ssid_fingerprint="test",
            timestamp=0
        )
        
        mood = self.engine.infer_mood(env, self.beast)
        self.assertEqual(mood, 'hot', "Hot temperature should trigger hot mood")
    
    def test_cold_mood_rule(self):
        """Test cold temperature rule has priority."""
        env = EnvFeatures(
            temp_c=5.0,   # Below cold threshold (10°C)
            lux=5000.0,   # Bright light (would normally be happy)
            rh=50.0,
            pressure_hpa=1013.0,
            pressure_trend=0.0,
            motion_rms_g=0.1,
            shake_events=0,
            heading_deg=180.0,
            roll=0.0, pitch=0.0, yaw=0.0,
            vbat=4.0, ibat=100.0, pwr_w=0.4,
            charging=False,
            ssid_fingerprint="test",
            timestamp=0
        )
        
        mood = self.engine.infer_mood(env, self.beast)
        self.assertEqual(mood, 'cold', "Cold temperature should trigger cold mood")
    
    def test_sick_mood_low_battery(self):
        """Test sick mood from low battery."""
        env = EnvFeatures(
            temp_c=20.0,  # Normal temperature
            lux=1000.0,   # Normal light
            rh=50.0,
            pressure_hpa=1013.0,
            pressure_trend=0.0,
            motion_rms_g=0.1,
            shake_events=0,
            heading_deg=180.0,
            roll=0.0, pitch=0.0, yaw=0.0,
            vbat=3.2,     # Low battery voltage
            ibat=100.0, pwr_w=0.32,
            charging=False,
            ssid_fingerprint="test",
            timestamp=0
        )
        
        mood = self.engine.infer_mood(env, self.beast)
        self.assertEqual(mood, 'sick', "Low battery should trigger sick mood")
    
    def test_playful_mood_shake(self):
        """Test playful mood from shake events.""" 
        env = EnvFeatures(
            temp_c=20.0,
            lux=1000.0,
            rh=50.0,
            pressure_hpa=1013.0,
            pressure_trend=0.0,
            motion_rms_g=0.3,  # High motion
            shake_events=2,    # Shake events
            heading_deg=180.0,
            roll=0.0, pitch=0.0, yaw=0.0,
            vbat=4.0, ibat=100.0, pwr_w=0.4,
            charging=False,
            ssid_fingerprint="test",
            timestamp=0
        )
        
        mood = self.engine.infer_mood(env, self.beast)
        self.assertEqual(mood, 'playful', "Shake events should trigger playful mood")
    
    def test_happy_mood_bright_comfortable(self):
        """Test happy mood from bright, comfortable conditions."""
        self.beast.energy = 80.0  # High energy
        
        env = EnvFeatures(
            temp_c=22.0,    # Comfortable temperature
            lux=10000.0,    # Bright light (above threshold)
            rh=50.0,
            pressure_hpa=1013.0,
            pressure_trend=0.0,
            motion_rms_g=0.05,  # Low motion
            shake_events=0,
            heading_deg=180.0,
            roll=0.0, pitch=0.0, yaw=0.0,
            vbat=4.0, ibat=100.0, pwr_w=0.4,
            charging=False,
            ssid_fingerprint="test",
            timestamp=0
        )
        
        mood = self.engine.infer_mood(env, self.beast)
        self.assertEqual(mood, 'happy', "Bright comfortable conditions should trigger happy mood")
    
    def test_calm_fallback(self):
        """Test calm mood as fallback."""
        env = EnvFeatures(
            temp_c=20.0,    # Normal temperature
            lux=1000.0,     # Normal light
            rh=50.0,
            pressure_hpa=1013.0,
            pressure_trend=0.0,
            motion_rms_g=0.1,   # Normal motion
            shake_events=0,
            heading_deg=180.0,
            roll=0.0, pitch=0.0, yaw=0.0,
            vbat=4.0, ibat=100.0, pwr_w=0.4,
            charging=False,
            ssid_fingerprint="test",
            timestamp=0
        )
        
        mood = self.engine.infer_mood(env, self.beast)
        self.assertEqual(mood, 'calm', "Normal conditions should default to calm mood")
    
    def test_needs_drift(self):
        """Test that needs drift over time."""
        original_hunger = self.beast.needs['hunger']
        
        # Simulate time passage
        import time
        self.beast.last_updated = time.time() - 3600  # 1 hour ago
        
        env = EnvFeatures(
            temp_c=20.0, lux=1000.0, rh=50.0, pressure_hpa=1013.0,
            pressure_trend=0.0, motion_rms_g=0.1, shake_events=0,
            heading_deg=180.0, roll=0.0, pitch=0.0, yaw=0.0,
            vbat=4.0, ibat=100.0, pwr_w=0.4, charging=False,
            ssid_fingerprint="test", timestamp=0
        )
        
        updated_beast = self.engine.update_needs(self.beast, env)
        
        # Hunger should have increased (need decreased)
        self.assertLess(updated_beast.needs['hunger'], original_hunger,
                       "Hunger need should drift down over time")
    
    def test_trait_learning(self):
        """Test that traits change based on actions."""
        original_playful = self.beast.traits['playful']
        
        env = EnvFeatures(
            temp_c=20.0, lux=1000.0, rh=50.0, pressure_hpa=1013.0,
            pressure_trend=0.0, motion_rms_g=0.5, shake_events=1,  # Active
            heading_deg=180.0, roll=0.0, pitch=0.0, yaw=0.0,
            vbat=4.0, ibat=100.0, pwr_w=0.4, charging=False,
            ssid_fingerprint="test", timestamp=0
        )
        
        actions = {'play': True}
        updated_beast = self.engine.tick_traits(env, self.beast, actions)
        
        # Playful trait should increase
        self.assertGreater(updated_beast.traits['playful'], original_playful,
                          "Playful trait should increase with play actions")
    
    def test_evolution_progression(self):
        """Test evolution progression."""
        original_prog = self.beast.evolution_prog
        
        env = EnvFeatures(
            temp_c=25.0,    # Warm
            lux=8000.0,     # Bright  
            rh=50.0,
            pressure_hpa=1013.0,
            pressure_trend=0.0,
            motion_rms_g=0.3,   # Active (sun path conditions)
            shake_events=0,
            heading_deg=180.0,
            roll=0.0, pitch=0.0, yaw=0.0,
            vbat=4.0, ibat=100.0, pwr_w=0.4,
            charging=False,
            ssid_fingerprint="test",
            timestamp=0
        )
        
        updated_beast = self.engine.update_evolution(env, self.beast)
        
        # Evolution progress should increase
        self.assertGreaterEqual(updated_beast.evolution_prog, original_prog,
                               "Evolution progress should increase")
    
    def test_task_generation_low_needs(self):
        """Test task generation for low needs.""" 
        self.beast.needs['hunger'] = 20.0  # Low hunger
        
        env = EnvFeatures(
            temp_c=20.0, lux=1000.0, rh=50.0, pressure_hpa=1013.0,
            pressure_trend=0.0, motion_rms_g=0.1, shake_events=0,
            heading_deg=180.0, roll=0.0, pitch=0.0, yaw=0.0,
            vbat=4.0, ibat=100.0, pwr_w=0.4, charging=False,
            ssid_fingerprint="test", timestamp=0
        )
        
        tasks = self.engine.generate_tasks(self.beast, env)
        
        # Should generate feeding task
        task_actions = [task['action'] for task in tasks]
        self.assertIn('feed', task_actions, "Should generate feeding task for low hunger")


if __name__ == '__main__':
    unittest.main()