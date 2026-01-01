#!/usr/bin/env python3
"""
Minecraft Clone - Python Edition
A high-performance Minecraft clone built with GLFW, PIL, and ModernGL.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.window import Window
from engine.renderer import Renderer
from ui.main_menu import MainMenu
from world.world import World
from utils.config import Config

def main():
    """Main entry point for the Minecraft clone."""
    # Load configuration
    config = Config()
    
    # Create window
    window = Window(
        title="Minecraft 1.0 (Python Edition)",
        width=config.get_int('width', 1280),
        height=config.get_int('height', 720),
        resizable=True,
        vsync=config.get_bool('vsync', True)
    )
    
    # Create renderer
    renderer = Renderer(window, fov=config.get_int('fov', 70))
    
    # Create main menu
    main_menu = MainMenu(window, renderer)
    
    # Main game loop
    running = True
    while running:
        # Handle input
        if window.should_close():
            running = False
        
        # Render
        main_menu.render()
        
        # Swap buffers
        window.swap_buffers()
        
        # Poll events
        window.poll_events()
    
    # Save configuration
    config.save()
    
    # Cleanup
    window.destroy()
    renderer.cleanup()

if __name__ == "__main__":
    main()
