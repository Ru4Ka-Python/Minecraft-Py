"""
Item system for Minecraft clone.
Defines all item types with their properties.
"""

from enum import Enum, auto
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from PIL import Image

from world.blocks import BlockType


class ItemType(Enum):
    """Enumeration of all item types."""
    # Tools
    WOODEN_PICKAXE = auto()
    STONE_PICKAXE = auto()
    IRON_PICKAXE = auto()
    GOLDEN_PICKAXE = auto()
    DIAMOND_PICKAXE = auto()
    
    WOODEN_SHOVEL = auto()
    STONE_SHOVEL = auto()
    IRON_SHOVEL = auto()
    GOLDEN_SHOVEL = auto()
    DIAMOND_SHOVEL = auto()
    
    WOODEN_AXE = auto()
    STONE_AXE = auto()
    IRON_AXE = auto()
    GOLDEN_AXE = auto()
    DIAMOND_AXE = auto()
    
    WOODEN_SWORD = auto()
    STONE_SWORD = auto()
    IRON_SWORD = auto()
    GOLDEN_SWORD = auto()
    DIAMOND_SWORD = auto()
    
    # Materials
    STICK = auto()
    COAL = auto()
    CHARCOAL = auto()
    IRON_INGOT = auto()
    GOLD_INGOT = auto()
    DIAMOND = auto()
    EMERALD = auto()
    REDSTONE = auto()
    LAPIS_LAZULI = auto()
    
    # Food
    APPLE = auto()
    BREAD = auto()
    RAW_PORKCHOP = auto()
    COOKED_PORKCHOP = auto()
    RAW_BEEF = auto()
    STEAK = auto()
    RAW_CHICKEN = auto()
    COOKED_CHICKEN = auto()
    ROTTEN_FLESH = auto()
    GOLDEN_APPLE = auto()
    MELON_SLICE = auto()
    CARROT = auto()
    POTATO = auto()
    BAKED_POTATO = auto()
    POISONOUS_POTATO = auto()
    BEETROOT = auto()
    BEETROOT_SOUP = auto()
    MUSHROOM_STEW = auto()
    
    # Blocks (as items)
    DIRT = auto()
    COBBLESTONE = auto()
    SAND = auto()
    GRAVEL = auto()
    PLANKS = auto()
    OAK_LOG = auto()
    SPRUCE_LOG = auto()
    BIRCH_LOG = auto()
    STONE = auto()
    OAK_LEAVES = auto()
    GLASS = auto()
    
    # Plants
    SAPLING = auto()
    OAK_SAPLING = auto()
    SPRUCE_SAPLING = auto()
    BIRCH_SAPLING = auto()
    FLOWER = auto()
    ROSE = auto()
    DEAD_BUSH = auto()
    SUGAR_CANE = auto()
    CACTUS = auto()
    MELON = auto()
    PUMPKIN = auto()
    VINE = auto()
    
    # Crafting items
    CRAFTING_TABLE = auto()
    FURNACE = auto()
    CHEST = auto()
    BOOKSHELF = auto()
    FENCE = auto()
    FENCE_GATE = auto()
    DOOR = auto()
    TRAPDOOR = auto()
    LADDER = auto()
    TORCH = auto()
    WORKBENCH = auto()
    
    # Utility
    BOW = auto()
    ARROW = auto()
    FISHING_ROD = auto()
    FLINT_AND_STEEL = auto()
    COMPASS = auto()
    CLOCK = auto()
    MAP = auto()
    SHEARS = auto()
    
    # Special
    EGG = auto()
    SNOWBALL = auto()
    ENDER_PEARL = auto()
    BLAZE_ROD = auto()
    GHAST_TEAR = auto()
    GOLD_NUGGET = auto()
    IRON_NUGGET = auto()
    SLIME_BALL = auto()
    BONE = auto()
    BONE_MEAL = auto()
    INK_SAC = auto()
    RABBIT_FOOT = auto()


class ToolType(Enum):
    """Tool material types."""
    WOOD = 1
    STONE = 2
    IRON = 3
    GOLD = 4
    DIAMOND = 5


@dataclass
class ToolProperties:
    """Tool properties."""
    tool_type: str  # 'pickaxe', 'shovel', 'axe', 'sword'
    material: ToolType
    damage: int
    speed: float
    durability: int


