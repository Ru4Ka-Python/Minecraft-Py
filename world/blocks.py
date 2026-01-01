"""
Block system for Minecraft clone.
Defines all block types with their properties, textures, and behaviors.
"""

from enum import Enum, auto
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from PIL import Image
import numpy as np

class BlockType(Enum):
    """Enumeration of all block types."""
    # Natural blocks
    AIR = auto()
    STONE = auto()
    GRASS = auto()
    DIRT = auto()
    COBBLESTONE = auto()
    BEDROCK = auto()
    SAND = auto()
    GRAVEL = auto()
    WATER = auto()
    LAVA = auto()
    
    # Ores
    COAL_ORE = auto()
    IRON_ORE = auto()
    GOLD_ORE = auto()
    REDSTONE_ORE = auto()
    LAPIS_ORE = auto()
    DIAMOND_ORE = auto()
    EMERALD_ORE = auto()
    
    # Wood/Flora
    OAK_LOG = auto()
    OAK_LEAVES = auto()
    SPRUCE_LOG = auto()
    SPRUCE_LEAVES = auto()
    BIRCH_LOG = auto()
    BIRCH_LEAVES = auto()
    PLANKS = auto()
    SAPLING = auto()
    FLOWER = auto()
    ROSE = auto()
    DEAD_BUSH = auto()
    MUSHROOM = auto()
    MUSHROOM_BLOCK = auto()
    SUGAR_CANE = auto()
    CACTUS = auto()
    
    # Utility blocks
    GLASS = auto()
    TNT = auto()
    CRAFTING_TABLE = auto()
    FURNACE = auto()
    CHEST = auto()
    BOOKSHELF = auto()
    FENCE = auto()
    FENCE_GATE = auto()
    DOOR = auto()
    TRAPDOOR = auto()
    TORCH = auto()
    LADDER = auto()
    RAIL = auto()
    LEVER = auto()
    BUTTON = auto()
    PRESSURE_PLATE = auto()
    SIGN = auto()
    
    # Wool
    WHITE_WOOL = auto()
    ORANGE_WOOL = auto()
    MAGENTA_WOOL = auto()
    LIGHT_BLUE_WOOL = auto()
    YELLOW_WOOL = auto()
    LIME_WOOL = auto()
    PINK_WOOL = auto()
    GRAY_WOOL = auto()
    LIGHT_GRAY_WOOL = auto()
    CYAN_WOOL = auto()
    PURPLE_WOOL = auto()
    BLUE_WOOL = auto()
    BROWN_WOOL = auto()
    GREEN_WOOL = auto()
    RED_WOOL = auto()
    BLACK_WOOL = auto()


class BlockMaterial(Enum):
    """Block material properties."""
    AIR = 0
    SOLID = 1
    LIQUID = 2
    TRANSPARENT = 3
    LEAVES = 4
    FIRE = 5


