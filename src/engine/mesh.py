import numpy as np
import moderngl as mgl

class Mesh:
    def __init__(self, ctx, program):
        self.ctx = ctx
        self.program = program
        self.vbo = None
        self.vao = None
        self.format = '3f 2f 1f'
        self.attrs = ['in_position', 'in_tex_coord', 'in_shading']

    def update_mesh(self, vertices):
        if self.vbo:
            self.vbo.release()
        if self.vao:
            self.vao.release()
            
        if not vertices:
            return

        vertices = np.array(vertices, dtype='f4')
        self.vbo = self.ctx.buffer(vertices)
        self.vao = self.ctx.vertex_array(self.program, [(self.vbo, self.format, *self.attrs)])

    def render(self):
        if self.vao:
            self.vao.render()

class ChunkMesh(Mesh):
    def __init__(self, ctx, program, voxels):
        super().__init__(ctx, program)
        self.voxels = voxels
        self.generate_mesh()

    def generate_mesh(self):
        # Implementation of Greedy Meshing
        vertices = []
        dims = self.voxels.shape
        
        # Iterate over each dimension
        for d in range(3):
            u = (d + 1) % 3
            v = (d + 2) % 3
            
            x = [0, 0, 0]
            q = [0, 0, 0]
            q[d] = 1
            
            mask = np.zeros(dims[u] * dims[v], dtype=np.int32)
            
            for x[d] in range(-1, dims[d]):
                # Compute mask
                n = 0
                for x[v] in range(dims[v]):
                    for x[u] in range(dims[u]):
                        a = self.get_voxel(x[0], x[1], x[2])
                        b = self.get_voxel(x[0] + q[0], x[1] + q[1], x[2] + q[2])
                        
                        if (a != 0) == (b != 0):
                            mask[n] = 0
                        elif a != 0:
                            mask[n] = a
                        else:
                            mask[n] = -b
                        n += 1
                
                # Generate mesh from mask
                n = 0
                for j in range(dims[v]):
                    for i in range(dims[u]):
                        if mask[n] != 0:
                            w, h = 1, 1
                            val = mask[n]
                            
                            # Find width
                            while i + w < dims[u] and mask[n + w] == val:
                                w += 1
                            
                            # Find height
                            done = False
                            while j + h < dims[v]:
                                for k in range(w):
                                    if mask[n + k + h * dims[u]] != val:
                                        done = True
                                        break
                                if done: break
                                h += 1
                                
                            # Add quad
                            x[u], x[v] = i, j
                            du, dv = [0,0,0], [0,0,0]
                            du[u], dv[v] = w, h
                            
                            self.add_quad(vertices, x, du, dv, val, d)
                            
                            # Zero out mask
                            for l in range(h):
                                for k in range(w):
                                    mask[n + k + l * dims[u]] = 0
                        n += 1
                        
        self.update_mesh(vertices)

    def get_voxel(self, x, y, z):
        if 0 <= x < self.voxels.shape[0] and 0 <= y < self.voxels.shape[1] and 0 <= z < self.voxels.shape[2]:
            return self.voxels[x, y, z]
        return 0

    def add_quad(self, vertices, x, du, dv, val, d):
        # Simplified quad addition for greedy meshing
        block_id = abs(val)
        u, v = (block_id % 16) / 16, (block_id // 16) / 16
        tw, th = 1/16, 1/16 # This should be adjusted for quad size but requires tiling texture
        
        # In a real engine, we'd use a shader that handles tiling or atlas coordinates
        # For this clone, we'll just use the block texture stretched (not ideal but works for greedy demo)
        
        shading = 1.0
        if d == 1: shading = 1.0 if val > 0 else 0.5
        elif d == 0: shading = 0.8
        else: shading = 0.6
        
        p0 = (x[0], x[1], x[2])
        p1 = (x[0] + du[0], x[1] + du[1], x[2] + du[2])
        p2 = (x[0] + du[0] + dv[0], x[1] + du[1] + dv[1], x[2] + du[2] + dv[2])
        p3 = (x[0] + dv[0], x[1] + dv[1], x[2] + dv[2])
        
        v_data = [
            *p0, u, v, shading,
            *p1, u+tw, v, shading,
            *p2, u+tw, v+th, shading,
            *p0, u, v, shading,
            *p2, u+tw, v+th, shading,
            *p3, u, v+th, shading,
        ]
        vertices.extend(v_data)
