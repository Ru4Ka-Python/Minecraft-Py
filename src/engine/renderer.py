import pygame as pg
import moderngl as mgl
from engine.shaders import get_shader_program
from engine.camera import Camera
import glm

class Renderer:
    def __init__(self, game):
        self.game = game
        self.ctx = game.ctx
        self.program = get_shader_program(self.ctx)
        self.camera = Camera(position=(0, 10, 0))
        
        # Uniforms
        self.program['m_proj'].write(self.camera.get_projection_matrix(1280/720))
        self.program['m_view'].write(self.camera.get_view_matrix())
        self.program['m_model'].write(glm.mat4(1.0))
        self.program['u_fog_color'].write(glm.vec3(0.5, 0.7, 1.0))
        self.program['u_fog_density'].value = 0.01
        
        self.textures = {}
        self.load_textures()
        
    def load_textures(self):
        # Try to load terrain.png, fallback to something else if missing
        import os
        terrain_path = '/home/engine/project/assets/terrain.png'
        if not os.path.exists(terrain_path):
            # Fallback to items.png or something just to have a texture
            terrain_path = '/home/engine/project/assets/gui/items.png'
            
        self.textures['terrain'] = self.load_texture(terrain_path)
        self.textures['terrain'].use(location=0)
        self.program['u_texture_0'] = 0
        
        from engine.world import WorldGenerator
        from engine.mesh import ChunkMesh
        self.world_gen = WorldGenerator()
        voxels = self.world_gen.generate_chunk_data(0, 0)
        self.chunk_mesh = ChunkMesh(self.ctx, self.program, voxels)

    def load_texture(self, path):
        texture_surface = pg.image.load(path).convert_alpha()
        texture_surface = pg.transform.flip(texture_surface, False, True)
        texture_data = pg.image.tostring(texture_surface, 'RGBA')
        texture = self.ctx.texture(texture_surface.get_size(), 4, texture_data)
        texture.filter = (mgl.NEAREST, mgl.NEAREST)
        texture.build_mipmaps()
        return texture

    def update(self):
        self.program['m_view'].write(self.camera.get_view_matrix())

    def render(self):
        # This will be called to render the world and entities
        self.chunk_mesh.render()
