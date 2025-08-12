#!/usr/bin/env python3
"""
Debug display - minimal test exactly like test5.py
"""

import sys
import time
from pathlib import Path

# Add correct paths for our structure
sys.path.append(str(Path(__file__).parent / "display" / "lib"))

import spidev as SPI
from LCD_1inch3 import LCD_1inch3
from PIL import Image, ImageDraw, ImageFont

def main():
    print("Starting minimal display test...")
    
    try:
        # Exact same config as test5.py
        RST = 27
        DC = 22  
        BL = 19
        bus = 1
        device = 0
        
        print(f"Using pins: RST={RST}, DC={DC}, BL={BL}")
        print(f"Using SPI: bus={bus}, device={device}")
        
        # Initialize display exactly like test5.py
        disp = LCD_1inch3()
        
        # Initialize and clear
        disp.Init()
        disp.clear()
        
        print("Display initialized, showing red screen...")
        
        # Create red image
        image1 = Image.new("RGB", (disp.width, disp.height), "RED")
        disp.ShowImage(image1)
        
        print("Red screen displayed for 5 seconds...")
        time.sleep(5)
        
        # Create image with text
        image1 = Image.new("RGB", (disp.width, disp.height), "BLACK")
        draw = ImageDraw.Draw(image1)
        draw.text((50, 100), "HELLO!", fill="WHITE")
        disp.ShowImage(image1)
        
        print("Text displayed for 5 seconds...")
        time.sleep(5)
        
        # Clear to black
        image1 = Image.new("RGB", (disp.width, disp.height), "BLACK")
        disp.ShowImage(image1)
        
        print("✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()