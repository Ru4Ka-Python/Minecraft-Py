"""
Renderer module using ModernGL for OpenGL rendering.
Handles terrain rendering, block faces, and 3D scene management.
"""

import moderngl
import numpy as np
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from PIL import Image
import math
import os

from engine.window import Window
from utils.config import Config

@dataclass
class BlockVertex:
    """Vertex data for a block face."""
    x: float
    y: float
    z: float
    u: float
    v: float
    texture_id: int
    light_level: int

class TerrainRenderer:
    """Handles terrain rendering using ModernGL."""
    
    VERTEX_SHADER = '''
        #version 330
        
        uniform mat4 model;
        uniform mat4 view;
        uniform mat4 projection;
        
        in vec3 in_position;
        in vec2 in_texcoord;
        in float in_texture_id;
        in float in_light;
        
        out vec2 v_texcoord;
        out float v_texture_id;
        out float v_light;
        out vec3 v_position;
        
        void main() {
            v_texcoord = in_texcoord;
            v_texture_id = in_texture_id;
            v_light = in_light;
            v_position = in_position;
            gl_Position = projection * view * model * vec4(in_position, 1.0);
        }
    '''
    
    FRAGMENT_SHADER = '''
        #version 330
        
        uniform sampler2DArray texture_array;
        uniform float fog_start;
        uniform float fog_end;
        uniform vec3 fog_color;
        uniform int fog_type;  // 0 = normal, 1 = underwater, 2 = lava
        
        in vec2 v_texcoord;
        in float v_texture_id;
        in float v_light;
        in vec3 v_position;
        
        out vec4 fragColor;
        
        void main() {
            vec4 texColor = texture(texture_array, vec3(v_texcoord, v_texture_id));
            
            // Apply lighting (simple ambient + directional)
            float light = v_light / 15.0;
            light = max(light, 0.3);  // Minimum ambient light
            
            // Tinting for biomes
            vec3 tinted = texColor.rgb * light;
            
            // Apply fog
            float dist = length(v_position);
            float fogFactor = clamp((dist - fog_start) / (fog_end - fog_start), 0.0, 1.0);
            
            vec3 finalFogColor = fog_color;
            if (fog_type == 1) {
                finalFogColor = vec3(0.0, 0.2, 0.4);  // Blue underwater
            } else if (fog_type == 2) {
                finalFogColor = vec3(0.6, 0.2, 0.0);  // Orange lava
            }
            
            fragColor = vec4(mix(tinted, finalFogColor, fogFactor), texColor.a);
        }
    '''
    
    def __init__(self, window: Window, fov: int = 70):
        """Initialize terrain renderer."""
        self.window = window
        self.ctx = moderngl.create_context()
        
        # Enable features
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.CULL_FACE)
        self.ctx.cull_face = 'back'
        
        # Create shader program
        self.program = self.ctx.program(
            vertex_shader=self.VERTEX_SHADER,
            fragment_shader=self.FRAGMENT_SHADER
        )
        
        # Create terrain buffer
        self.terrain_vbo = self.ctx.buffer(reserve=1024 * 1024 * 4 * 6 * 6)  # Reserve space
        self.terrain_vao = self.ctx.vertex_array(
            self.program,
            [
                (self.terrain_vbo, '3f 2f f f', 'in_position', 'in_texcoord', 'in_texture_id', 'in_light')
            ]
        )
        
        # Texture array for terrain
        self.texture_array = None
        self._load_texture_atlas()
        
        # Camera matrices
        self._fov = fov
        self._aspect = window.get_aspect_ratio()
        self._update_projection()
        
        # Render settings
        self.fog_start = 50.0
        self.fog_end = 100.0
        self.fog_color = (0.5, 0.7, 0.9)
        self.fog_type = 0
        
        # Block data
        self.visible_blocks: Set[Tuple[int, int, int]] = set()
        self.render_data: List[np.ndarray] = []
    
    def _load_texture_atlas(self) -> None:
        """Load terrain texture atlas."""
        atlas_path = 'assets/terrain.png'
        if not os.path.exists(atlas_path):
            # Create a simple placeholder texture
            self._create_placeholder_texture()
            return
        
        try:
            atlas = Image.open(atlas_path)
            atlas = atlas.convert('RGBA')
            width, height = atlas.size
            
            # Create 2D array texture for Minecraft's 16x16 grid
            # Standard terrain.png has 16x16 block faces = 256x16 or similar
            num_textures = 256  # Max textures
            
            # Convert atlas to numpy array
            atlas_data = np.array(atlas, dtype=np.uint8)
            
            # Create texture array
            self.texture_array = self.ctx.texture_array((num_textures, 16, 16), 4)
            
            # Extract each 16x16 tile
            tiles_x = width // 16
            tiles_y = height // 16
            
            for y in range(min(tiles_y, num_textures)):
                for x in range(min(tiles_x, num_textures // tiles_y)):
                    idx = y * tiles_x + x
                    if idx < num_textures:
                        tile = atlas_data[y*16:(y+1)*16, x*16:(x+1)*16]
                        self.texture_array.write(idx, tile.tobytes())
            
            self.texture_array.filter = (moderngl.NEAREST, moderngl.NEAREST)
            self.texture_array.use(0)
            
        except Exception as e:
            print(f"Failed to load texture atlas: {e}")
            self._create_placeholder_texture()
    
    def _create_placeholder_texture(self) -> None:
        """Create a placeholder texture when atlas is missing."""
        num_textures = 256
        
        # Create a simple colored texture
        data = np.zeros((num_textures, 16, 16, 4), dtype=np.uint8)
        
        # Generate unique colors for each texture
        for i in range(num_textures):
            r = (i % 16) * 17
            g = ((i // 16) % 16) * 17
            b = (i // 256) * 17
            data[i, :, :, 0] = r
            data[i, :, :, 1] = g
            data[i, :, :, 2] = b
            data[i, :, :, 3] = 255
        
        self.texture_array = self.ctx.texture_array((num_textures, 16, 16), 4)
        self.texture_array.write(data.tobytes())
        self.texture_array.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self.texture_array.use(0)
    
    def _update_projection(self) -> None:
        """Update projection matrix."""
        fov_rad = math.radians(self._fov)
        aspect = self._aspect
        near = 0.1
        far = 1000.0
        
        f = 1.0 / math.tan(fov_rad / 2)
        
        projection = np.array([
            [f / aspect, 0, 0, 0],
            [0, f, 0, 0],
            [0, 0, (far + near) / (near - far), -1],
            [0, 0, (2 * far * near) / (near - far), 0]
        ], dtype=np.float32)
        
        self.program['projection'].write(projection.T.tobytes())
    
    def set_fov(self, fov: int) -> None:
        """Set field of view."""
        self._fov = max(45, min(90, fov))
        self._update_projection()
    
    def set_fog(self, start: float, end: float, color: Tuple[float, float, float], fog_type: int = 0) -> None:
        """Set fog parameters."""
        self.fog_start = start
        self.fog_end = end
        self.fog_color = color
        self.fog_type = fog_type
        
        self.program['fog_start'].value = start
        self.program['fog_end'].value = end
        self.program['fog_color'].value = color
        self.program['fog_type'].value = fog_type
    
    def clear(self) -> None:
        """Clear the screen."""
        self.ctx.clear(*self.fog_color, 1.0)
    
    def render(self, camera_matrix: np.ndarray, model_matrix: np.ndarray = None) -> None:
        """Render terrain with given camera."""
        # Update view matrix
        self.program['view'].write(camera_matrix.T.tobytes())
        
        # Update model matrix
        if model_matrix is None:
            model_matrix = np.eye(4, dtype=np.float32)
        self.program['model'].write(model_matrix.T.tobytes())
        
        # Update fog uniforms
        self.program['fog_start'].value = self.fog_start
        self.program['fog_end'].value = self.fog_end
        self.program['fog_color'].value = self.fog_color
        self.program['fog_type'].value = self.fog_type
        
        # Render terrain VAO
        if self.terrain_vao and self.render_data:
            self.terrain_vao.render(moderngl.TRIANGLES)
    
    def update_terrain(self, blocks: Dict[Tuple[int, int, int], 'Block']) -> None:
        """Update terrain mesh with new block data."""
        vertices = []
        
        for pos, block in blocks.items():
            # Get visible faces using frustum culling
            visible = self._get_visible_faces(pos, blocks)
            
            for face, light_level in visible:
                face_verts = self._get_face_vertices(pos, face, block)
                vertices.extend(face_verts)
        
        if vertices:
            vertex_data = np.array(vertices, dtype=np.float32)
            self.terrain_vbo.write(vertex_data.tobytes())
            self.terrain_vao.num_vertices = len(vertices) // 6
        else:
            self.terrain_vao.num_vertices = 0
    
    def _get_visible_faces(self, pos: Tuple[int, int, int], blocks: Dict) -> List:
        """Get visible faces for a block (culling occluded faces)."""
        visible = []
        x, y, z = pos
        
        # Define neighbor offsets for each face
        neighbors = {
            'top': (0, 1, 0),
            'bottom': (0, -1, 0),
            'front': (0, 0, 1),
            'back': (0, 0, -1),
            'right': (1, 0, 0),
            'left': (-1, 0, 0)
        }
        
        for face, offset in neighbors.items():
            neighbor_pos = (x + offset[0], y + offset[1], z + offset[2])
            if neighbor_pos not in blocks:
                # Face is visible (no neighbor block)
                visible.append((face, 15))  # Default light level
        
        return visible
    
    def _get_face_vertices(self, pos: Tuple[int, int, int], face: str, block: 'Block') -> List:
        """Get vertices for a single face."""
        x, y, z = pos
        
        # Face definitions: (u, v) coordinates and texture index
        face_data = {
            'top': {'verts': [0,1,0, 1,1,0, 1,1,1, 0,1,0, 1,1,1, 0,1,1],
                    'uv': [0,0, 1,0, 1,1, 0,0, 1,1, 0,1],
                    'tex': block.get_top_texture()},
            'bottom': {'verts': [0,0,0, 1,0,1, 1,0,0, 0,0,0, 0,0,1, 1,0,1],
                       'uv': [0,0, 1,1, 1,0, 0,0, 0,1, 1,1],
                       'tex': block.get_bottom_texture()},
            'front': {'verts': [0,0,1, 1,0,1, 1,1,1, 0,0,1, 1,1,1, 0,1,1],
                      'uv': [0,0, 1,0, 1,1, 0,0, 1,1, 0,1],
                      'tex': block.get_side_texture()},
            'back': {'verts': [1,0,0, 0,0,0, 0,1,0, 1,0,0, 0,1,0, 1,1,0],
                     'uv': [0,0, 1,0, 1,1, 0,0, 1,1, 0,1],
                     'tex': block.get_side_texture()},
            'right': {'verts': [1,0,1, 1,0,0, 1,1,0, 1,0,1, 1,1,0, 1,1,1],
                      'uv': [0,0, 1,0, 1,1, 0,0, 1,1, 0,1],
                      'tex': block.get_side_texture()},
            'left': {'verts': [0,0,0, 0,0,1, 0,1,1, 0,0,0, 0,1,1, 0,1,0],
                     'uv': [0,0, 1,0, 1,1, 0,0, 1,1, 0,1],
                     'tex': block.get_side_texture()}
        }
        
        data = face_data[face]
        verts = data['verts']
        uvs = data['uv']
        tex = data['tex']
        
        # Create vertex data
        vertices = []
        for i in range(6):
            vertices.extend([x + verts[i*3], y + verts[i*3+1], z + verts[i*3+2]])
            vertices.extend([uvs[i*2], uvs[i*2+1]])
            vertices.append(tex)
            vertices.append(15.0)  # Light level
        
        return vertices
    
    def cleanup(self) -> None:
        """Cleanup renderer resources."""
        if self.terrain_vbo:
            self.terrain_vbo.release()
        if self.terrain_vao:
            self.terrain_vao.release()
        if self.texture_array:
            self.texture_array.release()
        if self.program:
            self.ctx.release()


class Renderer:
    """Main renderer class managing all rendering components."""
    
    def __init__(self, window: Window, fov: int = 70):
        """Initialize renderer."""
        self.window = window
        self.ctx = moderngl.create_context(require=330)
        
        # Enable OpenGL features
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.CULL_FACE)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        
        # Create terrain renderer
        self.terrain = TerrainRenderer(window, fov)
        
        # Create sky renderer
        self.sky = SkyRenderer(window)
        
        # Create entity renderer
        self.entities = EntityRenderer(window)
        
        # Create particle renderer
        self.particles = ParticleRenderer(window)
        
        # UI renderer
        self.ui = UIRenderer(window)
    
    def clear(self) -> None:
        """Clear screen for new frame."""
        self.ctx.clear(0.5, 0.7, 0.9, 1.0)
    
    def render(self, camera, world, entities, particles) -> None:
        """Render the complete scene."""
        # Clear
        self.clear()
        
        # Render sky
        self.sky.render(camera)
        
        # Update and render terrain
        if world:
            self.terrain.update_terrain(world.blocks)
            self.terrain.render(camera.view_matrix, camera.model_matrix)
        
        # Render entities
        if entities:
            self.entities.render(entities, camera)
        
        # Render particles
        if particles:
            self.particles.render(particles, camera)
        
        # Render UI (separate from 3D)
        self.ui.render()
    
    def set_fov(self, fov: int) -> None:
        """Set field of view."""
        self.terrain.set_fov(fov)
    
    def set_fog(self, start: float, end: float, color: Tuple, fog_type: int = 0) -> None:
        """Set fog parameters."""
        self.terrain.set_fog(start, end, color, fog_type)
    
    def resize(self, width: int, height: int) -> None:
        """Handle window resize."""
        self.ctx.viewport = (0, 0, width, height)
    
    def cleanup(self) -> None:
        """Cleanup all renderer resources."""
        self.terrain.cleanup()
        self.sky.cleanup()
        self.entities.cleanup()
        self.particles.cleanup()
        self.ui.cleanup()


class SkyRenderer:
    """Renders skybox and day/night cycle."""
    
    def __init__(self, window: Window):
        """Initialize sky renderer."""
        self.window = window
        self.ctx = moderngl.create_context(require=330)
        
        # Sky vertices (cube)
        vertices = np.array([
            -1, -1, -1,  1, -1, -1,  1,  1, -1, -1, -1, -1,  1,  1, -1, -1,  1, -1,
            -1, -1,  1,  1, -1,  1,  1,  1,  1, -1, -1,  1,  1,  1,  1, -1,  1,  1,
            -1, -1, -1, -1,  1, -1, -1,  1,  1, -1, -1, -1, -1,  1,  1, -1, -1,  1,
             1, -1, -1,  1,  1, -1,  1,  1,  1,  1, -1, -1,  1,  1,  1,  1, -1,  1,
            -1, -1, -1, -1, -1,  1,  1, -1,  1, -1, -1, -1,  1, -1,  1,  1, -1, -1,
            -1,  1, -1, -1,  1,  1,  1,  1,  1, -1,  1, -1,  1,  1,  1,  1,  1, -1,
        ], dtype=np.float32)
        
        self.vbo = self.ctx.buffer(vertices.tobytes())
        self.vao = self.ctx.vertex_array(
            self.ctx.program(
                vertex_shader='''
                    #version 330
                    uniform mat4 view;
                    uniform mat4 projection;
                    in vec3 in_position;
                    out vec3 v_position;
                    void main() {
                        v_position = in_position;
                        gl_Position = projection * view * vec4(in_position * 500, 1.0);
                    }
                ''',
                fragment_shader='''
                    #version 330
                    in vec3 v_position;
                    out vec4 fragColor;
                    uniform vec3 sky_color;
                    uniform float time;
                    void main() {
                        float t = (v_position.y + 1.0) * 0.5;
                        vec3 dayColor = sky_color;
                        vec3 nightColor = vec3(0.02, 0.02, 0.08);
                        vec3 sunsetColor = vec3(0.8, 0.4, 0.2);
                        
                        float sunPos = sin(time * 0.1);
                        if (v_position.y > 0) {
                            vec3 finalColor = mix(nightColor, dayColor, max(sunPos, 0));
                            finalColor = mix(finalColor, sunsetColor, max(-sunPos * 2, 0) * (1.0 - t));
                            fragColor = vec4(finalColor, 1.0);
                        } else {
                            fragColor = vec4(nightColor, 1.0);
                        }
                    }
                '''
            ),
            [(self.vbo, '3f', 'in_position')]
        )
        
        self.time = 0.0
    
    def render(self, camera) -> None:
        """Render sky."""
        self.ctx.disable(moderngl.DEPTH_TEST)
        
        self.vao.program['view'].write(camera.view_matrix.T.tobytes())
        self.vao.program['projection'].write(camera.projection_matrix.T.tobytes())
        self.vao.program['sky_color'].value = (0.5, 0.7, 0.9)
        self.vao.program['time'].value = self.time
        
        self.vao.render(moderngl.TRIANGLES)
        
        self.ctx.enable(moderngl.DEPTH_TEST)
    
    def update(self, delta_time: float) -> None:
        """Update sky time."""
        self.time += delta_time
    
    def cleanup(self) -> None:
        """Cleanup sky renderer."""
        self.vbo.release()
        self.vao.release()


class EntityRenderer:
    """Renders entities (mobs, items, player)."""
    
    def __init__(self, window: Window):
        """Initialize entity renderer."""
        self.window = window
        self.ctx = moderngl.create_context(require=330)
        
        # Simple quad for entities
        vertices = np.array([
            -0.5, 0, 0, 0, 0,
             0.5, 0, 0, 1, 0,
             0.5, 1, 0, 1, 1,
            -0.5, 0, 0, 0, 0,
             0.5, 1, 0, 1, 1,
            -0.5, 1, 0, 0, 1,
        ], dtype=np.float32)
        
        self.vbo = self.ctx.buffer(vertices.tobytes())
        self.vao = self.ctx.vertex_array(
            self.ctx.program(
                vertex_shader='''
                    #version 330
                    uniform mat4 view;
                    uniform mat4 projection;
                    uniform mat4 model;
                    in vec3 in_position;
                    in vec2 in_texcoord;
                    out vec2 v_texcoord;
                    void main() {
                        v_texcoord = in_texcoord;
                        gl_Position = projection * view * model * vec4(in_position, 1.0);
                    }
                ''',
                fragment_shader='''
                    #version 330
                    uniform sampler2D texture;
                    in vec2 v_texcoord;
                    out vec4 fragColor;
                    void main() {
                        fragColor = texture(texture, v_texcoord);
                    }
                '''
            ),
            [(self.vbo, '3f 2f', 'in_position', 'in_texcoord')]
        )
    
    def render(self, entities, camera) -> None:
        """Render all entities."""
        self.vao.program['view'].write(camera.view_matrix.T.tobytes())
        self.vao.program['projection'].write(camera.projection_matrix.T.tobytes())
        
        for entity in entities:
            if entity.is_visible(camera):
                # Build model matrix for entity
                model = entity.get_model_matrix()
                self.vao.program['model'].write(model.T.tobytes())
                self.vao.render(moderngl.TRIANGLES)
    
    def cleanup(self) -> None:
        """Cleanup entity renderer."""
        self.vbo.release()
        self.vao.release()


class ParticleRenderer:
    """Renders particles (dust, smoke, hearts, stars)."""
    
    def __init__(self, window: Window):
        """Initialize particle renderer."""
        self.window = window
        self.ctx = moderngl.create_context(require=330)
        
        # Billboard particles
        vertices = np.array([
            -0.1, -0.1, 0, 0, 0,
             0.1, -0.1, 0, 1, 0,
             0.1,  0.1, 0, 1, 1,
            -0.1, -0.1, 0, 0, 0,
             0.1,  0.1, 0, 1, 1,
            -0.1,  0.1, 0, 0, 1,
        ], dtype=np.float32)
        
        self.vbo = self.ctx.buffer(vertices.tobytes())
        self.vao = self.ctx.vertex_array(
            self.ctx.program(
                vertex_shader='''
                    #version 330
                    uniform mat4 view;
                    uniform mat4 projection;
                    uniform mat4 model;
                    in vec3 in_position;
                    in vec2 in_texcoord;
                    out vec2 v_texcoord;
                    void main() {
                        v_texcoord = in_texcoord;
                        gl_Position = projection * view * model * vec4(in_position, 1.0);
                    }
                ''',
                fragment_shader='''
                    #version 330
                    uniform sampler2D texture;
                    uniform float alpha;
                    in vec2 v_texcoord;
                    out vec4 fragColor;
                    void main() {
                        fragColor = texture(texture, v_texcoord);
                        fragColor.a *= alpha;
                    }
                '''
            ),
            [(self.vbo, '3f 2f', 'in_position', 'in_texcoord')]
        )
    
    def render(self, particles, camera) -> None:
        """Render all particles."""
        self.ctx.enable(moderngl.BLEND)
        self.vao.program['view'].write(camera.view_matrix.T.tobytes())
        self.vao.program['projection'].write(camera.projection_matrix.T.tobytes())
        
        for particle in particles:
            if particle.active:
                model = particle.get_model_matrix(camera)
                self.vao.program['model'].write(model.T.tobytes())
                self.vao.program['alpha'].value = particle.alpha
                self.vao.render(moderngl.TRIANGLES)
        
        self.ctx.disable(moderngl.BLEND)
    
    def cleanup(self) -> None:
        """Cleanup particle renderer."""
        self.vbo.release()
        self.vao.release()


class UIRenderer:
    """Renders UI elements (HUD, menus, inventory)."""
    
    def __init__(self, window: Window):
        """Initialize UI renderer."""
        self.window = window
        self.ctx = moderngl.create_context(require=330)
        
        # Disable depth testing for UI
        self.ctx.disable(moderngl.DEPTH_TEST)
        
        # Full screen quad for UI
        vertices = np.array([
            -1, -1, 0, 0,
             1, -1, 0, 1,
             1,  1, 0, 1,
            -1, -1, 0, 0,
             1,  1, 0, 1,
            -1,  1, 0, 0,
        ], dtype=np.float32)
        
        self.vbo = self.ctx.buffer(vertices.tobytes())
        self.vao = self.ctx.vertex_array(
            self.ctx.program(
                vertex_shader='''
                    #version 330
                    in vec2 in_position;
                    in vec2 in_texcoord;
                    out vec2 v_texcoord;
                    void main() {
                        v_texcoord = in_texcoord;
                        gl_Position = vec4(in_position, 0.0, 1.0);
                    }
                ''',
                fragment_shader='''
                    #version 330
                    uniform sampler2D texture;
                    in vec2 v_texcoord;
                    out vec4 fragColor;
                    void main() {
                        fragColor = texture(texture, v_texcoord);
                    }
                '''
            ),
            [(self.vbo, '2f 2f', 'in_position', 'in_texcoord')]
        )
    
    def render(self) -> None:
        """Render UI layer."""
        pass  # UI rendered separately
    
    def cleanup(self) -> None:
        """Cleanup UI renderer."""
        self.vbo.release()
        self.vao.release()
