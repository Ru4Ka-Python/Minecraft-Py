import numpy as np
from collections import deque

class LightEngine:
    def __init__(self, world):
        self.world = world
        self.light_map = np.zeros(world.voxels.shape, dtype=np.uint8)

    def propagate_sunlight(self):
        queue = deque()
        sx, sy, sz = self.world.voxels.shape
        
        # Fill top layer with sunlight
        for x in range(sx):
            for z in range(sz):
                for y in range(sy - 1, -1, -1):
                    if self.world.voxels[x, y, z] == 0:
                        self.light_map[x, y, z] = 15
                        queue.append((x, y, z))
                    else:
                        break # Block reached
        
        self.bfs_propagate(queue)

    def bfs_propagate(self, queue):
        sx, sy, sz = self.world.voxels.shape
        directions = [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1)]
        
        while queue:
            x, y, z = queue.popleft()
            curr_light = self.light_map[x, y, z]
            
            if curr_light <= 1: continue
            
            for dx, dy, dz in directions:
                nx, ny, nz = x + dx, y + dy, z + dz
                
                if 0 <= nx < sx and 0 <= ny < sy and 0 <= nz < sz:
                    if self.world.voxels[nx, ny, nz] == 0: # Only air/transparent blocks
                        if self.light_map[nx, ny, nz] < curr_light - 1:
                            self.light_map[nx, ny, nz] = curr_light - 1
                            queue.append((nx, ny, nz))
