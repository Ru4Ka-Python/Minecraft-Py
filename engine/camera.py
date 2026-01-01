"""
Camera module for 3D rendering.
Handles camera position, rotation, and view/projection matrices.
"""

import math
import numpy as np
from typing import Tuple
from dataclasses import dataclass

@dataclass
class CameraConfig:
    """Camera configuration."""
    fov: float = 70.0
    near: float = 0.1
    far: float = 1000.0
    sensitivity: float = 0.1
    movement_speed: float = 10.0
    sprint_multiplier: float = 1.5

class Camera:
    """First-person camera for Minecraft-style rendering."""
    
    def __init__(self, position: Tuple[float, float, float] = (0, 64, 0), config: CameraConfig = None):
        """Initialize camera."""
        self.position = np.array(position, dtype=np.float32)
        self.rotation = np.array([0.0, 0.0], dtype=np.float32)  # yaw, pitch
        self.velocity = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        
        if config is None:
            config = CameraConfig()
        self.config = config
        
        # Build matrices
        self.view_matrix = np.eye(4, dtype=np.float32)
        self.projection_matrix = np.eye(4, dtype=np.float32)
        self.model_matrix = np.eye(4, dtype=np.float32)
        
        self._update_projection()
        self._update_view()
    
    def _update_projection(self) -> None:
        """Update projection matrix based on FOV."""
        fov = self.config.fov
        aspect = 16.0 / 9.0  # Default aspect
        near = self.config.near
        far = self.config.far
        
        f = 1.0 / math.tan(math.radians(fov) / 2)
        
        self.projection_matrix = np.array([
            [f / aspect, 0, 0, 0],
            [0, f, 0, 0],
            [0, 0, (far + near) / (near - far), -1],
            [0, 0, (2 * far * near) / (near - far), 0]
        ], dtype=np.float32)
    
    def _update_view(self) -> None:
        """Update view matrix based on position and rotation."""
        yaw, pitch = self.rotation
        
        # Calculate forward vector
        cos_yaw = math.cos(yaw)
        sin_yaw = math.sin(yaw)
        cos_pitch = math.cos(pitch)
        sin_pitch = math.sin(pitch)
        
        forward = np.array([
            cos_yaw * cos_pitch,
            sin_pitch,
            sin_yaw * cos_pitch
        ], dtype=np.float32)
        
        # Normalize
        forward = forward / np.linalg.norm(forward)
        
        # Calculate right vector
        right = np.array([
            math.sin(yaw - math.pi / 2),
            0,
            math.cos(yaw - math.pi / 2)
        ], dtype=np.float32)
        
        # Calculate up vector
        up = np.cross(right, forward)
        
        # Build view matrix
        self.view_matrix = np.eye(4, dtype=np.float32)
        self.view_matrix[0, 0:3] = right
        self.view_matrix[1, 0:3] = up
        self.view_matrix[2, 0:3] = -forward
        self.view_matrix[0, 3] = -np.dot(right, self.position)
        self.view_matrix[1, 3] = -np.dot(up, self.position)
        self.view_matrix[2, 3] = np.dot(forward, self.position)
    
    def set_fov(self, fov: float) -> None:
        """Set field of view (45-90 degrees)."""
        self.config.fov = max(45, min(90, fov))
        self._update_projection()
    
    def get_fov(self) -> float:
        """Get current FOV."""
        return self.config.fov
    
    def rotate(self, delta_x: float, delta_y: float) -> None:
        """Rotate camera by delta amounts."""
        yaw, pitch = self.rotation
        
        yaw += delta_x * self.config.sensitivity
        pitch -= delta_y * self.config.sensitivity
        
        # Clamp pitch to avoid gimbal lock
        pitch = max(-math.pi / 2 + 0.01, min(math.pi / 2 - 0.01, pitch))
        
        self.rotation = np.array([yaw, pitch], dtype=np.float32)
        self._update_view()
    
    def set_rotation(self, yaw: float, pitch: float) -> None:
        """Set rotation directly."""
        pitch = max(-math.pi / 2 + 0.01, min(math.pi / 2 - 0.01, pitch))
        self.rotation = np.array([yaw, pitch], dtype=np.float32)
        self._update_view()
    
    def move(self, direction: str, delta_time: float) -> None:
        """Move camera in a direction."""
        speed = self.config.movement_speed * delta_time
        
        yaw = self.rotation[0]
        
        # Forward/backward
        if direction == 'forward':
            self.position[0] += math.sin(yaw) * speed
            self.position[2] += math.cos(yaw) * speed
        elif direction == 'backward':
            self.position[0] -= math.sin(yaw) * speed
            self.position[2] -= math.cos(yaw) * speed
        
        # Left/right
        if direction == 'left':
            self.position[0] -= math.cos(yaw) * speed
            self.position[2] += math.sin(yaw) * speed
        elif direction == 'right':
            self.position[0] += math.cos(yaw) * speed
            self.position[2] -= math.sin(yaw) * speed
        
        # Up/down
        if direction == 'up':
            self.position[1] += speed
        elif direction == 'down':
            self.position[1] -= speed
        
        self._update_view()
    
    def move_direction(self, direction: np.ndarray, delta_time: float, sprint: bool = False) -> None:
        """Move camera in a direction vector."""
        speed = self.config.movement_speed * delta_time
        if sprint:
            speed *= self.config.sprint_multiplier
        
        self.position += direction * speed
        self._update_view()
    
    def get_direction(self) -> np.ndarray:
        """Get forward direction vector."""
        yaw, pitch = self.rotation
        
        cos_yaw = math.cos(yaw)
        sin_yaw = math.sin(yaw)
        cos_pitch = math.cos(pitch)
        sin_pitch = math.sin(pitch)
        
        return np.array([
            cos_yaw * cos_pitch,
            sin_pitch,
            sin_yaw * cos_pitch
        ], dtype=np.float32)
    
    def get_look_vector(self) -> np.ndarray:
        """Get normalized look direction."""
        return self.get_direction()
    
    def get_pitch(self) -> float:
        """Get pitch angle."""
        return self.rotation[1]
    
    def get_yaw(self) -> float:
        """Get yaw angle."""
        return self.rotation[0]
    
    def get_position(self) -> np.ndarray:
        """Get camera position."""
        return self.position.copy()
    
    def set_position(self, position: Tuple[float, float, float]) -> None:
        """Set camera position."""
        self.position = np.array(position, dtype=np.float32)
        self._update_view()
    
    def update(self, delta_time: float) -> None:
        """Update camera (for physics/movement)."""
        pass  # Can be extended for smooth camera movements
    
    def get_frustum_planes(self) -> List[np.ndarray]:
        """Get frustum planes for culling."""
        # Returns 6 planes: left, right, top, bottom, near, far
        # Each plane is represented by (normal, distance)
        planes = []
        
        # Simplified frustum extraction
        # This would need full implementation for proper culling
        return planes
    
    def is_point_in_frustum(self, point: np.ndarray) -> bool:
        """Check if a point is inside the view frustum."""
        # Simplified check - would need full frustum planes
        direction = self.get_direction()
        to_point = point - self.position
        distance = np.linalg.norm(to_point)
        
        # Simple distance check
        return distance < self.config.far
    
    def get_ray(self, screen_x: float, screen_y: float, aspect: float = 16.0/9.0) -> np.ndarray:
        """Get a ray from camera through screen point."""
        # Normalized device coordinates
        ndc_x = (2.0 * screen_x / 1.0) - 1.0
        ndc_y = 1.0 - (2.0 * screen_y / 1.0)
        
        yaw, pitch = self.rotation
        
        # Ray direction
        ray = np.array([
            ndc_x * aspect * math.tan(math.radians(self.config.fov) / 2),
            ndc_y * math.tan(math.radians(self.config.fov) / 2),
            -1.0
        ], dtype=np.float32)
        
        # Rotate ray by camera rotation
        cos_yaw = math.cos(yaw)
        sin_yaw = math.sin(yaw)
        cos_pitch = math.cos(pitch)
        sin_pitch = math.sin(pitch)
        
        rotation_matrix = np.array([
            [cos_yaw, sin_yaw * sin_pitch],
            [0, cos_pitch],
            [sin_yaw, -cos_yaw * sin_pitch]
        ], dtype=np.float32)
        
        # This is a simplified ray calculation
        return self.get_direction()
    
    def get_pitch_yaw_from_vector(self, direction: np.ndarray) -> Tuple[float, float]:
        """Calculate pitch and yaw from a direction vector."""
        direction = direction / np.linalg.norm(direction)
        
        yaw = math.atan2(direction[0], direction[2])
        pitch = math.asin(direction[1])
        
        return yaw, pitch
    
    def set_sprint_fov(self, sprinting: bool) -> None:
        """Apply FOV change when sprinting."""
        if sprinting:
            self.set_fov(self.config.fov * 1.1)  # Slight FOV increase
        else:
            self.set_fov(self.config.fov)  # Reset to normal
    
    def reset(self) -> None:
        """Reset camera to default state."""
        self.position = np.array([0, 64, 0], dtype=np.float32)
        self.rotation = np.array([0.0, 0.0], dtype=np.float32)
        self.velocity = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self._update_view()
