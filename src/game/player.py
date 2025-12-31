from game.entity import Entity
import glm

class Player(Entity):
    def __init__(self, position=(0, 10, 0)):
        super().__init__(position)
        self.health = 20
        self.hunger = 20
        self.exp = 0
        self.oxygen = 20
        self.inventory = [None] * 36
        self.selected_slot = 0

    def update(self, dt, world, input_handler):
        # Handle movement based on input
        speed = 5.0
        if input_handler.is_pressed('forward'):
            # Move forward relative to rotation
            pass
        super().update(dt, world)
