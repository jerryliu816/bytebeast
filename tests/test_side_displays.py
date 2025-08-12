#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
Test 0.96" side displays - try different pin configurations
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "display" / "lib"))

import spidev as SPI
from lib import LCD_0inch96
from PIL import Image, ImageDraw, ImageFont
import time

def test_display_config(name, spi_bus, spi_device, rst_pin, dc_pin, bl_pin):
    """Test a specific display configuration"""
    print(f"\n=== Testing {name} ===")
    print(f"SPI: {spi_bus}.{spi_device}, RST: {rst_pin}, DC: {dc_pin}, BL: {bl_pin}")
    
    try:
        # Create display with specific pins
        disp = LCD_0inch96.LCD_0inch96(
            spi=SPI.SpiDev(spi_bus, spi_device),
            spi_freq=10000000,
            rst=rst_pin,
            dc=dc_pin,
            bl=bl_pin
        )
        
        # Initialize
        disp.Init()
        disp.clear()
        disp.bl_DutyCycle(100)
        
        # Test with bright red background
        print(f"  Showing RED background...")
        image = Image.new("RGB", (disp.width, disp.height), "RED")
        disp.ShowImage(image)
        time.sleep(2)
        
        # Test with text
        print(f"  Showing TEXT...")
        image = Image.new("RGB", (disp.width, disp.height), "BLUE")
        draw = ImageDraw.Draw(image)
        draw.text((20, 30), name, fill="WHITE")
        disp.ShowImage(image)
        time.sleep(2)
        
        # Clear
        image = Image.new("RGB", (disp.width, disp.height), "BLACK")
        disp.ShowImage(image)
        
        print(f"  ✅ {name} SUCCESS!")
        return True
        
    except Exception as e:
        print(f"  ❌ {name} FAILED: {e}")
        return False

def main():
    print("Testing different 0.96\" display configurations...")
    
    # Test various common pin configurations for 0.96" displays
    
    # Configuration 1: Default pins (same as 1.3")
    test_display_config(
        "Config1-Default", 
        spi_bus=0, spi_device=0, 
        rst_pin=27, dc_pin=22, bl_pin=19
    )
    
    # Configuration 2: Different pins to avoid conflict with 1.3"
    test_display_config(
        "Config2-Alt1", 
        spi_bus=0, spi_device=0, 
        rst_pin=26, dc_pin=23, bl_pin=13
    )
    
    # Configuration 3: SPI0 CE1
    test_display_config(
        "Config3-CE1", 
        spi_bus=0, spi_device=1, 
        rst_pin=24, dc_pin=25, bl_pin=18
    )
    
    # Configuration 4: Common 0.96" pins from examples
    test_display_config(
        "Config4-Common", 
        spi_bus=0, spi_device=0, 
        rst_pin=22, dc_pin=23, bl_pin=19
    )
    
    print("\n=== Test Complete ===")
    print("Check which configurations worked and note the pins!")

if __name__ == "__main__":
    main()