"""
Window management module using GLFW.
Provides cross-platform window creation and event handling.
"""

import glfw
import time
from typing import Callable, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

class KeyState(Enum):
    """Key state enumeration."""
    RELEASE = 0
    PRESS = 1
    REPEAT = 2

@dataclass
class WindowConfig:
    """Window configuration."""
    title: str = "Minecraft Clone"
    width: int = 1280
    height: int = 720
    resizable: bool = True
    vsync: bool = True
    samples: int = 0
    debug: bool = False

class Window:
    """GLFW window wrapper for Minecraft clone."""
    
    _instances = []
    
    def __init__(self, config: WindowConfig = None, **kwargs):
        """Initialize GLFW window."""
        Window._instances.append(self)
        
        # Apply configuration
        if config is None:
            config = WindowConfig(**kwargs)
        self._config = config
        self._title = config.title
        self._width = config.width
        self._height = config.height
        
        # Initialize GLFW
        if not glfw.init():
            raise RuntimeError("Failed to initialize GLFW")
        
        # Configure GLFW window hints
        self._configure_hints(config)
        
        # Create window
        self._window = glfw.create_window(
            config.width, config.height,
            config.title,
            None, None
        )
        
        if not self._window:
            glfw.terminate()
            raise RuntimeError("Failed to create GLFW window")
        
        # Make context current
        glfw.make_context_current(self._window)
        
        # Enable v-sync
        if config.vsync:
            glfw.swap_interval(1)
        
        # Initialize key states
        self._key_states: Dict[int, KeyState] = {}
        self._mouse_position = (0.0, 0.0)
        self._mouse_delta = (0.0, 0.0)
        self._mouse_buttons = {}
        self._mouse_captured = False
        
        # Callbacks
        self._key_callbacks = []
        self._mouse_callbacks = []
        self._resize_callbacks = []
        self._close_callbacks = []
        
        self._setup_callbacks()
        
        # Timing
        self._last_time = time.time()
        self._delta_time = 0.0
    
    def _configure_hints(self, config: WindowConfig) -> None:
        """Configure GLFW window hints."""
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.SAMPLES, config.samples)
        glfw.window_hint(glfw.RESIZABLE, glfw.TRUE if config.resizable else glfw.FALSE)
        glfw.window_hint(glfw.DOUBLEBUFFER, glfw.TRUE)
    
    def _setup_callbacks(self) -> None:
        """Setup GLFW callbacks."""
        glfw.set_key_callback(self._window, self._on_key)
        glfw.set_mouse_button_callback(self._window, self._on_mouse_button)
        glfw.set_cursor_pos_callback(self._window, self._on_mouse_move)
        glfw.set_window_size_callback(self._window, self._on_resize)
        glfw.set_window_close_callback(self._window, self._on_close)
        glfw.set_scroll_callback(self._window, self._on_scroll)
    
    def _on_key(self, window, key: int, scancode: int, action: int, mods: int) -> None:
        """Handle key event."""
        self._key_states[key] = KeyState(action)
        for callback in self._key_callbacks:
            callback(key, scancode, action, mods)
    
    def _on_mouse_button(self, window, button: int, action: int, mods: int) -> None:
        """Handle mouse button event."""
        self._mouse_buttons[button] = action
        for callback in self._mouse_callbacks:
            callback(button, action, mods)
    
    def _on_mouse_move(self, window, xpos: float, ypos: float) -> None:
        """Handle mouse movement."""
        self._mouse_delta = (xpos - self._mouse_position[0], ypos - self._mouse_position[1])
        self._mouse_position = (xpos, ypos)
        for callback in self._mouse_callbacks:
            callback(xpos, ypos)
    
    def _on_resize(self, window, width: int, height: int) -> None:
        """Handle window resize."""
        self._width = width
        self._height = height
        for callback in self._resize_callbacks:
            callback(width, height)
    
    def _on_close(self, window) -> None:
        """Handle window close."""
        for callback in self._close_callbacks:
            callback()
    
    def _on_scroll(self, window, xoffset: float, yoffset: float) -> None:
        """Handle scroll event."""
        pass  # Can be extended for zoom functionality
    
    def add_key_callback(self, callback: Callable) -> None:
        """Add a key event callback."""
        self._key_callbacks.append(callback)
    
    def add_mouse_callback(self, callback: Callable) -> None:
        """Add a mouse event callback."""
        self._mouse_callbacks.append(callback)
    
    def add_resize_callback(self, callback: Callable) -> None:
        """Add a resize event callback."""
        self._resize_callbacks.append(callback)
    
    def add_close_callback(self, callback: Callable) -> None:
        """Add a close event callback."""
        self._close_callbacks.append(callback)
    
    def should_close(self) -> bool:
        """Check if window should close."""
        return bool(glfw.window_should_close(self._window))
    
    def swap_buffers(self) -> None:
        """Swap front and back buffers."""
        glfw.swap_buffers(self._window)
    
    def poll_events(self) -> None:
        """Poll for pending events."""
        glfw.poll_events()
        self._mouse_delta = (0.0, 0.0)
    
    def get_key(self, key: int) -> KeyState:
        """Get the state of a key."""
        return self._key_states.get(key, KeyState.RELEASE)
    
    def is_key_pressed(self, key: int) -> bool:
        """Check if a key is currently pressed."""
        return self._key_states.get(key) == KeyState.PRESS
    
    def is_key_held(self, key: int) -> bool:
        """Check if a key is being held down (pressed or repeating)."""
        state = self._key_states.get(key)
        return state in (KeyState.PRESS, KeyState.REPEAT)
    
    def get_mouse_position(self) -> tuple:
        """Get current mouse position."""
        return self._mouse_position
    
    def get_mouse_delta(self) -> tuple:
        """Get mouse delta since last frame."""
        return self._mouse_delta
    
    def is_mouse_button_pressed(self, button: int) -> bool:
        """Check if a mouse button is pressed."""
        return self._mouse_buttons.get(button, 0) == 1
    
    def capture_mouse(self) -> None:
        """Capture mouse cursor for FPS controls."""
        glfw.set_input_mode(self._window, glfw.CURSOR, glfw.CURSOR_DISABLED)
        self._mouse_captured = True
    
    def release_mouse(self) -> None:
        """Release captured mouse cursor."""
        glfw.set_input_mode(self._window, glfw.CURSOR, glfw.CURSOR_NORMAL)
        self._mouse_captured = False
    
    def is_mouse_captured(self) -> bool:
        """Check if mouse is captured."""
        return self._mouse_captured
    
    def set_mouse_position(self, x: float, y: float) -> None:
        """Set mouse position."""
        glfw.set_cursor_pos(self._window, x, y)
        self._mouse_position = (x, y)
    
    def get_size(self) -> tuple:
        """Get window size."""
        return (self._width, self._height)
    
    def get_width(self) -> int:
        """Get window width."""
        return self._width
    
    def get_height(self) -> int:
        """Get window height."""
        return self._height
    
    def get_aspect_ratio(self) -> float:
        """Get window aspect ratio."""
        return self._width / self._height if self._height > 0 else 1.0
    
    def set_title(self, title: str) -> None:
        """Set window title."""
        self._title = title
        glfw.set_window_title(self._window, title)
    
    def set_size(self, width: int, height: int) -> None:
        """Set window size."""
        self._width = width
        self._height = height
        glfw.set_window_size(self._window, width, height)
    
    def maximize(self) -> None:
        """Maximize window."""
        glfw.maximize_window(self._window)
    
    def minimize(self) -> None:
        """Minimize window."""
        glfw.iconify_window(self._window)
    
    def get_window(self):
        """Get the raw GLFW window pointer."""
        return self._window
    
    def get_framebuffer_size(self) -> tuple:
        """Get framebuffer size (for retina displays)."""
        width, height = glfw.get_framebuffer_size(self._window)
        return (width, height)
    
    def get_delta_time(self) -> float:
        """Get time since last frame."""
        return self._delta_time
    
    def update(self) -> None:
        """Update window state."""
        current_time = time.time()
        self._delta_time = current_time - self._last_time
        self._last_time = current_time
    
    def destroy(self) -> None:
        """Destroy window and cleanup GLFW."""
        if self in Window._instances:
            Window._instances.remove(self)
        
        if self._window:
            glfw.destroy_window(self._window)
        
        if not Window._instances:
            glfw.terminate()
    
    @classmethod
    def create(cls, title: str = "Minecraft Clone", width: int = 1280, height: int = 720, **kwargs) -> 'Window':
        """Create a window with specified parameters."""
        config = WindowConfig(title=title, width=width, height=height, **kwargs)
        return cls(config)
