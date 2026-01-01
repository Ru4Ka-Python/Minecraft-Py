"""
Player controller for Minecraft clone.
Handles player movement, physics, collision, and input.
"""

import math
import numpy as np
from typing import Tuple, Optional, Dict
from dataclasses import dataclass, field

from engine.camera import Camera
from world.blocks import BlockType


@dataclass
class PlayerState:
    """Player state data."""
    position: Tuple[float, float, float] = (0, 64, 0)
    velocity: Tuple[float, float, float] = (0, 0, 0)
    yaw: float = 0.0
    pitch: float = 0.0
    
    # Player attributes
    health: int = 20
    hunger: int = 20
    saturation: float = 5.0
    
    # Armor
    armor: int = 0
    
    # Experience
    xp_level: int = 0
    xp_progress: float = 0.0
    
    # Status effects
    effects: Dict[str, int] = field(default_factory=dict)
    
    # Game mode
    is_creative: bool = False
    is_spectator: bool = False
    
    # Flags
    is_sneaking: bool = False
    is_sprinting: bool = False
    is_flying: bool = False
    on_ground: bool = False
    in_water: bool = False
    in_lava: bool = False
    is_sleeping: bool = False


class PhysicsEngine:
    """Physics engine for player movement and collision."""
    
    GRAVITY = 20.0
    TERMINAL_VELOCITY = 80.0
    
    # Movement speeds (blocks per second)
    WALK_SPEED = 4.317
    SPRINT_SPEED = 5.612
    SNEAK_SPEED = 1.308
    FLY_SPEED = 10.0
    
    # Jump velocities
    JUMP_VELOCITY = 8.0
    
    # Player dimensions
    PLAYER_WIDTH = 0.6
    PLAYER_HEIGHT = 1.8
    PLAYER_EYE_HEIGHT = 1.62
    
    def __init__(self, world):
        """Initialize physics engine."""
        self.world = world
    
    def update(self, player, delta_time: float) -> None:
        """Update player physics."""
        if player.state.is_spectator:
            return
        
        # Apply gravity
        if not player.state.is_flying:
            self._apply_gravity(player, delta_time)
        
        # Apply velocity
        self._apply_velocity(player, delta_time)
        
        # Handle collisions
        self._handle_collisions(player, delta_time)
        
        # Check water/lava
        self._check_fluids(player)
    
    def _apply_gravity(self, player, delta_time: float) -> None:
        """Apply gravity to player."""
        if player.state.in_water or player.state.in_lava:
            # Reduced gravity in water
            gravity = self.GRAVITY * 0.2
        else:
            gravity = self.GRAVITY
        
        # Apply gravity
        vx, vy, vz = player.state.velocity
        vy -= gravity * delta_time
        
        # Clamp terminal velocity
        if vy < -self.TERMINAL_VELOCITY:
            vy = -self.TERMINAL_VELOCITY
        
        player.state.velocity = (vx, vy, vz)
    
    def _apply_velocity(self, player, delta_time: float) -> None:
        """Apply velocity to position."""
        vx, vy, vz = player.state.velocity
        
        # Apply horizontal velocity
        px, py, pz = player.state.position
        px += vx * delta_time
        pz += vz * delta_time
        py += vy * delta_time
        
        player.state.position = (px, py, pz)
    
    def _handle_collisions(self, player, delta_time: float) -> None:
        """Handle collision detection and response."""
        px, py, pz = player.state.position
        vx, vy, vz = player.state.velocity
        
        # Check collision in each axis
        collision = self._check_collision(player, px, py, pz)
        
        # X axis
        if collision:
            player.state.velocity = (0, vy, vz)
            vx = 0
        
        # Z axis
        collision = self._check_collision(player, px, py, pz)
        if collision:
            player.state.velocity = (vx, vy, 0)
            vz = 0
        
        # Y axis
        py_collision = self._check_vertical_collision(player, px, py, pz)
        
        if py_collision == 'ground':
            player.state.on_ground = True
            if vy < 0:
                player.state.velocity = (vx, 0, vz)
                vy = 0
        elif py_collision == 'ceiling':
            if vy > 0:
                player.state.velocity = (vx, 0, vz)
                vy = 0
        else:
            player.state.on_ground = False
    
    def _check_collision(self, player, x: float, y: float, z: float) -> bool:
        """Check collision at position."""
        hw = self.PLAYER_WIDTH / 2
        
        # Check all corner points
        for dx in (-hw, hw):
            for dz in (-hw, hw):
                for dy in (0, self.PLAYER_HEIGHT - 0.1):
                    block = self.world.get_block(int(x + dx), int(y + dy), int(z + dz))
                    if block is not None and block.is_solid():
                        return True
        
        return False
    
    def _check_vertical_collision(self, player, x: float, y: float, z: float) -> Optional[str]:
        """Check vertical collision at position."""
        hw = self.PLAYER_WIDTH / 2
        
        # Check feet
        for dx in (-hw, hw):
            for dz in (-hw, hw):
                block = self.world.get_block(int(x + dx), int(y), int(z + dz))
                if block is not None and block.is_solid():
                    return 'ground'
        
        # Check head
        for dx in (-hw, hw):
            for dz in (-hw, hw):
                block = self.world.get_block(int(x + dx), int(y + self.PLAYER_HEIGHT), int(z + dz))
                if block is not None and block.is_solid():
                    return 'ceiling'
        
        return None
    
    def _check_fluids(self, player) -> None:
        """Check if player is in water or lava."""
        px, py, pz = player.state.position
        
        # Check at eye level
        eye_y = py + self.PLAYER_EYE_HEIGHT
        
        block = self.world.get_block(int(px), int(eye_y), int(pz))
        
        if block is None:
            player.state.in_water = False
            player.state.in_lava = False
            return
        
        if block.block_type == BlockType.WATER:
            player.state.in_water = True
            player.state.in_lava = False
        elif block.block_type == BlockType.LAVA:
            player.state.in_water = False
            player.state.in_lava = True
        else:
            player.state.in_water = False
            player.state.in_lava = False
    
    def get_speed(self, player) -> float:
        """Get current movement speed."""
        if player.state.is_sneaking:
            return self.SNEAK_SPEED
        elif player.state.is_sprinting:
            return self.SPRINT_SPEED
        elif player.state.is_flying:
            return self.FLY_SPEED
        else:
            return self.WALK_SPEED
    
    def can_jump(self, player) -> bool:
        """Check if player can jump."""
        if player.state.is_flying:
            return True
        
        if player.state.in_water:
            return True
        
        return player.state.on_ground
    
    def jump(self, player) -> None:
        """Make player jump."""
        if self.can_jump(player):
            vx, vy, vz = player.state.velocity
            if player.state.in_water:
                vy = self.JUMP_VELOCITY * 0.5
            else:
                vy = self.JUMP_VELOCITY
            player.state.velocity = (vx, vy, vz)
            player.state.on_ground = False


