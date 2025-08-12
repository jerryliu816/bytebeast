#!/usr/bin/env python3
"""
ByteBeast Demo Script

Demonstrates the ByteBeast virtual pet system in action.
"""

import time
import sys
from pathlib import Path

# Add bytebeast to path
sys.path.insert(0, str(Path(__file__).parent))

from sensors.manager import MockSensorManager  
from state.mood_engine import MoodEngine, create_default_beast
from display.manager import get_display_manager
from power.manager import MockPowerManager
from core.database import get_database


def main():
    """Run ByteBeast demo."""
    print("🐾 ByteBeast Virtual Pet Demo 🐾")
    print("================================")
    print()
    
    # Initialize components
    print("Initializing ByteBeast components...")
    sensor_manager = MockSensorManager()
    mood_engine = MoodEngine() 
    display_manager = get_display_manager()  # Will use real or mock based on hardware
    power_manager = MockPowerManager()
    db = get_database()
    
    # Create a new ByteBeast
    beast = create_default_beast()
    print(f"✨ Created new ByteBeast!")
    print(f"   Mood: {beast.mood}")
    print(f"   Evolution: {beast.evolution_path} (stage {beast.evolution_stage})")
    print(f"   Energy: {beast.energy:.0f}%")
    print()
    
    # Demo loop
    print("Running demo (Ctrl+C to stop)...")
    print()
    
    try:
        cycle = 0
        while True:
            cycle += 1
            print(f"--- Cycle {cycle} ---")
            
            # 1. Read sensors
            features = sensor_manager.read_all_sensors()
            print(f"🌡️  Environment: {features.temp_c:.1f}°C, {features.lux:.0f} lux, {features.rh:.0f}%RH")
            
            # 2. Update beast state  
            old_mood = beast.mood
            beast.mood = mood_engine.infer_mood(features, beast)
            beast = mood_engine.update_needs(beast, features)
            beast = mood_engine.tick_traits(features, beast)
            beast = mood_engine.update_evolution(features, beast)
            
            # 3. Show mood changes
            if beast.mood != old_mood:
                print(f"😊 Mood changed: {old_mood} → {beast.mood}")
            
            # 4. Display status
            avg_needs = sum(beast.needs.values()) / len(beast.needs)
            print(f"🎭 Status: {beast.mood} mood, {avg_needs:.0f}% avg needs, {beast.energy:.0f}% energy")
            
            # 5. Power status
            power_state = power_manager.read_power_state()
            print(f"🔋 Power: {power_state.battery_percent:.0f}% battery, {power_state.power_w:.2f}W")
            
            # 6. Generate tasks occasionally
            if cycle % 5 == 0:
                tasks = mood_engine.generate_tasks(beast, features)
                if tasks:
                    print(f"📋 Tasks: {tasks[0]['description']}")
            
            # 7. Update display
            emoji_frame = display_manager.create_emoji_frame(beast, features)
            display_manager.update_display(emoji_frame, features)
            
            # 8. Save data
            db.save_sensor_data(features)
            db.save_beast_state(beast)
            
            print()
            time.sleep(3)  # Wait 3 seconds between cycles
            
    except KeyboardInterrupt:
        print("\n👋 Demo stopped by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
    
    # Final status
    print(f"\n🏁 Final ByteBeast Status:")
    print(f"   Mood: {beast.mood}")
    print(f"   Evolution: {beast.evolution_path} stage {beast.evolution_stage}")  
    print(f"   Progression: {beast.evolution_prog:.0%}")
    print(f"   Needs: " + ", ".join(f"{k}: {v:.0f}%" for k, v in beast.needs.items()))
    print(f"   Traits: " + ", ".join(f"{k}: {v:.2f}" for k, v in beast.traits.items()))
    print()
    print("Thanks for playing with ByteBeast! 🐾")


if __name__ == '__main__':
    main()