"""
Display manager for ByteBeast - manages the triple LCD display system.

Integrates with existing LCD drivers for emoji rendering.
"""

import time
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, List
from PIL import Image, ImageDraw, ImageFont

# Add display libraries to path
sys.path.append(str(Path(__file__).parent / 'lib'))
sys.path.append('/home/jerry/dev/bytebeast')

from core.models import EmojiFrame, PowerState, Beast
from core.config import get_config

logger = logging.getLogger(__name__)

# Unicode to hexcode mapping for mood emojis
EMOJI_HEXCODES = {
    '😃': '1F603',  # happy
    '😌': '1F60C',  # calm
    '😴': '1F634',  # sleepy
    '😰': '1F630',  # anxious
    '🤒': '1F912',  # sick
    '🤩': '1F929',  # playful
    '😐': '1F610',  # bored
    '🧐': '1F9D0',  # curious
    '🥵': '1F975',  # hot
    '🥶': '1F976',  # cold
    # Evolution emojis
    '🐣': '1F423',  # sun path
    '🐥': '1F425',
    '🦅': '1F985',
    '🦄': '1F984',
    '🦇': '1F987',  # shadow path
    '🦉': '1F989',
    '🐺': '1F43A',
    '🐉': '1F409',
    '🦁': '1F981',  # ember path
    '🔥': '1F525',
    '🐯': '1F42F',
    '🐧': '1F427',  # frost path
    '❄️': '2744',
    '🐻‍❄️': '1F43B-200D-2744-FE0F',  # polar bear
    '🐒': '1F412',  # social path
    '👑': '1F451',
    '🐭': '1F42D',  # lone path
    '🦊': '1F98A',
    # Need badges
    '🍴': '1F374',  # hunger
    '😴': '1F634',  # rest (same as sleepy mood)
    '👥': '1F465',  # social
    '🚿': '1F6BF',  # hygiene
}

try:
    from display.lib import LCD_0inch96
    from display.lib import LCD_1inch3
    HARDWARE_AVAILABLE = True
except ImportError:
    logger.warning("Display hardware libraries not available, using mock mode")
    HARDWARE_AVAILABLE = False


