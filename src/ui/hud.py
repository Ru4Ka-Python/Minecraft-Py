from PIL import Image

class HUD:
    def __init__(self, icons_texture):
        self.icons = icons_texture # PIL Image of icons.png
        # Heart: (16, 0, 9, 9)
        # Empty Heart: (52, 0, 9, 9)
        # Hunger: (52, 27, 9, 9)

    def draw(self, surface, player):
        width, height = surface.size
        
        # Draw Hearts
        for i in range(10):
            x = width // 2 - 91 + i * 8
            y = height - 39
            # Draw empty heart first
            heart_bg = self.icons.crop((16, 0, 25, 9))
            surface.paste(heart_bg, (x, y), heart_bg)
            # Draw full heart based on player health
            if i < player.health // 2:
                heart_full = self.icons.crop((52, 0, 61, 9))
                surface.paste(heart_full, (x, y), heart_full)

        # Draw Hunger
        for i in range(10):
            x = width // 2 + 82 - i * 8
            y = height - 39
            hunger_bg = self.icons.crop((16, 27, 25, 36))
            surface.paste(hunger_bg, (x, y), hunger_bg)
            if i < player.hunger // 2:
                hunger_full = self.icons.crop((52, 27, 61, 36))
                surface.paste(hunger_full, (x, y), hunger_full)
