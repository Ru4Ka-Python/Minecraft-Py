from PIL import Image, ImageDraw

class Rect:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    
    @property
    def left(self):
        return self.x
    
    @property
    def right(self):
        return self.x + self.width
    
    @property
    def top(self):
        return self.y
    
    @property
    def bottom(self):
        return self.y + self.height
    
    @property
    def center(self):
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    def collidepoint(self, point):
        px, py = point
        return self.left <= px <= self.right and self.top <= py <= self.bottom

class Button:
    def __init__(self, rect, text, gui_texture):
        self.rect = Rect(*rect)
        self.text = text
        self.gui_texture = gui_texture # PIL Image of gui.png
        # Button texture in gui.png: 
        # Normal: (0, 66, 200, 20)
        # Hover: (0, 86, 200, 20)
        # Disabled: (0, 46, 200, 20)
        self.normal_uv = (0, 66, 200, 20)
        self.hover_uv = (0, 86, 200, 20)
        self.is_hovered = False

    def update(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def draw(self, surface, draw, font):
        uv = self.hover_uv if self.is_hovered else self.normal_uv
        # Scale button texture to rect size
        btn_img = self.gui_texture.crop(uv)
        scaled_btn = btn_img.resize((self.rect.width, self.rect.height), Image.NEAREST)
        surface.paste(scaled_btn, (self.rect.x, self.rect.y), scaled_btn)
        
        # Draw text (simplified)
        text_size = font.getbbox(self.text)
        text_width = text_size[2] - text_size[0]
        text_height = text_size[3] - text_size[1]
        text_x = self.rect.center[0] - text_width // 2
        text_y = self.rect.center[1] - text_height // 2
        draw.text((text_x, text_y), self.text, fill=(255, 255, 255), font=font)
