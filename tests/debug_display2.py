#!/usr/bin/env python3
"""
Debug display - test our DisplayManager approach
"""

import sys
import time
from pathlib import Path

# Add project paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.append("display/lib")

import spidev
from display.lib.LCD_1inch3 import LCD_1inch3
from PIL import Image, ImageDraw

def test_custom_spi():
    print("Testing with custom SPI configuration...")
    
    try:
        # Our DisplayManager approach
        spi_main = spidev.SpiDev(1, 0)
        display = LCD_1inch3(
            spi=spi_main,
            rst=27,
            dc=22,
            bl=19
        )
        
        print("Initializing display...")
        display.Init()
        
        print("Showing red background...")
        red_canvas = Image.new('RGB', (240, 240), (255, 0, 0))
        display.ShowImage(red_canvas)
        
        time.sleep(3)
        
        print("Showing text...")
        text_canvas = Image.new('RGB', (240, 240), (0, 0, 0))
        draw = ImageDraw.Draw(text_canvas)
        draw.text((60, 100), "Custom SPI", fill=(255, 255, 255))
        display.ShowImage(text_canvas)
        
        time.sleep(3)
        
        # Clear
        black_canvas = Image.new('RGB', (240, 240), (0, 0, 0))
        display.ShowImage(black_canvas)
        
        print("✅ Custom SPI test completed!")
        
    except Exception as e:
        print(f"❌ Custom SPI failed: {e}")
        import traceback
        traceback.print_exc()

def test_default_spi():
    print("\nTesting with default SPI configuration...")
    
    try:
        # Default approach like test5.py
        display = LCD_1inch3()
        
        print("Initializing display...")
        display.Init()
        
        print("Showing blue background...")
        blue_canvas = Image.new('RGB', (240, 240), (0, 0, 255))
        display.ShowImage(blue_canvas)
        
        time.sleep(3)
        
        print("Showing text...")
        text_canvas = Image.new('RGB', (240, 240), (0, 0, 0))
        draw = ImageDraw.Draw(text_canvas)
        draw.text((60, 100), "Default SPI", fill=(255, 255, 255))
        display.ShowImage(text_canvas)
        
        time.sleep(3)
        
        # Clear
        black_canvas = Image.new('RGB', (240, 240), (0, 0, 0))
        display.ShowImage(black_canvas)
        
        print("✅ Default SPI test completed!")
        
    except Exception as e:
        print(f"❌ Default SPI failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_default_spi()
    test_custom_spi()