"""
Main Menu screen for Minecraft clone.
Displays logo, splash text, and menu buttons with panorama background.
"""

import os
import random
import math
import time
from typing import Tuple, Optional, List
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

from ui.elements import (
    UIElement, Rect, Color, TextureManager, FontManager,
    Button, TextElement, ImageElement, Panel
)


class SplashText:
    """Animated splash text with sinusoidal scaling."""
    
    def __init__(self, text: str, x: int, y: int):
        """Initialize splash text."""
        self.text = text
        self.base_x = x
        self.base_y = y
        self._scale = 1.0
        self._rotation = 0.0
        self._phase = random.uniform(0, math.pi * 2)
        self._tick = 0
    
    def update(self, delta_time: float) -> None:
        """Update splash animation."""
        self._tick += delta_time
        
        # Sinusoidal scaling
        self._scale = 1.0 + 0.1 * math.sin(self._tick * 3 + self._phase)
        
        # Slight rotation
        self._rotation = 0.05 * math.sin(self._tick * 2 + self._phase)
    
    def get_position(self) -> Tuple[int, int]:
        """Get current position."""
        return self.base_x, self.base_y
    
    def get_scale(self) -> float:
        """Get current scale."""
        return self._scale


class Panorama:
    """360-degree rotating panorama background."""
    
    def __init__(self, width: int, height: int):
        """Initialize panorama renderer."""
        self.width = width
        self.height = height
        
        # Load panorama images
        self._load_panorama_images()
        
        # Animation state
        self._rotation = 0.0
        self._target_rotation = 0.0
        self._last_update = time.time()
    
    def _load_panorama_images(self) -> None:
        """Load panorama images from assets."""
        self.panorama_images: List[Image.Image] = []
        
        # Try to load panorama images
        panorama_dir = os.path.join(ASSETS_DIR, 'title', 'bg')
        
        if os.path.exists(panorama_dir):
            # Load numbered panorama images
            for i in range(1, 7):  # panorama1.png to panorama6.png
                path = os.path.join(panorama_dir, f'panorama{i}.png')
                if os.path.exists(path):
                    try:
                        img = Image.open(path).convert('RGBA')
                        img = img.resize((self.width, self.height), Image.LANCZOS)
                        self.panorama_images.append(img)
                    except Exception:
                        continue
        
        # Fallback: create gradient background
        if not self.panorama_images:
            self.panorama_images = [self._create_gradient_background()]
        
        self.image_count = len(self.panorama_images)
    
    def _create_gradient_background(self) -> Image.Image:
        """Create a gradient background as fallback."""
        img = Image.new('RGBA', (self.width, self.height))
        draw = ImageDraw.Draw(img)
        
        # Sky gradient
        for y in range(self.height):
            t = y / self.height
            r = int(100 + 100 * t)
            g = int(150 + 100 * t)
            b = int(200 + 55 * t)
            color = (r, g, b, 255)
            draw.rectangle([0, y, self.width, y + 1], fill=color)
        
        # Add some terrain-like features
        for x in range(0, self.width, 20):
            height = int(30 + 20 * math.sin(x * 0.05))
            draw.polygon(
                [(x, self.height - height), (x + 20, self.height - height), (x + 10, self.height)],
                fill=(34, 139, 34, 255)
            )
        
        return img
    
    def update(self, delta_time: float) -> None:
        """Update panorama rotation."""
        # Smooth rotation
        self._target_rotation += delta_time * 0.1
        self._rotation += (self._target_rotation - self._rotation) * 0.05
    
    def render(self, surface: Image.Image) -> Image.Image:
        """Render panorama to surface."""
        # Calculate which images to blend
        rotation = self._rotation % self.image_count
        
        idx1 = int(rotation) % self.image_count
        idx2 = (idx1 + 1) % self.image_count
        blend = rotation - int(rotation)
        
        # Get images
        img1 = self.panorama_images[idx1]
        img2 = self.panorama_images[idx2]
        
        # Blend images
        if blend > 0:
            result = Image.blend(img1, img2, blend)
        else:
            result = img1.copy()
        
        # Apply blur for depth of field effect
        # result = result.filter(ImageFilter.GaussianBlur(radius=2))
        
        return result


