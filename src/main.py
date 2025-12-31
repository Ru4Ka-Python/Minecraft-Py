import glfw
import moderngl as mgl
import sys
import os
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from engine.renderer import Renderer
from ui.panorama import Panorama
from ui.splash import SplashText
from ui.elements import Button
from ui.hud import HUD
from game.player import Player
from game.commands import CommandHandler

class MinecraftClone:
    def __init__(self):
        glfw.init()
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        
        self.screen_size = (1280, 720)
        self.window = glfw.create_window(self.screen_size[0], self.screen_size[1], "Minecraft Clone", None, None)
        glfw.make_context_current(self.window)
        glfw.set_window_user_pointer(self.window, self)
        glfw.set_key_callback(self.window, self.key_callback)
        glfw.set_mouse_button_callback(self.window, self.mouse_button_callback)
        glfw.set_cursor_pos_callback(self.window, self.cursor_position_callback)
        
        self.ctx = mgl.create_context()
        
        self.ctx.enable(mgl.DEPTH_TEST | mgl.CULL_FACE | mgl.BLEND)
        
        self.last_time = time.time()
        
        # Get root directory
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        self.renderer = Renderer(self)
        self.panorama = Panorama(self.renderer)
        self.splash = SplashText(os.path.join(self.root_dir, 'assets', 'title', 'splashes.txt'))
        
        self.gui_surface = Image.new('RGBA', self.screen_size, (0, 0, 0, 0))
        self.gui_tex = self.ctx.texture(self.screen_size, 4)
        
        self.state = 'MENU'
        self.is_running = True
        self.mouse_pos = (0, 0)
        self.keys_pressed = set()
        
        self.load_assets()
        self.init_ui()
        
        self.player = Player()
        self.hud = HUD(self.icons_img)
        self.command_handler = CommandHandler(self)

    def load_assets(self):
        self.gui_img = Image.open(os.path.join(self.root_dir, 'assets', 'gui', 'gui.png')).convert('RGBA')
        self.icons_img = Image.open(os.path.join(self.root_dir, 'assets', 'gui', 'icons.png')).convert('RGBA')
        self.logo_img = Image.open(os.path.join(self.root_dir, 'assets', 'title', 'mclogo.png')).convert('RGBA')
        self.font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 24)
        self.font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)

    def init_ui(self):
        hw, hh = self.screen_size[0] // 2, self.screen_size[1] // 2
        self.buttons = {
            'singleplayer': Button((hw - 200, hh - 48, 400, 40), "Singleplayer", self.gui_img),
            'options': Button((hw - 200, hh + 12, 400, 40), "Options...", self.gui_img),
            'quit': Button((hw - 200, hh + 72, 400, 40), "Quit Game", self.gui_img),
        }

    def key_callback(self, window, key, scancode, action, mods):
        if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
            if self.state == 'GAME':
                self.state = 'MENU'
                glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_NORMAL)
            else:
                self.is_running = False
    
    def mouse_button_callback(self, window, button, action, mods):
        if action == glfw.PRESS and button == glfw.MOUSE_BUTTON_LEFT:
            if self.state == 'MENU':
                if self.buttons['singleplayer'].is_hovered:
                    self.state = 'GAME'
                    glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)
                elif self.buttons['quit'].is_hovered:
                    self.is_running = False
    
    def cursor_position_callback(self, window, xpos, ypos):
        self.mouse_pos = (int(xpos), int(ypos))

    def handle_events(self):
        if glfw.window_should_close(self.window):
            self.is_running = False
        glfw.poll_events()

    def update(self):
        current_time = time.time()
        dt = current_time - self.last_time
        self.last_time = current_time
        now = time.time()
        
        if self.state == 'MENU':
            for btn in self.buttons.values():
                btn.update(self.mouse_pos)
        else:
            self.player.update(dt, None, None)
            self.renderer.update()
        
        fps = 1.0 / dt if dt > 0 else 0
        glfw.set_window_title(self.window, f"Minecraft 1.0 (Python Edition) - FPS: {fps:.0f}")

    def render(self):
        self.ctx.clear(color=(0.1, 0.1, 0.1))
        
        if self.state == 'MENU':
            self.panorama.render(time.time())
            self.render_menu_overlay()
        else:
            self.renderer.render()
            self.render_game_overlay()
            
        glfw.swap_buffers(self.window)

    def render_menu_overlay(self):
        self.gui_surface = Image.new('RGBA', self.screen_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(self.gui_surface)
        
        # Logo
        logo_size = self.logo_img.size
        logo_pos = ((self.screen_size[0] - logo_size[0]) // 2, 100 - logo_size[1] // 2)
        self.gui_surface.paste(self.logo_img, logo_pos, self.logo_img)
        
        # Splash Text
        scale = self.splash.get_scale(time.time())
        scaled_size = int(24 * scale)
        splash_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', scaled_size)
        
        splash_surf = Image.new('RGBA', (400, 50), (0, 0, 0, 0))
        splash_draw = ImageDraw.Draw(splash_surf)
        splash_draw.text((200, 25), self.splash.current_splash, fill=(255, 255, 0, 255), font=splash_font, anchor='mm')
        splash_surf = splash_surf.rotate(self.splash.angle, expand=True, fillcolor=(0, 0, 0, 0))
        
        splash_pos = (logo_pos[0] + logo_size[0] - 50, logo_pos[1] + logo_size[1] - 20)
        self.gui_surface.paste(splash_surf, splash_pos, splash_surf)
        
        # Buttons
        for btn in self.buttons.values():
            btn.draw(self.gui_surface, draw, self.font)
            
        # Version Label
        draw.text((10, self.screen_size[1] - 30), "Minecraft 1.0 (Python Edition)", fill=(255, 255, 255), font=self.font_small)
        
        self.draw_gui_surface()

    def render_game_overlay(self):
        self.gui_surface = Image.new('RGBA', self.screen_size, (0, 0, 0, 0))
        self.hud.draw(self.gui_surface, self.player)
        self.draw_gui_surface()

    def draw_gui_surface(self):
        data = self.gui_surface.tobytes()
        self.gui_tex.write(data)
        self.gui_tex.use(location=1)
        self.render_quad(self.gui_tex)

    def render_quad(self, texture):
        # Full screen quad rendering logic
        if not hasattr(self, 'quad_vao'):
            vertices = np.array([
                -1, -1, 0, 0, 0,
                 1, -1, 0, 1, 0,
                 1,  1, 0, 1, 1,
                -1, -1, 0, 0, 0,
                 1,  1, 0, 1, 1,
                -1,  1, 0, 0, 1,
            ], dtype='f4')
            self.quad_vbo = self.ctx.buffer(vertices)
            self.quad_program = self.ctx.program(
                vertex_shader="""
                #version 330 core
                layout (location = 0) in vec3 in_position;
                layout (location = 1) in vec2 in_tex_coord;
                out vec2 v_tex_coord;
                void main() {
                    gl_Position = vec4(in_position, 1.0);
                    v_tex_coord = in_tex_coord;
                }
                """,
                fragment_shader="""
                #version 330 core
                out vec4 fragColor;
                in vec2 v_tex_coord;
                uniform sampler2D u_texture;
                void main() {
                    fragColor = texture(u_texture, v_tex_coord);
                }
                """
            )
            self.quad_vao = self.ctx.vertex_array(self.quad_program, [(self.quad_vbo, '3f 2f', 'in_position', 'in_tex_coord')])
        
        texture.use(location=0)
        self.quad_vao.render()

    def run(self):
        while self.is_running:
            self.handle_events()
            self.update()
            self.render()
        glfw.terminate()
        sys.exit()

if __name__ == "__main__":
    game = MinecraftClone()
    game.run()
