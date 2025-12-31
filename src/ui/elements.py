import pygame as pg

class Button:
    def __init__(self, rect, text, gui_texture):
        self.rect = pg.Rect(rect)
        self.text = text
        self.gui_texture = gui_texture # pygame surface of gui.png
        # Button texture in gui.png: 
        # Normal: (0, 66, 200, 20)
        # Hover: (0, 86, 200, 20)
        # Disabled: (0, 46, 200, 20)
        self.normal_uv = (0, 66, 200, 20)
        self.hover_uv = (0, 86, 200, 20)
        self.is_hovered = False

    def update(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def draw(self, surface):
        uv = self.hover_uv if self.is_hovered else self.normal_uv
        # Scale button texture to rect size
        btn_img = self.gui_texture.subsurface(uv)
        scaled_btn = pg.transform.scale(btn_img, (self.rect.width, self.rect.height))
        surface.blit(scaled_btn, self.rect)
        
        # Draw text (simplified)
        font = pg.font.SysFont('Arial', 20)
        text_surf = font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
