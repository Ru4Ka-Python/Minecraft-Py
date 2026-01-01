"""
Configuration management module.
Handles video settings, controls, and game preferences.
"""

import os
import json
from typing import Any, Dict, Optional

class Config:
    """Configuration manager for game settings."""
    
    DEFAULT_CONFIG = {
        'width': 1280,
        'height': 720,
        'vsync': True,
        'fov': 70,
        'render_distance': 8,
        'smooth_lighting': True,
        'clouds': True,
        'particles': True,
        'key_attack': 0,
        'key_jump': 32,
        'key_drop': 0,
        'key_sneak': 161,
        'key_chat': 0,
        'key_inventory': 0,
        'sensitivity': 0.5,
        'mouse_sensitivity': 0.5,
        'auto_jump': True,
        'touch_enabled': False,
    }
    
    def __init__(self, config_path: str = None):
        """Initialize configuration manager."""
        if config_path is None:
            self.config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        else:
            self.config_path = config_path
        
        self.config: Dict[str, Any] = self.DEFAULT_CONFIG.copy()
        self.load()
    
    def load(self) -> None:
        """Load configuration from file."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
            except (json.JSONDecodeError, IOError):
                pass  # Use default config if file is corrupt or unreadable
    
    def save(self) -> None:
        """Save configuration to file."""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=4)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.config.get(key, default)
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Get an integer configuration value."""
        return int(self.get(key, default))
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """Get a float configuration value."""
        return float(self.get(key, default))
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get a boolean configuration value."""
        return bool(self.get(key, default))
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self.config[key] = value
    
    def reset(self) -> None:
        """Reset configuration to defaults."""
        self.config = self.DEFAULT_CONFIG.copy()
        self.save()
    
    def get_video_settings(self) -> Dict[str, Any]:
        """Get video settings as a dictionary."""
        return {
            'width': self.get_int('width'),
            'height': self.get_int('height'),
            'vsync': self.get_bool('vsync'),
            'fov': self.get_int('fov'),
            'render_distance': self.get_int('render_distance'),
            'smooth_lighting': self.get_bool('smooth_lighting'),
            'clouds': self.get_bool('clouds'),
            'particles': self.get_bool('particles'),
        }
    
    def set_video_settings(self, settings: Dict[str, Any]) -> None:
        """Apply video settings from a dictionary."""
        for key, value in settings.items():
            if key in self.config:
                self.config[key] = value
