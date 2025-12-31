import pygame as pg

class HUD:
    def __init__(self, icons_texture):
        self.icons = icons_texture # pygame surface of icons.png
        # Heart: (16, 0, 9, 9)
        # Empty Heart: (52, 0, 9, 9)
        # Hunger: (52, 27, 9, 9)

    def draw(self, surface, player):
        width, height = surface.get_size()
        
        # Draw Hearts
        for i in range(10):
            x = width // 2 - 91 + i * 8
            y = height - 39
            # Draw empty heart first
            surface.blit(self.icons.subsurface((16, 0, 9, 9)), (x, y))
            # Draw full heart based on player health
            if i < player.health // 2:
                surface.blit(self.icons.subsurface((52, 0, 9, 9)), (x, y))

        # Draw Hunger
        for i in range(10):
            x = width // 2 + 82 - i * 8
            y = height - 39
            surface.blit(self.icons.subsurface((16, 27, 9, 9)), (x, y)) # Background
            if i < player.hunger // 2:
                surface.blit(self.icons.subsurface((52, 27, 9, 9)), (x, y))
