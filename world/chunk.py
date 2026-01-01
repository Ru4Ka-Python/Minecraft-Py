"""
Chunk system for Minecraft clone.
Handles chunk data storage, meshing, and rendering optimization.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import struct

from world.blocks import Block, BlockType
from utils.noise import NoiseGenerator


# Chunk dimensions
CHUNK_WIDTH = 16
CHUNK_HEIGHT = 256
CHUNK_DEPTH = 16
CHUNK_VOLUME = CHUNK_WIDTH * CHUNK_HEIGHT * CHUNK_DEPTH


class ChunkPosition:
    """Represents a chunk position in world coordinates."""
    
    def __init__(self, x: int, z: int):
        """Initialize chunk position."""
        self.x = x
        self.z = z
    
    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash((self.x, self.z))
    
    def __eq__(self, other) -> bool:
        """Check equality."""
        if isinstance(other, ChunkPosition):
            return self.x == other.x and self.z == other.z
        return False
    
    def __str__(self) -> str:
        """String representation."""
        return f"Chunk({self.x}, {self.z})"
    
    def to_world(self, block_x: int, block_z: int) -> Tuple[int, int]:
        """Convert chunk-relative coordinates to world coordinates."""
        return (self.x * CHUNK_WIDTH + block_x, self.z * CHUNK_DEPTH + block_z)
    
    def from_world(world_x: int, world_z: int) -> 'ChunkPosition':
        """Get chunk position from world coordinates."""
        return ChunkPosition(
            world_x // CHUNK_WIDTH,
            world_z // CHUNK_DEPTH
        )
    
    def get_neighbors(self) -> List['ChunkPosition']:
        """Get neighboring chunk positions."""
        return [
            ChunkPosition(self.x + dx, self.z + dz)
            for dx in (-1, 0, 1)
            for dz in (-1, 0, 1)
            if not (dx == 0 and dz == 0)
        ]


@dataclass
class BlockData:
    """Compressed block data for efficient storage."""
    block_type: np.uint16
    metadata: np.uint8
    light: np.uint8
    sky_light: np.uint8
    
    @classmethod
    def empty(cls) -> 'BlockData':
        """Create empty block data."""
        return cls(
            block_type=np.uint16(BlockType.AIR.value),
            metadata=np.uint8(0),
            light=np.uint8(0),
            sky_light=np.uint8(15),
        )


class Chunk:
    """Represents a chunk of world data."""
    
    def __init__(self, position: ChunkPosition, generate: bool = True):
        """Initialize chunk."""
        self.position = position
        self.blocks: Dict[Tuple[int, int, int], Block] = {}
        self.block_data: np.ndarray = None
        self.sky_light: np.ndarray = None
        self.block_light: np.ndarray = None
        
        # Meshing data
        self.mesh_data: np.ndarray = None
        self.mesh_valid = False
        
        # State
        self.is_loaded = False
        self.is_modified = False
        self.is_generating = False
        self.is_dirty = True
        
        # Height map for optimization
        self.height_map: np.ndarray = np.full(CHUNK_WIDTH * CHUNK_DEPTH, CHUNK_HEIGHT, dtype=np.int16)
        
        # Initialize block arrays
        self._init_arrays()
        
        if generate:
            self.generate()
    
    def _init_arrays(self) -> None:
        """Initialize block data arrays."""
        total_blocks = CHUNK_WIDTH * CHUNK_HEIGHT * CHUNK_DEPTH
        
        self.block_data = np.zeros(total_blocks, dtype=[('type', 'u2'), ('metadata', 'u1')])
        self.sky_light = np.full(total_blocks, 15, dtype=np.uint8)
        self.block_light = np.zeros(total_blocks, dtype=np.uint8)
    
    def _get_index(self, x: int, y: int, z: int) -> int:
        """Get linear index for block coordinates."""
        return (y * CHUNK_DEPTH + z) * CHUNK_WIDTH + x
    
    def _get_coords(self, index: int) -> Tuple[int, int, int]:
        """Get block coordinates from linear index."""
        z = index // (CHUNK_WIDTH * CHUNK_HEIGHT)
        remainder = index % (CHUNK_WIDTH * CHUNK_HEIGHT)
        x = remainder // CHUNK_HEIGHT
        y = remainder % CHUNK_HEIGHT
        return x, y, z
    
    def get_block(self, x: int, y: int, z: int) -> Optional[Block]:
        """Get block at position."""
        if not (0 <= x < CHUNK_WIDTH and 0 <= y < CHUNK_HEIGHT and 0 <= z < CHUNK_DEPTH):
            return None
        
        index = self._get_index(x, y, z)
        block_type = BlockType(self.block_data[index]['type'])
        
        if block_type == BlockType.AIR:
            return None
        
        return Block(
            block_type=block_type,
            metadata=self.block_data[index]['metadata'],
            light_level=self.block_light[index],
            sky_light=self.sky_light[index],
        )
    
    def set_block(self, x: int, y: int, z: int, block: Block) -> None:
        """Set block at position."""
        if not (0 <= x < CHUNK_WIDTH and 0 <= y < CHUNK_HEIGHT and 0 <= z < CHUNK_DEPTH):
            return
        
        index = self._get_index(x, y, z)
        
        self.block_data[index]['type'] = np.uint16(block.block_type.value)
        self.block_data[index]['metadata'] = np.uint8(block.metadata)
        self.block_light[index] = np.uint8(block.light_level)
        self.sky_light[index] = np.uint8(block.sky_light)
        
        self.is_modified = True
        self.is_dirty = True
        self.mesh_valid = False
        
        # Update height map
        if block.block_type != BlockType.AIR:
            if y < self.height_map[z * CHUNK_WIDTH + x]:
                self.height_map[z * CHUNK_WIDTH + x] = y
        else:
            # Recalculate height for this column
            self._recalculate_height(x, z)
    
    def _recalculate_height(self, x: int, z: int) -> None:
        """Recalculate height map for a column."""
        for y in range(CHUNK_HEIGHT - 1, -1, -1):
            index = self._get_index(x, y, z)
            if self.block_data[index]['type'] != BlockType.AIR.value:
                self.height_map[z * CHUNK_WIDTH + x] = y
                return
        self.height_map[z * CHUNK_WIDTH + x] = -1
    
    def get_height_at(self, x: int, z: int) -> int:
        """Get surface height at x, z."""
        if 0 <= x < CHUNK_WIDTH and 0 <= z < CHUNK_DEPTH:
            return self.height_map[z * CHUNK_WIDTH + x]
        return -1
    
    def is_opaque(self, x: int, y: int, z: int) -> bool:
        """Check if block at position is opaque."""
        block = self.get_block(x, y, z)
        return block is not None and block.is_opaque()
    
    def is_transparent(self, x: int, y: int, z: int) -> bool:
        """Check if block at position is transparent."""
        block = self.get_block(x, y, z)
        return block is None or block.is_transparent()
    
    def generate(self) -> None:
        """Generate chunk terrain."""
        self.is_generating = True
        
        # Use world generator
        noise = NoiseGenerator()
        noise.seed(12345)  # Can be based on chunk position
        
        for x in range(CHUNK_WIDTH):
            for z in range(CHUNK_DEPTH):
                world_x, world_z = self.position.to_world(x, z)
                
                # Multi-octave Perlin noise for terrain height
                height = noise.get_height(world_x, world_z)
                height = max(0, min(CHUNK_HEIGHT - 1, height))
                
                # Set blocks
                for y in range(CHUNK_HEIGHT):
                    block_type = self._get_block_type_at(x, y, z, height)
                    if block_type != BlockType.AIR:
                        block = Block(block_type=block_type)
                        self.set_block(x, y, z, block)
        
        self.is_generating = False
        self.is_loaded = True
        self.is_dirty = True
    
    def _get_block_type_at(self, x: int, y: int, z: int, surface_height: int) -> BlockType:
        """Determine block type at position based on height."""
        noise = NoiseGenerator()
        
        # Bedrock
        if y < 5:
            return BlockType.BEDROCK
        
        # Surface blocks
        if y == surface_height:
            if surface_height > 180:  # Snowy
                return BlockType.SNOW
            elif surface_height > 140:  # Mountain
                return BlockType.STONE
            elif surface_height > 100:  # Desert
                return BlockType.SAND
            else:  # Plains
                return BlockType.GRASS
        
        # Underground
        if y < surface_height - 4:
            if noise.fast_noise(x, y, z) > 0.3:
                return BlockType.STONE
            elif noise.fast_noise(x * 2, y * 2, z * 2) > 0.6:
                return BlockType.DIRT
            return BlockType.STONE
        
        return BlockType.DIRT
    
    def get_visible_blocks(self, frustum) -> Set[Tuple[int, int, int]]:
        """Get blocks visible within the frustum (frustum culling)."""
        visible = set()
        
        # Get chunk world position
        world_x = self.position.x * CHUNK_WIDTH
        world_z = self.position.z * CHUNK_DEPTH
        
        # Check each block (optimization: check columns)
        for x in range(CHUNK_WIDTH):
            for z in range(CHUNK_DEPTH):
                height = self.get_height_at(x, z)
                if height < 0:
                    continue
                
                # Check top block visibility
                block_pos = (world_x + x, height, world_z + z)
                if self._is_in_frustum(block_pos, frustum):
                    # Add visible blocks from this column
                    for y in range(max(0, height - 10), height + 1):
                        if self.get_block(x, y, z) is not None:
                            visible.add((world_x + x, y, world_z + z))
        
        return visible
    
    def _is_in_frustum(self, position: Tuple[int, int, int], frustum) -> bool:
        """Check if a position is within the view frustum."""
        # Simplified check - full implementation would use actual frustum planes
        return True
    
    def build_mesh(self, visible_blocks: Set[Tuple[int, int, int]]) -> np.ndarray:
        """Build mesh data for visible blocks (greedy meshing)."""
        vertices = []
        
        for pos in visible_blocks:
            # Convert world position to chunk-relative
            chunk_x = pos[0] - self.position.x * CHUNK_WIDTH
            chunk_y = pos[1]
            chunk_z = pos[2] - self.position.z * CHUNK_DEPTH
            
            if not (0 <= chunk_x < CHUNK_WIDTH and 0 <= chunk_y < CHUNK_HEIGHT and 0 <= chunk_z < CHUNK_DEPTH):
                continue
            
            block = self.get_block(chunk_x, chunk_y, chunk_z)
            if block is None:
                continue
            
            # Get visible faces
            faces = self._get_visible_faces(chunk_x, chunk_y, chunk_z)
            
            for face, light in faces:
                face_verts = self._get_face_vertices(chunk_x, chunk_y, chunk_z, face, block, light)
                vertices.extend(face_verts)
        
        if vertices:
            return np.array(vertices, dtype=np.float32)
        return np.array([], dtype=np.float32)
    
    def _get_visible_faces(self, x: int, y: int, z: int) -> List[Tuple[str, int]]:
        """Get visible faces for a block with culling."""
        visible = []
        
        # Check each neighbor
        neighbors = {
            'top': (x, y + 1, z),
            'bottom': (x, y - 1, z),
            'front': (x, y, z + 1),
            'back': (x, y, z - 1),
            'right': (x + 1, y, z),
            'left': (x - 1, y, z),
        }
        
        block = self.get_block(x, y, z)
        if block is None:
            return []
        
        for face, (nx, ny, nz) in neighbors.items():
            neighbor = self.get_block(nx, ny, nz)
            
            if neighbor is None:
                # Face is visible
                light = self._get_light_level(x, y, z, face)
                visible.append((face, light))
            elif not neighbor.is_opaque() and block.is_opaque():
                # Transparent neighbor, face might be visible
                light = self._get_light_level(x, y, z, face)
                visible.append((face, light))
        
        return visible
    
    def _get_light_level(self, x: int, y: int, z: int, face: str) -> int:
        """Calculate light level for a face."""
        # Simplified - would use actual light propagation
        return self.sky_light[self._get_index(x, y, z)]
    
    def _get_face_vertices(self, x: int, y: int, z: int, face: str, block: Block, light: int) -> List:
        """Get vertices for a block face."""
        # Face definitions
        face_data = {
            'top': {'verts': [0,1,0, 1,1,0, 1,1,1, 0,1,0, 1,1,1, 0,1,1], 'uv': [0,0,1,0,1,1,0,0,1,1,0,1]},
            'bottom': {'verts': [0,0,0, 1,0,1, 1,0,0, 0,0,0, 0,0,1, 1,0,1], 'uv': [0,0,1,1,1,0,0,0,0,1,1,1]},
            'front': {'verts': [0,0,1, 1,0,1, 1,1,1, 0,0,1, 1,1,1, 0,1,1], 'uv': [0,0,1,0,1,1,0,0,1,1,0,1]},
            'back': {'verts': [1,0,0, 0,0,0, 0,1,0, 1,0,0, 0,1,0, 1,1,0], 'uv': [0,0,1,0,1,1,0,0,1,1,0,1]},
            'right': {'verts': [1,0,1, 1,0,0, 1,1,0, 1,0,1, 1,1,0, 1,1,1], 'uv': [0,0,1,0,1,1,0,0,1,1,0,1]},
            'left': {'verts': [0,0,0, 0,0,1, 0,1,1, 0,0,0, 0,1,1, 0,1,0], 'uv': [0,0,1,0,1,1,0,0,1,1,0,1]},
        }
        
        data = face_data[face]
        verts = data['verts']
        uvs = data['uv']
        tex = block.get_texture_id(face)
        
        vertices = []
        for i in range(6):
            vertices.extend([x + verts[i*3], y + verts[i*3+1], z + verts[i*3+2]])
            vertices.extend([uvs[i*2] * 0.0625, uvs[i*2+1] * 0.0625])  # 1/16 for texture atlas
            vertices.append(float(tex))
            vertices.append(float(light))
        
        return vertices
    
    def save(self, path: str) -> None:
        """Save chunk to file in binary format."""
        import os
        
        os.makedirs(path, exist_ok=True)
        chunk_file = os.path.join(path, f"chunk_{self.position.x}_{self.position.z}.bin")
        
        with open(chunk_file, 'wb') as f:
            # Write header
            f.write(struct.pack('ii', self.position.x, self.position.z))
            
            # Write block data
            for i in range(CHUNK_VOLUME):
                f.write(struct.pack('H', self.block_data[i]['type']))
                f.write(struct.pack('B', self.block_data[i]['metadata']))
            
            # Write light data
            f.write(self.sky_light.tobytes())
            f.write(self.block_light.tobytes())
            
            # Write height map
            f.write(self.height_map.tobytes())
    
    @classmethod
    def load(cls, position: ChunkPosition, path: str) -> 'Chunk':
        """Load chunk from file."""
        chunk_file = os.path.join(path, f"chunk_{position.x}_{position.z}.bin")
        
        if not os.path.exists(chunk_file):
            return None
        
        chunk = cls(position, generate=False)
        
        with open(chunk_file, 'rb') as f:
            # Read header
            x, z = struct.unpack('ii', f.read(8))
            position = ChunkPosition(x, z)
            
            # Read block data
            for i in range(CHUNK_VOLUME):
                block_type = struct.unpack('H', f.read(2))[0]
                metadata = struct.unpack('B', f.read(1))[0]
                chunk.block_data[i]['type'] = block_type
                chunk.block_data[i]['metadata'] = metadata
            
            # Read light data
            chunk.sky_light = np.frombuffer(f.read(CHUNK_VOLUME), dtype=np.uint8)
            chunk.block_light = np.frombuffer(f.read(CHUNK_VOLUME), dtype=np.uint8)
            
            # Read height map
            chunk.height_map = np.frombuffer(f.read(CHUNK_WIDTH * CHUNK_DEPTH * 2), dtype=np.int16)
        
        chunk.is_loaded = True
        chunk.is_dirty = False
        return chunk
    
    def tick(self) -> None:
        """Process random tick for blocks in chunk."""
        pass  # Would iterate through ticking blocks
    
    def is_empty(self) -> bool:
        """Check if chunk has no blocks."""
        for i in range(CHUNK_VOLUME):
            if self.block_data[i]['type'] != BlockType.AIR.value:
                return False
        return True
    
    def get_statistics(self) -> Dict:
        """Get chunk statistics."""
        block_counts = {}
        for i in range(CHUNK_VOLUME):
            block_type = BlockType(self.block_data[i]['type'])
            if block_type != BlockType.AIR:
                block_counts[block_type.name] = block_counts.get(block_type.name, 0) + 1
        
        return {
            'position': str(self.position),
            'block_count': sum(block_counts.values()),
            'block_types': block_counts,
            'is_modified': self.is_modified,
            'is_dirty': self.is_dirty,
        }
