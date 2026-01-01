"""
Noise generation module for terrain generation.
Uses Perlin noise with multiple octaves for realistic terrain.
"""

import math
import random
from typing import Tuple, List
import numpy as np

class PerlinNoise:
    """Perlin noise generator for terrain generation."""
    
    def __init__(self, seed: int = None):
        """Initialize Perlin noise generator."""
        self.permutation = []
        self._init_permutation(seed)
    
    def _init_permutation(self, seed: int = None) -> None:
        """Initialize permutation table with optional seed."""
        if seed is not None:
            random.seed(seed)
        
        self.permutation = list(range(256))
        random.shuffle(self.permutation)
        self.permutation += self.permutation  # Duplicate for overflow
    
    def fade(self, t: float) -> float:
        """6t^5 - 15t^4 + 10t^3."""
        return t * t * t * (t * (t * 6 - 15) + 10)
    
    def lerp(self, a: float, b: float, t: float) -> float:
        """Linear interpolation."""
        return a + t * (b - a)
    
    def grad(self, hash_val: int, x: float, y: float, z: float) -> float:
        """Calculate gradient for 3D noise."""
        h = hash_val & 15
        u = x if h < 8 else y
        v = y if h < 4 else (x if h == 12 or h == 14 else z)
        return (u if (h & 1) == 0 else -u) + (v if (h & 2) == 0 else -v)
    
    def noise_3d(self, x: float, y: float, z: float) -> float:
        """Generate 3D Perlin noise value."""
        # Find unit cube containing point
        X = int(math.floor(x)) & 255
        Y = int(math.floor(y)) & 255
        Z = int(math.floor(z)) & 255
        
        # Relative position in cube
        x -= math.floor(x)
        y -= math.floor(y)
        z -= math.floor(z)
        
        # Fade curves
        u = self.fade(x)
        v = self.fade(y)
        w = self.fade(z)
        
        # Hash coordinates
        p = self.permutation
        A = p[X] + Y
        AA = p[A] + Z
        AB = p[A + 1] + Z
        B = p[X + 1] + Y
        BA = p[B] + Z
        BB = p[B + 1] + Z
        
        # Blend results
        return self.lerp(
            self.lerp(
                self.lerp(self.grad(p[AA], x, y, z), self.grad(p[BA], x - 1, y, z), u),
                self.lerp(self.grad(p[AB], x, y - 1, z), self.grad(p[BB], x - 1, y - 1, z), u),
                v
            ),
            self.lerp(
                self.lerp(self.grad(p[AA + 1], x, y, z - 1), self.grad(p[BA + 1], x - 1, y, z - 1), u),
                self.lerp(self.grad(p[AB + 1], x, y - 1, z - 1), self.grad(p[BB + 1], x - 1, y - 1, z - 1), u),
                v
            ),
            w
        )
    
    def noise_2d(self, x: float, y: float) -> float:
        """Generate 2D Perlin noise value."""
        return self.noise_3d(x, y, 0)
    
    def fbm(self, x: float, y: float, z: float = 0, octaves: int = 6, lacunarity: float = 2.0, persistence: float = 0.5) -> float:
        """Fractal Brownian Motion - layered noise for natural terrain."""
        total = 0.0
        amplitude = 1.0
        frequency = 1.0
        max_value = 0.0
        
        for _ in range(octaves):
            if z == 0:
                total += self.noise_2d(x * frequency, y * frequency) * amplitude
            else:
                total += self.noise_3d(x * frequency, y * frequency, z * frequency) * amplitude
            
            max_value += amplitude
            amplitude *= persistence
            frequency *= lacunarity
        
        return total / max_value
    
    def ridge_noise(self, x: float, y: float, octaves: int = 6, lacunarity: float = 2.0, persistence: float = 0.5, ridge_offset: float = 1.0) -> float:
        """Ridge noise for more dramatic terrain features."""
        total = 0.0
        amplitude = 1.0
        frequency = 1.0
        max_value = 0.0
        
        for _ in range(octaves):
            n = self.noise_2d(x * frequency, y * frequency)
            n = 1.0 - abs(n)  # Ridge shape
            n = n * n * ridge_offset  # Sharpen ridges
            
            total += n * amplitude
            max_value += amplitude
            amplitude *= persistence
            frequency *= lacunarity
        
        return total / max_value


class SimplexNoise:
    """Simplex noise implementation for better performance."""
    
    def __init__(self, seed: int = None):
        """Initialize simplex noise."""
        self.perm = []
        self._init_permutation(seed)
    
    def _init_permutation(self, seed: int = None) -> None:
        """Initialize permutation table."""
        if seed is not None:
            random.seed(seed)
        
        self.perm = list(range(256))
        random.shuffle(self.perm)
        self.perm += self.perm
    
    def fast_noise(self, x: int, y: int, z: int = 0) -> float:
        """Fast integer noise for procedural generation."""
        # Simple hash-based noise for speed
        n = x * 374761393 + y * 668265263 + z * 1274126177
        n = (n ^ (n >> 13)) * 1274126177
        return (n & 0x7FFFFFFF) / 0x7FFFFFFF - 0.5


