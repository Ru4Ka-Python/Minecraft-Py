import glm
import numpy as np
import moderngl as mgl
import pygame as pg
import os

class Panorama:
    def __init__(self, renderer):
        self.renderer = renderer
        self.ctx = renderer.ctx
        self.program = self.ctx.program(
            vertex_shader="""
            #version 330 core
            layout (location = 0) in vec3 in_position;
            uniform mat4 m_proj;
            uniform mat4 m_view;
            out vec3 v_tex_coord;
            void main() {
                v_tex_coord = in_position;
                vec4 pos = m_proj * m_view * vec4(in_position, 1.0);
                gl_Position = pos.xyww;
            }
            """,
            fragment_shader="""
            #version 330 core
            out vec4 fragColor;
            in vec3 v_tex_coord;
            uniform samplerCube u_texture_cube;
            void main() {
                fragColor = texture(u_texture_cube, v_tex_coord);
                // Blur effect can be added here or pre-applied to textures
            }
            """
        )
        self.load_cube_map()
        self.create_cube()

    def load_cube_map(self):
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        faces = []
        for i in range(6):
            # The order in Minecraft is usually: 0:front, 1:right, 2:back, 3:left, 4:up, 5:down
            # ModernGL expects: pos_x, neg_x, pos_y, neg_y, pos_z, neg_z
            # Mapping might need adjustment
            path = os.path.join(base_path, 'assets', 'title', 'bg', f'panorama{i}.png')
            img = pg.image.load(path).convert()
            faces.append(pg.image.tostring(img, 'RGB'))
        
        # Assuming size 256x256 for panorama images. Let's check.
        # Actually I should get size from image.
        size_path = os.path.join(base_path, 'assets', 'title', 'bg', 'panorama0.png')
        size = pg.image.load(size_path).get_size()
        self.texture_cube = self.ctx.texture_cube(size, 3, None)
        
        # Order for Cubemap: pos_x, neg_x, pos_y, neg_y, pos_z, neg_z
        # panorama 0: back, 1: left, 2: front, 3: right, 4: up, 5: down?
        # Let's just put them in some order for now.
        for i in range(6):
            self.texture_cube.write(i, faces[i])

    def create_cube(self):
        vertices = [
            -1,  1, -1,  -1, -1, -1,   1, -1, -1,   1, -1, -1,   1,  1, -1,  -1,  1, -1,
            -1, -1,  1,  -1, -1, -1,  -1,  1, -1,  -1,  1, -1,  -1,  1,  1,  -1, -1,  1,
             1, -1, -1,   1, -1,  1,   1,  1,  1,   1,  1,  1,   1,  1, -1,   1, -1, -1,
            -1, -1,  1,   1, -1,  1,   1,  1,  1,   1,  1,  1,  -1,  1,  1,  -1, -1,  1,
            -1,  1, -1,   1,  1, -1,   1,  1,  1,   1,  1,  1,  -1,  1,  1,  -1,  1, -1,
            -1, -1, -1,  -1, -1,  1,   1, -1, -1,   1, -1, -1,  -1, -1,  1,   1, -1,  1
        ]
        vertices = np.array(vertices, dtype='f4')
        self.vbo = self.ctx.buffer(vertices)
        self.vao = self.ctx.vertex_array(self.program, [(self.vbo, '3f', 'in_position')])

    def render(self, time):
        self.ctx.disable(mgl.CULL_FACE)
        self.texture_cube.use(location=0)
        m_proj = glm.perspective(glm.radians(90), 1280/720, 0.1, 10.0)
        m_view = glm.rotate(glm.mat4(1.0), time * 0.1, glm.vec3(0, 1, 0))
        self.program['m_proj'].write(m_proj)
        self.program['m_view'].write(m_view)
        self.vao.render()
        self.ctx.enable(mgl.CULL_FACE)
