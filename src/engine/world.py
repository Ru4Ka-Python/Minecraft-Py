import numpy as np
from noise import pnoise2, pnoise3

class WorldGenerator:
    def __init__(self, seed=42):
        self.seed = seed
        self.scale = 100.0
        self.octaves = 6
        self.persistence = 0.5
        self.lacunarity = 2.0

    def generate_chunk_data(self, chunk_x, chunk_z, chunk_size=16, height=128):
        voxels = np.zeros((chunk_size, height, chunk_size), dtype=np.uint8)
        
        for x in range(chunk_size):
            for z in range(chunk_size):
                world_x = chunk_x * chunk_size + x
                world_z = chunk_z * chunk_size + z
                
                # Height map
                h = pnoise2(world_x / self.scale, world_z / self.scale, 
                            octaves=self.octaves, 
                            persistence=self.persistence, 
                            lacunarity=self.lacunarity, 
                            base=self.seed)
                
                h = int((h + 1) / 2 * 64) + 32
                
                # Fill voxels
                voxels[x, :h-5, z] = 1 # Stone
                voxels[x, h-5:h-1, z] = 2 # Dirt
                voxels[x, h-1:h, z] = 3 # Grass
                
                # Bedrock at the bottom
                bedrock_h = np.random.randint(1, 6)
                voxels[x, :bedrock_h, z] = 4 # Bedrock
                
        return voxels