@dataclass
class Block:
    """Block data class."""
    block_type: BlockType
    metadata: int = 0
    light_level: int = 0
    sky_light: int = 15
    
    # Dynamic properties
    tick_count: int = 0
    is_ticking: bool = False
    
    def is_opaque(self) -> bool:
        """Check if block is fully opaque."""
        opaque_types = {
            BlockType.STONE, BlockType.GRASS, BlockType.DIRT,
            BlockType.COBBLESTONE, BlockType.BEDROCK, BlockType.SAND,
            BlockType.GRAVEL, BlockType.COAL_ORE, BlockType.IRON_ORE,
            BlockType.GOLD_ORE, BlockType.REDSTONE_ORE, BlockType.LAPIS_ORE,
            BlockType.DIAMOND_ORE, BlockType.EMERALD_ORE, BlockType.OAK_LOG,
            BlockType.SPRUCE_LOG, BlockType.BIRCH_LOG, BlockType.PLANKS,
            BlockType.BOOKSHELF, BlockType.MUSHROOM_BLOCK, BlockType.CHEST,
            BlockType.TNT, BlockType.CRAFTING_TABLE, BlockType.FURNACE,
            BlockType.WHITE_WOOL, BlockType.ORANGE_WOOL, BlockType.MAGENTA_WOOL,
            BlockType.LIGHT_BLUE_WOOL, BlockType.YELLOW_WOOL, BlockType.LIME_WOOL,
            BlockType.PINK_WOOL, BlockType.GRAY_WOOL, BlockType.LIGHT_GRAY_WOOL,
            BlockType.CYAN_WOOL, BlockType.PURPLE_WOOL, BlockType.BLUE_WOOL,
            BlockType.BROWN_WOOL, BlockType.GREEN_WOOL, BlockType.RED_WOOL,
            BlockType.BLACK_WOOL, BlockType.CACTUS,
        }
        return self.block_type in opaque_types
    
    def is_transparent(self) -> bool:
        """Check if block is transparent (allows light through)."""
        transparent_types = {
            BlockType.AIR, BlockType.GLASS, BlockType.LEAVES,
            BlockType.SAPLING, BlockType.FLOWER, BlockType.ROSE,
            BlockType.DEAD_BUSH, BlockType.MUSHROOM, BlockType.MUSHROOM_BLOCK,
            BlockType.TORCH, BlockType.FENCE, BlockType.FENCE_GATE,
            BlockType.DOOR, BlockType.TRAPDOOR, BlockType.LADDER,
            BlockType.RAIL, BlockType.LEVER, BlockType.BUTTON,
            BlockType.PRESSURE_PLATE, BlockType.SIGN, BlockType.SUGAR_CANE,
            BlockType.WATER, BlockType.LAVA,
        }
        return self.block_type in transparent_types
    
    def is_liquid(self) -> bool:
        """Check if block is a liquid."""
        return self.block_type in (BlockType.WATER, BlockType.LAVA)
    
    def is_solid(self) -> bool:
        """Check if block has collision."""
        return self.block_type not in (BlockType.AIR, BlockType.WATER, BlockType.LAVA, BlockType.FIRE)
    
    def get_material(self) -> BlockMaterial:
        """Get block material type."""
        if self.block_type == BlockType.AIR:
            return BlockMaterial.AIR
        elif self.block_type in (BlockType.WATER, BlockType.LAVA):
            return BlockMaterial.LIQUID
        elif self.block_type == BlockType.GLASS:
            return BlockMaterial.TRANSPARENT
        elif self.block_type in (BlockType.OAK_LEAVES, BlockType.SPRUCE_LEAVES, BlockType.BIRCH_LEAVES):
            return BlockMaterial.LEAVES
        elif self.block_type == BlockType.FIRE:
            return BlockMaterial.FIRE
        else:
            return BlockMaterial.SOLID
    
    def get_texture_id(self, face: str) -> int:
        """Get texture ID for a block face."""
        type_textures = {
            BlockType.GRASS: {'top': 0, 'bottom': 2, 'side': 3},
            BlockType.DIRT: {'all': 2},
            BlockType.STONE: {'all': 1},
            BlockType.COBBLESTONE: {'all': 16},
            BlockType.BEDROCK: {'all': 17},
            BlockType.SAND: {'all': 18},
            BlockType.GRAVEL: {'all': 19},
            BlockType.WATER: {'all': 207},  # Animated
            BlockType.LAVA: {'all': 225},  # Animated
            BlockType.COAL_ORE: {'all': 20},
            BlockType.IRON_ORE: {'all': 21},
            BlockType.GOLD_ORE: {'all': 22},
            BlockType.REDSTONE_ORE: {'all': 23},
            BlockType.LAPIS_ORE: {'all': 24},
            BlockType.DIAMOND_ORE: {'all': 25},
            BlockType.EMERALD_ORE: {'all': 26},
            BlockType.OAK_LOG: {'top': 20, 'side': 21},
            BlockType.SPRUCE_LOG: {'top': 20, 'side': 22},
            BlockType.BIRCH_LOG: {'top': 20, 'side': 23},
            BlockType.OAK_LEAVES: {'all': 4},
            BlockType.SPRUCE_LEAVES: {'all': 29},
            BlockType.BIRCH_LEAVES: {'all': 30},
            BlockType.PLANKS: {'all': 4},
            BlockType.GLASS: {'all': 49},
            BlockType.TNT: {'top': 226, 'bottom': 227, 'side': 225},
            BlockType.CRAFTING_TABLE: {'top': 58, 'side': 57, 'front': 56},
            BlockType.FURNACE: {'top': 62, 'side': 61, 'front': 63},
            BlockType.CHEST: {'all': 54},
            BlockType.BOOKSHELF: {'all': 47},
            BlockType.FENCE: {'all': 85},
            BlockType.TORCH: {'all': 50},
            BlockType.LEVER: {'all': 69},
            BlockType.BUTTON: {'all': 77},
            BlockType.PRESSURE_PLATE: {'all': 72},
            BlockType.WHITE_WOOL: {'all': 64},
            BlockType.SUGAR_CANE: {'all': 73},
            BlockType.CACTUS: {'top': 70, 'side': 71, 'bottom': 69},
            BlockType.SAPLING: {'all': 15},
            BlockType.FLOWER: {'all': 13},
            BlockType.ROSE: {'all': 12},
        }
        
        if self.block_type not in type_textures:
            return 1  # Default to stone
        
        face_map = type_textures[self.block_type]
        
        if 'all' in face_map:
            return face_map['all']
        elif face in face_map:
            return face_map[face]
        elif 'side' in face_map and face in ('front', 'back', 'left', 'right'):
            return face_map['side']
        else:
            return 1  # Default
    
    def get_top_texture(self) -> int:
        """Get top face texture ID."""
        return self.get_texture_id('top')
    
    def get_bottom_texture(self) -> int:
        """Get bottom face texture ID."""
        return self.get_texture_id('bottom')
    
    def get_side_texture(self) -> int:
        """Get side face texture ID."""
        return self.get_texture_id('side')
    
    def get_light_emission(self) -> int:
        """Get light emission level (0-15)."""
        light_emitters = {
            BlockType.TORCH: 14,
            BlockType.LAVA: 15,
            BlockType.FIRE: 15,
            BlockType.GLOWSTONE: 15,
            BlockType.JACK_O_LANTERN: 15,
        }
        return light_emitters.get(self.block_type, 0)
    
    def get_hardness(self) -> float:
        """Get block hardness (mining time)."""
        hardness = {
            BlockType.BEDROCK: -1,
            BlockType.STONE: 1.5,
            BlockType.COBBLESTONE: 2.0,
            BlockType.DIRT: 0.5,
            BlockType.GRASS: 0.5,
            BlockType.SAND: 0.5,
            BlockType.GRAVEL: 0.6,
            BlockType.WOOD: 2.0,
            BlockType.PLANKS: 2.0,
            BlockType.OAK_LOG: 2.0,
            BlockType.STONE_BRICKS: 1.5,
            BlockType.GLASS: 0.3,
            BlockType.STONE_BUTTON: 0.5,
            BlockType.LEVER: 0.5,
        }
        return hardness.get(self.block_type, 3.0)
    
    def get_tool_efficiency(self, tool_type: str) -> float:
        """Get mining speed multiplier for tool type."""
        tool_speeds = {
            'pickaxe': {
                BlockType.STONE: 1.5,
                BlockType.COBBLESTONE: 1.5,
                BlockType.IRON_ORE: 1.5,
                BlockType.GOLD_ORE: 1.5,
                BlockType.DIAMOND_ORE: 1.5,
                BlockType.REDSTONE_ORE: 1.5,
                BlockType.LAPIS_ORE: 1.5,
                BlockType.EMERALD_ORE: 1.5,
                BlockType.COAL_ORE: 1.5,
            },
            'shovel': {
                BlockType.DIRT: 1.5,
                BlockType.GRASS: 1.5,
                BlockType.SAND: 1.5,
                BlockType.GRAVEL: 1.5,
            },
            'axe': {
                BlockType.OAK_LOG: 1.5,
                BlockType.PLANKS: 1.5,
                BlockType.WOOD: 1.5,
            },
        }
        
        tool_dict = tool_speeds.get(tool_type, {})
        return tool_dict.get(self.block_type, 1.0)
    
    def get_drop_items(self) -> List[Tuple['Item', int]]:
        """Get items dropped when block is broken."""
        drops = {
            BlockType.GRASS: [(BlockType.DIRT, 1)],
            BlockType.DIRT: [(BlockType.DIRT, 1)],
            BlockType.STONE: [(BlockType.COBBLESTONE, 1)],
            BlockType.COBBLESTONE: [(BlockType.COBBLESTONE, 1)],
            BlockType.SAND: [(BlockType.SAND, 1)],
            BlockType.GRAVEL: [(BlockType.GRAVEL, 1)],
            BlockType.COAL_ORE: [(BlockType.COAL, 1)],
            BlockType.IRON_ORE: [(BlockType.IRON_ORE, 1)],  # Silk touch
            BlockType.GOLD_ORE: [(BlockType.GOLD_ORE, 1)],
            BlockType.REDSTONE_ORE: [(BlockType.REDSTONE, 4)],
            BlockType.LAPIS_ORE: [(BlockType.LAPIS, 4)],
            BlockType.DIAMOND_ORE: [(BlockType.DIAMOND, 1)],
            BlockType.EMERALD_ORE: [(BlockType.EMERALD, 1)],
            BlockType.OAK_LEAVES: [(BlockType.SAPLING, 0.05), (BlockType.APPLE, 0.02)],
            BlockType.OAK_LOG: [(BlockType.OAK_LOG, 1)],
            BlockType.SPRUCE_LOG: [(BlockType.SPRUCE_LOG, 1)],
            BlockType.BIRCH_LOG: [(BlockType.BIRCH_LOG, 1)],
            BlockType.PLANKS: [(BlockType.PLANKS, 1)],
            BlockType.GLASS: [],  # No drops
            BlockType.TNT: [],  # No drops
            BlockType.STONE_BUTTON: [],  # No drops
            BlockType.LEVER: [],  # No drops
        }
        return drops.get(self.block_type, [(self.block_type, 1)])
    
    def tick(self) -> None:
        """Process random tick for this block."""
        self.tick_count += 1
        
        # Handle block-specific tick behavior
        if self.block_type == BlockType.FIRE:
            self._tick_fire()
        elif self.block_type == BlockType.MUSHROOM:
            self._tick_mushroom()
        elif self.block_type == BlockType.SUGAR_CANE:
            self._tick_sugar_cane()
        elif self.block_type == BlockType.CACTUS:
            self._tick_cactus()
    
    def _tick_fire(self) -> None:
        """Fire tick logic."""
        pass
    
    def _tick_mushroom(self) -> None:
        """Mushroom spread logic."""
        pass
    
    def _tick_sugar_cane(self) -> None:
        """Sugar cane growth logic."""
        pass
    
    def _tick_cactus(self) -> None:
        """Cactus growth logic."""
        pass
    
    def to_dict(self) -> Dict:
        """Serialize block to dictionary."""
        return {
            'type': self.block_type.name,
            'metadata': self.metadata,
            'light_level': self.light_level,
            'sky_light': self.sky_light,
            'tick_count': self.tick_count,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Block':
        """Deserialize block from dictionary."""
        return cls(
            block_type=BlockType[data['type']],
            metadata=data.get('metadata', 0),
            light_level=data.get('light_level', 0),
            sky_light=data.get('sky_light', 15),
            tick_count=data.get('tick_count', 0),
        )


class BlockRegistry:
    """Registry for block types and their properties."""
    
    _blocks: Dict[BlockType, Dict] = {}
    
    @classmethod
    def register(cls, block_type: BlockType, properties: Dict) -> None:
        """Register block properties."""
        cls._blocks[block_type] = properties
    
    @classmethod
    def get_properties(cls, block_type: BlockType) -> Dict:
        """Get block properties."""
        return cls._blocks.get(block_type, {})
    
    @classmethod
    def get_all_blocks(cls) -> List[BlockType]:
        """Get all registered block types."""
        return list(cls._blocks.keys())


# Initialize block registry
def _init_block_registry():
    """Initialize the block registry with default properties."""
    for block_type in BlockType:
        BlockRegistry.register(block_type, {'name': block_type.name})

_init_block_registry()
