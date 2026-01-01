"""
World system for Minecraft clone.
Manages chunks, terrain generation, and world state.
"""

import os
import threading
import time
from typing import Dict, List, Tuple, Set, Optional, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import numpy as np

from world.chunk import Chunk, ChunkPosition
from world.blocks import Block, BlockType
from utils.noise import NoiseGenerator
from utils.light import LightEngine


class World:
    """Main world manager for Minecraft clone."""
    
    def __init__(self, seed: int = None, save_path: str = "world"):
        """Initialize world."""
        self.seed = seed if seed is not None else int(time.time())
        self.save_path = save_path
        
        # World components
        self.chunks: Dict[ChunkPosition, Chunk] = {}
        self.noise = NoiseGenerator(self.seed)
        self.light_engine = LightEngine()
        
        # State
        self.is_loaded = False
        self.is_generating = False
        self._generation_lock = threading.Lock()
        
        # Thread pool for chunk generation
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # World dimensions
        self.world_height = 256
        self.sea_level = 62
        
        # Time of day (0-24000)
        self.time_of_day = 6000
        self.is_day = True
        
        # Weather
        self.is_raining = False
        self.rain_intensity = 0.0
        self.is_thundering = False
        self.thunder_intensity = 0.0
        
        # Update callbacks
        self.update_callbacks: List[Callable] = []
        
        # Initialize world
        self._init_world()
    
    def _init_world(self) -> None:
        """Initialize world components."""
        os.makedirs(self.save_path, exist_ok=True)
        
        # Create initial chunks around spawn
        self._generate_initial_chunks()
    
    def _generate_initial_chunks(self) -> None:
        """Generate initial chunks around spawn point."""
        spawn_x, spawn_z = self.get_spawn_position()
        spawn_chunk = ChunkPosition.from_world(spawn_x, spawn_z)
        
        # Generate 3x3 chunks around spawn
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                chunk_pos = ChunkPosition(spawn_chunk.x + dx, spawn_chunk.z + dz)
                self._generate_chunk(chunk_pos)
    
    def get_spawn_position(self) -> Tuple[int, int]:
        """Get spawn position based on seed."""
        # Use seed to determine spawn
        random.seed(self.seed)
        spawn_x = random.randint(-1000, 1000)
        spawn_z = random.randint(-1000, 1000)
        
        # Find surface at spawn
        noise = NoiseGenerator(self.seed)
        spawn_y = noise.get_height(spawn_x, spawn_z)
        
        return spawn_x, spawn_z
    
    def _generate_chunk(self, position: ChunkPosition, generate: bool = True) -> Chunk:
        """Generate or load a chunk."""
        with self._generation_lock:
            if position in self.chunks:
                return self.chunks[position]
            
            # Try to load from disk
            chunk = self._load_chunk(position)
            
            if chunk is None and generate:
                chunk = Chunk(position, generate=True)
            
            if chunk:
                self.chunks[position] = chunk
                self.light_engine.update_chunk(chunk)
            
            return chunk
    
    def _load_chunk(self, position: ChunkPosition) -> Optional[Chunk]:
        """Load chunk from disk."""
        chunk_file = os.path.join(self.save_path, f"chunk_{position.x}_{position.z}.bin")
        
        if not os.path.exists(chunk_file):
            return None
        
        try:
            return Chunk.load(position, self.save_path)
        except Exception as e:
            print(f"Failed to load chunk {position}: {e}")
            return None
    
    def save_chunk(self, position: ChunkPosition) -> None:
        """Save chunk to disk."""
        if position in self.chunks:
            self.chunks[position].save(self.save_path)
    
    def save_all(self) -> None:
        """Save all chunks to disk."""
        for position in self.chunks:
            if self.chunks[position].is_modified:
                self.save_chunk(position)
    
    def get_chunk(self, x: int, z: int) -> Optional[Chunk]:
        """Get chunk at position."""
        chunk_pos = ChunkPosition(x, z)
        return self.chunks.get(chunk_pos)
    
    def get_chunk_at(self, world_x: int, world_z: int) -> Tuple[Optional[Chunk], int, int]:
        """Get chunk containing world position."""
        chunk_pos = ChunkPosition.from_world(world_x, world_z)
        chunk = self.chunks.get(chunk_pos)
        
        if chunk:
            local_x = world_x - chunk_pos.x * 16
            local_z = world_z - chunk_pos.z * 16
            return chunk, local_x, local_z
        
        return None, -1, -1
    
    def get_block(self, x: int, y: int, z: int) -> Optional[Block]:
        """Get block at world position."""
        chunk, local_x, local_z = self.get_chunk_at(x, z)
        
        if chunk is None:
            # Generate chunk if needed
            chunk_pos = ChunkPosition.from_world(x, z)
            chunk = self._generate_chunk(chunk_pos)
            if chunk is None:
                return None
            local_x = x - chunk_pos.x * 16
            local_z = z - chunk_pos.z * 16
        
        return chunk.get_block(local_x, y, local_z)
    
    def set_block(self, x: int, y: int, z: int, block: Block) -> bool:
        """Set block at world position."""
        chunk, local_x, local_z = self.get_chunk_at(x, z)
        
        if chunk is None:
            # Generate chunk if needed
            chunk_pos = ChunkPosition.from_world(x, z)
            chunk = self._generate_chunk(chunk_pos)
            if chunk is None:
                return False
            local_x = x - chunk_pos.x * 16
            local_z = z - chunk_pos.z * 16
        
        chunk.set_block(local_x, y, local_z, block)
        
        # Update lighting
        self.light_engine.update_block(chunk, local_x, y, local_z)
        
        # Update neighbor chunks if on edge
        if local_x == 0:
            self._generate_chunk(ChunkPosition(chunk.position.x - 1, chunk.position.z))
        elif local_x == 15:
            self._generate_chunk(ChunkPosition(chunk.position.x + 1, chunk.position.z))
        
        if local_z == 0:
            self._generate_chunk(ChunkPosition(chunk.position.x, chunk.position.z - 1))
        elif local_z == 15:
            self._generate_chunk(ChunkPosition(chunk.position.x, chunk.position.z + 1))
        
        return True
    
    def get_blocks_in_radius(self, center: Tuple[int, int, int], radius: int) -> Dict[Tuple[int, int, int], Block]:
        """Get all blocks within a radius."""
        blocks = {}
        cx, cy, cz = center
        
        for x in range(cx - radius, cx + radius + 1):
            for y in range(max(0, cy - radius), min(256, cy + radius + 1)):
                for z in range(cz - radius, cz + radius + 1):
                    block = self.get_block(x, y, z)
                    if block is not None:
                        blocks[(x, y, z)] = block
        
        return blocks
    
    def get_height_at(self, x: int, z: int) -> int:
        """Get surface height at world position."""
        chunk, local_x, local_z = self.get_chunk_at(x, z)
        
        if chunk is None:
            chunk_pos = ChunkPosition.from_world(x, z)
            chunk = self._generate_chunk(chunk_pos)
            if chunk is None:
                return 64
        
        return chunk.get_height_at(local_x, local_z)
    
    def is_sky_visible(self, x: int, y: int, z: int) -> bool:
        """Check if position has sky access."""
        for check_y in range(y + 1, 256):
            block = self.get_block(x, check_y, z)
            if block is not None and block.is_opaque():
                return False
        return True
    
    def get_sky_light(self, x: int, y: int, z: int) -> int:
        """Get sky light level at position."""
        if not self.is_sky_visible(x, y, z):
            return 0
        
        # Calculate based on height
        surface = self.get_height_at(x, z)
        distance = surface - y
        return max(0, min(15, 15 - distance // 2))
    
    def get_block_light(self, x: int, y: int, z: int) -> int:
        """Get block light level at position."""
        chunk, local_x, local_z = self.get_chunk_at(x, z)
        
        if chunk is None:
            return 0
        
        return chunk.block_light[chunk._get_index(local_x, y, local_z)]
    
    def update(self, delta_time: float) -> None:
        """Update world state."""
        # Update time
        self.time_of_day = (self.time_of_day + delta_time * 20) % 24000
        self.is_day = 0 <= self.time_of_day < 12000
        
        # Update weather
        if self.is_raining:
            self.rain_intensity = min(1.0, self.rain_intensity + delta_time * 0.1)
        else:
            self.rain_intensity = max(0.0, self.rain_intensity - delta_time * 0.1)
        
        if self.is_thundering:
            self.thunder_intensity = min(1.0, self.thunder_intensity + delta_time * 0.1)
        else:
            self.thunder_intensity = max(0.0, self.thunder_intensity - delta_time * 0.1)
        
        # Tick random blocks
        self._tick_random_blocks()
        
        # Update callbacks
        for callback in self.update_callbacks:
            callback(delta_time)
    
    def _tick_random_blocks(self) -> None:
        """Process random ticks for blocks."""
        # Tick a percentage of chunks each update
        for chunk in list(self.chunks.values())[:10]:
            chunk.tick()
    
    def get_time_of_day_color(self) -> Tuple[float, float, float, float]:
        """Get fog/sky color based on time of day."""
        time = self.time_of_day
        
        if 0 <= time < 5000:  # Sunrise to noon
            t = time / 5000
            return (0.5 + 0.3 * t, 0.7 + 0.2 * t, 0.9 + 0.1 * t, 1.0)
        elif 5000 <= time < 12000:  # Noon to sunset
            t = (time - 5000) / 7000
            return (0.8 - 0.1 * t, 0.9 - 0.1 * t, 1.0, 1.0)
        elif 12000 <= time < 14000:  # Sunset to night
            t = (time - 12000) / 2000
            return (0.7 - 0.5 * t, 0.8 - 0.6 * t, 0.9 - 0.7 * t, 1.0)
        else:  # Night
            return (0.1, 0.1, 0.2, 1.0)
    
    def get_fog_distance(self) -> Tuple[float, float]:
        """Get fog start and end distances."""
        if self.is_raining:
            return (20.0, 80.0)
        else:
            return (50.0, 200.0)
    
    def get_all_visible_blocks(self, frustum) -> Set[Tuple[int, int, int]]:
        """Get all visible blocks in loaded chunks."""
        visible = set()
        
        for chunk in self.chunks.values():
            visible_chunk = chunk.get_visible_blocks(frustum)
            visible.update(visible_chunk)
        
        return visible
    
    def get_loaded_chunks(self) -> List[Chunk]:
        """Get all loaded chunks."""
        return list(self.chunks.values())
    
    def get_chunk_count(self) -> int:
        """Get number of loaded chunks."""
        return len(self.chunks)
    
    def add_update_callback(self, callback: Callable) -> None:
        """Add a callback for world updates."""
        self.update_callbacks.append(callback)
    
    def remove_update_callback(self, callback: Callable) -> None:
        """Remove a world update callback."""
        if callback in self.update_callbacks:
            self.update_callbacks.remove(callback)
    
    def get_statistics(self) -> Dict:
        """Get world statistics."""
        stats = {
            'seed': self.seed,
            'chunk_count': self.get_chunk_count(),
            'time_of_day': self.time_of_day,
            'is_day': self.is_day,
            'is_raining': self.is_raining,
            'is_thundering': self.is_thundering,
        }
        
        # Count block types
        block_counts = {}
        for chunk in self.chunks.values():
            for pos, block in chunk.blocks.items():
                name = block.block_type.name
                block_counts[name] = block_counts.get(name, 0) + 1
        
        stats['block_counts'] = block_counts
        return stats
    
    def cleanup(self) -> None:
        """Cleanup world resources."""
        self.save_all()
        self.executor.shutdown(wait=True)
