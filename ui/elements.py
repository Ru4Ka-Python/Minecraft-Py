"""
UI element classes for Minecraft clone.
Custom UI components using PIL for rendering.
"""

from typing import Tuple, Optional, Callable, List
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont
import os

# Import path for assets
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')


class Rect:
    """Rectangle class for UI element positioning."""
    
    def __init__(self, x: int, y: int, width: int, height: int):
        """Initialize rectangle."""
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    
    @property
    def left(self) -> int:
        """Get left edge."""
        return self.x
    
    @property
    def right(self) -> int:
        """Get right edge."""
        return self.x + self.width
    
    @property
    def top(self) -> int:
        """Get top edge."""
        return self.y
    
    @property
    def bottom(self) -> int:
        """Get bottom edge."""
        return self.y + self.height
    
    @property
    def center(self) -> Tuple[int, int]:
        """Get center point."""
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    def contains(self, x: int, y: int) -> bool:
        """Check if point is inside rectangle."""
        return self.x <= x <= self.right and self.y <= y <= self.bottom
    
    def intersects(self, other: 'Rect') -> bool:
        """Check if rectangle intersects with another."""
        return not (self.right < other.x or self.x > other.right or
                   self.bottom < other.y or self.y > other.bottom)
    
    def scale(self, factor: float) -> 'Rect':
        """Scale rectangle by factor."""
        return Rect(
            int(self.x * factor),
            int(self.y * factor),
            int(self.width * factor),
            int(self.height * factor)
        )
    
    def move(self, dx: int, dy: int) -> 'Rect':
        """Move rectangle by offset."""
        return Rect(self.x + dx, self.y + dy, self.width, self.height)


class Color:
    """Color definitions for UI."""
    # Minecraft UI Colors
    WHITE = (255, 255, 255, 255)
    BLACK = (0, 0, 0, 255)
    DARK_GRAY = (64, 64, 64, 255)
    GRAY = (128, 128, 128, 255)
    LIGHT_GRAY = (192, 192, 192, 255)
    
    # Button colors
    BUTTON_NORMAL = (120, 120, 120, 255)
    BUTTON_HOVER = (140, 140, 140, 255)
    BUTTON_DISABLED = (80, 80, 80, 255)
    
    # Text colors
    TEXT_NORMAL = (255, 255, 255, 255)
    TEXT_DISABLED = (128, 128, 128, 255)
    TEXT_SHADOW = (0, 0, 0, 255)
    
    # HUD colors
    HEALTH_RED = (19, 142, 18, 255)  # Actually green in minecraft texture
    HEALTH_BAR = (105, 105, 105, 255)
    HUNGER_ORANGE = (115, 204, 20, 255)  # Green in minecraft texture
    ARMOR_GRAY = (90, 90, 90, 255)
    AIR_BLUE = (70, 180, 230, 255)
    
    # Splash text colors
    SPLASH_YELLOW = (255, 215, 0, 255)
    SPLASH_ORANGE = (255, 140, 0, 255)
    
    # Menu background
    BACKGROUND_DARK = (20, 20, 20, 200)
    BACKGROUND_LIGHT = (40, 40, 40, 150)


