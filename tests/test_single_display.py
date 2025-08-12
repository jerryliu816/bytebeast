#!/usr/bin/env python3
"""
Test single 1.3" display using same config as test5.py
"""

import sys
import time
from pathlib import Path

# Add project paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent / 'display' / 'lib'))

from display.lib.LCD_1inch3 import LCD_1inch3
import spidev
from PIL import Image, ImageDraw, ImageFont

def test_single_display():
    """Test single 1.3" display with same config as test5.py"""
    
    try:
        print("Initializing single 1.3\" display...")
        
        # Use exact same config as test5.py
        spi_main = spidev.SpiDev(1, 0)  # SPI1 CE0
        display = LCD_1inch3(
            spi=spi_main,
            rst=27,   # Same as test5.py
            dc=22,    # Same as test5.py  
            bl=19     # Same as test5.py
        )
        
        # Initialize display
        display.Init()
        print("✅ Display initialized")
        
        # Test 1: Red background
        print("Test 1: Red background")
        red_canvas = Image.new('RGB', (240, 240), (255, 0, 0))
        display.ShowImage(red_canvas)
        time.sleep(2)
        
        # Test 2: Green background  
        print("Test 2: Green background")
        green_canvas = Image.new('RGB', (240, 240), (0, 255, 0))
        display.ShowImage(green_canvas)
        time.sleep(2)
        
        # Test 3: Blue background
        print("Test 3: Blue background")
        blue_canvas = Image.new('RGB', (240, 240), (0, 0, 255))
        display.ShowImage(blue_canvas)
        time.sleep(2)
        
        # Test 4: Text
        print("Test 4: Text")
        text_canvas = Image.new('RGB', (240, 240), (0, 0, 0))
        draw = ImageDraw.Draw(text_canvas)
        draw.text((60, 100), "ByteBeast!", fill=(255, 255, 255))
        display.ShowImage(text_canvas)
        time.sleep(2)
        
        # Test 5: Emoji
        print("Test 5: Emoji")
        emoji_canvas = Image.new('RGB', (240, 240), (0, 0, 0))
        draw = ImageDraw.Draw(emoji_canvas)
        draw.text((100, 100), "😊", fill=(255, 255, 255))
        display.ShowImage(emoji_canvas)
        time.sleep(2)
        
        # Clear
        black_canvas = Image.new('RGB', (240, 240), (0, 0, 0))
        display.ShowImage(black_canvas)
        
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_single_display()