class NoiseGenerator:
    """Combined noise generator with various utility methods."""
    
    def __init__(self, seed: int = None):
        """Initialize noise generator."""
        self.seed_value = seed if seed is not None else random.randint(0, 999999)
        self.perlin = PerlinNoise(self.seed_value)
        self.simplex = SimplexNoise(self.seed_value)
        
        # Cache for terrain generation
        self._terrain_cache = {}
    
    def seed(self, seed: int) -> None:
        """Reset generator with new seed."""
        self.seed_value = seed
        self.perlin = PerlinNoise(seed)
        self.simplex = SimplexNoise(seed)
        self._terrain_cache = {}
    
    def get_height(self, x: int, z: int, base_height: int = 64, amplitude: int = 32) -> int:
        """Get terrain height at world coordinates."""
        cache_key = (x, z)
        if cache_key in self._terrain_cache:
            return self._terrain_cache[cache_key]
        
        # Multi-octave terrain noise
        nx = x / 200.0
        nz = z / 200.0
        
        # Base terrain (large features)
        height = self.perlin.fbm(nx, nz, 0, octaves=4, lacunarity=2.0, persistence=0.5)
        
        # Detail terrain
        height += 0.5 * self.perlin.fbm(nx * 4, nz * 4, 0, octaves=3)
        
        # Ridge noise for mountains
        ridge = self.perlin.ridge_noise(nx * 2, nz * 2, octaves=2)
        height += ridge * 0.3
        
        # Convert to height value
        height = int(base_height + height * amplitude)
        
        self._terrain_cache[cache_key] = height
        return height
    
    def get_biome(self, x: int, z: int) -> str:
        """Get biome type at world coordinates."""
        nx = x / 400.0
        nz = z / 400.0
        
        # Temperature map (-1 to 1)
        temperature = self.perlin.fbm(nx, nz, 0, octaves=2)
        
        # Humidity map (-1 to 1)
        humidity = self.perlin.fbm(nx + 100, nz + 100, 0, octaves=2)
        
        # Determine biome
        if temperature < -0.3:
            return 'snow'
        elif temperature < 0.1:
            if humidity < -0.2:
                return 'taiga'
            else:
                return 'plains'
        elif temperature < 0.4:
            if humidity < -0.3:
                return 'desert'
            elif humidity > 0.3:
                return 'jungle'
            else:
                return 'forest'
        else:
            return 'desert'
    
    def get_cave_noise(self, x: int, y: int, z: int) -> float:
        """Get 3D noise for cave generation."""
        nx = x / 50.0
        ny = y / 50.0
        nz = z / 50.0
        
        # 3D noise for cave tunnels
        cave = self.perlin.noise_3d(nx, ny, nz)
        cave += 0.5 * self.perlin.noise_3d(nx * 2, ny * 2, nz * 2)
        cave += 0.25 * self.perlin.noise_3d(nx * 4, ny * 4, nz * 4)
        
        return cave
    
    def get_ore_noise(self, x: int, y: int, z: int, scale: float = 20.0) -> float:
        """Get noise for ore distribution."""
        return self.simplex.fast_noise(int(x * scale), int(y * scale), int(z * scale))
    
    def get_tree_position(self, x: int, z: int) -> bool:
        """Check if position is suitable for a tree."""
        # Sparse tree placement
        n = self.simplex.fast_noise(x, 0, z)
        return n > 0.6
    
    def get_river_position(self, x: int, z: int) -> bool:
        """Check if position is in a river valley."""
        nx = x / 150.0
        nz = z / 150.0
        
        river = self.perlin.fbm(nx, nz, 0, octaves=3)
        return river < -0.3
    
    def clear_cache(self) -> None:
        """Clear terrain cache."""
        self._terrain_cache = {}
    
    def generate_heightmap(self, start_x: int, start_z: int, width: int, depth: int) -> np.ndarray:
        """Generate a heightmap for a region."""
        heightmap = np.zeros((width, depth), dtype=np.int16)
        
        for x in range(width):
            for z in range(depth):
                heightmap[x, z] = self.get_height(start_x + x, start_z + z)
        
        return heightmap
    
    def generate_biome_map(self, start_x: int, start_z: int, width: int, depth: int) -> np.ndarray:
        """Generate a biome map for a region."""
        biomemap = np.empty((width, depth), dtype='<U10')
        
        for x in range(width):
            for z in range(depth):
                biomemap[x, z] = self.get_biome(start_x + x, start_z + z)
        
        return biomemap