class Player:
    """Player entity controller."""
    
    def __init__(self, world, position: Tuple[float, float, float] = (0, 64, 0)):
        """Initialize player."""
        self.world = world
        self.state = PlayerState(position=position)
        
        # Camera
        self.camera = Camera(
            position=position,
            config=CameraConfig(sensitivity=0.1)
        )
        
        # Physics
        self.physics = PhysicsEngine(world)
        
        # Inventory
        self.inventory = Inventory()
        
        # Cooldowns
        self.attack_cooldown = 0.0
        self.use_cooldown = 0.0
        
        # Connection status
        self.is_connected = True
    
    def update(self, delta_time: float) -> None:
        """Update player state."""
        # Update physics
        self.physics.update(self, delta_time)
        
        # Update camera position
        self.camera.set_position(self.state.position)
        
        # Update cooldowns
        if self.attack_cooldown > 0:
            self.attack_cooldown -= delta_time
        if self.use_cooldown > 0:
            self.use_cooldown -= delta_time
        
        # Update hunger
        if self.state.is_sprinting and self._is_moving():
            self.state.hunger -= delta_time * 0.1
        
        # Check fall damage
        self._check_fall_damage()
        
        # Update effects
        self._update_effects(delta_time)
    
    def _is_moving(self) -> bool:
        """Check if player is moving."""
        vx, vy, vz = self.state.velocity
        return abs(vx) > 0.1 or abs(vz) > 0.1
    
    def _check_fall_damage(self) -> None:
        """Check and apply fall damage."""
        vx, vy, vz = self.state.velocity
        
        if not self.state.on_ground and vy < -10:
            # Falling damage
            damage = int(abs(vy) - 3)
            if damage > 0:
                self.state.health -= damage
    
    def _update_effects(self, delta_time: float) -> None:
        """Update status effects."""
        for effect, duration in list(self.state.effects.items()):
            duration -= delta_time
            if duration <= 0:
                del self.state.effects[effect]
            else:
                self.state.effects[effect] = duration
    
    def move(self, direction: str, delta_time: float) -> None:
        """Move player in a direction."""
        speed = self.physics.get_speed(self)
        
        if self.state.is_sprinting:
            speed *= 1.1  # Slight FOV increase
        
        # Apply movement based on camera direction
        forward = self.camera.get_direction()
        
        # Project to horizontal plane
        forward_y = forward[1]
        forward = np.array([forward[0], 0, forward[2]])
        forward = forward / np.linalg.norm(forward)
        
        # Right vector
        right = np.array([-forward[2], 0, forward[0]])
        
        vx, vy, vz = self.state.velocity
        
        if direction == 'forward':
            vx += forward[0] * speed * delta_time
            vz += forward[2] * speed * delta_time
        elif direction == 'backward':
            vx -= forward[0] * speed * delta_time
            vz -= forward[2] * speed * delta_time
        elif direction == 'left':
            vx -= right[0] * speed * delta_time
            vz -= right[2] * speed * delta_time
        elif direction == 'right':
            vx += right[0] * speed * delta_time
            vz += right[2] * speed * delta_time
        
        self.state.velocity = (vx, vy, vz)
    
    def rotate(self, delta_x: float, delta_y: float) -> None:
        """Rotate player view."""
        self.camera.rotate(delta_x, delta_y)
        self.state.yaw = self.camera.get_yaw()
        self.state.pitch = self.camera.get_pitch()
    
    def jump(self) -> None:
        """Make player jump."""
        self.physics.jump(self)
    
    def set_sneaking(self, sneaking: bool) -> None:
        """Set sneaking state."""
        self.state.is_sneaking = sneaking
    
    def set_sprinting(self, sprinting: bool) -> None:
        """Set sprinting state."""
        self.state.is_sprinting = sprinting
    
    def attack(self) -> None:
        """Attack with held item."""
        if self.attack_cooldown > 0:
            return
        
        # Set cooldown
        self.attack_cooldown = 0.5
        
        # Get look direction
        direction = self.camera.get_direction()
        
        # Raycast for entities
        hit_entity = self._raycast_entities(direction, 3.0)
        
        if hit_entity:
            hit_entity.take_damage(1)
    
    def use_item(self) -> None:
        """Use (right-click) with held item."""
        if self.use_cooldown > 0:
            return
        
        self.use_cooldown = 0.5
        
        # Get look direction and position
        direction = self.camera.get_direction()
        position = np.array(self.state.position)
        
        # Eye position
        eye_pos = position + np.array([0, 1.62, 0])
        
        # Raycast for block
        hit_block = self._raycast_blocks(eye_pos, direction, 4.5)
        
        if hit_block:
            x, y, z, face = hit_block
            self._interact_with_block(x, y, z, face)
    
    def _raycast_blocks(self, start: np.ndarray, direction: np.ndarray, max_distance: float):
        """Raycast for blocks."""
        step = 0.1
        pos = start.copy()
        
        for _ in range(int(max_distance / step)):
            pos += direction * step
            
            x, y, z = int(pos[0]), int(pos[1]), int(pos[2])
            
            block = self.world.get_block(x, y, z)
            
            if block is not None and block.is_solid():
                return (x, y, z, None)
        
        return None
    
    def _raycast_entities(self, direction: np.ndarray, max_distance: float):
        """Raycast for entities."""
        # Would check entities in world
        return None
    
    def _interact_with_block(self, x: int, y: int, z: int, face) -> None:
        """Interact with a block."""
        block = self.world.get_block(x, y, z)
        
        if block is None:
            return
        
        # Handle different block interactions
        block_type = block.block_type
        
        if block_type == BlockType.DOOR:
            self._toggle_door(x, y, z)
        elif block_type == BlockType.LEVER:
            self._toggle_lever(x, y, z)
        elif block_type == BlockType.BUTTON:
            self._press_button(x, y, z)
        elif block_type == BlockType.CHEST:
            self._open_chest(x, y, z)
        elif block_type == BlockType.FURNACE:
            self._open_furnace(x, y, z)
        elif block_type == BlockType.CRAFTING_TABLE:
            self._open_crafting(x, y, z)
        elif block_type == BlockType.BED:
            self._sleep(x, y, z)
    
    def _toggle_door(self, x: int, y: int, z: int) -> None:
        """Toggle a door."""
        pass
    
    def _toggle_lever(self, x: int, y: int, z: int) -> None:
        """Toggle a lever."""
        pass
    
    def _press_button(self, x: int, y: int, z: int) -> None:
        """Press a button."""
        pass
    
    def _open_chest(self, x: int, y: int, z: int) -> None:
        """Open a chest."""
        pass
    
    def _open_furnace(self, x: int, y: int, z: int) -> None:
        """Open a furnace."""
        pass
    
    def _open_crafting(self, x: int, y: int, z: int) -> None:
        """Open crafting table."""
        pass
    
    def _sleep(self, x: int, y: int, z: int) -> None:
        """Sleep in bed."""
        self.state.is_sleeping = True
    
    def get_held_item(self):
        """Get currently held item."""
        return self.inventory.get_selected()
    
    def get_position(self) -> Tuple[float, float, float]:
        """Get player position."""
        return self.state.position
    
    def get_look_vector(self) -> np.ndarray:
        """Get look direction."""
        return self.camera.get_look_vector()
    
    def respawn(self) -> None:
        """Respawn player."""
        spawn_x, spawn_z = self.world.get_spawn_position()
        spawn_y = self.world.get_height_at(spawn_x, spawn_z) + 2
        
        self.state.position = (spawn_x, spawn_y, spawn_z)
        self.state.health = 20
        self.state.hunger = 20
        self.state.velocity = (0, 0, 0)
        
        self.camera.set_position(self.state.position)