class TextureManager:
    """Manager for UI textures."""
    
    _textures: dict = {}
    
    @classmethod
    def load(cls, name: str) -> Optional[Image.Image]:
        """Load a texture by name."""
        if name in cls._textures:
            return cls._textures[name].copy()
        
        # Try various paths
        paths = [
            os.path.join(ASSETS_DIR, 'gui', f'{name}.png'),
            os.path.join(ASSETS_DIR, 'title', f'{name}.png'),
            os.path.join(ASSETS_DIR, 'item', f'{name}.png'),
        ]
        
        for path in paths:
            if os.path.exists(path):
                try:
                    img = Image.open(path).convert('RGBA')
                    cls._textures[name] = img.copy()
                    return img.copy()
                except Exception:
                    continue
        
        return None
    
    @classmethod
    def get(cls, name: str) -> Optional[Image.Image]:
        """Get a texture (create placeholder if missing)."""
        img = cls.load(name)
        if img is None:
            img = cls._create_placeholder(name)
        return img
    
    @classmethod
    def _create_placeholder(cls, name: str) -> Image.Image:
        """Create a placeholder texture."""
        img = Image.new('RGBA', (16, 16), (128, 128, 128, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle([4, 4, 11, 11], fill=(100, 100, 100, 255))
        cls._textures[name] = img.copy()
        return img.copy()
    
    @classmethod
    def clear_cache(cls) -> None:
        """Clear texture cache."""
        cls._textures.clear()


class FontManager:
    """Manager for fonts."""
    
    _fonts: dict = {}
    
    @classmethod
    def get(cls, size: int = 16, bold: bool = False) -> ImageFont.FreeTypeFont:
        """Get a font of specified size."""
        key = (size, bold)
        if key in cls._fonts:
            return cls._fonts[key]
        
        # Try to load Minecraft-style font
        font_paths = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/TTF/DejaVuSansMono.ttf',
            '/usr/share/fonts/dejavu/DejaVuSansMono.ttf',
        ]
        
        font = None
        for path in font_paths:
            if os.path.exists(path):
                try:
                    font = ImageFont.truetype(path, size)
                    break
                except Exception:
                    continue
        
        if font is None:
            font = ImageFont.load_default()
        
        cls._fonts[key] = font
        return font
    
    @classmethod
    def get_minecraft(cls, size: int = 32) -> ImageFont.FreeTypeFont:
        """Get a Minecraft-style font."""
        return cls.get(size)
    
    @classmethod
    def get_title(cls, size: int = 64) -> ImageFont.FreeTypeFont:
        """Get title-sized font."""
        return cls.get(size)
    
    @classmethod
    def get_splash(cls, size: int = 24) -> ImageFont.FreeTypeFont:
        """Get splash text font."""
        return cls.get(size)


class UIElement:
    """Base class for UI elements."""
    
    def __init__(self, rect: Rect, visible: bool = True, enabled: bool = True):
        """Initialize UI element."""
        self.rect = rect
        self.visible = visible
        self.enabled = enabled
        self.parent = None
        self.children: List['UIElement'] = []
    
    def add_child(self, child: 'UIElement') -> None:
        """Add a child element."""
        child.parent = self
        self.children.append(child)
    
    def remove_child(self, child: 'UIElement') -> None:
        """Remove a child element."""
        if child in self.children:
            child.parent = None
            self.children.remove(child)
    
    def get_screen_rect(self) -> Rect:
        """Get rectangle in screen coordinates."""
        if self.parent is None:
            return self.rect
        parent_rect = self.parent.get_screen_rect()
        return Rect(
            parent_rect.x + self.rect.x,
            parent_rect.y + self.rect.y,
            self.rect.width,
            self.rect.height
        )
    
    def render(self, surface: Image.Image) -> None:
        """Render the element."""
        if not self.visible:
            return
        
        for child in self.children:
            child.render(surface)
    
    def update(self, delta_time: float) -> None:
        """Update the element."""
        for child in self.children:
            child.update(delta_time)
    
    def handle_event(self, event) -> bool:
        """Handle an input event."""
        return False


class ImageElement(UIElement):
    """Image display element."""
    
    def __init__(self, rect: Rect, image: Image.Image = None, visible: bool = True):
        """Initialize image element."""
        super().__init__(rect, visible)
        self.image = image
        self._scale_mode = 'contain'
    
    def set_image(self, image: Image.Image) -> None:
        """Set the image."""
        self.image = image
    
    def render(self, surface: Image.Image) -> None:
        """Render the image."""
        if not self.visible or self.image is None:
            return
        
        # Scale image to fit rect
        if self._scale_mode == 'contain':
            img = self._contain_scale(self.image)
        elif self._scale_mode == 'cover':
            img = self._cover_scale(self.image)
        else:
            img = self.image
        
        # Center in rect
        x = self.rect.x + (self.rect.width - img.width) // 2
        y = self.rect.y + (self.rect.height - img.height) // 2
        
        surface.paste(img, (x, y), img)
        
        super().render(surface)
    
    def _contain_scale(self, img: Image.Image) -> Image.Image:
        """Scale image to contain within rect."""
        ratio = min(self.rect.width / img.width, self.rect.height / img.height)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        return img.resize(new_size, Image.LANCZOS)
    
    def _cover_scale(self, img: Image.Image) -> Image.Image:
        """Scale image to cover rect."""
        ratio = max(self.rect.width / img.width, self.rect.height / img.height)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        return img.resize(new_size, Image.LANCZOS)


class TextElement(UIElement):
    """Text display element."""
    
    def __init__(self, rect: Rect, text: str = "", font: ImageFont.FreeTypeFont = None,
                 color: Tuple[int, int, int, int] = Color.TEXT_NORMAL,
                 shadow: bool = True, visible: bool = True):
        """Initialize text element."""
        super().__init__(rect, visible)
        self.text = text
        self.font = font if font else FontManager.get()
        self.color = color
        self.shadow = shadow
        self._alignment = 'left'
    
    def set_text(self, text: str) -> None:
        """Set the text."""
        self.text = text
    
    def render(self, surface: Image.Image) -> None:
        """Render the text."""
        if not self.visible or not self.text:
            return
        
        draw = ImageDraw.Draw(surface)
        
        # Get text size
        bbox = self.font.getbbox(self.text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Calculate position based on alignment
        if self._alignment == 'left':
            x = self.rect.x
        elif self._alignment == 'center':
            x = self.rect.x + (self.rect.width - text_width) // 2
        else:  # right
            x = self.rect.right - text_width
        
        y = self.rect.y + (self.rect.height - text_height) // 2
        
        # Draw shadow
        if self.shadow:
            shadow_offset = 2
            draw.text((x + shadow_offset, y + shadow_offset), self.text,
                     font=self.font, fill=Color.TEXT_SHADOW)
        
        # Draw text
        draw.text((x, y), self.text, font=self.font, fill=self.color)
        
        super().render(surface)
    
    def set_alignment(self, alignment: str) -> None:
        """Set text alignment ('left', 'center', 'right')."""
        self._alignment = alignment


class Button(UIElement):
    """Button element with hover and click states."""
    
    def __init__(self, rect: Rect, text: str = "", on_click: Callable = None,
                 font: ImageFont.FreeTypeFont = None, visible: bool = True):
        """Initialize button."""
        super().__init__(rect, visible)
        self.text = text
        self.on_click = on_click
        self.font = font if font else FontManager.get(20)
        
        # State
        self._is_hovered = False
        self._is_pressed = False
        self._background_normal = Color.BUTTON_NORMAL
        self._background_hover = Color.BUTTON_HOVER
        self._background_pressed = (100, 100, 100, 255)
        
        # Animation
        self._hover_animation = 0.0
        self._press_animation = 0.0
    
    def render(self, surface: Image.Image) -> None:
        """Render the button."""
        if not self.visible:
            return
        
        draw = ImageDraw.Draw(surface)
        
        # Determine background color
        if self._is_pressed:
            bg_color = self._background_pressed
            offset = 2
        elif self._is_hovered:
            bg_color = self._background_hover
            offset = 0
        else:
            bg_color = self._background_normal
            offset = 0
        
        # Draw button background with rounded corners
        self._draw_rounded_rect(draw, self.rect, bg_color, 8)
        
        # Draw border
        border_color = Color.WHITE
        self._draw_rounded_rect_outline(draw, self.rect, border_color, 2, 8)
        
        # Draw text
        bbox = self.font.getbbox(self.text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = self.rect.x + (self.rect.width - text_width) // 2
        y = self.rect.y + (self.rect.height - text_height) // 2 + offset
        
        # Shadow
        draw.text((x + 2, y + 2), self.text, font=self.font, fill=Color.TEXT_SHADOW)
        
        # Main text
        text_color = Color.TEXT_NORMAL
        draw.text((x, y), self.text, font=self.font, fill=text_color)
        
        super().render(surface)
    
    def _draw_rounded_rect(self, draw: ImageDraw.ImageDraw, rect: Rect, color: Tuple, radius: int) -> None:
        """Draw a filled rounded rectangle."""
        x1, y1 = rect.x, rect.y
        x2, y2 = rect.right, rect.bottom
        
        # Draw main rectangle
        draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=color)
        draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=color)
        
        # Draw corner circles
        draw.ellipse([x1, y1, x1 + radius * 2, y1 + radius * 2], fill=color)
        draw.ellipse([x2 - radius * 2, y1, x2, y1 + radius * 2], fill=color)
        draw.ellipse([x1, y2 - radius * 2, x1 + radius * 2, y2], fill=color)
        draw.ellipse([x2 - radius * 2, y2 - radius * 2, x2, y2], fill=color)
    
    def _draw_rounded_rect_outline(self, draw: ImageDraw.ImageDraw, rect: Rect, color: Tuple, width: int, radius: int) -> None:
        """Draw a rounded rectangle outline."""
        x1, y1 = rect.x, rect.y
        x2, y2 = rect.right, rect.bottom
        
        # Draw lines
        draw.line([x1 + radius, y1, x2 - radius, y1], fill=color, width=width)
        draw.line([x1 + radius, y2, x2 - radius, y2], fill=color, width=width)
        draw.line([x1, y1 + radius, x1, y2 - radius], fill=color, width=width)
        draw.line([x2, y1 + radius, x2, y2 - radius], fill=color, width=width)
        
        # Draw corners
        draw.arc([x1, y1, x1 + radius * 2, y1 + radius * 2], 180, 270, fill=color, width=width)
        draw.arc([x2 - radius * 2, y1, x2, y1 + radius * 2], 270, 360, fill=color, width=width)
        draw.arc([x1, y2 - radius * 2, x1 + radius * 2, y2], 90, 180, fill=color, width=width)
        draw.arc([x2 - radius * 2, y2 - radius * 2, x2, y2], 0, 90, fill=color, width=width)
    
    def handle_event(self, event) -> bool:
        """Handle mouse events."""
        if not self.visible or not self.enabled:
            return False
        
        if event.type == 'mouse_move':
            self._is_hovered = self.rect.contains(event.x, event.y)
            return self._is_hovered
        
        elif event.type == 'mouse_press':
            if event.button == 1 and self.rect.contains(event.x, event.y):
                self._is_pressed = True
                return True
        
        elif event.type == 'mouse_release':
            if event.button == 1 and self._is_pressed:
                if self.rect.contains(event.x, event.y) and self.on_click:
                    self.on_click()
                self._is_pressed = False
                return True
        
        return False
    
    def update(self, delta_time: float) -> None:
        """Update button animations."""
        # Smooth hover animation
        target_hover = 1.0 if self._is_hovered else 0.0
        self._hover_animation += (target_hover - self._hover_animation) * 0.2
        
        # Smooth press animation
        target_press = 1.0 if self._is_pressed else 0.0
        self._press_animation += (target_press - self._press_animation) * 0.3


class Slider(UIElement):
    """Slider element for numeric values."""
    
    def __init__(self, rect: Rect, min_value: float = 0.0, max_value: float = 1.0,
                 value: float = 0.5, on_change: Callable = None, visible: bool = True):
        """Initialize slider."""
        super().__init__(rect, visible)
        self.min_value = min_value
        self.max_value = max_value
        self.value = value
        self.on_change = on_change
        
        self._is_dragging = False
        self._handle_radius = 10
    
    def render(self, surface: Image.Image) -> None:
        """Render the slider."""
        if not self.visible:
            return
        
        draw = ImageDraw.Draw(surface)
        
        # Draw track
        track_rect = Rect(
            self.rect.x,
            self.rect.y + self.rect.height // 2 - 4,
            self.rect.width,
            8
        )
        draw.rounded_rectangle(
            [track_rect.x, track_rect.y, track_rect.right, track_rect.bottom],
            radius=4,
            fill=Color.DARK_GRAY,
            outline=Color.LIGHT_GRAY
        )
        
        # Draw filled portion
        fill_width = int(self.rect.width * (self.value - self.min_value) / (self.max_value - self.min_value))
        if fill_width > 0:
            draw.rounded_rectangle(
                [track_rect.x, track_rect.y, track_rect.x + fill_width, track_rect.bottom],
                radius=4,
                fill=Color.LIGHT_GRAY
            )
        
        # Draw handle
        handle_x = self.rect.x + fill_width
        handle_y = self.rect.y + self.rect.height // 2
        
        draw.ellipse(
            [handle_x - self._handle_radius, handle_y - self._handle_radius,
             handle_x + self._handle_radius, handle_y + self._handle_radius],
            fill=Color.WHITE,
            outline=Color.LIGHT_GRAY
        )
        
        super().render(surface)
    
    def handle_event(self, event) -> bool:
        """Handle slider events."""
        if not self.visible:
            return False
        
        if event.type == 'mouse_press':
            if event.button == 1:
                handle_x = self.rect.x + self.rect.width * (self.value - self.min_value) / (self.max_value - self.min_value)
                if abs(event.x - handle_x) < self._handle_radius * 2:
                    self._is_dragging = True
                    return True
        
        elif event.type == 'mouse_release':
            if event.button == 1:
                self._is_dragging = False
        
        elif event.type == 'mouse_drag':
            if self._is_dragging:
                relative_x = max(0, min(self.rect.width, event.x - self.rect.x))
                self.value = self.min_value + relative_x / self.rect.width * (self.max_value - self.min_value)
                if self.on_change:
                    self.on_change(self.value)
                return True
        
        return False


class Checkbox(UIElement):
    """Checkbox element for boolean values."""
    
    def __init__(self, rect: Rect, checked: bool = False, text: str = "",
                 on_change: Callable = None, visible: bool = True):
        """Initialize checkbox."""
        super().__init__(rect, visible)
        self.checked = checked
        self.text = text
        self.on_change = on_change
        
        self._box_size = 20
        self._is_hovered = False
    
    def render(self, surface: Image.Image) -> None:
        """Render the checkbox."""
        if not self.visible:
            return
        
        draw = ImageDraw.Draw(surface)
        
        # Draw checkbox
        box_rect = Rect(
            self.rect.x,
            self.rect.y + (self.rect.height - self._box_size) // 2,
            self._box_size,
            self._box_size
        )
        
        fill_color = Color.LIGHT_GRAY if self.checked else Color.DARK_GRAY
        draw.rectangle(
            [box_rect.x, box_rect.y, box_rect.right, box_rect.bottom],
            fill=fill_color,
            outline=Color.WHITE
        )
        
        # Draw checkmark
        if self.checked:
            draw.line(
                [box_rect.x + 4, box_rect.y + box_rect.height // 2,
                 box_rect.x + box_rect.width // 2, box_rect.bottom - 4],
                fill=Color.WHITE,
                width=2
            )
            draw.line(
                [box_rect.x + box_rect.width // 2, box_rect.bottom - 4,
                 box_rect.right - 4, box_rect.y + 4],
                fill=Color.WHITE,
                width=2
            )
        
        # Draw text
        if self.text:
            font = FontManager.get()
            bbox = font.getbbox(self.text)
            text_y = self.rect.y + (self.rect.height - (bbox[3] - bbox[1])) // 2
            draw.text((box_rect.right + 10, text_y), self.text, font=font, fill=Color.TEXT_NORMAL)
        
        super().render(surface)
    
    def handle_event(self, event) -> bool:
        """Handle checkbox events."""
        if not self.visible:
            return False
        
        if event.type == 'mouse_press':
            if event.button == 1:
                box_rect = Rect(
                    self.rect.x,
                    self.rect.y + (self.rect.height - self._box_size) // 2,
                    self._box_size,
                    self._box_size
                )
                if box_rect.contains(event.x, event.y):
                    self.checked = not self.checked
                    if self.on_change:
                        self.on_change(self.checked)
                    return True
        
        return False


class Panel(UIElement):
    """Panel container for UI elements."""
    
    def __init__(self, rect: Rect, background_color: Tuple = None, visible: bool = True):
        """Initialize panel."""
        super().__init__(rect, visible)
        self.background_color = background_color if background_color else (0, 0, 0, 128)
    
    def render(self, surface: Image.Image) -> None:
        """Render the panel."""
        if not self.visible:
            return
        
        # Draw background
        if self.background_color:
            draw = ImageDraw.Draw(surface)
            draw.rectangle(
                [self.rect.x, self.rect.y, self.rect.right, self.rect.bottom],
                fill=self.background_color
            )
        
        super().render(surface)
