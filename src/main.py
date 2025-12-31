import pygame as pg
import moderngl as mgl
import sys
import os
import time
import numpy as np
from engine.renderer import Renderer
from ui.panorama import Panorama
from ui.splash import SplashText
from ui.elements import Button
from ui.hud import HUD
from game.player import Player
from game.commands import CommandHandler

class MinecraftClone:
    def __init__(self):
        pg.init()
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MAJOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MINOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_PROFILE_MASK, pg.GL_CONTEXT_PROFILE_CORE)
        
        self.screen_size = (1280, 720)
        self.screen = pg.display.set_mode(self.screen_size, pg.OPENGL | pg.DOUBLEBUF)
        self.ctx = mgl.create_context()
        
        self.ctx.enable(mgl.DEPTH_TEST | mgl.CULL_FACE | mgl.BLEND)
        
        self.clock = pg.time.Clock()
        
        # Get root directory
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        self.renderer = Renderer(self)
        self.panorama = Panorama(self.renderer)
        self.splash = SplashText(os.path.join(self.root_dir, 'assets', 'title', 'splashes.txt'))
        
        self.gui_surface = pg.Surface(self.screen_size, pg.SRCALPHA)
        self.gui_tex = self.ctx.texture(self.screen_size, 4)
        
        self.state = 'MENU'
        self.is_running = True
        
        self.load_assets()
        self.init_ui()
        
        self.player = Player()
        self.hud = HUD(self.icons_img)
        self.command_handler = CommandHandler(self)

    def load_assets(self):
        self.gui_img = pg.image.load(os.path.join(self.root_dir, 'assets', 'gui', 'gui.png')).convert_alpha()
        self.icons_img = pg.image.load(os.path.join(self.root_dir, 'assets', 'gui', 'icons.png')).convert_alpha()
        self.logo_img = pg.image.load(os.path.join(self.root_dir, 'assets', 'title', 'mclogo.png')).convert_alpha()

    def init_ui(self):
        hw, hh = self.screen_size[0] // 2, self.screen_size[1] // 2
        self.buttons = {
            'singleplayer': Button((hw - 200, hh - 48, 400, 40), "Singleplayer", self.gui_img),
            'options': Button((hw - 200, hh + 12, 400, 40), "Options...", self.gui_img),
            'quit': Button((hw - 200, hh + 72, 400, 40), "Quit Game", self.gui_img),
        }

    def handle_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.is_running = False
            if event.type == pg.MOUSEBUTTONDOWN:
                if self.state == 'MENU':
                    if self.buttons['singleplayer'].is_hovered:
                        self.state = 'GAME'
                        pg.mouse.set_visible(False)
                        pg.event.set_grab(True)
                    elif self.buttons['quit'].is_hovered:
                        self.is_running = False
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    if self.state == 'GAME':
                        self.state = 'MENU'
                        pg.mouse.set_visible(True)
                        pg.event.set_grab(False)
                    else:
                        self.is_running = False

    def update(self):
        dt = self.clock.get_time() / 1000.0
        now = time.time()
        
        if self.state == 'MENU':
            mouse_pos = pg.mouse.get_pos()
            for btn in self.buttons.values():
                btn.update(mouse_pos)
        else:
            self.player.update(dt, None, None) # Pass actual world and input
            self.renderer.update()

        pg.display.set_caption(f"Minecraft 1.0 (Python Edition) - FPS: {self.clock.get_fps():.0f}")

    def render(self):
        self.ctx.clear(color=(0.1, 0.1, 0.1))
        
        if self.state == 'MENU':
            self.panorama.render(time.time())
            self.render_menu_overlay()
        else:
            self.renderer.render()
            self.render_game_overlay()
            
        pg.display.flip()

    def render_menu_overlay(self):
        self.gui_surface.fill((0, 0, 0, 0))
        
        # Logo
        logo_rect = self.logo_img.get_rect(center=(self.screen_size[0]//2, 100))
        self.gui_surface.blit(self.logo_img, logo_rect)
        
        # Splash Text
        scale = self.splash.get_scale(time.time())
        font = pg.font.SysFont('Arial', int(24 * scale), bold=True)
        splash_surf = font.render(self.splash.current_splash, True, (255, 255, 0))
        splash_surf = pg.transform.rotate(splash_surf, self.splash.angle)
        self.gui_surface.blit(splash_surf, (logo_rect.right - 50, logo_rect.bottom - 20))
        
        # Buttons
        for btn in self.buttons.values():
            btn.draw(self.gui_surface)
            
        # Version Label
        font_small = pg.font.SysFont('Arial', 18)
        ver_surf = font_small.render("Minecraft 1.0 (Python Edition)", True, (255, 255, 255))
        self.gui_surface.blit(ver_surf, (10, self.screen_size[1] - 30))
        
        self.draw_gui_surface()

    def render_game_overlay(self):
        self.gui_surface.fill((0, 0, 0, 0))
        self.hud.draw(self.gui_surface, self.player)
        self.draw_gui_surface()

    def draw_gui_surface(self):
        data = pg.image.tostring(self.gui_surface, 'RGBA')
        self.gui_tex.write(data)
        self.gui_tex.use(location=1)
        # We need a simple quad to render this texture
        # For simplicity, I'll just skip the complex shader-based UI for now
        # and use a blit if possible, but ModernGL doesn't blit to screen directly easily
        # I'll use a simple helper to render a full-screen quad
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
            self.clock.tick(60)
        pg.quit()
        sys.exit()

if __name__ == "__main__":
    game = MinecraftClone()
    game.run()
