import pickle
import os
import zlib

class WorldStorage:
    def __init__(self, world_dir):
        self.world_dir = world_dir
        if not os.path.exists(world_dir):
            os.makedirs(world_dir)

    def save_chunk(self, x, z, voxels):
        filename = os.path.join(self.world_dir, f'chunk_{x}_{z}.dat')
        data = voxels.tobytes()
        compressed_data = zlib.compress(data)
        with open(filename, 'wb') as f:
            f.write(compressed_data)

    def load_chunk(self, x, z, shape):
        filename = os.path.join(self.world_dir, f'chunk_{x}_{z}.dat')
        if not os.path.exists(filename):
            return None
        with open(filename, 'rb') as f:
            compressed_data = f.read()
        data = zlib.decompress(compressed_data)
        import numpy as np
        return np.frombuffer(data, dtype=np.uint8).reshape(shape)