class MainMenu:
    """Main menu screen for Minecraft clone."""
    
    def __init__(self, window, renderer):
        """Initialize main menu."""
        self.window = window
        self.renderer = renderer
        self.width, self.height = window.get_size()
        
        # State
        self.is_active = True
        self.last_time = time.time()
        
        # Load assets
        self._load_assets()
        
        # Initialize UI elements
        self._init_ui()
        
        # Initialize panorama
        self.panorama = Panorama(self.width, self.height)
        
        # Splash text
        self._init_splash_text()
        
        # Background panel for main menu
        self.background_panel = Panel(
            Rect(0, 0, self.width, self.height),
            background_color=(0, 0, 0, 0)
        )
        
        # Animation state
        self.logo_offset = 0
        self.buttons_animated_in = False
        self.animation_time = 0.0
    
    def _load_assets(self) -> None:
        """Load menu assets."""
        # Load logo
        self.logo_image = TextureManager.get('mclogo')
        
        # Load button textures
        self.button_texture = TextureManager.get('button')
        
        # Load splash texts
        self._load_splashes()
    
    def _load_splashes(self) -> None:
        """Load splash texts from file."""
        splash_path = os.path.join(ASSETS_DIR, 'title', 'splashes.txt')
        
        if os.path.exists(splash_path):
            with open(splash_path, 'r') as f:
                self.splashes = [line.strip() for line in f.readlines() if line.strip()]
        else:
            # Default splashes
            self.splashes = [
                "Awesome!", "Minecraft!", "Singleplayer!", "Made in Sweden!",
                "Reticulating splines!", "Yaaay!", "Check it out!", "It's here!",
                "Notch <3 ez!", "Music by C418!", "Best in class!", "Exclusive!",
            ]
    
    def _init_ui(self) -> None:
        """Initialize UI elements."""
        self.ui_elements: List[UIElement] = []
        
        # Version text (bottom-left)
        self.version_text = TextElement(
            Rect(20, self.height - 40, 300, 30),
            text="Minecraft 1.0 (Python Edition)",
            font=FontManager.get(16),
            color=Color.TEXT_NORMAL
        )
        self.ui_elements.append(self.version_text)
        
        # Menu buttons (centered)
        button_width = 200
        button_height = 40
        button_spacing = 10
        start_y = self.height // 2 + 50
        
        # Singleplayer button
        self.singleplayer_btn = Button(
            Rect(
                self.width // 2 - button_width // 2,
                start_y,
                button_width,
                button_height
            ),
            text="Singleplayer",
            font=FontManager.get(20),
            on_click=self._on_singleplayer
        )
        self.ui_elements.append(self.singleplayer_btn)
        
        # Options button
        self.options_btn = Button(
            Rect(
                self.width // 2 - button_width // 2,
                start_y + button_height + button_spacing,
                button_width,
                button_height
            ),
            text="Options...",
            font=FontManager.get(20),
            on_click=self._on_options
        )
        self.ui_elements.append(self.options_btn)
        
        # Quit button
        self.quit_btn = Button(
            Rect(
                self.width // 2 - button_width // 2,
                start_y + (button_height + button_spacing) * 2,
                button_width,
                button_height
            ),
            text="Quit Game",
            font=FontManager.get(20),
            on_click=self._on_quit
        )
        self.ui_elements.append(self.quit_btn)
        
        # Mojang logo (bottom-right)
        self.mojang_logo = ImageElement(
            Rect(self.width - 150, self.height - 50, 120, 40),
            image=TextureManager.get('mojang'),
            visible=True
        )
        self.ui_elements.append(self.mojang_logo)
    
    def _init_splash_text(self) -> None:
        """Initialize splash text."""
        # Pick random splash
        splash_text = random.choice(self.splashes)
        
        # Position next to logo
        logo_width = 256 if self.logo_image else 200
        splash_x = self.width // 2 + logo_width // 2 + 30
        splash_y = self.height // 2 - 100
        
        self.splash = SplashText(splash_text, splash_x, splash_y)
        self.splash_font = FontManager.get_splash(24)
    
    def _on_singleplayer(self) -> None:
        """Handle singleplayer button click."""
        print("Starting singleplayer...")
        # Transition to game screen
    
    def _on_options(self) -> None:
        """Handle options button click."""
        print("Opening options...")
        # Show options menu
    
    def _on_quit(self) -> None:
        """Handle quit button click."""
        print("Quitting game...")
        self.window.set_should_close(True)
    
    def update(self) -> None:
        """Update menu state."""
        current_time = time.time()
        delta_time = current_time - self.last_time
        self.last_time = current_time
        
        # Update panorama
        self.panorama.update(delta_time)
        
        # Update splash text
        self.splash.update(delta_time)
        
        # Animate buttons in
        if not self.buttons_animated_in:
            self.animation_time += delta_time
            if self.animation_time > 0.5:
                self.buttons_animated_in = True
        
        # Update UI elements
        for element in self.ui_elements:
            if hasattr(element, 'update'):
                element.update(delta_time)
    
    def render(self) -> None:
        """Render main menu."""
        # Create surface for rendering
        surface = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 255))
        
        # Render panorama background
        panorama = self.panorama.render(surface)
        
        # Apply vignette effect
        panorama = self._apply_vignette(panorama)
        
        # Clear and render
        self.renderer.clear()
        
        # Render logo (pixelated style)
        self._render_logo(surface)
        
        # Render splash text
        self._render_splash_text(surface)
        
        # Render menu buttons
        self._render_buttons(surface)
        
        # Render version text
        self.version_text.render(surface)
        
        # Render Mojang logo
        self.mojang_logo.render(surface)
    
    def _apply_vignette(self, image: Image.Image) -> Image.Image:
        """Apply vignette effect to image."""
        # Create vignette mask
        mask = Image.new('L', image.size, 0)
        draw = ImageDraw.Draw(mask)
        
        center_x, center_y = image.width // 2, image.height // 2
        max_dist = max(center_x, center_y)
        
        for y in range(image.height):
            for x in range(image.width):
                dist = math.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
                if dist < max_dist:
                    value = int(255 * (dist / max_dist) ** 0.5)
                    mask.putpixel((x, y), value)
        
        # Apply mask
        result = Image.composite(image, Image.new('RGBA', image.size, (0, 0, 0, 255)), mask)
        return result
    
    def _render_logo(self, surface: Image.Image) -> None:
        """Render Minecraft logo."""
        if self.logo_image is None:
            # Draw text logo as fallback
            draw = ImageDraw.Draw(surface)
            logo_text = "MINECRAFT"
            
            font = FontManager.get_title(64)
            
            # Draw shadow
            shadow_offset = 4
            bbox = font.getbbox(logo_text)
            text_width = bbox[2] - bbox[0]
            x = self.width // 2 - text_width // 2 + shadow_offset
            y = self.height // 4 + shadow_offset
            
            # Yellow/orange shadow
            draw.text((x - 2, y - 2), logo_text, font=font, fill=(100, 60, 0, 255))
            draw.text((x + 2, y + 2), logo_text, font=font, fill=(100, 60, 0, 255))
            
            # Main text
            x = self.width // 2 - text_width // 2
            y = self.height // 4
            
            # Multi-color logo
            colors = [
                (120, 120, 120, 255),  # Gray
                (100, 200, 100, 255),  # Green
                (80, 180, 80, 255),    # Darker green
            ]
            
            # Draw letter by letter
            char_width = text_width // len(logo_text)
            for i, char in enumerate(logo_text):
                color = colors[i % len(colors)]
                draw.text((x + i * char_width, y), char, font=font, fill=color)
            
            return
        
        # Draw image logo
        logo = self.logo_image.copy()
        
        # Scale logo
        target_width = min(400, self.width // 2)
        ratio = target_width / logo.width
        logo = logo.resize((target_width, int(logo.height * ratio)), Image.LANCZOS)
        
        # Position
        x = self.width // 2 - logo.width // 2
        y = self.height // 4 - logo.height // 2
        
        # Draw shadow
        shadow = logo.copy()
        shadow = ImageEnhance.Brightness(shadow).enhance(0.3)
        surface.paste(shadow, (x + 4, y + 4), shadow)
        
        # Draw logo
        surface.paste(logo, (x, y), logo)
    
    def _render_splash_text(self, surface: Image.Image) -> None:
        """Render animated splash text."""
        draw = ImageDraw.Draw(surface)
        
        x, y = self.splash.get_position()
        scale = self.splash.get_scale()
        
        # Get splash text
        text = self.splash.text
        bbox = self.splash_font.getbbox(text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Apply scale
        scaled_width = int(text_width * scale)
        scaled_height = int(text_height * scale)
        
        # Create temporary surface for splash
        splash_surface = Image.new('RGBA', (text_width, text_height), (0, 0, 0, 0))
        splash_draw = ImageDraw.Draw(splash_surface)
        
        # Draw yellow splash with shadow
        shadow_offset = 2
        splash_draw.text((shadow_offset, shadow_offset), text,
                        font=self.splash_font, fill=Color.TEXT_SHADOW)
        splash_draw.text((0, 0), text, font=self.splash_font,
                        fill=Color.SPLASH_YELLOW)
        
        # Scale and rotate
        scaled = splash_surface.resize((scaled_width, scaled_height), Image.LANCZOS)
        
        # Position
        draw_x = x
        draw_y = y - scaled_height // 2
        
        # Draw with slight rotation (simulated by offset)
        surface.paste(scaled, (draw_x, draw_y), scaled)
    
    def _render_buttons(self, surface: Image.Image) -> None:
        """Render menu buttons."""
        for element in self.ui_elements:
            if isinstance(element, Button):
                element.render(surface)
    
    def handle_event(self, event) -> bool:
        """Handle input events."""
        for element in reversed(self.ui_elements):
            if element.handle_event(event):
                return True
        return False
    
    def resize(self, width: int, height: int) -> None:
        """Handle window resize."""
        self.width = width
        self.height = height
        
        # Recreate panorama
        self.panorama = Panorama(width, height)
        
        # Update UI element positions
        self._init_ui()
        self._init_splash_text()
    
    def cleanup(self) -> None:
        """Cleanup menu resources."""
        TextureManager.clear_cache()
