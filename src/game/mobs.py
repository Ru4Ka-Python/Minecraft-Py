import random
import glm
from game.entity import Entity

class Mob(Entity):
    def __init__(self, position):
        super().__init__(position)
        self.target = None
        self.ai_state = 'idle'

    def update_ai(self, player_pos):
        dist = glm.distance(self.position, player_pos)
        if dist < 16:
            self.ai_state = 'chase'
            self.target = player_pos
        else:
            self.ai_state = 'idle'

class Zombie(Mob):
    def update(self, dt, world, player_pos):
        self.update_ai(player_pos)
        if self.ai_state == 'chase':
            dir = glm.normalize(player_pos - self.position)
            dir.y = 0
            self.velocity.x = dir.x * 2.0
            self.velocity.z = dir.z * 2.0
        else:
            self.velocity.x = 0
            self.velocity.z = 0
        super().update(dt, world)

class Creeper(Mob):
    def __init__(self, position):
        super().__init__(position)
        self.fuse_time = 0
        self.is_primed = False

    def update(self, dt, world, player_pos):
        dist = glm.distance(self.position, player_pos)
        if dist < 3:
            self.is_primed = True
            self.fuse_time += dt
        else:
            self.is_primed = False
            self.fuse_time = max(0, self.fuse_time - dt)
            
        if self.fuse_time > 1.5:
            self.explode()
        
        super().update(dt, world, player_pos)

    def explode(self):
        # Explosion logic
        pass