@dataclass
class Item:
    """Item data class."""
    item_type: ItemType
    count: int = 1
    damage: int = 0
    enchantments: Dict = None
    
    def __post_init__(self):
        if self.enchantments is None:
            self.enchantments = {}
    
    @property
    def max_stack(self) -> int:
        """Get maximum stack size."""
        stack_sizes = {
            # 64-stack items
            ItemType.DIRT, ItemType.COBBLESTONE, ItemType.SAND, ItemType.GRAVEL,
            ItemType.PLANKS, ItemType.STONE, ItemType.OAK_LOG, ItemType.SPRUCE_LOG,
            ItemType.BIRCH_LOG, ItemType.OAK_LEAVES, ItemType.GLASS,
            ItemType.COAL, ItemType.CHARCOAL, ItemType.IRON_INGOT, ItemType.GOLD_INGOT,
            ItemType.DIAMOND, ItemType.EMERALD, ItemType.REDSTONE, ItemType.LAPIS_LAZULI,
            ItemType.BREAD, ItemType.RAW_PORKCHOP, ItemType.COOKED_PORKCHOP,
            ItemType.RAW_BEEF, ItemType.STEAK, ItemType.RAW_CHICKEN, ItemType.COOKED_CHICKEN,
            ItemType.ROTTEN_FLESH, ItemType.MELON_SLICE, ItemType.CARROT, ItemType.POTATO,
            ItemType.BAKED_POTATO, ItemType.POISONOUS_POTATO, ItemType.BEETROOT,
            ItemType.SAPLING, ItemType.OAK_SAPLING, ItemType.SPRUCE_SAPLING, ItemType.BIRCH_SAPLING,
            ItemType.FLOWER, ItemType.ROSE, ItemType.SUGAR_CANE, ItemType.CACTUS,
            ItemType.TORCH, ItemType.ARROW, ItemType.BONE, ItemType.BONE_MEAL,
            ItemType.GOLD_NUGGET, ItemType.IRON_NUGGET, ItemType.SLIME_BALL,
            # 16-stack items
            ItemType.STICK, ItemType.FENCE, ItemType.FENCE_GATE, ItemType.LADDER,
            # 1-stack items
            ItemType.WOODEN_PICKAXE, ItemType.STONE_PICKAXE, ItemType.IRON_PICKAXE,
            ItemType.GOLDEN_PICKAXE, ItemType.DIAMOND_PICKAXE, ItemType.WOODEN_SHOVEL,
            ItemType.STONE_SHOVEL, ItemType.IRON_SHOVEL, ItemType.GOLDEN_SHOVEL,
            ItemType.DIAMOND_SHOVEL, ItemType.WOODEN_AXE, ItemType.STONE_AXE,
            ItemType.IRON_AXE, ItemType.GOLDEN_AXE, ItemType.DIAMOND_AXE,
            ItemType.WOODEN_SWORD, ItemType.STONE_SWORD, ItemType.IRON_SWORD,
            ItemType.GOLDEN_SWORD, ItemType.DIAMOND_SWORD, ItemType.BOW,
            ItemType.FISHING_ROD, ItemType.FLINT_AND_STEEL, ItemType.COMPASS,
            ItemType.CLOCK, ItemType.MAP, ItemType.SHEARS, ItemType.CRAFTING_TABLE,
            ItemType.FURNACE, ItemType.CHEST, ItemType.BOOKSHELF, ItemType.DOOR,
            ItemType.TRAPDOOR, ItemType.SHEARS, ItemType.EGG, ItemType.SNOWBALL,
            ItemType.ENDER_PEARL, ItemType.BLAZE_ROD, ItemType.GHAST_TEAR,
            ItemType.RABBIT_FOOT, ItemType.INK_SAC, ItemType.MUSHROW_STEW,
        }
        
        if self.item_type in stack_sizes:
            return 64
        
        # Default stack size
        return 16
    
    def can_stack_with(self, other: 'Item') -> bool:
        """Check if two items can stack."""
        return self.item_type == other.item_type and self.count < self.max_stack
    
    def get_name(self) -> str:
        """Get display name."""
        # Format enum name
        name = self.item_type.name.replace('_', ' ').title()
        
        # Apply damage prefix if damaged
        if self.damage > 0:
            name = f"{name} {self.damage}"
        
        return name
    
    def get_block_type(self) -> Optional[BlockType]:
        """Get block type if item is a block."""
        type_map = {
            ItemType.DIRT: BlockType.DIRT,
            ItemType.COBBLESTONE: BlockType.COBBLESTONE,
            ItemType.SAND: BlockType.SAND,
            ItemType.GRAVEL: BlockType.GRAVEL,
            ItemType.PLANKS: BlockType.PLANKS,
            ItemType.OAK_LOG: BlockType.OAK_LOG,
            ItemType.SPRUCE_LOG: BlockType.SPRUCE_LOG,
            ItemType.BIRCH_LOG: BlockType.BIRCH_LOG,
            ItemType.STONE: BlockType.STONE,
            ItemType.OAK_LEAVES: BlockType.OAK_LEAVES,
            ItemType.GLASS: BlockType.GLASS,
            ItemType.SAPLING: BlockType.SAPLING,
            ItemType.OAK_SAPLING: BlockType.SAPLING,
            ItemType.SPRUCE_SAPLING: BlockType.SAPLING,
            ItemType.BIRCH_SAPLING: BlockType.SAPLING,
            ItemType.FLOWER: BlockType.FLOWER,
            ItemType.ROSE: BlockType.ROSE,
            ItemType.DEAD_BUSH: BlockType.DEAD_BUSH,
            ItemType.SUGAR_CANE: BlockType.SUGAR_CANE,
            ItemType.CACTUS: BlockType.CACTUS,
            ItemType.TORCH: BlockType.TORCH,
            ItemType.CRAFTING_TABLE: BlockType.CRAFTING_TABLE,
            ItemType.FURNACE: BlockType.FURNACE,
            ItemType.CHEST: BlockType.CHEST,
            ItemType.BOOKSHELF: BlockType.BOOKSHELF,
            ItemType.FENCE: BlockType.FENCE,
            ItemType.FENCE_GATE: BlockType.FENCE_GATE,
            ItemType.DOOR: BlockType.DOOR,
            ItemType.TRAPDOOR: BlockType.TRAPDOOR,
            ItemType.LADDER: BlockType.LADDER,
        }
        
        return type_map.get(self.item_type)
    
    def get_tool_properties(self) -> Optional[ToolProperties]:
        """Get tool properties if item is a tool."""
        tool_types = {
            ItemType.WOODEN_PICKAXE: ('pickaxe', ToolType.WOODEN, 2, 2.0, 59),
            ItemType.STONE_PICKAXE: ('pickaxe', ToolType.STONE, 3, 4.0, 131),
            ItemType.IRON_PICKAXE: ('pickaxe', ToolType.IRON, 3, 6.0, 250),
            ItemType.GOLDEN_PICKAXE: ('pickaxe', ToolType.GOLD, 1, 12.0, 32),
            ItemType.DIAMOND_PICKAXE: ('pickaxe', ToolType.DIAMOND, 3, 8.0, 1561),
            
            ItemType.WOODEN_SHOVEL: ('shovel', ToolType.WOODEN, 1, 2.0, 59),
            ItemType.STONE_SHOVEL: ('shovel', ToolType.STONE, 2, 4.0, 131),
            ItemType.IRON_SHOVEL: ('shovel', ToolType.IRON, 2, 6.0, 250),
            ItemType.GOLDEN_SHOVEL: ('shovel', ToolType.GOLD, 1, 12.0, 32),
            ItemType.DIAMOND_SHOVEL: ('shovel', ToolType.DIAMOND, 2, 8.0, 1561),
            
            ItemType.WOODEN_AXE: ('axe', ToolType.WOODEN, 3, 2.0, 59),
            ItemType.STONE_AXE: ('axe', ToolType.STONE, 4, 4.0, 131),
            ItemType.IRON_AXE: ('axe', ToolType.IRON, 4, 6.0, 250),
            ItemType.GOLDEN_AXE: ('axe', ToolType.GOLD, 3, 12.0, 32),
            ItemType.DIAMOND_AXE: ('axe', ToolType.DIAMOND, 4, 8.0, 1561),
            
            ItemType.WOODEN_SWORD: ('sword', ToolType.WOODEN, 4, 2.0, 59),
            ItemType.STONE_SWORD: ('sword', ToolType.STONE, 5, 4.0, 131),
            ItemType.IRON_SWORD: ('sword', ToolType.IRON, 6, 6.0, 250),
            ItemType.GOLDEN_SWORD: ('sword', ToolType.GOLD, 4, 12.0, 32),
            ItemType.DIAMOND_SWORD: ('sword', ToolType.DIAMOND, 7, 8.0, 1561),
        }
        
        if self.item_type in tool_types:
            data = tool_types[self.item_type]
            return ToolProperties(
                tool_type=data[0],
                material=data[1],
                damage=data[2] + self.damage,
                speed=data[3],
                durability=data[4]
            )
        
        return None
    
    def get_food_value(self) -> int:
        """Get food value if item is food."""
        food_values = {
            ItemType.APPLE: 4,
            ItemType.BREAD: 5,
            ItemType.COOKED_PORKCHOP: 8,
            ItemType.STEAK: 8,
            ItemType.COOKED_CHICKEN: 6,
            ItemType.ROTTEN_FLESH: 4,
            ItemType.GOLDEN_APPLE: 20,
            ItemType.MELON_SLICE: 2,
            ItemType.CARROT: 3,
            ItemType.BAKED_POTATO: 5,
            ItemType.POISONOUS_POTATO: 2,
            ItemType.BEETROOT: 3,
            ItemType.BEETROOT_SOUP: 6,
            ItemType.MUSHROOM_STEW: 6,
        }
        
        return food_values.get(self.item_type, 0)
    
    def get_texture_id(self) -> int:
        """Get texture ID for rendering."""
        # Map items to texture atlas positions
        texture_map = {
            ItemType.WOODEN_PICKAXE: 270,
            ItemType.STONE_PICKAXE: 271,
            ItemType.IRON_PICKAXE: 272,
            ItemType.GOLDEN_PICKAXE: 273,
            ItemType.DIAMOND_PICKAXE: 274,
            ItemType.WOODEN_SHOVEL: 269,
            ItemType.STONE_SHOVEL: 268,
            ItemType.IRON_SHOVEL: 267,
            ItemType.GOLDEN_SHOVEL: 266,
            ItemType.DIAMOND_SHOVEL: 265,
            ItemType.WOODEN_AXE: 275,
            ItemType.STONE_AXE: 276,
            ItemType.IRON_AXE: 277,
            ItemType.GOLDEN_AXE: 278,
            ItemType.DIAMOND_AXE: 279,
            ItemType.WOODEN_SWORD: 268,
            ItemType.STONE_SWORD: 267,
            ItemType.IRON_SWORD: 266,
            ItemType.GOLDEN_SWORD: 265,
            ItemType.DIAMOND_SWORD: 264,
            ItemType.STICK: 320,
            ItemType.COAL: 288,
            ItemType.IRON_INGOT: 289,
            ItemType.GOLD_INGOT: 290,
            ItemType.DIAMOND: 291,
            ItemType.REDSTONE: 293,
            ItemType.LAPIS_LAZULI: 292,
            ItemType.BREAD: 297,
            ItemType.APPLE: 260,
            ItemType.BOW: 261,
            ItemType.ARROW: 262,
        }
        
        return texture_map.get(self.item_type, 256)
    
    def use(self, player) -> bool:
        """Use item (consume if applicable)."""
        food_value = self.get_food_value()
        
        if food_value > 0:
            # Restore hunger
            player.state.hunger = min(20, player.state.hunger + food_value)
            self.count -= 1
            if self.count <= 0:
                return True  # Item consumed
            return False
        
        return False
    
    def copy(self) -> 'Item':
        """Create a copy of this item."""
        return Item(
            item_type=self.item_type,
            count=self.count,
            damage=self.damage,
            enchantments=self.enchantments.copy()
        )
    
    def to_dict(self) -> Dict:
        """Serialize item to dictionary."""
        return {
            'type': self.item_type.name,
            'count': self.count,
            'damage': self.damage,
            'enchantments': self.enchantments,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Item':
        """Deserialize item from dictionary."""
        return cls(
            item_type=ItemType[data['type']],
            count=data.get('count', 1),
            damage=data.get('damage', 0),
            enchantments=data.get('enchantments', {}),
        )


class ItemRegistry:
    """Registry for item types and their properties."""
    
    _items: Dict[ItemType, Dict] = {}
    
    @classmethod
    def register(cls, item_type: ItemType, properties: Dict) -> None:
        """Register item properties."""
        cls._items[item_type] = properties
    
    @classmethod
    def get_properties(cls, item_type: ItemType) -> Dict:
        """Get item properties."""
        return cls._items.get(item_type, {})


# Initialize item registry
def _init_item_registry():
    """Initialize the item registry."""
    for item_type in ItemType:
        ItemRegistry.register(item_type, {'name': item_type.name})

_init_item_registry()
