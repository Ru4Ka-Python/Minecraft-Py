"""
Light engine for Minecraft clone.
Implements 16-level brightness with BFS light propagation.
"""

from typing import Dict, Tuple, Set, List
from collections import deque
from dataclasses import dataclass
import numpy as np

from world.chunk import Chunk, CHUNK_WIDTH, CHUNK_HEIGHT, CHUNK_DEPTH


class LightEngine:
    """Light propagation engine for Minecraft world."""
    
    def __init__(self):
        """Initialize light engine."""
        self.light_queue = deque()
        self.sky_light_queue = deque()
    
    def update_chunk(self, chunk: Chunk) -> None:
        """Update all lighting in a chunk."""
        # Recalculate sky light (top-down)
        self._recalculate_sky_light(chunk)
        
        # Recalculate block light (from light sources)
        self._recalculate_block_light(chunk)
    
    def update_block(self, chunk: Chunk, x: int, y: int, z: int) -> None:
        """Update lighting when a block changes."""
        block = chunk.get_block(x, y, z)
        
        if block is None:
            # Block was removed - light spreads
            self._propagate_light(chunk, x, y, z)
        else:
            # Block was added - may block light
            self._update_after_block_change(chunk, x, y, z)
    
    def _recalculate_sky_light(self, chunk: Chunk) -> None:
        """Recalculate sky light for entire chunk."""
        for x in range(CHUNK_WIDTH):
            for z in range(CHUNK_DEPTH):
                # Start from top, propagate down
                light = 15
                for y in range(CHUNK_HEIGHT - 1, -1, -1):
                    index = chunk._get_index(x, y, z)
                    block = chunk.get_block(x, y, z)
                    
                    if block is not None:
                        if block.is_opaque():
                            light = 0
                        elif block.is_transparent():
                            light = max(0, light - 1)
                        else:
                            light = max(0, light - 2)
                    
                    chunk.sky_light[index] = light
    
    def _recalculate_block_light(self, chunk: Chunk) -> None:
        """Recalculate block light for entire chunk."""
        # Reset block light
        chunk.block_light.fill(0)
        
        # Find light sources and propagate
        for x in range(CHUNK_WIDTH):
            for y in range(CHUNK_HEIGHT):
                for z in range(CHUNK_DEPTH):
                    block = chunk.get_block(x, y, z)
                    if block is not None:
                        emission = block.get_light_emission()
                        if emission > 0:
                            self._set_block_light(chunk, x, y, z, emission)
    
    def _set_block_light(self, chunk: Chunk, x: int, y: int, z: int, light: int) -> None:
        """Set block light level and propagate."""
        if light <= 0:
            return
        
        queue = deque([(x, y, z, light)])
        visited = set()
        
        while queue:
            cx, cy, cz, level = queue.popleft()
            
            if (cx, cy, cz) in visited:
                continue
            visited.add((cx, cy, cz))
            
            # Check bounds
            if not (0 <= cx < CHUNK_WIDTH and 0 <= cy < CHUNK_HEIGHT and 0 <= cz < CHUNK_DEPTH):
                continue
            
            block = chunk.get_block(cx, cy, cz)
            if block is not None and not block.is_transparent():
                continue
            
            index = chunk._get_index(cx, cy, cz)
            current_light = chunk.block_light[index]
            
            if level <= current_light:
                continue
            
            chunk.block_light[index] = level
            
            # Propagate to neighbors with reduced light
            if level > 1:
                for dx, dy, dz in self._get_neighbors():
                    new_level = level - 1
                    queue.append((cx + dx, cy + dy, cz + dz, new_level))
    
    def _propagate_light(self, chunk: Chunk, x: int, y: int, z: int) -> None:
        """Propagate light after block removal."""
        neighbors = self._get_neighbors()
        
        for dx, dy, dz in neighbors:
            nx, ny, nz = x + dx, y + dy, z + dz
            
            if 0 <= nx < CHUNK_WIDTH and 0 <= ny < CHUNK_HEIGHT and 0 <= nz < CHUNK_DEPTH:
                self._spread_light(chunk, nx, ny, nz)
    
    def _spread_light(self, chunk: Chunk, x: int, y: int, z: int) -> None:
        """Spread light to a position."""
        if not (0 <= x < CHUNK_WIDTH and 0 <= y < CHUNK_HEIGHT and 0 <= z < CHUNK_DEPTH):
            return
        
        block = chunk.get_block(x, y, z)
        if block is not None and not block.is_transparent():
            return
        
        index = chunk._get_index(x, y, z)
        
        # Get light from neighbors
        max_light = 0
        for dx, dy, dz in self._get_neighbors():
            nx, ny, nz = x + dx, y + dy, z + dz
            
            if 0 <= nx < CHUNK_WIDTH and 0 <= ny < CHUNK_HEIGHT and 0 <= nz < CHUNK_DEPTH:
                n_index = chunk._get_index(nx, ny, nz)
                max_light = max(max_light, chunk.block_light[n_index])
        
        new_light = max(0, max_light - 1)
        
        if new_light > chunk.block_light[index]:
            chunk.block_light[index] = new_light
            self._spread_light(chunk, x, y, z + 1)
            self._spread_light(chunk, x, y, z - 1)
            self._spread_light(chunk, x + 1, y, z)
            self._spread_light(chunk, x - 1, y, z)
            if y < CHUNK_HEIGHT - 1:
                self._spread_light(chunk, x, y + 1, z)
            if y > 0:
                self._spread_light(chunk, x, y - 1, z)
    
    def _update_after_block_change(self, chunk: Chunk, x: int, y: int, z: int) -> None:
        """Update lighting after a block is placed."""
        # Light may need to be removed or redirected
        block = chunk.get_block(x, y, z)
        
        if block is not None and not block.is_transparent():
            # Check if this block was a light source
            index = chunk._get_index(x, y, z)
            old_light = chunk.block_light[index]
            
            if old_light > 0 and block.get_light_emission() == 0:
                # Remove light source
                chunk.block_light[index] = 0
                self._spread_light(chunk, x, y, z)
    
    def _get_neighbors(self) -> List[Tuple[int, int, int]]:
        """Get neighbor offsets."""
        return [
            (0, 1, 0),   # top
            (0, -1, 0),  # bottom
            (1, 0, 0),   # right
            (-1, 0, 0),  # left
            (0, 0, 1),   # front
            (0, 0, -1),  # back
        ]
    
    def get_combined_light(self, chunk: Chunk, x: int, y: int, z: int) -> int:
        """Get combined light level (sky + block)."""
        if not (0 <= x < CHUNK_WIDTH and 0 <= y < CHUNK_HEIGHT and 0 <= z < CHUNK_DEPTH):
            return 0
        
        index = chunk._get_index(x, y, z)
        sky = chunk.sky_light[index]
        block = chunk.block_light[index]
        
        return max(sky, block)
    
    def get_light_color(self, light_level: int, underwater: bool = False) -> Tuple[float, float, float]:
        """Get light color based on level and conditions."""
        if underwater:
            return (0.0, 0.3 * light_level / 15, 0.5 * light_level / 15)
        
        # Daytime light
        intensity = light_level / 15.0
        return (intensity, intensity, intensity)
    
    def get_sky_color(self, time_of_day: int, light_level: int = 15) -> Tuple[float, float, float]:
        """Get sky color based on time of day."""
        # Normalize time
        normalized = time_of_day / 24000
        
        if normalized < 0.25:  # Night
            return (0.05, 0.05, 0.1)
        elif normalized < 0.35:  # Sunrise
            t = (normalized - 0.25) / 0.1
            return (0.3 + 0.4 * t, 0.2 + 0.4 * t, 0.3 + 0.4 * t)
        elif normalized < 0.45:  # Morning
            t = (normalized - 0.35) / 0.1
            return (0.7 * t, 0.6 * t, 0.9 * t)
        elif normalized < 0.75:  # Day
            return (0.5, 0.7, 0.9)
        else:  # Sunset
            t = (normalized - 0.75) / 0.25
            return (0.8 - 0.3 * t, 0.6 - 0.4 * t, 0.4 - 0.2 * t)
    
    def get_fog_color(self, time_of_day: int, underwater: bool = False, lava: bool = False) -> Tuple[float, float, float]:
        """Get fog color based on conditions."""
        if underwater:
            return (0.0, 0.2, 0.4)
        if lava:
            return (0.6, 0.2, 0.0)
        
        sky = self.get_sky_color(time_of_day)
        return sky
    
    def calculate_shadows(self, chunk: Chunk, sunlight: int) -> Dict[Tuple[int, int, int], float]:
        """Calculate shadow factors for rendering."""
        shadows = {}
        
        for x in range(CHUNK_WIDTH):
            for z in range(CHUNK_DEPTH):
                for y in range(CHUNK_HEIGHT):
                    block = chunk.get_block(x, y, z)
                    if block is not None and block.is_opaque():
                        # Cast shadow on blocks below
                        for dy in range(1, 5):
                            if y - dy < 0:
                                break
                            below = chunk.get_block(x, y - dy, z)
                            if below is not None and below.is_opaque():
                                break
                            shadows[(x, y - dy, z)] = 0.7
        
        return shadows
