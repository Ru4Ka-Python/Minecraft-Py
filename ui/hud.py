"""
HUD (Heads-Up Display) for Minecraft clone.
Renders health, hunger, XP, and other player status indicators.
"""

from typing import Tuple, Optional, List
from PIL import Image, ImageDraw

from ui.elements import TextureManager, FontManager, Rect, Color


class HUD:
    """Heads-Up Display for player status."""
    
    def __init__(self, player):
        """Initialize HUD."""
        self.player = player
    
    def render(self, surface: Image.Image) -> None:
        """Render HUD to surface."""
        # Get screen dimensions
        width, height = surface.size
        
        # Render each HUD element
        self._render_hotbar(surface, width, height)
        self._render_health(surface, width, height)
        self._render_hunger(surface, width, height)
        self._render_armor(surface, width, height)
        self._render_air(surface, width, height)
        self._render_xp(surface, width, height)
        self._render_mount_health(surface, width, height)
    
    def _render_hotbar(self, surface: Image.Image, width: int, height: int) -> None:
        """Render hotbar at bottom of screen."""
        bar_width = 182
        bar_height = 22
        slot_size = 18
        
        # Position at bottom center
        x = width // 2 - bar_width // 2
        y = height - bar_height - 10
        
        # Draw hotbar background
        draw = ImageDraw.Draw(surface)
        
        # Load hotbar texture or create fallback
        hotbar_bg = self._create_hotbar_background(bar_width, bar_height)
        surface.paste(hotbar_bg, (x, y), hotbar_bg)
        
        # Render slots
        for i in range(9):
            slot_x = x + i * slot_size + 3
            slot_y = y + 3
            
            # Draw slot background
            slot_bg = Image.new('RGBA', (slot_size, slot_size), (0, 0, 0, 0))
            slot_draw = ImageDraw.Draw(slot_bg)
            slot_draw.rectangle([0, 0, slot_size - 1, slot_size - 1],
                               fill=(80, 80, 80, 255), outline=(40, 40, 40, 255))
            surface.paste(slot_bg, (slot_x, slot_y), slot_bg)
            
            # Draw selection highlight
            if i == self.player.inventory.selected_slot:
                highlight = Image.new('RGBA', (slot_size + 2, slot_size + 2), (0, 0, 0, 0))
                highlight_draw = ImageDraw.Draw(highlight)
                highlight_draw.rectangle([0, 0, slot_size, slot_size],
                                        fill=(255, 255, 255, 100), outline=(200, 200, 200, 255))
                surface.paste(highlight, (slot_x - 1, slot_y - 1), highlight)
            
            # Draw item if present
            item = self.player.inventory.hotbar[i]
            if item:
                self._render_item(surface, slot_x, slot_y, item, slot_size)
    
    def _render_item(self, surface: Image.Image, x: int, y: int, item, size: int) -> None:
        """Render an item icon in a slot."""
        # Get item texture
        texture = TextureManager.get(item.item_type.name.lower())
        
        if texture:
            # Scale texture to fit
            texture = texture.resize((size - 4, size - 4), Image.LANCZOS)
            surface.paste(texture, (x + 2, y + 2), texture)
            
            # Draw count
            if item.count > 1:
                count_text = str(item.count)
                font = FontManager.get(10)
                draw = ImageDraw.Draw(surface)
                bbox = font.getbbox(count_text)
                text_x = x + size - bbox[2] - 2
                text_y = y + size - bbox[3] - 2
                draw.text((text_x, text_y), count_text, font=font, fill=(255, 255, 255, 255))
        else:
            # Draw placeholder
            draw = ImageDraw.Draw(surface)
            draw.rectangle([x + 4, y + 4, x + size - 4, y + size - 4],
                          fill=(100, 100, 100, 255))
    
    def _render_health(self, surface: Image.Image, width: int, height: int) -> None:
        """Render health bar (hearts)."""
        hearts = (self.player.state.health + 1) // 2
        max_hearts = 10
        
        heart_size = 9
        heart_spacing = 10
        
        # Position: top-left
        x = 10
        y = 10
        
        draw = ImageDraw.Draw(surface)
        
        for i in range(max_hearts):
            heart_x = x + i * heart_spacing
            
            # Determine heart type
            if i < hearts:
                # Full heart
                self._draw_heart(surface, heart_x, y, 'full')
            elif i == hearts and self.player.state.health % 2 == 1:
                # Half heart
                self._draw_heart(surface, heart_x, y, 'half')
            else:
                # Empty heart
                self._draw_heart(surface, heart_x, y, 'empty')
    
    def _draw_heart(self, surface: Image.Image, x: int, y: int, state: str) -> None:
        """Draw a heart in the specified state."""
        draw = ImageDraw.Draw(surface)
        
        if state == 'full':
            color = (255, 0, 0, 255)
        elif state == 'half':
            color = (255, 100, 100, 255)
        else:
            color = (100, 0, 0, 255)
        
        # Draw heart shape
        # Simplified: draw overlapping circles
        r = 4
        
        # Left circle
        draw.ellipse([x, y, x + r * 2, y + r * 2], fill=color)
        # Right circle
        draw.ellipse([x + r - 2, y, x + r * 2 - 2, y + r * 2], fill=color)
        # Bottom triangle
        draw.polygon([(x, y + r), (x + 9, y + r), (x + 4, y + 9)], fill=color)
    
    def _render_hunger(self, surface: Image.Image, width: int, height: int) -> None:
        """Render hunger bar (food icons)."""
        food = self.player.state.hunger
        max_food = 20
        
        food_size = 9
        food_spacing = 10
        
        # Position: bottom-left, above hotbar
        x = 10
        y = height - 40
        
        draw = ImageDraw.Draw(surface)
        
        for i in range(max_food // 2):
            food_x = x + i * food_spacing
            
            if i < food // 2:
                self._draw_food_icon(surface, food_x, y, 'full')
            elif i == food // 2 and food % 2 == 1:
                self._draw_food_icon(surface, food_x, y, 'half')
            else:
                self._draw_food_icon(surface, food_x, y, 'empty')
    
    def _draw_food_icon(self, surface: Image.Image, x: int, y: int, state: str) -> None:
        """Draw a food icon."""
        draw = ImageDraw.Draw(surface)
        
        if state == 'full':
            color = (255, 175, 0, 255)
        elif state == 'half':
            color = (255, 200, 100, 255)
        else:
            color = (80, 60, 40, 255)
        
        # Draw chicken drumstick shape (simplified)
        draw.ellipse([x, y, x + 8, y + 6], fill=color)
        draw.rectangle([x + 4, y + 6, x + 5, y + 10], fill=color)
    
    def _render_armor(self, surface: Image.Image, width: int, height: int) -> None:
        """Render armor bar."""
        armor = self.player.state.armor
        max_armor = 20
        
        if armor <= 0:
            return
        
        icon_size = 7
        
        # Position: above health
        x = 10
        y = 25
        
        draw = ImageDraw.Draw(surface)
        
        for i in range(max_armor // 5):
            icon_x = x + i * (icon_size + 1)
            
            # Full armor point
            if (i + 1) * 5 <= armor:
                self._draw_armor_icon(surface, icon_x, y, 'full')
            elif i * 5 < armor:
                self._draw_armor_icon(surface, icon_x, y, 'partial')
            else:
                self._draw_armor_icon(surface, icon_x, y, 'empty')
    
    def _draw_armor_icon(self, surface: Image.Image, x: int, y: int, state: str) -> None:
        """Draw an armor point icon."""
        draw = ImageDraw.Draw(surface)
        
        if state == 'full':
            color = (100, 100, 100, 255)
        elif state == 'partial':
            color = (150, 150, 150, 255)
        else:
            color = (50, 50, 50, 255)
        
        # Draw armor icon (simplified chestplate)
        draw.rectangle([x, y, x + 6, y + 8], fill=color, outline=(50, 50, 50, 255))
    
    def _render_air(self, surface: Image.Image, width: int, height: int) -> None:
        """Render air bubbles for underwater breathing."""
        # Check if player is underwater
        if not self.player.state.in_water:
            return
        
        # Calculate air
        air = 10  # Would be calculated from player state
        
        bubble_size = 8
        bubble_spacing = 10
        
        # Position: above hunger bar
        x = 10
        y = height - 60
        
        draw = ImageDraw.Draw(surface)
        
        for i in range(air):
            bubble_x = x + i * bubble_spacing
            self._draw_bubble(surface, bubble_x, y)
    
    def _draw_bubble(self, surface: Image.Image, x: int, y: int) -> None:
        """Draw an air bubble."""
        draw = ImageDraw.Draw(surface)
        draw.ellipse([x, y, x + 6, y + 6], fill=(100, 200, 255, 255))
        draw.ellipse([x + 1, y + 1, x + 3, y + 3], fill=(255, 255, 255, 200))
    
    def _render_xp(self, surface: Image.Image, width: int, height: int) -> None:
        """Render XP bar."""
        if self.player.state.xp_level <= 0:
            return
        
        bar_width = 182
        bar_height = 5
        
        # Position: below hotbar
        x = width // 2 - bar_width // 2
        y = height - 30
        
        draw = ImageDraw.Draw(surface)
        
        # Draw XP bar background
        draw.rectangle([x, y, x + bar_width, y + bar_height],
                      fill=(0, 0, 0, 128))
        
        # Draw XP level number
        level_text = str(self.player.state.xp_level)
        font = FontManager.get(10)
        draw.text((x - 25, y - 5), level_text, font=font, fill=(255, 255, 255, 255))
        
        # Draw XP progress
        progress_width = int(bar_width * self.player.state.xp_progress)
        if progress_width > 0:
            draw.rectangle([x, y, x + progress_width, y + bar_height],
                          fill=(255, 215, 0, 255))
    
    def _render_mount_health(self, surface: Image.Image, width: int, height: int) -> None:
        """Render mount health bar (for horses, etc.)."""
        # Would render if player is riding a mount
        pass
    
    def _create_hotbar_background(self, width: int, height: int) -> Image.Image:
        """Create hotbar background texture."""
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw hotbar with slots
        for i in range(9):
            slot_x = i * 18 + 3
            draw.rectangle([slot_x, 2, slot_x + 16, 18],
                          fill=(139, 139, 139, 255), outline=(0, 0, 0, 255))
        
        # Draw selection box
        selected_x = self.player.inventory.selected_slot * 18 + 2
        draw.rectangle([selected_x, 1, selected_x + 18, 19],
                      fill=(255, 255, 255, 100), outline=(255, 255, 255, 255))
        
        return img
    
    def update(self, delta_time: float) -> None:
        """Update HUD state."""
        pass


class DebugInfo:
    """Debug information display (F3 menu)."""
    
    def __init__(self, player, world):
        """Initialize debug info."""
        self.player = player
        self.world = world
    
    def render(self, surface: Image.Image) -> None:
        """Render debug information."""
        width, height = surface.size
        
        lines = self._get_debug_lines()
        
        font = FontManager.get(12)
        draw = ImageDraw.Draw(surface)
        
        line_height = 12
        x = 10
        y = 10
        
        for line in lines:
            # Draw text with shadow
            draw.text((x + 1, y + 1), line, font=font, fill=(0, 0, 0, 255))
            draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
            y += line_height
    
    def _get_debug_lines(self) -> List[str]:
        """Get debug information lines."""
        lines = []
        
        # Position
        px, py, pz = self.player.state.position
        lines.append(f"XYZ: {px:.3f} / {py:.3f} / {pz:.3f}")
        
        # Facing direction
        yaw = math.degrees(self.player.state.yaw) % 360
        pitch = math.degrees(self.player.state.pitch)
        lines.append(f"Facing: {yaw:.1f} / {pitch:.1f}")
        
        # Chunk info
        chunk_x = int(px) // 16
        chunk_z = int(pz) // 16
        lines.append(f"Chunk: {chunk_x}, {chunk_z}")
        
        # World info
        lines.append(f"World: {self.world.seed}")
        lines.append(f"Time: {int(self.world.time_of_day)}")
        
        # Performance
        lines.append("FPS: 60")  # Would be calculated
        
        # Game mode
        mode = "Creative" if self.player.state.is_creative else "Survival"
        lines.append(f"Game Mode: {mode}")
        
        # Difficulty
        lines.append("Difficulty: Normal")
        
        return lines


import math