class DisplayManager:
    """Real display manager using hardware LCD drivers."""
    
    def __init__(self):
        """Initialize the triple display system."""
        if not HARDWARE_AVAILABLE:
            raise RuntimeError("Hardware display libraries not available")
            
        self.config = get_config()
        
        # Initialize displays
        try:
            import spidev as SPI
            
            # Main 1.3" display - exact same pattern as working test5.py
            RST = 27
            DC = 22  
            BL = 19
            bus = 1
            device = 0
            
            self.display_main = LCD_1inch3.LCD_1inch3(
                spi=SPI.SpiDev(bus, device),
                spi_freq=10000000,  # 10MHz like working example
                rst=RST,
                dc=DC,
                bl=BL
            )
            
            # Initialize and configure backlight
            self.display_main.Init()
            self.display_main.clear()
            self.display_main.bl_DutyCycle(100)  # Full brightness
            
            logger.info("✅ Main display initialized successfully")
            
            # Initialize side displays with pins matching working test5.py
            # Left display - SPI0 CE0 (disp_0 in test5.py)
            self.display_left = LCD_0inch96.LCD_0inch96(
                spi=SPI.SpiDev(0, 0),
                spi_freq=10000000,
                rst=24,
                dc=4, 
                bl=13,
                bl_freq=1000
            )
            self.display_left.Init()
            self.display_left.clear()
            self.display_left.bl_DutyCycle(100)
            
            # Right display - SPI0 CE1 (disp_1 in test5.py)
            self.display_right = LCD_0inch96.LCD_0inch96(
                spi=SPI.SpiDev(0, 1),
                spi_freq=10000000,
                rst=23,
                dc=5,
                bl=12,
                bl_freq=1000
            )
            self.display_right.Init()
            self.display_right.clear() 
            self.display_right.bl_DutyCycle(100)
            
            logger.info("✅ All displays initialized successfully")
            
            # Clear displays to black (no test patterns)
            self.clear_displays()
            
        except Exception as e:
            logger.error(f"Failed to initialize displays: {e}")
            raise
    
    def render_frame(self, frame: EmojiFrame, power_state: PowerState):
        """Render emoji frame to displays based on power state."""
        try:
            if power_state.critical_battery:
                # Show battery warning on main display only
                self._render_power_warning()
                return
                
            # Render main emoji on center display
            if frame.emoji:
                self._render_main_emoji_char(frame.emoji)
            
            # Render badges on side displays
            if frame.badges:
                if len(frame.badges) > 0:
                    self._render_side_emoji_char(frame.badges[0], 'left')
                if len(frame.badges) > 1:
                    self._render_side_emoji_char(frame.badges[1], 'right')
                
        except Exception as e:
            logger.error(f"Failed to render frame: {e}")
    
    def _render_main_emoji_char(self, emoji_char: str):
        """Render OpenMoji PNG on main 240x240 display."""
        try:
            # Get hexcode for emoji
            hexcode = EMOJI_HEXCODES.get(emoji_char)
            if not hexcode:
                logger.warning(f"No hexcode found for emoji: {emoji_char}")
                self._render_fallback_main(emoji_char)
                return
            
            # Load OpenMoji PNG file
            openmoji_path = Path(__file__).parent / 'openmoji' / f'{hexcode}.png'
            if not openmoji_path.exists():
                logger.warning(f"OpenMoji file not found: {openmoji_path}")
                self._render_fallback_main(emoji_char)
                return
            
            # Load and resize emoji image
            emoji_img = Image.open(openmoji_path).convert('RGBA')
            
            # Create canvas with dark background
            canvas = Image.new('RGB', (240, 240), (20, 20, 40))  # Dark blue-gray background
            
            # Resize emoji to fit nicely (leave some padding)
            target_size = 180  # 180x180 emoji on 240x240 canvas
            emoji_resized = emoji_img.resize((target_size, target_size), Image.Resampling.LANCZOS)
            
            # Center the emoji on canvas
            x_offset = (240 - target_size) // 2
            y_offset = (240 - target_size) // 2
            
            # Paste emoji onto canvas (handle transparency)
            canvas.paste(emoji_resized, (x_offset, y_offset), emoji_resized)
            
            # Send to display
            self.display_main.ShowImage(canvas)
            logger.info(f"📱 Rendered main OpenMoji: {emoji_char} ({hexcode})")
            
        except Exception as e:
            logger.error(f"Failed to render main emoji {emoji_char}: {e}")
            self._render_fallback_main(emoji_char)
    
    def _render_fallback_main(self, emoji_char: str):
        """Fallback rendering for main display when OpenMoji fails."""
        try:
            from PIL import ImageDraw, ImageFont
            
            canvas = Image.new('RGB', (240, 240), (50, 50, 150))
            draw = ImageDraw.Draw(canvas)
            
            # Draw border
            draw.rectangle([(5, 5), (235, 235)], outline=(255, 255, 255), width=2)
            
            # Draw large text fallback
            font = ImageFont.load_default()
            text = f"MOOD\n{emoji_char}"
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (240 - text_width) // 2
            y = (240 - text_height) // 2
            
            draw.text((x, y), text, fill=(255, 255, 0), font=font)
            self.display_main.ShowImage(canvas)
            
        except Exception as e:
            logger.error(f"Fallback render failed: {e}")
    
    def _render_side_emoji_char(self, emoji_char: str, side: str):
        """Render OpenMoji PNG on side 160x80 displays."""
        try:
            # Get hexcode for emoji
            hexcode = EMOJI_HEXCODES.get(emoji_char)
            if not hexcode:
                logger.warning(f"No hexcode found for side emoji: {emoji_char}")
                self._render_fallback_side(emoji_char, side)
                return
            
            # Load OpenMoji PNG file
            openmoji_path = Path(__file__).parent / 'openmoji' / f'{hexcode}.png'
            if not openmoji_path.exists():
                logger.warning(f"OpenMoji file not found: {openmoji_path}")
                self._render_fallback_side(emoji_char, side)
                return
            
            # Load and resize emoji image
            emoji_img = Image.open(openmoji_path).convert('RGBA')
            
            # Create canvas with dark background
            canvas = Image.new('RGB', (160, 80), (10, 10, 20))  # Very dark background
            
            # Resize emoji to fit the smaller display (leave some padding)
            target_size = 60  # 60x60 emoji on 160x80 canvas
            emoji_resized = emoji_img.resize((target_size, target_size), Image.Resampling.LANCZOS)
            
            # Center the emoji on canvas
            x_offset = (160 - target_size) // 2
            y_offset = (80 - target_size) // 2
            
            # Paste emoji onto canvas (handle transparency)
            canvas.paste(emoji_resized, (x_offset, y_offset), emoji_resized)
            
            # Send to appropriate display
            if side == 'left':
                self.display_left.ShowImage(canvas)
            else:
                self.display_right.ShowImage(canvas)
            logger.info(f"📱 Rendered {side} OpenMoji: {emoji_char} ({hexcode})")
                
        except Exception as e:
            logger.error(f"Failed to render side emoji {emoji_char} on {side}: {e}")
            self._render_fallback_side(emoji_char, side)
    
    def _render_fallback_side(self, emoji_char: str, side: str):
        """Fallback rendering for side displays when OpenMoji fails."""
        try:
            from PIL import ImageDraw, ImageFont
            
            canvas = Image.new('RGB', (160, 80), (30, 30, 60))
            draw = ImageDraw.Draw(canvas)
            
            # Draw border
            draw.rectangle([(2, 2), (158, 78)], outline=(255, 255, 255), width=1)
            
            # Draw text fallback
            font = ImageFont.load_default()
            bbox = draw.textbbox((0, 0), emoji_char, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (160 - text_width) // 2
            y = (80 - text_height) // 2
            
            draw.text((x, y), emoji_char, fill=(255, 255, 0), font=font)
            
            if side == 'left':
                self.display_left.ShowImage(canvas)
            else:
                self.display_right.ShowImage(canvas)
                
        except Exception as e:
            logger.error(f"Fallback side render failed: {e}")
    
    
    def _render_power_warning(self):
        """Render low battery warning."""
        try:
            # Create warning image
            canvas = Image.new('RGB', (240, 240), (255, 0, 0))
            draw = ImageDraw.Draw(canvas)
            
            # Draw warning text
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            except OSError:
                font = ImageFont.load_default()
            
            text = "LOW\nBATTERY"
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (240 - text_width) // 2
            y = (240 - text_height) // 2
            
            draw.text((x, y), text, fill=(255, 255, 255), font=font)
            
            # Send to main display
            self.display_main.ShowImage(canvas)
            
            # Clear side displays
            black = Image.new('RGB', (160, 80), (0, 0, 0))
            self.display_left.ShowImage(black)
            self.display_right.ShowImage(black)
            
        except Exception as e:
            logger.error(f"Failed to render power warning: {e}")
    
    def clear_displays(self):
        """Clear all displays."""
        try:
            black_main = Image.new('RGB', (240, 240), (0, 0, 0))
            black_side = Image.new('RGB', (160, 80), (0, 0, 0))
            
            self.display_main.ShowImage(black_main)
            self.display_left.ShowImage(black_side)
            self.display_right.ShowImage(black_side)
            
        except Exception as e:
            logger.error(f"Failed to clear displays: {e}")
    
    def create_emoji_frame(self, beast: Beast, env_features: 'EnvFeatures') -> EmojiFrame:
        """Create emoji frame based on beast state and environment."""
        from core.models import MOOD_EMOJIS, EVOLUTION_PATHS
        
        # Get main emoji based on mood
        main_emoji = MOOD_EMOJIS.get(beast.mood, '😌')  # Default calm
        
        # Create badges list
        badges = []
        
        # Show evolution badge
        if beast.evolution_path in EVOLUTION_PATHS:
            stage_emoji = EVOLUTION_PATHS[beast.evolution_path]['stages'][beast.evolution_stage - 1]
            badges.append(stage_emoji)
        
        # Show need status badge (most urgent need)
        lowest_need = min(beast.needs.items(), key=lambda x: x[1])
        if lowest_need[1] < 40:  # Show warning for low needs
            if lowest_need[0] == 'hunger':
                badges.append('🍴')  # Fork/knife
            elif lowest_need[0] == 'rest':
                badges.append('😴')  # Sleeping
            elif lowest_need[0] == 'social':
                badges.append('👥')  # People
            elif lowest_need[0] == 'hygiene':
                badges.append('🚿')  # Shower
        
        # Create progress bars for needs
        bars = {need: value / 100.0 for need, value in beast.needs.items()}
        
        return EmojiFrame(
            emoji=main_emoji,
            badges=badges,
            bars=bars
        )
    
    def update_display(self, emoji_frame: EmojiFrame, env_features: 'EnvFeatures'):
        """Update display with emoji frame."""
        # Create mock power state (simplified)
        power_state = PowerState(
            battery_percent=75.0,
            voltage=3.7,
            current_ma=250.0,
            power_w=0.925,
            charging=False
        )
        self.render_frame(emoji_frame, power_state)
    
    def cleanup(self):
        """Cleanup display resources."""
        try:
            self.clear_displays()
            logger.info("Display cleanup completed")
        except Exception as e:
            logger.error(f"Display cleanup failed: {e}")


class MockDisplayManager:
    """Mock display manager for testing without hardware."""
    
    def __init__(self):
        """Initialize mock display manager."""
        self.config = get_config()
        self.frame_count = 0
        logger.info("Mock display manager initialized")
    
    def render_frame(self, frame: EmojiFrame, power_state: PowerState):
        """Mock render emoji frame."""
        self.frame_count += 1
        
        if power_state.critical_battery:
            logger.info(f"[MOCK DISPLAY {self.frame_count}] 🔋 LOW BATTERY WARNING")
            return
        
        # Log what would be displayed with intended layout
        badges_str = " + ".join(frame.badges) if frame.badges else "None"
        
        logger.info(f"[MOCK DISPLAY {self.frame_count}] Layout:")
        logger.info(f"  Main (1.3\"): {frame.emoji} mood emoji")
        if frame.badges:
            if len(frame.badges) > 0:
                logger.info(f"  Left (0.96\"): {frame.badges[0]} evolution stage")
            if len(frame.badges) > 1:
                logger.info(f"  Right (0.96\"): {frame.badges[1]} need warning")
        else:
            logger.info(f"  Side displays: No badges to show")
    
    def clear_displays(self):
        """Mock clear displays."""
        logger.info("[MOCK DISPLAY] Cleared all displays")
    
    def create_emoji_frame(self, beast: 'Beast', env_features: 'EnvFeatures') -> EmojiFrame:
        """Mock create emoji frame."""
        from core.models import MOOD_EMOJIS, EVOLUTION_PATHS
        
        # Get main emoji based on mood
        main_emoji = MOOD_EMOJIS.get(beast.mood, '😌')  # Default calm
        
        # Create badges list
        badges = []
        
        # Show evolution badge
        if beast.evolution_path in EVOLUTION_PATHS:
            stage_emoji = EVOLUTION_PATHS[beast.evolution_path]['stages'][beast.evolution_stage - 1]
            badges.append(stage_emoji)
        
        # Show need status badge (most urgent need)
        lowest_need = min(beast.needs.items(), key=lambda x: x[1])
        if lowest_need[1] < 40:  # Show warning for low needs
            if lowest_need[0] == 'hunger':
                badges.append('🍴')  # Fork/knife
            elif lowest_need[0] == 'rest':
                badges.append('😴')  # Sleeping
            elif lowest_need[0] == 'social':
                badges.append('👥')  # People
            elif lowest_need[0] == 'hygiene':
                badges.append('🚿')  # Shower
        
        # Create progress bars for needs
        bars = {need: value / 100.0 for need, value in beast.needs.items()}
        
        return EmojiFrame(
            emoji=main_emoji,
            badges=badges,
            bars=bars
        )
    
    def update_display(self, emoji_frame: EmojiFrame, env_features: 'EnvFeatures'):
        """Mock update display."""
        # Create mock power state (simplified)
        power_state = PowerState(
            battery_percent=75.0,
            voltage=3.7,
            current_ma=250.0,
            power_w=0.925,
            charging=False
        )
        self.render_frame(emoji_frame, power_state)
    
    def cleanup(self):
        """Mock cleanup."""
        logger.info("[MOCK DISPLAY] Display cleanup completed")


def get_display_manager() -> DisplayManager:
    """Get appropriate display manager based on hardware availability."""
    config = get_config()
    
    if config.get('mock_mode', True) or not HARDWARE_AVAILABLE:
        return MockDisplayManager()
    else:
        return DisplayManager()