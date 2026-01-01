"""
Entity system for Minecraft clone.
Base entity class and common functionality.
"""

from typing import Tuple, Optional, Dict, List
from dataclasses import dataclass, field
import numpy as np
import math


@dataclass
class EntityAttributes:
    """Base entity attributes."""
    # Movement
    speed: float = 0.1
    jump_strength: float = 0.5
    
    # Combat
    health: int = 1
    damage: int = 0
    armor: int = 0
    
    # Physics
    gravity: float = 0.02
    friction: float = 0.9
    knockback_resistance: float = 0.0
    
    # AI
    can_despawn: bool = True
    experience_reward: int = 0


class Entity:
    """Base entity class for all in-game entities."""
    
    def __init__(self, position: Tuple[float, float, float], attributes: EntityAttributes = None):
        """Initialize entity."""
        self.position = np.array(position, dtype=np.float32)
        self.velocity = np.zeros(3, dtype=np.float32)
        self.rotation = np.zeros(2, dtype=np.float32)  # yaw, pitch
        
        self.attributes = attributes if attributes else EntityAttributes()
        
        # State
        self.is_alive = True
        self.is_on_ground = False
        self.is_in_water = False
        self.is_in_lava = False
        
        # Collision
        self.width = 0.6
        self.height = 1.8
        
        # Visual
        self.model_matrix = np.eye(4, dtype=np.float32)
        self._update_model_matrix()
        
        # Shadow
        self.shadow_scale = 1.0
        
        # Metadata
        self.entity_id = id(self)
        self.entity_type = 'base'
    
    def _update_model_matrix(self) -> None:
        """Update the model matrix from position and rotation."""
        
        # Translation
        self.model_matrix[0, 3] = self.position[0]
        self.model_matrix[1, 3] = self.position[1]
        self.model_matrix[2, 3] = self.position[2]
        
        # Rotation (simplified)
        yaw = self.rotation[0]
        cos_yaw = math.cos(yaw)
        sin_yaw = math.sin(yaw)
        
        rotation_matrix = np.array([
            [cos_yaw, 0, sin_yaw, 0],
            [0, 1, 0, 0],
            [-sin_yaw, 0, cos_yaw, 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)
        
        self.model_matrix = rotation_matrix @ self.model_matrix
    
    def get_model_matrix(self) -> np.ndarray:
        """Get the model matrix for rendering."""
        return self.model_matrix
    
    def update(self, delta_time: float, world) -> None:
        """Update entity state."""
        # Apply gravity
        if not self.is_in_water and not self.is_in_lava:
            self.velocity[1] -= self.attributes.gravity
        
        # Apply friction
        self.velocity[0] *= self.attributes.friction
        self.velocity[2] *= self.attributes.friction
        
        # Apply velocity
        self.position += self.velocity
        
        # Handle collisions
        self._handle_collisions(world)
        
        # Check fluids
        self._check_fluids(world)
        
        # Update model matrix
        self._update_model_matrix()
        
        # Update shadow (shrinks when entity rises)
        ground_level = self._get_ground_level(world)
        distance = self.position[1] - ground_level
        self.shadow_scale = max(0.5, min(1.0, 1.0 - distance * 0.1))
        
        # Update rotation to face movement direction
        if np.linalg.norm(self.velocity) > 0.01:
            target_yaw = math.atan2(self.velocity[0], self.velocity[2])
            self.rotation[0] += (target_yaw - self.rotation[0]) * 0.1
    
    def _handle_collisions(self, world) -> None:
        """Handle collision with blocks."""
        # Simplified collision detection
        hw = self.width / 2
        
        # Check feet
        feet_y = self.position[1]
        if world.get_block(int(self.position[0]), int(feet_y), int(self.position[2])):
            self.position[1] = math.ceil(feet_y)
            self.velocity[1] = 0
            self.is_on_ground = True
        
        # Check head
        head_y = self.position[1] + self.height
        if world.get_block(int(self.position[0]), int(head_y), int(self.position[2])):
            self.position[1] = math.floor(head_y) - self.height
            self.velocity[1] = 0
    
    def _check_fluids(self, world) -> None:
        """Check if entity is in water or lava."""
        block = world.get_block(int(self.position[0]), int(self.position[1] + 0.5), int(self.position[2]))
        
        if block is None:
            self.is_in_water = False
            self.is_in_lava = False
            return
        
        if block.block_type.value == 8:  # Water
            self.is_in_water = True
            self.is_in_lava = False
        elif block.block_type.value == 10:  # Lava
            self.is_in_water = False
            self.is_in_lava = True
        else:
            self.is_in_water = False
            self.is_in_lava = False
    
    def _get_ground_level(self, world) -> float:
        """Get the ground level below the entity."""
        for y in range(int(self.position[1]), 0, -1):
            block = world.get_block(int(self.position[0]), y, int(self.position[2]))
            if block is not None and block.is_solid():
                return y + 1
        return 0
    
    def take_damage(self, amount: int, source: str = None) -> None:
        """Take damage."""
        self.attributes.health -= amount
        
        if self.attributes.health <= 0:
            self.die(source)
    
    def die(self, source: str = None) -> None:
        """Entity death."""
        self.is_alive = False
    
    def is_visible(self, camera) -> bool:
        """Check if entity is visible to camera."""
        direction = self.position - camera.position
        distance = np.linalg.norm(direction)
        
        if distance > 100:  # Max render distance
            return False
        
        # Simple dot product check
        view_dir = camera.get_direction()
        dot = np.dot(view_dir, direction / distance)
        
        return dot > 0.5  # Within field of view
    
    def get_look_vector(self) -> np.ndarray:
        """Get look direction vector."""
        yaw, pitch = self.rotation
        return np.array([
            math.sin(yaw) * math.cos(pitch),
            math.sin(pitch),
            math.cos(yaw) * math.cos(pitch)
        ], dtype=np.float32)
    
    def get_bounding_box(self) -> Tuple[np.ndarray, np.ndarray]:
        """Get entity bounding box."""
        hw = self.width / 2
        return (
            self.position - np.array([hw, 0, hw]),
            self.position + np.array([hw, self.height, hw])
        )
    
    def push(self, force: np.ndarray) -> None:
        """Apply knockback force."""
        self.velocity += force * (1 - self.attributes.knockback_resistance)
    
    def spawn_particles(self, particle_system, particle_type: str, count: int = 5) -> None:
        """Spawn death/hurt particles."""
        for _ in range(count):
            offset = np.random.uniform(-0.2, 0.2, 3)
            particle_system.spawn(
                self.position + offset,
                velocity=np.random.uniform(-0.1, 0.1, 3),
                particle_type=particle_type
            )


class ItemEntity(Entity):
    """Dropped item entity."""
    
    def __init__(self, position: Tuple[float, float, float], item, count: int = 1):
        """Initialize item entity."""
        super().__init__(position)
        
        self.item = item
        self.count = count
        
        # Pickup delay
        self.pickup_delay = 40
    
    def update(self, delta_time: float, world) -> None:
        """Update item entity."""
        super().update(delta_time, world)
        
        # Decrease pickup delay
        if self.pickup_delay > 0:
            self.pickup_delay -= 1
        
        # Magnetic effect when player is close
        player_pos = world.player.position if world.player else None
        if player_pos is not None and self.pickup_delay <= 0:
            direction = player_pos - self.position
            distance = np.linalg.norm(direction)
            
            if distance < 3.0:
                # Move towards player
                self.position += direction / distance * 0.1
                self.velocity *= 0.9
    
    def get_model_matrix(self) -> np.ndarray:
        """Get spinning model matrix."""
        matrix = super().get_model_matrix()
        
        # Add rotation animation
        yaw = self.entity_id % 360 / 180 * math.pi
        cos_yaw = math.cos(yaw)
        sin_yaw = math.sin(yaw)
        
        rotation = np.array([
            [cos_yaw, 0, sin_yaw, 0],
            [0, 1, 0, 0],
            [-sin_yaw, 0, cos_yaw, 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)
        
        return rotation @ matrix


class ExperienceOrb(Entity):
    """Experience orb entity."""
    
    def __init__(self, position: Tuple[float, float, float], value: int = 1):
        """Initialize experience orb."""
        super().__init__(position)
        
        self.value = value
        self.attributes.speed = 0.15
    
    def update(self, delta_time: float, world) -> None:
        """Update experience orb."""
        super().update(delta_time, world)
        
        # Move towards nearby player
        player_pos = world.player.position if world.player else None
        if player_pos is not None:
            direction = player_pos - self.position
            distance = np.linalg.norm(direction)
            
            if distance < 4.0:
                self.position += direction / distance * self.attributes.speed


class Arrow(Entity):
    """Arrow projectile entity."""
    
    def __init__(self, position: Tuple[float, float, float], direction: np.ndarray, power: float = 1.0):
        """Initialize arrow."""
        super().__init__(position)
        
        self.velocity = direction * power * 1.5
        self.attributes.gravity = 0.015
        self.is_stuck = False
    
    def update(self, delta_time: float, world) -> None:
        """Update arrow."""
        if self.is_stuck:
            return
        
        super().update(delta_time, world)
        
        # Check for collision
        block = world.get_block(
            int(self.position[0]),
            int(self.position[1]),
            int(self.position[2])
        )
        
        if block is not None and block.is_solid():
            self.is_stuck = True
            self.velocity = np.zeros(3)