class Inventory:
    """Player inventory system."""
    
    def __init__(self):
        """Initialize inventory."""
        self.hotbar: List[Optional['Item']] = [None] * 9
        self.main_inventory: List[Optional['Item']] = [None] * 27
        self.armor_slots: List[Optional['Item']] = [None] * 4
        self.offhand: Optional['Item'] = None
        
        self.selected_slot = 0
        
        # Initialize with basic items
        self._init_starting_items()
    
    def _init_starting_items(self) -> None:
        """Initialize player with starting items."""
        # Give wooden pickaxe in creative mode
        from world.items import Item, ItemType
        self.hotbar[0] = Item(ItemType.WOODEN_PICKAXE)
    
    def get_selected(self):
        """Get currently selected item."""
        return self.hotbar[self.selected_slot]
    
    def set_selected(self, slot: int) -> None:
        """Set selected hotbar slot."""
        if 0 <= slot < 9:
            self.selected_slot = slot
    
    def select_next(self) -> None:
        """Select next hotbar slot."""
        self.selected_slot = (self.selected_slot + 1) % 9
    
    def select_previous(self) -> None:
        """Select previous hotbar slot."""
        self.selected_slot = (self.selected_slot - 1) % 9
    
    def add_item(self, item) -> bool:
        """Add item to inventory (stack if possible)."""
        # First try to stack
        for slot in self.hotbar + self.main_inventory:
            if slot and slot.can_stack_with(item):
                if slot.count < slot.max_stack:
                    slot.count += 1
                    return True
        
        # Find empty slot
        for i, slot in enumerate(self.hotbar):
            if slot is None:
                self.hotbar[i] = item.copy()
                return True
        
        for i, slot in enumerate(self.main_inventory):
            if slot is None:
                self.main_inventory[i] = item.copy()
                return True
        
        return False
    
    def remove_item(self, item_type, count: int = 1) -> bool:
        """Remove item from inventory."""
        # Search all slots
        for i, slot in enumerate(self.hotbar):
            if slot and slot.item_type == item_type:
                if slot.count >= count:
                    slot.count -= count
                    if slot.count <= 0:
                        if i < 9:
                            self.hotbar[i] = None
                        else:
                            self.main_inventory[i - 9] = None
                    return True
                else:
                    count -= slot.count
                    if i < 9:
                        self.hotbar[i] = None
                    else:
                        self.main_inventory[i - 9] = None
        
        return False
    
    def get_count(self, item_type) -> int:
        """Get total count of item type in inventory."""
        count = 0
        for slot in self.hotbar + self.main_inventory:
            if slot and slot.item_type == item_type:
                count += slot.count
        return count


@dataclass
class CameraConfig:
    """Camera configuration."""
    fov: float = 70.0
    near: float = 0.1
    far: float = 1000.0
    sensitivity: float = 0.1
    movement_speed: float = 10.0
    sprint_multiplier: float = 1.5


# Import items module
from world.items import Item, ItemType
